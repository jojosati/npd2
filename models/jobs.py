# -*- coding: utf-8 -*-

# schema part
# warning:  any changes to _tablename_, _fields_[name, datatype, index,unique,]  may effect to existed table
_tablename_ = "jobs"
_fields_ = [
    # common
    {'name': 'jobtype', 'options' : {'label':'//th:ประเภทงาน', 'required': True, 'colgroup':'common'} } ,
    {'name': 'jobno', 'index':True, 'unique':True, 'options' : {'label':'//th:เลขที่','access':'gva', 'required': True, 'colgroup':'common',}},
    {'name': 'start_date', 'datatype' : 'Date', 'options' : {'label':'//th:วันที่เริ่ม','required': True, 'colgroup':'common',}},
    {'name': 'end_date', 'datatype' : 'Date', 'options' : {'label':'//th:วันที่จบ','colgroup':'common',}},
    {'name': 'jobstatus', 'options' : {'label':'//th:สถานะ','access':'gve','colgroup':'common',}},
    {'name': 'client', 'options' : {'label':'//th:ลูกค้า','required': True, 'colgroup':'mission', 'colwidth' : 8, 'rowlength' : 1,}},
    {'name': 'client_info', 'datatype': 'Text', 'options' : {'label':'//th:ที่อยู่','access' : 'vae', 'colgroup':'mission', 'colwidth' : 8, 'rowlength' : 2,} },

    # mission
    {'name': 'site', 'options' : {'label':'//th:สถานที่ใช้งาน','required': True, 'colgroup':'mission-site',} },
    {'name': 'machine', 'options' : {'label':'//th:หมายเลขรถ','colgroup':'mission-machine',} },
    {'name': 'driver', 'options' : {'label':'//th:พนักงานขับ','access' : 'vae', 'colgroup':'mission-staff',}},
    {'name': 'driver2', 'options' : {'label':'//th:พนักงานขับ2','access' : 'vae', 'colgroup':'mission-staff',}},
    {'name': 'transportation', 'options' : {'label':'//th:การขนส่ง','colgroup':'mission-transport',} },
    {'name': 'orderer', 'options' : {'label':'//th:ผู้สั่งงาน','access' : 'vae', 'colgroup':'mission-staff',}},
    {'name': 'holder', 'options' : {'label':'//th:ผู้ควบคุมงาน','access' : 'vae', 'colgroup':'mission-staff',}},

    # quoting
    {'name': 'charge_type', 'options' : {'label':'//th:เงื่อนไขเช่า','access':'vae', 'colgroup':'quoting',}},
    {'name': 'charge_rate', 'datatype' : 'Float', 'options' : {'label':'//th:อัตราค่าเช่า','access':'vae', 'colgroup':'quoting',} } ,
    {'name': 'charge_ot', 'datatype' : 'Float', 'options' : {'label':'//th:อัตราล่วงเวลา','access':'vae', 'colgroup':'quoting',}},
    {'name': 'charge_tp', 'datatype' : 'Float', 'options' : {'label':'//th:ค่าบริการขนส่ง','access':'vae', 'colgroup':'quoting',}} ,

    # billing
    {'name': 'bill_total', 'datatype' : 'Float', 'options' : {'label':'//th:ยอดชำระสุทธิ','access':'ve', 'colgroup':'billing',}} ,
    {'name': 'bill_credit', 'datatype' : 'Float', 'options' : {'label':'//th:เงื่อนไขชำระ','access':'ve', 'colgroup':'billing',}} ,

    # memo
    {'name': 'memo', 'datatype': 'Text', 'options' : {'label':'//th:บันทึก','access' : '', 'colgroup':'memo', 'colwidth' : 8, 'rowlength' : 4,} }, # +++
    ]

# -------------------------------------
# framework definitoin part
# custom update to individual field
_fld_options_ = {
    }

_options_ = {
    'suburl' : 'crane',
    'sql_dbfile': 'db/crane.sqlite.db',
    'modelname' : "Jobs",
    'caption' : 'P.Siriyont Jobs//th:ป.ศิริยนต์',
    'autocomplete_scope' : {
            'transportation': ['transporter'],
            'jobtype': ['jobno','machine','driver','driver2'],
            'client':['client_info','site'],
            'machine':['machine_info'],
            },
    'autocomplete_mixin' : {
            'driver': ['driver','driver2','orderer','holder'],
            'driver2': ['driver2','driver','orderer','holder'],
            'orderer': ['orderer','holder','driver','driver2'],
            'holder': ['holder','orderer','driver','driver2'],
            },
    'maxonomy_suppressnumsize' : 2,
    'maxonomy_format' : {'jobno':'%y%m-0000'},
    }

_permissions_ = {
    "developer" : {'*' : None,'code':'gave',}, # use default access in colModel, except field 'code'
    "administrator" : {'*' : None,'code':'gave',},
    "manager" : {'*' : None,'code':'gav','memo':'ave'},
    "editor" : {
                '__table__' : 'gpsqvae', # grid, pivot-url, search, quick search, view, add, edit
                '*' : None,
                'code':'gav',
                'base_cost' : '', # not allow all
                'extra_cost' : '',
                'mark_cost' : '',
                'buy_date' : 'av',
                'owner' : 'av',
                'buy_cond' : 'av',
                '_hashlev_':2,
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
                },
    '' : {
                '__table__' : '',
        },
    # other role
    "*" : {
                '__table__' : 'gq',
                '__hashlev__' : -3,
                'acat' : 'gv',
                'code' : 'gv',
                'detail' : 'gv',
                'weight' : 'gv',
                'condition' : 'gv',
                'target_price' : 'gv',
                },
    }

