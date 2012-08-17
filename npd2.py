# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        npd2
# Purpose:     RESTful server
#
# Author:      jojosati
#
# Created:     07/11/2011
# Copyright:   (c) jojosati 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import optparse
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker,scoped_session,column_property,deferred
from sqlalchemy.orm import mapper as sqla_mapper
#from sqlalchemy.orm import polymorphic_union
import os,datetime,re,csv,json,hashlib,random
import StringIO
import fnmatch,glob
import bottle
from beaker.middleware import SessionMiddleware

import server_default
import taxonomies_default
import users_default
import aliases_default
import regex_default
import summaries_default

_restrict_cfg =  {
    'server' : {
        'version': '1.4e',
        'host': "0.0.0.0",
        'port': 8080,
        'suburl': "app",
        'debug': True,
        #'sql_dbfile' : 'db/default.sqlite.db',
        #'sql_echo' : False,
        'server_type' : 'auto',
        }
     }

_cfg = {
    'server': {},
    'taxonomies':{},
    'users':{},
    'aliases':{},
    'regex':{},
    'summaries':{},
        }
_models = []
# --------------------------------------------------------
def _l(accepts): return (''.join([l[:2] if l[:2] in (accepts.split(',')) else '' for l in bottle.request.headers.get('Accept-Language','').split(',')])+(accepts.split(',')[0]))[:2]
def _m(m,lang,msg): return m.split('//'+(lang or 'en')+':',1)[-1].split('//')[0] if not m or '//' in m or ' ' in m else _m(msg.get(m,m.title().replace('_',' '))+'//',lang,msg)
def reload_cfg (restrict=True,sub='./cfg/') :
    if '_cache_ctrl' not in globals() :
        globals()['_cache_ctrl'] = {}

    for entry in _cfg :
        fname = sub+entry+'_cfg.py'
        if not os.path.isfile(fname) : fname = entry + '_cfg.py'
        mtime = None
        try:
            mtime = os.path.getmtime(fname)
            if _cache_ctrl.get(fname) == mtime :  continue
        except:
            if restrict : continue

        _e = {}
        _d = globals().get(entry+'_default')
        if _d :
            for k,v in _d.__dict__.iteritems() :
                if k.startswith('__') : continue
                _e[k] = v
        if mtime :
            glb = {} if not restrict else _restrict_cfg.get(entry,{})
            try:
                execfile(fname,glb,_e)
                _cache_ctrl[fname] = mtime
            except: pass

        if not restrict and entry in _restrict_cfg : # update restrict
            for k,v in _restrict_cfg[entry].iteritems() :
                _restrict_cfg[entry][k] = _e.get(k,v)
                if k not in _e : _e[k] = v
        _cfg[entry] = _e

def  getcfg (cls,name=None,*args,**kwargs) :
    r = kwargs.get('_root') or _cfg
    if name is None :
        if r is not _cfg and cls not in r :
            getcfg (cls,name,*args)
        return r.get(cls,{})
    if cls=='regex' and name.startswith('re_') and name in r[cls] and isinstance(r[cls][name],basestring) :
        r[cls][name] = re.compile(r[cls][name],re.I)
    if r is not _cfg and name not in r[cls] :
        return getcfg (cls,name,*args)
    return r[cls][name] if not args else r[cls].get(name,args[0])
    #return cls.get(name,default)

# --------------------------------------------------------

class NowObj(object) :
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
        if format is None : format = getattr(self,'dateformat',getcfg('server','dateformat'))
        if date is None : date = self.date
        return date.strftime(format)

    def __str__(self) :
        return self.str

    def __call__(self,*args,**kwargs) :
        date = self.assign(self.date,*args,**kwargs)
        return NowObj(date.day,date.month,date.year)

class Model (object) :
    ##Session = scoped_session(sessionmaker())
    ##metadata = sqla.MetaData()
    #mapper = Session.mapper
    #http://www.sqlalchemy.org/trac/wiki/UsageRecipes/SessionAwareMapper
    modelpath = './models/'
    sqlservers = {}

    @staticmethod
    def concurrent_str(lastupdate):
        if isinstance(lastupdate,basestring) :
            try: lastupdate = datetime.datetime.strptime(last_updated,self.datetimeformat)
            except: return lastupdate
        if isinstance(lastupdate,datetime.datetime) :
            return lastupdate.strftime('%y%m%d%H%M%S')
        return ''

    @staticmethod
    def session_mapper(scoped_session):
        def mapper(cls, *arg, **kw):
            cls.query = scoped_session.query_property()
            return sqla_mapper(cls, *arg, **kw)
        return mapper

    @property
    def suburl (self) :
        u = self.getcfg('server','suburl','') or self.modeler._options_.get('suburl')
        u = u or self.modeler._options_.get('modelname') or self.name
        return u.lower()

    def sqlite_custom_function (self):
        if not self.dbfile.startswith('sqlite:') :
            return
        con = self.sqlserver['engine'].connect()
        def charindex(needle,hay,start=0) :
            try : return hay.find(needle,start)+1
            except : return 0
        def floor(val) :
            try : return float(int(val))
            except : return val
        def format(val,decimal) :
            try : return "%.*f" % (decimal,float(val))
            except : return val
        try:
            con.execute('select charindex(?,?),floor(?),format(?,2)',('A','ABC',12.34,12.3))
        except :
            con.connection.create_function("charindex",2,charindex)
            con.connection.create_function("floor",1,floor)
            con.connection.create_function("format",2,format)

        echo = self.getcfg('server','sql_echo',False)
        if echo :
            print 'testing custom function for',self.dbfile
            for r in con.execute('select charindex(?,?),floor(?),format(?,2)',('A','ABC',12.34,12.3)):
                print '(charindex,floor,format)',r
            session = self.Session()
            for r in session.query(sqla.func.charindex('A','ABC'),sqla.func.floor(12.34),sqla.func.format(12.3,2)).all() :
                print '(charindex,floor,format)',r

    @property
    def sqlserver (self) :
        if not hasattr(self,'dbfile') :
            dbfile= self.getcfg('server','sql_dbfile',None) or self.modeler._options_.get('sql_dbfile')
            if ':' not in dbfile : dbfile = 'sqlite:///'+dbfile
            self.dbfile = dbfile
        else: dbfile = self.dbfile
        if dbfile in self.sqlservers :
            return Model.sqlservers[dbfile]
        #print self.name,dbfile
        echo = self.getcfg('server','sql_echo',False)
        engine = sqla.create_engine(dbfile,echo=echo)
        metadata =  sqla.MetaData()
        Session = scoped_session(sessionmaker())
        mapper = Model.session_mapper(Session)
        metadata.bind = engine
        Session.configure(bind=engine)
        Model.sqlservers[dbfile] = {
            'engine' : engine,
            'metadata' : metadata,
            'Session' : Session,
            'mapper' : mapper,
            }
        return Model.sqlservers[dbfile]

    @property
    def dateformat (self) :
        return self.getcfg('server','dateformat','%x')

    @property
    def datetimeformat (self) :
        return self.dateformat + ' %X'

    def version_tag (self,**kwargs) :
        tags = [datetime.datetime.now().strftime('%y%m%d.%H%M%S'),
                kwargs.get('oper') or '',
                kwargs.get('user_id') or '',
                ]
        return '['+','.join(tags)+']'

    @property
    def version_taglike (self) :
        return '[%]'

    def randomseed(self,seed=1):
        return (seed * random.random())

    def merge_fld_options (self) :
        for fld in self.modeler._fields_ :
            n = fld['name']
            if n in self.modeler._fld_options_ :
                if 'options' not in fld : fld['options'] = {}
                fld['options'].update(self.modeler._fld_options_[n])

    def reload_model (self) :
        fname = './models/'+self.name+'/model_cfg.py'
        try: mtime = os.path.getmtime(fname)
        except: return

        if not hasattr(self,'_cache_ctrl') :
            self._cache_ctrl = {}
        if mtime==self._cache_ctrl.get(fname): return

        xname = {};
        try :
            execfile(fname,{},xname)
            self._cache_ctrl[fname] = mtime
        except : return

        for k in xname :
            if k == '_fields_' : continue
            if not hasattr(self.modeler,k) :
                setattr(self.modeler,k,xname[x])
            else :
                getattr(self.modeler,k).update(xname[k])
        self.merge_fld_options()

    def reload_cfg (self,reloadmodel=True) :
        if not hasattr(self,'_cache_ctrl') :
            self._cache_ctrl = {}
        if not hasattr(self,'_cfg') :
            self._cfg = {}

        sub = self.modelpath +self.name + '/'

        for entry in _cfg :
            fname = sub+entry+'_cfg.py'
            mtime = None
            try: mtime = os.path.getmtime(fname)
            except: pass

            md5 = hashlib.md5(str(_cfg[entry])).digest()
            ch = (self._cache_ctrl.get('md5_'+entry) != md5)
            if not ch and mtime :
                ch = (self._cache_ctrl.get(fname) != mtime)
            if ch :
                self._cfg[entry] = dict(_cfg[entry])
                self._cache_ctrl['md5_'+entry] = md5
                if mtime :
                    try:
                        execfile(fname,_restrict_cfg.get(entry,{}),self._cfg[entry])
                        self._cache_ctrl[fname] = mtime
                    except:
                        if _restrict_cfg.get('debug') : raise
        if reloadmodel : self.reload_model()

    def  getcfg (self,cls,name=None,*args) :
        return getcfg(cls,name,*args,_root=getattr(self,'_cfg',None))

    def __init__ (self,name,dbfile=None) :
        self.name = name
        #self._cfg = dict(_cfg)

        #ilist = ["_fields_","_tablename_","_options_","_permissions_"]
        if isinstance(name,basestring) :
            fname = './models/'+name+'.py'
            if not os.path.isfile(fname) : fname =name + '.py'
            name = {}
            execfile (fname,{},name) # if not exists, raise error
        if isinstance(name,dict) :
            for k in ('_options_','_permissions_','_fld_options_') :
                if k not in name : name[k] = {}
            self.modeler = type((name['_options_'].get('modelname') or name.get('_tablename_',self.name)) + '_modeler',(object,),name)
        if not hasattr(self.modeler,'_wrapper_') : self.modeler._wrapper_= None
        self._cfg = {}
        self.reload_cfg(False)
        if dbfile : self._cfg['server']['sql_dbfile'] = dbfile
        self.metadata = self.sqlserver['metadata']
        self.mapper = self.sqlserver['mapper']
        self.Session= self.sqlserver['Session']
        tbname = getattr(self.modeler,'_tablename_',self.name)
        odbname = self.modeler._options_.get('modelname') or ('tbl'+ tbname)
        isvc = self.modeler._options_.get('version_control') and self.modeler._options_.get('version_table')
        if self.getcfg('server',"debug",False):
            print 'dbfile:',self.dbfile
            print 'table:',odbname,',',tbname
            if self.modeler._options_.get('version_control') :
                print 'version control:',self.modeler._options_.get('version_control'),',',self.modeler._options_.get('version_table')

        def _metatable(_vc=False) :
            #prepare columns
            cols =[
                sqla.Column('id', sqla.Integer, primary_key=True),
                sqla.Column('last_updated', sqla.DateTime, default=sqla.func.current_timestamp(),onupdate=sqla.func.current_timestamp()),
                ]
            #mapper_prop = {}
            for fld in self.modeler._fields_ :
                if fld.get('calculated') : continue
                n = fld.get('name')
                if n and n[0]!='~' :
                    c = sqla.Column(
                                n,
                                getattr(sqla,fld.get('datatype') or 'String'),
                                index=fld.get('index',False),
                                unique=fld.get('unique',False),
                            )
                    cols.append(c)
                    #if fld.get('deferred'):
                    #    mapper_prop[n] = deferred(c)

            if not _vc :
                self.table = sqla.Table(tbname,self.metadata,*cols)
                self.odb = type(odbname,(object,),{})
            else:
                self.vc_table = sqla.Table('vc_'+tbname,self.metadata,*cols)
                self.vc_odb = type('vc_'+odbname,(object,),{})
            return #mapper_prop

            # --- end metatable
        #mapper_prop = _metatable()
        #self.mpobj = self.mapper(self.odb, self.table,properties=mapper_prop)
        _metatable()
        self.mpobj = self.mapper(self.odb, self.table)
        wrapper = getattr(self.modeler._wrapper_,'mapper_prop',None)
        sqlfn = {'sqla':sqla,'column_property':column_property,'deferred':deferred}
        if wrapper : wrapper(self,self.mpobj,sqlfn);
        if isvc :
            #vc_mapper_prop = _metatable(True)
            #self.vc_mpobj = self.mapper(self.vc_odb, self.vc_table,properties=vc_mapper_prop)
            _metatable(True)
            self.vc_mpobj = self.mapper(self.vc_odb, self.vc_table)
            if wrapper : wrapper(self,self.vc_mpobj,sqlfn);
            #self.metadata.drop_all(tables=[self.vc_table])

        self.metadata.create_all()
        self.sqlite_custom_function()

    def colModel (self,name=None) :
        if not isinstance(name,basestring) and hasattr(name,'key') :
            name = name.key
        if name is None :
            return self.modeler._fields_
        for fld in self.modeler._fields_ :
            if fld['name'] == name :
                #if 'options' not in fld : fld['options'] = {}
                #fld['options'].update(self.modeler._fld_options_.get(name,{}))
                return fld
        if name=='id' :
            return {'name':name,'datatype':'Integer', 'primary_key':True, 'options': {'access':'gv'}}
        if name=='last_updated' :
            return {'name':name,'datatype':'DateTime',  'options': {'access':'gv'}}
        if name=='__table__' :
            return {'name':name,  'options': {'label':self.modeler._options_.get('caption') or self.modeler._options_.get('modelname') or self.modeler._tablename_}}
        return None

    def colPermission (self,name,role,access=None) :
        if not isinstance(name,basestring) and hasattr(name,'key') :
            name = name.key
        fld = self.colModel (name)
        if not fld : return True # not in table allow all

        tblperm = None
        if not name.startswith('__') :
            tblperm = self.colPermission ('__table__',role)
            if not tblperm : return False

        plst = {}
        role = role or ''
        for r in role.split(',') :
            _tperm = '*' if not tblperm else tblperm.get(r,tblperm.get('*',''))
            _perm_ = getattr(self.modeler,'_permissions_',{})
            if r not in  _perm_ : r = '*'
            p = _perm_.get(r)
            if p is not None :
                p = p.get(name,p.get('*',''))
                if p is None : p = fld.get('options',{}).get('access','*')
                if p and p!='!*' :
                    if _tperm!='*' :
                        if p=='*' : p = _tperm
                        else :
                            _p = ''
                            for achr in _tperm :    # filter by __table__ permission
                                if achr in p :  _p += achr
                            p = _p
                    plst[r] = p
        if not access : return plst
        for achr in access :
            for r,p in plst.iteritems() :
                p = plst[r]
                if len(p)>1 and p[0]=='!' :
                    if achr not in p[1:] and p[1:] != '*' :  return r  # allow by role r
                elif achr in p  or p=='*' : return r  # allow by role r
        return False

    def mediaPermission (self,mediapath,role) :
        mediapath = mediapath.replace('\\','/')
        role = role or ''
        for r in role.split(',') :
            _perm_ = getattr(self.modeler,'_permissions_',{})
            if r not in  _perm_ : r = '*'
            p = _perm_.get(r)
            if p is not None :
                p = p.get('__media__','')
                for n in p.split(',') :
                    if n and (bool('/' in n) == bool('/' in mediapath)):
                        if fnmatch.fnmatch(mediapath,n) :
                            return True
        return False

    def historyPermission (self,role,access=None) :
        return self.colPermission('__history__',role,access)

    def load_csv_base (self,csvfile,**kwargs) :
        if kwargs.get('drop',True) :
            self.metadata.drop_all(tables=[self.table])
        self.metadata.create_all(tables=[self.table])
        _encoding = kwargs.get('_encoding')
        if _encoding is None :
            _encoding = self.modeler._options_.get('csv_encoding',self.getcfg('server','csv_encoding'))
        if ',' in csvfile :
            csvfile,_encoding = csvfile.split(',',1)
        if not kwargs.get('quiet'):
            print 'CSV file',csvfile,_encoding
        cnt = kwargs.get('cnt',0)
        csvcnt = 0
        rowcnt = 0
        errcnt = 0
        with open(csvfile) as f:
            cf = csv.DictReader(f, delimiter=',')
            for row in cf:
                csvcnt += 1
                rowdata = {}
                rowvalid = True
                for fld in self.modeler._fields_ :
                    n = fld['name']
                    fld = self.colModel(n)
                    csvfld = self.modeler._fld_options_.get(n,{}).get('csv_field',fld.get('options',{}).get('csv_field'))
                    if not csvfld : continue
                    if _encoding :
                        csvfld = unicode(csvfld,"utf-8").encode(_encoding)
                    cdata = row.get(csvfld,'').rstrip()
                    if _encoding :
                        cdata = unicode(cdata,_encoding)
                        csvfld = unicode(csvfld,_encoding)
                    if not cdata :
                        if self.modeler._fld_options_.get(n,{}).get('csv_valid',fld.get('options',{}).get('csv_valid')) :
                            rowvalid = False
                            break
                        continue

                    if fld.get('datatype') in ['Date'] :
                        try :
                            cdata = datetime.datetime.strptime(cdata,self.dateformat)
                        except :
                            continue
                    elif fld.get('datatype') in ['DateTime'] :
                        try :
                            cdata = datetime.datetime.strptime(cdata,self.datetimeformat)
                        except :
                            continue
                    elif fld.get('datatype') in ['Float','Integer'] :
                        try :
                            cdata = float(cdata.replace(self.getcfg('server','numbersep'),''))
                        except :
                            xn = fld.get('options',{}).get('csv_exception')
                            if xn :
                                xdata = cdata #csvfld + '=' + cdata
                                if not rowdata.get(xn) :
                                    rowdata[xn] = xdata
                                else :
                                    rowdata[xn] += '\n'+xdata
                            continue

                    if n and n[0] not in '~$' :
                        rowdata[n] = cdata

                if rowvalid :
                    if 'verifyrowdata' in kwargs :
                        rowvalid = kwargs['verifyrowdata'](rowdata)
                if rowvalid :
                    try :
                        self.table.insert().values(**rowdata).execute()
                        rowcnt += 1
                    except Exception as e :
                        errcnt += 1
                        if not kwargs.get('quiet'):
                            print "error: %s" % e

                if csvcnt % 100 == 0 and not kwargs.get('quiet'):
                    print 'reading',csvcnt,',writing',rowcnt,'so far...'
                if csvcnt == cnt : break
            if not kwargs.get('quiet'):
                print  'Total- read:',csvcnt,',write:',rowcnt,',error:',errcnt
            return [csvcnt,rowcnt,errcnt]

    def load_csv (self,csvfile,**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'load_csv',None)
        if wrapper : return wrapper(self,csvfile,**kwargs)
        return self.load_csv_base(csvfile,**kwargs)

    def ajaxCols (self,use_cols=True,**kwargs) :
        if use_cols :
            cols = kwargs.get('_cols')
            if cols :
                if isinstance(cols,basestring) : cols = self.json_loads(cols,True)
                return cols
        cols = []
        role = kwargs.get('user_role')
        def _add_cols_ (_fld,_pp) :
            _nn = _fld['name']
            if self.colPermission(_nn,role,'gave') :
                _p = ':h' if 'h' in _pp else ''
                if not _p and not self.colPermission(_nn,role,'g') : _p = ':h'
                cols.append(_nn+_p)

        ajaxflds = self.modeler._options_.get('ajax_fields') # get default ajax list
        if ajaxflds :
            for n in ajaxflds :
                (n,l) = n.split('|',1) if '|' in n else (n,'')
                (n,p) = n.split(':',1) if ':' in n else (n,'')
                fld = self.colModel(n)
                if fld : _add_cols_(fld,p)

        for fld in self.modeler._fields_ :
            _add_cols_(fld,'')
        return cols

    def ajaxExtCols (self,**kwargs) :
        cols = []
        role = kwargs.get('user_role')

        def _add_cols_ (_fld,_pp,_ll) :
            _nn = _fld['name']
            if self.colPermission(_nn,role,'gave') :
                _fld_o = _fld.get('options',{})
                p = _pp
                if not _pp :
                    if not self.colPermission(_nn,role,'g') : p += 'h' # hidden on grid
                    for _p in 'ave' :
                        if self.colPermission(_nn,role,_p) : p += _p
                    if _fld_o.get('required') : p += 'r'
                else :
                    for _p in 'ae' : # checking not allow permission
                        if _p in p and not self.colPermission(_nn,role,_p) : p.replace(_p,'')

                if 'N' not in p and 'D' not in p and 'I' not in p:
                    if  _fld.get('datatype') in ['Float'] : p += 'N'
                    elif _fld.get('datatype') in ['Integer'] : p += 'I'
                    elif _fld.get('datatype') in ['Date'] : p += 'D'
                if 'W' not in p and _fld_o.get('colwidth') : p += 'W('+str(_fld_o.get('colwidth'))+')'
                if 'L' not in p and _fld_o.get('rowlength') : p += 'L('+str(_fld_o.get('rowlength'))+')'
                if 'G' not in p and _fld_o.get('colgroup') : p += 'G('+str(_fld_o.get('colgroup'))+')'
                lbl = _ll or _fld_o.get('label',_fld_o.get('csv_field',''))

                if p : _nn += ':' + p
                if lbl : _nn += '|' + lbl
                cols.append(_nn)

        ajaxflds = self.modeler._options_.get('ajax_fields') # get default ajax list
        if ajaxflds :
            for n in ajaxflds :
                (n,l) = n.split('|',1) if '|' in n else (n,'')
                (n,p) = n.split(':',1) if ':' in n else (n,'')
                fld = self.colModel(n)
                if fld : _add_cols_(fld,p,l)
        if not cols :
            for fld in self.modeler._fields_ : # or create ajax list from _fields_
                _add_cols_ (fld,'','')
        n = '__table__'
        p = ''
        # grid, pivot-url, search, quick-search, add, delete, edit, view, zummary, export, history
        for _p in self.modeler._options_.get('all_permission') or  self.getcfg('server','all_permission','') or 'gpsqadevzxh' :
            if self.colPermission(n,role,_p) : p += _p
        fld = self.colModel(n)
        lbl = '' if not fld else fld.get('options').get('label','')
        if p : n += ':' + p
        if lbl : n += '|' + lbl
        cols.append(n)
        return cols

    def qsearchCols (self,**kwargs) :
        qscols = kwargs.get ('qscols')
        if qscols :
            return qscols

        qscols = []
        role = kwargs.get('user_role')
        _cols = self.ajaxCols (**kwargs)
        if _cols :
            for c in _cols :
                (n,p) = c.split(':',1) if ':' in c else (c,'')
                if not self.colModel(n) : continue
                if not self.colPermission(n,role,'gave') : continue
                if 'h' not in p :
                    qscols.append(n)
        return qscols

    @classmethod
    def json_loads(self,jstr,shortlist=False) :
        jstr = self.utf8_bytefix(jstr)
        try :
            return json.loads(jstr)
        except Exception as e:
            if not shortlist : raise e
        return jstr.split(',')

    @classmethod
    def json_dumps(self,obj) :
        return json.dumps(obj)

    @staticmethod
    def unicode_bytefix (u,encoding='utf-8') :
        if not isinstance(u,unicode) :
            u = unicode(u,encoding)
        ru = repr(u)
        if '\\x' in ru and '\\\\x' not in ru :
            u = unicode(eval(ru[1:]),'utf-8')
        return u

    @classmethod
    def _utf8 (self,s,encoding='utf-8') :
        if encoding not in  ('utf-8','utf8') :
            s = self.unicode_bytefix(s,encoding)
        if isinstance(s,unicode) :
            s = s.encode('utf-8')
        return s

    @classmethod
    def utf8_bytefix (self,s,encoding='utf-8') :
        return self._utf8 (self.unicode_bytefix(s,encoding))

    def split_subpage (self,subpage) :
        return subpage.split('//',1) if '//' in subpage else (subpage,'')

    def split_pagetag (self,pagetag) :
        pageoptions =  re.split(self.getcfg('regex','re_pageoption'),pagetag)
        if pageoptions :
            for i in range(len(pageoptions)) :
                pageoptions[i] =pageoptions[i].replace("~/","/").replace("~~","~")
        return pageoptions

    def expand_now_alias (self,exp,_aliases=None) :
        if _aliases is None :
            _aliases = self.getcfg('aliases','now_alias',{})
        _exp = exp
        if _aliases :
            for w,aw in _aliases.iteritems() :
                _exp = _exp.replace(w,aw)
            if _exp != exp :
                _exp = self.expand_now_alias (_exp,_aliases) # recursive alias

        ##note: move to server_default /server_cfg
        ##for k in ('$prd','$within','$period') :
        ##   _exp = _exp.replace(k,'$now.prd')
        return _exp

    def now_var(self,exp) :
        exp = self.expand_now_alias (exp)

        _now = NowObj()
        phases = re.split(self.getcfg('regex','re_nowvar'),exp)
        for i in range(1,len(phases),2) :
            e = phases[i]
            try :
                e = e.replace('$now','_now')
                phases[i] = str(eval(e))
            except :
                phases[i] = ''
                if self.getcfg('server','debug') : raise
        return ''.join(phases)

    def like_str (self,s) :
        not_ = ''
        s = self.unicode_bytefix(s)

        if s == '!' : s += '?'
        if s and s[0]=='!' :
            not_ = s[0]
            s = s[1:]
        # translate $now
        s = self.now_var(s)

        # translate range sign
        # .. gt/lt, ... ge/lt, .... ge/le, ..... gt/le
        rangesign = self.getcfg('regex','rangesign')
        if rangesign not in s :
            ss = re.split(self.getcfg('regex','re_openrange'),s)
            if len(ss)==3 and not ss[0].strip() and  ss[2].strip() :
                if ss[1]=='>=' : s = ss[2] + rangesign + (rangesign[0]*2)
                if ss[1]=='>' : s = ss[2] + rangesign
                if ss[1]=='<' : s = rangesign + ss[2]
                if ss[1]=='<=' : s = rangesign + (rangesign[0]*2) + ss[2]
            elif self._is_quoteqry (s)==1 :
                s = s.strip()[1:-1].replace('\\','')
            elif ',' in s and self._is_blockqry (s)==1 :
                pass
            elif s :
                if s.strip()[0] in '\'' :
                    s = s.strip()[1:]
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
        return (not_,s)

    def _range_where (self,fld,s,chktype=False) :
        rangesign = self.getcfg('regex','rangesign')
        if rangesign not in s :
            return None
        srange = re.split(self.getcfg('regex','re_range'),s)
        if len(srange) != 3 : return None

        q = None
        dfld = fld
        t = dfld.property.columns[0].type
        rt = None
        for ir in range(0,3,2) :
            if not srange[ir] : continue
            if chktype :
                try:
                    x = datetime.datetime.strptime(srange[ir],self.dateformat)
                    if rt is None or (rt is sqla.Date) : rt =sqla.Date
                    else : rt = sqla.String; break
                except: pass
                try:
                    x = datetime.datetime.strptime(srange[ir],self.datetimeformat)
                    if rt is None or (rt is sqla.DateTime) : rt =sqla.DateTime
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
                if (rt is sqla.Float) and not isinstance(t,(sqla.Float,sqla.Integer)) :
                    return False
        for ir in range(0,3,2) :
            if isinstance(t,sqla.DateTime) :
                try: srange[ir] = datetime.datetime.isoformat(datetime.datetime.strptime(srange[ir],self.datetimeformat))
                except: srange[ir] = None
            elif isinstance(t,sqla.Date) :
                try: srange[ir] = datetime.date.isoformat(datetime.datetime.strptime(srange[ir],self.dateformat))
                except: srange[ir] = None
            elif isinstance(t,sqla.Float) :
                try: srange[ir] = float(srange[ir])
                except: srange[ir] = None
            elif isinstance(t,sqla.Integer) :
                try: srange[ir] = int(srange[ir])
                except: srange[ir] = None
        # .. gt/lt, ... ge/lt, .... ge/le, ..... gt/le
        slen = len(rangesign)
        clen = len(srange[1])
        if srange[0] :
            q = dfld.__ge__(srange[0]) if clen in  [slen+1,slen+2] else dfld.__gt__(srange[0])
        if srange[2] :
            q2 = dfld.__lt__(srange[2]) if clen in [slen,slen+1] else  dfld.__le__(srange[2])
            q = q2 if q is None else sqla.and_(q,q2)
        return q

    def _is_wholeqry (self,re_str,s) :
        ''' return 0=no quote, 1=whole quote, otherwise = number of segment '''
        x = re.split(re_str,s)
        l = len(x)
        if l > 1 :
            if not x[0] : l -= 1
            if not x[-1] : l -= 1
        else : l = 0
        return l

    def _is_quoteqry (self,s) :
        return self._is_wholeqry(self.getcfg('regex','re_quoteqry'),s)

    def _is_blockqry (self,s) :
        return self._is_wholeqry(self.getcfg('regex','re_blockqry'),s)

    def _sqlformatfld (self,fld,shortfmt=False) :
        if hasattr(fld,'property') :
            t = fld.property.columns[0].type
            dfld = fld
            if  isinstance(t,sqla.Date) : dfld = sqla.func.strftime(self.dateformat,fld)
            if  isinstance(t,sqla.DateTime) :
                if shortfmt :
                    dfld = sqla.func.strftime(self.dateformat,fld)
                else :
                    dfld = sqla.func.strftime('%c',fld)
            if isinstance(t,(sqla.Float,sqla.Integer)) :
                dfld = sqla.cast(fld,sqla.String)
            return sqla.func.ifnull(dfld,'')
        return fld

    def _like_where (self,fld,s) :
        q = None
        if s :
            dfld = self._sqlformatfld(fld)
##            t = fld.property.columns[0].type
##            dfld = fld
##            if  isinstance(t,sqla.Date) : dfld = sqla.func.strftime(self.dateformat,fld)
##            if  isinstance(t,sqla.DateTime) : dfld = sqla.func.strftime('%c',fld)
            if self._is_blockqry(s)==1 :
                ss = s.strip()[1:-1].replace('\\','').split(',')
                if len(ss) > 1 :
                    if '' in ss : dfld = sqla.func.ifnull(dfld,'')
                    q = dfld.in_(ss)
                else :
                    ss = s.strip()[1:-1].replace('\\','')
                    if not ss : dfld = sqla.func.ifnull(dfld,'')
                    q = dfld.contains(ss)
            if q is None and self._is_quoteqry(s)==1 :
                ss = s.strip()[1:-1].replace('\\','')
                if not ss: dfld = sqla.func.ifnull(dfld,'')
                q = dfld.__eq__(ss)
            if q is None :
                q = dfld.like(s,escape='\\')
        return q

    def _and_ (self,*qlst) :
        if qlst :
            _q = []
            for q in qlst :
                if q is None : continue
                if q is False : return False
                _q.append(q)
            if _q :
                return sqla.and_ (*_q)
        return None

    def _or_ (self,*qlst) :
        if qlst :
            _q = []
            for q in qlst :
                if q is None or q is False : continue
                _q.append(q)
            if _q :
                return sqla.or_ (*_q)
        return None

    def _where (self,fld,s,**kwargs) :
        if fld is None :
            fld = kwargs['qscols'] = self.qsearchCols (**kwargs)
            if s.startswith('@') :
                q = self._pivotcmds(self.split_pagetag(s),**kwargs)
                if q is not None : return q

        if isinstance(fld,basestring) :
            try : fld = self.json_loads(fld)
            except :
                if ',' in fld : fld = fld.split(',')
                else : fld = getattr(kwargs.get('_odb') or self.odb,fld)

        if isinstance(fld,dict) :
            qs = []
            for f,v in fld.iteritems() :
                q = self._where (f,v,**kwargs)
                if q is not None : qs.append(q)
            if s :
                q = self._where (fld.keys(),s,**kwargs)
                if q is not None : qs.append(q)
            return self._and_(qs)

        if isinstance(fld,(list,tuple)) :
            # multiple fields search (quick search)
            qs = []
            for f in fld :
                q = self._where (f,s,**kwargs)
                if q is not None :  qs.append (q)
            if qs :
                not_ = self.like_str(s)[0] if isinstance(s,basestring) else False
                return  self._and_(*qs) if not_ else self._or_(*qs)
            return None

        if isinstance(s,basestring) :
            # note s must be utf-8
            s = self.utf8_bytefix(s)
            # translate $now
            s = self.now_var(s)
            subqry = re.split(self.getcfg('regex','re_subqry'),s)
            if len(subqry) > 1 and subqry[1] != s :
                s = ''
                for i in range(0,len(subqry)-1,2) :
                    s += subqry[i] if subqry[i].strip() else ('and' if i>0 else '')
                    s += ' $qry' + str(i+1) + ' '
                s = (s+subqry[-1]).strip()
            else :
                subqry = re.split(self.getcfg('regex','re_extractqry'),s)
                if len(subqry)>1 :
                    if subqry[0].strip() : # "not" qry
                        return self._where(fld,subqry[1],_not_=True,**kwargs)
                        #if q is not None :
                        #    q = None if q is False else sqla.or_(sqla.not_(q),fld==None)
                        #return q
            if self._is_blockqry(s)==1 :
                s = s.strip()
                _s = s[1:-1]
                qlst = re.split(self.getcfg('regex','re_and_or'),_s)
                if len(qlst) > 1 and qlst[1].strip() != s :
                    s = _s
            elif  self._is_quoteqry(s)==1 :
                qlst =  [s]
            else :
                qlst = re.split(self.getcfg('regex','re_and_or'),s)
            if len(qlst) > 1 and qlst[1].strip() != s.strip() :
                # multiple searchs for single/multiple fields
                for i in range(0,len(qlst),2) : # each search
                    s = qlst[i]
                    sqv = re.split(self.getcfg('regex','re_subqryvar'),s)
                    if len(sqv)>1 :
                        for vi in range(len(sqv)) :
                            s =sqv[vi]
                            if (vi % 2) : s = subqry[int(s)]
                            sqv[vi] = None if not s else self._where (fld,s,**kwargs)
                        qlst[i] = self._and_(*sqv)
                    else :
                        qlst[i] = self._where(fld,s,**kwargs) # call single/multiple fields with single search
                q = qlst[0]
                for i in range(1,len(qlst),2) :
                    try : q2 = qlst[i+1]
                    except: continue
                    qx = qlst[i].strip()
                    if qx=='&&' or qx.lower() in self.getcfg('regex','andwords') :
                        q = self._and_ (q,q2)
                    if qx=='||' or qx.lower() in self.getcfg('regex','orwords') :
                        q = self._or_ (q,q2)
                return q

        # single field search
        q = None
        if s : #and self.colPermission(fld,kwargs.get('user_role'),'gave') :
            if isinstance(s,basestring) :
                not_,s = self.like_str(s)
                q = self._range_where(fld,s,kwargs.get('chktype'))
                if q is None :
                    q = self._like_where (fld,s)
            elif isinstance(s,(list,tuple)) :
                not_ = False
                q = fld.in_(s)
            if q is not None :
                if kwargs.get('_not_') : not_ = not not_
                if not_:
                    q = None if q is False else sqla.or_(sqla.not_(q),sqla.func.nullif(fld,'')==None)
        else :
            if isinstance(s,basestring):
                q = (sqla.func.nullif(fld,'')==None)
        return q

    def expand_pivotcmds_alias (self,pivots,_aliases=None,_recur=None) :
        if _recur is None : _recur = []
        if _aliases is None :
            _aliases = self.getcfg('aliases','pivotcmd_alias',{})
        cmds = []
        for c in pivots :
            if not c : continue
            if c in _aliases :
                if c not in _recur :
                    _recur.append(c)
                    cmds += self.expand_pivotcmds_alias(self.split_pagetag(_aliases[c]),_aliases,_recur)
            else :
                cmds.append(c)

        return cmds

    def _pivot_where (self,cmd,**kwargs) :
        try : cmd = self.json_loads (cmd)
        except : pass

        if isinstance(cmd,dict) :
            qlst = []
            for f,v in cmd.iteritems() :
                q = self._pivot_where (f+'-'+v,qscols)
            return self._and_(*qlst)

        if isinstance(cmd,(list,tuple)) :
            qlst = []
            op_ = 'or'
            def _pack_qlst_ () :
                if len(qlst) >= 1 :
                    fn = sqla.and_ if op_ in ('and','nand') else sqla.or_
                    q = sqla.not_(fn(*qlst)) if op_ in ('nand','nor') else fn(*qlst)
                    qlst = [q]
            for c in cmd :
                if c in ['or','and','nor','nand'] :
                    _pack_qlst_ ()
                    op_ = c
                    continue
                q = self._pivot_where (c,qscols)
                if q is not None :
                    qlst.append(q)
            _pack_qlst ()
            return qlst[0] if qlst else None

        if isinstance(cmd,basestring) :
            f,v = cmd.split('-',1) if '-' in cmd else (cmd,'?')
            kwargs['chktype'] =not f
            return self._where (f,v,**kwargs)
        return None

    def _pivotcmds (self,cmds,**kwargs) :
        ''' pivot filter cmds @f-[fldname][-[filter] ]
            - filter for not empty field : @f-fldname
            - filter a field : @f-fldname-filter
            - filter some fields : @f-fldname,fldname,...-filter
            - filter any field : @f--filter
            - filter "and" using key,value pair : {"fldname" : "filter","fldname" : "filter",...}
            - filter with "or" expression : @f-["fldname-filter","fldname-filter",...]
            - filter with any operand ("or","and","nor","nand") expression :
                @f-["operand","fldname-filter","fldname-filter",...]
            - mixed in :
                @f-["or",{"fldname" : "filter",...},["nor","fldname-filter",...]]
        '''
        qlst = []
        cmds = self.expand_pivotcmds_alias(cmds)
        while cmds :
            c = cmds.pop()
            if c.startswith ("@f-") :
                c = c[len('@f-'):]
                if not c : continue
                q = self._pivot_where (c,**kwargs)
                if q is not None : qlst.append(q)
        return self._and_(*qlst)

    def _filters (self,filters,**kwargs) :
        '''
        jqGrid json filters
        avialable groupOp : ['AND','OR']
        rules.op = ['eq','ne','lt','le','gt','ge','bw','bn','in','ni','ew','en','cn','nc']
        _search = true
        filters {
            "groupOp":"AND",
            "rules":[
                {"field":"IsOnline","op":"eq","data":"True"},
                {"field":"Name","op":"cn","data":"asdasd"}
               ]
            }
        '''
        if filters :
            qrylst = []
            for r in filters['rules'] :
                data = r['data']
                op = r['op']
                if op=='eq' : data ='\'' + data +'\''
                elif op=='ne' : data ='!\'' + data + '\''
                elif op=='lt' : data ='<' + data
                elif op=='le' : data ='<=' + data
                elif op=='gt' : data ='>' + data
                elif op=='ge' : data ='>=' + data
                elif op=='bw' : data += '*' # begin with
                elif op=='bn' : data = '!' + data + '*' # not begin with
                elif op=='ew' : data = '*' + data # end with
                elif op=='en' : data = '!*' + data # not end with
                elif op=='in' : data = '[' + data + ']' # in
                elif op=='ni' : data = '![' + data + ']' # not in
                elif op=='nc' : data = '!' + data # not contain

                q = self._where (r['field'],data,**kwargs)
                if q is not None : qrylst.append(q)
            return self._or_(*qrylst) if filters['groupOp'] == 'OR' else self._and_(*qrylst)
        return None

    def taxonomy_base (self,field,_encoding='utf8',**kwargs) :
        _start = 0
        try : _start = int(kwargs.get('_start'))
        except : pass
        _limit = None
        try : _limit = int(kwargs.get('_limit'))
        except : pass
        if _limit is None :
            _limit = self.getcfg('server','taxonomy_limit',50)

        if not isinstance (field,basestring): field = field.key
        media_field = self.modeler._options_.get('media_field',{})
        if field in media_field :
            globarg = ''
            globfnmatch = media_field[field]
            if isinstance(globfnmatch,(list,tuple)):
                if len(globarg)>1 : globarg = globfnmatch[1]
                globfnmatch = globfnmatch[0] if len(globfnmatch)>0 else ''
            globarg = globarg or '{1}'

            codes = []
            climit = _start + abs(_limit)
            args = dict(kwargs)
            args['_start'] = 0
            args['_limit'] = climit
            margs = {}
            for k in ['fnmatch','sord','user_role'] :
                if k in args : margs[k] = args[k]
            if globfnmatch and 'fnmatch' not in margs:
                margs['fnmatch'] = globfnmatch
            nlimit = 0
            while True :
                clist = self.taxonomy('code',_encoding,**args)
                if not clist : break
                for c in clist:
                    # check existance of file
                    wildc = globarg.replace('{1}',c)
                    files = self.mediaglob(wildc,_encoding,**margs)
                    if files : codes.append(';'.join(files)+'||'+c)
                    if len(codes)>=climit : break
                if len(codes)>=climit : break
                # fetch more block of taxonomy
                args['_start'] += args['_limit']
                args['_limit'] = abs(_limit)
                if len(codes)*2 < abs(_limit) :
                    if nlimit < 10 : nlimit += 1
                    args['_limit'] = abs(_limit)*nlimit

            if _start : codes = codes[_start:]
            return codes

        tagging = (field==self.modeler._options_.get('tagging_control',None))
        version = self.modeler._options_.get('version_control',None)
        qryversion = None
        history = version and version in kwargs
        if version and not history :
            qryversion = sqla.not_(getattr(self.odb,version).like('%'+self.version_taglike))
        taxflds = kwargs.get('autocomplete_mixin')
        if taxflds :
            if isinstance(taxflds,basestring) : taxflds = taxflds.split(',')
            if not isinstance(taxflds,(list,tuple)) :
                taxflds = self.modeler._options_.get('autocomplete_mixin',{}).get(field)
                if isinstance(taxflds,basestring) : taxflds = taxflds.split(',')
        if not isinstance(taxflds,(list,tuple)) : taxflds = [field]

        taxonomies = None
        if kwargs.get('autocomplete_mixin'):
            # mixed in predefined taxonomies
            taxonomies = self.getcfg('taxonomies',field,{})
        # -------------------
        ret = []
        term = kwargs.get('term','')
        if tagging : # modify tagging term
            term = term.split(',')[-1].strip()
        not_,term = self.like_str(term)
        tlen = 0
        tt = '%'
        if not not_ and term : # partial term lookup
            tt *= term.count('%')
            if ((len(tt) > 1) and (tt in term)) or tt == term:
                tlen = len(term) or 1

        session = self.Session()
        kwargs['_cols'] = self.ajaxCols (**kwargs)
        kwargs['qscols'] = self.qsearchCols (**kwargs)
        cfield = field
        queries = []

        for field in taxflds:
            pivots = self.split_pagetag(field)
            nofilter = '@@' in pivots
            fname = pivots.pop(0) or cfield

            if not self.colPermission (fname,kwargs.get('user_role'),access='gvae') : # allow taxonomy
                continue

            def subqry(_vc=False) :
                qlst = []
                _odb = self.odb if not _vc else self.vc_odb
                _fld = getattr (_odb,fname)
                qlst.append(sqla.func.nullif(_fld,'')!= None)
                if not _vc and version and not history :
                    q = sqla.not_(getattr(_odb,version).like('%'+self.version_taglike))
                    qlst.append(q)
                if kwargs.get('hide_untaxable',True) :
                    qlst.append(sqla.not_(self._where(_fld,'/@/@',_odb=_odb)))
                if pivots :
                    q = self._pivotcmds(pivots,qscols=[cfield],_odb=_odb)
                    if q is not None : qlst.append(q)

                if not nofilter :
                    qsearch = self.utf8_bytefix(kwargs.get('qsearch',''))
                    if qsearch :
                        q = self._where (None,qsearch,chktype=True,_odb=_odb,**kwargs)
                        if q is not None : qlst.append(q)

                    pivotcmds = kwargs.get('pivotcmds')
                    if pivotcmds :
                        pivotcmds = self.json_loads(pivotcmds,True)
                        q = self._pivotcmds (pivotcmds,_odb=_odb,**kwargs)
                        if q is not None : qlst.append(q)

                    filters = kwargs.get('filters')
                    if filters :
                        try :
                            filters = self.json_loads(filters)
                            q = self._filters (filters,_odb=_odb)
                            if q is not None : qlst.append(q)
                        except : pass

                    for k in kwargs :
                        scope = getattr(_odb,k,None)
                        if hasattr(scope,'__eq__') :
                            v = kwargs.get(k,'')
                            if not v : scope = sqla.func.ifnull(scope,'')
                            q = scope.__eq__(self.unicode_bytefix(v))
                            if k == version :
                                qlst.append(sqla.or_(q,scope.like(v+self.version_taglike)))
                            else :
                                qlst.append(q)
                qry = None
                taxfld = self._sqlformatfld(_fld)
                termfld = self._sqlformatfld(_fld)
                descriptor = kwargs.get('autocomplete_descriptor')
                if descriptor :
                    if isinstance(descriptor,basestring) : descriptor = descriptor.split(',')
                    if not isinstance(descriptor,(list,tuple)) :
                        descriptor = self.modeler._options_.get('autocomplete_descriptor',{}).get(_fld.key)
                    if descriptor :
                        if isinstance(descriptor,basestring) : descriptor = descriptor.split(',')
                        taxfld = taxfld + '||'
                        sep = ''
                        for tag in descriptor :
                            tagfld = getattr(_odb,tag,tag)
                            if not isinstance(tagfld,basestring) :
                                tagfld = self._sqlformatfld(tagfld,True)
                            taxfld += sep+tagfld
                            sep = ', '

                if tlen : # partial term lookup
                    taxfld = sqla.func.substr(taxfld,0,tlen)
                    #qry = session.query(taxfld.distinct())
                    if len(tt) != len(term) :
                        qlst.append (termfld.like(term.replace(tt,'%'),escape='\\'))
                if tlen==0 and term:
                    #qry = session.query(field.distinct())
                    t = kwargs.get('term','')
                    if tagging : # modify tagging term
                        t = t.split(',')[-1].strip()
                    q = self._where(termfld,t,_odb=_odb)
                    if q is not None : qlst.append(q)

                q = self._and_(*qlst)
                if q is not False :
                    if history :
                        queries.append(session.query(taxfld.distinct().label('taxonomy'),getattr(_odb,version).label(version)).filter(q))
                    else :
                        queries.append(session.query(taxfld.distinct().label('taxonomy')).filter(q))
            # --- end def subqry ---
            subqry()
            if history and self.modeler._options_.get('version_table') :
                subqry(True)
        if not queries:
            return [] if _limit else [0]
        qry = session.query(sqla.union(*queries)) if len(queries)>1 else queries[0]
        if _limit==0 : return [qry.count()]
        ord = 'taxonomy'
        if history :
            qry = qry.group_by('taxonomy')
            ord = version
        if _limit<0 : ord += ' desc'
        qry = qry.order_by(ord).limit(abs(_limit)).offset(_start)
        rows = qry.all() if hasattr(qry,'all') else qry.execute()
        for val in rows :
            val = val[0]
            if isinstance(val,basestring) and _encoding : val = val.encode(_encoding)
            if tlen : val += '*'
            ret.append(val)
        if len(queries)>1 : # extract mixin
            rows = queries[0].order_by(ord).limit(abs(_limit)).offset(_start).all()
            xret = []
            for val in rows:
                val= val[0]
                if isinstance(val,basestring) and _encoding : val = val.encode(_encoding)
                if tlen : val += '*'
                if val in ret :
                    xret.append(val)
                    try: ret.remove(val)
                    except: pass
            if len(ret):
                xret.append('||---')
                xret.extend(ret)
            ret = xret
        # check mix_in
        if len(ret) < abs(_limit) and taxonomies:
            re_s = True
            if term :
                rterm = term
                if tlen : rterm = rterm.replace(tt,'%')
                rterm = re.escape(rterm)
                rterm = rterm.replace('\\\\\\','$$$')
                rterm = rterm.replace('\\%','.*').replace('\\_','.')
                rterm = rterm.replace('$$$','\\')
                try :
                    re_s = re.compile(rterm,re.I)
                except : re_s = None
            if re_s :
                xret = []
                for val in taxonomies :
                    val = self.unicode_bytefix(val)
                    found = True
                    if term :
                        found = re_s.search(val)
                    if not_ : found = not found
                    if not found : continue
                    if tlen : val = val[:tlen] + '*'
                    if _encoding : val = val.encode(_encoding)
                    if val not in ret and val not in xret:
                        xret.append(val)
                        reord = True
                        if (len(ret)+len(xret)) >= abs(_limit) : break
                if xret :
                    xret.sort()
                    if _limit < 0 : xret.reverse()
                    ret.append('||---')
                    ret.extend(xret)
        if tagging :
            tags = []
            xret = []
            ret.append(None)
            for val in ret :
                if val=='||---' or val is None :
                    if xret :
                        xret.sort()
                        if _limit<0 : xret.reverse()
                    tags.extend(xret)
                    if val : tags.append(val)
                    xret = []
                    continue
                for t in val.split(',') :
                    t = t.strip()
                    if not t : continue
                    if t not in tags and t not in xret : xret.append(t)
            return tags
        return ret

    def taxonomy (self,field,_encoding='utf8',**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'taxonomy',None)
        if wrapper : return wrapper(self,field,_encoding,**kwargs)
        return self.taxonomy_base(field,_encoding,**kwargs)

    def next_runno (self,val) :
        segs = re.split(self.getcfg('regex','re_maxonomy'),val)
        if not segs or segs[-1] != '' : return False
        for i in xrange(len(segs)-2,0,-2) :
            num = int(segs[i])
            newnum = "%0*d" % (len(segs[i]),num+1)
            if len(segs[i]) == len(newnum) :
                segs[i] = newnum
                break
            else :
                segs[i] = "%0*d" % (len(segs[i]),1)
        return "".join(segs)

    def maxonomy_base (self,field,_encoding='utf8',**kwargs) :
        session = self.Session()
        term = self.utf8_bytefix(kwargs.get('term',''))

        ret = []
        if isinstance (field,basestring) :
            field = getattr (self.odb,field)
        t = field.property.columns[0].type
        if not isinstance(t,sqla.String) :
           return []

        if not self.colPermission (field.key,kwargs.get('user_role'),access='ae') : # allow maxonomy
            return []

        fgrp = field
        for i in xrange(10) :
            fgrp = sqla.func.replace(fgrp,str(i),' ')
        mlength = sqla.func.length(sqla.func.rtrim(fgrp))
        grp = sqla.func.substr(field,0,sqla.func.max(2,mlength)).label('maxonomy')
        gqry = session.query(grp).distinct()

        #qry = session.query(sqla.func.max(field))
        qlst = [mlength != sqla.func.length(field) ]
        version = self.modeler._options_.get('version_control',None)
        if version :
            qlst.append(sqla.not_(getattr(self.odb,version).like('%'+self.version_taglike)))

        isnum = '([0-9]{'+str(self.modeler._options_.get('maxonomy_suppressnumsize',2))+',})'
        re_isnum = re.compile(isnum)
        nterm = re.sub(re_isnum,'*',term)
        if nterm and nterm!='?' :
            qlst.append(self._where(field,nterm+('*' if nterm[-1]!='*' else '')))
        for k in kwargs :
            if hasattr(getattr(self.odb,k,None),'__eq__') :
                qlst.append(getattr(self.odb,k).__eq__(self.unicode_bytefix(kwargs[k])))
        q = self._and_(*qlst)
        if q is False : return []
        if q is not None : gqry = gqry.filter(q)
        gqry = gqry.group_by('maxonomy')

        #qry = session.query(sqla.func.max(field))
        gresults = []
        for gval, in gqry.all() :
            nonumval = re.sub(re_isnum,'',gval)
            for i in range(len(gresults)):
                nnv = re.sub(re_isnum,'',gresults[i])
                if nnv==nonumval :
                    nonumval = re.split(re_isnum,gval)
                    nnv = re.split(re_isnum,gresults[i])
                    for ii in range(1,len(nonumval)-1,2):
                        if ii > len(nnv) or int(nonumval[ii])>int(nnv[ii]):
                            gresults[i] = gval
                            break
                        if int(nonumval[ii])<int(nnv[ii]) : break
                    gval = None
                    break
            if gval: gresults.append(gval)
        newrunno =  self.modeler._options_.get('maxonomy_format',{}).get(field.key,'-0000')
        newrunpre = re.sub('[0-9]+$','',newrunno)
        newrunno = datetime.datetime.now().strftime(newrunno)
        newrunpre = datetime.datetime.now().strftime(newrunpre)
        re_newrun = re.compile('^([^0-9]*)'+re.sub('[0-9]+','[0-9]+',re.escape(newrunpre))+'$') #+'[0-9]+$')
        nret = []
        for gval in gresults :
            nrun = re.split(re_newrun,gval)
            if len(nrun)<=1 : continue
            prefix = nrun[1]
            nrun = prefix + newrunpre
            if nrun not in nret :
                nret.append(prefix+newrunpre)
        if nret :
            nret.append(None)
            #gresults[0:0] = nret
        for gval in gresults :
            if gval not in nret : nret.append(gval)
        if nret and nret[-1] is None : del nret[-1]
        if not nret and len(term)>0 :
            xterm = re.sub('[0-9]+$','',term)
            nrun = re.split(re_newrun,xterm)
            if len(nrun) <=1 :
                nret.append(xterm+newrunpre)
            else:
                nret.append(nrun[1]+newrunpre)

        for gval in nret :
            if gval is None :
                ret.append('||---')
                continue
            for val, in  session.query(sqla.func.max(field)).filter(field.like(gval+'%')).all() :
                if not val: val = gval + newrunno.replace(newrunpre,'')
                if _encoding : val = val.encode(_encoding)
                segs = re.split(self.getcfg('regex','re_maxonomy'),val)
                if not segs or segs[-1] != '' : continue
                for i in xrange(len(segs)-2,0,-2) :
                    num = int(segs[i])
                    newnum = "%0*d" % (len(segs[i]),num+1)
                    if len(segs[i]) == len(newnum) :
                        segs[i] = newnum
                        break
                    else :
                        segs[i] = "%0*d" % (len(segs[i]),1)
                val = "".join(segs)
                ret.append(val)

        if not ret and len(term)>0 :
            if term[-1]=='*' : term = term[:-1]
            xterm = re.sub('[0-9]+$','',term)
            nrun = re.split(re_newrun,xterm)
            if len(nrun)<=1 :
                ret.append(xterm+newrunno)
            else :
                ret.append(nrun[1]+newrunno)
            #if xterm != term :
            #    ret.append(xterm+datetime.datetime.now().strftime(newrunno))
        return ret

    def maxonomy (self,field,_encoding='utf8',**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'maxonomy',None)
        if wrapper : return wrapper(self,field,_encoding,**kwargs)
        return self.maxonomy_base(field,_encoding,**kwargs)

    def autocomplete_base (self,field,_encoding='utf8',**kwargs) :
        cm = self.colModel(field)
        if not cm or cm.get('unique') :
            return self.maxonomy(field,_encoding,**kwargs)
        kwargs['autocomplete_mixin'] = kwargs.get('autocomplete_mixin',True)
        kwargs['autocomplete_descriptor'] = kwargs.get('autocomplete_descriptor',True)
        ret = self.taxonomy(field,_encoding,**kwargs)
        return ret

    def autocomplete (self,field,_encoding='utf8',**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'autocomplete',None)
        if wrapper : return wrapper(self,field,_encoding,**kwargs)
        return self.autocomplete_base(field,_encoding,**kwargs)

    def mediaglob_base (self,pattern,_encoding='utf8',**kwargs) :
        if ',' in pattern : pattern = pattern.split(',')
        if isinstance(pattern,(list,tuple)) :
            jsobj = {}
            for ptn in pattern :
                if not ptn : continue
                ret = self.mediaglob_base(ptn,_encoding,**kwargs)
                if ret : jsobj[ptn] = ret
            return jsobj
        filters = self.json_loads(kwargs.get('fnmatch','[]'),True)
        wild = ''
        if '*' not in pattern:   # may be code pattern
            wild = '*'
        mdir = self.getcfg('server','media_root','') or self.modeler._options_.get('media_root')
        files = []
        dirs = []
        if mdir:
            if mdir[-1] not in '/\\' : mdir += '/'
            dirs.append(mdir)
            if wild : dirs.append(mdir+wild+'/')
        role = kwargs.get('user_role')
        while (dirs) :
            mdir = dirs.pop(0)
            if not mdir: continue
            ptn = mdir+pattern+wild
            if wild : mdir = mdir.replace(wild+'/','')
            for n in glob.glob(ptn):
                n = n.replace('\\','/')
                if os.path.isdir(n):
                    if wild: dirs.push(n+'/')
                    continue
                n = n.replace(mdir,'')
                #print role,n,filters
                if not self.mediaPermission(n,role) :
                    continue
                if filters :
                    m = None
                    for f in filters :
                        if f :
                            m = False
                            if fnmatch.fnmatch(n,f):
                                m = True
                                break
                    if m is False : continue
                n = self.unicode_bytefix(n)
                if _encoding : n = n.encode(_encoding)
                #print n
                files.append(n)

        sord = kwargs.get('sord','')
        if sord :
            files.sort()
            if sord=='desc': files.reverse()
        if 'rows' in kwargs :
            limit =  int(kwargs.get('rows',0))
            page = int(kwargs.get('page',1))

            count = len(files)
            if limit==0 : limit = 1
            if limit<0 : limit = count
            if page<=0 : page = 1
            total_pages = 0
            if count > 0 :
                total_pages = int(count/limit)
                if count > total_pages*limit : total_pages += 1
            if page > total_pages : page = total_pages
            offset = (page * limit) - limit
            if offset : files = files[offset:offset+limit]
            return {
                'total' : count,
                'page' : page,
                'records' : len(files),
                'rows' : files,
                }
        return files

    def mediaglob(self,pattern,_encoding='utf8',**kwargs):
        wrapper = getattr(self.modeler._wrapper_,'mediaglob',None)
        if wrapper : return wrapper(self,pattern,_encoding,**kwargs)
        return self.mediaglob_base(pattern,_encoding,**kwargs)

    def jqgrid_grid_generator (self,outtype='json',_encoding='',**kwargs) :
        if not self.colPermission ('__table__',kwargs.get('user_role'),'g'):
            return
        self.sqlite_custom_function()

        session = self.Session()

        page = int(kwargs.get('page',1))
        limit =  int(kwargs.get('rows',1))
        sidx = kwargs.get('sidx','')
        sord = kwargs.get('sord','')
        npage = int(kwargs.get('npage',1))

        kwargs['_cols'] =  self.ajaxCols(**kwargs)
        kwargs['qscols'] = self.qsearchCols (**kwargs)
        qrycount = kwargs.get('_count','').lower() not in ['false','0','']
        if outtype=='csv' and not qrycount :
            hdr = []
            for c in kwargs['_cols'] :
                n = c.split(':',1)[0]
                hdr.append(n)
            yield hdr

        filters = {}
        if kwargs.get('_search','').lower() not in ['false','0',''] :
            try:
                filters = self.json_loads(kwargs.get('filters','{}'))
            except: pass
        if 'filters' in kwargs : del kwargs['filters']

        version = self.modeler._options_.get('version_control')
        history = version and kwargs.get('_history') and self.historyPermission(kwargs.get('user_role'),'g')

        _summary = kwargs.get('_summary',None)
        if str(_summary).lower() in ('false','none','null','0') : _summary = None
        if _summary is not None :
            sfmts = {}
            sfmts.update(self.getcfg('summaries','__',{}))
            if _summary :
                sfmts.update(self.getcfg('summaries','_'+_summary+'_',{}))

        pivotcmds = self.json_loads(kwargs.get('pivotcmds','[]'),True)
        if 'pivotcmds' in kwargs : del kwargs['pivotcmds']

        qsearch = self.utf8_bytefix(kwargs.get('qsearch',''))

        concurrent = self.modeler._options_.get('concurrent_control')

        media_field = self.modeler._options_.get('media_field',{})
        _mflds = {}
        queries = []
        cqueries = []
        def subqry (_vc=False):
            _odb = self.odb if not _vc else self.vc_odb
            qrylst = []
            if pivotcmds :
                q = self._pivotcmds (pivotcmds,_odb=_odb,**kwargs)
                if q is not None : qrylst.append(q)
            if qsearch :
                q = self._where (None,qsearch,chktype=True,_odb=_odb,**kwargs)
                if q is not None : qrylst.append(q)
            if filters :
                q = self._filters (filters,_odb=_odb,**kwargs)
                if q is not None :
                    qrylst.append(q)

            if not _vc and version and not history:
                qrylst.append(sqla.not_(getattr(_odb,version).like('%'+self.version_taglike)))
            q = self._and_(*qrylst)
            if q is False :
                if outtype!='csv' :
                    return [0] if qrycount else {'page':0,'total':0,'records':0,'rows':[]}
                return None

            # select cols
            _mfldno = 0
            _flds = []
            sfmt = None
            #gfld = None
            glbl = None
            for c in kwargs['_cols'] :
                n = c.split(':',1)[0]
                nlbl = n
                ismedia = n in media_field
                if ismedia:
                    if not _vc :
                        if n not in _mflds : _mflds[n] = [_mfldno]
                        else : _mflds[n].append(_mfldno)
                    n = 'code'

                f = getattr(_odb,n,None)
                _mfldno += 1
                if f is not None and _summary is not None:
                    t = f.property.columns[0].type
                    if sidx != n:
                        if isinstance(t,(sqla.Float,sqla.Integer)) :
                            f = sqla.func.sum(f)
                        else :
                            f = sqla.func.count(f)
                    else :
                        sfmt = sfmts.get(f.key)
                        if isinstance(t,sqla.Date) :
                            sfmt = sfmt or sfmts.get('@date')
                            if sfmt : f = sqla.func.strftime(sfmt,f)
                        elif isinstance(t,sqla.DateTime) :
                            sfmt = sfmt or sfmts.get('@datetime',sfmts.get('@date'))
                            if sfmt : f = sqla.func.strftime(sfmt,f)
                        elif isinstance(t,(sqla.Float,sqla.Integer)) :
                            try :
                                k = '@integer' if isinstance(t,(sqla.Integer)) else '@float'
                                sfmt = float(sfmt or sfmts.get(k,sfmts.get('@number')))
                            except : sfmt = None
                            if sfmt :
                                f = (sqla.func.floor(f / sfmt) * sfmt)
                                f = (''+f+'*')
                        elif isinstance(t,(sqla.String)) :
                            sfmt = sfmt or sfmts.get('@string')
                            if sfmt :
                                if not hasattr(sfmt,'__iter__') : sfmt = list(sfmt)
                                for c in sfmt :
                                    if isinstance(c,basestring) :
                                        f = sqla.case([(sqla.func.charindex(c,f)==0,f)],else_=sqla.func.substr(f,0,sqla.func.charindex(c,f)-1))
                                    if isinstance(c,int) :
                                        f = sqla.func.substr(f,0,c)
                        #gfld = f
                        glbl = nlbl
                    # --- end if _summary
                if f is not None and self.colPermission (n,kwargs.get('user_role'),'gvae') :
                    _flds.append(f.label(nlbl)) #('' + sqla.func.count(1) + ': '+ f)
                else :
                    _flds.append(sqla.null().label(nlbl))
            if concurrent :
                _flds.append(_odb.last_updated.label('last_updated'))
            _flds.append(_odb.id.label('id'))

            cqry = session.query(_odb.id.label('id'))
            qry = session.query(*_flds)

            if q is not None :
                cqry = cqry.filter(q)
                qry = qry.filter(q)

            if glbl is not None :
                cqry = cqry.group_by(glbl)
                qry = qry.group_by(glbl)
            cqueries.append(cqry)
            queries.append(qry)
            return None
        # --- end def subqry
        result = subqry(False)
        if result:
            yield result
            return
        if history and self.modeler._options_.get('version_table'):
            result = subqry(True)
            if result:
                yield result
                return
        if not queries :
            return
        cqry = session.query(sqla.union(*cqueries)) if len(cqueries)>1 else cqueries[0]
        qry = session.query(sqla.union(*queries)) if len(queries)>1 else queries[0]
##        count = 0
##        for cqry in cqueries :
##            count += cqry.count()
##            print 'count=',count
        count = cqry.count()
        #ret['iTotalDisplayRecords'] = qry.count()
        if qrycount :
            yield [count] if outtype!='csv' else count
            return
        # sorting
        if sidx :
            ord = sidx #getattr(self.odb,sidx)
            if sord :
                ord = sidx + ' ' + sord.lower() #getattr(ord,sord.lower())()
            qry = qry.order_by(ord)

        # limit
        if limit==0 : limit = 1
        if limit<0 : limit = count
        if page<=0 : page = 1
        total_pages = 0
        if count > 0 :
            total_pages = int(count/limit)
            if count > total_pages*limit : total_pages += 1
        if page > total_pages : page = total_pages

        offset = (page * limit) - limit

        ret= {
            'page' : page,
            'total' : total_pages,
            'records' : count,
            'rows' : []
            }
        if outtype!='csv' : yield ret

        r = 0
        for d in qry[offset:(limit*npage)+offset] :
            r += 1
            id = d[-1]
            d = list(d[:-1])
            if concurrent :
                id = str(id) + ':'+ self.concurrent_str(d[-1])
                d = d[:-1]
            # media extension
            for m in _mflds :
                globarg = ''
                globfnmatch = media_field[m]
                if isinstance(globfnmatch,(list,tuple)):
                    if len(globarg)>1 : globarg = globfnmatch[1]
                    globfnmatch = globfnmatch[0] if len(globfnmatch)>0 else ''
                globarg = globarg or '{1}'
                wildc = globarg.replace('{1}',d[_mflds[m][0]])
                files = self.mediaglob(wildc,fnmatach=globfnmatch,user_role=kwargs.get('user_role'))
                v = None if not files else ';'.join(files)
                for i in _mflds[m]: d[i] = v

            for i in xrange(len(d)) : # correct datetime and multiline presenting data
                if isinstance(d[i],basestring) :
                    if _encoding and outtype=='csv': d[i] = d[i].encode(_encoding)
                if isinstance(d[i],datetime.datetime) : d[i] = d[i].strftime(self.datetimeformat)
                if isinstance(d[i],datetime.date) : d[i] = d[i].strftime(self.dateformat)
                if d[i] is None and outtype=='csv' : d[i] = ''
                if isinstance(d[i],(int,float)) and outtype=='csv': d[i] = str(d[i])

            yield {'id':id,'cell':d} if outtype!='csv' else d
            # ret['rows'].append({'id':id,'cell':d})
        #return ret

    def jqgrid_grid_base (self,**kwargs) :
        ret = None
        for r in self.jqgrid_grid_generator ('jqgrid',**kwargs) :
            if ret is None : ret = r ; continue
            if 'rows'in ret : ret['rows'].append(r)
        return ret

    def jqgrid_grid (self,**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'jqgrid_grid',None)
        if wrapper : return wrapper(self,**kwargs)
        return self.jqgrid_grid_base(**kwargs)

    def reform_tags(self,tags) :
        tt = []
        for t in tags.split(',') :
            t = t.strip()
            if not t : continue
            if t not in tt : tt.append(t)
        tt.sort()
        return ','.join(tt)

    def update_field(self,rec,k,val,user_role='',permcode='') :
        if hasattr(rec,k) :
            v = self.unicode_bytefix(val.rstrip())
            if not v : v = None
            t = getattr(self.odb,k).property.columns[0].type

            if v and isinstance(t,sqla.DateTime) :
                try : v = datetime.datetime.strptime(v,self.datetimeformat)
                except Exception as e :
                    raise e
            elif v and isinstance(t,sqla.Date) :
                try : v = datetime.datetime.strptime(v,self.dateformat)
                except Exception as e :
                    raise e
            if k==self.modeler._options_.get('tagging_control'):
                v = self.reform_tags(v)
            ov = getattr(rec,k)
            if ov != v :
                if permcode and not self.colPermission (k,user_role,permcode) :
                    raise Exception('permission denied for '+k)
                setattr(rec,k,v)
            return True
        return False

    def concurrent_ctrl (self,rec,**kwargs) :
        id = kwargs.get('id')
        concurrent = None
        if id and ':' in id :
            concurrent = id.split(':',1)[1]
        else:
            if 'last_updated' in kwargs :
                concurrent = self.concurrent_str(kwargs['last_updated'])

        if concurrent:
            if self.concurrent_str(rec.last_updated) != concurrent :
                raise Exception('Concurrent conflict, data changed by other client')
        return concurrent

    def version_ctrl (self,rec,**kwargs) :
        vcrec = None
        version = self.modeler._options_.get('version_control')
        if version and re.search(re.escape(self.version_taglike).replace('\\%','.*'),getattr(rec,version)) :
            if not self.historyPermission(kwargs.get('user_role'),'e') :
                raise Exception('permission denied for historial data')
            version = False # disable versioning
        if version :
            vcrec = getattr(self,'vc_odb',self.odb)()
            for k in self.table.c :
                k = k.key
                if k in ['id','last_updated']: continue
                if k==version:
                    setattr(vcrec,version,getattr(rec,version)+self.version_tag(**kwargs))
                    continue
                v = getattr(rec,k)
                if v : setattr(vcrec,k,v)
        return vcrec

    def jqgrid_edit_base (self,**kwargs) :
        cmd = kwargs.get('oper')
        id = kwargs.get('id','')
        if not cmd: return [False,'unknown command.',id]
        if id=='_empty' : id = ''
        if ':' in id : id = id.split(':',1)[0]

        vcrec = None # version control
        session = self.Session()
        msg = cmd
        if not id :
            rec = self.odb()
        else :
            msg += ('(id='+id+')')
            try :
                rec = session.query(self.odb).filter(getattr(self.odb,'id')==id).one()
                self.concurrent_ctrl(rec,**kwargs)
                vcrec = self.version_ctrl(rec,**kwargs)
            except Exception as e :
                return [False,"%s %s" % (msg,e),id]

        if cmd=="del" :
            if not self.colPermission ('__table__',kwargs.get('user_role'),'d') :
                return [False,"%s permission denied." % (msg),id]
            try:
                if vcrec is not None : session.add(vcrec)
                session.delete(rec)
                session.commit()
            except Exception as e : #sqla.exc.SQLAlchemyError,exc :
                session.rollback()
                return [False,"%s %s" % (msg,e),id]
            return [True,msg,id]

        if cmd in ("add","edit") :
            permcode = 'a' if cmd=='add' else 'e'
            if not self.colPermission ('__table__',kwargs.get('user_role'),permcode) :
                return [False,"%s permission denied." % (msg),id]
            chflag = False
            for k in kwargs.iterkeys() :
                if k=='id' or k=='last_updated': continue
                try:
                    if self.update_field(rec,k,kwargs[k],kwargs.get('user_role'),permcode):
                        chflag = True
                except Exception as e :
                    return [False,"%s %s" % (msg,e),id]
            if chflag :
                try:
                    if vcrec is not None: session.add(vcrec)
                    session.add(rec)
                    session.commit()
                    id = rec.id
                except Exception as e  : #sqla.exc.SQLAlchemyError,exc :
                    session.rollback()
                    return [False,"%s %s" % (msg,e),id]
            return [True,msg,id]
        return [False,"unknown command - "+cmd + ".",id]

    def jqgrid_edit (self,**kwargs) :
        wrapper = getattr(self.modeler._wrapper_,'jqgrid_edit',None)
        if wrapper : return wrapper(self,**kwargs)
        return self.jqgrid_edit_base(**kwargs)

    def expand_subpage_alias (self,subpage,_recur=[]) :
        alias = self.getcfg('aliases','subpage_alias',{})
        subpage,pagetag = self.split_subpage(subpage)
        if subpage not in _recur and subpage in alias :
            _recur.append(subpage)
            subpage,tag  = self.expand_subpage_alias(alias[subpage],_recur)
            if tag :
                if pagetag : pagetag += '/'
                pagetag += tag
        return (subpage,pagetag)

    def expand_pageoption_alias (self,urloptions,_recur=[]) :
        alias = self.getcfg('aliases','pageoption_alias',{})
        options = []
        for o in urloptions :
            if not o : continue
            if o not in _recur and o in alias :
                _recur.append(o)
                options += self.expand_pageoption_alias(split_pagetag(alias[o]),_recur)
            else :
                options.append(o)
        return options

    def __call__ (*args,**kwargs) :
        return self.odb(*args,**kwargs)

# ----------------------------------------
def downloadable (args,ext,prefix='download',encoding='') :
    download = args.get('_dl',False)
    if download :
        if download.lower() in ['1','true'] :
            if encoding : encoding = '_'+encoding
            download = prefix+datetime.datetime.now().strftime("_%Y%m%d%H%M")+encoding+ext
        if not download.lower().endswith(ext) : download += ext
        download = os.path.basename(download)
    return download

def send_fileobj(filename, root, guessmime=True, mimetype=None, download=False):
    """ replacement for bottle's static_file
        with more support for sending string, or file object like StringIO
        special keyword for root : ':string', ':file'
        when passing other data through filename
    """
    header = dict()
    if root in (':string',':file') : fileobj = filename
    elif root==':json' :
        fileobj = bottle.json_dumps(filename)
        mimetype = 'application/json'

    if fileobj :
        filename = download if isinstance(download,basestring) else 'noname'
    else :
        root = os.path.abspath(root) + os.sep
        filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))

        if not filename.startswith(root):
            return bottle.HTTPError(403, "Access denied.")
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return bottle.HTTPError(404, "File does not exist.")
        if not os.access(filename, os.R_OK):
            return bottle.HTTPError(403, "You do not have permission to access this file.")

    if not mimetype and guessmime:
        header['Content-Type'] = bottle.mimetypes.guess_type(filename)[0]
    else:
        header['Content-Type'] = mimetype if mimetype else 'text/plain'

    if download == True:
        download = os.path.basename(filename)
    if download:
        header['Content-Disposition'] = 'attachment; filename="%s"' % download
    if fileobj:
        l = None
        if isinstance(fileobj,basestring):
            l = fileobj.__sizeof__() - type(fileobj)().__sizeof__()
        elif hasattr(fileobj,'len') :
            l = fileobj.len
        elif hasattr(fileobj,'tell') and hasattr(fileobj,'seek') :
            old = fileobj.tell()
            fileobj.seek(0,2)
            l = fileobj.tell()
            fileobj.seek(old)
        if l : header['Content-Length'] = l
    else:
        stats = os.stat(filename)
        lm = bottle.time.strftime("%a, %d %b %Y %H:%M:%S GMT", bottle.time.gmtime(stats.st_mtime))
        header['Last-Modified'] = lm
        ims = bottle.request.environ.get('HTTP_IF_MODIFIED_SINCE')
        if ims:
            ims = ims.split(";")[0].strip() # IE sends "<date>; length=146"
            ims = bottle.parse_date(ims)
            if ims is not None and ims >= int(stats.st_mtime):
                header['Date'] = bottle.time.strftime("%a, %d %b %Y %H:%M:%S GMT", bottle.time.gmtime())
                return bottle.HTTPResponse(status=304, header=header)
        header['Content-Length'] = stats.st_size

    if bottle.request.method == 'HEAD':
        return bottle.HTTPResponse('', header=header)
    if not fileobj : fileobj = open(filename, 'rb')
    return bottle.HTTPResponse(fileobj, header=header)
    #return bottle.HTTPResponse(open(filename, 'rb'), header=header)


def suburlModel (suburl,abortcode=None) :
    if suburl is None:
        return [m.suburl for m in _models]

    if getcfg('server','suburl','') == suburl : return _models[0] if _models else Model
    for m in _models :
        if suburl == m.suburl :
            return m
    if abortcode :
        bottle.abort (abortcode,"Incorrect suburl ("+suburl+").")
    return None

def getparams () :
    params = {}
    params.update (bottle.request.params)
    params.update(bottle.request.environ.get('beaker.session',{}))
    return params

@bottle.route('/')
def index () :
    redir = getcfg('server','redir_index','')
    if not redir :
        redir = getcfg('server','suburl','')
        if not redir and _models :
            redir =  _models[0].suburl
        if not redir :
            return bottle.template('index')
        redir = '/' + redir
    return bottle.redirect(redir)

@bottle.route('/:suburl/resource/:filename#.*[^/]$#')
def resource(suburl,filename):
    suburlModel(suburl,404)
    return bottle.static_file(filename,root = './resource/')

@bottle.route('/:suburl/media/:filename#.*[^/]$#')
def media(suburl,filename):
    ''' public media '''
    model = suburlModel(suburl,404)
    mdir = model.getcfg('server','media_root','') or model.modeler._options_.get('media_root')
    if not mdir : bottle.abort (404,"Media root is not defined.")
    if mdir[-1] not in '/\\' : mdir += '/'
    args = getparams()
    if not model.mediaPermission(filename,args.get('user_role')) :
        bottle.abort (403,"Not allow to access media.")
    return bottle.static_file(filename,root = mdir)

@bottle.route('/:suburl/ajax/taxonomy/:field',method=['GET','POST'])
def ajax_taxonomy (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','taxonomy')
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
         abort (403,"Not allow to download data.")
    return send_fileobj(model.taxonomy (field,**args),':json',download=download)

@bottle.route('/:suburl/ajax/maxonomy/:field',method=['GET','POST'])
def ajax_maxonomy (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','maxonomy')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    return send_fileobj(model.maxonomy (field,**args),':json',download=download)

@bottle.route('/:suburl/ajax/autocomplete/:field',method=['GET','POST'])
def ajax_autocomplete (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','autocomplete')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    return send_fileobj(model.autocomplete (field,**args),':json',download=download)

@bottle.route('/:suburl/ajax/jqgrid',method=['GET','POST'])
@bottle.route('/:suburl/ajax/jqgrid/grid',method=['GET','POST'])
def ajax_jqgrid_grid (suburl) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','grid')
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")

    return send_fileobj (model.jqgrid_grid(**args),':json',download=download)

@bottle.route('/:suburl/csv/jqgrid',method=['GET','POST'])
@bottle.route('/:suburl/csv/jqgrid/grid',method=['GET','POST'])
def csv_jqgrid_grid (suburl) :
    model = suburlModel(suburl,404)

    args = getparams()
    encoding = args['_encoding'] = args.get('_encoding') or model.getcfg('server','csv_encoding','utf-8')
    download = downloadable(args,'.csv','grid',encoding)
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")

    output = StringIO.StringIO()
    re_csv_needquote = re.compile(r'([",]|^\s|\s$|[\n\r\f\v]|^-?[0-9]*(?:[.][0-9]*)?$)')
    rno = 0
    for row in model.jqgrid_grid_generator ('csv',**args):
        rno += 1
        for i in range(len(row)) :
            c = row[i]
            if rno==1 and args.get('_lang'):
                fld = model.colModel(c)
                if fld :
                    fld_o = fld.get('options')
                    lang = args.get('_lang')
                    c = model.unicode_bytefix(_m(fld_o.get('label'),args.get('_lang'),{}) or c)
                    if encoding :
                        c = c.encode(encoding)
            if isinstance(c,basestring) :
                if c and re.search(re_csv_needquote,c) :
                    c = '"'+c.replace('"','""')+'"'
            elif c is None : c = ''
            else : c = str(c)
            row[i] = c
        output.write(','.join(row)+'\r\n')
    output.seek(0)
    return send_fileobj (output,':file',mimetype='text/csv',download=download)

@bottle.route('/:suburl/ajax/jqgrid/edit',method=['GET','POST'])
def ajax_jqgrid_edit (suburl) :
    model = suburlModel(suburl,404)
    return json.dumps(model.jqgrid_edit (**getparams()))

@bottle.route('/:suburl/ajax/jqgrid/empty',method=['GET','POST'])
@bottle.route('/:suburl/ajax/jqgrid/noedit',method=['GET','POST'])
def ajax_jqgrid_nop (suburl) :
    return '[true,"",""]'

@bottle.route('/:suburl/ajax/media')
@bottle.route('/:suburl/ajax/media/:pattern#.*[^/]$#')
def ajax_media(suburl,pattern=None):
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','media')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    if not pattern: pattern = '*'
    return send_fileobj(model.mediaglob (pattern,**args),':json',download=download)

@bottle.route('/:suburl',method=['GET','POST'])
@bottle.route('/:suburl/:subpage#.*#',method=['GET','POST'])
def mainpage (suburl,subpage=None) :
    template_lookup = ['./views/'+suburl+'/','./views/__default__/','./views/']
    urltagstr = getcfg('server',"urltagstr",'') or '//'
    alturltagstr = getcfg('server',"alturltagstr",'') or '/='
    if urltagstr=='//' and getcfg('server',"server_type",'')=='paste' : urltagstr = alturltagstr

    if not subpage :
        if subpage is None: return bottle.redirect('/'+suburl+'/')
        else: subpage = 'index'
    else :
        subpage = '/'+Model.utf8_bytefix(subpage)
        if urltagstr != '//':
            subpage = subpage.replace(urltagstr,'//')
        subpage = subpage.replace(alturltagstr,'//')
        if not subpage.startswith('//') : subpage = subpage[1:]

    #if subpage.endswith('/') : subpage += 'index'
    for ext in getcfg('server','resource_ext') :
        if subpage.lower().endswith(ext):
            for spath in template_lookup :
                fname = os.path.join(spath,subpage)
                if os.path.isfile(fname):
                    return bottle.static_file(subpage,root = spath)

    if subpage and subpage[0]=='/' : subpage = '/' + subpage
    redir_url = '/'+suburl+'/'+(subpage if subpage else 'index')
    if urltagstr != '//' :
        redir_url = redir_url.replace('//',urltagstr)
    action = bottle.request.params.get('action')
    if action=='debug' :
        m = (bottle.request.params.get('mode','true').lower() in ['true','1'])
        if _cfg['server'].get('debug',False) != m :
            _cfg['server']['debug'] = m
            _restrict_cfg['server']['debug'] = m
            bottle.debug(getcfg('server',"debug",False))
        return bottle.redirect(redir_url)

    if action=='loadm':
        m = bottle.request.params.get('name')
        if m : load_model(m)
        return bottle.redirect(redir_url)
    if action=='unloadm':
        m = bottle.request.params.get('name')
        for i in range(len(_models)) :
            if _models[i].name==m :
                del _models[i]
                break
        if not suburlModel(suburl) :
            return bottle.redirect('/')
        return bottle.redirect(redir_url)

    model = suburlModel(suburl,404)

    args = {}
    if subpage.startswith('~') :
        subpage = subpage[1:]
        args['layout_loaded'] = '~'
    ss = bottle.request.environ.get('beaker.session')

    if getcfg('server','debug')  or action=='reload':
        reload_cfg()
        if isinstance(model,Model) : model.reload_cfg()
        bottle.TEMPLATES.clear()

    if action=='logout' :
        if 'logged_in' in ss : del ss['logged_in']
        if 'user_role' in ss : del ss['user_role']
        ss.save()
        return bottle.redirect(redir_url)

    if 'alert_msg' not in args : args['alert_msg'] = []
    loginparms = bottle.request.params if getcfg('server','debug') else bottle.request.forms
    if loginparms.get('action')=='login' :
        u = model.utf8_bytefix(loginparms.get('user'))
        p = model.utf8_bytefix(loginparms.get('password'))
        uinf = model.getcfg('users',u,None)
        if uinf :
            role = uinf.get('role',model.getcfg('server','default_role','viewer'))
            # find hash lev
            hash = 0
            if role :
                _prm = model.modeler._permissions_
                for r in role.split(',') :
                    _h = _prm.get(r,{}).get('__hashlev__')
                    if _h is None : _h = _prm.get('*',{}).get('__hashlev__')
                    if _h and _h > hash : hash = _h
            pwd = uinf.get('password','')
            plst = []
            if hash<0 : plst.append(p)
            elif  not hash or hash==1 or hash==-1:
                plst.append(hashlib.md5(p).hexdigest())
            elif  not hash or hash==2 or hash==-2 :
                plst.append(hashlib.md5(u+':'+p).hexdigest())
            elif  not hash or hash>=3 or hash<=-3 :
                plst.append(hashlib.md5(u+':'+p+'@'+uinf.get('role','')).hexdigest())
            if pwd in plst :
                ss.update ({'user_id': u, 'logged_in': 1, 'user_role': role})
                return bottle.redirect(redir_url)
            args['alert_msg'].append('Invalid username or incorrect password.')
        else :
            if not model.getcfg('users')  and u==p :
                ss.update( {'user_id': u, 'logged_in' : 1, 'user_role' : u} )
                ss.save()
                return bottle.redirect(redir_url)
            args['alert_msg'].append('Invalid username or incorrect password.')

    sepoption,pagetag = '',''
    urloptions,pageoptions,pivotcmds = [],[],[]
    kwoptions = {}

    if subpage and subpage[0]=='/' : subpage = '/' + subpage
    (urlsubpage,urlpagetag) = model.split_subpage(subpage)
    paramstag = bottle.request.params.get('$','')
    if paramstag: paramstag = '/'+paramstag
    if urlpagetag :
        urloptions = model.split_pagetag (urlpagetag)
    if not subpage:
        subpage = _cfg['server'].get('default_subpage','')
    subpage,pagetag = model.expand_subpage_alias(subpage)
    pagetag += paramstag
    if pagetag :
        sepoption = '/' #deprecate
        pageoptions = model.expand_pageoption_alias (model.split_pagetag (pagetag))
        for o in pageoptions :
            if o[0] == '@' :
                pivotcmds.append(o)
            if '-' in o :
                (k,v) = o.split('-',1)
                if k : kwoptions[k] = v

    args.update({
        #'urlsuburl' : suburl,
        'suburl' : suburl,
        'urlsubpage' : urlsubpage,
        'urlpagetag' : urlpagetag,
        'urloptions' : urloptions,
        'subpage' : subpage,
        'urltagstr' : urltagstr,
        'pagetag' : pagetag,
        'pageoptions' : pageoptions,
        'kwoptions' : kwoptions,
        'sepoption' : sepoption,
        'pivotcmds' : pivotcmds,
        'user' : ss.get('user_id',ss.get('user','')),
        'logged_in' : ss.get('logged_in',''),
        'user_role' : ss.get('user_role',''),
        '_libs_' : {'json' : json, 're' : re},
        '_server_' : dict(getcfg('server')),
        '_header_' : dict(bottle.request.headers),
        })
    #args.update(_cfg['server'])
    args['_server_'].update(model.getcfg('server'))
    if isinstance(model,Model) :
        # deprecate --- for grid-base.tpl
        args['ajax_fields'] = model.utf8_bytefix(json.dumps(model.ajaxCols(False,**getparams())).replace(' ',''))

        # new --- for grid-base2.tpl
        args['ajax_extfields'] = model.ajaxExtCols(**getparams())
        args['modeler_options'] = model.modeler._options_
        args['summary_keys'] = []
        skeys = model.getcfg('summaries')
        if skeys :
            for k in skeys.keys() :
                k = k[1:-1]
                if k and k[0]!='_' : args['summary_keys'].append(k)
            args['summary_keys'].sort()
        args['_msg'] = {}
        args['_libs_']['_m']= _m
        args['_libs_']['_l']= _l
    if subpage :
        try :
            pg = subpage
            #return subpage
            if subpage.endswith('/') : pg += 'index'
            return bottle.template(pg,template_lookup=template_lookup,_vars=args)
        except bottle.TemplateError as e :
            #print pg
            if subpage.startswith('subpage/'): raise e
    mainpage = _cfg['server'].get('default_mainpage') or 'mainpage'
    return bottle.template(mainpage,template_lookup=template_lookup,_vars=args)

def load_model (model,dbfile=''):
    if isinstance(model,basestring) : model = model.split(',')
    if isinstance(model,(list,tuple)) :
        for m in model :
            found = False
            for mm in _models :
                if mm.name==m :
                    found = True
                    break
            if not found :
                _models.append(Model(m,dbfile=dbfile))

    if isinstance(model,dict) :
        for mm in _models :
            if mm.name==model.name :
                model = None
                break
        if model :
            _models.append(Model(model,dbfile=dbfile))


def start_http_server () :
    session_opts = {
        'session.type': 'file',
        'session.cookie_expires': 300,
        'session.data_dir': './sessions',
        'session.auto': True
    }
    server_app = SessionMiddleware(bottle.app(), session_opts)
    bottle.debug(getcfg('server',"debug",False))
    print 'start server port',getcfg('server',"port")
    bottle.run(server=(getcfg('server',"server_type",'') or 'wsgiref'),app=server_app,host=getcfg('server','host','0.0.0.0'),port=getcfg('server',"port",8080))


def start (model=None) :
    parser = optparse.OptionParser()
    parser.add_option("-d", "--dbfile",
                      action="store",
                      dest="dbfile",
                      default="",
                      help="database file")
    parser.add_option("-c", "--csv",
                      action="store",
                      dest="csv",
                      default="",
                      help="clear current database and import new csv data to database",)
    parser.add_option("-m", "--model",
                      action="store",
                      dest="model",
                      default="",
                      help="import model name",)
    parser.add_option("-p", "--port",
                      action="store",type="int",
                      dest="port",
                      default=0,
                      help="server listening port",)
    parser.add_option("-x", "--exit",
                      action="store_true",
                      dest="exit",
                      default=False,
                      help="exit without start server")

    reload_cfg (False)
    (options, args) = parser.parse_args()
    if model is None : model = getcfg('server','startup_model',None)
    if options.model : model = options.model
    if model :
        load_model(model,options.dbfile)

    if options.port :
        _restrict_cfg['server']['port'] = options.port
        _cfg['server']['port'] = options.port

    #Model.start_sql_server ()

    if options.csv :
        _models[0].load_csv (options.csv)

    if not options.exit :
        #Model.metadata.create_all()
        start_http_server()

if __name__ == "__main__":
    start ()
