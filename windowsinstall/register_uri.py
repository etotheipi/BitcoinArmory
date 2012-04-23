from _winreg import *

import platform

osBits = platform.architecture()[0][:2]

x86str = ''
if osBits=='64':
   x86str = ' (x86)'

updateKeys = []
updateKeys.append([r'bitcoin', '', None])
updateKeys.append([r'bitcoin', 'URL Protocol', ""])
updateKeys.append([r'bitcoin\shell', '', None])
updateKeys.append([r'bitcoin\shell\open', '',  None])
updateKeys.append([r'bitcoin\shell\open\command',  '', \
   r'"C:\Program Files%s\Armory\Armory Bitcoin Client\Armory.exe" %1'])
updateKeys.append([r'bitcoin\DefaultIcon', '',   \
   r'"C:\Program Files%s\Armory\Armory Bitcoin Client\armory48x48.ico'])

for k,v in updateKeys:
   key = CreateKey(HKEY_CURRENT_USER, 
