%_vars['grid_showcols'] = 'buy_date|วันที่,acat,!condition,code,detail,!weight,!serial,keeper,target_price'
%_vars['grid_sort']='buy_date-desc'

%_vars['grid_caption']='Sellable Assets//th:สินค้า่เดิม'
%_vars['grid__able']='gqv'
%_vars['pageoptions'].extend(['@f-buyer-','@f-buy_date-<$now(0,0,-1)']) #for grid-base4

%include subpage/grid _vars=_vars
