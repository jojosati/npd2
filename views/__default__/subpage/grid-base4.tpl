%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
<div id="grid-base4-x" class="grid-base4-container"></div>

<script type="text/javascript">
$(document).ready(function() {
	var gridoptions = {{!_vars['gridwrapper_options'](_vars)}};
	gridoptions.login_tag = login_tag;
	var $container = $('#grid-base4-x');
	var id ;
	if ($container) {
		var i = 0 ;
		while(true) {
			i++;
			id = 'grid-base4-'+i;
			if ($('#'+id).length==0) break;
		} 
		$container.attr('id',id);
	}
	jqGrid$(gridoptions).gridDOM({container: $container});
});
</script>

