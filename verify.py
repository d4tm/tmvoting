#!/usr/bin/python
import urllib2, json, sqlite3
apicode = "QGEF-ADMP-34XV-DR9H"
formname = "z30733o0zq9upo"
baseurl = "https://district4tm.wufoo.com/api/v3/forms/"

# Load the validation codes
conn = sqlite3.connect('dec.db')
c = conn.cursor()

# Create a password manager
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, baseurl, apicode, 'footastic')
handler = urllib2.HTTPBasicAuthHandler(password_mgr)

# Create "opener"
opener = urllib2.build_opener(handler)

#fields = opener.open(baseurl + formname + '/fields.json').read()
#fields = json.loads(fields)['Fields']
#print fields
#print len(fields)

# For this round, we're going to ignore the fields and use hardcoded values

ecount = json.load(opener.open(baseurl + formname + '/entries/count.json'))['EntryCount']
ecount = int(ecount)


fvote = 'Field6'
fvalidation = 'Field8'
fname = 'Field10'
femail = 'Field13'
fields = (fvote, fvalidation, fname, femail)

enext = 0
pagesize = 100
newvoters = set()
badvoters = set()

while enext <= ecount:

    entries = json.load(opener.open(baseurl + formname + '/entries.json?pageStart=%d&pageSize=%d' % (enext, pagesize)))['Entries']
    enext += pagesize

    for e in entries:
        (vote, validation, name, email) = [e[f] for f in fields]
        c.execute('SELECT first, last, title, area, division, email, vote, confirmed FROM voters WHERE validation=?', (validation,))
        res = c.fetchone()
        if res:
            (first, last, title, area, division, realemail, oldvote, confirmed) = res
            if confirmed and oldvote == vote:
                continue  # Ignore votes already registered
            print '%s %s%s %s %s votes %s' % (title, division, area, first, last, vote)
            if realemail.lower() <> email.lower():
                print 'email mismatch: db has %s, entered %s' % (realemail, email)
            if oldvote and vote <> oldvote:
                print 'vote change from %s to %s' % (oldvote, vote)
            c.execute('UPDATE voters SET vote = ? WHERE validation=?', (vote, validation))
            if not confirmed:
              newvoters.add(email.lower())
              newvoters.add(realemail.lower())
              badvoters.discard(email.lower())
              badvoters.discard(realemail.lower())
        else:
            print 'Fail!', name, email, validation
            badvoters.add(email.lower())

conn.commit()
conn.close()
vfile = open('newvoters.txt', 'w')
vfile.write('\n'.join(newvoters))
vfile.write('\n')
vfile.close()
vfile = open('badvoters.txt', 'w')
vfile.write('\n'.join(badvoters))
vfile.write('\n')
vfile.close()
