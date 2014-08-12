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
import json
from datetime import datetime

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



#uploads.sort(key=lambda x: x[1])
   
# Now actually execute the uploads and make them public
forumTextList = []
htmlTextList  = []
rawUrlList    = []
s3cmdList     = []


# Try to make things sorted properly
osSort = ['Windows', 'MacOSX', 'Ubuntu', 'RaspberryPi'][::-1]

pkgPairs = []
while len(osSort)>0:
   thisOS = osSort.pop()
   for pkgName,pkgInfo in masterPkgList.iteritems():
      if thisOS == pkgInfo['OSNameDisp']:
         pkgPairs.append([pkgName,pkgInfo])
      

uploadsRegular = []
uploadsOffline = []
for pkgName,pkgInfo in pkgPairs:
   pkgDict = {}
   pkgDict['SrcFile']   = getPkgFilename(pkgName)
   pkgDict['SrcPath']   = os.path.join(inDir, 'installers', pkgDict['SrcFile'])
   pkgDict['OSName']    = pkgInfo['OSNameDisp']
   pkgDict['OSVar']     = pkgInfo['OSVarDisp']
   pkgDict['OSArch']    = pkgInfo['OSArchDisp']
   pkgDict['IsHash']    = False
   pkgDict['IsBundle']  = False
   pkgDict['DstUpload'] = '%s%s' % (s3Release,   pkgDict['SrcFile'])
   pkgDict['DownLink']  = '%s%s' % (htmlRelease, pkgDict['SrcFile'])
   uploadsRegular.append(pkgDict)

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
      pkgDict['DownLink']  = '%s%s' % (htmlRelease, pkgDict['SrcFile'])
      uploadsOffline.append(pkgDict)

uploads = uploadsRegular + uploadsOffline
   

ascDict = {}
ascDict['SrcFile']   = getPkgFilename('SHAFILE_ASC')
ascDict['SrcPath']   = os.path.join(inDir, 'installers', ascDict['SrcFile'])
ascDict['IsHash']    = True
ascDict['IsBundle']  = False
ascDict['DstUpload'] = '%s%s' % (s3Release,   ascDict['SrcFile'])
ascDict['DownLink']   = '%s%s' % (htmlRelease, ascDict['SrcFile'])
uploads.append(ascDict)


jsonOut = {}
jsonOut['VersionStr'] = topVerStr + topVerType
jsonOut['ReleaseDate'] = datetime.fromtimestamp(time.time()).strftime("%B %d, %Y")
jsonOut['Downloads'] = uploads

print json.dumps(jsonOut, indent=4)

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
      humanText += ' for %s %s (%s)' % tuple(osParams)
            
   uploadurl = pkgDict['DstUpload']
   linkurl   = pkgDict['DownLink']

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

