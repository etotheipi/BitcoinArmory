from _winreg import *

import platform

osBits = platform.architecture()[0][:2]

x86str = ''
if osBits=='64':
   x86str = ' (x86)'

baseDir = 'C:\\Program Files%s\\Armory\\Armory Bitcoin Client' % x86str

updateKeys = []
updateKeys.append(['bitcoin', '', 'URL:bitcoin Protocol'])
updateKeys.append(['bitcoin', 'URL Protocol', ""])
updateKeys.append(['bitcoin\\shell', '', None])
updateKeys.append(['bitcoin\\shell\\open', '',  None])
updateKeys.append(['bitcoin\\shell\\open\\command',  '', \
                   '"%s\\Armory.exe" %%1' % baseDir])
updateKeys.append(['bitcoin\\DefaultIcon', '',  \
                   '"%s\\armory48x48.ico"' % baseDir])

print 'Attempting to read registry keys...'

# First get the existing keys
origRegistry = {}
for key,name,val in updateKeys:
   dkey = '%s\\%s' % (key,name)
   print '\tReading key: [HKEY_CURRENT_USER]\\]' + dkey
   try:
      registryKey = OpenKey(HKEY_CURRENT_USER, key, 0, KEY_READ)
      origRegistry[dkey] = QueryValueEx(registryKey, name)
   except:
      raise
      origRegistry[dkey] = ''

print 'Keys read:'
for k,v in origRegistry.iteritems():
   print k,v[0]
   print '\t', k.ljust(40), '"%s"'%v[0]

print 'Attempting to write registry keys...'

for key,name,val in updateKeys:
   dkey = '%s\\%s' % (key,name)
   print '\tWriting key: [HKEY_CURRENT_USER\\]' + dkey
   registryKey = CreateKey(HKEY_CURRENT_USER, key)
   SetValueEx(registryKey, name, 0, REG_SZ, val)
   CloseKey(registryKey)
      
