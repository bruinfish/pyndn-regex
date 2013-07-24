#!/usr/bin/env python

from matcher import *
from ndn import Name
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

try:
    m = ComponentMatcher('a', None)
    m.match(Name('/a/b/'), 0, 1)
    assert m.matchResult == ['a']
    m.match(Name('/a/b/'), 1, 1)
    assert m.matchResult == []

    m = ComponentSetMatcher('<a>', None)
    m.match(Name('/a/b/'), 0, 1)
    assert m.matchResult == ['a']
    m.match(Name('/a/b/'), 1, 1)
    assert m.matchResult == []
    m.match(Name('/a/b/'), 0, 2)
    assert m.matchResult == []
    
    m = ComponentSetMatcher('[<a><b><c>]', None)
    m.match(Name('/a/b/d'), 0, 1)
    assert m.matchResult == ['a']
    m.match(Name('/a/b/d'), 2, 1)
    assert m.matchResult == []
    m.match(Name('/a/b/d'), 0, 2)
    assert m.matchResult == []
    
    m = ComponentSetMatcher('[^<a><b><c>]', None)
    m.match(Name('/b/d/'), 1, 1)
    assert m.matchResult == ['d']

    m = RepeatMatcher('[<a><b><c>]*', None, 11)
    m.match(Name('/a/b/c'), 0, 0)
    assert m.matchResult == []
    m.match(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
except RegexError as e:
    print str(e)
