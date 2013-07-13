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
tag_pat = compile(r'(^|\s)#(?P<tag>[^\-\+\)\(\[\]\?\=\*\}\{\:\.\;\,\"\'\!\<\>\|\s\~\&\§\$\%\/\\\\µ#]+)')

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
            hashtags = []
            
            path = str(int(1e10 + sequence))
            path = '%s/%s/%s.osm.gz' % (path[-9:-6], path[-6:-3], path[-3:])

            url = urljoin(base, path)
            raw = StringIO(urlopen(url).read())
            xml = GzipFile(fileobj=raw)
            osm = ElementTree.parse(xml)
            
            #
            # Look at each changeset element in the file.
            #
            for cs in osm.findall('changeset'):
                changeset_id = int(cs.attrib['id'])
                changeset_created = timegm(parse(cs.attrib['created_at']).timetuple())
                prev_hashtags_len = len(hashtags)
                changeset_comment = False
                
                #
                # Changeset comments are stored as tags, so iterate over those.
                #
                for tag in cs.findall('tag'):
                    if tag.attrib['k'] != 'comment':
                        continue

                    changeset_comment = tag.attrib['v']
                    
                    for match in tag_pat.finditer(changeset_comment):
                        hashtag_row = [
                            # tag, chset_id, chset_date
                            match.group('tag'),
                            changeset_id,
                            changeset_created,
                            
                            # tag_start, tag_end
                            match.start('tag') - 1,
                            match.end('tag'),
                            ]
                    
                        hashtags.append(hashtag_row)
                
                #
                # Skip this changeset if no comment or hashtag was found.
                #
                if not changeset_comment or len(hashtags) == prev_hashtags_len: 
                    continue
                
                changeset_row = [
                    # id, created
                    changeset_id,
                    changeset_created,

                    # uid, user
                    int(cs.attrib['uid']),
                    cs.attrib['user'],
                
                    # comment
                    changeset_comment,
                    
                    # minlat, minlon, maxlat, maxlon
                    float(cs.attrib.get('min_lat', '0')),
                    float(cs.attrib.get('min_lon', '0')),
                    float(cs.attrib.get('max_lat', '0')),
                    float(cs.attrib.get('max_lon', '0')),
                    ]
                
                changesets.append(changeset_row)
            
            #
            # Write all hashtags and changesets to database.
            #
            with connect('changesets.db') as db:
                db.executemany('''INSERT OR REPLACE INTO changesets
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', changesets)

                db.executemany('''INSERT OR REPLACE INTO hashtags
                                  VALUES (?, ?, ?, ?, ?)''', hashtags)
            
            #
            # Record the sequence number.
            #
            local = dict(sequence=sequence)
        
            last.seek(0)
            last.truncate(0)
            dump(local, last)
            
            print sequence, 'of', remote['sequence'], 'had', len(changesets),
            print 'changeset' + ('s' if len(changesets) != 1 else '')
