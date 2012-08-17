   $.fn.multicheckbox = function(settings) {
     var config = {mixed: '', checkedValue: 'true', uncheckedValue: 'false', mixedValue: 'mixed'};
 
     if (settings) $.extend(config, settings);
 
     this.each(function() {
                 $(this).css("cursor", "pointer");
                 if (typeof $(this).attr('value')!='string'){
                      var v = config.uncheckedValue;
	        if($(this).is(':checked')) v = config.checkedValue;
                      $(this).attr('value',v);
                 }
                 if (settings){
                    if (config.mixed) $(this).attr('value',config.mixed);
                 }

                 if ($(this).attr('value')==config.uncheckedValue) 
                        $(this).attr('checked','');
                 else $(this).attr('checked','checked');

                 if ($(this).attr('value')!=config.uncheckedValue && $(this).attr('value')!=config.checkedValue)
                       $(this).fadeTo(1, .3);
	   else $(this).fadeTo(1,1);

             
	   $(this).click(function(){
                       var v = config.uncheckedValue ;
                       if ($(this).attr('value')==config.uncheckedValue) v = config.checkedValue ;
                       $(this).fadeTo(1,1);
                       $(this).attr('value',v);

	   });
     });
 
     return this;
	}
 