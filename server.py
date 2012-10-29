from flask import Flask, render_template, request, Response
import pymongo
import bson

from ddd import IN_DEVELOPMENT
from datetime import datetime
import json

app = Flask(__name__)
if IN_DEVELOPMENT:
    CONN = pymongo.Connection()
else:
    CONN = pymongo.Connection(port=29919)
DB = CONN.hnmod.cleaned
DB.ensure_index('idx')
ACCEPTED_ARGS = set(('spec', 'fields', 'skip', 'limit', 'sort'))

class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return Response(json.dumps(dict(*args, **kwargs), cls=MongoEncoder),
        mimetype='application/json')

@app.route('/api/v1/pages')
def api():
    args = dict((k, json.loads(v)) for k,v in request.args.items() if k in ACCEPTED_ARGS)
    args['limit'] = min(200, args.get('limit', 30))
    if args.get('sort') is not None:
        args['sort'] = [('idx', args['sort'])]
    args.setdefault('fields', {'_id': False, 'html': False})
    data = list(DB.find(**args))
    return jsonify(results=data, count=len(data))

@app.route('/')
def home():
    last_page = DB.find_one({'page':0}, {'_id':False, 'html':False}, sort=[('created_at', -1)])
    max_page_idx = last_page['idx']
    return render_template('base.html',
        pages={ max_page_idx: last_page })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=IN_DEVELOPMENT)
