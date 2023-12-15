# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import logging
import os
import time

from aiohttp import ClientSession
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector

from .api import task_creat, task_comsume, task_status, download_mini, size
from .utils import resource_path, loaddata


async def newInfos(url: str, outputPath: str, length: int, chunkSize: int=6059)->dict:
    infos = {}
    chunks = length // chunkSize + 1 if length%chunkSize != 0 else length // chunkSize
    for index in range(chunks):
        start = index * chunkSize
        end = (index+1)*chunkSize - 1
        if end > length:
            end = length-1
        info = {
            "Key": index,
            "Url": url,
            "Output": outputPath,
            "Start": start,
            "Length": end - start+1,
            "DownLen": 0,
            "Scale": 0.0,
            "Status": -1,
            "Error": None,
            "Retry": 5
        }
        infos[index] = info
    if chunks == 0:
        infos[0] = {
            "Key": 0,
            "Url": url,
            "Output": outputPath,
            "Start": 0,
            "Length": 0,
            "DownLen": 0,
            "Scale": 0.0,
            "Status": -1,
            "Error": None,
            "Retry": 5
        }
    return infos


async def download(url: str, outputPath: str, *, proxy: str=None, timeout: int=300, chunkSize: int = 60590, threadNum: int = 22, verbose: bool=False):
    connector = TCPConnector(ssl=False)
    if proxy:
        logging.info(f'[+]proxy: {proxy}')
        connector = ProxyConnector.from_url(proxy, ssl=False)
    timeout = {'total': timeout, 'connect': None, 'sock_connect': None, 'sock_read': None}
    async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(**timeout)) as session:
        infos = loaddata(f"{outputPath}.json")
        if not infos:
            length, status = await size(url, session)
            # length = 14019
            # length, status = 0, True
            if not status:
                logging.warning(f'[-]failed to head: {url}')
                return
            if length < 0:
                length = 0
            if not os.path.exists(outputPath):
                if len(os.path.dirname(outputPath)) > 0 and not os.path.exists(os.path.dirname(outputPath)):
                    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
                fp = open(outputPath, "wb")
                fp.truncate(length)
                fp.close()
            infos = await newInfos(url, outputPath, length, chunkSize)
        # logging.info(infos)
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

async def download_sync(url: str, outputPath: str, *, proxy: str=None, timeout: int=300):
    connector = TCPConnector(ssl=False)
    if proxy:
        logging.info(f'[+]proxy: {proxy}')
        connector = ProxyConnector.from_url(proxy, ssl=False)
    timeout = {'total': timeout, 'connect': None, 'sock_connect': None, 'sock_read': None}
    async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(**timeout)) as session:
        return await download_mini(url, outputPath, session)

def main():
    from logger import getLogger
    getLogger()
    # url = "https://la3.killcovid2021.com/m3u8/907823/907823.m3u8"
    url = "https://askzycdn.com/20231124/X55udrAS/2000kb/hls/index.m3u8"
    # url = "https://la3.killcovid2021.com/m3u8/907823/9078230.ts"
    outputPath = f"dist/{resource_path(url)}"
    start_time = time.time()
    asyncio.run(download(url, outputPath, proxy="socks5://127.0.0.1:1080", verbose=True))
    # asyncio.run(download_sync(url, outputPath, proxy="socks5://127.0.0.1:1080"))
    logging.info(f"程序执行时间为 {time.time()-start_time} 秒")

if __name__ == '__main__':
    main()