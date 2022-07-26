import os
import json
from importlib import import_module

# environment
GCP_ENV = os.getenv('GCP_ENV', default='local')

# config
ENV_CONFIG = import_module(f"config.{GCP_ENV}")
CMN_CONFIG = import_module("config.common")

# report list
report_list_json = open("config/target_report_list.json", "r")
REPORT_LIST = json.load(report_list_json)
