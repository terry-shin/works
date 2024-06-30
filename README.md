# 公開用 個人開発リポジトリ

## ■ブランチの運用例
環境別のブランチは以下で管理し、**デプロイもそのブランチへのpushで実行**とする
- 本番用
    - master
        - **※※基本的にこれにマージされるのはreleaseブランチのみ※※**
        - **マージ時:要ダブルチェック**
- 開発用
    - develop
        - **マージ条件 特になし**
- 検証様
    - staging 
        - **現在は環境は未構築**

以下ブランチは用途に応じて作成する

- feature
    - 新しい機能を開発するための開発者用のブランチ
        - **feature/**[jiraのタスク番号や、開発内容がわかる文字列]
            - 例：feature/keword_serach_crawler  
    - リリース後または不要となった時点で削除

- release
    - 次回リリース資材の取りまとめ用ブランチ
        - **release/**[リリース日]
            - 例：release/20210302
    - リリース後または不要となった時点で削除

- hotfix
    - 本番で稼働中バージョンのバグフィックス用ブランチ
        - **hotfix/**[バグ報告チケットの番号など]
            - 例：hotfix/bug12345
    - リリース後または不要となった時点で削除

![git workflow](/doc/image/git_workflow.png)

----

## ■ディレクトリ構成

```
works
│
├── .devcontainer  # vscode用localコンテナ設定Dir
│
├── .github/workflows  # github Actionsディレクトリ
│   │
│   ├── temp                            # 設定ファイルテンプレート格納ディレクトリ 
│   │
│   ├── deploy_[app名・関数名etc].yml   # デプロイ設定ファイル
│   │
│   ├── lint.yml                        # lint設定ファイル
│   │
│   └── unittest_python.yml                    # ユニット設定ファイル
│
├── doc                   # ドキュメントディレクトリ
│
├── src                   # ソースディレクトリ
│   │
│   ├── appまたは関数別ディレクトリ
│   │
│   │
│   └── tools                 # 検証などに使うツール系関数
│       │
│       └── 関数別ディレクトリ
│
└── READMEなど
```

----

## ■基本環境
- python3.8
    - コーディングスタイルはpep8に準拠させる
        - http://pep8-ja.readthedocs.io/ja/latest/
    - コードチェック：flake8

---

## ■ソースコード
- src配下に、関数あるいはアプリ単位でディレクトリを作成する
    - READMEを[テンプレート](/doc/template/temp_README.md)から作成

---
## ■テストコード
- **基本的に開発はテストコードとセットで行う**

### 【共通】
- src配下の各処理または関数毎のディレクトリ単位で管理する
    - テストコードはsrc配下の各ディレクトリに作成する**tests配下**に格納する
- ファイル名は **test_*.py** でつける
    - 関数も **test_[テスト対称の関数名]** で命名する 
- 実行時はtestsのあるディレクトリに移動し、下記コマンドを実行

 ```
# テストコードを全て実行
 $ pytest -v --cov=src
 
# 特定のテストのみ実行
$ pytest  --cov=[テスト対象のディレクトリ ] tests/test_*.py(対称testを指定)

# 以降は必要に応じて指定
# printを出力
--capture=no

# 結果をファイルにアウトプット
--result-log=出力先ファイル

# 網羅できていないコードの割合出力
--cov-report=term-missing
```

### 【main_crawler】
- testディレクトリは、app直下に配置

## ■ローカル開発環境についての覚書
以下が必要そう
- Python interpreter
- Python
- flake8
- Remote - Containers
