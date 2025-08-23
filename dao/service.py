from typing import Callable, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from constants.scraping import (
    COOKIE_BUTTON_ID,
    WEBDRIVER_DELAY,
)


# We define the function that allows us to get the class name of a given method
def get_class_that_defined_method(method: Callable) -> str | None:
    qualname = getattr(method, "__qualname__", "")
    if "." in qualname:
        return qualname.rsplit(".", 1)[0]
    return None


class BrowserManager:
    def __init__(self):
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

        # Create the webdriver object and pass the arguments
        options = webdriver.ChromeOptions()

        # Chrome will start in Headless mode
        options.add_argument("headless")

        # Ignores any certificate errors if there is any
        options.add_argument("--ignore-certificate-errors")
        self.wd = webdriver.Chrome()
        self.delay = WEBDRIVER_DELAY

    def quit_driver(self):
        self.wd.quit()

    def open_page(self, url: str) -> None:
        # We load the page at the url 'url'
        self.wd.get(url)
        time.sleep(self.delay)

    def consent_cookies(self) -> None:
        # We search the element in the html content of the current page that have for id the constant COOKIE_BUTTON_ID
        # we click it
        self.wd.find_element(By.ID, COOKIE_BUTTON_ID).click()
        time.sleep(self.delay)

    def get_cdp_log(self) -> dict:
        return self.wd.get_log("performance")

    # We define the function which retrieve the useragent
    def get_user_agent(self) -> str:
        useragent = self.wd.execute_script("return navigator.userAgent")
        return useragent

    # We define the function which retrieve the cookies
    def get_cookies(self) -> dict:
        cookies = self.wd.get_cookies()
        return cookies


def get_tokens(searched_uri: str, logs: dict) -> None | Tuple[str]:
    for log in logs:
        msg = json.loads(log["message"]).get("message", {})
        if msg.get("method") == "Network.requestWillBeSent":
            req = msg.get("params", {}).get("request")
            if not req:
                continue
            if not req.get("url", "").endswith("/pathfinder/v2/query"):
                continue

            headers = req.get("headers", {})
            post_data = req.get("postData")  # camelCase correct
            if not post_data:
                continue

            try:
                post_json = json.loads(post_data)
            except json.JSONDecodeError:
                continue

            uri = post_json.get("variables", {}).get("uri", "")
            if not uri.startswith(searched_uri):
                continue

            client_token = headers.get("client-token")
            access_token = headers.get("authorization")
            hash_value = (
                post_json.get("extensions", {})
                .get("persistedQuery", {})
                .get("sha256Hash")
            )

            if client_token and access_token and hash_value:
                return client_token, access_token, hash_value
    return None
