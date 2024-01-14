# -*- coding: utf-8 -*-

import asyncio, time, logging
from pydl import api, utils, m3u8, download

def main_file():
    from pydl.logger import getLogger
    getLogger()
    # url = "https://la3.killcovid2021.com/m3u8/907823/907823.m3u8"
    # url = "https://askzycdn.com/20231124/X55udrAS/2000kb/hls/index.m3u8"
    url = "https://la3.killcovid2021.com/m3u8/907823/9078230.ts"
    outputPath = f"dist/{utils.resource_name(url)}"
    start_time = time.time()
    asyncio.run(api.download(url, outputPath, download.new_file_infos, proxy="socks5://127.0.0.1:1080", verbose=True))
    logging.info(f"程序执行时间为 {time.time()-start_time} 秒")

def main_m3u8():
    from pydl.logger import getLogger
    getLogger()
    # url = "https://la3.killcovid2021.com/m3u8/907823/907823.m3u8"
    # url = "https://askzycdn.com/20231124/X55udrAS/2000kb/hls/index.m3u8"
    # url = "https://vip3.lbbf9.com/20231129/9PyUSSFA/index.m3u8"
    # url = "https://vip3.lbbf9.com/20231129/9PyUSSFA//700kb/hls/index.m3u8"	
    # url = "https://video56.zdavsp.com/video/20230613/6ab714fed9a9cb653d6eeec3937b70d6/index.m3u8"
    # url = "https://videozmwbf.0afaf5e.com/decry/vd/20231126/MDZhZmU0ND/151813/720/libx/hls/encrypt/index.m3u8"
    url = "https://la3.killcovid2021.com/m3u8/907759/907759.m3u8"
    url = "https://jkunbf.com/20240109/893YFIza/2000kb/hls/index.m3u8"
    outputPath = f"dist/{utils.resource_path(url)}"
    start_time = time.time()
    result = asyncio.run(api.download(url, outputPath, m3u8.new_m3u8_infos, proxy="socks5://127.0.0.1:1080", verbose=True))
    logging.info(f"result: {result}")
    logging.info(f"程序执行时间为 {time.time()-start_time} 秒")


def parse_m3u8():
    from pydl.logger import getLogger
    getLogger()
    # url = "https://la3.killcovid2021.com/m3u8/907823/907823.m3u8"
    # url = "https://askzycdn.com/20231124/X55udrAS/2000kb/hls/index.m3u8"
    url = "https://vip3.lbbf9.com/20231129/9PyUSSFA/index.m3u8"
    url = "https://jkunbf.com/20240109/893YFIza/2000kb/hls/index.m3u8"
    outputPath = f"dist/{utils.resource_path(url)}"
    start_time = time.time()

    async def _parse():
        async with api.get_session() as session:
            result = []
            await m3u8.parse_m3u8(url, outputPath, session, result)
            print(result)
    asyncio.run(_parse())
    logging.info(f"程序执行时间为 {time.time()-start_time} 秒")
if __name__ == '__main__':
    # parse_m3u8()
    main_m3u8()