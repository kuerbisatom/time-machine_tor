from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyautogui

def initialize_tor_browser(path):
    return TorBrowserDriver(path)

# function to set the proxy
def set_proxy(driver,port):
    ## Visit About:config
    driver.get("about:config")
    driver.find_element_by("#warningButton").send_keys(Keys.RETURN)
    #Find Correct Setting
    elem = driver.find_element_by("#textbox")
    elem.send_keys("network.proxy.socks_port")
    elem.send_keys(Keys.RETURN)
    elem.send_keys(Keys.TAB)
    # Switch to bar
    curEle = driver.switch_to.active_element
    curEle.send_keys(Keys.RETURN)
    # Get opened Window
    handler = driver.switch_to.alert
    handler.send_keys(port)
    handler.send_keys(Keys.RETURN)

# visit Website
def visit(driver,url):
    try:
        driver.load_url(url)
    except:
        print "[*] Website couldn't be loaded"
        print url

# find all links on current Website
def find_urls(driver):
    url = []
    elems = driver.find_elements_by_tag_name("a")
    for elem in elems:
        # elem can be added to URL-Array
        url.append(elem.get_attribute("href"))
    return url

def close_browser(driver):
    return driver.quit()
