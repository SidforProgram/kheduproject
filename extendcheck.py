import requests
import time
import json
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from browsermobproxy import Server
from pyquery import PyQuery as pq

from __init__ import tz, login_url, username, password


class ExtentCase(object):
    def __init__(self):
        self.login_url = login_url
        self._username = username
        self._password = password
        self.allow_list =[]
        self.deny_list = []
        self.hire_list = []
    def login(self,proxy_location, webdriver_location):
        server = Server(proxy_location + r'\browsermob-proxy.bat')
        server.start()
        proxy = server.create_proxy()
        proxy.new_har(options={
            'captureContent': True,
            'captureHeaders': True
        })
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--proxy-server={}'.format(proxy.proxy))
        #chrome_options.add_argument('--headless')  # 無頭模式
        browser = webdriver.Chrome(webdriver_location + r'\chromedriver', options=chrome_options)
        browser.set_page_load_timeout(30)
        wait = WebDriverWait(browser, 10)
        # 登入
        browser.get(self.login_url)
        id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '')  # 抓第一行 每個id，都會隨機亂產生
        browser.find_element_by_xpath('//*[@id="{}b"]'.format(id0)).send_keys(self._username)  # 亂數+b
        browser.find_element_by_xpath('//*[@id="{}c"]'.format(id0)).send_keys(self._password)  # 亂數+c
        browser.find_element_by_xpath('//*[@id="{}g"]'.format(id0)).click()  # 亂數+g
        time.sleep(4)
        content_id = pq(browser.page_source)('div.z-page').attr('id').replace('_', '')  # 主頁面的亂數
        return browser, wait, proxy, content_id
    def get_reviw_check(self, browser, wait, proxy, content_id):
        # print("進入流程表單中心")
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}y-cnt"]/img'.format(content_id)))).click()
            time.sleep(2)
            try:
                # print("進入租用表單審核")
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}f0-cnt"]/img'.format(content_id)))).click()
                time.sleep(2)
                # print("選擇selection表單")
                try:
                    #  print("抓成員資料")
                    s1 = Select(browser.find_element_by_id('{}i1'.format(content_id)))
                    s1.select_by_visible_text("期限展延")
                    s2 = Select(browser.find_element_by_id('{}k1'.format(content_id)))
                    s2.select_by_visible_text("已經完成的任務")
                    time.sleep(3)
                    event_rows = len(browser.find_elements_by_xpath('//*[@id="{}p1-cave"]/tbody/tr'.format(content_id)))
                    # print("點選個人列表")
                    for i in range(9, 13):
                        try:
                            event_name = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[1]'.format(content_id, i)).text
                            event_school = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[3]'.format(content_id, i)).text
                            if (event_name.find("期限展延") != -1 and len(event_school)>0):  # double check
                                self.hire_list.append(event_school)
                                # 點選單一任務的審核
                                browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[7]/div/table/tbody/tr/td/table/tbody/tr/td/button'.format(content_id, i)).click()
                                print("選擇表單細節")
                                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@class="paddingless-tabbox z-tabbox z-tabbox-top"]/div/ul/li[1]'))).click()
                                time.sleep(5)
                                #抓網頁內容
                                print("抓網頁內容")
                                dom = pq(browser.page_source)
                                check_autoextend = 0
                                for j in dom('tbody.z-rows > tr').items():
                                    check_content = j('span.z-label').parent('div.z-vlayout-inner').text()
                                    if(check_content.find(" 自動展延")!=-1):
                                        check_autoextend +=1 
                                if(check_autoextend>0):
                                    self.deny_list.append("展延拒絕-" + event_school)
                                else:
                                    self.allow_list.append("展延核可-" + event_school)
                            else:
                                self.error_report("lost","No.{} 遺忘處理".format(i))
                            misson_closetag = browser.find_element_by_xpath('//*[@class="z-window-icon z-window-close"]')
                            misson_closetag.click()
                            time.sleep(2)
                        except Exception as e:
                            errortype = e.__class__.__name__
                            detail = e.args[0]
                            if(errortype =="ElementClickInterceptedException" and detail.find("z-button")!=-1):
                                self.error_report("process","細節點擊失敗")
                            elif(errortype =="ElementClickInterceptedException" and detail.find("z-tab-text")!=-1):
                                self.error_report("process","表單細節點擊失敗")
                            elif(errortype =="ElementClickInterceptedException" and detail.find("z-window-icon")!=-1):
                                self.error_report("process","關閉擊失敗")
                            else:
                                self.error_report("process",e)

                except:
                    self.error_report("process","抓成員資料 error")    
            except:
                self.error_report("process","進入流租用表單審核 error")
        except:
            self.error_report("process","進入流程表單中心 error")
   
    def error_report(self, type, message):
        now_dt = datetime.datetime.today() 
        datetime_format = now_dt.strftime("%Y/%m/%d %H:%M:%S")
        file_datetime = now_dt.strftime("%Y/%m/%d")
        if(type=="system"):
            with open(r'C:\python_job\khedu-process\error_log\{}-error-system.txt'.format(file_datetime), 'a+', encoding='utf-8') as f:
                f.write("{0}    {1}\n".format(datetime_format,message))
                f.close()
        if(type=="process"):
            with open(r'C:\python_job\khedu-process\error_log\{}-error-process.txt'.format(file_datetime), 'a+', encoding='utf-8') as f:
                f.write("{0}    {1}\n".format(datetime_format,message))
                f.close()
        
    def main(self):   
        browerpath = r"C:\python_job\khedu-test\browsermob-proxy-2.1.4\bin"
        webdriver_browser = r"C:\python_job\khedu-test"
        print("login")
        # initialization browser
        try:
            browser, wait, proxy, content_id = self.login( browerpath, webdriver_browser)
            time.sleep(3)
            self.get_reviw_check(browser, wait, proxy, content_id) 
        except:
            self.error_report("system","browswe initialization error")
        
        
        with open(r'C:\python_job\khedu-process\extend-allow.txt', 'w', encoding='utf-8') as f:
            allow='\n'.join(self.allow_list)
            f.write(allow)
            f.close()
        with open(r'C:\python_job\khedu-process\extend-deny.txt', 'w', encoding='utf-8') as f:
            deny='\n'.join(self.deny_list)
            f.write(deny)
            f.close() 
if __name__ == "__main__":
    ExtentCase().main()
