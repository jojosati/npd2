
%_subpage = _vars.get('subpage')
%if _vars.get('subpage')=='subpage': _vars['subpage'] = ''
%_vars['subpage'] = _vars.get('subpage','')
%if not _vars['subpage'] or _vars['subpage'].endswith('/') : _vars['subpage'] += 'index'
%if _vars['subpage'].startswith('subpage/') : _vars['subpage'] = _vars['subpage'].replace('subpage/','',1)
%if _vars['subpage'] :
%if _vars.get('_server_',{}).get('subpage_ajax',True):
%include helper/subpage-ajax _vars=_vars
%else :
%_include('subpage/'+_vars['subpage'],_stdout, _vars=_vars)
%end
%end
%_vars['subpage'] = _subpage
%if _subpage is None : del _vars['subpage']
%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})

 
