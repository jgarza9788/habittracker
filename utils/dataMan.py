
import os
import json5 as json
from logging import Logger

class DataManager():
    def __init__(self,
                file_dir: str = None,
                logger:Logger = None,
                default=[],
                throwError: bool = True
                ):
        self.default = default
        self.throwError = throwError

        self.file_dir = file_dir
        
        self.logger = logger
        if self.logger == None:
            self.logger =  Logger('log')
            self.logger.warn('new logger was made')

        self.data = self.load()
        self.logger.info('init DataManager done')

    def load(self):
        self.logger.info('loading Json data')
        try:
            with open(self.file_dir,'r') as file:
                return json.load(file)
        except:
            self.logger.error('error, while loading json file - creating a new json file')
            if self.throwError:
                raise Exception("error, while loading json file - creating a new json file")
            self.data = self.default
            self.save()
            return self.data

    def save(self):
        with open(self.file_dir,'w') as file:
            file.write(json.dumps(self.data,indent=4))
            self.logger.info(f'saved file {self.file_dir}')

    def print(self):
        print(json.dumps(self.data,indent=4))