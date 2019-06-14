import requests
import re
from xlwt import Workbook
import xlrd
import time
import json
from datetime import datetime
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler

cookie_str='你自己的cookie字符串'
# 把cookie字符串处理成字典，以便接下来使用
cookies = {}
for line in cookie_str.split(';'):
    key, value = line.split('=', 1)
    cookies[key] = value
header = {
    'referer':'你自己的',
    "User-Agent":"你自己的"
}

mycartnames=['想要搜索的商品']

def parse_timestamp(time_stamp, flag=True):
    """
    把时间戳转换为时间字符串
    :param time_stamp: 时间戳
    :param flag: 标志位，可以指定输出时间字符串的格式
    :return: 时间字符串,格式为：2019-01-01 12:12:12 或 2019-01-01
    """
    localtime = time.localtime(time_stamp)
    if flag:
        time_str = time.strftime("%Y_%m_%d_%H", localtime)
    else:
        time_str = time.strftime("%Y_%m_%d", localtime)
    return time_str
    
 def key_name(number,name):
    try:
        URL_1 = "https://s.taobao.com/search?ie=utf8&initiative_id=staobaoz_20170905&stats_click=search_radio_all%3A1&js=1&imgfile=&q="
        URL_2 = "&suggest=0_1&_input_charset=utf-8&wq=u&suggest_query=u&source=suggest&p4ppushleft=5%2C48&s="
        URL = (URL_1 + name + URL_2 + str(number))
        # print(URL)
        res = requests.get(URL, timeout=30, headers=header, cookies=cookies)
        return res.text
    except Exception as e:
        return False

def replacestr(str):
    str=''.join(str.split())
    return str
def find_date(text):
    #step1=text.split('</script>')
    text=replacestr(text.strip())
    print(text)
    step1 = re.findall("(?<=<script>)g_page_config.*?(?=</script>)", text, re.A)
    print(step1)
    if step1 !=None and len(step1)>0:
        step2=step1[0].split('};')

        res=step2[0].replace('g_page_config=','')
        #判断结尾是否多了或者少了}
        if res.endswith('}}}')==True:

            return json.loads(res[:-1])
        if res.endswith('}}}')==True:

            return json.loads(res)

        return json.loads(res+'}')

    return None
    
import redis
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)   # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
r = redis.Redis(connection_pool=pool)
pointkey='taobao_goods_'

def gettimef(flag):
    return parse_timestamp(time.time(),flag)
def redis_data(info, name):
    try:
        global timef, timef_d
        name=replacestr(name)
        arr = info['mods']['itemlist']['data']['auctions']
        errornid=''
        getar= [elem for elem in arr if replacestr(elem['raw_title']) == name]#一层检索
        if getar==None or len(getar)==0:#二重检索
            print(name)
            print('again')
            for d in arr:
                name = replacestr(name)
                d['raw_title']=replacestr(d['raw_title'])

                if name in d['raw_title'] or  d['raw_title'] in name:

                    errornid=str(d['nid'])
                  
                    item={
                        'nid':d['nid'],
                        'view_price': d['view_price'],
                        'title': d['raw_title']
                    }
                    r.hset(pointkey+name+timef, timef_d+'_'+d['nid'],
                           json.dumps(item, ensure_ascii=False).encode("utf-8", 'ignore'))
        else:
            print(name)
            d=getar[0]
            errornid = str(d['nid'])
            item = {
                'nid': d['nid'],
                'view_price': d['view_price'],
                'title': d['raw_title']
            }

            r.hset(pointkey + name+timef,timef_d+'_'+ d['nid'],
                   json.dumps(item, ensure_ascii=False).encode("utf-8", 'ignore'))
    except Exception as e:
        print('error======================================')
        r.hset('taobao_goods_error%s%s' % (name,timef ), errornid,str(e))
    return name
    
timef = gettimef(False)
timef_d = gettimef(True)
def main():
    global timef,timef_d
    timef = gettimef(False)#因为用了后台定时任务，这里要每次去重新取时间，不能直接用全局的时间
    timef_d = gettimef(True)#
    print(timef)
    for name in mycartnames:

        text = key_name(0, name)#因为是按照名称去找商品，第0页就可以找到我的商品
        if text==False:
            # scheduler.shutdown()
            # bup()
            break
        info = find_date(text)

        if info == None:
            continue

        redis_data(info, name)
        
import winsound
def sound(hz):
    duration = 500  # millisecond
    freq = hz  # Hz
    winsound.Beep(freq, duration)

def bup():
    while True:
        sound(840)
        
scheduler = None
if __name__ == '__main__':
    #main()
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(main, 'interval', seconds=120)
    
    scheduler.start() # 非阻塞
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        # 其他任务是独立的线程执行
        while True:
            time.sleep(12)
            sound(440)
            print('heart')
    except Exception:
        scheduler.shutdown()
        bup()
        print('Exit The Job!')