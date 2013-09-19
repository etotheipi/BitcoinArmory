

#ifndef WIN32EXPORTS_H_
#define WIN32EXPORTS_H_

#if defined LEVELDB_DLL
#define LEVELDB_EXPORT __declspec(dllimport)
#elif defined DLL_BUILD
#define LEVELDB_EXPORT __declspec(dllexport)
#else
#define LEVELDB_EXPORT 
#endif

#endif