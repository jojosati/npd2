%_require_vars=['suburl','subpage','pagetag','urltagstr']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_url = '/'+suburl+'/subpage/'+subpage + ((urltagstr+pagetag) if pagetag else '')
<div id="contentajax"><span class="ui-state-highlight" style="padding:0 1em 0 1em;border:solid thin;line-height:400%;">... loading content from <b>{{_url}}</b></span></div>
<script type="text/javascript">
$(document).ready(function() {
	var url = '{{!_url}}';
%if _vars['_server_'].get('debug') :
	if (url.indexOf('?')<0) url+='?'
	else url += '&';
	url += 'nd='+ new Date().getTime();
%end
    $('#contentajax').load(url);
    });
</script>
