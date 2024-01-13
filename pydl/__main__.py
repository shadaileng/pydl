# -*- coding: utf-8 -*-
import asyncio

from . import api, utils, m3u8, download
from os import path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog='download', description="a download tool develop by aiohttp")
    parser.add_argument("url", help="Provide url")
    parser.add_argument("--mode", help="Provide download mode: [file|m3u8], default file", default="file")
    parser.add_argument("--dist", help="Provide output path, default ./", default="./")
    parser.add_argument("--proxy", help="Provide proxy addr", default=None)
    parser.add_argument("--log", help="log to ./logs", action="store_true", dest="is_log", default=False)
    parser.add_argument("-v", help="show log where is downloading", action="store_true", dest="is_verbose", default=False)
    parser.add_argument("-n", help="Provide thread num, default 22", type=int, default=22)
    args = parser.parse_args()
    # print(args)
    if args.is_log:
        from .logger import getLogger
        getLogger()
    if args.mode == "file": 
        outputPath = path.join(args.dist, utils.resource_name(args.url))
        asyncio.run(api.download(args.url, outputPath, download.new_file_infos, proxy=args.proxy, verbose=args.is_verbose))
    elif args.mode == "m3u8":
        outputPath = path.join(args.dist, utils.resource_path(args.url))
        asyncio.run(api.download(args.url, outputPath, m3u8.new_m3u8_infos, proxy=args.proxy, verbose=True))
    else:
        print("mode error")
        exit(1)