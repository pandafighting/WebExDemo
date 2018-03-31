from pymongo import MongoClient
from bson import BSON
import os
import secret

_client = MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

_useCred=secret.CRED
_serviceUrl="https://stream.cisco.us.watsonplatform.net/speech-to-text/api"
_customizationId="86dc2718-e7bd-4f2d-b4a3-baa01e6bd1b8"
_acousticCustomizationId="84b6c2e8-d62d-40f5-a7c3-4101f5b147f0"

def Process(task):
    print("Processing task:", task['_id'])
    basedir = task['basedir']
    if not basedir:
        return (-1, 'Basedir cannot be empty')
    videofile = task['videofile']
    if not videofile:
        return (-1, 'Videofile cannot be empty')
    audiofile = os.path.join(basedir, 'audiofile.json')
    print("Calling Waton API and writing to", audiofile)
    api = ''.join([_serviceUrl,
                   '/v1/recognize?&smart_formatting=true&customization_id=',
                   _customizationId,
                   '&acoustic_customization_id=',
                   _acousticCustomizationId])
    cmd = ' '.join(['curl -k -X POST -u',
                    _useCred,
                    api,
                    '--header "Content-Type: audio/wav"',
                    '--header "Transfer-Encoding: chunked"',
                    '--header "x-watson-learning-opt-out: 1"',
                    '--data-binary',
                    '@' + videofile,
                    '>' + audiofile])
    print(cmd)
    print('Audio translate is done')


if __name__ == "__main__":
    for task in _tasks.find({'status': 0}):
        Process(task)
        break
