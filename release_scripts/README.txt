Build & Release Process for Armory

This directory contains a variety of scripts that will be used to compile,
bundle, sign, and upload new releases of Armory.  There are three scripts
because it is assumed that the signing keys are offline, requiring something
similar to an offline transaction:  create everything online, take offline
for signing, take online again to broadcast (upload to Amazon S3).


The following is assumed to have been done already before starting this 
process:

   - Local & remote machines and VMs have compiled & bundled installers
   - master_list.py file that returns nested dictionary of all release/installer
      information (see example at end of this doc)
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
      
   Script Output:

      <outputDir>/BitcoinArmory       (clone of repo)
      <outputDir>/release_scripts     (copy of release_scripts dir from repo)
      <outputDir>/installers          (all non-offline-bundle packages)
      <outputDir>/announceFiles       (all unsigned announcement files)
      <outputDir>/SHA256SUMS.asc      (if present)

Note the release_scripts dir is itself copied because it has master_list.py
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
         argv[3]   gpgKeyID
         argv[4]   btcWltID
         argv[5]*  git branch to tag (default ~ "master")
      
   Script Output:

      <outputDir>/BitcoinArmory       (same repo but with signed tag v0.91.1)
      <outputDir>/release_scripts     (same copy, unmodified)
      <outputDir>/installers          (now includes offline bundles)
      <outputDir>/announceFiles       (all txt signed, added announce.txt)




-----
Step 3 Script:

Will expect to find the three directories above with signed data.  It will
actually execute verification of all signatures, though you will have to
manually verify the output before continuing.  After that, it will attempt
to upload everything.

It expects to find the .s3cmd configuration file, already setup with your
S3 API key to be able to upload files to the BitoinArmory-releases bucket.
It will do the following:

      -- Upload all installers and offline bundles to BitcoinArmory-releases 
      -- Upload all announce files to BitcoinArmory-media bucket
      -- Ask if you'd like to push the latest git tag (if this is a testing
         version, you may not want to push the tag)


   Script Arguments (* is optional)
         argv[0]   <>
         argv[1]   inputDir  (from Step2)
         argv[5]*  git branch to tag (default ~ "master")
      
   Script Output:

      <outputDir>/BitcoinArmory       (same repo but with signed tag v0.91.1)
      <outputDir>/release_scripts     (same copy, unmodified)
      <outputDir>/installers          (now includes offline bundles)
      <outputDir>/announceFiles       (all txt signed, added announce.txt)

  






################################################################################
#                                                                              #
# Example master_list.py file                                                  #
#                                                                              #
################################################################################

#! /usr/bin/python
import os

def getMasterPackageList():
   masterPkgList = {}
   m = masterPkgList
   
   pkg = 'Windows (All)'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['cp', '~/windows_share/armory_%s_win32.exe']
   m[pkg]['FileSuffix'] = 'winAll.exe'
   m[pkg]['OSName']     = 'Windows'
   m[pkg]['OSVar']      = 'XP, Vista, 7, 8+'
   m[pkg]['OSArch']     = '32- and 64-bit'
   m[pkg]['HasBundle']  = False
   
   pkg = 'MacOSX (All)'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['scp', 'joeschmode', '192.168.1.22', 22, '~/BitcoinArmory/osxbuild/armory_%s_osx.tar.gz']
   m[pkg]['FileSuffix'] = 'osx.tar.gz'
   m[pkg]['OSName']     = 'MacOSX'
   m[pkg]['OSVar']      = '10.7+'
   m[pkg]['OSArch']     = '64bit'
   m[pkg]['HasBundle']  = False
   
   
   pkg = 'Ubuntu 12.04-32bit'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['scp', 'guest', '192.168.1.23', 5111, '~/buildenv/armory_%s-1_i386.deb']
   m[pkg]['FileSuffix'] = 'ubuntu-32bit.deb'
   m[pkg]['OSName']     = 'Ubuntu'
   m[pkg]['OSVar']      = '12.04+'
   m[pkg]['OSArch']     = '32bit'
   m[pkg]['HasBundle']  = True
   m[pkg]['BundleDeps'] = 'offline_deps_ubuntu32'
   m[pkg]['BndlSuffix'] = 'offline_ubuntu_12.0432.tar.gz'
   
   
   pkg = 'Ubuntu 12.04-64bit'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['scp', 'joe', '192.168.1.80', 5111, '~/buildenv/armory_%s-1_amd64_osx.deb']
   m[pkg]['FileSuffix'] = 'ubuntu-64bit.deb'
   m[pkg]['OSName']     = 'Ubuntu'
   m[pkg]['OSVar']      = '12.04+'
   m[pkg]['OSArch']     = '64bit'
   m[pkg]['HasBundle']  = True
   m[pkg]['BundleDeps'] = 'offline_deps_ubuntu64'
   m[pkg]['BndlSuffix'] = 'offline_ubuntu64.tar.gz'
   
   pkg = 'RaspberryPi'
   m[pkg] = {}
   m[pkg]['FetchFrom']  = ['cp', '~/buildenv/rpibuild/armory_%s-1.tar.gz']
   m[pkg]['FileSuffix'] = 'raspbian-armhf.tar.gz'
   m[pkg]['OSName']     = 'Raspbian'
   m[pkg]['OSVar']      = None
   m[pkg]['OSArch']     = 'armhf'
   m[pkg]['HasBundle']  = True
   m[pkg]['BundleDeps'] = 'offline_deps_raspbian'
   m[pkg]['BndlSuffix'] = 'rpi_bundle.tar.gz'


   return masterPkgList




