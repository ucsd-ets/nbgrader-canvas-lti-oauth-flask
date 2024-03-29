from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

import pytest
import os
import time
import signal
import psutil


SECONDS_WAIT = 10

import json
import pytest
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import os

SECONDS_WAIT = 10

@pytest.fixture()
def driver(pytestconfig):
    browser = pytestconfig.getoption("browser")
    headless = pytestconfig.getoption('headless')
    # browser = 'firefox'
    # headless = False

    if browser == 'firefox':
        options = webdriver.FirefoxOptions()
        if headless:
            options.headless = True
        driver = webdriver.Firefox(options=options)
    elif browser == 'chrome':
        options = webdriver.ChromeOptions()
        if headless:
            options.headless = True
        driver = webdriver.Chrome(options=options)

    else:
        raise Exception(f'No browser option available for {browser}')

    yield driver

    driver.quit()

@pytest.fixture
def login(driver):
    base_url = os.getenv('CANVAS_BASE_URL')
    canvas_sso_username = os.getenv('CANVAS_SSO_USERNAME')
    canvas_sso_pw = os.getenv('CANVAS_SSO_PASSWORD')
    print(base_url, '\n\n\n\n')
    driver.get(base_url)

    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "ssousername"))
    )
    driver.find_element(By.ID, "ssousername").send_keys(canvas_sso_username)
    driver.find_element(By.ID, "ssopassword").click()
    driver.find_element(By.ID, "ssopassword").send_keys(canvas_sso_pw)

    driver.find_element(By.NAME, "_eventId_proceed").click()
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.visibility_of_element_located(
            (By.ID, "footer"))
    )
    elements = driver.find_elements(By.ID, "application")
    assert len(elements) > 0

    yield driver


def scroll_to_bottom(driver):
    try:

        SCROLL_PAUSE_TIME = 0.5

        # Get scroll height
        last_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        while True:
            # Scroll down to bottom
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script(
                "return document.body.scrollHeight"
            )
            if new_height == last_height:
                break
            last_height = new_height

    except Exception:
        raise