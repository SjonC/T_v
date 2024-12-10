import requests
import json
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import socket
from requests.packages.urllib3.util.connection import create_connection
from urllib.parse import urlparse

# 设置全局 socket 超时
def set_global_timeout(timeout):
    def patched_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, *args, **kwargs):
        if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
            timeout = timeout
        return create_connection(address, timeout=timeout, *args, **kwargs)

    requests.packages.urllib3.util.connection.create_connection = patched_create_connection


set_global_timeout(5)
def check_m3u8_url(url,isLog):
    print(url)
    with open('blackList.json', 'r', encoding='utf-8') as file:
        jsonString = file.read()
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.split(':')[0] 
    blackList = json.loads(jsonString)
    if url in blackList or domain in jsonString:
        print("黑名单 链接无效")
        return False,11
    try:
        start_time = time.time()
        # 设置请求头模拟浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
        }
        session = requests.Session()
        retry = Retry(connect=0, backoff_factor=0)  # 禁用重试
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        response = session.get(url, headers=headers,stream=True,timeout=(5, 5), allow_redirects=False)
        latency = time.time() - start_time
        if latency > 3.5:
            with open('timeout.txt', 'a+', encoding='utf-8') as file:
                file.write(url+"\n")
            return False,99
        content_length = response.headers.get('Content-Length')
        content = ""
        if content_length is None:
            chunkIndex = 0
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                chunkIndex +=1
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')
                if chunkIndex == 1:
                    content =  chunk
                if isLog:
                    print("chunk", chunk)
                if chunkIndex>10:
                    return False ,latency
                if "#EXTINF" in chunk or "#EXTM3U" in chunk:
                    if isLog:
                        print(f"链接有效1，延迟: {latency:.2f} 秒")
                    return True,latency
                 

        if content_length and int(content_length) > 10 * 1024 * 1024:  # 限制 10MB
            print("文件过大，跳过处理")
            return False,latency
        if isLog:
            print(response.status_code,response.headers.get("Content-Type", ""),content)
        if response.status_code == 302:
            with open('302.txt', 'a+', encoding='utf-8') as file:
                file.write(url+"\n")
            if isLog:
                print("  链接有效")
            return True,latency
        
        if response.status_code == 200 and "application/vnd.apple.mpegurl" in response.headers.get("Content-Type", ""):
            if isLog:
                print(f"链接有效，延迟: {latency:.2f} 秒")
            return True,latency
        else:
            print(response.status_code,"  链接无效")
            if response.status_code == 200:
                with open('other.txt', 'a+', encoding='utf-8') as file:
                    file.write(str(response.status_code)+" "+url+"\n")
            blackList.append(url)
            with open('blackList.json', 'w', encoding='utf-8') as file:
                json.dump(blackList, file, ensure_ascii=False, indent=4) 
            
            return False,999

    except requests.exceptions.RequestException as e:
        if isLog:
            print(f"请求失败: {e}")
        blackList.append(url)
        with open('blackList.json', 'w', encoding='utf-8') as file:
            json.dump(blackList, file, ensure_ascii=False, indent=4) 
        return False,999

def getUrls(urlStr):
    try: 
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
        }
        response = requests.get(urlStr, headers=headers, timeout=30)
 
        if response.status_code == 200:
            
            urlString = response.text
            alllines = urlString.split("\n")
            allUrl = []
            CCTV = []
            weishi = []
            movices = []
            others = []
            TVBs = []
            lives = []
            体育 = []
            index = 0
            for line in alllines:
                if "," in line and "http" in line and "//[" not in line:
                    array = line.split(",") 
                    if len(array)==2:
                        url = array[1]
                        url= url.replace("\n", "").replace(" ", "").replace("\t", "")
                        name = array[0]
                        isGoodUrl,latency = check_m3u8_url(url,False)
                        if(isGoodUrl):
                            hasName = False
                            if name.startswith("CCTV"):
                                for di in CCTV:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    CCTV.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            elif "卫视" in name:
                                for di in weishi:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    weishi.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            elif "电影" in name:
                                for di in movices:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    movices.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            elif "直播" in name:
                                for di in lives:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    lives.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            elif "TVB" in name or "无线" in name or "翡翠台" in name:
                                for di in TVBs:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    TVBs.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            elif "体育" in name or "球" in name :
                                for di in 体育:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    体育.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})
                            
                            else:
                                for di in others:
                                    diName = di["name"]
                                    if name == diName:
                                        hasName = True
                                        sourcess = di["sources"]
                                        urls = [source["url"] for source in sourcess]
                                        if url not in urls:
                                            di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url,"latency":latency})
                                        break
                                if hasName is False:
                                    others.append({"name":name,"sources":[{"name":"源1","url":url,"latency":latency}]})


            order = ["CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5","CCTV6", "CCTV7", "CCTV8", "CCTV9", "CCTV10","CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15","CCTV16","CCTV17","CCTV18","CCTV19","CCTV20","CCTV5+","CCTV4K","CCTV8K","CCTV16(4K)","CCTV+"]
            CCTVs = sorted(CCTV, key=lambda x: order.index(x["name"]) if x["name"] in order else float('inf'))
            allUrl.append({"name":"CCTV","channel":CCTVs})
            allUrl.append({"name":"TVB","channel":TVBs})
            allUrl.append({"name":"卫视","channel":weishi})
            allUrl.append({"name":"电影","channel":movices})
            allUrl.append({"name":"体育","channel":体育})
            allUrl.append({"name":"直播","channel":lives})
            allUrl.append({"name":"其他","channel":others})
            for dic in allUrl:
                channel = dic['channel']
                for dit in channel:
                    sources = dit['sources']
                    sources.sort(key=lambda x: x['latency'])
                    i = 1
                    for obj in sources:
                        obj['name'] = '源'+str(i) 
                        i +=1

            with open('allUrls.json', 'w', encoding='utf-8') as file:
                json.dump(allUrl, file, ensure_ascii=False, indent=4) 
            for dic in allUrl:
                channel = dic['channel']
                for dit in channel:
                    sources = dit['sources']
                    sources.sort(key=lambda x: x['latency'])
                    i = 1
                    for obj in sources:
                        # obj['name'] = '源'+str(i)
                        obj.pop('latency')
                        i +=1
            channels = allUrl[:7]
            config = {
                "appversion": "103", 
                "apkUrl":"https://gitee.com/Csjon/apks/raw/master/app-release.apk",
                "channels":  channels
            }
            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False,separators=(',', ':'))
            
            return True
        

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        getUrls('https://live.iptv365.org/live.txt')
        


getUrls("https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt")

# check_m3u8_url("https://fanmingming.com/fm?id=843",True)


# with open('allUrls2.json', 'r', encoding='utf-8') as file:
#     jsonString = file.read()

# allUrls = json.loads(jsonString)
# config = {
#     "appversion": "103", 
#     "apkUrl":"https://gitee.com/Csjon/apks/raw/master/app-release.apk",
#     "channels":  allUrls
# }
# with open('config1.json', 'w', encoding='utf-8') as file:
#     json.dump(config, file, ensure_ascii=False, separators=(',', ':'))

# with open('allUrls2.json', 'r', encoding='utf-8') as file:
#     jsonString = file.read()
# allUrl = []
# allUrls = json.loads(jsonString)
# CCTV = []
# weishi = []
# movices = []
# others = []
# TVBs = []
# lives = []
# 体育 = []
# for dic in allUrls:
#     name = dic["name"]
#     sources = dic["sources"][0] 
#     hasName = False
#     if name.startswith("CCTV"):
#         for di in CCTV:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             CCTV.append({"name":name,"sources":[{"name":"源1","url":url}]})
#     elif "卫视" in name:
#         for di in weishi:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             weishi.append({"name":name,"sources":[{"name":"源1","url":url}]})
#     elif "电影" in name:
#         for di in movices:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             movices.append({"name":name,"sources":[{"name":"源1","url":url}]})
#     elif "直播" in name:
#         for di in lives:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             lives.append({"name":name,"sources":[{"name":"源1","url":url}]})
#     elif "TVB" in name or "无线" in name or "翡翠台" in name:
#         for di in TVBs:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             TVBs.append({"name":name,"sources":[{"name":"源1","url":url}]})
#     elif "体育" in name or "球" in name :
#         for di in 体育:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             体育.append({"name":name,"sources":[{"name":"源1","url":url}]})
    
#     else:
#         for di in others:
#             diName = di["name"]
#             if name == diName:
#                 hasName = True
#                 sourcess = di["sources"]
#                 urls = [source["url"] for source in sourcess]
#                 if url not in urls:
#                     di["sources"].append({"name":"源"+str(len(sourcess)+1),"url":url})
#                 break
#         if hasName is False:
#             others.append({"name":name,"sources":[{"name":"源1","url":url}]})


# order = ["CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5","CCTV6", "CCTV7", "CCTV8", "CCTV9", "CCTV10","CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15","CCTV16","CCTV17","CCTV18","CCTV19","CCTV20","CCTV5+","CCTV4K","CCTV8K","CCTV16(4K)","CCTV+"]
# CCTVs = sorted(CCTV, key=lambda x: order.index(x["name"]) if x["name"] in order else float('inf'))


# allUrl.append({"name":"CCTV","channel":CCTVs})
# allUrl.append({"name":"卫视","channel":weishi})
# allUrl.append({"name":"电影","channel":movices})
# allUrl.append({"name":"TVB","channel":TVBs})
# allUrl.append({"name":"体育","channel":体育})
# allUrl.append({"name":"直播","channel":lives})
# allUrl.append({"name":"其他","channel":others})

# with open('allUrls.json', 'w', encoding='utf-8') as file:
#     json.dump(allUrl, file, ensure_ascii=False, indent=4) 