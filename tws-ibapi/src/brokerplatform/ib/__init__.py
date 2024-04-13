import logging

def init_logging(level=logging.INFO):
  conf = {
    'level': level,
    'format': '[%(asctime)s] [%(threadName)s(%(thread)d)] [%(levelname)s] %(name)s:%(lineno)d %(funcName)s(): %(message)s'
  }
  logging.basicConfig(**conf)
