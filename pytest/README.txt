To run tests from the command line use "RunPyTest.py"

Examples:

> python RunPyTest.py

Runs all tests

> pyth RunPyTest.py PyTxTest MultiSigTest

Runs PyTxTest and MultiSigTest. Any number of module names can be added to the command line to include them in the run.

Note: All tests should extend pytest.TiabTest. To make sure pytest.TiabTest can be imported make sure your
test starts with these two lines:

import sys
sys.path.append('..')