#!/usr/bin/env python
###
# IPython Re-Load Magic:
#
# > %alias_magic rld %load -p ./test.py
#
# # then we can do the following to reload.
# > %rld
###

import sys
sys.path.append('./src')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz

import divdetect as dd

LOCAL_TZ = pytz.timezone('Asia/Jakarta')
KEY_FILE = './creds/eodhd-api-key'

df = dd.get_ohlcv(
    key_file=KEY_FILE,
    # https://eodhd.com/financial-apis/list-supported-forex-currencies/
    # https://eodhd.com/financial-apis/intraday-historical-data-api/
    api_path='/intraday/AAPL.US',
    tz=LOCAL_TZ,
    search_params={
        'interval': '1h',
        'from': dd.to_utc_timestamp('2024-03-08 00:00:00'),
        'to': dd.to_utc_timestamp('2024-04-11 00:00:00'),
    })


def find_peaks(ser: pd.Series):
    # centre bar is higher than previous and next
    peaks = (ser.shift(1) > ser.shift(2)) & (ser.shift(1) > ser)
    # shift result forward so that the peak is marked on the centre bar
    return peaks.shift(-1)


def find_valleys(ser: pd.Series):
    # centre bar is lower than previous and next
    valleys = (ser.shift(1) < ser.shift(2)) & (ser.shift(1) < ser)
    # shift result forward so that the valley is marked on the centre bar
    return valleys.shift(-1)

def mark_divergence(df: pd.DataFrame,
                    series_peak_col_name: str,
                    series_valley_col_name: str,
                    high_price_col_name: str,
                    low_price_col_name: str) -> tuple[pd.Series, pd.Series]:
    '''
    Returns a tuple of two series, the first series is a bullish divergence
    series, the second series is a bearish divergence series. They will contain
    NaN values where there is no divergence.

    Supply a dataframe containing the oscillator series, identified by the names
    series_peak_col_name and series_valley_col_name, and the high and low price
    series identified by the names high_price_col_name and low_price_col_name.

    The logic is based on: https://academy.ftmo.com/lesson/divergence-trading/
    except we don't worry about having a pivot high/low on the prices series, only
    on the oscillator series. And only 3 adjacent bars are taken into account
    on the oscillator. On the price series we just want the relative high/low
    prices to follow the rules of the divergence.

    Returns a dict with 4 keys, each has a value of a pandas boolean series where
    true values at the dataframe indexes are where a divergence is detected.

    The keys are:

    * bullish_divergence
    * bearish_divergence
    * hidden_bullish_divergence
    * hidden_bearish_divergence
    '''
    peak_idx = []
    valley_idx = []

    for index, row in df.iterrows():
        if row[series_peak_col_name] == True:
            peak_idx.append(index)

        if row[series_valley_col_name] == True:
            valley_idx.append(index)

    # Init with False values
    bullish_divergence = pd.Series(index=df.index, data=False)
    bearish_divergence = pd.Series(index=df.index, data=False)
    hidden_bullish_divergence = pd.Series(index=df.index, data=False)
    hidden_bearish_divergence = pd.Series(index=df.index, data=False)

    # The logic we will use is not terribly precise, in particular we don't care
    # that the price is also at a peak or valley. Just that there is a divergence.
    # Further visual inspection or analysis is always required for divergence
    # trading.
    #
    # A bullish divergence is when:
    #
    # * We take two consecutive/adjacent valleys in the oscillator series.
    # * The second valley is higher than the first valley.
    # * But the prices across the indexes registered a lower low in the second valley.
    #
    # Meaning the momentum of the new price low is weaker than the previous low.
    #
    # A bearish divergence is when:
    #
    # * We take two consecutive/adjacent peaks in the oscillator series.
    # * The second peak is lower than the first peak.
    # * But the prices across the indexes registered a higher high in the second peak.
    #
    # Meaning the momentum of the new price high is weaker than the previous high.
    #
    # A bullish hidden divergence is when:
    #
    # * We take two consecutive/adjacent valleys in the oscillator series.
    # * The second valley is lower than the first valley.
    # * But the prices across the indexes registered a higher low in the second valley.
    #
    # This is counterintuitive, but it almost means that we have exhausted the down
    # move's momentum and a reversal to the upside is likely.
    #
    # A bearish hidden divergence is when:
    #
    # * We take two consecutive/adjacent peaks in the oscillator series.
    # * The second peak is higher than the first peak.
    # * But the prices across the indexes registered a lower high in the second peak.
    #
    # This is counterintuitive, but it almost means that we have exhausted the up
    # move's momentum and a reversal to the downside is likely.

    # TODO ...
    return {
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'hidden_bullish_divergence': hidden_bullish_divergence,
        'hidden_bearish_divergence': hidden_bearish_divergence,
    }


def lbr310(ser: pd.Series) -> (pd.Series, pd.Series):
    fast_ser = ser.rolling(window=3).mean()
    slow_ser = ser.rolling(window=10).mean()
    macd = fast_ser - slow_ser
    signal = macd.rolling(window=16).mean()
    return (macd, signal)


def plot_gapless(df: pd.DataFrame, cols: list[str]):
    df = df.copy()

    # Use integers for indexing
    int_idx_ser = np.arange(len(df))

    # Plot the data
    df.index = int_idx_ser
    _df = df[cols]
    _df.plot()
    plt.tight_layout()
    plt.show()

# lookback = 30
# df = df.tail(lookback).copy()

# Price peaks, use the highs
df['peaks'] = find_peaks(df['high'])
# Price peaks, use the lows
df['valleys'] = find_valleys(df['low'])

# LBR 3-10 oscillator
macd, signal = lbr310(df['close'])
df['macd'] = macd
df['signal'] = signal

#print(df[df['peaks'] == True])
# print(df[['high', 'peaks']])
# print(df[['low', 'valleys']])


# plot_gapless(df, ['close'])
# plt.show()

# For the MACD, we need to find peaks only on the positive zone
df['macd_peaks'] = find_peaks(macd.where(macd > 0))
# For the MACD, we need to find valleys only on the negative zone
df['macd_valleys'] = find_valleys(macd.where(macd < 0))

print(df[['macd', 'macd_peaks', 'macd_valleys']])



