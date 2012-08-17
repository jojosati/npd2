# setup.py
from distutils.core import setup
import py2exe
import glob
import os

import sys
sys.argv[1:] = ['py2exe','-d','dist/npd1c2']

data_files = [
            ("cfg",[
                "cfg/server_cfg.sample.py",
                "cfg/users_cfg.sample.py",
                ]),
            ("models",["models/assets.py",]),
            ("models/assets",[
                "models/assets/aliases_cfg.sample.py",
                "models/assets/model_cfg.sample.py",
                "models/assets/taxonomies_cfg.sample.py",
                ]),
            #("db",["db/npd2.sqlite.db",]),
            ]

def mk_tree (root):
    data_files.append((root,glob.glob(root+'/*.*')))
    for d in os.listdir (root) :
        p = os.path.join(root,d)
        if os.path.isdir(p) :
            data_files.append((p,glob.glob(p+'/*.*')))
            mk_tree(p)

mk_tree ('resource')
mk_tree('views/__default__')
mk_tree('views/npd')
#mk_tree('media/npd')

setup(
        version = "1.7.c2",
        description = "NetScraft Server - Nariga-D",
        name = "npd server",
        console=[{'script':"npd1server.py",'dest_base':"npd1c2"}],
        options={
            "py2exe": {
                "compressed": 1,"optimize": 2,"ascii": 1,
                "bundle_files": 1,
                "includes": ["encodings","encodings.*","dbhash"],
                "packages": ["sqlalchemy.dialects.sqlite"],
                "excludes": ["tcl","Tkconstants","Tkinter"]
                }
            },
        data_files=data_files,
        zipfile = None,
        )
