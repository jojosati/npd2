%if 'naked' in _vars.get('pageoptions',[]):
<div id="pageheader" style="padding-bottom:0.5em;">
<table style="width:100%;"><tr>
<td style="text-align:left;padding-left:1em;">
</td>
<td id="header_login_block" style="text-align:right;padding-right:0.5em;">
</td>
</tr></table>
</div>
%else:
%_require_vars=['suburl','urloptions','urlsubpage','sepoption','urltagstr']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_option_vars=[]
%[locals().update({k:_vars.get(k)}) for k in _option_vars]
%#--------------------------------------------------------
<div id="pageheader" style="padding-bottom:0.5em;">
<div id="pageheadcaption" class="ui-widget ui-widget-header ui-corner-top">
<span style="font-size:180%;letter-spacing:0.2em;margin-left:0.1em;">
<span style="color:#FF0000;text-shadow:gray 3px 3px 2px;">Net</span><span style="color:#0000CC;text-shadow:gray 3px 3px 2px;">Scraft</span>
</span>
<span style="color:red;margin-right:8pt;text-shadow:gray 3px 3px 2px;"><sup>{{_vars['_server_'].get('version','')}}</sup></span>
<span style="font-size:80%;font-weight:normal;"> your <b>scraft</b> is going to fly with you. </span>
</div>
<div id="pageheadnav" class="ui-widget ui-widget-content ui-corner-bottom">
<table style="width:100%;"><tr>
<td>
%_url = '/'+suburl
/<a href="{{!_url}}">{{suburl}}</a>
%if urlsubpage :
%if '/' in urlsubpage :
%for u in urlsubpage.split('/')[:-1] :
%_url += '/'+u
/<a href="{{!_url}}/">{{u}}</a>
%end
%u = urlsubpage.split('/')[-1]
%_url += '/'+u
/<a href="{{!_url}}">{{u}}</a>
%else: 
%_url += '/'+urlsubpage
/<a href="{{!_url}}">{{urlsubpage}}</a>
%end
%end #urlsubpage
%_urltag = ''
%for _o in urloptions :
%_uo = _o.replace('~','~~').replace('/','~/')
%if not _urltag :
%_urltag = _uo
{{!urltagstr}}
%else:
%_urltag += sepoption + _uo
{{sepoption}}
%end #if not 
<a href="{{!_url}}{{!urltagstr}}{{!_urltag}}">{{_o}}</a>
%end #for _o
</td>
<td></td>
<td id="header_login_block" style="text-align:right;padding-right:0.5em;">
</td>
</tr></table>
</div>
</div>
%end



