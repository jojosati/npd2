%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_msg['buying_entry'] = 'Buying Entry//th:ทำรายการซื้อ'
%_msg['sold_summary']='Sold({1}) {2}//th:เคยขาย({1}) {2}'
%_msg['show_sold_detail']='Show sold details//th:แสดงรายการที่เคยขาย'
<div id='buying-workspace'>
<table><tr>
<td id="buying-container" style="padding:0 0.5em 0 0.5em;vertical-align:top;">
<div id="buying-printarea">
<div id="buying-head"></div>
<div id="buying-body"></div>
</div>
</td>
</tr></table>
</div>
<script type="text/javascript">
function buying(){{''}}{
	var frame = $('.gridwrapperframe').first() ;
	var destwidth = 490;
	var srcoptions = {{!_vars['gridwrapper_options'](_vars)}};
	var destoptions = {
		colmodels : srcoptions.colmodels
		,language : srcoptions.language
		,shortdesc_field : srcoptions.shortdesc_field
		,datatype: 'local'
		,showcols: 'acat,code,!condition,detail,!weight,!gold_weight,!serial,base_cost|ราคาซื้อ,!provider_cost,!lowest_price,!target_price|ราคาขาย,!taker_price,!memo,!last_updated'
		,_able: 'gaed'
		,autofit: [destwidth,'auto']
		//,width: $(window).width()*0.5, height: 'auto' //$(window).height()*0.4
		,caption: ''
		,edit_url: '/{{_vars["suburl"]}}/ajax/jqgrid/noedit' // require to enable add/edit/del feature
		,autocomplete_url: srcoptions.autocomplete_url
		,autocomplete_scopes: srcoptions.autocomplete_scopes
		,rowList: []
		,pginput: false
		,pgbuttons: false
		,footerrow: true
		};
	var srcgrid = jqGrid$(srcoptions);
	var destgrid = jqGrid$(destoptions) ;
	var $dest = destgrid.$grid;

	function insert_destRow(rowdata,ask) {
		var rowid = 'dnd_'+rowdata.code ;
		function isexist() {
			var data = $dest().jqGrid('getGridParam','data') ;
			for (var r in data) {
				r = data[r];
				if (r.code==rowdata.code)
					return true ;
				}
			return false;
			}
		if (isexist()){
			if (!ask) 
				srcgrid.alertDialog(rowdata.code+', '+destgrid._('Data_existed')) ;
			return ;
		}
		rowdata.base_cost = rowdata.sell_price;
		if (ask) {
			id = 'askinsert-buying';
			if ($('#'+id).length==0) {
				destgrid.alertDialog(rowdata.code+', '+destgrid._('Select_found_item?'),
					{buttons:[
						{text:destgrid._('OK'),click:function(){
							$(this).dialog('close');
							if (isexist()){
								srcgrid.alertDialog(rowdata.code+', '+destgrid._('Data_existed')) ;
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
	
	function sum_footerTotal(grid){
		var data = $(grid).jqGrid('getGridParam','data') ;
		var total = {base_cost:0,extra_cost:0,mark_cost:0,lowest_price:0,target_price:0};
		for(var r in data){
			r = data[r];
			for (var t in total) {
				if(r[t]) total[t] += Number(r[t]);
			}
		}
		total.detail = destgrid._('Total') ;
		$(grid).jqGrid('footerData','set',total);
	}
	function resetInput($table){
		$dest().jqGrid('clearGridData');
		$('[name="buy_cond"],[name="keeper"],[name="owner"],[name="keep_date"]',$table)
		.each(function(){$(this).val('').blur();}) ;
	}
	function submitBuying($table,rowdata){
		var url = '/{{suburl}}/ajax/jqgrid/edit'
		var	mtype = 'GET'
		var postdata = {};
		var head={} ;
		
		$('input[name],textarea[name]',$table).each(function(){
			head[$(this).attr('name')]= $(this).val();
			});
		postdata.head = destgrid.array2json(head);
		postdata.items = destgrid.array2json(rowdata);
		postdata.oper = 'buy';
		$.ajax({
			type:mtype, url:url, data:postdata
			,success: function(data){
				if (data[0]==false){
					destgrid.alertDialog(data[1],{title:destgrid._('Error'),dialogClass:'ui-state-error'});
				} else {
					codes = data[2].split(',');
					var msg = '';
					if (codes.length) {
						for(var i in codes){
							msg += '<div class="ui-state-highlight">';
							if (rowdata[i].code != codes[i])
								msg += destgrid._html(rowdata[i].code + ' changed to ') ;
							msg += destgrid._html(codes[i]) ;
							msg += '</div>';
							rowdata[i].code = codes[i];
						}
						//alert(destgrid.array2json(rowdata));
						//$dest().updateGridRows(rowdata);
						$dest().trigger("reloadGrid");
					}
					destgrid.alertDialog(destgrid._('Success') + msg
						,{buttons: [
							{text:destgrid._('OK'),click:function(){$(this).dialog('close');}}
							,{text:destgrid._('Print'),click:function(){printBuying($table);}}
							]
						,close: function(){resetInput($table);}
						});
				}
			}
			,dataType: 'json'
			})
		.error(function(obj,status,msg){destgrid.alertDialog(status+', '+msg);});
	}
	function clearBuying($table){
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
	function printBuying($table) {
		var $print = $('#buying-printarea');
		var $hide = $('.ui-button',$('[name="owner"]',$table).parent()).hide();
		$print.printElement({
			pageTitle:'buying-'+$.datepicker.strftime('%Y%m%d%H%M%S-')+$('[name="owner"]',$print).val().substr(0,20).replace(/[\.\\'\"\\/ -]/g,'_')
		});
		$hide.show();
	}

	function buyerGridDialog(buyer) {
		var buyeroptions = {{!_vars['gridwrapper_options'](_vars)}};
		var qbuyer = '"'+buyer.replace(/\\/g,'\\\\').replace(/\"/g,'\\\"')+'"'
		buyeroptions.pageoptions.unshift('@f-buyer-'+qbuyer);
		buyeroptions.caption = '';
		buyeroptions.showcols = '!acat,code,!condition,detail,!weight,!serial,buy_date,sell_price,!last_updated' ;
		buyeroptions.width = $(window).width()*0.45;
		buyeroptions.height = $(window).height()*0.4;
		buyeroptions._able = 'gq';
		delete buyeroptions.autofit ;
		var buyergrid = jqGrid$(buyeroptions);
		buyergrid.gridDOM({
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
			,title:buyer
			,close:function(){delete buyergrid;}
			,zIndex:200
			});
	}
	function soldSummary(container,buyer) {
		if (buyer=='') return;
		var url = '/{{suburl}}/ajax/jqgrid'
		var	mtype = 'GET'
		var postdata = {};
		var qbuyer = '"'+buyer.replace(/\\/g,'\\\\').replace(/\"/g,'\\\"')+'"'
		postdata.pivotcmds = destgrid.array2json(['@f-buyer-'+qbuyer+'']);
		postdata._summary = '1';
		postdata._cols= destgrid.array2json(['buyer','code','sell_price']);
		postdata.sidx = 'buyer';
		$.ajax({
			type:mtype, url:url, data:postdata
			,success: function(data){
				if ($.isPlainObject(data) && data.records==1){
					var $info = $('<span>',{style:'padding:0 0.5em 0 0.5em;'});
					var r = data.rows[0].cell;
					if (r) {
						$info
						.html($.jgrid.format(destgrid._('{{_msg['sold_summary']}}'),r[0],r[1],$.fmatter.util.NumberFormat(r[2],$.jgrid.formatter.number)))
						;
					}
					$info
					.attr('title',destgrid._('{{_msg['show_sold_detail']}}')+' - '+r[0])
					.button()
					.click(function(){
							buyerGridDialog(buyer);
						});
					$info.appendTo(container);
				}
			}});
	}
	// ------------------------------------------
	$('<div>',{style:'text-align:right;margin-bottom:1em;width:100%;','class':'ui-widget-header ui-corner-all'})
	.append($('<span>',{style:'float:left',html:'{{_m("buying_entry")}}',class:'unload_warning'}))
	.append(login_tag())
	.prependTo("#buying-printarea");

	// checking permission
	var chklst = 'buy_date,buy_cond,owner';
	if (destgrid.chkPermission(chklst,'a')==false 
	|| destgrid.chkPermission(destoptions.showcols,'a')==false){
		destgrid.errDOM(destgrid._('Not_allow_here')).appendTo('#buying-body');
		return;
	}
	destgrid.gridDOM({
		container: "#buying-body"
		,beforeInitDOM: function(gopt) {
			//gopt.grid.gridComplete = function(){sum_footerTotal(this);};
			gopt.form.del.afterComplete = function(){sum_footerTotal($dest());};
			gopt.form.edit.afterComplete = function(){sum_footerTotal($dest());};
			gopt.form.add.afterComplete = function(){sum_footerTotal($dest());};
			}
		,ready: function($grid){
			var $table = this.tableDOM(this.inputDOM([
				['buy_date','buy_cond'],
				'owner',
				['keep_date','keeper']
					],true,'5em')).css('width','95%').appendTo('#buying-head');
			var $summary = $('<span>').css({'margin-left':'0.5em'});
			var lastowner = '';
			//$('[name="buy_date"]',$table).val($.datepicker.strftime('%d/%m/%Y'));
			$('[name="owner"]',$table)
				.blur(function(){if(lastowner!=$(this).val()){lastowner=$(this).val();$summary.html('');soldSummary($summary,$(this).val());}})
				.after($summary)
				;
			$('<div>',{style:'margin-bottom:1em;width:100%;'})
			.append($('<span>',{html:destgrid._('Save'),style:'margin:0.5em;'})
				.button()
				.click(function(){
					var errors = [];
					$('[name="buy_date"],[name="owner"]',$table)
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
						for (var r in data){
							if (data[r].code=='')
								errors.push(destgrid.ajaxcol('code').label+'-'+destgrid._('No_value'));
							if (data[r].detail=='')
								errors.push(destgrid.ajaxcol('detail').label+'-'+destgrid._('No_value'));
							if (data[r].acat=='')
								errors.push(destgrid.ajaxcol('acat').label+'-'+destgrid._('No_value'));
							if (errors.length) break;
						}
						if (errors.length){
							destgrid.alertDialog(errors.join('<br>')
							,{title:destgrid._('Error'),dialogClass: 'ui-state-error'});
							return;
						} else submitBuying($table,data);
					} else {
						destgrid.alertDialog(destgrid._('No_value')
							,{title:destgrid._('Error'),dialogClass: 'ui-state-error'});
						return;
					}
				}))
			.append($('<span>',{html:destgrid._('Print'),style:'margin:0.5em;'})
				.button()
				.click(function(){printBuying($table);})
				)
			.append($('<span>',{html:destgrid._('Clear'),style:'margin:0.5em;'})
				.button()
				.click(function(){clearBuying($table);})
				)
			.appendTo("#buying-container");
			$('tr.footrow','#buying-container').addClass('ui-state-default');
		}
	});
}

$(document).ready(buying);
</script>