# -*- coding: utf-8 -*-
import os
import json
import smtplib
import datetime

import pandas as pd
from email.header import Header
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import poplib
from mail__init__ import MAIL_ADDR, UN, PD

class AlertMail(object):
    def __init__(self):
        self.mailaddr = MAIL_ADDR
        self.username = UN
        self.password = PD
        self.smtp = smtplib.SMTP('casarray.systex.tw', 25)
        self.smtp.login(UN, PD)
    def createmailcontent(self, **kwargs):
        msg = MIMEMultipart()
        msg['subject'] = self.subject
        msg['from'] = self.send_from
        msg['to'] = self.reciver
        msg['cc'] = self.cc
        with open(self.template, 'r',encoding="utf-8") as fp: # 模板
            html = fp.read()
        content = MIMEText(html, 'html')
        msg.attach(content)
        return msg
    def controller(self, sender,mail_addr,cc,subject,template):
        self.__init__()
        self.subject = subject
        self.send_from = sender
        self.cc = cc
        self.template = template
        self.reciver = mail_addr
        msg = self.createmailcontent()
        self.smtp.sendmail(sender, mail_addr, msg.as_string())

if __name__ =="__main__":
    sender = "kheservice@systex.com"
    mail_addr = "chengtingliu@systex.com"
    cc = "kheservice@systex.com"
    subject = "雲端系統期限展延問題(精誠國小)"
    template = r"C:\python_job\khedu-process\templates\extemd-alert.html"
    test = AlertMail()
    test.controller(sender=sender, mail_addr=mail_addr,cc=cc,subject=subject,template =template)