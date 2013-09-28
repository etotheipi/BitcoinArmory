This file directory is maintained in the repo solely for snappy compression support.

The code itself doesn't require snappy, but the original port needed it in order to
compile on Windows in MSVS.  As soon as I figure out how to cut the umbilical cord,
I will remove the snappy project from the MSVS solution and remove this directory.