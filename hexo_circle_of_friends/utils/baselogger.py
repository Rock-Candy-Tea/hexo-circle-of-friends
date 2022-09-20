import logging
import sys
import time
import traceback
from functools import wraps
from logging.config import dictConfig


class ExitHooks(object):
    def __init__(self, logger):
        self.exit_code = None
        self.exception = None
        self.logger = logger

    def hook(self):
        self._orig_exit = sys.exit
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc: BaseException, tb, *args):
        traceback.format_exception(exc_type, exc, tb)
        self.exception = exc

    def excepthook(self, exc_type, exc_value, tb):
        self.logger.error("SYSTEM ERROR", exc_info=(exc_type, exc_value, tb))


def init_logging_conf():
    # 日志日期
    base_conf = {
        # Always 1. Schema versioning may be added in a future release of logging
        "version": 1,
        # "Name of formatter" : {Formatter Config Dict}
        "formatters": {
            # Formatter Name
            "standard": {
                # class is always "logging.Formatter"
                "class": "logging.Formatter",
                # Optional: logging output format
                "format": "%(asctime)s|%(levelname)s|%(process)d|%(name)s|%(message)s",
                # Optional: asctime format
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        # Handlers use the formatter names declared above
        "handlers": {
            # Name of handler
            "console": {
                # The class of logger. A mixture of logging.config.dictConfig() and
                # logger class-specific keyword arguments (kwargs) are passed in here.
                "class": "logging.StreamHandler",
                # This is the formatter name declared above
                "formatter": "standard",
                "level": "INFO",
                # The default is stderr
                "stream": "ext://sys.stdout"
            },
            # Same as the StreamHandler example above, but with different
            # handler-specific kwargs.

        },
        # Loggers use the handler names declared above
        "loggers": {

        },
        # Just a standalone kwarg for the root logger
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }
    # linux平台添加文件记录
    if sys.platform == "linux":
        handler_conf = {
            "class": "logging.handlers.RotatingFileHandler",
            'formatter': 'standard',
            'filename': '/tmp/crawler.log',
            'level': 'DEBUG',
            'maxBytes': 4096000,
            'backupCount': 5,
        }
        base_conf["handlers"]["file"] = handler_conf
        base_conf["root"]["handlers"].append("file")
    logging.getLogger('scrapy').propagate = False
    dictConfig(base_conf)


def logger_global_setup(logger):
    # 设置系统全局异常钩子
    exit_hook = ExitHooks(logger)
    exit_hook.hook()
    sys.excepthook = exit_hook.excepthook


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger_global_setup(logger)
    return logger


def cal_run_time(*args, **kwargs):
    """函数运行时间记录日志"""
    logger = kwargs.get('logger', get_logger('default'))

    def run_time(func):
        @wraps(func)
        def cal_print(*args, **kwargs):
            logger.info('{} start. '.format(func.__name__))
            start = time.process_time()
            ret = func(*args, **kwargs)
            end = time.process_time()
            logger.info('\033[1;32mFunc Name: {:<25}Time Used: {:.8f}s\033[0m'.format(func.__name__, end - start))

            return ret

        return cal_print

    return run_time
