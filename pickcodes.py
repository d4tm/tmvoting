#!/usr/bin/python
""" Select 'n' random numbers """
import sys, random

needed = int(sys.argv[1])

random.seed()
results = ['%d' % p for p in random.sample(xrange(10000000, 99999999), needed)]
print '\n'.join(results)
