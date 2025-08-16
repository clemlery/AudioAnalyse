from typing import Callable, Tuple
from selenium import webdriver 
from contextlib import contextmanager

# We define the function that allows us to get the class name of a given method
def get_class_that_defined_method(method : Callable) -> str|None:
    qualname = getattr(method, "__qualname__", "")
    if "." in qualname:
        return qualname.rsplit(".", 1)[0]
    return None

# We define the function which retrieve the useragent
def get_user_agent(driver) -> str:
    useragent = driver.execute_script("return navigator.userAgent")
    return useragent

# We define the function which retrieve the cookies
def get_cookies(driver) -> dict:
    cookies = driver.get_cookies()
    return cookies



