GCP_PROJECT = 'gcpプロジェクト'
CRAWLER_ADMIN_SUB = 'crawler_admin-sub'
CRAWLER_STOP_TOPIC = 'crawler_stop'
CRAWLER_IRREG_SUB = 'crawler_irreg-sub'

SETTING_BUCKET = "crawler-setting-bucket"
HTML_BUCKET = "scraping-html-bucket"

DATA_SET = 'data_set'

USER_AGEMT = [
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
]

SUBSCRIPTION_LIST = {
    "A": {
        "hourly": "crawler_admin-sub",
        "daily": "crawler_irreg-sub"
    },
    "B": {
        "hourly": "ranking_crawler_admin-sub",
        "daily": "ranking_crawler_irreg-sub"
    }
}
