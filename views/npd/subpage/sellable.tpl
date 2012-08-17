%_vars['grid_showcols'] = 'acat,!condition,code,detail,!weight,!serial,keeper,target_price'
%_vars['grid_sort']='detail'

%_vars['grid_caption']='Sellable Assets//th:พร้อมขาย'
%_vars['grid__able']='gqv'
%_vars['pageoptions'].append('@f-buyer-') #for grid-base4

%include subpage/grid _vars=_vars
