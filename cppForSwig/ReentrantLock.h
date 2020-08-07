////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_REENTRANT_LOCK
#define _H_REENTRANT_LOCK

using namespace std;

#include <thread>
#include <mutex>
#include <memory>
#include <string>

#include "make_unique.h"

class LockableException : public runtime_error
{
public:
   LockableException(const string& err) : runtime_error(err)
   {}
};

////////////////////////////////////////////////////////////////////////////////
class Lockable
{
   friend struct ReentrantLock;

protected:
   mutable mutex mu_;
   mutable thread::id mutexTID_;

public:
   virtual ~Lockable(void) = 0;
};

////////////////////////////////////////////////////////////////////////////////
struct ReentrantLock
{
   const Lockable* lockablePtr_;
   unique_ptr<unique_lock<mutex>> lock_;

   ReentrantLock(const Lockable* ptr) :
      lockablePtr_(ptr)
   {
      if (ptr == nullptr)
         throw LockableException("null lockable ptr");
      if (lockablePtr_->mutexTID_ != this_thread::get_id())
      {
         lock_ =
            make_unique<unique_lock<mutex>>(lockablePtr_->mu_, defer_lock);

         lock_->lock();
         lockablePtr_->mutexTID_ = this_thread::get_id();
      }
   }

   ~ReentrantLock(void)
   {
      if (lock_ == nullptr)
         return;

      if (lock_->owns_lock())
      {
         if (lockablePtr_ != nullptr)
            lockablePtr_->mutexTID_ = thread::id();
      }
   }
};


#endif
