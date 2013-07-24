import sys
import re
import logging
from ndn import Name

class RegexError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class BaseMatcher(object):
    def __init__(self, expr, backRef, exact=True):
        logging.debug("BaseMatcher Constructor")
        self.expr    = expr
        self.backRef = backRef
        self.exact   = exact
        self.matchResult = []
        self.matcherList = []

    def match(self, name, offset, len):
        logging.debug("BaseMatcher.match()")
        self.matchResult = []

        if self._recursiveMatch(0, name, offset, len):
            for i in range(offset,  offset + len):
                self.matchResult.append(name[i])
            return True
        else:
            return False

    def _recursiveMatch(self, mId, name, offset, length):
        logging.debug("BaseMatcher._recursiveMatch()")
        logging.debug("mId: " + str(mId) + " name: " +  str(name) + " offset: " + str(offset) + " length: " + str(length))
        tried = 0

        if mId >= len(self.matcherList) :
            if length != 0 :
                return False
            else:
                return True
    
        matcher = self.matcherList[mId]

        while tried <= length:
            if matcher.match(name, offset, tried) and self._recursiveMatch(mId + 1, name, offset + tried, length - tried) :
                return True     
            tried += 1
            logging.debug("tried: " + str(tried) + " length: " + str(length))

        return False



class ComponentMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug("ComponentMatcher Constructor")
        logging.debug("expr " + expr)
        
        super(ComponentMatcher, self).__init__(expr, backRef, exact)

    def match(self, name, offset, len):
        logging.debug("ComponentMatcher match")
        logging.debug("Name " + str(name) + " offset " +  str(offset) + " len " +str(len))

        self.matchResult = []
        
        matcher = re.compile(self.expr)
        if self.exact:
            if matcher.match(name[offset]):
                self.matchResult.append(name[offset])
                return True
        else:
            if matcher.search(name[offset]):
                self.matchResult.append(name[offset])
                return True
            
        return False
            

class ComponentSetMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug("ComponentSetMatcher Constructor")
        
        errMsg = "Error: ComponentSetMatcher.Constructor: "
        self.include = True
    
        super(ComponentSetMatcher, self).__init__(expr, backRef, exact)

        if '<' == self.expr[0]:
            self._compileSingleComponent()
        elif '[' == self.expr[0]:
            lastIndex = len(self.expr) - 1
            if ']' != self.expr[lastIndex]:
                raise RegexError(errMsg + " No matched ']' " + self.expr)
            if '^' == self.expr[1]:
                self.include = False

                self._compileMultipleComponents(2, lastIndex)
            else:
                self._compileMultipleComponents(1, lastIndex)


    def _compileSingleComponent(self):
        logging.debug("ComponentSetMatcher _compileSingleComponent")
        
        errMsg = "Error: ComponentSetMatcher.CompileSingleComponent(): "

        end = self._extractComponent(1)

        if len(self.expr) != end:
            raise RegexError(errMsg + "out of bound " + self.expr)
        else:
            self.matcherList.append(ComponentMatcher(self.expr[1:end-1], self.backRef))

    def _compileMultipleComponents(self, start, lastIndex):
        logging.debug("ComponentSetMatcher _compileMultipleComponents")
        
        errMsg = "Error: ComponentSetMatcher.CompileMultipleComponents(): "
        
        index = start
        tmp_index = start
    
        while index < lastIndex:
            if '<' != self.expr[index]:
                raise RegexError(errMsg + "Component expr error " + self.expr)            
            tmp_index = index + 1
            index = self._extractComponent(tmp_index)
            self.matcherList.append(ComponentMatcher(self.expr[tmp_index:index-1], self.backRef))

        if index != lastIndex:
           raise RegexError(errMsg + "Not sufficient expr to parse " + self.expr)

    def _extractComponent(self, index):
        logging.debug("ComponentSetMatcher _extractComponent")
        lcount = 1
        rcount = 0

        while lcount > rcount :
            if len(self.expr) == index:
                break
            elif '<' == self.expr[index]:
                lcount += 1
            elif '>' == self.expr[index]:
                rcount += 1

            index += 1
            
        return index

    def match(self, name, offset, len):
        logging.debug("ComponentSetMatcher match")

        self.matchResult = []
        
        matched = False
        
        if 1 != len:
            return False

        for matcher in self.matcherList:
            res = matcher.match(name, offset, len)
            if True == res:
                matched = True
                break

        if(matched if self.include else (not matched)):
            self.matchResult.append(name[offset])
            return True
        else:
            return False

class BackRefMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        super(BackRefMatcher, self).__init__(expr, backRef, exact)
        logging.debug ("BackRefMatcher Constructor")

        errMsg = "Error: BackRefMatcher Constructor: "
    
        logging.debug ("backRefManager " + str(self.backRef) + " size: " + str(len(self.backRef)))

        lastIndex = len(self.expr) - 1
        
        if '(' == self.expr[0] and ')' == self.expr[lastIndex]:
            self.backRef.append(self)
            self.matcherList.append(PatternListMatcher(self.expr[1:lastIndex-1], self.backRef, self.exact))
        else:
            raise RegexError(errMsg + " Unrecognoized format " + self.expr)


class PatternListMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        super(PatternListMatcher, self).__init__(expr, backRef, exact)
        logging.debug("PatternListMatcher Constructor")

        exprSize = len(self.expr)
        index = 0
        subHead = index
    
        while index < exprSize:
            subHead = index
            (r_res, r_index) = self._extractPattern(subHead, index)
            index = r_index
            if not r_res:
                raise RegexError("Fail to create PatternListMatcher")


    def _extractPattern(self, index, next):
        logging.debug("PatternListMatcher _extractPattern")

        errMsg = "Error: PatternListMatcher._extractPattern: "
    
        start = index
        End = index
        indicator = index

        logging.debug ("expr: " + self.expr + " index: " + str(index))

        if '(' == self.expr[index]:
            index += 1
            index = _extractSubPattern('(', ')', index)
            indicator = index
            end = _extractRepetition(index)
        elif '<' == self.expr[index]:
            index += 1
            index = self._extractSubPattern('<', '>', index)
            indicator = index
            end = self._extractRepetition(index)
            logging.debug("start: " + str(start) + " end: " + str(end) + " indicator: " + str(indicator))
        elif '[' == self.expr[index]:
            index += 1
            index = self._extractSubPattern('[', ']', index)
            indicator = index
            end = self._extractRepetition(index)
            logging.debug("start: " + str(start) + " end: " + str(end) + " indicator: " + str(indicator))
        else:
            raise RegexError(errMsg +"unexpected syntax")
        
        self.matcherList.append(RepeatMatcher(self.expr[start:end], self.backRef, indicator - start))

        return (True, end)

    def _extractSubPattern(self, left, right, index):
        logging.debug("PatternListMatcher _extractSubPattern")

        lcount = 1
        rcount = 0

        while lcount > rcount:
            if index >= len(self.expr):
                raise RegexError("Error: parenthesis mismatch")
            if left == self.expr[index]:
                lcount += 1
            if right == self.expr[index]:
                rcount += 1
            index += 1
            
        return index
    
    def _extractRepetition(self, index):
        logging.debug("PatternListMatcher _extractRepetition")

        exprSize = len(self.expr)

        logging.debug("expr: " + self.expr + " index: " + str(index))

        errMsg = "Error: PatternListMatcher._extractRepetition: "
    
        if index == exprSize:
            return index
    
        if '+' == self.expr[index] or '?' == self.expr[index] or '*' == self.expr[index] :
            index += 1
            return index
        
        if '{' == self.expr[index]:
            while '}' != self.expr[index]:
                index += 1
                if index == exprSize:
                    break
            if index == exprSize:
                raise RegexError(errMsg + "Missing right brace bracket")
            else:
                index += 1
                return index
        else:
            logging.debug ("return index: " + str(index))
            return index

class RepeatMatcher(BaseMatcher):
    def __init__(self, expr, backRef, indicator, exact=True):
        logging.debug("RepeatMatcher Constructor")
        logging.debug("expr: " + expr);
        super(RepeatMatcher, self).__init__(expr, backRef, exact)
        self.indicator = indicator
        if '(' == self.expr[0]:
            self.matcherList.append(BackRefMatcher(self.expr[0:self.indicator], self.backRef))
        else:
            self.matcherList.append(ComponentSetMatcher(self.expr[0:self.indicator], self.backRef))

        self._parseRepetition()
        logging.debug("repeatMin: " + str(self.repeatMin) + " repeatMax: " + str(self.repeatMax))

    def _parseRepetition(self):
        logging.debug("RepeatMatcher _parseRepetition")

        errMsg = "Error: RepeatMatcher._parseRepetition(): ";
    
        exprSize = len(self.expr)
        intMax = sys.maxint
    
        if exprSize == self.indicator:
            self.repeatMin = 1
            self.repeatMax = 1
            return
        else:
            if exprSize == (self.indicator + 1):
                if '?' == self.expr[self.indicator]:
                    self.repeatMin = 0
                    self.repeatMax = 1
                if '+' == self.expr[self.indicator]:
                    self.repeatMin = 1
                    self.repeatMax = intMax
                if '*' == self.expr[self.indicator]:
                    self.repeatMin = 0
                    self.repeatMax = intMax
                return
            else:
                repeatStruct = self.expr[m_indicator:exprSize]
                min = 0
                max = 0

        if re.match('{[0-9]+,[0-9]+}', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = int(repeats[0])
            max = int(repeats[1])
        elif re.match('{[0-9]+,}', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = int(repeat[0])
            max = intMax
        elif re.match('{,[0-9]+}', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = 0
            max = int(repeat[1])
        elif re.match('{[0-9]+}', repeatStruct):
            min = int(repeatsStruct[1:- 1])
            max = min;
        else:
            raise RegexError(errMsg + "Unrecognized format "+ self.expr);
        
        if min > intMax or max > intMax or min > max:
            raise RegexError(errMsg + "Wrong number " + self.expr);
          
        self.repeatMin = min
        self.repeatMax = max

    def match(self, name, offset, len):
        logging.debug("RepeatMatcher.match()")
        self.matchResult = []

        if 0 == self.repeatMin:
            if 0 == len:
                return True

        if self._recursiveMatch(0, name, offset, len):
            for i in range(offset, offset+len):
                self.matchResult.append(name[i])
            return True
        else:
            return False

    def _recursiveMatch(self, repeat, name, offset, len):
        logging.debug ("RepeatMatcher._recursiveMatch()")
        tried = 0
        matcher = self.matcherList[0]

        if 0 < len and repeat > self.repeatMax:
            logging.debug("Match Fail: Reach m_repeatMax && More components")
            return False

        if 0 == len and repeat < self.repeatMin:
            logging.debug("Match Fail: No more components && have NOT reached m_repeatMin")
            return False

        if 0 == len and repeat >= self.repeatMin:
            logging.debug("Match Succeed: No more components && reach m_repeatMin")
            return True

        while tried <= len:
            logging.debug("Attempt tried: " + str(tried))
            
            if matcher.match(name, offset, tried) and self._recursiveMatch(repeat + 1, name, offset + tried, len - tried):
                return True;
            logging.debug("Failed at tried: " + str(tried));
            tried += 1

        return False

class RegexMatcher(BaseMatcher):
    def __init__(self, expr, exact=True):
        super(RegexMatcher, self).__init__(expr, None, exact)
        logging.debug("RegexTopMatcher Constructor")

        self.backRef = []
        errMsg = "Error: RegexTopMatcher Constructor: "
        tmp_expr = self.expr
        if '^' != tmp_expr[0]:
            tmp_expr = "<.*>*" + tmp_expr
        else:
            tmp_expr = tmp_expr[1:]

        if '$' != tmp_expr[-1]:
            tmp_expr = tmp_expr + "<.*>*";
        else:
            tmp_expr = tmp_expr[0:-1]

        logging.debug ("reconstructed expr " + tmp_expr);

        self.matcherList.append(PatternListMatcher(tmp_expr, self.backRef, self.exact))

    def matchName(name):
        return self.match(name, 0, len(name))
        












    
