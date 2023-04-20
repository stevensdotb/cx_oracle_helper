import logging
from os import path, mkdir
from datetime import datetime

def setup_logger(log_dir: str, log_file: str) -> logging.Logger:


    if not path.exists(path.abspath(log_dir)):
        mkdir(path.abspath(log_dir))

    log_file = path.abspath(path.join(log_dir, f"{log_file}_{datetime.now().strftime('%d%m%Y-%H%M%S')}.log"))
    logging.basicConfig(
        encoding='utf-8',
        format='[%(asctime)s] (%(levelname)s): %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S %p',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
