
phpサーバー構築


apachインストール(phpコマンド先ならいらないかも)
```
yum -y install httpd
```


```
yum -y install php
```


index作る

```
cd /var/www/html

vim index.php


<?php
phpinfo();
?>
```


ファイアウォール設定



httpd 自動起動
```
sudo systemctl enable httpd.service
```

httpd 起動
```
sudo service httpd start
```

証明書ない場合は、httpでアクセスか