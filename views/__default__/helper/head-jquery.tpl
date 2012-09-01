%suburl = _vars['suburl']
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=9,8,7;FF=3;OtherUA=4">
<link type="text/css" href="/{{suburl}}/resource/css/base.css" rel="Stylesheet">
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery-1.7.2.min.js"></script>
<script type="text/javascript">
	$(window).on('beforeunload',function(){ 
		var msg = '';
		$('.unload_warning')
		.each(function(){
				var m = $(this).text(); 
				if (m.length){
					if (msg.length) msg += ', ';
					msg += m ;
				}
			}) ;
		if (msg.length)
			return msg;
	});
</script>
