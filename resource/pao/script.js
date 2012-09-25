//Print ข้อมูลประวัติการยืม
$.fn.printTakenHistory = function(data) {

	//ฟังก์ชั่น addCommas สำหรับคั่น comma เลขหลักพันขึ้นไป
	function addCommas(nStr)
	{
		nStr += '';
		x = nStr.split('.');
		x1 = x[0];
		x2 = x.length > 1 ? '.' + x[1] : '';
		var rgx = /(\d+)(\d{3})/;
		while (rgx.test(x1)) {
			x1 = x1.replace(rgx, '$1' + ',' + '$2');
		}
		return x1 + x2;
	}
	
	$(this).empty();
	var has_taken_history = false;
	var history = '';
	count = 1;	//For print report count
	for(i=1;i<data.length;i++) {
		if(data[i].printRow == true) {
			//Processing Taken History Here
			history += '<span class="bold underline">ครั้งที่ '+ count + '</span><br/>';
			if(data[i][2] != null) {
				history += '<span class="bold take">สินค้ายืมโดย</span> ' + data[i][2] + 
				((data[i][4] != null) ? ' <span class="bold">วันที่</span> ' + data[i][4] : ' <span class="bold red">ไม่ระบุวันที่</span>') +
				((data[i][3] != null) ? ' <span class="bold">ราคายืม</span> ' + addCommas(data[i][3]) : ' <span class="bold red">ไม่ระบุราคายืม</span>') +'<br/>';
			} else {
				history += '<span class="bold recieve">รับคืนสินค้ามาที่</span> ' + data[i][6] + ' <span class="bold">วันที่</span> '+ data[i][5] +'<br/>';
			}
			count++;
			has_taken_history = true;
		}
	}
	
	if(data[0].printRow == true)
	{
		history += '<span class="bold underline">ครั้งที่ '+ count + '</span><br/>';
		if(data[0][2] != null) {
				history += '<span class="bold take">สินค้ายืมโดย</span> ' + data[0][2] +
				((data[0][4] != null) ? ' <span class="bold">วันที่</span> ' + data[0][4] : ' <span class="bold red">ไม่ระบุวันที่</span>') +
				((data[0][3] != null) ? ' <span class="bold">ราคายืม</span> ' + addCommas(data[0][3]) : ' <span class="bold red">ไม่ระบุราคายืม</span>') +'<br/>';
			} else {
				history += '<span class="bold recieve">รับคืนสินค้ามาที่</span> ' + data[0][6] + ' <span class="bold">วันที่</span> '+ data[0][5] +'<br/>';
			}
		count++;
		has_taken_history = true;
	}
	
	if(has_taken_history == false) {
		$(this).append('ไม่มีประวัติการยืม');	
	}
	else {
		$(this).append(history);
	}
}
//ฟังก์ชัน distinct สำหรับกรองข้อมูลอาร์เรย์ที่ซ้ำกัน
$.extend({
    distinct : function(anArray) {
       var result = [];
       $.each(anArray, function(i,v){
           if ($.inArray(v, result) == -1) result.push(v);
       });
       return result;
    }
});

/* Convert JSON data object To 2 Dimension Array */
function objectToArray (data) {
	var rows = data.rows;
	var dataArray = [];
	for(i=0;i<rows.length;i++) {
		dataArray[i] = rows[i].cell;
	}
	return dataArray;
}

//Filter Only Taker Row
function FilterOnlyTakerRow(data) {
	//1. Last Row Fetch
	for(i=0;i<data.length;i++) {
		if(i == 0) {
			if(data[i][2] == data[data.length -1][2]) {
				data[i].printRow = true;
			}
		}
		else if(i != data.length -1 ) {
			if(data[i][2] == data[i+1][2]) {
				data[i].printRow = false;
			}
		} else { 
			if(data[i][2] == data[0][2]) {
				data[i].printRow = false;
			}
		}
	}
	
	//2. Check NULL on First data
	var all_is_null = true;
	for(i=1;i<data.length;i++) {
		if(data[i][2] == null){
			data[i].printRow = false;
		} else {
			all_is_null = false;
			break;
		}
	}
	if(data[0][2] == null && all_is_null == true) {
		data[0].printRow = false;
	}
	return data;
}

//Main Jquery Function of the page
$(document).ready(function(){

	function selectingProduct() {
		
		var type = $('input:radio[name=radio_type]:checked').val();
		var product_code;
		if(type=='type_1'){
			product_code = $("#text_product").val().toUpperCase();
			if(product_code == ""){
				alert("โปรดกรอกรหัสสินค้าด้วยก่อนกดปุ่ม submit");
				return false;
			}
		} else {
			product_code = $("#select_product").val();
		}
		var url = '/npd/ajax/jqgrid?rows=100&_cols=["code","rev_id","taker","taker_price","take_date","keep_date","keeper"]&_history=history&pivotcmds=@f-code-'+product_code;
		$.getJSON(url,function(data){
			if(data.total==0) {
				$("#taken_history").text('ประวัติการยืม : '+product_code);
				$("#result_taken_history").empty();
				$("#result_taken_history").append('ไม่พบรหัสสินค้าที่ระบุ');
			} else {
				var dataArray = objectToArray (data);
				var header = ["Revision","ที่ยืม","ราคายืม","วันที่ยืม","วันที่เก็บ","ที่เก็บ"];
				for(i=0;i<dataArray.length;i++) {
					dataArray[i].printRow = true;
				}
				
				dataArray = FilterOnlyTakerRow(dataArray);
				//$("#result_table").printTable(dataArray,header);
				
				$("#taken_history").text('ประวัติการยืม : '+product_code);
				$("#result_taken_history").printTakenHistory(dataArray);
				
				$("#result_table table tr.hide").hide();
				$("#toggle_full_table").toggle(function(){
					$("#result_table table tr.hide").show();
				},
				function() {
					$("#result_table table tr.hide").hide();
				});
			}
		});
	}
	
	function selectingCategory() {
		$("#select_product").attr("disabled","disabled");
		$("#select_product").empty();
		$("#select_product").append('<option>Now Loading ...</option>');
		
		var mycode = $("#select_category").val();
		
		var url;
		if($('#chk_has_taken').attr('checked')=="checked") {
			if(mycode == 'all') {
				url = '/npd/ajax/jqgrid?rows=10000&_cols=["code"]&pivotcmds=["@f-taker"]';
			} else {
				url = '/npd/ajax/jqgrid?rows=10000&_cols=["code"]&pivotcmds=["@f-acat-' + mycode + '","@f-taker"]';
			}
		} else {
			if(mycode == 'all') {
				url = '/npd/ajax/jqgrid?rows=10000&_cols=["code"]&pivotcmds=[]';
			} else {
				url = '/npd/ajax/jqgrid?rows=10000&_cols=["code"]&pivotcmds=["@f-acat-' + mycode + '"]';
			}
		}
		$.getJSON(url,function(data){
			//var rows = data.rows;
			$("#select_product").removeAttr("disabled");
			$("#select_product").empty();
			
			//ดึงข้อมูลรหัสสินค้าออกจาก json ที่มาจาก server
			var rows = [];
			for(i=0;i<data.rows.length;i++) {
				rows[i] = data.rows[i].cell[0];
			}
			rows = $.distinct(rows);	//ทำให้รหัสสินค้าไม่ซ้ำ
			//วนลูปรหัสสินค้าทั้งหมด (ไม่เอาตัวแรก เพราะตัวแรกคือ 0)
			for(i=1;i<rows.length;i++) {
				 $("#select_product").append('<option value="'+ rows[i] +'">'+ rows[i] +'</option>');
			}
		});
	}
	
	$("#select_category").change(selectingCategory);
	$('#chk_has_taken').change(selectingCategory);
	$("#select_product").change(selectingProduct);
	
	$("#submit_product").click(selectingProduct);
	
	$('input:radio[name=radio_type]').change(function(){
		var type = $('input:radio[name=radio_type]:checked').val();
		if(type=='type_1'){
			$("#text_product").removeAttr("disabled");
			$("#submit_product").removeAttr("disabled");
			
			$("#select_category").attr("disabled","disabled");
			$("#select_product").attr("disabled","disabled");
			$("#chk_has_taken").attr("disabled","disabled");
		} else {	//type_2
			$("#text_product").attr("disabled","disabled");
			$("#submit_product").attr("disabled","disabled");
			
			$("#chk_has_taken").removeAttr("disabled");
			$("#select_category").append('<option>Now Loading ...</option>');
			function getlist () {
				$.getJSON('/npd/ajax/taxonomy/acat',function(data) {
					$("#select_category").removeAttr("disabled");
					$("#select_category").empty();
					$.each(data, function(key, val) {
						$("#select_category").append('<option value="'+ val +'">'+ val +'</option>');
						if (val.search(/^(\|\|...waiting)/) == 0) {		//ถ้าขึ้นต้นด้วย ||...waiting เป็นจริง จะ return 0
							getlist(); // <---- recursive
							return ;
						}
					});
					$("#select_category").append('<option value="all">-- แสดงสินค้าทุกชนิด --</option>');
				});
			}
			getlist();
		}
	});
	
	$("#select_category").attr("disabled","disabled");
	$("#select_product").attr("disabled","disabled");
	$("#chk_has_taken").attr("disabled","disabled");
});
