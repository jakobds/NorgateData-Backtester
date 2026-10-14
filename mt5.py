import MetaTrader5 as mt5
import pandas as pd

from strategies import MaCrossTwist
from strategies import DollarExit

import MetaTrader5 as mt5

if not mt5.initialize():
    raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

def search_symbols(pattern):
    symbols = mt5.symbols_get(pattern)

    print(f"\nSearching: {pattern}")

    if symbols is None:
        print("symbols_get failed:", mt5.last_error())
        return

    if len(symbols) == 0:
        print("No matches found.")
        return

    for s in symbols[:50]:
        print(f"{s.name} | {s.description} | visible={s.visible}")

search_symbols("*SPY*")
search_symbols("*SPX*")
search_symbols("*US500*")
search_symbols("*S&P*")
search_symbols("*ETF*")

mt5.shutdown()
def connect_mt5():


    
    """
    Connect Python to the open MetaTrader 5 terminal.
    Make sure MT5 is open and logged in first.
    """
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    account = mt5.account_info()
    if account is None:
        raise RuntimeError(f"MT5 connected, but no account found: {mt5.last_error()}")

    print("Connected to MT5")
    print("Account:", account.login)
    print("Server:", account.server)


def get_mt5_data(symbol, timeframe=mt5.TIMEFRAME_D1, bars=300):
    """
    Pulls closed candle data from MT5 and converts it to your backtester format.
    start_pos=1 skips the currently forming candle.
    """
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select symbol {symbol}: {mt5.last_error()}")

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, bars)

    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Could not get rates for {symbol}: {mt5.last_error()}")

    df = pd.DataFrame(rates)
    df["Date"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("Date")

    df = df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "tick_volume": "Volume"
    })

    return df[["Open", "High", "Low", "Close", "Volume"]]


try:
    connect_mt5()

    entry_strategy = MaCrossTwist("mact")
    exit_strategy = DollarExit("dollarexit", stop_dollars=200, target_dollars=400)

    df = get_mt5_data("SPY_CFD.ETF", mt5.TIMEFRAME_D1, 300)
    df = entry_strategy.prepare(df)

    print(df.tail())


finally:
    mt5.shutdown()