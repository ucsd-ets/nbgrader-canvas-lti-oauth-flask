from . import driver, SECONDS_WAIT, scroll_to_bottom
import json
import time
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium


def test_oauth_workflow(driver):
    try:
        # select the courses btn
        courses_btn = driver.find_element_by_id('global_nav_courses_link')
        courses_btn.click()

        # navigate to the course page
        WebDriverWait(driver, SECONDS_WAIT).until(
            expected_conditions.element_to_be_clickable(
                (By.LINK_TEXT, 'Canvas Caliper Events Testing'))
        ).click()

        scroll_to_bottom(driver)

        # navigate to the lti
        WebDriverWait(driver, SECONDS_WAIT).until(
            expected_conditions.element_to_be_clickable(
                (By.LINK_TEXT, 'nbgrader-selenium'))
        ).click()

        # select the load nbgrader-selenium button
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

        finally:
            assert 'Courses' in driver.page_source
        
        driver.save_screenshot('selenium/oauth-workflow-success.png')
    except Exception as e:
        driver.save_screenshot('selenium/oauth-workflow-fail.png')
        raise e
