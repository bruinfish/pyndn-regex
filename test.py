#!/usr/bin/env python

from matcher import *
from ndn import Name
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

try:
    logging.debug("==========Test on ComponentMatcher==========")
    m = ComponentMatcher('a', None)
    m.match(Name('/a/b/'), 0, 1)
    assert m.matchResult == ['a']
    m.match(Name('/a/b/'), 1, 1)
    assert m.matchResult == []

    logging.debug("==========Test on ComponentSetMatcher==========")
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

    logging.debug("==========Test on RepeatMatcher==========")
    m = RepeatMatcher('[<a><b>]*', None, 8)
    m.match(Name('/a/b/c'), 0, 0)
    assert m.matchResult == []
    m.match(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
    
    m = RepeatMatcher('[<a><b>]+', None, 8)
    res = m.match(Name('/a/b/c'), 0, 0)
    assert res == False
    assert m.matchResult == []
    m.match(Name('/a/b/c'), 0, 1)
    assert m.matchResult == ['a']
    m.match(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
    
    m = RepeatMatcher('[<.*>]*', None, 6)
    m.match(Name('/a/b/c/d/e/f'), 0, 6)
    assert m.matchResult == ['a','b','c','d','e','f']
    res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []
    
    m = RepeatMatcher('[<.*>]+', None, 6)
    res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == False
    assert m.matchResult == []
    res = m.match(Name('/a/b/c/d/e/f'), 0, 1)
    assert m.matchResult == ['a']

    m = RepeatMatcher('[<a>]?', None, 5)
    res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []
    res = m.match(Name('/a/b/c/d/e/f'), 0, 1)
    assert m.matchResult == ['a']
    res = m.match(Name('/a/b/c/d/e/f'), 0, 2)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a>]{3}', None, 5)
    res = m.match(Name('/a/a/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'a', 'a']



    logging.debug("==========Test on PatternListMatcher==========")
    m = PatternListMatcher('<a><b><c>', None)
    m.match(Name('/a/b/c/'), 0, 3)
    assert m.matchResult == ['a', 'b', 'c']
    m = PatternListMatcher('<a>[<a><b>]', None)
    m.match(Name('/a/b/c/'), 0, 2)
    assert m.matchResult == ['a', 'b']

except RegexError as e:
    print str(e)
