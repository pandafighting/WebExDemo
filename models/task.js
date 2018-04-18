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
    basedir: {
	type: String,
	required: true
    },
    videofile: {
	type: String,
	required: true
    },
    video_status: {
	type: Number,
	get: v => Math.round(v),
	set: v => Math.round(v),
	required: true,
	default: 0
    },
    video_output: {
	type: String,
	required: false,
	default: ""
    },
    audio_status: {
	type: Number,
	get: v => Math.round(v),
	set: v => Math.round(v),
	required: true,
	default: 0
    },
    audio_output: {
	type: String,
	required: false,
	default: ""
    },
    email_status: {
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
