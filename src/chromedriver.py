import time
from typing import Optional
from webbrowser import Chrome

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def init_browser(headless: Optional[bool] = True) -> Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Opens the browser up in background

    browser = Chrome(options=chrome_options)

    # Agree to google cookies
    browser.get('https://www.google.com/?hl=en')
    time.sleep(0.2)
    agree_button = browser.find_element(By.XPATH, '//div[text()="I agree"]')
    agree_button.click()

    return browser
