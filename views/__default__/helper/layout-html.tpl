
%if not _vars.get('layout_loaded'): _vars['layout_loaded']='html'
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
{{_vars.get('prepend_htmlhead','')}}
  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  <title>{{_vars.get('title_htmlhead','')}}</title>
{{_vars.get('append_htmlhead','')}}
</head>
<body class="ui-widget" style="font-size:75%;">
%include
</body>
</html>