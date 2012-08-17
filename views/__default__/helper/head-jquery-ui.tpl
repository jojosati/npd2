%include helper/head-jquery _vars=_vars
%include helper/language _vars=_vars
%suburl = _vars['suburl']
%language = _vars['language']
%theme = _vars.get('kwoptions',{}).get('theme') or _vars.get('_server_',{}).get('theme') or 'ui-lightness' 
%scrollpane = False
%touchscroll = True
%touchpunch = True
<link type="text/css" href="/{{suburl}}/resource/themes/{{theme}}/jquery-ui.css" rel="Stylesheet">
%if scrollpane :
<link type="text/css" href="/{{suburl}}/resource/css/jquery.jscrollpane.css" rel="stylesheet" media="all" />
%end
%if language!='en':
<script type="text/javascript" src="/{{suburl}}/resource/js/i18n/jquery.ui.datepicker-{{language}}.js"></script>
%else:
<script type="text/javascript">	
$.datepicker.setDefaults({dateFormat:'dd/mm/yy'});
</script>
%end
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery-ui-1.8.15.custom.min.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.mousewheel.js"></script>
%if touchscroll :
<script type="text/javascript" src="/{{suburl}}/resource/js/touch-scroll.min.js"></script>
%end
%if touchpunch :
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.ui.touch-punch.min.js"></script>
%end
%if scrollpane :
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.jscrollpane.min.js"></script>
%end
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.ui.datepicker.strftime.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/json2.js"></script>
<script type="text/javascript" src="/{{suburl}}/resource/js/autoNumeric-1.7.5.js"></script>
<style type="text/css">
.ui-button-text-only .ui-button-text {padding: 0.1em 0.5em 0.1em 0.5em; line-height:90%;}
</style>
<script type="text/javascript">
	window.onbeforeunload = function(){ 
		var msg = '';
		$('.unload_warning')
		.each(function(){
				var m = $(this).text(); 
				if (m.length){
					if (msg.length) msg += ', ';
					msg += m ;
				}
			}) ;
		/*if ($('iframe')) {
			$('iframe').each(function(){
				$(this).contents().find('.unload_warning')
				.each(function(){
				var m = $(this).text(); 
					if (m.length){
						if (msg.length) msg += ', ';
						msg += m ;
					}
				});
			});
		}*/
		if (msg.length)
			return msg;
		} ;
</script>
