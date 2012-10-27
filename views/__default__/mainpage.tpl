%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-netscraft',{'_vars':_vars}); _vars['layout_loaded'] = 'pending'
<div id="content" style="padding:1em;">
%if _vars.get('subpage')=='mainpage': _vars['subpage'] = ''
%_vars['subpage'] = _vars.get('subpage','')
%if not _vars['subpage'] or _vars['subpage'].endswith('/') : _vars['subpage'] += 'index'
%if _vars['subpage'] :
%if _vars.get('_server_',{}).get('subpage_ajax',True):
%include helper/subpage-ajax _vars=_vars
%else :
%_include('subpage/'+_vars['subpage'],_stdout, _vars=_vars)
%end
%end
</div>

 
