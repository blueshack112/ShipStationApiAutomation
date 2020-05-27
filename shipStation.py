#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Suredone Download

@author: Hassan Ahmed
@contact: ahmed.hassan.112.ha@gmail.com
@owner: Patrick Mahoney
@version: 0.0.1

This module is created to use the Suredone API to create a custom CSV of store's 
product and sales records, and get it downloaded
The CSV currently intended to download has the following columns:
    - total_stock
    - TODO: Document this part
    
Usage:
    - TODO: Document this part
    The script is capable of running without any argument provided. All behavorial
    variables will be reset to default.
    
    $ python3 suredone_download.py [options]

Parameters/Options:
    - TODO: Document this part
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
    - TODO: Document this part
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
- TODO: Document this part
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
LOGGER = Logger(verbose=True)

if __name__ == "__main__":
    sys.stdout = LOGGER
    sys.excepthook = LOGGER.exceptionLogger
    main(sys.argv[1:])