# pydl
基于`aiohttp`开发的下载工具,主要利用多协程下载单文件或`m3u8`文件及其切片文件

## 安装
```
pip install git+https://github.com/shadaileng/pydl.git
```

## 用法

```bash
$ python -m pydl -h
usage: download [-h] [--mode MODE] [--dist DIST] [--proxy PROXY] [--log] [-v] [-n N] url

a download tool develop by aiohttp

positional arguments:
  url            Provide url

options:
  -h, --help     show this help message and exit
  --mode MODE    Provide download mode: <file|m3u8>
  --dist DIST    Provide output path, default ./
  --proxy PROXY  Provide proxy addr
  --log          log to ./logs
  -v             show log where is downloading
  -n N           Provide thread num, default 22
```
