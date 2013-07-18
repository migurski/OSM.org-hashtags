'''

Run me:
    python api.py
    
Or:
    gunicorn api:app
'''
from os import environ
from sqlite3 import connect
from json import dumps

from flask import Flask, request, make_response

#
# Core API parts.
#
__db_file__ = environ.get('CHANGE_DB', 'changesets.db')

def tag_changes(hashtag):
    ''' 
    '''
    with connect(__db_file__) as db:
        cur = db.execute('''SELECT t.chset_id, t.chset_date,
                                   c.uid, c.user, c.comment,
                                   c.minlon, c.minlat,
                                   c.maxlon, c.maxlat
                            FROM hashtags AS t
                            LEFT JOIN changesets AS c
                              ON c.id = t.chset_id
                            WHERE t.tag = ?
                            ORDER BY t.chset_date DESC
                            LIMIT 25''',
                         (hashtag, ))
        
        rows = [dict(id=id, time=time, uid=uid, user=user,
                     user_href='http://www.openstreetmap.org/user/' + user.encode('utf8'),
                     href='http://www.openstreetmap.org/browse/changeset/' + str(id),
                     comment=comment, bounds=(b0, b1, b2, b3))
                for (id, time, uid, user, comment, b0, b1, b2, b3) in cur]

        return rows

#
# Flask app parts.
#

app = Flask(__name__)

@app.route('/')
def flask_index():
    ''' Say hi.
    '''
    res = make_response('Hello world.')
    res.headers['Content-Type'] = 'text/plain'
    return res

@app.route('/tag/<string:hashtag>', methods=['GET'])
def flask_tag(hashtag):
    ''' Mark a tile as done with with tile content.
    '''
    changes = tag_changes(hashtag)
    callback = request.args.get('callback', None)
    
    if callback:
        res = make_response(callback + '(' + dumps(changes) + ');\n')
        res.headers['Content-Type'] = 'application/javascript'

    else:
        res = make_response(dumps(changes))
        res.headers['Content-Type'] = 'application/json'

    return res

#
# Run the app.
#

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
