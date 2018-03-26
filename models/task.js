var mongoose = require('mongoose');

var taskSchema = mongoose.Schema({
    user: {
	type: String,
	required: true
    },
    url: {
	type: String,
	required: true
    },
    password: {
	type: String,
	required: true
    },
    sr: {
	type: String,
	required: true
    }
});

// Add a static method to this model.
taskSchema.static({
  list: function(callback) {
    this.find({}, null, {}, callback);
  }
});

module.exports = mongoose.model('Task', taskSchema);
