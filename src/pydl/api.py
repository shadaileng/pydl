# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import logging
import os
import time
import copy
import base64

from .utils import byteunit, dumpdata
from aiohttp import ClientSession
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector

from typing import Callable



async def download_task(info: dict, session: ClientSession, processFunc: Callable=None, *, headers: dict={}, chunk_size: int=10240, task_id: int=-1):
    url, outputPath, length, start, downLen = info["Url"], info["Output"], info["Length"], info["Start"], info["DownLen"]
    start, end = start+downLen, start+length-1
    _headers = copy.deepcopy(headers)
    if start < end:
        _headers["Range"] = f"bytes={start}-{end}"
    try:
        logging.info(f"[{task_id}][+]{url}: {info['Key']}")
        async with session.get(url, headers=_headers) as resp:
            # logging.info(f"[{task_id}]{[url, _headers, resp.headers]}")
            if not os.path.exists(outputPath):
                if len(os.path.dirname(outputPath)) > 0 and not os.path.exists(os.path.dirname(outputPath)):
                    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
                fp = open(outputPath, "wb")
                fp.truncate(length)
                fp.close()
            with open(outputPath, "r+b") as fp:
                # 'Content-Range': 'bytes 2012939-2437419/2437420'
                range = resp.headers.get("Content-Range", None)
                _start = 0
                if range:
                    _start = int(range.split("/")[0].split("-")[0].split(" ")[1])
                fp.seek(_start, 0)
                while True:
                    chunk = await resp.content.read(chunk_size)
                    if not chunk:
                        break
                    fp.write(chunk)
                    downLen += len(chunk)
                    info["DownLen"] = downLen
                    info["Scale"] = downLen / length if length > 0 else 0.0
                    if processFunc is not None:
                        await processFunc(copy.deepcopy(info))
            info["Scale"] = 1.0
            info["Status"] = 1
            logging.info(f"[{task_id}][-]{url}: {info}")
            if processFunc is not None:
                await processFunc(copy.deepcopy(info))
    except Exception as e:
        logging.error(f"[{task_id}][-]{url}: {e}")
        info["Error"] = str(e)
        info["Status"] = -1
        if info["Retry"] - 1 <= 0:
            info["Status"] = -2
        info["Retry"] -= 1
        if processFunc is not None:
            await processFunc(copy.deepcopy(info))

async def size(url: str, session: ClientSession, *, headers: dict={})-> (int, bool):
    try:
        async with session.head(url, headers=headers) as resp:
            return int(resp.headers.get('Content-Length', '0')), True
    except Exception as e:
        logging.error(e)
        return 0, False

async def task_comsume(task_id: int, session: ClientSession, tasks: asyncio.Queue, status: asyncio.Queue, create: asyncio.Queue):
    while not tasks.empty():
        info = await tasks.get()
        if info is None:
            logging.info(f"tasks recive None, exit the task_comsume_{ task_id }")
            break
        if info["Status"] != 0:
            continue
        await download_task(info, session, status.put, task_id = task_id)
        await create.put(1)
    logging.info(f"task_comsume_{ task_id } exit")

async def task_creat(infos: dict, threadNum: int, tasks: asyncio.Queue, status: asyncio.Queue, create: asyncio.Queue):
    flag = True
    for key, info in infos.items():
        if info["Status"] == -1:
            flag = False
            info["Status"] = 0
            info["Error"] = None
            await tasks.put(info)
    
    while not flag:
        creat_info = await create.get()
        if creat_info is None: break
        flag = True
        for key, info in infos.items():
            if info["Status"] in (-1, 0):
                flag = False
                if info["Status"] == -1:
                    info["Status"] = 0
                    info["Error"] = None
                    await tasks.put(info)
    logging.info(f"task_creat exit")
    # 所有运行中任务已结束 关闭任务队列
    # logging.info(f"All download task finished, put {threadNum} None into tasks")
    # await asyncio.gather(*[tasks.put(None) for i in range(threadNum)])
    # 所有下载任务完成 关闭status队列
    logging.info("All download task finished, put None into status")
    await status.put(None)

async def task_status(outputPath: str, infos: dict, status: asyncio.Queue, *, verbose: bool=False, speed: dict={"now": 0.0, "last": 0.0, "nTotal": 0.0, "lTotal": 0.0}):
    while True:
        try:
            info = await asyncio.wait_for(status.get(), timeout=1)
            if info is None:
                logging.info("status recive None, exit the task_status")
                break
        except asyncio.TimeoutError:
            # print('timeout!')
            pass
        flag = True
        downLen, length, chunks, avaible = 0, 0, 0, 0
        complete, error = 0, 0
        for key, info in infos.items():
            if info["Status"] in (-1, 0):
                flag = False
                avaible += 1
            if info["Status"] == 1:
                complete += 1
            if info["Status"] == -2:
                error += 1
            downLen += info["DownLen"]
            length += info["Length"]
            chunks += 1
        
        if time.time() - speed["now"] > 0.5:
            speed["last"] = speed["now"]
            speed["lTotal"] = speed["nTotal"]
            speed["nTotal"] = downLen
            speed["now"] = time.time()
        dtl = (speed["nTotal"]-speed["lTotal"]) if (speed["nTotal"]-speed["lTotal"]) > 0 else 0
        speed_val = dtl/(speed["now"]-speed["last"]) if speed["now"] != speed["last"] else 0
        status_data = {
            "Output": outputPath,
            "Chunks": chunks,
            "Avaible": avaible,
            "Complete": complete,
            "Error": error,
            "Size": length,
            "DSize": downLen,
            "Speed": speed,
            "Scale": downLen/length if length > 0 else 0,
        }
        status_info = "Output: %s, Chunks: %d, Avaible: %d, Size: %d, DSize: %d, Speed: %s\t%.2f%%" % (outputPath, chunks, avaible, length, downLen, f"{byteunit(speed_val)}/s", downLen/length*100 if length > 0 else 0)
        if verbose:
            logging.info(status_info)
        # 缓存下载信息及状态
        dumpdata(f"{outputPath}.json", infos)
        dumpdata(f"{outputPath}.status", status_data)
        if flag: 
            logging.info(f"[+]Download Finished!")
            break

async def download_mini(url: str, path: str, session: ClientSession)->bool:
    """
    Downloads a small file.
    """
    length, status = await size(url, session)
    if not status:
        logging.warning(f'[-]failed to head: {url}')
        return
    DownLen = 0
    Status = -1
    if length <= 0:
        length = 0
    else:
        if os.path.exists(path):
            DownLen = os.path.getsize(path)
            if length == DownLen: 
                Status = 1
    info = {
        "Key": url,
        "Url": url,
        "Output": path,
        "Start": 0,
        "Length": length,
        "DownLen": DownLen,
        "Scale": 0.0,
        "Status": Status,
        "Error": None,
        "Retry": 5
    }
    if Status < 0:
        await download_task(info, session, None)
    if info["Status"] != 1:
        logging.warning(f'[-]failed to dowload: {url}, {info["Error"]}')
        return False
    return True
