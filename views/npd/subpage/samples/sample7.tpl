%_vars['grid_showcols'] = 'acat,condition,code,detail,weight,target_price,last_updated,id,$pic'
%_vars['grid_sort']='target_price-desc'

%_vars['grid_caption']='Sellable Assets'
%_vars['grid_able']='gv'
%_vars['pivotcmds'].append('@sellable')

<div style="position:fixed;top:0;left:0;z-index:5000;opacity:0.7;"><a href='./' style="padding-left:0.5em;padding-right:0.5em;" class='ui-state-default ui-corner-all ui-button'>back</a></div>
%include subpage/grid _vars=_vars
