# Stock Strategy Backtester

This is a Python-based stock strategy backtester I built to develop, test, and evaluate mechanical trading strategies using historical price data.

The goal is to take trading ideas, turn them into defined rules, and see how those rules perform over time. Rather than relying on individual trades or assumptions about what should work, I want to understand how a strategy behaves across different market conditions, particularly in terms of profitability, drawdown, and risk.

The project is split into four files so I can work on indicators, strategy logic, execution, and data separately.

## How the files work together

```text
Historical OHLCV data (CSV)
            |
            v
     strategy_test.py  <------ strategies.py
        |     |                   |
        |     +-------------------+----> indicators.py
        |
        v
Trade simulation and position tracking
        |
        v
Trade log, performance statistics, equity curve

mt5.py ---> MetaTrader 5 daily candles ---> strategy preparation
```

### `indicators.py` — Calculations

This file contains the technical indicator functions used to build strategies. It takes price and volume series and returns calculated values that can be added to a pandas DataFrame.

It currently includes moving averages, RSI, rate of change, stochastic, MACD components, ADX, ATR, Bollinger Bands, Keltner Channels, money flow, CCI, and other indicators.

Keeping these calculations separate means I can reuse the same indicators across different strategies without rewriting them.

### `strategies.py` — Trading rules

This is where I define the actual strategies. Each strategy is its own class, with rules for when to enter a long or short position. Some use trend and momentum, while others focus on breakouts, mean reversion, volatility, or day-of-week conditions.

Strategies generally use the following methods:

- `prepare(df)` calculates any indicators or additional columns needed before testing.
- `get_signal(df, i, position, open_pnl)` returns `1` for a long signal, `-1` for a short signal, or `None` when no new signal is generated.
- `get_order(...)`, where implemented, returns pending buy-stop or sell-stop orders instead of a directional signal.

The same file also contains exit strategies, including dollar-based stops and targets, ATR-based exits, time-based exits, and other exit conditions. Entry and exit logic can be selected independently when running a backtest.

### `strategy_test.py` — Backtesting engine

This is the main file. It loads historical stock data, selects the entry and exit strategies, runs the simulation, and reports the results.

The `run_backtest()` function processes the data one candle at a time while tracking positions, entry and exit prices, shares, realized and unrealized PnL, cash, and equity.

The current execution logic includes:

- Long and short positions.
- Directional signals executed at the next candle's open.
- Pending buy-stop and sell-stop orders, with gap-aware fill prices.
- Stop-loss and profit-target checks using daily OHLC prices.
- A conservative assumption that the stop is hit first if both the stop and target are reached within the same candle.
- Position sizing based on a percentage of current cash.
- Trade history, drawdown calculations, and an equity curve by closed trade.

The output includes final cash and equity, percentage gains, maximum drawdown, long and short trade counts, individual trade records, and details about any position still open at the end of the test.

### `mt5.py` — Market data connection

This file connects Python to a running MetaTrader 5 terminal. It can search available broker symbols and request historical daily candles.

The returned data is converted into the same `Open`, `High`, `Low`, `Close`, and `Volume` format used by the backtester. The data request skips the currently forming candle.

At the moment, this is a separate data-access and strategy-preparation script. The main backtest in `strategy_test.py` still reads historical data from a local CSV file; it does not automatically run on the data retrieved by `mt5.py`.

## Running a backtest

Install the core dependencies:

```bash
pip install pandas numpy matplotlib
```

If using the MetaTrader 5 integration, also install:

```bash
pip install MetaTrader5
```

The MT5 integration requires an accessible MetaTrader 5 terminal and a connected account. It is separate from the CSV-based backtest.

The current test script expects historical data at:

```text
algo/stockdata/SPY.csv
```

The CSV should contain a `Date` column and `Open`, `High`, `Low`, `Close`, and `Volume` columns. Update the file path in `strategy_test.py` to match your own data location.

Near the bottom of `strategy_test.py`, select the strategies and testing parameters:

```python
entry_strategy = Ultimate('mac')
exit_strategy = None

df2, trades_df, stats = run_backtest(
    df,
    entry_strategy,
    exit_strategy,
    account_size=20000,
    risk_percent=0.01,
    position_percent=1.00
)
```

Then run:

```bash
python strategy_test.py
```

The script prints the trade history and performance statistics and displays an equity curve based on closed trades.

## What I'm evaluating

The main things I care about are whether a strategy makes money, how much risk it takes to do so, and whether the results are consistent enough to justify further testing.

Right now, the engine directly reports returns, maximum drawdown, trade counts, and trade-level PnL. I use those results as a starting point for comparing entry rules, exit rules, and position sizing. A profitable backtest by itself does not establish that a strategy has an edge.

## Current limitations

This is still a work in progress. The backtester uses daily OHLCV candles, so it cannot reconstruct the exact intraday sequence of prices. The stop-first assumption helps handle one source of ambiguity, but it does not replace intraday data.

The current engine does not explicitly model commissions, slippage, borrowing costs, or realistic short-sale constraints. `risk_percent` is used by strategies that expose an `openloss` setting; it is not a universal account-risk cap. `position_percent` controls the notional size of an entry relative to cash, not a guaranteed maximum loss.

Some strategies are experimental and may need additional validation before they are suitable for comparison or live use. The MT5 script is also not yet connected directly to the backtesting workflow.

## Direction of the project

I want to continue building this into a more complete strategy research framework, with better risk controls, more realistic execution assumptions, and a more consistent way to compare strategies across different stocks and market environments.

The objective is not to find one backtest that looks good. It is to develop a process for testing ideas, identifying weaknesses, and understanding whether a strategy holds up beyond the data it was developed on.

*For research and educational use. Historical performance does not guarantee future results.*
