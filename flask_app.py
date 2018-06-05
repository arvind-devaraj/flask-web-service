from flask_restful import reqparse, abort, Api, Resource
import os
import string
import random
import hashlib
import json
from urlparse import urlparse
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from datetime import datetime
	 

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='!@#Flaskr<>?',
    USERNAME='admin',
    PASSWORD='vinay'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print 'Initialized the database.'
	
	
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
	
	
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


parser = reqparse.RequestParser()

#userprofile related
parser.add_argument('name')
parser.add_argument('guid')
parser.add_argument('token')
parser.add_argument('phash')
parser.add_argument('profile')

#bookmarks related
parser.add_argument('userid')
parser.add_argument('site')
parser.add_argument('timestamp')
parser.add_argument('tags')
parser.add_argument('folder')
parser.add_argument('notes')
parser.add_argument('tickcount')
parser.add_argument('permalink')
parser.add_argument('usertags')
parser.add_argument('score')


#urlmaster related
parser.add_argument('title')
parser.add_argument('description')
parser.add_argument('autotag')
parser.add_argument('keywords')
parser.add_argument('imgurl')
parser.add_argument('preview')

#feed related
parser.add_argument('start')
parser.add_argument('filter')
parser.add_argument('auto')

#calender related
parser.add_argument('year')
parser.add_argument('month')

MAX_FEED = 50

def get_userId(username):
    db = get_db()
    cur = db.execute('select profile from userprofile where name=?',
                 [username])
    profile = cur.fetchall()[0]
    print profile
    return profile[0]


#todo: calculate url hash
def get_urlHash(site):
    print site
    print "calculating url hash!!"
    urlhash = hashlib.sha1(site).hexdigest()
    print urlhash
    return urlhash

def calculate_domain(site):
    parsed_uri = urlparse(site)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    print domain
    return domain


def profile_json(profile):
    new_profile =  {
        'name': profile[0],
        'guid': profile[1],
        'profile': profile[2],
        'token': profile[3],
        'phash': profile[4]
    }
    return new_profile


class UserProfile(Resource):
    def get(self):
        db = get_db()
        cur = db.execute('select * from userprofile')
        profiles = cur.fetchall()
        print profiles
        print 'total count: ', len(profiles)
        all_profiles = []
        for profile in profiles:
            new_profile = profile_json(profile)
            all_profiles.append(new_profile)
             
        return all_profiles

    def post(self):
        print "in profile post!!!!!!"
        args = parser.parse_args()
        print args
        db = get_db()
        db.execute('insert into userprofile (name, guid, token, phash, profile) values (?, ?, ?, ?, ?)',
                     [args['name'], args['guid'], args['token'], args['phash'], args['profile']])
        db.commit()
        cur = db.execute('select * from userprofile where guid=?', (args['guid'],))
        profile = cur.fetchall()[0]
        print profile
        new_profile = profile_json(profile)
        return new_profile, 201


def urlmaster_json(urlmaster):
    new_urlmaster =  {
            'pid': urlmaster[0],
            'site': urlmaster[1],
            'title': urlmaster[2],
            'description': urlmaster[3],
            'autotag': urlmaster[4],
            'urlhash': urlmaster[5],            #todo: are we sending urlhash to client side ? if not then comment this line
            'domain': urlmaster[6],
            'keywords': urlmaster[7],
            'imgurl': urlmaster[8],
            'preview': urlmaster[9]
        }
    return new_urlmaster


def update_urlmaster(args):
    urlhash = get_urlHash(args['site'])
    try:
        db = get_db()
        cur = db.execute('select * from urlmaster where urlhash=?',
                     [urlhash])
        urlmaster = cur.fetchall()[0]
        print "already exists!!!!!"
    except:
        print "does not exists!!! adding!!!"
        domain = calculate_domain(args['site'])
        db = get_db()
        db.execute('insert into urlmaster (site, title, description, autotag, urlhash, domain, keywords, imgurl, preview) values (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     [args['site'], args['title'], '', '.', urlhash, domain, 'keywords','image.png',0])       #default values as per php script
        db.commit()
        cur = db.execute('select * from urlmaster where urlhash=?', (urlhash,))
        urlmaster = cur.fetchall()[0]

    print urlmaster
    new_urlmaster = urlmaster_json(urlmaster)
    return new_urlmaster    


def bookmark_json(bookmark):
    new_bookmark =  {
            'userid': bookmark[0],
            'urlhash': bookmark[1],         #todo: comment this line ?
            'timestamp': bookmark[2],
            'tags': bookmark[3],
            'folder': bookmark[4],
            'notes': bookmark[5],
            'tickcount': bookmark[6],
            'permalink': bookmark[7],
            'usertags': bookmark[8],
            'score': bookmark[9]
        }
    return new_bookmark

class Bookmarks(Resource):
    def get(self):
        db = get_db()
        cur = db.execute('select * from bookmarks')
        bookmarks = cur.fetchall()
        print bookmarks
        print 'total count: ', len(bookmarks)
        all_bookmarks = []
        for bookmark in bookmarks:
            new_bookmark = bookmark_json(bookmark)
            all_bookmarks.append(new_bookmark)
             
        return all_bookmarks

    def post(self):
        print "in bookmarks post!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        urlmaster = update_urlmaster(args)
        db = get_db()
        db.execute('insert into bookmarks (userid, urlhash, timestamp, tags, folder, notes, tickcount, permalink, usertags, score) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     [userid, urlhash, datetime.now(), args['tags'], args['folder'], args['notes'], 0, 'permalink', '', 0])       #default values as per php script
        db.commit()
        cur = db.execute('select * from bookmarks where urlhash=?', (urlhash,))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201
    
    def delete(self):
        print "in delete bookmark!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        db = get_db()
        db.execute('delete from bookmarks where userid=? and urlhash=?',
                     [userid, urlhash])
        db.commit()
        return 202



class UrlMaster(Resource):
    def get(self):
        db = get_db()
        cur = db.execute('select * from urlmaster')
        urlmasters = cur.fetchall()
        print urlmasters
        print 'total count: ', len(urlmasters)
        all_urlmasters = []
        for urlmaster in urlmasters:
            new_urlmaster = urlmaster_json(urlmaster)
            all_urlmasters.append(new_urlmaster)
            
        return all_urlmasters

    def post(self):
        print "in urlmaster post!!!!!!"
        args = parser.parse_args()
        print args
        urlmaster = update_urlmaster(args)
        return urlmaster, 201



def get_random_string(size):
    random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))
    return random_str


class GetProfile(Resource):
    def get(self, guid):
        #how to get guid ? from url ?
        #case1: guid exists
        try:
            db = get_db()
            cur = db.execute('select * from userprofile where guid=?',
                         [guid])
            profile = cur.fetchall()[0]
        
        #case 2: guid not available i.e. new browser 
        except:
            name = get_random_string(10)
            token = get_random_string(10)
            phash = get_random_string(10)       #how to calculate phash, for temp taken random
            
            db = get_db()
            db.execute('insert into userprofile (name, guid, token, phash) values (?, ?, ?, ?)',
                     [name, guid, token, phash])
            db.commit()
            cur = db.execute('select * from userprofile where guid=?',
                         [guid])
            profile = cur.fetchall()[0]
            
        print profile
        cur = db.execute('select * from userprofile where guid=?', (guid,))
        profile = cur.fetchall()[0]
        print profile
        get_userId(profile[0])
        new_profile = profile_json(profile)
        return new_profile



class SetPass(Resource):

    def put(self):
        #are we sending guid from url ?
        print "in setpass post!!!!!!"
        args = parser.parse_args()
        print args
        db = get_db()
        db.execute('update userprofile set phash=? where guid=?',
                     [args['phash'], args['guid']])
        db.commit()
        cur = db.execute('select * from userprofile where guid=?', (args['guid'],))
        profile = cur.fetchall()[0]
        print profile
        new_profile = profile_json(profile)
        return new_profile, 201


class BookmarkPrivate(Resource):

    def put(self):
        print "in setprivate post!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        print "user with userid : ", userid
        urlhash = get_urlHash(args['site'])
        db = get_db()
        db.execute('update bookmarks set tags=? where userid=? and urlhash=?',
                     ['private',userid, urlhash])
        db.commit()
        cur = db.execute('select * from bookmarks where userid=? and urlhash=?', (userid,urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201


class BookmarkPublic(Resource):
 
    def put(self):
        print "in set public post!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        db = get_db()
        db.execute('update bookmarks set tags=? where userid=? and urlhash=?',
                     ['public',userid, urlhash])
        db.commit()
        cur = db.execute('select * from bookmarks where userid=? and urlhash=?', (userid, urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201


class BookmarkNotes(Resource):
    def get(self):
        print "in bookmark get notes!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(request.args.get('name'))
        urlhash = get_urlHash(request.args.get('site'))
        print "user with userid : ", userid
        db = get_db()
        cur = db.execute('select notes from bookmarks where userid=? and urlhash=?', (userid, urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        return bookmark[0], 201

    
    def put(self):
        print "in bookmark add notes post!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        db = get_db()
        db.execute('update bookmarks set notes=? where userid=? and urlhash=?',
                     [args['notes'],userid, urlhash])
        db.commit()
        cur = db.execute('select * from bookmarks where userid=? and urlhash=?', (userid, urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201


class BookmarkStarred(Resource):
 
    def put(self):
        print "in set bookmark starred post!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        db = get_db()
        db.execute('update bookmarks set folder=? where userid=? and urlhash=?',
                     ['starred',userid, urlhash])
        db.commit()
        cur = db.execute('select * from bookmarks where userid=? and urlhash=?', (userid, urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201


class BookmarkFolderChange(Resource):

    def put(self):
        print "in bookmark change folder!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(args['name'])
        urlhash = get_urlHash(args['site'])
        print "user with userid : ", userid
        db = get_db()
        db.execute('update bookmarks set folder=? where userid=? and urlhash=?',
                     [args['folder'],userid, urlhash])
        db.commit()
        cur = db.execute('select * from bookmarks where userid=? and urlhash=?', (userid, urlhash))
        bookmark = cur.fetchall()[0]
        print bookmark
        new_bookmark = bookmark_json(bookmark)
        return new_bookmark, 201


class GetUrlInfo(Resource):
    
    def get(self):
        print "in get url info!!!!!!"
        args = parser.parse_args()
        print args
        urlhash = get_urlHash(request.args.get('site'))
        db = get_db()
        print urlhash
        try:
            cur = db.execute('SELECT DESCRIPTION,IMGURL FROM URLMASTER WHERE URLHASH=?', (urlhash,))
            urlmaster = cur.fetchall()[0]
            print urlmaster
            response = {
                        'description': urlmaster[0],
                        'imgurl': urlmaster[1]
                        }
            status_code = 200
        except:
            response = 'Not found in master db'
            status_code = 404
            
        return response, status_code


def feed_json(feed):
    new_feed =  {
            'pid': feed[0],
            'url': feed[1],
            'title': feed[2],
            'description': feed[3],
            'imgurl': feed[4],
            'folder': feed[5],
            'domain': feed[6],
            'autotag': feed[7],
            'tags': feed[8],
            'notes': feed[9],
            'timestamp': feed[10]
        }
    return new_feed

class Feed(Resource):
    
    def get(self):
        print "in feed!!!!!!"
        args = parser.parse_args()
        print args
        userid = get_userId(request.args.get('name'))
        db = get_db()
        var_list = [userid]
        base_query = 'SELECT PID,SITE as url,TITLE as title,DESCRIPTION,IMGURL,FOLDER,DOMAIN,AUTOTAG,TAGS, NOTES,TIMESTAMP from URLMASTER,BOOKMARKS WHERE URLMASTER.URLHASH=BOOKMARKS.URLHASH AND USERID=?'
        if request.args.get('filter'):
            base_query += ' AND FOLDER = ?'
            var_list.append(request.args.get('filter'))
        
        auto_clause =  " AND TAGS!='auto'"
        order = " ORDER BY TIMESTAMP DESC"
        base_query = base_query + auto_clause + order
        
        if request.args.get('start'):
            limit = ' LIMIT ? OFFSET ?'             #added offset.. check for other database
            base_query += limit
            var_list.append(request.args.get('start'))
            var_list.append(MAX_FEED)
        print base_query
        cur = db.execute(base_query,
                         var_list)
#         (userid, args['filter'], args['start'], MAX_FEED,)

        #todo: check last 4 lines of display_feed method from php script
        feeds = cur.fetchall()
        all_feeds = []
        for feed in feeds:
            new_feed = feed_json(feed)
            all_feeds.append(new_feed)
        return all_feeds



def event_json(event):
    new_event =  {
            'pid': event[0],
            'site': event[1],
            'title': event[2],
            'description': event[3],
            'imgurl': event[4],
            'folder': event[5],
            'domain': event[6],
            'autotag': event[7],
            'tags': event[8],
            'notes': event[9],
            'timestamp': event[10]
        }
    return new_event


class Calender(Resource):
    
    def get(self):
        print "in calender!!!!!!"
        print request.args.get('name')
        args = parser.parse_args()
        print args
        userid = get_userId(request.args.get('name'))
        db = get_db()
        base_query = 'SELECT PID,SITE,TITLE,DESCRIPTION,IMGURL,FOLDER,DOMAIN,AUTOTAG,TAGS, NOTES,TIMESTAMP from URLMASTER,BOOKMARKS WHERE URLMASTER.URLHASH=BOOKMARKS.URLHASH AND USERID=?'
        base_query += " AND TIMESTAMP LIKE '?-?%' ORDER BY TIMESTAMP DESC LIMIT ? OFFSET 10 "
        print base_query
        cur = db.execute(base_query,
                         (userid, request.args.get('start')))

        events = cur.fetchall()
        all_events = []
        for event in events:
            new_event = event_json(event)
            all_events.append(new_event)
        return all_events


        
##
## Actually setup the Api resource routing here
##

api.add_resource(UserProfile, '/profiles')
api.add_resource(Bookmarks, '/bookmarks')

api.add_resource(GetProfile, '/get_profile/<guid>')
api.add_resource(SetPass, '/setpass/')

api.add_resource(BookmarkPrivate, '/set_private/')
api.add_resource(BookmarkPublic, '/set_public/')
api.add_resource(BookmarkNotes, '/bookmark_notes/')
api.add_resource(BookmarkStarred, '/set_starred/')
api.add_resource(BookmarkFolderChange, '/change_folder/')

api.add_resource(UrlMaster, '/urlmaster')
api.add_resource(GetUrlInfo, '/geturlinfo')

api.add_resource(Feed, '/feed')
api.add_resource(Calender, '/calender')


if __name__ == '__main__':
    app.run(debug=True)
    


#commands provided : for reference of variabls paasssed

# >>> put('http://localhost:5000/change_folder/', data={'name':'nik', 'urlhash':'w
# ww.dummy.com','folder':'new folder'}).json()
# >>> put('http://localhost:5000/bookmark_notes/', data={'name':'nik', 'urlhash':'
# www.dummy.com','notes':'notes update test on fb'}).json()
# >>> post('http://localhost:5000/bookmarks', data={'name':'vinay', 'site':'www.sa
# mple1.com', 'tags':'sampletag', 'folder':'otherfolder', 'notes':'some dummy note
# s', 'title':'sample site'}).json()
# >>> post('http://localhost:5000/urlmaster', data={'site':'http://www.sample.com/
# otherfloor', 'title':'sample title'}).json()
#>>> get('http://localhost:5000/geturlinfo', data={'site':'www.sample.com'}).json()
#>>> get('http://localhost:5000/feed', data={'name':'vinay','site':'www.sample.co
#m','start':10, 'filter':'others folder'}).json()

# >>> get('http://localhost:5000/calender', data={'name':'vinay','year':2016,'mont
# h':11,'start':10}).json()