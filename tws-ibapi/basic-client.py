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
import time

from brokerplatform.ib import init_logging
from brokerplatform.ib.app import TwsApp
init_logging()

import logging

from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails


log = logging.getLogger(__name__)

class AppMessageHandler(EWrapper):
    """
    Overrides handlers for messages we are interested in.
    """
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        '''Overriden method'''
        errPrefix = 'Info' if errorCode == -1 else 'Error'
        log.info(f"[{errPrefix}] reqId={reqId}|code={errorCode}|msg={errorString}|advOrderRejectJson={advancedOrderRejectJson}")

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        '''Overriden method'''
        log.info(f"[ContractDetails] reqId={reqId}|contractDetails={contractDetails}")



app = TwsApp(message_handler=AppMessageHandler())
app.start()

# https://ibkrcampus.com/ibkr-api-page/twsapi-doc/#contracts
c = Contract()
c.symbol = "MCL" # Mini Futures Crude Oil
c.secType = "CONTFUT" # Continuous Futures, for historical data access
c.exchange = "NYMEX"
app.client.reqContractDetails(app.nextId, c)

time.sleep(2) # Wait to get async response before stopping
app.stop()
# app.start()
