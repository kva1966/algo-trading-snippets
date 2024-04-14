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
                    peak_col_name: str,
                    valley_col_name: str,
                    high_price_col_name: str,
                    low_price_col_name: str) -> tuple[pd.Series, pd.Series]:
    '''
    Returns a tuple of two series, the first series is a bullish divergence
    series, the second series is a bearish divergence series. They will contain
    NaN values where there is no divergence.
    '''
    peak_idx = []
    valley_idx = []

    for index, row in df.iterrows():
        if row[peak_col_name] == True:
            peak_idx.append(index)

        if row[valley_col_name] == True:
            valley_idx.append(index)

    # Init with NaN values
    bullish_divergence = pd.Series(index=df.index, data=np.nan)
    bearish_divergence = pd.Series(index=df.index, data=np.nan)

    # TODO ...



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



