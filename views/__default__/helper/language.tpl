%if 'language' not in _vars :
%_vars['language'] = _vars['_libs_']['_l']('en,th') #select supported language for this view
%_vars['_m'] = (lambda m : _vars['_libs_']['_m'](m,_vars['language'],_vars['_msg']))
%end
