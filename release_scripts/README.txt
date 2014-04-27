Build & Release Process for Armory

This directory contains a variety of scripts that will be used to compile,
bundle, sign, and upload new releases of Armory.  There are three scripts
because it is assumed that the signing keys are offline, requiring something
similar to an offline transaction:  create everything online, take offline
for signing, take online again to broadcast (upload to Amazon S3).


The following is assumed to have been done already before starting this 
process:

-- Local & remote machines and VMs have compiled & bundled installers
-- fetchlist.txt contains location data for each installer, specified by
   cp and scp commands
-- Each remote system has our public key in its authorized_keys file
-- Offline computer has GPG key & Armory wallet spec'd at top of Step2 script
-- All announce files are updated (except for dllinks which will be updated
   by the script itself once files are signed and hashes are known)
-- The Step2 script contains an accurate list of everything file/installer
-- The computer running Step3 has write-access to the git repo, and a 
   configuration file with API key for uploading results to Amazon S3
-- Directories on the offline computer containing dependencies for each 
   OS-specific offline-bundle
-- Already have an installed version of Armory offline in the /usr/lib/armory
   directory, to be used for creating signature blocks


The result of this process will be:

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

   Directory tree to be transferred to offlie computer:
   
      unsigned/BitcoinArmory       (clone of repo)
      unsigned/release_scripts     (copy of release_scripts dir from repo)
      unsigned/installers          (all non-offline-bundle packages)
      unsigned/announceFiles       (all unsigned announcement files)

Note the release_scripts dir is copied because we likely made modifications
to it to support the current release, and it wouldn't be in the cloned repo
yet.  After the release is successful, we commit the updated scripts as the
basis for the next release.  


-----
Step2 Script:

This script will be executed from the release_scripts directory above --
we will copy the directory to the offline computer, then cd into
the unsigned/release_scripts dir, then [modify if necessary and] run the 
Step2 script from there.  It does not depend on the cloned repo -- it adds
/usr/lib/armory to its python path, to use the currently installed version
of Armory for any non-generic-python operations.

When it's done, it should create a similar directory tree to take back
to the online computer:

      signed/BitcoinArmory      (now with signed git tag v0.XX-beta)
      signed/installers         (debs signed, bundles added, signed hash file)
      signed/announceFiles      (dllinks.txt updated, announce.txt created)



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



  







