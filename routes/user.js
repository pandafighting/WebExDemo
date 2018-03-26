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
	res.render('user', { 'tasks': tasks });
    });
});

module.exports = router;
