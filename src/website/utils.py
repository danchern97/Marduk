#
import json

def send_email(email):
    pass

def serialize_project(project):
    return json.loads(project.table)

def create_empty_table():
    return {
        "contents":[],
        "columns":[],
        "rows":[],
        "meta":[]
    }
