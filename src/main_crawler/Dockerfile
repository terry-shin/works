# GCPデプロイイメージ用Dockerfile
FROM python:3.8-slim-buster
USER root

SHELL ["/bin/bash", "-c"]

ENV workd_dir /usr/local/src

WORKDIR ${workd_dir}

RUN apt -y update
RUN apt -y upgrade
RUN apt -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm
RUN apt install -y fonts-ipafont

# cron動作時のtz設定
RUN sh -c "echo 'Asia/Tokyo' > /etc/timezone"

RUN apt -y install -y --no-install-recommends git vim wget gnupg cron procps openssh-server curl
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt -y update && \
    apt -y install google-chrome-stable

#Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt -y update && apt -y install google-cloud-sdk

# Cloud SQL Auth Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy && \
    chmod +x cloud_sql_proxy

# Db関連
RUN apt -y install gcc libmariadb-dev mariadb-server

# 必要なPythonパッケージを記載(都度編集)
RUN python -m pip install --upgrade pip && pip install \
    beautifulsoup4
ADD requirements.txt /tmp/
RUN pip install --upgrade -r /tmp/requirements.txt

# デプロイ周り設定
RUN mkdir /root/.ssh
ADD ssh/id_rsa /root/.ssh
ADD ssh/id_rsa.pub /root/.ssh
RUN chmod 0600  /root/.ssh/id_rsa
RUN ssh -o StrictHostKeyChecking=no github.com; exit 0

# git clone & setting shell
ARG branch
RUN git clone -b $branch git@github.com:[gitアカウント]/works.git && \
    cd works && \
    chmod 755 src/main_crawler/shell/container_setting.sh && \
    chmod 755 src/main_crawler/shell/execute_crawler.sh  

ENTRYPOINT ["/usr/local/src/works/src/main_crawler/shell/container_setting.sh"]
