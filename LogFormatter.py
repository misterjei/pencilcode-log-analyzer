import os
import sys
import argparse
import glob

import edtech.file as EtFile
import edtech.tools as EtTools

global isDebugging


'''
@summary: Handles command line arguments and determines path(s).
'''
def parseArguments():
    logPath = None
    isDebugging = False

    # handle command line args
    parser = argparse.ArgumentParser(description='A program to build a CSV file from Pencil Code log files.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_help = True
    parser.add_argument('path', help='path of a log file or directory (required)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='display debug information')
    args = parser.parse_args()
    if args.debug:  isDebugging = True
    if args.path: logPath = args.path

    # Path required as parameter
    if not logPath:
        print("Error: no path specified!")
        sys.exit(2)

    # debug program
    if isDebugging:
        print("SYSTEM" + " " + sys.version + "\n")

    return logPath


'''
@summary: Loads and formats logs.

This function will load, format, sort, and return a list of log entries.

Incoming log entry format:
'IPADDRESS USER UID [DD/Mmm/YYYY:HH:MM:SS +####] "REQUEST" STATUS SIZE REFERRER BROWSER'

Outgoing log entry format:
[IPADDRESS, USER, TIME_IN_MS, DOCUMENT, RESOURCE_URL, { QUERY_KV_PAIR* }, STATUS]
'''
def formatFromPath(logPath):
    logEntries = []
    errorEntries = []

    toBeLogged = ['log', 'error', 'load', 'save', 'home']

    # load data and process
    logPaths = glob.glob(logPath)

    if len(logPaths) == 0:
        if not os.path.isfile(logPath) and not os.path.isdir(logPath):
            print("Error: invalid path specified!")
            sys.exit(2)
        logPaths = [logPath]

    # First, follow all directories and add their children to the path set.
    for path in logPaths:
        if os.path.isdir(path):
            print("Adding directory " + path + "...")
            logPaths.extend(EtFile.getFilesRecursive(path))

    # Once directories have been address, go through the individual logs.
    for path in logPaths:
        print("Processing " + path + "...")
        if os.path.isfile(path):
            logFile = EtFile.openFile(path, 'r')

            for line in logFile:
                log_data = EtTools.parse_http_log_line(line)

                if log_data['document'] and log_data['access_time'] and log_data['query'] and log_data['document'][1:log_data['document'][1:].find('/') + 1] in toBeLogged:
                    logEntries.append([log_data['ip_address'], log_data['local_user'], log_data['access_time'],
                        log_data['document'], log_data['resource_url'], log_data['query'], log_data['status']])
                else:
                    errorEntries.append(line)

    logEntries = sorted(logEntries)
    return logEntries, errorEntries


'''
@summary: Main module entry point.
'''
def main():
    logPath = parseArguments()
    logEntries, errorEntries = formatFromPath(logPath)
    print("Completed log loading: " + str(len(logEntries)) + " entries total.")

    EtFile.saveJsonFile("logs.json", logEntries)
    EtFile.saveJsonFile("errors.json", errorEntries)


if __name__ == "__main__":
    main()
