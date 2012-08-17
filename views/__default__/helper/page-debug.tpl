
%if _vars.get('_server_',{}).get('debug') :
<!-- debug_dump -->
<div id="debug_btn" style="margin:.5em;"><b>debug</b></div>
<div id="debug_info" style="display:none;margin:.5em 0 .5em 0;">
%def _debugdata(_v) :
%if isinstance(_v,(list,tuple)) :
<b>[</b> {{!" <b>,</b> ".join([_escape(__v) for __v in _v])}} <b>]</b>
%elif isinstance(_v,dict):
<b>{</b><div style="margin-left:2em;">
%__k = _v.keys(); __k.sort()
%for _k in __k :
<div><b>{{_k}}</b> : 
%_debugdata(_v[_k])
<b>,</b></div>
%end #for
<b>}</b></div>
%else :
{{_v}}
%end #if/elif/else isinstance
%end #def
<b>_vars</b> <b>:</b>
%_debugdata(_vars)
</div>
<script type="text/javascript">
$(document).ready(function() {
$("#debug_btn")
.button()
.click(function(){ $("#debug_info").toggle("explode");});
});
</script>
<!-- /debug_dump -->
%end
