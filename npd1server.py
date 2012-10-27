# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        npd1server
# Purpose:     npd1 server
#
# Author:      jojosati
#
# Created:     05/01/2012
# Copyright:   (c) jojosati 2012
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import json,re
import datetime,os,StringIO
import threading
import optparse
import bottle
from beaker.middleware import SessionMiddleware

from npd1view import Npd1View as Model, _utf8, _unicode
from npd1view import reload_cfg, getcfg, _cfg

# ----------------------------------------
_models = []
# ----------------------------------------
def _l(accepts): return (''.join([l[:2] if l[:2] in (accepts.split(',')) else '' for l in bottle.request.headers.get('Accept-Language','').split(',')])+(accepts.split(',')[0]))[:2]
def _m(m,lang,msg): return m.split('//'+(lang or 'en')+':',1)[-1].split('//')[0] if not m or '//' in m or ' ' in m else _m(msg.get(m,m.title().replace('_',' '))+'//',lang,msg)

def downloadable (args,ext,prefix='download',encoding='') :
    download = args.get('_dl',False)
    if download :
        if download.lower() in ['1','true'] :
            if encoding : encoding = '_'+encoding
            download = prefix+datetime.datetime.now().strftime("_%Y%m%d%H%M")+encoding+ext
        if not download.lower().endswith(ext) : download += ext
        download = os.path.basename(download)
    return download

def send_fileobj(filename, root, guessmime=True, mimetype=None, download=False):
    """ replacement for bottle's static_file
        with more support for sending string, or file object like StringIO
        special keyword for root : ':string', ':file'
        when passing other data through filename
    """
    header = dict()
    if root in (':string',':file') : fileobj = filename
    elif root==':json' :
        fileobj = bottle.json_dumps(filename)
        mimetype = 'application/json'

    if fileobj :
        filename = download if isinstance(download,basestring) else 'noname'
    else :
        root = os.path.abspath(root) + os.sep
        filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))

        if not filename.startswith(root):
            return bottle.HTTPError(403, "Access denied.")
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return bottle.HTTPError(404, "File does not exist.")
        if not os.access(filename, os.R_OK):
            return bottle.HTTPError(403, "You do not have permission to access this file.")

    if not mimetype and guessmime:
        header['Content-Type'] = bottle.mimetypes.guess_type(filename)[0]
    else:
        header['Content-Type'] = mimetype if mimetype else 'text/plain'

    if download == True:
        download = os.path.basename(filename)
    if download:
        header['Content-Disposition'] = 'attachment; filename="%s"' % download
    if fileobj:
        l = None
        if isinstance(fileobj,basestring):
            l = fileobj.__sizeof__() - type(fileobj)().__sizeof__()
        elif hasattr(fileobj,'len') :
            l = fileobj.len
        elif hasattr(fileobj,'tell') and hasattr(fileobj,'seek') :
            old = fileobj.tell()
            fileobj.seek(0,2)
            l = fileobj.tell()
            fileobj.seek(old)
        if l : header['Content-Length'] = l
    else:
        stats = os.stat(filename)
        lm = bottle.time.strftime("%a, %d %b %Y %H:%M:%S GMT", bottle.time.gmtime(stats.st_mtime))
        header['Last-Modified'] = lm
        ims = bottle.request.environ.get('HTTP_IF_MODIFIED_SINCE')
        if ims:
            ims = ims.split(";")[0].strip() # IE sends "<date>; length=146"
            ims = bottle.parse_date(ims)
            if ims is not None and ims >= int(stats.st_mtime):
                header['Date'] = bottle.time.strftime("%a, %d %b %Y %H:%M:%S GMT", bottle.time.gmtime())
                return bottle.HTTPResponse(status=304, header=header)
        header['Content-Length'] = stats.st_size

    if bottle.request.method == 'HEAD':
        return bottle.HTTPResponse('', header=header)
    if not fileobj : fileobj = open(filename, 'rb')
    return bottle.HTTPResponse(fileobj, header=header)
    #return bottle.HTTPResponse(open(filename, 'rb'), header=header)


def suburlModel (suburl,abortcode=None) :
    if suburl is None:
        return [m.suburl for m in _models]

    if getcfg('server','suburl','') == suburl :
        return _models[0] if _models else Model
    for m in _models :
        if suburl == m.suburl :
            return m
    if abortcode :
        bottle.abort (abortcode,"Incorrect suburl ("+suburl+").")
    return None

def getparams () :
    params = {}
    params.update (bottle.request.params)
    params.update(bottle.request.environ.get('beaker.session',{}))
    return params

datacache = []
dcachewait = {}
def dcache(delay=5,**options) :
    callback = options.get('callback')
    if callable(delay) :
        callback = delay
        delay = 5
    ignore = ['logged_in','_creation_time','_accessed_time','nd',]
    if options.get('ignore') :
        ignore.extend(options.get('ignore'))

    def decorator(callback) :
        def wrapper(channel,target,*args,**kwargs) :
            global datacache,dcachewait

            taskid = kwargs.get('_creation_time')
            if taskid not in dcachewait :
                dcachewait[taskid] = 0

            ka = dict([ (k,v)
                        for k,v in kwargs.iteritems()
                            if k not in ignore ])
            if args :
                ka['*'] = args
            now = datetime.datetime.now()
            if datacache and delay:
                # strip outdate cache
                datacache = [c for c in datacache if now <= c[0]]
                for c in datacache :
                    if ka == c[1] :
                        #print '*** dcache hit',ka
                        return c[2]
            def _tproc(ka) :
                ret = callback(channel,target,*args,**kwargs)
                if taskid in dcachewait :
                    dcachewait[taskid] = 0
                #if ret is not None and delay:
                if ret is not None :
                    now = datetime.datetime.now()
                    datacache.insert(0, [
                            now + datetime.timedelta(minutes=delay or 5),
                            ka,
                            ret
                            ])
            t = threading.Thread(target=_tproc,args=(ka,))
            t.start()
            t.join(1.0)
            if t.isAlive() :
                if taskid in dcachewait :
                    dcachewait[taskid] += 1
                return ['||...waiting'+('.' * dcachewait.get(taskid,0))]
            for c in datacache :
                if ka == c[1] :
                    #print '*** dcache hit',ka
                    return c[2]

        return wrapper
    if callback :
        return decorator(callback)
    return decorator

taskcache = {}
def tprocess(channel,target,*args,**kwargs) :
    def _tproc(result) :
        result.append(
            target(*args,**kwargs)
            )

    #ss = bottle.request.environ.get('beaker.session')
    taskid = kwargs.get('_creation_time')
##    taskid = ss.get('taskid')
##    if not taskid :
##        taskid = str(hash(datetime.datetime.now()))
##        ss['taskid'] = taskid

    if taskid not in taskcache :
        taskcache[taskid] = {}

    task = taskcache[taskid]
    pid = None
    if task.get(channel) :
        if task.get(channel+'.args') == args :
            pid = task.get(channel)

            ka = dict([ (k,v)
                        for k,v in task.get(channel+'.kwargs').iteritems()
                            if k not in ['_creation_time','_accessed_time']
                            ])
            if ka == dict([(k,v)
                        for k,v in kwargs.iteritems()
                            if k not in ['_creation_time','_accessed_time']
                            ]) :
                #print 're-request',channel,pid,args,kwargs
                while pid.isAlive() :
                    pid.join(0.1)
                    if task.get(channel) != pid :
                        #print '*** re-abort',channel,pid,args,kwargs
                        return
                #print '*** re-success',channel,pid,args,kwargs
                return task.get(channel+'.result')

    #pid = str(hash(datetime.datetime.now()))

    result = []
    pid = threading.Thread(target=_tproc,args=(result,))

    task[channel] = pid
    task[channel+'.args'] = args
    task[channel+'.kwargs'] = kwargs

    now = datetime.datetime.now()
    print 'request',channel,pid,args,kwargs
    pid.start()
    while pid.isAlive() :
        pid.join(0.1)
        if task.get(channel) != pid :
            print '*** abort',channel,pid,datetime.datetime.now(),datetime.datetime.now() - now,args
            return
    if result :
        task[channel+'.result'] = result[0]
        print '*** success',channel,pid,datetime.datetime.now(),datetime.datetime.now() - now,args
        return result[0]



@bottle.route('/')
def index () :
    redir = getcfg('server','redir_index','')
    if not redir :
        redir = getcfg('server','suburl','')
        if not redir and _models :
            redir =  _models[0].suburl
        if not redir :
            return bottle.template('index')
        redir = '/' + redir
    return bottle.redirect(redir)

@bottle.route('/:suburl/resource/:filename#.*[^/]$#')
def resource(suburl,filename):
    suburlModel(suburl,404)
    return bottle.static_file(filename,root = './resource/')

@bottle.route('/:suburl/media/:filename#.*[^/]$#')
def media(suburl,filename):
    ''' public media '''
    model = suburlModel(suburl,404)
    mdir = model.getcfg('server','media_root','') or model.modeler._options_.get('media_root')
    if not mdir : bottle.abort (404,"Media root is not defined.")
    if mdir[-1] not in '/\\' : mdir += '/'
    args = getparams()
    if not model.mediaPermission(filename,args.get('user_role')) :
        bottle.abort (403,"Not allow to access media.")
    return bottle.static_file(filename, root = mdir)

@bottle.route('/:suburl/ajax/taxonomy/:field',method=['GET','POST'])
def ajax_taxonomy (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','taxonomy')
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
         abort (403,"Not allow to download data.")

    delay = 30
    if not args.get('term') :
        delay = 60
    #ret = model.taxonomy (field,**args)
    ret = dcache(delay,callback=tprocess)('taxonomy',model.taxonomy, field, **args)
    return send_fileobj(ret,':json',download=download)

@bottle.route('/:suburl/ajax/maxonomy/:field',method=['GET','POST'])
def ajax_maxonomy (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','maxonomy')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    #ret = model.maxonomy (field,**args)
    ret = tprocess('maxonomy',model.maxonomy, field, **args)
    return send_fileobj(ret,':json',download=download)

@bottle.route('/:suburl/ajax/autocomplete/:field',method=['GET','POST'])
def ajax_autocomplete (suburl,field) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','autocomplete')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    rules = model.modeler._options_.get('autocomplete_rule',{}).get(field)
    term = args.get('term')
    ret = None

    if rules is not None and term!='?' :
        ret = rules
        if isinstance(ret,basestring) :
            ret = ret.split(',')

        if hasattr(ret,'keys') :
            ret = ret.keys()
            #ret.sort()
        if ret :
            limit = args.get('limit',0)
            try : limit = int(limit)
            except: pass
            ret.sort()
            if isinstance(limit,int) and limit < 0 : ret.reverse()
            if term :
                term = _utf8(term)
                ret = model.taxonomy_mix(term,ret,xmax=abs(limit))
    if ret is None and field=='code' and not term :
        acat = args.get('acat')
        if acat and not term :
            acat_rules = model.modeler._options_ \
                    .get('autocomplete_rule',{}) \
                        .get('acat')
            if isinstance(acat_rules,dict) and acat in acat_rules :
                prefix = acat_rules[acat].get('code_prefix')
                if prefix :
                    ret =prefix
                    if isinstance(ret,basestring) :
                        ret = ret.split(',')
                    if hasattr(ret,'keys') :
                        ret = ret.keys()
                        ret.sort()

    if ret is None :
        delay = 5
        if not term :
            delay = 30
        if field == 'code' :
            delay = 0
        ignore = ['user_id','user_role']

        #ret = model.autocomplete (field,**args)
        ret = dcache(delay,callback=tprocess,ignore=ignore)('autocomplete',model.autocomplete, field, **args)
        if field == 'code' :
            if ret :
                if not args.get('term') :
                    _ret = []
                    for x in ret :
                        if not x :
                            continue
                        prefix = ''.join(re.split('([0-9]+)',x)[:1])
                        if prefix and prefix not in _ret :
                            _ret.append(prefix) #+'||('+x+')')
                    _ret.append('||---')
                    ret[0:0] = _ret
                else :
                    t = args.get('term')
                    _ret = [x for x in ret if isinstance(x,basestring) and x.startswith(t)]
                    if _ret :
                        ret = _ret
    if ret :
        return send_fileobj(ret,':json',download=download)

@bottle.route('/:suburl/ajax/jqgrid',method=['GET','POST'])
@bottle.route('/:suburl/ajax/jqgrid/grid',method=['GET','POST'])
def ajax_jqgrid_grid (suburl) :
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','grid')
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    #ret = model.jqgrid_grid(**args)
    ret = tprocess('grid',model.jqgrid_grid, **args)
    return send_fileobj (ret,':json',download=download)

@bottle.route('/:suburl/csv/jqgrid',method=['GET','POST'])
@bottle.route('/:suburl/csv/jqgrid/grid',method=['GET','POST'])
def csv_jqgrid_grid (suburl) :
    model = suburlModel(suburl,404)

    args = getparams()
    encoding = args['_encoding'] = args.get('_encoding') or model.getcfg('server','csv_encoding','utf-8')
    download = downloadable(args,'.csv','grid',encoding)
    if download and not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")

    output = StringIO.StringIO()
    re_csv_needquote = re.compile(r'([",]|^\s|\s$|[\n\r\f\v]|^-?[0-9]*(?:[.][0-9]*)?$)')
    rno = 0
    for row in model.jqgrid_grid_generator ('csv',**args):
        rno += 1
        for i in range(len(row)) :
            c = row[i]
            if rno==1 and args.get('_lang'):
                c = _utf8(c)
                fld = model.colModel(c)
                if fld :
                    fld_o = fld.get('options')
                    lang = args.get('_lang')
                    c = _unicode(_m(fld_o.get('label'),args.get('_lang'),{}) or c)
                    if encoding :
                        c = c.encode(encoding)
            if isinstance(c,basestring) :
                if c and re.search(re_csv_needquote,c) :
                    c = '"'+c.replace('"','""')+'"'
            elif c is None : c = ''
            else : c = str(c)
            row[i] = c
        output.write(','.join(row)+'\r\n')
    output.seek(0)
    return send_fileobj (output,':file',mimetype='text/csv',download=download)

@bottle.route('/:suburl/ajax/jqgrid/edit',method=['GET','POST'])
def ajax_jqgrid_edit (suburl) :
    model = suburlModel(suburl,404)
    ret = json.dumps(model.jqgrid_edit (**getparams()))
    model.logging("{0}",ret)
    return ret

@bottle.route('/:suburl/ajax/jqgrid/empty',method=['GET','POST'])
@bottle.route('/:suburl/ajax/jqgrid/noedit',method=['GET','POST'])
def ajax_jqgrid_nop (suburl) :
    return '[true,"",""]'

@bottle.route('/:suburl/ajax/media')
@bottle.route('/:suburl/ajax/media/:pattern#.*[^/]$#')
def ajax_media(suburl,pattern=None):
    model = suburlModel(suburl,404)
    args = getparams()
    download = downloadable(args,'.json','media')
    if download and  not model.colPermission('__table__',args.get('user_role'),'x') :
        abort (403,"Not allow to download data.")
    if not pattern: pattern = '*'
    #ret = model.mediaglob (pattern,**args)
    delay = 30
    ignore = ['user_id','user_role']

    ret = dcache(delay,ignore=ignore,callback=tprocess)('media',model.mediaglob, pattern, **args)
    return send_fileobj(ret,':json',download=download)

@bottle.route('/:suburl',method=['GET','POST'])
@bottle.route('/:suburl/:subpage#.*#',method=['GET','POST'])
def mainpage (suburl,subpage=None) :
    template_lookup = ['./views/'+suburl+'/','./views/__default__/','./views/']
    urltagstr = getcfg('server',"urltagstr",'') or '//'
    alturltagstr = getcfg('server',"alturltagstr",'') or '/='
    if urltagstr=='//' and getcfg('server',"server_type",'')=='paste' : urltagstr = alturltagstr

    if not subpage :
        if subpage is None: return bottle.redirect('/'+suburl+'/')
        else: subpage = 'index'
    else :
        subpage = '/'+_utf8(subpage)
        if urltagstr != '//':
            subpage = subpage.replace(urltagstr,'//')
        subpage = subpage.replace(alturltagstr,'//')
        if not subpage.startswith('//') : subpage = subpage[1:]

    #if subpage.endswith('/') : subpage += 'index'
    for ext in getcfg('server','resource_ext',[]) :
        if subpage.lower().endswith(ext):
            for spath in template_lookup :
                fname = os.path.join(spath,subpage)
                if os.path.isfile(fname):
                    return bottle.static_file(subpage,root = spath)


    if subpage and subpage[0]=='/' : subpage = '/' + subpage
    redir_url = '/'+suburl+'/'+(subpage if subpage else 'index')
    if urltagstr != '//' :
        redir_url = redir_url.replace('//',urltagstr)
    action = bottle.request.params.get('action')
    if action=='debug' :
        m = (bottle.request.params.get('mode','true').lower() in ['true','1'])
        if _cfg['server'].get('debug',False) != m :
            _cfg['server']['debug'] = m
            _restrict_cfg['server']['debug'] = m
            bottle.debug(getcfg('server',"debug",False))
        return bottle.redirect(redir_url)

    if action=='loadm':
        m = bottle.request.params.get('name')
        if m : load_model(m)
        return bottle.redirect(redir_url)
    if action=='unloadm':
        m = bottle.request.params.get('name')
        for i in range(len(_models)) :
            if _models[i].name==m :
                del _models[i]
                break
        if not suburlModel(suburl) :
            return bottle.redirect('/')
        return bottle.redirect(redir_url)

    model = suburlModel(suburl,404)

    args = {}
    if subpage.startswith('~') :
        subpage = subpage[1:]
        args['layout_loaded'] = '~'

    if getcfg('server','debug')  or action=='reload':
        reload_cfg()
        if isinstance(model,Model) : model.reload_cfg()
        bottle.TEMPLATES.clear()

    if action=='logout' :
        ss = bottle.request.environ.get('beaker.session')
        if 'logged_in' in ss :
            del ss['logged_in']
        if 'user_role' in ss :
            del ss['user_role']
        #ss.save()
        return bottle.redirect(redir_url)

    if 'alert_msg' not in args : args['alert_msg'] = []
    loginparms = bottle.request.params if getcfg('server','debug') else bottle.request.forms
    if loginparms.get('action')=='login' :
        u = _utf8(loginparms.get('user'))
        p = _utf8(loginparms.get('password'))
        uinf = model.getcfg('users',u,None)
        if uinf :
            role = uinf.get('role',model.getcfg('server','default_role','viewer'))
            # find hash lev
            hash = 0
            if role :
                _prm = model.modeler._permissions_
                for r in role.split(',') :
                    _h = _prm.get(r,{}).get('__hashlev__')
                    if _h is None : _h = _prm.get('*',{}).get('__hashlev__')
                    if _h and _h > hash : hash = _h
            pwd = uinf.get('password','')
            plst = []
            if hash<0 : plst.append(p)
            elif  not hash or hash==1 or hash==-1:
                plst.append(hashlib.md5(p).hexdigest())
            elif  not hash or hash==2 or hash==-2 :
                plst.append(hashlib.md5(u+':'+p).hexdigest())
            elif  not hash or hash>=3 or hash<=-3 :
                plst.append(hashlib.md5(u+':'+p+'@'+uinf.get('role','')).hexdigest())
            if pwd in plst :
                ss = bottle.request.environ.get('beaker.session')
                ss.update ({'user_id': u, 'logged_in': 1, 'user_role': role})
                #ss.save()
                return bottle.redirect(redir_url)
            args['alert_msg'].append('Invalid username or incorrect password.')
        else :
            if not model.getcfg('users')  and u==p :
                ss = bottle.request.environ.get('beaker.session')
                ss.update( {'user_id': u, 'logged_in' : 1, 'user_role' : u} )
                #ss.save()
                return bottle.redirect(redir_url)
            args['alert_msg'].append('Invalid username or incorrect password.')

    sepoption,pagetag = '',''
    urloptions,pageoptions,pivotcmds = [],[],[]
    kwoptions = {}

    if subpage and subpage[0]=='/' : subpage = '/' + subpage
    (urlsubpage,urlpagetag) = model.split_subpage(subpage)
    paramstag = bottle.request.params.get('$','')
    if paramstag: paramstag = '/'+paramstag
    if urlpagetag :
        urloptions = model.split_pagetag (urlpagetag)
    if not subpage:
        subpage = _cfg['server'].get('default_subpage','')
    subpage,pagetag = model.expand_subpage_alias(subpage)
    pagetag += paramstag
    if pagetag :
        sepoption = '/' #deprecate
        pageoptions = model.expand_pageoption_alias (model.split_pagetag (pagetag))
        for o in pageoptions :
            if o[0] == '@' :
                pivotcmds.append(o)
            if '-' in o :
                (k,v) = o.split('-',1)
                if k : kwoptions[k] = v

    params = getparams()
    args.update({
        #'urlsuburl' : suburl,
        'suburl' : suburl,
        'urlsubpage' : urlsubpage,
        'urlpagetag' : urlpagetag,
        'urloptions' : urloptions,
        'subpage' : subpage,
        'urltagstr' : urltagstr,
        'pagetag' : pagetag,
        'pageoptions' : pageoptions,
        'kwoptions' : kwoptions,
        'sepoption' : sepoption,
        'pivotcmds' : pivotcmds,
        'user' : params.get('user_id',''),
        'logged_in' : params.get('logged_in',''),
        'user_role' : params.get('user_role',''),
        '_libs_' : {'json' : json, 're' : re},
        '_server_' : dict(getcfg('server')),
        '_header_' : dict(bottle.request.headers.items()),
        })
    #args.update(_cfg['server'])
    args['_server_'].update(model.getcfg('server'))
    if isinstance(model,Model) :
        # deprecate --- for grid-base.tpl
        args['ajax_fields'] = _utf8(json.dumps(model.ajaxCols(False,**params)).replace(' ',''))

        # new --- for grid-base2.tpl
        args['ajax_extfields'] = model.ajaxExtCols(**params)
        args['modeler_options'] = model.modeler._options_
        args['summary_keys'] = []
        skeys = model.getcfg('summaries')
        if skeys :
            for k in skeys.keys() :
                k = k[1:-1]
                if k and k[0]!='_' : args['summary_keys'].append(k)
            args['summary_keys'].sort()
        args['_msg'] = {}
        args['_libs_']['_m']= _m
        args['_libs_']['_l']= _l
    if subpage :
        try :
            pg = subpage
            #return subpage
            if subpage.endswith('/') : pg += 'index'
            if subpage.startswith('subpage/') :
                pg = _cfg['server'].get('default_subpage') or pg
            return bottle.template(pg,template_lookup=template_lookup,_vars=args)
        except bottle.TemplateError as e :
            if subpage.startswith('subpage/'): raise e
    mainpage = _cfg['server'].get('default_mainpage') or 'mainpage'
    return bottle.template(mainpage,template_lookup=template_lookup,_vars=args)

def load_model (model,dbfile=''):
    if isinstance(model,basestring) : model = model.split(',')
    if isinstance(model,(list,tuple)) :
        if len(model)>1 :
            dbfile = None
        for m in model :
            found = False
            for mm in _models :
                if mm.name==m :
                    found = True
                    break
            if not found :
                mm = Model(m,dbfile=dbfile)
                mm.reload_cfg()
                _models.append(mm)

    if isinstance(model,dict) :
        if len(model)>1 :
            dbfile = None
        for mm in _models :
            if mm.name==model.name :
                model = None
                break
        if model :
            _models.append(Model(model,dbfile=dbfile))

def start_http_server () :
    session_opts = {
        'session.type': 'file',
        #'session.timeout': False,
        'session.cookie_expires': (8*60*60),
        'session.data_dir': './sessions',
        'session.auto': True
    }
    debug = getcfg('server',"debug",False)
    bottle.debug(debug)
    server_app = SessionMiddleware(bottle.app(), session_opts)
    bottle.run(server=(getcfg('server',"server_type",'') or 'wsgiref'),app=server_app,host=getcfg('server','host','0.0.0.0'),port=getcfg('server',"port",8080))


def start (model=None) :
    parser = optparse.OptionParser()
    parser.add_option("-d", "--dbfile",
                      action="store",
                      dest="dbfile",
                      default="",
                      help="database file")
    parser.add_option("-c", "--csv",
                      action="store",
                      dest="csv",
                      default="",
                      help="clear current database and import new csv data to database",)
    parser.add_option("-m", "--model",
                      action="store",
                      dest="model",
                      default="",
                      help="import model name",)
    parser.add_option("-p", "--port",
                      action="store",type="int",
                      dest="port",
                      default=0,
                      help="server listening port",)
    parser.add_option("-x", "--exit",
                      action="store_true",
                      dest="exit",
                      default=False,
                      help="exit without start server")

    reload_cfg (False)
    (options, args) = parser.parse_args()
    if model is None : model = getcfg('server','startup_model',None)
    if options.model : model = options.model
    if model :
        load_model(model,options.dbfile)

    if options.port :
        _restrict_cfg['server']['port'] = options.port
        _cfg['server']['port'] = options.port

    #Model.start_sql_server ()

    if options.csv :
        _models[0].load_csv (options.csv)

    if not options.exit :
        #Model.metadata.create_all()
        print getcfg('server')
        start_http_server()

if __name__ == "__main__":
    start ()
