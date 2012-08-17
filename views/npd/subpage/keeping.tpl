%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_msg['keeping_entry'] = 'Keeping Entry//th:ทำรายการเปลี่ยนที่เก็บ/รับคืนยืม'
%_msg['taken_summary']='Taken({1}) {2}//th:ยืม({1}) {2}'
%_msg['show_taken_detail']='Show taken details//th:แสดงรายการยืมเดิม'
<div id='keeping-workspace'>
<table><tr>
<td id="keeping-container" style="padding:0 0.5em 0 0.5em;vertical-align:top;">
<div id="keeping-printarea">
<div id="keeping-head"></div>
<div id="keeping-body"></div>
</div>
</td>
<td  id="keeping-instk-container" style="padding:0 0.5em 0 0.5em;vertical-align:top;">
<div id="keeping-instk-body"></div>
</td>
</tr></table>
</div>
<script type="text/javascript">
function taking() {
	var frame = $('.gridwrapperframe').first() ;
	var destwidth = 490;
	//alert ($(frame).width());
	var srcoptions = {{!_vars['gridwrapper_options'](_vars)}};
	srcoptions.pageoptions.unshift('@f-taker-');
	srcoptions.pageoptions.unshift('@f-buyer-');
	srcoptions.showcols = 'code,condition,detail,keeper,!last_updated' ;
	//srcoptions.width = ($(frame).width() * 0.9) - destwidth;
	//srcoptions.height = $(window).height()*0.4;
	srcoptions.autofit = [-625,0.4];
	srcoptions.caption = 'Sellable//th:พร้อมขาย'
	srcoptions._able = 'gq';
	//delete srcoptions.autofit ;	
	
	var destoptions = {
		colmodels : srcoptions.colmodels
		,language : srcoptions.language
		,datatype: 'local'
		,autofit: [destwidth,'auto']
		//,width: destwidth, height: 'auto' //$(window).height()*0.4
		//,height: '100'
		,showcols: 'code,detail,keeper,taker,!last_updated'
		,_able: 'gd'
		,caption: ''
		//,cellEdit: true
		,edit_url: '/{{_vars["suburl"]}}/ajax/jqgrid/noedit' // require to enable add/edit/del feature
		,autocomplete_url: srcoptions.autocomplete_url
		,autocomplete_scopes: srcoptions.autocomplete_scopes
		,rowList: []
		,pginput: false
		,pgbuttons: false
		//,footerrow: true
		};

	var srcgrid = jqGrid$(srcoptions);
	var $src = srcgrid.$grid;
	var destgrid = jqGrid$(destoptions) ;
	var $dest = destgrid.$grid;

	function insert_destRow(rowdata,ask) {
		var rowid = 'dnd_'+rowdata.code ;
		function isexist(){
			var data = $dest().jqGrid('getGridParam','data') ;
			for (var r in data) {
				r = data[r];
				if (r.code==rowdata.code)
					return true ;
				}
			return false ;
			}
		if (isexist()){
			if (!ask) 
				destgrid.alertDialog(rowdata.code+', '+destgrid._('Data_existed')) ;
			return ;
			}
		if (ask) {
			id = 'askinsert-keeping';
			if ($('#'+id).length==0) {
				destgrid.alertDialog('<span id="'+id+'">'+rowdata.code+'</span>, '+destgrid._('select found item?//th:เลือกรายการที่พบ?'),
				{buttons:[
					{text:destgrid._('OK'),click:function(){
						$(this).dialog('close');
						if (isexist()) {
							destgrid.alertDialog(rowdata.code+', '+destgrid._('Data_existed')) ;
							return ;
							}
						$dest().jqGrid('addRowData',rowid,rowdata,'last');
						}}
					]
					}) ;
				} 
		}else {
			$dest().jqGrid('addRowData',rowid,rowdata,'last');
		}
		return ;
	}

	function add_destRow(rowid) {
		rowdata = $(this).jqGrid('getRowData',rowid);
		insert_destRow(rowdata) ;
	}
	
	function auto_add_destRow(grid) {
		var ids = $(grid).jqGrid('getDataIDs') ;
		if (ids.length==1) {
			insert_destRow($(grid).jqGrid('getRowData',ids[0]),true);
		}
	}

	function sum_footerTotal(grid) {
/*		var data = $(grid).jqGrid('getGridParam','data') ;
		var total = 0;
		for(var r in data){
			r = data[r];
			if(r.taker_price){
				total += Number(r.taker_price);
				}
			}
		$(grid).jqGrid('footerData','set',{detail:destgrid._('Total'),taker_price:total});
*/	}
	function resetInput($table){
		$dest().jqGrid('clearGridData');
		$('[name="taker"],[name="keeper"]',$table)
		.each(function(){$(this).val('').blur();}) ;
	}
	function submitkeeping($table,data){
		var url = '/{{suburl}}/ajax/jqgrid/edit'
		var	mtype = 'GET'
		var postdata = {};
		var head={};
		var items=[];

		$('input[name],textarea[name]',$table).each(function(){
			head[$(this).attr('name')]= $(this).val();
			});
		for (var r in data){
			items.push({code:data[r].code});
		}
		postdata['head'] = destgrid.array2json(head);
		postdata['items'] = destgrid.array2json(items);
		postdata['oper'] = 'keep';
		$.ajax({
			type:mtype, url:url, data:postdata
			,success: function(data){
				if (data[0]==false){
					destgrid.alertDialog(data[1],{title:destgrid._('Error'),dialogClass:'ui-state-error'});
				} else {
					$src().trigger("reloadGrid");
					destgrid.alertDialog(destgrid._('Success')
						,{buttons: [
							{text:destgrid._('OK'),click:function(){$(this).dialog('close');}}
							,{text:destgrid._('Print'),click:function(){printTaking($table);}}
							]
						,close: function(){resetInput($table);}
						});
				}
			}
			,dataType: 'json'
			})
			.error(function(obj,status,msg){destgrid.alertDialog(status+', '+msg);});
	}
	function clearkeeping($table){
		/*if ($dest().jqGrid('getGridParam','reccount')>0)*/{
			destgrid.alertDialog(destgrid._('Clear_data?')
				,{	title:destgrid._('Warning')
					,buttons:[
						{text:destgrid._('Clear')
						,click:function(){
							resetInput($table);
							$(this).dialog('close');}
						}
						,{text:destgrid._('Cancel'),click:function(){$(this).dialog('close');}}
						]
				});
		}
	}
	function printTaking($table) {
		$("#keeping-printarea")
		.printElement({
			pageTitle:'keeping-'+$.datepicker.strftime('%Y%m%d%H%M%S-')+$('[name="taker"]',$table).val().substr(0,20).replace(/[\.\\'\"\\/ -]/g,'_')
		});
	}
	function takerGridDialog(taker) {
		var takeroptions = {{!_vars['gridwrapper_options'](_vars)}};
		var qtaker = '"'+taker.replace(/\\/g,'\\\\').replace(/\"/g,'\\\"')+'"'
		takeroptions.pageoptions.unshift('@f-taker-'+qtaker);
		takeroptions.pageoptions.unshift('@f-buyer-');
		takeroptions.caption = '';
		takeroptions.showcols = 'code,detail,take_date,taken_days,taker_price,!taker,!keeper,!last_updated' ;
		takeroptions.width = $(window).width()*0.45;
		takeroptions.height = $(window).height()*0.4;
		takeroptions._able = 'gq';
		delete takeroptions.autofit ;
		var takergrid = jqGrid$(takeroptions);
		takergrid.gridDOM({
			beforeInitDOM: function(gopt) {
				//gopt.grid.afterSaveCell = function() {sum_footerTotal(this);}
				//gopt.grid.gridComplete = function(){sum_footerTotal(this);}
				gopt.grid.ondblClickRow = add_destRow;
				gopt.grid.gridComplete = function(){auto_add_destRow(this);};
				}
			,ready : function(dom){
				this.$grid().jqGrid('gridDnD',{
						connectWith:'#'+$dest().attr('id')
						,droppos:'last'
						,dropbyname:true
						,beforedrop: function(event,ui,rowdata){
							ui.helper.dropped = false;
							insert_destRow(rowdata);
							}
					})
				}
		}).dialog({
			width:'auto'
			,title:taker
			,close:function(){delete takergrid;}
			,zIndex:200
			});

	}
	function takenSummary(container,taker) {
		if (taker=='') return;
		var url = '/{{suburl}}/ajax/jqgrid'
		var	mtype = 'GET'
		var postdata = {};
		var qtaker = '"'+taker.replace(/\\/g,'\\\\').replace(/\"/g,'\\\"')+'"'
		postdata.pivotcmds = destgrid.array2json(['@f-taker-'+qtaker,'@f-buyer-']);
		postdata._summary = '1';
		postdata._cols= destgrid.array2json(['taker','code','taker_price']);
		postdata.sidx = 'taker';
		$.ajax({
			type:mtype, url:url, data:postdata
			,success: function(data){
				var $info = $('<span>',{style:'padding:0 0.5em 0 0.5em;'});
				if ($.isPlainObject(data) && data.records==1){
					var r = data.rows[0].cell;
					if (r) {
						$info
						.html($.jgrid.format(destgrid._('{{_msg['taken_summary']}}'),r[0],r[1],$.fmatter.util.NumberFormat(r[2],$.jgrid.formatter.number)))
						;
					}
					$info
					.attr('title',destgrid._('{{_msg['show_taken_detail']}}')+' - '+r[0])
					.button()
					.click(function(){
							takerGridDialog(taker);
						});
				}
				$info.appendTo(container);
			}});
	}
	//--------------------------------
	$('#keeping-instk-body').hide();
	$('<div>',{style:'text-align:right;margin-bottom:1em;width:100%;','class':'ui-widget-header ui-corner-all'})
	.append($('<span>',{style:'float:left',html:'{{_m("keeping_entry")}}'}))
	.append(login_tag())
	.append($('<span>',{title:'{{_m("toggle_takable_list")}}'})
		.button({text: false,icons: {primary:'ui-icon-transferthick-e-w'}})
		.click(function(){$('#keeping-instk-body').toggle({effect:'slide',speed:1000});}))
	.prependTo("#keeping-printarea");

	// checking permission
	var chklst = 'take_date,taker,taker_price,keep_date,keeper';
	if (destgrid.chkPermission(chklst,'e')==false){
		destgrid.errDOM(destgrid._('Not_allow_here')).appendTo('#keeping-body');
		return;
	}
	//var xx='';for(var x in $.fn.fmatter)xx+=x+'=\n'/*+$.fn.fmatter[x]+'\n'*/;alert(xx);
	destgrid.gridDOM({
		container: "#keeping-body"
		,beforeInitDOM: function(gopt) {
			gopt.grid.afterSaveCell = function() {sum_footerTotal(this);};
			gopt.grid.gridComplete = function(){sum_footerTotal(this);};
			gopt.form.del.afterComplete = function(){sum_footerTotal($dest());};
			}
		,ready: function($grids,$grid){
			var $table = this.tableDOM(this.inputDOM(['keep_date|return date//th:วันที่รับคืน','keeper|new keeper//th:ที่เก็บใหม่','taker'],true,'5em')).css('width','95%').appendTo('#keeping-head');
			var $summary = $('<span>').css({'margin-left':'0.5em'});
			var lasttaker = '';
			$('[name="taker"]',$table)
				.blur(function(){if(lasttaker!=$(this).val()){lasttaker=$(this).val();$summary.html('');takenSummary($summary,$(this).val());}})
				.after($summary)
				;
			$('<div>',{style:'margin-bottom:1em;width:100%;'})
			.append($('<span>',{html:destgrid._('Save'),style:'margin:0.5em;'})
				.button()
				.click(function(){
					var errors = [];
					$('[name="keep_date"],[name="keeper"]',$table)
					.each(function(){
						if(!$(this).val()){
							var c = destgrid.ajaxcol(this.name);
							errors.push(this.name+': '+c.label+'-'+destgrid._('No_value'));
							}
						});
					if (errors.length){
						destgrid.alertDialog(errors.join('<br>')
							,{title:destgrid._('Error'),dialogClass: 'ui-state-error'});
						return;
					}
					var data = $dest().jqGrid('getGridParam','data');
					if(data.length){
						submitkeeping($table,data);
					} else {
						destgrid.alertDialog(destgrid._('No_value')
							,{title:destgrid._('Error'),dialogClass: 'ui-state-error'});
						return;
					}
				}))
			.append($('<span>',{html:destgrid._('Print'),style:'margin:0.5em;'})
				.button()
				.click(function(){printTaking($table);})
				)
			.append($('<span>',{html:destgrid._('Clear'),style:'margin:0.5em;'})
				.button()
				.click(function(){clearkeeping($table);})
				)
			.appendTo("#keeping-container");
			//$('tr.footrow','#keeping-container').addClass('ui-state-default');
			srcgrid.gridDOM({
				container: "#keeping-instk-body"
				,beforeInitDOM: function(gopt) {
					gopt.grid.ondblClickRow = add_destRow;
					gopt.grid.gridComplete = function(){auto_add_destRow(this);};
					}
				,ready : function(dom){
					this.$grid().jqGrid('gridDnD',{
							connectWith:'#'+$dest().attr('id')
							,droppos:'last'
							,dropbyname:true
							,beforedrop: function(event,ui,rowdata){
								ui.helper.dropped = false;
								insert_destRow(rowdata);
								}
						})
					}
				})
				;
			}
		});
}
$(document).ready(taking);
</script>

