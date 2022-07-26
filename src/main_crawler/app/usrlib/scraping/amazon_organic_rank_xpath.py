# キーワード検索結果ページ用xpath設定
pagination_xpath = [
    "//a[@class='s-pagination-item s-pagination-next "
    "s-pagination-button s-pagination-separator']"
]

ranking_xpath_list = [
    "//div[@class='s-main-slot s-result-list "
    "s-search-results sg-row']"
    "/div[@data-asin]"
]

title_xpath_list = [
    ".//div[@class='a-section a-spacing-none a-spacing-top-small s-title-instructions-style']"
    "/h2/a/span",
    ".//div[@class='a-section a-spacing-none a-spacing-top-micro s-title-instructions-style']"
    "/h2/a/span",
    ".//div[@class='a-section a-spacing-none a-spacing-top-small']"
    "/h2/a/span"
]
