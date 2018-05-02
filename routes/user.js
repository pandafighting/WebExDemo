var express = require('express');
var router = express.Router();

/* GET users listing. */
router.get('/:userid', function(req, res, next) {
    req.models.Task.findByUser(req.params.userid, function(err, tasks) {
	if (err) {
	    // TODO: handle this error.
	    console.log(err);
	    return;
	}
	annotatedTasks = tasks.map(task => {
	    const video_status = task.video_status;
	    if (video_status == 0) {
		task.video_status_msg = 'Waiting for video analysis';
	    } else if (video_status == -1) {
		task.video_status_msg = 'Error occurred';
	    } else {
		// No message.
	    }
	    const audio_status = task.audio_status;
	    if (audio_status == 0) {
		task.audio_status_msg = 'Waiting for audio translation';
	    } else if (audio_status == -1) {
		task.audio_status_msg = 'Error occured';
	    } else {
		// No message.
	    }
	    const google_audio_status = task.google_audio_status;
	    if (google_audio_status == 0) {
		task.google_audio_status_msg = 'Waiting for Google  audio translation';
	    } else if (google_audio_status == -1) {
		task.google_audio_status_msg = 'Error occured';
	    } else {
		// No message.
	    }

	    return task;
	});
	res.render('user', { 'tasks': annotatedTasks });
    });
});

module.exports = router;
