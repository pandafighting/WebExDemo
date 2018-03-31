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
	    const status = task.status;
	    if (status == 0) {
		task.status_name = 'Processing';
	    } else {
		task.status_name = 'Unknown';
	    }
	    return task;
	});
	res.render('user', { 'tasks': annotatedTasks });
    });
});

module.exports = router;
