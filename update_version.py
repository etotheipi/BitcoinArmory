import os

script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

if os.path.exists('.git') \
   and os.path.exists(os.path.join("armoryengine", "ArmoryUtils.py")):
    current_head = os.path.join(".git", "HEAD")
    f = open(current_head, "r")
    ref = f.read()
    f.close()
    path_parts = ref[5:-1].split("/")
    hash_loc = os.path.join(".git", *path_parts)
    f = open(hash_loc, "r")
    build = f.read()[:10]
    f.close()

    build_file = os.path.join("armoryengine", "ArmoryBuild.py")
    f = open(build_file, "w")
    f.write("BTCARMORY_BUILD = '%s'\n" % build)
    f.close()

    print "Build number has been updated to %s" % build

else:
    print "Please run this script from the root Armory source directory" \
        " along with the .git directory"

