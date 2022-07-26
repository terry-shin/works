import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from google.cloud import secretmanager

CRAWLER_ENV = os.environ.get('CRAWLER_ENV', 'local')
PROJECT_NUM = os.environ.get('PROJECT_NUM', 'local')

if CRAWLER_ENV != "local":
    secret_name = f"{CRAWLER_ENV}-db-pass"
    client = secretmanager.SecretManagerServiceClient()
    secret_path = client.secret_version_path(PROJECT_NUM, secret_name, "latest")
    response = client.access_secret_version({"name": secret_path})

    DB_PASS = response.payload.data.decode('UTF-8')
else:
    DB_PASS = "test"


# Cloud SQL設定
connection_name = f"{gcpプロジェクト}:asia-northeast1:{RDB名}"
db_user = "crawler_user"
db_pass = DB_PASS
db_name = "master"
db_ip = "127.0.0.1"
db_port = 3306

DATABASE = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (
    db_user,
    DB_PASS,
    db_ip,
    db_port,
    db_name,
)
print(DATABASE)

ENGINE = create_engine(
  DATABASE,
  encoding='utf-8',
  pool_size=5,
  max_overflow=2,
  pool_timeout=30,
  pool_recycle=1800,
  echo=False
)

# DBに対してORM操作するときに利用
# Sessionを通じて操作を行う
session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
)

# 各modelで利用
# classとDBをMapping
Base = declarative_base()
Base.query = session.query_property()

print("db session:success")
