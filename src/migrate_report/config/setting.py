import os
import json
from importlib import import_module

# env & config
GCP_ENV = os.environ.get('GCP_ENV', 'local')
ENV_CONFIG = import_module(f"config.{ GCP_ENV }")
CMN_CONFIG = import_module("config.common")

table_list_json = open("config/target_table_list.json", "r")
TABLE_LIST = json.load(table_list_json)
