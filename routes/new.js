var express = require('express');
var router = express.Router();
var path = require('path');
var fs = require('fs');

router.get('/', function(req, res, next) {
    res.render('new', { 'data': { } });
});

router.post('/', function(req, res, next) {
    console.log('reqbody:', req.body);
    console.log('req.files', req.files);
    if (!req.files) {
	var data = {
	    msgHeader: 'Need to upload file',
	    msgBody: 'Please remember to upload WebEx video file in mp4 format.'
	};
	res.render('new', { 'data': data });
	return;
    }
    var sr = req.body.sr.trim();
    if (!sr) {
	var data = {
	    msgHeader: 'SR is empty',
	    msgBody: 'SR number cannot be empty.'
	};
	res.render('new', { 'data' : data });
	return;
    }
    var user = req.body.user.trim();
    if (!user) {
	var data = {
	    msgHeader: 'User is empty',
	    msgBody: 'User ID cannot be empty.'
	};
	res.render('new', { 'data' : data });
	return;
    }
    // Save file first.
    var basedir = path.join('/home/cisco/qishao/WebExDemo/tmp', Date.now().toString());
    fs.mkdirSync(basedir, 0740);
    var webexfile = req.files.webexfile;
    var videoFilename = webexfile.name;
    var videoLocation = path.join(basedir, videoFilename);
    webexfile.mv(videoLocation)
	.then(function(err) {
	    if (err) {
		res.render('new', { 'data': data });
		return;
	    }
	    // Now add task to DB.
	    var task = new req.models.Task({
		sr: sr,
		user: user,
		basedir: basedir,
		videofile: videoFilename
	    });
	    task.save(function(err) {
		if (err) {
		    var data = {
			msgHeader: 'DB connection error',
			msgBody: err
		    };
		    res.render('new', { 'data': data });
		    return;
		}
		var data = {
		    msgHeader: 'Request Created!',
		    msgBody: 'Your request ID is ' + task._id + '. We will email you result.'
		};
		console.log('data', data);
		res.render('new', { 'data' : data});
	    });
	});
});

module.exports = router;
