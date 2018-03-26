from pymongo import MongoClient
from bson import BSON

_client = MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

def Process(task):
    pass

if __name__ == "__main__":
    for task in _tasks.find({'status': 0}):
        Process(task)
