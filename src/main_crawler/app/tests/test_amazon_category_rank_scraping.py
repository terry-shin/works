# テスト実行時のimport用pathを設定(削除不可)
import tests.common.pathappend

import urllib.parse
import pytest

import usrlib.scraping.amazon_category_rank_xpath as amazon_category_rank_xpath
from usrlib.scraping import amazon_category_rank_scraping
from usrlib.webdriver import crawler_webdriver

# テスト用url
target_url = "https://www.amazon.co.jp/gp/bestsellers/beauty/ref=zg_bs_nav_0"


def test_fetch_ranking_products(capsys):
    """
    以下をチェック
    ・スクロールして１ページあたり50位まで取れているか
    """

    # ドライバー立ち上げ
    try:
        driver = crawler_webdriver.setting_webdriver(False)
        driver.get(target_url + "&pg=1")

        result_list = amazon_category_rank_scraping.fetch_ranking_products(
                            driver,
                            amazon_category_rank_xpath
                        )

        print(result_list)
        assert len(result_list) >= 50
        for idx, result_item in enumerate(result_list):
            assert result_item['rank'] == idx + 1
            assert result_item['product_name']
            assert result_item['asin']

    finally:
        driver.close()
        driver.quit()


def test_click_pagenation(capsys):
    """
    以下をチェック
    ・次ページへの遷移ができるか(urlのページ数もチェック)
    """

    target_url = "https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_0"

    # ドライバー立ち上げ
    try:
        driver = crawler_webdriver.setting_webdriver(False)
        driver.get(target_url + "&pg=1")

        result = amazon_category_rank_scraping.click_pagenation(
                            driver,
                        )

        qs = urllib.parse.parse_qs(driver.current_url)

        assert qs['pg'][0] == "2"
        assert result

    finally:
        driver.close()
        driver.quit()


@pytest.mark.parametrize(('first_category', 'second_category', 'url'), [
    ("売れ筋", "おもちゃ", "https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_pg_1?ie=UTF8"),
    ("新着", "ゲーム", "https://www.amazon.co.jp/gp/new-releases/videogames/ref=zg_bsnr_pg_1?ie=UTF8"),
])
def test_get_url_info(first_category, second_category, url):
    result = amazon_category_rank_scraping.get_url_info(
                        url
                    )
    assert result['first_category'] == first_category
    assert result['second_category'] == second_category
