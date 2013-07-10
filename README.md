OSM.org-hashtags
================

Idea for using hashtags in OSM changesets and elsewhere for social features; heavily under-featured and experimental at the moment.

Install
----

This is a python application. Package requirements are listed in `requirements.txt`. Data from [replication changesets](http://planet.openstreetmap.org/replication/changesets/) is downloaded and stored in a SQLite3 database, `changesets.db`.

To install needed packages and prepare the database, use `make`:

make changesets.db
    make venv-osm-tagwatch

...then activate your virtual environment:

source venv-osm-tagwatch/bin/activate

To run, use this command:

python process.py

On first run, the file `last.yaml` will be created to mark the last-known sequence number. On subsequent runs, all intervening changesets files will be downloaded in turn and saved; delete `last.yaml` to ignore missing history.
