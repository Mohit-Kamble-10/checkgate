import json
import os
def read_json(path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            data=json.load(file)
        return data,"Done reading"
    else:
        return {},"Error File does not exist"