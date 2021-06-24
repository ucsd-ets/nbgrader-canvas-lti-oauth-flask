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
    stayopen = pytestconfig.getoption('stayopen')
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
    if not stayopen:
        driver.quit()

@pytest.fixture
def login(driver):
    base_url = os.getenv('CANVAS_BASE_URL')
    canvas_sso_username = os.getenv('CANVAS_SSO_USERNAME')
    canvas_sso_pw = os.getenv('CANVAS_SSO_PASSWORD')

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

def test_selenium_is_working(driver):
    """Check this by querying a known endpoint"""
    
    driver.get('https://www.google.com')
    txt = driver.find_element_by_tag_name('body').text
    assert len(txt) > 0