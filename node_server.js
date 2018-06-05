var express = require('express');
var bodyParser = require('body-parser');
var app = express();

var cors = require('cors');

//app.configure(function () {
//    app.use(express.logger('dev'));
//    app.use(express.bodyParser());
//});



app.all('/*', function(req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "X-Requested-With");
  next();
});


var mongo = require('mongodb');

var Server = mongo.Server,
Db = mongo.Db,
ObjectID = mongo.ObjectID;

var server = new Server('127.0.0.1', 27017, {auto_reconnect: true});

db = new Db('folderdb', server);
	      
db.open(function(err, db){
    if(!err){
	console.log("Connected to database ");
	db.collection('folders', { strict: true}, function(err, collection) {
	    if(err) {
		console.log('Folders do not exist, creating ....');
		populateDb();
	    }
	});
    } else {
	console.log('Failed to connect db');
    }
});

var findById = function(req, res){
    id = req.params.id;
    db.collection('folders', {safe: true}, function(err, collection) {
	collection.find({ $and: [ {'username': id }, { 'type': 'folder'}] }).toArray(function(err, items){
	    res.send(items);
	});
    });
};

var addFolder = function (req, res) {
    
    var folder = req.body;
    console.log("Adding new folder " + JSON.stringify(folder));
    db.collection('folders', function (err,collection){
	collection.insert(folder, {safe: true}, function(err,result){
	    if(err){
		res.send("Error occured while inserting ");
	    } else {
		console.log('Success:  ' + JSON.stringify(result));
		res.send(result)
	    }
	});
    });
};


var deleteFolder = function (req, res) {

    //TODO delete all notes also
    var id = req.params.id;
    db.collection('folders',function(err,collection){
	collection.remove( {'_id': new ObjectID(id) }, { safe: true}, function(err, result){
	    if(err){
		res.send("Error in removing folder..Sorry!!");
	    } else {
		console.log('' + result + ' folder removed');
		res.send(req.body);
	    }
	});
    });
}

var updateFolder = function(req, res) {
    var id = req.params.id;
    var folder = req.body;

    console.log("Updating folder to " + JSON.stringify(folder));
    db.collection('folders', function(err,collection) {
	collection.update({'_id': new ObjectID(id)}, folder , {safe: true},function(err, result) {

	    if(err){
		res.send("Failed to update sorry");
	    }
	    else {
		console.log("Updated to " + JSON.stringify(result));
		res.send(result);
	    }
	});
    });

};


// Notes

var addNote = function (req, res) {
    var note = req.body;
    console.log("Adding new note " + JSON.stringify(note));
    db.collection('folders').insert(note, function(err,res){
		console.log(err);
	    }
	);
};

var listNotes = function ( req, res) {
    var parent_id = req.params.id;
    db.collection('folders', { safe: true}, function(err,collection){
	collection.find({'parent_id' : parent_id}).toArray(function(err,arrayOfNotes){
	    if(err){
		res.send(err);
	    }
	    else {
		res.send(arrayOfNotes);
	    }
	});
    });
};



////////////////////////////////


app.get('/folders/:id', findById);
app.post('/folders',addFolder);
app.delete('/folders/:id', deleteFolder);
app.put('/folders', updateFolder);

// Notes

app.post('/note', addNote);
app.get('/note/:id', listNotes);
app.delete('/note/:id', deleteFolder);

//ssapp.get('/folders/:user', findOne(req,res));

app.listen(3000);
console.log("Listening at 3000\n");



var populateDb = function() {
    
    var folders = [
	{
	    name: "test",
	    username: "s12",
	    count: 23,
	    created: ""
	},
	{
	    name: "test1",
	    username: "s12",
	    count: 23,
	    created: ""
	}
    ];
    db.collection('folders', {safe: true}, function(err, collection){
	collection.insert(folders, {safe: true}, function(err,result){});
});
    
};
