#!/usr/bin/env python

from matcher import RepeatMatcher, ComponentSetMatcher, RegexError
from ndn import Name
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    # m = ComponentSetMatcher('[^<a><b><c>]', None)
    # print m.match(Name('/b/d/'), 1, 1)
    # print m.matchResult

    m = RepeatMatcher('[<a><b><c>]*', None, 11)
    m.match(Name('/a/b/c'), 0, 2)
    assert m.matchResult == ['a', 'b']
except RegexError as e:
    print str(e)
