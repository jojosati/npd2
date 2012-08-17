# -*- coding: utf-8 -*-
# -------------------------------------
# framework definitoin part
# custom update to individual field
_fld_options_ = {
    # ข้อมูลทั่วไป
##    'acat' :  {'csv_field': 'ชนิด', 'required': True,}  , # - ROLEX, กำไล, จี้, ฯลฯ
##    'code' : {'csv_field': 'รหัส', 'access':'gvi', 'required': True,},
##    'detail' : {'csv_field': 'รายการสินค้า', 'required': True, 'colwidth' : 8,},
##    'weight' : {'csv_field': 'น้ำหนัก',},
##    'serial' : {'csv_field': 'เบอร์',},
##    'condition' : {'label' : 'สภาพ', 'colwidth' : 2,}, # +++ สภาพของทรัพย์ - ชำรุด, ใหม่, xx%
##    'memo' : {'access' : 'vae', 'colwidth' : 8, 'rowlength' : 3,}, # +++

    # ต้นทุน - costing
##    'base_cost' : {'csv_field': 'ทุน', 'access':'vae', 'colgroup':2,} , #(ราคาซื้อ)
##    'extra_cost' : {'csv_field': 'ปรับปรุง', 'access':'vae', 'colgroup':2,},
##    'mark_cost' : {'csv_field': 'ทุนร้าน', 'access':'vae', 'colgroup':2,} , # (ราคาซื้อ + คชจ.ปรับปรุง + markup คนหาของ)

    # ราคาขาย - pricing
##    'lowest_price' : {'csv_field': 'ขายประเมิน', 'access':'vae', 'colgroup':3,}, #(ราคาต่ำสุด ที่ขายได้)
##    'target_price' : {'csv_field': 'ราคาตั้งขาย', 'colgroup':3,},

    # เจ้าของ - owning
##    'buy_date' : {'csv_field': 'วันที่ซื้อ', 'access':'vae', 'colgroup':4,},
##    'owner' : {'csv_field': 'ซื้อจาก', 'access':'gvae', 'access':'vae', 'colgroup':4,},
##    'buy_cond' : {'label': 'เงื่อนไขซื้อ', 'access':'vae', 'colwidth' : 2, 'colgroup':4,}, # +++ เงื่อนไขซื้อ - จำนำ, ฝากขาย

    # ผู้เก็บรักษา - keeping
##    'keep_date' : {'csv_field': 'วันที่', 'label': 'วันที่เก็บ', 'colgroup':5,},
##    'keeper' : {'csv_field': 'ที่เก็บ', 'colgroup':5,},
##    'take_date' : {'csv_field': 'วันที่ยืม', 'access':'vae', 'colgroup':6,},
##    'taker' : {'csv_field': 'ผู้ยืม', 'access':'ve', 'colgroup':6,},
##    'taker_price' : {'csv_field': 'หมายเหตุ', 'label':'ราคายืม', 'csv_exception': 'memo', 'access':'ve', 'colgroup':6,}, #(ราคายืม = ราคาที่ตั้งขายให้ผู้ยืม)

    # ประวัติขายและรับชำระ - selling
##    'sell_date' : {'csv_field': 'วันที่ขาย', 'access':'ve', 'colgroup':7,},
##    'sell_site' : {'csv_field': 'สถานที่ขาย', 'access':'ve', 'colgroup':7,},
##    'buyer' : {'csv_field': 'ผู้ซื้อ', 'label' : 'ขายให้', 'access':'ve', 'colgroup':7,},
##    'sell_price' : {'access':'ve', 'csv_field': 'ราคาขาย', 'colgroup':7,}, #(ราคาที่ขายได้จริง)

    # การชำระ - receiving
##    'receive_date' : {'csv_field': 'วันที่รับ', 'label': 'วันที่รับ', 'access':'ve', 'colgroup':8,},
##    'receive_type' : {'csv_field': 'ชนิดรับ', 'label': 'ชนิดเงินรับ', 'access':'ve', 'colgroup':8,},
    }

_options_ = {
##    'modelname' : "Assets",
##    'caption' : 'Precious Assets',
##    'autocomplete_scope' : {
##            'acat': ['code','detail','weight','serial'],
##            'detail':['memo'],
##            },
##    'ajax_fields' : [],
    }

_permissions_ = {
##    "developer" : {'*' : None,'code':'gave',}, # use default access in colModel, except field 'code'
##    "administrator" : {'*' : None,'code':'gave',},
##    "manager" : {'*' : None,'code':'gave',},
##    "editor" : {
##                '__table__' : 'gpsqvae', # grid, pivot-url, search, quick search, view, add, edit
##                '*' : None,
##                'code':'gave',
##                'base_cost' : '', # not allow all
##                'extra_cost' : '',
##                'mark_cost' : '',
##                '_hashlev_':2,
##                },
##    "viewer" : {
##                '__table__' : 'gpsqv', # grid, pivot-url, search, quick search, view,
##                'acat' : 'gv',
##                'code' : 'gv',
##                'detail' : 'gv',
##                'weight' : 'gv',
##                'serial' : 'gv',
##                'condition' : 'gv',
##                'target_price' : 'gv',
##                'keeper' : 'gv',
##                },
##    '' : {
##                '__table__' : '',
##        },
##    # other role
##    "*" : {
##                '__table__' : 'gq',
##                '__hashlev__' : -3,
##                'acat' : 'gv',
##                'code' : 'gv',
##                'detail' : 'gv',
##                'weight' : 'gv',
##                'condition' : 'gv',
##                'target_price' : 'gv',
##                },
    }



