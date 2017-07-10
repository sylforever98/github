# -*- coding: utf-8 -*-
import chardet
import string
import cookielib
import traceback
from collections import deque
import time
import json
import random
import re
import headerfile
from selenium import webdriver
import requests
import threading
import inspect
import ctypes
import os
import sys
import urllib2
from selenium import webdriver
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
GET_NUM = 10000000
# 检测是否发生了 Redirect 动作
class RedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        pass

    def http_error_302(self, req, fp, code, msg, headers):
        pass


# 代理设置
enable_proxy = True


# ----------- 处理页面上的各种标签 -----------
class HTML_Tool:
    # 用非 贪婪模式 匹配 \t 或者 \n 或者 空格 或者 超链接 或者 图片
    BgnCharToNoneRex = re.compile("(\t|\n| |<a.*?>|<img.*?>)")

    # 用非 贪婪模式 匹配 任意<>标签
    EndCharToNoneRex = re.compile("<.*?>")

    # 用非 贪婪模式 匹配 任意<p>标签
    BgnPartRex = re.compile("<p.*?>")
    CharToNewLineRex = re.compile("(<br/>|</p>|<tr>|<div>|</div>)")
    CharToNextTabRex = re.compile("<td>")

    # 将一些html的符号实体转变为原始符号
    replaceTab = [("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"), ("&amp;", "\""), ("&nbsp;", " ")]

    def Replace_Char(self, x):
        x = self.BgnCharToNoneRex.sub("", x)
        x = self.BgnPartRex.sub("\n    ", x)
        x = self.CharToNewLineRex.sub("\n", x)
        x = self.CharToNextTabRex.sub("\t", x)
        x = self.EndCharToNoneRex.sub("", x)

        for t in self.replaceTab:
            x = x.replace(t[0], t[1])
        return x


def utf82gbk(s):
    return s.decode('utf-8', 'ignore').encode('gbk')


class Baidu_Spider:
    # 申明相关的属性
    def __init__(self):
        self.myUrl  = deque()
        self.datas = []
        self.myTool = HTML_Tool()
        self.closetable = []
        self.tie_page_num = 0
        self.Read_into_closetable()
        self.Read_url()
        self.num = 0
        print u'已经启动百度贴吧爬虫...'

    # 开启代理
    def set_proxy_handler(self, IPPROXY):
        # proxy_handler = urllib2.ProxyHandler({"http": 'http://some-proxy.com:8080'})
        proxy_handler = urllib2.ProxyHandler(IPPROXY)
        null_proxy_handler = urllib2.ProxyHandler({})

        if enable_proxy:
            proxy_handler = urllib2.ProxyHandler(IPPROXY)
            opener = urllib2.build_opener(proxy_handler)
        else:
            opener = urllib2.build_opener(null_proxy_handler)

        urllib2.install_opener(opener)

    def Write_into_closetable(self,url):
        if not os.path.exists('Url_log.txt'):
            output = open('Url_log.txt', 'w')
        else:
            output = open('Url_log.txt', 'a')
        try:
            output.write(url)
            output.write('\n')
        finally:
            output.close()
    def Write_url(self,url):
        if not os.path.exists('Url.txt'):
            output=open('Url.txt', 'w')
        else:
            file = open('IP.txt', 'r')
            try:
                text = file.read()
            finally:
                file.close()
            output = open('Url.txt', 'a')
            try:
                if json.dumps(url) not in text:
                    output.write(json.dumps(url))
                    output.write('\n')
                else:
                    print u"Ip已存在"
            finally:
                output.close()

    def Read_url(self):
        print u"读入url"
        if not os.path.exists('Url.txt'):
            file = open('Url.txt', 'w')
        else:
            file = open('Url.txt', 'r')
        for line in file.readlines():
            self.myUrl.append(line.strip().replace('"',''))

    def Read_into_closetable(self):
        print u"读入closetable"
        if not os.path.exists('Url_log.txt'):
            file = open('Url_log.txt', 'w')
        else:
            file = open('Url_log.txt', 'r')
        for line in file.readlines():
            self.closetable.append(line.strip())

    # 初始化加载页面并将其转码储存
    def get_baidu_tieba(self,url):
        opener = urllib2.build_opener(RedirectHandler)
        response = opener.open(url)
        geturl = response.geturl()
        print geturl
        myPage = response.read()
        # 计算楼主发布内容一共有多少页
        endPage = self.page_counter(myPage)
        # 获取该帖的标题
        title = self.find_title(myPage)
        print '文章名称：' + title
        # 获取最终的数据
        self.save_data(url, title, endPage)

        #获取楼层内信息
    def baidu_tieba(self):
       while  1:
           if  self.myUrl:
               url =self.myUrl.popleft()
               print url
               self.get_baidu_tieba(url)
               self.num+=1




    # 用来计算一共有多少页
    def page_counter(self, myPage):
        # 匹配 "共有<span class="red">12</span>页" 来获取一共有多少页
        myMatch = re.search(r'class="red">(\d+?)</span>', myPage, re.S)
        if myMatch:
            endPage = int(myMatch.group(1))
            print u'log：共有%d页的原创内容' % endPage
        else:
            endPage = 0
            print u'log：无法计算发布内容有多少页！'
        return endPage
    #找出该贴吧共有多少页帖子
    def tie_counter(self, myPage):
        # 匹配 "<a href="//tieba.baidu.com/f?kw=%E5%A4%A7%E8%BF%9E%E6%B5%B7%E4%BA%8B%E5%A4%A7%E5%AD%A6&amp;ie=utf-8&amp;pn=96600" class="last pagination-item ">尾页</a>" 来获取尾页内容
        lastpage = re.search(r'class="th_footer_l">(.*?)个', myPage, re.S)

        if lastpage:
            lastpage = re.search(r'"red_text">(\d+?)</span>', str(lastpage.group(1)), re.S)
            if lastpage :
                 endPage = int(lastpage.group(1))
            # endPage = int(lastpage.group(1))
        else:
            endPage = 0
            print u'log：无法计算该帖吧有多少页！'
        return endPage
    # 用来寻找该帖的标题
    def find_title(self, myPage):
        # 匹配 <h1 class="core_title_txt" title="">xxxxxxxxxx</h1> 找出标题
        myMatch = re.search(r'<h1.*?>(.*?)</h1>', myPage, re.S)
        title = u'暂无标题'
        if myMatch:
            title = myMatch.group(1)
        else:
            print u'log：无法加载文章标题！'
        # 文件名不能包含以下字符： \ / ： * ? " < > |
        title = title.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"',
                                                                                                                    '').replace(
            '>', '').replace('<', '').replace('|', '')
        return title

    # 用来存储楼主发布的内容
    def save_data(self, url, title, endPage):
        # 加载页面数据到数组中
        self.get_data(url, endPage)
        # 打开本地文件
        if not os.path.exists('dongbeicaijingdatatime1.txt'):
            file = open('dongbeicaijingdatatime1.txt', 'w')
        else:
            file = open('dongbeicaijingdatatime1.txt', 'a')
            file.writelines(self.datas)
            file.close()
        print u'log：文件已写入txt文件'




    # 获取页面源码并将其存储到数组中
    def get_data(self, url, endPage):
        cookie = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        print u'log：加载中...'
        response = opener.open(url)
        code = response.geturl()
        print code
        myPage = response.read()
        self.deal_data(myPage)
        # 从第二页开始爬取
        url = url + '?pn='
        for i in range(2, endPage + 1):
            url = url + str(i)
            response = opener.open(url)
            code_stats = response.geturl()
            print code_stats
            myPage = response.read()
            # 判断是否成功获取网页信息
            if code_stats == url:
                print u'获取成功'
            else:
                print u'获取失败-。-'
            self.deal_data(myPage)

    # 将内容从页面代码中抠出来
    def deal_data(self, myPage):
        myItems = re.findall('<div class="l_post j_l_post l_post_bright(.*?)<div class="clear"></div></div>', myPage,
                             re.S)
        for ite in myItems:
            # print ite
            details = re.findall('id="post_content.*?>(.*?)</div>', ite, re.S)
            times = re.findall('date&quot;:&quot;(.*?)&quot;', ite, re.S)
            floors = re.findall('post_no&quot;:(.*?),&quot;', ite, re.S)
            userids = re.findall("user_id&quot;:(.*?),&quot;user_name", ite, re.S)
            usernames = re.findall("user_name&quot;:&quot;(.*?)cccrr&quot;,&quot;name_u&", ite, re.S)
            usersexs = re.findall("user_sex&quot;:(.*?),&quot;", ite, re.S)

            if userids:
                for userid in userids:
                    userid = self.myTool.Replace_Char(userid.replace("\n", ""))
                    print userid
            else:
                userid = 'userid'


            if floors:
                for floor in floors:
                    floor = self.myTool.Replace_Char(floor.replace("\n", ""))
                    print floor
            else:
                floor = 'floor'

            if times:
                for time in times:
                    time = self.myTool.Replace_Char(time.replace("\n", ""))
                    print time
            else:
                time = 'time'


            if details:
                for detail in details:
                    detail = self.myTool.Replace_Char(detail.replace("\n", ""))
                    print detail
            else:
                detail = 'detail'

            if usersexs:
                for usersex in usersexs:
                    usersex = self.myTool.Replace_Char(usersex.replace("\n", ""))
                    print usersex
            else:
                usersex = 'usersex'

            self.datas.append(detail + '\t'+time+ '\t'+floor+ '\t'+userid+ '\t'+usersex+'\n')

    #获取帖子内容
    def get_Html_Data(self, url):
        userAgent = headerfile.USER_AGENTS
        time.sleep(random.uniform(0.5, 1.6))
        if url not in self.closetable:
            request = urllib2.Request(url)
            request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            request.add_header('User-Agent', random.choice(userAgent))
            proxy_handler = urllib2.ProxyHandler(random.choice(self.readIp()))
            urllib2.build_opener(proxy_handler)
            response = urllib2.urlopen(request,timeout=5)
            if response.geturl() == url:
                htmlpage = response.read()
                self.get_tie(htmlpage)
                return htmlpage
            else:
                return 0
                print '获取网页出错'
        else:
            print '已获取过该网页'

    def main_in(self,url):
        htmlpage = self.get_Html_Data(url)
        self.tie_page_num = self.tie_counter(htmlpage) / 50
        url = url + '&ie=utf-8&pn='
        for i  in range(1, self.tie_page_num):
            in_url = url + str(i*50)
            self.get_Html_Data(in_url)
            self.Write_into_closetable(in_url)
            print in_url
    #获取帖子链接
    def get_tie(self,htmlpage):
        # <a href="/p/5208053884" title="朋友过个招？" target="_blank" class="j_th_tit ">朋友过个招？</a>
        print '获取网页'
        htmlpage = htmlpage.decode('utf-8')#----------------------------------有问题需要修改（UnicodeDecodeError: 'utf8' codec can't decode bytes in position 151173-151174: invalid continuation by）
        tie_nums = re.findall('<a href="/p/(.*?)" title="', htmlpage, re.S)
        for num in tie_nums:
            bdurl = 'http://tieba.baidu.com/p/' + num
            self.myUrl.append(bdurl)
            self.Write_url(bdurl)
            print '写入链接' + bdurl

    #读取IP
    def readIp(self):
            ipresult = []
            file = open('IP.txt', 'r')
            for line in file.readlines():
                proxies = {'http': line}
                ipresult.append(proxies)
            return ipresult
    def thread_in(self,main_url):
        t1 = threading.Thread(target=self.main_in, args=(main_url,))
        t1.setDaemon(False)
        t1.start()
        for i in range(1,60):
            t2 = threading.Thread(target=self.baidu_tieba, args=())
            t2.setDaemon(True)
            t2.start()
        print self.num


# -------- 程序入口处 ------------------

# 以某吧为例子
if __name__ == "__main__":  # 相当于c语言中的main()函数
    name = '贴吧名字'
    main_url = 'http://tieba.baidu.com/f?kw='+name
    mySpider = Baidu_Spider()
    mySpider.thread_in(main_url)



