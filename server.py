from flask import Flask, render_template, request, Response
from db import DB
import json
from devel import IN_DEVELOPMENT
from scrape import MongoEncoder
from werkzeug.contrib.cache import RedisCache
cache = RedisCache()

app = Flask(__name__)
ACCEPTED_ARGS = set(('spec', 'fields', 'skip', 'limit', 'sort'))

def jsonify(*args, **kwargs):
    return Response(json.dumps(dict(*args, **kwargs), cls=MongoEncoder),
        mimetype='application/json')


@app.route('/api/v1/pages')
def api():
    kwargs = dict((k, json.loads(v)) for k,v in request.args.items() if k in ACCEPTED_ARGS)
    kwargs['limit'] = min(200, kwargs.get('limit', 30))
    if kwargs.get('sort') is not None:
        kwargs['sort'] = [('idx', kwargs['sort'])]
    kwargs.setdefault('fields', {'_id': False, 'html': False})
    stringified = json.dumps(kwargs)
    data = cache.get(stringified)
    if data is None:
        data = list(DB.cleaned.find(**kwargs))
        cache.set(stringified, data, timeout=10 * 60)
    return jsonify(results=data, count=len(data))

@app.route('/')
def home():
    last_page = DB.cleaned.find_one({'page':0}, {'_id':False, 'html':False}, sort=[('created_at', -1)])
    max_page_idx = last_page['idx']
    return render_template('base.html',
        pages={ max_page_idx: last_page })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=IN_DEVELOPMENT)
