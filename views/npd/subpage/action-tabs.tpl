
%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%include helper/language _vars=_vars
%include helper/user-login _vars=_vars
%include helper/gridwrapper-options _vars=_vars
%_require_vars=['suburl','_m','_msg','urlpagetag']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%if urlpagetag : urlpagetag = '/'+urlpagetag

<div id='action-tabs-container'></div>
<script type="text/javascript">
var pages=[
	'/{{suburl}}/~subpage/grid|{{_m("grid//th:ตารางข้อมูล")}}'
%if _vars.get('logged_in') :
	,'/{{suburl}}/~subpage/taking|{{_m("taking//th:การยืม")}}'
	,'/{{suburl}}/~subpage/keeping|{{_m("keeping//th:เปลี่ยนที่เก็บ/รับคืน")}}'
	,'/{{suburl}}/~subpage/selling|{{_m("selling//th:การขาย")}}'
	,'/{{suburl}}/~subpage/buying|{{_m("buying//th:การซื้อ")}}'
%end
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
	$tabs = $('<div>');
	if (!$('.gridwrapperframe'))
		$tabs.addClass('gridwrapperframe').width($(window).width()*0.9);
	$tabs.append($tabnav).appendTo('#action-tabs-container').tabs({cache:true});
})
</script>