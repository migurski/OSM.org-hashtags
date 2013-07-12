from yaml import load, dump
from xml.etree import ElementTree
from dateutil.parser import parse
from fcntl import flock, LOCK_EX, LOCK_UN
from StringIO import StringIO
from urlparse import urljoin
from calendar import timegm
from sqlite3 import connect
from urllib import urlopen
from gzip import GzipFile
from re import compile

base = 'http://planet.openstreetmap.org/replication/changesets/'

# regular expression partly borrowed from http://code.google.com/p/twitter-api/issues/detail?id=1508
hashtag = compile(r'(^|\s)#(?P<tag>[^\-\+\)\(\[\]\?\=\*\}\{\:\.\;\,\"\'\!\<\>\|\s\~\&\§\$\%\/\\\\µ#]+)')

class OpenLocked:
    ''' Context manager for a locked file open in a+ mode, seek(0).
    '''
    def __init__(self, fname):
        self.fname = fname
        self.file = None
    
    def __enter__(self):
        self.file = open(self.fname, 'a+')
        flock(self.file, LOCK_EX)
        self.file.seek(0)
        return self.file
    
    def __exit__(self, *args):
        flock(self.file, LOCK_UN)
        self.file.close()

if __name__ == '__main__':

    remote = load(urlopen(urljoin(base, 'state.yaml')))
    
    with OpenLocked('last.yaml') as last:
        local = load(last)
        
        #
        # With no local state, at least capture current remote state.
        #
        if local is None:
            local = {'sequence': remote['sequence'] - 1}
        
        #
        # Look at each changeset file and record comments, IDs, bboxes, etc.
        #
        for sequence in range(local['sequence'] + 1, remote['sequence'] + 1):
            changesets = []
            
            path = str(int(1e10 + sequence))
            path = '%s/%s/%s.osm.gz' % (path[-9:-6], path[-6:-3], path[-3:])

            url = urljoin(base, path)
            raw = StringIO(urlopen(url).read())
            xml = GzipFile(fileobj=raw)
            osm = ElementTree.parse(xml)
            
            for cs in osm.findall('changeset'):
                changeset = [
                    int(cs.attrib['id']),
                    timegm(parse(cs.attrib['created_at']).timetuple()),

                    int(cs.attrib['uid']),
                    cs.attrib['user'],
                
                    '', # comment
                    
                    float(cs.attrib.get('min_lat', '0')),
                    float(cs.attrib.get('min_lon', '0')),
                    float(cs.attrib.get('max_lat', '0')),
                    float(cs.attrib.get('max_lon', '0')),
                    ]
                
                for tag in cs.findall('tag'):
                    if tag.attrib['k'] == 'comment':
                        changeset[4] = tag.attrib['v']
                        
                        for match in hashtag.finditer(tag.attrib['v']):
                            print match.group('tag')
                
                changesets.append(changeset)
            
            with connect('changesets.db') as db:
                db.executemany('''INSERT OR REPLACE INTO changesets
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', changesets)
            
            local = dict(sequence=sequence)
        
            last.seek(0)
            last.truncate(0)
            dump(local, last)
            
            print sequence, 'of', remote['sequence']
