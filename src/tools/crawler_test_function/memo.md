- この関数は自動デプロイしないので、下記コマンドでデプロイ必須
- デプロイ時はbinは解凍
    - IP国籍チェック
        - https://www.whtop.com/ja/tools.ip/
        - https://testpage.jp/tool/ip_address_country.php
        - https://www.iphiroba.jp/ip.php
        - https://www.geolocation.com/ja?ip=37.44.218.45#ipresult

```
gcloud functions deploy crawler_test_asia_northeast1 \
          --runtime python38 \
          --entry-point crawler \
          --timeout 300 \
          --source crawler_test_function \
          --trigger-http \
          --memory 512M \
          --allow-unauthenticated \
          --set-env-vars TZ=Asia/Tokyo,CRAWLER_ENV=dev,REGION=asia-northeast1 \
          --region asia-northeast1
```

```
gcloud functions deploy crawler_test_asia_northeast3 \
          --runtime python38 \
          --entry-point crawler \
          --timeout 300 \
          --source crawler_test_function \
          --trigger-http \
          --memory 512M \
          --allow-unauthenticated \
          --set-env-vars TZ=Asia/Tokyo,CRAWLER_ENV=dev,REGION=asia-northeast3  \
          --region asia-northeast3
```

```
gcloud functions deploy crawler_test_asia_east1 \
          --runtime python38 \
          --entry-point crawler \
          --timeout 300 \
          --source crawler_test_function \
          --trigger-http \
          --memory 512M \
          --allow-unauthenticated \
          --set-env-vars TZ=Asia/Tokyo,CRAWLER_ENV=dev,REGION=asia-east1  \
          --region asia-east1
```


```

