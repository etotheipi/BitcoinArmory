COMPILER = g++ 
#COMPILER_OPTS = -c -g -Wall
COMPILER_OPTS = -c -march=native -O2 -pipe


LINKER = g++ 
OBJS = blockUtils.o

INCLUDE_OPTS += -Icryptopp
LIBRARY_OPTS += -Lcryptopp -lcryptopp

INCLUDE_OPTS += 
LIBRARY_OPTS += 

all :
	make blockUtilsTest.out
	

blockUtilsTest.out : $(OBJS)
	$(LINKER) $(OBJS) -o blockUtilsTest.out $(INCLUDE_OPTS) $(LIBRARY_OPTS) blockUtilsTest.cpp


#**************************************************************************
# Rules for performing the compilation of each individual object file.

blockUtils.o: blockUtils.h  binaryData.h blockUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) blockUtils.cpp


##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************


clean:
	-rm *.o *.out 


