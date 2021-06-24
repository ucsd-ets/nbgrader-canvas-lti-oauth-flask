from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
driver = webdriver.Remote("http://selenium:4444/wd/hub", DesiredCapabilities.CHROME)

#TODO: Add a page that the program goes to when there's an error
# Current Plan:
# login using the test account credentials
# hopefully this doesn't cause issues with DUO requiring 2 step auth
# if it does require 2 step auth, find a way to spoof oauth credentials
# driver.get("https://ucsd.test.instructure.com")
# user_name = driver.find_element_by_id('ssousername')
# user_name.send_keys('testacct111')
driver.get("http://web:5000/oauthlogin")
driver.save_screenshot('foo.png')

driver.quit()