#! /usr/bin/python
from distutils.core import setup
import py2exe


opts = {"py2exe":{
    "dll_excludes":["MSWSOCK.dll", "IPHLPAPI.dll", "MSWSOCK.dll", "WINNSI.dll", "WTSAPI32.dll"]
    }}

setup( options = opts, windows = [
                        {
                            "script": "../../ArmoryQt.py",
                            "icon_resources": [(1, "../../img/armory256x256.ico")]
                        }
                ],
    )


