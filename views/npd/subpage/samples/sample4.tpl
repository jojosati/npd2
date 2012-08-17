%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg']
%[locals().update({k:_vars[k]}) for k in _require_vars]

<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
<div id='workspace'>
<table><tr>
<td id="left-container" style="padding:0 0.5em 0 0.5em;vertical-align:top;">
<div id="printarea">
<div id="left-head"></div>
<div id="left-body"></div>
</div>
</td>
<td  id="right-container" style="padding:0 0.5em 0 0.5em;vertical-align:top;">
<div id="right-head"></div>
<div id="right-body"></div>
</td>
</tr></table>
</div>
<script type="text/javascript">
	login_tag('#header_login_block')
	var timeoutHnd;
	var gridoptions = {{!_vars['gridwrapper_options'](_vars)}};
	$.extend(gridoptions, {
		showcols: 'acat,code,detail,weight,lowest_price,target_price,keeper'
		,_able: 'gq'
		,width: $(window).width()*0.6
		,height: $(window).height()*0.5
		,autofit: false
		});
	var grid$ = jqGrid$(gridoptions);
	grid$.gridDOM({
		container:'#right-body'
		,ready: function($dom,$grid){
			var $table = this.tableDOM(this.inputDOM({
								inputs:['acat','keeper']
								,showlabel:'top'
								,initmode:'search'}))
				.css('width','95%')
				.appendTo('#left-body');
	
			function pivotcmds (name,val) {
				var pageoptions = gridoptions.pageoptions;
				var cmd = '@f-'+name+'-' ;
				for (var i=0;i<pageoptions.length;i++) {
					if (pageoptions[i].indexOf(cmd)==0) {
						pageoptions.splice(i,1);
						break;
					}
				}
				if (typeof val=='string' &&  val!='') pageoptions.push(cmd+val);

				var postdata = $grid.jqGrid('getGridParam','postData') ;
				if (pageoptions) {
					var pv = [];
					for (var c in pageoptions) {
						c = pageoptions[c];
						if (c[0]=='@') {
							pv.push(c)
					}}
					postdata.pivotcmds = grid$.array2json(pv);
				}
				grid$.scheduleReload();
			}
			$('input[name],textarea[name]',$table).each(function(){
				$(this)
				.keyup(function(){
					pivotcmds($(this).attr('name'),$(this).val());
					})
				.bind('autocompletechange',function(){
					pivotcmds($(this).attr('name'),$(this).val());
					});
			});
		}
	});

</script>