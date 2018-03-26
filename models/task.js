var mongoose = require('mongoose');

var taskSchema = mongoose.Schema({
    user: {
	type: String,
	required: true
    },
    sr: {
	type: String,
	required: true
    },
    video: {
	type: String,
	required: true
    },
    status: {
	type: Number,
	get: v => Math.round(v),
	set: v => Math.round(v),
	required: true,
	default: 0
    }
});

// Add a static method to this model.
taskSchema.static({
    list: function(callback) {
	this.find({}, null, {}, callback);
    },
    findByUser: function(userid, callback) {
	this.find({'user': userid}, null, {}, callback);
    }
});

module.exports = mongoose.model('Task', taskSchema);
