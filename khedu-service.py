
import os
import re
import time
import json
import datetime

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
import json
from __init__ import tz, login_url, username, password

class ServiceCrawler(object):
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
        browser.set_page_load_timeout(30)
        wait = WebDriverWait(browser,30)
        browser.get(login_url)
        # -- login --
        id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') # 每次重load網站都有個隨機id
        browser.find_element_by_xpath('//*[@id="{}b"]'.format(id0)).send_keys(username)
        browser.find_element_by_xpath('//*[@id="{}c"]'.format(id0)).send_keys(password)
        browser.find_element_by_xpath('//*[@id="{}g"]'.format(id0)).click()
        time.sleep(0.5) # not so fast
        # -- main --(TODO: 這邊是給雲端管理中心的)
        id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') # id會再變
        browser.find_element_by_xpath('//*[@id="{}_0-cnt"]/img'.format(id0)).click() # 雲端管理中心
        time.sleep(2)
        browser.find_element_by_xpath('//*[@id="{}j2-cave"]'.format(id0)).click() # 雲端中心
        time.sleep(2)
        browser.find_element_by_xpath('//*[@id="{}03"]'.format(id0)).click() # user search(list)
        
        return browser, proxy, wait
    def proxy_analysis(self,proxy_content):
        CPU_count = 0
        Memory_count = 0
        Storage1 = 0
        Storage2 = 0
        backupcount =0
        ipcount = 0
        networkcount = 0
        school_resource = {}
        for k, v in proxy_content:
            if k =='text':
                print("re fiilter specific string")
                pattn = r"value:\'.*\'"
                devicelist = re.findall(pattn, v)
                if(len(devicelist)==0):
                    return school_resource
                for node in devicelist:
                    if(node.find("CPU")!=-1):
                        print("cpu here")
                        others, cpumajor = node.split("CPU ")
                        CPU_count = int(cpumajor[0:2])
                        print("memory here")
                        others, memorymajor = node.split("記憶體 ")
                        Memory_count = int(memorymajor[0:memorymajor.index("MB")])
                        print("storage1 here")
                        others, storagemajor = node.split("磁碟")
                        Storage1 = int(storagemajor[0:storagemajor.index("GB")])
                        print("storage2 here")
                    elif(node.find("磁碟類型")!=-1):
                        others, otherstoragemajor = node.split("value:'")
                        Storage2 = int(otherstoragemajor[0:otherstoragemajor.index("GB")])
                    elif(node.find("備份")!=-1):
                        print("backup here")
                        backupcount +=1
                    elif(node.find("網路 public")!=-1): 
                        print("IP here")
                        ipcount +=1
                    elif(node.find(".edu.tw")!=-1):
                        #目前先設定EDU.TW
                        print("network here")
                        networkcount +=1
        school_resource['CPU'] = CPU_count
        school_resource['Memory'] = Memory_count
        school_resource['Storage'] = Storage1+Storage2
        school_resource['Backup_num'] = backupcount
        school_resource['IP_num'] = ipcount
        school_resource['Network_num'] = networkcount
        return  school_resource

    def main(self):
        browser, proxy, wait = self.init_browser()
        # 取得總頁數
        time.sleep(1)
        content_id = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') # 該頁面的id
        #帳號表格要用的
        usertableid = browser.find_element_by_xpath('//div[@class="borderless z-listbox"]').get_attribute("id")
        total_page = int(pq(browser.page_source)('span.z-paging-text').text().replace('/', '').strip())
        matrix = []
        for page in range(1, total_page):
            print('now page: %d.' % page)
            time.sleep(3)
            # 換頁
            if page > 1:
                try:
                    page_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'z-paging-input')))
                except:
                    time.sleep(1)
                    page_input = browser.find_element_by_class_name('z-paging-input')
                actionChains = ActionChains(browser)
                actionChains.move_to_element(page_input).click().perform()
                actionChains.move_to_element(page_input).send_keys(Keys.BACKSPACE,page,Keys.ENTER).perform()
                #頁面會更新，需要重抓
                usertableid = browser.find_element_by_xpath('//div[@class="borderless z-listbox"]').get_attribute("id")
                #第一頁會點到小黑人    
            time.sleep(5)
            #抓該頁有多少間學校
            num_rows = len(browser.find_elements_by_xpath('//*[@id="{}-cave"]/tbody/tr'.format(usertableid)))
            print(num_rows)
            #分頁內容
            for i in range(1,num_rows):
                item = dict()
                #點選小黑人，使用者列表的id會亂跳
                usertableid = browser.find_element_by_xpath('//div[@class="borderless z-listbox"]').get_attribute("id")
                schoolname = browser.find_element_by_xpath('//*[@id="{0}-cave"]/tbody/tr[{1}]/td[2]'.format(usertableid,i)).text
                accountname = browser.find_element_by_xpath('//*[@id="{0}-cave"]/tbody/tr[{1}]/td[1]'.format(usertableid,i)).text
                #如果抓不到要移動bar
                if(schoolname):
                    item['name'] = schoolname
                    item['account'] = accountname
                else:
                    userlist  = browser.find_element_by_xpath('//*[@id="{}-body"]'.format(usertableid))
                    jsCode = "arguments[0].scrollTop = 200"
                    browser.execute_script(jsCode,userlist)
                    schoolname = browser.find_element_by_xpath('//*[@id="{0}-cave"]/tbody/tr[{1}]/td[2]'.format(usertableid,i)).text
                    accountname = browser.find_element_by_xpath('//*[@id="{0}-cave"]/tbody/tr[{1}]/td[1]'.format(usertableid,i)).text
                    item['account'] = accountname
                    item['name']    = schoolname
                print(page,i,schoolname)
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, '//div[text()="{}"]'.format(schoolname)))).click()
                except:
                    browser.find_element_by_xpath('//div[text()="{}"]'.format(schoolname)).click()
               
                wait.until(EC.presence_of_element_located((By.XPATH, '//button[text()="選擇"]'))).click()
                time.sleep(5)
                #分析頁面
                dom = pq(browser.page_source)
                item['data'] = list()
                try:
                    for j in dom('tbody.z-rows > tr').items():
                        _tag = False
                        tmp = dict()
                        title = j('img').attr('title') # 電腦
                        device_list = j('div > span.itemTitle').text() # khmtas
                        #khmtas', 'info_content': 'CPU 4 ( 1 socket * 4 core ) | 記憶體 4096 MB | 磁碟 100 GB | 直接連結外部網路 / Windows2019
                        device_list = j('div > span.itemTitle').parent('div').siblings('div > span').text()
                        livetime = j('div.z-hlayout-inner').parent('div').parent('div').parent('td').prev('td').text()
                        if(title.find("電腦")!=-1):
                            CPU_sub = device_list.split("CPU ")[1]
                            tmp['CPU']= int(CPU_sub[0:CPU_sub.index(" (")])
                            Mem_sub = device_list.split("記憶體 ")[1]
                            tmp['Memory'] = int(Mem_sub[0:Mem_sub.index(" MB")])/1024
                            Sto_sub = device_list.split("磁碟 ")[1]
                            tmp['Storage'] = int(Sto_sub[0:Sto_sub.index(" GB")])                 
                        elif(title.find("磁碟空間")!=-1):
                            substring = device_list.split(" | 磁碟類型")[0]
                            tmp['Storage'] = int(substring[0: substring.index(" GB")])
                        elif (title.find("備份配額") != -1):
                            tmp['Backup_count']= 1
                        elif (title.find("外部IP") != -1):
                            tmp['IP_count']= 1
                        elif (title.find("網域名稱") != -1):
                            tmp['network_count']= 1
                        # 自動展延排除判斷
                        try:
                            if j('div.z-hlayout-inner > span').parent('div').next('div').find('div').attr('title') == '自動展延':
                                _tag = True
                        except:
                            pass
                        if _tag:
                            tmp['left'] = 'auto-extension'
                        else:
                            tmp['left'] = j('div.z-hlayout-inner > span').text()
                        tmp['cutoff']= livetime
                        
                        item['data'].append(tmp)
                except:
                    raise RuntimeError('詳細頁解析錯誤')
                item['datetime'] = datetime.datetime.strftime(datetime.datetime.now(tz), '%Y-%m-%d %H:%M:%S')
                matrix.append(item)
                #點選完學校後，還要再點選一次小黑人
                browser.find_element_by_xpath('//*[@id="{}03-cnt"]/img'.format(content_id)).click()
                if page > 1:
                    try:
                        page_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'z-paging-input')))
                    except:
                        time.sleep(1)
                        page_input = browser.find_element_by_class_name('z-paging-input')
                    time.sleep(2)
                    actionChains = ActionChains(browser)
                    actionChains.move_to_element(page_input).click().perform()
                    actionChains.move_to_element(page_input).send_keys(Keys.BACKSPACE,page,Keys.ENTER).perform()
                time.sleep(5)
            print('page: %d done.' % page)

                
if __name__ == "__main__":
    starttime = datetime.datetime.now()
    ServiceCrawler().main()
    endtime = datetime.datetime.now()
    timespend =  (endtime - starttime).seconds
    print("這次任務所花的時間{} 秒".format(timespend))