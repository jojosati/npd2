%if '_plugin_' not in _vars: _vars['_plugin_'] = []
%if 'user-login' not in _vars['_plugin_'] :
%_vars['_plugin_'].append('user-login')
%include helper/language _vars=_vars
%_require_vars=['suburl']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_option_vars=['user','logged_in','user_role','language','_m','_msg']
%[locals().update({k:_vars.get(k)}) for k in _option_vars]

<script type="text/javascript" src="/{{suburl}}/resource/js/user-login.js"></script>
<script type="text/javascript">
if (typeof login_tag=='undefined') {
login_tag = function (container) {
	$login = new user_login({
			language : '{{language or "en"}}'
			,user : '{{user}}'
			,logged_in : {{logged_in or 0}}
			,user_role: '{{user_role or ""}}'
			});
	$tag = $login.loginDOM();
	if (container) $tag.appendTo(container);
	return $tag;
}}
</script>
%end