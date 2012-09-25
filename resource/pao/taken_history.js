// Use Name space taken_history
// By using jQuery plugin

$.takenHistory = {
  	 objectToArrayFunction : function(data) {
		var rows = data.rows;
		var dataArray = [];
		for(i=0;i<rows.length;i++) {
			dataArray[i] = rows[i].cell;
		}
		return dataArray;
	},
	
	FilterOnlyTakerRowFunction : function(data) {
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
	},
	
	//Print ข้อมูลประวัติการยืม
	printTakenHistoryFunction : function(data) {
	
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
		
		
		var result = '';
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
			result += 'ไม่มีประวัติการยืม';
		}
		else {
			result += history;
		}
		return result;
	},
	
	getArrayFromToTaken : function(data) {
		var new_data = [];
		var row = new Array();
		for(i=1;i<data.length;i++) {
			if(data[i].printRow == true) {

				if(data[i][2] != null) {			
					row.push(data[i][2]);
					row.push(data[i][4]);
					row.push(data[i][3]);
				} else {
					row.push(data[i][5]);
					
					var temp = row[3];
					row[3] = row[2];
					row[2] = temp;
					
					new_data.push(row);
					row = new Array();
				}
			}
		}
		
		if(data[0].printRow == true)
		{
			if(data[0][2] == null) {
				row.push(data[0][5]);
						
				var temp = row[3];
				row[3] = row[2];
				row[2] = temp;
				
				new_data.push(row);
				row = new Array();
			}
			else
			{
				row.push(data[0][2]);
				row.push(data[0][4]);
				row.push(null);
				row.push(null);
				new_data.push(row);
				row = new Array();
			}
		}
		return new_data;
	},
	
	//Print ข้อมูลประวัติการยืม
	printTakenHistoryFromToFunction : function(data) {
	
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

		var result = '';

		if(data.length != 0)
		{
			for(i=0;i<data.length;i++) {
				result += '<span class="bold take">ยืมครั้งที่ ' + (i+1)+ ' โดย</span> ' + data[i][0];
				
				if(data[i][1] != null) {
					result += ' <strong>ตั้งแต่วันที่</strong> ' + data[i][1] 
				} else {
					result += ' <strong>ไม่ระบุวันที่ยืม</strong> ';
				}
				
				if(data[i][2] != null) {
					result += ' ถึง ' + data[i][2];
				} else {
					result += ' ถึงปัจจุบัน';
				}
				
				
				if(data[i][1] != null) {
					var fromDate;
					var toDate;
					
					result += ' <strong>เป็นระยะเวลาทั้งหมด</strong> ' ;
					
					var str = data[i][1].split("/");
					fromDate = new Date(str[2],str[1]-1,str[0]);
					
					if(data[i][2] == null) {
						toDate = new Date();
					} else {
						str = data[i][2].split("/");
						toDate = new Date(str[2],str[1]-1,str[0]);
					}
					
					var one_day=1000*60*60*24;

					//Calculate difference btw the two dates, and convert to days
					var days = Math.ceil((toDate.getTime()-fromDate.getTime())/(one_day));
					
					result += days;
					result += ' วัน';
				}
				
				result += ' <strong>ราคายืม</strong> ';
				if(data[i][3] != null) {
					result += addCommas(data[i][3]);
				} else {
					result += 'ไม่ระบุ';
				}
				result += '<br/>';
			}
		}
		else
		{
			result += "ไม่มีประวัติการยืม";
		}
		return result;
	},
	
	getTakenHistoryFromToObject : function(data) {
		var result = new Object();
		
		if(data.length != 0)
		{
			
			var history = new Array();
			history.count = data.length;
			for(i=0;i<data.length;i++) {
			
				var myarray = new Object();
				myarray.no = i+1;
				myarray.by = data[i][0];
				myarray.from = data[i][1];
				myarray.to = data[i][2];
				
				if(data[i][1] != null) {
					var fromDate;
					var toDate;
					
					var str = data[i][1].split("/");
					fromDate = new Date(str[2],str[1]-1,str[0]);
					
					if(data[i][2] == null) {
						toDate = new Date();
					} else {
						str = data[i][2].split("/");
						toDate = new Date(str[2],str[1]-1,str[0]);
					}
					
					var one_day=1000*60*60*24;

					//Calculate difference btw the two dates, and convert to days
					var days = Math.ceil((toDate.getTime()-fromDate.getTime())/(one_day));
					
					myarray.days = days;

				} else {
					myarray.days = -1;
				}
				
				myarray.price = data[i][3];
				
				history.push(myarray);
			}
			
			result.data = history;
		}
		else
		{
			result.data = 0;
		}
		
		return result;
	},
	
	getTakenHistoryObject : function(data) {
		var result = new Object();
		var has_taken_history = false;
		var history = new Array();
		count = 1;	//For print report count
		var myarray = new Object();
		for(i=1;i<data.length;i++) {
			if(data[i].printRow == true) {
				var myarray = new Object();
				myarray.count = count;
				if(data[i][2] != null) {
					myarray.state = 'take';
					myarray.take_by = data[i][2];
					myarray.date = data[i][4];
					myarray.price = data[i][3];
				} else {
					myarray.state = 'recieve';
					myarray.takeplace = data[i][6];
					myarray.date = data[i][5];
				}
				count++;
				has_taken_history = true;
				
				history.push(myarray);
			}
		}
		
		if(data[0].printRow == true)
		{
			var myarray = new Object();
			myarray.count = count;
			if(data[0][2] != null) {
					myarray.state = 'take';
					myarray.take_by = data[0][2];
					myarray.date = data[0][4];
					myarray.price = data[0][3];
				} else {
					myarray.state = 'recieve';
					myarray.takeplace = data[0][6];
					myarray.date = data[0][5];
				}
			count++;
			has_taken_history = true;
			
			history.push(myarray);
		}
		
		if(has_taken_history == false) {
			result.data = 0;
		}
		else {
			result.data = history;
		}
		
		return result;
	},
	
	/*
		function getTakenHistory(product_code,print_html)
		ใส่พารามิเตอร์ 2 ตัวครับ 
		product_code คือ รหัสสินค้าที่ต้องการ
		print_html คือ ระบุว่าจะปริ้นท์ออกมาเป็น html หรือไม่ ถ้าใส่ true จะปริ้นท์เป็น html ถ้า ใส่ false จะ print เป็น object ดังตัวอย่าง (ค่า default คือ true)
	*/
	getTakenHistory : function(product_code,print_html,custom_url) {
	
		//Set default print_html parameter value.
		if(print_html == undefined){
			print_html = true;
		}
		
		if(product_code == '' && print_html == true){
			return '';
		} else if(product_code == '' && print_html == false){
			return null;
		}
		
		product_code = product_code.toUpperCase();
		
		if(custom_url == undefined)
		{
			var url = '/npd/ajax/jqgrid?rows=100&_cols=["code","rev_id","taker","taker_price","take_date","keep_date","keeper"]&_history=history&pivotcmds=@f-code-'+product_code;
		}
		else
		{
			var url = custom_url+'?rows=100&_cols=["code","rev_id","taker","taker_price","take_date","keep_date","keeper"]&_history=history&pivotcmds=@f-code-'+product_code;
		}
		if(print_html == true) {
			var result = '';
		} else {
			var result = new Object();
		}
		$.ajax({
		  url: url,
		  dataType: 'json',
		  async: false,
		  success: function(data) {
			if(data.total==0) {
				if(print_html == true) {
					result += '<h3>ประวัติการยืม : '+product_code+'</h3>';
					result += '<div id="result_taken_history">ไม่พบรหัสสินค้าที่ระบุ</div>';
				} else {
					result.product_code = product_code;
					result.data = 0;
				}
			} else {
				var dataArray = $.takenHistory.objectToArrayFunction (data);
				
				for(i=0;i<dataArray.length;i++) {
					dataArray[i].printRow = true;
				}
				
				dataArray = $.takenHistory.FilterOnlyTakerRowFunction(dataArray);
				
				dataArray = $.takenHistory.getArrayFromToTaken(dataArray);
				
				if(print_html == true){
					result += '<h3>ประวัติการยืม : '+product_code+'</h3>';
					result += $.takenHistory.printTakenHistoryFromToFunction(dataArray);
				} else {
					result = $.takenHistory.getTakenHistoryFromToObject(dataArray);
					result.product_code = product_code;
				}
			}
		  }
		});
		return result;
	}
};

