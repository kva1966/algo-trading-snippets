from collections import defaultdict
import datetime as dt
import logging

import pandas as pd
import pytz
import requests

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def init_logging(level=logging.INFO):
  conf = {
    'level': level,
    'format': '[%(asctime)s] [%(threadName)s(%(thread)d)] [%(levelname)s] %(name)s:%(lineno)d %(funcName)s(): %(message)s'
  }
  logging.basicConfig(**conf)

init_logging()

_log = logging.getLogger(__name__)


def _log_api_request(url, params):
    safe_params = dict(params)
    safe_params['api_token'] = '***' # don't print!
    _log.info(f"Requesting data from [{url}] with params: {safe_params}")


def to_utc_timestamp(d: dt.datetime|str) -> int:
    if isinstance(d, str):
        d = dt.datetime.strptime(d, DATE_FORMAT)
    return int(d.astimezone(dt.UTC).timestamp())


def read_api_key(key_file: str):
    with open(key_file, 'r') as file:
        return file.read().strip()


def get_ohlcv(key_file: str, api_path: str, tz, search_params: dict = {}) -> pd.DataFrame:
    def to_df(data_json, local_tz) -> pd.DataFrame:
        data = defaultdict(list)
        idx = []
        for row in data_json:
            # Incoming timestamp is in UTC
            d = dt.datetime.fromtimestamp(row['timestamp'], tz=dt.UTC)
            # Now convert to local timezone
            d = d.astimezone(local_tz)
            # then convert to pandas Timestamp
            pd_ts = pd.Timestamp(d)
            idx.append(pd_ts)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                data[col].append(row[col])
        df = pd.DataFrame(data, index=idx)
        assert len(df) == len(data_json)
        return df

    url = f'https://eodhd.com/api/{api_path}'
    params = {
        'api_token': read_api_key(key_file=key_file),
        'fmt': 'json',
    }
    params.update(search_params)
    _log_api_request(url, params)
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise Exception(f"Error on [{url}]: {resp.status_code}|{resp.text}")
    return to_df(resp.json(), local_tz=tz)

