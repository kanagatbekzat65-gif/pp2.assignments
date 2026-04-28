import os
from configparser import ConfigParser

def load_config(filename='database.ini', section='postgresql'):
    current_dir = os.path.dirname(__file__)
    path_to_ini = os.path.join(current_dir, filename)
    
    parser = ConfigParser()
    parser.read(path_to_ini)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {path_to_ini} file')
        
    return config

