import asyncio
import base64
import os
import urllib
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import traceback
import time

basic_url = "http://www.birdnet.cn/"
base_save_path = "./pic" # 图片保存父级目录
headers = {
    'Host': 'www.birdnet.cn',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cookie': 'Uy6T_2132_saltkey=r9v1lbpZ; Uy6T_2132_lastvisit=1554615809; Uy6T_2132_sid=DvAUaX; Uy6T_2132_sendmail=1; Hm_lvt_44bc9d6e0d240a547107872c37798d70=1554619410; Uy6T_2132_lastact=1554619566%09atlas.php%09show; Hm_lpvt_44bc9d6e0d240a547107872c37798d70=1554619567'
}

'''初始化爬虫'''
max_tries = 2  # 图片下载失败重试次数
max_tasks = 4  # 接口请求进程数
pic_tasks = 32  # 图片下载队列

# page_queue = asyncio.Queue(maxsize=64)  # 接口队列
page_list = [] # 接口列表
pic_queue = asyncio.Queue(maxsize=128)  # 图片队列
totals = 0 # 图片总数
count = 1 # 当前下载图片计数

if not os.path.exists(base_save_path):
    os.mkdir(base_save_path)

'''
初始化页面， 构造15个抓取页面URL地址，放入page_list中等待生产者提取
'''
def initPageList(bird_name):
    for page in range(1, 15):
        page_url = f"http://www.birdnet.cn/atlas.php?mod=show&action=atlaslist&searchType=1&all_name={bird_name}&page={page}"
        page_list.insert(0, page_url)

'''
使用aiohttp异步抓取的HTML抓取器
'''
async def getHTML(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60, headers=headers) as r:
                # await r.raise_for_status()
                html = await r.content.read()
                return html
    except:
        print("ERROR in getHTML().")
        traceback.print_exc()
        pass

"""
生产者协程，获得图片的url链接加入pic_url队列
"""
async def producer(_id):
    global totals

    try:
        #print(f'producer {_id}: running.')
        while len(page_list) > 0:
            page_url = page_list.pop()
            print(f"正在获取 {page_url} 的所有图片链接.")

            html = await getHTML(page_url)
            soup = BeautifulSoup(html, 'html.parser', from_encoding='iso-8859-1')

            # 解析html页面， 找到图片URL, 并放入队列中
            rs = soup.find("div", {"class": "picturel"}).find_all('img')
            for item in rs:
                raw_url = item.attrs['src']
                raw_split = raw_url.split('.')
                if raw_split[-2] == 'thumb':
                    raw_url = '.'.join(raw_split[:-2])
                #print('producer {}: added item {} to the queue'.format(_id, raw_url))
                totals += 1
                await pic_queue.put(raw_url)
        #print(f'producer {_id}: ending.')
    except:
        print("ERROR in producer().")
        traceback.print_exc()
        pass

"""
消费者协程，取出pic_url队列中的图片URL地址，配合使用syncio进行异步下载
"""
async def consumer(_id):
    global count
    #print(f"customer {_id}: running.")
    try:
        while True:
            pic_url = await pic_queue.get()

            # 在这个程序中 None 是个特殊的值，表示终止信号
            if pic_url is None: # is None:
                #print("队列空!")
                break

            else:
                """处理图片请求"""
                tries = 0

                save_path = file_dir + '/' + pic_url.split('/')[-1]
#                save_path = base_save_path + '/' + bird_name + '/' + pic_url.split('/')[-1]

                while tries < max_tries:
                    try:
                        if os.path.exists(save_path):  # 文件存在不再下载
                            print("图片已存在.")
                            count+=1
                            break
                        async with aiohttp.ClientSession() as session:
                            async with session.get(pic_url, timeout=60) as response:
                                async with aiofiles.open(save_path, 'wb') as f:
                                    await f.write(await response.read())
                                    print(f'图片下载成功 {count}/{totals} : {pic_url} ')
                                    count += 1
                                    break

                    except aiohttp.ClientError:
                        traceback.print_exc()
                        pass
                    tries += 1
        #print(f'consumer {_id}: ending')
    except:
        traceback.print_exc()

'''
 （暂时关闭）队列监视器， 返回队列的一些属性， 方便调试与观测实时数据；
'''
async def monitor(loop):
    while True:
        await asyncio.sleep(3)
        left_elem = pic_queue
        #print("Monitor: ", left_elem.qsize())
        print("Monitor", left_elem)
        # if count == totals:
        #     for task in asyncio.Task.all_tasks():
        #         task.close()
        #     loop.close()
        #     loop.stop()


async def run(loop, file_dir):
    # 先进行一下字符串编码转换，将其转换为Unicode with gbk
    name = urllib.parse.quote(bird_name, encoding='gbk')

    #初始化页面链接
    initPageList(name)

    # 调度生产者、消费者
    producers = [loop.create_task(producer(j)) for j in range(max_tasks)]
    consumers = [loop.create_task(consumer(i)) for i in range(pic_tasks)]

    # 等待生产者结束
    await asyncio.wait(producers)

    # 生产者完成任务后添加pic_tasks数量个None进入队列当中
    # 若当前消费者协程检测到当前从队列中获取的是None值， 即ending掉当前协程
    for i in range(pic_tasks):
         await pic_queue.put(None)

    # 等待监视器， 暂时关闭状态，若启用task将死锁
    #await monitor(loop)

    # 等待消费者结束
    await asyncio.wait(consumers)

    # jobs = asyncio.Task.all_tasks()
    # print(asyncio.gather(*jobs).cancel())  # 关闭线程方法，返回True

    # 所有tasks完成， 关闭所有协程
    for c in consumers:
        c.cancel()
    for p in producers:
        p.cancel()

if __name__ == '__main__':
    bird_name = input("请输入您想搜索的鸟类中文名称： ")
    # bird_name = "黑颈鸬鹚"

    file_dir = base_save_path + '/' + bird_name
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
        print(f"{bird_name}目录建立完成...")
    print(f"开始启动...\n当前启动协程数：抓取器 {max_tasks}；下载器{pic_tasks}\n")
    start = time.time()
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(run(event_loop, file_dir))
    except KeyboardInterrupt as e:
        event_loop.stop()

    finally:
        event_loop.close()

    end = time.time()
    print("Time used: ", end - start)
