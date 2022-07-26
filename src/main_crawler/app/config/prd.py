"""
production用設定
"""
# 20211028までの設定：Amazon比較的安定
# SLEEP_MIN = 25
# SLEEP_MAX = 45

SLEEP_MIN = 10
SLEEP_MAX = 20

LOOP_COUNT_MAX = 80
CRAWLER_END_MIN = 45

# 既定のサイズ未満の場合、ipがブロックされたと判断する。
IP_BLOCKED_HTML_SIZE = 10000
