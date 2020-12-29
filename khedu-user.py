import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from browsermobproxy import Server
from pyquery import PyQuery as pq
import os
import re
import time
import json
import datetime

from __init__ import tz, login_url, username, password

class UserCrawler(object):
    def __init__(self):
        self.login_url = login_url
        self._username = username
        self._password = password
    def init_browser(self):
        # response listen proxy
        server = Server(r'C:\python_job\khedu-test\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
        server.start()
        proxy = server.create_proxy()
        proxy.new_har(options={
            'captureContent': True,
            'captureHeaders': True
        })
        # -- chromedriver --
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
        chrome_options.add_argument('--headless')  # 無頭模式
        browser = webdriver.Chrome(r'C:\python_job\khedu-test\chromedriver.exe', options=chrome_options)
        browser.maximize_window()
        time.sleep(1)#變大視窗需要等待
        browser.set_page_load_timeout(30)
        wait = WebDriverWait(browser,30)
        browser.get(login_url)
        # -- login --
        id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') # 每次重load網站都有個隨機id
        browser.find_element_by_xpath('//*[@id="{}b"]'.format(id0)).send_keys(username)
        browser.find_element_by_xpath('//*[@id="{}c"]'.format(id0)).send_keys(password)
        browser.find_element_by_xpath('//*[@id="{}g"]'.format(id0)).click()
        time.sleep(2) # not so fast
        browser.refresh() #頁面會卡在轉圈圈 需要reload
        time.sleep(2) 
        return browser, proxy, wait
    def main(self):
        matrix =[]
        browser, proxy, wait = self.init_browser()
        content_id = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') # id會再變
        print(content_id)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}n-cnt"]/img'.format(content_id)))).click() # 使用者中心
        time.sleep(5)
        try:
            total_page = int(pq(browser.page_source)('span.z-paging-text').text().replace('/', '').strip())
        except:
            raise RuntimeError('總頁數擷取錯誤')
        for page in range(1, total_page):
            print('now page: %d.' % page)
            time.sleep(5)
            # 換頁
            if page > 1:
                try:
                    page_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'z-paging-input')))
                except:
                    time.sleep(1)
                    page_input = browser.find_element_by_class_name('z-paging-input')
                time.sleep(1)
                actionChains = ActionChains(browser)
                actionChains.move_to_element(page_input).click().perform()
                actionChains.move_to_element(page_input).send_keys(Keys.BACKSPACE,page,Keys.ENTER).perform()               
                time.sleep(5) # for listening response
            #抓該頁的使用者
            time.sleep(3)
            num_rows = len(browser.find_elements_by_xpath('//*[@id="{}u0-cave"]/tbody/tr'.format(content_id)))
            print(num_rows)
            # 一個個抓，最後一格不需要讀取
            for i in range(1,num_rows):
                item = dict()
                schoolname = browser.find_element_by_xpath('//*[@id="{0}u0-cave"]/tbody/tr[{1}]/td[2]'.format(content_id,i)).text
                if(schoolname):
                    item['name'] = schoolname
                else:
                    userlist  = browser.find_element_by_xpath('//*[@id="{}u0-body"]'.format(content_id))
                    jsCode = "arguments[0].scrollTop = 200"
                    browser.execute_script(jsCode,userlist)
                    schoolname = browser.find_element_by_xpath('//*[@id="{0}u0-cave"]/tbody/tr[{1}]/td[2]'.format(content_id,i)).text
                    item['name'] = schoolname
                print(page,i, schoolname)
                
                time.sleep(1)

                # parsing info
                browser.find_element_by_xpath('//*[@id="{0}u0-cave"]/tbody/tr[{1}]/td[2]'.format(content_id,i)).click()
                time.sleep(5)
                dom = pq(browser.page_source)
                try:
                    for i in dom('tbody.z-rows').eq(0).items():
                        item['email'] = i('span:contains("電子郵件")').parent('div').parent('td').next('td').find('input').attr('value')
                        item['department'] = i('span:contains("部門")').parent('div').parent('td').next('td').find('input').attr('value')
                        item['note'] = i('span:contains("註記")').parent('div').parent('td').next('td').find('input').attr('value')
                except:
                    raise RuntimeError('詳細頁解析錯誤')
                print(item)
                matrix.append(item)
            print('page: %d done.' % page)
            
        # -- final output --
        with open('users.json', 'w', encoding='utf-8') as fp:
            json.dump(matrix, fp, ensure_ascii=False)

            

if __name__ == "__main__":
    starttime = datetime.datetime.now()
    UserCrawler().main()   
    endtime = datetime.datetime.now()
    timespend =  (endtime - starttime).seconds
    print("這次任務所花的時間{} 秒".format(timespend))