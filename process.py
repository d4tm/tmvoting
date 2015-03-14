#!/usr/bin/python
import urllib2, json, sqlite3, yaml, smtplib, sys
from email.mime.text import MIMEText
try:
    info = yaml.load(open(sys.argv[1],'r'))
except IndexError:
    print 'usage: %s configuration_file' % sys.argv[0]
    sys.exit(1)
except yaml.YAMLError, exc:
    print 'Error in configuration file:', exc
    sys.exit(2)

def sendbadmail(b, info):
    print 'Sending error notice to', b
    message = MIMEText('\n'.join(info['badtext']))
    message['Subject'] = info['badsubj']
    message['From'] = info['from']
    message['To'] = b
    if 'cc' in info:
        message['cc'] = info['cc']
    info['s'].sendmail(info['from'], [b], message.as_string())
    if 'cc' in info:
        info['s'].sendmail(info['from'], [info['cc']], message.as_string())
    if 'bcc' in info:
        info['s'].sendmail(info['from'], [info['bcc']], message.as_string())

def sendgoodmail(voter, info):
    print 'Sending successful vote notice to', ';'.join(voter['emails'])
    print 'Positions:', ';'.join(voter['positions'])
    additional = ''
    if len(voter['positions']) > 1:
        additional += '\nPositions:\n  * '
    else:
        additional += '\nPosition:\n  * '
    additional += '\n  * '.join(voter['positions'])
    print info['goodtext'] + additional
    message = MIMEText(info['goodtext'] + additional)
    message['Subject'] = info['goodsubj']
    message['From'] = info['from']
    message['To'] = ', '.join(voter['emails'])
    if 'cc' in info:
        message['cc'] = info['cc']
    info['s'].sendmail(info['from'], voter['emails'], message.as_string())
    if 'cc' in info:
        info['s'].sendmail(info['from'], [info['cc']], message.as_string())
    if 'bcc' in info:
        info['s'].sendmail(info['from'], [info['bcc']], message.as_string())


# Connect to the database
conn = sqlite3.connect(info['db'])
c = conn.cursor()

# Create a password manager
baseurl = info['baseurl'] + '/api/v3/forms/'
formurl = baseurl + info['formname']
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, baseurl, info['apicode'], 'footastic')
handler = urllib2.HTTPBasicAuthHandler(password_mgr)

# Connect to the mail server
info['s'] =  smtplib.SMTP(info['mailserver'], info.get('mailport', 25))
info['s'].login(info['from'], info['mailpw'])

# Create "opener"
opener = urllib2.build_opener(handler)

#fields = opener.open(formurl + '/fields.json').read()
#fields = json.loads(fields)['Fields']
#print fields
#print len(fields)

# For this round, we're going to ignore the fields and use hardcoded values

ecount = json.load(opener.open(formurl + '/entries/count.json'))['EntryCount']
ecount = int(ecount)


fvote = 'Field6'
fvalidation = 'Field8'
fname = 'Field10'
femail = 'Field13'
fields = (fvote, fvalidation, fname, femail)

enext = 0
c.execute ('SELECT MAX(highwater) FROM entries;')
results = c.fetchone()
try:
  highwater = 0 + results[0] 
except TypeError:
  highwater = 0

pagesize = 100
newvoters = {}
badvoters = {}

while enext <= ecount:

    entries = json.load(opener.open(formurl + '/entries.json?pageStart=%d&pageSize=%d' % (enext, pagesize)))['Entries']
    if not entries:
	break;

    enext += pagesize

    for e in entries:
        #print e
        (vote, validation, name, email) = [e[f].strip() for f in fields]
        if int(e['EntryId']) <= highwater:
          #print 'Already processed', e['EntryId'], name, email
          continue
        c.execute('SELECT first, last, title, "Club Name" as clubname, area, division, email, vote, confirmed FROM voters WHERE validation=?', (validation,))
        results = c.fetchall()
        if results:
            for res in results:
                (first, last, title, clubname, area, division, realemail, oldvote, confirmed) = res
                if confirmed and oldvote == vote:
                    continue  # Ignore votes already registered
                dbname = '%s %s' % (first, last)
                position = ' '.join((' %s%s %s %s' % (division, area, clubname, title)).split())
                print position, dbname, 'votes', vote
                # Normalize email addresses
                realemail = realemail.lower()
                email = email.lower()
                
                if realemail <> email:
                    print 'email mismatch: db has %s, entered %s' % (realemail, email)
                if oldvote and vote <> oldvote:
                    print 'vote change from %s to %s' % (oldvote, vote)
                    confirmed = False  # Need to confirm any changes
                c.execute('UPDATE voters SET vote = ? WHERE validation=?', (vote, validation))
                if not confirmed:
                    if validation not in newvoters:
                        newvoters[validation] = {'positions': set(), 'emails': set(),
                                 'validation': validation}
                    newvoters[validation]['positions'].add(position)
                    newvoters[validation]['emails'].add(email)
                    newvoters[validation]['emails'].add(realemail)
                              
                    badvoters.pop(realemail, None)  # A good vote overrides a bad one
        else:
            print 'Fail!', name, email, validation
            badvoters[email] = email
        highwater = max(highwater, int(e['EntryId']))

conn.commit()  # Commit votes

# If there were any validation fails, send out the error
for b in badvoters:
    sendbadmail(b, info)
    print 'error for', b

# Now, send out emails to successful voters; every time we send an email,
# commit that it's been done.
for b in newvoters:
    print '_________________________________'
    print 'success for', b
    sendgoodmail(newvoters[b], info)
    c.execute('UPDATE voters SET confirmed = 1 WHERE validation = ?', (newvoters[b]['validation'],))
    conn.commit() # Commit this one

# Finally, update the entry number
c.execute('INSERT INTO ENTRIES (highwater) VALUES (%d);' % highwater);

conn.commit()


conn.close()

