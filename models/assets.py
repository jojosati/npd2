# -*- coding: utf-8 -*-

# schema part
# warning:  any changes to _tablename_, _fields_[name, datatype, index,unique,]  may effect to existed table
_tablename_ = "asset"
_fields_ = [
    # ข้อมูลทั่วไป
    {'name': 'acat',
    'options' : {
            'label':'category//th:ชนิด',
            'csv_field':'ชนิด',
            'required': True,
            } } , # - ROLEX, กำไล, จี้, ฯลฯ
    {'name': 'code',
    'index':True, 'unique':True,
    'options' : {
            'label':'//th:รหัส',
            'csv_field':'รหัส',
            'csv_valid':True,
            'access':'va',
            'required':True,
            'colgroup':'code',

            }},
    {'name': 'condition',
    'options' : {
            'label':'//th:สภาพ',
            'colwidth' : 2,
            'colgroup':'code',
            }}, # +++ สภาพของทรัพย์ - ชำรุด, ใหม่, xx%
    {'name': 'detail',
    'options' : {
            'label':'//th:รายการ',
            'csv_field': 'รายการสินค้า',
            'csv_valid':True,
            'required': True,
            'colwidth' : 8,
            'rowlength': 3,
            }},
    {'name': 'weight',
    'options' : {
            'label':'//th:น้ำหนัก',
            'csv_field': 'น้ำหนัก',
            }},
    {'name': 'gold_weight',
    'options' : {
            'label':'//th:น.น.ทอง',
            }},
    {'name': 'serial',
    'options' : {
            'label':'//th:เบอร์',
            'csv_field': 'เบอร์',
            }},
    #{'name': 'tag', 'options' : {'label':'//th:คำค้น','access':'vae','colwidth' : 8,} }, # +++
    #{'name': 'outline', 'options' : {'label':'//th:ข้อความโปรย','access':'vae','colwidth' : 8,}},
    {'name': 'memo',
    'datatype': 'Text',
    'options' : {
            'label':'//th:บันทึก',
            'access':'vae',
            'colwidth':8,
            'rowlength':3,
            } }, # +++

    # ต้นทุน - costing
    {'name': 'base_cost',
    'datatype' : 'Float',
    'options' : {
            'label':'//th:ทุนซื้อ',
            'csv_field': 'ทุน',
            'access':'vae',
            'colgroup':'costing',
            } } , #(ราคาซื้อ)
    {'name': 'provider_cost',
    'datatype' : 'Float',
    'options' : {
            'label':'//th:คชจ.จัดซื้อ',
            'access':'vae',
            'colgroup':'costing',
            }} , # npd1c2
    {'name': 'extra_cost',
    'options' : {
            'label':'//th:ทุนปรับปรุง',
            'csv_field': 'ปรับปรุง',
            'access':'vae',
            'colgroup':'costing',
            'colwidth':6,'rowlength': 1.4,
            }},

    {'name': 'repair_cost',
    'datatype' : 'Float',
    'calculated':True,
    'options' : {
            'label': '//th:คชจ.ซ่อม',
            'access':'_g',
            'colgroup':'costing',
            }}, # npd1c2

    {'name': 'mark_cost',
    'datatype' : 'Float',
    'calculated':True,
    'options' : {
            'label':'//th:ทุนร้าน',
            'csv_field': 'ทุนร้าน',
            'access':'_g',
            'colgroup':'costing',
            }} , # npd1c2 - calculated field

    # ราคาขาย - pricing
    {'name': 'lowest_price',
    'datatype' : 'Float',
    'options' : {
            'label':'//th:ราคาประเมิน',
            'csv_field':'ขายประเมิน',
            'access':'vae',
            'colgroup':'pricing',
            }}, #(ราคาต่ำสุด ที่ขายได้)
    {'name': 'target_price',
    'datatype' : 'Float',
    'options' : {
            'label':'//th:ราคาขาย',
            'csv_field':'ราคาตั้งขาย',
            'colgroup':'pricing',
            }},

    # เจ้าของ - owning
    {'name': 'buy_date',
    'datatype' : 'Date',
    'options' : {
            'label':'//th:วันที่ซื้อ',
            'colwidth' : 2.2,
            'csv_field': 'วันที่ซื้อ',
            'access':'vae',
            'colgroup':'owning',
            }},
    {'name': 'owner',
    'options' : {
            'label':'//th:ซื้อจาก',
            'csv_field': 'ซื้อจาก',
            'colwidth' : 3,
            'access':'vae',
            'colgroup':'owning',
            }},
    {'name': 'buy_cond',
    'options' : {
            'label': '//th:เงื่อนไขซื้อ',
            'access':'vae',
            'colwidth' : 2,
            'colgroup':'owning',
            }}, # +++ เงื่อนไขซื้อ - จำนำ, ฝากขาย

    # เก็บรักษา - keeping
    {'name': 'keep_date',
    'datatype' : 'Date',
    'options' : {
            'label': '//th:วันที่เก็บ',
            'colwidth' : 2.2,
            'csv_field': 'วันที่',
            'colgroup':'keeping',
            }},
    {'name': 'keeper',
    'options' : {
            'label': '//th:ที่เก็บ',
            'csv_field': 'ที่เก็บ',
            'colwidth' : 3,
            'colgroup':'keeping',
            }},
    # ยืม - taking
    {'name': 'take_date',
    'datatype' : 'Date',
    'options' : {
            'label': '//th:วันที่ยืม',
            'colwidth' : 2.2,
            'csv_field': 'วันที่ยืม',
            'access':'ve',
            'colgroup':'taking',}},
    {'name': 'taker',
    'options' : {
            'label': '//th:ผู้ยืม',
            'csv_field': 'ผู้ยืม',
            'colwidth' : 3,
            'access':'ve',
            'colgroup':'taking',
            }},
    {'name': 'taker_price',
    'datatype' : 'Float',
    'options' : {
            'label': '//th:ราคายืม',
            'csv_field': 'หมายเหตุ',
            'csv_exception': 'memo',
            'access':'vea',
            'colgroup':'taking',
            }},
    {'name': 'taken_days',
    'datatype' : 'Integer',
    'calculated':True,
    'options' : {
            'label': '//th:จำนวนวันยืม',
            'colwidth' : 2,
            'access':'_g',
            'colgroup':'taking',
            }},

    # ประวัติขายและรับชำระ - selling
    {'name': 'sell_date',
    'datatype' : 'Date',
    'options' : {
            'label': '//th:วันที่ขาย',
            'colwidth' : 2.2,
            'csv_field': 'วันที่ขาย',
            'access':'ve',
            'colgroup':'selling',
            }},
    {'name': 'sell_site',
    'options' : {
            'label':'//th:สถานที่ขาย',
            'csv_field': 'สถานที่ขาย',
            'access':'ve',
            'colgroup':'selling',
            }},
    {'name': 'buyer',
    'options' : {
            'label': '//th:ขายให้',
            'colwidth' : 3,
            'csv_field': 'ผู้ซื้อ',
            'access':'ve',
            'colgroup':'selling',
            }},
    {'name': 'sell_price',
    'datatype' : 'Float',
    'options' : {
            'label': '//th:มูลค่าขาย',
            'access':'ve',
            'csv_field': 'ราคาขาย',
            'colgroup':'selling',
            }},

    {'name': 'sell_profit',
    'datatype' : 'Float',
    'calculated':True,
    'options' : {
            'label': '//th:กำไร',
            'access':'_g',
            'colgroup':'selling',
            }}, # npd1c2

    # การชำระ - receiving
    {'name': 'receive_date',
    'datatype' : 'Date',
    'options' : {
            'label': '//th:วันที่รับชำระ',
            'colwidth' : 2.2,
            'csv_field': 'วันที่รับ',
            'access':'ve',
            'colgroup':'receiving',
            }},
    {'name': 'receive_type',
    'options' : {
            'label': '//th:รับชำระโดย',
            'csv_field': 'ชนิดรับ',
            'access':'ve',
            'colgroup':'receiving',
            }},
    {'name': 'invalidity',
    'options' : {
            'label':'invalidity',
            'colwidth' : 2,
            'access':'gve',
            'colgroup':'system',
            } } ,
    {'name': 'rev_id',
    'options' : {
            'label':'rev_id',
            'colwidth' : 2,
            'access':'gv',
            'colgroup':'version',
            } } ,
    {'name': 'revision',
    'options' : {
            'label':'revision',
            'colwidth' : 2,
            'access':'gv',
            'colgroup':'version',
            } } ,

    ]

# -------------------------------------
# framework definitoin part
# custom update to individual field
_fld_options_ = {
    }

_options_ = {
    'suburl' : 'npd',
    'concurrent_control' : True,
    'version_control' : 'code',
    'version_table' : True,
    'tagging_control' : 'tag',
    #'tagging_table' : True,
    'media_root': 'media/npd/',
    'shortdesc_field' : ['code','detail'],
    'media_field' : {'$media':'*.jpg,*.png,*.avi,*.wmv,*.mp3','$pic':'*.jpg,*.png'},
    'sql_dbfile': 'db/npd2.sqlite.db',
    'modelname' : "Assets",
    'caption' : 'Precious Assets',
    'autocomplete_scope' : {
            'acat': ['code','detail','weight','serial'],
            '!':['memo'],
            #'buy_cond': ['owner'],
            'code' : ['base_cost','extra_cost','mark_cost','lowest_price','target_price','taker_price']
            },
    'autocomplete_mixin' : {
            'buyer': ['taker/@f-buyer-','buyer'],
            'sell_site': ['sell_site','keeper/@f-buyer-'],
            'owner': ['owner/@@','buyer',],
            'memo': [],
            },
    'maxonomy_suppressnumsize' : 1,
    'maxonomy_format' : {'code':'%y-0000'},
    'autocomplete_descriptor' : {
            'taker_price' : 'take_date,taker',
            },
    }

_permissions_ = {
    "developer" : {'*' : None,'code':'gave','__media__':'*,*/*','__history__':'*'}, # use default access in colModel, except field 'code'
    "administrator" : {'*' : None,'code':'gave','__media__':'*,*/*','__history__':'g'},
    "manager" : {'*' : None,'code':'gav','__media__':'*,*/*',},
    "editor" : {
                '__table__' : '!hz', # grid, pivot-url, search, quick search, view, add, edit
                '*' : None,
                'code':'gav',
                'base_cost' : '', # not allow all
                'extra_cost' : '',
                'mark_cost' : '',
                'provider_cost': '',
                'sell_profit': '',
                'buy_date' : 'av',
                'owner' : 'av',
                'buy_cond' : 'av',
                '_hashlev_':2,
                '__media__':'*,more/*,wallpapers/*',
                },
    "viewer" : {
                '__table__' : 'gpsqv', # grid, pivot-url, search, quick search, view,
                'acat' : 'gv',
                'code' : 'gv',
                'detail' : 'gv',
                'weight' : 'gv',
                'serial' : 'gv',
                'condition' : 'gv',
                'target_price' : 'gv',
                'keeper' : 'gv',
                '__media__':'*,more/*,wallpapers/*',
                },
    '' : {
                '__table__' : '',
                '__media__':'*,wallpapers/*',
        },
    # other role
    "*" : {
                '__table__' : 'gq',
                '__hashlev__' : -3,
                '__media__':'*,more/*,wallpapers/*',
                'acat' : 'gv',
                'code' : 'gv',
                'detail' : 'gv',
                'weight' : 'gv',
                'condition' : 'gv',
                'target_price' : 'gv',
                },
    }

class _wrapper_: #wrapper implement for custom action
    @staticmethod
    def mapper_prop(model,mpobj,sqlfn):
        prop = {}
        prop['memo'] = sqlfn['deferred'](mpobj.c.memo)
        sqla = sqlfn['sqla']
        func = sqla.func
        prop['taken_days'] = sqlfn['column_property'](sqla.cast(func.julianday('now') - func.julianday(mpobj.c.take_date),sqla.Integer))
        mpobj.add_properties(prop)

    @staticmethod
    def load_csv(model,csvfile,**kwargs) :
        fake = csvfile[0]=='!'
        if fake :
            if not kwargs.get('quiet') : print 'fake cost mode'
            csvfile = csvfile[1:]
        skip = csvfile[0]=='!'
        if skip :
            if not kwargs.get('quiet') : print 'random skip mode'
            csvfile = csvfile[1:]

        def verifyrowdata(rowdata) :
            if not fake: return True
            if skip and (10*model.randomseed()) < 0.1 : return False

            # faking cost
            val = 100*int((10*model.randomseed())+(100*model.randomseed()))
            for k in ['base_cost','mark_cost','lowest_price','target_price'] :
                val = 100*int(val/100 * (1+model.randomseed(0.5)))
                rowdata[k] = val
            k = 'extra_cost'
            if k in rowdata :
                rowdata[k] = rowdata[k].replace(',','')

            k = 'taker_price'
            if k in rowdata :
                val = rowdata['mark_cost']
                val = 100*int(val/100*(1+model.randomseed(0.3)))
                rowdata[k] = val
            return True

        return model.load_csv_base(csvfile,verifyrowdata=verifyrowdata,**kwargs)

    @staticmethod
    def _new_items(model,**kwargs) :
        cmd = kwargs.get('oper')
        user_role = kwargs.get('user_role')
        if not model.colPermission ('__table__',user_role,'a') :
            return [False,"permission denied",'']
        session = model.Session()
        recs =[]
        codes = []
        head = model.json_loads(kwargs['head'])
        if head['keeper'] :
            head['keep_date'] = head['buy_date']
        items = model.json_loads(kwargs['items'])
        for item in items:
            item['ocode'] = item['code']
            args = {
                'term':item['code'],
                'acat':item['acat'],
                'user_role':kwargs['user_role'],
                }
            code = model.maxonomy('code',**args)
            if not code:
                return [False,"%s, finding maxonomy code fail" % (item['ocode'],),'']
            code = code[0]
            while code in codes :
                code = model.next_runno(code)
                if not code :
                    return [False,"%s, try running new code fail" % (item['code'],),'']
            rec = model.odb()
            brec = None
            vcbrec = None
            if item['id'].startswith('dnd_') or item['id'].startswith('clk_') :
                try :
                    brec = session.query(model.odb).filter(model.odb.code==item['code']).one()
                    vcbrec = model.version_ctrl(brec,**kwargs)
                except Exception as e:
                    return [False,"%s, %s %s" % (cmd,item['code'],e),'']
            if brec is not None :
                if '(#' in brec.buyer :
                    return [False,"%s, already transfer as %s" % (item['code'],brec.buyer),'']

                brec.buyer += '(#'+code+')/@/@' # untaxable sign
                if vcbrec : recs.append(vcbrec)
                recs.append(brec)
            codes.append(code)
            item['code'] = code
            for c in head:
                if c=='id': continue
                try:
                    model.update_field(rec,c,head[c],user_role,'a')
                except Exception as e :
                    return [False,"%s, %s" % (item['code'],e),'']
            for c in item :
                if c in ['id','last_updated']: continue
                try:
                    model.update_field(rec,c,item[c],user_role,'a')
                except Exception as e :
                    return [False,"%s, %s" % (item['code'],e),'']
            if brec is not None :
                rec.owner += '(#'+brec.code+')/@/@'
            recs.append(rec)
        try:
            session.add_all(recs)
            session.commit()
        except Exception as e :
            session.rollback()
            return [False,"%s %s" % (cmd,e),'']
        return [True,cmd,','.join(codes)]

    @staticmethod
    def _update_items(model,uflds,**kwargs) :
        cmd = kwargs.get('oper')
        user_role = kwargs.get('user_role')
        if not model.colPermission ('__table__',user_role,'e') :
            return [False,"permission denied",'']
        session = model.Session()
        recs = []
        qry = session.query(model.odb)
        head = model.json_loads(kwargs['head'])
        items = model.json_loads(kwargs['items'])
        for item in items :
            vcrec = None
            try:
                rec = qry.filter(model.odb.code==item['code']).one()
                model.concurrent_ctrl(rec,last_updated=item.get('last_updated'),**kwargs)
                vcrec = model.version_ctrl(rec,**kwargs)
            except Exception as e :
                return [False,"%s, %s" % (item['code'],e),'']
            chflag = False
            for f in uflds:
                pfix = ''
                if f[0] in '!&' :
                    pfix = f[0]
                    f = f[1:]
                v = '' if pfix=='!' else item.get(f,head.get(f))
                try:
                    if model.update_field(rec,f,v,user_role,'e') :
                        chflag = True
                except Exception as e :
                    return [False,"%s, %s" % (item['code'],e),rec.id]
            if chflag :
                if vcrec is not None : recs.append(vcrec)
                recs.append(rec)
        try:
            session.add_all(recs)
            session.commit()
        except Exception as e :
            session.rollback()
            return [False,"%s %s" % (cmd,e),'']
        return [True,cmd,'']

    @staticmethod
    def jqgrid_edit(model,**kwargs) :
        _wrapper_ = model.modeler._wrapper_
        cmd = kwargs.get('oper')
        id = kwargs.get('id','')
        if cmd=='take' :
            uflds = ['&take_date','&taker','&taker_price']
            return _wrapper_._update_items(model,uflds,**kwargs)
        if cmd=='sell' :
            uflds = ['&sell_date','&buyer','&sell_price','sell_site','receive_date','receive_type']
            return _wrapper_._update_items(model,uflds,**kwargs)
        if cmd=='keep' :
            uflds = ['&keep_date','&keeper','!take_date','!taker','!taker_price']
            return _wrapper_._update_items(model,uflds,**kwargs)
        if cmd=='buy' :
            return _wrapper_._new_items(model,**kwargs)

        return model.jqgrid_edit_base(**kwargs)
