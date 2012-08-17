%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg','urlpagetag']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%if urlpagetag : urlpagetag = '/'+urlpagetag
<div id='grid-tabs-container'></div>
<script type="text/javascript">
var pages=[
	'/{{suburl}}/~subpage/grid/=_able-gqv{{!urlpagetag}}|{{_m("grid//th:ตารางข้อมูล")}}'
	,'/{{suburl}}/~subpage/newstk/=_able-gqv{{!urlpagetag}}|{{_m("new items//th:สินค้าล่าสุด")}}'
	,'/{{suburl}}/~subpage/oldstk/=_able-gqv{{!urlpagetag}}|{{_m("old items//th:สินค้าเดิม")}}'
	,'/{{suburl}}/~subpage/sellable/=_able-gqv{{!urlpagetag}}|{{_m("sellable//th:พร้อมขาย")}}'
	,'/{{suburl}}/~subpage/taken/=_able-gqv{{!urlpagetag}}|{{_m("taken//th:ถูกยืม")}}'
	,'/{{suburl}}/~subpage/sold/=_able-gqv{{!urlpagetag}}|{{_m("sold//th:ขายไปแล้ว")}}'
	];
$(document).ready(function() {
	$tabnav = $('<ul>') ;
	for (var i in pages){
		var url = pages[i].split('|',2).shift();
		var lbl = pages[i].split('|',2)[1] || url ;
		if (url=='') continue;
		$('<li>')
		.append($('<a>',{href:url,html:lbl}))
		.appendTo($tabnav)
		;
	}
	$tabs = $('<div>').append($tabnav).appendTo('#grid-tabs-container').tabs();
})
</script>