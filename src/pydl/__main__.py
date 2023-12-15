# -*- coding: utf-8 -*-
import asyncio

from .m3u8 import download_m3u8
from .download import download, download_sync
from .utils import resource_path, resource_name
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
        outputPath = path.join(args.dist, resource_name(args.url))
        asyncio.run(download(args.url, outputPath, proxy=args.proxy, verbose=args.is_verbose))
    elif args.mode == "m3u8":
        outputPath = path.join(args.dist, resource_path(args.url))
        asyncio.run(download_m3u8(args.url, outputPath, proxy=args.proxy, verbose=args.is_verbose))
    else:
        print("mode error")
        exit(1)