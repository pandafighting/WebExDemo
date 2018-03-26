var express = require('express');
var router = express.Router();

router.get('/', function(req, res, next) {
    res.render('new', { 'data': { } });
});

router.post('/', function(req, res, next) {
    var data = {
	url: req.body.url.trim(),
	password: req.body.password.trim(),
	sr: req.body.sr.trim(),
	user: req.body.user.trim()
    };
    // Validate request first.
    if (!data.url) {
	data.msgHeader = 'URL is empty';
	data.msgBody = 'Download URL cannot be empty.';
	res.render('new', { 'data' : data });
	return;
    }
    if (!data.password) {
	data.msgHeader = 'Password is empty';
	data.msgBody = 'Download password cannot be empty.';
	res.render('new', { 'data' : data });
	return;
    }
    if (!data.sr) {
	data.msgHeader = 'SR is empty';
	data.msgBody = 'SR number cannot be empty.';
	res.render('new', { 'data' : data });
	return;
    }
    if (!data.user) {
	data.msgHeader = 'User is empty';
	data.msgBody = 'User ID cannot be empty.';
	res.render('new', { 'data' : data });
	return;
    }
    // Now add task to DB.
    var task = new req.models.Task({
	url: data.url,
	password: data.password,
	sr: data.sr,
	user: data.user
    });

    return task.save(function(err) {
	console.log(task);
	console.log('error:', err);
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

module.exports = router;
