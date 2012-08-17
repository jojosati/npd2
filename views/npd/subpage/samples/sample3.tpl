%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%#include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg']
%[locals().update({k:_vars[k]}) for k in _require_vars]

<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
<div id="sample3-page"><b>sample3</b> </div>

<script>
//<!-- must login before get taxonomy -->
login_tag('<div/>').appendTo('#sample-page');
//<!-- select widget with taxonomy/acat -->
$.getJSON('/{{suburl}}/ajax/taxonomy/acat', function(data) {
	var items = ['<option value="">select category</option>'];
	var subpage = $('<div/>');
	$.each(data, function(key, val) {items.push('<option value="' + val + '">' + val + '</option>');});
	$('<div>ajax/taxonomy "acat" select </div>').append(
		$('<select/>', {'class': 'ui-widget-content','html': items.join('')})
			//<!-- ajax load subpage when selection change -->
			.change( 
				function(){subpage.load('/{{suburl}}/subpage/grid//@f-acat-'+$(this).val());}
				)
		).appendTo('#sample3-page');
	subpage.appendTo('#sample3-page');
});

</script>