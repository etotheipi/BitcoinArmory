//Defines path translation for unicode support. Currently only active in Windows

#ifndef _MSC_VER
	#define OS_TranslatePath(X) X
#else
	#include <Win_TranslatePath.h>
	#define OS_TranslatePath Win_TranslatePath
#endif
