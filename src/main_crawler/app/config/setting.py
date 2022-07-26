import os
from importlib import import_module

# instance info
CRAWLER_ENV = os.getenv('CRAWLER_ENV', default='local')
print(CRAWLER_ENV)
HOST_NAME = os.getenv('HOST_NAME', default='')
print(HOST_NAME)
VM_ZONE = os.getenv('VM_ZONE', default='')
print(VM_ZONE)
CRAWLER_TYPE = os.getenv('CRAWLER_TYPE', default='A')
print(CRAWLER_TYPE)

# import config
CMN_CONFIG = import_module("config.common")
ENV_CONFIG = import_module(f"config.{ CRAWLER_ENV }")

# 処理するのをタイプによって分ける
if CRAWLER_TYPE in CMN_CONFIG.SUBSCRIPTION_LIST:
    HOURLY_SUB_PATH = f"{CRAWLER_ENV}-{CMN_CONFIG.SUBSCRIPTION_LIST[CRAWLER_TYPE]['hourly']}"
    IRREG_SUB_PATH = f"{CRAWLER_ENV}-{CMN_CONFIG.SUBSCRIPTION_LIST[CRAWLER_TYPE]['daily']}"
else:
    HOURLY_SUB_PATH = f"{CRAWLER_ENV}-{CMN_CONFIG.SUBSCRIPTION_LIST['A']['hourly']}"
    IRREG_SUB_PATH = f"{CRAWLER_ENV}-{CMN_CONFIG.SUBSCRIPTION_LIST['A']['daily']}"
