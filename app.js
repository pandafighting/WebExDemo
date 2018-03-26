var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
var mongoose = require('mongoose');
var fileUpload = require('express-fileupload');

// Load routes.
var indexRouter = require('./routes/index');
var userRouter = require('./routes/user');
var newRouter = require('./routes/new');

// Load models.
var models = require('./models/index');

var app = express();
// Set up MongoDB connection.
var mongodbUrl = 'mongodb://localhost:4000/demodb';
mongoose.connect(mongodbUrl);

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(fileUpload());

// Make models available to the route handlers.
app.use(function(req, res, next) {
    if (!models.Task) {
	return next(new Error('No models'));
    }
    req.models = models;
    return next();
});

app.use('/', indexRouter);
app.use('/user', userRouter);
app.use('/new', newRouter);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
