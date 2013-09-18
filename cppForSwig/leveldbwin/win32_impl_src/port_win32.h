

#ifndef STORAGE_LEVELDB_PORT_PORT_WIN32_H_
#define STORAGE_LEVELDB_PORT_PORT_WIN32_H_

#ifndef OS_WIN
#define OS_WIN
#endif

#if defined _MSC_VER
#define COMPILER_MSVC
#endif

#include <sdkddkver.h>

#include "stdint.h"


#include <string>
#include <cstring>
#include <list>
#include "port/atomic_pointer.h"



typedef INT64 int64;

#ifdef min
#undef min
#endif

#ifdef small
#undef small
#endif

#define snprintf _snprintf
#define va_copy(a, b) do { (a) = (b); } while (0)

# if !defined(DISALLOW_COPY_AND_ASSIGN)
#  define DISALLOW_COPY_AND_ASSIGN(TypeName) \
    TypeName(const TypeName&); \
    void operator=(const TypeName&)
#endif 

#if defined _WIN32_WINNT_VISTA 
#define USE_VISTA_API
#endif

#pragma warning(disable:4996)
#pragma warning(disable:4018)
#pragma warning(disable:4355)
#pragma warning(disable:4244)
#pragma warning(disable:4800)
//#pragma warning(disable:4996)
    
namespace leveldb
{
namespace port
{
#if defined _M_IX86
    static const bool kLittleEndian = true;
#endif

class Event
{
public:
    Event(bool bSignal = true,bool ManualReset = false);
    ~Event();
    void Wait(DWORD Milliseconds = INFINITE);
    void Signal();
    void UnSignal();
private:
    HANDLE _hEvent;
    DISALLOW_COPY_AND_ASSIGN(Event);
};

class Mutex 
{
public:
    friend class CondVarNew;
    Mutex();
    ~Mutex();
    void Lock();
    void Unlock();
    BOOL TryLock();
    void AssertHeld();

private:
    CRITICAL_SECTION _cs;
    DISALLOW_COPY_AND_ASSIGN(Mutex);
};

class AutoLock
{
public:
    explicit AutoLock(Mutex& mu) : _mu(mu)
    {
        _mu.Lock();
    }
    ~AutoLock()
    {
        _mu.Unlock();
    }
private:
    Mutex& _mu;
    DISALLOW_COPY_AND_ASSIGN(AutoLock);
};

#ifndef Scoped_Lock_Protect
#define Scoped_Lock_Protect(mu) AutoLock __auto_lock__(mu)
#endif

class AutoUnlock
{
public:
    explicit AutoUnlock(Mutex& mu) : _mu(mu)
    {
        _mu.Unlock();
    }
    ~AutoUnlock()
    {
        _mu.Lock();
    }
private:
    Mutex& _mu;
    DISALLOW_COPY_AND_ASSIGN(AutoUnlock);
};

#ifndef Scoped_Unlock_Protect
#define Scoped_Unlock_Protect(mu) AutoUnlock __auto_unlock__(mu)
#endif

//this class come from project Chromium
class CondVarOld
{
public:
    // Construct a cv for use with ONLY one user lock.
    explicit CondVarOld(Mutex* mu);
    ~CondVarOld();
    // Wait() releases the caller's critical section atomically as it starts to
    // sleep, and the reacquires it when it is signaled.
    void Wait();
    void timedWait(DWORD dwMilliseconds);
    // Signal() revives one waiting thread.
    void Signal();
    // SignalAll() revives all waiting threads.
    void SignalAll();

private:
    class Event {
    public:
        // Default constructor with no arguments creates a list container.
        Event();
        ~Event();

        // InitListElement transitions an instance from a container, to an element.
        void InitListElement();

        // Methods for use on lists.
        bool IsEmpty() const;
        void PushBack(Event* other);
        Event* PopFront();
        Event* PopBack();

        // Methods for use on list elements.
        // Accessor method.
        HANDLE handle() const;
        // Pull an element from a list (if it's in one).
        Event* Extract();

        // Method for use on a list element or on a list.
        bool IsSingleton() const;

    private:
        // Provide pre/post conditions to validate correct manipulations.
        bool ValidateAsDistinct(Event* other) const;
        bool ValidateAsItem() const;
        bool ValidateAsList() const;
        bool ValidateLinks() const;

        HANDLE handle_;
        Event* next_;
        Event* prev_;
        DISALLOW_COPY_AND_ASSIGN(Event);
    };
    // Note that RUNNING is an unlikely number to have in RAM by accident.
    // This helps with defensive destructor coding in the face of user error.
    enum RunState { SHUTDOWN = 0, RUNNING = 64213 };

    // Internal implementation methods supporting Wait().
    Event* GetEventForWaiting();
    void RecycleEvent(Event* used_event);

    RunState run_state_;

    // Private critical section for access to member data.
    Mutex internal_lock_;

    // Lock that is acquired before calling Wait().
    Mutex& user_lock_;

    // Events that threads are blocked on.
    Event waiting_list_;

    // Free list for old events.
    Event recycling_list_;
    int recycling_list_size_;

    // The number of allocated, but not yet deleted events.
    int allocation_counter_;
    DISALLOW_COPY_AND_ASSIGN(CondVarOld);
};

#if defined USE_VISTA_API

class CondVarNew
{
public:
    explicit CondVarNew(Mutex* mu);
    ~CondVarNew();
    void Wait();
    void Signal();
    void SignalAll();
private:
    CONDITION_VARIABLE _cv;
    Mutex* _mu;
};

typedef CondVarNew CondVar;
#else
typedef CondVarOld CondVar;
#endif

bool Snappy_Compress(const char* input, size_t length,std::string* output);

bool Snappy_GetUncompressedLength(const char* input, size_t length,size_t* result);

bool Snappy_Uncompress(const char* input, size_t length,char* output);

inline bool GetHeapProfile(void (*func)(void*, const char*, int), void* arg) {
    return false;
}

}
}

#endif