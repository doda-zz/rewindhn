import pymongo
from devel import IN_DEVELOPMENT
if IN_DEVELOPMENT:
    CONN = pymongo.Connection(safe=True)
else:
    CONN = pymongo.Connection(port=29919, safe=True)
DB = CONN.rewind
