%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%suburl = _vars['suburl']
<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
<div id="sample5-container"></div>
<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.cycle.lite.js"></script>
<script type="text/javascript">
$(document).ready(function() {
	var $container = $('#sample5-container');
	var $select = $('<select/>', {'class': 'ui-widget-content'})
		.change(function(){slide_show($(this).val())})
		.appendTo($container) ;
	var $pic = $('<div>');
	var $detail = $('<div>');
	var $info = $('<div>')
		.append($('<table>')
			.append($('<tr>')
				.append($('<td>',{style:'vertical-align:top;padding:1em;'}).append($pic))
				.append($('<td>',{style:'vertical-align:top;padding:1em;'}).append($detail))
				))
		.appendTo($container) ;
		;
	var $slide = $('<div>').appendTo($pic) ;
	function slide_show(code) {
		$info.hide();
		if ($('img',$slide).length>1) {
			$slide.cycle('destroy');
		}
		$slide.empty();
		$detail.empty();
		$.getJSON('/{{suburl}}/ajax/media/'+code, function(pics) {
			var dsp='block';
			for (var i in pics) {
				$('<img>',{src:'/{{suburl}}/media/'+pics[i],style:'padding:0.5em;','class':'ui-widget-content'})
				.css('display',dsp)
				.appendTo($slide)
				;
				if (i==0) {
					var params = {pivotcmds:'["@f-code-'+code+'"]',_cols:'["acat","detail","keeper","target_price"]'} ;
					var $pinf = $('<div>',{'class':'ui-widget-content',style:'width:100%;padding:0.5em;'})
						.append($('<div>',{'class':'ui-widget-header',style:'padding-left:0.5em;'}).html(pics[i].split('.').shift()))
						.appendTo($detail);
					$.getJSON('/{{suburl}}/ajax/jqgrid?'+$.param(params), function(data) {
						for (var r in data.rows) {
							r = data.rows[r];
							for (var c in r.cell) {
								if (r.cell[c])
									$pinf.append($('<div>',{style:'padding-left:0.5em;'}).html(r.cell[c]));
								}
							}
						});
				
					$detail.append($('<div>').html('<hr> '+pics.length+' picture(s):'));
				}
				$detail.append($('<div>').html(pics[i]));
				dsp = 'none';
			}
			if (pics.length>1) {
				$slide.cycle({
					fit:true
					,width:'250px'
					,height:'250px'
					});
				}
			$info.show({effect:'slide',speed:'slow'});
		});
	}
	// --- json get list of cover pics
	$.getJSON('/{{suburl}}/ajax/media/*.jpg', function(pics) {
		var items=[];
		for (var i in pics) {
			var code = pics[i].split('.',2).shift()
			items.push('<option value="' + code + '">' + code  + '</option>');
			if (i==0) $select.val(code);
		}
		$select.html(items.join(''));
		$select.change();
	});
});
</script>