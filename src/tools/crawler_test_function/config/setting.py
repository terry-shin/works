import os

from importlib import import_module

# instance info
CRAWLER_ENV = os.getenv('CRAWLER_ENV', default='local')

CMN_CONFIG = import_module("config.common")
ENV_CONFIG = import_module(f"config.{ CRAWLER_ENV }")

