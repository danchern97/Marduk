#
import os
import json

def send_email(email):
    pass

def serialize_project(project):
    return project.table

def serialize_table(table):
    return json.dumps(table)

def dump_project(project, dir_path="", filename='temp.json'):
    serialized = serialize_project(project)
    filepath = os.path.join(dir_path, filename)
    with open(os.path.join(dir_path, filename), 'w') as fp:
        json.dump(serialized, fp)
    return filepath



def create_empty_table():
    return {
        "contents":[],
        "columns":[],
        "rows":[],
        "meta":[]
    }
