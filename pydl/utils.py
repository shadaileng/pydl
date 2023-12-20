# -*- coding: utf-8 -*-
import logging, sys, json, re, os
from urllib.parse import urlparse, urlunparse, ParseResult
from os import path

from typing import Any


def resource_name(url: str)->str:
    """
    Returns the name of the resource from a url.
    """
    return path.basename(resource_path(url))

def resource_dir(url: str)->str:
    """
    Returns the name of the resource from a url.
    """
    return path.dirname(resource_path(url))

def resource_path(url: str)->str:
    """
    Returns the path of the resource from a url.
    """
    url_data = parse_url(url)
    return f"{url_data.netloc}{clean_url(url_data.path)}"

def parse_url(url: str)->Any:
    url_data = urlparse(url)
    url = urlunparse(ParseResult(scheme=url_data.scheme, netloc=url_data.netloc, path=clean_url(url_data.path),
            params=url_data.params, query=url_data.query, fragment=url_data.fragment))
    url_data = urlparse(url)
    return url_data

def clean_url(url: str)->str:
    return re.sub(r'/{2,}', '/', url)

def dumpdata(filename: str, data: Any):
    try:
        with open(filename, 'w') as src:
            src.truncate(0)
            json.dump(data, src)
        return True
    except BaseException as e:
        logging.error('[-]Error[%s]: %s' % (sys.exc_info()[2].tb_lineno, e))
        if isinstance(e, KeyboardInterrupt): raise e
    return False

def loaddata(filename: str)->Any:
    try:
        if not os.path.exists(filename):
            return None
        with open(filename, 'r') as src:
            return json.load(src)
    except BaseException as e:
        # logging.error('[-]Error[%s]: %s' % (sys.exc_info()[2].tb_lineno, e))
        if isinstance(e, KeyboardInterrupt): raise e
    return None




def byteunit(byte):
    return '%.2fKB' % (byte / 1024.0) if byte / 1024.0 < 1024 else ('%.2fMB' % (byte / 1024.0 / 1024.0) if (byte / 1024.0 / 1024.0) < 1024 else '%.2fGB' % (byte / 1024.0 / 1024.0 / 1024.0))

