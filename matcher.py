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
        logging.debug(self.__class__.__name__ + ".Constructor")
        self.expr    = expr
        self.backRef = backRef
        self.exact   = exact
        self.matchResult = []
        self.matcherList = []

    def match(self, name, offset, len):
        logging.debug(self.__class__.__name__ + ".match(): " + "expr: " + self.expr + " offset: " + str(offset) + " length: " + str(len))
        self.matchResult = []

        if self._recursiveMatch(0, name, offset, len):
            for i in range(offset,  offset + len):
                self.matchResult.append(name[i])
            return True
        else:
            return False

    def _recursiveMatch(self, mId, name, offset, length):
        logging.debug(self.__class__.__name__ + "._recursiveMatch(): " + self.expr)
        logging.debug("mId: " + str(mId) + " name: " +  str(name) + " offset: " + str(offset) + " length: " + str(length) + " matcherListSize: " + str(len(self.matcherList)))
        tried = 0

        if mId >= len(self.matcherList) :
            if length != 0 :
                logging.debug("Fail " + self.__class__.__name__ + "._recursiveMatch(): no more matcher, but more components")
                return False
            else:
                logging.debug("Succeed " + self.__class__.__name__ + "._recursiveMatch(): no more matcher, no more components")
                return True
    
        matcher = self.matcherList[mId]

        while tried <= length:
            if matcher.match(name, offset, tried) and self._recursiveMatch(mId + 1, name, offset + tried, length - tried) :
                return True
            logging.debug(self.__class__.__name__ + " expr: " + self.expr + " mId: " + str(mId) + " tried: " + str(tried) + " length: " + str(length))
            tried += 1
            
        return False


    def aggressiveMatch(self, name, offset, len):
        logging.debug(self.__class__.__name__ + ".aggressiveMatch(): " + "expr: " + self.expr + " offset: " + str(offset) + " length: " + str(len))
        self.matchResult = []

        if self._aRecursiveMatch(0, name, offset, len):
            for i in range(offset,  offset + len):
                self.matchResult.append(name[i])
            return True
        else:
            return False

    def _aRecursiveMatch(self, mId, name, offset, length):
        logging.debug(self.__class__.__name__ + "._aRecursiveMatch(): " + self.expr)
        logging.debug("mId: " + str(mId) + " name: " +  str(name) + " offset: " + str(offset) + " length: " + str(length) + " matcherListSize: " + str(len(self.matcherList)))

        tried = length

        if mId >= len(self.matcherList) :
            if length != 0 :
                logging.debug("Fail " + self.__class__.__name__ + "._recursiveMatch(): no more matcher, but more components")
                return False
            else:
                logging.debug("Succeed " + self.__class__.__name__ + "._recursiveMatch(): no more matcher, no more components")
                return True

        matcher = self.matcherList[mId]

        while tried >= 0:
            if matcher.aggressiveMatch(name, offset, tried) and self._aRecursiveMatch(mId + 1, name, offset + tried, length - tried):
                return True
            logging.debug(self.__class__.__name__ + " expr: " + self.expr + " mId: " + str(mId) + " tried: " + str(tried) + " length: " + str(length))
            tried -= 1

        return False


class ComponentMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug(self.__class__.__name__ + ".Constructor")
        logging.debug("expr " + expr)
        
        super(ComponentMatcher, self).__init__(expr, backRef, exact)

    def match(self, name, offset, len):
        logging.debug(self.__class__.__name__ + ".match(): " + self.expr)
        logging.debug("Name " + str(name) + " offset " +  str(offset) + " len " +str(len))

        self.matchResult = []
        
        matcher = re.compile(self.expr)
        if self.exact:
            if matcher.match(name[offset]):
                self.matchResult.append(name[offset])
                logging.debug("Succeed " + self.__class__.__name__ + ".match() ")
                return True
        else:
            if matcher.search(name[offset]):
                self.matchResult.append(name[offset])
                return True
            
        return False

    def aggressiveMatch(self, name, offset, len):
        return self.match(name, offset, len)
            

class ComponentSetMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug(self.__class__.__name__ + ".Constructor")
        
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
        logging.debug(self.__class__.__name__ + "._compileSingleComponent")
        
        errMsg = "Error: ComponentSetMatcher.CompileSingleComponent(): "

        end = self._extractComponent(1)

        if len(self.expr) != end:
            raise RegexError(errMsg + "out of bound " + self.expr)
        else:
            self.matcherList.append(ComponentMatcher(self.expr[1:end-1], self.backRef))

    def _compileMultipleComponents(self, start, lastIndex):
        logging.debug(self.__class__.__name__ + "._compileMultipleComponents")
        
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
        logging.debug(self.__class__.__name__ + "._extractComponent")
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
        logging.debug(self.__class__.__name__ + ".match(): " + self.expr)

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

    def aggressiveMatch(self, name, offset, len):
        return self.match(name, offset, len)

class BackRefMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug (self.__class__.__name__ + ".Constructor")
        super(BackRefMatcher, self).__init__(expr, backRef, exact)
        
        errMsg = "Error: BackRefMatcher Constructor: "

        logging.debug ("expr: " +  self.expr);
        logging.debug ("backRefManager " + str(self.backRef) + " size: " + str(len(self.backRef)))

        lastIndex = len(self.expr) - 1
        
        if '(' == self.expr[0] and ')' == self.expr[lastIndex]:
            self.backRef.append(self)
            self.matcherList.append(PatternListMatcher(self.expr[1:lastIndex], self.backRef, self.exact))
        else:
            raise RegexError(errMsg + " Unrecognoized format " + self.expr)


class PatternListMatcher(BaseMatcher):
    def __init__(self, expr, backRef, exact=True):
        logging.debug(self.__class__.__name__ + ".Constructor")
        super(PatternListMatcher, self).__init__(expr, backRef, exact)
        logging.debug("expr: " + self.expr)

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
        logging.debug(self.__class__.__name__ + "._extractPattern")

        errMsg = "Error: PatternListMatcher._extractPattern: "
    
        start = index
        End = index
        indicator = index

        logging.debug ("expr: " + self.expr + " index: " + str(index))

        if '(' == self.expr[index]:
            index += 1
            index = self._extractSubPattern('(', ')', index)
            indicator = index
            end = self._extractRepetition(index)
            if indicator == end:
                self.matcherList.append(BackRefMatcher(self.expr[start:end], self.backRef, self.exact))
            else:
                self.matcherList.append(RepeatMatcher(self.expr[start:end], self.backRef, indicator-start, self.exact))
        elif '<' == self.expr[index]:
            index += 1
            index = self._extractSubPattern('<', '>', index)
            indicator = index
            end = self._extractRepetition(index)
            self.matcherList.append(RepeatMatcher(self.expr[start:end], self.backRef, indicator-start, self.exact))
            logging.debug("start: " + str(start) + " end: " + str(end) + " indicator: " + str(indicator))
        elif '[' == self.expr[index]:
            index += 1
            index = self._extractSubPattern('[', ']', index)
            indicator = index
            end = self._extractRepetition(index)
            self.matcherList.append(RepeatMatcher(self.expr[start:end], self.backRef, indicator-start, self.exact))
            logging.debug("start: " + str(start) + " end: " + str(end) + " indicator: " + str(indicator))
        else:
            raise RegexError(errMsg +"unexpected syntax")
        
        

        return (True, end)

    def _extractSubPattern(self, left, right, index):
        logging.debug(self.__class__.__name__ + "._extractSubPattern")

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
        logging.debug(self.__class__.__name__ + "._extractRepetition")

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
        logging.debug(self.__class__.__name__ + ".Constructor")
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
        logging.debug(self.__class__.__name__ + "._parseRepetition")

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
                repeatStruct = self.expr[self.indicator:exprSize]
                min = 0
                max = 0

        if re.match('{[0-9]+,[0-9]+}$', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = int(repeats[0])
            max = int(repeats[1])
        elif re.match('{[0-9]+,}$', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = int(repeats[0])
            max = intMax
        elif re.match('{,[0-9]+}$', repeatStruct):
            repeats = repeatStruct[1:-1].split(',')
            min = 0
            max = int(repeats[1])
        elif re.match('{[0-9]+}$', repeatStruct):
            min = int(repeatStruct[1:- 1])
            max = min;
        else:
            raise RegexError(errMsg + "Unrecognized format "+ self.expr);
        
        if min > intMax or max > intMax or min > max:
            raise RegexError(errMsg + "Wrong number " + self.expr);
          
        self.repeatMin = min
        self.repeatMax = max

    def match(self, name, offset, len):
        logging.debug(self.__class__.__name__ + ".match(): " + "expr: " + self.expr + " offset: " + str(offset) + " len: " + str(len) + " repeatMin: " + str(self.repeatMin))
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
        logging.debug (self.__class__.__name__ + "._recursiveMatch()" + " repeat: " + str(repeat) + " offset: " + str(offset) + " len: " + str(len) + " rMin: " + str(self.repeatMin) + " rMax: " + str(self.repeatMax))
        tried = 0
        matcher = self.matcherList[0]

        if 0 < len and repeat >= self.repeatMax:
            logging.debug("Match Fail: Reach m_repeatMax && More components")
            return False

        if 0 == len and repeat < self.repeatMin:
            logging.debug("Match Fail: No more components && have NOT reached m_repeatMin " + str(len) + ", " + str(self.repeatMin))
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


    def aggressiveMatch(self, name, offset, len):
        logging.debug(self.__class__.__name__ + ".aggressiveMatch(): " + "expr: " + self.expr + " offset: " + str(offset) + " len: " + str(len) + " repeatMin: " + str(self.repeatMin))
        self.matchResult = []

        if 0 == self.repeatMin:
            if 0 == len:
                return True

        if self._aRecursiveMatch(0, name, offset, len):
            for i in range(offset, offset+len):
                self.matchResult.append(name[i])
            return True
        else:
            return False

    def _aRecursiveMatch(self, repeat, name, offset, len):
        logging.debug (self.__class__.__name__ + "._aRecursiveMatch()" + " repeat: " + str(repeat) + " offset: " + str(offset) + " len: " + str(len) + " rMin: " + str(self.repeatMin) + " rMax: " + str(self.repeatMax))
        tried = len
        matcher = self.matcherList[0]

        if 0 < len and repeat >= self.repeatMax:
            logging.debug("Match Fail: Reach m_repeatMax && More components")
            return False

        if 0 == len and repeat < self.repeatMin:
            logging.debug("Match Fail: No more components && have NOT reached m_repeatMin " + str(len) + ", " + str(self.repeatMin))
            return False

        if 0 == len and repeat >= self.repeatMin:
            logging.debug("Match Succeed: No more components && reach m_repeatMin")
            return True

        while tried >= 0:
            logging.debug("Attempt tried: " + str(tried))
            
            if matcher.aggressiveMatch(name, offset, tried) and self._aRecursiveMatch(repeat + 1, name, offset + tried, len - tried):
                return True;
            logging.debug("Failed at tried: " + str(tried));
            tried -= 1

        return False



class RegexMatcher(BaseMatcher):
    def __init__(self, expr, exact=True):
        logging.debug(self.__class__.__name__ + ".Constructor")
        super(RegexMatcher, self).__init__(expr, None, exact)

        self.backRef = []
        self.second_backRef = []

        self.secondaryMatcher = None

        
        errMsg = "Error: RegexTopMatcher Constructor: "
        tmp_expr = self.expr

        if '$' != tmp_expr[-1]:
            tmp_expr = tmp_expr + "<.*>*";
        else:
            tmp_expr = tmp_expr[0:-1]
        
        if '^' != tmp_expr[0]:
            self.secondaryMatcher = PatternListMatcher("<.*>*" + tmp_expr, self.second_backRef, self.exact)
        else:
            tmp_expr = tmp_expr[1:]

        logging.debug ("reconstructed expr " + tmp_expr);

        self.primaryMatcher = PatternListMatcher(tmp_expr, self.backRef, self.exact)



    def firstMatcher():
        return None

    def matchName(self, name):
        logging.debug(self.__class__.__name__ + ".matchName")
        
        self.secondaryUsed = False
        
        res = self.primaryMatcher.match(name, 0, len(name))
        self.matchResult += self.primaryMatcher.matchResult
        if False == res and None != self.secondaryMatcher:
            res = self.secondaryMatcher.match(name, 0, len(name))
            self.matchResult += self.secondaryMatcher.matchResult
            self.secondaryUsed = True
        return res

    def extract(self, rule):
        logging.debug(self.__class__.__name__ + ".extract")
        
        if not re.match('(\\\\[0-9]+)+$', rule):
            raise RegexError("Wrong format of rule")
        
        refs = rule.split('\\')
        refs.pop(0)

        backRef = self.backRef
        if self.secondaryUsed:
            backRef = self.second_backRef

        result = []
        for index in refs:
            i = int(index) - 1
            
            if len(backRef) <= i or 0 > i:
                raise RegexError("Wrong back reference number!")
            
            result += backRef[i].matchResult

        return result

    def matchN(self, name):
        logging.debug(self.__class__.__name__ + ".matchN")

        self.secondaryUsed = False
        
        res = self.primaryMatcher.aggressiveMatch(name, 0, len(name))
        self.matchResult += self.primaryMatcher.matchResult
        if False == res and None != self.secondaryMatcher:
            res = self.secondaryMatcher.aggressiveMatch(name, 0, len(name))
            self.matchResult += self.secondaryMatcher.matchResult
            self.secondaryUsed = True
        return res









    
