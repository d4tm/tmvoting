#!/usr/bin/python

# Update the voting file to confirm voters.

import sys, sqlite3

voters = open('newvoters.txt').read().split()
conn = sqlite3.connect('dec.db')
for v in voters:
    conn.execute('UPDATE voters SET confirmed = 1 WHERE email = ? COLLATE NOCASE', (v,))
conn.commit()
conn.close()
