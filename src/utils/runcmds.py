import sys
from logging.handlers import RotatingFileHandler
import logging

log = logging.getLogger(__name__)
class RemoveNoise(logging.Filter):
    """removes random messages from logs"""

    def __init__(self, message_type: str, messages: list):
        super().__init__(name=message_type)
        self.messages = messages

    def filter(self, record):
        for msg in self.messages:
            if msg in record.msg:
                return False
        return True

def find_level():
    """defines the verbosity of logging"""

    if len(sys.argv) == 1:
        level = "DEBUG"
    elif sys.argv[1] == "d" or sys.argv[1] == "1" or sys.argv[1] == "debug" or sys.argv[1] == "DEBUG":
        level = "DEBUG"
    elif sys.argv[1] == "i" or sys.argv[1] == "2" or sys.argv[1] == "info" or sys.argv[1] == "INFO":
        level = "INFO"
    elif sys.argv[1] == "w" or sys.argv[1] == "3" or sys.argv[1] == "warn" or sys.argv[1] == "WARN":
        level = "WARNING"
    elif sys.argv[1] == "e" or sys.argv[1] == "4" or sys.argv[1] == "error" or sys.argv[1] == "ERROR":
        level = "ERROR"
    elif sys.argv[1] == "c" or sys.argv[1] == "5" or sys.argv[1] == "critical" or sys.argv[1] == "CRITICAL":
        level = "CRITICAL"
    else:
        log.CRITICAL("no log level found")
        sys.exit("please have a valid log level")

    return level

def startlogging(filename: str):
    """start root logger

    Parameters
    ----------
    filename : `str`
        filename to log to\n
    """

    level = find_level()
    max_bytes = 8 * 1024 * 1024  # 8 MiB
    log_formatter = logging.Formatter(
        '%(asctime)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', '%m-%d %H:%M:%S')

    logging.getLogger('discord').setLevel(logging.INFO)
    logging.getLogger('discord.gateway').addFilter(
        RemoveNoise('discord.gateway', 'shard'))
    logging.getLogger('urllib3.connectionpool').addFilter(
        RemoveNoise('urllib3.connectionpool', 'Starting new HTTPS connection'))
    logging.getLogger('discord.state').addFilter(
        RemoveNoise('discord.state', 'referencing an unknown'))

    logging.getLogger('discord.http').setLevel(logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    handler = RotatingFileHandler(
        filename=filename, encoding='utf-8', mode='a', maxBytes=max_bytes, backupCount=10)
    handler.setFormatter(log_formatter)
    root_logger.addHandler(handler)
    if level == "DEBUG":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
