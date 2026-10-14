from indicators import Moving_Average
from indicators import ADX
from indicators import ATR
from indicators import RSI
from indicators import Exponential_Moving_Average
from indicators import Triangular_Moving_Average
from indicators import Stochastic
from indicators import MoneyFlow
from indicators import BollingerBands
from indicators import Keltner
from indicators import CCI
from indicators import TR
from indicators import AwesomeOscillator
from indicators import UltimateOscillator
import numpy as np
import pandas as pd
from datetime import date

#200 day MA, reversal entry/exit simple
class SimpleStrategy:
    def __init__(self, name="Simply"):
        self.name=name
    def prepare(self, df):
        df['MA']=Moving_Average(df["Close"], 200)
        return df
    def get_signal(self, df, i, position, open_pnl):
        close=df["Close"].iloc[i]
        ma=df["MA"].iloc[i]

        if pd.isna(ma):
            return None
        if close > ma:
            return 1
        if close < ma:
            return -1
        return None

# 1 day lookback, reversal entry
class GoWithTheFlow:
    def __init__(self, name="GoWithTheFlow", openloss=200):
        self.name = name
        self.openloss = openloss

    def get_signal(self, df, i, position, open_pnl):
        close = df["Close"].iloc[i]
        prev_close = df["Close"].iloc[i - 1]

        can_trade = position == 0 or open_pnl < -self.openloss

        if close < prev_close and can_trade:
            return -1
        if close > prev_close and can_trade:
            return 1
        return None
    
#trade on fridays monthly h/l
class LoveFriday:
    def __init__(self, name="LoveFriday"):
        self.name=name
    def prepare(self, df):
        df["Lookback High"] = df["Close"].rolling(window=25).max().shift(1)
        df["Lookback Low"] = df["Close"].rolling(window=25).min().shift(1)
        df["Day"] = df.index.isocalendar().day.astype(int)
        return df
    
    def get_signal(self, df, i, position, open_pnl):
        close=df["Close"].iloc[i]
        high=df["Lookback High"].iloc[i]
        low=df["Lookback Low"].iloc[i]
        day = df['Day'].iloc[i]

        can_trade = day==5

        if pd.isna(high) or pd.isna(low):
            return None
        if close>high and can_trade:
            return 1
        if close<low and can_trade:
            return -1
        return None
    
class Books:
    def __init__(self, name="Books"):
        self.name=name
    def prepare(self, df):
        df["MA5"]=Moving_Average(df["Close"], 5)
        df["MA10"]=Moving_Average(df["Close"], 10)
        return df
    def get_signal(self, df, i, position, openpnl):
        close=df["Close"].iloc[i]
        ma5=df["MA5"].iloc[i]
        ma10=df["MA10"].iloc[i]

        if pd.isna(ma5) or pd.isna(ma10):
            return None
        if ma5<ma10 and close<ma5:
            return 1
        if ma5>ma10 and close>5:
          return -1
        return None  
    
class BreakoutTiwst:
    def __init__(self, name="BreakoutTwish"):
        self.name=name
    def prepare(self, df):
        df["ADX"]=ADX(df["Close"], 15, df["High"], df["Low"])
        df["Buy Stop Price"]=df["High"].rolling(window=15).max().shift(1)
        df["Sell Stop Price"]=df["Low"].rolling(window=15).min().shift(1)
        return df
    
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return []
        adx=df["ADX"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]
        if pd.isna(adx) or pd.isna(buy_stop) or pd.isna(sell_stop):
            return []
        if adx < 20:
            return [{"type": "buy_stop", "price": buy_stop},{"type": "sell_stop", "price": sell_stop}]
        return []
    
class TRBreakout:
    def __init__(self, name="TRBreakout"):
        self.name=name
    def prepare(self, df):
        df["ATR"]=ATR(df["Close"], df["High"], df["Low"], 15)
        df["Buy Stop Price"]=df["Close"]+df["ATR"]
        df["Sell Stop Price"]=df["Close"]-df["ATR"]
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, open_pnl):
        if position != 0:
            return []

        buy_stop = df["Buy Stop Price"].iloc[i]
        sell_stop = df["Sell Stop Price"].iloc[i]

        if pd.isna(buy_stop) or pd.isna(sell_stop):
            return []

        return [
            {"type": "buy_stop", "price": buy_stop},
            {"type": "sell_stop", "price": sell_stop}
        ]

class PercentRank:
    def __init__(self, name="PercentRanker"):
        self.name=name
    def prepare(self, df):
        df["25"]=df["Close"].rolling(window=25).quantile(0.25).shift(1)
        df["75"]=df["Close"].rolling(window=25).quantile(0.75).shift(1)
        df["ADX"]=ADX(df["Close"], 14, df["High"], df["Low"])
        return df
    def get_signal(self, df, i, position, openpnl):
        adx=df["ADX"].iloc[i]
        p25=df["25"].iloc[i]
        p75=df["75"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(adx) or pd.isna(p25) or pd.isna(p75) or pd.isna(close):
            return None
        if adx>20 and adx < 30 and close<p25:
            return -1 
        if adx>20 and adx<30 and close>p75:
            return 1
        
class DayofWeek:
    def __init__(self, name="dayofweek"):
        self.name=name
    def prepare(self, df):
        df["Day"] = df.index.isocalendar().day.astype(int)
        df["Next Day"] = df["Day"].shift(-1)
        df["Buy Stop Price"]=df["High"]
        df["Sell Stop Price"]=df["Low"]
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return []
        if i>=len(df)-1:
            return []
        next_day=df["Next Day"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]

        if pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(next_day):
            return []
        if next_day==3:
            return[{
                "type":"buy_stop",
                "price":buy_stop
            }]
        if next_day==4:
            return[{
                "type":"sell_stop",
                "price": sell_stop
            }]
        return []
    
class DayofWeekMomentum:
    def __init__(self, name="dayofweek"):
        self.name=name
    def prepare(self, df):
        df["Day"] = df.index.isocalendar().day.astype(int)
        df["Next Day"] = df["Day"].shift(-1)
        df["Buy Stop Price"]=df["High"]
        df["Sell Stop Price"]=df["Low"]
        df["Lookback"]=df["Close"].shift(10)
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return []
        if i>=len(df)-1:
            return []
        next_day=df["Next Day"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]
        lookback_close=df["Lookback"].iloc[i]
        close=df["Close"].iloc[i]

        if pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(next_day):
            return []
        if next_day==3 and close>lookback_close:
            return[{
                "type":"buy_stop",
                "price":buy_stop
            }]
        if next_day==4 and close<lookback_close:
            return[{
                "type":"sell_stop",
                "price": sell_stop
            }]
        return []

class NotDayOfWeek:
    def __init__(self, name="dayofweek"):
        self.name=name
    def prepare(self, df):
        df["Day"] = df.index.isocalendar().day.astype(int)
        df["Next Day"] = df["Day"].shift(-1)
        df["Buy Stop Price"]=df["High"]
        df["Sell Stop Price"]=df["Low"]
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return []
        if i>=len(df)-1:
            return []
        next_day=df["Next Day"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]

        if pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(next_day):
            return []
        if next_day != 3:
            return[{
                "type":"buy_stop",
                "price":buy_stop
            }]
        if next_day != 4:
            return[{
                "type":"sell_stop",
                "price": sell_stop
            }]
        return []
    
class RsiTrigger:
    def __init__(self, name="rsitrigger"):
        self.name=name
    def prepare(self, df):
        df["RSI"]=RSI(df["Close"], 5)
        df["Moving Average"]=Moving_Average(df["Close"], 5)
        return df
    def get_signal(self, df, i, position, openpnl):
        ma=df["Moving Average"].iloc[i]
        rsi=df["RSI"].iloc[i]
        close=df['Close'].iloc[i]
        if pd.isna(ma) or pd.isna(rsi) or pd.isna(close):
            return None
        if position !=0:
            return None
        if rsi<80 and close>ma:
            return 1
        if rsi>20 and close<ma:
            return -1
        return None
    
class MaCrossTwist:
    def __init__(self, name="macrosstwist"):
        self.name=name
    def prepare(self, df):
        df["MA5"]=Moving_Average(df["Close"], 5)
        df["MA10"]=Moving_Average(df["Close"], 10)
        df["YesterdayHigh"]=df["High"].shift(1)
        df["YesterdayLow"]=df["Low"].shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        ma5=df["MA5"].iloc[i]
        ma10=df["MA10"].iloc[i]
        yh=df["YesterdayHigh"].iloc[i]
        yl=df["YesterdayLow"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(yl) or pd.isna(yh) or pd.isna(ma10) or pd.isna(ma5):
            return None
        if position != 0:
            return None
        if ma5>ma10 and close<yl+3:
            return 1
        if ma5<ma10 and close>yh-3:
            return -1
        return None

class SplitWeek:
    def __init__(self, name="SplitWeek"):
        self.name=name
    def prepare(self, df):
        df["Lookback High"]=df["High"].rolling(window=15).max().shift(1)
        df["Lookback Low"]=df["Low"].rolling(window=15).min().shift(1)
        df["Lookback High Close"]=df["Close"].rolling(window=15).max().shift(1)
        df["Lookback Low Close"]=df["Close"].rolling(window=15).min().shift(1)
        df["Day"] = df.index.isocalendar().day.astype(int)
        df["ATR"]=ATR(df["Close"], df["High"], df["Low"], 14)
        return df
    def get_signal(self, df, i, position, openpnl):
        lbh=df["Lookback High"].iloc[i]
        lbl=df["Lookback Low"].iloc[i]
        lbhc=df["Lookback High Close"].iloc[i]
        lblc=df["Lookback Low Close"].iloc[i]
        day=df["Day"].iloc[i]
        atr=df["ATR"].iloc[i]
        close=df["Close"].iloc[i]
        high=df["High"].iloc[i]
        low=df["Low"].iloc[i]

        can_trade= day==2 or day==3 or day==4
        if pd.isna(atr) or pd.isna(day) or pd.isna(lbl) or pd.isna(lbh) or pd.isna (lbhc) or pd.isna(lblc) or pd.isna(close) or pd.isna(high) or pd.isna(low) :
            return None
        if position !=0:
            return None
        if can_trade and high>lbh and close>lbhc and atr<8:
            return 1
        if can_trade and low<lbl and close<lblc and atr<8:
            return -1
        return None
    
class SerialCorrelation:
    def __init__(self, name='serialcorrelation'):
        self.name=name
    def prepare(self, df):
        df["Lowest Close"]=df["Close"].rolling(window=15).min()
        df["Highest Close"]=df["Close"].rolling(window=15).max()
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        close=df["Close"].iloc[i]
        lowest_close=df["Lowest Close"].iloc[i]
        highest_close=df["Highest Close"].iloc[i]
        last_trade_pnl=df["Last Trade PnL"].iloc[i]
        bars_since_exit=df["Bars Since Exit"].iloc[i]
        total_trades=df["Total Trades"].iloc[i]
        if pd.isna(close) or pd.isna(lowest_close) or pd.isna(highest_close):
            return None
        first_trade = total_trades == 0
        after_winner =(total_trades>0 and last_trade_pnl>0 and bars_since_exit>=5)
        after_loser=(total_trades>0 and last_trade_pnl<=0 and bars_since_exit>=20)
        can_trade=first_trade or after_loser or after_winner
        if not can_trade:
            return None
        if close <= lowest_close:
            return 1
        if close >= highest_close:
            return -1
        return None
    
class BackInStyle:
    def __init__(self, name="BackInStyle"):
        self.name=name
    def prepare(self, df):
        df["3 Low"]=df["Low"].shift(3)
        df["2 Low"]=df["Low"].shift(2)
        df["1 Low"]=df["Low"].shift(1)
        df["3 High"]=df["High"].shift(3)
        df["2 High"]=df["High"].shift(2)
        df["1 High"]=df["High"].shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position!=0:
            return None
        low3=df["3 Low"].iloc[i]
        low2=df["2 Low"].iloc[i]
        low1=df["1 Low"].iloc[i]
        high3=df["3 High"].iloc[i]
        high2=df["2 High"].iloc[i]
        high1=df["1 High"].iloc[i]
        high=df["High"].iloc[i]
        low=df["Low"].iloc[i]
        if pd.isna(low1) or pd.isna(low2) or pd.isna(low3) or pd.isna(high1) or pd.isna(high2) or pd.isna(high3):
            return None
        if low3>high and high>low1 and low>low2 and low1>low2:
            return -1
        if high3<low and low<high1 and high<high2 and high1<high2:
            return 1
        return None
    
class WhereYouAt:
    def __init__(self, name="WhereYouAt"):
        self.name=name
    def prepare(self, df):
        df["EMA10"]=Exponential_Moving_Average(df["Close"], 10)
        df["EMA40"]=Exponential_Moving_Average(df["Close"], 40)
        df["Buy Stop Price"]=df["High"]
        df["Sell Stop Price"]=df["Low"]
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        ema10=df["EMA10"].iloc[i]
        ema40=df["EMA40"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]

        if pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(ema10) or pd.isna(ema40):
            return []
        if ema10>ema40:
            return[{
                "type":"buy_stop",
                "price":buy_stop
            }]
        if ema10<ema40:
            return[{
                "type":"sell_stop",
                "price": sell_stop
            }]
        return []

class AsymetricTriple:
    def __init__(self, name="AsymetricTriple", atrmult=1.5):
        self.name=name
        self.atrmult=atrmult
    def prepare(self, df):
        df["ATR"]=ATR(df["Close"], df["High"], df["Low"], 14)
        df["Buy Stop Price"]=df["Close"]+self.atrmult*df["ATR"]
        df["Sell Stop Price"]=df["Low"]-self.atrmult*df["ATR"]
        df["TriAvgLow"]=Triangular_Moving_Average(df["Low"], 10)
        df["Low 12"]=df["Low"].shift(12)
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return[]
        atr=df["ATR"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]
        triavglow=df["TriAvgLow"].iloc[i]
        low12=df["Low 12"].iloc[i]
        if pd.isna(atr) or pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(triavglow) or pd.isna(low12):
            return []
        if triavglow>=low12:
            return[{"type":"buy_stop","price":buy_stop},{"type":"sell_stop","price": sell_stop}]
        return [{"type": "sell_stop", "price": sell_stop}]

class AsymetricTwo: #requires intraday entry which i do not have yet
    def __init__(self, name="AsymetricTwo", atrmult=1.5):
        self.name=name
        self.atrmult=atrmult
    def prepare(self, df):
        df["ATR"]=ATR(df["Close"], df["High"], df["Low"], 14)
        df["Buy Stop Price"]=df["Open"]+self.atrmult*df["ATR"]
        df["Sell Stop Price"]=df["Low"]-self.atrmult*df["ATR"]
        df["Yesterday Close"]=df["Close"].shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return[]
        atr=df["ATR"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]
        open=df["Open"].iloc[i]
        yesterday_close=df["Yesterday Close"].iloc[i]
        if pd.isna(atr) or pd.isna(buy_stop) or pd.isna(sell_stop) or pd.isna(open) or pd.isna(yesterday_close):
            return []
        if open>=yesterday_close:
            return[{"type":"buy_stop","price":buy_stop}, {"type":"sell_stop","price": sell_stop}]   
        return [{"type": "sell_stop", "price": sell_stop}]
    
class StochasticCross:
    def __init__(self, name="StochasticCross"):
        self.name=name
    def prepare(self, df):
        stoch_k, stoch_d=Stochastic(df["High"], df["Low"], df["Close"], k_period=8, d_period=22, k_smooth=23)
        df["Stochastic_K"]=stoch_k
        df["Stochastic_D"]=stoch_d
        return df
    def get_signal(self, df, i, position, openpnl):
        if position!=0:
            return None
        sK=df["Stochastic_K"].iloc[i]
        sD=df["Stochastic_D"].iloc[i]
        if pd.isna(sK) or pd.isna(sD):
            return None
        if sK > sD:
            return 1
        if sK < sD:
            return -1
        return None
    
class Flow:
    def __init__(self, name="Flow"):
        self.name=name
    def prepare(self, df):
        df["Money Flow"]=MoneyFlow(df["High"], df["Low"], df["Close"], df["Volume"], 14)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position!=0:
            return None
        money_flow=df["Money Flow"].iloc[i]
        previous_money_flow=df["Money Flow"].iloc[i-1]
        if pd.isna(money_flow) or pd.isna(previous_money_flow):
            return None
        if money_flow > 20 and previous_money_flow <= 20:
            return 1
        if money_flow < 80 and previous_money_flow >= 80:
            return -1
        return None
    
class BB:
    def __init__(self, name="BB", period=20, std=2):
        self.name=name
        self.period=period
        self.std=std
    def prepare(self, df):
        upper, middle, lower = BollingerBands(df["Close"], self.period, self.std)
        df["BB_Upper"] = upper
        df["BB_Middle"] = middle
        df["BB_Lower"] = lower
        df["10 Close"]=df["Close"].shift(10)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        bb_upper=df["BB_Upper"].iloc[i]
        prev_bb_upper=df["BB_Upper"].iloc[i-1]
        bb_middle=df["BB_Middle"].iloc[i]
        bb_lower=df["BB_Lower"].iloc[i]
        prev_bb_lower=df["BB_Lower"].iloc[i-1]
        close10=df["10 Close"].iloc[i]
        close=df["Close"].iloc[i]
        prev_close=df["Close"].iloc[i-1]
        if pd.isna(bb_upper) or pd.isna(bb_middle) or pd.isna(bb_lower) or pd.isna(close10) or pd.isna(prev_close) or pd.isna(prev_bb_upper) or pd.isna(prev_bb_lower):
            return None
        low_cross=prev_close<=prev_bb_lower and close > bb_lower
        up_cross=prev_close>=prev_bb_upper and close < bb_upper
        if low_cross and close > close10:
            return 1
        if up_cross and close < close10:
            return -1
        return None
    
class KeltnerChannel:
    def __init__(self, name="KeltnerChannel"):
        self.name=name
    def prepare(self, df):
        upper, middle, lower = Keltner(df["Close"], 20, df["High"], df["Low"], 20, 2)
        df["Keltner_Upper"] = upper
        df["Keltner_Middle"] = middle
        df["Keltner_Lower"] = lower
        df["10 Close"]=df["Close"].shift(10)
        return df
    def get_signal(self, df, i, position, openpnl):
        keltner_upper=df["Keltner_Upper"].iloc[i]
        prev_keltner_upper=df["Keltner_Upper"].iloc[i-1]
        keltner_middle=df["Keltner_Middle"].iloc[i]
        keltner_lower=df["Keltner_Lower"].iloc[i]
        prev_keltner_lower=df["Keltner_Lower"].iloc[i-1]
        close=df["Close"].iloc[i]
        prev_close=df["Close"].iloc[i-1]
        close10=df["10 Close"].iloc[i]
        if pd.isna(keltner_upper) or pd.isna(keltner_middle) or pd.isna(keltner_lower) or pd.isna(prev_keltner_upper) or pd.isna(prev_keltner_lower) or pd.isna(close10) or pd.isna(prev_close):
            return None
        lower_cross=prev_close<=prev_keltner_lower and close > keltner_lower
        upper_cross=prev_close>=prev_keltner_upper and close < keltner_upper
        if lower_cross and close>close10:
            return 1
        if upper_cross and close<close10:
            return -1
        return None

class ThreeAmigos:
    def __init__(self, name="ThreeAmigos"):
        self.name=name
    def prepare(self, df):
        df["ADX"] = ADX(df["Close"], 14, df["High"], df["Low"])
        df["RSI"] = RSI(df["Close"], 14)
        df["Long Lookback"] = df["Close"].shift(20)
        df["Short Lookback"] = df["Close"].shift(10)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position!=0:
            return None
        adx=df["ADX"].iloc[i]
        rsi=df["RSI"].iloc[i]
        long_lookback=df["Long Lookback"].iloc[i]
        short_lookback=df["Short Lookback"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(adx) or pd.isna(rsi) or pd.isna(long_lookback) or pd.isna(short_lookback):
            return None
        can_trade=adx>25
        if can_trade and rsi<50 and close<long_lookback and close>short_lookback:
            return 1
        if can_trade and rsi>50 and close>long_lookback and close<short_lookback:
            return -1
        return None
    
class TwoAmigos:
    def __init__(self, name="TwoAmigos"):
        self.name=name
    def prepare(self, df):
        df["ADX"]=ADX(df["Close"], 14, df["High"], df["Low"])
        df["Lookback Close"]=df["Close"].shift(20)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        adx=df["ADX"].iloc[i]
        lookback_close=df["Lookback Close"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(adx) or pd.isna(lookback_close) or pd.isna(close):
            return None
        can_trade=adx>20
        if can_trade and close>lookback_close:
            return 1
        if can_trade and close<lookback_close:
            return -1
        return None
    
class PitterPatter:
    def __init__ (self, name="PitterPatter"):
        self.name=name
    def prepare(self, df):
        df["Previous Open"]=df["Open"].shift(1)
        df["Previous Close"]=df["Close"].shift(1)
        df["Previous Low"]=df["Low"].shift(1)
        df["Previous High"]=df["High"].shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        prev_open=df["Previous Open"].iloc[i]
        prev_close=df["Previous Close"].iloc[i] 
        prev_low=df["Previous Low"].iloc[i]
        prev_high=df["Previous High"].iloc[i]
        close=df["Close"].iloc[i]
        high=df["High"].iloc[i]
        open=df["Open"].iloc[i]
        low=df["Low"].iloc[i]
        if pd.isna(prev_open) or pd.isna(prev_close) or pd.isna(prev_low) or pd.isna(close) or pd.isna(high) or pd.isna(open):
            return None
        if prev_open>high and open>prev_close and prev_close>prev_low and prev_low>close:
            return 1
        if prev_open<low and open<prev_close and prev_close<prev_high and prev_high<close:
            return -1
        return None
    
class PitterPatterTwo:
    def __init__ (self, name="pitpat2"):
        self.name=name
    def prepare(self, df):
        df["Low 3"]=df["Low"].shift(3)
        df["Low 1"]=df["Low"].shift(1)
        df["Low 2"]=df["Low"].shift(2)
        df["Close 1"]=df["Close"].shift(1)
        df["High 3"]=df["High"].shift(3)
        df["High 1"]=df["High"].shift(1)
        df["High 2"]=df["High"].shift(2)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        low3=df["Low 3"].iloc[i]
        low2=df["Low 2"].iloc[i]
        low1=df["Low 1"].iloc[i]
        close1=df["Close 1"].iloc[i]
        high3=df["High 3"].iloc[i]
        high2=df["High 2"].iloc[i]
        high1=df["High 1"].iloc[i]
        low=df["Low"].iloc[i]
        close=df["Close"].iloc[i]
        high=df["High"].iloc[i]
        if pd.isna(low3) or pd.isna(low2) or pd.isna(low1) or pd.isna(close1) or pd.isna(high3) or pd.isna(high2) or pd.isna(high1) or pd.isna(low) or pd.isna(close) or pd.isna(high):
            return None
        if low3>high and high>low1 and low1>low2 and close>close1:
            return 1
        if high3<low and low<high1 and high1<high2 and close<close1:
            return -1
        return None
    
class ClosingOnly:
    def __init__(self, name="CloseOnly"):
        self.name=name
    def prepare(self, df):
        df["Close 1"]=df["Close"].shift(1)
        df["Close 2"]=df["Close"].shift(2)
        df["Close 3"]=df["Close"].shift(3)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        close=df["Close"].iloc[i]
        close1=df["Close 1"].iloc[i]
        close2=df["Close 2"].iloc[i]
        close3=df["Close 3"].iloc[i]
        if pd.isna(close) or pd.isna(close1) or pd.isna(close2) or pd.isna(close3):
            return None
        if close1>close3 and close>close2 and close2>close1:
            return 1
        if close1<close3 and close<close2 and close2<close1:
            return -1
        return None
    
class QuickPullback:
    def __init__ (self, name="QuickPullback"):
        self.name=name
    def prepare(self, df):
        df["High 1"]=df["High"].shift(1)
        df["High 2"]=df["High"].shift(2)
        df["Low 1"]=df["Low"].shift(1)
        df["Low 2"]=df["Low"].shift(2)
        return df
    def get_signal(self, df, i, position, openpnl):
        high1=df["High 1"].iloc[i]
        high2=df["High 2"].iloc[i]
        low1=df["Low 1"].iloc[i]
        low2=df["Low 2"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(high1) or pd.isna(high2) or pd.isna(low1) or pd.isna(low2) or pd.isna(close):
            return None
        if position !=0:
            return None
        if high2>high1 and low2<low1 and close>high2:
            return 1
        if low2<low1 and high2>high1 and close<low2:
            return -1
        return None
    
class CloseOnly2:
    def __init__(self, name="Closeonly2"):
        self.name=name
    def prepare(self, df):
        df["Close 1"]=df["Close"].shift(1)
        df["Close 2"]=df["Close"].shift(2)
        df["Close 3"]=df["Close"].shift(3)
        df["Close 4"]=df["Close"].shift(4)
        df["Close 5"]=df["Close"].shift(5)
        return df
    def get_signal(self, df, i, position, openpnl):
        close1=df["Close 1"].iloc[i]
        close2=df["Close 2"].iloc[i]
        close3=df["Close 3"].iloc[i]
        close4=df["Close 4"].iloc[i]
        close5=df["Close 5"].iloc[i]
        close=df["Close"].iloc[i]
        if position !=0:
            return None
        if pd.isna(close) or pd.isna(close1) or pd.isna(close2) or pd.isna(close3) or pd.isna(close4) or pd.isna(close5):
            return None
        if close1<close2 and close2<close5 and close5<close3 and close3<close4:
            return 1
        if close1>close2 and close2>close5 and close5>close3 and close3>close4:
            return -1
        return None


class BreakdownAhead:
    def __init__ (self, name="BreakdownAhead"):
        self.name=name
    def prepare(self, df):
        df["10 Close"]=df["Close"].shift(10)
        df["TR"]=TR(df["High"], df["Low"], df["Close"])
        df["AVG TR"]=df[["TR"]].rolling(3).mean()
        df["Buy Stop Price"]=df["Close"]+2*df["AVG TR"]
        df["Sell Stop Price"]=df["Close"]-2*df["AVG TR"]
        return df
    def get_signal(self, df, i, position, openpnl):
        return None
    def get_order(self, df, i, position, openpnl):
        if position!=0:
            return []
        avg_tr=df["AVG TR"].iloc[i]
        close=df["Close"].iloc[i]
        close10=df["10 Close"].iloc[i]
        buy_stop=df["Buy Stop Price"].iloc[i]
        sell_stop=df["Sell Stop Price"].iloc[i]
        if pd.isna(avg_tr) or pd.isna(close) or pd.isna(close10):
            return []
        if close<close10:
            return [{"type":"buy_stop", "price": buy_stop}]
        if close>close10:
            return [{"type":"sell_stop", "price":sell_stop}]
        return []
    
class ComChIn:
    def __init__ (self, name="comchin"):
        self.name=name
    def prepare(self, df):
        df["CCI"], df["CCIMA"]=CCI(df["High"], df["Low"], df["Close"], 14, 9)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        cci=df["CCI"].iloc[i]
        ccima=df["CCIMA"].iloc[i]
        if pd.isna(cci) or pd.isna(ccima):
            return None
        if ccima>100:
            return -1
        if ccima<-100:
            return 1
        return None

class BigTailBars:
    def __init__(self, name="BigTailBars", period=10, thresh=5):
        self.name = name
        self.period = period
        self.thresh = thresh

    def prepare(self, df):
        body_up = df["Close"] - df["Open"]
        body_down = df["Open"] - df["Close"]
        lower_tail = df["Open"] - df["Low"]
        upper_tail = df["High"] - df["Open"]
        df["Bull Tail Bar"] = (
            (df["Close"] > df["Open"]) &
            (lower_tail > body_up) &
            (df["High"] > df["High"].shift(1))
        )
        df["Bear Tail Bar"] = (
            (df["Close"] < df["Open"]) &
            (upper_tail > body_down) &
            (df["Low"] < df["Low"].shift(1))
        )
        # TradeStation CountIF(condition, Period)
        df["BullBarTail"] = df["Bull Tail Bar"].astype(int).rolling(self.period).sum()
        df["BearBarTail"] = df["Bear Tail Bar"].astype(int).rolling(self.period).sum()
        return df
    def get_signal(self, df, i, position, openpnl):
        bull_count = df["BullBarTail"].iloc[i]
        bear_count = df["BearBarTail"].iloc[i]
        if pd.isna(bull_count) or pd.isna(bear_count):
            return None
        if bull_count > bear_count and bull_count > self.thresh:
            return 1
        if bull_count < bear_count and bear_count > self.thresh:
            return -1
        return None

class HIGHAF:
    def __init__(self, name="HiAF"):
        self.name=name
    def prepare(self, df):
        df["LB High"]=df["Close"].rolling(window=10).max().shift(1)
        df["LB Low"]=df["Close"].rolling(window=10).min().shift(1)
        df["close 1"]=df["Close"].shift(1)
        df["close 2"]=df["Close"].shift(2)
        df["close 3"]=df["Close"].shift(3)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        lb_high=df["LB High"].iloc[i]
        lb_low=df["LB Low"].iloc[i]
        close1=df["close 1"].iloc[i]
        close2=df["close 2"].iloc[i]
        close3=df["close 3"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(lb_high) or pd.isna(lb_low) or pd.isna(close1) or pd.isna(close2) or pd.isna(close3):
            return None
        if close>lb_high and close>close1 and close>close3 and close1>close2:
            return 1
        if close<lb_low and close<close1 and close<close3 and close1<close2:
            return -1
        return None
    
class AwsOsc:
    def __init__(self, name="AwsOsc"):
        self.name=name
    def prepare(self, df):
        df["AWS"]=AwesomeOscillator(df["High"], df["Low"], 5, 7)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        aws=df["AWS"].iloc[i]
        prev_aws=df["AWS"].iloc[i-1]
        high=df["High"].iloc[i]
        low=df["Low"].iloc[i]
        close=df["Close"].iloc[i]
        prev_high=df["High"].iloc[i-1]
        prev_low=df["Low"].iloc[i-1]
        if pd.isna(aws) or pd.isna(prev_aws) or pd.isna(high) or pd.isna(low) or pd.isna(close) or pd.isna(prev_high) or pd.isna(prev_low):
            return None
        close_location=(close-low)/(high-low +0.000001)
        condition1=aws>prev_aws
        condition2=aws<prev_aws
        condition3=low<prev_low and close_location>0.5
        condition4=high>prev_high and close_location < 0.5
        if condition1 and condition4:
            return 1
        if condition2 and condition3:
            return -1
        return None
    
class SeasonLong:
    def __init__(self, name="SeasonLong"):
        self.name=name
    def prepare(self, df):
        df["Month"]=df.index.month
        df["Lb High"]=df["Close"].rolling(window=10).max().shift(1)
        df["lb Low"]=df["Close"].rolling(window=10).min().shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        month=df["Month"].iloc[i]
        lb_high=df["Lb High"].iloc[i]
        lb_low=df["lb Low"].iloc[i]
        close=df["Close"].iloc[i]
        low=df["Low"].iloc[i]
        high=df["High"].iloc[i]
        if pd.isna(month) or pd.isna(lb_high) or pd.isna(lb_low) or pd.isna(close) or pd.isna(low) or pd.isna(high):
            return None
        if position !=0:
            return None
        if month<=6 and close>=lb_high and ((close-low)/(high-low)<0.5):
            return 1
        if month>6 and close<=lb_low and ((close-low)/(high-low)<0.5):
            return -1
        return None
    
class FilterEntry:
    def __init__(self, name="FilterEntry"):
        self.name=name
    def prepare(self, df):
        df["high1"]=df["High"].shift(1)
        df["low1"]=df["Low"].shift(1)
        df["high2"]=df["High"].shift(2)
        df["low2"]=df["Low"].shift(2)
        df["LL"]=df["Low"].rolling(window=25).min().shift(1)
        df["HH"]=df["High"].rolling(window=25).max().shift(1)
        return df
    def get_signal(self, df, i, position, openpnl):
        if position !=0:
            return None
        h1=df["high1"].iloc[i]
        l1=df["low1"].iloc[i]
        h2=df["high2"].iloc[i]
        l2=df["low2"].iloc[i]
        LL=df["LL"].iloc[i]
        HH=df["HH"].iloc[i]
        close=df["Close"].iloc[i]
        if pd.isna(h1) or pd.isna(l1) or pd.isna(h2) or pd.isna(l2) or pd.isna(LL) or pd.isna(HH) or pd.isna(close):
            return None
        can_trade=(h1-l1)<(h2-l2)
        if can_trade and close>=HH:
            return 1
        if can_trade and close<=LL:
            return -1
        return None

class Ultimate:
    def __init__(self, name="Ultimate"):
        self.name=name
    def prepare(self, df):
        df["Ultimate"]=UltimateOscillator(df["High"], df["Low"], df["Close"], 7, 14, 28)
        df["Ultimate 10"]=df["Ultimate"].rolling(window=10).min()
        df["Ultimate 10 High"]=df["Ultimate"].rolling(window=10).max()
        return df
    def get_signal(self, df, i, position, openpnl):
        ult=df["Ultimate"].iloc[i]
        ult10=df["Ultimate 10"].iloc[i]
        ult10_high=df["Ultimate 10 High"].iloc[i]
        if pd.isna(ult) or pd.isna(ult10) or pd.isna(ult10_high):
            return None
        if ult<=ult10:
            return 1
        if ult>=ult10_high:
            return -1

class DayTwist:
    def __init__(self, name="TwistDay"):
        self.name=name
    def prepare(self, df):
        df["Day"]=df.index.dayofweek
        return df
    def get_signal(self, df, i, position, openpnl):
        if i < 200:
            return None
        total_equity = df["Equity"].iloc[i]
        past_equity = df["Equity"].iloc[i-200]
        day=df["Day"].iloc[i]
        if pd.isna(total_equity) or pd.isna(past_equity) or pd.isna(day):
            return None
        can_trade=(total_equity-past_equity)>-600
        if day==3 and can_trade:
            return 1
        if day==4 and can_trade:
            return -1
        return None
    



##########################################################################
######################## EXIT STRATEGIES #################################
##########################################################################

class NoExit:
    def __init__(self, name="NoExit"):
        self.name=name
    def prepare(self, df):
        df["Highest Close"]=df["Close"].rolling(window=50).max()
        df["Lowest Close"]=df["Close"].rolling(window=50).min()
        return df
    def get_exit(self, df, i, position, openpnl):
        close=df["Close"].iloc[i]
        closehigh=df['Highest Close'].iloc[i]
        closelow=df["Lowest Close"].iloc[i]
        if pd.isna(closehigh) or pd.isna(closelow):
            return False
        if position==1 and close<=closelow:
            return True
        if position==-1 and close>=closehigh:
            return True
        return False
    
class DollarExit:
    def __init__(self, name="DollarExit", stop_dollars=200, target_dollars=400):
        self.name=name
        self.stop_dollars=stop_dollars
        self.target_dollars=target_dollars
    def prepare(self,df):
        return df
    def get_stop_target(self, df, i, position, entry_price, shares, cash):
        if position == 0 or entry_price is None or shares==0:
            return None
        stop_distance=self.stop_dollars/shares
        target_distance=self.target_dollars/shares
        if position == 1:
            stop_price=entry_price-stop_distance
            target_price = entry_price + target_distance
        elif position == -1:
            stop_price=entry_price+stop_distance
            target_price=entry_price-target_distance
        else:
            return None
        return{ "stop": stop_price,
                "target": target_price}
    
class ATRExit:
    def __init__(self, name="ATRExit", stop_atr=2, target_atr=3, atr_length=15):
        self.name=name
        self.stop_atr=stop_atr
        self.target_atr=target_atr
        self.atr_length=atr_length
    def prepare(self, df):
        df["Exit ATR"]=ATR(df["Close"], df["High"], df["Low"], self.atr_length)
        return df
    def get_stop_target(self, df, i, position, entry_price, shares, cash):
        if position == 0 or entry_price is None or shares == 0:
            return None
        atr=df["Exit ATR"].iloc[i]
        if pd.isna(atr):
            return None
        stop_distance=self.stop_atr*atr
        target_distance = self.target_atr*atr
        if position == 1:
            stop_price = entry_price - stop_distance
            target_price = entry_price + target_distance
        elif position == -1:
            stop_price = entry_price + stop_distance
            target_price = entry_price - target_distance
        else:
            return None
        return { "stop": stop_price,
                 "target": target_price}
    
class TimeExit:
    def __init__(self, name="TimeExit", bars=10, method="profit_time"):
        self.name=name
        self.bars=bars
        self.method=method
    def prepare(self, df):
        return df
    def get_exit(self, df, i, position, openpnl):
        bars_since_entry = df["Bars Since Entry"].iloc[i]
        if pd.isna(bars_since_entry) or pd.isna(openpnl) or pd.isna(position):
            return False
        if self.method == "time" and bars_since_entry >= self.bars:
            return True
        if self.method == "profit_time" and bars_since_entry >= self.bars and openpnl > 0:
            return True
        if self.method == "loss_time" and bars_since_entry >= self.bars and openpnl < 0:
            return True
        return False

class DateExit:
    def __init__(self, name="DateExit"):
        self.name=name
    def prepare(self, df):
        df["Month"]=df.index.month
        return df
    def get_exit(self, df, i, position, openpnl):
        month=df["Month"].iloc[i]
        prev_month=df["Month"].iloc[i-1]
        if pd.isna(month) or pd.isna(position):
            return False
        if position !=0 and month==1 and prev_month==12 or month==7 and prev_month==6:
            return True
        return False
    
class PercentileExit:
    def __init__(self, name="percentile", lookback=5):
        self.name=name
        self.lookback=lookback
    def prepare(self, df):
        df["Close Percentile"]=df["Close"].rolling(self.lookback).quantile(0.5)
        return df
    def get_exit(self, df, i, position, openpnl):
        close=df["Close"].iloc[i]
        close_percentile=df["Close Percentile"].iloc[i]
        if pd.isna(close) or pd.isna(close_percentile) or pd.isna(position):
            return False
        if position == 1 and close < close_percentile:
            return True
        if position == -1 and close > close_percentile:
            return True
        return False

class GetOut:
    def __init__(self, name="GetOut"):
        self.name=name
    def prepare(self, df):
        df["Close 1"]=df["Close"].shift(1)
        df["Close 2"]=df["Close"].shift(2)
        df["Close 3"]=df["Close"].shift(3)
        return df
    def get_exit(self, df, i, position, openpnl):
        close=df["Close"].iloc[i]
        close1=df["Close 1"].iloc[i]
        close2=df["Close 2"].iloc[i]
        close3=df["Close 3"].iloc[i]
        if position==0 or pd.isna(close) or pd.isna(close1) or pd.isna(close2) or pd.isna(close3):
            return False
        if position == 1 and close>close1 and close1>close2 and close2>close3:
            return True
        if position == -1 and close<close1 and close1<close2 and close2<close3:
            return True
        return False
    
class AtrAverage:
    def __init__ (self, name="AtrAverage"):
        self.name=name
    def prepare(self, df):
        df["ATR"]=ATR(df["Close"], df["High"], df["Low"], 15)
        return df
    def get_exit(self, df, i, position, openpnl):
        max_open_pnl=df["Max Open PnL"].iloc[i]
        shares=df["Current Shares"].iloc[i]
        atr=df["ATR"].iloc[i]
        if pd.isna(max_open_pnl) or pd.isna(atr) or pd.isna(position):
            return False
        if max_open_pnl-openpnl>3*atr*shares:
            return True
        return False
    
class Protector:
    def __init__(self, name="Protector"):
        self.name=name
    def prepare(self, df):
        return df
    def get_exit(self, df, i, position, openpnl):
        max_open_pnl=df["Max Open PnL"].iloc[i]
        floor=400
        ratio=0.5
        exit= max_open_pnl>=floor
        if pd.isna(max_open_pnl):
            return False
        if exit and (openpnl/max_open_pnl)<ratio:
            return True
        return False

class WhereYouLike:
    def __init__(self, name="WhereYouLike"):
        self.name=name
    def prepare(self, df):
        df["Long Target"]=df["High"].rolling(window=10).max().shift(1)
        df["Long Loss"]=df["Low"].rolling(window=7).min().shift(1)
        df["Short Target"]=df["Low"].rolling(window=10).min().shift(1)
        df["Short Loss"]=df["High"].rolling(window=7).max().shift(1)
        return df
    def get_stop_target(self, df, i, position, entry_price, shares, cash):
        if position == 1:
            stop_price=df["Long Loss"].iloc[i]
            target_price=df["Long Target"].iloc[i]
        elif position == -1:
            stop_price=df["Short Loss"].iloc[i]
            target_price=df["Short Target"].iloc[i]
        else:
            return None
        if pd.isna(stop_price) or pd.isna(target_price):
             return None

        return {"stop": stop_price, "target": target_price}
    
class Tiered:
    def __init__ (self, name="Tiered"):
        self.name=name 
    def prepare(self, df):
        return df
    def get_exit(self, df, i, position, openpnl):
        floor1=100
        floor2=200
        floor3=300
        ratio1=.6
        ratio2=.75
        ratio3=.90
        max_open_pnl=df["Max Open PnL"].iloc[i]
        if pd.isna(max_open_pnl) or pd.isna(openpnl):
            return False
        ppratio=0.0
        if pd.isna(max_open_pnl) or pd.isna(position):
            return None
        if max_open_pnl>floor1:
            ppratio=ratio1
        if max_open_pnl>floor2:
            ppratio=ratio2
        if max_open_pnl>floor3:
            ppratio=ratio3
        if max_open_pnl>floor1:
            if openpnl/max_open_pnl<ppratio:
                return True
        return False
    

