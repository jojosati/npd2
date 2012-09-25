# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        srchexp
# Purpose:     translate search expression to SQL like pattern
#
# Author:      jojosati
#
# Created:     21/12/2011
# Copyright:   (c) jojosati 2011
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import re
import datetime

def _unicode(u,encoding='utf8') :
    if isinstance(u,unicode) :
        # utf-8 byte within unicode class
        # example : thai ko-kai char
        # utf-8 '\xe0\xb8\x81'
        # sometime from url we got  u'\xe0\xb8\x81'
        ru = repr(u)
        if '\\x' in ru and '\\\\x' not in ru :
            u = unicode(eval(ru[1:]),'utf8')
    if not isinstance(u,unicode) and isinstance(u,basestring):
        u = unicode(u,encoding)
    return u

def _utf8(s,encoding='utf8') :
    if not isinstance(s,unicode) \
    and encoding in ('utf8','utf8') :
        return s

    return _unicode(s,encoding).encode('utf8')

def re_non_escape(c=None):
    if c == '\\' :
        return re.compile(r'(?<!\\)\\(?!\\)')
    return re.compile(r'(?<!\\)'+re.escape(c))

def like2re (ptn_like) :
    ptn_re = re.escape(ptn_like) \
            .replace('\\\\\\','$$$') \
            .replace('\\%','.*') \
            .replace('\\_','.') \
            .replace('$$$','\\')
    ptn_re = re.compile(ptn_re,re.I)
    return ptn_re

class NowObj(object) :
    varname = '$now'
    dateformat = "%d/%m/%Y"
    now_aliases = {
        "$today" : "$now",
        "$yesterday" : "$now(-1)",
        "$tomorrow" : "$now(+1.)",
        "$thisweek" : "$now.bow.prd(+7.)",
        "$lastweek" : "$now.bow.prd(-7.)",
        "$thismonth" : "$now(1).prd(0,+1.)",
        "$lastmonth" : "$now(1).prd(0,-1)",
        "$thisyear" : "$now(1,1).prd(0,0,+1.)",
        "$lastyear" : "$now(1,1).prd(0,0,-1)",
        "$bom" : "$now(1)",
        "$boy" : "$now(1,1)",
        }
    re_nowvar = \
        re.compile(r'((?:\$(?:now(?:\.\w+)*|period))\s*(?:\([^)]*\))*(?:\.\w+(?:\([^)]*\))*)*)')

    def __init__ (self,*args,**kwargs) :
        self.date = self.assign(datetime.date.today(),*args,**kwargs)

    def add (self,date,day=0,month=0,year=0,**kwargs) :
        y = date.year + year
        m = date.month
        d =date.day
        if month :
            m += month
            while m > 12 :
                y += 1; m -= 12
            while m < 1 :
                m += 12; y -= 1
            ld = self.monthdays (datetime.date(y,m,1))
            if d > ld :
                d = ld
        date = datetime.date (y,m,d)
        if day :
            date += datetime.timedelta(days=day)
        return date

    def assign (self,date,*args,**kwargs) :
        # support parms both day,month,year and d,m,y
        parms = ['day','month','year']
        for i in range(len(parms)) :
            v = kwargs.get(parms[i][0])
            if not v and i < len(args) :
                v = args[i]
            if v : kwargs[parms[i]] = v
        for k in ('year','month','day') :
            v = kwargs.get(k)
            if not v : continue
            aflag = isinstance(v,float) or (isinstance(v,basestring) and v.startswith('+'))
            try : v = int(v)
            except : continue #skip this
            parm = {k : v}
            try :
                if aflag or v < 0 :
                    date = self.add(date,**parm)
                else :
                    date = date.replace(**parm)
            except : raise
        return date

    def monthdays (self,date) :
        date = datetime.date (date.year,date.month,28)
        while True :
            try :
                date = date.replace (day=date.day+1)
            except : break
        return date.day

    @property
    def d (self) :
        ''' day value '''
        return self.date.day

    @property
    def day (self) :
        return self.d

    @property
    def m (self) :
        ''' month value '''
        return self.date.month

    @property
    def month (self) :
        return self.m

    @property
    def y (self) :
        ''' year value'''
        return self.date.year

    @property
    def year (self) :
        return self.y

    @property
    def eom (self) :
        '''end of month'''
        return NowObj(self.monthdays(self.date),self.m,self.y)

    @property
    def bow (self) :
        '''begin of week, monday date'''
        wd = self.date.weekday()
        if wd==0 :
            return self
        date = self.date + datetime.timedelta(days=-wd)
        return NowObj(date.day,date.month,date.year)

    @property
    def eow (self) :
        '''end of week, sunday date'''
        wd = 6 - self.date.weekday()
        if wd==0 :
            return self
        date = self.date + datetime.timedelta(days=wd)
        return NowObj(date.day,date.month,date.year)

    @property
    def boq (self) :
        '''begin of quater'''
        m = (int((self.m-1) /3) * 3) +1
        return NowObj(1,m,self.y)

    @property
    def eoq (self) :
        '''begin of quater'''
        return self.boq(m=+2.).eom

    @property
    def boh (self) :
        '''begin of half year'''
        m = 1 if self.m <= 6 else 7
        return NowObj(1,m,self.y)

    @property
    def eoh (self) :
        '''end of half year'''
        return self.boh(m=+5.).eom

    @property
    def str (self) :
        return self.strftime()

    def prd(self,*args,**kwargs) :
        '''period from now ... now(day,month,year)'''
        xdate = self.assign(self.date,*args,**kwargs)
        sign = kwargs.get('sign') or '...'
        if xdate < self.date : return self.strftime(date=xdate)+"..."+self.str
        if xdate > self.date : return self.str+sign+self.strftime(date=xdate)
        return self.str

    def strftime(self,format=None,date=None) :
        if format is None : format = getattr(self,'dateformat')
        if date is None : date = self.date
        return date.strftime(format)

    def __str__(self) :
        return self.str

    def __call__(self,*args,**kwargs) :
        date = self.assign(self.date,*args,**kwargs)
        return NowObj(date.day,date.month,date.year)

class _SrchExp(object) :
    re_exp_items = re.compile(r'(\&\&|\|\||\$qry[0-9]+\:)')
    re_list_items = re.compile(r'(?<!\\)\,')
    re_subexpvar = re.compile(r'^\$qry([0-9]+)\:$')
    re_openrange = re.compile(r'^([><=]=?)')
    def __init__(self,exp,debug=False) :
        self._exp = exp
        self._debug = debug
        self._exptypes = []
        self._subexps = []
        self._not_ = None

    def _translator(self,s) :
        return s

    @property
    def not_(self):
        exp = self.exp # trigger translator
        return self._not_

    @property
    def exp(self) :
        # lazy translation
        if not hasattr(self,'_texp') :
            self._texp = self._translator(self._exp or '')
        return self._texp

    @property
    def items(self) :
        exp = self.exp # trigger translator
        if self.istype('list'):
            ret = []
            for x in re.split(self.re_list_items,exp):
                ret.append(x.replace('\\,',','))
            return [ret]

        elif self.istype('quote','semiquote'):
            ret = [exp]
        elif self.istype('openrange'):
            phases = re.split(self.re_openrange,exp)
            if len(phases)==3 :
                if phases[1]=='=' :
                    phases[1]=='=='
                return [phases[1:]]
        else:
            ret = []
            xret = re.split(self.re_exp_items,exp)
            ex0 = ''
            xlen = len(xret)
            for x in xrange(0,xlen-1,2) :
                ex = xret[x].strip()
                if ex:
                    ex0 += ('%' if ex0 else '') + ex
                ex = xret[x+1]
                phases = re.split(self.re_subexpvar,ex)
                if len(phases)==3 :
                    ex = self._subexps[int(phases[1])]
                ret.append(ex)
            ex = xret[-1].strip()
            if xlen>1 and (ex0 or ex) :
                ex0 += '%' + ex
            else:
                ex0 = ex
            if ex0 :
                ret.insert(0,ex0)
        if self.not_:
            ret.insert(0,'!!')
        return ret

    def new(self,s) :
        cls = self.__class__
        return cls(s,debug=self._debug)

    def newsubexp(self,s) :
        i = len(self._subexps)
        self._subexps.append(self.new(s))
        return '$qry%d:' % i

    def istype(self,*types) :
        if not types :
            return self._exptypes

        for t in types :
            if t in self._exptypes:
                return t

    def __str__(self):
        s = self.exp
        if self._subexps :
            for i in xrange(len(self._subexps)) :
                s = s.replace('$qry'+str(i)+':',str(self._subexps[i]))
            if len(self._subexps)>1 and not self.not_:
                s = '{'+s+'}'
        if self.not_: s = '!{'+s+'}'
        return s
    def __repr__(self):
        n = self.__class__.__name__
        return "<%s('%s')>" % (n,(self._exp or '').replace('\\','\\\\').replace('\'','\\\''))

def unicode_translator(cls,encoding='utf8') :
    # usage : @utf8_translator or @utf8_translator(encoding)
    if isinstance(cls,basestring) :
        encoding = cls
        def wrapper(wcls) :
            return unicode_translator(wcls,encoding)
        return wrapper

    if issubclass(cls,object) :
        _trn = cls._translator
        def _translator(self,s) :
            s = _trn(self,s)
            return _unicode(s,encoding)
        cls._translator = _translator

    return cls

def not_translator(cls) :
    _trn = cls._translator
    def _translator(self,s) :
        s = _trn(self,s)
        if s and s[0]=='!' :
            self._not_ = s[0]
            return s[1:]
        return s

    cls._translator = _translator
    return cls

def nowvar_translator(cls,nowcls=None) :
    if issubclass(cls,NowObj) :
        def wrapper(wcls) :
            return nowvar_translator(wcls,cls)
        return wrapper

    _trn = cls._translator
    nowcls = nowcls or NowObj
    def expand_alias (exp,aliases) :
        _exp = exp
        for w,aw in aliases.iteritems() :
            _exp = _exp.replace(w,aw)
        if _exp != exp :
            _exp = expand_alias (_exp,aliases) # recursive alias
        return _exp

    def _translator(self,s) :
        s = _trn(self,s)
        _now = nowcls()
        s = expand_alias (s,_now.now_aliases)
        phases = re.split(_now.re_nowvar,s)
        for i in range(1,len(phases),2) :
            e = phases[i]
            try :
                e = e.replace(_now.varname,'_now')
                phases[i] = str(eval(e))
            except :
                phases[i] = ''
                if self._debug: raise
        return ''.join(phases)
    cls._translator = _translator
    return cls

def quote_translator(cls):
    _trn = cls._translator
    re_quote = re.compile(
        r'^\s*("(?:[^"]|(?<=\\)")+"|\'(?:[^\']|(?<=\\)\')+\')\s*$'
        )
    re_semiquote = re.compile(
        r'^\s*(\'\'?[^\']+)$'
        )
    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype() : return s
        phases = re.split(re_quote,s)
        if len(phases)==3:
            self._exptypes.append("quote")
            c = phases[1][0]
            return (phases[1][1:-1]) #.replace('\\'+c,c)
        phases = re.split(re_semiquote,s)
        if len(phases)==3:
            c = phases[1][0]
            self._exptypes.append("semiquote")
            return (phases[1][1:]) #.replace('\\'+c,c)
        return s
    cls._translator = _translator
    return cls

def list_translator(cls):
    _trn = cls._translator
    re_listexp = re.compile(
        r'^\s*(\((?:(?:[^),]|\\\)|\\\,)+\,)+(?:[^),]|\\\)|\\\,)+\)|'
        r'\[(?:(?:[^\],]|\\\]|\\\,)+\,)+(?:[^\],]|\\\]|\\\,)+\])\s*$'
        )

    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype() : return s
        phases = re.split(re_listexp,s)
        if len(phases)==3 :
            self._exptypes.append("list")
            return phases[1][1:-1]
        return s
    cls._translator = _translator
    return cls

def range_translator(cls) :
    _trn = cls._translator
    rangesign = '..'
    def _re_range() :
        sign = rangesign[0]
        signlen = len(rangesign)
        return re.compile(
            '(['+sign+']{'+str(signlen)+','+str(signlen+3)+'})')
    re_range = _re_range()
    rangepairs = {
        0: ['>','<'],
        1: ['>=','<'],
        2: ['>=','<='],
        3: ['>','<='],
                }
    # posible openrange sign >,>=,<,<=,=,==
    re_openrange = re.compile(r'^\s*([<>=]=?)')

    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype() : return s

        # .. gt/lt, ... ge/lt, .... ge/le, ..... gt/le
        phases = re.split(re_range,s)
        if len(phases) == 3 :
            pairs = rangepairs[len(phases[1])-len(rangesign)]
            s = ''
            s1 = phases[0].strip()
            s2 = phases[2].strip()
            if s1 :
                s1 = pairs[0]+s1
            if s2 :
                s2 = pairs[1]+s2
            if s1 and s2 :
                self._exptypes.append("range")
                return self.newsubexp(s1+"&&"+s2)
            s = s1+s2
        phases = re.split(re_openrange,s)
        if len(phases)==3 and phases[2].strip() :
            self._exptypes.append("openrange")
        return s

    cls._translator = _translator
    return cls

def autowild_translator(cls,beginlen=1) :
    _trn = cls._translator
    re_wildchar = re.compile(r'(?<!\\)\*')

    def _translator(self,s) :
        s = _trn(self,s)
        semiquote = self.istype('semiquote')
        if not semiquote and self.istype() :
            return s
        s = s.strip()
        if s :
            if semiquote :
                if s.startswith('\'') : # double semi quote
                    self._exptypes.append("raw")
                    return s[1:] # raw expression
            else :
                l = len(s)
                if not re.search(re_non_escape('*'),s) :   # auto wildcard
                    s += '*'
                    if l>beginlen: s = '*' + s
        return s

    cls._translator = _translator
    return cls

def like_translator(cls) :
    _trn = cls._translator
    re_nonlike_esc = re.compile(r'\\(?![%_])')
    re_nonlist_esc = re.compile(r'\\(?![,])')
    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype("raw") : return s
        if self.istype("list") :
            return re.sub(re_nonlist_esc,'',s)
        s = s.strip()
        if s :
            # escape reserved like sign
            s = re.sub(re_non_escape('%'),'\\%',s)
            s = re.sub(re_non_escape('_'),'\\_',s)
            if not self.istype("semiquote","quote","list","subexp") :
                # convert wildcard char to SQL like sign
                s = re.sub(re_non_escape('*'),'%',s)
                s = re.sub(re_non_escape('?'),'_',s)
            # de-escape non like sign
            s = re.sub(re_nonlike_esc,'',s)
        return s

    cls._translator = _translator
    return cls

def subexp_translator(cls):
    _trn = cls._translator
    notwords = ['not','ไม่','ไม่มี']
    re_subexp = re.compile(
        r'(?:\s+|^|(?<=[)\]}]))((?:'\
        +r'\s*|'.join(notwords) +r'\s*|\!)?' \
        +r'(?:\([^)]+\)|\[[^\]]+\]|\{[^}]+\}|\'(?:[^\']|\'\S)+\'|"(?:[^"]|"\S)+"))'
        )
    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype()  : return s

        phases = re.split(re_subexp,s)
        if len(phases) > 1 :
            self._exptypes.append("subexp")
            #self._subexps = subexp
            s = ''
            for i in xrange(0,len(phases)-1,2) :
                ss = phases[i].strip() if phases[i].strip() else (' and ' if i>0 else '')
                if s: ss = ' '+ss
                s += ss + ' '

                ss = phases[i+1]
                c = ss[-1]
                c = {')':'(',']':'[','}':'{'}.get(c,c)
                cidx = ss.find(c)
                if len(phases)==3 and not (phases[0]+phases[2]).strip():
                    # single whole exp
                    ss = ss[cidx:]
                    if cidx:
                        self._not_ = True
                    elif c in '([{':
                        ss = ss[1:-1]
                    return self.newsubexp(ss)
                s += self.newsubexp(ss)
            s = (s+phases[-1]).strip()
        return s

    cls._translator = _translator
    return cls

def and_or_translator(cls):
    _trn = cls._translator
    andwords = ['and',u'และ',]
    orwords = ['or',u'หรือ',]
    re_and_or = re.compile(
        r'(\s+(?:'+'|'.join(orwords) \
        +'|' \
        +'|'.join(andwords) \
        +r')\s+|\s*(?:\&\&|\|\|)\s*)'
        )
    re_subexpvar = re.compile(r'\$qry([0-9]+):')
    def _translator(self,s) :
        s = _trn(self,s)
        if self.istype("quote","semiquote","list") : return s

        phases = re.split(re_and_or,s)
        if len(phases) > 1 :
            self._exptypes.append("and_or")
            #print '<and_or:',phases,'>',
            ss = phases[0]
            if ss and not re.match(re_subexpvar,ss) :
                ss = self.newsubexp(phases[0])
            s = ss
            for i in xrange(1,len(phases)-1,2) :
                ss = phases[i+1].strip()
                if ss and not re.match(re_subexpvar,ss) :
                    ss = self.newsubexp(ss).strip()

                op = phases[i].strip()
                if op in orwords : op = '||'
                if op in andwords : op = '&&'
                if ss :
                    s += (op if op else '') + ss

        return s
    cls._translator = _translator
    return cls

@like_translator
@autowild_translator
@range_translator
@not_translator
@and_or_translator
@subexp_translator
@list_translator
@quote_translator
@nowvar_translator
@unicode_translator
class Search(_SrchExp) :
    pass

if __name__ == '__main__':
    exps= [
        "!cat and not(black or white)",
        "'cat' or 'car'",
        "[cat and (tom or garfield)] and !jerry",
        "!",
        "?",
        "{1 or [2,3]}",
        "(1,2\,3)",
        "1...10",
        "!1..20",
        "$today",
        "$now(1,1).prd(0,0,+1.)",
        "$thismonth",
        ]
    for s in exps:
        src = Search(s)
        print s,"=>",src,src.items


    _now = NowObj()
    print _now(1).prd(0,1.)
##    while True:
##        try:
##            s = raw_input('search:')
##        except: break
##        if not s : break
##        src = Search(s)
##        print s,"=>",src,src.items


