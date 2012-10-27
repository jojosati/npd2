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
