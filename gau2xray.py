import concurrent.futures
import threading
import queue
import random
import time
import os
from playwright.sync_api import sync_playwright

proxy_server = "http://127.0.0.1:7777"  # 替换为实际的xray IP 和端口

# 读取gau处理结果中的url
with open(r'gau_urls.txt', 'r', encoding='utf-8') as file:
    urls = file.readlines()

# 随机化 URL 列表，因为有时候gau_urls中有连续多个相同域名的url，随机化后能在不同url间检测
random.shuffle(urls)

# 创建线程安全的队列和计数器
loaded_urls_queue = queue.Queue()
counter = 0

# 检查 URL 是否已扫描过，因为url数量很多时，一次可能扫不完
loaded_urls_set = set()

# 读取已扫描过的 URL 到集合中
with open('loaded_urls.txt', 'r', encoding='utf-8') as f:
    for line in f:
        loaded_urls_set.add(line.strip())


# 检查 URL 是否已经加载
def is_url_loaded(url):
    return url in loaded_urls_set


# 创建 Playwright 实例
def process_url(url):
    if is_url_loaded(url):
        print(f"URL already loaded: {url}")
        return None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(proxy={'server': proxy_server},headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url)
            # 在这里执行页面操作
            print(f"Loaded URL: {url}")

            # 将已加载的 URL 添加到队列中
            loaded_urls_queue.put(url)

            # 将已加载的 URL 写入文件_loaded_urls
            with open('loaded_urls.txt', 'a', encoding='utf-8') as f:
                f.write(url + '\n')

            # 添加更长的加载时间
            time.sleep(0.8)  # 延迟一会再加载下一个URL

            return url  # 返回已加载的 URL

        except Exception as e:
            print(f"Exception occurred while loading URL: {url}")
            print(e)

        finally:
            page.close()
            context.close()
            browser.close()

    return None  # 返回 None 表示加载失败


# 在程序退出前确保所有浏览器进程被关闭


# 实时显示已加载的 URL 数量
def display_loaded_count():
    global counter
    while True:
        counter = loaded_urls_queue.qsize()
        print(f"Loaded URLs: {counter}")
        time.sleep(0.8)


# 设置一个定时器，在 *** 秒后引发 KeyboardInterrupt 异常
def timeout_handler():
    time.sleep(10000)
    os._exit(0)


# 创建线程池，使用多线程并行处理 URL，max_workers为chromium浏览器实例数量
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    # 提交任务
    futures = [executor.submit(process_url, url.strip()) for url in urls]

    # 创建并启动实时显示线程
    display_thread = threading.Thread(target=display_loaded_count)
    display_thread.start()

    # 创建定时器线程，在指定时间后引发 KeyboardInterrupt 异常退出程序，主要用于扫描大量目标URL费时较久，用于控制扫描时间
    timer_thread = threading.Thread(target=timeout_handler)
    timer_thread.start()

    # 迭代已完成的任务
    try:
        for future in concurrent.futures.as_completed(futures):
            # 获取任务的结果
            result = future.result()
            if result is not None:
                print(f"ok")
    except KeyboardInterrupt:
        print("Timeout: Program terminated.")
        os._exit(0)


    # 等待显示线程和定时器线程结束
    display_thread.join()
    timer_thread.join()

print("All URLs processed.")
