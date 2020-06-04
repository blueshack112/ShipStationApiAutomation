#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
ShipStation API for Order Automation

@author: Hassan Ahmed
@contact: ahmed.hassan.112.ha@gmail.com
@owner: Patrick Mahoney
@version: 0.0.4

This script is written to automate the orders placed on ShipStation using ShipStation's API
Currently, this script gets a list of all the orders from ShipStation where the order status is "awaiting_shipment".
TODO: Define further functionality after receiving from Patrick 
"""
HELP_MESSAGE = """Usage:
    The script is capable of running without any argument provided. All behavorial
    variables will be reset to default.
    
    $ python3 shipstation.py [options]

Parameters/Options:
    - TODO: Update as the file is scripted more
    -h  | --help            : View usage help and examples
    -f  | --file            : Path to the configuration file containing API keys
        |                       - Default in %APPDATA%/local/shipstation.yaml on Windows
        |                       - Default in $HOME/shipstation.yaml on Linux
    -o  | --output          : Path tothe directory where the output of this script needs to be saved
        |                       - Default in %USERPROFILE%/Downloads/shipstation.json
        |                       - Default in $HOME/downloads//shipstation.json
        |                       - TODO: These defaults are subject to change
    -v  | --verbose         : Show outputs in terminal as well as log file

Example:
    $ python3 shipstation.py

    $ python3 shipstation.py -f [shipstation.yaml]
    $ python3 shipstation.py -file [shipstation.yaml]

    $ python3 shipstation.py -f [shipstation.yaml] -o [Docs/]
    $ python3 shipstation.py -file [shipstation.yaml] --output_file [output.csv]

    $ python3 shipstation.py -f [shipstation.yaml] -o [Docs/] -v
    $ python3 shipstation.py -file [shipstation.yaml] --output_file [Docs/] --verbose
"""
import sys
import os
import getopt
import platform
import requests
import base64
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
    configPath, outputDIRPath, verbose = parseArgs(argv)

    # Check if python version is 3.5 or higher
    if not PYTHON_VERSION >= 3.5:
        LOGGER.writeLog("Must use Python version 3.5 or higher!", localFrame.f_lineno, severity='code-breaker', data={'code':1})
        exit()
    
    LOGGER.writeLog("Shipstation order automation initalized.", localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Configurations path: {}.".format(configPath), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Download path: {}.".format(outputDIRPath), localFrame.f_lineno, severity='normal')
    LOGGER.writeLog("Verbose: {}.\n".format(verbose), localFrame.f_lineno, severity='normal')

    # Get authentication string
    authString = loadConfig(configPath)

    # Make the api call to list all the orders with "awaiting_shipment" order status
    ordersList = listOrders(authString)
    
    # Let's just save for now
    with open(os.path.join(outputDIRPath, 'shipstation.json'), 'w') as f:
        json.dump(ordersList, f, indent=3)

def loadConfig (configPath):
    """
    Function that parses the configuration file and reads user and apiToken variables

    Parameters
    ----------
        - configPath : str
            Path to the configuration file
    
    Returns
    -------
        - authString : str
            API key and API Secret for shipstation account merged and processed to form the stardardized authentication string that will be used during api calls
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
        apiKey = config['api-key']
        apiSecret = config['api-secret']
    except KeyError as exc:
        LOGGER.writeLog("Not found user or token in config file.", localFrame.f_lineno, severity='code-breaker', data={'code':3, 'error':exc})
        exit()
    
    # Pre-process the apiKey and apiSecret to form the authString
    authString = "{}:{}".format(apiKey, apiSecret)
    authString = base64.b64encode(authString.encode('utf-8'))
    authString = "Basic {}".format(str(authString, 'utf-8'))
    return authString

def listOrders(authString, filters={'orderStatus':'awaiting_shipment'}, url="https://ssapi.shipstation.com/orders"):
    """
    This function will prepare the headers as well as params/data and make the api
    call to the ship station orders url.

    Parameters
    ----------
        - authString : str
            The custom download path that needs to be validated
        - filters : dict
            A dictionary that will contain all the filters we want to apply.
        - url
            The endpoint for the api call
    Returns
    -------
        - jsonData : json
            A json element containing all the orders it recieved
    """
    localFrame = inspect.currentframe()
    # Prepare the header
    headers = {
        'Host': 'ssapi.shipstation.com',
        'Authorization': authString
    }
    payload = {}

    # Iterate though filters and add each filter to payload
    for key, value in filters.items():
        payload[key] = value
    
    # Note: Don't delete: data is for posts and params is for gets
    orderRequest = requests.request("GET", url, headers=headers, params=payload)

    # Successful response codes
    if orderRequest.status_code in (200, 201, 204):
        jsonData = json.loads(orderRequest.text)
    else:
        LOGGER.writeLog("The api request produced an unsuccessful status code. Details follow below.", localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("Status code from the reuqest: {}.".format(orderRequest.status_code), localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("Response text: .".format(orderRequest.text), localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("Url: {}.".format(url), localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("Headers: {}.".format(headers), localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("Payload: {}.".format(payload), localFrame.f_lineno, severity='code-breaker', data={'code':1})
        LOGGER.writeLog("*RESPONSE DETAILS END*", localFrame.f_lineno, severity='code-breaker', data={'code':1})

    return jsonData

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
        - configPath : str
            A custom path to the configuration file containing API keys
        - verbose : bool
        - outputDIRPath : str
            Path to the directory where output files are to be saved by this script
    """
    # Defining options in for command line arguments
    options = "hf:o:v"
    long_options = ['help', 'file=', 'output=', 'verbose']
    
    # Arguments
    configPath = 'shipstation.yaml'
    customConfigPathFoundAndValidated = False
    outputDIRPath = ''
    customOutputPathFoundAndValidated = False
    verbose = False

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
        elif option in ("-f", "--file"):
            configPath = value
            customConfigPathFoundAndValidated = validateConfigPath(configPath)
        elif option in ("-o", "--output"):
            outputDIRPath = value
            customOutputPathFoundAndValidated = validateDownloadPath(outputDIRPath)
        elif option in ("-v", "--verbose"):
            verbose = True
            # Updating logger's behavior based on verbose
            LOGGER.verbose = verbose

    # If custom path to config file wasn't found, search in default locations
    if not customConfigPathFoundAndValidated:
        configPath = getDefaultConfigPath()
    if not customOutputPathFoundAndValidated:
        outputDIRPath = getDefaultDownloadPath()

    return configPath, outputDIRPath, verbose

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
    Function to get the degault config file path.
    This function is invoked when the specified configPath has an error.
    Or when the config path is not specified in the command line.

    Returns
    -------
        - configPath : str
            Path to the configuration file if found in the default locations
    """
    localFrame = inspect.currentframe()
    fileName = 'shipstation.yaml'
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

    LOGGER.writeLog("shipstation.yaml config file wasn't found in default locations!\nSpecify a path to configuration file using (-f --file) argument.", localFrame.f_lineno, severity='code-breaker', data={'code':1})
    exit()

def validateDownloadPath(path):
    """
    Function that will vlidate the custom download path and load defaul if not found.

    Parameters
    ----------
        - path : str
            The custom download path that needs to be validated
    Returns
    -------
        - validated : bool
            True of False based on validation of the provided downloadDIRPath
    """
    localFrame =  inspect.currentframe()
    if not os.path.exists(path):
        LOGGER.writeLog("The download path defined does not exist. Make sure that the path is reachable. Switching to default download paths...", localFrame.f_lineno, severity='warning')
        return False
    if not os.path.isdir(path):
        LOGGER.writeLog("The specified download path is a file. Make sure that a directory is specified. Switching to default download paths...", localFrame.f_lineno, severity='warning')
        return False
    return True

def getDefaultDownloadPath():
    """
    Function to check the operating system and determine the appropriate 
    download path for the output files based on operating system.
    
    Returns
    -------
        - downloadPath : str
            A valid path that points to the diretory where the file should be downloaded
    """
    localFrame = inspect.currentframe()
    # No file name in this one for now
    # suffix = datetime.now().strftime('%Y_%m_%d-%H-%M-%S')
    # fileName = 'SureDone_Downloads_' + suffix + '.csv'    

    # If the platform is windows, set the download path to the current user's Downloads folder
    if sys.platform == 'win32' or sys.platform == 'win64': # Windows
        downloadPath = os.path.expandvars(r'%USERPROFILE%')
        downloadPath = os.path.join(downloadPath, 'Downloads')
        return downloadPath
    # If Linux, set the download path to the $HOME/downloads folder
    elif sys.platform == 'linux' or sys.platform == 'linux2': # Linux
        downloadPath = expanduser('~')        
        return downloadPath
    # Unrecognized operating system    
    else:
        LOGGER.writeLog("Platform couldn't be recognized. Are you sure you are running this script on Windows or Ubuntu Linux?", localFrame.f_lineno, severity='code-breaker', data={'code':1})
        exit()

    LOGGER.writeLog("A download directory could not be specified in default locations!\nSpecify a path to the directory using (-o --output) argument.", localFrame.f_lineno, severity='code-breaker', data={'code':1})
    exit()

""" Custom logging class """
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
        logFileName = "shipstation_" + temp + ".log"

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

# Determine log file path
# TODO: Switch to false
LOGGER = Logger(verbose=False)

if __name__ == "__main__":
    sys.stdout = LOGGER
    sys.excepthook = LOGGER.exceptionLogger
    main(sys.argv[1:])