%if not _vars.get('layout_loaded'): globals()['_rebase']=('helper/layout-dynamic',{'_vars':_vars})
%suburl = _vars['suburl']

<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
<div id="sample6-container"></div>

<script type="text/javascript" src="/{{suburl}}/resource/js/jquery.cycle.lite.js"></script>
<script type="text/javascript">
var $qsearch = $('<input>',{style:'margin:1em;'}) ;
var $products = $('<table>');
var $result = $('<span>',{style:'margin:1em;'});

$('#sample6-container')
.append($('<span>',{html:'Search:',style:'margin-left:1em;'}))
.append($qsearch)
.append($result)
.append($products)
;

$qsearch
.change(function(){reload($(this).val());})
.change()
;

function reload (qsearch) {
	$products.empty();
	$result.html('Loading...');
	// --- json get list of cover pics
	$.getJSON('/{{suburl}}/ajax/taxonomy/$pic?term=w1*&_cols=acat,detail,keeper,target_price&qsearch='+qsearch, function(pics) {
		$result.html('found ' + pics.length+' item(s).');
		
		for (var pic in pics) {
			pic = pics[pic].split('||');
			var code = pic[1];
			pic = pic[0];
			
			var $item = $('<tr>',{id:code,title:code}).appendTo($products);
			var $itempic = $('<div>',{'class':'ui-widget-content',style:'margin:4px;'}).appendTo($('<td>').appendTo($item));
			pic = pic.split(';');
			for (var p in pic){
				p = pic[p] ;
				$('<img>',{src:'/{{suburl}}/media/'+p,style:'width:100px;height:100px;margin:4px;'})
				.appendTo($itempic);
			}
			if (pic.length>2) {
				$($itempic).cycle({width:108,height:108});

			}
			var $itemdesc = $('<div>').appendTo($('<td>').appendTo($item));
			var params = {pivotcmds:'["@f-code-'+code+'"]',_cols:'["acat","detail","keeper","target_price"]'} ;
			var $pinf = $('<div>',{'class':'ui-widget-content',style:'width:100%;padding:0.5em;'})
				.append($('<div>',{'class':'ui-widget-header',style:'padding-left:0.5em;'}).html(code))
				.appendTo($itemdesc);
			function showdesc($container) {
				return function (data) {
					for (var r in data.rows) {
						r = data.rows[r];
						for (var c in r.cell) {
							if (r.cell[c])
								$container.append($('<div>',{style:'padding-left:0.5em;'}).html(r.cell[c]));
							}
						}
					} ;
				}
			$.getJSON('/{{suburl}}/ajax/jqgrid?'+$.param(params), showdesc($pinf));
			/* 
			//following code not work, cause $pinf has been changed before complete event
			$.getJSON('/{{suburl}}/ajax/jqgrid?'+$.param(params), function(data) {
					for (var r in data.rows) {
						r = data.rows[r];
						for (var c in r.cell) {
							if (r.cell[c])
								$pinf.append($('<div>',{style:'padding-left:0.5em;'}).html(r.cell[c]));
							}
						}
					} ;
				});
			*/
		}
	});
}
$(document).ready(function() {
	reload () ;
});
</script>