import requests
import re
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
import pprint
import time
import json
import threading
#登入權限


# 參數區
hire_list = []
allow_list = []
deny_list = []
hire_resource = {}
def login(weburl, user, passwd,proxy_location, webdriver_location):
    server = Server(proxy_location+r'\browsermob-proxy.bat')
    server.start()
    proxy = server.create_proxy()
    proxy.new_har(options={
    'captureContent': True,
    'captureHeaders': True
    })
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--proxy-server={}'.format(proxy.proxy))
    browser = webdriver.Chrome(webdriver_location+r'\chromedriver', options=chrome_options)
    browser.set_page_load_timeout(30)
    wait = WebDriverWait(browser,10)
    #登入
    browser.get(login_url)
    id0 = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') #抓第一行 每個id，都會隨機亂產生
    browser.find_element_by_xpath('//*[@id="{}b"]'.format(id0)).send_keys(username) #亂數+b
    browser.find_element_by_xpath('//*[@id="{}c"]'.format(id0)).send_keys(password) #亂數+c
    browser.find_element_by_xpath('//*[@id="{}g"]'.format(id0)).click() #亂數+g
    time.sleep(4)
    content_id = pq(browser.page_source)('div.z-page').attr('id').replace('_', '') #主頁面的亂數
    print(id0)
    print(content_id)
    #回傳 browser, wait ,webid, proxy
    return browser, wait,proxy, content_id

                
def get_reviw_check(browser,wait,proxy,content_id):
    #參數區
    global hire_list
    time.sleep(3)
    #print("進入流程表單中心")
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}y-cnt"]/img'.format(content_id)))).click()
    time.sleep(3)
    #print("進入租用表單審核")
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="{}f0-cnt"]/img'.format(content_id)))).click()
    time.sleep(3)
    #print("選擇selection表單")
    type_menu = Select(browser.find_element_by_id('{}i1'.format(content_id)))
    type_menu.select_by_visible_text("設備租用")
    time.sleep(3)
    #print("抓成員資料")
    event_rows = len(browser.find_elements_by_xpath('//*[@id="{}p1-cave"]/tbody/tr'.format(content_id)))
    #print(event_rows)
    for  i in range(1,event_rows):
        event_name = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[1]'.format(content_id,i)).text
        event_school = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[3]'.format(content_id,i)).text
        if(len(event_school)==0):
            print(event_school,"none? ")
            type_menu.select_by_visible_text("全部流程")
            time.sleep(2)
            type_menu.select_by_visible_text("設備租用")
            time.sleep(2)
            event_name = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[1]'.format(content_id,i)).text
            event_school = browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[3]'.format(content_id,i)).text  
        print("serial {0} {1}".format(i,event_school))  
        if(event_name.find("設備租用")!=-1): # double check
            hire_list.append(event_school)
            #點選單一任務的審核
            browser.find_element_by_xpath('//*[@id="{0}p1-cave"]/tbody/tr[{1}]/td[7]/div/table/tbody/tr/td/table/tbody/tr/td/button'.format(content_id,i)).click()
            time.sleep(3)
            #選擇表單細節
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@class="paddingless-tabbox z-tabbox z-tabbox-top"]/div/ul/li[1]'))).click()
            #抓自動展延checkbox
            hireauto_check = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@class="hr-top z-hlayout"]/div/span/input')))
            if(hireauto_check.get_attribute("checked")):    
                deny_list.append("租用拒絕-"+event_school)
            else:
                allow_list.append("租用核可-"+event_school)
            #抓目前學校的設備
            time.sleep(5)
            dom = pq(browser.page_source)
            CPU_core = 0
            Mem_size = 0
            Sto_size = 0
            IP_count = 0
            Backup_count = 0
            Network_count = 0
            for i in dom('tbody.z-rows > tr').items():
                title=i('img').attr('title')
                device_list = i('span.z-label').text()
                try:
                    if(title.find("電腦")!=-1):
                        CPU_sub = device_list.split("CPU ")[1]
                        CPU_core= int(CPU_sub[0:CPU_sub.index(" (")])
                        Mem_sub = device_list.split("記憶體 ")[1]
                        Mem_size = int(Mem_sub[0:Mem_sub.index("MB")])
                        Sto_sub = device_list.split("磁碟 ")[1]
                        Sto_size = int(Sto_sub[0:Sto_sub.index("GB")])
                        
                    elif(title.find("磁碟空間")!=-1):
                        substring = device_list.split("磁碟 ")[1]
                        Sto_size += int(substring[0: substring.index(" GB")])
                    elif (title.find("備份配額") != -1):
                        Backup_count += 1
                    elif (title.find("外部IP") != -1):
                        IP_count += 1
                    elif (title.find("網域名稱") != -1):
                        Network_count += 1
                except:
                    if(title):
                        print(title, title.find("電腦"))
            #填入學校資源dict
            if (event_school in hire_resource):
               # print(event_school)
                #print(hire_resource[event_school])
                hire_resource[event_school]['CPU'] += CPU_core
                hire_resource[event_school]['Memory'] += Mem_size/1024
                hire_resource[event_school]['Storage'] += Sto_size
                hire_resource[event_school]['Backupcount'] += Backup_count
                hire_resource[event_school]['IPcount'] += IP_count
                hire_resource[event_school]['Network'] += Network_count
                #print(hire_resource[event_school])
            else: 
                hire_resource[event_school]  = {'CPU':CPU_core, 'Memory':Mem_size/1024, 'Storage':Sto_size , 'Backupcount':Backup_count, 'IPcount':IP_count, 'Network':Network_count} 
        try:    
            misson_closetag = browser.find_element_by_xpath('//*[@class="z-window-icon z-window-close"]')
            misson_closetag.click()
            time.sleep(3)
        except:
            print(event_school)
    for allownode in allow_list:
        school = allownode.split("租用核可-")[1]
        school_resource = hire_resource[school]
        if(school.find("國小")!= -1 or school.find("國中")!= -1 ):
            if(school_resource['CPU']>8 or school_resource['Memory']>8 or school_resource['Storage']>300 or school_resource['IPcount']>2 or school_resource['Network']>2):
                allow_list.remove(allownode)
                deny_list.append("超出配額-"+school)
        elif(school.find("高中")!= -1):
            if(school_resource['CPU']>16 or school_resource['Memory']>16 or school_resource['Storage']>500 or school_resource['IPcount']>2 or school_resource['Network']>2):
                allow_list.remove(allownode)
                deny_list.append("超出配額-"+school)
    with open('allow.txt', 'w', encoding='utf-8') as f:
        allow='\n'.join(allow_list)
        f.write(allow)
        f.close()
    with open('deny.txt', 'w', encoding='utf-8') as f:
        deny='\n'.join(deny_list)
        f.write(deny)
        f.close()      


                
if __name__ =="__main__":
    login_url = 'https://www.vi.kh.edu.tw/cloud/login'
    username  = 'systexkh'
    password  = 'rh2020systex@123'
    browerpath  = r"C:\python_job\khedu-test\browsermob-proxy-2.1.4\bin"
    webdriver_browser = r"C:\python_job\khedu-test"
    print("login")
    browser, wait,proxy, content_id = login(login_url, username, password, browerpath, webdriver_browser)
    get_reviw_check(browser,wait,proxy,content_id)
    #selection_menu = browser.find_element_by_xpath('//select[@id="{}i1"]'.format(content_id))
    #wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="{}f0-cnt"]/img'.format(content_id))))
    
