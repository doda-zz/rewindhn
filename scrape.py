import subprocess
from path import path
from datetime import datetime
import sys
import json
import bson
from pyquery import PyQuery
from urlparse import urlparse
import logging
from sensitive import grab, UPLOAD_COMMAND
from db import DB

FRONT_PAGE = 'http://news.ycombinator.com/'
SECOND_PAGE = 'http://news.ycombinator.com/news2'
PAGES = (FRONT_PAGE, SECOND_PAGE)
DUMP_PATH = path('rewindhn-dump.json')

class MongoEncoder(json.JSONEncoder):
    '''custom JSONEncoder that additionally handles dates and ObjectIds'''
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def parse(html):
    '''return a list of dictionaries describing the stories on the front page'''
    elements = []
    p = PyQuery(html)
    # 90s markup woohoo!
    anchors = p('.title:nth-child(3) a:nth-child(1)')
    for a in anchors:
        # have to re-wrap here, because PyQuery just exposes internal lxml objects upon getting iterated
        a = PyQuery(a)
        subtext = a.closest('tr').next().find('.subtext')
        if not subtext:
            # More link
            continue
        children = map(PyQuery, subtext.children())
        try:
            span, submitted, comments = children[0], children[1], children[-1]
        except IndexError:
            # filter out ads
            continue
        comments = comments.text().rpartition(' ')[0]
        comments = int(comments) if comments else 0
        url = a.attr('href')
        elements.append({
                      'pos': len(elements) + 1,
                    'title': a.text(),
                      'url': url,
                   'domain': urlparse(url).netloc.rpartition('www.')[2],
                 'comments': comments,
                'submitter': submitted.text(),
                   'points': int(span.text().split()[0]),
                       'id': int(span.attr('id').split('_', 1)[1]),
                      'ago': submitted[0].tail.split('ago')[0].strip(),
                })
    logging.warning('parsed %s elements', len(elements))
    return elements

def do_parse():
    '''go through everything and see if it's been inserted into cleaned'''
    grabbed = list(DB.grabbed.find().sort('created_at', 1))
    cleaned = set((x['idx'], x['page']) for x in DB.cleaned.find())
    for page, _ in enumerate(PAGES):
        for idx, g in enumerate(p for p in grabbed if p['page'] == page):
            if not (idx, page) in cleaned:
                new = clean(g)
                new['idx'] = idx
                DB.cleaned.insert(new)

def clean(page):
    page.pop('_id', None)
    page['created_at'] = page['created_at'].isoformat()
    page['posts'] = parse(page['html'])
    return page

def upload():
    '''upload an entire dump to S3'''
    all_ = DB.cleaned.find()
    j = json.dumps(list(all_), cls=MongoEncoder)
    DUMP_PATH.write_text(j)
    subprocess.call('gzip -9 -c %s > rewindhn.gz' % DUMP_PATH, shell=True)
    subprocess.call(UPLOAD_COMMAND, shell=True)

def grab_pages():
    DB.grabbed.ensure_index('created_at', 1)
    # if either of the grabs fail the program should die
    try:
        grabbed = [grab(page) for page in PAGES]
    except:
        logging.warning('unable to grab one of the pages')
        sys.exit(1)
    else:
        for i, grabbo in enumerate(grabbed):
            obj = {'html': grabbo, 'created_at': datetime.utcnow(), 'page': i}
            DB.grabbed.insert(obj)

def main():
    grab_pages()
    do_parse()
    upload()

if __name__ == '__main__':
    main()
