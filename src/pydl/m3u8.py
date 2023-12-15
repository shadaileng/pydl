# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import logging
import os
import time
import base64

from aiohttp import ClientSession
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector

from .api import task_creat, task_comsume, task_status, download_mini, size
from .utils import parse_url, resource_path, resource_name, resource_dir, loaddata


async def parse_m3u8(url: str, path: str, session: ClientSession, result: list=[])->bool:
    """
    Parses a m3u8 playlist file.
    """
    path_bak = path + ".bak"
    if not os.path.exists(path_bak):
        # 下载m3u8文件
        if not await download_mini(url, path_bak, session):
            return False
    with open(path_bak, 'r') as src:
        data = src.read()
    if not data.startswith("#EXTM3U"):
        data = base64.b64decode(data).decode()
    data = data.split('\n')
    url_data = parse_url(url)
    relate_path = resource_dir(path)
    contents = []
    for line in data:
        line = line.strip()
        content = line
        if line.startswith("#EXT-X-KEY"):
            key_uri = [item for item in line[10:].split(",") if item.startswith("URI")]
            if len(key_uri) == 1:
                key_uri = key_uri[0][5:-1]
                content = content.replace(key_uri, resource_name(key_uri))
                if not key_uri.startswith("http"):
                    if key_uri.startswith("/"):
                        key_uri = f"{url_data.scheme}://{url_data.netloc}{key_uri}"
                    else:
                        key_uri = f"{url_data.scheme}://{url_data.netloc}{resource_dir(url_data.path)}/{key_uri}"
                result.append({"url": key_uri, "path": f"{relate_path}/{content}"})
        if line.startswith("#EXTINF"):
            pass
        if not line.startswith("#"):
            line_uri = line
            if line.startswith("http"):
                content = resource_path(line)
                line_url_data = parse_url(line)
                if line_url_data.netloc == url_data.netloc:
                    content = line_url_data.path
                    if line_url_data.path.startswith(resource_dir(url_data.path)):
                        content = line_url_data.path[len(resource_dir(url_data.path))+1:]
            else:
                line_uri = f"{url_data.scheme}://{url_data.netloc}{resource_dir(url_data.path)}/{line}"
                if line.startswith("/"):
                    line_uri = f"{url_data.scheme}://{url_data.netloc}{line}"
                    content = line[1:]
                    if line.startswith(resource_dir(url_data.path)):
                        content = line[len(resource_dir(url_data.path))+1:]
            if ".ts" in line:
                result.append({"url": line_uri, "path": f"{relate_path}/{content}"})
            if ".m3u8" in line:
                await parse_m3u8(line_uri, f"{relate_path}/{content}", session, result)
        contents.append(content)
        if line.startswith("#EXT-X-ENDLIST"):
            with open(path, "w", encoding="utf-8") as f:
                f.write( "\n".join(contents) + "\n")
            break
    return True

async def download_m3u8(url: str, outputPath: str, *, proxy: str=None, timeout: int=300, chunkSize: int = 6059, threadNum: int = 22, verbose: bool=False):
    connector = TCPConnector(ssl=False)
    if proxy:
        logging.info(f'[+]proxy: {proxy}')
        connector = ProxyConnector.from_url(proxy, ssl=False)
    timeout = {'total': timeout, 'connect': None, 'sock_connect': None, 'sock_read': None}
    async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(**timeout)) as session:
        infos = loaddata(f"{outputPath}.json")
        if not infos:
            # 解析m3u8文件
            # infos = parse_m3u8(outputPath + ".bak")
            result = []
            await parse_m3u8(url, outputPath, session, result)
            # print(result)
            # 构建infos
            infos = {}
            for item in result:
                item_url = item["url"]
                info = {
                    "Key": item_url,
                    "Url": item_url,
                    "Output": item["path"],
                    "Start": 0,
                    "Length": 0,
                    "DownLen": 0,
                    "Scale": 0.0,
                    "Status": -1,
                    "Error": None,
                    "Retry": 10
                }
                infos[item_url] = info
            await calc_ts_size(outputPath, session, infos, threadNum, verbose=verbose)
        # logging.info(infos)
        # return        
        if len(infos) < threadNum:
            threadNum = len(infos)
        for key, info in infos.items():
            if info["Status"] in (-2, 0):
                info["Status"] = -1
                info["Retry"] = 10
                info["Error"] = None

        tasks = asyncio.Queue(threadNum)
        create = asyncio.Queue(threadNum)
        status = asyncio.Queue()
        download_tasks = []
        for index in range(threadNum):
            download_tasks.append(task_comsume(index, session, tasks, status, create))
        logging.info("开始下载")
        tasks_working = [task_creat(infos, threadNum, tasks, status, create), task_status(outputPath, infos, status, verbose=verbose)] + download_tasks
        await asyncio.gather(*tasks_working)
        logging.info("下载完成")

async def calc_ts_size(outputPath: str, session: ClientSession, infos: dict, threadNum: int, verbose: bool=False):
    """
    计算每个分片的大小
    """
    tasks = asyncio.Queue()
    status = asyncio.Queue()
    flag = []
    retry_time = {}
    async def _task_comsume():
        while not tasks.empty():
            info = await tasks.get()
            length, size_status = await size(info["Url"], session)
            if size_status:
                info["Length"] = length
            else:
                if retry_time[info["Key"]] > 0:
                    tasks.put(info)
            await status.put(info)
        flag.append(1)
        if len(flag) == threadNum:
            await status.put(None)
        
    for key, info in infos.items():
        retry_time[key] = 5
        await tasks.put(info)
    download_tasks = []
    for index in range(threadNum):
        download_tasks.append(_task_comsume())
    logging.info("开始获取文件大小")
    tasks_working = [task_status(outputPath, infos, status, verbose=verbose)] + download_tasks
    await asyncio.gather(*tasks_working)
    logging.info("获取文件大小完成")


def main_m3u8():
    from logger import getLogger
    getLogger()
    # url = "https://la3.killcovid2021.com/m3u8/907823/907823.m3u8"
    # url = "https://askzycdn.com/20231124/X55udrAS/2000kb/hls/index.m3u8"
    # url = "https://vip3.lbbf9.com/20231129/9PyUSSFA//700kb/hls/index.m3u8"	
    # url = "https://video56.zdavsp.com/video/20230613/6ab714fed9a9cb653d6eeec3937b70d6/index.m3u8"
    # url = "https://videozmwbf.0afaf5e.com/decry/vd/20231126/MDZhZmU0ND/151813/720/libx/hls/encrypt/index.m3u8"
    url = "https://la3.killcovid2021.com/m3u8/907759/907759.m3u8"

    outputPath = f"dist/{resource_path(url)}"
    start_time = time.time()
    asyncio.run(download_m3u8(url, outputPath, proxy="socks5://127.0.0.1:1080", verbose=True))
    logging.info(f"程序执行时间为 {time.time()-start_time} 秒")

if __name__ == '__main__':
    main_m3u8()