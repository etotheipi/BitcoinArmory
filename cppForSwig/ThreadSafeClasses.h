////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_ATOMICVECTOR_ 
#define _H_ATOMICVECTOR_

#include <atomic>
#include <memory>
#include <future>
#include <map>

#include "make_unique.h"

using namespace std;

class IsEmpty
{};

class StopBlockingLoop
{};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class Entry
{
private:
   T obj_;

public:
   Entry<T>* next_ = nullptr;

public:
   Entry<T>(const T& obj) :
      obj_(obj)
   {}

   Entry<T>(T&& obj) : 
      obj_(obj)
   {}

   T get(void)
   {
      return move(obj_);
   }
};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class AtomicEntry
{
private:
   T obj_;

public:
   atomic<AtomicEntry<T>*> next_;

public:
   AtomicEntry(const T& obj) :
      obj_(obj)
   {      
      next_.store(nullptr, memory_order_relaxed);
   }

   AtomicEntry(T&& obj)  :
      obj_(move(obj))
   {
      next_.store(nullptr, memory_order_relaxed);
   }

   T get(void)
   {
      return move(obj_);
   }
};

////////////////////////////////////////////////////////////////////////////////
template<typename T> class Pile
{
   /***
   lockless LIFO container class
   ***/
private:
   atomic<Entry<T>*> top_;

   atomic<size_t> count_;

public:
   Pile()
   {
      top_.store(nullptr, memory_order_relaxed);
      count_.store(0, memory_order_relaxed);
   }

   ~Pile()
   {
      clear();
   }

   T pop_back(void)
   {
      auto topentry = top_.load(memory_order_acquire);

      if (topentry == nullptr)
         throw IsEmpty();

      while (!top_.compare_exchange_weak(topentry, topentry->next_,
         memory_order_release, memory_order_relaxed));
      
      auto&& retval = topentry->get();
      delete topentry;

      count_.fetch_sub(1, memory_order_relaxed);

      return move(retval);
   }

   void push_back(const T& obj)
   {
      Entry<T>* nextentry = new Entry<T>(obj);
      nextentry->next_ = top_;

      while (!top_.compare_exchange_weak(nextentry->next_, nextentry,
         memory_order_release, memory_order_relaxed));

      count_.fetch_add(1, memory_order_relaxed);
   }

   void clear(void)
   {
      try
      {
         while (1)
            pop_back();
      }
      catch (IsEmpty&)
      {}

      count_.store(0, memory_order_relaxed);
   }

   size_t size(void) const
   {
      return count_.load(memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class Stack
{
   /***
   lockless FIFO container class
   ***/

private:
   atomic<AtomicEntry<T>*> top_;
   atomic<AtomicEntry<T>*> bottom_;

protected:
   atomic<size_t> count_;

public:
   Stack()
   {
      top_.store(nullptr, memory_order_relaxed);
      bottom_.store(nullptr, memory_order_relaxed);
      count_.store(0, memory_order_relaxed);
   }

   ~Stack()
   {
      clear();
   }

   T pop_front(void)
   {
      //throw if empty
      auto valptr = bottom_.load(memory_order_acquire);

      if (valptr == nullptr)
         throw IsEmpty();

      auto nextptr = valptr->next_.load(memory_order_acquire);

      //pop val
      while (!bottom_.compare_exchange_weak(valptr, nextptr,
         memory_order_release, memory_order_relaxed))
      {
         nextptr = valptr->next_.load(memory_order_acquire);
      }

      //set top_ to nullptr if bottom_ is null
      if (bottom_.load(memory_order_acquire) == nullptr)
      {
         auto prevbottom = valptr;
         top_.compare_exchange_strong(prevbottom, nullptr,
            memory_order_release, memory_order_relaxed);
      }

      //update count
      count_.fetch_sub(1, memory_order_relaxed);

      //delete ptr and return value
      auto&& retval = valptr->get();
      delete valptr;

      return move(retval);
   }

   virtual void push_back(T&& obj)
   {
      //create object
      AtomicEntry<T>* newentry = new AtomicEntry<T>(move(obj));
      AtomicEntry<T>* nullentry;

      {
         atomic<AtomicEntry<T>*>* nextptr;

         //loop as long as top_->next_ is not null, then set next_ to new entry
         while (1)
         {
            nullentry = nullptr;
            if (top_.compare_exchange_strong(nullentry, newentry,
               memory_order_release, memory_order_relaxed))
            {
               //top_ was empty and we just set it
               //set bottom_ as it has to be empty too
               bottom_.store(newentry, memory_order_release);
               break;
            }

            //TODO: fix top_ getting deleted after the load and before the 
            //compare_exchange
            nextptr = &nullentry->next_;
            nullentry = nullptr;
            if (nextptr->compare_exchange_weak(nullentry, newentry,
               memory_order_release, memory_order_relaxed))
               break;
         }

         //it's possible bottom_ was consumed before we got there, we
         //should test and set it
         nullentry = nullptr;
         bottom_.compare_exchange_strong(nullentry, newentry,
            memory_order_release, memory_order_relaxed);

         //top_ had an empty next_, we set it to newentry, we can now set top_
         //to newentry. Other threads are testing still testing next_ so only 
         //the one thread that set top_->next_ gets to store top_
         top_.store(newentry, memory_order_release);
      }

      //update count
      count_.fetch_add(1, memory_order_relaxed);
   }

   void clear()
   {
      //pop as long as possible
      try
      {
         while (1)
            pop_front();
      }
      catch (IsEmpty&)
      {
      }
   }
};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class BlockingStack : public Stack<T>
{
   /***
   get() blocks as long as the container is empty
   ***/

private:
   typedef shared_ptr<promise<bool>> promisePtr;
   Pile<promisePtr> promisePile_;
   atomic<int> waiting_;
   atomic<bool> terminate_;

public:
   BlockingStack() : Stack<T>()
   {
      terminate_.store(false, memory_order_relaxed);
      waiting_.store(0, memory_order_relaxed);
   }

   T get(void)
   {
      //blocks as long as there is no data available in the chain.

      //run in loop until we get data or a throw

      waiting_.fetch_add(1, memory_order_relaxed);

      try
      {
         while (1)
         {
            auto terminate = terminate_.load(memory_order_relaxed);
            if (terminate)
            {
               waiting_.fetch_sub(1, memory_order_relaxed);
               throw IsEmpty();
            }

            //try to pop_front
            try
            {
               auto&& retval = Stack<T>::pop_front();
               waiting_.fetch_sub(1, memory_order_relaxed);
               return move(retval);
            }
            catch (IsEmpty&)
            {}

            //if there are no items, create promise, push to promise pile
            auto haveItemPromise = make_shared<promise<bool>>();
            promisePile_.push_back(haveItemPromise);

            auto haveItemFuture = haveItemPromise->get_future();

            /***
            3 cases here:

            a) New object was pushed back to the chain after the promise was pushed
            to the promise pile. Future will be set.

            b) New object was pushed back before the promise was pushed to the promise
            pile. Promise won't be set.

            c) Nothing was pushed after the promise, just wait on future.

            a and c are covered by waiting on the future. To cover b, we need to try
            to pop_front once more first. If it fails, wait on future.

            In case of a, this approach (test a second time before waiting on future)
            wastes the promise, but that's only a slight overhead so it's an
            acceptable trade off.
            ***/

            try
            {
               auto&& retval = Stack<T>::pop_front();
               waiting_.fetch_sub(1, memory_order_relaxed);
               return retval;
            }
            catch (IsEmpty&)
            {
            }

            haveItemFuture.wait();
         }
      }
      catch (StopBlockingLoop&)
      {
         //loop stopped unexpectedly
         waiting_.fetch_sub(1, memory_order_relaxed);
         throw IsEmpty();
      }
   }

   void push_back(T&& obj)
   {
      Stack<T>::push_back(move(obj));

      //pop promises
      while (Stack<T>::count_.load(memory_order_relaxed) > 0)
      {
         try
         {
            auto&& p = promisePile_.pop_back();
            p->set_value(true);
         }
         catch (IsEmpty&)
         {
            break;
         }
      }
   }

   void terminate(void)
   {
      terminate_.store(true, memory_order_relaxed);

      while (waiting_.load(memory_order_relaxed) > 0)
      {
         try
         {
            auto&& p = promisePile_.pop_back();
            exception_ptr eptr;
            try
            {
               throw(StopBlockingLoop());
            }
            catch (...)
            {
               eptr = current_exception();
            }

            p->set_exception(eptr);
         }
         catch (IsEmpty&)
         {
         }
      }
   }

   void reset(void)
   {
      Stack<T>::clear();

      terminate_.store(false, memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
template<typename T, typename U> class TransactionalMap
{
   //locked writes, lockless reads
private:
   mutex mu_;
   shared_ptr<map<T, U>> map_;

public:

   TransactionalMap(void)
   {
      map_ = make_shared<map<T, U>>();
   }

   void insert(pair<T, U>&& mv)
   {
      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      newMap->insert(move(mv));
      map_ = newMap;
   }

   void insert(const pair<T, U>& obj)
   {
      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      newMap->insert(obj);
      map_ = newMap;
   }

   void erase(const T& id)
   {
      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      newMap->erase(id);
      map_ = newMap;
   }

   shared_ptr<map<T, U>> get(void) const
   {
      return map_;
   }
};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class TimedStack : public Stack<T>
{
   /***
   get() blocks as long as the container is empty
   ***/

private:
   typedef shared_ptr<promise<bool>> promisePtr;
   TransactionalMap<thread, promisePtr> promiseMap_;
   atomic<int> waiting_;
   atomic<bool> terminate_;

public:
   TimedStack() : Stack<T>()
   {
      terminate_.store(false, memory_order_relaxed);
      waiting_.store(0, memory_order_relaxed);
   }

   T get(std::chrono timetout = std::chrono::seconds(600))
   {
      //blocks as long as there is no data available in the chain.

      //run in loop until we get data or a throw

      waiting_.fetch_add(1, memory_order_relaxed);

      try
      {
         while (1)
         {
            auto terminate = terminate_.load(memory_order_relaxed);
            if (terminate)
            {
               waiting_.fetch_sub(1, memory_order_relaxed);
               throw IsEmpty();
            }

            //try to pop_front
            try
            {
               auto&& retval = Stack<T>::pop_front();
               waiting_.fetch_sub(1, memory_order_relaxed);
               return move(retval);
            }
            catch (IsEmpty&)
            {
            }

            //if there are no items, create promise, push to promise pile
            auto haveItemPromise = make_shared<promise<bool>>();
            promiseMap_.insert(this_thread::get_id(), haveItemPromise);

            auto haveItemFuture = haveItemPromise->get_future();

            /***
            3 cases here:

            a) New object was pushed back to the chain after the promise was pushed
            to the promise pile. Future will be set.

            b) New object was pushed back before the promise was pushed to the promise
            pile. Promise won't be set.

            c) Nothing was pushed after the promise, just wait on future.

            a and c are covered by waiting on the future. To cover b, we need to try
            to pop_front once more first. If it fails, wait on future.

            In case of a, this approach (test a second time before waiting on future)
            wastes the promise, but that's only a slight overhead so it's an
            acceptable trade off.
            ***/

            try
            {
               auto&& retval = Stack<T>::pop_front();
               waiting_.fetch_sub(1, memory_order_relaxed);
               return retval;
            }
            catch (IsEmpty&)
            {
            }

            haveItemFuture.wait();
         }
      }
      catch (StopBlockingLoop&)
      {
         //loop stopped unexpectedly
         waiting_.fetch_sub(1, memory_order_relaxed);
         throw IsEmpty();
      }
   }

   void push_back(T&& obj)
   {
      Stack<T>::push_back(move(obj));

      //pop promises
      while (Stack<T>::count_.load(memory_order_relaxed) > 0)
      {
         try
         {
            auto&& p = promisePile_.pop_back();
            p->set_value(true);
         }
         catch (IsEmpty&)
         {
            break;
         }
      }
   }

   void terminate(void)
   {
      terminate_.store(true, memory_order_relaxed);

      while (waiting_.load(memory_order_relaxed) > 0)
      {
         try
         {
            auto&& p = promisePile_.pop_back();
            exception_ptr eptr;
            try
            {
               throw(StopBlockingLoop());
            }
            catch (...)
            {
               eptr = current_exception();
            }

            p->set_exception(eptr);
         }
         catch (IsEmpty&)
         {
         }
      }
   }

   void reset(void)
   {
      Stack<T>::clear();

      terminate_.store(false, memory_order_relaxed);
   }
};

#endif
