%if '_plugin_' not in _vars: _vars['_plugin_'] = []
%if 'gridwrapper-options' not in _vars['_plugin_'] :
%_vars['_plugin_'].append('gridwrapper-options')
%# ---- server page script prepare gridoptions ----
%if 'gridwrapper_options' not in _vars:
%include helper/language _vars=_vars
%suburl=_vars['suburl']
%language=_vars['language'] or 'en'
%if _vars.get('layout_loaded') != '~' :
<script type='text/javascript'>
//$('head')
//.append('<link type="text/css" href="/{{suburl}}/resource/css/ui.jqgrid.css" rel="Stylesheet">')
//.append($('<script>',{type:"text/javascript",src:"/{{suburl}}/resource/js/i18n/grid.locale-{{language}}.js"}))
//.append($('<script>',{type:"text/javascript",src:"/{{suburl}}/resource/js/jquery.jqGrid.min.js"}))
//.append($('<script>',{type:"text/javascript",src:"/{{suburl}}/resource/js/jqGridWrapper.js"}))
//.append($('<script>',{type:"text/javascript",src:"/{{suburl}}/resource/js/jquery.printElement.js"}))
//;
</script>
<link type="text/css" href="/{{suburl}}/resource/css/ui.jqgrid.css" rel="Stylesheet">
<script type="text/javascript" src="/{{suburl}}/resource/js/i18n/grid.locale-{{language}}.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.jqGrid.min.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jqGridWrapper.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.printElement.js"></script>
%end
%def gridwrapper_options(vars):
%def jsval(val) :
%	if val is None : return 'undefined'
%	if isinstance(val,bool): return 'true' if val else 'false'
%	if isinstance(val,(list,tuple)):
%		ret = ''
%		for x in val : 
%			if ret : ret += ','
%			ret += jsval(x)
%		end
%		return '['+ret+']'
%	end
%	if isinstance(val,(dict)):
%		ret = ''
%		for x in val : 
%			if ret : ret += ','
%			ret += jsval(x)+':'+jsval(val[x])
%		end
%		return '{'+ret+'}'
%	end
%	if isinstance(val,basestring) :
%		try : float(val); return val
%		except : pass
%		if val.lower() in ['true','false']: return val.lower()
%		if val.lower() in ['none','undefined']: return 'undefined'
%		return '"'+val.replace('"','\\"')+'"'		
%	end
%	return str(val)
%end
%def listformatter(val): return jsval(val.split('-')) 
%def gridkwoption(kw,default=None,pgdefault=None,ifempty=None,formatter=jsval): 
%	val = vars.get('kwoptions',{}).get(kw,pgdefault if (pgdefault is not None and kw in vars['pageoptions']) else vars.get('grid_'+kw,default))
%	return formatter(val or ifempty)
%end
%gopt = {'_able':['*'],'vscroll':['',1],'addnew':[False,True]}
%gopt.update({'colreorder':[False,True],'scroll':[None,1],'showcols':[],'form_colnum':[None,None,2]})
%gopt.update({'rownum':[None,None,20],'rownumlist':[None,None,'10-20-50-100',listformatter]})
%gopt.update({'autofit':[None,None,'',listformatter],'height':[],'width':[],'resizable':[False,True],'minwidth':[None,None,350]})
%gopt.update({'sort':[],'summary':[],'tbsrch':[False,True],'searchonenter':[]})
%gopt.update({'language':[None,None,vars.get('language') or 'en']})
%gopt.update({'caption':[vars.get('modeler_options',{}).get('caption')],'shortdesc_field': [vars.get('modeler_options',{}).get('shortdesc_field')]})
%gopt.update({'media_field':[vars.get('modeler_options',{}).get('media_field',{}).keys()]})
%# --- start function gridoptions
%	tab = '	'
%	nl = '\n'
%	script = ''
%	script += tab+'datatype:"json"'+nl
%	script += tab+',gridview:true'+nl
%	script += tab+',scrollrows:true'+nl
%	script += tab+',viewrecords:true'+nl
%	script += tab+',show_history:true'+nl
%	script += tab+',show_invalidity:true'+nl
%	script += tab+',tagging_field:'+jsval(vars.get('modeler_options',{}).get('tagging_control',''))+nl
%	script += tab+',grid_url:'+jsval('/'+vars['suburl']+'/ajax/jqgrid')+nl
%	script += tab+',edit_url:'+jsval('/'+vars['suburl']+'/ajax/jqgrid/edit')+nl
%	script += tab+',taxonomy_url:'+jsval('/'+vars['suburl']+'/ajax/taxonomy')+nl
%	script += tab+',autocomplete_url:'+jsval('/'+vars['suburl']+'/ajax/autocomplete')+nl
%	script += tab+',media_url:'+jsval('/'+vars['suburl']+'/media')+nl
%	if _vars['user_role'] in ['manager','administrator','developer']:
%		script += tab+',pivot_url:'+jsval('/'+_vars["suburl"]+'/'+_vars["urlsubpage"])+nl;
%	end
%	script += tab+',export_url:'+jsval('/'+vars['suburl']+'/csv/jqgrid')+nl
%	for k in ['suburl','urlsubpage','pageoptions','urltagstr','summary_keys','ajax_fields'] :
%		if vars.get(k) is not None : script += tab+','+k+':'+jsval(vars.get(k))+nl
%	end
%	script += tab+',colmodels:'+jsval(vars.get('ajax_extfields'))+nl
%	script += tab+',autocomplete_scopes:'+jsval(vars.get('modeler_options',{}).get('autocomplete_scope'))+nl
%	for k in gopt :
%		v = gridkwoption(k,*gopt[k])
%		if v!='undefined' : script += tab+','+k+':'+v+nl
%	end
%	return '{'+nl+script+'}'
%end
%_vars['gridwrapper_options'] = gridwrapper_options
%end
%# ---- end of server page script prepare gridoptions ----
%end

