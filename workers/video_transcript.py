from pymongo import MongoClient
from bson import BSON
import os
import video_core

_client = MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

def Process(task):
    print("Processing task:", task['_id'])
    videofile = task['videofile']
    if not videofile:
        return (-1, 'Videofile cannot be empty')
    print("Calling video-core with", videofile)
    cmds = video_core.get_transcript_commands(videofile)
    print(cmds)

if __name__ == "__main__":
    for task in _tasks.find({'status': 0}):
        Process(task)
        break
