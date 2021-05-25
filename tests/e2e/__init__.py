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

def restart_app():
    flask_pid = None
    python_pid = None

    for proc in psutil.process_iter():
        try:
            process_name = proc.name()
            if process_name == 'flask':
                flask_pid = proc.pid
            elif process_name == 'python':
                python_pid = proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if flask_pid == None or python_pid == None:
        raise Exception('Could not restart flask app!')

    # processes must be restarted in a specific order
    os.kill(python_pid, signal.SIGKILL)
    os.kill(flask_pid, signal.SIGKILL)


@pytest.fixture
def driver():
    # initialize the selenium testing environment
    os.system('touch /app/selenium/on')
    restart_app()

    driver = webdriver.Remote(
    command_executor='http://selenium:4444/wd/hub',
    desired_capabilities=DesiredCapabilities.CHROME)

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

    # client up the selenium testing environment
    os.system('rm -rf /app/selenium/on')
    restart_app()

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