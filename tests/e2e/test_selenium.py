from json import load
from canvasapi import Canvas
import time
from attr import s
import pytest
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

import os

SECONDS_WAIT = 30

def clear_grades(course):
    users = course.get_recent_students()
    clear_grades = {user.id: {'posted_grade':''} for user in users}
    for assignment in course.get_assignments_for_group(92059):
        if assignment.published:
            try:
                progress = assignment.submissions_bulk_update(grade_data=clear_grades)
                timeout = time.time()+10
                while not progress.workflow_state == 'completed' and timeout > time.time():
                    progress = progress.query()
                    time.sleep(.2)
                    if progress.workflow_state == 'failed':
                        print('failed')
                        break
                print(assignment.name, progress.workflow_state)
                print(progress.url)
            except:
                print(assignment.name)
                print(progress.url)


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
        curs.execute("DELETE FROM assignment_status;")
    conn.commit()
    conn.close()


    # remove canvas classes

    for assignment in course.get_assignments_for_group(92059):
        if not 'Week' in assignment.name:
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
        EC.presence_of_element_located(
            (By.ID, "ssousername"))
    )
    driver.find_element(By.ID, "ssousername").send_keys(canvas_sso_username)
    driver.find_element(By.ID, "ssopassword").click()
    driver.find_element(By.ID, "ssopassword").send_keys(canvas_sso_pw)

    driver.find_element(By.NAME, "_eventId_proceed").click()
    WebDriverWait(driver, SECONDS_WAIT).until(
        EC.visibility_of_element_located(
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
# Check this by querying a known endpoint
def test_selenium_is_working(driver):
    driver.get('https://www.google.com')
    txt = driver.find_element_by_tag_name('body').text
    assert len(txt) > 0

# Tests that driver can login to testacct111
def test_login_gets_driver_logged_in(login):
    logged_in = login.find_element(By.ID, "dashboard_header_container") is not None
    assert logged_in

# Tests that driver opens up the program properly
def test_localhost_gets_driver_to_overview_page(localhost):
    assert localhost.title == 'Nbgrader to Canvas Grading'

# Tests that you can upload an assignment using the create canvas assignment feature
def test_create_and_upload_unmatched_assignment(localhost, course):
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'
    localhost.find_element_by_id('submit_Test Assignment 3').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "Uploaded"
        )
    )
    assert localhost.find_element_by_id('Test Assignment 3').text == 'Uploaded'
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

# Tests uploading to assignment with different name
def test_upload_assignment_to_different_name(localhost, course):
    assert localhost.find_element_by_id('assign1').text == 'No match found'
    clear_grades(course)
    localhost.find_element_by_id('select_assign1').click() #open dropdown
    localhost.find_element_by_xpath('//*[@id="select_assign1"]/option[4]').click()   #select week 3: assignment
    localhost.find_element_by_id('submit_assign1').click()   #click upload grades
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )
    assert localhost.find_element_by_id('assign1').text == 'Uploaded'
    time.sleep(2)
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

# Tests uploading 4 assignments at once
def test_multiple_uploads(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    localhost.find_element_by_id('submit_Test Assignment 1').click()
    localhost.find_element_by_id('submit_Test Assignment 2').click()
    localhost.find_element_by_id('submit_Test Assignment 3').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "Fetching Students"
        )
    )
    time.sleep(2)
    assert localhost.find_element_by_id('assign1').get_attribute("class") == 'orangeText'
    assert localhost.find_element_by_id('Test Assignment 1').get_attribute("class") == 'orangeText'
    assert localhost.find_element_by_id('Test Assignment 2').get_attribute("class") == 'orangeText'
    assert localhost.find_element_by_id('Test Assignment 3').get_attribute("class") == 'orangeText'
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 1"), "Uploaded"
        )
    )
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 2"), "Uploaded"
        )
    )
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "Uploaded"
        )
    )    
    
    assert localhost.find_element_by_id('assign1').text == 'Uploaded'
    assert localhost.find_element_by_id('Test Assignment 1').text == 'Uploaded'
    assert localhost.find_element_by_id('Test Assignment 2').text == 'Uploaded'
    assert localhost.find_element_by_id('Test Assignment 3').text == 'Uploaded'

# Tests deleting an assignment through Canvas will remove corresponding Status and Match
def test_delete_assignment_updates_db(localhost):
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'
    localhost.find_element_by_id('submit_Test Assignment 3').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 3"), "Uploaded"
        )
    )
    time.sleep(1)
    assign_id = localhost.find_element_by_id('select_Test Assignment 3').get_attribute("value")
    localhost.switch_to.window(localhost.window_handles[0])
    localhost.find_element_by_xpath('//*[@id="section-tabs"]/li[5]/a').click()
    time.sleep(2)
    localhost.find_element_by_xpath('//*[@id="element_toggler_0"]/div/button/i').click()
    localhost.find_element_by_xpath('//*[@id="assign_'+assign_id+'_manage_link"]').click()
    localhost.find_element_by_id('assignment_'+assign_id+'_settings_delete_item').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(EC.alert_is_present())
    localhost.switch_to.alert.accept()
    localhost.switch_to.window(localhost.window_handles[1])
    localhost.refresh()
    time.sleep(3)
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'

# Test that the expected Nbgrader assignments are being displayed
def test_correct_number_of_assignments(localhost):
    assert localhost.find_element_by_id('assign1').text == 'No match found'
    assert localhost.find_element_by_id('Test Assignment 1').text == 'No match found'
    assert localhost.find_element_by_id('Test Assignment 2').text == 'No match found'
    assert localhost.find_element_by_id('Test Assignment 3').text == 'No match found'
    
# Tests that the correct buttons disable during uploads
def test_upload_button_disables_during_upload(localhost):
    submit = localhost.find_element_by_id('submit_assign1')
    submit.click()
    assert submit.get_attribute("disabled") == 'true'

# Tests that correct dropdowns disable during uploads
def test_dropdown_disables_during_upload(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    assert localhost.find_element_by_id('select_assign1').get_attribute("disabled") == 'true'

# Tests uploading nbgrader assignments to canvas assignments that share a name with a different Nbgrader assignment
def test_assignments_to_each_others_names(localhost, course):
    assignment_groups = course.get_assignment_groups()
    group = None
    for ag in assignment_groups:
        if (ag.name == "Assignments"):
            group= ag.id
    course.create_assignment({'name':'Test Assignment 1', 'published':'true', 'assignment_group_id':group})
    course.create_assignment({'name':'assign1', 'published':'true', 'assignment_group_id':group})
    localhost.refresh()
    time.sleep(2)
    localhost.find_element_by_id('select_assign1').click() #open dropdown
    localhost.find_element_by_xpath('//*[@id="select_assign1"]/option[7]').click()   #select Test Assignment 1
    localhost.find_element_by_id('submit_assign1').click()   #click upload grades
    localhost.find_element_by_id('select_Test Assignment 1').click() #open dropdown
    localhost.find_element_by_xpath('//*[@id="select_Test Assignment 1"]/option[7]').click()   #select assign1
    localhost.find_element_by_id('submit_Test Assignment 1').click()   #click upload grades
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "Test Assignment 1"), "Uploaded"
        )
    )
    assignments = course.get_assignments()
    for assignment in assignments:
        if assignment.name == 'Test Assignment 1':
            submission = assignment.get_submission(114262)
            assert submission.score == 6.0
        elif assignment.name == 'assign1':
            submission = assignment.get_submission(114262)
            assert submission.score == 2.0

# Tests that the correct name persists upon refreshing during upload
def test_different_name_persists_during_upload(localhost, course):
    assignment_groups = course.get_assignment_groups()
    group = None
    for ag in assignment_groups:
        if (ag.name == "Assignments"):
            group= ag.id
    course.create_assignment({'name':'Test Assignment 1', 'published':'true', 'assignment_group_id':group})
    localhost.refresh()
    time.sleep(2)
    localhost.find_element_by_id('select_assign1').click() #open dropdown
    localhost.find_element_by_xpath('//*[@id="select_assign1"]/option[7]').click()   #select Test Assignment 1
    localhost.find_element_by_id('submit_assign1').click()   #click upload grades
    localhost.refresh()
    time.sleep(.4)
    assert localhost.find_element_by_xpath('//*[@id="select_assign1"]/option[1]').text == 'Test Assignment 1'
    
