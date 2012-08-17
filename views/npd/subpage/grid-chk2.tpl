%_vars['grid_showcols'] = 'acat,code,detail,keeper,buyer,sell_date,sell_site,sell_price,mark_cost,sell_profit,base_cost,provider_cost,repair_cost,invalidity'
%_vars['grid_sort']='sell_date-desc'

%_vars['grid_caption']='grid check 2'
%_vars['grid__able']='gadeqsvzph' # z=zoom, p=pivot url, h=history
%_vars['pageoptions'].extend([]) #for grid-base4

%include subpage/grid _vars=_vars
