/**
 * Refs:
 * https://www.amibroker.com/guide/objects.html
 * https://www.amibroker.com/guide/d_ascii.html
 * https://docs.microsoft.com/en-us/office/vba/language/reference/user-interface-help/filesystemobject-object
 * https://docs.microsoft.com/en-us/previous-versions//98591fh7%28v%3dvs.85%29
 * https://forum.amibroker.com/t/cant-import-data-from-ascii-file-by-using-js-ole/4416
 */
var HOME = 'C:\\Users\\DonJuan'
var SRC_DIR = HOME + '\\checkouts\\my-projects\\trading-tools\\dukascopy-downloader'
var FORMAT_FILE = SRC_DIR + '\\conf\\dukascopydl-amibroker-csv.format'
var DATABASE = HOME + '\\software-config\\ami-broker\\databases\\dukascopydl'
var LOG_CTX = '[amibroker-db-update-ole]'

var shell = WScript.CreateObject("WScript.Shell");
var amiBroker = new ActiveXObject("Broker.Application");

function echo(s) {
  var d = new Date();
  var ts = '[' + d.toLocaleString() + ']';
  WScript.Echo(ts + LOG_CTX + ' ' + s);
}

function importData(files) {
  echo('Importing data into AmiBroker');
  
  try {
    echo('Loading Database[' + DATABASE + ']');
    amiBroker.LoadDatabase(DATABASE);
  
    echo('Processing[' + files.length + '] datasets');

    var i = 0;

    for (i = 0; i < files.length; i++) {
      var datasetFile = files(i);
      var formatFile = FORMAT_FILE;

      echo('Importing Dataset[' + datasetFile + '] with format[' + formatFile + ']');
      amiBroker.Import(
        0,
        datasetFile,
        formatFile
      );
    }
    
    echo('Saving and refreshing database');
    amiBroker.SaveDatabase();
    amiBroker.RefreshAll();
  } catch (err) {
    echo("Failed to import one or more files: " + err);
  }
}


/*
 * MAIN
 *
 * Args: <datafile> [<datafile2> ...]
 */
filenames = WScript.Arguments;
importData(filenames);
