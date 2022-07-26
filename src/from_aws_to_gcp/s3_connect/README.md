# AWS S3 〜 GCP BigQuery 登録機能

## ■概要
- 機能概要
    - AWSのS3からレポートデータファイルを取得し、GCP側のBigQueryに登録する

---

## ■機能詳細
### 【処理の流れ】
1. トリガーとなるPub/Sub MSGを受け取り、対象日と対象レポートを特定する
    - トピック：**[dev|prd]-s3_connect**
2. AWSのS3から、対象となるレポートのcsvファイルを取得し、GCPのCloudStorageに格納
    - バケット：**[dev|prd]-bucket**
3. CloudStorageに格納されたcsvファイルを取得し、BigQueryに登録する
    - テーブル定義は、本ディレクトリ配下のdocから取得する

---

## ■ディレクトリ構成
下記の形式で記載
```
s3_connect
│
├── config
│   │
│   ├── target_report_list.json     # 対象レポートリスト
│   │
│   └── 各種config設定ファイル 
│
├── doc         
│   │
│   └── bigquery/datalake     # BigQueryのテーブル定義
│
├── mainn.py
│
└── READMEなど
```

---

## ■実行について
- 手動実行
    - target_date
        - 省略時は**前日日付**
    - target_report
        - 省略時は全レポート(target_report_list.jsonに記載のある者)が対象
    ```
    gcloud pubsub topics publish dev-s3_connect --message'{"target_date": "YYYYMMDD", "target_report", "[拡張子抜きの対象ファイル名]"}'
    ```



