import os
import queue
import sys
import threading
import time
import traceback
import uuid
import json
import inspect
from datetime import datetime

class SoleLog:

    def __init__(self, colouredLog:bool,showTime:bool,logPriority:str = "DEBUG", logSaveFormat:str = "json", logDirPath:str = None,
                 logDirName:str = "myLog",flushInterval:float = 0,maxLogSizeMb:float = 5, showLogInConsole:bool = True,formatJsonLog:bool = False,makeNewLogDir:bool = True):
        """
        Initializes the logger instance with the specified configuration.

        Args:
            colouredLog (bool): Whether to display logs in color for terminal output.
                                When set to `True`, log messages will be color-coded based on the
                                severity level (e.g., INFO will be green, ERROR will be red).
            showTime (bool): Whether to include a timestamp in the log entries.
                             If set to `True`, each log message will include the time
                             it was generated.
            maxLogSizeMb (float, optional): The maximum size of the log file in megabytes.
                                  If the log file exceeds this size, it will be rotated
                                  (archived) and a new file will be created. The default is "5 mb"
            logPriority (str, optional): The minimum log level to record. Log messages with a
                                          priority lower than this value will be ignored.
                                          Options include "CRITICAL", "ERROR", "WARNING",
                                          "INFO", and "DEBUG". The default is "DEBUG",
                                          which logs all messages.
            logSaveFormat (str, optional): The format for saving log messages. It must be
                                            either "json" or "txt". The default is "json",
                                            which provides a structured format for logs.
                                            "txt" will save logs in a simple text format.
            logDirPath (str, optional): The directory path where log files will be saved.
                                         If not provided (`None`), logs will not be saved
                                         to disk, and only the console output will be used.
            logDirName (str, optional): The name of the log directory within `logDirPath`.
                                         This will be used to store log files. The default is "myLog".
            flushInterval (float, optional): The interval (in seconds) at which logs are written
                                             to the file. A lower value ensures logs are written
                                             more frequently. The default is 0 seconds.
            showLogInConsole (bool, optional): Whether to print log messages to the console.
                                                If set to `True`, logs will be printed to the
                                                terminal. The default is `True`.
            formatJsonLog (bool, optional): Whether to format logs as a JSON object with
                                            structured fields. The default is `False`, meaning
                                            logs will be in plain text format.
            makeNewLogDir (bool, optional): Whether to create a new log directory inside the specified `logDirPath`.
                                If set to `True`, a new subdirectory with the name given in `logDirName`
                                will be created under `logDirPath`, allowing for organized log storage.
                                If `False`, logs will be saved directly into the provided `logDirPath`
                                without creating a new folder. The default is `True`.
        Raises:
            FileNotFoundError: If the `logDirPath` is provided and does not exist,
                                this exception will be raised. Ensure that the specified
                                path exists or provide a valid directory.
            ValueError: If the provided `logDirPath` is not a directory or if an invalid
                        `logSaveFormat` is provided (anything other than "json" or "txt"),
                        a `ValueError` will be raised.
            OSError: If there is an issue creating the log files in the specified directory,
                     such as insufficient permissions, an `OSError` will be raised.
        """
        self.__queue = queue.Queue()
        self.__lock = threading.Lock()
        self.__sessions = 1
        self.__logDir = None
        self.__logSaveFormat = logSaveFormat.lower().strip()
        self.__logDirName = logDirName
        self.__makeNewLogDir = makeNewLogDir

        self.logPriority = logPriority.upper()
        self.__formatJsonLogs = formatJsonLog
        self.colouredLog = colouredLog
        self.showTime = showTime
        self.flushInterval = flushInterval
        self.maxLogSize = maxLogSizeMb * 1024 * 1024
        self.showLogInConsole = showLogInConsole
        if self.__formatJsonLogs:
            self.sessionUuid = str(uuid.uuid4())
        if self.__formatJsonLogs:
            self.__sessionLogs = {}
        try:
            if logDirPath is not None:
                self.__logDir = os.path.abspath(logDirPath)
                if not os.path.exists(self.__logDir):
                    try:
                        os.makedirs(self.__logDir)
                    except Exception as pathException:
                        _ = pathException
                        raise ValueError("Please Provide a Valid Path!")
                if not os.path.isdir(self.__logDir):
                    raise ValueError("Please Provide The Path Of a Dir!")
                if self.__makeNewLogDir:
                    self.rootDir = os.path.join(self.__logDir, f"{self.__logDirName}")
                else:
                    self.rootDir = os.path.join(self.__logDir)
                self.__sessionStartTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if self.__logSaveFormat == "json":
                    self.__logFile = os.path.join(self.rootDir, fr"{self.__logDirName}_{self.__sessionStartTime}({self.__sessions}).json")
                    self.__sessions += 1
                elif self.__logSaveFormat == "txt":
                    self.__logFile = os.path.join(self.rootDir, f"{self.__logDirName}_{self.__sessionStartTime}({self.__sessions}).txt")
                    self.__sessions += 1
                else:
                    raise ValueError("Only accepts: 'json' and 'txt' format")
                os.makedirs(self.rootDir, exist_ok=True)
                with open(self.__logFile, "w") as _:
                    pass
        except (FileNotFoundError,OSError,ValueError):
            print(f"{'\033[91m'}{'\033[1m'}Error During Logger Initialization:\n{traceback.format_exc()}{'\033[0m'}")
            sys.exit(1)
        try:
            self.__writer = threading.Thread(target=self.__writeToFile, daemon = True)
            self.__writer.start()
        except (AttributeError, TypeError, RuntimeError, AssertionError, MemoryError, ImportError,
            ModuleNotFoundError, OSError, ValueError, EOFError, IOError, PermissionError,
            BlockingIOError, InterruptedError):
            self.__selfException("An Error Occurred During File Writer Thread Initialization")
            sys.exit(1)

    __LOGGINGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    __LOGS = {
        "STYLEALT": "\033[95m",
        "DEBUG": '\033[94m',
        "INFO": '\033[96m',
        "STYLE": '\033[92m',
        "WARNING": '\033[93m',
        "ERROR": '\033[91m',
        "RESET": '\033[0m',
        "BOLD": '\033[1m',
        "WHITE": '\033[97m',
        "UNDERLINE": '\033[4m',
        'CRITICAL': '\033[91m'
    }

    @staticmethod
    def __getTime():
        """
           Retrieves the current date and time with millisecond precision.

           The returned format is ISO 8601 (YYYY-MM-DD HH:MM:SS.sss).

           Returns:
               str: The current date and time as an ISO 8601 formatted string with
                    millisecond precision.
           """
        return datetime.now().isoformat(sep=' ', timespec='milliseconds')

    def __log(self, logType:str, message, showTime:bool, explicitLogConsole:bool = None):
        """
        Logs a message with a specified log type, optionally including a timestamp,
        and decides whether to display it in the console or save it to a file.

        This internal method is used by all public logging methods (e.g., `info()`, `debug()`, `error()`)
        and handles formatting, log filtering based on priority, writing to disk, and console output.

        Args:
            logType (str): The severity level of the log message. Must be one of:
                           "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL".
            message (Any): The content of the log message. Can be any data type.
            showTime (bool): Whether to include the current timestamp in the log output.
                             Overrides the default instance-level `showTime` setting.
            explicitLogConsole (bool, optional): Whether to force showing the log in the console.
                                                 Overrides the default `showLogInConsole` setting.
                                                 If not provided, the logger uses the instance-level default.

        Returns:
            str or None: Returns the formatted log string **only if** it's meant to be shown in the console;
                         otherwise, returns `None`.

        Notes:
            - **Log Filtering:** This method respects the `logPriority` setting of the logger. If the log's
              severity is lower than the configured priority, it is ignored and not saved or shown.
              For example, if `logPriority="WARNING"`, then "DEBUG" and "INFO" logs will be skipped.
            - **Console Output Rules:**
                - If `explicitLogConsole=True`, the log is returned (and typically printed by caller).
                - If `explicitLogConsole=False`, it is never returned.
                - If `explicitLogConsole=None`, it uses `self.showLogInConsole` to decide.
            - **Log Rotation:** If the current log file exceeds `maxLogSizeMb`, a new log file is created.
            - **File Format Support:** Logs can be saved in either JSON or TXT format depending on settings.
        """

        currentFrame = inspect.currentframe().f_back.f_back
        information = inspect.getframeinfo(currentFrame)

        sepColor = self.__LOGS['STYLEALT']
        callerInfoColor = "\033[37m"

        if showTime is not None:
            if showTime:
                currentTime = SoleLog.__getTime() + ' '
            else:
                currentTime = ''
        else:
            if self.showTime:
                currentTime = SoleLog.__getTime() + ' '
            else:
                currentTime = ''

        if self.colouredLog:
            generatedLog = (f"{self.__LOGS['STYLE']}{currentTime}"
                    f"{self.__LOGS['BOLD']}{sepColor}|{self.__LOGS['RESET']} "
                    f"{self.__LOGS['BOLD']}{self.__LOGS['UNDERLINE'] if logType.upper() == 'CRITICAL' else ''}{self.__LOGS[logType]}{logType:<8}{self.__LOGS['RESET']} "
                    f"{sepColor}{self.__LOGS['BOLD']}|{self.__LOGS['RESET']}"
                    f"{callerInfoColor} {information.filename:<65}{self.__LOGS['STYLEALT']}{self.__LOGS['BOLD']} -> {self.__LOGS['RESET']}"
                    f"{self.__LOGS['INFO']}{information.function:<20}{self.__LOGS['STYLEALT']}{self.__LOGS['BOLD']} -> {self.__LOGS['RESET']}"
                    f"{self.__LOGS['WHITE']}{self.__LOGS['BOLD']}{information.lineno:<5}{self.__LOGS['STYLEALT']} -{self.__LOGS['RESET']}"
                    f"{self.__LOGS[logType]}{self.__LOGS['BOLD']} {self.__LOGS['UNDERLINE'] if logType.upper() == 'CRITICAL' else ''}{message}{self.__LOGS['RESET']}")
        else:
            generatedLog = f"{currentTime}| {logType:<8}| {information.filename:<65}{information.function:<20} -> {information.lineno:<5} - {message}"

        if self.__logDir is None:
            if self.__getPriority(logType) < self.__getPriority(self.logPriority):
                return None
            else:
                return generatedLog
        else:
            if self.__getPriority(logType) < self.__getPriority(self.logPriority):
                generatedLog = None
            currentLog = {
                "Timestamp": currentTime,
                "Level": f"{logType:<8}",
                "Path": f"{information.filename:<65}",
                "Module": f"{information.function:<10}",
                "Line": f"{information.lineno:<5}",
                "Message": message
                }
            try:
                self.__queue.put(currentLog)
            except Exception as queueException:
                _ = queueException
                self.__selfException("An error Occurred in Queue")
                sys.exit(1)

            if self.__formatJsonLogs:
                if self.sessionUuid not in self.__sessionLogs:
                    self.__sessionLogs[self.sessionUuid] = []

            if explicitLogConsole:
                return generatedLog

            elif explicitLogConsole == False and self.showLogInConsole:
                return None

            elif self.showLogInConsole:
                return generatedLog

            else:
                return None

    def __getPriority(self,level):
        """
                Returns the numeric priority of a given log level.

                Args:
                    level (str): The log level to evaluate. Must be one of:
                                 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

                Returns:
                    int: The index of the log level in priority order (lower = less severe).

                Raises:
                    ValueError: If the provided log level is invalid.
                """
        if level.upper() not in self.__LOGGINGLEVELS:
            raise ValueError(f"Invalid log level: '{level}'. Must be one of: {self.__LOGGINGLEVELS}")
        return self.__LOGGINGLEVELS.index(level)

    def __logRotation(self):
        """
            Checks the size of the current log file and performs log rotation if the size exceeds
            the maximum allowed size. A new log file is created, and the session count is incremented.

            This method ensures that log files do not grow indefinitely, and when the log file
            reaches the specified size limit, a new file is created for further logging.

            Returns:
                None: This method does not return any value. It only performs log file rotation.

            Behavior:
                - If the log file size exceeds the specified `maxLogSize`, a new file is created.
                - The new file name includes the current session count and timestamp to ensure uniqueness.
            """
        try:
            with self.__lock:
                if os.path.getsize(self.__logFile) >= self.maxLogSize:
                    if self.__logSaveFormat == "json":
                        self.__logFile = os.path.join(self.rootDir, fr"{self.__logDirName}_{self.__sessionStartTime}({self.__sessions}).json")
                    elif self.__logSaveFormat == "txt":
                        self.__logFile = os.path.join(self.rootDir, fr"{self.__logDirName}_{self.__sessionStartTime}({self.__sessions}).txt")
                    self.__sessions += 1
                    with open(self.__logFile, "w") as _:
                        pass
        except Exception as rotationException:
            _ = rotationException
            # noinspection PyUnboundLocalVariable
            self.__selfException("An Error Occurred in Log rotation")
            sys.exit(1)

    def __writeToFile(self):
        """
            Continuously writes log messages from the queue to a log file.

            This method is intended to run in a background thread. It retrieves log
            entries from an internal queue and writes them to the specified log file
            in either JSON or plain text format, based on the logger configuration.

            Behavior:
                - If `__formatJsonLogs` is True, logs are appended to a session-based
                  dictionary for structured JSON output.
                - If `__logSaveFormat` is "json":
                    - And `__formatJsonLogs` is True: Entire session log is dumped as JSON.
                    - And `__formatJsonLogs` is False: Each log is written as a JSON object per line.
                - If `__logSaveFormat` is "txt": Each log is written in plain text with
                  a timestamp and log level.

            This function also respects `flushInterval` to avoid frequent disk writes,
            and uses a lock to ensure thread-safe file access.

            Returns:
                None
            """
        while True:
            collectedLogs = self.__queue.get()
            if collectedLogs is None:
                break
            try:
                self.__logRotation()
                with self.__lock:
                    if self.__formatJsonLogs:
                        self.__sessionLogs[self.sessionUuid].append(collectedLogs)
                    if self.__logSaveFormat == "json" and self.__formatJsonLogs:
                        with open(self.__logFile, "w", encoding="utf-8") as dumpLogJson:
                            json.dump(self.__sessionLogs, dumpLogJson, indent=2)

                    elif self.__logSaveFormat == "json" and not self.__formatJsonLogs:
                        with open(self.__logFile, "a", encoding="utf-8") as noFormatJson:
                            noFormatJson.write(json.dumps(collectedLogs) + "\n")

                    elif self.__logSaveFormat == "txt":
                            with open(self.__logFile, "a", encoding="utf-8") as dumpLogTxt:
                                dumpLogTxt.write(f"[{collectedLogs['Timestamp']}] -> [{collectedLogs["Level"]:<8}] - {collectedLogs["Message"]}\n")

                time.sleep(self.flushInterval)
            except Exception as fileWriteException:
                _ = fileWriteException
                self.__selfException(f"Error writing logs to file. Logging has failed and no logs were written")
                sys.exit(1)

    def getSessionStartTime(self):
        return self.__sessionStartTime

    def logFilePath(self):
        return self.__logFile

    def exception(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
        Logs an error message along with the full traceback of the current exception.

        This method is designed to be used within an `except` block. It automatically
        captures the stack trace of the most recent exception and includes it in the log.

        Args:
            message (Any): A custom message describing the context of the exception.
            showTime (bool, optional): Whether to include the current date and time
                in the log. Overrides the instance-level `showTime` setting if provided.
            showLogInConsole (bool, optional): Whether to print the log to the console.
                Overrides the instance-level `showLog` setting if provided.

        Returns:
            None

        Example:
            try:
                1 / 0
            except ZeroDivisionError:
                logger.exception("An error occurred while dividing numbers")
        """
        fullmsg = f"{message}\n{traceback.format_exc()}"
        log = self.__log(logType="ERROR", message=fullmsg, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)

    def __selfException(self,msg):
        print(f"{self.__LOGS['ERROR']}{self.__LOGS['BOLD']}{msg}:\n{traceback.format_exc()}{self.__LOGS['RESET']}")

    def close(self):
        """
            Gracefully stops the logging system.

            Signals the background log writing thread to terminate by placing a
            sentinel value (`None`) in the queue, and then waits for the thread to finish.

            Returns:
                None
            """
        self.__queue.put(None)
        self.__writer.join()
        with open(self.__logFile,"r") as checkSize:
            if checkSize.read():
                print(f"\n{self.__LOGS['BOLD']}>>>> {self.__LOGS['STYLE']}Logger shutdown completed successfully.")
                return

        print(f"\n{self.__LOGS['BOLD']}>>>> {self.__LOGS['WARNING']}No Logs in {self.__logFile}. Deleting...{self.__LOGS['RESET']}")
        try:
            os.remove(os.path.join(self.__logDir,self.__logFile))
            print(f"{self.__LOGS['BOLD']}>>>> {self.__LOGS['STYLE']}Logger shutdown completed successfully.{self.__LOGS['RESET']}")
        except Exception as deleteException:
            print(f"{self.__LOGS['BOLD']}>>>> {self.__LOGS['ERROR']}Can't Delete {self.__logFile} But there are No Logs Written!.{deleteException}{self.__LOGS['RESET']}")

    def INFO(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
            Logs an informational message.

            Args:
                message (Any): The content of the log message.
                showTime (bool, optional): Whether to include the current date and time
                    in the log. Overrides the instance-level `showTime` setting if provided.
                showLogInConsole (bool, optional): Whether to print the log to the console.
                    Overrides the instance-level `showLog` setting if provided.

            Returns:
                None
            """
        log = self.__log(logType="INFO", message=message, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)

    def WARNING(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
            Logs a warning message.

            Args:
                message (Any): The content of the log message.
                showTime (bool, optional): Whether to include the current date and time
                    in the log. Overrides the instance-level `showTime` setting if provided.
                showLogInConsole (bool, optional): Whether to print the log to the console.
                    Overrides the instance-level `showLog` setting if provided.

            Returns:
                None
            """
        log = self.__log(logType="WARNING", message=message, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)

    def ERROR(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
            Logs an error message.

            Args:
                message (Any): The content of the log message.
                showTime (bool, optional): Whether to include the current date and time
                    in the log. Overrides the instance-level `showTime` setting if provided.
                showLogInConsole (bool, optional): Whether to print the log to the console.
                    Overrides the instance-level `showLog` setting if provided.

            Returns:
                None
            """
        log = self.__log(logType="ERROR", message=message, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)

    def DEBUG(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
            Logs a debug message.

            Args:
                message (Any): The content of the log message.
                showTime (bool, optional): Whether to include the current date and time
                    in the log. Overrides the instance-level `showTime` setting if provided.
                showLogInConsole (bool, optional): Whether to print the log to the console.
                    Overrides the instance-level `showLog` setting if provided.

            Returns:
                None
            """
        log = self.__log(logType="DEBUG", message=message, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)

    def CRITICAL(self, message, showTime:bool = None, showLogInConsole:bool = None):
        """
        Logs a critical message.

        Args:
            message (Any): The content of the log message.
            showTime (bool, optional): Whether to include the current date and time
                in the log. Overrides the instance-level `showTime` setting if provided.
            showLogInConsole (bool, optional): Whether to print the log to the console.
                Overrides the instance-level `showLog` setting if provided.

        Returns:
            None
        """
        log = self.__log(logType="CRITICAL", message=message, showTime=showTime, explicitLogConsole=showLogInConsole)
        if log is not None:
            print(log)