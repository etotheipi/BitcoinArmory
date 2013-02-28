#!/usr/bin/env python
#
# Copyright 2006, 2007 Google Inc. All Rights Reserved.
# Author: danderson@google.com (David Anderson)
#
# Script for uploading files to a Google Code project.
#
# This is intended to be both a useful script for people who want to
# streamline project uploads and a reference implementation for
# uploading files to Google Code projects.
#
# To upload a file to Google Code, you need to provide a path to the
# file on your local machine, a small summary of what the file is, a
# project name, and a valid account that is a member or owner of that
# project.   You can optionally provide a list of labels that apply to
# the file.   The file will be uploaded under the same name that it has
# in your local filesystem (that is, the "basename" or last path
# component).   Run the script with '--help' to get the exact syntax
# and available options.
#
# Note that the upload script requests that you enter your
# googlecode.com password.   This is NOT your Gmail account password!
# This is the password you use on googlecode.com for committing to
# Subversion and uploading files.   You can find your password by going
# to http://code.google.com/hosting/settings when logged in with your
# Gmail account. If you have already committed to your project's
# Subversion repository, the script will automatically retrieve your
# credentials from there (unless disabled, see the output of '--help'
# for details).
#
# If you are looking at this script as a reference for implementing
# your own Google Code file uploader, then you should take a look at
# the upload() function, which is the meat of the uploader.   You
# basically need to build a multipart/form-data POST request with the
# right fields and send it to https://PROJECT.googlecode.com/files .
# Authenticate the request using HTTP Basic authentication, as is
# shown below.
#
# Licensed under the terms of the Apache Software License 2.0:
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Questions, comments, feature requests and patches are most welcome.
# Please direct all of these to the Google Code users group:
#   http://groups.google.com/group/google-code-hosting
#
################################################################################
#
# Script downloaded from code.google.com and adapted for uploading
# new Armory releases.   It is included simply for my own convenience
# having this backed up
#
################################################################################

"""Google Code file uploader script.
"""

__author__ = 'danderson@google.com (David Anderson)'

import httplib
import os.path
import optparse
import getpass
import base64
import sys


def upload(file, project_name, user_name, password, summary, labels=None):
   """Upload a file to a Google Code project's file server.

   Args:
      file: The local path to the file.
      project_name: The name of your project on Google Code.
      user_name: Your Google account name.
      password: The googlecode.com password for your account.
                     Note that this is NOT your global Google Account password!
      summary: A small description for the file.
      labels: an optional list of label strings with which to tag the file.

   Returns: a tuple:
      http_status: 201 if the upload succeeded, something else if an
                         error occured.
      http_reason: The human-readable string associated with http_status
      file_url: If the upload succeeded, the URL of the file on Google
                     Code, None otherwise.
   """
   # The login is the user part of user@gmail.com. If the login provided
   # is in the full user@domain form, strip it down.
   if user_name.endswith('@gmail.com'):
      user_name = user_name[:user_name.index('@gmail.com')]

   form_fields = [('summary', summary)]
   if labels is not None:
      form_fields.extend([('label', l.strip()) for l in labels])

   content_type, body = encode_upload_request(form_fields, file)

   upload_host = '%s.googlecode.com' % project_name
   upload_uri = '/files'
   auth_token = base64.b64encode('%s:%s'% (user_name, password))
   headers = {
      'Authorization': 'Basic %s' % auth_token,
      'User-Agent': 'Googlecode.com uploader v0.9.4',
      'Content-Type': content_type,
      }

   server = httplib.HTTPSConnection(upload_host)
   server.request('POST', upload_uri, body, headers)
   resp = server.getresponse()
   server.close()

   if resp.status == 201:
      location = resp.getheader('Location', None)
   else:
      location = None
   return resp.status, resp.reason, location


def encode_upload_request(fields, file_path):
   """Encode the given fields and file into a multipart form body.

   fields is a sequence of (name, value) pairs. file is the path of
   the file to upload. The file will be uploaded to Google Code with
   the same file name.

   Returns: (content_type, body) ready for httplib.HTTP instance
   """
   BOUNDARY = '----------Googlecode_boundary_reindeer_flotilla'
   CRLF = '\r\n'

   body = []

   # Add the metadata about the upload first
   for key, value in fields:
      body.extend(
         ['--' + BOUNDARY,
          'Content-Disposition: form-data; name="%s"' % key,
          '',
          value,
          ])

   # Now add the file itself
   file_name = os.path.basename(file_path)
   f = open(file_path, 'rb')
   file_content = f.read()
   f.close()

   body.extend(
      ['--' + BOUNDARY,
       'Content-Disposition: form-data; name="filename"; filename="%s"'
       % file_name,
       # The upload server determines the mime-type, no need to set it.
       'Content-Type: application/octet-stream',
       '',
       file_content,
       ])

   # Finalize the form body
   body.extend(['--' + BOUNDARY + '--', ''])

   return 'multipart/form-data; boundary=%s' % BOUNDARY, CRLF.join(body)


def upload_find_auth(file_path, project_name, summary, labels=None,
                               user_name=None, password=None, tries=3):
   """Find credentials and upload a file to a Google Code project's file server.

   file_path, project_name, summary, and labels are passed as-is to upload.

   Args:
      file_path: The local path to the file.
      project_name: The name of your project on Google Code.
      summary: A small description for the file.
      labels: an optional list of label strings with which to tag the file.
      config_dir: Path to Subversion configuration directory, 'none', or None.
      user_name: Your Google account name.
      tries: How many attempts to make.
   """
   if user_name is None or password is None:
      from netrc import netrc
      authenticators = netrc().authenticators("code.google.com")
      if authenticators:
         if user_name is None:
            user_name = authenticators[0]
         if password is None:
            password = authenticators[2]

   while tries > 0:
      if user_name is None:
         # Read username if not specified or loaded from svn config, or on
         # subsequent tries.
         sys.stdout.write('Please enter your googlecode.com username: ')
         sys.stdout.flush()
         user_name = sys.stdin.readline().rstrip()
      if password is None:
         # Read password if not loaded from svn config, or on subsequent tries.
         print 'Please enter your googlecode.com password.'
         print '** Note that this is NOT your Gmail account password! **'
         print 'It is the password you use to access Subversion repositories,'
         print 'and can be found here: http://code.google.com/hosting/settings'
         password = getpass.getpass()

      status, reason, url = upload(file_path, project_name, user_name, password,
                                                 summary, labels)
      # Returns 403 Forbidden instead of 401 Unauthorized for bad
      # credentials as of 2007-07-17.
      if status in [httplib.FORBIDDEN, httplib.UNAUTHORIZED]:
         # Rest for another try.
         user_name = password = None
         tries = tries - 1
      else:
         # We're done.
         break

   return status, reason, url


# Copied from armoryengine.py
def getVersionString(vquad, numPieces=4):
   vstr = '%d.%02d' % vquad[:2]
   if (vquad[2] > 0 or vquad[3] > 0) and numPieces>2:
      vstr += '.%d' % vquad[2]
   if vquad[3] > 0 and numPieces>3:
      vstr += '.%d' % vquad[3]
   return vstr

def readVersionString(verStr):
   verList = [int(piece) for piece in verStr.split('.')]
   while len(verList)<4:
      verList.append(0)
   return tuple(verList)

def getVersionInt(vquad, numPieces=4):
   vint  = int(vquad[0] * 1e7)
   vint += int(vquad[1] * 1e5)
   if numPieces>2:
      vint += int(vquad[2] * 1e3)
   if numPieces>3:
      vint += int(vquad[3])
   return vint

def main():
   print ''
   print '-'*80
   print 'Executing upload script for bitcoinarmory.googlecode.com...'
   parser = optparse.OptionParser(usage='googlecode-upload.py [--dryrun] dirFilesToUpload')
   parser.add_option("--dryrun", dest="dryrun",  default=False, action="store_true", \
                     help="Detect and parse files to upload without actually executing the upload")
   parser.add_option("--testver", dest="testver",  default=False, action="store_true", \
                     help="Uploading a testing version; Only windows installers")
   options, args = parser.parse_args()

   if len(args)==0:
      print 'ERROR: must supply directory containing new installers to upload'
      return
   
   if not os.path.exists(args[0]):
      print 'ERROR: supplied path does not exist! %s' % args[0]
      return 

   theDir = args[0]
   latestVersion = 0
   latestVerStr  = None
   for fname in os.listdir(theDir):
      if fname.endswith('.msi') or fname.endswith('.deb'):
         try:
            verQuad = readVersionString(fname.split('_')[1].split('-')[0])
            verInt  = getVersionInt(verQuad)
            if verInt > latestVersion:
               latestVersion = verInt
               latestVerStr  = getVersionString(verQuad)
         except:
            print 'WARNING: Could not parse installer filename: %s' % fname
            continue


   verstr = '%s-beta' % latestVerStr
   if options.testver:
      verstr = '%s-testing' % latestVerStr

   print 'Latest version detected: ', verstr
   print '-'*80
   print ''

   prefix   = 'armory_'
   suffix = [['_amd64.deb',         'Version %s for Ubuntu/Debian 64-bit',   ['DebianPackage', 'OS-Linux64']], \
             ['_i386.deb',          'Version %s for Ubuntu/Debian 32-bit',   ['DebianPackage', 'OS-Linux32']], \
             ['_win64.msi',         'Version %s for Windows 64-bit',         ['WindowsMSI',    'OS-Win64']], \
             ['_windows_all.msi',   'Version %s for Windows 32- and 64-bit', ['WindowsMSI',    'OS-Win32']], \
             ['_sha256sum.txt.asc', 'Version %s SHA256 hashes of installers',['HashesSHA256']]]

   urlSummList = []
   password = getpass.getpass('Enter your googlecode password: ')
   for suf,summ,lbls in suffix:
      basename = prefix + verstr + suf
      fullpath = os.path.join(theDir, basename)

      if options.testver:
         # Only Windows pkgs uploaded for testing ver.  Linux can compile.
         if '.deb' in basename:
            continue
         else:
            # Change "Version..." to "Testing version..."
            summ = 'Testing v' + summ[1:]
         
      summary = summ % verstr

      if not os.path.exists(fullpath):
         print 'ERROR: Could not find installer to upload: %s', fullpath
         continue

      if not options.dryrun: 
         # Disabled for testing, just in case I forget --dryrun
         status, reason, url = upload_find_auth( fullpath, 'bitcoinarmory', summary, lbls, 'etotheipi', password)
         if url.startswith('http') and not url.startswith('https:'):
            print 'Original URL:', url
            url = 'https' + url[4:]
            print 'New URL:     ', url
      else:
         print 'Dryun requested, no actual upload performed'
         url = 'https://bitcoinarmory.googlecode.com/files/%s' % basename

      urlSummList.append([url, summary])
      if not url:
         print 'An error occurred. Your file was not uploaded.'
         print 'Google Code upload server said: %s (%s)' % (reason, status)
    

   print ''
   print '-'*80
   print 'Printing forum-formatted links to uploaded installers'
   for url,summary in urlSummList:
      print '[url=%s]%s[/url]' % (url, summary)

   print ''
   print '-'*80
   print 'Printing html/href links to include on webpage:'
   for url,summary in urlSummList:
      print '<a href="%s">%s</a>' % (url, summary)

   print '-'*80

if __name__ == '__main__':
   sys.exit(main())


    

    
