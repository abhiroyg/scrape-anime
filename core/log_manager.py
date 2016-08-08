import logging
import logging.config
import os
import yaml

## With help from http://stackoverflow.com/questions/15727420/using-python-logging-in-multiple-modules

def singleton(cls):
    instances = {}
    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance()

@singleton
class LogManager:
    def __init__(self):
        resources = os.path.join(
            os.path.abspath(os.path.join(__file__, os.path.pardir)),
            'resources'
        )
        with open(os.path.join(resources, 'logging.conf')) as f:
            logging.config.dictConfig(yaml.load(f))

    @staticmethod
    def getLogger(logger_name):
        return logging.getLogger(logger_name)
