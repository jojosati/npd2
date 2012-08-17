%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%if 'ajax_extfields' not in _vars :
<div style="padding:2em;"><span class="ui-state-error">
Warning, No model loaded at startup.
</span></div>
%else:
%include helper/language _vars=_vars
%locals().update(_vars)
%#-----------------------------------------------
%_able = kwoptions.get('able',locals().get('grid_able','gpsqadevzx'))
%_caption = kwoptions.get('caption',locals().get('grid_caption'))
%#-----------------------------------------------
%for _c in ajax_extfields :
% (_c,_lbl) = _c.split('|',1) if '|' in _c else (_c,'')
% (_c,_perm) = _c.split(':',1) if ':' in _c else (_c,'')
% if _c=='__table__' :
% _caption = _m(_caption if _caption is not None else _lbl)
% for _p in list(_able) :
% 	_able = _able.replace(_p,'') if _p not in _perm else _able
% end #for
% break
% end #if _c
%end #for
%#################################################
%if 'g' not in _able :
%#################################################
<div style="padding:2em;"><span class="ui-state-error">
{{_m('Please Login before viewing this page.//th:กรุณา ลงชื่อ ก่อนเข้าดูหน้านี้ ')}} <span id="login_required"></span>
</span></div>

<script type="text/javascript">
login_tag('#login_required');
$(document).ready(function() {
//login_dialog();
});
</script>
%#################################################
%else: #if 'g' not in _able :
%#################################################
<div id="grid-container"><div id="pivoturl"></div><table id="grid-list"></table><div id="grid-pager"></div></div>

%if language=='th' :
%_msg['summary_is_active']= 'ยอดสรุป เปิดใช้งานอยู่, ไม่อนุญาตให้ทำงานข้อนี้.'
%_msg['toggle_toolbar_search']= 'ซ่อน/แสดงแถบช่องค้นหา'
%_msg['select_export_scope']= 'เลือกขอบเขตการส่งออก'
%_msg['export_data_as_csv']= 'ส่งออกข้อมูลเป็น CSV'
%_msg['export_this_page'] = 'เฉพาะหน้านี้'
%_msg['export_all_pages'] = 'ทุกหน้า'
%_msg['close_button'] = 'ปิด'
%_msg['quick_search'] = 'ค้นหาด่วน'
%_msg['no_summary'] = 'รายการปกติ'
%_msg['summary'] = 'ยอดสรุป'
%else:
%_msg['summary_is_active']= 'Summary is active, not allow doing this operation.'
%_msg['toggle_toolbar_search']= 'Toggle toolbar search'
%_msg['select_export_scope']= 'Select export scope'
%_msg['export_data_as_csv']= 'Export data as CSV'
%_msg['export_this_page'] = 'Export this page'
%_msg['export_all_pages'] = 'Export all pages'
%_msg['close_button'] = 'Close'
%_msg['quick_search'] = 'Quick search'
%_msg['no_summary'] = 'no summary'
%_msg['summary'] = 'summary'
%end if
%_vscroll = kwoptions.get('vscroll',locals().get('grid_vcroll','false'))
%if _vscroll != '1' : _vscroll = 'false'
%_summary = 'z' in _able and kwoptions.get('summary',locals().get('grid_summary',''))
%_addnew = 'a' in _able and ('addnew' in pageoptions or locals().get('grid_addnew',False))
%_colreorder = 'colreorder' in pageoptions or locals().get('grid_colreorder',False)
%_colreorder = 'true' if _colreorder else 'false'
%_autocomplete_scope = locals().get('modeler_options',{}).get('autocomplete_scope',{})
%try: _rownum = int(kwoptions.get('rownum',locals().get('grid_rownum',20)))
%except: _rownum = 10
%if _vscroll!='false' and _rownum < 30 : _rownum = 30
%_autofit = ((kwoptions.get('autofit',locals().get('grid_autofit')) or '.9') + '-.5').replace('-',',').split(',')[:2]
%#if len(_autofit)==1 : _autofit.append('.5')
%_rownumlist = locals().get('grid_rownumlist') or '10,20,50,100'
%_rownumlist = [int(_n) for _n in _rownumlist.split(',')]
%if _rownum not in _rownumlist :
%_rownumlist.append(_rownum)
%_rownumlist.sort()
%end 
%_height=locals().get('grid_height','"auto"' if _rownum < 20 and _vscroll=='false' else '($(window).height() * '+_autofit[-1]+')')
%_width=locals().get('grid_width','($(window).width() * '+_autofit[0]+')')
%#-----------------------------------------------
%_tbsrch = 'tbsrch' in pageoptions or kwoptions.get('tbsrch',locals().get('grid_tbsrch'))
%if isinstance(_tbsrch,basestring) : 
%_tbsrch = _tbsrch.lower() not in ('false','off','no','0')
%end #if
%#-----------------------------------------------
%_sortname = kwoptions.get('sort',locals().get('grid_sort','id-desc'))
%(_sortname,_sortorder) = _sortname.split('-',-1) if '-' in _sortname else (_sortname,'')
%if _sortorder not in ('asc','desc') : _sortorder = 'desc'
%#-----------------------------------------------
%_urltag = ''
%for _o in pageoptions :
%_uo = _o.replace('~','~~').replace('/','~/')
%if not _urltag :
%_urltag = _uo
%else:
%_urltag += "//" + _uo
%end #if not 
%end #for _o
%#-----------------------------------------------


<link type="text/css" href="/{{suburl}}/resource/css/ui.jqgrid.css" rel="Stylesheet">
<script type="text/javascript" src="/{{suburl}}/resource/js/i18n/grid.locale-{{language}}.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.jqGrid.min.js"></script>
<script type="text/javascript">

var colModel = [
%_sep = ''
%_frmpos = [1,1,2,'']
%for _c in ajax_extfields :
% (_c,_lbl) = _c.split('|',1) if '|' in _c else (_c,'')
% (_c,_perm) = _c.split(':',1) if ':' in _c else (_c,'')
% if _c=='__table__' : continue
% _lbl = _m(_lbl or _c)
% _w = _perm.find('W(')
% if _w >= 0 :
%   _e = _perm.find(')',_w)
%	_w = int(_perm[_w+2:_e]) if _e > _w else None
% end #_w
% _l = _perm.find('L(')
% if _l >= 0 :
%   _e = _perm.find(')',_l)
%	_l = int(_perm[_l+2:_e]) if _e > _l else None
% end #_l
% _g = _perm.find('G(')
% if _g >= 0 :
%   _e = _perm.find(')',_g)
%	_g = _perm[_g+2:_e] if _e > _g else None
% end #_g
% if (_w > 5 or _g!=_frmpos[3]) and _frmpos[1]!=1:
%   _frmpos[0] += 1; _frmpos[1] = 1
% end
	{{_sep}}{	'name':'{{!_c}}', 'index':'{{!_c}}', 'label':'{{!_lbl}}', 'width': {{str(_w*50) if _w > 0 else '150'}}
		,'align' : '{{ 'right' if 'N' in _perm else ('center' if 'D' in _perm else 'left')}}'{{",'formatter':'number'" if 'N' in _perm else ""}}
		,'hidden':{{'true' if 'h' in _perm else 'false'}}
		,'editrules':{'edithidden':true, 'required':{{'true' if 'r' in _perm else 'false'}}, 'number':{{'true' if 'N' in _perm else 'false'}} }
		,'editable' :{{'true' if 'a' in _perm or 'e' in _perm else 'false'}}{{" ,'edittype':'textarea'" if _w > 5 else ""}}
		,'editoptions':{'dataInit':{{'function(elem){$(elem).datepicker();}' if 'D' in _perm else ('edit_autocomplete' if 'N' not in _perm else 'undefined')}}{{(", 'cols':"+str(_w*10)) if _w > 3 else ""}}{{(", 'rows':"+('1' if _l<=0 else str(_l))) if _w > 5 else ""}} }
		,'formoptions':{'rowpos':{{_frmpos[0]}}, 'colpos':{{_frmpos[1]}} }{{",'addform': 'hide'" if 'a' not in _perm else ""}}{{",'editform': 'disabled'" if 'e' not in _perm else ""}}
		,'search':true
		,'searchoptions': {'searchhidden': true, 'dataInit' : {{'toolbar_autocomplete' if 'N' not in _perm and 'D' not in _perm else 'undefined'}} }
		
	}
% _frmpos[3] = _g
% if _w > 5 :
%   _frmpos[0] += 1; _frmpos[1] = 1
% else :
%   _frmpos[1] += 1 ;
%   if _frmpos[1]>_frmpos[2] : _frmpos[0] += 1; _frmpos[1] = 1
% end

%_sep = ','
%end #for _c
	] ;
var editOption = {/*add & edit*/'modal':true, 'width':600, 'labelswidth':'10%'
			,'closeAfterEdit': true, 'clearAfterAdd' : false, 'reloadAfterSubmit':false, 'checkOnUpdate':true
			,'recreateForm': true
			,'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}
			,"beforeShowForm" : editform_colspan
			,'mtype':'GET'
			} ;
var addOption = {/*add & edit*/'modal':true, 'width':600, 'labelswidth':'10%'
			,'closeAfterEdit': true, 'clearAfterAdd' : false, 'reloadAfterSubmit':false, 'checkOnUpdate':true
			,'recreateForm': true
			,'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}
			,"beforeShowForm" : addform_colspan
			,'mtype':'GET'
			} ;
var delOption = {/*del*/'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}};
var searchOption = {/*search*/} ;
var viewOption = {/*view*/'modal':true, 'width':'750', 'labelswidth':'10%'
			,"beforeShowForm" : showform_colspan
			} ;

var gridOption = {
	'sortable': {{!_colreorder}},
	'url':'/{{suburl}}/ajax/jqgrid',
	'editurl':'/{{suburl}}/ajax/jqgrid/edit',
	'postData': { {{("'_summary':'"+_summary+"'") if _summary else ""}} },
	'datatype': "json",
	'colModel': colModel,
%if _width :
	'width': {{_width}},
%end
%if _height :
	'height': {{_height}}, //"100%",
%end
%if _addnew :
	'hiddengrid' : true,
%end
	'rowNum':{{_rownum}},
	'rowList':{{_rownumlist}},
	'pager': '#grid-pager',
	'prmNames' : {'npage':'npage'},
	'scroll' : {{!_vscroll}},
	'scrollrows' : {{'true' if _vscroll else 'false'}},
	'sortname': '{{!_sortname}}',
	'viewrecords': true,
	'sortorder': '{{!_sortorder}}',
	'caption': '{{!_caption}}',
	/*'onPaging': function(pgButton){
			if (pgButton=='records'){
				if ($('.ui-pg-selbox').val() < 20) { h = 'auto';}
				else {h=$(window).height() * .5;}
				$(this).setGridHeight(h);
				$(this).setGridHeight($(window).width() * .9);
				}},*/
	'beforeRequest' : beforeRequest,
	//'cmTemplate': {'resizable':false},
%if 'v' in _able:
	'ondblClickRow':function( rowid ) { $(this).viewGridRow (rowid,viewOption);},
%end
	'toolbar': [{{'true' if 'q' in _able  or 'z' in _able else 'false'}},'top'] //,
    }
// auto manipulate customizable part
%if 'pivotcmds' in locals() :
	gridOption.postData['pivotcmds'] = stringify_list({{!pivotcmds}});
%end
%if 'grid_showcols' in locals():
	_show = {{grid_showcols.split(',')}};
	// prepare col order
	_colmodel = [] ;
	for (x in _show) {
		_n = _show[x] ;
		_h = ''
		if (_n[0]=='!' || _n[0]=='~') {
			_h = _n[0] ;
			_n = _n.slice(1) ;
		}
		if (_n=='*')
		{
			for (i in colModel) {
				_n = colModel[i].name ;
				_exist = false;
				for (ii in _colmodel) {
					_exist =(_n==_colmodel[ii].name)
					if (_exist) break ;
				}
				if (!_exist) {
					if (_h != '~') {
						colModel[i]['hidden'] = (_h=='!') ;
					}
					_colmodel.push(colModel[i]) ;
				}
			}
		}
		else {
			_exist = false;
			for (i in _colmodel) {
				_exist = (_n==_colmodel[i].name) ;
				if (_exist) {
					if (_h != '~') 
						_colmodel[i]['hidden'] = (_h=='!') ;
					break ;
				}
			}
			if (!_exist) {
				for (i in colModel) {
					if (_n==colModel[i].name) {
						if (_h != '~') 
							colModel[i]['hidden'] = (_h=='!') ;
						delete colModel[i]['formoptions']
						_colmodel.push(colModel[i]) ;
					}
				}
			}
		}
	}
	if (_colmodel.length)
		gridOption.colModel = _colmodel ;
%end

function edit_autocomplete (elem,tax,len,gridfilter) {
	if (!tax) tax = elem.id ;
	len = (typeof len == 'undefined')? 0 : len;
	gridfilter = (typeof gridfilter=='undefined')? false : gridfilter;
	var urlfn = gridfilter? 'taxonomy' :'autocomplete' ;
	var url = "/{{suburl}}/ajax/"+urlfn+"/"+tax;
	var scope = '';
	if (!gridfilter) {
		_scopes = {{!_autocomplete_scope}} ;
		for (sc in _scopes) {
			if ($.inArray(tax,_scopes[sc])>=0) {
				scope = sc ;
				break ;
				}
			}
		}

    $(elem).autocomplete ({
        'source': url
        ,'minLength':len
		,'delay':gridfilter?1500:500
        });

    if (len==0) {
        $(elem).click(function () {if (!$(this).val()) {$(this).autocomplete("search","");}});
        }
	//if (typeof(scope) == "string") {
		$(elem).bind( "autocompletesearch", function(event, ui) {
			var grid = $("#grid-list");
			var qry = {} ;
			var u = url
			if (scope) qry[scope] = $('#'+scope).val() ;
			if (gridfilter) {
				var postdata = grid.jqGrid('getGridParam','postData') ;
				for (k in postdata) {
					if (k == "pivotcmds" || k == "qsearch" || k=="_cols") {
						if (postdata[k]) {
							qry[k] = postdata[k];
							}
						}
				}
				if (postdata['_search']) {
					k = 'filters'
					if (postdata[k]) qry[k] = postdata[k];
					}
				}
			q = $.param(qry);
			if (q)
				u += "?"+q
			
			$(elem).autocomplete( "option", "source",u);
			return true;
			});
	//	}
}

function toolbar_autocomplete (elem) {
	tax = elem.id.replace('gs_','');
	len = 1
    edit_autocomplete(elem,tax,len,true);
    $(elem).bind( "autocompletechange", function(event, ui) {$("#grid-list")[0].triggerToolbar();});
}

function stringify_list (obj) {
	s = "" ;
	for (n in obj) {
		if (s.length > 0) s += "," ;
		s += "\"" + obj[n].replace(/\\/g,'\\\\').replace(/\"/g,'\\"') + "\"" ;
	}
	return "[" + s + "]" ;
}

function getColModel () {
	var grid = $("#grid-list");
	var cols = grid.jqGrid('getGridParam','colModel');
	var ret = new Array()
	for (i=0; i<cols.length; i++) {
		//var prop = grid.jqGrid("getColProp", cols[i].name)
		p = ""
		if (cols[i].hidden) p += "h" ; 
		if (p.length) p = ":" + p ;
		ret.push(cols[i].name+p)
	}
	return stringify_list(ret)
}

function gridReload(){
	var grid = $("#grid-list");
    grid.trigger("reloadGrid");
}

function autofitGrid(elem,w,h){
	var grid = $("#grid-list");
	if (!w) w = {{_autofit[0]}}; 
	if (w<1) w *=$(window).width() ;
	if (!h) h = {{_autofit[-1]}};
	if (h<1) h *=$(window).height() ;
	grid.setGridHeight(h);
	grid.setGridWidth(w,true);
}

%#------------ quick search
%if 'q' in _able :
var timeoutHnd;
function quickSearch(ev){
	if(timeoutHnd)
		clearTimeout(timeoutHnd)
	timeoutHnd = setTimeout(gridReload,500)
}
%end 

%if 'z' in _able and summary_keys :
function summaryChange() {
	var grid = $("#grid-list");
    var postdata = grid.jqGrid('getGridParam','postData') ;
	var zval = $('#summary_mode').val() ;
	
	if (!zval) delete postdata._summary
	else postdata._summary = zval ;
	
	gridReload();
}
%end #----------- quick search

function prepare_pivoturl () {
	var alink = $("#pivoturl_link") ;
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	var pv = []; //(postdata.pivotcmds)? eval("(" + "{{!pageoptions}}" + ")") : [] ;
	var pvstr = "" ; //{{!_urltag}}" ;
	var isnew = false ;

	pageoptions = {{!pageoptions}};
	for (s in pageoptions) {
		s = pageoptions[s] ;
		if (s.search('summary-')==0 || s.search('sort-')==0) continue ;
		if (pvstr) pvstr += '/' ;
		pvstr += s ;
		}
	if (postdata._search && postdata.filters) {
		filters = eval("(" + postdata.filters + ")") ;
		for (x in filters.rules) {
			x = filters.rules[x] ;
			pv.push ("@f-"+x.field+"-"+x.data) ;
			}
		}
	if (postdata.qsearch) {
		pv.push ("@f--"+postdata.qsearch) ;
		}
	if (postdata._summary) {
		pv.push ("summary-"+postdata._summary) ;
		if (postdata.sidx) {
			s = postdata.sidx ;
			if (postdata.sord) s += '-' + postdata.sord ;
			pv.push ("sort-"+s);
			}
		}
		
	alink.html("") ;
	if (pv.length>0) {
		for (x in pv) {
			//opv =(pv[x]) ;
			pv[x] = pv[x].replace(/~[/]/g,"/").replace(/~~/g,"~").replace(/~/g,"~~").replace(/[/]/g,"~/") ;
			}
		if (pvstr) pvstr += "//";
		pvstr += pv.join('//') ;
		pv = pvstr.split("//"); 
		sep = "/"
		for (x in pv) {
			if (x.indexOf("/") >= 0) {
				sep = "//" ;
				break ;
			}
		}

		if (sep!="//") pvstr = pv.join(sep) ;
		subpage = "{{!urlsubpage}}".replace('subpage/','') ;
		if (subpage) subpage = "/" + subpage
		alink.html("<a href='"+("/{{!suburl}}"+subpage+"//"+pvstr)+"'>pivot-url</a>") ;
	}
}

var postData_cols = ''
function beforeRequest () {
	var grid = $("#grid-list");
    var postdata = grid.jqGrid('getGridParam','postData') ;
	
	if (!postData_cols) {
		postData_cols = getColModel() ;
	}
	if (postData_cols != '{{ajax_fields}}') {
		postdata._cols = postData_cols ;
	} else delete postdata._cols ;
	
	if ($("#qsearch").val()) {
		postdata.qsearch =  $("#qsearch").val() ;
	} else {
		delete postdata.qsearch ;
	}
	/*if ($("#summary_mode").val()) {
		postdata._summary =  $("#qsearch").val() ;
	} else {
		delete postdata._summary ;
	}*/
	grid.jqGrid('setGridParam',{'postData':postdata})
	prepare_pivoturl() ;
	return true;
}

function showform_colspan (form,formmode) {
    formmode = (typeof formmode=='undefined')? '' : formmode;
    form = $(form);
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
	if (formmode) {
		var grid = $("#grid-list");
		var cols = grid.jqGrid('getGridParam','colModel');
		var modecol = function(name) {
			for (c in cols){
				c=cols[c];
				if(c['name']==name){return c[formmode+'form'];}
				}
			return undefined
			} ;
		$("tr", form).each(
			function() {
				var tds = $(">td", this);
				for (i=0; i < tds.length; i++) {
					if (tds.eq(i).hasClass('DataTD')) {
						inp = $('input,select,textarea:first',tds.eq(i));
						n = inp.attr('name') ;
						if (!n) continue;
						m = modecol(n);
						if (m=='hide') {
							tds.eq(i-1).hide();
							tds.eq(i).hide();
						}
						if (m=='disabled') {
							inp.attr('disabled','disabled');
						}
					}
				}
		});
	}
}

function editform_colspan (form) {showform_colspan(form,'edit');}

function addform_colspan (form) {showform_colspan(form,'add');}

function doAddRow() {
%if 'a' in _able :
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	if (!postdata['_summary']) {
		grid.jqGrid('editGridRow','new',addOption);
	} else {
		$('<div/>',{'html': '{{_m('summary_is_active')}}'}).dialog({'dialogClass':'ui-state-focus','close': function(){$(this).remove();}});
	}
%end
}
function doEditRow(rowid) {
%if 'e' in _able :
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	if (!postdata['_summary']) {
		grid.jqGrid('editGridRow',rowid,editOption);
	}  else {
		$('<div/>',{'html': '{{_m('summary_is_active')}}'}).dialog({'dialogClass':'ui-state-focus','close': function(){$(this).remove();}});
	}
%end
}
function doDelRow(rowid) {
%if 'd' in _able :
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	if (!postdata['_summary']) {
		grid.jqGrid('delGridRow',rowid,delOption);
	}  else {
		$('<div/>',{'html': '{{_m('summary_is_active')}}'}).dialog({'dialogClass':'ui-state-focus','close': function(){$(this).remove();}});
	}
%end
}
%# -----------------------------------------
$(document).ready(function() {
    $("#grid-list")
	.jqGrid(gridOption)
    .jqGrid('navGrid','#grid-pager'
		,{
			'edit':{{'true' if 'e' in _able else 'false'}}
			,'add': {{'true' if 'a' in _able else 'false'}}
			,'del': {{'true' if 'd' in _able else 'false'}}
			,'search': false // alternate use filter toolbar below
			,'view': {{'true' if 'v' in _able else 'false'}}
			,'beforeRefresh' : function () {
				/*$("#grid-list")
					.setGridHeight({{_height}})
					.setGridWidth({{_width}})
					;*/
				$(".ui-jqgrid")
					.css({
						'height': ($(".ui-jqgrid-view").height() + $(".ui-jqgrid-pager").height()) + "px",
						'width': $(".ui-jqgrid-view").width() + "px"
						});
				}
			,'addfunc': doAddRow
			,'editfunc': doEditRow
			,'delfunc': doDelRow
			
			}
		,editOption
		,addOption
		,delOption
		,searchOption
		,viewOption
		)
    .jqGrid('gridResize',{'minWidth':350,'handles':'se'})
	.jqGrid('bindKeys', {
		"onEnter":function( rowid ) {
%if 'e' in _able :
			doEditRow(rowid);
%end
			}
		,"onSpace":function( rowid ) {
%if 'v' in _able :
		 $(this).jqGrid('viewGridRow',rowid,viewOption);
%end
			}
		} )
%if 's' in _able :
    .jqGrid('filterToolbar', {'stringResult': true, 'searchOnEnter': false,'defaultSearch': 'cn'})
    //.jqGrid('filterToolbar',{stringResult: true,searchOnEnter : true})
%end #if
    ;

%if 's' in _able : # button search toolbar
$("#grid-list").navButtonAdd('#grid-pager',{
   'caption':"", 
   'title': '{{_m('toggle_toolbar_search')}}',
   'buttonicon':"ui-icon-search", 
   'onClickButton': function(){ $("#grid-list")[0].toggleToolbar();}, 
   'position':"last" //,
});
%end #if
%if 'x' in _able : # button export
function exportCSV () {
	//beforeRequest () ;
	var url = '/{{!suburl}}/csv/jqgrid' ;
	var dlg = $('<div id="exportDialog"></div>');
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	var qry = {} ;
	
	for (k in postdata) {qry[k] = postdata[k];}
	if (!qry['_search']) { delete qry['_search']; delete qry['filters']; }
	qry['_dl'] = '1';
	dlg.html('<div id="expdlg_msg"></div><div id="expdlg_content"></div>') ;
	q = $.param(qry); if (q) q = '?'+q ;
	$('#expdlg_msg',dlg).html('{{_m('select_export_scope')}}') ;
	$('#expdlg_content',dlg).html('<table><tr><td><a id="exportPage" target="self" style="width:100%"></a></td></tr><tr><td><a id="exportAll" target="self" style="width:100%"></a></td></tr></table>') ;
	$('#exportPage',dlg).html('{{_m('export_this_page')}}').attr('href',url+q).button();
	qry['rows'] = '-1'; qry['page'] = '1';
	q = $.param(qry); if (q) q = '?'+q ;
	$('#exportAll',dlg).html('{{_m('export_all_pages')}}').attr('href',url+q).button();
	dlg.dialog({ 
		'modal':true,
		'title': '{{_m('export_data_as_csv')}}',
		'open' : function() {$('#exportPage',this).blur();},
		'close': function() {this.dialog('destroy');},
		'buttons': {'{{_m('close_button')}}':function() { $(this).dialog("close");}}
		}) ;
}

$("#grid-list")
	.navSeparatorAdd("#grid-pager",{'sepclass' : 'ui-separator','sepcontent': ''})
	.navButtonAdd('#grid-pager',{
		'caption':"",'title': '{{_m('export_data_as_csv')}}','buttonicon':"ui-icon-disk", 
		'onClickButton': exportCSV ,'position':"last" //,
	});
%end #if

%#---------------------------------
%#---- custom toolbar ----
%sepelem = '<td class="ui-state-disabled" style="width:4px;"><span class="ui-seperator"></span></td>\\n'
%if 'q' in _able or 'z' in _able :
%#---- quick search
%if 'q' in _able :
%	qelem = '<td style="padding-left:2px;padding-right:2px;">\\n'
%	qelem += '<input id="qsearch" title="'+_m('quick_search')+'" placeholder="'+_m('quick_search')+'" style="height:1em;" onkeydown="quickSearch(arguments[0]||event);"/>\\n'
%	qelem += '</td>\\n' + sepelem
%else :
%	qelem = '<td></td>\\n'
%end if
%#---- autofit grid
%afelem = '<td id="_block" style="padding-left:2px;padding-right:2px;"><span id="autofit_btn"></span></td>\\n'
%#---- search toolbar
%selem = '<td id="tbsearch_block" style="padding-left:2px;padding-right:2px;"><span id="tbsearch_btn"></span></td>\\n'
%#---- pivot url
%pelem = '<td style="padding-left:2px;padding-right:2px;">\\n'
%pelem += '<span id="pivoturl_link" style="padding-left:4px;padding-right:4px;'
%pelem += 'display:none;' if 'p' not in _able else ''
%pelem += '"></span>\\n</td>\\n'
%#---- zummary
%if 'z' in _able and summary_keys :
%  zelem = '<option value="">'+_m('no_summary')+'</option>\\n'
%  for z in summary_keys :
%    zelem += '<option value="'+z+'"'
%    zelem += ' selected="selected"' if z==_summary else '' 
%    zelem += '>'+_m('summary')+'-'+z+'</option>\\n'
%  end #for
%  zelem = '<select id="summary_mode" class="ui-widget-content" style="height:96%;" onchange="summaryChange();">\\n' +zelem + '</select>\\n'
%  zelem = '<td style="padding-left:2px;padding-right:2px;">\\n'+zelem+'</td>\\n'+sepelem
%else :
%  zelem = '<td></td>\\n'
%end if
$('#t_grid-list').append(''
	+'<table cellspacing="0" cellpadding="0" border="0" style="height:100%;float:left;padding-left:2px;"><tbody><tr>\n'
	+'{{!zelem}}'
	+'{{!afelem}}'
	+'</tr></tbody></table>\n'
	+'<table cellspacing="0" cellpadding="0" border="0" style="height:100%;float:right;padding-right:2px;"><tbody><tr>\n'
	+'{{!pelem}}'
	+'{{!qelem}}'
	+'{{!selem}}'
	+'</tr></tbody></table>\n'
	);

%if 's' in _able :
$("#tbsearch_btn")
	.button ({
		'text': false,
		'icons': {'primary': "ui-icon-search"}
		})
	.click (function () { $("#grid-list")[0].toggleToolbar();})
	.attr('title','{{_m("toggle_toolbar_search")}}')
	;
%end #if
$("#autofit_btn")
	.button ({
		'text': false,
		'icons': {'primary': "ui-icon-arrow-4-diag"}
		})
	.click (autofitGrid)
	.attr('title',"autofit")
	;
%end #---- custom toolbar ----
%#---------------------------------
ttb_box = $('<span style="float:right;margin-right:20px;"></span>');
ttb_box.append(login_tag());
$('.ui-jqgrid-titlebar').append(ttb_box);
%if not _tbsrch :
$("#grid-list")[0].toggleToolbar();
%end
%if _addnew :
$("#grid-list").jqGrid('editGridRow','new',addOption) ;
%end

	
}); // end document ready process

</script>
%#################################################
%end ####if 'g' not in _able :
%#################################################
%end ####if 'ajax_extfields' in _vars :
