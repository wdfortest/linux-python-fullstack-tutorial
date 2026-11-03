"""07 章 lab：Selenium 演示——登录表单交互 + 分类点击导航 + 渲染后源码交接。

目标站点仍是两个练习站（quotes.toscrape.com / books.toscrape.com）。
- quotes 站：真实填写登录表单、点击提交、显式等待错误提示——演示“交互 + 等待”。
- books 站：首页点击分类链接、等待页面跳转、统计图书数——演示“点击导航”。
- 最后把渲染后的 page_source 交给 BeautifulSoup 复用第 03 章的解析技能。

依赖：本机需装有 Chrome（selenium 4.44 自带 Selenium Manager，会自动下载匹配的驱动）。
运行：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/07_selenium_demo.py
"""

import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10  # 显式等待统一超时


def make_driver() -> webdriver.Chrome:
    """无头 Chrome：不弹出窗口，CI 服务器上也能跑。"""
    options = Options()
    options.add_argument("--headless=new")          # Selenium 4 用 new 模式无头
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)        # Selenium Manager 自动匹配驱动


def demo_quotes_login(driver: webdriver.Chrome) -> None:
    """演示 1：quotes 站登录表单——输入、点击、显式等待状态变化。

    练习站接受任意用户名/密码（它存在的意义就是让人练表单交互）。
    我们等待的不是固定秒数，而是“登录成功的状态”：URL 回到首页 + Logout 链接出现。
    """
    print("== 演示 1：quotes.toscrape.com 登录交互 ==")
    driver.get("https://quotes.toscrape.com/login")

    wait = WebDriverWait(driver, TIMEOUT)
    # 显式等待：表单可见再操作。绝对不要用 time.sleep 代替！
    username = wait.until(EC.visibility_of_element_located((By.ID, "username")))
    password = driver.find_element(By.ID, "password")

    username.clear()
    username.send_keys("demo_user")          # 模拟键盘输入
    password.send_keys("demo_password")
    driver.find_element(By.CSS_SELECTOR, "input.btn").click()

    # 等待登录成功的标志：出现指向 /logout 的链接（最多 10s）
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/logout"]')))
    print("  登录后 URL:", driver.current_url)
    print("  页面头部出现:", driver.find_element(By.CSS_SELECTOR, 'a[href="/logout"]').text)


def demo_books_navigation(driver: webdriver.Chrome) -> None:
    """演示 2：books 站首页点击分类 -> 等待跳转 -> 统计图书。

    注意：books 首页右上角的搜索框是装饰品（form 没有 action，
    /search.html 直接 404）——这就是“页面上有控件不代表功能可用，
    自动化前必须先查看真实 HTML”的活教材。
    """
    print("== 演示 2：books.toscrape.com 分类点击导航 ==")
    driver.get("https://books.toscrape.com/")

    wait = WebDriverWait(driver, TIMEOUT)
    # 真实经验：无头 Chrome 在跨页会话后偶发“坐标点击被吞”（事件未到达元素，
    # 页面也无遮挡）。工程做法：先滚动到元素 + 原生点击重试，仍失败则用
    # JS 点击兜底——它把事件直接派发到元素上，绕开输入管线。
    travel_url_ok = False
    for attempt in range(1, 3):
        travel_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Travel"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", travel_link)
        travel_link.click()
        try:
            # URL 包含 travel_2 才算跳转成功——等待的是“状态”，不是固定时长
            WebDriverWait(driver, 5).until(EC.url_contains("travel_2"))
            travel_url_ok = True
            break
        except TimeoutException:
            print(f"  第 {attempt} 次原生点击未跳转（URL: {driver.current_url}），重试")
    if not travel_url_ok:
        travel_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Travel")))
        driver.execute_script("arguments[0].click();", travel_link)
        wait.until(EC.url_contains("travel_2"))

    books = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.product_pod h3 a"))
    )
    print("  跳转后 URL:", driver.current_url)
    print("  Travel 分类图书数:", len(books))
    print("  第一本书:", books[0].get_attribute("title"))
    print("  第二本书:", books[1].get_attribute("title"))


def demo_rendered_source_handoff(driver: webdriver.Chrome) -> None:
    """演示 3：把渲染后的 HTML 交给 BeautifulSoup 复用第 03 章技能。"""
    print("== 演示 3：渲染后源码 -> BeautifulSoup ==")
    driver.get("https://quotes.toscrape.com/js/")
    wait = WebDriverWait(driver, TIMEOUT)
    # /js/ 页面由 JavaScript 拼装内容，requests 拿到的是空壳，
    # 等到第一条名言出现才说明渲染完成
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.quote")))

    soup = BeautifulSoup(driver.page_source, "lxml")
    quotes = soup.select("div.quote span.text")
    authors = soup.select("div.quote small.author")
    print("  /js/ 页渲染后可解析的名言数:", len(quotes))
    print("  第一条:", quotes[0].get_text(strip=True)[:40], "...")
    print("  第一位作者:", authors[0].get_text(strip=True))


def main() -> None:
    start = time.time()
    driver = make_driver()
    try:
        demo_quotes_login(driver)
        print()
        demo_books_navigation(driver)
        print()
        demo_rendered_source_handoff(driver)
    finally:
        driver.quit()  # 必须退出，否则 Chrome 进程残留
        print(f"\n总耗时 {time.time() - start:.1f}s（含 3 次页面加载）")


if __name__ == "__main__":
    main()
