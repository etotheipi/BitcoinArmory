#! /usr/bin/python

# This script doesn't actually do the verification stuff yet.  You should 
# manually check, after this script completes, that signed_release_unpack:
#   dpkg-sig --verify *.deb
#   gpg -v *.asc
#   cd BitcoinArmory; git tag -v v0.90-beta  (or whatever the tag is)
from sys import argv
import os
import time
import shutil
from release_utils import *

#####
from release_settings import getReleaseParams, getMasterPackageList
#####

if len(argv)<2:
   import textwrap
   print textwrap.dedent("""
      Script Arguments (* is optional)
            argv[0]   "python %s"
            argv[1]   inputDir       (from Step2)
            argv[2]*  isDryRun       (default ~ 0)
            argv[3]*  useTestParams  (default ~ 0)
      """) % argv[0]
   exit(1)
   

# Parse CLI args
inDir      = checkExists(argv[1])
isDryRun   = (len(argv)>2 and not argv[2]=='0')
testParams = (len(argv)>3 and not argv[3]=='0')


masterPkgList = getMasterPackageList()
RELEASE = getReleaseParams(testParams)

signAddress    = RELEASE['SignAddr']
announceName   = RELEASE['AnnounceFile']
bucketPrefix   = RELEASE['BucketPrefix']
htmlRelease    = bucketPrefix + RELEASE['BucketReleases']
htmlAnnounce   = bucketPrefix + RELEASE['BucketAnnounce']
s3Release      = 's3://%s' % RELEASE['BucketReleases']
s3Announce     = 's3://%s' % RELEASE['BucketAnnounce']
gpgKeyID       = RELEASE['GPGKeyID']
btcWltID       = RELEASE['BTCWltID']


#uploadlog = open('step3_log_%d.txt' % long(time.time()), 'w')
uploadlog = open('step3_log.txt', 'w')
def logprint(s):
   print s
   uploadlog.write(s + '\n')

srcGitRepo  = checkExists(os.path.join(inDir, 'BitcoinArmory'))
srcInstalls = checkExists(os.path.join(inDir, 'installers'))
srcAnnounce = checkExists(os.path.join(inDir, 'signedannounce'))

# Scan the list of files in installers dir to get latest 
instList = [fn for fn in os.listdir(srcInstalls)]
topVerInt,topVerStr,topVerType = getLatestVerFromList(instList)


def getPkgFilename(pkgName, offline=False):
   if pkgName=='SHAFILE_TXT':
      suffix = 'sha256sum.txt'
   elif pkgName=='SHAFILE_ASC':
      suffix = 'sha256sum.txt.asc'
   else:
      suffixType = 'BundleSuffix' if offline else 'FileSuffix'
      suffix = masterPkgList[pkgName][suffixType]

   return 'armory_%s%s_%s' % (topVerStr, topVerType, suffix)


# Create [relpath, filename, isBundle, isHashes, [pentuple]] 
"""
uploads = []
ascfile = ''
for fn in os.listdir(unpackDir):
   fullfn = os.path.join(unpackDir, fn)
   fivevals = parseInstallerName(fullfn, ignoreExt=True)
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

"""

#uploads.sort(key=lambda x: x[1])
   
# Now actually execute the uploads and make them public
forumTextList = []
htmlTextList  = []
rawUrlList    = []
s3cmdList     = []


uploads = []
for pkgName,pkgInfo in masterPkgList.iteritems():
   pkgDict = {}
   pkgDict['SrcFile']   = getPkgFilename(pkgName)
   pkgDict['SrcPath']   = os.path.join(inDir, 'installers', pkgDict['SrcFile'])
   pkgDict['OSName']    = pkgInfo['OSNameDisp']
   pkgDict['OSVar']     = pkgInfo['OSVarDisp']
   pkgDict['OSArch']    = pkgInfo['OSArchDisp']
   pkgDict['IsHash']    = False
   pkgDict['IsBundle']  = False
   pkgDict['DstUpload'] = '%s%s' % (s3Release,   pkgDict['SrcFile'])
   pkgDict['DstHtml']   = '%s%s' % (htmlRelease, pkgDict['SrcFile'])
   uploads.append(pkgDict)

   if pkgInfo['HasBundle']:
      pkgDict = {}
      pkgDict['SrcFile']   = getPkgFilename(pkgName, offline=True)
      pkgDict['SrcPath']   = os.path.join(inDir, 'installers', pkgDict['SrcFile'])
      pkgDict['OSName']    = pkgInfo['OSNameDisp']
      pkgDict['OSVar']     = pkgInfo['BundleOSVar']
      pkgDict['OSArch']    = pkgInfo['OSArchDisp']
      pkgDict['IsHash']    = False
      pkgDict['IsBundle']  = True
      pkgDict['DstUpload'] = '%s%s' % (s3Release,   pkgDict['SrcFile'])
      pkgDict['DstHtml']   = '%s%s' % (htmlRelease, pkgDict['SrcFile'])
      uploads.append(pkgDict)
   

ascDict = {}
ascDict['SrcFile']   = getPkgFilename('SHAFILE_ASC')
ascDict['SrcPath']   = os.path.join(inDir, 'installers', ascDict['SrcFile'])
ascDict['IsHash']    = True
ascDict['IsBundle']    = True
ascDict['DstUpload'] = '%s%s' % (s3Release,   pkgDict['SrcFile'])
ascDict['DstHtml']   = '%s%s' % (htmlRelease, pkgDict['SrcFile'])
uploads.append(ascDict)


for upl in uploads:
   print 'Going to upload:'
   for key,val in upl.iteritems():
      print '   ', key.ljust(10), ':', val
   print ''



for pkgDict in uploads:

   #osStr, subOS, bits, vi, vs = fivevals
   #print fullfn, fn, isbundle, ishash, osStr, subOS, bits, vi, vs
   verFullStr = topVerStr + topVerType

   humanText = 'Armory %s' % verFullStr
   if pkgDict['IsBundle']:
      humanText += ' Offline Bundle'

   if pkgDict['IsHash']: 
      humanText += ': Signed hashes of all installers '
   else:
      osParams = [pkgDict[a] for a in ['OSName', 'OSVar', 'OSArch']]
      humanText += ' for %s %s %s' % tuple(osParams)
            
   uploadurl = pkgDict['DstUpload']
   linkurl   = pkgDict['DstHtml']

   s3cmd = 's3cmd put --acl-public %s %s' % (pkgDict['SrcPath'], uploadurl)
   forumText = '[url=%s]%s[/url]' % (linkurl, humanText)
   htmlText  = '<a href="%s">%s</a>' % (linkurl, humanText)

   forumTextList.append(forumText)
   htmlTextList.append(htmlText)
   rawUrlList.append(linkurl)
   s3cmdList.append(s3cmd)


announceDir = os.path.join(inDir, 'signedannounce')
for fn in os.listdir(announceDir):
   fpath = os.path.join(announceDir, fn)
   uploadurl = '%s%s' % (s3Announce, fn)
   s3cmd = 's3cmd put --acl-public %s %s' % (fpath, uploadurl)
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

if not isDryRun:
   
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
   logprint('   cd %s/BitcoinArmory; git push origin v%s' % (inDir, verFullStr))

