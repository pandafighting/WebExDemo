import pymongo
import os
import video_core
import time

_client = pymongo.MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

def Process(task):
    print("Processing task:", task['_id'])
    basedir = task['basedir']
    videofile = task['videofile']
    if not basedir or not videofile:
        return (-1, 'Videofile cannot be empty')

    filename = os.path.join(basedir, videofile)
    print("Calling video-core with", filename)
    status, cmds = video_core.try_transcript_commands(filename)
    print(status, cmds)
    if status == 1:
        task['video_status'] = -1
        return
    soln_id = os.path.basename(basedir)
    destdir = os.path.join('/home/cisco/qishao/WebExDemo/public/'
                           'soln', soln_id)
    os.makedirs(destdir, exist_ok=True)
    cmd_file = os.path.join(destdir, 'video_output.txt')
    print('Output commands to', cmd_file)
    with open(cmd_file, 'w') as f:
        for cmd in cmds:
            f.write(cmd[0] + ':' + cmd[1])
            f.write('\n')
    task['video_status'] = 1
    task['video_output'] = os.path.join('soln', soln_id, 'video_output.txt')

if __name__ == "__main__":
    while True:
        for task in _tasks.find({'video_status': 0}):
            Process(task)
            print('updating',task, '...\n')
            print(_tasks.replace_one({'_id': task['_id']}, task))
        print('No more task, sleep for 5s')
        time.sleep(5)
