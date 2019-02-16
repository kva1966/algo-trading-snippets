from typing import List
from types import LambdaType

class MissingDataSetsException(Exception):
  def __init__(self, total_checked: int, missing_datasets: List[str]):
    assert missing_datasets
    self.datasets = missing_datasets
    self.total_checked = total_checked
    self.missing_count = len(missing_datasets)

class ImportLog:
  """
  Examines an AmiBroker import.log file, e.g. in C:\Program Files\AmiBroker\import.log
  to do some sanity checks to confirm datasets were loaded in. The assumption here is
  that if the import logs are clean, we are less likely to have missed data loading.

  Further checks can be done by doing bar count comparisons in AFL, etc., this is just
  one part of error checking.

  Operations are heuristics-based, non-deterministic, and load data in memory. 


  SAMPLE: Clean import.log: each logging entry in one line, followed by a blank line 
  before the entry

  ----FILE----
Logging started for 'C:\\Users\DonJuan\AppData\Roaming\data\AUDJPY-2012-01-01.dukasdl-amibroker-csv' file, using format definition file 'C:\\Users\DonJuan\checkouts\dukascopydl-amibroker-csv.format'

Logging started for 'C:\\Users\DonJuan\AppData\Roaming\data\AUDJPY-2012-01-02.dukasdl-amibroker-csv' file, using format definition file 'C:\\Users\DonJuan\checkouts\dukascopydl-amibroker-csv.format'

Logging started for 'C:\\Users\DonJuan\AppData\Roaming\data\AUDJPY-2012-01-01.dukasdl-amibroker-csv' file, using format definition file 'C:\\Users\DonJuan\checkouts\dukascopydl-amibroker-csv.format'

  ----EOF----


  SAMPLE: import.log with errors --- errors are reported in consecutive lines (no blank line) 
  after the logging entry:
  ----FILE----

Logging started for 'C:\\Users\DonJuan\AppData\Roaming\data\\badtest.dukasdl-amibroker-csv' file, using format definition file 'Formats\dukascopydl-amibroker-csv.format'
Error in line nthountohnu,nthaousnthon,onetuhonu,090808,09888
Invalid (close) price. Prices must be positive. If you want to import no quotation data please specify $NOQUOTES 1 ('no quotation data' box in Wizard)
Invalid date format/value

  ----EOF----

  """
  def __init__(self, log_file: str):
    assert log_file
    self.log_file = log_file

  def verify_no_errors(self, error_string='Error in line'):
    """
    Fuzzy match for 'Error in line' strings, nothing deterministic, throws error on
    finding any such string.
    """
    assert error_string

    def check_errors(s):
      if error_string in s:
        raise Exception(f'Log contained string[{error_string}], check failed')

    self._with_file_data(check_errors)
  
  def verify_datasets_imported(self, dataset_names: List[str]):
    """
    Searches for each item in the list within the file, throwing a
    MissingDataSets exception whose `datasets` property contains what entries
    could not be found in the log file.
    """
    def check_datasets(s):
      missing = [dset for dset in dataset_names if dset not in s]
      if missing:
        raise MissingDataSetsException(
          missing_datasets=missing,
          total_checked=len(dataset_names)
        )

    self._with_file_data(check_datasets)
  
  def _with_file_data(self, handler_fn: LambdaType):
    data = None
    with open(self.log_file, 'r') as f:
      data = f.read()
    handler_fn(data)
