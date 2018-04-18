import pymongo
import time
import smtplib
from email.mime.text import MIMEText

_client = pymongo.MongoClient('mongodb://localhost:4000/')
_demodb = _client['demodb']
_tasks = _demodb.tasks

def Process(task):
    print('processing task:', task['_id'])
    audio_status = task['audio_status']
    video_status = task['video_status']
    if audio_status == 0 or video_status == 0:
        print('task is not fully processed yet')
        return False
    # Both audio and video processing is done. Send email.
    user = task['user']
    user_email = user + '@cisco.com'
    msg = MIMEText(
        '''
        Dear {0},
        Your WebEx transcripts are ready. Please visit http://starpoc-022.cisco.com:3000/user/{1} for more details.
        '''.format(user, user))
    msg['Subject'] = 'Your Webex transcript is ready'
    msg['From'] = 'no-reply@cisco.com'
    msg['To'] = user_email
    print('Sending email to', user_email)
    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
    return True

if __name__ == "__main__":
    while True:
        for task in _tasks.find({'email_status': 0}):
            if Process(task):
                print('updating',task, '...\n')
                print(_tasks.update_one(
                    {'_id': task['_id']}, 
                    { '$set': { 'email_status': 1 } }))
        print('No more task, sleep for 5s')
        time.sleep(5)
