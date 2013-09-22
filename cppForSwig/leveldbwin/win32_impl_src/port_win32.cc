
#include "port_win32.h"

#include <stack>
#include <cassert>
#include <algorithm>

#include "snappy.h"
#define USE_SNAPPY

namespace leveldb
{

namespace port
{

Event::Event( bool bSignal,bool ManualReset ) : _hEvent(NULL)
{
    _hEvent = ::CreateEvent(NULL,ManualReset,bSignal,NULL);
}

Event::~Event()
{
    Signal();
    CloseHandle(_hEvent);
}

void Event::Wait(DWORD Milliseconds /*= INFINITE*/ )
{
    WaitForSingleObject(_hEvent,Milliseconds);
}

void Event::Signal()
{
    SetEvent(_hEvent);
}

void Event::UnSignal()
{
    ResetEvent(_hEvent);
}

Mutex::Mutex()
{
    InitializeCriticalSection(&_cs);
}

Mutex::~Mutex()
{
    DeleteCriticalSection(&_cs);
}

void Mutex::Lock()
{
    EnterCriticalSection(&_cs);
}

void Mutex::Unlock()
{
    LeaveCriticalSection(&_cs);
}

void Mutex::AssertHeld()
{
    assert( _cs.OwningThread == reinterpret_cast<HANDLE>(GetCurrentThreadId() ) );
        
}

BOOL Mutex::TryLock()
{
    return TryEnterCriticalSection(&_cs);
}

CondVarOld::CondVarOld(Mutex* mu)
    : user_lock_(*mu),
      run_state_(RUNNING),
      allocation_counter_(0),
      recycling_list_size_(0)
{

}

CondVarOld::~CondVarOld()
{
    Scoped_Lock_Protect(internal_lock_);
    run_state_ = SHUTDOWN; // Prevent any more waiting.
    if(recycling_list_size_ != allocation_counter_){
        // Rare shutdown problem.
        // There are threads of execution still in this->TimedWait() and yet the
        // caller has instigated the destruction of this instance :-/.
        // A common reason for such "overly hasty" destruction is that the caller
        // was not willing to wait for all the threads to terminate.  Such hasty
        // actions are a violation of our usage contract, but we'll give the
        // waiting thread(s) one last chance to exit gracefully (prior to our
        // destruction).
        // Note: waiting_list_ *might* be empty, but recycling is still pending.
        Scoped_Unlock_Protect(internal_lock_);
        SignalAll(); // Make sure all waiting threads have been signaled.
        Sleep(10); // Give threads a chance to grab internal_lock_.
        // All contained threads should be blocked on user_lock_ by now :-).
    } // Reacquire internal_lock_.
    assert(recycling_list_size_ == allocation_counter_);
}

void CondVarOld::Wait()
{
    timedWait(INFINITE);
}

void CondVarOld::timedWait(DWORD dwMilliseconds)
{
    Event* waiting_event;
    HANDLE handle;
    {
        Scoped_Lock_Protect(internal_lock_);
        if (RUNNING != run_state_) return;  // Destruction in progress.
        waiting_event = GetEventForWaiting();
        handle = waiting_event->handle();
    }  // Release internal_lock.

    {
        Scoped_Unlock_Protect(user_lock_);  // Release caller's lock
        WaitForSingleObject(handle, dwMilliseconds);
        // Minimize spurious signal creation window by recycling asap.
        Scoped_Lock_Protect(internal_lock_);
        RecycleEvent(waiting_event);
        // Release internal_lock_
    }  // Reacquire callers lock to depth at entry.
}

// Broadcast() is guaranteed to signal all threads that were waiting (i.e., had
// a cv_event internally allocated for them) before Broadcast() was called.
void CondVarOld::SignalAll()
{
    std::stack<HANDLE> handles;  // See FAQ-question-10.
    {
        Scoped_Lock_Protect(internal_lock_);
        if (waiting_list_.IsEmpty())
            return;
        while (!waiting_list_.IsEmpty())
            // This is not a leak from waiting_list_.  See FAQ-question 12.
            handles.push(waiting_list_.PopBack()->handle());
    }  // Release internal_lock_.
    while (!handles.empty()) {
        SetEvent(handles.top());
        handles.pop();
    }
}

// Signal() will select one of the waiting threads, and signal it (signal its
// cv_event).  For better performance we signal the thread that went to sleep
// most recently (LIFO).  If we want fairness, then we wake the thread that has
// been sleeping the longest (FIFO).
void CondVarOld::Signal() {
    HANDLE handle;
    {
        Scoped_Lock_Protect(internal_lock_);
        if (waiting_list_.IsEmpty())
            return;  // No one to signal.
        // Only performance option should be used.
        // This is not a leak from waiting_list.  See FAQ-question 12.
        handle = waiting_list_.PopBack()->handle();  // LIFO.
    }  // Release internal_lock_.
    SetEvent(handle);
}

// GetEventForWaiting() provides a unique cv_event for any caller that needs to
// wait.  This means that (worst case) we may over time create as many cv_event
// objects as there are threads simultaneously using this instance's Wait()
// functionality.
CondVarOld::Event* CondVarOld::GetEventForWaiting() {
    // We hold internal_lock, courtesy of Wait().
    Event* cv_event;
    if (0 == recycling_list_size_) {
        assert( recycling_list_.IsEmpty() );
        cv_event = new Event();
        cv_event->InitListElement();
        allocation_counter_++;
        assert( cv_event->handle() );
    } else {
        cv_event = recycling_list_.PopFront();
        recycling_list_size_--;
    }
    waiting_list_.PushBack(cv_event);
    return cv_event;
}

// RecycleEvent() takes a cv_event that was previously used for Wait()ing, and
// recycles it for use in future Wait() calls for this or other threads.
// Note that there is a tiny chance that the cv_event is still signaled when we
// obtain it, and that can cause spurious signals (if/when we re-use the
// cv_event), but such is quite rare (see FAQ-question-5).
void CondVarOld::RecycleEvent(Event* used_event) {
    // We hold internal_lock, courtesy of Wait().
    // If the cv_event timed out, then it is necessary to remove it from
    // waiting_list_.  If it was selected by Broadcast() or Signal(), then it is
    // already gone.
    used_event->Extract();  // Possibly redundant
    recycling_list_.PushBack(used_event);
    recycling_list_size_++;
}

CondVarOld::Event::Event() : handle_(0) {
    next_ = prev_ = this;  // Self referencing circular.
}

CondVarOld::Event::~Event() {
    if (0 == handle_) {
        // This is the list holder
        while (!IsEmpty()) {
            Event* cv_event = PopFront();
            assert ( cv_event->ValidateAsItem() );
            delete cv_event;
        }
    }
    assert ( IsSingleton());
    if (0 != handle_) {
        int ret_val = CloseHandle(handle_);
    }
}

// Change a container instance permanently into an element of a list.
void CondVarOld::Event::InitListElement() {
    assert (!handle_);
    handle_ = CreateEvent(NULL, false, false, NULL);
    assert ( handle_);
}

// Methods for use on lists.
bool CondVarOld::Event::IsEmpty() const {
    assert(ValidateAsList());
    return IsSingleton();
}

void CondVarOld::Event::PushBack(Event* other) {
    assert(ValidateAsList());
    assert(other->ValidateAsItem());
    assert(other->IsSingleton());
    // Prepare other for insertion.
    other->prev_ = prev_;
    other->next_ = this;
    // Cut into list.
    prev_->next_ = other;
    prev_ = other;
    assert( ValidateAsDistinct(other));
}

CondVarOld::Event* CondVarOld::Event::PopFront() {
    assert(ValidateAsList());
    assert(!IsSingleton());
    return next_->Extract();
}

CondVarOld::Event* CondVarOld::Event::PopBack() {
    assert(ValidateAsList());
    assert(!IsSingleton());
    return prev_->Extract();
}

// Methods for use on list elements.
// Accessor method.
HANDLE CondVarOld::Event::handle() const {
    assert( ValidateAsItem());
    return handle_;
}

// Pull an element from a list (if it's in one).
CondVarOld::Event* CondVarOld::Event::Extract() {
    assert( ValidateAsItem());
    if (!IsSingleton()) {
        // Stitch neighbors together.
        next_->prev_ = prev_;
        prev_->next_ = next_;
        // Make extractee into a singleton.
        prev_ = next_ = this;
    }
    assert(IsSingleton());
    return this;
}

// Method for use on a list element or on a list.
bool CondVarOld::Event::IsSingleton() const {
    assert( ValidateLinks() );
    return next_ == this;
}

// Provide pre/post conditions to validate correct manipulations.
bool CondVarOld::Event::ValidateAsDistinct(Event* other) const {
    return ValidateLinks() && other->ValidateLinks() && (this != other);
}

bool CondVarOld::Event::ValidateAsItem() const {
    return (0 != handle_) && ValidateLinks();
}

bool CondVarOld::Event::ValidateAsList() const {
    return (0 == handle_) && ValidateLinks();
}

bool CondVarOld::Event::ValidateLinks() const {
    // Make sure both of our neighbors have links that point back to us.
    // We don't do the O(n) check and traverse the whole loop, and instead only
    // do a local check to (and returning from) our immediate neighbors.
    return (next_->prev_ == this) && (prev_->next_ == this);
}



#if defined USE_VISTA_API

CondVarNew::CondVarNew( Mutex* mu ) : _mu(mu)
{
    InitializeConditionVariable(&_cv);
}

CondVarNew::~CondVarNew()
{
    WakeAllConditionVariable(&_cv);
}

void CondVarNew::Wait()
{
    SleepConditionVariableCS(&_cv,&_mu->_cs,INFINITE);
}

void CondVarNew::Signal()
{
    WakeConditionVariable(&_cv);
}

void CondVarNew::SignalAll()
{
    WakeAllConditionVariable(&_cv);
}

#endif

bool Snappy_Compress(const char* input, size_t length,std::string* output)
{
#if defined USE_SNAPPY
    output->resize(snappy::MaxCompressedLength(length));
    size_t outlen;
    snappy::RawCompress(input, length, &(*output)[0], &outlen);
    output->resize(outlen);
    return true;
#endif
    return false;
}

bool Snappy_GetUncompressedLength(const char* input, size_t length,size_t* result)
{
#ifdef USE_SNAPPY
    return snappy::GetUncompressedLength(input, length, result);
#else
    return false;
#endif
}

bool Snappy_Uncompress(const char* input, size_t length,char* output)
{
#ifdef USE_SNAPPY
    return snappy::RawUncompress(input, length, output);
#else
    return false;
#endif
}

}


}