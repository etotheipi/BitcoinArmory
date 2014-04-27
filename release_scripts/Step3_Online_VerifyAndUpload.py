#! /usr/bin/python

# This script doesn't actually do the verification stuff yet.  You should 
# manually check, after this script completes, that signed_release_unpack:
#   dpkg-sig --verify *.deb
#   gpg -v *.asc
#   cd BitcoinArmory; git tag -v v0.90-beta  (or whatever the tag is)
import sys
import os
import time
import shutil
from release_utils import *


startDir = os.getcwd()
latestVerInt, latestVerStr, latestRelease = 0,'',''
unpackDir = 'signed_release_unpack'
bucket = 'bitcoinarmory-releases'
buckets3 = 's3://%s' % bucket
bucketdl = 'https://s3.amazonaws.com/%s' % bucket

#uploadlog = open('step3_log_%d.txt' % long(time.time()), 'w')
uploadlog = open('step3_log.txt', 'w')
def logprint(s):
   print s
   uploadlog.write(s + '\n')

# Find the latest signed_release archive 
for fn in os.listdir('.'):
   if not fn.startswith('signed_release'):
      continue 

   fivevals = parseInstallerName2(fn, ignoreExt=True)

   if fivevals==None:
      continue

   vs,vi,vt = fivevals[1:4]
   if vi>latestVerInt:
      latestVerInt = vi
      latestVerStr = vs
      latestVerType = vt
      latestRelease = fn
   
   
# Get the version type "testing", "beta", etc
locver  = latestRelease.index(latestVerStr)
lenver  = len(latestVerStr)
locdot  = latestRelease.index('.', locver+lenver+1)
verFullStr = latestVerStr + latestVerType


logprint('')
logprint('*'*80)
logprint('Detected Release Parameters:')
logprint('   Version type: ' + latestVerType)
logprint('   Full version: ' + verFullStr)
logprint('   Release file: ' + latestRelease)
logprint('   S3 Bucket   : ' + buckets3)
logprint('   DL Links    : ' + bucketdl)
logprint('')

################################################################################
# Now unpack and start doing our thing
if os.path.exists(unpackDir):
   logprint('Removing previous unpack-directory: %s' % unpackDir)
   shutil.rmtree(unpackDir)

os.mkdir(unpackDir)
execAndWait('tar -zxf %s -C %s' % (latestRelease, unpackDir))

# Create [relpath, filename, isBundle, isHashes, [pentuple]] 
uploads = []
ascfile = ''
for fn in os.listdir(unpackDir):
   fullfn = os.path.join(unpackDir, fn)
   fivevals = parseInstallerName2(fullfn, ignoreExt=True)
   if fivevals==None or os.path.isdir(fullfn):
      continue

   osName,verStr,verInt,verType,suffix = fivevals[:]
   isBundle = suffix.lower().startswith('offline')
   isHashes = ("sha256" in fn)
   uploads.append( [fullfn, fn, isBundle, isHashes, fivevals] )

   ascfile = ascfile if not isHashes else fullfn


# Read hashes from signed hashes file and put into a map
hashmap = {}
with open(ascfile,'r') as asc:
   allLines = [l.strip().split() for l in asc.readlines()]
   for line in allLines:
      if len(line)==2 and 'armory' in line[1].lower():
         hashmap[line[1]] = line[0]


#####
logprint('*'*80)
logprint('Checking signatures on debian packages:')
out,err = execAndWait('dpkg-sig --verify %s/*.deb' % unpackDir)
logprint(out)
logprint(err)


#####
logprint('*'*80)
logprint('Checking signed tag on repo:')
os.chdir('%s/BitcoinArmory' % unpackDir)
out,err = execAndWait('git tag -v v%s' % verFullStr)
os.chdir(startDir)
logprint(out)
logprint(err)


#####
logprint('*'*80)
logprint('Checking signature on hashes file:')
out,err = execAndWait('gpg -v %s/*.asc' % unpackDir)
logprint(out)
logprint(err)


#####
logprint('*'*80)
logprint('Checking individual file hashes')
for fn,signedhash in hashmap.iteritems():
   out,err = execAndWait('sha256sum %s/%s' % (unpackDir, fn))
   computedhash = out.split()[0]
   if computedhash==signedhash:
      logprint('   [GOOD] ' + signedhash + ' ' + fn)
   else:
      logprint('   XXXXXX ' + signedhash + ' ' + fn)



raw_input('\nConfirm all signature checks passed...[press enter when done]')


pkgMap = {}
pkgMap['osx'] = ['MacOSX', '(All)', '(64bit)']
pkgMap['winAll'] = ['Windows', '(All)', '(32- and 64-bit)']
pkgMap['raspbian'] = ['Raspberry Pi', '', '(armhf)' ]
pkgMap['ubuntu32'] = ['Ubuntu', '12.04+', '(32bit)' ]
pkgMap['ubuntu64'] = ['Ubuntu', '12.04+', '(64bit)' ]


uploads.sort(key=lambda x: x[1])
   
# Now actually execute the uploads and make them public
forumTextList = []
htmlTextList  = []
rawUrlList    = []
s3cmdList     = []
for fullfn, fn, isbundle, ishash, fivevals in uploads:

   #osStr, subOS, bits, vi, vs = fivevals
   #print fullfn, fn, isbundle, ishash, osStr, subOS, bits, vi, vs

   osName,verStr,verInt,verType,ext = fivevals[:]
   humanOS,humanVer,humanBits = pkgMap[ext]

   humanText = 'Armory %s' % verFullStr
   if isbundle:
      humanText += ' Offline Bundle'

   if ishash: 
      humanText += ': Signed hashes of all installers '
   else:
      humanText += ' for %s %s %s' % tuple(pkgMap[ext])
            
   uploadurl = '%s/%s' % (buckets3, fn)
   linkurl = '%s/%s' % (bucketdl, fn)

   s3cmd = 's3cmd put --acl-public %s %s' % (fullfn, uploadurl)
   #s3cmd = 's3cmd put %s %s' % (fullfn, uploadurl)
   forumText = '[url=%s]%s[/url]' % (linkurl, humanText)
   htmlText  = '<a href="%s">%s</a>' % (linkurl, humanText)

   forumTextList.append(forumText)
   htmlTextList.append(htmlText)
   rawUrlList.append(linkurl)
   s3cmdList.append(s3cmd)
   

logprint('\nRAW URL LIST')
for txt in rawUrlList:
   logprint('  '+txt)

logprint('\nFORUM POSTING LINKS')
for txt in forumTextList:
   logprint('  '+txt)

logprint('\nWEBSITE POSTING LINKS')
for txt in htmlTextList:
   logprint('  '+txt)

logprint('\nS3CMD UPLOAD COMMANDS')
for txt in s3cmdList:
   logprint('  '+txt)

logprint('')
yn = raw_input('Continue with upload? [y/N]')

if yn.lower().startswith('y'):
   logprint('STARTING UPLOADS')
   for s3cmd in s3cmdList:
      logprint('Uploading: ' + s3cmd.split()[-1].strip())
      execAndWait(s3cmd, usepipes=False)


logprint('')
logprint('Not actually pushing the signed tag; do it manually --')
logprint('Copy the following command to push the tag:')
logprint('   cd %s/BitcoinArmory; git push origin v%s' % (unpackDir, verFullStr))

