# -*- coding: utf-8 -*-
import traceback
from collections import deque
import time
import json
import headerfile
import random
import re
import MySQLdb
from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import threading
import inspect
import ctypes
import os
import sys
import urllib2

reload(sys)
sys.setdefaultencoding('utf-8')
closetable = []
logs_deque = deque()
threads = []
num = 0
headers = {'User-Agent': random.choice(headerfile.USER_AGENTS)}
'''
终止线程操作
'''
#https://movie.douban.com/tag/%E7%88%B1%E6%83%85?start=0&type=T

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        print "invalid thread %d" %tid
        # raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        # raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread():
    for t in threads:
        try:
            _async_raise(t.ident, SystemExit)
            # threads.remove(t)
        except:
            return 0
'''
写入错误到日志
'''
def write_error_log(url):
    output = open('error_log', 'a')
    try:
        output.write("{0} ".format(time.strftime("%H:%M:%S"))+url)
        output.write('\n')
    finally:
        output.close()
'''
--------------------------------获取网页信息操作-----------------------------
'''

def Write_into_closetable(url):
    output = open('Url_log', 'a')
    try:
        output.write(url)
        output.write('\n')
    finally:
        output.close()

def Write_into_opentable():
    print "读入closetable"
    file = open('Url_log', 'r')
    for line in file.readlines():
        closetable.append(line.strip())



'''
判断网页相似度，返回排序后的列表
'''
def Calculate_Similarity(mainurl,url):
    similarity_valu = 0
    new_valu = 0
    new_valu1 = 0
    main_url = mainurl.split('/')
    inputurl = url.split('/')
    rmin = min(len(mainurl),len(url))
    rmax = max(len(mainurl),len(url))
    if len(main_url)==len(inputurl):
        similarity_valu =similarity_valu+ 0.5
    for i in range(0,rmin):
        if mainurl[i] == url[i]:
            new_valu = new_valu+1
    similarity_valu = similarity_valu + float(new_valu)/rmax
    if len(main_url) == len(inputurl):
        similarity_valu = similarity_valu + 5.5
    for i in range(0,min(len(main_url),len(inputurl))):
        if main_url[i] == inputurl[i]:
            new_valu1 = new_valu1+1
    if new_valu1 == min(len(main_url),len(inputurl)):
        similarity_valu = 0
    similarity_valu = similarity_valu + float(new_valu1) / max(len(main_url),len(inputurl))
    return  float(similarity_valu)/8

def Sort_Page_Similarity(mainurl,dicturl):
    for url in dicturl.keys():
        dicturl[url] = Calculate_Similarity(mainurl,url)
    return dicturl



'''
--------------------------------获取IP操作-----------------------------
'''
# 测试IP是否可用，是--1，否--0
def IPtest(ProxyIp):
    session = requests.session()
    proxy = {'http': ProxyIp,
             'https': ProxyIp}
    url = "http://ip.chinaz.com/getip.aspx"  # 用来测试IP是否可用的url
    try:
        response = session.get(url, proxies=proxy, timeout=0.5)
        print '可用IP：', ProxyIp
        return 1
    except Exception, e:
        print '失效IP：', ProxyIp
        return 0


def Write_Html_test(filepath,filename,html):
    filename = filename.replace('https://','').replace('http://','').replace('/','.')
    if filename[-1] == '.':
        filename = filename[0:-1]
    print filename
    filepath = filepath.replace('\\','\\\\')
    file = open(filepath+'/'+'%s.txt' %filename, 'w')
    try:
        file.write(str(html))
    finally:
        file.close()

# 单个IP写入文件
def Write_text(proxy):
    file = open('IP.txt', 'r')
    try:
        text = file.read()
    finally:
        file.close()

    output = open('IP.txt', 'a')
    try:
        if json.dumps(proxy) not in text:
            output.write(json.dumps(proxy))
            output.write('\n')
        else:
            print "Ip已存在"
    finally:
        output.close()


# 将可用IP写入文件
def Write_into_text(proxyList):
    file = open('IP.txt', 'r')
    try:
        text = file.readlines()
    finally:
        file.close()

    output = open('IP.txt', 'a')
    try:
        for Proxy in proxyList:
            if json.dumps(Proxy) not in text:
                output.write(json.dumps(Proxy))
                output.write('\n')
            else:
                print "Ip已存在"
    finally:
        output.close()


# 测试已有IP是否可用，删除不可用
def gettextIp():
    with open("IP.txt", "r") as f:
        lines = f.readlines()
    with open("IP.txt", "w") as f_w:
        for line in lines:
            if IPtest(line.strip().replace('"', '')):
                f_w.write(line.strip().replace('"', ''))
                f_w.write('\n')


# 主函数
class Ip_spider:
    def __init__(self):
        self.queue = deque()
        self.local = threading.local()
        print '启动IP采集爬虫'

    '''
    --------------------------------更新IP操作-----------------------------
    '''
    def Ip_Proxy_State(self):
        Alive_Ip = 0
        with open("IP.txt", "r") as f:
            lines = f.readlines()
        with open("IP.txt", "w") as f_w:
            for line in lines:
                if IPtest(line.strip().replace('"', '')):
                    Write_text(line.strip().replace('"', ''))
                    Alive_Ip = Alive_Ip + 1
                    print '可用IP：' + line.strip().replace('"', '')
                else:
                    print '失效IP：' + line.strip().replace('"', '')
        print 'IP池可用IP总量：%d' % Alive_Ip
    '''
    --------------------------------获取IP操作-----------------------------
    '''
    def getHtml(self, url):
        driver = webdriver.PhantomJS(executable_path='C:/Python27/phantomjs')
        driver.get(url)
        print "获取", url
        self.data = driver.page_source  # 取到加载js后的页面content
        driver.quit

        return self.data

        # getIproxy用来测试IP是否可用

    def getIproxyxici(self, ProxyUrl):
        session = requests.session()
        page = session.get(ProxyUrl, headers=headers)
        print '读取页面：', ProxyUrl
        soup = BeautifulSoup(page.text, 'lxml')
        taglist = soup.find_all('tr', attrs={'class': re.compile("(odd)|()")})
        self.local.proxyList2 = []
        for ttag in taglist:
            tdlist = ttag.find_all('td')
            trtag = tdlist[1].string + ':' + tdlist[2].string
            if (IPtest(trtag)):
                self.local.proxyList2.append(trtag)
                print '成功获取IP：' + trtag
                Write_text(trtag)
        return self.local.proxyList2

    # 获取66IP代理网址内容
    def Url66Getter(self, ProxyUrl):
        headers = {'User-Agent': random.choice(headerfile.USER_AGENTS)}
        session = requests.session()
        page = session.get(ProxyUrl, headers=headers)
        soup = BeautifulSoup(page.text, 'lxml')
        Str = str(soup.find_all("p")).replace("\\t", "").replace("\\r", "").replace("\\n", "").replace("<p>",
                                                                                                       "").replace(" ",
                                                                                                                   "")
        taglist = re.findall(r'(.*?)<br/>', Str)
        self.local.proxyList1 = []
        for trtag in taglist:
            if (IPtest(trtag)):
                self.local.proxyList1.append(trtag)
                print '成功获取IP：' + trtag
                Write_text(trtag)
        return self.local.proxyList1

    # -----------------获取youdaili网站IP-------------------#
    def get_proxy(self, Url):
        self.local.proxyList3 = []
        data = self.getHtml(Url)
        soup = BeautifulSoup(data, "lxml")
        html = soup.find_all(class_="content")
        res = re.findall(r'\d+\.\d+\.\d+\.\d+\:\d+', str(html))
        for trtag in res:
            if (IPtest(trtag)):
                self.local.proxyList3.append(trtag)
                print '成功获取IP：' + trtag
                Write_text(trtag)
        return self.local.proxyList3

    def run(self,URL):

            print '开始获取IP'
            if "xici" in URL:
                proxyListxici = self.getIproxyxici(URL)
                # Write_into_text(proxyListxici)
            if "www.66ip.cn" in URL:
                proxyList66 = self.Url66Getter(URL)
                # Write_into_text(proxyList66)
            if "youdaili" in URL:
                proxyListyoudaili = self.get_proxy(URL)
                # Write_into_text(proxyListyoudaili)
            print '获取IP结束'

    '''
    --------------------------------获取网页信息操作-----------------------------
    '''
    def readIp(self):
            ipresult = []
            file = open('IP.txt', 'r')
            for line in file.readlines():
                proxies = {'http': line}
                ipresult.append(proxies)
            return ipresult



    '''
    --------------------------------获取IP入口操作-----------------------------
    '''
    def Get_ip_main(self):
        #thread = threading.Thread(target=gettextIp)
        #threads.append(thread)
        for url in headerfile.PROXY_URL:
            try:
                t1 = threading.Thread(target=self.run, args=(url,))
                threads.append(t1)
            except Exception, e:
                print "线程创建错误"
        for t in threads:
            try:
                # t.setDaemon(False)
                t.start()
                # t.join()
                print "线程启动成功"
            except Exception, e:
                print "线程启动出错"






if __name__ == "__main__":  # 相当于c语言中的main()函数
    myspider = Ip_spider()
    # myspider.Ip_Proxy_State()
    myspider.Get_ip_main()

