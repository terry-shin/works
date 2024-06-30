# キーワード検索結果ページ用xpath設定
sponsor_ads_xpath_list = [
    "//div[@class='s-result-list "
    "s-search-results sg-row']"
    "/div[contains(@class,'AdHolder')]",
    "//div[@class='s-main-slot s-result-list "
    "s-search-results sg-row']"
    "/div[contains(@class,'AdHolder')]",
    "//div[@class='s-main-slot s-result-list "
    "s-search-results sg-row']/div[@data-component-type='s-search-result']"
]

sponsor_ads_title_xpath_list = [
    ".//div[@class='a-section a-spacing-none a-spacing-top-small s-title-instructions-style']"
    "/h2/a/span",
    ".//div[@class='a-section a-spacing-none a-spacing-top-small']"
    "/h2/a/span"
]
