
import os
import datetime

import logging 
from logging import Logger
from logging.handlers import RotatingFileHandler
# import logging.config
from io import StringIO

def createLogger(
                root: str = None,
                strtime_name: str = '%Y%m%d%H%M', 
                useFileHander:bool = True, 
                useStreamHandler:bool = True,
                strIO:StringIO = None,
                ) -> Logger:
    if root == None:
        root = os.path.dirname(os.path.realpath(__file__))
        root = os.path.join(root,'log')
    
    if os.path.exists(root) == False:
        os.mkdir(root)

    log_name_time = datetime.datetime.now().strftime(strtime_name)
    # log_name_time = datetime.datetime.now().strftime()

    # new logging
    if strIO != None:
        logging.basicConfig(stream=strIO, level=logging.INFO)
    logger = logging.getLogger(name=log_name_time + '.log')
    logger.setLevel(logging.DEBUG)

    logger.dir = root
    # logger.filename = os.path.join(root, log_name_time + '.log')
    logger.filename = os.path.join(root, 'log')

    if useFileHander:
        # add file hander
        # fh = logging.FileHandler(filename=os.path.join(root, log_name_time + '.log'),encoding='utf-8')
        fh = RotatingFileHandler(filename=os.path.join(root, 'log'),encoding='utf-8',maxBytes=25*1024*1024,backupCount=10)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s',
            # datefmt='%Y%m%d %H:%M:%S.%f'
            )
        # formatter = logging.Formatter(
        #     '%(asctime)s - %(levelname)s - %(message)s',
        #     datefmt=strtime)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if useStreamHandler:
        # add stream hander
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            # datefmt='%Y%m%d %H:%M:%S.%f'
            )
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger


if __name__ == '__main__':
    import os
    from io import StringIO

    dir = os.path.dirname(os.path.realpath(__file__))
    logStream = StringIO()

    thislogger = createLogger(
        root=os.path.join(dir,'log'),
        useStreamHandler=True,
        strIO=logStream,
        )
    
    thislogger.info("test-info")
    thislogger.debug("test-debug")