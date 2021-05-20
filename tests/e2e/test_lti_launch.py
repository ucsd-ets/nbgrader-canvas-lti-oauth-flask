from . import driver, SECONDS_WAIT, scroll_to_bottom
import json
import time
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium
import os


def test_lti_launch(driver):
    try:
        _lti_launch(driver)
        driver.save_screenshot('selenium/lti-launch-success.png')
    except Exception as e:
        driver.save_screenshot('selenium/lti-launch-fail.png')
        raise e

# test upload grades when user has selected the canvas assignment  
def test_upload_grades_canvas_assignment_selected(driver):
    try:
        _lti_launch(driver)
        upload_btn = driver.find_element_by_name('assign1')
        upload_btn.click()

        # wait for page reload


        driver.save_screenshot('selenium/upload-grades-success.png')
    except Exception as e:
        driver.save_screenshot('selenium/upload-grades-fail.png')
        raise e

# TODO: test upload grades if "create canvas assignment selected"

def _lti_launch(driver):
    # TODO this will change when overwritten by prod
    nbgrader_lti_path = "/courses/20774/modules/items/901696"
    driver.get(os.getenv('CANVAS_BASE_URL') + nbgrader_lti_path)
    # navigate to the lti
    # TODO: change link text once prod overwrites test (remove "-test")
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.LINK_TEXT, 'nbgrader-localhost-3-test'))
    ).click()

    # select the load nbgrader-* button
    external_lti_btn_selector = '//*[@id="tool_form"]/div/div[1]/div/button'
    driver.find_element_by_xpath(external_lti_btn_selector)
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.XPATH, external_lti_btn_selector))
    ).click()

    # switch tabs and confirm output
    driver.switch_to.window(driver.window_handles[-1])
    try:
        WebDriverWait(driver, SECONDS_WAIT).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '//*[@id="oauth2_accept_form"]/div/input'))
        ).click()

    except selenium.common.exceptions.TimeoutException:
        """May not have the authorize screen if already clicked from previous test"""
        pass

        