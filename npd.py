# -*- coding: utf-8 -*-

import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker,scoped_session,column_property
from sqlalchemy.orm import mapper as sqla_mapper

from optparse import OptionParser
import os
import csv,datetime,json,re,urllib
import bottle

import server_default
import taxonomies_default
import users_default

from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './sessions',
    'session.auto': True
}
server_app = SessionMiddleware(bottle.app(), session_opts)

rangesign = '..'
re_pageoption = re.compile(r'(?<!~)(?:/+)')
re_rangesign = re.compile('^([^.]*)([\.]{'+str(len(rangesign))+','+str(len(rangesign)+3)+'})')
re_and_or = re.compile(r'(\s+(?:or|หรือ|and|และ)\s+|\s*(?:\&\&|\|\|)\s*)')
#re_and_or = re.compile(r'\s*(\|\||\&\&)\s*')
re_nowvar = re.compile(r'((?:\$(?:now(?:\.\w+)*|period))\s*(?:\(.*\))*(?:\.\w+)*)')

_restrict =  {
    'server' : {
        'host': "0.0.0.0",
        'port': 8080,
        'suburl': "npd",
        'debug': True,
        'sql_dbfile' : 'npd.sqlite.db',
        'sql_echo' : False,
        }
    }

_cfg = {
    'server': {},
    'taxonomies':{},
    'users':{},
    }
    
_cache_ctrl = {}
def reload_cfg (restrict=True) :
    for entry in _cfg :
        fname = 'cfg/'+entry+'_cfg.py'
        if fname in _cache_ctrl :
            try:
                mtime = os.path.getmtime(fname)
                if _cache_ctrl.get(fname) == mtime :  continue
            except: continue
        _e = {}
        _d = globals().get(entry+'_default')
        if _d :
            for k,v in _d.__dict__.iteritems() :
                if k.startswith('__') or k in _d.__builtins__ : continue
                _e[k] = v
        try: 
            execfile(fname,locals(),_e)
            _cache_ctrl[fname] = mtime
            _entry = _restrict.get(entry)
            if _entry :
                if restrict : _e.update(_entry)
                else : 
                    for k in _restrict : _entry[k] = _e.get(k,_entry[k]) 
        except: pass
        _cfg[entry] = _e

# load server_cfg_default
reload_cfg(False)

#----------------------------------------------------

fldmap = [
    # ข้อมูลทั่วไป
    {'name': 'acat', 'csv_field': u'ชนิด',} , # - LOREX, กำไล, จี้, ฯลฯ
    {'name': 'code', 'csv_field': u'รหัส','index':True,'unique':True}, 
    {'name': 'detail', 'csv_field': u'รายการสินค้า',}, 
    {'name': 'weight', 'csv_field': u'น้ำหนัก'},  
    {'name': 'serial', 'csv_field': u'เบอร์',},
    {'name': 'condition',}, # +++ สภาพของทรัพย์ - ชำรุด, ใหม่, xx%
    {'name': 'memo', 'datatype': sqla.Text,}, # +++
    
    # ต้นทุน - costing
    {'name': 'base_cost', 'datatype' : sqla.Float, 'csv_field': u'ทุน',} , #(ราคาซื้อ)
    {'name': 'extra_cost', 'datatype' : sqla.Float, 'csv_field': u'ปรับปรุง',},
    {'name': 'mark_cost', 'datatype' : sqla.Float, 'csv_field': u'ทุนร้าน',} , # (ราคาซื้อ + คชจ.ปรับปรุง + markup คนหาของ)
    #{'name': 'cost_info', 'datatype': sqla.Text,}, # +++

    # ราคาขาย - pricing
    {'name': 'lowest_price', 'datatype' : sqla.Float, 'csv_field': u'ขายประเมิน',}, #(ราคาต่ำสุด ที่ขายได้)
    {'name': 'target_price', 'datatype' : sqla.Float, 'csv_field': u'ราคาตั้งขาย',}, 
    
    # เจ้าของ - owning
    {'name': 'buy_date', 'datatype' : sqla.Date, 'csv_field': u'วันที่ซื้อ',}, 
    {'name': 'owner', 'csv_field': u'ซื้อจาก',}, 
    {'name': 'buy_cond',}, # +++ เงื่อนไขซื้อ - จำนำ, ฝากขาย
    #{'name': 'buy_info', 'datatype': sqla.Text,}, # +++

    # ผู้เก็บรักษา - keeping
    {'name': 'keep_date', 'datatype' : sqla.Date, 'csv_field': u'วันที่',}, 
    {'name': 'keeper', 'csv_field': u'ที่เก็บ',},
    {'name': 'take_date', 'datatype' : sqla.Date, 'csv_field': u'วันที่ยืม',},
    {'name': 'taker', 'csv_field': u'ผู้ยืม',}, 
    {'name': 'taker_price', 'datatype' : sqla.Float, 'csv_field': u'หมายเหตุ','exception': 'memo'}, #(ราคายืม = ราคาที่ตั้งขายให้ผู้ยืม)
    #{'name': 'keep_info', 'datatype': sqla.Text,}, # +++
    
    # ประวัติขายและรับชำระ - selling
    {'name': 'sell_date', 'datatype' : sqla.Date, 'csv_field': u'วันที่ขาย',}, 
    {'name': 'sell_site', 'csv_field': u'สถานที่ขาย',}, 
    {'name': 'buyer', 'csv_field': u'ผู้ซื้อ',}, 
    {'name': 'sell_price', 'datatype' : sqla.Float, 'csv_field': u'ราคาขาย',}, #(ราคาที่ขายได้จริง)
    
    # การชำระ - receiving
    {'name': 'receive_date', 'datatype' : sqla.Date, 'csv_field': u'วันที่รับ',}, 
    {'name': 'receive_type', 'csv_field': u'ชนิดรับ',}, 

    ]
#prepare columns
cols =[
    sqla.Column('id', sqla.Integer, primary_key=True),
    sqla.Column('last_updated', sqla.DateTime, default=sqla.func.current_timestamp(),onupdate=sqla.func.current_timestamp()),
    ]
for fld in fldmap :
    if fld['name'] and fld['name'][0]!='~' :
        cols.append( 
            sqla.Column(fld['name'],
            fld.get('datatype',sqla.String),
            index=fld.get('index',False),
            unique=fld.get('unique',False),
            ))

metadata = sqla.MetaData()

table = sqla.Table('asset',metadata,*cols)

Session = scoped_session(sessionmaker())   
#mapper = Session.mapper
#http://www.sqlalchemy.org/trac/wiki/UsageRecipes/SessionAwareMapper
def session_mapper(scoped_session):
    def mapper(cls, *arg, **kw):
        cls.query = scoped_session.query_property()
        return sqla_mapper(cls, *arg, **kw)
    return mapper
mapper = session_mapper(Session)

class Assets(object): pass
mapper(Assets, table)

def load_csv (csvfile,cnt=0) :
    metadata.drop_all()
    metadata.create_all()

    with open(csvfile) as f:
        i = 0
        cf = csv.DictReader(f, delimiter=',')
        for row in cf:
            rowdata = {}
            for fld in fldmap :
                csvfld = fld.get('csv_field',u'').encode('cp874')
                if not csvfld : continue
                cdata = row[csvfld].rstrip()
                if not cdata : continue
                n = fld['name']

                if fld.get('datatype') is sqla.Date :
                    try :
                        cdata = datetime.datetime.strptime(cdata,'%d/%m/%Y')
                    except :
                        continue
                elif fld.get('datatype') is sqla.Float :
                    try :
                        cdata = float(cdata.replace(',','')) 
                    except : 
                        xn = fld.get('exception')
                        if xn :
                            xdata = unicode(csvfld + '=' + cdata,'cp874')
                            if xn not in rowdata :
                                rowdata[xn] = xdata         
                            else :
                                rowdata[xn] += '\n' + xdata
                        continue
                else :
                    cdata = unicode(cdata,'cp874')
                if n and n[0]!='~' :
                   rowdata[n] = cdata
            if rowdata.get('code') :
                try :
                    table.insert().values(**rowdata).execute()
                    i += 1
                except Exception as e :
                    print "error: %s" % e

            if i % 100 == 0 : print 'insert',i,'rows'
            if i == cnt : break
        print  'total',i,'rows ------------------'

def unicode_bytefix (u,encoding='utf-8') :
    if not isinstance(u,unicode) :
        u = unicode(u,encoding)
    ru = repr(u)
    if '\\x' in ru and '\\\\x' not in ru :
        u = unicode(eval(ru[1:]),'utf-8')
    return u

def _utf8 (s,encoding='utf-8') :
    if encoding not in  ('utf-8','utf8') :
        s = unicode_bytefix(s,encoding)
    if isinstance(s,unicode) :
        s = s.encode('utf-8')
    return s

def utf8_bytefix (s,encoding='utf-8') :
    return _utf8 (unicode_bytefix(s,encoding))

def split_subpage (subpage) :
    return subpage.split('//',1) if '//' in subpage else (subpage,'')

def split_pagetag (pagetag) :
    pageoptions =  re.split(re_pageoption,utf8_bytefix(pagetag))
    if pageoptions :
        for i in range(len(pageoptions)) :
            pageoptions[i] =pageoptions[i].replace("~/","/").replace("~~","~")
    return pageoptions

def expand_subpage (subpage,_recur=[]) :
    alias = _cfg['server'].get('subpage_alias',{})
    (subpage,pagetag) = subpage.split('//',1) if '//' in subpage else (subpage,'')
    if subpage not in _recur and subpage in alias :
        _recur.append(subpage)
        subpage,tag  = expand_subpage(alias[subpage],_recur)
        if tag :
            if pagetag : pagetag += '/'
            pagetag += tag

    return (subpage,pagetag)

def expand_pageoptions (urloptions,_recur=[]) :
    alias = _cfg['server'].get('pageoption_alias',{})
    options = []
    for o in urloptions :
        if not o : continue
        if o not in _recur and o in alias :
            _recur.append(o)
            options += expand_pageoptions(split_pagetag(alias[o]),_recur)
        else :
            options.append(o)
    return options

def expand_pivotcmds (pivots,_recur=None) :
    if _recur is None : _recur = []
    alias = _cfg['server'].get('pivotcmd_alias',{})
    cmds = []
    for c in pivots :
        if not c : continue
        if c not in _recur and c in alias :
            _recur.append(c)
            cmds += expand_pivotcmds(split_pagetag(alias[c]),_recur)
        else :
            cmds.append(c)
    return cmds
    
class NowObj(object) :
    format = "%d/%m/%Y"
    def __init__ (self,*args,**kwargs) :
        self.date = self.assign(datetime.date.today(),*args,**kwargs)
    
    @classmethod
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
        if d :
            date += datetime.timedelta(days=day)
        return date

    @classmethod
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

    @classmethod
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
        if format is None : format = self.format
        if date is None : date = self.date
        return date.strftime(format)

    def __str__(self) :
        return self.str
 
    def __call__(self,*args,**kwargs) :
        date = self.assign(self.date,*args,**kwargs)
        return NowObj(date.day,date.month,date.year)
    
def now_var(exp) :
    _now = NowObj()
    for k in ('$prd','$within','$period') :
        exp = exp.replace(k,'$now.prd')

    phases = re.split(re_nowvar,exp)
    for i in range(1,len(phases),2) :
        e = phases[i]
        try :
            e = e.replace('$now','_now')
            phases[i] = str(eval(e))
        except :
            phases[i] = ''
            if _cfg['server']['debug'] : raise
    return ''.join(phases)

def now_alias (exp) :
    _exp = exp
    for w,aw in _cfg['server']['now_alias'].iteritems() :
        _exp = _exp.replace(w,aw)
    if _exp != exp :
        _exp = now_alias (_exp)
    return _exp
        
def _like_str (s) :
    not_ = ''

    s = now_alias(s)
    
    if s and s[0]=='!' :
        not_ = s[0]
        s = s[1:]
    # translate $now var
    s = now_var(s)
##.. gt/lt
##... ge/lt
##.... ge/le
##..... gt/le
    if s.startswith ('>=') :
        s = s[2:] + '....'
    elif s.startswith ('>') :
        s = s[1:]+'..'
    elif s.startswith ('<=') :
        s = '....' + s[2:]
    elif s.startswith ('<') :
        s = '..' + s[1:]
    #print "rangestr-->",s
    if s  and rangesign not in s :
        if s[0]=='\'' :
            if s[-1] != '\'' :
                s = s[1:]
                if s and s[0]=='\'' :
                    s = s[1:]
                else :
                    s = s.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        else:
            l = len(s)
            s = s.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            if '*' not in s :
                s += '*'
                if l>1: s = '*' + s
            s = s.replace('*','%').replace('?','_')
    return (not_,unicode_bytefix(s))

def maxonomy (field,term='',encoding='utf8',**filter_by) :
    session = Session()
    ret = []

    grp = field
    for i in xrange(10) :
        grp = sqla.func.replace(grp,str(i),' ')
    grp = sqla.func.substr(field,0,sqla.func.max(2,sqla.func.length(sqla.func.rtrim(grp))))
   
    gqry = session.query(grp).distinct()

    #qry = session.query(sqla.func.max(field))
    if term :
        if '%' not in term : term = term+"%" 
        gqry = gqry.filter(field.like(term))
    if filter_by : 
        flts = {}
        for k in filter_by :
            if hasattr(Assets,k) and hasattr(getattr(Assets,k),'property') :
                flts[k] = filter_by[k]
        if flts :
            gqry = gqry.filter_by(**flts) 
    gqry = gqry.group_by(grp)
    #gqry = gqry.subquery()
    
    qry = session.query(sqla.func.max(field))
    for gval, in gqry.all() :
        #print repr(val)
        for val, in  session.query(sqla.func.max(field)).filter(field.like(gval+'%')).all() :
            if encoding : val = val.encode(encoding)
            segs = re.split("([0-9]*)([^0-9]*)([0-9]*)([^0-9]*)$",val)
            if not segs : continue
            for i in xrange(len(segs)-1,-1,-1) :
                if segs[i].isdigit() and len(segs[i])>2 :
                    segs[i] = "%0*d" % (len(segs[i]),int(segs[i]) + 1)
                    break
            val = "".join(segs)
            ret.append(val) 
    return ret

def qry_rangestr (fld,s,chktype=False) :
    q = None
    if rangesign in s :
        dfld = fld
        t = dfld.property.columns[0].type
        srange = re_rangesign.split(s)[1:]
        rt = None
        for ir in range(0,3,2) :
            if not srange[ir] : continue
            if chktype :
                try: 
                    x = datetime.datetime.strptime(srange[ir],"%d/%m/%Y")
                    if rt is None or (rt is sqla.Date) : rt =sqla.Date
                    else : rt = sqla.String; break
                except: pass
                try: 
                    x = int(srange[ir])
                    if rt is None : rt = sqla.Integer
                    elif not ((rt is sqla.Integer) or (rt is sqla.Float)) : 
                        rt = sqla.String; break
                except: pass
                try: 
                    x = float(srange[ir])
                    if rt is None or (rt is sqla.Float) or (rt is sqla.Integer) : rt = sqla.Float
                    else : rt = sqla.String; break
                except: pass
                if (rt is sqla.Date) and not isinstance(t,sqla.Date) :
                    return  False
                if (rt is sqla.Float) and not (isinstance(t,sqla.Float) or isinstance(t,sqla.Integer)) :
                    return False
        
        for ir in range(0,3,2) :
            if isinstance(t,sqla.Date) :
                try: srange[ir] = datetime.date.isoformat(datetime.datetime.strptime(srange[ir],"%d/%m/%Y"))
                except: srange[ir] = None
            if isinstance(t,sqla.Float) :
                try: srange[ir] = float(srange[ir])
                except: srange[ir] = None
            if isinstance(t,sqla.Integer) :
                try: srange[ir] = int(srange[ir])
                except: srange[ir] = None
##.. gt/lt
##... ge/lt
##.... ge/le
##..... gt/le
        slen = len(rangesign)
        clen = len(srange[1])
        #print "--->",srange[1],clen,slen
        if srange[0] :
            q = dfld.__ge__(srange[0]) if clen in  [slen+1,slen+2] else dfld.__gt__(srange[0])
        if srange[2] :
            q2 = dfld.__lt__(srange[2]) if clen in [slen,slen+1] else  dfld.__le__(srange[2])
            q = q2 if q is None else sqla.and_(q,q2)
    return q
    
def taxonomy (field,term='',_start=0,_limit=None,_encoding='utf8',pivotcmds=None,qsearch=None,qscols=None,filters=None,**filter_by) : 
    session = Session()
    ret = [] 
    notop,term = _like_str(term)
    qry = None
    tlen = 0
    if not qscols : qscols = _qsearch_cols()

    if not notop and term :
        tt = '%' * term.count('%')
        if ((len(tt) > 1) and (tt in term)) or tt == term:
            suffix = '*'
            tlen = len(term)
            if not tlen : tlen = 1
            qry = session.query(sqla.func.substr(field,0,tlen).distinct()).filter(field!=None).filter(field!='').order_by(field) 
            if len(tt) != len(term) :
                term = term.replace(tt,'%')
                qry = qry.filter(field.like(term,escape='\\'))
    if qry is None :
        qry = session.query(field.distinct()).filter(field!=None).filter(field!='')
        if term or notop:
            q = qry_rangestr (field,term)
            if q is None :
                q = field.like(term,escape='\\')
            if notop :
                q =sqla.not_(q)
            qry = qry.filter(q)
    if filter_by : 
        qry = qry.filter_by(**filter_by) 

    if qsearch :
        q = _qsearch_qry (qsearch,qscols)
        if q is not None :
            qry = qry.filter(q)
            
    if pivotcmds :
        q = _pivotcmds_qry (pivotcmds,qscols)
        if q is not None :
            qry = qry.filter(q)
    if filters :
        q = _filters_qry (filters)
        if q is not None :
            qry = qry.filter(q)
    if _limit is None :
        _limit = _cfg['server'].get('taxonomy_limit',50)
    if _limit==0 :
        return [qry.count()]
    ord = field 
    if _limit < 0 :
        ord = ord.desc()
        _limit = -_limit
    qry = qry.order_by(ord) 
    rows = qry[_start:_start+_limit] if _limit else qry[_start:]
    for val, in rows :
        if _encoding : val = val.encode(_encoding)
        if tlen : val += '*'
        ret.append(val)
    # append taxonomies
    taxonomies = _cfg['taxonomies']
    if field.key in taxonomies :
        for val in taxonomies[field.key] :
            if term and not tlen and not notop  :
                if len(term)==1 :
                    if not re.match(term,val,re.I) : continue
                else :
                    if not re.search(term,val,re.I) : continue
            if val not in ret : 
                if len(ret) >= _limit : break
                ret.append(val)
    return ret

@bottle.route('/'+_cfg['server']['suburl']+'/ajax/taxonomy/:field')
def ajax_taxonomy_ (field) :
    #t = bottle.request.GET.get('term')
    args = {}
    for x in bottle.request.GET :
        #if x == 'term' : continue
        if x=='_cols' : continue
        if x=='filters' :
            args[x] = json.loads(utf8_bytefix(bottle.request.GET.get(x,'{}')))
            continue
        if x=='pivotcmds' :
            args[x] = json.loads(utf8_bytefix(bottle.request.GET.get(x,'[]')))
            continue
        args[x] = utf8_bytefix(bottle.request.GET.get(x))
    f = eval('Assets.'+field)
    if field == 'code' :
        return json.dumps(maxonomy (f,**args))
    
    return json.dumps(taxonomy (f,**args))

@bottle.route('/'+_cfg['server']['suburl']+'/ajax/jqgrid/edit',method=('POST','GET'))
def ajax_jqgrid_edit () :
    session = Session()
    cmd = bottle.request.POST.get('oper') or bottle.request.GET.get('oper')
    id = bottle.request.POST.get('id') or bottle.request.GET.get('id','')
    msg = cmd +'(id='+id+')'
    try :
        rec = Assets() if id=='_empty' else session.query(Assets).filter(Assets.id==id).one()
    except Exception as e :
        return json.dumps([False,"%s %s" % (msg,e),id])
        
    if cmd=="del" :
        try:
            session.delete(rec)
            session.commit() 
        except Exception as e : #sqla.exc.SQLAlchemyError,exc :
            session.rollback() 
            return json.dumps([False,"%s %s" % (msg,e),id])
        return json.dumps([True,msg,id])

    if cmd in ("add","edit") :
        chflag = False
        for k in bottle.request.POST.keys() :
            if k=='id' : continue
            if hasattr(rec,k) :
                v = unicode(bottle.request.POST.get(k).rstrip(),'utf-8-sig')
                if not v : v = None
                if v and 'date' in k :
                    try : v = datetime.datetime.strptime(v,"%d/%m/%Y")
                    except Exception as e :
                        return json.dumps([False,"%s %s" % (msg,e),id])

                ov = getattr(rec,k)
                if ov != v :
                    setattr(rec,k,v)
                    chflag = True
        for k in bottle.request.GET.keys() :
            if k=='id' : continue
            if hasattr(rec,k) :
                v = unicode(bottle.request.GET.get(k).rstrip(),'utf-8-sig')
                if not v : v = None
                if v and 'date' in k :
                    try: v = datetime.datetime.strptime(v,"%d/%m/%Y")
                    except Exception as e :
                        return json.dumps([False,"%s %s" % (msg,e),id])
                ov = getattr(rec,k)
                if ov != v :
                    setattr(rec,k,v)
                    chflag = True
        if chflag :
            try:
                session.add(rec)
                session.commit() 
                id = rec.id
            except Exception as e  : #sqla.exc.SQLAlchemyError,exc :
                flag = False
                session.rollback() 
                return json.dumps([False,"%s %s" % (msg,e),id])
        return json.dumps([True,msg,id])
    return bottle.HTTPError(403, "unknown command - "+cmd + ".")

def _and_or_qlst (qlst) :
    for i in range(1,len(qlst),2) :
        try : q = qlst[i+1]
        except: continue
        if qlst[i].strip() in ('and','และ','&&') :
            if qlst[0] is False or q is None : 
                continue
            if q is False or qlst[0] is None : 
                qlst[0] = q
                continue
            qlst[0] = sqla.and_(qlst[0],q)
        if qlst[i].strip() in ('or','หรือ','||') :
            if q is False or q is None : 
                continue
            if qlst[0] is False or qlst[0] is None : 
                qlst[0] = q
                continue
            qlst[0] = sqla.or_(qlst[0],q)
    return qlst[0]

def _where (fld,s,chktype=False) :
    s = utf8_bytefix(s)
    if isinstance(fld,list) :
        return _qsearch_qry (s,fld)
    
    if isinstance(fld,basestring) : fld = eval('Assets.'+fld)

    qlst = re.split(re_and_or,s)
    for i in range(0,len(qlst),2) :
        notop,s = _like_str (qlst[i])
        q = None
        if s :
            t = fld.property.columns[0].type
            q = qry_rangestr(fld,s,chktype)
            if q is None :
                dfld = fld
                if  isinstance(t,sqla.Date) : dfld = sqla.func.strftime('%d/%m/%Y',fld)
                if s[0]=='\'' and s[-1]=='\'' :
                    q = dfld.__eq__ (s[1:-1])
                else :
                    q = dfld.like(s,escape='\\')
            if q is not None and q is not False:
                if notop: q = sqla.or_(sqla.not_(q),fld==None)
        else :
            if notop :
                q = sqla.or_(fld=='',fld == None)
        qlst[i] = q

    return _and_or_qlst(qlst)

def _select_cols (_cols=None,_condchk=None) :
    if not _cols :
        _cols = json.loads(utf8_bytefix(bottle.request.GET.get('_cols',_cfg['server']['ajax_fields'])))
    _flds = []
    #if not _condchk : print '--->',
    for f in _cols :
        (n,p) = f.split(':',1) if ':' in f else (f,'')
        n = n.strip()
        if not _condchk  or _condchk (n,p) :
            #if not _condchk : print n,
            _flds.append (eval('Assets.'+n))
    #if not _condchk : print ''
    return _flds

def _qsearch_cols (_cols=None) :
    def cond (n,p) :
        return 'h' not in p
    return _select_cols (_cols,cond)

def _pivotcmds_qry (pivots,cols) :
    qrylst = []
    flst = []
    # -----------------------------
    def _addnew_qlst (*_cs) :
        for _c in _cs :
            if _c not in qlst :
                qlst.append(_c)
    # -----------------------------
    for c in expand_pivotcmds(pivots) :
        if c.startswith('@f-') : 
            f = c[len('@f-'):]
            if f :
                if f[0] in ('[','{'): flst.append(json.loads(f))
                else : flst.append(f)
                
    # @f- pivot filter command
    for c in flst :
        if isinstance(c,basestring) :
            (f,v) = c.split('-',1) if '-' in c else (c,'?')
            if not v : v = '!'
            q = _where (f or cols,v)
            if q is not None : qrylst.append(q)

        if isinstance(c,dict) :
            for f,v in c.iteritems() :
                if not v : v = '!'
                q = _where (f or cols,v)
                if q is not None : qrylst.append(q)

        if isinstance(c,list) :
            for f in c :
                (f,v) = f.split('-',1) if '-' in f else (f,'?')
                if not v : v = '!'
                q = _where (f or cols,v)
                if q is not None : qrylist.append(q)
    if qrylst :
        return sqla.and_(*qrylst)
    return None

def _qsearch_qry (qsearch,cols) :
    qlst = re.split(re_and_or,qsearch)
    for qi in range(0,len(qlst),2) :
        qsearch = qlst[qi]
        qlst[qi] = None
        if qsearch :
            qrylst = []
            for i in xrange(len(cols)) :
                q = _where (cols[i],qsearch,chktype=True)
                if q is not None and q is not False : 
                    qrylst.append(q)
            if qrylst :
                notop = _like_str(qsearch)[0]
                qlst[qi] =  sqla.and_(*qrylst) if notop else sqla.or_(*qrylst)
        
    return _and_or_qlst (qlst)

def _filters_qry (filters) :
    if filters :
        qrylst = []
        for r in filters['rules'] :
            q = _where (r['field'],r['data'])
            if q is not None : qrylst.append(q)
        if qrylst :
            c ='sqla.'+filters['groupOp'].lower()+'_(*qrylst)'
            return eval(c)
    return None

@bottle.route('/'+_cfg['server']['suburl']+'/ajax/jqgrid')
def ajax_jqgrid () :
    #for k in bottle.request.GET.keys() :
    #    print k,repr(unicode(bottle.request.GET.get(k),'utf-8-sig'))
    page = int(bottle.request.GET.get('page',0))
    limit =  int(bottle.request.GET.get('rows',0))
    sidx = bottle.request.GET.get('sidx','')
    sord = bottle.request.GET.get('sord','')
    #print unicode_bytefix(bottle.request.GET.get('_cols',_cfg['server']['ajax_fields']))

    _cols = json.loads(utf8_bytefix(bottle.request.GET.get('_cols',_cfg['server']['ajax_fields'])))
    qsearch = utf8_bytefix(bottle.request.GET.get('qsearch',''))
    pivotcmds = json.loads(utf8_bytefix(bottle.request.GET.get('pivotcmds','[]')))
    filters = {}
    if bottle.request.GET.get('_search','').lower() not in ['false',''] :
        filters = json.loads(utf8_bytefix(bottle.request.GET.get('filters','{}')))

    _qsflds = _qsearch_cols (_cols)

    session = Session()
    ret = {'page':0,'total':0,'records':0,'rows':[]}

    qrylst = []
    if pivotcmds :
        q = _pivotcmds_qry (pivotcmds,_qsflds)
        if q is False : 
            return json.dumps(ret)
        if q is not None :
            qrylst.append(q)
    if qsearch :
        q = _qsearch_qry (qsearch,_qsflds)
        if q is False : 
            return json.dumps(ret)
        if q is not None :
            qrylst.append(q)
    if filters :
        q = _filters_qry (filters)
        if q is False : 
            return json.dumps(ret)
        if q is not None :
            qrylst.append(q)

    # select cols
    _flds = _select_cols (_cols)
    _flds.append(Assets.id)
    qry = session.query(*_flds)
    if qrylst :
        qry = qry.filter(sqla.and_(*qrylst))

    count = qry.count()
    #ret['iTotalDisplayRecords'] = qry.count()
    
    # sorting
    if sidx :
        if sord :
            sord = '.' + sord + '()'
        qry = qry.order_by(eval('Assets.'+sidx+sord))
    
    # limit
    total_pages = 0
    if count > 0 :
        total_pages = int(count/limit)
        if count > total_pages*limit : total_pages += 1
    if page > total_pages : page = total_pages

    offset = (page * limit) - limit

    ret['page'] = page
    ret['total'] = total_pages
    ret['records'] = count
    ret['rows'] = []
    r = 0
    for d in qry[offset:limit+offset] :
        r += 1
        id = d[-1]
        d = list(d[:-1])
        for i in xrange(len(d)) :
            if isinstance(d[i],datetime.date) : d[i] = d[i].strftime('%d/%m/%Y')
            if isinstance(d[i],(str,unicode)) and '\n' in d[i] : d[i] = d[i].replace('\n','<br>')
            #if (r==1) :
            #    print '--->',i,_flds[i].key,repr(d[i])
        ret['rows'].append({'id':id,'cell':d})
    return json.dumps(ret)

#<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.placeholder.js"></script>
#$(function() {	$(document).placeholder(); });

@bottle.route('/'+_cfg['server']['suburl']+'/resource/:filename#.*[^/]$#')
def resource(filename):
    return bottle.static_file(filename,root = './resource/')

@bottle.route('/')
def index () :
    redir = _cfg['server'].get('redir_index')
    if not redir :
        redir = '/'+_cfg['server']['suburl']
    return bottle.redirect(redir)

@bottle.route('/'+_cfg['server']['suburl'],method=['GET','POST'])
@bottle.route('/'+_cfg['server']['suburl']+'/:subpage#.*[^/]$#',method=['GET','POST'])
def npd (subpage='') :
    args = {}
    ss = bottle.request.environ.get('beaker.session')
    subpage = utf8_bytefix(subpage)
    redir_url = '/'+_cfg['server']['suburl']+('/'+subpage) if subpage else ''
    action = bottle.request.params.get('action')

    if _cfg['server'].get('debug')  or action=='reload':
        reload_cfg ()
        bottle.TEMPLATES.clear()
        
    if action=='logout' :
        del ss['logged_in']
        del ss['role']
        ss.save()
        return bottle.redirect(redir_url)
    if action=='login' :
        u = utf8_bytefix(bottle.request.params.get('user'))
        users = _cfg['users']
        if users :
            if u in users:
                p = utf8_bytefix(bottle.request.params.get('password'))
                if p==users[u].get('password',u) :
                    ss.update ({'user': u, 'logged_in': 1, 'role': users[u].get('role','viewer')})
                    return bottle.redirect(redir_url)
            if 'alert_msg' not in args :
                args['alert_msg'] = []
            args['alert_msg'].append('Invalid username or incorrect password.')
        else :
            ss.update( {'user': u, 'logged_in' : 1, 'role' : 'administrator'} )
            ss.save()
            return bottle.redirect(redir_url)
            
    sepoption,pagetag = '',''
    urloptions,pageoptions,pivotcmds = [],[],[]
    kwoptions = {}
    
    if subpage and subpage[0]=='/' : subpage = '/' + subpage
    (urlsubpage,urlpagetag) = split_subpage(subpage)
    if urlpagetag :
        urloptions = split_pagetag (urlpagetag)

    if not subpage : subpage = _cfg['server'].get('default_subpage','')
    subpage,pagetag = expand_subpage(subpage)
    if pagetag :
        sepoption = '/' #deprecate
        pageoptions = expand_pageoptions (split_pagetag (pagetag))
        for o in pageoptions :
            if o[0] == '@' :
                pivotcmds.append(o)
            if '-' in o :
                (k,v) = o.split('-',1)
                if k : kwoptions[k] = v

    args.update({
        'urlsubpage' : urlsubpage,
        'urlpagetag' : urlpagetag,
        'urloptions' : urloptions,
        'subpage' : subpage,
        'pagetag' : pagetag,
        'pageoptions' : pageoptions,
        'kwoptions' : kwoptions,
        'sepoption' : sepoption,
        'pivotcmds' : pivotcmds,
        'title' : '',
        'pagenav' : '',
        'user' : ss.get('user'),
        'logged_in' : ss.get('logged_in'),
        'user_role' : ss.get('role'),
        })
    args.update(_cfg['server'])
    #args['ajax_fields'] = json.dumps(json.loads(args['ajax_fields'])).replace(' ','')
    if subpage :
        try :
            #return subpage
            return bottle.template(subpage,_vars=args)
        except bottle.TemplateError : pass
    mainpage = _cfg['server'].get('default_mainpage') or 'mainpage' 
    return bottle.template(mainpage,_vars=args)


def start_http_server () :
    bottle.debug(_cfg['server'].get("debug",False))
    bottle.run(app=server_app,host=_cfg['server'].get('host','0.0.0.0'),port=_cfg['server'].get("port",8080))

def start_sql_server () :
    engine = sqla.create_engine('sqlite:///'+_cfg['server']['sql_dbfile'],echo=_cfg['server']['sql_echo'])
    # bind engine to 
    metadata.bind = engine
    Session.configure(bind=engine)


if __name__ == "__main__":
    def main () :
        parser = OptionParser()
        parser.add_option("-d", "--dbfile",
                          action="store",
                          dest="dbfile",
                          default=_cfg['server'].get('sql_dbfile',":memory"),
                          help="database file")
        parser.add_option("-c", "--csv",
                          action="store",
                          dest="csv",
                          default="",
                          help="clear current database and import new csv data to database",)
        parser.add_option("-p", "--port",
                          action="store",type="int",
                          dest="port",
                          default=_cfg['server'].get('port',8080),
                          help="server listening port",)
        parser.add_option("-x", "--exit",
                          action="store_true",
                          dest="exit",
                          default=False,
                          help="exit without start server")

        (options, args) = parser.parse_args()
        if options.dbfile :
            _cfg['server']['sql_dbfile'] = options.dbfile
        if options.port :
            _restrict['server']['port'] = options.port
            _cfg['server']['port'] = options.port
            
        start_sql_server ()
        
        if options.csv :
            load_csv (options.csv)

        if not options.exit :
            metadata.create_all()
            start_http_server()

    # ----------------------------------------------------
    main ()
    # ----------------------------------------------------
