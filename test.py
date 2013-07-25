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

    m = RepeatMatcher('[<a><b>]{3}', None, 8)
    res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == False
    assert m.matchResult == []
    res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{2,3}', None, 8)
    res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []
    res = m.match(Name('/a/b/a/d/e/f'), 0, 1)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{2,}', None, 8)
    res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []
    res = m.match(Name('/a/b/a/b/e/f'), 0, 4)
    assert res == True
    assert m.matchResult == ['a','b','a','b']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 1)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{,2}', None, 8)
    res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == False
    assert m.matchResult == []
    res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.match(Name('/a/b/a/b/e/f'), 0, 1)
    assert res == True
    assert m.matchResult == ['a']
    res = m.match(Name('/a/b/a/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []

    logging.debug("==========Test on BackRefMatcher==========")
    backRef = []
    m = BackRefMatcher('(<a><b>)', backRef)
    res = m.match(Name('/a/b/'), 0, 2)
    assert res == True 
    assert m.matchResult == ['a','b',]
    assert len(m.backRef) == 1

    backRef = []
    m = RepeatMatcher('(<a><b>)+', backRef, 8)
    res = m.match(Name('/a/b/a/b/'), 0, 4)
    assert res == True 
    assert m.matchResult == ['a','b', 'a', 'b']
    assert len(m.backRef) == 1

    backRef = []
    m = RepeatMatcher('(<a>(<a><b>){2})+', backRef, 16)
    res = m.match(Name('/a/a/b/a/b/'), 0, 5)
    assert res == True 
    assert m.matchResult == ['a', 'a', 'b', 'a', 'b']
    assert len(m.backRef) == 2
    assert backRef[1].matchResult == ['a', 'b']
    

    logging.debug("==========Test on PatternListMatcher==========")
    m = PatternListMatcher('<a><b><c>', None)
    m.match(Name('/a/b/c/'), 0, 3)
    assert m.matchResult == ['a', 'b', 'c']
    
    m = PatternListMatcher('<a>[<a><b>]', None)
    m.match(Name('/a/b/c/'), 0, 2)
    assert m.matchResult == ['a', 'b']

    m = PatternListMatcher('<.*>*<a>', None)
    res = m.match(Name('/a/b/c/'), 0, 3)
    assert res == False
    assert m.matchResult == []

    m = PatternListMatcher('<.*>*<a><.*>*', None)
    res = m.match(Name('/a/b/c/'), 0, 3)
    assert res == True
    assert m.matchResult == ['a','b','c']

    logging.debug("==========Test on RegexMatcher==========")
    m = RegexMatcher('^<a><b><c>')
    res = m.matchName(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<b><c><d>$')
    res = m.matchName(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('^<a><b><c><d>$')
    res = m.matchName(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<a><b><c><d>')
    res = m.matchName(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<b><c>')
    res = m.matchName(Name('/a/b/c/d'))
    assert res == True

    logging.debug("==========Test on RegexMatcher BackReference==========")
    m = RegexMatcher('^(<.*>*)<.*>$')
    res = m.matchName(Name('/n/a/b/'))
    assert m.extract('\\1') == ['n', 'a']

    m = RegexMatcher('^(<.*>*)<.*>')
    res = m.matchName(Name('/n/a/b/c/'))
    assert res == True
    assert m.extract('\\1') == []

    logging.debug("==============================================================================")
    logging.debug("===========================Test on Aggressive Match===========================")
    logging.debug("==============================================================================")

    logging.debug("==========Test on RepeatMatcher==========")
    m = RepeatMatcher('[<a><b>]*', None, 8)
    m.aggressiveMatch(Name('/a/b/c'), 0, 0)
    assert m.matchResult == []
    m.aggressiveMatch(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
    
    m = RepeatMatcher('[<a><b>]+', None, 8)
    res = m.aggressiveMatch(Name('/a/b/c'), 0, 0)
    assert res == False
    assert m.matchResult == []
    m.aggressiveMatch(Name('/a/b/c'), 0, 1)
    assert m.matchResult == ['a']
    m.aggressiveMatch(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
    
    m = RepeatMatcher('[<.*>]*', None, 6)
    m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 6)
    assert m.matchResult == ['a','b','c','d','e','f']
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []
    
    m = RepeatMatcher('[<.*>]+', None, 6)
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == False
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 1)
    assert m.matchResult == ['a']

    m = RepeatMatcher('[<a>]?', None, 5)
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 1)
    assert m.matchResult == ['a']
    res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 2)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{3}', None, 8)
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == False
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{2,3}', None, 8)
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 1)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{2,}', None, 8)
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == True
    assert m.matchResult == ['a', 'b', 'a']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
    assert res == False
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/a/b/e/f'), 0, 4)
    assert res == True
    assert m.matchResult == ['a','b','a','b']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 1)
    assert res == False
    assert m.matchResult == []

    m = RepeatMatcher('[<a><b>]{,2}', None, 8)
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
    assert res == False
    assert m.matchResult == []
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
    assert res == True
    assert m.matchResult == ['a', 'b']
    res = m.aggressiveMatch(Name('/a/b/a/b/e/f'), 0, 1)
    assert res == True
    assert m.matchResult == ['a']
    res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 0)
    assert res == True
    assert m.matchResult == []

    logging.debug("==========Test on BackRefMatcher==========")
    backRef = []
    m = BackRefMatcher('(<a><b>)', backRef)
    res = m.match(Name('/a/b/'), 0, 2)
    assert res == True 
    assert m.matchResult == ['a','b',]
    assert len(m.backRef) == 1

    backRef = []
    m = RepeatMatcher('(<a><b>)+', backRef, 8)
    res = m.match(Name('/a/b/a/b/'), 0, 4)
    assert res == True 
    assert m.matchResult == ['a','b', 'a', 'b']
    assert len(m.backRef) == 1

    backRef = []
    m = RepeatMatcher('(<a>(<a><b>){2})+', backRef, 16)
    res = m.match(Name('/a/a/b/a/b/'), 0, 5)
    assert res == True 
    assert m.matchResult == ['a', 'a', 'b', 'a', 'b']
    assert len(m.backRef) == 2
    assert backRef[1].matchResult == ['a', 'b']
    

    logging.debug("==========Test on PatternListMatcher==========")
    m = PatternListMatcher('<a><b><c>', None)
    m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
    assert m.matchResult == ['a', 'b', 'c']
    
    m = PatternListMatcher('<a>[<a><b>]', None)
    m.aggressiveMatch(Name('/a/b/c/'), 0, 2)
    assert m.matchResult == ['a', 'b']

    m = PatternListMatcher('<.*>*<a>', None)
    res = m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
    assert res == False
    assert m.matchResult == []

    m = PatternListMatcher('<.*>*<a><.*>*', None)
    res = m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
    assert res == True
    assert m.matchResult == ['a','b','c']

    logging.debug("==========Test on RegexMatcher==========")
    m = RegexMatcher('^<a><b><c>')
    res = m.matchN(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<b><c><d>$')
    res = m.matchN(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('^<a><b><c><d>$')
    res = m.matchN(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<a><b><c><d>')
    res = m.matchN(Name('/a/b/c/d'))
    assert res == True
    assert m.matchResult == ['a','b','c', 'd']

    m = RegexMatcher('<b><c>')
    res = m.matchN(Name('/a/b/c/d'))
    assert res == True

    m = RegexMatcher('^(<.*>*)<.*>')
    res = m.matchN(Name('/n/a/b/c/'))
    assert res == True
    assert m.extract('\\1') == ['n','a','b']

    m = RegexMatcher('^(<.*>*)<.*><c>(<.*>)<.*>')
    res = m.matchN(Name('/n/a/b/c/d/e/f/'))
    assert res == True
    assert m.extract('\\1\\2') == ['n','a', 'd']

    m = RegexMatcher('(<.*>*)<.*>$')
    res = m.matchN(Name('/n/a/b/c/'))
    assert res == True
    assert m.extract('\\1') == ['n', 'a', 'b']
    
    m = RegexMatcher('<.*>(<.*>*)<.*>$')
    res = m.matchN(Name('/n/a/b/c/'))
    assert res == True
    assert m.extract('\\1') == ['a','b']

    m = RegexMatcher('<a>(<.*>*)<.*>$')
    res = m.matchN(Name('/n/a/b/c/'))
    assert res == True
    assert m.extract('\\1') == ['b']

except RegexError as e:
    print str(e)
