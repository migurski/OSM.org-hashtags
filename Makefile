venv-osm-tagwatch: venv-osm-tagwatch/bin/activate

venv-osm-tagwatch/bin/activate: requirements.txt
	test -d venv-osm-tagwatch || virtualenv --no-site-packages venv-osm-tagwatch
	. venv-osm-tagwatch/bin/activate; pip install -Ur requirements.txt
	touch venv-osm-tagwatch/bin/activate

changesets.db: create.sql
	sqlite3 changesets.db < create.sql
