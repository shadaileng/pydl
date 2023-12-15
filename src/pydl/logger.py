# -*- coding: utf-8 -*-
import logging, os
from logging import handlers

format = "%(asctime)s - %(name)s - %(filename)s line %(lineno)d - %(levelname)s - %(message)s"
logging.basicConfig(
    format=format, level=logging.INFO
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(filename)s line %(lineno)d - %(levelname)s: %(message)s")


def getLogger(name=__name__):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/info.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)