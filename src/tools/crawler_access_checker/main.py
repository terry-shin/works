import csv

from io import StringIO
from flask import Flask, render_template
from google.cloud import storage

app = Flask(__name__)


def save_access_info(access_ip, save_file):

    strage_client = storage.Client()
    save_bucket = strage_client.bucket("test-bucket")
    blob = save_bucket.blob(f"access_check/{access_ip}.tsv")
    blob.upload_from_string(data=save_file, content_type="text/tab-separated-values")


# リクエスト元の情報を収集する
@app.route('/', methods=['GET', 'POST'])
def web_access(request):

    si = StringIO()
    tsv_writer = csv.writer(si, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
    output_list = {}

    # リクエスト情報収集
    print(request)
    header_str = f"==========ACCESSED IP IS {request.remote_addr}============"
    print(header_str)
    access_ip = request.remote_addr
    tsv_writer.writerow(["IP", access_ip])

    for key, value in request.headers:
        value_str = f"{key} : {value}"
        print(value_str)
        output_list[key] = value
        tsv_writer.writerow([key, value])

    save_access_info(access_ip, si.getvalue())

    # return output_str
    return render_template("index.html", access_ip=access_ip, output_list=output_list)


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=80)
