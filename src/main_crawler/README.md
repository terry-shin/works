# クロール&スクレイピング機能

## ■概要および前提条件
- url_listにあるURLをクローリングし、htmlファイルをCloudStrageに格納する
    - **※htmlファイル保存停止中**
- クローラーのカスタマイズは極力行わない
    - クローリングするという目的だけを遂行させる
- GCE VMインスタンス内のコンテナ上で稼働する
    - VMインスタンスはクローリング処理の実行前に起動、終了後に停止させる
        - 同一ipからの大量アクセスの回避と、ipを頻繁に付け替えるのが目的
        - 起動コストを最低限に抑える
    - クローラーの起動はcronにて行う。

## ■ディレクトリ構成
[主なディレクトリ構成]
```
works
│
├── app
│   ├── config  # 環境別config 
│   │   │
│   │   ├── [local|dev|prod|common].py    # 各環境用config
│   │   │
│   │   └── setting.py    # 各種設定ファイル読み込み
│   │ 
│   ├── tmp        # 一時ファイル格納用ディレクトリ
│   │ 
│   ├── usrlib     # モジュール群
│   │   │
│   │   ├── rdb    # RDB(CloudSQL)処理 系
│   │   │
│   │   ├── util    # 共通処理 系
│   │   │
│   │   ├── scraping    # スクレイピング処理 系
│   │   │   │
│   │   │   ├── *_scraping.py    # 各種スクレイピング本処理
│   │   │   │
│   │   │   └── *_xpath # 各種スプレイピングxpath設定
│   │   │   
│   │   └── webdriver.py    # webドライバ関連
│   │
│   └── main.py    # クローリング本処理
│
├── doc        # ドキュメント
│   │
│   └── bigquery/*.json # Bigqueryのテーブル定義など
│
├── shell  # config格納ディレクトリ
│   │ 
│   ├── [local|production].crontab   # 各環境用cron設定
│   │ 
│   ├── container_setting.sh    # crawlerコンテナ起動用shell
│   │ 
│   └── execute_crawler.sh      # crawler 実行shell
│
├── ssh  # SSH鍵
│   │ 
│   └── id_rsa.pub                      # 公開鍵
│
├── tool  # ツール格納ディレクトリ
│   │ 
│   └──generate_label_data_sql   # キーワードラベル登録SQL生成
│       │ 
│       ├── generate_label_data_sql.py    # メインスクリプト
│       │ 
│       ├── input    # インプット用ディレクトリ
│       │ 
│       ├── output    # アウトプット用ディレクトリ
│       │ 
│       └── template   # テンプレート用ディレクトリ
│
├── Dockerfile  # デプロイイメージ用Dockerfile
│
├── requirements.txt  #  デプロイイメージ用requirements
│
└── READMEなど
```


## ■ローカル実行
- 検討中


## ■クローラー　各種設定
### 起動するインスタンス
- ブロック対策として、午前(AM)、午後(PM)で起動対象のリージョン(ZONE)を切り替える
    - AM：東京
    - PM：大阪

### クローラー開始時刻
- **shell/container_setting.sh** の**RUN_M**で変更できる

### １インスタンスあたりのクロール回数
- 1回の稼働につき、クロールするURLの最大数を設定
    - **app/config**配下のファイルにて、各環境単位で設定する
        - **CRAWL_COUNT_MAX**は、１回の稼働で処理するMAXのURL数
        - **LOOP_COUNT_MAX**は、1回の稼働で処理するpub/subのMSG数
            - pub/subのMSGは、urlリストとurl単体の２種類ある為、URL数とは別に判定

### クロール時の待機時間
- クロール対象URLにアクセスした後、一定範囲のランダム秒数待機
    - **app/main.py**の **time.sleep(random.randint([最小], [最大]))** で設定

---

## ■クロール対象管理
### クローラー設定
- Cloud Strageに以下の構成で格納する
    - 最下層のcsvにクロール対象urlを記載する
```
[dev|prd]-crawler-setting-bucket
│
├── [クロール設定文字列 A]
│   └── url_list
│       ├── hourly
│       │   ├── url_list.csv
│       │   (略)
│       │ 
│       └── daily
│           ├── url_list.csv
│           (略)
│
├── [クロール設定文字列 B]
(略)
```

### クロール対象
- クロール対象はPub/Subのメッセージで管理する。処理スパン毎にTOPICを分ける
    - インスタンスにCRAWLER_TYPEが未設定か「A」の場合、以下のTOPICからクロール対象取得
        - **[dev|prd]-crawler_admin-sub**
            - 1時間単位でのクロール対象
            - メッセージの有効期間は**45分**
        - **[dev|prd]-crawler_irreg-sub**
            - 日次などでのクロール対象
            - メッセージの有効期間は**5時間**
    - インスタンスにCRAWLER_TYPEが「B」の場合、以下のTOPICからクロール対象取得
        - こちらで処理する場合は、「crawler_setup_function/config/common.py 」のTOPIC_MAPPINGに対象のクロール設定を追加
        - **[dev|prd]-ranking_crawler_admin-sub**
            - 1時間単位でのクロール対象
            - メッセージの有効期間は**45分**
        - **[dev|prd]-ranking_crawler_irreg-sub**
            - 日次などでのクロール対象
            - メッセージの有効期間は**5時間**
- **[dev|prd]-crawler_setup_function** をCloudScheduler→Pub/Subで起動する
    - メッセージの設定項目
        - mode：hourly or daily
        - clawler_setting：クロール設定文字列


---

## ■デプロイについて
デプロイ対象は以下の２つ

### コンテナイメージ
- 以下が更新されたら、要デプロイ
    - Dockerfile
    - shellディレクトリ配下
    - sshディレクトリ配下
        - SSH鍵

#### 【デプロイ】
- 対象ファイル更新時、当該ブランチをデプロイ環境に応じたブランチ **[develop | master]** へpush(marge)。
    - **.github/workflows** のデプロイ設定(deploy_main_crawler.yml)の内容でbuild　〜　対象インスタンスのデプロイ対象コンテナ設定の更新が実行される
        - イメージは「Container Registry」にpushされる

### ソースコード
- appディレクトリ配下が更新されたら要デプロイ
- git pullによるソースコード更新によるデプロイを行う

#### 【SSH鍵認証の準備】
- [SSH キーペアを作成する](https://choppydays.com/ssh-keygen-heteml/)  
- 秘密鍵の内容をgithubの **「Deploy Keys」** に登録する
- 秘密鍵の内容をgithubの **「Cecrets」** に登録する
    - github Actionsで、秘密鍵をコンテナイメージへコピーする用に設定
- 公開鍵(id_rsa.pub)を本ディレクトリの **「sshディレクトリ」** に配置

※キーペアを差し替える場合は、当手順を必ず実施する

#### 【デプロイ】
- 対象ファイル更新時、当該ブランチをデプロイ環境に応じたブランチ **[develop | master]** へpush(marge)
    - 対象環境のインスタンス起動時にgit pullが実行され、最新の内容に反映される
    - タグを指定する場合は**インスタンスのコンテナ環境変数に「RELEASE_TAG」を追加し、デプロイ対象のタグを指定**する。
- 開発環境で修正しながら検証したい場合は、対象インスタンスおよびコンテナにsshし、gitコマンドで対象のブランチを持ってくる

