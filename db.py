import pymongo
from devel import IN_DEVELOPMENT
if IN_DEVELOPMENT:
    CONN = pymongo.Connection()
else:
    CONN = pymongo.Connection(port=29919)
DB = CONN.rewind
