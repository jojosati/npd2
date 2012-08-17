<!doctype html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
%include helper/head-jquery-ui _vars=_vars
%include helper/head-title _vars=_vars
</head>
<body>
<script type="text/javascript">
$(document).ready(function() {
	var $frame = $('.frame-dynamic').first() ;
	if (!$frame.css('margin')) {
		$frame.css('margin','0 auto'); //'margin-left':'auto','margin-right':'auto';
	}
});
</script>
<table class="ui-widget frame-dynamic"><tr><td>
%include
</td></tr></table>
</body>

</html>
%if not _vars.get('layout_loaded'): _vars['layout_loaded']='dynamic'

