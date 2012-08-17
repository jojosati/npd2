%_require_vars=['suburl']
%[locals().update({k:_vars[k]}) for k in _require_vars]
%_option_vars=['title','urlsubpage','urloptions']
%[locals().update({k:_vars.get(k)}) for k in _option_vars]
%title = title or (suburl + (('/'+urlsubpage) if urlsubpage else '').replace('/',' - ')+((' '+'*') if urloptions else ''))
<title>{{title}}</title>
