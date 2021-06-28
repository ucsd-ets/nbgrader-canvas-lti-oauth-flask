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
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)

    else:
        raise Exception(f'No browser option available for {browser}')

    driver.implicitly_wait(10)

    yield driver
    if not stayopen:
        driver.quit()

@pytest.fixture
def login(driver):
    base_url = 'https://ucsd.test.instructure.com'
    canvas_sso_username = 'testacct111'
    canvas_sso_pw = 'kZChv89xmNbyf3b*'
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

@pytest.fixture
def localhost(login):
    login.find_element_by_css_selector('#DashboardCard_Container > div > div:nth-child(1) > div > div:nth-child(1) > div').click()
    login.find_element_by_css_selector('#section-tabs > li:nth-child(4) > a').click()
    login.find_element_by_css_selector('#context_module_item_903706 > div > div.ig-info > div.module-item-title > span > a').click()
    login.find_element_by_css_selector('#tool_form > div > div.load_tab > div > button').click()
    login.switch_to.window(login.window_handles[-1])
    try:
        print('Attempting to authorize')
        login.find_element_by_css_selector('#oauth2_accept_form > div > input').click()
    except:
        print('Already authorized')
    
    
    assert login.title == 'Nbgrader to Canvas Grading'

    yield login

def test_selenium_is_working(driver):
    """Check this by querying a known endpoint"""
    
    driver.get('https://www.google.com')
    txt = driver.find_element_by_tag_name('body').text
    assert len(txt) > 0

def test_login_gets_driver_logged_in(login):
    logged_in = login.find_element(By.ID, "dashboard_header_container") is not None
    assert logged_in

def test_localhost_gets_driver_to_overview_page(localhost):
    assert localhost.title == 'Nbgrader to Canvas Grading'

def test_create_and_upload_unmatched_assignment(localhost):
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'
    localhost.find_element_by_css_selector('#main-table > tr:nth-child(4) > td:nth-child(4) > input.uploadbtn').click()
    #TODO: make it wait for refresh before checking
    WebDriverWait(localhost, SECONDS_WAIT).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "completed"
        )
    )
    assert localhost.find_element_by_id('Test Assignment 3').text == 'completed'
    
