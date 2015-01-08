Build & Release Process for Armory

This directory contains a variety of scripts that will be used to compile,
bundle, sign, and upload new releases of Armory.  There are three scripts
because it is assumed that the signing keys are offline, requiring something
similar to an offline transaction:  create everything online, take offline
for signing, take online again to broadcast (upload to Amazon S3).


The following is assumed to have been done already before starting this 
process:

   - Local & remote machines and VMs have compiled & bundled installers
   - release_settings.py file that returns nested dictionary of all 
     release/installer information (see example at end of this doc)
   - Each remote system has our public key in its authorized_keys file
   - Offline computer has GPG key & Armory wallet spec'd at top of Step2 script
   - All announce files are updated (except for dllinks which will be updated
      by the script itself once files are signed and hashes are known)
   - The Step2 script contains an accurate list of everything file/installer
   - The computer running Step3 has write-access to the git repo, and a 
      configuration file with API key for uploading results to Amazon S3
   - Directories on the offline computer containing dependencies for each 
      OS-specific offline-bundle
   - Already have an installed version of Armory offline in the /usr/lib/armory
      directory, to be used for creating signature blocks

The output of this process will be:

   - Signed git tag that can be pushed to the repo
   - All .deb installers will be signed using dpkg-sig
   - Offline bundles using the signed deb files
   - GPG-signed hashes file including all regular installers and offline bundles
   - Append URLs and hashes to dllinks.txt
   - New announce.txt file that contains URLs and hashes of all notify files
     signed by offline BITCOIN private key
   - Full list of URLs of uploaded installers & bundles in HTML and forum
     markdown, for easy updating of website and forum posts


-----
Step1 Script:

Fetch all the installers, and do a fresh checkout of the 
repo. It should also include updates to the announcement files
After that, put everything into a single directory that 
can be copied to a USB key to be taken to the offline computer.

   Script Arguments (* is optional)
         argv[0]   <>
         argv[1]   version string,  "0.91.1"
         argv[2]   version type,    "-testing", "-beta", ""
         argv[3]*  output directory      (default ~ ./exportToOffline)
         argv[4]*  unsigned announce dir (default ~ ./unsignedannounce)
         argv[5]*  Bitcoin Core SHA256SUMS.asc (default ~ "None")
         argv[7]*  use testing settings (default ~ "0")
      
   Script Output:

      <outputDir>/BitcoinArmory       (clone of repo)
      <outputDir>/release_scripts     (copy of release_scripts dir from repo)
      <outputDir>/installers          (all non-offline-bundle packages)
      <outputDir>/unsignedannounce    (all unsigned announcement files)
      <outputDir>/SHA256SUMS.asc      (if present)

Note the release_scripts dir is itself copied because it has release_settings.py
which is needed by all three steps.  Plus, we most likely made tweaks to 
these Step* scripts to support the current release, and it wouldn't be in 
the cloned repo yet.  After the release is successful, we commit the updated 
scripts as the basis for the next release.  




-----
Step2 Script:

This script will be executed from the release_scripts directory above --
we will copy the directory to the offline computer, then cd into it then run 
Step2 script from there.  It does not depend on the cloned repo -- it adds
/usr/lib/armory to sys.path, to use the currently installed version
of Armory for any non-generic-python operations.

   Script Arguments (* is optional)
         argv[0]   <>
         argv[1]   inputDir  (from Step1)
         argv[2]   outputDir (for Step3)
         argv[3]   bundleDir 
         argv[6]*  git branch to tag (default ~ "master")
         argv[7]*  use testing settings (default ~ 0)
      
   Script Output:

      <outputDir>/BitcoinArmory       (same repo but with signed tag v0.91.1)
      <outputDir>/release_scripts     (same copy, unmodified)
      <outputDir>/installers          (signed, now includes offline bundles)
      <outputDir>/announceFiles       (all txt signed, added announce.txt)

The "bundleDir" should contain one directory for everything in the master
package list that "hasBundle==True".  It's "BundleDeps" will be the name
of the directory that the Step 2 script will look for.   The bundle deps dir
will contain all dependencies (all of them .debs, as of this writing), as
well as a script that installs everything including the package itself.  
i.e. Step2 script will make a copy of the bundle deps, it will copy the
signed installer into the copy, and then tar it all up.  The bundle deps
dir should have, in addition to the deps themselves, a script that will
install everything in that directory including the signed package.

The testing settings use a different GPG key, BTC key, and different bucket
for uploading



-----
Step 3 Script:

Will expect to find the three directories above with signed data.  It will
actually execute verification of all signatures, though you will have to
manually verify the output before continuing.  After that, it will attempt
to upload everything.

It expects to find the .s3cmd configuration file, already setup with your
S3 API key to be able to upload files to the BitoinArmory-releases bucket.
It will do the following:


   Script Arguments (* is optional)
         argv[0]   <>
         argv[1]   inputDir  (from Step2)
         argv[2]*  isDryRun  (default ~ False)
      
   Script Output:

         -- Upload all installers and offline bundles to BitcoinArmory-releases 
         -- Upload all announce files to BitcoinArmory-media bucket
         -- Ask if you'd like to push the latest git tag (if this is a testing
            version, you may not want to push the tag)

  


################################################################################
#                                                                              #
# Example release_settings.py file                                             #
#                                                                              #
# Provides dictionaries "getReleaseParams" and "getMasterPackageList"          #
#                                                                              #
################################################################################

#! /usr/bin/python
import os


def getReleaseParams(doTest=False):
   rparams = {}
   rparams['Builder']        = 'Armory Technologies, Inc.'
   rparams['GitUser']        = 'Armory Technologies, Inc.'
   rparams['GitEmail']       = 'contact@bitcoinarmory.com'

   if not doTest:
      rparams['SignAddr']       = '1NWvhByxfTXPYNT4zMBmEY3VL8QJQtQoei'
      rparams['AnnounceFile']   = 'announce.txt'
      rparams['BucketAnnounce'] = 'https://s3.amazonaws.com/bitcoinarmory-media/'
      rparams['BucketReleases'] = 'https://s3.amazonaws.com/bitcoinarmory-releases/'
      rparams['GPGKeyID']       = '98832223'
      rparams['BTCWltID']       = '2DTq89wvw'
   else:
      rparams['SignAddr']       = '1PpAJyNoocJt38Vcf4AfPffaxo76D4AAEe'
      rparams['AnnounceFile']   = 'testannounce.txt'
      rparams['BucketAnnounce'] = 'https://s3.amazonaws.com/bitcoinarmory-testing/'
      rparams['BucketReleases'] = 'https://s3.amazonaws.com/bitcoinarmory-testing/'
      rparams['GPGKeyID']       = 'FB596985'
      rparams['BTCWltID']       = '2XqAdZZ8B'

   return rparams



def getMasterPackageList():
   masterPkgList = {}
   m = masterPkgList
   
   pkg = 'Windows (All)'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['cp', '~/windows_share/armory_%s_win32.exe']
   m[pkg]['FileSuffix'] = 'winAll.exe'
   m[pkg]['OSNameDisp'] = 'Windows'
   m[pkg]['OSVarDisp']  = 'XP, Vista, 7, 8+'
   m[pkg]['OSArchDisp'] = '32- and 64-bit'
   m[pkg]['OSNameLink'] = 'Windows'
   m[pkg]['OSVarLink']  = 'XP,Vista,7,8,8.1'
   m[pkg]['OSArchLink'] = '32,64'
   m[pkg]['HasBundle']  = False
   
   pkg = 'MacOSX (All)'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['scp', 'joeschmoe', '192.168.1.22', 22, '~/BitcoinArmory/osxbuild/armory_%s_osx.tar.gz']
   m[pkg]['FileSuffix'] = 'osx.tar.gz'
   m[pkg]['OSNameDisp'] = 'MacOSX'
   m[pkg]['OSVarDisp']  = '10.7+'
   m[pkg]['OSArchDisp'] = '64bit'
   m[pkg]['OSNameLink'] = 'MacOSX'
   m[pkg]['OSVarLink']  = '10.7,10.8,10.9,10.9.1,10.9.2'
   m[pkg]['OSArchLink'] = '64''
   m[pkg]['HasBundle']  = False
   
   
   pkg = 'Ubuntu 12.04-32bit'
   m[pkg] = {}
   m[pkg]['FetchFrom']    = ['scp', 'guest', 'buildmachine1', 3822, '~/buildenv/armory_%s-1_i386.deb']
   m[pkg]['FileSuffix']   = 'ubuntu-32bit.deb'
   m[pkg]['OSNameDisp']   = 'Ubuntu'
   m[pkg]['OSVarDisp']    = '12.04+'
   m[pkg]['OSArchDisp']   = '32bit'
   m[pkg]['OSNameLink']   = 'Ubuntu'
   m[pkg]['OSVarLink']    = '12.04,12.10,13.04,13.10,14.04'
   m[pkg]['OSArchLink']   = '32'
   m[pkg]['HasBundle']    = True
   m[pkg]['BundleDeps']   = 'offline_deps_ubuntu32'
   m[pkg]['BundleSuffix'] = 'offline_ubuntu_12.04-32.tar.gz'
   m[pkg]['BundleOSVar']  = '12.04 exact'
   m[pkg]['BundleDLLVar'] = '12.04'
   
   
   pkg = 'Ubuntu 12.04-64bit'
   m[pkg] = {}
   m[pkg]['FetchFrom']    = ['scp', 'guest', '192.168.0.83', 1899, '~/buildenv/armory_%s-1_amd64_osx.deb']
   m[pkg]['FileSuffix']   = 'ubuntu-64bit.deb'
   m[pkg]['OSNameDisp']   = 'Ubuntu'
   m[pkg]['OSVarDisp']    = '12.04+'
   m[pkg]['OSArchDisp']   = '64bit'
   m[pkg]['OSNameLink']   = 'Ubuntu'
   m[pkg]['OSVarLink']    = '12.04,12.10,13.04,13.10,14.04'
   m[pkg]['OSArchLink']   = '64'
   m[pkg]['HasBundle']    = True
   m[pkg]['BundleDeps']   = 'offline_deps_ubuntu64'
   m[pkg]['BundleSuffix'] = 'offline_ubuntu_12.04-64.tar.gz'
   m[pkg]['BundleOSVar']  = '12.04 exact'
   m[pkg]['BundleDLLVar'] = '12.04'
   
   pkg = 'RaspberryPi'
   m[pkg] = {}
   m[pkg]['FetchFrom']    = ['cp', '~/buildenv/rpibuild/armory_%s-1.tar.gz']
   m[pkg]['FileSuffix']   = 'raspbian-armhf.tar.gz'
   m[pkg]['OSNameDisp']   = 'Raspbian'
   m[pkg]['OSVarDisp']    = None
   m[pkg]['OSArchDisp']   = 'armhf'
   m[pkg]['OSNameLink']   = 'RaspberryPi'
   m[pkg]['OSVarLink']    = None
   m[pkg]['OSArchLink']   = '32'
   m[pkg]['HasBundle']    = True
   m[pkg]['BundleDeps']   = 'offline_deps_raspbian'
   m[pkg]['BundleSuffix'] = 'rpi_bundle.tar.gz'
   m[pkg]['BundleOSVar']  = None
   m[pkg]['BundleDLLVar'] = 'Raspbian'


   return masterPkgList




