

#ifndef STORAGE_LEVELDB_UTIL_ENV_WIN32_H_
#define STORAGE_LEVELDB_UTIL_ENV_WIN32_H_

#include <atlbase.h>
#include <atlconv.h>
#include <map>

#if defined DeleteFile
#undef DeleteFile
#endif

#include "leveldb/env.h"

//Declarations
namespace leveldb
{

namespace Win32
{

typedef ATL::CA2WEX<MAX_PATH> MultiByteToWChar;
typedef ATL::CW2AEX<MAX_PATH> WCharToMultiByte;
typedef ATL::CA2AEX<MAX_PATH> MultiByteToAnsi;

std::string GetCurrentDir();
std::wstring GetCurrentDirW();

static const std::string CurrentDir = GetCurrentDir();
static const std::wstring CurrentDirW = GetCurrentDirW();

std::string& ModifyPath(std::string& path);
std::wstring& ModifyPath(std::wstring& path);

std::string GetLastErrSz();
std::wstring GetLastErrSzW();

size_t GetPageSize();

typedef void (*ScheduleProc)(void*) ;

struct WorkItemWrapper
{
    WorkItemWrapper(ScheduleProc proc_,void* content_);
    ScheduleProc proc;
    void* pContent;
};

DWORD WINAPI WorkItemWrapperProc(LPVOID pContent);


}

class Win32SequentialFile : public SequentialFile
{
public:
    friend class Win32Env;
    virtual ~Win32SequentialFile();
    virtual Status Read(size_t n, Slice* result, char* scratch);
    virtual Status Skip(uint64_t n);
    BOOL isEnable();
private:
    BOOL _Init();
    void _CleanUp();
    Win32SequentialFile(const std::string& fname);
    std::string _filename;
    ::HANDLE _hFile;
    DISALLOW_COPY_AND_ASSIGN(Win32SequentialFile);
};

class Win32RandomAccessFile : public RandomAccessFile
{
public:
    friend class Win32Env;
    virtual ~Win32RandomAccessFile();
    virtual Status Read(uint64_t offset, size_t n, Slice* result,char* scratch) const;
    BOOL isEnable();
private:
    BOOL _Init(LPCWSTR path);
    void _CleanUp();
    Win32RandomAccessFile(const std::string& fname);
    HANDLE _hFile;
    const std::string _filename;
    DISALLOW_COPY_AND_ASSIGN(Win32RandomAccessFile);
};

class Win32MapFile : public WritableFile
{
public:
    Win32MapFile(const std::string& fname);

    ~Win32MapFile();
    virtual Status Append(const Slice& data);
    virtual Status Close();
    virtual Status Flush();
    virtual Status Sync();
    BOOL isEnable();
private:
    std::string _filename;
    HANDLE _hFile;
    size_t _page_size;
    size_t _map_size;       // How much extra memory to map at a time
    char* _base;            // The mapped region
    HANDLE _base_handle;	
    char* _limit;           // Limit of the mapped region
    char* _dst;             // Where to write next  (in range [base_,limit_])
    char* _last_sync;       // Where have we synced up to
    uint64_t _file_offset;  // Offset of base_ in file
    //LARGE_INTEGER file_offset_;
    // Have we done an munmap of unsynced data?
    bool _pending_sync;

    // Roundup x to a multiple of y
    static size_t _Roundup(size_t x, size_t y);
    size_t _TruncateToPageBoundary(size_t s);
    bool _UnmapCurrentRegion();
    bool _MapNewRegion();
    DISALLOW_COPY_AND_ASSIGN(Win32MapFile);
    BOOL _Init(LPCWSTR Path);
};

class Win32FileLock : public FileLock
{
public:
    friend class Win32Env;
    virtual ~Win32FileLock();
    BOOL isEnable();
private:
    BOOL _Init(LPCWSTR path);
    void _CleanUp();
    Win32FileLock(const std::string& fname);
    HANDLE _hFile;
    std::string _filename;
    DISALLOW_COPY_AND_ASSIGN(Win32FileLock);
};

class Win32Logger : public Logger
{
public: 
    friend class Win32Env;
    virtual ~Win32Logger();
    virtual void Logv(const char* format, va_list ap);
private:
    explicit Win32Logger(WritableFile* pFile);
    WritableFile* _pFileProxy;
    DISALLOW_COPY_AND_ASSIGN(Win32Logger);
};

class Win32Env : public Env
{
public:
    Win32Env();
    virtual ~Win32Env();
    virtual Status NewSequentialFile(const std::string& fname,
        SequentialFile** result);

    virtual Status NewRandomAccessFile(const std::string& fname,
        RandomAccessFile** result);
    virtual Status NewWritableFile(const std::string& fname,
        WritableFile** result);

    virtual bool FileExists(const std::string& fname);

    virtual Status GetChildren(const std::string& dir,
        std::vector<std::string>* result);

    virtual Status DeleteFile(const std::string& fname);

    virtual Status CreateDir(const std::string& dirname);

    virtual Status DeleteDir(const std::string& dirname);

    virtual Status GetFileSize(const std::string& fname, uint64_t* file_size);

    virtual Status RenameFile(const std::string& src,
        const std::string& target);

    virtual Status LockFile(const std::string& fname, FileLock** lock);

    virtual Status UnlockFile(FileLock* lock);

    virtual void Schedule(
        void (*function)(void* arg),
        void* arg);

    virtual void StartThread(void (*function)(void* arg), void* arg);

    virtual Status GetTestDirectory(std::string* path);

    //virtual void Logv(WritableFile* log, const char* format, va_list ap);

    virtual Status NewLogger(const std::string& fname, Logger** result);

    virtual uint64_t NowMicros();

    virtual void SleepForMicroseconds(int micros);
};

}

#endif