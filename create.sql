DROP TABLE IF EXISTS changesets;
DROP TABLE IF EXISTS hashtags;
DROP INDEX IF EXISTS hashtag_changes;
DROP INDEX IF EXISTS hashtag_dates;

CREATE TABLE changesets
(
    id      INTEGER PRIMARY KEY,
    created INTEGER,

    uid     INTEGER,
    user    TEXT,

    comment TEXT,
    
    minlat  REAL,
    minlon  REAL,
    maxlat  REAL,
    maxlon  REAL
);

CREATE TABLE hashtags
(
    tag         TEXT,
    chset_id    INTEGER,
    chset_date  INTEGER,
    
    tag_start   INTEGER,
    tag_end     INTEGER
);

CREATE UNIQUE INDEX hashtag_changes ON hashtags (tag, chset_id);
CREATE INDEX hashtag_dates ON hashtags (tag, chset_date);
