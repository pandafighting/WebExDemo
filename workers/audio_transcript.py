import pymongo
import os
import secret
import time
import subprocess
import json

_client = pymongo.MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

_useCred=secret.CRED
_serviceUrl="https://stream.cisco.us.watsonplatform.net/speech-to-text/api"
_customizationId="86dc2718-e7bd-4f2d-b4a3-baa01e6bd1b8"
_acousticCustomizationId="84b6c2e8-d62d-40f5-a7c3-4101f5b147f0"

def ConvertMp4ToWav(mp4file):
    wavfile = mp4file.replace("mp4", "wav", 1)
    cmd = ' '.join(['ffmpeg -n -i ', mp4file, wavfile])
    print('Converting mp4 to wav:', cmd)
    proc = subprocess.Popen(['ffmpeg', '-n', '-i', mp4file, wavfile], stdout=subprocess.PIPE)
    output, err = proc.communicate()
    return err, wavfile


def Translate(wavfile):
    basedir = os.path.dirname(wavfile)
    outputfile = os.path.join(basedir, 'audiofile.json')
    print("Calling Waton API and writing to", outputfile)
    api = ''.join([_serviceUrl,
                   '/v1/recognize?firmup_silence_time=60&smart_formatting=true&customization_id=',
                   _customizationId,
                   '&acoustic_customization_id=',
                   _acousticCustomizationId])
    cmd = ' '.join(['curl', '-k', '-X', 'POST', '-u',
                    _useCred,  '"' + api + '"',
                    '--header', '"Content-Type: audio/wav"',
                    '--header', '"Transfer-Encoding: chunked"',
                    '--header', '"x-watson-learning-opt-out: 1"',
                    '--data-binary',
                    '@' + wavfile, 
                    '>', outputfile])
    print ('Calling translation:', cmd)
    subprocess.call(cmd, shell=True)
    return None, outputfile


def OutputReadableFile(jsonfile):
    basedir = os.path.dirname(jsonfile)
    outputfile = os.path.join(basedir, 'audio_output.txt')
    with open(jsonfile, 'r') as in_f:
        data = json.load(in_f)
        total_item = len(data["results"])
        keys = []
        for i in range(0,total_item):
            keys.append(data["results"][i]["alternatives"][0]["transcript"].strip().strip('"'))
        l = []
        for key in keys:
            l.append(key)
            l.append("\n")
        content = ''.join(l)
        with open(outputfile, 'w') as out_f:
            out_f.write(content)
    return outputfile


def Process(task):
    print("Processing task:", task['_id'])
    basedir = task['basedir']
    videofile = task['videofile']
    if not basedir or not videofile:
        task['audio_status'] = -1
        print('## Error: basedir or videofile cannot be empty')
        return
    mp4file = os.path.join(basedir, videofile)
    err, wavfile = ConvertMp4ToWav(mp4file)
    if err:
        task['audio_status'] = -1
        print('## Error: Conversion to wav failed')
        return
    err, transfile = Translate(wavfile)
    if err:
        task['audio_status'] = -1
        print('## Error: Translate failed')
        return
    output_file = OutputReadableFile(transfile)
    # Copy to download place.
    soln_id = os.path.basename(basedir)
    destdir = os.path.join('/home/cisco/qishao/WebExDemo/public/'
                           'soln', soln_id)
    os.makedirs(destdir, exist_ok=True)
    dest_file = os.path.join(destdir, 'audio_output.txt')
    cmd = ' '.join(['cp -f', output_file, dest_file])
    print('Copy to download place:', cmd)
    subprocess.call(cmd, shell=True)
    task['audio_status'] = 1
    task['audio_output'] = os.path.join('/soln', soln_id, 'audio_output.txt')


if __name__ == "__main__":
    while True:
        for task in _tasks.find({'audio_status': 0}):
            Process(task)
            print('updating',task, '...\n')
            print(_tasks.update_one(
                {'_id': task['_id']},
                { '$set': {
                    'audio_status': task['audio_status'],
                    'audio_output': task['audio_output']
                }}))
        print('No more task, sleep for 5s')
        time.sleep(5)
