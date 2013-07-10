from yaml import load, dump
from xml.etree import ElementTree
from dateutil.parser import parse
from StringIO import StringIO
from urlparse import urljoin
from calendar import timegm
from sqlite3 import connect
from urllib import urlopen
from gzip import GzipFile

base = 'http://planet.openstreetmap.org/replication/changesets/'

if __name__ == '__main__':

    remote = load(urlopen(urljoin(base, 'state.yaml')))
    
    with open('last.yaml', 'a+') as last:
        last.seek(0)
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
                
                changesets.append(changeset)
            
            with connect('changesets.db') as db:
                db.executemany('''INSERT OR REPLACE INTO changesets
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', changesets)
            
            local = dict(sequence=sequence)
        
            last.seek(0)
            last.truncate(0)
            dump(local, last)
            
            print sequence, 'of', remote['sequence']
