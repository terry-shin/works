# BigQuery　テーブルセット間のデータ連携
## ■ディレクトリ構成
```
worksw
│
├── check_dataset_info    # 取得元データセットとのテーブル差分チェック
│   │
│   └── 省略
│
├── config  #  CloudFunctions用設定ファイル
│   │
│   └── 省略
│
├── doc  #  関連ドキュメント
│   │
│   └── bigquery
│       │
│       └── datalake
│           │
│　　　　　　 ├── 各種テーブルのカラム定義.json
│           │
│           └── 移動先_各種テーブルのカラム定義.json ※取得元と移動先でテーブル定義が違う場合に作成
│
├── sync_report    # BigQuery　テーブルセット間のデータ連携　本処理
│   │
│   └── 省略
│
├── sync_report_setup    # sync_report　起動関数
│   │
│   └── 省略
│
└── README.md

```

## ■概要
- データセットAからBに定期的にデータを移動させる
- データはBigQueryへ格納する

---

## ■新連携：データ提供方式
### [提供方法]
- 取得元のBigQueryテーブルセットに直接クエリを発行する
- 洗い替え方式について
    - バックアップとして移動先の **[dev|prd]_batch_backupデータセットに対象テーブルをコピー**
    - 対象テーブルから指定期間（**指定なしは過去１４日、指定ありの場合はその日付から現在まで**）のデータを削除
    - 取得元の対象テーブルから**2と同じ期間のデータをSELECT → 移動先の対象テーブルにINSERT**
        - テーブルのカラム定義はdocディレクトリ配下のjsonを参照する

---


### 【CloudFunctions】
- BigQuery　テーブルセット間のデータ連携
    - [dev|prd]-sync_report_setup
        - 日次の洗い替え関数起動
        - Cloud Functionsタイムアウト対策:１テーブル=1関数の処理にする
    - [dev|prd]-sync_report
        - 取得元のBigQueryで直接クエリを発行　→　移動先BigQueryのデータセットにINSERTする 
- データセット テーブル差分チェック
    - [dev|prd]-check_dataset_info
        - 月一くらい


### 【Pub/Sub】
- [dev|prd]-sync_report_setup
    - BigQuery　テーブルセット間のデータ連携機能 セットアップ関数 起動トリガー
- [dev|prd]-sync_report
    - BigQuery　テーブルセット間のデータ連携 本処理 起動トリガー


### 【BigQuery】
- 各種テーブル

### 【Cloud Scheduler】
- [dev|prd]-report_export_job
    - 定期実行用


---

### 【新連携 洗い替え方式　データ取り込み 手動実行コマンド】
- target_dateを指定した場合、**その日付を起点として現在の日付までの期間**のデータを洗い替え対象とする。
    - 指定なしの場合は、**過去14日間**を対象とする

```
$ gcloud pubsub topics publish dev-sync_report  --message '{"target_date":"[データ取り込み期間 基準日:YYYmmdd]", "target_report":"対象テーブル名"}'
```
- テーブル追加後の初回
    - テーブル追加後の初回は、名前の頭に「tmp_」をつけた空テーブルを用意
    - 下記のコマンドを実行して、tmpテーブルに初期データを投入する
    - 旧テーブルを別データセット等に退避したのちに削除し、tmpテーブルをtmpなしのテーブル名でコピーする
```
$ gcloud pubsub topics publish dev-sync_report  --message '{"initial_flg":"True", "target_report":"対象レポート名"}'
```


---

## ■対象データ追加および、テーブル定義変更時の対応

###  【データセット テーブル差分チェック】
- **[dev|prd]-check_dataset_info**関数を実行
    - CloudFunctionsのメニューの「テスト実行」で起動
- 以下の４種類のファイルを出力
    - **not_exist_table.json**
        - 移動先側に存在しないテーブルの一覧
    - **diff_[テーブル名].json**
        - 移動先側にないカラムを抽出
    - **[テーブル名].json**
        - BigQueryのテーブル定義
            - 移動先側に存在しないか、カラムに差分があるテーブルを対象に出力
            - 適用対象は、当ディレクトリの **「doc/bigquery/datalake/** に格納しておく
    - **[テーブル名].sql**
        - BigQueryでカラムを追加する為のクエリ
            - カラムに差分のあるテーブルを対象に、以下のSQLを出力
            ```
            ALTER TABLE `[テーブル名]`
            ADD COLUMN [カラム名] [データ型 例:STRING],
            ADD COLUMN test_column STRING
            ```
            - 適用する場合は、BigQueryコンソールからこのファイルのクエリを実行

### 【各種ファイル】
- **config**
    - 新規の場合はtarget_table_list.jsonに対象テーブル名を追加
    ```
    "取り込み先のBigQueryテーブル名"
    ```
- **doc/bigquery/datalake/**
    - 主にBigQueryのテーブルスキーマ定義jsonを格納



