import argparse
import getpass
import os
import sys
import time
from typing import List, Tuple, TypeAlias

from dotenv import load_dotenv

Locator: TypeAlias = tuple[str, str]


def L(by: str, value: str) -> Locator:
    return (by, value)


from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# webdriver-manager（未インストールでもOK。ある場合はこちらを優先）
USE_WDM = True
try:
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    USE_WDM = False

load_dotenv(os.path.join(os.path.expanduser("~"), "WANSTAGE", ".env"))

NOTE_EMAIL = os.getenv("NOTE_EMAIL", "")
NOTE_PASSWORD = os.getenv("NOTE_PASSWORD", "")
CHROME_BINARY = os.getenv(
    "CHROME_BINARY", ""
)  # 例: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "")  # 例: /opt/homebrew/bin/chromedriver


def _driver(headless: bool):
    opts = Options()
    if CHROME_BINARY:
        opts.binary_location = CHROME_BINARY
    # 安定化
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=ja-JP")
    if headless:
        opts.add_argument("--headless=new")

    if USE_WDM:
        service = Service(ChromeDriverManager().install())
    else:
        service = Service(CHROMEDRIVER_PATH or "/opt/homebrew/bin/chromedriver")

    return webdriver.Chrome(service=service, options=opts)


def find_first(drv, candidates: List[Tuple[By, str]], timeout=10):
    last_err = None
    for by, sel in candidates:
        try:
            return WebDriverWait(drv, timeout).until(EC.presence_of_element_located((by, sel)))
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    raise NoSuchElementException("no candidates matched")


def login(drv, email: str, password: str):
    drv.get("https://note.com/login")
    # 入力欄候補（UI変更に備え複数）
    email_box = find_first(
        drv,
        [
            (str(By.CSS_SELECTOR), 'input[type="email"]'),
            (str(By.CSS_SELECTOR), 'input[name="login[email]"]'),
            (str(By.CSS_SELECTOR), 'input[name="email"]'),
        ],
        timeout=20,
    )
    email_box.clear()
    email_box.send_keys(email)

    pwd_box = find_first(
        drv,
        [
            (str(By.CSS_SELECTOR), 'input[type="password"]'),
            (str(By.CSS_SELECTOR), 'input[name="login[password]"]'),
            (str(By.CSS_SELECTOR), 'input[name="password"]'),
        ],
    )
    pwd_box.clear()
    pwd_box.send_keys(password)
    pwd_box.send_keys(Keys.ENTER)

    # 任意：プロフィールアイコン or 新規作成ボタンが見えるまで待機
    try:
        WebDriverWait(drv, 20).until(
            EC.any_of(
                EC.presence_of_element_located(
                    (str(By.XPATH), "//a[contains(@href,'/notes/new')]")
                ),
                EC.presence_of_element_located((str(By.CSS_SELECTOR), 'img[alt*="icon"]')),
            )
        )
    except TimeoutException:
        pass


def create_draft(drv, title: str, body: str, tags: str = ""):
    drv.get("https://note.com/notes/new")

    # タイトル欄候補
    title_el = find_first(
        drv,
        [
            (str(By.CSS_SELECTOR), 'input[placeholder*="タイトル"]'),
            (str(By.CSS_SELECTOR), 'textarea[placeholder*="タイトル"]'),
            (
                str(By.XPATH),
                '//input[@type="text" and contains(@placeholder,"タイトル")]',
            ),
            (
                str(By.XPATH),
                '//*[@contenteditable="true" and contains(@data-placeholder,"タイトル")]',
            ),
        ],
        timeout=30,
    )
    title_el.click()
    title_el.clear()
    title_el.send_keys(title)

    # 本文エディタ候補（contenteditableのdivなど）
    body_el = find_first(
        drv,
        [
            (str(By.CSS_SELECTOR), 'div[contenteditable="true"]'),
            (str(By.CSS_SELECTOR), '[data-editor-root="true"]'),
            (str(By.CSS_SELECTOR), '[role="textbox"]'),
        ],
    )
    body_el.click()
    # 改行含む本文を1行ずつ送ると安定
    for line in body.splitlines():
        body_el.send_keys(line)
        body_el.send_keys(Keys.SHIFT, Keys.ENTER)  # 段落感を保つ（必要に応じて ENTER に変更）
    body_el.send_keys(Keys.ENTER)

    # タグ（任意）
    if tags.strip():
        # よくあるパターン：タグ入力欄 or 「タグを追加」のinput
        try:
            tag_input = find_first(
                drv,
                [
                    (str(By.XPATH), '//input[contains(@placeholder, "タグ")]'),
                    (str(By.CSS_SELECTOR), 'input[name*="tag"]'),
                    (
                        str(By.XPATH),
                        '//div[contains(text(),"タグ")]/following::input[1]',
                    ),
                ],
                timeout=5,
            )
            tag_input.click()
            tag_input.clear()
            tag_input.send_keys(tags)
            tag_input.send_keys(Keys.ENTER)
            time.sleep(0.5)
        except Exception:
            pass

    # 下書き保存（Cmd+S）
    body_el.send_keys(Keys.COMMAND, "s")
    # 保存インジケータが消える/表示されるまで少し待機
    time.sleep(2)


def publish(drv):
    """公開（UI変更に弱いため、押せなければ例外にせず戻る）"""
    try:
        # 「公開」ボタン候補
        pub_btn = find_first(
            drv,
            [
                (str(By.XPATH), '//button[normalize-space()="公開"]'),
                (str(By.XPATH), '//span[normalize-space()="公開"]/ancestor::button[1]'),
            ],
            timeout=5,
        )
        pub_btn.click()
        # 確認モーダルの「公開」
        confirm = find_first(
            drv,
            [
                (str(By.XPATH), '//button[.//span[normalize-space()="公開"]]'),
                (str(By.XPATH), '//button[normalize-space()="公開"]'),
            ],
            timeout=5,
        )
        confirm.click()
        WebDriverWait(drv, 15).until(EC.url_matches(r"/@.+/n/.+"))
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="note.com 自動投稿（Selenium/Chrome）")
    ap.add_argument("title")
    ap.add_argument("body")
    ap.add_argument("--tags", default="")
    ap.add_argument("--publish", action="store_true", help="公開まで実施（不安定時は下書きのまま）")
    ap.add_argument("--headless", action="store_true", help="ヘッドレスで実行")
    args = ap.parse_args()

    email = NOTE_EMAIL or input("NOTE_EMAIL: ")
    password = NOTE_PASSWORD or getpass.getpass("NOTE_PASSWORD: ")

    drv = _driver(headless=args.headless)
    try:
        login(drv, email, password)
        create_draft(drv, args.title, args.body, args.tags)
        ok = False
        if args.publish:
            ok = publish(drv)
        print({"ok": True, "published": ok})
    finally:
        drv.quit()


if __name__ == "__main__":
    sys.exit(main())
