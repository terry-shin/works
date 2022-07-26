#!/bin/bash
/usr/local/bin/python /usr/local/src/works/src/main_crawler/app/main.py >> /var/log/cron.log 2>&1 && \
    gcloud compute instances stop $HOST_NAME --zone=$VM_ZONE
