# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        csvmixin
# Purpose:     csv mixin for dyndmod
#
# Author:      jojosati
#
# Created:     05/01/2012
# Copyright:   (c) jojosati 2012
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import datetime

from dyndmod import sqla, re
from dyndmod import _unicode, attr_name_dimension

class _CSV_implement(object) :
    # _Model mixin class to sunpport CSV
    encoding = 'utf8' # 'cp874'
    dateformat = '%Y-%m-%d'
    timeformat = '%H:%M:%S'
    datetimeformat = dateformat+' '+timeformat
    numseperator = ','
    typecasters = {
        sqla.Integer :
            lambda cls,v: int(float(v.replace(cls.numseperator,''))),
        sqla.Float :
            lambda cls,v: float(v.replace(cls.numseperator,'')),
        sqla.Date :
            lambda cls,v: datetime.datetime.strptime(v,cls.dateformat).date(),
        sqla.DateTime :
            lambda cls,v: datetime.datetime.strptime(v,cls.datetimeformat),
        sqla.Time :
            lambda cls,v: datetime.datetime.strptime(v,cls.timeformat).time(),
        }
    colmappings = {}

class _CSV_mixin(object):
    import random

    def csv_importer (self,csvfile,**kwargs) :
        return self.csv_importer_imp(csvfile,**kwargs)

    def csv_importer_imp (self,csvfile,**kwargs) :
        '''
            implemented method for csv_importer
            with built-in transformer function
            using csv_imp class to control transform data
            or self's class attribute
        '''
        model = kwargs.get('model') or self

        #csvimp = csvimp or self
        csvimp = getattr(self,'_csv_implement_class_',None) or self
        encoding = kwargs.pop('encoding',csvimp.encoding) # default encoding
        rawmode = 0
        if ',' in csvfile :
            files = csvfile.split(',',1)
            csvfile = files.pop(0)
            if 'raw' in files :
                rawmode = 1
                files.remove('raw')
            if 'rawonly' in files :
                rawmode = 2
                files.remove('rawonly')
            if files :
                encoding = files.pop(0)

        fake = 0
        while csvfile[0]=='!':
            fake += 1
            csvfile = csvfile[1:]
        if fake :
            import random
        colnamed = kwargs.get('colnamed')
        mappings = csvimp.colmappings
        def setdata(data,k,c,v=None) :
            # k use as referrence to csv column header, for error reporting
            if isinstance(c,tuple) :
                # if c is tuple, ignore v
                for cv in c :
                    setdata(data,k,*cv)
                return
            if isinstance(c,dict):
                # if c is dict, ignore v
                for cv in c.iteritems() :
                    setdata(data,k,*cv)
                return
            if not v :
                return
            if not c :  # support raw mode
                if not rawmode :
                    return
                c = k
            if callable(colnamed) :
                c = colnamed(c,'import')
            if not c :  # support raw mode
                if not rawmode :
                    return
                c = k
            n,dim = attr_name_dimension(c)
            t = model._fld_dbtype(n,*dim)
            if rawmode and t is None :
                return
            cc = c
            fn = csvimp.typecasters.get(t)
            if fn :
                try:
                    v = fn(csvimp,v)
                except Exception as e :
                    errmsg = _unicode(_unicode("{0} ({1}/{2})={3!r}").format(str(e),k,c,v))
                    if model.debug and not rawmode :
                        raise type(e)(errmsg)
                    else:
                        try :
                            v = model.cast_result_value(t,v)
                        except :
                            model.echo_(errmsg)
                            if model.debug :
                                raise
                            model.echo_('suppress to None.')
                            v = None
            if fake and isinstance(v,float):
                v = ((v+5000)*2)*(random.random()+0.3)
            if v is not None :
                data[cc] = v

        def transformer(csvdata) :
            # if fake skip enable
            if fake>=2 and (10 * random.random()) < 0.1 :
                return
            data = {}
            for k,v in csvdata.iteritems() :
                if rawmode>=2 :
                    c = None
                else :
                    c = mappings.get(k)
                    if callable(c) :
                        c = c(k,csvdata,data)
                setdata(data,k,c,v)
            return data
        kwargs['encoding'] = encoding
        return self.csv_importer_base(csvfile,transformer=transformer,**kwargs)

    def csv_importer_base(self,csvfile,transformer=None,**kwargs) :
        import csv

        model = kwargs.get('model') or self

        newtable = kwargs.pop("newtable",False)
        encoding = kwargs.pop('encoding','utf8')
        limit = kwargs.pop('limit',0)
        start = kwargs.pop('start',0)
        encoding = encoding or 'utf8'
        echo_ = model.echo_
        echo_('CSV file: {0} encoding: {1}',csvfile,encoding)
        if newtable :
            echo_('drop all tables, before create new.')
            model.metadata.drop_all()
        model.create_all()
        session = model.session

        csvcnt = 0
        rowcnt = 0
        errcnt = 0
        with open(csvfile) as f:
            cf = csv.DictReader(f, delimiter=',')
            for data in cf:
                csvcnt += 1
                if csvcnt < start :
                    continue
                csvdata = {}
                for k,v in data.iteritems():
                    k,v = _unicode(k,encoding).rstrip(),_unicode(v,encoding).rstrip()
                    csvdata[k] = v
                data = csvdata
                try :
                    try:
                        if transformer :
                            data = transformer(data)
                        if isinstance(data,dict) :
                            data = model.mainbase(data)
                        if isinstance(data,model.ormbase) :
                            session.add(data)
                        if not session.new :
                            continue
                    except:
                        session.expunge_all()
                        raise
                    else:
                        try :  session.commit()
                        except :
                            session.rollback()
                            raise
                except Exception as e:
                    errcnt += 1
                    #errmsg = _unicode("{0} csvrow #{1}".format(str(e),csvcnt))
                    if model.debug :
                        for k,v in csvdata.iteritems() :
                            model.debug_("{0}={1}",k,v)
                        raise #type(e)(errmsg)
                    else:
                        echo_('{0}',e)
                    continue
                rowcnt += 1
                if rowcnt % 100 == 0 :
                    echo_('reading {0}, writing {1} so far...',csvcnt,rowcnt)
                if rowcnt == limit : break

            echo_('--- end of csv data ---')
            echo_('Total read {0}, write {1}, error {2}',csvcnt,rowcnt,errcnt)
            return [csvcnt,rowcnt,errcnt]

if __name__ == '__main__':
    pass
