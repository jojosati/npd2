# -*- coding: utf-8 -*-

## .. gt/lt, ... ge/lt, .... ge/le, ..... gt/le
rangesign = '..'
andwords = ['and','และ']
orwords = ['or','หรือ']
notwords = ['not','ไม่','ไม่มี']
re_range = '(['+rangesign[0]+']{'+str(len(rangesign))+','+str(len(rangesign)+3)+'})'
re_openrange ='^(?:\s*)([<>]=?)'
re_pageoption = r'(?<!~)(?:/+)'
#re_subqry = r'(?:\s+|^|(?<=[)\]]))((?:not\s*|ไม่\s*|ไม่มี\s*|!)?(?:\([^)]+\)|\[[^\]]+\]|\'(?:[^\']|\'\S)+\'|"(?:[^"]|"\S)+"))'
re_subqry = r'(?:\s+|^|(?<=[)\]]))((?:'+r'\s*|'.join(notwords)+r'\s*|'+r'!)?(?:\([^)]+\)|\[[^\]]+\]|\'(?:[^\']|\'\S)+\'|"(?:[^"]|"\S)+"))'
re_extractqry = r'(\([^)]+\)|\[[^\]]+\]|\'(?:[^\']|\'\S)+\'|"(?:[^"]|"\S)+")'
re_quoteqry = r'(\s*(?:\'(?:[^\']|(?<=\\)\')+\'|"(?:[^"]|(?<=\\)")+")\s*)'
re_blockqry = r'(\s*(?:\((?:[^)]|(?<=\\)\))+\)|\[(?:[^\]]|(?<=\\)\])+\])\s*)'
re_subqryvar = r'\$qry([0-9]+)'
#re_and_or = r'(\s+(?:or|หรือ|and|และ)\s+|\s*(?:\&\&|\|\|)\s*)'
re_and_or = r'(\s+(?:'+'|'.join(orwords)+'|'+'|'.join(andwords)+r')\s+|\s*(?:\&\&|\|\|)\s*)'
#re_and_or = r'\s*(\|\||\&\&)\s*'
re_nowvar = r'((?:\$(?:now(?:\.\w+)*|period))\s*(?:\(.*\))*(?:\.\w+)*)'
re_maxonomy = r'([0-9]{3,})'
re_tokentag = r'(\S{3,})'
re_inlinetag = r"\[\[(\S{3,})\]\]"