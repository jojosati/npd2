# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        npd2model
# Purpose:     npd2 data model base on dyndmod
#
# Author:      jojosati
#
# Created:     05/01/2012
# Copyright:   (c) jojosati 2012
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import datetime
import json
import re

from dyndmod import _Model, Filter, sqla
from dyndmod import all_sum, schema_columns, attr_name_dimension

def tryfloat(s) :
    try:
        return float(s)
    except :
        return 0.0

def split_urlsegs (urlstr,re_urloptions=None,re_default=re.compile('(?<!~)(?:/+)')) :
    re_urloptions = re_urloptions or re_default
    options =  re.split(re_urloptions,urlstr)
    if options :
        for i in range(len(options)) :
            options[i] = options[i].replace("~/","/").replace("~~","~")
    return options

def filter_rule2cmd(rule) :
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
    opdata = {
        'eq' : lambda data: '=' + data,
        'ne' : lambda data: '!=' + data,
        'lt' : lambda data: '<' + data,
        'le' : lambda data: '<=' + data,
        'gt' : lambda data: '>' + data,
        'ge' : lambda data: '>=' + data,
        'bw' : lambda data: data + '*', # begin with
        'bn' : lambda data: '!' + data + '*', # not begin with
        'ew' : lambda data: '*' + data, # end with
        'en' : lambda data: '!*' + data, # not end with
        'in' : lambda data: '[' + data + (',' if ',' not in data else '') +']', # in
        'ni' : lambda data: '![' + data + (',' if ',' not in data else '') +']', # not in
        'nc' : lambda data: '!*' + data + '*', # not contain
    }

    if isinstance(rule,dict) \
    and 'groupOp' in rule and 'rules' in rule :
        cmds = []
        for r in rule['rules'] :
            data = r['data']
            if not isinstance(data,basestring) :
                data = str(data)
            if data :
                fn = opdata.get(r['op'])
                if fn :
                    data = fn(re.escape(data))
                if data :
                    cmds.append(r['field']+'-'+data)
        if cmds :
            if len(cmds)>1:
                cmds.insert(0,rule['groupOp'])
            return json.dumps(cmds)

def next_runno (val,re_runno_part=None,re_defalut=re.compile('([0-9]{3,})')) :
    re_runno_part = re_runno_part or re_default
    segs = re.split(re_runno_part,val)
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

class Npd2(_Model) :
    _tablename_ = 'assets2'
    _staticflds_ = [
        "code:notnull,unique,index",
        ]
    _dynamicflds_ = [
        'state', # ('buying',)
        'what', # ('category','title', 'weight', 'serial', 'condition', 'tags')
        'when:date', #('buying', 'keeping', 'taking', 'selling', 'receiving',)
        'who', # ('owner', 'buyer',  'taker', 'sellto',)
        'staff', #('keeper','seller',)
        'price:float', # ('retail', 'estimate', 'taking', 'selling', 'receiving', )
        'cost:float',
        'base_cost:float', # ('buying', 'repairing','provider')
        'note', # ('comment', 'receiving', 'repairing',)
        'what.title:notnull',
        ]

    _calculatedflds_ = {
        'taken_days:int': (
                lambda cls: # expr
                            sqla.func.round(sqla.func.julianday('now') -
                            sqla.func.julianday(cls.when.dim('taking'))),
                lambda obj: #fget
                    (datetime.date.today() - obj.dfields('when.taking')).days \
                    if obj.dfields('when.taking') else \
                    None
                ),
        'repair_cost:float': (
                lambda cls: # expr
                    sqla.cast(sqla.func.ifnull(cls.note.dim('repairing'),0.0),sqla.Float)
                    ,
                lambda obj: #fget
                    tryfloat(obj.dfields('note.repairing'))
                ),
        'total_cost:float': (
                lambda cls: # expr
                    cls.base_cost.query('sum') \
                    + sqla.cast(cls.repair_cost,sqla.Float)
                    #+ sqla.cast(sqla.func.ifnull(cls.note.dim('repairing'),0.0),sqla.Float)
                    ,
                lambda obj: #fget
                    all_sum(getattr(obj.base_cost)) + obj.repair_cost
                ),
        'sell_profit:float': (
                lambda cls: # expr
                    cls.price.dim('selling') \
                        - cls.total_cost
                        #- cls.base_cost.query('sum')
                        #- cls.base_cost.dim('buying') \
                        #- cls.base_cost.dim('repairing') \
                        #- cls.base_cost.dim('provider')
                        ,
                    #cls.base_cost.query('sum'),
                lambda obj :
                    (obj.dfields('price.selling') - obj.total_cost) if obj.dfields('price.selling') else None
            ),
            }

    _formattercfg_ = {
        sqla.Date: '%d/%m/%Y',
        sqla.DateTime: '%d/%m/%Y %H:%M:%S',
        sqla.Float: 2
        }


    def filter_cmd(self,cmd,**kwargs) :
        '''
        cmd - a string or list of pivot filter cmd "@f-expression"
            *filter for not empty field :
                @f-fldname
            *filter a field :
                @f-fldname-term
            *filter some fields :
                @f-fldname,fldname[,..]-term
            *filter any field :
                @f--term
            *filter "and" for key,value pair :
                @f-{"fldname" : "term","fldname" : "term"}
            *filter "or" for list type :
                @f-["fldname-term","fldname-term"]
            *filter with operand for list type ("or","and","nor","nand") expression :
                @f-["operand","fldname-term","fldname-term"]
            *mixed in :
                @f-["or",{"fldname" : "term"[,..]},["nor","fldname-term"[,..]]

        optional arguments :
        qscols - list of column for global search in filter any field
        colnamed - function to translate column name (npd1to2)
        alias - True for use alias Table instead of base table
        translator - function to translate short-cmd
        cmdprefix - default is @f-
        idcol - pass to search function
        version - pass to search function
        formatter -
        Returns clause or None
        '''

        colnamed = kwargs.pop('colnamed',None)
        base = kwargs.pop('alias',None) or self.mainbase
        if base is True :
            base = sqla.orm.aliased(self.mainbase)

        qscols = kwargs.pop('qscols',None)

        # ---------------------------------
        prefix = kwargs.pop('cmdprefix',None) or '@f-'
        if isinstance(cmd,basestring) :
            cmd = _unicode(cmd)
        translator = kwargs.pop('translator',None)
        if callable(translator) :
            cmd = translator(cmd)
        if isinstance(cmd,basestring) :
            # may be json list
            try :
                cmd = json.loads(cmd)
            except :
                pass
        if 'formatter' not in kwargs :
            kwargs['formatter'] = self._formattercfg_

        # may be dict of rule
        rule = filter_rule2cmd(cmd)
        if rule :
            cmd = prefix+rule
        if isinstance(cmd,basestring) :
            # may be open list @f-name-term,@f-name-term
            cc = []
            segs = re.split(r'\s*(?:,\s*)?'+re.escape(prefix),cmd)
            for x in segs[1:] :
                if x :
                    cc.append(prefix+x)
            cmd = cc

        # now cmd should be a list
        if isinstance(cmd,(list,tuple)) :
            qlst = []
            for c in cmd :
                if c.startswith (prefix) :
                    c = c[len(prefix):]
                    if not c :
                        continue
                    v = '?'
                    try :
                        c = json.loads(c)
                        xc = filter_rule2cmd(c)
                        if xc is not None :
                            c = xc
                    except :
                        pass

                    if isinstance(c,basestring) and '-' in c:
                        c,v = c.split('-',1)

                    q = base.search(v,c or qscols,colnamed=colnamed,**kwargs)
                    if q is not None :
                        qlst.append(q)
            if qlst :
                return sqla.and_(*qlst)
        return None


    def taxonomy(self,name=None,**kwargs):
        '''
            name - name of taxonomy column
            term - searching word
            colnamed - function to convert colname from npd1 to 2
            X --> history - False or True (use taxtype='history')
            taxtype = 'history','maxonomy'
            untaxable - default '!/@/@' - exclude data that contain untaxable sign
            qscols - quick search cols
            fcmd - filter cmd @f-xxxx
            fcmd_transtator - function for translate filter_cmd
            frule - filter rule
            scopes - scope with specific column value
            descriptors - concat fields for taxonomy description
            offset - default 0
            limit - default 50
            invalidity - True or likestr
            X --> mixtaxes - [xxx,..] including  predefined taxonomies
            pass through args :
                decorfunc -
                formatter -
        '''
        colnamed = kwargs.get('colnamed')
        term = kwargs.get('term') or ''
        taxtype = kwargs.get('taxtype','taxonomy')
        label = kwargs.get('label') or 'taxonomy'
        if not isinstance(term,list) :
            term = [term]
        untaxable = (name is not None) and (taxtype=='taxonomy')
        untaxable = kwargs.get('untaxable',untaxable)
        if untaxable is True:
            untaxable = '!/@/@'
        if callable(untaxable) :
            untaxable = untaxable(name,term,taxtype)
        if untaxable :
            term.extend(untaxable) \
                if isinstance(untaxable,(list,tuple)) else \
                term.append(untaxable)
        if len(term)==1 and term[0]=='' :
            term.append(lambda tcol: tcol!=None)
        # -------------------------
        selargs = {
            'formatter': True,
            'label': label,
            'term': term,
            }
        for k in ('decorfunc',):
            if k in kwargs :
                selargs[k] = kwargs[k]

        if taxtype=='history':
            selargs['version'] = self.verbase.version

        scopes= {}
        invalidity = kwargs.get('invalidity')
        if invalidity is True :
            invalidity = '_%'
        if isinstance(invalidity,basestring) :
            invalidity = (lambda s: (lambda c : c.like(s)))(invalidity)
        if invalidity is None or callable(invalidity) :
            scopes['invalidity'] = invalidity

        selargs['scopes'] = scopes
        fltargs = dict(selargs)
        # -------------------------
        if taxtype=='history':
            scopes = {}
            fltargs['v0scopes'] = scopes
##        else :
##            scopes = dict(scopes)

        for c,t in (kwargs.get('scopes') or {}).iteritems() :
            if colnamed :
                c = colnamed(c,'filter')
            if c :
                scopes[c] = t
##        if taxtype=='history':
##            fltargs['v0scopes'] = scopes
##        else :
##            fltargs['scopes'] =scopes

        # -------------------------
        qscols = kwargs.get('qscols')
        translator = kwargs.get('fcmd_translator')

        def filterfunc(cmd,rule) :
            def func(_base) :
                _idcol = getattr(_base,'parent_id',None)
                if _idcol is None :
                    _idcol = getattr(_base,'id')
                crel = getattr(_base,'_AliasedClass__alias',
                                getattr(_base,'__table__',None))
                cs = []
                if cmd :
                    c = self.filter_cmd(
                            cmd,
                            colnamed=colnamed,
                            qscols=qscols,idcol=_idcol,
                            translator=translator,
                            )
                    if c is not None :
                        #if crel is not None:
                        #    c = c.correlate(crel)
                        cs.append(c)
                if rule :
                    c = self.filter_cmd(
                            rule,
                            colnamed=colnamed,
                            idcol=_idcol,
                            )
                    if c is not None :
                        #if crel is not None :
                        #    c = c.correlate(crel)
                        cs.append(c)
                return cs
            return func

        filter_cmd = kwargs.get('fcmd')
        filter_rule = kwargs.get('frule')
        fltargs['mixclauses'] = filterfunc(filter_cmd,filter_rule)

        qlst = []
        if name is None :
            q = self.mainbase.select(name,**fltargs)
            if q is not None :
                qlst.append(q)
        else :
            cols = name
            if not isinstance(cols,(list,tuple)) :
                cols = (cols,)
            descriptors = kwargs.get('descriptors')
            for c in cols :
                args = fltargs
                dsc = descriptors
                # column may be column with filter cmd tag
                if isinstance(c,basestring) :
                    fc = split_urlsegs(c)
                    c = fc.pop(0)

                    if callable(dsc) :
                        dsc = dsc(c)
                    if colnamed :
                        c = colnamed(c,'read')
                    if not c :
                        continue
                    nofilter = '@@' in fc
                    if nofilter :
                        fc.remove('@@')
                        args = selargs

                    fr = None
                    if not nofilter :
                        fr = filter_rule
                        if filter_cmd :
                            fc.extend(filter_cmd) \
                            if isinstance(filter_cmd,(list,tuple)) else \
                            fc.append(filter_cmd)
                    if fc or fr :
                        args = dict(args)
                        args['mixclauses'] = filterfunc(fc,fr)

                if colnamed :
                    if isinstance(dsc,basestring) :
                        dsc = dsc.split(',')
                    if isinstance(dsc,(list,tuple)) :
                        dsc = [colnamed(d,'read') for d in dsc]
                        while None in dsc :
                            dsc.remove(None)
                q = self.mainbase.select(c,descriptors=dsc,**args)

                if q is not None :
                    qlst.append(q)

        if not qlst :
            return None
        if len(qlst)==1 :
            q = qlst[0]
            if name is not None :
                q = q.distinct()
        else :
            q = sqla.union(*qlst) #qlst[0].union(*qlst[1:])
        if taxtype=='maxonomy' and name is not None :
            taxcol = sqla.sql.column(label)
            maxcol = taxcol
            for i in xrange(10) :
                maxcol = sqla.func.replace(maxcol,str(i),' ')

            maxotax = sqla.sql.column('maxotax')
            maxo = sqla.sql.column('maxo')
            q = sqla.select(
                    [taxcol.label('maxotax'),maxcol.label('maxo')],
                    sqla.func.rtrim(maxo)!=maxo,
                    from_obj=[q])
            q = sqla.select([
                    sqla.func.max(maxotax).label(label),
                    ],
                    from_obj=[q],
                    group_by= [sqla.func.substr(
                        maxotax,
                        1,
                        sqla.func.max(2,sqla.func.length(sqla.func.rtrim(maxo)))
                        )]
                    )
        offset = kwargs.get('offset')
        limit = kwargs.get('limit',50)
        try :
            limit = int(limit)
        except:
            pass

        if offset :
            q = q.offset(offset)
        if limit :
            if isinstance(limit,int) :
                q = q.limit(abs(limit))
            else :
                q = q.limit(limit)

        if name is not None :
            ord = None
            if label or isinstance(name,basestring) :
                ord = sqla.sql.column(label or name)
            elif isinstance(name,sqla.orm.attributes.QueryableAttribute) :
                ord = name
            if ord is not None :
                if isinstance(limit,int) and limit < 0 :
                    ord = ord.desc()
                q = q.order_by(ord)
        return q


if __name__ == '__main__':
    from csvmixin import _CSV_implement, _CSV_mixin
    class Npd2_csv_implement (_CSV_implement) :
        encoding = 'cp874'
        dateformat = '%d/%m/%Y'
        timeformat = '%H:%M:%S'
        datetimeformat = dateformat+' '+timeformat
        numseperator = ','
        colmappings = {
            u'ชนิด'
                    : 'what.category',
            u'รหัส'
                    : 'code',
            u'รายการสินค้า'
                    : 'what.title',
            u'น้ำหนัก'
                    : 'what.weight',
            u'เบอร์'
                    : 'what.serial',
            u'ทุน'
                    : 'base_cost.buying',
            u'ปรับปรุง'
                    : 'base_cost.repairing',
            u'ทุนร้าน'
                    : 'cost',
            u'ขายประเมิน'
                    : 'price.estimate',
            u'ราคาตั้งขาย'
                    : lambda k,csvdata,*args: (
                            ('price.retail', csvdata[k] or
                                csvdata.get(u'ขายประเมิน')),
                            ),
            u'วันที่ซื้อ'
                    : 'when.buying',
            u'ซื้อจาก'
                    : 'who.owner',
            u'วันที่'
                    : 'when.keeping',
            u'ที่เก็บ'
                    : 'who.keeper',
            u'วันที่ยืม'
                    : 'when.taking',
            u'ผู้ยืม'
                    : 'who.taker',
            u'หมายเหตุ'
                    : 'note.comment',
            u'วันที่ขาย'
                    : 'when.selling',
            u'สถานที่ขาย'
                    : 'who.sellby',
            u'ผู้ซื้อ'
                    : 'who.sellto',
            u'ราคาขาย'
                    : 'price.selling',
            u'วันที่รับ'
                    : 'when.receiving',
            u'ชนิดรับ'
                    : 'note.receiving',
            }

    class Npd2CSV(Npd2,_CSV_mixin) :
        _csv_implement_class_ = Npd2_csv_implement

    #model = Npd2CSV(user="csv_importer",dbpath="sqlite:///npd2.sqlite.db",quiet=False)
    model = Npd2CSV(user="csv_importer",quiet=False,echo=True)
    model.csv_importer('25541006.csv',start=0,limit=1,newtable=True)

    session = model.session
    mainbase = model.mainbase
    fldbase = model.fldbase
    verbase = model.verbase

    print '--------------------'
    print Filter('abc').query(mainbase.code)
def xxx():
    #q = model.taxonomy(['who.keeper','who.taker'])

    #q = mainbase.select('who.taker',label='taxonomy',term='*ร*')
    #q = q.union(mainbase.select('who.keeper',scopes={'invalidity':None},label='taxonomy',term='*ร*'))
    #expr = model.taxonomy(fcmd='@f-what.serial')
    #qry = session.query(mainbase.when.dim('buying').label('title'),mainbase.id.label('_id_'),).filter(expr._whereclause)
    #qry = qry.from_self(sqla.sql.label('test',sqla.sql.column('_id_',sqla.String)+ sqla.literal(': ')+ sqla.sql.column('title',sqla.String)))
    #q = qry.order_by(sqla.sql.column('title'))

    #print mainbase.price.as_formatted()

    expr = model.taxonomy(
            'price.retail',
            )
    print expr

##    #q = session.query(mainbase.what.dim('title')).filter(expr._whereclause)
##    q = session.query('1').filter(mainbase.what.search('?'))
##    print type(q._from_obj)
##    q._from_obj = (mainbase,)
    for row in session.execute(expr) :
        print row[0]

##    print q
##    for row in q.all() :
##        #print type(row),dir(row)
##        print row


##    for row in session.query(mainbase).filter(q._whereclause).all():
##        print row
##        print row._ver
'''
    print '-----------'
    validity = verbase.scalar(
            'invalidity',
            fldbase.version,fldbase.parent_id)==None

    chkcat = fldbase.scalar('what.category',fldbase.version,fldbase.parent_id)=='จี้'
    q1 = fldbase.select(
            'what.category',
            mixclauses=[validity],
            label='taxonomy'
            )

    q2 = fldbase.select('who.sellto',
            mixclauses=[validity,chkcat],
            label='taxonomy'
            )
    qry = session.query(q1.union(q2)).order_by('taxonomy')
    print qry
    print '---------------------------------------'
    for tax in qry.all():
        print tax[0]
'''

'''
    qry = session.query(
            mainbase,mainbase.taken_days
        ).filter(
            mainbase.price.dim('selling') != None
        ).filter(
            model.filter_cmd('@f-what-เพชร')
        )
    print qry
    for m in qry[:5]:
        print m,
        m = m[0]
        print m.price,m.dfields('price.selling'),
        print ''
        print m.dfields('what.title'),m.dfields('what.category')
'''
