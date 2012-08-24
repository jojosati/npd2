# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        npd1view
# Purpose:     npd1 view with npd2 data model base on dyndmod
#
# Author:      jojosati
#
# Created:     05/01/2012
# Copyright:   (c) jojosati 2012
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os, hashlib, datetime, fnmatch, glob, re

from npd2model import Npd2, next_runno, attr_name_dimension, split_urlsegs
from dyndmod import sqla, _utf8, _unicode, json_loads, Filter
from dyndmod import sqlite_custom_function
from csvmixin import _CSV_implement, _CSV_mixin

import server_default
import taxonomies_default
import users_default
import aliases_default
import regex_default
import summaries_default

__version__ = '1.8.1'
_restrict_cfg =  {
    'server' : {
        'version': __version__,
        'host': "0.0.0.0",
        'port': 8080,
        'suburl': "app",
        'debug': True,
        #'sql_dbfile' : 'db/default.sqlite.db',
        #'sql_echo' : False,
        'server_type' : 'auto',
        }
     }

def csvfloat(s) :
    return float(s.replace(',','') or 0)

npd1to2name = {
    'acat': 'what.category',
    'code': 'code',
    'detail': 'what.title',
    'weight': 'what.weight',
    'gold_weight': 'what.gold_weight',
    'serial': 'what.serial',
    'condition': 'what.condition',
    #'tag': 'what.tags',
    #'outline': 'what.outline',
    'memo': 'note.comment',
    'base_cost': 'base_cost.buying',
    'provider_cost': 'base_cost.provider',
    'mark_cost': 'total_cost', # <--- calculate fld
    'extra_cost': 'note.repairing',
    'lowest_price': 'price.estimate',
    'target_price': 'price.retail',
    'buy_date': 'when.buying',
    'owner': 'who.owner',
    'buy_cond': 'state.buying',
    'keep_date': 'when.keeping',
    'keeper': 'staff.keeper',
    'take_date': 'when.taking',
    'taker': 'who.taker',
    'taker_price': 'price.taker',
    'taken_days': 'taken_days', # <--- calculate fld
    'sell_date': 'when.selling',
    'sell_price': 'price.selling',
    'sell_site': 'staff.seller',
    'sell_profit' : 'sell_profit',
    'repair_cost' : 'repair_cost',
    'buyer': 'who.sellto',
    'receive_date': 'when.receiving',
    'receive_type': 'note.receiving',
    'last_updated': 'ver_logged_time',
    'invalidity' : 'ver_invalidity',
    'revision' : '_last_version',
    'rev_id' : 'ver_version',
    }

npd1csvcols = {
        u'ชนิด'
                : 'acat',
        u'รหัส'
                : 'code',
        u'รายการสินค้า'
                : 'detail',
        u'น้ำหนัก'
                : 'weight',
        u'เบอร์'
                : 'serial',
        u'ทุน'
                : 'base_cost',
        u'ปรับปรุง'
                : 'extra_cost',
        u'ทุนร้าน'
                #: 'mark_cost',
                : lambda k,csvdata,*args: (
                        ('mark_cost',
                            csvfloat(csvdata[k])
                                - csvfloat(csvdata[u'ทุน'])
                                - csvfloat(csvdata[u'ปรับปรุง'] )),
                        ),
        u'ขายประเมิน'
                : 'lowest_price',
        u'ราคาตั้งขาย'
                : lambda k,csvdata,*args: (
                        ('target_price',
                            csvdata[k] or csvdata.get(u'ขายประเมิน')),
                        ),
        u'วันที่ซื้อ'
                : 'buy_date',
        u'ซื้อจาก'
                : 'owner',
        u'วันที่'
                : 'keep_date',
        u'ที่เก็บ'
                : 'keeper',
        u'วันที่ยืม'
                : 'take_date',
        u'ผู้ยืม'
                : 'taker',
        u'หมายเหตุ'
                : 'memo',
        u'วันที่ขาย'
                : 'sell_date',
        u'สถานที่ขาย'
                : 'sell_site',
        u'ผู้ซื้อ'
                : 'buyer',
        u'ราคาขาย'
                : 'sell_price',
        u'วันที่รับ'
                : 'receive_date',
        u'ชนิดรับ'
                : 'receive_type',
        u'mark_cost'
                : lambda k,csvdata,*args: (
                        ('provider_cost',
                            csvfloat(csvdata[k])
                                - csvfloat(csvdata[u'base_cost'])
                                - csvfloat(csvdata[u'extra_cost'])),
                        ),
        }

class Npd1_csv_implement (_CSV_implement) :
    encoding = 'cp874'
    dateformat = '%d/%m/%Y'
    timeformat = '%H:%M:%S'
    datetimeformat = dateformat+' '+timeformat
    numseperator = ','
    colmappings = npd1csvcols

class Npd1C2(Npd2,_CSV_mixin) :
    _csv_implement_class_ = Npd1_csv_implement

_cfg = {
    'server': {},
    'taxonomies':{},
    'users':{},
    'aliases':{},
    'regex':{},
    'summaries':{},
        }
# --------------------------------------------------------
def reload_cfg (restrict=True,sub='./cfg/') :
    if '_cache_ctrl' not in globals() :
        globals()['_cache_ctrl'] = {}
    for entry in _cfg :
        fname = sub+entry+'_cfg.py'
        if not os.path.isfile(fname) :
            fname = entry + '_cfg.py'
        mtime = None
        try:
            mtime = os.path.getmtime(fname)
            if _cache_ctrl.get(fname) == mtime :
                continue
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

        if entry in _restrict_cfg : # update restrict
            for k,v in _restrict_cfg[entry].iteritems() :
                if not restrict :
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

class Npd1View (object) :
    ##Session = scoped_session(sessionmaker())
    ##metadata = sqla.MetaData()
    #mapper = Session.mapper
    #http://www.sqlalchemy.org/trac/wiki/UsageRecipes/SessionAwareMapper
    modelpath = './models/'

    @property
    def suburl (self) :
        u = self.getcfg('server','suburl','') or self.modeler._options_.get('suburl')
        u = u or self.modeler._options_.get('modelname') or self.name
        return u.lower()

    @property
    def dateformat (self) :
        return self.getcfg('server','dateformat','%x')

    @property
    def datetimeformat (self) :
        return self.dateformat + ' %X'

    def concurrent_str(self,lastupdate):
        if isinstance(lastupdate,basestring) :
            try:
                lastupdate = datetime.datetime.strptime(lastupdate,self.datetimeformat)
            except Exception as e: return lastupdate
        if isinstance(lastupdate,datetime.datetime) :
            return lastupdate.strftime('%y%m%d%H%M%S')
        return ''

    def merge_fld_options (self) :
        for fld in self.modeler._fields_ :
            n = fld['name']
            if n in self.modeler._fld_options_ :
                if 'options' not in fld : fld['options'] = {}
                fld['options'].update(self.modeler._fld_options_[n])

    def reload_model (self) :
        fname = './models/'+self.name+'/model_cfg.py'
        try: mtime = os.path.getmtime(fname)
        except Exception as e:
            if _restrict_cfg.get('debug'):
                print fname,type(e).__name__,e.message
            return

        if not hasattr(self,'_cache_ctrl') :
            self._cache_ctrl = {}
        if mtime==self._cache_ctrl.get(fname): return

        xname = {};
        try :
            execfile(fname,{},xname)
            self._cache_ctrl[fname] = mtime
        except Exception as e :
            if _restrict_cfg.get('debug'):
                print fname,type(e).__name__,e.message
            return

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
            except Exception as e:
                if _restrict_cfg.get('debug'):
                    print fname,type(e).__name__,e.message
                pass

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
        tbname = None
        if isinstance(name,basestring) :
            tbname = name
            fname = './models/'+name+'.py'
            if not os.path.isfile(fname) : fname =name + '.py'
            name = {}
            execfile (fname,{},name) # if not exists, raise error
        if isinstance(name,dict) :
            for k in ('_options_','_permissions_','_fld_options_') :
                if k not in name : name[k] = {}
            self.modeler = type((name['_options_'].get('modelname') or name.get('_tablename_',tbname)) + '_modeler',(object,),name)

        if not hasattr(self.modeler,'_wrapper_') : self.modeler._wrapper_= None
        self._cfg = {}
        self.reload_cfg(False)
        echo = self.getcfg('server',"sql_echo",False)
        debug = self.getcfg('server',"debug",False)
        if dbfile :
            self._cfg['server']['sql_dbfile'] = dbfile
        if tbname and not getattr(self.modeler,'_tablename_',None) :
            self.modeler._tablename_= tbname
        tbname = getattr(self.modeler,'_tablename_')
        dbfile = self.getcfg('server','sql_dbfile',None) \
                    or self.modeler._options_.get('sql_dbfile')
        if ':' not in dbfile :
            dbfile = 'sqlite:///'+dbfile
        self.npd2 = Npd1C2(debug=debug,echo=echo,dbpath=dbfile,tablename=tbname)
        self.npd2.echo_("view version: {0}",self.getcfg('server',"version",'-'))

        #self.npd2.create_all()
    def logging(self,fmt,*args) :
        self.npd2.echo_(str(datetime.datetime.now())+' '+fmt,*args)

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
                #p = plst[r]
                if len(p)>1 and p[0]=='!' :
                    if achr not in p[1:] and p[1:] != '*' :
                        return r  # allow by role r
                elif achr in p  or (p=='*' and achr.isalnum()) :
                    return r  # allow by role r
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

    def load_csv (self,csvfile,**kwargs) :
        #if 'drop' in kwargs:
        user_role = kwargs.pop('user_role','administrator')
        kwargs['newtable'] = kwargs.pop('drop',True)
        _encoding = kwargs.pop('_encoding',None)
        if _encoding is None :
            _encoding = self.modeler._options_.get('csv_encoding',self.getcfg('server','csv_encoding',None))
        if _encoding :
            kwargs['encoding'] = _encoding
        kwargs['colnamed'] = lambda c,*a: npd1to2name.get(c) #self._colnamed(c,user_role,*a,)
        return self.npd2.csv_importer(csvfile,**kwargs)

    def ajaxCols (self,use_cols=True,**kwargs) :
        if use_cols :
            cols = kwargs.get('_cols')
            if cols :
                if isinstance(cols,basestring) : cols = json_loads(cols,True)
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
                    if self.colPermission(_nn,role,'_') \
                    or not self.colPermission(_nn,role,'g') :
                        p += 'h' # hidden on grid
                    for _p in 'ave' :
                        if self.colPermission(_nn,role,_p) :
                            p += _p
                    if _fld_o.get('required') :
                        p += 'r'
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
        for _p in self.modeler._options_.get('all_permission') or  self.getcfg('server','all_permission','') or 'gpsqadevzxhi' :
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


    def split_subpage (self,subpage) :
        return subpage.split('//',1) if '//' in subpage else (subpage,'')

    def split_pagetag (self,pagetag) :
        return split_urlsegs(pagetag)
##        pageoptions =  re.split(self.getcfg('regex','re_pageoption'),pagetag)
##        if pageoptions :
##            for i in range(len(pageoptions)) :
##                pageoptions[i] =pageoptions[i].replace("~/","/").replace("~~","~")
##        return pageoptions

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

    def _pivotcmds_translator(self,cmds) :
        if not isinstance(cmds,(list,tuple)):
            cmds = [cmds]
        return self.expand_pivotcmds_alias(cmds)

    def _colnamed (self,col,user_role=None,access=None) :
        acode = {
                'read':'gvae',
                'write':'ae',
                'delete':'d',
                }.get(access)
        if acode and not self.colPermission (col,user_role,access=acode) :
            return None
        return npd1to2name.get(col)

    def _npd2_taxonomy_newargs(self,mappings=None,**kwargs) :

        user_role = kwargs.get('user_role')
        newargs = {
            'colnamed': lambda c,a: self._colnamed(c,user_role,a,),
            'fcmd_translator': lambda c: self._pivotcmds_translator(c),
            'qscols' : kwargs['qscols'],
                }

        fcmd = []
        qsearch = kwargs.get('qsearch','')
        if qsearch :
            fcmd.append(_utf8('@f--'+qsearch))
        pivotcmds = kwargs.get('pivotcmds')
        if pivotcmds :
            fcmd.extend(json_loads(_utf8(pivotcmds),True))
        if fcmd :
            newargs['fcmd'] = fcmd

        if kwargs.get('_search','1').lower() not in ['false','0',''] :
            if 'filters' in kwargs :
                newargs['frule'] = json_loads(_unicode(kwargs.get('filters')))

        scopes = {}
        for k in kwargs :
            if npd1to2name.get(k) :
                scopes[k] = _utf8(kwargs[k])
        if scopes :
            newargs['scopes'] = scopes
        if mappings :
            for x,y in mappings.iteritems() :
                if x in kwargs :
                    newargs[y or x] = _unicode(kwargs.pop(x))
        return newargs

    def taxonomy_mix (self,term,taxes,gret=None,xmax=0) :
        ret = []
        xcnt = 0
        tlen = None
        nterm = term
        if nterm=='*' or nterm.endswith('**') :
            tlen = len(nterm)
        ts = '*' * term.count('*')
        while (len(ts)>1) :
            nterm = nterm.replace(ts,'*')
            ts = ts[1:]
        flt = Filter(nterm) if term else None
        for t in taxes :
            if flt and not flt.match(t) :
                continue
            t = _unicode(t)
            if tlen :
                t = t[:tlen] + '*'
            if (gret and t in gret) or t in ret :
                continue
            ret.append(t)
            xcnt += 1
            if xmax and xcnt>=xmax :
                break
        return ret

    def taxonomy_field (self,field,_encoding='utf8',**kwargs) :
        user_role = kwargs.get('user_role')
        kwargs['_cols'] = self.ajaxCols (**kwargs)
        kwargs['qscols'] = self.qsearchCols (**kwargs)
        term = _utf8(kwargs.get('term'))
        # translate to new argument
        mappings = {
                    '_start':'offset',
                    '_limit':'limit',
                    'hide_untaxable':'untaxable',
                    'term':None,
                    'taxtype':None,
                    }
        newargs = self._npd2_taxonomy_newargs(mappings,**kwargs)

        if 'limit' not in newargs :
            newargs['limit'] = self.getcfg('server','taxonomy_limit',50)

        limit = newargs['limit']
        try : limit = int(limit)
        except: pass

        taxtype = kwargs.get('taxtype')
        if taxtype == 'maxonomy' :
            # 1. taxflds
            taxflds = None

            # 2. term
            if term and isinstance(term,basestring) and '*' not in term :
                term = _utf8(term)
                isnum = '([0-9]{'+str(self.modeler._options_.get('maxonomy_suppressnumsize',2))+',})'
                #re_isnum = re.compile(isnum)
                nterm = re.sub(isnum,'*',term)
                if nterm : #and nterm!='?' :
                    if nterm[-1]!='*' : nterm += '*'
                kwargs['term'] = nterm
        else :
            # 1. taxflds
            taxflds = kwargs.get('autocomplete_mixin')
            if taxflds :
                if isinstance(taxflds,basestring) : taxflds = taxflds.split(',')
                if not isinstance(taxflds,(list,tuple)) :
                    taxflds = self.modeler._options_.get('autocomplete_mixin',{}).get(field)
                    if isinstance(taxflds,basestring) : taxflds = taxflds.split(',')
            # 2. taxtype
            if 'taxtype' not in newargs :
                version = self.modeler._options_.get('version_control',None)
                if version and (version in kwargs) :
                    newargs['taxtype'] = 'history'
                #newargs['history'] = bool(version and (version in kwargs))

            # 3. descriptor
            dsc = kwargs.get('autocomplete_descriptor')
            descriptors = self.modeler._options_.get(
                                'autocomplete_descriptor',{})
            # ------------------------
            def descriptfunc(col) :
                d = dsc
                if d :
                    if not isinstance(d,(basestring,list,tuple)) :
                        d = descriptors.get(col)
                if d :
                    if isinstance(d,basestring) :
                        d = d.split(',')
                return d
            # --------------------------
            if dsc and descriptors :
                newargs['descriptors'] = descriptfunc

        if not isinstance(taxflds,(list,tuple)) :
            taxflds = [field]
        expr = self.npd2.taxonomy(taxflds,**newargs)
        if expr is None :
            return [None]

        session = self.npd2.session
        if limit == 0 :
            return session.execute(expr.count())

        ret = [x[0] for x in session.execute(expr)]

        if taxtype=='maxonomy' :
            rundate = datetime.datetime.now()
            newrunno =  self.modeler._options_.get('maxonomy_format',{}).get(field,'%y-0000')
            newrunpre = re.sub('[0-9]+$','',newrunno)
            if newrunpre :
                newrunno = rundate.strftime(newrunno)
                newrunpre = rundate.strftime(newrunpre)
            re_runprefix = re.compile('('+re.sub('[0-9]','[0-9]',re.escape(newrunpre))+')[0-9]{3,}(?:[^0-9].*)?$')

            nret = []
            xret = []
            re_maxonomy = self.getcfg('regex','re_maxonomy',None)
            if isinstance(re_maxonomy,basestring) :
                re_maxonomy = re.compile(re_maxonomy)
            for x in ret :
                rsegs = re.split(re_runprefix,x)
                if len(rsegs)<2 :
                    continue
                #x = next_runno(x,re_maxonomy)
                #print 'next',x
                #xrunpre = rsegs[0] + rsegs[1]
                #if xrunpre not in nret :
                #    nret.append(xrunpre)
                xrunpre = (rsegs[0] + newrunpre)
                if xrunpre not in nret :
                    nret.append(xrunpre)

##                if x.startswith(nrunpre) :
##                    nret.append(x)
##                else :
##                    xret.append(x)
##                    nrunno = rsegs[0]+newrunpre
##                    #nrunno = next_runno(rsegs[0]+newrunno,re_maxonomy)
##                    if nrunno and nrunno not in nret :
##                        print 'nrunpre',nrunpre,nrunno,rsegs[0],newrunpre
##                        nret.append(nrunno)

            segs = re.split('([0-9]+)',term)
            if len(segs)==1 :
                tpf = term + newrunpre
            else :
                tpf = ''.join(segs[:3])
            if tpf not in nret :
                nret.append(tpf)

            ret = []
            if nret :
                mainbase = self.npd2.mainbase
                qlst = []
                for n in nret :
                    qlst.append(sqla.select([sqla.func.max(mainbase.code).label('nmaxo')],sqla.func.substr(mainbase.code,1,len(n))==n))
                expr = sqla.union(*qlst) if len(qlst)>1 else qlst[0]
                ord = sqla.sql.column('nmaxo')
                if limit<0 :
                    ord = ord.desc()
                expr.order_by(ord)
                for x in session.execute(expr) :
                    x = x[0]
                    if not x :
                        continue
                    xr = []
                    while nret:
                        nn = nret.pop(0)
                        if x.startswith(nn) :
                            break
                        xr.append(next_runno(nn.replace(newrunpre,'')+newrunno,re_maxonomy))
                    ret.extend(xr)
                    ret.append(next_runno(x,re_maxonomy))
            if xret :
                if ret :
                    ret.append('||---')
                ret.extend(xret)
            #if isinstance(limit,int) and len(ret) > abs(limit) :

        else:
            # ---- taxonomy mode
            # 1. seperate primary tax section
            # 2. mixed with pre-defined tax
            xret = []
            if ret and len(taxflds)>1 and hasattr(expr,'selects'):
                # for union query, extract main list
                expr = self.npd2.taxonomy(taxflds[0],**newargs)
                for x in session.execute(expr) :
                    x = x[0]
                    if x in ret :
                        xret.append(x)
                        ret.remove(x)
            if xret :
                if ret :
                    xret.append(u'||---')
                ret = xret + ret
                del xret

            # 3. mixed predefined tax
            if kwargs.get('autocomplete_mixin'):
                # mixed in predefined taxonomies
                mixtaxes = self.getcfg('taxonomies',field,{})
                if mixtaxes :
                    if isinstance(limit,int) and len(ret) < abs(limit) :
                        xmax = abs(limit) - len(ret)
                        taxes = [_unicode(x) for x in mixtaxes]
                        taxes.sort()
                        if limit<0 : taxes.reverse()

                        xret = self.taxonomy_mix(term,taxes,gret=ret,xmax=xmax)
                        if xret :
                            ret.append(u'||---')
                            ret.extend(xret)

        if _encoding :
            for i in xrange(len(ret)) :
                if isinstance(ret[i],unicode):
                    ret[i] = ret[i].encode(_encoding)
        return ret

    def taxonomy_media (self,field,_encoding='utf8',**kwargs) :
        '''
        Returns list of media filenames that match against mediafn
        '''
        media_field = self.modeler._options_.get('media_field',{})
        if field not in media_field :
            return self.taxonomy_field(field,_encoding,**kwargs)

        newargs = dict(kwargs)
        try:
            _start = int(newargs.get('_start') or 0)
        except:
            return None

        try :
            _limit = int(newargs.get('_limit',
                        self.getcfg('server','taxonomy_limit',50)))
        except :
            return None
        climit = _start + abs(_limit)
        if limit<0 :
            climit = -climit
        newargs['_start'] = 0
        newargs['_limit'] = climit

        globarg = ''
        globfnmatch = media_field[field]
        if isinstance(globfnmatch,(list,tuple)):
            if len(globarg)>1 : globarg = globfnmatch[1]
            globfnmatch = globfnmatch[0] if len(globfnmatch)>0 else ''
        globarg = globarg or '{1}'

        codes = []
        margs = {}
        for k in ['fnmatch','sord','user_role'] :
            if k in args : margs[k] = newargs[k]
        if globfnmatch and 'fnmatch' not in margs:
            margs['fnmatch'] = globfnmatch
        nlimit = 0
        while True :
            clist = self.taxonomy('code',_encoding,**newargs)
            if not clist : break
            for c in clist:
                # check existance of file
                wildc = globarg.format(c,c)
                files = self.mediaglob(wildc,_encoding,**margs)
                if files : codes.append(';'.join(files)+'||'+c)
                if len(codes)>=climit : break
            if len(codes)>=climit : break
            # fetch more block of taxonomy
            newargs['_start'] += abs(newargs['_limit'])
            newargs['_limit'] = _limit

        if _start : codes = codes[_start:]
        return codes

    def taxonomy_base (self,field,_encoding='utf8',**kwargs) :
        return self.taxonomy_media(field,_encoding,**kwargs)

    def taxonomy (self,field,_encoding='utf8',**kwargs) :
        #wrapper = getattr(self.modeler._wrapper_,'taxonomy',None)
        #if wrapper : return wrapper(self,field,_encoding,**kwargs)
        return self.taxonomy_base(field,_encoding,**kwargs)

    def maxonomy_base (self,name,_encoding='utf8',**kwargs) :
        kwargs['taxtype'] = 'maxonomy'
        kwargs['hide_untaxable'] = False
        return self.taxonomy_field(name,_encoding,**kwargs)

    def maxonomy (self,field,_encoding='utf8',**kwargs) :
        #wrapper = getattr(self.modeler._wrapper_,'maxonomy',None)
        #if wrapper : return wrapper(self,field,_encoding,**kwargs)
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
        #wrapper = getattr(self.modeler._wrapper_,'autocomplete',None)
        #if wrapper : return wrapper(self,field,_encoding,**kwargs)
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
        filters = json_loads(kwargs.get('fnmatch','[]'),True)
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
                n = _unicode(n)
                if _encoding : n = n.encode(_encoding)
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
        #wrapper = getattr(self.modeler._wrapper_,'mediaglob',None)
        #if wrapper : return wrapper(self,pattern,_encoding,**kwargs)
        return self.mediaglob_base(pattern,_encoding,**kwargs)

    def jqgrid_grid_generator (self,outtype='json',_encoding='',**kwargs) :
        user_role = kwargs.get('user_role')
        if not self.colPermission ('__table__',kwargs.get('user_role'),'g'):
            return
        kwargs['_cols'] = self.ajaxCols (**kwargs)
        kwargs['qscols'] = self.qsearchCols (**kwargs)

        page = int(kwargs.get('page',1))
        limit =  int(kwargs.get('rows',1))
        sidx = kwargs.get('sidx','')
        sord = kwargs.get('sord','')
        npage = int(kwargs.get('npage',1))
        concurrent = self.modeler._options_.get('concurrent_control')
        media_field = self.modeler._options_.get('media_field',{})
        qrycount = kwargs.get('_count','').lower() not in ['false','0','']

        require_custom_func = []
        _summary = None
        if sidx :
            _summary = kwargs.get('_summary',None)
            if str(_summary).lower() in ('false','none','null','0') : _summary = None
        if _summary :
            sfmts = {}
            sfmts.update(self.getcfg('summaries','__',{}))
            sfmts.update(self.getcfg('summaries','_'+str(_summary)+'_',{}))

        # translate to new argument
        newargs = self._npd2_taxonomy_newargs(**kwargs)

        #version = self.modeler._options_.get('version_control')
        history = self.historyPermission(user_role,'g') and kwargs.get('_history')
        if history :
            #if history not in ('history',) :
            #history = 'history'
            newargs['taxtype'] = 'history'

        invalidity = self.historyPermission(user_role,'g') and kwargs.get('_invalidity')
        if invalidity :
            invalidity = invalidity.lower() in ('invalidity','true') or invalidity
            newargs['invalidity'] = invalidity


        def _summarycol(sidx,nlbl,t,sfmts):
            fref = sqla.sql.column('_'+nlbl)
            if sidx != nlbl:
                if t in (sqla.Float,sqla.Integer) :
                    return sqla.func.sum(fref)
                return sqla.func.count(fref) # <---
            sfmt = sfmts.get(nlbl)
            # date/datetime
            if t in (sqla.Date,sqla.DateTime) :
                if t == sqla.DateTime :
                    sfmt = sfmt or sfmts.get('@datetime') or self.datetimeformat
                sfmt = sfmt or sfmts.get('@date') or self.dateformat
                if sfmt :
                    return sqla.func.strftime(sfmt,f) # <---
            # float/integer
            elif t in (sqla.Float,sqla.Integer) :
                try :
                    k = '@integer' if t == sqla.Integer else '@float'
                    sfmt = int(sfmt or sfmts.get(k,sfmts.get('@number')))
                except :
                    sfmt = None
                if sfmt :
                    return sqla.cast(sqla.cast(fref/sfmt, sqla.Integer) * sfmt,t)
            # string
            elif t == sqla.String :
                sfmt = sfmt or sfmts.get('@string')
                if sfmt :
                    if not hasattr(sfmt,'__iter__') :
                        sfmt = list(sfmt)
                    sfo = fref
                    for c in sfmt :
                        if isinstance(c,basestring) :
                            if 'charindex' not in require_custom_func :
                                require_custom_func.append('charindex')
                            sfo = sqla.case([
                                    (sqla.func.charindex(c,sfo)==0,sfo)],
                                    else_=sqla.func.substr(sfo,1,sqla.func.charindex(c,sfo))
                                    )
                        elif isinstance(c,int) :
                            sfo = sqla.func.substr(sfo,1,c)
                    return sfo
            return fref

        mainbase = self.npd2.mainbase
        verbase = self.npd2.verbase
        _lbls = []
        _flds = []
        _sflds = []
        _cflds = []
        glbl = None
        _ver = verbase.version if history else 0
        for c in kwargs['_cols'] :
            n = c.split(':',1)[0]
            nlbl = n

            if not self.colPermission (n,user_role,'gvae') :
                f = None
            else :
                ismedia = n in media_field
                if ismedia:
                    n = 'code'
                f = nn = npd1to2name.get(n)
                if nn :
                    nn,dim = attr_name_dimension(nn)
                    t = self.npd2._fld_dbtype(nn,*dim)
                    f = None
                    if history and nn.startswith('ver_') :
                        f = getattr(verbase,nn.replace('ver_',''),None)
                    if f is None :
                        f = getattr(mainbase,nn,None)
                        if dim and hasattr(f,'dim'):
                            f = f.dim(*dim)
                        if hasattr(f,'scalar') :
                            f = f.scalar(version=_ver,cast=True)
            _lbls.append((nlbl,t))
            if nlbl in dict(_lbls[:-1]) :
                continue

            fo = sqla.null() \
                    if f is None else f

            if _summary :
                sfo = sqla.null() \
                        if isinstance(f,type(None)) else \
                            _summarycol(sidx,nlbl,t,sfmts)
                if sidx==nlbl:
                    _cflds.append(fo.label('_'+nlbl))
                _flds.append(fo.label('_'+nlbl))
                _sflds.append(sfo.label(nlbl))
            else :
                _flds.append(fo.label(nlbl))

            # <-- end -- if summary
        # <-- end -- for c in kwargs['_cols'] :

        session = self.npd2.session
        if require_custom_func :
            sqlite_custom_function(session,require_custom_func)

        expr = self.npd2.taxonomy(**newargs)
        # query count
        if _summary :
            #cqry = session.query(mainbase.id,*_cflds).filter(expr._whereclause)
            #cqry = cqry.from_self(
            #            sqla.func.count(sqla.sql.column('_'+sidx).distinct())
            #            )
            cqry = session.query(mainbase.id,*_cflds) \
                        .filter(expr._whereclause) \
                        .group_by(sqla.sql.column('_'+sidx))
            if history :
                cqry = cqry.join(verbase).filter(mainbase.id==verbase.parent_id)
            count = cqry.count()
        else:
            cqry = session.query(mainbase.id).filter(expr._whereclause)
            if history :
                cqry = cqry.join(verbase).filter(mainbase.id==verbase.parent_id)
            count = cqry.count()
        if qrycount :
            yield count if outtype=='csv' else [count]
            return

        # prepare query data
        if _summary :
            _flds.append(mainbase.id.label('__id_'))
            qry = session.query(*_flds).filter(expr._whereclause)
            _sflds.append(sqla.sql.column('__id_').label('_id_'))
            if history :
                qry = qry.add_column(verbase.version.label('__ver_')).filter(mainbase.id==verbase.parent_id)
                _sflds.append(sqla.sql.column('__ver_').label('_ver_'))
            qry = qry.from_self(*_sflds).group_by(sqla.sql.column(sidx))
        else:
            _flds.append(mainbase.id.label('_id_'))
            if concurrent :
                _flds.append(mainbase.ver_logged_time.label('_last_update_'))
            qry = session.query(*_flds).filter(expr._whereclause)
            if history :
                qry = qry.add_column(verbase.version.label('_ver_')).filter(mainbase.id==verbase.parent_id)

        # append query order_by
        if sidx :
            ord = sqla.sql.column(('_' if _summary else '') + sidx)
            if sord.lower()=='desc' :
                ord = ord.desc()
            qry = qry.order_by(ord)

        # append query offset/limit
        if npage<1 :
            npage = 1

        #if limit<0 :
        #    limit = 1

        total_pages = 0
        if count > 0 :
            if limit > 0 :
                total_pages = int(count/limit)
                if count > total_pages*limit :
                    total_pages += 1
            else :
                total_pages = 1

        if page<1 :
            page = 1

        if page > total_pages :
            page = total_pages

        if limit > 0 :
            offset = 0
            if page :
                offset = (page-1) * limit

            if limit>0 :
                qry = qry.limit(limit * npage)

            if offset :
                qry = qry.offset(offset)

        # yeild header
        if outtype=='csv' :
            hdr = list(_unicode(n[0]) for n in _lbls)
            if _encoding :
                hdr = list(n.encode(_encoding) for n in hdr)
        else :
            hdr ={
                    'page' : page,
                    'total' : total_pages,
                    'records' : count,
                    'rows' : [],
                    }
        yield hdr

        # yeild rows
        rno = 0
        for row in qry.all() :
            rno += 1
            id = row._id_
            if history and row._ver_ :
                id = str(id) + '.' + str(row._ver_)
            if concurrent and not _summary:
                id = str(id) + ':'+ self.concurrent_str(row._last_update_)
            data = []
            for n,t in _lbls :
                d = getattr(row,n)
                if n in media_field :
                    globarg = ''
                    globfnmatch = media_field[n]
                    if isinstance(globfnmatch,(list,tuple)):
                        if len(globarg)>1 :
                            globarg = globfnmatch[1]
                        globfnmatch = globfnmatch[0] if len(globfnmatch)>0 else ''
                    globarg = globarg or '{1}'
                    wildc = globarg.format(d,d)
                    files = self.mediaglob(
                                wildc, fnmatach=globfnmatch, user_role=user_role)
                    d = None if not files else ';'.join(files)
                else :
                    if not _summary :
                        d = self.npd2.cast_result_value(t,d)
                        if isinstance(d,(datetime.date,datetime.datetime)) :
                            dfmt = None
                            if isinstance(d,datetime.datetime) :
                                dfmt = self.datetimeformat
                            dfmt = dfmt or self.dateformat
                            if dfmt :
                                d = d.strftime(dfmt)
                if outtype=='csv' and _encoding and isinstance(d,unicode) :
                    d = d.encode(_encoding)
                data.append(d)

            yield (data if outtype=='csv' else {'id':id, 'cell':data})


    def jqgrid_grid_base (self,**kwargs) :
        ret = None
        for r in self.jqgrid_grid_generator ('jqgrid',**kwargs) :
            if ret is None : ret = r ; continue
            if 'rows'in ret : ret['rows'].append(r)
        return ret

    def jqgrid_grid (self,**kwargs) :
        #wrapper = getattr(self.modeler._wrapper_,'jqgrid_grid',None)
        #if wrapper : return wrapper(self,**kwargs)
        return self.jqgrid_grid_base(**kwargs)

    def reform_tags(self,tags) :
        if tags is None : return tags
        tt = []
        for t in tags.split(',') :
            t = t.strip()
            if not t : continue
            if t not in tt : tt.append(t)
        tt.sort()
        return ','.join(tt)

    def update_field(self,rec,k,val,user_role='',permcode='') :
        nn = npd1to2name.get(k)
        if not nn :
            return False
        nn,dim = attr_name_dimension(nn)
##        if k=='provider_cost' :
##            print '1',nn,dim
        oval = getattr(rec,nn) if not dim else rec.dfields(nn,*dim)
##        if k=='provider_cost' :
##            print '2 oval',oval
        val = _unicode(val.rstrip()) or None

        t = self.npd2._fld_dbtype(nn,*dim,storable=True)
        if t is None :
            return False
        def _cnv(v) :
            if v and isinstance(v,basestring):
                if t == sqla.DateTime :
                    try : v = datetime.datetime.strptime(v,self.datetimeformat)
                    except Exception as e :
                        raise e
                elif t == sqla.Date :
                    try : v = datetime.datetime.strptime(v,self.dateformat).date()
                    except Exception as e :
                        raise e
                elif t == sqla.Float:
                    try : v = float(v) or None
                    except Exception as e :
                        raise e
                elif t == sqla.Integer:
                    try : v = int(v) or None
                    except Exception as e :
                        raise e
                if k==self.modeler._options_.get('tagging_control'):
                    v = self.reform_tags(v)
            return v or None

        val = _cnv(val)
        oval = _cnv(oval)
        if oval != val :
            if permcode and not self.colPermission (k,user_role,permcode) :
                raise Exception('permission denied for '+k)
            setattr(rec,nn,val) if not dim else rec.dfields.set_fld(nn,val,*dim)
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
            last_updated = rec._ver.logged_time
            if self.concurrent_str(last_updated) != concurrent :
                raise Exception('Concurrent conflict ({0}<>{1}), data changed by other client'.format(self.concurrent_str(last_updated),concurrent))
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
                if not isinstance(k,sqla.Column) :
                    continue
                k = k.key
                if k in ['id','last_updated']: continue
                if k==version:
                    setattr(vcrec,version,getattr(rec,version)+self.version_tag(**kwargs))
                    continue
                v = getattr(rec,k)
                if v : setattr(vcrec,k,v)
        return vcrec

    def jqgrid_new_items(self,**kwargs) :
        cmd = kwargs.get('oper')
        user_role = kwargs.get('user_role')
        if not self.colPermission ('__table__',user_role,'a') :
            return [False,"permission denied",'']
        re_maxonomy = self.getcfg('regex','re_maxonomy',None)

        if isinstance(re_maxonomy,basestring) :
            re_maxonomy = re.compile(re_maxonomy)
        user_id = kwargs.get('user_id')
        session = self.npd2.user_session(user_id)
        mainbase = self.npd2.mainbase
        head = json_loads(kwargs.get('head','{}'))
        #if head['keeper'] :
        #    head['keep_date'] = head['buy_date']
        items = json_loads(kwargs.get('items','[]'))
        ncodes = []

        def _addrec(ncode,item,refcode=None) :
            rec = mainbase(code=ncode)
            if refcode :
                refcode = '(#'+refcode+')/@/@'
            data = {}
            data.update(head)
            data.update(item)
            for c in data:
                if c in ['code','id','last_updated']: continue
                v = data[c]
                if refcode and c=='owner' :
                    v = (v or '') + refcode
                # note: update_field may raise exception permission not allow
                self.update_field(rec,c,v,user_role,'a')
            session.add(rec)
            #ncodes.append(ncode)

        def _fail(msg):
            session.rollback()
            return [False,msg,'']

        def npd1fld(brec,fld,*value) :
            bname = npd1to2name.get(fld)
            bname,bdim = attr_name_dimension(bname)

            if value :
                setattr(brec,bname,bval) \
                    if not bdim else \
                    brec.dfields.set_fld(bname,value[0],*bdim)
            return getattr(brec,bname) \
                        if not bdim else \
                        brec.dfields.get_fld(bname,*bdim)
        xitems = []
        # pass 1: checking for valid code without rerun
        while items :
            item = items.pop(0)
            ncode = item['code'].rstrip() # fix bug trailing space
            fixcode,detail = None,item['detail']
            if '/' in detail[:1] and '/' in detail[1:] :
                fixcode,detail = detail.split('/',2)[1:]
                fixcode = fixcode.rstrip() or ncode
                item['detail'] = detail

            brec = None
            if item['id'].startswith('dnd_') \
                or item['id'].startswith('clk_') :
                try :
                    brec = session.query(mainbase).filter(mainbase.code==ncode).one()
                    bval = npd1fld(brec,'buyer') or ''
                    if '(#' in bval :
                        return _fail("{0}, already transfer as {1}".format(ncode,_utf8(bval)))
                except : pass

            if fixcode or re.search(re_maxonomy,ncode) :
                try :
                    session.query(mainbase).filter(mainbase.code==fixcode or ncode).one()
                    if fixcode :
                        return _fail("{0}, code already existed.".format(fixcode))
                except :
                    bcode = None
                    if brec :
                        bval = npd1fld(brec,'buyer')
                        bval += '(#'+(fixcode or ncode)+')/@/@' # refer new code, untaxable sign
                        npd1fld(brec,'buyer',bval)
                        bcode = brec.code
                        session.add(brec)
                    # add new data record
                    try :  _addrec(fixcode or ncode,item,bcode)
                    except Exception as e :
                        return _fail("{0}, {1}".format(fixcode or ncode,e))
                    ncodes.append(fixcode or ncode)
                    continue

            ncodes.append(None)
            # leave require running new code for pass 2
            item['(brec)'] = brec
            xitems.append(item)

        while xitems :
            item = xitems.pop(0)
            brec = item.pop('(brec)')
            ncode = item['code'].rstrip()
            # running new code
            args = {
                'term':ncode,
                'acat':item['acat'],
                'user_role':user_role,
                #'_limit':1,
                }
            ncode = self.maxonomy('code',**args)
            if not ncode:
                return _fail("{0}, fail in trying to run new valid code.".format(item['code']))
            ncode = ncode[0] # use first suitable code

            bcode = None
            if brec :
                # marking back-ref code in buyer field of back-ref-item
                bval = npd1fld(brec,'buyer')
                bval += '(#'+ncode+')/@/@' # refer new code, untaxable sign
                npd1fld(brec,'buyer',bval)
                bcode = brec.code
                session.add(brec)
            # add new data record
            try :
                _addrec(ncode,item,bcode)
            except Exception as e :
                return _fail("{0}, {1}".format(ncode,e))
            i = ncodes.index(None)
            if i>=0 :
                ncodes[i] = ncode
        try:
            session.commit()
        except Exception as e :
            return _fail("{0}, {1}".format(cmd,e))
        return [True,cmd,','.join(ncodes)]

    def jqgrid_update_items(self,uflds,**kwargs) :
        cmd = kwargs.get('oper')
        user_role = kwargs.get('user_role')
        if not self.colPermission ('__table__',user_role,'e') :
            return [False,"'{0}' permission denied".format(cmd),'']
        user_id = kwargs.get('user_id')
        session = self.npd2.user_session(user_id)
        mainbase = self.npd2.mainbase
        head = json_loads(kwargs.get('head','{}'))
        items = json_loads(kwargs.get('items','[]'))
        recs = []
        for item in items :
            try:
                #lu = item.get('last_updated')
                rec = session.query(mainbase).filter(mainbase.code==item['code']).one()
                self.concurrent_ctrl(rec,last_updated=item.get('last_updated'),**kwargs)
            except Exception as e :
                return [False,"{0}, {1}".format(item['code'],e),'']
            chflag = False
            for f in uflds:
                pfix = ''
                if f[0] in '!&' :
                    pfix,f = f[0],f[1:]
                v = '' if pfix=='!' else item.get(f,head.get(f))
                try:
                    if self.update_field(rec,f,v,user_role,'e') :
                        chflag = True
                except Exception as e :
                    return [False,"{0}, {1}".format(item['code'],e),'']
            if chflag :
                try:
                    session.add(rec)
                except Exception as e  : #sqla.exc.SQLAlchemyError,exc :
                    session.rollback()
                    return [False,"{0} {1} {2}".format(rec.code,e),id]
                recs.append(rec.code)
        codes = recs
        if recs :
            try:
                session.commit()
            except Exception as e :
                session.rollback()
                return [False,"{0} {1} {2}".format(cmd,','.join(codes),e),'']
        return [True,cmd,','.join(codes)]

    def jqgrid_edit_base (self,**kwargs) :
        '''
            oper - standard jquery ['add','edir','del']
                 - extend for npd1 ['take','sell','keep','buy']
        '''
        cmd = kwargs.get('oper')
        ucmds = {
            'take' : ['&take_date','&taker','&taker_price'],
            'sell' : ['&sell_date','&buyer','&sell_price','sell_site','receive_date','receive_type'],
            'keep' : ['&keep_date','&keeper','!take_date','!taker','!taker_price'],
            }
        if cmd in ucmds :
            return self.jqgrid_update_items(ucmds[cmd],**kwargs)
        if cmd=='buy' :
            return self.jqgrid_new_items(**kwargs)


        id = kwargs.get('id','')

        if id=='_empty' : id = ''
        id,cc = id.split(':',1) if ':' in id else (id,'')

        idmsg = "({0})".format(id or "new id")
        user_role = kwargs.get('user_role')
        user_id = kwargs.get('user_id')
        session = self.npd2.user_session(user_id)
        mainbase = self.npd2.mainbase
        # verify concurrent control
        if cmd == "add" :
            rec = mainbase()
        if id and cmd in ("del","edit") :
            try :
                rec = session.query(mainbase).filter(mainbase.id==id).one()
                self.concurrent_ctrl(rec,**kwargs)
                idmsg += " '{0}'".format(rec.code)
                #vcrec = self.version_ctrl(rec,**kwargs)
            except Exception as e :
                return [False,"{0} {1}".format(idmsg,e),id]

        if cmd=="del" :
            if not self.colPermission ('__table__',user_role,'d') :
                return [False,"%s permission denied." % (idmsg),id]
            try:
                session.delete(rec)
                session.commit()
            except Exception as e : #sqla.exc.SQLAlchemyError,exc :
                session.rollback()
                return [False,"{0} {1}".format(idmsg,e),id]
            return [True,idmsg,id]

        if cmd in ("add","edit") :
            permcode = 'a' if cmd=='add' else 'e'
            if not self.colPermission ('__table__',user_role,permcode) :
                return [False,"%s permission denied." % (idmsg),id]
            chflag = False
            for k in kwargs.iterkeys() :
                if k in ('id','last_updated'):
                    continue
                #if not isinstance(getattr(self.odb,k),sqla.Column) : continue
                try:
                    if self.update_field(rec,k,kwargs[k],user_role,permcode):
                        chflag = True
                        if k=='code':
                            idmsg += " ('{0}')".format(rec.code)
                except Exception as e :
                    return [False,"{0} (field='{1}') {2}".format(idmsg,k,e),id]
            if chflag :
                try:
                    session.add(rec)
                    session.commit()
                    id = rec.id
                except Exception as e  : #sqla.exc.SQLAlchemyError,exc :
                    session.rollback()
                    return [False,"{0} {1}".format(idmsg,e),id]
            return [True,cmd+idmsg,id]
        return [False,"unknown command '{0}'".format(cmd),id]

    def jqgrid_edit (self,**kwargs) :
        #wrapper = getattr(self.modeler._wrapper_,'jqgrid_edit',None)
        #if wrapper : return wrapper(self,**kwargs)
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

##    def __call__ (*args,**kwargs) :
##        return self.odb(*args,**kwargs)


if __name__ == "__main__":
    reload_cfg(False)
    npd1 = Npd1View('assets')
    #npd1.npd2.engine.echo = False
    #npd1.npd2.quiet = False
    #npd1.npd2.debug = False
    #npd1.load_csv('asset-20120225.csv,raw',limit=0,user_id='csvimporter')

def xxx():
    #role = {'user_role':'manager'}
    #print npd1._pivotcmds(['@f-acat-test'],**role)
    filters = u'''{
                "groupOp":"AND",
                "rules": [
                    {"field":"target_price","op":"cn","data":"==800.0"}
                    ]
                }'''
##    for tax in npd1.taxonomy_base('target_price',user_role='manager',filters=filters):
##        print _unicode(tax) #u'"{0}"'.format(tax)

    for tax in npd1.maxonomy_base('code',user_role='manager',acat='กำไล') :
        print _unicode(tax)


    print '---- test grid generator ----'
    args = {
        '_cols':[
                'acat','code',#'detail','weight','serial','condition','tag','outline','memo',
                'base_cost','mark_cost','extra_cost','lowest_price','target_price',
                'buy_date',
                #'owner','buy_cond',
                #'keep_date','keeper','takedate','taker',
                #'taken_days',
                #'sell_date','sell_site','buyer','sell_price',
                #'receive_date','receive_type',
                ],
        'rows':20,
        'user_role':'manager',
        'sidx':'buy_date',
        '_summary':0,
        'sord':'desc',
        'pivotcmds': '@f-acat-!=จี้'
        }
##    for row in npd1.jqgrid_grid_generator(**args):
##        if 'cell' in row :
##            for x in row['cell'] :
##                print x,
##            print ''
    print '---- test grid ----'
    args = {
        'sidx': 'detail',
        'rows': '20',
        'user_id': 'manager',
        '_search': 'true',
        'filters': '{"groupOp":"AND","rules":[{"field":"detail","op":"cn","data":"black"}]}',
        'user_role': 'manager',
        'pivotcmds': '[]',
        'sord': 'asc',
        'logged_in': 1,
        'page': '1',
        '_cols': 'acat,detail,target_price',
        '_summary': '',
        'qsearch': '',
        }


    for k,v in npd1.jqgrid_grid(**args).iteritems():
        if k=='rows' :
            #print k,'='
            for r in v :
                for x in r['cell'] :
                    print '  ',x,
                print ''
            continue
        #print k,'=',v


