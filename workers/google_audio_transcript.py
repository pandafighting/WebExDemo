import pymongo
import os
import secret
import time
import subprocess
import json
import time
import google.cloud.storage
import google.cloud.speech

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/cisco/qishao/WebExDemo/workers/config/service_acc.json'

_client = pymongo.MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

_timeout = 900

_storage = google.cloud.storage.Client()
_speech = google.cloud.speech.SpeechClient()

_sample_rate = 48000

for bucket in _storage.list_buckets():
    print(bucket)

_bucket = _storage.get_bucket('speech2text--storage')

def ConvertMp4ToFlac(basedir, mp4file, user):
    flacfile = '-'.join([user, str(int(time.time())),
                         mp4file.replace('mp4', 'flac', 1)])
    from_file = os.path.join(basedir, mp4file)
    to_file = os.path.join(basedir, flacfile)
    cmd = ' '.join(['ffmpeg -n -i ', from_file, '-ar', str(_sample_rate), '-c:a flac', to_file])
    print('Converting mp4 to flac:', cmd)
    proc = subprocess.Popen(['ffmpeg', '-n', '-i', from_file,
                             '-ar', str(_sample_rate), '-c:a', 'flac', to_file],
                            stdout=subprocess.PIPE)
    output, err = proc.communicate()
    return err, flacfile

def UploadToGoogleStorage(basedir, mp4file, user):
    err, flacfile = ConvertMp4ToFlac(basedir, mp4file, user)
    if err:
        # Conversion failed.
        return err, ''
    print('Uploading', basedir, flacfile, 'for user', user)
    blob = google.cloud.storage.Blob(flacfile, _bucket)
    with open(os.path.join(basedir, flacfile), 'rb') as f:
        blob.upload_from_file(f, content_type='audio/flac')
    print('Complete with URL', blob.public_url)
    return None, blob.public_url


def GoogleSpeechTranslate(uri):
    from google.cloud.speech import types
    from google.cloud.speech import enums
    audio = types.RecognitionAudio(uri= uri)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=_sample_rate,
        language_code='en-US')
    print('Google translate audio:', audio)
    print('Google translate config:', config)
    operation = _speech.long_running_recognize(config, audio)
    response = operation.result(timeout=_timeout)
    return response


def OutputReadableFile(response):
    total_item = len(response["results"])
    keys = []
    for i in range(0,total_item):
        keys.append(data["results"][i]["alternatives"][0]["transcript"].strip().strip('"'))
    l = []
    for key in keys:
        l.append(key)
        l.append("\n")
    content = ''.join(l)
    return content


def Process(task):
    print("Processing task:", task['_id'])
    basedir = task['basedir']
    mp4file = task['videofile']
    if not basedir or not mp4file:
        task['google_audio_status'] = -1
        err = '## Error: basedir or videofile cannot be empty'
        return err
    user = task['user']
    if not user:
        task['google_audio_status'] = -1
        err = '## Error: user cannot be empty'
        return err
    err, gsurl = UploadToGoogleStorage(basedir, mp4file, user)
    if err:
        return err
    #gsurl = 'gs://speech2text--storage/sample.flac'
    gsurl = gsurl.replace('https://storage.googleapis.com/', 'gs://', 1)
    print('Calling translate API with:', gsurl)
    response = GoogleSpeechTranslate(gsurl)
    print(response)
    output_content = OutputReadableFile(response)
    outputfile = os.path.join(basedir, 'googleaudiofile.json')
    with open(outputfile, 'w') as f:
        f.write(content)

"""
results {
  alternatives {
    transcript: "what was the Maryland Lottery number"
    confidence: 0.8972623944282532
  }
}
results {
  alternatives {
    transcript: "penicillin 190"
    confidence: 0.8290839195251465
  }
}
results {
  alternatives {
    transcript: " 190"
    confidence: 0.6241641044616699
  }
}
"""
    # if err:
    #     task['audio_status'] = -1
    #     print('## Error: Translate failed')
    #     return
   
    # output_file = OutputReadableFile(transfile)
    # # Copy to download place.
    # soln_id = os.path.basename(basedir)
    # destdir = os.path.join('/home/cisco/qishao/WebExDemo/public/'
    #                        'soln', soln_id)
    # os.makedirs(destdir, exist_ok=True)
    # dest_file = os.path.join(destdir, 'google_audio_output.txt')
    # cmd = ' '.join(['cp -f', output_file, dest_file])
    # print('Copy to download place:', cmd)
    # subprocess.call(cmd, shell=True)
    # task['audio_status'] = 1
    # task['audio_output'] = os.path.join('/soln', soln_id, 'google_audio_output.txt'
    # )


if __name__ == "__main__":
    while True:
        for task in _tasks.find({'google_audio_status': 0}):
            err = Process(task)
            print('ERROR:', err)
            # print('updating',task, '...\n')
            # print(_tasks.update_one(
            #     {'_id': task['_id']},
            #     { '$set': {
            #         'audio_status': task['audio_status'],
            #         'audio_output': task['audio_output']
            #     }}))
        print('No more task, sleep for 5s')
        break
        time.sleep(5)

