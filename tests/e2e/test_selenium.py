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
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By

import os

SECONDS_WAIT = 120

def get_group_id(course):
    for ag in course.get_assignment_groups():
            if (ag.name == "Assignments"):
                return ag.id
    raise Exception('No assignment group named "Assignments"')

def get_group_id(course):
    for ag in course.get_assignment_groups():
            if (ag.name == "Assignments"):
                return ag.id
    raise Exception('No assignment group named "Assignments"')

def clear_grades(course):
    users = course.get_recent_students()
    clear_grades = {user.id: {'posted_grade':''} for user in users}
    group_id = get_group_id(course)
        
    for assignment in course.get_assignments_for_group(group_id):
        if assignment.published:
            try:
                progress = assignment.submissions_bulk_update(grade_data=clear_grades)
                timeout = time.time()+20
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

def get_conn():
    conn = psycopg2.connect(
        host = "postgres-service",
        database = "test",
        user = os.getenv('POSTGRES_USER'),
        password = os.getenv('POSTGRES_PASSWORD')
    )
    return conn
@pytest.fixture()
def course():
    conn = get_conn()
    refresh_token = None
    user_id = 114217
    
    with conn.cursor() as curs:
        curs.execute("SELECT refresh_key FROM users WHERE user_id="+ str(user_id) +";")
        refresh_token = curs.fetchone()
    payload = {
            'grant_type': 'refresh_token',
            'client_id': os.getenv('OAUTH2_ID'),
            'redirect_uri': os.getenv('OAUTH2_URI'),
            'client_secret': os.getenv('OAUTH2_KEY'),
            'refresh_token': refresh_token
        }
    response = requests.post(
        os.getenv('CANVAS_BASE_URL')+'/login/oauth2/token',
        data=payload
    )
    canvas = None
    try:
        api_key = response.json()['access_token']
        canvas = Canvas(os.getenv('CANVAS_BASE_URL'),api_key)
        conn = get_conn()
        with conn.cursor() as curs:
            curs.execute("UPDATE users "+
                        "SET api_key='"+api_key+"' "+
                        "WHERE user_id="+ str(user_id) +";")
        conn.commit()
        conn.close()
        course = canvas.get_course(20774)
        return course
    except Exception as ex:
        print(response,ex)


@pytest.fixture()
def setup(course):
    # clear AssignmentMatches
    conn = get_conn()
    with conn.cursor() as curs:
        curs.execute("DELETE FROM assignment_status;")
    conn.commit()
    conn.close()


    # remove canvas classes

    for assignment in course.get_assignments_for_group(get_group_id(course)):
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
            driver = webdriver.Remote(
                options=options,
                desired_capabilities=webdriver.DesiredCapabilities.FIREFOX,
                command_executor='http://localhost:4444/wd/hub'
            )
    elif browser == 'chrome':
        options = webdriver.ChromeOptions()
        if headless:
            options.headless = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Remote(
                options=options,
                desired_capabilities=webdriver.DesiredCapabilities.CHROME,
                command_executor='http://localhost:4444/wd/hub'
            )

    else:
        raise Exception(f'No browser option available for {browser}')

    driver.implicitly_wait(10)

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
        EC.presence_of_element_located(
            (By.ID, "ssousername"))
    )
    driver.find_element(By.ID, "ssousername").send_keys(canvas_sso_username)
    driver.find_element(By.ID, "ssopassword").send_keys(canvas_sso_pw)

    print(driver.find_element(By.ID, "ssousername").get_attribute("value"))
    print(driver.find_element(By.ID, "ssopassword").get_attribute("value"))
    
    element = driver.find_element(By.XPATH, '//*[@id="login"]/button').click()
    
    WebDriverWait(driver, SECONDS_WAIT).until(
        EC.visibility_of_element_located(
            (By.ID, "footer"))
    )
    elements = driver.find_elements(By.ID, "application")
    assert len(elements) > 0

    yield driver

@pytest.fixture
def localhost(login):
    login.find_element_by_xpath('//*[@id="DashboardCard_Container"]/div/div[1]/div/div[1]/div/a').click()
    login.find_element_by_xpath('//*[@id="section-tabs"]/li[4]/a').click()
    login.find_element_by_xpath('//*[@id="context_module_item_1018581"]/div/div[2]/div[1]/span/a').click()
    login.find_element_by_xpath('//*[@id="tool_form"]/div/div[1]/div/button').click()
    login.switch_to.window(login.window_handles[-1])
    try:
        print('Attempting to authorize')
        login.find_element_by_css_selector('#oauth2_accept_form > div > input').click()
    except:
        print('Already authorized')
    login.refresh()
    time.sleep(3)

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
    assignments = course.get_assignments()
    for assignment in assignments:
        if assignment.name == 'Test Assignment 3':
            submission = assignment.get_submission(141754)
            assert submission.score == 2.0
            return

# Tests uploading to assignment with different name
def test_upload_assignment_to_different_name(localhost, course):
    assert localhost.find_element_by_id('assign1').text == 'No match found'
    clear_grades(course)
    sel = Select(localhost.find_element_by_id('select_assign1'))
    for opt in sel.options:
        if opt.text == 'Week 3: Assignment':
            opt.click()
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
            submission = assignment.get_submission(141753)
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
    # localhost.find_element_by_xpath('//*[@id="element_toggler_0"]/div/button/i').click()
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
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )

# Tests that correct dropdowns disable during uploads
def test_dropdown_disables_during_upload(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    assert localhost.find_element_by_id('select_assign1').get_attribute("disabled") == 'true'
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )

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
    sel = Select(localhost.find_element_by_id('select_assign1'))
    for opt in sel.options:
        if(opt.text == 'Test Assignment 1'):
            opt.click()
    localhost.find_element_by_id('submit_assign1').click()   #click upload grades
    sel = Select(localhost.find_element_by_id('select_Test Assignment 1'))
    for opt in sel.options:
        if(opt.text == 'assign1'):
            opt.click()
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
            submission = assignment.get_submission(141753)
            assert submission.score == 6.0
        elif assignment.name == 'assign1':
            submission = assignment.get_submission(141753)
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
    sel = Select(localhost.find_element_by_id('select_assign1'))
    for opt in sel.options:
        if(opt.text == 'Test Assignment 1'):
            opt.click()
            print('option clicked')
    localhost.find_element_by_id('submit_assign1').click()   #click upload grades
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Initializing"
        )
    )
    print(localhost.find_element_by_id('submit_assign1').text)
    localhost.refresh()
    time.sleep(2)
    assert Select(localhost.find_element_by_id('select_assign1')).first_selected_option.text == 'Test Assignment 1'
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )

# Tests that uploading an assignment then 
def test_cancel_removes_entries_from_db(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )
    localhost.find_element_by_id('cancel_assign1').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "No match found"
        )
    )
    status_length = 10
    match_length = 10
    conn = psycopg2.connect(
        host = "postgres-service",
        database = "test",
        user = "dev",
        password = "mypassword"
    )
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM assignment_status;")
        status_length = curs.rowcount
    conn.commit()
    conn.close()

    assert status_length == 0

# Tests that while an assignment is being reuploaded the cancel button disables again
def test_cancel_disabled_during_upload(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Initializing"
        )
    )
    assert localhost.find_element_by_id('cancel_assign1').get_attribute('disabled') == 'true'
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploading Grades"
        )
    )
    assert localhost.find_element_by_id('cancel_assign1').get_attribute('disabled') == 'true'
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )


    
# Tests that cancel button disables after being used
def test_cancel_disabled_after_canceling(localhost):
    localhost.find_element_by_id('submit_assign1').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "Uploaded"
        )
    )
    assert not localhost.find_element_by_id('cancel_assign1').get_attribute('disabled')
    localhost.find_element_by_id('cancel_assign1').click()
    WebDriverWait(localhost, SECONDS_WAIT).until(
        EC.text_to_be_present_in_element(
            (By.ID, "assign1"), "No match found"
        )
    )
    assert localhost.find_element_by_id('cancel_assign1').get_attribute('disabled') == 'true' 
