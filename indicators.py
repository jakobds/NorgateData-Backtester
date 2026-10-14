import numpy as np
import pandas as pd

#FOR TESTING INDICATORS
#df=pd.read_csv("algo/stockdata/SPY.csv", parse_dates=['Date'], index_col=['Date'])


def Rate_of_Change(price, period):
    #Momentum indicator that measures the percentage change in price over a specified period
    return ((price - price.shift(period)) / price.shift(period))*100

def RSI(price, period):
    #Momentum oscilator that measures price direction and change of speed
    delta = price.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.rolling(window=period, min_periods=period).mean()
    average_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period+1, len(price)):
        average_gain.iloc[i] = ((average_gain.iloc[i - 1] * (period - 1)) + gain.iloc[i]) / period
        average_loss.iloc[i] = ((average_loss.iloc[i - 1] * (period - 1)) + loss.iloc[i]) / period
    rsi=100-(100/(1+(average_gain/average_loss)))
    return rsi


def Stochastic(high,low,price,k_period=14,d_period=3,k_smooth=3):
    highest_high = high.rolling(window=k_period).max()
    lowest_low = low.rolling(window=k_period).min()
    fast_k=(((price-lowest_low)/(highest_high-lowest_low))*100)
    k=fast_k.rolling(window=k_smooth).mean()
    d=k.rolling(window=d_period).mean()
    return k, d

def Moving_Average(price, period):
    ma=price.rolling(window=period).mean()
    return ma
def Exponential_Moving_Average(price, period):
    return price.ewm(span=period, adjust=False).mean()

def MACD(price, short=12, long=26, trigger=9):
    emashort=price.ewm(span=short, adjust=False).mean()
    emalong=price.ewm(span=long, adjust=False).mean()
    macd=emashort-emalong
    return macd
def MACD_Signal(price, short=12, long=26, trigger=9):
    emashort=price.ewm(span=short, adjust=False).mean()
    emalong=price.ewm(span=long, adjust=False).mean()
    macd=emashort-emalong
    signal=macd.ewm(span=trigger, adjust=False).mean()
    return signal
def MACD_Histogram(price, short=12, long=26, trigger=9):
    emashort=price.ewm(span=short, adjust=False).mean()
    emalong=price.ewm(span=long, adjust=False).mean()
    macd=emashort-emalong
    signal=macd.ewm(span=trigger, adjust=False).mean()
    histogram= macd-signal
    return histogram

def ADX(close, period, high, low):
    tr = pd.concat([
        high - low, 
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()],
            axis=1).max(axis=1)
    plus_dm=(high-high.shift(1)).where(((high-high.shift(1))>low.shift(1)-low) & ((high-high.shift(1))>0), 0)
    minus_dm=(low.shift(1)-low).where(((low.shift(1)-low)>(high-high.shift(1))) & ((low.shift(1)-low)>0), 0)
    tr.iloc[0]=np.nan
    plus_dm.iloc[0]=np.nan
    minus_dm.iloc[0]=np.nan
    smooth_tr=tr.rolling(window=period, min_periods=period).sum()
    smooth_plus_dm=plus_dm.rolling(window=period, min_periods=period).sum()
    smooth_minus_dm=minus_dm.rolling(window=period, min_periods=period).sum()
    for i in range(period + 1, len(close)):
        smooth_tr.iloc[i] = smooth_tr.iloc[i - 1] - (smooth_tr.iloc[i - 1] / period) + tr.iloc[i]
        smooth_plus_dm.iloc[i] = smooth_plus_dm.iloc[i - 1] - (smooth_plus_dm.iloc[i - 1] / period) + plus_dm.iloc[i]
        smooth_minus_dm.iloc[i] = smooth_minus_dm.iloc[i - 1] - (smooth_minus_dm.iloc[i - 1] / period) + minus_dm.iloc[i]
    plus_di=100*(smooth_plus_dm/smooth_tr)
    minus_di=100*(smooth_minus_dm/smooth_tr)
    dx=100*(plus_di-minus_di).abs()/(plus_di+minus_di).replace(0, np.nan)
    adx=dx.rolling(window=period, min_periods=period).mean()
    for i in range((period*2), len(close)):
        adx.iloc[i]=((adx.iloc[i-1]*(period-1))+dx.iloc[i])/period
    return adx
    
def ATR(close, high, low, period):
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()  # Wilder smoothing

    return atr

def Triangular_Moving_Average(price, period):
    if period % 2 == 0:
        length1 = period // 2
        length2 = length1 + 1
    else:
        length1 = (period + 1) // 2
        length2 = length1
    return price.rolling(length1).mean().rolling(length2).mean()

def MoneyFlow(high, low, close, volume, period):
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    price_change=typical_price.diff()
    positive_flow = raw_money_flow.where(price_change > 0, 0)
    negative_flow = raw_money_flow.where(price_change < 0, 0)
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    money_flow_ratio = positive_mf / negative_mf.replace(0, np.nan)
    mfi = 100 - (100 / (1 + money_flow_ratio))
    return mfi

def BollingerBands(close, period, std=2):
    middle=close.rolling(window=period).mean()
    rolling_std=close.rolling(window=period).std()
    upper=middle+(rolling_std*std)
    lower=middle-(rolling_std*std)
    return upper, middle, lower


def Keltner(close, ma_period, high, low, atr_period, atr_mult):
    # Calculate the middle band (Moving Average)
    middle = close.rolling(window=ma_period).mean()

    # Calculate the ATR
    atr = ATR(close, high, low, atr_period)

    # Calculate the upper and lower bands
    upper = middle + (atr * atr_mult)
    lower = middle - (atr * atr_mult)

    return upper, middle, lower

def TR(high, low, close):
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    return tr

def CCI(high, low, close, CCIperiod, maperiod):
    typical_price=(high+low+close)/3
    sma=typical_price.rolling(window=CCIperiod).mean()
    md=typical_price.rolling(window=CCIperiod).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    cci=(typical_price-sma)/(0.015*md)
    ccima=cci.rolling(window=maperiod).mean()
    return cci, ccima

def AwesomeOscillator(high, low, short=5, long=34):
    median_price=(high+low)/2
    ao=median_price.rolling(window=short).mean()-median_price.rolling(window=long).mean()
    return ao

def UltimateOscillator(high, low, close, short=7, medium=14, long=28):
    bp = close - low.combine(close.shift(1), func=min)
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    avg7 = bp.rolling(window=short).sum() / tr.rolling(window=short).sum()
    avg14 = bp.rolling(window=medium).sum() / tr.rolling(window=medium).sum()
    avg28 = bp.rolling(window=long).sum() / tr.rolling(window=long).sum()
    uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / (4 + 2 + 1)
    return uo

#FOR TESTIGN INDIACTORAS

#df["CCI"], df["CCIMA"]=CCI(df["High"], df["Low"], df["Close"], 14, 14)
#print(df.tail(14))