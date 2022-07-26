#!/bin/bash
env=$1
gcp_project=$2
img_name=$3
tag=$4

# 対象のインスタンス取得(起動中は除く)
gcloud compute instances list --filter="status:TERMINATED and labels.crawler-env:${env}" --format="csv[no-heading](name,zone)" > vm_list.csv

while read vm_info; do
    host_name=`echo ${vm_info} | cut -d , -f 1`
    zone=`echo ${vm_info} | cut -d , -f 2`
    echo "${host_name}, ${zone}: image update"

    gcloud compute instances update-container $host_name --zone $zone	\
        --container-image asia.gcr.io/${gcp_project}/${img_name}:${tag}
done < vm_list.csv
