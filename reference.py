#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Suredone Download

@contributor: Hassan Ahmed
@contact: ahmed.hassan.112.ha@gmail.com
@owner: Patrick Mahoney
@version: 1.0.7

This module is created to use the Suredone API to create a custom CSV of store's 
product and sales records, and get it downloaded
The CSV currently intended to download has the following columns:
    - guid
    - stock
    - price
    - msrp
    - cost
    - title
    - longdescription
    - condition
    - brand
    - upc
    - media1
    - weight
    - datesold
    - totalsold
    - manufacturerpartnumber
    - warranty
    - mpn
    - ebayid
    - ebaysku
    - ebaycatid
    - ebaystoreid
    - ebayprice
    - ebaytitle
    - ebaystarttime
    - ebayendtime
    - ebaysiteid
    - ebaysubtitle
    - ebaypaymentprofileid
    - ebayreturnprofileid
    - ebayshippingprofileid
    - ebaybestofferenabled
    - ebaybestofferminimumprice
    - ebaybestofferautoacceptprice
    - ebaybuyitnow
    - ebayupcnot
    - ebayskip
    - amznsku
    - amznasin
    - amznprice
    - amznskip
    - walmartskip
    - walmartprice
    - walmartcategory
    - walmartdescription
    - walmartislisted
    - walmartinprogress
    - walmartstatus
    - walmarturl
    - total_stock
    
Usage:
    The script is capable of running without any argument provided. All behavorial
    variables will be reset to default.
    
    $ python3 suredone_download.py [options]

Parameters/Options:
    -h  | --help            : View usage help and examples
    -d  | --delimter        : Delimiter to be used as the separator in the CSV file saved by the script
        |                       - Default is comma ','.
    -f  | --file            : Path to the configuration file containing API keys
        |                       - Default in %APPDATA%/local/suredone.yaml on Window
        |                       - Default in $HOME/suredone.yaml
    -o  | --output          : Path for the output file to be downloaded at
        |                       - Default in %USERPROFILE%/Downloads/SureDone_Downloads_yyyy_mm_dd-hh-mm-ss.csv
        |                       - Default in $HOME/downloads/SureDone_Downloads_yyyy_mm_dd-hh-mm-ss.csv
    -p  | --preserve        : Do not delete older files that start with 'SureDone_' in the download directory
        |                       - This funciton is limited to default download locations only.
        |                       - Defining custom output path will render this feature useless.
    -v  | --verbose         : Show outputs in terminal as well as log file
    -w  | --wait            : Custom timeout for requests invoked by the script (specified in seconds)
        |                       - Default: 15 seconds

Example:
    $ python3 suredone_download.py

    $ python3 suredone_download.py -f [config.yaml]
    $ python3 suredone_download.py -file [config.yaml]

    $ python3 suredone_download.py -f [config.yaml] -o [output.csv]
    $ python3 suredone_download.py -file [config.yaml] --output_file [output.csv]

    $ python3 suredone_download.py -f [config.yaml] -o [output.csv] -v -p
    $ python3 suredone_download.py -file [config.yaml] --output_file [output.csv] --verbose --preserve
"""

# Help message
HELP_MESSAGE = """
Usage:
    The script is capable of running without any argument provided. All behavorial
    variables will be reset to default.
    
    $ python3 suredone_download.py [options]

Parameters/Options:
    -h  | --help            : View usage help and examples
    -d  | --delimter        : Delimiter to be used as the separator in the CSV file saved by the script
        |                       - Default is comma ','.
    -f  | --file            : Path to the configuration file containing API keys
        |                       - Default in %APPDATA%/local/suredone.yaml on Window
        |                       - Default in $HOME/suredone.yaml
    -o  | --output          : Path for the output file to be downloaded at
        |                       - Default in %USERPROFILE%/Downloads/SureDone_Downloads_yyyy_mm_dd-hh-mm-ss.csv
        |                       - Default in $HOME/downloads/SureDone_Downloads_yyyy_mm_dd-hh-mm-ss.csv
    -p  | --preserve        : Do not delete older files that start with 'SureDone_' in the download directory
        |                       - This funciton is limited to default download locations only.
        |                       - Defining custom output path will render this feature useless.
    -v  | --verbose         : Show outputs in terminal as well as log file
    -w  | --wait            : Custom timeout for requests invoked by the script (specified in seconds)
        |                       - Default: 15 seconds

Example:
    $ python3 suredone_download.py

    $ python3 suredone_download.py -f [config.yaml]
    $ python3 suredone_download.py -file [config.yaml]

    $ python3 suredone_download.py -f [config.yaml] -o [output.csv]
    $ python3 suredone_download.py -file [config.yaml] --output_file [output.csv]

    $ python3 suredone_download.py -f [config.yaml] -o [output.csv] -v -p
    $ python3 suredone_download.py -file [config.yaml] --output_file [output.csv] --verbose --preserve
"""

# Imports
import sys
import os
import getopt
import platform
import requests
import yaml
import json
import pandas as pd
import re
import time
import inspect
import traceback
from os.path import expanduser
from datetime import datetime

currentMilliTime = lambda: int(round(time.time() * 1000))

PYTHON_VERSION = float(sys.version[:sys.version.index(' ')-2])

# Time tracking variables
RUN_TIME = currentMilliTime()
START_TIME = datetime.now()

def main(argv):
    localFrame = inspect.currentframe()

    # Parse arguments
    # When verbose argument is added, change the verbose of the logger based on the argument as well
    waitTime, configPath, delimiter, outputFilePath, preserveOldFiles, verbose = parseArgs(argv)

    # Check if python version is 3.5 or higher
    if not PYTHON_VERSION >= 3.5:
        LOGGER.writeLog("Must use Python version 3.5 or higher!", localFrame.f_lineno, severity='code-breaker', data={'code':1})
        exit()
    
    LOGGER.writeLog("SureDone bulk downloader initalized.", localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Wait time: {} seconds.".format(waitTime), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Configurations path: {}.".format(configPath), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Delimiter: {}.".format(delimiter), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Preserve old files: {}.".format(preserveOldFiles), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Verbose: {}.\n".format(verbose), localFrame.f_lineno, severity='normal')

    # Parse configuration
    user, apiToken = loadConfig(configPath)

    LOGGER.writeLog("Configuration read.", localFrame.f_lineno, severity='normal')
    
    # Initialize API handler object
    sureDone = SureDone(user, apiToken, waitTime)

    # Get data to send to the bulk/exports sub module
    data = getDataForExports()

    # Invoke the GET API call to bulk/exports sub module
    exportRequestResponse = sureDone.apicall('get', 'bulk/exports', data)
    
    LOGGER.writeLog("API response recieved.", localFrame.f_lineno, severity='normal')
    
    # If the returning json has a 'result' key with 'success' value...
    if exportRequestResponse['result'] == 'success':
        # Get the file name of the newly exported file
        fileName = exportRequestResponse['export_file']

        # Download and save the file
        downloadExportedFile(fileName, outputFilePath, sureDone, delimiter=delimiter)

        safeExit(outputFilePath, marker='execution-complete')

    # If the returning JSON wasn't successful in the first place, end the code with a generic error.
    else:
        LOGGER.writeLog("Can not export for some reason.", localFrame.f_lineno, severity='code-breaker', data={'code':2, 'response':exportRequestResponse})

def safeExit(downloadPath, marker=''):
    """
    Function that will perform a basic print job at the end of the script.

    Parameters
    ----------
        - downloadPath : str
            Path to the download file that was saved during this script's execution.
        - marker : str
            An identifier of what initiated the function.
            Currently we only have one initiator of this function, could be more later.
    """
    # Read the csv's length
    numRows = len(pd.read_csv(downloadPath))

    # Get ending time
    END_TIME = datetime.now()

    # Get runtime length
    executionTime = currentMilliTime() - RUN_TIME

    # For execution-completed
    if marker == 'execution-complete':
        print("=================================================================")
        print("SCRIPT EXECUTED SUCCESSFULLY")
        print("Starting time: {}".format(START_TIME.strftime("%H:%M:%S")))
        print("Ending time: {}".format(END_TIME.strftime("%H:%M:%S")))
        print("Total execution time: {} milliseconds ({} seconds)".format(executionTime, (executionTime/1000)))
        print("Total records in downloaded file: {}".format(numRows))
        print("=================================================================")

def loadConfig (configPath):
    """
    Function that parses the configuration file and reads user and apiToken variables

    Parameters
    ----------
        - configPath : str
            Path to the configuration file
    
    Returns
    -------
        - user : str
            Username from the configuration file
        - apiToken : str
            Api authentication token from the configuration file
    """
    # Loading configurations
    with open(configPath, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            LOGGER.writeLog("Error while loading YAML.", localFrame.f_lineno, severity='code-breaker', data={'code':3, 'error':exc})
    
    # Try to read the user and api_token from suredone_api set in the settings
    # Print error that the settings weren't found and exit
    try:
        user = config['user']
        apiToken = config['token']
    except KeyError as exc:
        LOGGER.writeLog("Not found user or token in config file.", localFrame.f_lineno, severity='code-breaker', data={'code':3, 'error':exc})
        exit()
    return user, apiToken

def getDefaultDownloadPath(preserve):
    """
    Function to check the operating system and determine the appropriate 
    download path for the export file based on operating system.

    This funciton also purges the whole directory with any previous export files.
    
    Returns
    -------
        - downloadPath : str
            A valid path that points to the diretory where the file should be downloaded
    """
    localFrame = inspect.currentframe()
    # Generate file name
    suffix = datetime.now().strftime('%Y_%m_%d-%H-%M-%S')
    fileName = 'SureDone_Downloads_' + suffix + '.csv'    

    # If the platform is windows, set the download path to the current user's Downloads folder
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        downloadPath = os.path.expandvars(r'%USERPROFILE%')
        downloadPath = os.path.join(downloadPath, 'Downloads')
        if not preserve:
            purge(downloadPath, 'SureDone_')
            LOGGER.writeLog("Purged existing files.", localFrame.f_lineno, severity='normal')
        
        downloadPath = os.path.join(downloadPath, fileName)
        return downloadPath

    # If Linux, set the download path to the $HOME/downloads folder
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        downloadPath = expanduser('~')
        downloadPath = os.path.join(downloadPath, 'downloads')
        if os.path.exists(downloadPath):
            if not preserve:
                purge(downloadPath, 'SureDone_')
                LOGGER.writeLog("Purged existing files.", localFrame.f_lineno, severity='normal')
        else:   # Create the downloads directory
            os.mkdir(downloadPath)
        
        downloadPath = os.path.join(downloadPath, fileName)
        return downloadPath

def getDataForExports():
    """
    Function that prepares the data that will be sent to the bulk/exports sub module.
    
    Returns
    -------
        - data : dict
            Dictionary that contains all the necessary key-value pairs that need to be sent to the Suredone API's bulk/exports sub module.
    """
    # Prepare to send api call. Create the SureDone object and create the data dict
    data = {}
    data['type'] = 'items'
    data['mode'] = 'include'
    # data['fields'] = 'guid,stock,price, msrp,cost,title,condition,brand,media1,weight,fitmentfootnotes, manufacturerpartnumber, otherpartnumber,chaincablepattern, compatibletiresizes,caution, howmanywheelsdoesthisdo,howmanytiresdoesthiscover,ebayid,ebaypaymentprofileid,ebayreturnprofileid,ebayshippingprofileid'
    data['fields'] ='guid,stock,price,msrp,cost,title,longdescription,condition,brand,upc,media1,weight,datesold,totalsold,manufacturerpartnumber,warranty,mpn,ebayid,ebaysku,ebaycatid,ebaystoreid,ebayprice,ebaytitle,ebaystarttime,ebayendtime,ebaysiteid,ebaysubtitle,ebaypaymentprofileid,ebayreturnprofileid,ebayshippingprofileid,ebaybestofferenabled,ebaybestofferminimumprice,ebaybestofferautoacceptprice,ebaybuyitnow,ebayupcnot,ebayskip,amznsku,amznasin,amznprice,amznskip,walmartskip,walmartprice,walmartcategory,walmartdescription,walmartislisted,walmartinprogress,walmartstatus,walmarturl,total_stock'

    # Split the data fields based on ',' and they strip each field of any spaces
    t=list(map(lambda x: x.strip(' '),data['fields'].split(',')))
    seen = set()
    seen_add = seen.add
    field_list = list()

    # Iterate through each field and make sure a duplicate isn't present
    for element in t:
        k = element
        if k not in seen:
            seen_add(k)
            field_list.append(k)

    # Rejoin the fields into a single string, separated by a ','
    data['fields'] = ','.join(field_list)

def downloadExportedFile(fileName, downloadFilePath, sureDone, delimiter=','):
    """
    Fucntion that is invoked once the file is exported and is ready to download.
    Invokes the download stream, reads it and write to the file in the decided download directory.

    Parameters
    ----------
        - fileName : str
            Name of the file that is being saved.
        - downloadPath : str
            Path to the download directory.
        - sureDone : SureDone object
            Object of the SureDone API handler class
    """
    localFrame = inspect.currentframe()
    errorCount=0
    while True:
        # Invoke api call to the same module but with a filename and no data 
        fileDownloadURLResponse = sureDone.apicall('get', 'bulk/exports/' + fileName, {})

        # If the result was successfull...
        if fileDownloadURLResponse['result'] == 'success':
            # Set the path, get the download URL of the file requested, and start a stream to download it
            LOGGER.writeLog("Starting file download.", localFrame.f_lineno, severity='normal')
            downloadStream = requests.get(fileDownloadURLResponse['url'], stream=True)
            
            # Get all the file bytes in the stream and write to the file
            index = 0
            with open(downloadFilePath, 'wb') as downloadedFile:
                for index, chunk in enumerate(downloadStream.iter_content(chunk_size=1024)):
                    if chunk:  # filter out keep-alive new chunks
                        downloadedFile.write(chunk)
            
            # Re open the saved csv and save it back with the desired delimiter
            # As long as the delimiter desired is not ',' becasue the default way of delimiting the csv is via ','
            if delimiter != ',':
                temp = pd.read_csv(downloadFilePath, index_col='id')
                temp.to_csv(downloadFilePath, sep=delimiter)
                
            LOGGER.writeLog("Saved to " + downloadFilePath, localFrame.f_lineno, severity='normal')
            break
        else:
            # If the api call with the file name in the url wasn't successfull
            # Increase the error count and check if error count has crossed 10 or not.
            # More than 10 attempts with errors will end the code
            errorCount += 1
            if errorCount > 10:
                LOGGER.writeLog("Can not download.", localFrame.f_lineno, severity='code-breaker', data={'code':2, 'response':fileDownloadURLResponse})
                # TODO: exit()
                break
            else:
                LOGGER.writeLog('Attempt ' + str(errorCount) + ' ' + str(fileDownloadURLResponse), localFrame.f_lineno, severity='warning')
                time.sleep(30)
                continue

def parseArgs(argv):
    """
    Function that parses the arguments sent from the command line 
    and returns the behavioral variables to the caller.

    Parameters
    ----------
        - argv : str
            Arguments sent through the command line
    
    Returns
    -------
        - waitTime : int
            The time defined in seconds by the user before which the requests must not timeout if a response is not received from the API
            Can be float in order to access millisecond scale
        - configPath : str
            A custom path to the configuration file containing API keys
        - delimiter : str
            A single character that is to be used as the delimiter in the CSVs
        - outputFilePath : str
            A custom path to the location where the file needs to be downloaded. Must contain the file name as well.
        - verbose : bool
        - preserveOldFiles : bool
            A boolean variable that will tell the script to keep or remove older downloaded files in the download path
    """
    # Defining options in for command line arguments
    options = "hw:f:d:o:vp"
    long_options = ["help", "wait=", "file=", 'delimiter=','output=', 'verbose', 'preserve']
    
    # Arguments
    waitTime = 15
    configPath = 'suredone.yaml'
    customConfigPathFoundAndValidated = False
    delimiter = ','    
    outputFilePath = ''
    customOutputPathFoundAndValidated = False
    verbose = False
    preserveOldFiles = False

    # Extracting arguments
    try:
        opts, args = getopt.getopt(argv, options, long_options)
    except getopt.GetoptError:
        # Not logging here since this is a command-line feature and must be printed on console
        print ("Error in arguments!")
        print (HELP_MESSAGE)
        exit()

    for option, value in opts:
        if option == '-h':
            # Turn on verbose, print help message, and exit
            LOGGER.verbose = True
            print (HELP_MESSAGE)
            sys.exit()
        elif option in ("-w", "--wait"):
            waitTime = float(value)
        elif option in ("-f", "--file"):
            configPath = value
            customConfigPathFoundAndValidated = validateConfigPath(configPath)
        elif option in ("-d", "--delimiter"):
            delimiter = value
            delimiter = validateDelimiter(delimiter)
        elif option in ("-o", "--output"):
            outputFilePath = value
            customOutputPathFoundAndValidated = validateDownloadPath(outputFilePath)
        elif option in ("-p", "--preserve"):
            preserveOldFiles = True
        elif option in ("-v", "--verbose"):
            verbose = True
            # Updating logger's behavior based on verbose
            LOGGER.verbose = verbose


    # If custom path to config file wasn't found, search in default locations
    if not customConfigPathFoundAndValidated:
        configPath = getDefaultConfigPath()
    if not customOutputPathFoundAndValidated:
        outputFilePath = getDefaultDownloadPath(preserve=preserveOldFiles)

    return waitTime, configPath, delimiter, outputFilePath, preserveOldFiles, verbose

def validateDownloadPath(path):
    """
    Function that will vlidate the custom download path and load defaul if not found.

    Parameters
    ----------
        - path : str
            The custom download path that needs to be validated
    Returns
    -------
        - path : str
            The same path as input if validated and a default download path if invalidated
    """
    localFrame =  inspect.currentframe()
    if not path.endswith('.csv'):
        LOGGER.writeLog("The download path must define the filename as well with '.csv' extension. Switching to default download location.", localFrame.f_lineno, severity='warning')
        return False
    return True

def validateDelimiter(delimiter):
    """
    Function that validates the delimiter option input by the user.
    Main issues to check for is length and make sure that the chosen delimiter is within a list of acceptable options.

    Parameters
    ----------
        - delimiter : str
            The user-specified delimiter option
    
    Returns
    -------
        - delimiter : str
            The same delimiter if validated and a ',' as a delimiter if not validated.
    """
    localFrame = inspect.currentframe()
    # Account for '\\t' and '\t'
    if delimiter == '\\t':
        delimiter = '\t'
    
    # Check for length
    if len(delimiter) > 1:
        LOGGER.writeLog("Length of the delimiter was greater than one character, switching to default ',' delimiter.", localFrame.f_lineno, severity='warning')
        delimiter = ','
        return delimiter

    # Check that it's within acceptable options
    acceptableDelimiters = [',', '\t', ':', '|', ' ']


    if delimiter not in acceptableDelimiters:
        LOGGER.writeLog("Delimiter was not selected from acceptable options, switching to ',' default delimiter.", localFrame.f_lineno, severity='warning')
        delimiter = ','
        return delimiter
    
    return delimiter

def validateConfigPath(configPath):
    """
    Function to validate the provided config file path.

    Parameters
    ----------
        - configPath : str
            Path to the configuration file
    Returns
    -------
        - validated : bool
            A True or False as a result of the validation of the path
    """
    localFrame = inspect.currentframe()
    # Check extension, must be YAML
    if not configPath.endswith('yaml'):
        LOGGER.writeLog("Configuration file must be .yaml extension.\nLooking for configuration file in default locations.", localFrame.f_lineno, severity='error')
        return False

    # Check if file exists
    if not os.path.exists(configPath):
        LOGGER.writeLog("Specified path to the configuration file is invalid.\nLooking for configuration file in default locations.", localFrame.f_lineno, severity='error')
        return False
    else:
        return True

def getDefaultConfigPath():
    """
    Function to validate the provided config file path.

    Returns
    -------
        - configPath : str
            Path to the configuration file if found in the default locations
    """
    localFrame = inspect.currentframe()
    fileName = 'suredone.yaml'
    # Check in current directory
    directory = os.getcwd()
    configPath = os.path.join(directory, fileName)
    if os.path.exists(configPath):
        return configPath
    
    # Check in alternative locations
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        directory = os.path.expandvars(r'%LOCALAPPDATA%')
        configPath = os.path.join(directory, fileName)
        if os.path.exists(configPath):
            return configPath
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        directory = expanduser('~')
        configPath = os.path.join(directory, fileName)
        if os.path.exists(configPath):
            return configPath
    else:
        LOGGER.writeLog("Platform couldn't be recognized. Are you sure you are running this script on Windows or Ubuntu Linux?", localFrame.f_lineno, severity='code-breaker', data={'code':1})
        exit()

    LOGGER.writeLog("suredone.yaml config file wasn't found in default locations!\nSpecify a path to configuration file using (-f --file) argument.", localFrame.f_lineno, severity='code-breaker', data={'code':1})
    exit()

""" Custom Exceptions that will be caught by the script """
class Logger(object):
    """ The logger class that will handle all outputs, may it be console or log file. """
    def __init__(self, verbose=False):
        self.terminal = sys.stdout
        self.log = open(self.getLogPath(), "a")
        # Write the header row
        self.log.write(' Ind. |LineNo.| Time stamp  : Message')
        self.log.write('\n=====================================\n')
        self.verbose = verbose

    def getLogPath(self):
        """
        Function that will determine the default log file path based on the operating system being used.
        Will also create appropriate directories they aren't present.

        Returns
        -------
            - logFile : fileIO
                File IO for the whole script to log to.
        """
        # Define the file name for logging
        temp = datetime.now().strftime('%Y_%m_%d-%H-%M-%S')
        logFileName = "suredone_download_" + temp + ".log"

        # If the platform is windows, set the log file path to the current user's Downloads/log folder
        if sys.platform == 'win32' or sys.platform == 'win64': # Windows
            logFilePath = os.path.expandvars(r'%USERPROFILE%')
            logFilePath = os.path.join(logFilePath, 'Downloads')
            logFilePath = os.path.join(logFilePath, 'log')
            if os.path.exists(logFilePath):
                return os.path.join(logFilePath, logFileName)
            else:   # Create the log directory
                os.mkdir(logFilePath)
                return os.path.join(logFilePath, logFileName)

        # If Linux, set the download path to the $HOME/downloads folder
        elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
            logFilePath = expanduser('~')
            logFilePath = os.path.join(logFilePath, 'log')
            if os.path.exists(logFilePath):
                return os.path.join(logFilePath, logFileName)
            else:   # Create the log directory
                os.mkdir(logFilePath)
                return os.path.join(logFilePath, logFileName)

    def write(self, message):
        if self.verbose:
            self.terminal.write(message)
            self.terminal.flush()
        self.log.write(message)
    
    def writeLog(self, message, lineNumber, severity='normal', data=None):
        """
        Function that writes out to the log file and console based on verbose.
        The function will change behavior slightly based on severity of the message.

        Parameters
        ----------
            - message : str
                Message to write
            - severity : str
                Defines what the message is related to. Is the message:
                    - [N] : A 'normal' notification
                    - [W] : A 'warning'
                    - [E] : An 'error'
                    - [!] : A 'code-breaker error' (errors that are followed by the script exitting)
            - data : dict
                A dictionary that will contain additional information when a code-breaker error occurs
                Attributes:
                    - code : error code
                        1 : Generic error, only print the message.
                        2 : An API call was not successful. Response object attached.
                        3 : YAML loading error. Error object attached
                    - response : str
                        JSON-like str - the response recieved from the request in conern at the point of error.
                    - error : str
                        String produced by exception if an exception occured
        """
        # Get a timestamp
        timestamp = self.getCurrentTimestamp()

        # Format the message based on severity
        lineNumber = str(lineNumber)
        if severity == 'normal':
            indicator = '[N]'
            toWrite = ' ' + indicator + '  |  ' + lineNumber + '  | ' + timestamp + ': ' + message
        elif severity == 'warning':
            indicator = '[W]'
            toWrite = ' ' + indicator + '  |  ' + lineNumber + '  | ' + timestamp + ': ' + message
        elif severity == 'error':
            indicator = '[X]'
            toWrite = ' ' + indicator + '  |  ' + lineNumber + '  | ' + timestamp + ': ' + message        
        elif severity == 'code-breaker':
            indicator = '[!]'
            toWrite = ' ' + indicator + '  |  ' + lineNumber + '  | ' + timestamp + ': ' + message
            
            if data['code'] == 2: # Response recieved but unsuccessful
                details = '\n[ErrorDetailsStart]\n' + data['response'] + '\n[ErrorDetailsEnd]'
                toWrite = toWrite + details
            elif data['code'] == 3: # YAML loading error
                details = '\n[ErrorDetailsStart]\n' + data['error'] + '\n[ErrorDetailsEnd]'
                toWrite = toWrite + details
        
        # Write out the message
        self.log.write(toWrite + '\n')
        if self.verbose:
            self.terminal.write(message + '\n')
            self.terminal.flush()

    def getCurrentTimestamp(self):
        """
        Simple function that calculates the current time stamp and simply formats it as a string and returns.
        Mainly aimed for logging.

        Returns
        -------
            - timestamp : str
                A formatted string of current time
        """
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def exceptionLogger(self, exctype, value, traceBack):
        """
        A simple printing function that will take place of the sys.excepthook function and print the results to the log instead of the console.

        Parameters
        ----------
            - exctype : object
                Exception type and details
            - Value : str
                The error passed while the exception was raised
            - traceBack : traceback object
                Contains information about the stack trace.
        """
        LOGGER.write('Exception Occured! Details follow below.\n')
        LOGGER.write('Type:{}\n'.format(exctype))
        LOGGER.write('Value:{}\n'.format(value))
        LOGGER.write('Traceback:\n')
        for i in traceback.format_list(traceback.extract_tb(traceBack)):
            LOGGER.write(i)

    def flush(self):
        # This flush method is needed for python 3 compatibility.
        # This handles the flush command by doing nothing.
        # You might want to specify some extra behavior here.
        pass

class LoadingError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class SureDone:
    """ A driver class to manage connection and make requests to the Suredone API """
    def __init__(self, user, api_token, timeout):
        """
        Constructor function. Basically creates a header template for api calls.

        Parameters
        ----------
            - user : str
                User name for API
            - 'api_token' : str
                Auth token provided by the API
        """
        self.timeout = timeout
        self.api_endpoint = 'https://api.suredone.com/v1/'
        self.headers = {}
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['x-auth-integration'] = 'partnername'
        self.headers['x-auth-user'] = user
        self.headers['x-auth-token'] = api_token
    
    def apicall(self, typ, endpoint, data=None):
        """
        Function that will concatenate the intended endpoint with the main URL that
        goes to the Suredone API and initiate the request with the provided data.

        Parameters
        ----------
            - typ : str
                Defines the type of request. (REST functionality)
                Available types:
                    - get
                    - put
                    - post
                    - delete
            - endpoint : str
                Specific module of the API that needs to be called.
            - data : dict
                The data that is meant to be sent in the API request in key-value dict format.
        
        Returns
        -------
            - r : str
                The JSON formatted response data after the request was made
        """
        localFrame = inspect.currentframe()
        # Build url string by concatenating the main url with the sub module
        url = self.api_endpoint + endpoint
        errorCount = 0

        # Main loop
        while True:
            # 3 or more errors break the loop
            if errorCount >= 3:
                break
            try:
                # Invoke the corresponding api call based on the type
                if typ == 'get':
                    resp = requests.get(url, params=data, headers=self.headers, timeout=self.timeout)
                elif typ == 'put':
                    resp = requests.put(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
                elif typ == 'post':
                    resp = requests.post(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
                elif typ == 'delete':
                    resp = requests.delete(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            except requests.exceptions.RequestException as e:
                # Error handling. Increment error counter and sleep for
                # 15 seconds and try again if error was ocurred
                temp = 'HTTP Error {} {} {} {}.'.format(typ, url, data, e) + '\nAttempt ' + str(errorCount)
                LOGGER.writeLog(temp, localFrame.f_lineno, severity='error')
                errorCount += 1
                time.sleep(15)
                continue

            # If the response code is 200 (Which means OK)
            if resp.status_code == requests.codes.ok:
                # Try loading the response in json format
                try:
                    r = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    # Error handling. Increment error counter and raise LoadingError
                    # if the response was OK but data couldn't be read in JSON
                    temp = 'JSONDecodeError Error ' + typ + ' ' + url + ' ' + data + "\n" + resp.text
                    LOGGER.writeLog(temp, localFrame.f_lineno, severity='error')
                    errorCount += 1
                    # TODO: remove custom exceptions probably
                    raise LoadingError
                
                # Return the JSON formatted data
                return r
            elif resp.status_code == 401:  # Unauthorized
                # Error handling. Handle for unauthorized error.
                LOGGER.writeLog(json.dumps(self.headers, indent=4), localFrame.f_lineno, severity='error')
                raise UnauthorizedError
            elif resp.status_code == 403:
                try:
                    # Try to load the data in JSON to get more information on error
                    r = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    # Error handling. Increment error counter and sleep for 15 seconds 
                    # and try again if the 403 error couldn't also be decoded to JSON either.
                    LOGGER.writeLog('API json.decoder 403 ' + resp.text, localFrame.f_lineno, severity='error')
                    errorCount += 1
                    time.sleep(15)
                    continue
                try:
                    # If the message tells us that the account has been expired
                    if r['message'] == 'The requested Account has expired.':
                        print('The requested Account has expired.')
                        raise LoadingError
                except KeyError:
                    # Error handling. Increment error counter and sleep for 15 seconds
                    # and try again if r['message'] wasn't present in the response.
                    LOGGER.writeLog('Api not message: 403 ' + resp.text + ' ' + data, localFrame.f_lineno, severity='error')
                    errorCount += 1
                    time.sleep(15)
                    continue
            # ?? TODO: Find out more
            elif resp.status_code == 429:  # X-Rate-Limit-Time-Reset-Ms
                time.sleep(40)
                continue
            # elif resp.status_code == 422:
            #     error_count += 1
            #     print(' Error 422', error_count,resp.status_code, typ, url, data)
            #     print(resp.headers)
            #
            #     print(resp.text)
            #     time.sleep(60)
            #     continue
            else:
                errorCount += 1
                temp = 'Error' + ' ' + errorCount + ' ' + resp.status_code + ' ' + typ + ' ' + url + ' ' + data + '\n' + resp.text
                LOGGER.writeLog(temp, localFrame.f_lineno, severity='error')
                time.sleep(10)
                continue
            break
        # TODO: logxx
        temp = 'Error ' + str(errorCount) + ' ' + typ + ' ' + url + ' ' + data
        LOGGER.writeLog(temp, localFrame.f_lineno, severity='error')
        raise LoadingError

def purge(dir, pattern, inclusive=True):
    """
    A simple function to remove everything within a directory and it's subdirectories if the file name mathces a specific pattern.

    Parameters
    ----------
        - dir : str
            The top level path of the directory from where the searching will begin
        - pattern : regex-like str
            A regex-like string that defines the pattern that needs to be deleted
        - inclusive : boolean
            Currently only has a True implementation
    
    Returns
    -------
        - count : int
            The number files that were removed by the function
    """
    count = 0
    regexObj = re.compile(pattern)
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            if bool(regexObj.search(path)) == bool(inclusive):
                if path.endswith('.csv'):
                    os.remove(path)
                    count += 1
    return count

# Determine log file path
LOGGER = Logger(verbose=False)

if __name__ == "__main__":
    sys.stdout = LOGGER
    sys.excepthook = LOGGER.exceptionLogger
    main(sys.argv[1:])