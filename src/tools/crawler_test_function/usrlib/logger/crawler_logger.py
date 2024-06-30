import logging

from logging import getLogger, Formatter
from config.setting import ENV_CONFIG, CMN_CONFIG

# handler_format = Formatter('%(asctime)s - %(name)s:%(funcName)s (%(lineno)d) [%(levelname)s] %(message)s')
handler_format = Formatter('{"date": "%(asctime)s", "severity": "%(levelname)s", "function": "%(name)s:%(funcName)s(%(lineno)d)", "message": "%(message)s"}')

# stream handler設定
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(handler_format)

# 本ファイル用logger crawler_logger周りでの動作確認用
base_logger = getLogger(__name__)
base_logger.setLevel(logging.DEBUG)
base_logger.addHandler(stream_handler)


def get_module_logger(module_name, log_level=''):
    """モジュール単位でのloggerを定義
    Args:
        module_name (str):
            基本的に呼び出し元モジュール名
        log_level (str):
            呼び出し元におけるログの出力レベル
                    "DEBUG","INFO","WARN","ERROR"
    Returns:
        logger: 該当モジュールのlogger
    """
    module_logger = getLogger(module_name)
    if log_level not in CMN_CONFIG.LOG_LEVEL:
        log_level = ENV_CONFIG.LOG_LEVEL

    module_logger.setLevel(CMN_CONFIG.LOG_LEVEL[log_level])
    module_logger.addHandler(stream_handler)

    return module_logger
