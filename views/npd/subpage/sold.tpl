%_vars['grid_showcols'] = 'acat,code,detail,buyer,sell_date,sell_price,sell_site'
%_vars['grid_sort']='detail'

%_vars['grid_caption']='Sold Assets//th:ขายแล้ว'
%_vars['grid__able']='gqv'
%_vars['pageoptions'].append('@f-buyer') #for grid-base4

%include subpage/grid _vars=_vars
