#!/usr/bin/env node



var qs=require("querystring");

var sys= require("sys");
var my_http = require("http");

var  mongojs = require("mongojs");

var crypto = require('crypto');


var MongoClient = require('mongodb').MongoClient;
var format = require('util').format;


////////////////////////  USER VARS ////////////
var rsp;
var origin;

var url="http://example.com";

var collection;

var cached;
/////////////////////////  HELPERS /////////////////


function write(){
	process.stdout.write(Array.prototype.join.call(arguments, " ") + "\n");
};


//////////////////////// Logging ///////////////
var fs = require('fs');
var util = require('util');
var log_file = fs.createWriteStream('/root/debug_nodejs.log', {flags : 'w'});
var log_stdout = process.stdout;

console.log = function(d) { //
  log_file.write(util.format(d) + '\n');
  log_stdout.write(util.format(d) + '\n');
};


///////////////// CONNECT DB ////////////////

MongoClient.connect('mongodb://hyperbook:hyperbook@localhost:27017/admin',

  /////////////// CALLBACK ON SUCCESS CONNECTION /////////////
  function(err, db) {
    if(err) throw err;

    collection = db.collection('bookmarks');
  });





/////// CREATE SERVER LISTENING ON PORT  ///////////////////////
my_http.createServer(function(request,response) {

   origin = (request.headers.origin || "*");

  rsp = response;
  getURL(request);
  sys.puts("listening on port 8082");
 // require("./getURL.js")(url,  "html" ,output );//getURL invocation

}).listen(8082); //createServer


function getURL(request) {
    if(request.method=='POST') {

	var body = '';
        request.on('data', function (data) {
            body += data;

            // Too much POST data, kill the connection!
            if (body.length > 1e6)
                req.connection.destroy();
        });

	// callback when POST params are received
        request.on('end', function () {
            var post = qs.parse(body);
	    url = post['url'];
	    getURLContents(url);	
            // use post['blah'], etc.
	    //console.log(url);
 	       //   require("./getURL.js")(url,  "html" ,output );//getURL invocation
        });	
    }
    else {
         rsp.write( "No POST URL specified");
    } 	
}


function getURLContents(url) {

          var shasum = crypto.createHash('sha1');
	  shasum.update(url);
	  var urlhash = shasum.digest('hex');

	   collection.count({_id:urlhash}, function(err,c) {
		console.log("Count="+c);
		if (c==1)  {
		   //read CACHED versions
		   read_db(url);			
		}
		else  { 
		   // call Node Readability module and cache it 
 	           require("./getURL.js")(url,  "html" , dom_output );//getURL invocation
		}
	   });
}

var dom_output=function(result){
	console.log("DOM:"+url);
	if(result.error) return write("ERROR:", result.text);

	//else
	write("TITLE:", result.title);
	write("SCORE:", result.score);
	if(result.nextPage) write("NEXT PAGE:", result.nextPage);
	write("LENGTH:", result.textLength);
	write("");
	
	var text;
	if("text" in result){
		text = require("entities").decodeHTML5(result.text);
	} else {
		text = result.html.replace(/\s+/g, " ");
	}
	//write(text);
	emit_http_response(text, result.textLength);
	write_db(url,text);

}

//                        "content-length": length
function emit_http_response(text, length) {

        rsp.writeHead(
                    "200",
                    "OK",
                    {
                        "access-control-allow-origin": origin,
                        "content-type": "text/plain"
                    }
                );
	rsp.write(text);
        rsp.end();

}
function write_db(url,text) {

	console.log("WRITE TO MONGO");

          var shasum = crypto.createHash('sha1');
	  shasum.update(url);
	  var urlhash = shasum.digest('hex');

	  collection.insert({_id: urlhash , dom: text}, function(err, docs) {
           collection.count(function(err, count) {
            console.log(err);
            console.log(format("count = %s", count));
           });
       });

}


function read_db(url) {
	
          var shasum = crypto.createHash('sha1');
	  shasum.update(url);
	  var urlhash = shasum.digest('hex');
	  console.log(urlhash);
	  collection.find({_id : urlhash}).toArray(function(err, result) {
	        //console.dir(result[0].dom);
		console.log("CACHED: TRUE" + url);
		cached=true;

		emit_http_response(result[0].dom, result[0].dom.length + 200 );
    	    });
	 

}











sys.puts("listening on port 8082");
