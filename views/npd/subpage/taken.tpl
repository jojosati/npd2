%_vars['grid_showcols'] = 'acat,code,detail,taker,take_date,taken_days,taker_price'
%_vars['grid_sort']='detail'

%_vars['grid_caption']='Taken Assets//th:ถูกยืม'
%_vars['grid__able']='gqv'
%_vars['pageoptions'].extend(['@f-taker','@f-buyer-']) #for grid-base4

%include subpage/grid _vars=_vars
