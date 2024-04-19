#!/usr/bin/env python

##
# Old page: https://interactivebrokers.github.io/tws-api/index.html
# New page: https://ibkrcampus.com/ibkr-api-page/twsapi-doc/
##

###
# IPython Re-Load Magic:
#
# > %alias_magic rld %load -p ./basic-client.py
#
# # then we can do the following to reload.
# > %rld
###

import sys
sys.path.append('./src')
from collections import defaultdict
import datetime as dt
import time

from brokerplatform.ib import init_logging
from brokerplatform.ib.app import TwsApp
init_logging()

import logging

from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails
from ibapi.common import BarData

import pandas as pd
import pytz


log = logging.getLogger(__name__)

class AppMessageHandler(EWrapper):
    """
    Overrides handlers for messages we are interested in.
    """

    def __init__(self):
        EWrapper.__init__(self)
        self.hist_data = None
        self.tmp_hist_data_idx = []
        self.tmp_hist_data_dict = defaultdict(list)

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        '''Overriden method'''
        errPrefix = 'Info' if errorCode == -1 else 'Error'
        log.info(f"[{errPrefix}] reqId={reqId}|code={errorCode}|msg={errorString}|advOrderRejectJson={advancedOrderRejectJson}")

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        '''Overriden method'''
        log.info(f"[ContractDetails] reqId={reqId}|contractDetails={contractDetails}")

    def historicalData(self, reqId: int, bar: BarData):
        """returns the requested historical data bars

        reqId - the request's identifier
        date  - the bar's date and time (either as a yyyymmss hh:mm:ssformatted
             string or as system time according to the request)
        open  - the bar's open point
        high  - the bar's high point
        low   - the bar's low point
        close - the bar's closing point
        volume - the bar's traded volume if available
        count - the number of trades during the bar's timespan (only available
            for TRADES).
        WAP -   the bar's Weighted Average Price
        hasGaps  -indicates if the data has gaps or not."""
        log.info(f"[HistoricalData] reqId={reqId}|bar={bar}")

        local_tz = pytz.timezone('Asia/Jakarta')
        # Incoming timestamp is in UTC
        bar_dt = dt.datetime.fromtimestamp(float(bar.date), tz=dt.UTC)
        # Now convert to local timezone
        bar_dt = bar_dt.astimezone(local_tz)
        # then convert to pandas Timestamp
        pd_ts = pd.Timestamp(bar_dt)
        self.tmp_hist_data_idx.append(pd_ts)
        row_dict = self.tmp_hist_data_dict
        row_dict['open'].append(bar.open)
        row_dict['high'].append(bar.high)
        row_dict['low'].append(bar.low)
        row_dict['close'].append(bar.close)
        row_dict['volume'].append(bar.volume)


    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Marks the ending of the historical bars reception."""
        log.info(f"[HistoricalDataEnd] reqId={reqId}|start={start}|end={end}")
        self.hist_data = pd.DataFrame(self.tmp_hist_data_dict, index=self.tmp_hist_data_idx)
        # reset holding vars
        self.tmp_hist_data_dict = defaultdict(list)
        self.tmp_hist_data_idx = []



handler = AppMessageHandler()
app = TwsApp(message_handler=handler)
app.start()

# https://ibkrcampus.com/ibkr-api-page/twsapi-doc/#contracts
c = Contract()
c.symbol = "MCL" # Mini Futures Crude Oil
c.secType = "CONTFUT" # Continuous Futures, for historical data access
c.exchange = "NYMEX"
app.client.reqContractDetails(app.nextId, c)


# Time format
# In [25]: [2024-04-14 02:21:25,421] [Thread-14 (_run)(6180450304)] [INFO] __main__:43 error():
# [Error] reqId=7|code=10314|msg=End Date/Time: The date, time, or time-zone entered is invalid.
# The correct format is yyyymmdd hh:mm:ss xx/xxxx where yyyymmdd and xx/xxxx are optional.
# E.g.: 20031126 15:59:00 US/Eastern  Note that there is a space between the date and time,
# and between the time and time-zone.  If no date is specified, current date is assumed. If
# no time-zone is specified, local time-zone is assumed(deprecated).  You can also provide
# yyyymmddd-hh:mm:ss time is in UTC. Note that there is a dash between the date and time in
# UTC notation.|advOrderRejectJson=

# Specify our date time in UTC, using the following format.
# So when we get it back, we will get a UTC timestamp, which we convert back to
# our local time.
utc_fmt = "%Y%m%d-%H:%M:%S"

app.client.reqHistoricalData(
    reqId=app.nextId,
    contract=c,
    #endDateTime="", # Till now
    #endDateTime=dt.datetime.now(tz).strftime(f"%Y%m%d %H:%M:%S {tz.zone}"), # Till now
    endDateTime=dt.datetime.now(dt.UTC).strftime(utc_fmt), # Till now
    durationStr="5 D",
    barSizeSetting="2 mins",
    whatToShow="MIDPOINT",
    useRTH=1,
    formatDate=2, # Better to use the Epoch, and then convert to local time
    keepUpToDate=False, # We don't want new incoming updates
    chartOptions=[], # internal use, just specify empty list
)

time.sleep(10) # Wait to get async response
df = handler.hist_data
#app.stop()
# app.start()

###
# [2024-04-19 14:41:57,697] [Thread-2 (_run)(6140243968)] [INFO] __main__:54 error():
# [Error] reqId=2|code=2174|msg=Warning: You submitted request with date-time attributes
# without explicit time zone. Please switch to use yyyymmdd-hh:mm:ss in UTC
# or use instrument time zone, like US/Eastern. Implied time zone functionality
# will be removed in the next API release|advOrderRejectJson=
###
