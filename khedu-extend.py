import os
import json
import time

import extendcheck
import weboutlook
#登入高教網-爬自動展延的列表
extendprocess = extendcheck.ExtentCase()
extendprocess.main()
#確認名單
allowpath = r"C:\python_job\khedu-process\extend-allow.txt"
denypath = r"C:\python_job\khedu-process\extend-deny.txt"
contactpath = r"C:\python_job\khedu-process\users.json"
allow_list = []
deny_list = []
if os.path.isfile(allowpath):
    with open(allowpath, 'r', encoding='utf-8') as allowfile:
        for node in allowfile:
            schoolname = node.split("-")[1].replace("\n", "")
            allow_list.append(schoolname)
if os.path.isfile(denypath) and os.path.isfile(contactpath):
    contact_list = open(contactpath, 'r', encoding='utf-8')
    school_resource = json.load(contact_list)
    total_school = len(school_resource)
    with open(denypath, 'r', encoding='utf-8') as denyfile:
        for node in denyfile:
            schoolname = node.split("-")[1].replace("\n", "")
            for i in range(total_school):
                if(school_resource[i]['name'].find(schoolname)!= -1):
                    email = school_resource[i]['email']
                    deny_list.append([schoolname,email])
    contact_list.close()
print(allow_list)
print(deny_list)             
#審核-成功

#審核-失敗
outlook = weboutlook.AlertMail()
lostlist = []
alertlist =[]
for denynode in deny_list:
    if len(denynode[1])>0:
        sender = "kheservice@systex.com"
        #mail_addr = denynode[1]
        mail_addr = "chengtingliu@systex.com"
        cc = "kheservice@systex.com"
        subject = "雲端系統期限展延問題({})".format(denynode[0])
        template = r"C:\python_job\khedu-process\templates\extend-alert.html"
        alertlist.append(denynode[0])
        outlook.controller(sender,mail_addr,cc,subject,template)
        time.sleep(2)
    else:
       lostlist.append("{}-缺少聯絡方式".format(denynode[0])) 
print(alertlist)
print(lostlist)