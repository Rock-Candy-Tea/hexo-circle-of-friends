import sys
import logging
from logging import handlers


def get_logger():
    # 日志记录配置
    if sys.platform == "linux":
        # linux，输出到文件
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.WARNING)
        handler = handlers.RotatingFileHandler("/tmp/crawler.log", mode="w", maxBytes=1024, backupCount=3,encoding="utf-8")
        logger.addHandler(handler)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
    else:
        # 其它平台，标准输出
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler(sys.stderr)
        logger.addHandler(handler)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
    return logger
