# README

Original sources obtained from:

https://interactivebrokers.github.io/#

For reference when developing, see the two main classes:

* EWrapper: a message handler interface.
  * IBJts/source/pythonclient/ibapi/wrapper.py
* EClient: the client that connects to the IB Gateway/TWS, and takes an EWrapper
  instance, passing responses to it, for requests invoked on the client.
  * IBJts/source/pythonclient/ibapi/client.py
