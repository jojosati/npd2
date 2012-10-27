%
%if not _vars.get('layout_loaded'): _vars['layout_loaded']='netscraft'
%
%rebase helper/layout-dynamic _vars=_vars
%
%include helper/page-header _vars=_vars
%
%include
%
%include helper/page-debug _vars=_vars
%include helper/page-footer _vars=_vars
%include helper/alert-dialog _vars=_vars
%
%rebase helper/layout-dynamic _vars=_vars
