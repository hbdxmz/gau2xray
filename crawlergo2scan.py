# coding:UTF-8
import simplejson, json
import subprocess, random, time, requests


headers_list = [
    {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12A365 MicroMessenger/5.4.1 NetType/WIFI'},
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36 MicroMessenger/6.0.0.54_r849063.501 NetType/WIFI'},
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36'},
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; d0xing-hackerone) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76'},
]

# 将已爬取过的url放入集合
loaded_urls_set = set()

# 读取已爬取的URL到集合中
with open('爬取过的urls.txt', 'r', encoding="utf-8") as f:
    for line in f:
        loaded_urls_set.add(line.strip())


# 检查 URL 是否已爬取过
def is_url_loaded(url):
    return url in loaded_urls_set


file_path = r"url.txt"  # 待爬取url文件路径
with open(file_path, "r", encoding="utf-8") as file:
    urls = file.readlines()

try:

    start_time = time.time()
    count = 1
    # 将req_urls保存到文件
    output_file = "urls爬取结果.txt"
    with open(output_file, "a", encoding="utf-8") as resultfile, open("爬取过的urls.txt", "a", encoding="utf-8") as loaded:
        for url in urls:
            target = url.strip()  # 去除换行符和空格
            if is_url_loaded(target):
                print(f"URL already loaded: {url}")
                continue

            print(f"crawler加载第{count}个url:{target}")
            count = count + 1
            # 将爬取过的url保存到文件"
            loaded.write(target + '\n')

            cmd = ["crawlergo_win_amd64.exe","-c",
                   "D:\chrome-win\chrome.exe","--push-to-proxy","http://127.0.0.1:7777",
                       "--custom-headers",json.dumps(random.choice(headers_list)),"-o", "json","-t", "20", target]

            rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = rsp.communicate()
            result = simplejson.loads(output.decode().split("--[Mission Complete]--")[1])
            req_list = result["all_req_list"]
            for req in req_list:
                print(req['url'])
                # 排除掉wss:// data://image/这些无效url
                if ('wss://' not in req['url']) and ("data://image/" not in req['url']):
                    resultfile.write(req['url'] + "\n")

            end_time = time.time()
            # 计算程序运行时间（单位：秒）
            run_time = end_time - start_time
          
            days = run_time // (24 * 3600)
            hours = (run_time % (24 * 3600)) // 3600
            minutes = ((run_time % (24 * 3600)) % 3600) // 60
            print(f"crawler运行时间：{int(days)}天 {int(hours)}小时 {int(minutes)}分钟")
          
            rsp.wait()  # 等待子进程结束
            time.sleep(0.5)

except Exception as e:
    print(e)
    msg = "crawlergo出现未知异常，去看看吧"
    print(msg)
