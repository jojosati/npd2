
%if 'naked' in _vars.get('pageoptions',[]):
<div id="pagefooter" style="padding-top:8px;"></div>
%else:
<div id="pagefooter" style="padding-top:8px;">
<table class="ui-widget ui-widget-content ui-corner-all" style="width:100%;font-size:80%;"><tr>
	<td>
	<span>inspired by <a href="http://admthai.homeip.net">sathit jittanupat</a></span>
	</td>
	<td style="text-align:right">
	<span>powered by 
	<a href="http://www.python.org/">python</a> (<a href="http://bottle.paws.de/">bottle</a>, <a href="http://www.sqlalchemy.org/">sqlalchemy</a>) 
	<a href="http://jquery.com/">jquery</a> (<a href="http://jqueryui.com/">jquery ui</a>, <a href="http://www.trirand.com/blog/">jqGrid</a>)
	</span>
	</td>
</tr></table>
</div>
%end