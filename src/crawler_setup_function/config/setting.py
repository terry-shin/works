import os
from importlib import import_module

# instance info
CRAWLER_ENV = os.getenv('CRAWLER_ENV', default='local')
print(CRAWLER_ENV)
HOST_NAME = os.getenv('HOST_NAME', default='')
print(HOST_NAME)
VM_ZONE = os.getenv('VM_ZONE', default='')
print(VM_ZONE)

# import config
CMN_CONFIG = import_module("config.common")
ENV_CONFIG = import_module(f"config.{ CRAWLER_ENV }")
