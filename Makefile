# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

all :
	cd cppForSwig; make swig

clean :
	cd cppForSwig; make clean
