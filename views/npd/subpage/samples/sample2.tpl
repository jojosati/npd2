%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%#include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg']
%[locals().update({k:_vars[k]}) for k in _require_vars]

<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
<div id="sample2-page"><b>sample2</b> </div>
<script>
//<!-- jquery ui tabs widget with taxonomy/acat -->
$.getJSON('/{{suburl}}/ajax/taxonomy/acat', function(data) {
	var items = [];
	$.each(data, function(key, val) {items.push('<li><a href="/{{suburl}}/subpage/grid//@f-acat-'+val+'">'+val+'</a></li>');});
	$('<div>')
		.append($('<ul>', {'class': 'ui-widget-content','html': items.join('')}))
		.tabs({cache:true})
		.appendTo('#sample2-page');
});
</script>