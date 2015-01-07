from subprocess import check_output, CalledProcessError

import os


try:
    # check if the build file exists
    build_file = os.path.join("armoryengine", "ArmoryBuild.py")
    if os.path.exists('ArmoryQt.py') \
       and os.path.exists(os.path.join("armoryengine", "ArmoryUtils.py")):
        build = check_output(["git", "rev-parse", "HEAD"])[:10]
        f = open(build_file, "w")
        f.write("BTCARMORY_BUILD = '%s'\n" % build)
        f.close()
        print "Build number has been updated to %s" % build
    else:
        print "Please run this script from the root Armory source directory"
except CalledProcessError:
    print "\nPlease update the build version when using the git source tree"

