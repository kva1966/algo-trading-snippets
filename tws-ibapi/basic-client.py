#!/usr/bin/env python

##
# https://interactivebrokers.github.io/tws-api/index.html
##

###
# IPython Re-Load Magic:
#
# > %alias_magic rld %load -p ./basic-client.py
#
# # then we can do the following to reload.
# > %rld
###

import threading
import logging
from dataclasses import dataclass

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails

TWS_HOST = "127.0.0.1"
TWS_PORT = 7497

def init_logging(level=logging.INFO):
  conf = {
    'level': level,
    'format': '[%(asctime)s] [%(threadName)s(%(thread)d)] [%(levelname)s] %(name)s:%(lineno)d %(funcName)s(): %(message)s'
  }
  logging.basicConfig(**conf)

init_logging()

log = logging.getLogger(__name__)

# Max request id (use a practical value on 32 bit system), before we reset.
MAX_REQUEST_ID = 2**31 - 1

class TwsMessageHandler(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

    def _connect(self):
        self.connect(TWS_HOST, TWS_PORT, clientId=0)

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        '''Overriden method'''
        errPrefix = 'Info' if errorCode == -1 else 'Error'
        log.info(f"[{errPrefix}] reqId={reqId}|code={errorCode}|msg={errorString}|advOrderRejectJson={advancedOrderRejectJson}")

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        '''Overriden method'''
        log.info(f"[ContractDetails] reqId={reqId}|contractDetails={contractDetails}")


@dataclass
class TwsApp:
    def __init__(self):
        log.info("Initialising TwsApp")
        self._requestId = 0
        self._running = False
        self._messageHandler = None

    def start(self):
        log.info("Starting TwsApp")
        if not self._messageHandler:
            self._messageHandler = TwsMessageHandler()
        self._connect()
        self._runInThread()

    def stop(self):
        log.info("Stopping TwsApp")
        self._disconnect() # Stops the message handler's run() loop and thread
        self._running = False

    def reqContractDetails(self, c: Contract):
        self._messageHandler.reqContractDetails(self._genRequestId(), c)

    def _genRequestId(self) -> int:
        self._requestId += 1
        if self._requestId >= MAX_REQUEST_ID:
            self._requestId = 1
        return self._requestId

    def _connect(self):
        log.info("Connecting to TWS")
        if self._messageHandler.isConnected():
            log.info("Already connected")
            return
        self._messageHandler.connect(TWS_HOST, TWS_PORT, clientId=0)

    def _disconnect(self):
        log.info("Disconnecting from TWS")
        if not self._messageHandler.isConnected():
            log.info("Not connected, nothing to do")
            return
        self._messageHandler.disconnect()

    def _runInThread(self):
        if self._running:
            log.info("Application is already running")
            return
        log.info("Running application")
        def _run():
            self._messageHandler.run()
            # A disconnect() call will stop the message handler's run() loop
            log.info("MessageHandler stopped, exiting thread")
        threading.Thread(target=_run).start()
        self._running = True

app = TwsApp()
app.start()

c = Contract()
c.symbol = "MCL" # Mini Futures Crude Oil
c.secType = "CONTFUT" # Continuous Futures, for historical data access
c.exchange = "NYMEX"
