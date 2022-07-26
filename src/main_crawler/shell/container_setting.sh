#!/bin/bash
SETTING_ENV="${CRAWLER_ENV:-dev}"
echo $SETTING_ENV

SETTING_TYPE="${CRAWLER_TYPE:-A}"
echo $SETTING_ENV

SETTING_HOST_NAME="${HOSTNAME:-local}"
echo $SETTING_HOST_NAME

SETTING_ZONE="${VM_ZONE:-none}"
echo $SETTING_ZONE

SETTING_NUM="${PROJECT_NUM:-none}"
echo $SETTING_NUM

DEPLOY_TAG="${RELEASE_TAG}"
echo $DEPLOY_TAG

#RUN_M=$((RANDOM%9+1))
RUN_M=0
echo $RUN_M

echo "app update start"
cd /usr/local/src/works/
echo "RELEASE TAG: ${DEPLOY_TAG}"
if [ ! $DEPLOY_TAG = "" ]; then
    echo "checkout ${DEPLOY_TAG}"
    git checkout refs/tags/$DEPLOY_TAG
else
    echo "pull"
    git pull origin
fi
echo "app update end"

if [ ! $SETTING_ENV = "local" ] && [ ! $SETTING_HOST_NAME = "local" ] && [ ! $SETTING_ZONE = "none" ]; then
    CURRENT=$(cd $(dirname $0);pwd)
    echo $CURRENT

    cp $CURRENT/crontab /var/spool/cron/crontabs/root
    sed -i -e "s/__env__/${SETTING_ENV}/g" -e "s/__type__/${SETTING_TYPE}/g" -e "s/__hostname__/${SETTING_HOST_NAME}/g" -e "s/__zone__/${SETTING_ZONE}/g" -e "s/__m__/${RUN_M}/g" -e "s/__projectnum__/${SETTING_NUM}/g"  /var/spool/cron/crontabs/root

    crontab /var/spool/cron/crontabs/root
    /etc/init.d/cron start

    # tail -f /dev/null
fi

/usr/local/src/cloud_sql_proxy -instances=[GCPプロジェクト]:asia-northeast1:[RDB名]=tcp:3306
