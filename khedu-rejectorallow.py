import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from browsermobproxy import Server
from pyquery import PyQuery as pq
import pprint
import time
import json
login_url = 'https://www.vi.kh.edu.tw/cloud/login'
username  = 'systexkh'
password  = 'rh2020systex@123'
# 參數區
hire_list = []
continue_list = []
continue_device_dict = {}
allow_list = []
deny_list = []
# 設定網頁
server = Server(r'C:\python_job\khedu-test\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
server.start()
proxy = server.create_proxy()
proxy.new_har(options={
    'captureContent': True,
    'captureHeaders': True
})
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--proxy-server={}'.format(proxy.proxy))
browser = webdriver.Chrome(r'C:\python_job\khedu-test\chromedriver', options=chrome_options)
browser.set_page_load_timeout(30)
wait = WebDriverWait(browser,10)
#登入
browser.get(login_url)
id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') #抓第一行 每個id，都會隨機亂產生
browser.find_element_by_xpath('//*[@id="{}b"]'.format(id0)).send_keys(username) #亂數+b
browser.find_element_by_xpath('//*[@id="{}c"]'.format(id0)).send_keys(password) #亂數+c
browser.find_element_by_xpath('//*[@id="{}g"]'.format(id0)).click() #亂數+g
print(id0)
time.sleep(4)
id1 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '')
print(id1)
#進入流程表單中心
wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}y-cnt"]/img'.format(id1)))).click()
time.sleep(3)
#選擇表單審核
wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}f0-cnt"]/img'.format(id1)))).click()
time.sleep(1)
i=1
event_name = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[1]'.format(id1,i)).text
event_school = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[3]'.format(id1,i)).text
browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[7]/div/table/tbody/tr/td/table/tbody/tr/td/button'.format(id1,i)).click()
#抓核准
#td[1] = 核可
#td[3] = 拒絕

time.sleep(3)
#get_button =browser.find_element_by_xpath('//*[@class="button-box-trans z-hbox"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td[3]/button')
get_button = browser.find_element_by_xpath('//button[text()="拒絕"]')
get_button.click()
time.sleep(3)
#抓到最後的button
get_final_button = browser.find_element_by_xpath('//button[text()="是"]')
get_final_button.click()
#print(get_final_button.get_attribute("id"))