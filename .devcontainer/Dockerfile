# local開発用Dockerfile
FROM python:3.8-slim-buster
USER root

SHELL ["/bin/bash", "-c"]

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

RUN apt -y install -y --no-install-recommends git vim wget gnupg cron procps
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get -y install google-chrome-stable 


# 必要なPythonパッケージを記載(都度編集)
RUN python -m pip install --upgrade pip && pip install \
    flake8 \
    pytest \
    pytest-cov
ADD .devcontainer/requirements.txt /tmp/
RUN pip install --upgrade -r /tmp/requirements.txt
