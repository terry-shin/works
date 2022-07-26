GCP_PROJECT = 'gcpプロジェクト'
CRAWLER_ADMIN_TOPIC = 'crawler_admin'
CRAWLER_IRREG_TOPIC = 'crawler_irreg'
DATA_SET = 'data_set'

TOPIC_LIST = {
    "A": {
        "hourly": "crawler_admin",
        "daily": "crawler_irreg"
    },
    "B": {
        "hourly": "ranking_crawler_admin",
        "daily": "ranking_crawler_irreg"
    }
}

TOPIC_MAPPING = {
    "amazon_category_rank": "B"
}
