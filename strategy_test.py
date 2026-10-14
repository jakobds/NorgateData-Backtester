import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


from strategies import BB, BigTailBars, NoExit, QuickPullback
from strategies import DollarExit
from strategies import ATRExit



df=pd.read_csv("algo/stockdata/SPY.csv", parse_dates=['Date'], index_col=['Date'])

#create function that will execute backtest
def run_backtest(df, entry_strategy, exit_strategy, account_size=20000, risk_percent=0.01, position_percent=1.00):

    #copy df to not manipulate original data
    df = df.copy()

    #Check for indicators, if yes, add to DF
    if hasattr(entry_strategy, "prepare"):
        df = entry_strategy.prepare(df)
    if exit_strategy is not None and hasattr(exit_strategy, "prepare"):
        df=exit_strategy.prepare(df)

    #initialize variables that will hold important values
    cash = account_size
    position = 0
    entry_price = None
    entry_date = None
    shares = 0
    pending_signal = None
    pending_order = []
    trades = []
    last_trade_pnl=np.nan
    bars_since_exit=np.nan
    total_trades=0
    entry_bar_i= None
    max_open_pnl=np.nan

    df["Signal"] = np.nan
    df["Entry"] = 0
    df["Exit"] = 0
    df["Entry Price"] = np.nan
    df["Exit Price"] = np.nan
    df["Trade Direction"] = np.nan
    df["Open PnL"] = 0.0
    df["Position"] = 0
    df["Equity"] = float(account_size)
    df["Order Type"]=None
    df["Order Price"]=None
    df["Stop Filled"]=0
    df["Exit Signal"]=0
    df["Stop Price"] = np.nan
    df["Target Price"] = np.nan
    df["Exit Reason"] = None
    df["Last Trade PnL"]=np.nan
    df["Bars Since Exit"]=np.nan
    df['Total Trades']=0
    df["Bars Since Entry"]=np.nan
    df["Max Open PnL"]=np.nan
    df["Current Shares"]=0.0
    df["Total Equity"]=np.nan
    df["Open Loss Limit"]=np.nan

    #for every row: execute the logic below
    for i in range(1, len(df)):
        date = df.index[i]
        row = df.iloc[i]
        
        if len(pending_order) > 0 and position == 0:

            filled_order = None
            fill_price = None
            new_position = None

            for order in pending_order:
                order_type = order["type"]
                stop_price = order["price"]

                if order_type == "buy_stop":
                    if row["Open"] >= stop_price:
                        filled_order = order
                        fill_price = row["Open"]
                        new_position = 1
                        break
                    elif row["High"] >= stop_price:
                        filled_order = order
                        fill_price = stop_price
                        new_position = 1
                        break

                elif order_type == "sell_stop":
                    if row["Open"] <= stop_price:
                        filled_order = order
                        fill_price = row["Open"]
                        new_position = -1
                        break
                    elif row["Low"] <= stop_price:
                        filled_order = order
                        fill_price = stop_price
                        new_position = -1
                        break

            # Clear orders after checking today's bar
            pending_order = []

            if filled_order is not None:
                position = new_position
                entry_price = fill_price
                entry_date = date
                entry_bar_i = i
                max_open_pnl=0

                trade_amount = cash * position_percent
                shares = trade_amount / entry_price

                df.at[date, "Entry"] = 1
                df.at[date, "Entry Price"] = entry_price
                df.at[date, "Trade Direction"] = position
                df.at[date, "Order Type"] = filled_order["type"]
                df.at[date, "Order Price"] = filled_order["price"]
                df.at[date, "Stop Filled"] = 1
                df.at[date, "Bars Since Entry"] = 0

        #If there is a pending signal: Enter next bar at open
        if pending_signal is not None:

            #logic to avoid same strategy entries/exits
            target_position=pending_signal
            if target_position != position:

                # If already in a trade, exit it at today's open
                if position != 0:
                    exit_price = row["Open"]
                    pnl = shares * (exit_price - entry_price) * position
                    cash += pnl
                    last_trade_pnl = pnl
                    total_trades += 1
                    bars_since_exit = 0

                    df.at[date, "Exit"] = 1
                    df.at[date, "Exit Price"] = exit_price

                    #append the time/position/price/shares at time of entry to display later during analysis
                    bars_held = i - entry_bar_i if entry_bar_i is not None else np.nan
                    trade_max_open_pnl=max_open_pnl
                    trades.append({
                        "Entry Date": entry_date,
                        "Exit Date": date,
                        "Direction": position,
                        "Entry Price": entry_price,
                        "Exit Price": exit_price,
                        "Shares": shares,
                        "Position Size": shares*entry_price,
                        "PnL": pnl,
                        "Account Size": cash,
                        "Exit Reason": "Signal Exit",
                        "Bars Held": bars_held,
                        "max_open_pnl": trade_max_open_pnl
                    })
                    #reset position data
                    position = 0
                    entry_price = None
                    entry_date = None
                    shares = 0
                    entry_bar_i = None
                    max_open_pnl=np.nan
            # Enter new position at the same open / change dataframe vars to reflect so
            if target_position !=0:
                position = target_position
                entry_price = row["Open"]
                entry_date = date
                entry_bar_i = i
                trade_amount = cash * position_percent
                shares = trade_amount / entry_price
                max_open_pnl=0
            
                df.at[date, "Entry"] = 1
                df.at[date, "Entry Price"] = entry_price
                df.at[date, "Trade Direction"] = position
                pending_signal = None

        if position != 0 and entry_bar_i is not None:
            bars_since_entry = i - entry_bar_i
            df.at[date, "Bars Since Entry"] = bars_since_entry
        else:
            bars_since_entry = np.nan
            df.at[date, "Bars Since Entry"] = np.nan

        if position != 0 and exit_strategy is not None and hasattr(exit_strategy, "get_stop_target"):
            
            levels = exit_strategy.get_stop_target(
                df,
                i,
                position,
                entry_price,
                shares,
                cash
            )

            if levels is not None:
                stop_price = levels["stop"]
                target_price = levels["target"]

                df.at[date, "Stop Price"] = stop_price
                df.at[date, "Target Price"] = target_price

                stop_fill = None
                target_fill = None

                # Long trade
                if position == 1:
                    if row["Open"] <= stop_price:
                        stop_fill = row["Open"]
                    elif row["Low"] <= stop_price:
                        stop_fill = stop_price

                    if row["Open"] >= target_price:
                        target_fill = row["Open"]
                    elif row["High"] >= target_price:
                        target_fill = target_price

                # Short trade
                elif position == -1:
                    if row["Open"] >= stop_price:
                        stop_fill = row["Open"]
                    elif row["High"] >= stop_price:
                        stop_fill = stop_price

                    if row["Open"] <= target_price:
                        target_fill = row["Open"]
                    elif row["Low"] <= target_price:
                        target_fill = target_price

                exit_price = None
                exit_reason = None

                # Conservative daily-candle rule:
                # If both stop and target hit on same candle, assume stop hit first.
                if stop_fill is not None and target_fill is not None:
                    exit_price = stop_fill
                    exit_reason = "Stop and Target Hit - Stop First"

                elif stop_fill is not None:
                    exit_price = stop_fill
                    exit_reason = "Stop Loss"

                elif target_fill is not None:
                    exit_price = target_fill
                    exit_reason = "Profit Target"

                if exit_price is not None:
                    pnl = shares * (exit_price - entry_price) * position
                    cash += pnl
                    last_trade_pnl = pnl
                    total_trades += 1
                    bars_since_exit = 0

                    df.at[date, "Exit"] = 1
                    df.at[date, "Exit Price"] = exit_price
                    df.at[date, "Exit Reason"] = exit_reason

                    bars_held = i - entry_bar_i if entry_bar_i is not None else np.nan
                    trade_max_open_pnl=max_open_pnl
                    trades.append({
                        "Entry Date": entry_date,
                        "Exit Date": date,
                        "Direction": position,
                        "Entry Price": entry_price,
                        "Exit Price": exit_price,
                        "Shares": shares,
                        "Position Size": shares * entry_price,
                        "PnL": pnl,
                        "Account Size": cash,
                        "Exit Reason": exit_reason,
                        "Bars Held": bars_held,
                        "max_open_pnl": trade_max_open_pnl
                    })

                    position = 0
                    entry_price = None
                    entry_date = None
                    shares = 0
                    pending_signal = None
                    entry_bar_i = None
                    pending_order = []
                    max_open_pnl=np.nan

                    df.at[date, "Position"] = position
                    df.at[date, "Equity"] = cash
                    df.at[date, "Last Trade PnL"] = last_trade_pnl
                    df.at[date, "Bars Since Exit"] = bars_since_exit
                    df.at[date, "Total Trades"] = total_trades

                    if not pd.isna(bars_since_exit):
                        bars_since_exit += 1
    
                    continue


        # Open position profit at current close / changes pnl column
        if position != 0:
            open_pnl = shares * (row["Close"] - entry_price) * position
        else:
            open_pnl = 0
        df.at[date, "Open PnL"] = open_pnl
        df.at[date, "Current Shares"] = shares
        if position != 0:
            max_open_pnl = max(max_open_pnl, open_pnl)
            df.at[date, "Max Open PnL"] = max_open_pnl
        else:
            df.at[date, "Max Open PnL"] = np.nan


        # Strategy gives signal
        current_equity=cash+open_pnl

        #check for openloss variable in certian strategies        
        if hasattr(entry_strategy, "openloss"):
            entry_strategy.openloss = current_equity * risk_percent
            df.at[date, "Open Loss Limit"] = entry_strategy.openloss

        exit_triggered = False
        if (exit_strategy is not None and hasattr(exit_strategy, "get_exit") and position!=0):
            exit_signal=exit_strategy.get_exit(df, i, position, open_pnl)
            if exit_signal:
                pending_signal=0
                exit_triggered = True

        # Enter new signal next bar open
        if not exit_triggered:
            entry_signal = entry_strategy.get_signal(df, i, position, open_pnl)
            if entry_signal is not None:
                df.at[date, "Signal"]=entry_signal
                if entry_signal != position:
                    pending_signal=entry_signal

        if not exit_triggered and pending_signal is None and hasattr(entry_strategy, "get_order") and position == 0:
            orders = entry_strategy.get_order(df, i, position, open_pnl)

            if orders is not None and len(orders) > 0:
                pending_order = orders

                df.at[date, "Order Type"] = ", ".join([o["type"] for o in orders])
                df.at[date, "Order Price"] = ", ".join([str(o["price"]) for o in orders])

        # update equity based on trade
        if position != 0:
            equity = cash + shares * (row["Close"] - entry_price) * position
        else:
            equity = cash

        df.at[date, "Position"] = position
        df.at[date, "Equity"] = equity

        if not pd.isna(bars_since_exit):
            bars_since_exit += 1

    #get trades statistics
    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
            trades_df = pd.DataFrame(columns=[
                "Entry Date",
                "Exit Date",
                "Direction",
                "Entry Price",
                "Exit Price",
                "Shares",
                "Position Size",
                "PnL",
                "Account Size",
                "Exit Reason"
            ])
    elif "Exit Reason" not in trades_df.columns:
        trades_df["Exit Reason"] = "Signal Exit"

    df["Equity Peak"] = df["Equity"].cummax()
    df["Drawdown"] = df["Equity"] - df["Equity Peak"]
    df["Drawdown %"] = (df["Drawdown"] / df["Equity Peak"])*100

    #handle current trade in output stats
    if position != 0:
        current_price = df["Close"].iloc[-1]
        current_date = df.index[-1]

        unrealized_pnl = shares * (current_price - entry_price) * position
        current_equity = cash + unrealized_pnl
        total_equity = current_equity-account_size

        current_trade = {
            "Status": "OPEN",
            "Entry Date": entry_date,
            "Current Date": current_date,
            "Direction": position,
            "Entry Price": entry_price,
            "Current Price": current_price,
            "Shares": shares,
            "Position Size": shares * entry_price,
            "Unrealized PnL": unrealized_pnl,
            "Cash": cash,
            "Current Equity": current_equity,
            "Total Equity": total_equity,
            "max_open_pnl": max_open_pnl    
        }
    else:
        current_trade = None

    equity_gain_pct = ((df["Equity"].iloc[-1] / account_size) - 1) * 100
    cash_gain_pct = ((cash / account_size) - 1) * 100
    long_entries=((df["Entry"]==1)&(df["Trade Direction"]==1)).sum()
    short_entries = ((df["Entry"] == 1) & (df["Trade Direction"] == -1)).sum()
    long_closed_trades = (trades_df["Direction"] == 1).sum()
    short_closed_trades = (trades_df["Direction"] == -1).sum()
    #output statistics for trading strategy
    stats = {
    "Final Cash": cash,
    "Final Equity": df["Equity"].iloc[-1],
    "Cash Gain %": cash_gain_pct, 
    "Equity Gain %": equity_gain_pct,
    "Max Drawdown": df["Drawdown"].min(),
    "Max Drawdown %": df["Drawdown %"].min(),
    "Long Entries": int(long_entries),
    "Short Entries": int(short_entries),
    "Closed Long Trades": int(long_closed_trades),
    "Closed Short Trades": int(short_closed_trades),
    "Current Trade": current_trade
}

    return df, trades_df, stats




from strategies import SimpleStrategy
from strategies import GoWithTheFlow
from strategies import LoveFriday
from strategies import Books
from strategies import BreakoutTiwst
from strategies import TRBreakout
from strategies import PercentRank
from strategies import DayofWeek
from strategies import DayofWeekMomentum
from strategies import NotDayOfWeek
from strategies import RsiTrigger
from strategies import MaCrossTwist
from strategies import SplitWeek
from strategies import SerialCorrelation
from strategies import BackInStyle
from strategies import WhereYouAt
from strategies import AsymetricTriple
from strategies import AsymetricTwo
from strategies import StochasticCross
from strategies import Flow
from strategies import BB
from strategies import KeltnerChannel
from strategies import ThreeAmigos
from strategies import TwoAmigos
from strategies import PitterPatter
from strategies import PitterPatterTwo
from strategies import ClosingOnly
from strategies import QuickPullback
from strategies import CloseOnly2
from strategies import BreakdownAhead
from strategies import ComChIn
from strategies import HIGHAF
from strategies import AwsOsc
from strategies import SeasonLong
from strategies import FilterEntry
from strategies import TimeExit
from strategies import DateExit
from strategies import PercentileExit
from strategies import GetOut
from strategies import AtrAverage
from strategies import Protector
from strategies import WhereYouLike
from strategies import Tiered
from strategies import Ultimate
from strategies import DayTwist

#choose strategy
entry_strategy = Ultimate('mac')
exit_strategy = None

#run backtest and initialize parameters
df2, trades_df, stats = run_backtest(
    df,
    entry_strategy,
    exit_strategy,
    account_size=20000,
    risk_percent = 0.01,
    position_percent = 1.00
)

print(trades_df)

print("Final Cash:", stats["Final Cash"])
print("Final Equity:", stats["Final Equity"])
print("Cash Gain %:", f"{stats['Cash Gain %']:.2f}%")
print("Equity Gain %:", f"{stats['Equity Gain %']:.2f}%")
print("Max Drawdown:", stats["Max Drawdown"])
print("Max Drawdown %:", stats["Max Drawdown %"])

print()

if stats["Current Trade"] is not None:
    print("Current Open Trade:")
    print(pd.Series(stats["Current Trade"]))
else:
    print("No current open trade.")

print()

print("Entries:", df2["Entry"].sum())
print("Exits:", df2["Exit"].sum())
print("Shorts:", stats["Closed Short Trades"])
print("Longs:", stats["Closed Long Trades"])
print("Stop Losses:", (trades_df["Exit Reason"] == "Stop Loss").sum())
print("Profit Targets:", (trades_df["Exit Reason"] == "Profit Target").sum())
print("Signal Exits:", (trades_df["Exit Reason"]=="Signal Exit").sum())
print("Open Position:", df2["Position"].iloc[-1])
print("Last Open PnL:", df2["Open PnL"].iloc[-1])

account_size = 20000

trade_curve = trades_df.copy().reset_index(drop=True)
trade_curve["Trade #"] = trade_curve.index + 1
trade_curve["Equity %"] = ((trade_curve["Account Size"] / account_size) - 1) * 100

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(trade_curve["Trade #"], trade_curve["Equity %"], marker="o")
ax.axhline(0, linestyle="--")

ax.set_title("Equity Curve by Trade")
ax.set_xlabel("Trade Number")
ax.set_ylabel("Gain / Loss %")
ax.yaxis.set_major_formatter(mtick.PercentFormatter())

step = max(1, len(trade_curve) // 10)

tick_positions = trade_curve["Trade #"].iloc[::step]
date_labels = [
    date.strftime("%Y")
    for date in trade_curve["Exit Date"].iloc[::step]
]

ax.set_xticks(tick_positions)

# Second x-axis for years
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(tick_positions)
ax2.set_xticklabels(date_labels)
ax2.set_xlabel("Exit Year")

plt.tight_layout()
plt.show()