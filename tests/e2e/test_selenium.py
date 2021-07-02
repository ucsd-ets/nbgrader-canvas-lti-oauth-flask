from canvasapi import Canvas
import json
from attr import s
import pytest
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

import os

SECONDS_WAIT = 10

@pytest.fixture()
def course():
    payload = {
            'grant_type': 'refresh_token',
            'client_id': '131710000000000203',
            'redirect_uri':'http://localhost:5000/oauthlogin',
            'client_secret': 'jBwYwIHSsUCfHaBnkdN8Ff56o3WpjJfztp5JEe5DUcCKJ6VB7iYZkMTNt1URrTvo',
            'refresh_token': '13171~bngbhxjVx3G7sqnWFC3BFs0r9MgN408enlV3I3uN74pCPpjkQvK2bI3eEcStdPH1'
        }
    response = requests.post(
        'https://ucsd.test.instructure.com/login/oauth2/token',
        data=payload
    )
    canvas = None
    try:
        api_key = response.json()['access_token']
        canvas = Canvas('https://ucsd.test.instructure.com',api_key)
        course = canvas.get_course(20774)
        return course
    except Exception as ex:
        print(response,ex)


@pytest.fixture()
def setup(course):
    # clear AssignmentMatches
    conn = psycopg2.connect(
        host = "localhost",
        database = "test",
        user = "dev",
        password = "mypassword"
    )
    with conn.cursor() as curs:
        curs.execute("DELETE FROM assignment_match;")
    conn.commit()
    conn.close()


    # remove canvas classes

    for assignment in course.get_assignments_for_group(92059):
        if 'Test Assignment' in assignment.name or assignment.name == 'assign1':
            assignment.delete()
        

@pytest.fixture()
def driver(pytestconfig, setup):
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

def test_create_and_upload_unmatched_assignment(localhost, course):
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'
    localhost.find_element_by_css_selector('#main-table > tr:nth-child(4) > td:nth-child(4) > input.uploadbtn').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "completed"
        )
    )
    assert localhost.find_element_by_id('Test Assignment 3').text == 'completed'
    # check gradebook is updated accordingly
    if not course:
        print('Error creating course')
        assert False
    assignments = course.get_assignments()
    for assignment in assignments:
        if assignment.name == 'Test Assignment 3':
            submission = assignment.get_submission(90840)
            assert submission.score == 2.0
            return




def test_upload_assignment_to_different_name(localhost, course):
    assert localhost.find_element_by_id('assign1').text == 'No match found'
    localhost.find_element_by_xpath('//*[@id="main-table"]/tr[1]/td[2]/select').click() #open dropdown
    localhost.find_element_by_xpath('//*[@id="main-table"]/tr[1]/td[2]/select/option[4]').click()   #select week 3: assignment
    localhost.find_element_by_xpath('//*[@id="main-table"]/tr[1]/td[3]/input[1]').click()   #click upload grades
    WebDriverWait(localhost, SECONDS_WAIT).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "assign1"), "completed"
        )
    )
    assert localhost.find_element_by_id('assign1').text == 'completed'
    # check gradebook is updated accordingly
    if not course:
        print('Error creating course')
        assert False
    assignments = course.get_assignments()
    for assignment in assignments:
        if assignment.name == 'Week 3: Assignment':
            submission = assignment.get_submission(114262)
            assert submission.score == 6.0
            return
