import threading
import logging
from dataclasses import dataclass

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

IBGATEWAY_LIVE_TRADING_PORT = 4001
IBGATEWAY_PAPER_TRADING_PORT = 4002
TWS_LIVE_TRADING_PORT = 7496
TWS_PAPER_TRADING_PORT = 7497
IBAPI_HOST = "127.0.0.1"

log = logging.getLogger(__name__)

# Max request id (use a practical value on 32 bit system), before we reset.
MAX_REQUEST_ID = 2**31 - 1

@dataclass
class TwsApp:
    """
    TWS/IB Gateway Client Application.

    Access the underlying client directly via the `client` property. This class
    provides handy methods to start and stop the client within a thread.

    ```
    # Initialise
    app = TwsApp(message_handler=EWrapperMessageHandler())
    app.start()

    # Request contract details (EWrapperMessageHandler must implement contractDetails())
    c = Contract()
    c.symbol = "MCL" # Mini Futures Crude Oil
    c.secType = "CONTFUT" # Continuous Futures, for historical data access
    c.exchange = "NYMEX"
    app.client.reqContractDetails(app.nextId, c)

    # Stop the app
    app.stop()
    ```

    References:
    * Old page: https://interactivebrokers.github.io/tws-api/index.html
    * New page: https://ibkrcampus.com/ibkr-api-page/twsapi-doc/
    * Udemy Course: https://www.udemy.com/course/algorithmic-trading-using-interactive-brokers-python-api/learn/lecture/21427678#overview
    """
    message_handler: EWrapper
    host: str = IBAPI_HOST
    port: int = IBGATEWAY_PAPER_TRADING_PORT
    max_request_id: int = MAX_REQUEST_ID
    client_id: int = 0

    """
    This is a generic TWS/IB Gateway client application class.

    Supply a message handler that inherits from EWrapper to handle messages that
    we expect to get back via calls from `TwsApp.client` to the TWS/IB Gateway.
    """
    def __post_init__(self):
        log.info("Initialising TwsApp")
        assert isinstance(self.message_handler, EWrapper), "message_handler must inherit from EWrapper"
        assert self.host, "host must be a valid IP address or domain"
        assert self.port >= 0 and self.port <= 65535, "port must be a valid port number"
        assert self.client_id >= 0, "client_id must be a positive integer"
        assert self.max_request_id >= 0, "max_request_id must be 0 or greater"
        self._client = None
        self._curr_request_id = 0
        self._running = False

    def start(self):
        log.info("Starting TwsApp")
        if not self._client:
            self._client = EClient(self.message_handler)
        self._connect()
        self._runInThread()

    def stop(self):
        log.info("Stopping TwsApp")
        self._disconnect() # Stops the message handler's run() loop and thread
        self._running = False

    @property
    def nextId(self):
        '''Generates a request id for use in various `client.req*` calls.'''
        self._curr_request_id += 1
        if self._curr_request_id >= MAX_REQUEST_ID:
            self._curr_request_id = 1
        return self._curr_request_id

    @property
    def client(self):
        '''Access the EClient instance, to make `req*` calls.'''
        return self._client

    def _connect(self):
        log.info(f"Connecting to TWS[{self.host}:{self.port}]")
        if self._client.isConnected():
            log.info("Already connected")
            return
        self._client.connect(self.host, self.port, clientId=self.client_id)

    def _disconnect(self):
        log.info("Disconnecting from TWS")
        if not self._client.isConnected():
            log.info("Not connected, nothing to do")
            return
        self._client.disconnect()

    def _runInThread(self):
        if self._running:
            log.info("Application is already running")
            return
        log.info("Running application")
        def _run():
            self._client.run()
            # A disconnect() call will stop the client's run() loop
            log.info("Client stopped, exiting thread")
        threading.Thread(target=_run).start()
        self._running = True
