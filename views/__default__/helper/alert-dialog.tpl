
%include helper/language _vars=_vars
%_require_vars=[]
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_option_vars=['alert_msg','language','_m','_msg']
%[locals().update({k:_vars.get(k)}) for k in _option_vars]

%if alert_msg :
%_msg['alert_message'] = _msg.get('alert_msg') or 'Alert message//th:ข้อความเตือน'
%_msg['OK'] = _msg.get('OK') or 'OK//th:ตกลง'

%alert_msg = '<br/>\n'.join(['<span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>'+_escape(m) for m in alert_msg])
<script type="text/javascript">
//alert ('{{language}}\n'+'{{!alert_msg}}');
$(document).ready(function() {
	var $dlg = $('<div>',{title:"{{_m('alert_message')}}"}) ;
	
	$dlg
	.append($('<p>',{'class':'ui-state-error-text'}).html('{{!alert_msg}}'))
	.dialog({zIndex:2000,modal:false, dialogClass:"ui-state-error", close:function(){$(this).remove();}, buttons: { "{{_m('OK')}}": function() { $dlg.dialog("close");}}})
	;
});
</script>
%end