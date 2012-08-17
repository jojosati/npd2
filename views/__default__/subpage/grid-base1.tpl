%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%locals().update(_vars)
%#-----------------------------------------------
%try: _rownum = int(kwoptions.get('rownum',locals().get('grid_rownum',10)))
%except: _rownum = 10
%_rownumlist = locals().get('grid_rownumlist') or '10,20,50,100'
%_rownumlist = _rownumlist.split(',')
%_rownumlist = [int(n) for n in _rownumlist]
%if _rownum not in _rownumlist :
%_rownumlist.append(_rownum)
%_rownumlist.sort()
%end 
%_height=locals().get('grid_height','"auto"' if _rownum <= 10 else '($(window).height() * .5)')
%_width=locals().get('grid_width','($(window).width() * .9)')
%#-----------------------------------------------
%_tbsrch = 'tbsrch' in pageoptions or kwoptions.get('tbsrch',locals().get('grid_tbsrch'))
%if isinstance(_tbsrch,basestring) : 
%_tbsrch = _tbsrch.lower() in ('false','off','no','0')
%end #if
%#-----------------------------------------------
%_sortname = kwoptions.get('sort',locals().get('grid_sort','id-desc'))
%(_sortname,_sortorder) = _sortname.split('-',-1) if '-' in _sortname else (_sortname,'')
%if _sortorder not in ('asc','desc') : 
%_sortorder = 'desc'
%end #if
%#-----------------------------------------------
%_caption = kwoptions.get('caption',locals().get('grid_caption','Procious Assets'))
%#-----------------------------------------------
%_able = kwoptions.get('able',locals().get('grid_able','eadsvq'))
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
%user_role = user_role or "guest"
%if user_role not in ['developer','administrator','manager','editor'] :
%_able = _able.replace('e','').replace('d','').replace('a','') #disable eda ability
%if '@sellable' not in pivotcmds:
%pivotcmds.append('@sellable')
%end
%end
%#-----------------------------------------------
<link type="text/css" href="/{{suburl}}/resource/css/ui.jqgrid.css" rel="Stylesheet" />
<script type="text/javascript" src="/{{suburl}}/resource/js/i18n/grid.locale-en.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.jqGrid.min.js"></script>

<div id="grid-container"><div id="pivoturl"></div><table id="grid-list"></table><div id="grid-pager"></div></div>

<script>
var colModel = [
		{'name':'acat','index':'acat','width':150,'label':'ชนิด'
			,'editable':true, 'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'acat',0);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':1, 'colpos':1}
			, 'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'acat',0);}}
			}
		,{'name':'condition','index':'condition','width':100,'label':'สภาพ'
			,'editable':true, 'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'condition',0);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':1, 'colpos':2}
			,'search':true, 'searchoptions':{'searchhidden': true,'dataInit' : function (elem) {toolbar_autocomplete(elem,'condition',0);}}
			}
		,{'name':'code','index':'code','width':180,'label':'รหัส'
			,'editable':true, 'editrules':{'required':true},'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'code',0,'acat');}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':2, 'colpos':1}
			, 'search':true, 'searchoptions':{'searchhidden': true,'dataInit' : function (elem) {toolbar_autocomplete(elem,'code',1);}}
			}
		,{'name':'detail','index':'detail','width':400,'label':'รายละเอียด'
			,'editable':true, 'edittype': 'textarea', 'editoptions': {'rows':3, 'cols':50, 'dataInit' : function (elem) {edit_autocomplete(elem,'detail',1,'acat');}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':3, 'colpos':1}
			, 'search':true, 'searchoptions':{'searchhidden': true,'dataInit' : function (elem) {toolbar_autocomplete(elem,'detail',1);}}
			}
		,{'name':'weight','index':'weight','width':200,'label':'น้ำหนัก'
			,'editable':true, 'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'weight',1,'acat');}}
			,'formoptions': {'rowpos':4, 'colpos':1}
			,'editrules':{'edithidden':true}
			, 'search':true, 'searchoptions':{'searchhidden': true,'dataInit' : function (elem) {toolbar_autocomplete(elem,'weight',1);}}
			}
		,{'name':'serial','index':'serial','width':200,'label':'เบอร์'
			,'editable':true, 'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'serial',1,'acat');}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':4, 'colpos':2}
			, 'search':true, 'searchoptions':{'searchhidden': true,'dataInit' : function (elem) {toolbar_autocomplete(elem,'serial',1);}}
			}
%if user_role in ['developer','administrator','manager','editor'] :
		,{'name':'owner','index':'owner','label':'ซื้อจาก'
			,'hidden':true
			,'editable':true,'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'owner',1);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':5, 'colpos':1}
			, 'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'owner',1);}}
			}
		,{'name':'buy_date','index':'buy_date','width':200,'label':'วันที่ซื้อ'
			,'hidden' : false
			,'editable':true,'editoptions': {'dataInit' : function (elem) {$(elem).datepicker();}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':5, 'colpos':2}
			//,'datefmt':'d/m/Y', 'formatter':'date'
			, 'search':true, 'searchoptions':{'searchhidden': true/*, 'dataInit' : function (elem) {$(elem).datepicker();}*/}
			}
%end
%if user_role in ['developer','administrator','manager'] :
			,{'name':'base_cost','index':'base_cost','width':200,'label':'ทุนซื้อ'
			,'hidden':true
			,'editable':true 
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':6, 'colpos':1}
			, 'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
		,{'name':'extra_cost','index':'extra_cost','width':200,'label':'ปรับปรุง'
			,'hidden':true
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':6, 'colpos':2}
			, 'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
		,{'name':'mark_cost','index':'mark_cost','width':200,'label':'ทุนร้าน'
			,'hidden':true
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':7, 'colpos':1}
			, 'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
%end
		,{'name':'keeper','index':'keeper','label':'ที่เก็บ'
			,'editable':true,'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'keeper',0);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':8, 'colpos':1}
			,'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'keeper',0);}}
			}
%if user_role in ['developer','administrator','manager','editor'] :
		,{'name':'keep_date','index':'keep_date','width':100,'label':'วันที่เก็บ'
			,'hidden':true 
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':8, 'colpos':2}
			,'editable':true,'editoptions': {'dataInit' : function (elem) {$(elem).datepicker();}}
			//,'datefmt':'d/m/Y', 'formatter':'date'
			, 'search':true, 'searchoptions':{'searchhidden': true/*, 'dataInit' : function (elem) {$(elem).datepicker();}*/}
			}
%end
%if user_role in ['developer','administrator','manager','editor','viewer'] :
		,{'name':'taker','index':'taker','label':'ผู้ยืม'
			,'editable':true,'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'taker',1);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':9, 'colpos':1}
			,'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'taker',1);}}
			}
%end
%if user_role in ['developer','administrator','manager','editor'] :
		,{'name':'take_date','index':'take_date','width':100,'label':'วันที่ยืม'
			,'hidden':true
			,'editable':true,'editoptions': {'dataInit' : function (elem) {$(elem).datepicker();}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':9, 'colpos':2}
			//,'datefmt':'d/m/Y', 'formatter':'date'
			, 'search':true, 'searchoptions':{'searchhidden': true/*, 'dataInit' : function (elem) {$(elem).datepicker();}*/}
			}
		,{'name':'taker_price','index':'taker_price','width':200,'label':'ราคายืม'
			,'hidden':true
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':10, 'colpos':1}
			, 'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
		,{'name':'lowest_price','index':'lowest_price','width':200,'label':'ราคาประเมิน'
			,'hidden':true
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':11, 'colpos':1}
			,'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
%end
			,{'name':'target_price','index':'target_price','width':200,'label':'ราคาตั้งขาย'
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':11, 'colpos':2}
			,'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
%if user_role in ['developer','administrator','manager','editor'] :
		,{'name':'buyer','index':'buyer','label':'ขายให้'
			,'editable':true
			,'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'buyer',1);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':12, 'colpos':1}
			,'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'buyer',1);}}
			}
		,{'name':'sell_date','index':'sell_date','width':200,'label':'วันที่ขาย'
			,'hidden':true
			,'editable':true,'editoptions': {'dataInit' : function (elem) {$(elem).datepicker();}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':12, 'colpos':2}
			//,'datefmt':'d/m/Y', 'formatter':'date'
			, 'search':true, 'searchoptions':{'searchhidden': true/*, 'dataInit' : function (elem) {$(elem).datepicker();}*/}
			}
		,{'name':'sell_price','index':'sell_price','width':200,'label':'ราคาขาย'
			,'hidden':true
			,'editable':true
			,'editrules':{'edithidden':true, 'number':true}
			,'formoptions': {'rowpos':13, 'colpos':1}
			,'align':'right', 'formatter':'number', 'formatoptions':{'defaultValue': ' '}
			,'search':true, 'searchoptions':{'searchhidden': true}
			}
		,{'name':'sell_site','index':'sell_site','label':'สถานที่ขาย'
			,'hidden':true
			,'editable':true,'editoptions': {'dataInit' : function (elem) {edit_autocomplete(elem,'sell_site',1);}}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':13, 'colpos':2}
			,'search':true, 'searchoptions':{'searchhidden': true, 'dataInit' : function (elem) {toolbar_autocomplete(elem,'sell_site',1);}}
			}
		,{'name':'memo','index':'memo','label':'บันทึก'
			,'hidden':true
			,'editable':true,'edittype': 'textarea','editoptions': {'rows':3, 'cols':50}
			,'editrules':{'edithidden':true}
			,'formoptions': {'rowpos':14, 'colpos':1}
			,'search':true, 'searchoptions':{'searchhidden': true,}
			}
%end
] ;
var gridOption = {
	'sortable': true,
	'url':'/{{suburl}}/ajax/jqgrid',
	'editurl':'/{{suburl}}/ajax/jqgrid/edit',
	'postData': {},
	'datatype': "json",
	'colModel': colModel,
%if _width :
	'width': {{_width}},
%end
%if _height :
	'height': {{_height}}, //"100%",
%end
	'rowNum':{{_rownum}},
	'rowList':{{_rownumlist}},
	'pager': '#grid-pager',
	'sortname': '{{!_sortname}}',
	'viewrecords': true,
	'sortorder': '{{!_sortorder}}',
	'caption': '{{!_caption}}',
	//'onPaging': function(){$('#gbox_'+this.id).css('height','');$(this).setGridHeight('auto');},
	'beforeRequest' : beforeRequest,
	'toolbar': [{{'true' if 'q' in _able else 'false'}},'top'] //,
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

function stringify_list (obj) {
	s = "" ;
	for (n in obj) {
		if (s.length > 0) s += "," ;
		s += "\"" + obj[n].replace(/\\/g,'\\\\').replace(/\"/g,'\\"') + "\"" ;
	}
	//alert (s);
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
		//if (cols[i].search) p += "s" ; 
		//if (cols[i].editable) p += "e" ; 
		//if (cols[i].viewable) p += "v" ; 
		if (p.length) p = ":" + p ;
		ret.push(cols[i].name+p)
	}
	return stringify_list(ret)
}

var timeoutHnd;
function gridReload(){
	var grid = $("#grid-list");
    grid.trigger("reloadGrid");
}

function quickSearch(ev){
	if(timeoutHnd)
		clearTimeout(timeoutHnd)
	timeoutHnd = setTimeout(gridReload,500)
}

function prepare_pivoturl () {
	var alink = $("#pivoturl_link") ;
	var grid = $("#grid-list");
	var postdata = grid.jqGrid('getGridParam','postData') ;
	var pv = []; //(postdata.pivotcmds)? eval("(" + "{{!pageoptions}}" + ")") : [] ;
	var pvstr = "{{!_urltag}}" ;
	var isnew = false ;

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
	alink.html("") ;
	if (pv.length>0) {
		for (x in pv) {
			//opv =(pv[x]) ;
			pv[x] = pv[x].replace(/~[/]/g,"/").replace(/~~/g,"~").replace(/~/g,"~~").replace(/[/]/g,"~/") ;
			//alert (sep+"\n"+opv +"\n" + pv[x]) ;
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
		//alert (escape(pvstr));
		subpage = "{{!urlsubpage}}".replace('subpage/','') ;
		if (subpage) subpage = "/" + subpage
		alink.html("<a href='"+("/{{!suburl}}"+subpage+"//"+pvstr)+"'>pivot-url</a>") ;
	}
	//alert ($.param(postdata));
}

var postData_cols = ''
function beforeRequest () {
	var grid = $("#grid-list");
    var postdata = grid.jqGrid('getGridParam','postData') ;
	
	if (!postData_cols) {
		postData_cols = getColModel() ;
		//alert ('{{ajax_fields}}'+'\n'+postData_cols) ;
	}
	if (postData_cols != '{{ajax_fields}}') {
		postdata._cols = postData_cols ;
	} else delete postdata._cols ;
	
	if ($("#qsearch").val()) {
		postdata.qsearch =  $("#qsearch").val() ;
	} else {
		delete postdata.qsearch ;
	}
	grid.jqGrid('setGridParam',{'postData':postdata})
	prepare_pivoturl() ;
	return true;
}

function edit_autocomplete (elem,tax,len,scope,gridfilter) {
	var url = "/{{suburl}}/ajax/taxonomy/"+tax;
    $(elem).autocomplete ({
        'source': url
        ,'minLength':len
        });

    if (len==0) {
        $(elem).click(function () {if (!$(this).val()) $(this).autocomplete("search","");});
        }
	//if (typeof(scope) == "string") {
		$(elem).bind( "autocompletesearch", function(event, ui) {
			var grid = $("#grid-list");
			var qry = {} ;
			var u = url
			if (scope && $('#'+scope).val()) qry[scope] = $('#'+scope).val() ;
			if (gridfilter) {
				var postdata = grid.jqGrid('getGridParam','postData') ;
				for (k in postdata) {
					if (k == "pivotcmds" || k == "qsearch" || k=="_cols") {
						if (postdata[k]) {
							qry[k] = postdata[k];
							//alert (k + "=" + qry[k]);
							}
						}
				}
				if (postdata['_search']) {
					k = 'filters'
					if (postdata[k]) qry[k] = postdata[k];
					}
				}
			q = $.param(qry);
			//alert ("param---> " + q) ;
			if (q)
				u += "?"+q
			
			$(this).autocomplete( "option", "source",u);
			return true;
			});
	//	}
}
function toolbar_autocomplete (elem,tax,len) {
    edit_autocomplete(elem,tax,len,'',true);
    $(elem).bind( "autocompletechange", function(event, ui) {$("#grid-list")[0].triggerToolbar();});
}
function showform_colspan (form) {
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
        }
    );
}
$(document).ready(function() {
    $("#grid-list")
	.jqGrid(gridOption)
    .jqGrid('navGrid','#grid-pager'
		,{
			'edit':{{'true' if 'e' in _able else 'false'}},
			'add': {{'true' if 'a' in _able else 'false'}},
			'del': {{'true' if 'd' in _able else 'false'}},
			'search': false, // alternate use filter toolbar below
			'view': {{'true' if 'v' in _able else 'false'}}
			,'beforeRefresh' : function () {
				$("#grid-list")
					.setGridHeight({{_height}})
					.setGridWidth({{_width}})
					;
				$(".ui-jqgrid")
					.css({
						'height': ($(".ui-jqgrid-view").height() + $(".ui-jqgrid-pager").height()) + "px",
						'width': $(".ui-jqgrid-view").width() + "px"
						});
				}
			}
		,{/*edit*/'modal':true, 'width':600, 'labelswidth':'10%', 'closeAfterEdit': true
			,'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}
			,"beforeShowForm" : showform_colspan
			}
		,{/*add*/'modal':true, 'width':600, 'labelswidth':'10%'
			,'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}
			,"beforeShowForm" : showform_colspan
			}
		,{/*del*/'afterSubmit': function(response, postdata) { return $.parseJSON(response.responseText);}}
		,{/*search*/}
		,{/*view*/'modal':true, 'width':'750', 'labelswidth':'10%'
			,"beforeShowForm" : showform_colspan
			}
		)
    .jqGrid('gridResize',{'minWidth':350,'handles':'se'})
    .jqGrid('filterToolbar', {'stringResult': true, 'searchOnEnter': false,'defaultSearch': 'cn'})
    //.jqGrid('filterToolbar',{stringResult: true,searchOnEnter : true})
%if 's' in _able :
    .navButtonAdd('#grid-pager',{
       'caption':"", 
       'title':"toggle toolbar search",
       'buttonicon':"ui-icon-search", 
       'onClickButton': function(){ $("#grid-list")[0].toggleToolbar();}, 
       'position':"last" //,
    })
%end #if	
    ; 
    $('#t_grid-list').append('\
		<table cellspacing="0" cellpadding="0" border="0" style="height:100%;float:left;padding-left:2px;"><tbody><tr>\n\
		<td style="display:none;padding-left:2px;padding-right:2px;"><span id="pivoturl_btn"></span></td>\n\
		</tr></tbody></table>\n\
		<table cellspacing="0" cellpadding="0" border="0" style="height:100%;float:right;padding-right:2px;"><tbody><tr>\n\
		<td style="padding-left:2px;padding-right:2px;">\n\
		<span id="pivoturl_link" style="padding-left:4px;padding-right:4px;"></span>\n\
		</td>\n\
		<td style="padding-left:2px;padding-right:2px;">\n\
		<input id="qsearch" title="quick search" placeholder="quick search" style="height:1em;" onkeydown="quickSearch(arguments[0]||event);"/>\n\
		</td>\n\
		<td id="tbsearch_block" style="padding-left:2px;padding-right:2px;"></td>\n\
		</tr></tbody></table>\n\
		');
%if 's' in _able :
	$("#tbsearch_block").html('<span id="tbsearch_btn"></span>')
    $("#tbsearch_btn")
		.button ({
			'text': false,
			'icons': {'primary': "ui-icon-search"}
			})
		.click (function () { $("#grid-list")[0].toggleToolbar();})
		.attr('title',"toggle toolbar search")
		;
%end #if
%if not _tbsrch :
    $("#grid-list")[0].toggleToolbar();
%end
}); // end document ready process

</script>

