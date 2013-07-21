from sqlite3 import connect

with connect('changesets.db') as db:

    db.execute('DROP TABLE IF EXISTS hashtags_nocase')

    db.execute('''
CREATE TABLE hashtags_nocase
(
    tag         TEXT COLLATE NOCASE,
    chset_id    INTEGER,
    chset_date  INTEGER,
    
    tag_start   INTEGER,
    tag_end     INTEGER
)
''')

    db.execute('INSERT INTO hashtags_nocase SELECT * FROM hashtags')

    db.execute('DROP TABLE IF EXISTS hashtags')
    db.execute('DROP INDEX IF EXISTS hashtag_changes')
    db.execute('DROP INDEX IF EXISTS hashtag_dates')
    db.execute('ALTER TABLE hashtags_nocase RENAME TO hashtags')
    db.execute('CREATE UNIQUE INDEX hashtag_changes ON hashtags (tag, chset_id)')
    db.execute('CREATE INDEX hashtag_dates ON hashtags (tag, chset_date)')
