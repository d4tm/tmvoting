#!/bin/sh
echo 'select vote, count(vote) from voters where vote <> "" group by vote;' | sqlite3 dec.db | tr '|' ' '
echo 'select title, division, area, first, last from voters where vote <> "" order by division, area, title;' | sqlite3 dec.db | tr '|' ' '


