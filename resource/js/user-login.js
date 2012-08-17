if (typeof user_login=='undefined'){
user_login = function (options){
	var messages = {
		User_login: '//th:ลงชื่อผู้ใช้'
		,User_name: '//th:ชื่อผู้ใช้'
		,User_password: '//th:รหัสผ่าน'
		,Login: '//th:ลงชื่อ'
		,Logout: '//th:ถอนชื่อ'
		,Invalid_user_name: '//th:ไม่มีชื่อผู้ใช้'
		} ;
	this.loginDOM = loginDOM;
	this.loginDialog = loginDialog;
	// --------------------------------
	// service function select best message depend on language
	function _(m,lang,ms){
		// optional: options.language, options.messages
		// 1. lookup from messages table
		// 2. extract with language selector example: "english//th:xxx"
		if (!m) return m;
		if (m.indexOf('//')<0 && m.indexOf(' ')<0) {
			// lookup from messages table
			if (!ms || ms[m] == undefined) ms = options.messages;
			if (!ms || ms[m] == undefined) ms = messages;
			if (!ms || ms[m] == undefined) {return m.replace(/_/g,' ');}
			var tm = _(messages[m]+'//'); // recursive for lang selector
			if (!tm) return m.replace(/_/g,' ');
			return tm ;
		}
		lang = lang || options.language || 'en' ;
		m = m.split('//'+lang+':',2).pop() ;
		return m.split('//',2).shift() ;
	}

	function loginDialog(){
		if (options.user && options.logged_in) return;

		var $frm = $('<form/>',{method:'post',title:_('User_login')});
		var $fld_name = $('<input/>',{
				name:'user'
				,placeholder:_('User_name')
				,title:_('User_name')
				,style:'width:8em;'}).val(options.user);
		var $fld_password = $('<input/>',{
				name:'password'
				,type:'password'
				,placeholder:_('User_password')
				,title:_('User_password')
				,style:'width:8em;'});
		$tbl = $('<table/>')
			.append($('<tr/>')
				.append('<td/>',{style:'padding-right:4px;text-align:right;',html:_('User_name')})
				.append($('<td/>').append($fld_name))
				)
			.append($('<tr/>')
				.append('<td/>',{style:'padding-right:4px;text-align:right;',html:_('User_password')})
				.append($('<td/>').append($fld_password))
				);
		$frm.append($tbl);
		$frm.append('<input name="action" type="hidden" value="login" />');
		$('input',$frm).keypress(function (e){
			if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
				$("button:first",$('.ui-dialog-buttonset',$frm.parent())).click();
				return false;
				}
			else return true;
			});
		$frm.dialog({
			zIndex: 2000,
			close : function () {	$(this).dialog( "destroy" ).remove();},
			modal:true,
			buttons:[
					{
					text : _('Login') 
					,'class' : 'ui-state-focus'
					,click :function (){
						if(!$fld_name.val()){alert(_("Invalid_user_name."));}
						else{
							$frm.submit() ;
							$frm.dialog( "close" );
							}
						}
					}]
			}) ;
	}
	function loginDOM(){
		if (options.user && options.logged_in){
			// already logged_in, show logout tag
			return  $('<span/>',{
				style:'padding-right:0.5em;padding-left:0.5em;'
				,title:options.user_role||''
				,html:options.user
				})
				.append($('<a/>',{
					href:'?action=logout'
					,style:'margin-right:0.2em;margin-left:0.2em;'
					,html:_('Logout')
					}).button()) ;
		}
		
		// not logged_in, show login tag
		return $('<span/>',{style:'margin-left:0.5em;margin-right:0.5em'})
			.button({label:_('Login')})
			.click(loginDialog);
	}
}}
