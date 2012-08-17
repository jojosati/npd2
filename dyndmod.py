# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        dyndmod
# Purpose:     dynamic data model
#
# Author:      sathit jittanupat
#
# Created:     30/11/2011
# Copyright:   (c) jojosati 2011
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import datetime, re, json
import sqlalchemy as sqla
from sqlalchemy.ext import declarative as sqla_declarative
from sqlalchemy.ext import hybrid as sqla_hybrid

from srchexp import _SrchExp, Search, _unicode, _utf8, like2re

sqla_Base = sqla_declarative.declarative_base()

#http://www.sqlalchemy.org/trac/wiki/UsageRecipes/SessionAwareMapper
def sqla_session_mapper(scoped_session):
    def mapper(cls, *arg, **kw):
        cls.query = scoped_session.query_property()
        return sqla.orm.mapper(cls, *arg, **kw)
    return mapper

def sqlite_custom_function (session,funcs=None):
    conn = session.connection()
    if funcs is None or 'charindex' in funcs :
        def charindex(needle,hay,start=0) :
            try : return hay.find(needle,start)+1
            except : return 0
        expr = "select charindex('A','ABC')"
        try:
            conn.execute(expr)
        except :
            #print "create function charindex"
            conn.connection.create_function("charindex",2,charindex)
            conn.execute(expr)

def parse_column_args(cdef) :
    """
    prepare argument for Column schema
    http://www.sqlalchemy.org/docs/core/schema.html#sqlalchemy.schema.Column
    """
    _terms = {
        'type_' : {
            'integer':sqla.Integer,
            'float':sqla.Float,
            'date':sqla.Date,
            'time':sqla.Time,
            'datetime':sqla.DateTime,
            '':sqla.String, # default
            },
        'nullable' : {'notnull': False},
        'unique' : {'unique' : True},
        'index' : {'index': True},
        'deferred' : {'deferred': True},
        }

    if isinstance(cdef,dict) : return cdef
    if isinstance(cdef,basestring) :
        args = {}
        n = cdef
        if ':' in n :
            n,ts = n.split(':',1)
            for t in ts.split(','):
                t = t.strip().lower()
                if not t : continue
                for e in _terms :
                    if e not in args and t in _terms[e] :
                        args[e] = _terms[e][t]
        args['name'] = n
        # set default
        for e in _terms :
            if e not in args and '' in _terms[e] :
                args[e] = _terms[e]['']
        return args

def nullif_value (dbtype) :
    return {
        sqla.Integer: 0,
        sqla.Float: 0,
        sqla.String: '',
        }.get(dbtype)

##    if v is not None :
##        return sqla.func.nullif(col,v)
##    return col

def schema_columns(obj) :
    cols = []
    cc = []
    if hasattr(obj,'c') :
        cc = obj.c
    elif hasattr(obj,'__table__') :
        cc = obj.__table__.c
    elif hasattr(obj,'_sa_class_manager') :
        cc = obj._sa_class_manager.mapper.c
    for c in cc :
        if isinstance(c,sqla.Column) :
            cols.append(c.name)
    return cols


def attr_name_dimension(name,dimension=None) :
    if isinstance(name,basestring) :
        if '.' in name :
            name,dimension = name.split('.',1)
    if dimension is None :
        dimension = []
    if isinstance(dimension,basestring) :
        dimension = dimension.split(',')
    if not isinstance(dimension,(list,tuple)):
        dimension = [dimension]
    return (name,dimension)

def all_sum (vals) :
    if isinstance(vals,dict) :
        return all_sum(dict.values())
    if isinstance(val,(list,tuple)) :
        v = 0
        for x in vals :
            if isintance(x,(list,tuple)) :
                x = all_sum(x)
            if x:
                try:
                    x = float(x)
                    v += x
                except :
                    pass
    else :
        try :
            v = float(x)
        except:
            v = 0
    return v

def json_loads(jsonstr,shortlist=False) :
    if not isinstance(jsonstr,basestring) :
        return None
    jstr = _utf8(jsonstr)
    try :
        return json.loads(jstr,strict=False)
    except :
        if not shortlist : raise
    return jstr.split(',')

def json_dumps(obj) :
    return json.dumps(obj)

def col_formatted_expr(col,name,type_,fmtcfg) :
    q = None
    if not fmtcfg :
        fmtcfg = {}
    fmt = fmtcfg.get(name)
    if fmt is None and name :
        if '.' in name :
            fmt = fmtcfg.get(name.split('.',1)[0])
    if fmt is None and type_:
        fmt = fmtcfg.get(type_) or fmtcfg.get(type_.__visit_name__)
    if fmt and callable(fmt) :
        return fmt(col)
    if fmt :
        if type_ in (sqla.Date,sqla.DateTime,sqla.Time) :
            q = sqla.func.strftime(fmt,col)
        if type_ in (sqla.Float,) :
            ddv = 10**(fmt-1)
            q = sqla.cast(sqla.cast(col,sqla.Integer),sqla.String) + \
                '.' + \
                sqla.func.substr(sqla.func.replace(
                    sqla.func.round(
                        (1+sqla.func.abs(col - sqla.cast(col,sqla.Integer)))*ddv,12)
                    ,'.',''),2)
            #q = sqla.func.round(col,fmt)
    if q is None :
        if hasattr(col,'type') :
            t = col.type
        else :
            t = col.property.columns[0].type
        q = col if t == sqla.String else sqla.cast(col,sqla.String)
    return q #sqla.func.ifnull(q,'')

class __Flds(object) :
    # abstract class for static & dynamic fields object
    def __init__(self,mainobj) :
        object.__setattr__(self,"_mainobj",mainobj)
        #object.__setattr__(self,"_reserved",['_mainobj','_vc'])

    def __repr__(self) :
        return "<%s(%s)>" % (self.__class__.__name__,repr(self.__call__()))

    def __getattr__(self,name,*default) :
        return self.__dict__.get(
                    name, self.get_fld(name))
##        if name in attrs : #object.__getattribute__(self,'__dict__') :
##            return attrs[name] #object.__getattribute__(self,name)
##        return self.get_fld(name,*default)

    def __setattr__(self,name,value) :
        if name in self.__dict__:
            return object.__setattr__(self,name,value)
        return self.set_fld(name,value)

    def __delattr__ (self,name) :
        if name in self.__dict__:
            return object.__delattr__(self,name)
        return self.del_fld(name)

    def __call__(self,name=None) :
        if name :
            return self.get_fld(name)
        return self.get_cols()

    def data(self,**settings) :
        ret = {}
        if settings :
            for n in settings :
                self.set_fld(n,settings[n])
        for n in self.get_cols():
            ret[n] = self.get_fld(n)
        return ret

    @property
    def _model_(self) :
        return self._mainobj._model_

    def get_cols(self) :
        raise NotImplementedError()

    def get_fld(self,name) :
        raise NotImplementedError()

    def set_fld(self,name,value) :
        raise NotImplementedError()

    def del_fld(self,name) :
        raise NotImplementedError()

class _DynamicFlds(__Flds) :
    @property
    def _flds(self) :
        n = self._model_.named("_flds")
        return getattr(self._mainobj,n)

    @property
    def fldbase(self) :
        return self._model_.fldbase

    def get_cols(self) :
        ret = []
        for arg in self._model_._dynamicflds_args :
            n = attr_name_dimension(arg['name'])[0]
            if n not in ret :
                ret.append(n)

        for fld in self._flds :
            if not fld.version and fld.value is not None:
                n = str(fld.name)
                if n not in ret : ret.append(n)
        return ret

    def _fldobjs(self,name,*dimension) :
        flds = []
        dims = list(str(dimension[i]) for i in xrange(len(dimension)))
        for fld in self._flds :
            if name == fld.name and fld.version==0 \
            and (not dims or str(fld.dimension_key) in dims) :
                flds.append(fld)
        return flds
##        if flds :
##            return flds if len(flds)>1 else flds[0]
##        return None

##    def _get_fldobj(self,name) :
##        flds = self._fldobjs(name)
##        if flds :
##            return flds if len(flds)>1 else flds[0]
##        return None

    def get_fld(self,name,*dimension) :
        '''
        return value depend on type of dimension
        1 scalar - single value / single dimension
        2 list - multiple value / single dimension
        3 dict - multiple dimension
        '''
        name,dimension = attr_name_dimension(name,dimension)
        t = self._model_._fld_dbtype(name)

        flds = self._fldobjs(name,*dimension)
        if flds :
            vals = {}
            for f in flds :
                k = f.dimension_key
                idx = f.dimension_idx
                tt = self._model_._fld_dbtype(name,k)
                v = self._model_.cast_result_value(tt or t,f.value)
                if v is None :
                    continue
                if k not in vals :
                    vals[k] = {}
                if v is not None :
                    vals[k][idx] = v

            # warp up idx component
            for k in vals.keys() :
                vk = vals[k].keys()
                if vk :
                    maxi = max(*vk) if len(vk)>1 else vk[0]
                    v = []
                    for i in xrange(maxi+1) :
                        v.append(vals[k].get(i))
                    if len(v)==1 :
                        v = v[0]
                    vals[k] = v
                else :
                    del vals[k]
            if vals :
                # wrap up single dimension
                if len(vals)==1 and (vals.keys()[0]=='' or len(dimension)==1) :
                    return vals.values()[0]
                return vals
            return None
        if t is not None :
            return None
        raise AttributeError("dynamic field '%s' not found." % name)

    def set_fld(self,name,value,*dimension,**otherfields) :
        '''
        value could be
        1. scalar
        2. list/tuple in same dimension
        3. dict for different dimension
        '''
        def _alldims() :
            dims = []
            for f in flds :
                if f.dimension_key not in dims :
                    dims.append(f.dimension_key)
            return dims

        name,dimension = attr_name_dimension(name,dimension)

        if isinstance(value,dict):
            flds = self._fldobjs(name)
            for d in value.iterkeys() :
                if not dimension or d in dimension :
                    self.set_fld(name,value[d],d,**otherfields)
            if not dimension :
                # clear all non-listed dimension
                for d in _alldims():
                    if d not in value :
                        self.set_fld(name,None,d)
            return

        if len(dimension)>1 :
            for d in dimension :
                self.set_fld(name,value,d,**otherfields)
            return

        # if not passing parm dimension, use default dimension ''
        dimension = dimension[0] if dimension else ''
        # if passing parm dimension as None, effect to all existing dimension
        if dimension is None :
            flds = self._fldobjs(name)
            self.set_fld(name,value,*_alldims(),**otherfields)
            return


        dimension = str(dimension) # make sure dimension must be str
        flds = self._fldobjs(name,dimension)
        if not isinstance(value,(list,tuple)) :
            value = [value]

        others = {}
        for k,v in otherfields.iteritems():
            if k not in self.fldbase.__table__.c :
                raise AttributeError(
                    "attribute '%s' not in %s."
                    % (k,self.fldbase.__name__))
            if k in ('parent_id','dimension_key','dimension_idx','name','value'):
                continue
            if isinstance(v,dict) :
                for x in v.iterkeys() :
                    if dimension == str(x) :
                        others[k] = v[x]
                        break
                if dimension not in others and None in v :
                    others[k] = v[None]
            else :
                others[k] = v

        #flen = len(flds)
        vlen = len(value)
        for i in xrange(vlen) :
            v = value[i]
            fld  = None
            for f in flds :
                if f.dimension_idx == i :
                    fld = f
                    break ;
            if fld is None and v is not None :
                fld = self.fldbase(
                        name=name,
                        dimension_key=dimension,
                        dimension_idx=i,
                        )

                self._flds.append(fld)
            if fld is not None :
                fld.value = v
                for k,v in others.iteritems():
                    if isinstance(v,(list,tuple)) :
                        v = v[i] if i < len(v) else None

                    # for scalar = set all in same dimension
                    # for list/tuple, set None if out of range
                    setattr(fld,k,v)

    def del_fld(self,name,*dimension) :
        name,dimension = attr_name_dimension(name,dimension)
        self.set_fld(name,None,*dimension)

    def __call__(self,*args,**kwargs) :
        settings = {}
        if args :
            settings['name'] = args[0]
            if args[1:] :
                settings['dimension'] = args[1:]
        settings.update(kwargs)
        if settings.get('name') :
            return self.get_fld(settings['name'],*settings.get('dimension',[]))
        return self.get_cols()

class _ChildFlds(__Flds) :
    @property
    def _flds(self) :
        n = self._model_.named("_children")
        return getattr(self._mainobj,n,[])

    @property
    def childbase(self) :
        return self._model_.childbase

    def get_cols(self) :
        ret = list (n for n in self._model_._childflds_args)
        ivname = self._model_.named("versionfld",'invalidity')
        for fld in self._flds :
            n = str(fld.parent_entity)
            if n not in ret and not getattr(fld,ivname) :
                    ret.append(n)
        return ret

    def _fldobjs(self,name) :
        flds = []
        ivname = self._model_.named("versionfld",'invalidity')
        for fld in self._flds :
            if name == fld.parent_entity and not getattr(fld,ivname) :
                flds.append(fld)
        return flds

    def get_fld(self,name) :
        return self._fldobjs(name)
        #raise AttributeError("dynamic field '%s' not found." % name)

    def set_fld(self,name,value) :
        flds = self._fldobjs(name)
        if value is None :
            if flds :
                #delname = self._model_.named("versionfld",'invalidity')
                for f in flds :
                    del f
            return
        if isinstance(value,dict) :
            value = [value]
        for val in value :
            id = val.pop('id',None)
            fld = None
            if id :
                for f in flds :
                    if fld.id==id :
                        fld = f
                        break
            if fld is None :
                fld = self.childbase(name=name)
                self._flds.append(fld)
            for k,v in val.iteritems() :
                if hasattr(fld,k) :
                    setattr(fld,k,v)
                elif hasattr(fld._ver,k) :
                    setattr(fld._ver,k,v)
                else :
                    fld.dfields.set_fld(k,v)

    def del_fld(self,name) :
        self.set_fld(name,None)

class _StaticFlds(__Flds) :
    def get_cols(self) :
        cols = schema_columns(self._mainobj)
        cols.remove('id')
        return cols

    def get_fld(self,name) :
        return getattr(self._mainobj,name)

    def set_fld(self,name,value) :
        if name not in self.get_cols():
            raise AttributeError("static filed '%s' not found." % name)
        setattr(self._mainobj,name,value)

    def del_fld(self,name) :
        self.set_fld(name,None)

class dynamicfld_hybrid_property(sqla_hybrid.hybrid_property):
    def __get__(self, instance, owner):
        if instance is None:
            self.dim = lambda *dimension: \
                            self.expr(owner,*dimension)
        return sqla_hybrid.hybrid_property.__get__(self, instance,owner)

    def comparator(self, comparator):
        proxy_attr = sqla_hybrid.attributes.create_proxied_attribute(self)
        def expr(owner,*dimension):
            return proxy_attr( owner, self.__name__,
                                self, comparator(owner,*dimension))
        self.expr = expr
        return self

class dfields_hybrid_property(sqla_hybrid.hybrid_property):
    def __get__(self, instance, owner):
        if instance is None:
            self.get_fld = lambda *args,**kwargs : \
                                self.expr(owner,*args,**kwargs)
        return sqla_hybrid.hybrid_property.__get__(self, instance,owner)

    def comparator(self, comparator):
        proxy_attr = sqla_hybrid.attributes.create_proxied_attribute(self)
        def fcall(_self,name=None) :
            if name :
                return _self.get_fld(name)
        proxy_attr.__call__= fcall

        def expr(owner,*args,**kwargs):
            return proxy_attr( owner, self.__name__,
                                self, comparator(owner,*args,**kwargs))
        self.expr = expr
        return self

class commonComparator(object):
    def _fld(self) :
        return self.__clause_element__()

    def _fldversion(self) :
        return sqla.func.abs(0)

    def _fldtype(self) :
        fld = self._fld()
        if hasattr(fld,'type') :
            return fld.type
        return fld.property.columns[0].type

    def _fldname(self) :
        return self._fld().key

    def _deltaversion(self) :
        return sqla.func.abs(0)

    def as_formatted(self,formatter=None):
        fld = self._fld()

        if formatter in (None,True) :
            if hasattr(fld,'_annotations') :
                class_ = fld._annotations['parentmapper'].class_
            else :
                class_ = fld.class_
            formatter = getattr(class_._model_,'_formattercfg_',None)
        return col_formatted_expr(
                    fld,self._fldname(),self._fldtype(),formatter)

    def search(self,other,**kwargs):
        if not hasattr(other,'query') :
            srch = Filter(other)
        clause = self.operate(srch.query)
        return clause

    def nullif(self,v=None) :
        c = self._fld()
        if v is None :
            if hasattr(c,'type') :
                v = nullif_value(type(c.type))

        if v is not None :
            return sqla.func.nullif(c,v)==None
        return c==None

##    def operate(self, op, *other,**kwargs):
##        # determine whether to use exist where
##        type_ = kwargs.pop('type_',None)
##        cast = kwargs.pop('cast',False)
##        scargs = {}
##        for x in ('mixclauses','idcol','version') :
##            if x in kwargs :
##                scargs[x] = kwargs.pop(x)
##        existwhere = kwargs.pop('existwhere',None)
##        return \
##            op(self._fld(),*other,**kwargs)


class _MainComparator(sqla.orm.ColumnProperty.Comparator,commonComparator):
    pass

class _CalculatedComparator(sqla_hybrid.Comparator,commonComparator):
    def operate(self, op, *other,**kwargs):
        return \
            op(self._fld(),
                *other,**kwargs)

class _BaseComparator(sqla_hybrid.Comparator) :
    def __init__(self,cls,name,type_=None) :
        self.cls = cls  # mainbase
        self.name = name
        self.type_= type_
        self.args = getattr(cls,"__comparator_args__",{})
        self.version = self.args.get("version",0)
        self.base= self._base()
        sqla_hybrid.Comparator.__init__(self,self.scalar())

##    @property
##    def default_label(self) :
##        n = self.cls.__tablename__+"_"+self.name
##        if self.version is None :
##            n += '_xx'
##        else :
##            if self.version<0 :
##                n += "_l"+str(-self.version)
##            elif self.version>0 :
##                n += "_"+str(self.version)
##        return n
##
##    def lazy_clause(self,queryobj=None) :
##        lbl = self.default_label
##        if queryobj and 'entities' in queryobj:
##            for ent in queryobject.entities :
##                if lbl==ent.column._label :
##                    return lbl
##        return self.__clause_element__()
##    def __clause_element__(self,querycontainer=None):
##        entities = querycontainer.get
##        return self.query().label(self.default_label)

    def _base(self) :
        raise NotImplementedError()

    def _fldtype(self) :
        fld = self._fld()
        return fld.property.columns[0].type

    def _fldname(self) :
        return self._fld().key

    def _fld(self) :
        raise NotImplementedError()

    def _fldversion(self) :
        return self.base.version

    def _deltaversion(self) :
        return sqla.case(
        [(self._fldversion()==0,0)],
        else_=self._fldversion -self.cls._last_version -1)

    def _cast(self,fld=None,type_=None,cast=True) :
        if fld is None :
            fld = self._fld()
        if type_ is None :
            type_ = self.type_ #self._fldtype()
        if cast=='formatted' or isinstance(cast,dict) :
            if not isinstance(cast,dict) :
                cast = None
            return col_formatted_expr(fld,self._fldname(),type_,cast)
        if not cast :
            return fld
        if type_ not in (sqla.Integer,sqla.Float) :
            return fld
        col = fld.property.columns[0]
        if isinstance(col.type,type_) :
            return fld
        return sqla.cast(fld,type_)

    def _version_clauses(self,**kwargs) :
        clauses = []
        version = kwargs.get('version',self.version)
        if not isinstance(version,(type(None),bool)):
            clauses.append(self._fldversion()==version)
        return clauses

    def _scope_clauses(self,**kwargs) :
        clauses = self._version_clauses(**kwargs)

        id = kwargs.get('idcol',self.cls.id)
        if id is not None :
            clauses += [self.base.parent_id==id]

        mixclauses = kwargs.get('mixclauses')
        if callable(mixclauses):
            mixclauses = mixclauses(self.base)
        if mixclauses :
            clauses += mixclauses

        return  clauses

    def query(self,*args,**kwargs) :
        type_ = kwargs.get('type_')
        mixfunc = kwargs.get('mixfunc')
        cast = kwargs.get('cast',False)
        if not mixfunc and args :
            mixfunc = args[0]
        if isinstance(mixfunc,basestring) :
            mixfunc = getattr(sqla.func,mixfunc)
        clauses = self._scope_clauses(**kwargs)
        clause = sqla.and_(*clauses)

        fld = self._cast(type_=type_,cast=cast)
        if callable(mixfunc) :
            fld = mixfunc(fld)
        if not isinstance(fld,(list,tuple)):
            fld = [fld]
        q = sqla.select(fld,clause)

        return q

    def scalar(self,*args,**kwargs) :
        return self.query(*args,**kwargs).as_scalar()

    def search(self,other,**kwargs):
        if not hasattr(other,'query') :
            other = Filter(other)
        clause = self.operate(other.query,existwhere=True,**kwargs)
        if other._exp=='' :
            clause = sqla.not_(clause)
            xother = Filter(None)
            xclause = self.operate(xother.query,existwhere=True,**kwargs)
            if xclause is not None :
                clause = sqla.or_(clause,xclause)
        return clause

    def nullif(self,v=None,**kwargs) :
        if v is None :
            v = nullif_value(self.name) # (self.cls._model_.fld_dbtype(self.name))
        if v is not None :
            qs = self._scope_clauses(**kwargs) \
                    +[sqla.func.nullif(self._cast(),v)==None]
            clause = sqla.and_(*qs)
            if len(qs)>1: clause = clause.self_group()
            return clause
        return self.operate(self.__eq__,None)

    def as_formatted(self,formatter=None):
        if formatter in (None,True):
            formatter = getattr(self.cls._model_,'_formattercfg_',None)
        return col_formatted_expr(
            self._fld(),self._fldname(),self._fldtype(),formatter)

    def operate(self, op, *other,**kwargs):
        # determine whether to use exist where
        type_ = kwargs.pop('type_',None)
        cast = kwargs.pop('cast',False)
        scargs = {}
        for x in ('mixclauses','idcol','version') :
            if x in kwargs :
                scargs[x] = kwargs.pop(x)
        existwhere = kwargs.pop('existwhere',None)
        if existwhere is None :
            oprs = sqla.sql.operators
            existwhere = \
                oprs.is_precedent(op,oprs.eq) \
                and not oprs.is_precedent(op,oprs.exists) \
                and op != oprs.distinct_op
        if existwhere :
            qs = self._scope_clauses(**scargs)

            qs.append(op(self._cast(cast=cast),*other,**kwargs))
            clause = sqla.and_(*qs)
            if len(qs)>1 :
                clause = clause.self_group()
            return sqla.sql.exists("1").where(clause)

        return \
            op(self.scalar(type_=type_,cast=cast,**scargs),
                *other,**kwargs)


class _VerComparator(_BaseComparator):
    def _base(self) :
        base = self.args.get('verbase')
        if base is None :
            base = self.cls._model_.verbase
            if self.version is None or self.version!=0 :
                base = self.cls._model_.verxbase
            base = sqla.orm.aliased(base)
        return base

    def _fld(self) :
        return getattr(self.base,self.name)


class _FldComparator(_BaseComparator):
    def __init__(self,cls,name,*args,**kwargs) :
        name,self.dimension = attr_name_dimension(name,kwargs.pop('dimension',[]))
        _BaseComparator.__init__(self,cls,name,*args,**kwargs)

    def _base(self) :
        base = self.args.get('fldbase')
        if base is None :
            base = self.cls._model_.fldbase
            if self.version is None or self.version!=0 :
                base = self.cls._model_.fldxbase
            base = sqla.orm.aliased(base)
        return base

    def _fldtype(self) :
        return self.cls._model_._fld_dbtype(self.name,*self.dimension)

    def _fld(self) :
        return self.base.value

    def _fldname(self) :
        n = self.name
        d = ','.join(self.dimension)
        if d :
            n += '.'+d
        return n

    def _cast(self,fld=None,type_=None,cast=True) :
        if type_ is None :
            type_ = self._fldtype()
        return _BaseComparator._cast(self,fld,type_,cast=cast)

    def _version_clauses(self,**kwargs) :
        clauses = []
        version = kwargs.get('version',self.version)
        if not isinstance(version,(type(None),bool)):
            if isinstance(version,int) and version==0 :
                clauses.append(self._fldversion()==version)
            else :
                xq = self.base.best_version(
                        self.base.name, version,
                        self.base.parent_id, self.base.dimension_key,
                        )
                clauses.append(self._fldversion()==xq.label(None))
        return clauses

    def _scope_clauses(self,**kwargs) :
        clauses = _BaseComparator._scope_clauses(self,**kwargs)
        if self.name:
            clauses.append(self.base.name==self.name)
        if self.dimension :
            if len(self.dimension)==1 :
                clauses.append(self.base.dimension_key==self.dimension[0])
            else :
                clauses.append(self.base.dimension_key.in_(self.dimension))
        return clauses

class _AnyBase(object) :
    def __init__(self,*args,**kwargs) :
        settings = {}
        if len(args)==1 and isinstance(args[0],dict) :
            settings.update(args[0])
        else :
            cols = schema_columns(self)
            for c in getattr(self,'_skip_seqinit_',[]):
                if c in cols : cols.remove(c)
            for i in xrange(len(args)):
                settings[cols[i]] = args[i]
        settings.update(kwargs)
        self.set_data(settings)

    @classmethod
    def metabase(cls,alias=None) :
        b = cls
        if alias not in (None,False) :
            b = sqla.orm.aliased(cls) if alias is True else alias
        return b

    def set_data (self,data):
        for k in data :
            if hasattr(self,k) :
                setattr(self,k,data[k])
            else:
                raise AttributeError(
                    "no column '{0}' in {1}".format(k,type(self)))
    def __repr__(self) :
        name = self.__class__.__name__
        cols = getattr(self,"_reprcols_",None) or schema_columns(self)
        mode = getattr(self,"_reprmode_",None)
        if mode :
            if mode == "short" :
                r = "(" \
                    +", ".join(repr(getattr(self,c)) for c in cols) \
                    + ")"
            else :
                r = mode.format(*tuple(getattr(self,c) for c in cols))
        else :
            r = "{" \
                +", ".join("\'"+c+"\': "+repr(getattr(self,c)) for c in cols) \
                + "}"
        return "<{0}{1}>".format(name,r)

    @classmethod
    def _selcol(cls,name,cast=True):
        if name :
            col = getattr(cls,name)
            t = col.property.columns[0].type
            if cast=='formatted' or isinstance(cast,dict) :
                if not isinstance(cast,dict) :
                    cast = None
                return col_formatted_expr(col,name,t_,cast)
            return col
        return None
    @classmethod
    def _searchcols(cls):
        return list(cls.__table__.c)

    @staticmethod
    def _decorterm(col,term):
        if term is not None and isinstance(term,basestring) :
            if term=='*' or term.endswith('**') :
                tlen = len(term)
                col = sqla.func.substr(col,1,tlen) + '*'
        return col

    @classmethod
    def _singlesearch(cls,term,c=None,colnamed=None,**kwargs) :
        cast = kwargs.pop('formatter',None) or 'formatted'
        if isinstance(c,basestring) and '-' in c :
            c,term = c.split('-',1)
        if not c:
            return cls.search(term,cls._searchcols(),cast=cast,**kwargs)
        if colnamed :
            c = colnamed(c,'filter')
        if c :
            c = cls._selcol(c,cast=False)
            if hasattr(c,'search') :
                return c.search(term,cast=cast,**kwargs)

            if not isinstance(term,Filter) :
                term = Filter(term)
            return term.query(c)
        return None

    @classmethod
    def search(cls,term,cols=None,**kwargs) :
        '''
        cols
            - a string for single fieldname
            - python tuple or list of fieldnames
            - a string with comma seperate for list of fieldnames
                name1,name2,...
            - json string for list of fieldnames,fieldname-term,operand ['or','and','nor','nand']
                ["name1","name2",...]
                ["name1","name2-term2",...]
                ["and","name1","name2-term2",...]
            - json string for dict of fieldname:term pair
                {"name1":"term1","name2":"term2"}
        optional argument :
            colnamed - pass through for _singlesearch
            idcol - pass through for _singlesearch
            version - pass through for _singlesearch

        '''
        if not cols:
            return cls._singlesearch(term,**kwargs)

        if isinstance(cols,basestring) :
            cols = json_loads(cols,True)

        if isinstance(cols,dict) :
            qlst = []
            for c,t in cols.iteritems() :
                if t is None :
                    t = term
                q = cls._singlesearch(t,c,**kwargs)
                if q is not None :
                    qlst.append(q)
            return sqla.and_(*qlst)

        if isinstance(cols,(list,tuple)) :
            qlst = []
            op = None
            for c in cols :
                if not c :
                    continue
                if isinstance(c,basestring) :
                    if c.lower() in ['or','and','nor','nand'] :
                        c = c.lower()
                        if op != c :
                            if qlst and op is not None:
                                q = sqla.and_(*qlst) \
                                    if op in ['and','nand'] else \
                                    sqla.or_(*qlst)
                                if op in ['nand','nor'] :
                                    q = sqla.not_(q)
                                qlst= [q]
                            op = c
                        continue
                    q = cls._singlesearch(term,c,**kwargs)
                    if q is not None :
                        qlst.append(q)
                else :
                    if not isinstance(term,Filter) :
                        term = Filter(term)
                    q = term.query(c)
                    if q is not None :
                        qlst.append(q)
            if qlst :
                q = sqla.and_(*qlst) \
                        if op in ['and','nand'] else \
                        sqla.or_(*qlst)
                if op in ['nand','nor'] :
                    q = sqla.not_(q)
                return q
            return None

        # otherwise: cols may be Column, literal etc.
        if not isinstance(term,Filter) :
            term = Filter(term)
        return term.query(cols)

    @classmethod
    def select(cls,name,*args,**kwargs):
        label = kwargs.get('label')
        mixclauses = kwargs.get('mixclauses')
        #mixfunc = kwargs.get('mixfunc')
        alias = kwargs.get('alias')
        decorfunc = kwargs.get('decorfunc')
        formatter = kwargs.get('formatter')
        term = kwargs.get('term') or None
        mixselect = kwargs.get('mixselect')
        leftmixselect = kwargs.get('leftmixselect')
        order_by = kwargs.get('order_by')
        oterms = None
        if isinstance(term,(list,tuple)):
            oterms = term
            term = term[0]

        base = cls.metabase(alias)
        clauses = []
        if callable(mixclauses) :
            mixclauses = mixclauses(base)
        if mixclauses :
            clauses += mixclauses
        termcol = col = name
        if isinstance(name,basestring):
            col = base._selcol(name)
            termcol = base._selcol(name,cast=False)
        if isinstance(termcol,(sqla.sql.ColumnElement,sqla.orm.attributes.QueryableAttribute)):
            if formatter :
                n,d = attr_name_dimension(name)
                t = base._model_._fld_dbtype(n,*d)
                if formatter in (None,True) :
                    formatter = getattr(base._model_,'_formattercfg_',None)
##                    if hasattr(fld,'_annotations') :
##                        class_ = fld._annotations['parentmapper'].class_
##                    else :
##                        class_ = fld.class_
##                    formatter = getattr(class_._model_,'_formattercfg_',None)
                col = col_formatted_expr(termcol,name,t,formatter)
            if callable(decorfunc) :
                col = decorfunc(col,term)
            else :
                col = base._decorterm(col,term)
            if label :
                col = col.label(label)

            if oterms :
                tcol = termcol
                for t in oterms :
                    if callable(t) :
                        t = t(tcol)
                    else :
                        if isinstance(t,basestring):
                            ts = '*' * t.count('*')
                            while (len(ts)>1) :
                                t = t.replace(ts,'*')
                                ts = ts[1:]
                            t = Filter(t) if t and t != '*' else None
                        if hasattr(t,'query') :
                            t = t.query(tcol)
                    if t is not None:
                        clauses.append(t)

        def _mixsel(mixer) :
            if not mixer :
                return []
            if callable(mixer) :
                mixer = mixer(base)
            if isinstance(mixer,basestring):
                mixer = mixer.split(',')
            sels = []
            for c in mixer :
                if callable(c):
                    c = c(base)
                if isinstance(c,basestring) :
                    c = getattr(base,c,sqla.sql.literal(c))
                sels.append(c)
            return sels

        if col is None :
            col = base
        if hasattr(col,'__table__') :
            col = list(col.__table__.c)
        else :
            if not isinstance(col,(tuple,list)) :
                col = [] if col in ('',False) else [col]
        if leftmixselect :
            col = _mixsel(leftmixselect) + col
        if mixselect :
            col += _mixsel(mixselect)

        clauses = sqla.and_(*clauses) if clauses else None
        q = sqla.select(col,clauses) if col else clauses
        if col :
            if callable(order_by) :
                order_by = order_by(base)
            if order_by :
                if isinstance(order_by,basestring) :
                    order_by = order_by.split(',')
                if isinstance(order_by,(list,tuple)) :
                    ords = []
                    for o in order_by :
                        if isinstance(o,basestring) :
                            o,d = o.split(' ')
                            o = getattr(base,o)
                            if d=='desc' : o = o.desc()
                        ords.append(o)
                    if ords :
                        q = q.order_by(ords)
        return q

    @classmethod
    def scalar(cls,*args,**kwargs) :
        if 'alias' not in kwargs:
            kwargs['alias'] = True
        return cls.select(*args,**kwargs).as_scalar()

class _VerAnyBase(_AnyBase) :
    parent_id = sqla.Column(sqla.Integer,
                primary_key = True)
    version = sqla.Column(sqla.Integer,
                primary_key = True, default = 0)
    _skip_seqinit_ = ['parent_id','version']
    #__inherit_on__ = "version"
    __inherit_id__ = None

    def __init__(self,*args,**kwargs) :
        inherit = getattr(self,'__inherit_on__',None)
        if inherit :
            cls = type(self)
            cls.__mapper_args__ = {'polymorphic_on': getattr(cls,inherit)}

        _AnyBase.__init__(self,*args,**kwargs)

    @classmethod
    @property
    def is_inherit(cls) :
        return 'polymorphic_identity' in getattr(cls,"__mapper_args__",{})

    @classmethod
    def _searchcols(cls):
        cols = []
        for c in schema_columns(cls) :
            if c in ('parent_id','version') :
                continue
            cols.append(getattr(cls,c))
        return cols

    @classmethod
    def select(cls,name,version=0,id=None,**kwargs):
        kwargs['alias'] = base = cls.metabase(kwargs.get('alias'))
        q = _AnyBase.select(name,**kwargs)
        clauses = []
        if id is not None :
            clauses.append(base.parent_id==id)
        if version is not None :
            clauses.append(base.version==version)
        if clauses :
            q = q.where(sqla.and_(*clauses))
        return q

class _VerBase(_VerAnyBase) :
    logged_time = sqla.Column(sqla.DateTime,
        default = sqla.func.current_timestamp())
    logged_user = sqla.Column(sqla.String)
    accessability = sqla.Column(sqla.String)
    invalidity = sqla.Column(sqla.String)

class _FldBase(_VerAnyBase) :
    name = sqla.Column(sqla.String, primary_key = True)
    dimension_key = sqla.Column(sqla.String, primary_key = True, default='')
    dimension_idx = sqla.Column(sqla.Integer, primary_key = True, default=0)
    value = sqla.Column(sqla.String)
    _reprcols_ = ["version","name","value","dimension_key","dimension_idx",]
    _reprmode_ = "({0},{3},{4}) {1} = {2!r}"

    @classmethod
    def best_version(cls,name,version,id,dimension='',**kwargs) :
        base = sqla.orm.aliased(cls) #self.metabase(self,kwargs.get('alias',True))
        name,dimension = attr_name_dimension(name,dimension)
        cc =[
            base.version>=version,
            base.parent_id==id,
            ]
        if name :
            cc.append(base.name==name)
        if dimension :
            if len(dimension)==1 :
                cc.append(base.dimension_key==dimension[0])
            else:
                cc.append(base.dimension_key.in_(dimension))
        clause = sqla.and_(*cc)
        correlate = []
        for c in (version,id,name,dimension) :
            if isinstance(c,sqla.orm.attributes.QueryableAttribute) :
                t = getattr(c.class_,'_AliasedClass__alias',
                        getattr(c.class_,'__table__',None))
                if t is not None and t not in correlate :
                    correlate.append(t)
        q = sqla.select(
                [sqla.func.ifnull(sqla.func.min(base.version),0)],
                clause,
                )
        if correlate :
            q = q.correlate(*correlate)
        return q

    @classmethod
    def _selcol(cls,name,cast=True):
        col = cls.value
        if name :
            n,d = attr_name_dimension(name)
            t = cls._model_._fld_dbtype(n,*d)
            if cast=='formatted' or isinstance(cast,dict) :
                if not isinstance(cast,dict) :
                    cast = None
                return col_formatted_expr(col,name,t_,cast)

            if cast \
                and t != col.property.columns[0].type \
                and t in (sqla.Integer,sqla.Float) :
                col = sqla.cast(col,t)
        return col

    @classmethod
    def _singlesearch(cls,term,c=None,colnamed=None,**kwargs) :
        cast = kwargs.pop('formatter',None) or 'formatted'
        if isinstance(c,basestring) and '-' in c :
            c,term = c.split('-',1)
        if not c:
            if not isinstance(term,Filter) :
                term = Filter(term)
            return term.query(cls._selcol(None,cast=cast,**kwargs))
        if colnamed :
            c = colnamed(c,'filter')
        n,d = attr_name_dimension(c)
        if n :
            q = [cls.name==n]
            if d :
                if len(d)==1 :
                    q.append(cls.dimension_key==d[0])
                else :
                    q.append(cls.dimension_key.in_(d))
            if not isinstance(term,Filter) :
                term = Filter(term)
            q.append(term.query(cls._selcol(c,cast=cast,**kwargs)))
            return sqla.and_(*q)
        return None

    @classmethod
    def select(cls,name,version=0,id=None,*args,**kwargs) :
        fixver = kwargs.pop('fixver',None)
        kwargs['alias'] = base = cls.metabase(kwargs.get('alias'))
        q = _VerAnyBase.select(
                    name,version=None,id=id,*args,**kwargs)
        n,d = attr_name_dimension(name) if '.' in name else (name,None)
        clauses = [base.name==n]
        if d :
            if len(d)==1 :
                clauses.append(base.dimension_key==d[0])
            else :
                clauses.append(base.dimension_key.in_(d))
        if version is not None :
            if version==0 or fixver :
                #fixver = True
                clauses.append(base.version==version)
            else :
                xq = base.best_version(
                        base.name, version,
                        base.parent_id, base.dimension_key,
                    ).label(None)
                clauses.append(base.version==xq)
        q = q.where(sqla.and_(*clauses))
        return q

class _MainBase(_AnyBase) :
    id = sqla.Column(sqla.Integer, primary_key=True)
    _skip_seqinit_ = ['id']

    @dfields_hybrid_property
    def dfields(self) : # dynamic fields
        if not hasattr(self,'_dfields') :
            self._dfields = _DynamicFlds(self)
        return self._dfields
    @dfields.comparator
    def dfields(cls,name='',*args,**kwargs) : # dynamic fields
        if hasattr(cls,name) :
            return getattr(cls,name)
        return _FldComparator(cls,name,*args,**kwargs)

    def set_data(self,data) :
        for k in data :
            if hasattr(self,k) :
                setattr(self,k,data[k])
            else :
                kn = k
                n,dim = attr_name_dimension(k)
                if hasattr(self,n) :
                    for arg in self._model_._dynamicflds_args:
                        if n == self._model_.named("dynamicfld",arg['name']):
                            kn = arg['name']+'.'+','.join(dim)
                            break
                self.dfields.set_fld(kn,data[k])

    @classmethod
    def v(cls,*args,**kwargs):
        # comparator control parameter
        args = list(args)
        for k in ('version','verbase','fldbase') :
            if not args:
                break
            kwargs[k] = args.pop(0)

        if kwargs:
            args = {}
            args.update(getattr(cls,'__comparator_args__',kwargs))
            cls.__comparator_args__ = args

        return cls

    @classmethod
    def j(cls,version=True,validity=True,*args,**kwargs):
        def bypass(qry):
            return qry

        def transform(qry):
            if verbase :
                qry = qry.join(verbase,verclause)
            if fldbase :
                qry = qry.join(fldbase,fldclause)
            return qry

        args = list(args)
        for v in ('verbase','fldbase'):
            if not args:
                break
            kwargs[k] = args.pop(0)

        if not hasattr(cls,'__comparator_args__') :
            setattr(cls,'__comparator_args__',{})

        cmp_args = getattr(cls,'__comparator_args__')

        if version is True :
            if version not in cmp_args :
                cmp_args['version'] = None
            if cmp_args.get('version',0) is None :
                version = 0

        if version is False :
            cmp_args['version'] = None
            version = None

        if validity is None and version is None :
            return bypass

        if version not in cmp_args :
            cmp_args['version'] = None if version >= 0 else True

        verbase = kwargs.get('verbase',True)
        verclause = None
        if isinstance(verbase,sqla.sql.ClauseElement):
            verclause,verbase = (verbase,True)
        if isinstance(verbase,(list,tuple)):
            verbase,verclause = verbase
        if verbase is True:
            verbase = cmp_args.get('verbase',cls._model_.verbase)
        elif verbase :
            cmp_args['verbase'] = verbase

        fldbase = kwargs.get('fldbase',True)
        fldclause = None
        if isinstance(fldbase,sqla.sql.ClauseElement):
            fldclause,fldbase = fldbase,True
        if isinstance(fldbase,(list,tuple)):
            fldclause,fldbase = fldbase[1],fldbase[0]
        if fldbase is True:
            fldbase = cmp_args.get('fldbase',cls._model_.fldbase)
        elif fldbase :
            cmp_args['fldbase'] = fldbase

##        if cmp_args != getattr(cls,'__comparator_args__',{}) :
##            setattr(cls,'__comparator_args__',cmp_args)

        named = cls._model_.named
        if not verclause :
            clauses = getattr(cls,named('versionfld','invalidity')) \
                    ._version_clauses(version)
            q = None
            if validity is True :
                q = (verbase.invalidity==None)
            elif validity is False :
                q = (verbase.invalidity!=None)
            elif isinstance(validity,basestring):
                q = Filter(validity).query(verbase.invalidity)
            if q is not None:
                clauses.append(q)
            verclause = sqla.and_(
                cls.id==verbase.parent_id,
                *clauses)

        if not fldclause :
            c = cls._model_._dynamicflds_args[0]['name']
            fldclause = sqla.and_(
                cls.id==fldbase.parent_id,
                *getattr(cls,cls._model_.named('dynamicfld',c)) \
                    ._version_clauses(version))

        return transform


    @property
    def cfields(self): # child fields
        if not hasattr(self,'_chfields') :
            self._chfields = _ChildFlds(self)
        return self._chfields

    @classmethod
    def _selcol(cls,name,cast=True):
        if name :
            n,d = attr_name_dimension(name)
            col = getattr(cls,n)
            if d :
                col = col.dim(*d)
            if (cast or isinstance(cast,dict)) \
                and hasattr(col,'_cast') : # hybrid comparator
                return col.scalar(cast=cast)

            t = cls._model_._fld_dbtype(n,*d)
            if cast=='formatted' or isinstance(cast,dict) :
                if not isinstance(cast,dict) :
                    cast = None
                return col_formatted_expr(col,name,t_,cast)
            if cast and t in (sqla.Integer,sqla.Float) :
                if not hasattr(col,'property') \
                    or t != col.property.columns[0].type :
                    col = sqla.cast(col,t)
            return col
        return None

    @classmethod
    def _searchcols(cls):
        cols = []
        for c in schema_columns(cls) :
            if c in ('id','parent_id'):
                continue
            cols.append(getattr(cls,c))
        for arg in cls._model_._dynamicflds_args :
            n,d = attr_name_dimension(arg['name'])
            if not d :
                n = cls._model_.named('dynamicfld',n)
                c = getattr(cls,n)
                cols.append(c)
        for arg in cls._model_._dynamicflds_args :
            n,d = attr_name_dimension(arg['name'])
            if d :
                n = cls._model_.named('dynamicfld',n)
                c = getattr(cls,n)
                if c not in cols :
                    cols.append(c.dim(*d))
        return cols

    @classmethod
    def select(cls,name,version=0,id=None,**kwargs):
        model = cls._model_
        mixclauses = kwargs.pop('mixclauses',[])
        descriptors = kwargs.pop('descriptors',[])
        if callable(descriptors) :
            descriptors = descriptors(name)
        if isinstance(descriptors,dict) :
            descriptors = descriptors.get(name)
        if isinstance(descriptors,basestring):
            descriptors = descriptors.split(',')
        formatter = kwargs.get('formatter')
        alias = kwargs.pop('alias',None)
        decorfunc = kwargs.pop('decorfunc',None)
        mcols = schema_columns(cls)
        vcols = schema_columns(model.verbase)
        def _arrange_scopes(_sc) :
            if not _sc :
                return None
            ret = {'m' : {},'v' : {},'d' :{},}
            for c,t in _sc.iteritems() :
                g = 'd'
                if c in mcols :
                    g = 'm'
                elif c in vcols :
                    g = 'v'
                ret[g][c] = t
            return ret
        vxscopes = _arrange_scopes(kwargs.get('scopes'))
        v0scopes = _arrange_scopes(kwargs.get('v0scopes'))

        def _clause(_col,_t,) :
            _t = _unicode(_t)
            if _t or _t is None:
                return _t(_col) if callable(_t) else (_col==_t)
            return sqla.func.nullif(_col,_t)==None

        def _scope_clauses(_base,_idcol,_vercol,_basescopes,_xbasescopes):
            cs = []
            for base,scopes in _basescopes.iteritems() :
                for c,t in scopes.iteritems():
                    t = _clause(getattr(base,c),t)
                    if t is not None :
                        cs.append(t)
            for base,scopes in _xbasescopes.iteritems() :
                for c,t in scopes.iteritems():
                    t = _clause(base.scalar(c,_vercol,_idcol),t)
                    if t is not None :
                        cs.append(t)
            return cs

        def _decor(_idcol,_vercol,_base=None,_schcols=None) :
            def func(col,term) :
                if callable(decorfunc) :
                    col = decorfunc(col,term)
                if not descriptors :
                    if not callable(decorfunc) :
                        col = cls._decorterm(col,term)
                    return col
                ks = {}
                if formatter :
                    ks['formatter'] = formatter
                _cnt = 0
                for c in descriptors :
                    if not c :
                        continue
                    if _base is not None and c in _schcols :
                        c = getattr(_base,c)
                        if formatter :
                            c = c.as_formatted(**ks)
                    else :
                        c = cls.scalar(c,_vercol,_idcol,**ks)
                    if _cnt==0 and not formatter:
                        col = sqla.literal('')+col
                    col = col + sqla.literal('|| ' if _cnt==0 else ', ') + sqla.func.ifnull(c,'-')
                    _cnt += 1
                return col
            return func
        #mbase = cls
        #if name is None :
        mbase = cls.metabase(alias)
        if name in mcols or name is None or name==cls :
            if name==cls :
                name = None

            base = mbase
            qlst = []

##            if version is None or version<=0 :
##                base = cls.metabase(alias)
            clauses = []
            if vxscopes :
                clauses.extend(_scope_clauses(
                        base, base.id, version,
                        {base:vxscopes['m']},
                        {model.verbase: vxscopes['v'], model.fldbase: vxscopes['d']},
                        ))

            if v0scopes :
                clauses.extend(_scope_clauses(
                        base, base.id, 0,
                        {base:v0scopes['m']},
                        {model.verbase: v0scopes['v'], model.fldbase: v0scopes['d']},
                        ))
            if mixclauses :
                t = mixclauses
                if callable(mixclauses) :
                    t = mixclauses(base)
                if t :
                    clauses.extend(t)

            if id is not None :
                clauses.insert(0,base.id==id)

            q = _AnyBase.select(
                    name,
                    mixclauses=clauses,alias=base,
                    decorfunc=_decor(base.id,version,base,mcols),
                    **kwargs)

            if version==0 or name is None:
                return q
            fldbase = model.fldbase
            if alias :
                fldbase = sqla.orm.aliased(fldbase)

            clauses = []
            if vxscopes :
                cversion = version if version==0 or version is None else fldbase.version
                clauses.extend(_scope_clauses(
                        fldbase, fldbase.parent_id, cversion,
                        {},
                        {fldbase: vxscopes['m'], model.verbase: vxscopes['v'], fldbase: vxscopes['d']},
                        ))
            if v0scopes :
                clauses.extend(_scope_clauses(
                        fldbase, fldbase.parent_id, 0,
                        {},
                        {fldbase: v0scopes['m'], model.verbase: v0scopes['v'], fldbase: v0scopes['d']},
                        ))

            if callable(mixclauses) :
                t = mixclauses(fldbase)
                if t :
                    clauses.extend(t)
            return q.union(
                    fldbase.select(
                        name+'.', version, id,
                        mixclauses=clauses, alias=fldbase,
                        decorfunc=_decor(fldbase.parent_id,fldbase.version),
                        **kwargs))

        # verbase ---------------------
        if name==model.verbase :
            name = None
        nn = name
        if isinstance(name,basestring):
            for c in model.verbase.__table__.c :
                if isinstance(c,sqla.Column) \
                    and c.name not in ("parent_id","version") :
                    if name == model.named("versionfld",c.name):
                        nn = c.name
                        break
        if nn in vcols or name is None :
            base = model.verbase.metabase(alias)
            clauses = []
            if vxscopes :
                cversion = version if version==0 else base.version
                clauses.extend(_scope_clauses(
                        base, base.parent_id, cversion,
                        {base:vxscopes['v']},
                        {cls: vxscopes['m'], model.fldbase: vxscopes['d']},
                        ))
            if v0scopes :
                clauses.extend(_scope_clauses(
                        base, base.parent_id, 0,
                        {base:v0scopes['v']},
                        {cls: v0scopes['m'], model.fldbase: v0scopes['d']},
                        ))
            if mixclauses :
                t = mixclauses
                if callable(mixclauses) :
                    t = mixclauses(base)
                if t :
                    clauses.extend(t)
            print 'verbase query =',base.select(
                    nn, version, id,
                    mixclauses=clauses, alias=base,
                    decorfunc=_decor(base.parent_id,base.version,base,vcols),
                    **kwargs)
            return base.select(
                    nn, version, id,
                    mixclauses=clauses, alias=base,
                    decorfunc=_decor(base.parent_id,base.version,base,vcols),
                    **kwargs)
        # fldbase ------------------
        if name==model.fldbase :
            name = ''
        nn,d = attr_name_dimension(name)
        for arg in model._dynamicflds_args:
            n = attr_name_dimension(arg['name'])[0]
            if nn == model.named("dynamicfld",n) :
                nn = n
                break ;

        base = model.fldbase.metabase(alias)
        clauses = []
        if vxscopes :
            cversion = version if version==0 else base.version
            clauses.extend(_scope_clauses(
                    base, base.parent_id, cversion,
                    {},
                    {cls: vxscopes['m'], model.verbase: vxscopes['v'], model.fldbase: vxscopes['d']},
                    ))
        if v0scopes :
            clauses.extend(_scope_clauses(
                    base, base.parent_id, 0,
                    {},
                    {cls: v0scopes['m'], model.verbase: v0scopes['v'], model.fldbase: v0scopes['d']},
                    ))
        if mixclauses :
            t = mixclauses
            if callable(mixclauses) :
                t = mixclauses(base)
            if t :
                clauses.extend(t)

        if d :
            nn += '.'+','.join(d)
        return base.select(
                nn, version, id,
                mixclauses=clauses, alias=base,
                decorfunc=_decor(base.parent_id,base.version),
                **kwargs)


class _ChildBase(_MainBase):
    parent_id = sqla.Column(sqla.Integer,nullable=False,index=True)
    parent_entity = sqla.Column(sqla.String,nullable=False,index=True)
    #dimension_key = sqla.Column(sqla.String,index=True,default='')
    #dimension_idx = sqla.Column(sqla.Integer,index=True,default=0)
    _skip_seqinit_ = _MainBase._skip_seqinit_ + ['parent_id']

    def __repr__(self) :
        name = self.__class__.__name__
        return "<{0}({1!r}){2}>".format(name,str(self.parent_entity),self.dfields.data())


class _Model(object) :
    re_nonnamed = re.compile('[^a-zA-Z0-9_]')
    re_oldverphase = re.compile(r'[<][<]((?:[^>]|[>](?![>]))*)[>][>]')
    def __init__ (self,**kwargs) :
        '''
            echo : False
            tbame : 'main'
            dbpath : 'sqlite://'
            degbug : False
            quiet : False
            user : None
            session : auto
            ormbase : auto


        '''
        self.debug= kwargs.get("debug",False)
        self.quiet= kwargs.get("quiet",False)
        self.echo_("debug: {0}",self.debug)
        self.user_id = kwargs.get("user")
        self.Session = kwargs.get("session") \
            or sqla.orm.scoped_session(sqla.orm.sessionmaker())

        self.lazy = kwargs.get("lazy") \
            or getattr(self,"_lazy_",None) \
            or 'subquery'

        #Base = sqla_declarative_base()
        self.ormbase = kwargs.get("ormbase") \
            or getattr(self,"_ormbase_",None) \
            or sqla_Base

        # ---- initialize engine
        if not self.engine :    # engine = self.ormbase.metadata.bind
            dbecho = kwargs.get("echo",self.debug)
            dbpath = kwargs.get("dbpath") or getattr(self,"_dbpath_",None) or "sqlite://"
            self.echo_("dbecho: {0}",dbecho)
            self.echo_("dbpath: {0}",dbpath)
            self.engine = sqla.create_engine(dbpath,echo=dbecho)

        usechild = hasattr(self,'_childflds_')
        #mapper = sqla.orm.mapper #sqla_session_mapper(self.Session)

        self.orms= {}
        # main mapper
        mainbase = kwargs.get("mainbase") \
            or getattr(self,"_mainbase_",None) \
            or type(
                kwargs.get("tablename")
                or getattr(self,'__tablename__',None)
                or self.named("main"),(_MainBase,),{})
        tbname = kwargs.get("tablename") \
            or getattr(mainbase,"__tablename__",None) \
            or getattr(self,'__tablename__',None) \
            or self.named("main")
        clsname = mainbase.__name__
        attrs = {
            "__tablename__":tbname
            }
        bases = (mainbase,self.ormbase)
        if issubclass(mainbase,self.ormbase) :
            bases = (mainbase,)
        mainbase = type(clsname,bases,attrs)
        # post initialize attribute
        mainbase._model_= self
        self.orms["main"] = mainbase #.__mapper__
        self.__class__.mainbase = property(lambda cls: cls.orms["main"])

        # append custom + static main column
        for c in self.cols_main():
            mainbase.__table__.append_column(c)
        # override default comparator to support qsearch and nullif
        for c in mainbase.__table__.c :
            n = c.name
            c = sqla.orm.column_property(c,comparator_factory=_MainComparator)
            setattr(mainbase,n,c)

        # single table inheritance
        # http://www.sqlalchemy.org/docs/orm/extensions/declarative.html#single-table-inheritance

        # ver mapper
        verbase = kwargs.get("verbase") \
            or getattr(self,"_verbase_",None) \
            or _VerBase
        n = getattr(verbase,"__tablename__",None) \
            or self.named(tbname+"_ver")
        attrs = {"__tablename__":n,}
        verxbase = type(clsname+"Verx",(verbase,self.ormbase),attrs)
        verxbase._model_= self
        self.orms["verx"] = verxbase #.__mapper__
        self.__class__.verxbase = property(lambda cls: cls.orms["verx"])

        # append custom ver column
        for c in self.cols_ver():
            verxbase.__table__.append_column(c)

        #if 'polymorphic_on' in getattr(verxbase(),"__mapper_args__",{}) :
        if hasattr(verxbase,'__inherit_on__') :
            attrs = {
                "__inherit_on__": None,
                #"__tablename__": None,
                "__mapper_args__": {'polymorphic_identity': 0},
                }
            ver0base = type(clsname+"Ver0",(verxbase),attrs)
        else :
            ver0base = verxbase

        self.orms["ver"] = ver0base #.__mapper__
        self.__class__.verbase = property(lambda cls: cls.orms["ver"])

        # fld mapper
        fldbase = kwargs.get("fldbase") \
            or getattr(self,"_fldbase_",None) \
            or _FldBase
        n = getattr(fldbase,"__tablename__",None) \
            or self.named(tbname+"_fld")
        attrs = {"__tablename__":n,}
        fldxbase = type(clsname+"Fldx",(fldbase,self.ormbase),attrs)
        fldxbase._model_= self
        self.orms["fldx"] = fldxbase #.__mapper__
        self.__class__.fldxbase = property(lambda cls: cls.orms["fldx"])
        # append custom fld column
        for c in self.cols_fld():
            fldxbase.__table__.append_column(c)

        #if 'polymorphic_on' in getattr(fldxbase,"__mapper_args__",{}) :
        if hasattr(fldxbase,'__inherit_on__') :
            attrs = {
                "__inherit_on__": None,
                #"__tablename__": None,
                "__mapper_args__": {'polymorphic_identity': 0},
                }
            fld0base = type(clsname+"Fld0",(fldxbase),attrs)
        else :
            fld0base = fldxbase

        self.orms["fld"] = fld0base #.__mapper__
        self.__class__.fldbase = property(lambda cls: cls.orms["fld"])

        # child mapper
        if usechild :
            childbase = kwargs.get("childbase") \
                or getattr(self,"_childbase_",None) \
                or _ChildBase
            n = getattr(childbase,"__tablename__",None) \
                or self.named(tbname+"_child")
            dflds = []
            for a in self._childflds_args.itervalues() :
                for arg in a :
                    if arg not in dflds :
                        dflds.append(arg)
            childbase._dynamicflds_ = dflds
            childmodel = _Model(
                    mainbase=childbase,
                    tablename=n,
                    ormbase=self.ormbase,
                    session=self.Session,
                    user=self.user,
                    lazy=self.lazy,
                    )
            childbase = childmodel.mainbase
            self.orms["child"] = childbase #.__mapper__
            self.__class__.childbase = property(lambda cls: cls.orms["child"])

        # prepare relation and intregrate child's fields to mainbase property
        self.prepare_relationship()
        self.prepare_versionfld()
        self.prepare_dynamicfld()
        if usechild :
            self.prepare_childfld()
        self.prepare_calculatedfld()

        sqla.event.listen(self.Session, "before_flush", self.before_flush())

        # override default comparator to support qsearch and nullif
        for c in mainbase.__table__.c :
            n = c.name
            c = sqla.orm.column_property(c,comparator_factory=_MainComparator)
            setattr(mainbase,n,c)

        # ---- initialize engine
        #self.metadata = mainbase.metadata
        engine = kwargs.get("engine")
        if not engine :
            echo = kwargs.get("echo") or False
            dbpath = kwargs.get("dbpath") or getattr(self,"_dbpath_",None) or "sqlite://"
            self.engine = sqla.create_engine(dbpath,echo=echo)

    def echo_(self,msg,*fmt) :
        if not self.quiet or self.debug :
            print _unicode(_unicode(msg).format(*fmt))

    def debug_(self,msg,*fmt) :
        if self.debug:
            print "[DEBUG] ",
            self.echo_(msg,*fmt)

    def cast_bind_value(self,dbtype,value):
        if dbtype :
            t = dbtype()
            dialect = self.engine.dialect
            fn = t._cached_bind_processor(dialect)
            if fn is not None:
                value = fn(value)
        return value


    def cast_result_value(self,dbtype,value):
        if dbtype not in (None,sqla.String) and isinstance(value,basestring) :
            t = dbtype()
            dialect = self.engine.dialect
            dt = t #t.dialect_impl(dialect).get_dbapi_type(dialect.dbapi)
            fn = t._cached_result_processor(dialect,dt)
            if fn is not None:
                value = fn(value)
            else :
                if dbtype in (sqla.Integer,sqla.Float):
                    try : value = t.python_type(value)
                    except : pass
        return value
    #return dbtype().python_type(value)

    @property
    def _flds_args(self) :
        if not hasattr(self,'_flds_args_') :
            self._flds_args_ = {}
        return self._flds_args_

    @property
    def _staticflds_args(self) :
        if 'static' not in self._flds_args:
            # compile custom static & dynamic field definitions
            a = getattr(self.mainbase,"_staticflds_",
                    getattr(self,"_staticflds_",[]))
            self._flds_args['static'] = list(parse_column_args(n) for n in a)
        return self._flds_args['static']

    @property
    def _dynamicflds_args(self) :
        if 'dynamic' not in self._flds_args:
            a = getattr(self.mainbase,"_dynamicflds_",
                    getattr(self,"_dynamicflds_",[]))
            self._flds_args['dynamic'] = list(parse_column_args(n) for n in a)
        return self._flds_args['dynamic']

    @property
    def _calculatedflds_args(self) :
        if 'calculated' not in self._flds_args:
            a = getattr(self.mainbase,"_calculatedflds_",
                    getattr(self,"_calculatedflds_",{}))
            self._flds_args['calculated'] = list(parse_column_args(n) for n in a.iterkeys())
        return self._flds_args['calculated']

    @property
    def _childflds_args(self) :
        if 'child' not in self._flds_args:
            args = {}
            for k,a in getattr(self,"_childflds_",{}).iteritems():
                args[k] = list(parse_column_args(n) for n in a)
            self._flds_args['child'] = args
        return self._flds_args['child']

    def flush_dirty(self,session,o):
        if not isinstance(o,self.mainbase): return

##        self.debug_('*** flush dirty {0}',o)
        lastver = getattr(o,self.named("_last_version")) +1
        parent_id = o.id
        changed = False
        # create versioned history
        vo =  getattr(o,self.named("_ver"))
        if vo :
            newver = self.verxbase(version=lastver,parent_id=parent_id)
            for c in schema_columns(vo) :
                if c in ('version','parent_id') :
                    continue
                h = sqla.orm.attributes.get_history(vo,c)
                oldval = h.non_added()[0]
                if c == 'invalidity' :
                    # special case: invalidity
                    # may push status to oldver record via <<some texts....>>
                    # to make oldver's invalidity as incorrect flag
                    # example <<{misspell}>>
                    val = getattr(vo,c)
                    if val :
                        phases = re.split(self.re_oldverphase,val)
                        cv = phases[::2]
                        ov = phases[1::2]
                        if ov :
                            if oldval : oldval += '\n'
                            oldval += '\n'.join(ov)
                            setattr(vo,c,'\n'.join(cv))
                setattr(newver,c,oldval)
            session.add(newver)
            vo.timestamp = sqla.func.current_timestamp()
            #print 'add',vo,newver
            if vo not in session.dirty :
                session.add(vo)

        # tracking dynamic field
        fhis = sqla.orm.attributes.get_history(o,self.named("_flds"))
##        for fo in fhis.non_deleted() :
##            self.debug_('*** _flds non_deleted {0} {1}',fo,fo.parent_id)
##        for fo in fhis.deleted :
##            self.debug_('*** _flds deleted {0} {1}',fo,fo.parent_id)

##            if fo.value is None :
##                sqla.orm.make_transient(fo)
##                continue
##            fo.parent_id = parent_id
##            newfo = self.fldbase(
##                        version=lastver,parent_id=parent_id,
##                        name=fo.name,
##                        dimension_key=fo.dimension_key,dimension_idx=fo.dimension_idx,
##                        )
##            session.add(newfo)
            #print 'add',fo,newfo

        #for fo in fhis.non_added() :
        #for fo in fhis.non_deleted() :
        for fo in fhis.sum() :
            #print parent_id,fo
            newfo = self.fldbase(version=lastver,parent_id=parent_id,)

            ch = False
            for c in schema_columns(fo) :
                if c in ('version','parent_id') :
                    continue
##                if c in ('name','dimension_key','dimension_idx') :
##                    setattr(newfo,c,getattr(fo,c))
##                    continue ;
                h = sqla.orm.attributes.get_history(fo,c)
                oldval = h.non_added()
                if c in ('name','dimension_key','dimension_idx') :
                    if not oldval or not oldval[0] :
                        oldval = h.added

                if oldval :
                    setattr(newfo,c,oldval[0])

                if h.deleted :
                    ch = True
            if ch :
                if fo.parent_id is None :
                    fo.parent_id = parent_id
                session.add(newfo)
                #print 'change',fo,newfo

        # tracking static field
        #print 'tracking static field'
        for c in schema_columns(o) :
            if c in ('id',) :
                continue
            h = sqla.orm.attributes.get_history(o,c)
            oldval = h.deleted
            if oldval :
                changed = True
                newfo = self.fldbase(name=c,value=oldval[0],version=lastver,parent_id=parent_id)
                session.add(newfo)
                #print 'change',c,newfo

        if not changed and o not in session.deleted :
            sqla.orm.make_transient(o)

    def flush_new(self,session,o):
        if not isinstance(o,self.mainbase): return
        #if o._ver is None :
        vercol = self.named("_ver")
        usercol = self.named("versionfld","logged_user")
        ver = getattr(o,vercol)
        if not ver or not getattr(o,usercol) :
            setattr(o,usercol,getattr(session,'user_id',self.user_id))
            if not ver :
                session.add(getattr(o,vercol))

    def flush_deleted(self,session,o):
        if not isinstance(o,self.mainbase): return
        vercol = self.named("_ver")
        ivcol = self.named('versionfld','invalidity')
        if not getattr(o,ivcol) :
            session.expunge(o)
            setattr(o,ivcol,'{delete}')
            session.add(o)
            sqla.orm.attributes.flag_modified(o,vercol)
            return
        # saving all static field, before deleted main
        parent_id = o.id
        lastver = getattr(o,self.named("_last_version"))+1
        for c in schema_columns(o) :
            if c in ('id',) :
                    continue
            h = sqla.orm.attributes.get_history(o,c)
            oldval = h.non_added()
            if oldval :
                newfo = self.fldbase(name=c,value=oldval[0],
                        version=-1,parent_id=parent_id)
                session.add(newfo)
        # create versioned history
        newver = self.verxbase(version=-1,parent_id=parent_id,
                logged_user=getattr(session,'user_id',self.user_id))
        vo =  getattr(o,vercol)
        if vo :
            for c in schema_columns(vo) :
                if c in ('version', 'parent_id', 'logged_user', 'logged_time') :
                    continue
                h = sqla.orm.attributes.get_history(vo,c)
                oldval = h.non_added()[0]
                setattr(newver,c,oldval)
        session.add(newver)

    def flush_dynamicfld_notnull(self,o) :
        if isinstance(o,self.fldbase) and o.version==0 and o.value is None :
            nullable= True
            n = [o.name,o.name+'.'+o.dimension_key]
            for arg in self._dynamicflds_args :
                if arg['name'] in n :
                    nullable = arg.get('nullable',nullable)
                    if arg['name'] == n[1]:
                        break
            if not nullable :
                n = n[0] if n[1][-1]=='.' else n[1]
                raise sqla.orm.exc.FlushError("dynamicfld '{0}' value is None (id={1})".format(n,o.parent_id))

    def flush_dynamicfld_cast(self,o) :
        if isinstance(o,self.fldbase) :
            type_ = self._fld_dbtype(o.name,o.dimension_key)
            try:
                o.value = self.cast_bind_value(type_,o.value)
            except Exception as e:
                raise type(e)(str(e)+' '+str(o))

    def before_flush(self) :
        def listener(session,flush_context, instances) :
            _echo = self.engine.echo
            #self.engine.echo = True
            if self.engine.echo:
                self.debug_("***** before flush '{0}' *****",self.mainbase.__name__)
            mids = []
            if session.dirty :
                for o in session.dirty :
                    if isinstance(o,self.fldbase) \
                        and o.parent_id not in mids :
                            mids.append(o.parent_id)
##            if session.new :
##                for o in session.dirty :
##                    if isinstance(o,self.fldbase) \
##                        and o.parent_id not in mids :
##                            mids.append(o.parent_id)
##
##            if session.deleted :
##                for o in session.dirty :
##                    if isinstance(o,self.fldbase) \
##                        and o.parent_id not in mids :
##                            mids.append(o.parent_id)
            if mids:
                for o in session.dirty :
                    if isinstance(o,self.mainbase):
                        if o.id in mids :
                            mids.remove (o.id)
                for o in session.deleted :
                    if isinstance(o,self.mainbase) :
                        if o.id in mids :
                            mids.remove (o.id)
            if mids :
                for m in session.query(self.mainbase) \
                    .filter(self.mainbase.id.in_(mids)) :
                        sqla.orm.attributes.flag_modified(m,self.named("_flds"))

            # verify type casting dynamicfld value
            for o in session.new:
                self.flush_dynamicfld_notnull(o)
                self.flush_dynamicfld_cast(o)
            for o in session.dirty:
                self.flush_dynamicfld_notnull(o)
                self.flush_dynamicfld_cast(o)

            # verify not null dynamicfld value

            # prepare versioned data
            for o in session.new :
                self.flush_new(session,o)
            for o in session.deleted :
                self.flush_deleted(session,o)
            for o in session.dirty :
                #print "flush dirty",o
                self.flush_dirty(session,o)

            if self.debug :
                bases = (self.mainbase,self.fldbase,self.verbase)
                for o in session.new :
                    if isinstance(o,bases) :
                        if self.engine.echo:
                            self.debug_('+ {0}',o)
                for o in session.deleted :
                    if isinstance(o,bases) :
                        if self.engine.echo:
                            self.debug_('- {0}',o)
                for o in session.dirty :
                    if isinstance(o,bases) :
                        if self.engine.echo:
                            self.debug_('~ {0}',o)
            self.engine.echo = _echo

        return listener

    def prepare_relationship (self) :
        # append foreign key
        main_id = self.mainbase.id
        self.verxbase.__table__.c.parent_id \
            .append_foreign_key(sqla.ForeignKey(main_id))
        self.fldxbase.__table__.c.parent_id \
            .append_foreign_key(sqla.ForeignKey(main_id))
        childbase = None
        if hasattr(self,'childbase') :
            childbase = self.childbase
            childbase.__table__.c.parent_id \
                .append_foreign_key(sqla.ForeignKey(main_id))

        props = {}
        # append relationship
        n = self.named("_ver")
        props[n] = sqla.orm.relationship(
            self.verbase,
            active_history = True,
            lazy=self.lazy,
            passive_deletes = "all",
##            cascade = "all",
            uselist=False,
            primaryjoin = sqla.and_(
                self.verbase.parent_id==self.mainbase.id, self.verbase.version == 0),
            )

        n = self.named("_ver_logs")
        props[n] = sqla.orm.relationship(
            self.verxbase,
            lazy = "dynamic",
            passive_deletes = "all",
##            cascade = "all",
##            active_history = True,
##            primaryjoin = sqla.and_(
##                mainobj.c.id == verobj.c.parent_id, verobj.c.version != 0),
##            order_by = sqla.desc(verobj.c.version),
            )

        n = self.named("_flds")
        props[n] = sqla.orm.relationship(
            self.fldbase,
            active_history = True,
            lazy=self.lazy,
            passive_deletes = "all",
##            cascade = "all",
            primaryjoin = sqla.and_(
                self.fldbase.parent_id==self.mainbase.id, self.fldbase.version == 0),
            #order_by = self.fldbase.name,
            )

        n = self.named("_flds_logs")
        props[n] = sqla.orm.relationship(
            self.fldbase,
            lazy="dynamic",
            passive_deletes = "all",
##            cascade = "all",
##            active_history = True,
##            primaryjoin = sqla.and_(
##                mainobj.c.id == fldobj.c.parent_id, fldobj.c.version != 0),
##            order_by = (sqla.desc(fldobj.c.version), fldobj.c.name),
            )

        n = self.named("_last_version")
        averbase = sqla.orm.aliased(self.verbase)
        props[n] =  sqla.orm.column_property( \
##            sqla.select([sqla.func.count(self.verbase.parent_id)], \
##                self.mainbase.id == self.verbase.parent_id
##                ),
            sqla.select([sqla.func.max(averbase.version)],
                self.mainbase.id == averbase.parent_id,
                ),
            deferred=True, )

        if childbase :
            n = self.named("_children")
            props[n] = sqla.orm.relationship(
                self.childbase,
                active_history = False,
                lazy='dynamic',
                passive_deletes = "all",
                )

            for name in getattr(self,'_childflds_'):
                n = self.named("childfld",name)
                props[n] = sqla.orm.relationship(self.childbase,
                    active_history = False,
                    #lazy=self.lazy,
                    passive_deletes = "all",
                    primaryjoin = sqla.and_(
                        self.childbase.parent_id==self.mainbase.id,
                        self.childbase.parent_entity == name),
                    )

        self.mainbase.__mapper__.add_properties(props)

##        prop = sqla_hybrid.hybrid_property(
##            lambda cls:
##                sqla.select([cls._model_.verbase.version],
##                (self.mainbase.id == self.verbase.parent_id),
##                order_by=self.verbase.version.desc(),
##                limit=1),
##            )
##        setattr(self.mainbase,"_lastversion",prop)


    def prepare_versionfld (self) :
        vercol = self.named("_ver")
        verbase = self.verbase
        def _fget(name):
            def getter(cls) :
                ver  = getattr(cls,vercol)
                if not ver : return None
                return getattr(ver,name)
##                for ver in cls._ver_logs :
##                    if not ver.version :
##                        return getattr(ver,name)
            return getter
        def _fset(name):
            def setter(cls,value) :
                ver  = getattr(cls,vercol)
                if not ver :
                    ver = verbase()
                    setattr(cls,vercol,ver)
                return setattr(ver,name,value)
##                setattr(cls._ver,name,value)
##                for ver in cls._ver_logs :
##                    if not ver.version :
##                        setattr(ver,name,value)
##                        return
##                ver = self.verbase()
##                setattr(ver,name,value)
##                cls._ver_logs.append(ver)
            return setter
        def _comp(name):
            return lambda cls: _VerComparator(cls,name)

        for c in verbase.__table__.c :
            if isinstance(c,sqla.Column) \
                and c.name not in ("parent_id",) :
                #and c.name not in ("parent_id","version") :

                n = self.named("versionfld",c.name)
                if not hasattr(self.mainbase,n):
                    prop = sqla_hybrid.hybrid_property(
                            _fget(c.name),fset=_fset(c.name)
                            )
                    prop = prop.comparator(_comp(c.name))
                    setattr(self.mainbase,n,prop)


    def prepare_dynamicfld (self) :
        def _fget(name,*dimension):
            return lambda cls,*dimension: getattr(cls.dfields,name) \
                if not dimension \
                else cls.dfields.get_fld(name,*dimension)

        def _fset(name):
            return lambda cls,value,*dimension: setattr(cls.dfields,name,value) \
                if not dimension \
                else cls.dfields.set_fld(name,*dimension)

        def _fdel(name):
            return lambda cls,*dimension: delattr(cls.dfields,name) \
                if not dimension \
                else cls.dfields.set_fld(name,None,*dimension)

        def _comp(name,type_):
            return lambda cls,*dimension : \
                    _FldComparator(cls,name,type_,dimension=dimension)

        for arg in self._dynamicflds_args:
            name,type_ = arg["name"],arg["type_"]
            name,dim = attr_name_dimension(name)
            n = self.named("dynamicfld",name)
            if n and not hasattr(self.mainbase,n) :
##                prop = sqla_hybrid.hybrid_property(
##                        _fget(name),fset=_fset(name),fdel=_fdel(name),
##                        )
                prop = dynamicfld_hybrid_property(
                        _fget(name),fset=_fset(name),fdel=_fdel(name),
                        )
                prop = prop.comparator(_comp(name,type_))

                setattr(self.mainbase,n,prop)

    def prepare_calculatedfld(self):
        def _comp(expr) :
            return lambda cls: _CalculatedComparator(expr(cls))

        props = {}
        a = getattr(self.mainbase,"_calculatedflds_",
                getattr(self,"_calculatedflds_",{}))
        for arg in self._calculatedflds_args:
            name,type_ = arg["name"],arg["type_"]
            # add calculate field
            for na in a.iterkeys() :
                if na==name or na.startswith(name+':'):
                    expr = a[na]
                    if callable(expr) :
                        expr = expr(self.mainbase)
                    if isinstance(expr,tuple):
                        fnlst = expr[1:]
                        expr = expr[0]
                        prop = sqla_hybrid.hybrid_property(*fnlst)
                        prop = prop.comparator(_comp(expr))
                        setattr(self.mainbase,name,prop)
                    else :
                        xarg = dict(arg)
                        xarg.pop('name',None)
                        xarg.pop('type_',None)
                        props[name] = sqla.orm.column_property(
                            expr, comparator_factory=_MainComparator,**xarg)
                    break
        if props :
            self.mainbase.__mapper__.add_properties(props)

    def prepare_childfld (self) :
##        def _fget(name):
##            return lambda cls: getattr(cls.cfields,name)
##        def _fset(name):
##            return lambda cls,value: setattr(cls.cfields,name,**value)
##        def _fdel(name):
##            return lambda cls: delattr(cls.cfields,name)
##        def _comp(name):
##            return lambda cls: _ChFldComparator(cls,name)
##
##        for name in getattr(self,'_childflds_',{}):
##            n = self.named("childfld",name)
##            prop = sqla_hybrid.hybrid_property(
##                    _fget(name),fset=_fset(name),fdel=_fdel(name),
##                    )
##            prop = prop.comparator(_comp(name))
##
##            setattr(self.mainbase,n,prop)
        pass

    @classmethod
    def named(self,name,vname=None) :
        """ hook function to change default name."""
        # example:
        # if vname and name=='dynamicfld':
        #     vname = "d_"+vname
        if vname and name=='versionfld':
             vname = "ver_"+vname
        if vname and name=='dynamicfld' :
            # suppress non-named char
            vname = re.sub(self.re_nonnamed,'',vname)
        return vname if vname else name

    def user_session(self,user_id,**user_props) :
        ss = self.Session()
        ss.user_id = user_id
        ss.user_props = user_props
        return ss

    @property
    def session(self) :
        return self.user_session(self.user_id)

    @property
    def metadata(self) :
        return self.ormbase.metadata

    @property
    def engine(self) :
        return self.metadata.bind

    @engine.setter
    def engine(self, e) :
        self.metadata.bind = e
        self.Session.configure(bind = e)

    def create_all (self, tables = None, checkfirst = True) :
        self.metadata.create_all (tables=tables, checkfirst=checkfirst)

##    def drop_all (self, tables = None, checkfirst = True) :
##        self.metadata.drop_all (tables=tables, checkfirst=checkfirst)

    def cols_ver(self) :
        return []

    def cols_fld(self) :
        return []

    def cols_child(self) :
        return []

    def cols_main(self) :
        cols = []
        for arg in self._staticflds_args:
            cols.append(sqla.Column(**arg))
        return cols

    def _fld_dbtype(self,name,*dimension,**classes) :
        # name must be original defined name, not mainbase's attribute name
        #name,dimension = attr_name_dimension(name,dimension)
        type_ = None
        for d in dimension :
            # force type in dimension_key
            t = None
            for et,tt in {
                    '!s':sqla.String,
                    '!f':sqla.Float,
                    '!i':sqla.Integer,
                    '!d':sqla.Date,
                    '!t':sqla.Time,
                    '!dt':sqla.DateTime}.iteritems():
                if d.endswith(et) :
                    t = tt
                    break
            if t is None :
                t = self._fld_dbtype(name+'.'+d)
            if t is None or t ==type_ :
                continue
            if type_ is None:
                type_ = t
                continue
            type_ = None
            break
        if type_ is not None :
            return type_
        if not classes or classes.get('dynamicfld') or classes.get('storable') :
            for arg in self._dynamicflds_args :
                n = arg['name'] # self.named("dynamicfld",arg['name'])
                if n == name :
                    return arg['type_']
        if not classes or classes.get('calculatedfld') :
            for arg in self._calculatedflds_args :
                n = arg['name'] # self.named("dynamicfld",arg['name'])
                if n == name :
                    return arg['type_']

        if not classes or classes.get('verfld') or classes.get('storable') :
            for c in self.verbase.__table__.c :
                if isinstance(c,sqla.Column) \
                    and c.name not in ("parent_id","version") :
                    n = self.named("versionfld",c.name)
                    if n==name :
                        return type(c.type)

        if not classes or classes.get('staticfld') or classes.get('storable')  :
            for c in self.mainbase.__table__.c :
                if isinstance(c,sqla.Column) :
                    if c.name==name :
                        return type(c.type)
        return None
        #raise AttributeError("field '%s' not found." % name)

class Filter(Search):
    query_operands = {
        '&&' : sqla.and_,
        '||' : sqla.or_,
        }
    query_openranges = {
        '>' : '__gt__',
        '>=' : '__ge__',
        '<' : '__lt__',
        '<=' : '__le__',
        '==' : '__eq__',
        }

    def query(self,*cols) :
        qs = []
        and_or_ = None
        echk = [None,None,None]

        for itm in self.items:
            if itm=='!!' :
                continue

            if isinstance(itm,_SrchExp) :
                n_ = itm.not_
                itm._not_ = None # hacking native _not_ property
                q_ = []
                for c in cols :
                    q_.append(itm.query(c))
                q_ = sqla.or_(*q_)
                if n_ :
                    echk[1] = True # not statement
                    q_ = sqla.not_(q_)
                else :
                    echk[0] = True # simple statement
                qs.append(q_)
                continue

            if isinstance(itm,list) :
                echk[0] = True # simple statement
                if len(itm)==2 and itm[0] in self.query_openranges :
                    q_ = []
                    for c in cols :
                        fn = getattr(c,self.query_openranges[itm[0]])
                        q_.append(fn(itm[1]))
                    qs.append(sqla.or_(*q_))
                    continue

                q_ = []
                for c in cols :
                    q_.append(c.in_(itm))
                qs.append(sqla.or_(*q_))
                continue

            if itm in self.query_operands:
                if itm != and_or_ :
                    if len(qs)>1 :
                        op = self.query_operands.get(and_or_,sqla.and_)
                        qs = [op(*qs)]
                        # checking for empty field exception
                        if op == sqla.and_ :
                            if echk[0]:
                                echk[2] = True
                            echk[0] = None # reset simple expression
                    and_or_ = itm
                continue
            echk[0] = True
            q_ = []
            for c in cols :
                if hasattr(c,'as_formatted') :
                    c = c.as_formatted()
                if hasattr(c,'like') :
                    q_.append(c.like(itm,escape='\\'))
            if q_ :
                qs.append(sqla.or_(*q_))

        if len(qs)>1 :
            op = self.query_operands.get(and_or_,sqla.and_)
            # checking for empty field exception
            if op == sqla.and_ :
                if echk[0]:
                    chkempty = True
                    echk[0] = None
            qs = [op(*qs)]

        if qs :
            q = qs[0]
            if self.not_ :
                q = sqla.not_(q)
            if (self.not_ and not echk[1] and (echk[2] or echk[0]) ) \
            or (not self.not_ and echk[1] and not echk[2]) :
                # insert exception empty field clause
                eq_ = []
                for c in cols :
                    if hasattr(c,'nullif') :
                        eq_.append(c.nullif())
                    else :
                        eq_.append(c==None)
                q = sqla.and_(q,sqla.not_(sqla.or_(*eq_)))
            return q
        else :
            if self._exp is None :
                eq_ = []
                for c in cols :
                    q = c.nullif() \
                        if hasattr(c,'nullif') else \
                        sqla.func.nullif(c,'')==None
                    eq_.append(q)
                if eq_ :
                    return sqla.or_(*eq_)
        return None

    def match(self,*texts) :
        qs = []
        and_or_ = None

        def _isret(flag):
            flag = bool(flag)
            if and_or_ is not None:
                chk = (and_or_ == '||')
                if chk == flag or chk in qs :
                    return not chk if self.not_ else chk
            else :
                qs.append(flag)
            return None

        for itm in self.items:
            if itm=='!!' :
                continue

            if isinstance(itm,_SrchExp) :
                flag = _isret(itm.match(*texts))
                if flag is not None :
                    return flag
                continue

            if isinstance(itm,list) :
                flag = False
                if len(itm)==2 and itm[0] in self.query_openranges :
                    # may be range expression
                    for text in texts :
                        fn = getattr(text,self.query_openranges[itm[0]],None)
                        if callable(fn) :
                            flag = fn(itm[1])
                            if flag :
                                break
                else :
                    # or list expression
                    for text in texts :
                        flag = (text in itm)
                        if flag :
                            break
                flag = _isret(flag)
                if flag is not None :
                    return flag
                continue

            if itm in self.query_operands:
                # may be and/or operand
                and_or_ = itm
                continue
            # otherwise simple like expression
            # convert like str to regex str
            if not hasattr(self,'_like2re_cache_') :
                self._like2re_cache_ = {}
            ritm = self._like2re_cache_.get(itm)
            if ritm is None :
                self._like2re_cache_[itm] = ritm = like2re(itm)
            for text in texts :
                #print 'match',itm,text
                flag = bool(re.match(ritm,_unicode(text)))
                if flag :
                    break
            if self.not_ :
                flag = not flag
            return flag
        return True

##    def query(self,col):
##        qs = []
##        and_or_ = None
##
##        for itm in self.items:
##            if itm=='!!' :
##                continue
##
##            if isinstance(itm,_SrchExp) :
##                qs.append(itm.query(col))
##                continue
##
##            if isinstance(itm,list) :
##                if len(itm)==2 and itm[0] in self.query_openranges :
##                    # may be range expression
##                    fn = getattr(col,self.query_openranges[itm[0]])
##                    qs.append(fn(itm[1]))
##                    continue
##                # or list expression
##                qs.append(col.in_(itm))
##                continue
##
##            if itm in self.query_operands:
##                # may be and/or operand
##                if itm != and_or_ :
##                    if len(qs)>1 :
##                        op = self.query_operands.get(and_or_,sqla.and_)
##                        qs = [op(*qs)]
##                    and_or_ = itm
##                continue
##
##            # otherwise simple like expression
##            qs.append(col.like(itm,escape='\\'))
##        if len(qs)>1 :
##            op = self.query_operands.get(and_or_,sqla.and_)
##            qs = [op(*qs)]
##
##        if qs :
##            q = qs[0]
##            if self.not_ :
##                q = sqla.not_(q)
##
##            return q
##        return None

if __name__ == "__main__":
    import time

    class TestModel(_Model) :
        _staticflds_ = ["code:notnull,unique,index","category","title:notnull"]
        _dynamicflds_ = ['weight','serial','cost:float','price:float','weight.value:float']
        #_childflds_ = {'addresses': ['road','city','postcode']}
        #_calculatedflds_ = {'detail:float,deferred': lambda cls: cls.code+' '+cls.serial}

##    model = TestModel(user="sathit",debug=False,echo=True)
##    model.create_all()
    flt = Filter('ส')
    print flt.match('สาธิต')
def zzz():
    session = model.session

    mainbase = model.mainbase
    verbase = model.verbase
    fldbase = model.fldbase
    childbase = model.childbase

    #print mainbase.weight.search('')
    formatter = {
        sqla.Date: '%d/%m/%Y',
        sqla.DateTime: '%d/%m/%Y %H:%M:%S',
        sqla.Float: 2
        }
    print 'cost',type(mainbase._selcol('cost',cast=formatter)),mainbase._selcol('cost',cast=formatter)
    print 'weight',type(mainbase._selcol('weight'))
    print 'ver_logged_time',type(mainbase._selcol('ver_logged_time'))
    print 'code',type(mainbase._selcol('code'))
##    num = -5.2345
##    qry = session.query(
##                sqla.cast(sqla.cast(num,sqla.Integer),sqla.String) +
##                '.' +
##                sqla.func.substr(sqla.func.replace(
##                    sqla.func.round((1+sqla.func.abs(num - sqla.cast(num,sqla.Integer)))*100,12)
##                    ,'.',''),2)
##            )
##    print qry
##    for row in qry.all() :
##        print row
##    print dir(sqla.Float)
##    print sqla.DateTime.__visit_name__

##    print type(mainbase.code),isinstance(mainbase.code,sqla.orm.attributes.QueryableAttribute)
##    print type(mainbase.weight),isinstance(mainbase.weight,sqla.orm.attributes.QueryableAttribute)
##    print type(mainbase.ver_logged_user),isinstance(mainbase.ver_logged_user,sqla.orm.attributes.QueryableAttribute)
##    print type(mainbase.addresses),isinstance(mainbase.addresses,sqla.orm.attributes.QueryableAttribute)
##    print type(mainbase.detail),isinstance(mainbase.detail,sqla.orm.attributes.QueryableAttribute)

def yyy():
    model.create_all()

    m = model.mainbase(
            code="JW54-0123",
            category="test category",
            title="test title message",
            weight="this is weight value",
            serial = '1234',
            cost={'markup':550,'valued':'12000',},
            **{'price.retail':15000, 'weight.value':123}
            )


    # special field not listed in _dynamicflds_
    m.dfields.test_field = "test_value"
    m.addresses.append(childbase('addresses',road='Ladprao',city='Bangkok'))
    m.addresses.append(childbase('addresses',road='Praram3',city='Samutsakorn'))
##    m.addresses += [{'road':'Ladprao','city':'Bangkok'}]
##    m.addresses += [{'road':'Ladprao','city':'Bangkok'}]
##    print m.addresses

    # add data to database
    session.add(m)
    session.commit()

    qry = session.query(mainbase,) \
        .order_by(mainbase.title)

    filters = (
        mainbase.search('test'),
        mainbase.price.dim('retail')>=15000,
        mainbase.weight.search("this or that"),
        )
    qry = qry.filter(sqla.and_(*filters))
    print '------------ query ----------------------'
    print qry
    print '-----------------------------------------'
    print "*** test query and change ***"
    for r in qry.all() :
        print r
        print r._ver
        print type(r._ver.logged_time),r._ver.logged_time
        print 'cost:',r.cost
        print "dfields:",r.dfields.data()
        print r.addresses
        r.dfields.set_fld('weight',"that value is changed")
        print r.cost,r.dfields('cost')
        del r.serial
        session.add(r)

    model.engine.echo = True
    session.flush()
def xxx():
##    print '---------------------------------'
##    print sqla.select([mainbase.cost.dim('markup')])
##    print sqla.select([mainbase.dfields('cost.markup')])

##    maxo1 = sqla.sql.column('maxo1')
##    maxo2 = sqla.sql.column('maxo2')
##    def _decor(col) :
##        xcol = col
##        for i in xrange(10) :
##            xcol = sqla.func.replace(xcol,str(i),' ')
##        return xcol
##    def _mixsel(base) :
##        return [
##            base._selcol(base,'code').label('maxo2')
##            ]
##        #xcol =  sqla.func.length(sqla.func.rtrim(xcol))
##        #return sqla.func.substr(col,0,sqla.func.max(2,xcol))
##
##    expr = mainbase.select(
##            'code',decorfunc=_decor,label='maxo1', mixselect=_mixsel
##        ) .where(maxo1!=sqla.func.rtrim(maxo1))
##    expr = sqla.select([
##                sqla.func.substr(
##                    maxo2,1,
##                    sqla.func.max(2,sqla.func.length(sqla.func.rtrim(maxo1)))
##                    ).label('maxonomy')],from_obj=[expr])

##    expr = sqla.select([mainbase.__table__])
##    print expr


##    print expr
##    for tax in session.execute(expr):
##        print tax.items()
##        print mainbase(**dict(tax.items()))
##
##    print list(mainbase.__table__.c)

##    expr = fldbase.select(
##            'weight.',version=None,
##            alias=True,
##            mixselect=lambda b: [
##                b.version,
##                fldbase.scalar('price.retail',b.version,b.parent_id),
##                fldbase.scalar('serial.',b.version,b.parent_id),
##                ],
##            )
##    for tax in session.execute(expr) :
##        print 'weight ->',tax


##    expr = mainbase.select(
##            'version', version=None,
##            alias=True,
##            mixselect = lambda b: [
##                fldbase.scalar('weight.',version=b.version,id=b.parent_id),
##                fldbase.scalar('serial.',version=b.version,id=b.parent_id),
##                ],
##            )
##    for tax in session.execute(expr.count()) :
##        print 'version ->',tax


    model.engine.echo = False
    print "*** test query and delete ***"
    for r in qry.all() :
        print r
        print r._ver
        print "dfields:",r.dfields.data()
        print "last version", r._last_version
        session.delete(r)

    print mainbase.serial._deltaversion()



    time.sleep(1)
    session.flush()
    print "*** recheck and force delete ***"
    for r in qry.all() :
        print r
        print r._ver
        print "dfields:",r.dfields.data()
        print "ver_logs:",r._ver_logs.filter(model.verxbase.version!=0).all()
        session.delete(r)

    time.sleep(1)
    session.flush()
    print "*** recheck after force delete ***"
    for r in qry.all() :
        print r
        print r._ver
        print "dfields:",r.dfields.data()
    print "--- remaining -----"
    for r in session.query(mainbase).all():
        print r
    for r in session.query(verbase).all():
        print r
    for r in session.query(fldbase).all():
        print r

##    print "test search expr -----------------"
##    srch = Filter("(sathit or anan)")
##    print srch.items,srch
##    print srch.qsearch(mainbase.title,mainbase.owner,mainbase.serial)

