//---------------------------------
if (typeof jqgridwrapper == 'undefined') {
if ($.jgrid.formatter.integer.thousandsSeparator!=','){
	$.jgrid.formatter.integer.thousandsSeparator=',';
	$.jgrid.formatter.number.thousandsSeparator=',';
	$.jgrid.formatter.currency.thousandsSeparator=',';
}
if ($.jgrid.edit.bNo=='ละทิ้งการแก้ไข'){
	$.jgrid.edit.bNo='กลับไปแก้ไข';
	$.jgrid.edit.bExit='ละทิ้งไม่บันทึก';
}
if ($.jgrid.edit.bExit=='Cancel'){
	$.jgrid.edit.bExit='Exit';
}
jqgridwrapper = function(options) {
	if (!options.colmodels) return;
	var messages = {
		Not_allow_here: '//th:ตรวจสอบสิทธิ์ ไม่สามารถเข้าได้'
		,Summary_is_active: '//th:ยอดสรุป เปิดใช้งานอยู่'
		,Not_allow_this_action: '//th:ตรวจสอบสิทธิ์ ไม่สามารถทำงานหัวข้อนี้'
		,Toggle_toolbar_search: '//th:แสดง/ซ่อน ช่องค้นหา'
		,Quick_search: '//th:ค้นหาด่วน'
		,autofit: '//th:ปรับขนาดให้พอดี'
		,no_summary: '//th:รายการปกติ'
		,summary: '//th:ยอดสรุป'
		,Export_data_as_csv: '//th:ส่งออก ข้อมูลเป็น CSV'
		,Select_export_scope: '//th:เลือกขอบเขต'
		,Export_this_page: '//th:เฉพาะหน้านี้'
		,Export_all_pages: '//th:ทุกหน้า'
		,Total: '//th:รวม'
		,Data_existed: '//th:มีข้อมูลอยู่แล้ว'
		,Save: '//th:บันทึก'
		,OK: '//th:ตกลง'
		,Cancel: '//th:ยกเลิก'
		,Clear: '//th:ล้าง'
		,Continue: '//th:ทำต่อ'
		,Print: '//th:พิมพ์'
		,Warning: '//th:คำเตือน'
		,Error: '//th:ข้อผิดพลาด'
		,'Clear_data?': '//th:ล้างข้อมูล?'
		,No_value: '//th:ไม่มีข้อมูล'
		,Success: '//th:ทำเสร็จแล้ว'
		,'Select_found_item?': '//th:เลือกรายการที่พบ?'
		,history: '//th:ประวัติ'
		,invalidity: 'invalid'
		} ;
	// ---- initialize part -----
	var self = this;
	var gparams = {_able:'',caption:'',ajaxcols:[]};
	var $grids ; // grid container
	var $grid,$pager,_gopt ;
	var timeoutHnd;
	_init_ajaxcols();
	if (this!=window) {
		this.new_grid = new_grid ;
		this.new_input = new_input ;
		this.chkPermission = chkPermission;
		this.errDOM = errDOM ;
		this.gridDOM = gridDOM ;
		this.inputDOM = inputDOM ;
		this.tableDOM = tableDOM ;
		this.$grid = function(){return $grid;};
		this.$pager = function(){return $pager;};
		this.$container = function(){return $grids;};
		this.messages = messages;
		this.colModel = colModel;
		this.gridOption = gridOption;
		this.formOption = formOption;
		this.navOption = navOption;
		this._ = _;
		this._html = _html;
		this.alertDialog = alertDialog;
		this.array2json = array2json;
		this.gparams = gparams;
		this.ajaxcol = ajaxcol;
		this.isReady= function(){return true;};
		this.scheduleReload = scheduleReload;
	}
	//.append('<script type="text/javascript" src="/{{suburl}}/resource/js/json2.js"></script>')
	/*if (typeof $.autoNumeric=='undefined' && options.suburl) {
		var src = '/'+options.suburl+'/resource/js/autoNumeric-1.7.5.js' ;
		//$head.append('<script type="text/javascript" src="/{{suburl}}/resource/js/autoNumeric-1.7.5.js"></script>') ;
		$('head').append('<script type="text/javascript" src="'+src+'"></script>') ;
	}*/
	// --------------------------------
	// service function select best message depend on language
	function _(m,lang,ms){
		// optional: options.language, options.messages
		// 1. lookup from messages table
		// 2. extract with language selector example: "english//th:xxx"
		if (!m) return m;
		if (m.indexOf('//')<0 && m.indexOf(' ')<0) {
			// lookup from messages table
			if (!ms || ms[m] == undefined) ms = options.messages;
			if (!ms || ms[m] == undefined) ms = messages;
			if (!ms || ms[m] == undefined) {return m.replace(/_/g,' ');}
			var tm = _(ms[m]+'//',lang); // recursive for lang selector
			if (!tm) return m.replace(/_/g,' ');
			return tm ;
		}
		lang = lang || options.language || 'en' ;
		m = m.split('//'+lang+':',2).pop() ;
		return m.split('//',2).shift() ;
	}
	function _html(s){
		return s.replace(/[<]/g,'&lt;').replace(/[>]/g,'&gt;').replace(/[&]/g,'$amp;')
	}
	// --------------------------------
	function _gable(chr) {
		if (options.datatype!='local'){
			if ('f'==chr) return true; //refresh
		}
		if (gparams._able.indexOf(chr)<0) return false;
		if (options.datatype!='local'){
			if ('ead'.indexOf(chr)>=0)	// edit, add, delete
				return options.edit_url?true:false ;
			if ('x'==chr)	// export
				return options.export_url?true:false;
			if ('z'==chr) // zummary
				return options.summary_keys?true:false;
			if ('h'==chr) // history
				return options.show_history?true:false;
			if ('i'==chr) // invalidity
				return options.show_invalidity?true:false;
		}else {
			if ('q'==chr) return false;	// quick search
		}
		return true;
	}
	function chkPermission(chklst,chkperm) {
		if (typeof chklst == 'string') chklst = chklst.split(',');
		for(var name in chklst) {
			var flag = undefined ;
			name = chklst[name];
			if (name[0]=='!' || name[0]=='~') name = name.slice(1);
			name = name.split('|').shift().split(':').shift();
			for (var c in options.colmodels) {
				c = _extfield_split(options.colmodels[c])
				if (c.name==name){
					var perm = _permflags(c.perm);
					flag = false;
					for (var i=0;i<chkperm.length;i++){
						if (perm.indexOf(chkperm[i])>=0){
							flag = true;
							break;
							}
						}
					break;
					}}
			if (flag===false) return false;
			if (flag==undefined && name!='last_updated') {
				for (var i=0;i<chkperm.length;i++){
					if ('dae'.indexOf(chkperm[i])>=0) {
						return false ;
						}
					}
				}
		}
		return true;
	}
	// --------------------------------
	function _extfield_split(c) {
		c = c.split('|',2);
		var lbl = c[1] || '' ;
		c = c[0].split(':',2)
		var perm = c[1] || '';
		c = c[0];
		lbl = _(lbl)
		if (lbl=='') lbl = _(c);
		return {name:c,perm:perm,label:lbl}
	}
	// --------------------------------
	function _permflags(p) {
		p = p || '';
		return p.replace(/\(.*\)/g,'');
	}
	// --------------------------------
	function _permval(p,k) {
		p = p || '';
		var i1 = p.indexOf(k+'(');
		if (i1>=0) {
			var i2 = p.indexOf(')',i1);
			if (i2>i1) return p.slice(i1+k.length+1,i2);
		}}
	// --------------------------------
	function _cmdl(c) {
		// subfunction prepare individual colmodel from cm string "name:perm|lbl"
		var mdl = { 
			name : c.name, index : c.name, label : c.label, search : true
			,editrules : {edithidden : true}
			,editoptions : {}
			,formoptions : {}
			,searchoptions : {searchhidden: true}
		} ;
		var perm = _permflags(c.perm);
		mdl.hidden = (perm.indexOf('h')>=0);
		mdl.editrules.required = (perm.indexOf('r')>=0);
		mdl.editable = (perm.indexOf('a')>=0 || perm.indexOf('e')>=0 || perm.indexOf('v')>=0);
		if (perm.indexOf('a')<0) mdl.formoptions.add = 'hide';
		if (perm.indexOf('e')<0) mdl.formoptions.edit = (perm.indexOf('v')<0 && perm.indexOf('a')<0)?'hide':'disable';
		if (perm.indexOf('v')<0) mdl.formoptions.view = 'hide';
		if (perm.indexOf('N')>=0){
			mdl.align = 'right';
			mdl.formatter = 'number'; 
			//mdl.formatter = function(value,options,rowobj) { return $.fn.fmatter.number(value,options,rowobj);}; // 'number'
			//mdl.formatoptions = $.jgrid.formatter.number ;
			mdl.unformat = function(value,options,obj) { return value.replace(/,/g,'');};
			//mdl.editrules.number = true;
			mdl.editoptions.dataInit = _edit_number_autocomplete;
		} else if (perm.indexOf('I')>=0) {
			mdl.align = 'right';
			mdl.formatter = 'integer';
			mdl.editrules.number = true;
			mdl.editoptions.dataInit = _edit_autocomplete;
		} else if (perm.indexOf('D')>=0) {
			mdl.align = 'center';
			mdl.editoptions.dataInit = _datepicker ;
		} else {
			mdl.editoptions.dataInit = _edit_autocomplete;
			mdl.searchoptions.dataInit = _toolbar_autocomplete;
		}
		if (options.media_field && $.inArray(c.name,options.media_field)>-1) {
			mdl.formatter = _media_formatter;
			mdl.search = false;
			mdl.editable = false;
			mdl.sortable = false;
			mdl.viewable = false;
			mdl.hidedlg = true;
		}
		var wid = _permval(c.perm,'W');
		var len = _permval(c.perm,'L');
		mdl.width = wid? (wid*50) : 150;
		if (wid>5 && len>1){
			mdl.edittype = 'textarea';
			mdl.editoptions.style = 'width:'+(wid*4)+'em;'+'height:'+len+'em;';
			mdl.editoptions.cols = wid*8;
			mdl.editoptions.rows = len;
		} else {
			if (wid) {
				mdl.editoptions.style = 'width:'+(wid*4)+'em;';
			}
		}
		var grp = _permval(c.perm,'G');
		if (grp) mdl.formoptions.grp = grp;	// extend properties
		return mdl;
	}
	function _init_ajaxcols( ) {
		var ajaxcols= []
		for (var c in options.colmodels) {
			c = _extfield_split(options.colmodels[c])
			if (c.name=='__table__') {
				gparams.caption = c.label ;
				if(options._able==undefined || options._able=='*') gparams._able=c.perm;
				else {
					gparams._able = '';
					if (options._able.indexOf('*')>=0 || options._able.indexOf('!')>=0) {
						var neg = false ;
						gparams._able = c.perm;
						for(i in options._able){
							if (options._able[i]=='*') {neg = false; continue ;}
							if (options._able[i]=='!') {neg = true; continue ;}
							if (neg) continue;
							gparams._able += options._able[i];
						}}
					else {
						var perm = _permflags(c.perm);
						for(var i=0; i<options._able.length; i++){
							if (options.datatype=='local'|| perm.indexOf(options._able[i])>=0)
								gparams._able += options._able[i];
						}}
					
				}
				continue;
			}
			var cm = _cmdl(c);
			if (!cm) continue ;
			ajaxcols.push(cm);
		}
		gparams.ajaxcols = ajaxcols;
	}
	
	// --------------------------------
	// service function convert array to jsonstring
	function array2json(aobj) {
		//return JSON.stringify(aobj);
		if (typeof aobj=='undefined') return '';
		if (typeof aobj=='number' || typeof aobj=='boolean')
			return aobj.toString();
		if ($.isPlainObject(aobj)){
			var ret='';
			for(var x in aobj){
				if (typeof aobj[x]!='undefined'){
					if(ret)ret+=',';
					ret+='"'+x+'":'+array2json(aobj[x]);
				}
			}
			return '{'+ret+'}' ;
		}
		if ($.isArray(aobj)){
			var ret='' ;
			for(var x in aobj){
				if (typeof aobj[x] != 'undefined') {
					if(ret)ret+=',';
					ret+=array2json(aobj[x]);
				}
			}
			return '['+ret+']' ;
		}
		return '"'+aobj.toString().replace(/[\\]/g,'\\\\').replace(/[\"]/g,'\\"')+'"';
	}
	// --------------------------------
	// service function show dialog with message
	function alertDialog(msg,dialogoptions) {
		var options = {/*dialogClass:'ui-state-focus',*/buttons:[{text:_('OK'),click:function(){$(this).dialog('close');}}]};
		var closefn ;
		if (dialogoptions) {
			closefn = dialogoptions.close ;
			$.extend(options,dialogoptions);
			if (dialogoptions.dialogClass) {
				//options.create = function(){$('.')};
			}
		}
		
		options.close = function(){ if(closefn)closefn(); $(this).remove();};
		$('<div>',{'html': msg}).dialog(options);
	}
	// --------------------------------
	function _gridReload() {
		$grid.trigger("reloadGrid");
	}
	// --------------------------------
	function isNumber(n) {
		return !isNaN(parseFloat(n)) && isFinite(n);
	}
	function isTouch() {
		return true || window.Touch;
	}
	function _scrollPane(elem,auto){
		if ((options.iscroll=='auto' || options.iscroll=='touchScroll') 
		&& $(elem).touchScroll){
			if (isNumber($(elem).touchScroll('getPosition'))){
				$(elem).touchScroll('update');
			} else $(elem).touchScroll();
			return;
		}
		if ((options.iscroll=='auto' || options.iscroll=='scrollPane') 
		&& $(elem).jScrollPane){
			if (auto!='force') {
				var api = $(elem).data('jsp');
				if (auto=='empty'){
					$(elem).empty();
					if (api)
						$(elem).removeData('jsp');
					return;
				}
				if (auto=='destroy'){
					if(api) api.destroy();
					return;
				}
				if (api){
					api.reinitialise();
					return api;
				}
			}
			if (auto!==true) auto = false;
			$(elem).jScrollPane({autoReinitialise:auto});
			return;
		}
	}
	function _gridAutoHeight() {
		if (!options.autofit) return;
		var h,o;
		h = options.autofit[1] || '';
		if (h!='' && !isNumber(h)) return h;
		if (h=='') h = 0;
		o = options.autofit[2] ;
		if (o=='#' || o=='') 
			//o = $grids ; //.parentsUntil('[style~="height"]').first();
			o = $grid.parents('.gridwrapperframe').first();
		if (!o || !$(o).length){
			o = window;
			if (!h)
				h = window.parent.length?0.6:0.5;
		}
		if (!h) h = 0.9;
		if (h>=-10 && h<=10) h *=$(o).height() ;
		if (h < 0) h += $(o).height() ;
		if (h<100) h = 100;
		return h;
	}
	// --------------------------------
	function _gridAutoWidth() {
		if (!options.autofit) return ;
		var w,o;
		w = options.autofit[0] || '' ;
		if (w!='' && !isNumber(w)) return w;
		if (w=='') w = 0;
		o = options.autofit[2] || '' ;
		if (o=='#' || o=='') 
			//o = $grids; //.parentsUntil('[style~="width"]').first();
			o = $grid.parents('.gridwrapperframe').first();
			if (!$(o).hasClass('gridwrapperframe')) o = null;
		if (!o || !$(o).lenghth){
			o = window;
			if (!w) w = 0.85;
		}
		if (!w) w = 1;
		//alert($(o).css('width')+' autowidth '+w+'*'+$(o).width());
		if (w>=-10 && w<=10) w *=$(o).width() ;
		if (w < 0) w += $(o).width() ;
		//alert ('wrapper '+$(o).attr('id')+'='+$(o).width()+'\n'+$grid.attr('id')+'='+w) ;
		if (w<100) w = 100;
		return w;
	}
	// --------------------------------
	function _summaryChange(elem) {
		var postdata = $grid.jqGrid('getGridParam','postData') ;
		var zval = $(elem).val() ;
	
		if (!zval) delete postdata._summary
		else postdata._summary = zval ;
		_gridReload();
	}
	// --------------------------------
	function _datepicker(elem) {
		$(elem)
		.datepicker({
				showButtonPanel:true,changeMonth:true,changeYear:true 
				//showOn:'both', buttonImage: "/"+options.suburl+"/resource/images/sort_desc.png", buttonImageOnly: true
				})
		.blur(function(){
				if (this.value!='') {
					var nums = this.value.split('/');
					var dd = new Date()
					if (nums[2]) {
						var y = new Number(nums[2]) ;
						if (y < 100) y += 2000 ;
						dd.setFullYear(y);
					}
					if (nums[1]) dd.setMonth(new Number(nums[1]) - 1);
					if (nums[0]) dd.setDate(new Number(nums[0]));
					
					this.value = $.datepicker.strftime('%d/%m/%Y',dd);
					}
				});
		$("#ui-datepicker-div").hide();
	}
	function _autocomplete(elem,tax,len,gridfilter) {
		// require options: taxonomy_url, autocomplete_url, autocomplete_scopes
		var url = (gridfilter? options.taxonomy_url : options.autocomplete_url) ;
		if (!url) return false; // no url do nothing
		if (!tax) tax = $(elem).attr('name');
		if (!tax) {
			tax = $(elem).attr('id');
			var prefix = ['ge_','gs_',$grid.attr('id')+'_'];
			for (var p in prefix) {
				p = prefix[p];
				if (tax.indexOf(p)==0) {
					tax = tax.replace(p,'');
				}
			}
		}
		url += '/'+tax;
		len = len || 0;
		var scope, focusclass='focusout' ;
		if (!gridfilter && options.autocomplete_scopes) {
			for (var sc in options.autocomplete_scopes) {
				if ($.inArray(tax,options.autocomplete_scopes[sc])>=0) {
					if (sc=='!')
						return ;	// do nothing
					scope = sc ;
					break ;
					}}}
		var option = {
			source: url
			,minLength:len
			//,disabled: true
			,delay:gridfilter?300:100
			//,position: {my:'left top',at:'left bottom',collision:'flip'}
			/*,select:function(event,ui){
				if(ui.item.value==''){
					$(ui.item).autocomplete('search','');
					return false;
					}}*/
			,open: function (event,ui){
				if ($(elem).hasClass(focusclass)) {
					$(elem).autocomplete("close") ;
					return ;
				}
					
				var maxh = 100;
				var $ul = $(elem).autocomplete('widget');
				$('li.ui-menu-item[disabled=disabled]',$ul).each(function(){
					$(this)
					.attr('class','ui-autocomplete-category')
					.removeAttr('role')
					;
					});
				$ul.css({
					'overflow-y':'auto',
					'max-height':maxh+'px'
					});
				var o = $grid.parents('.gridwrapperframe').first();
				if (!$(o).hasClass('gridwrapperframe'))	o = document;
				var y = $(o).offset() || 0 ;
				if (y) y = y.top ;
				y += $(o).height()*3/4 ;
				if($ul.offset().top > y){
					$ul.position({my:'left bottom',at:'left top',of:$(elem)});
					}
				//alert ($ul[0].scrollHeight+'/'+$ul.height()+'\n'+$ul[0].scrollWidth+'/'+$ul.width());
				var w = $ul.width() - $ul[0].scrollWidth ;
				if (w > 0) $ul.width($ul.width()+w+8);
				_scrollPane($ul);

				}
			/*,close: function(event,ui){
				var $ul = $(elem).autocomplete('widget');
				$ul.empty();
				$ul.removeData('jsp');
				}*/
			,search: function(event,ui){
				var $ul = $(elem).autocomplete('widget');
				_scrollPane($ul,'empty');

				}
			};
		if (options.tagging_field==tax) {
			option.focus = function(){return false;};
			option.select = function( event, ui ) {
					var terms = this.value.split( /,\s*/ );
					// remove the current input
					terms.pop();
					// add the selected item
					terms.push( ui.item.value );
					// add placeholder to get the comma-and-space at the end
					terms.push( "" );
					this.value = terms.join( ", " );
					return false;
				}
		}
		function _render(ul,item ) {
			var lbl = item.value.split('||',2) ;
			item.value = lbl[0];
			lbl[0] = _html(lbl[0]);
			if (lbl.length>1){
				if (lbl[1].search('...waiting')>=0) {
					if (!$(elem).hasClass(focusclass))
						$(elem).autocomplete('search'); // search again if found special word	
					}
				lbl[1] = lbl[1].replace(/-{3,}/g,'<hr>');
				lbl = lbl[0]+' <span class="ui-state-disabled">'+lbl[1]+'</span>';
			} else lbl = lbl[0];
			var $a = $('<a>').html(lbl);
	
			var $li = $('<li>')
				.data( 'item.autocomplete', item)
				.append( $a )
				.appendTo( ul );
			if (!item.value){
				$li.attr('disabled','disabled');
				}
		}
		function _init() {
			$(elem)
			.autocomplete(option)
			.data( "autocomplete" )._renderItem = _render
			;
			/*var _='';
			for (var __ in $(elem).data('autocomplete'))
				_ += __+ ', ';
			alert (_) ;*/
		}
		function _onsearch(event,ui) {
			if ($(elem).hasClass(focusclass)) return false ; // abort search
			var qry = {} ;
			var u = option.source
			if (scope) {
				if (!options.cellEdit) {
					//qry[scope] = $('#'+scope).val() ;
					qry[scope] = $('[name="'+scope+'"]').val()
				} else {
					var id = $grid.jqGrid('getGridParam','selrow')
					var rowdata = $grid.jqGrid('getRowData',id) ;
					qry[scope] = rowdata[scope];
				}
			}
			if (gridfilter) {
				var postdata = $grid.jqGrid('getGridParam','postData') ;
				var k;
				for (k in postdata) {
					if (k == "pivotcmds" || k == "qsearch" || k=="_cols") {
						if (postdata[k]) {
							qry[k] = postdata[k];
						}}}
				if (postdata['_search']) {
					k = 'filters'
					if (postdata[k]) {
						qry[k] = postdata[k];
					}
				}}
			var q = $.param(qry);
			if (q) u += "?"+q
			$(elem).autocomplete( "option", "source",u);
			return true;
		}
		$(elem)
		.focus(function(){ 
			if (typeof $(this).autocomplete('option','delay')==typeof $(this)){
				_init();
				}
			$(elem).removeClass(focusclass) ;
			})
		.blur(function(){
			$(elem).addClass(focusclass) ;
			})
		.click(function(){
			if (typeof $(this).autocomplete('option','delay')==typeof $(this)){
				_init();
				}
			if (!option.minLength){
				if ($(this).val()=='' || (isNumber($(this).val()) && $(this).val()==0))  {
					$(this).autocomplete('search','');
					}
				}
			});
		//_init();
		$(elem).bind("autocompletesearch", _onsearch);
	}
	// --------------------------------
	function _edit_autocomplete(elem) {
		_autocomplete(elem);	
	}
	function _edit_number_autocomplete(elem) {
		//_autocomplete(elem);
		/*$(elem)
		.focus(function(){
			this.value = this.value.replace(/,/g,'');
			})
		.blur(function(){
			var fmt = $.jgrid.formatter.number || {};
			this.value = $.fmatter.util.NumberFormat(this.value.replace(/,/g,''),fmt)
			})
		.blur()
		;*/
		$(elem).css('text-align','right').autoNumeric().autoNumericSet(elem.value) ;
		//if ($grid.jqGrid('getGridParam','cellEdit'))
		//	$(elem).change(function(){if( $(this).parent().hasClass('edit-cell')) this.value = $(this).autoNumericGet();});

	}
	function _toolbar_autocomplete(elem) {
		if (!elem) return;
		var pf = null;
		var tax = undefined;
		var len = 1;
		_autocomplete(elem,tax,len,true);
		// trigger autosearch when select
		//$(elem).bind( "autocompletechange", function(event, ui) {alert('change');$grid[0].triggerToolbar();});
		$(elem).bind( "autocompleteselect", function(event, ui) {$(elem).keydown();});
	}
	function _media_formatter(cellvalue, fmtoptions, rowObject) {
		if (!cellvalue) return ''
		if (options.media_url) {
			var pics = cellvalue.split(';');
			cellvalue = '';
			for (var i in pics) {
				cellvalue += '<a class="ui-button ui-state-default ui-button-text" style="padding-left:3px;padding-right:3px;" onclick="$(\'<img>\',{style:\'width:100%;display:none;\',src:\''+options.media_url+'/'+pics[i]+'\'}).dialog({title:\''+pics[i]+'\',width:\'350\',height:\'auto\',open:function(){$(this).width($(this).parent().width()-28);},close:function(){$(this).remove();}});">'+(Number(i)+1)+'</a>';
			}
		}
		return cellvalue ;
	}
	// --------------------------------
	//# rearrange formpos in colmodels
	function _adjfrmpos(colmodels) {
		// sub function assign rowpos, colpos for each editable colmodel
		// optional options : form_colnum
		var colnum = options.form_colnum || 2;
		var fpos = [1,1,colnum,'*'] ;
		for (var i=0; i < colmodels.length; i++) {
			var cm = colmodels[i];
			//if (!cm.editable) continue;

			if (fpos[1]!=1 && fpos[1]>fpos[2] || cm.formoptions.grp!=fpos[3] || cm.width > 250) {
				// if colpos is beyond colnum, or group change, or too wide input field
				// must start new line
				fpos[0]++; fpos[1]=1; fpos[3]= cm.formoptions.grp;
			}
			cm.formoptions.rowpos = fpos[0];
			cm.formoptions.colpos = fpos[1];
			//alert (cm.name+' '+cm.formoptions.rowpos+','+cm.formoptions.colpos);
			fpos[1]++; // next column
			if (cm.width > 250){
				fpos[0]++; fpos[1]=1;
			}
		}
		return colmodels;
	}
	// --------------------------------
	function colModel() {
		// require options : colmodels
		// optional options : form_colnum, showcols
		var colmodels;
		var ajaxcols = gparams.ajaxcols;
		if (!options.showcols) { 
			colmodels = $.extend(true,[],ajaxcols) ;
		}else{
			function _override_perm(cm,perm,label){
				if (label) cm.label = label;
				if (perm!=undefined) {
					cm.editrules.required = cm.editrules.required || (perm.indexOf('r')>=0);
					cm.editable = cm.editable && (perm.indexOf('a')>=0 || perm.indexOf('e')>=0 || (perm.indexOf('v')>=0&& !options.cellEdit));
					if (perm.indexOf('a')<0) cm.formoptions.add = 'hide';
					if (perm.indexOf('e')<0) cm.formoptions.edit = (perm.indexOf('v')<0 && perm.indexOf('a')<0)?'hide':'disable';
					if (perm.indexOf('v')<0) cm.formoptions.view = 'hide';
				}
			}
			colmodels = [];

			cols = (typeof options.showcols=='string')?options.showcols.split(',') : options.showcols;
			for (var i in cols) {
				var c = _extfield_split(cols[i])
				if (cols[i].indexOf(':')<0) delete c.perm;
				if (cols[i].indexOf('|')<0) delete c.label;
				
				var _n = c.name;
				var _h = ''
				if (_n[0]=='!' || _n[0]=='~') {
					_h = _n[0] ;_n = _n.slice(1) ;
					}
				if (_n=='*'){
					for (var i in ajaxcols) {
						_n = ajaxcols[i].name ;
						var _exist = false;
						for (var ii in colmodels) {
							_exist =(_n==colmodels[ii].name)
							if (_exist) break ;
						}
						if (!_exist) {
							var cm = $.extend(true,{},ajaxcols[i]);
							if (_h != '~') cm.hidden = (_h=='!') ;
							_override_perm(cm,c.perm,c.label);
							colmodels.push(cm) ;
						}}
				}else{
					var _exist = false;
					for (i in colmodels) {
						var cm = colmodels[i] ;
						_exist = (_n==cm.name) ;
						if (_exist) {
							if (_h != '~') colmodels[i]['hidden'] = (_h=='!') ;
							_override_perm(cm,c.perm,c.label);
							break ;
						}}
					if (!_exist) {
						for (i in ajaxcols) {
							_exist = (_n==ajaxcols[i].name);
							if (_exist) {
								cm = $.extend(true,{},ajaxcols[i]);
								if (_h != '~') cm.hidden = (_h=='!') ;
								_override_perm(cm,c.perm,c.label);
								colmodels.push(cm) ;
								break;
							}}}
					if (!_exist) {
						c.name = _n;
						c.label = _(_n)
						cm = _cmdl(c);
						cm.hidden = (_h=='!') ;
						colmodels.push(cm) ;
					}
					
			}} // for ..
		}
		colmodels = _adjfrmpos(colmodels);
		return colmodels;
	}
	// --------------------------------
	function _prepare_pivoturl() {
		// called by _beforeRequest
		// required options : pageoptions,pivot_url
		if (!options.pivot_url) return '';
		var postdata = $grid.jqGrid('getGridParam','postData') ;
		var pv = [];
		var pvstr = "" ;
		var isnew = false ;

		var pageoptions = options.pageoptions || [];
		var keepsum = true ;
		if (postdata._summary) {
			var scmd = "summary-"+postdata._summary;
			keepsum = ($.inArray(scmd,pageoptions)>=0);
			if (postdata.sidx) {
				var idxcmd = postdata.sidx ;
				if (postdata.sord) idxcmd += '-' + postdata.sord ;
				idxcmd = 'sort-'+idxcmd;
				if (keepsum) keepsum = ($.inArray(idxcmd,pageoptions)>=0);
				if (!keepsum) pv.push(idxcmd);
			}
			if (!keepsum) pv.push(scmd) ;
		}
		else {
			for (var s in pageoptions) {
				s = pageoptions[s] ;
				if (s.search('summary-')==0) {
					keepsum = false ;
					break;
				}
			}
		}
		for (var s in pageoptions) {
			s = pageoptions[s] ;
			if (!keepsum && (s.search('summary-')==0 || s.search('sort-')==0)) continue ;
			if (pvstr) pvstr += '/' ;
			pvstr += s.replace(/~/g,'~~').replace(/\//g,'~/') ;
		}
		if (postdata.qsearch) {
			pv.push ("@f--"+postdata.qsearch) ;
		}
		if (postdata._search && postdata.filters) {
			filters = eval("(" + postdata.filters + ")") ;
			for (x in filters.rules) {
				x = filters.rules[x] ;
				pv.push ("@f-"+x.field+"-"+x.data) ;
		}}
		if (pv.length>0) {
			for (x in pv) {
				//opv =(pv[x]) ;
				pv[x] = pv[x].replace(/~/g,"~~").replace(/\//g,"~/") ;
			}
			if (pvstr) pvstr += "/";
			pvstr += pv.join('/') ;
			return options.pivot_url+(options.urltagstr||'//')+pvstr ;
		}
		return '';
	}
	function _beforeSaveCell(rowid, cellname, value, iRow, iCol){
		var cols = $(this).jqGrid('getGridParam','colModel');
		for (var i in cols){
			if(cols[i].name==cellname) {
				if (cols[i].formatter=='number') {
					return value.replace(/,/g,'');
				}
				break;
			}
		}
	}
	function _beforeRequest(){
		var postdata = $(this).jqGrid('getGridParam','postData') ;
/*		var cols = $(this).jqGrid('getGridParam','colModel');
		var flds= [] ;
		for (var i in cols) {
			n = cols[i].name;
			p = (cols[i].hidden)? ':h':'';
			flds[i] = n+p;
		}
		postdata._cols = array2json(flds);
*/
		postdata._cols = $(this).jqGrid('getGridParam','_cols');
		if (postdata._cols == options.ajax_fields)
			delete postdata._cols ;
		$pvlinks = $(".pivoturl-widget",$grids) ;
		if ($pvlinks) {
			var pvurl = _prepare_pivoturl() ;
			if (pvurl) {
				pvurl = '<a href="'+encodeURI(pvurl)+'">pivot-url</a>';
			}
			$pvlinks.each(function(){
				$(this).html(pvurl);
			});
		}
		return true;
	}
	function _dblclickRow(rowid) {
		var action ;
		if (_gable('v')) action = 'view';
		if (_gable('e') && !options.cellEdit) action = 'edit';
		if (action) _doRow(action)(rowid);
	}
	function _gridComplete(ofunc){
		function wrapper() {
			if (ofunc){
				ofunc.apply(this);
			}
			if (isNumber(_gridAutoHeight())){
				var $bdiv = $grid.parents('div.ui-jqgrid-bdiv').first();
				if ($bdiv) _scrollPane($bdiv);
			}
		}
		return wrapper;
	}
	// --------------------------------
	// gridoption + colmodels
	function gridOption() {
		var gopt = {
			datatype : 'json'
			,hiddengrid : false
			,caption : undefined
			,gridview : true
			,sortable : false
			,width : undefined
			,height : undefined
			,hiddengrid : false
			,rowNum : 20
			,rowList : [10,20,50,100]
			,pgbuttons: true
			,pginput: true
			,scroll : false
			,scrollrows : true
			,sortname : ''
			,sortorder : 'asc'
			,viewrecords : true
			//,pager : undefined
			,postData : {}
			,mtype : 'GET'
			,cellEdit: false
			,cellsubmit: null
			,cellurl: null
			,footerrow: false
			,rownumbers: false
			,iscroll: 'auto'
			};
		// override value from options
		for (var k in gopt) {if (options[k] != undefined) gopt[k] = options[k];}
		if (options.grid_url) gopt.url = options.grid_url;
		if (options.edit_url) gopt.editurl = options.edit_url;
		if (options.colreorder) gopt.sortable = true;
		if (options.sort){
			var s = options.sort.split('-')
			gopt.sortname = s[0];
			if (s[1]=='asc' || s[1]=='desc') gopt.sortorder = s[1];
		}
		if (gopt.datatype=='local'){
			//if (!gopt.cellEdit) gopt.editurl = clientArray';
			gopt.cellsubmit = 'clientArray' ;
			gopt.cellurl = 'clientArray' ;
		}
		if (!gopt.width){
			gopt.width = _gridAutoWidth() || 0.9 * $(window).width();
		}
		if (!gopt.height){
			gopt.height = _gridAutoHeight() || 'auto' ;
		}
		// caption
		if (gopt.caption == undefined) gopt.caption = gparams.caption;
		gopt.caption = _(gopt.caption);
		// check if rowNum not in rowList
		if (gopt.rowList) {
			for (var i=0; i <gopt.rowList.length; i++) {
				if (gopt.rowNum == gopt.rowList[i]) break;
				if (gopt.rowNum <= gopt.rowList[i]) {
					gopt.rowList.splice(i,0,gopt.rowNum);
				}}}
		// pivot-url -> postData.pivotcmds
		if (options.pageoptions) {
			var pv = [];
			for (var c in options.pageoptions) {
				c = options.pageoptions[c];
				if (c[0]=='@') {
					pv.push(c);
					continue;
				}
				if (c.search('summary-')==0) {
					var zval = c.split('-',2).pop();
					if (zval && zval!='') gopt.postData._summary = zval
					else delete gopt.postData._summary;
				}
			}
			if (pv) gopt.postData.pivotcmds = array2json(pv);
		}
		// toolbar for quick search, zummary, pivot-url
		if (_gable('q') 
		|| (_gable('z')) 
		|| (_gable('h')) 
		|| (_gable('p')))
			gopt.toolbar = [true,'top'];
		// bind event
		//if (_gable('v')) 
		gopt.ondblClickRow = _dblclickRow ; //function(rowid){_doRow('view')(rowid)};
		gopt.beforeRequest = _beforeRequest;
		gopt.colModel = colModel();

		if (gopt.sortname){
			var flag;
			for (var c in gparams.ajaxcols){
				c = gparams.ajaxcols[c];
				flag = (c.name==gopt.sortname);
				if (flag) break;
			}
			if (!flag) gopt.sortname = '';
		}
		if (!gopt.sortname){
			for (var c in gopt.colModel){
				c = gopt.colModel[c];
				if (c.hidden) continue;
				gopt.sortname = c.name;
				break;
			}}
		if (gopt.sortorder!='asc' && gopt.sortorder!='desc')
			gopt.sortorder= 'asc';
		return gopt ;
	};
	function _formColspan(frmtype) {
		function wrapper(form) {
			form = $(form);
			if (frmtype=='edit' || frmtype=='add') {
				/*$('<div>',{class:'.unload_warning',style:'display:none'})
				.html('grid entry form is active')
				.appendTo(form);*/
				
				var m = $('.ui-jqgrid-title:first',$grids).text() 
						+ ' - entry form - ' 
						+ $('.ui-jqdialog-title',$('#editmod'+$grid.attr('id'))).text();
				$('.unload_warning',$grids).html(m) ;
				}
			$("div.ui-jqconfirm",form.parent()).each(
				function(){
					$(this).css('top','10px');
				});
			$("tr", form).each(
				function() {
					var inputs = $(">td.DataTD:has(input,select,textarea,span)",this);
					var tds = $(">td", this);
					var w = tds.eq(0).attr("width") ;
					if (!w) {
						w = "10%" ;
						tds.eq(0).attr("width",w) ;
						}
					if (inputs.length == 1) {
						tds.eq(1).attr("colSpan",tds.length-1);
						tds.slice(2).hide();
					}
					else {
						for (var i=1; i<inputs.length; i++)
							tds.eq(i*2).attr("width",w);
					}
					$(">td.CaptionTD",this).addClass("ui-state-default").css("text-align","right").css("padding-right","4px");
				});
			if (frmtype) {
				var cols = $grid.jqGrid('getGridParam','colModel');
				function modecol (name) {
					for (var c in cols){
						c=cols[c];
						if(c['name']==name){return c.formoptions[frmtype];}
					}
					return undefined
				}
				$("tr", form).each(
					function() {
						var tds = $(">td", this);
						for (var i=0; i < tds.length; i++) {
							if (tds.eq(i).hasClass('DataTD')) {
								var inp = $('input,select,textarea,span:first',tds.eq(i));
								var n = inp.attr('name') ;
								if (!n) continue;
								var m = modecol(n);
								if (m=='hide') {
									tds.eq(i-1).hide();
									tds.eq(i).hide();
								}
								if (m=='disable') {
									inp.attr('disabled','disabled');
									tds.eq(i-1).removeClass('ui-state-default');
									tds.eq(i-1).addClass('ui-state-disabled');
									tds.eq(i).addClass('ui-state-disabled');
						}}}
				});
		}}
		return wrapper;
	}

	function _formResize (form) {
		var o = $grid.parents('.gridwrapperframe').first();
		//if (!o)
		//	o = $grid.parents('.frame-dynamic').first()
		//if (!o) o = window; //if (!$(o).hasClass('gridwrapperframe')) o = window;
		if (!o.length) o = $grids ;
		var h = $(o).height() * 0.8 ; //$(form).offset().top ;
		if ($(form).height() > h) $(form).height(h); 
		_scrollPane(form,true) ;
	}
	
	function _formDelData(form) {
		if (options.shortdesc_field) {
			var $dd = $('td.delmsg',form); //.hide() ;
			var msg = '';
			var selrows = [] ;
			if ($grid.jqGrid('getGridParam','multiselect'))
				selrows = $grid.jqGrid('getGridParam','selarrrow') ;
			if (selrows.length==0){
				var r = $grid.jqGrid('getGridParam','selrow');
				if (r)
					selrows = [r] ;
				}
			for (var rowid in selrows) {
				rowid = selrows[rowid];
				var rowdata = $grid.jqGrid('getRowData',rowid);
				var m = '';
				for (var c in options.shortdesc_field) {
					c = options.shortdesc_field[c];
					if (m.length) m += ' ';
					m += rowdata[c];
				}
				if (m) {
					//if (msg.length>0)
					msg += '<div class="ui-state-highlight">'+_html(m)+'</div>' ;
				}
			}
			$('div.short_desc',$dd).remove();
			if (msg.length>0) {
				$dd.html('<div class="short_desc">'+msg+'<hr/></div>'+$dd.html());
				//$('td',$dd).html(msg);
			}
			//$dd.show();
		}
	}
	function _formCheckValues(postdata,frmid,mode) {
		var cols = $grid.jqGrid('getGridParam','colModel');

		for (var n in postdata) {
			for (var i in cols){
				if(cols[i].name==n) {
					if (cols[i].formatter=='number') {
						postdata[n] = postdata[n].replace(/,/g,'');
					}
					break;
				}
			}
		}
		//return postdata
	}
	
	function formOption(frmtype) {
		var o = $grid.parents('.gridwrapperframe').first();
		if (!$(o).hasClass('gridwrapperframe')) o = window;
		var width = $(window).width()*0.5;
		switch (frmtype) {
		case 'edit': 
			return {
				modal:true, width:width, labelswidth:'15%'
				,closeAfterEdit: true, reloadAfterSubmit:false, checkOnUpdate:true
				,recreateForm: true
				,beforeCheckValues: _formCheckValues
				,afterSubmit: function(response, postdata) { return $.parseJSON(response.responseText);}
				,beforeShowForm : _formColspan(frmtype)
				,afterShowForm : _formResize
				,onClose : function(){$('.unload_warning',$grids).html('') ;}
				,mtype:'GET'
			} ;
		case 'add':
			return {
				modal:true, width:width, labelswidth:'15%'
				,clearAfterAdd : true, reloadAfterSubmit:false, checkOnUpdate:true
				,recreateForm: true
				,beforeCheckValues: _formCheckValues
				,afterSubmit: function(response, postdata) { return $.parseJSON(response.responseText);}
				,beforeShowForm : _formColspan(frmtype)
				,afterShowForm : _formResize
				,onClose : function(){$('.unload_warning',$grids).html('') ; }
				,mtype:'GET'
			};
		case 'del':
			return {
				afterSubmit: function(response, postdata) { return $.parseJSON(response.responseText);}
				,beforeShowForm: _formDelData
			};
		case 'view':
			return {
				modal:true, width:$(window).width()*0.5, labelswidth:'15%'
				,beforeShowForm : _formColspan(frmtype)
			} ;
		}
		return {};
	}
	
	function _doRow(action){
		function wrapper(rowid) { 
			var postdata = $grid.jqGrid('getGridParam','postData') ;
			if (postdata._summary) {
				alertDialog(_('Summary_is_active'));
				return;
			}
			// action : [edit, add, del, view]
			if (!_gable(action[0])){
				alertDialog(_('Not_allow_this_action'));
				return ;
			}
			var a = action;
			if (action=='add') {
				rowid = 'new'; a='edit';
				}
			if (action=='view') {
				$('#viewmod'+$grid.attr('id')).remove();
				}
			$grid.jqGrid(a+'GridRow',rowid,/*formOption(action)*/_gopt.form[action]);
		}
		return wrapper;
	}
	
	function navOption( ){
		ret = {
			edit: _gable('e') && !options.cellEdit
			,add: _gable('a')
			,del: _gable('d')
			,search: false // alternate use filter toolbar below
			,view: _gable('v')
			,refresh: _gable('f')
			,beforeRefresh : function () {
				$(".ui-jqgrid",$grids).first()
					.css({
						height: ($(".ui-jqgrid-view",$grids).height() + $(".ui-jqgrid-pager",$grids).height()) + "px",
						width: $(".ui-jqgrid-view",$grids).width() + "px"
						});
				}
		} ;
		if (options.datatype!='local') {
			ret.addfunc = _doRow('add') ;
			ret.editfunc = _doRow('edit') ;
			ret.delfunc = _doRow('del');
		}
		ret.viewfunc = _doRow('view');
		return ret ;
	}
	function scheduleReload(msec) {
		if (!msec) msec=300;
		if(timeoutHnd) {		
			clearTimeout(timeoutHnd) ;
			msec = 600 ;
			}
		timeoutHnd = setTimeout(_gridReload,msec);
	}
	function _autofitGrid(){
		$grid.setGridHeight(_gridAutoHeight());
		$grid.setGridWidth(_gridAutoWidth(),true);
		_gridComplete()();
	}
	function _exportDialog (dlmode) {
		function wrapper() {
			var url = options.export_url;
			var $dlg = $('<div>');
			var postdata = $grid.jqGrid('getGridParam','postData') ;
			var qry = {} ;
			$dlg.append($('<div>',{style:"margin-left:1em;",html:_('Select_export_scope')}));
			for (k in postdata) {qry[k] = postdata[k];}
			if (!qry['_search']) { delete qry['_search']; delete qry['filters']; }
			qry['_dl'] = dlmode || '1';
			if (options.language) qry['_lang'] = options.language ;
			var q = $.param(qry); if (q) q = '?'+q ;
			qry['rows'] = '-1'; qry['page'] = '1';
			var qa = $.param(qry); if (qa) qa = '?'+qa ;
			var st = {width:'60%',margin:'.5em 1em'};
			$dlg
			.append($('<a>',{html:_('Export_this_page'),href:url+q})
					.css(st)
					.button())
			.append($('<a>',{html:_('Export_all_pages'),href:url+qa})
					.css(st)
					.button())
			.dialog({ 
				modal:true
				,title: _('Export_data_as_CSV')
				,open : function() {$('a',this).blur();}
				,close: function() {this.dialog('destroy');}
				//,buttons: {_('Close'):function() { $(this).dialog("close");}}
				}) ;
			$('.ui-button-text',$dlg).css('line-height','1.4em');
		}
		return wrapper;
	}

	function customToolbar () {
		// optional: options.autofit
		// ---- custom toolbar ----
		var sepelem = $('<td class="ui-state-disabled" style="width:4px;"><span class="ui-seperator"></span></td>');
		var qelem = $('<td>');
		if (_gable('q')) {
			qelem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			// ---- quick search
			function _quick_search(event){
				if (!options.searchonenter || event.keyCode == 13) {
					var postdata = $grid.jqGrid('getGridParam','postData') ;
					if ($(this).val()) postdata.qsearch = $(this).val()
					else delete postdata.qsearch ;
					scheduleReload();
				}}
			qelem.append($('<input>',{ 'class':'qsearch-widget',title:_('Quick_search'),placeholder:_('Quick_search'),style:"height:1em;"})
					.keyup(_quick_search)
					) ;
			qelem.after(sepelem);
		}
		// ---- inalidity switch
		var ielem = $('<td>');
		if (_gable('i')) {
			ielem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			i_id = $grid.attr('id')+'_invalidity';	
			i_button = $('<input>',{id:i_id,'type':'checkbox','class':"invalidity-widget",title:_('invalidity')})
				.change(_invalidity_change) ;
				
			function _invalidity_change(){
				var postdata = $grid.jqGrid('getGridParam','postData') ;
				var ival = $(this).attr('checked');
				if (!ival) {
					delete postdata._invalidity ;
					$('label.ui-button',ielem).removeClass('ui-state-highlight');
				}
				else {
					postdata._invalidity= 'invalidity' ;
					$('label.ui-button',ielem).addClass('ui-state-highlight');
				}
				_gridReload();			
			}
			ielem
			.append(i_button)
			.append($('<label>',{'for':i_id,html:_('invalidity')}));
			i_button.button();
		}
		// ---- history switch
		var helem = $('<td>');
		if (_gable('h')) {
			helem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			h_id = $grid.attr('id')+'_history';	
			h_button = $('<input>',{id:h_id,'type':'checkbox','class':"history-widget",title:_('history')})
				.change(_history_change) ;
				
			function _history_change(){
				var postdata = $grid.jqGrid('getGridParam','postData') ;
				var hval = $(this).attr('checked');
				if (!hval) {
					delete postdata._history ;
					$('label.ui-button',helem).removeClass('ui-state-highlight');
				}
				else {
					postdata._history= 'history' ;
					$('label.ui-button',helem).addClass('ui-state-highlight');
				}
				_gridReload();			
			}
			helem
			.append(h_button)
			.append($('<label>',{'for':h_id,html:_('history')}));
			h_button.button();
		}
		// ---- autofit grid
		var afelem = $('<td>');
		if (options.autofit) {
			afelem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			afelem.append($('<span>',{'class':"autofit-widget",title:_('autofit')})
				.button ({text: false,icons: {primary:'ui-icon-arrow-4-diag'}})
				.click (_autofitGrid)
				);
		}
		// ---- search toolbar
		var selem = $('<td>');
		if (_gable('s')){
			selem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			selem.append($('<span>',{ 'class':"tbsearch-widget",title:_('Toggle_toolbar_search')})
				.button ({text:false, icons:{primary:'ui-icon-search'}})
				.click (function () { $grid[0].toggleToolbar();}) 
				);
		}
		// ---- pivot url
		var pelem = $('<td>');
		if (_gable('p')) {
			pelem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			pelem.append($('<span class="pivoturl-widget" style="padding-left:4px;padding-right:4px;">')) ;
		}
		// ---- zummary
		var zelem = $('<td>');
		if (_gable('z')){
			zelem.css({
				'padding-left':'2px',
				'padding-right':'2px',
				});
			function _summary_change () {
				var postdata = $grid.jqGrid('getGridParam','postData') ;
				var zval = $(this).val() ;
				if (!zval || zval=='') delete postdata._summary
				else postdata._summary = zval ;
				_gridReload();			
			}
			//var postdata = $grid.jqGrid('getGridParam','postData') ;
			var zsel = $('<select>',{'class':'summary-widget',style:'height:98%;'});
			zsel.append($('<option>',{value:'',html:_('no_summary')}));
			for (var z in options.summary_keys){
				z = options.summary_keys[z] ;
				zsel.append($('<option>',{value:z,html:_('summary')+'-'+z}));
			}
			var postdata = $grid.jqGrid('getGridParam','postData') ;
			var zval = postdata._summary || '';
			zsel.change(_summary_change).val(zval);
			zelem.append(zsel);
			zelem.after(sepelem);
		}
		var lbox = $('<table style="height:100%;float:left;padding-left:2px;">').append(
				$('<tr>').append(afelem).append(helem).append(ielem).append(zelem));
		var rbox = $('<table style="height:100%;float:right;padding-right:2px;">').append(
				$('<tr>').append(pelem).append(qelem).append(sepelem).append(selem));
		return $('<div style="width:100%;line-height:1em;">').append(lbox).append(rbox) ;
	}
	function errDOM(domoptions) {
		var attr = {'class':'ui-state-error',style:'padding:0.5em;line-height:3em;'};
		if ($.isPlainObject(domoptions)) $.extend(attr,domoptions);
		if (typeof domoptions=='string') attr.html = domoptions;
		
		var $err = $('<span>',attr) ;
		if (options.login_tag) {
			var $login = (typeof options.login_tag =='function')?options.login_tag() : $(options.login_tag) ;
			if ($login) $err.append($login);
		}
		return $err;
	}
	function gridDOM(domoptions) {
		var container = domoptions.container ;
		var gridid = domoptions.gridid;
		var pagerid = domoptions.pagerid;
		
		if (container) $grids = $(container);
		if (!$grids)
		{
			$grids = $('<div>',{style:'margin:.5em 0 .5em 0;width:100%'}).appendTo('body');
			if (container) $grids.attr('id',container.replace(/^#/,''));
		}
		$grids.append('<div class="unload_warning" style="display:none;" />');
		if (gridid) $grid = $(gridid);
		if (!$grid) {
			$grid = $('<table>') ;
			$grids.append($grid) ;
		}
		if (pagerid) $pager = $(pagerid);
		if (!$pager) {
			$pager = $('<div>');
			$grids.append($pager)
		}
		if (!$grid.attr('id')) {
			if (!gridid) {
				// --- global instance count ----
				if (typeof gridinstance=='undefined') gridinstance = 0;
				gridinstance++;
				gridid = '#grid'+gridinstance;
			}
			$grid.attr('id',gridid.replace(/^#/,''));
		}
		if (!$pager.attr('id')) {
			if (!pagerid)
				pagerid = gridid+'pager';
			$pager.attr('id',pagerid.replace(/^#/,''));
		}
		
		gridid = $grid.attr('id');
		pagerid = $pager.attr('id');
		var gopt = {
			grid: gridOption()
			,nav: navOption()
			,form: {
				edit: formOption('edit')
				,add: formOption('add')
				,del: formOption('del')
				,search: formOption('search')
				,view: formOption('view')
				}
			};
		_gopt = gopt;
		gopt.bindKeys = {onEnter: function(rowid){gopt.grid.ondblClickRow(rowid);},onSpace: _doRow('view')};
		gopt.grid.pager = '#'+pagerid ;
		if ($.inArray('addnew',options.pageoptions||[])>=0) gopt.grid.hiddengrid = true;

		if (typeof domoptions.beforeInitDOM=='function')
			domoptions.beforeInitDOM(gopt);
		if (!gopt.grid.colModel.length) {
			$grids.prepend($('<div>').append(errDOM(_('Not_allow_here'))));
			return $grids ;
		}
		if (gopt.grid.cellEdit) {
			gopt.grid.beforeSaveCell = _beforeSaveCell ;
		}
		gopt.grid.gridComplete = _gridComplete(gopt.grid.gridComplete);
		var flds= [] ;
		var cols = gopt.grid.colModel;
		for (var i in cols) {
			n = cols[i].name;
			p = (cols[i].hidden)? ':h':'';
			flds[i] = n+p;
		}
		gopt.grid._cols = array2json(flds);
		if (gopt.grid.scroll==1){
			gopt.grid.scrollrows = false;
			if (gopt.bindKeys) gopt.bindKeys.scrollingRows=false;
		}

		$grid
		.jqGrid(gopt.grid)
		.jqGrid('navGrid',gopt.grid.pager,gopt.nav
			,gopt.form.edit,gopt.form.add,gopt.form.del,gopt.form.search,gopt.form.view) ;
		if (gopt.bindKeys) {
			$grid.jqGrid('bindKeys', gopt.bindKeys);
		}
		if (options.grid_resizable!==false) {
			var minw = options.grid_minWidth || 350 ;
			if ($grid.width()<minw) minw = $grid.width();
			$grid.jqGrid('gridResize',{minWidth: minw,handles:'se',stop:_gridComplete()})
		}
		if (_gable('s')) {
			// ---- toolbar search
			$grid
			.jqGrid('filterToolbar', {stringResult: true,searchOnEnter: options.searchOnEnter||false,defaultSearch: 'cn'})
			.navButtonAdd(gopt.grid.pager,{
				caption:''
				,title:_('Toggle_toolbar_search')
				,buttonicon:'ui-icon-search' 
				,onClickButton:function(){ $grid[0].toggleToolbar();}
				,position:'last'
			});
		}

		if (_gable('x')){
			// export button

			$grid
			.navSeparatorAdd(gopt.grid.pager,{'sepclass' : 'ui-separator','sepcontent': ''})
			.navButtonAdd(gopt.grid.pager,{
				caption:""
				,title: _('Export_data_as_csv')
				,buttonicon:'ui-icon-disk'
				,onClickButton: _exportDialog()
				,position:'last'
				});
		}
		
		if (_gable('q') || _gable('z')) {
			$tb = customToolbar();
			$('#t_'+$grid.attr('id')).append($tb);
		}
		if (options.login_tag){
			var $login = (typeof options.login_tag=='function')?options.login_tag() : $(options.login_tag) ;
			if ($login) {
				ttb_box = $('<span style="float:right;margin-right:25px;">').append($login);
				$('.ui-jqgrid-titlebar',$grids).append(ttb_box);
			}
		}

		if (_gable('s') && $.inArray('tbsrch',options.pageoptions||[])<0)
			$grid[0].toggleToolbar();

		if (_gable('a') && $.inArray('addnew',options.pageoptions||[])>=0)
			_doRow('add')();

		if (typeof domoptions.ready=='function') 
			domoptions.ready.apply(this,[$grids,$grid]);
		if (isTouch())
		{
			$('.ui-icon-seek-first,.ui-icon-seek-prev,.ui-icon-seek-next,.ui-icon-seek-end',$pager)
			.wrap('<div class="ui-pg-div" style="padding:0 4px;">');
			$('div.ui-pg-div',$pager).css('padding','0 4px');
		}
		return $grids;
	}
	function ajaxcol(name){
		var ajaxcols = gparams.ajaxcols;
		if (!name) return ajaxcols;
		for (var c in ajaxcols) {
			c = ajaxcols[c];
			if (c.name==name) return c;
		}
	}
	function _inputDOM(domoptions,showlabel,labelwidth,initmode,idprefix) {
		var ajaxcols = gparams.ajaxcols;

		if ($.isArray(domoptions)){
			var ret = []
			for(var n in domoptions){
				ret.push(_inputDOM(domoptions[n],showlabel,labelwidth,initmode,idprefix));
			}
			return ret;
		}
		if ($.isPlainObject(domoptions)){
			var $input ;
			showlabel = showlabel || domoptions.showlabel;
			labelwidth = labelwidth || domoptions.labelwidth; 
			idprefix = idprefix || domoptions.idprefix;
			initmode = initmode || domoptions.initmode;
			if (domoptions.name) $input = _inputDOM(domoptions.name,showlabel,labelwidth,initmode,idprefix);
			if (domoptions.inputs){
				var $inputs = _inputDOM(domoptions.inputs,showlabel,labelwidth,initmode,idprefix);
				if ($input) $input = [$input,$inputs];
				else $input = $inputs;
			}
			return $input;
		}
		var inputname = domoptions.split('|').shift() ;
		var c = ajaxcol(inputname) ;
		if (c){
			var label = _(domoptions.split('|',2)[1] || '')
			if (label=='') label = _(c.label)
			var etype = c.edittype || 'input' ;
			idprefix = idprefix || $grid.attr('id')+'_';
			var option = {id:idprefix+inputname, name:inputname,title:label,placeholder:label} ;
			if (c.editoptions) option = $.extend(option,c.editoptions);
			delete option.datainit
			var $input = $('<'+etype+'>',option) ;
			var datainit = (initmode=='search')?c.searchoptions.dataInit:c.editoptions.dataInit;
			if (typeof datainit=='function')
				datainit($input[0]);
			if (showlabel){
				if (typeof showlabel!='string') showlabel = 'rleft';
				var ap = (showlabel == 'bottom' || showlabel == 'rbottom')?'append':'prepend';
				if (!labelwidth) labelwidth = '5em';
				if (showlabel=='left') showlabel = 'float:left;width:'+labelwidth+';'
				else if (showlabel=='cleft') showlabel = 'float:left;width:'+labelwidth+';text-align:center;'
				else if (showlabel=='rleft') showlabel = 'float:left;width:'+labelwidth+';text-align:right;'
				else if (showlabel=='right') showlabel = 'float:right;width:'+labelwidth+';'
				else if (showlabel=='cright') showlabel = 'float:right;width:'+labelwidth+';text-align:center;'
				else if (showlabel=='rright') showlabel = 'float:right;width:'+labelwidth+';text-align:right;'
				else if (showlabel=='top'||showlabel=='bottom') showlabel = 'display:block;'
				else if (showlabel=='rtop'||showlabel=='rbottom') {
					showlabel = 'display:block;width:100%;text-align:right;';
					$input.css('float','right');
					}
				else if (showlabel=='ctop'||showlabel=='cbottom') {
					showlabel = 'display:block;width:100%;text-align:center;';
					}
				var $lbl = $('<label>',{
					'for':$input.attr('name')
					,html:$input.attr('placeholder') || $input.attr('title')||$input.attr('name')
					,style:'overflow-x:hidden;white-space:nowrap;margin:0;padding-left:0.5em;padding-right:0.5em;'+showlabel
					});
				$input = ($('<div>',{style:'width:100%'}).append($input))[ap]($lbl);
			}
			return $input;
		}
		return name;
	}
	function inputDOM(domoptions,showlabel,labelwidth,initmode,idprefix) {
		var $input = _inputDOM(domoptions,showlabel,labelwidth,initmode,idprefix) ;
		if (domoptions.container){
			var $container = $(domoptions.container);
			if ($.isArray($input)) $input = tableDOM($input);
			if ($container) $container.append($input) ;
		}
		if (typeof domoptions.ready=='function') domoptions.ready.apply(this,[$input]);
		return $input;
	}

	function tableDOM(domarray) {
		var maxcol = 0;
		for (var dom in domarray) {
			dom = domarray[dom] ;
			var c = ($.isArray(dom))? dom.length:1;
			if (c>maxcol) maxcol = c;
		}

		var $table = $('<table>');
		for (var dom in domarray){
			$tr = $('<tr>');
			dom = domarray[dom];
			if (!$.isArray(dom)) dom = [dom];
			var $lasttd ;
			for (var i=0; i<maxcol; i++){
				$td = $('<td>');
				if (i==0 || (dom[i]!=false && dom[i]!=undefined && dom[i]!=null)){
					if (dom[i]) {$td.append(dom[i]);}
					$lasttd = $td;
				}else{
					$lasttd.attr('colspan',($lasttd.attr('colspan')||1)+1);
				}
				$tr.append($td);
			}
			$table.append($tr);
		}
		return $table;
	}
	function new_grid(domoptions) {
		gridDOM(domoptions);
		return this ;
	}
	function new_input(domoptions) {
		inputDOM(domoptions);
		return this ;
	}
}}
//----------------------
if (typeof jqGrid$=='undefined'){
jqGrid$ = function(options) {
	var grid = new jqgridwrapper(options);
	return grid;
}}

