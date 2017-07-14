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
#include <vector>
#include <map>
#include <set>
#include <chrono>
#include <thread>
#include <exception>
#include <iostream>

#include "make_unique.h"

using namespace std;

class IsEmpty
{};

class StopBlockingLoop
{};

struct StackTimedOutException
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
   atomic<AtomicEntry<T>*> top_;
   AtomicEntry<T>* maxptr_;

   atomic<size_t> count_;

public:
   Pile()
   {
      maxptr_ = (AtomicEntry<T>*)SIZE_MAX;
      top_.store(nullptr, memory_order_relaxed);
      count_.store(0, memory_order_relaxed);
   }

   ~Pile()
   {
      clear();
   }

   void push_back(const T& obj)
   {
      AtomicEntry<T>* nextentry = new AtomicEntry<T>(obj);
      nextentry->next_.store(maxptr_, memory_order_release);

      auto topentry = top_.load(memory_order_acquire);
      do
      {
         while (topentry == maxptr_)
            topentry = top_.load(memory_order_acquire);
      }
      while (!top_.compare_exchange_weak(topentry, nextentry,
         memory_order_release, memory_order_relaxed));

      nextentry->next_.store(topentry, memory_order_release);

      count_.fetch_add(1, memory_order_relaxed);
   }
  
   T pop_back(void)
   {
      AtomicEntry<T>* topentry = top_.load(memory_order_acquire);

      do
      {
         //1: make sure the value we got out of top_ is not the marker 
         //invalid value, otherwise keep load top_
         while (topentry == maxptr_)
            topentry = top_.load(memory_order_acquire);

         //2: with a valid topentry, try to compare_exchange top_ for
         //the invalid value
      } 
      while (!top_.compare_exchange_weak(topentry, maxptr_,
         memory_order_release, memory_order_relaxed));

      //3: if topentry is empty, the container is emtpy, throw
      if (topentry == nullptr)
      {
         //make sure the replace the marker value with nullptr in top_
         top_.store(nullptr, memory_order_release);
         throw IsEmpty();
      }

      /*4: if we got this far we guarantee 2 things:
      - topentry is neither null nor the invalid marker
      - topentry has yet to be derefenced in any thread, in other 
        words it is safe to read and delete in this particular thread
      - top_ is set to the invalid marker so we have to set it
        before other threads can get this far
      */ 

      while (topentry->next_.load(memory_order_acquire) == maxptr_);
      top_.store(topentry->next_, memory_order_release);

      auto&& retval = topentry->get();

      count_.fetch_sub(1, memory_order_relaxed);

      delete topentry;
      return move(retval);
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

   size_t count(void) const
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
   AtomicEntry<T>* maxptr_;

protected:
   atomic<size_t> count_;
   exception_ptr exceptPtr_ = nullptr;

   atomic<void*> promPtr_;
   atomic<void*> futPtr_;

   atomic<int> replaceFut_;

protected:
   virtual shared_future<bool> get_future()
   {
      int val = -1, val1;

      do
      {
         while (val == -1)
            val = replaceFut_.load(memory_order_acquire);

         val1 = val + 1;
      } while (!replaceFut_.compare_exchange_weak(val, val1,
         memory_order_release, memory_order_relaxed));

      auto futptr = futPtr_.load(memory_order_acquire);
      auto fut = *(shared_future<bool>*)futptr;

      replaceFut_.fetch_sub(1, memory_order_acq_rel);
      return fut;
   }

   void pop_promise(void)
   {
      int zero = 0;
      while (!replaceFut_.compare_exchange_weak(zero, -1,
         memory_order_release, memory_order_relaxed))
      {
         if (zero == -1)
            return;

         zero = 0;
      }

      auto oldprom = (promise<bool>*)promPtr_.load(memory_order_acquire);
      oldprom->set_value(true);

      auto newprom = new promise<bool>();
      promPtr_.store((void*)newprom, memory_order_release);

      auto newfut = new shared_future<bool>();
      shared_future<bool> fut = newprom->get_future();
      *newfut = fut;

      auto futval =
         (shared_future<bool>*)futPtr_.load(memory_order_acquire);
      futPtr_.store((void*)newfut, memory_order_release);

      delete futval;
      delete oldprom;

      replaceFut_.store(0, memory_order_release);
   }

public:
   Stack()
   {
      maxptr_ = (AtomicEntry<T>*)SIZE_MAX;
      top_.store(nullptr, memory_order_relaxed);
      bottom_.store(nullptr, memory_order_relaxed);
      count_.store(0, memory_order_relaxed);

      auto newprom = new promise<bool>();
      promPtr_.store((void*)newprom, memory_order_release);

      auto futptr = new shared_future<bool>();
      *futptr = newprom->get_future();
      futPtr_.store((void*)futptr, memory_order_release);

      replaceFut_.store(0, memory_order_release);
   }

   ~Stack()
   {
      clear();

      auto futptr = (shared_future<bool>*)futPtr_.load();
      auto promptr = (promise<bool>*)promPtr_.load();

      delete futptr;
      delete promptr;
   }

   virtual T pop_front(bool rethrow = true)
   {
      //throw if empty
      auto valptr = bottom_.load(memory_order_acquire);

      do
      {
         while (valptr == maxptr_)
            valptr = bottom_.load(memory_order_acquire);

         if (valptr == nullptr)
         {
            /*if (this->count() != 0)
               cout << "~~~ count != 0" << endl;*/
            throw IsEmpty();
         }
      } 
      while (!bottom_.compare_exchange_weak(valptr, maxptr_,
      memory_order_acq_rel, memory_order_acquire));

      auto valptrcopy = valptr;
      if (!top_.compare_exchange_strong(valptrcopy, maxptr_,
         memory_order_acq_rel, memory_order_acquire))
      {
         AtomicEntry<T>* nextptr;
         do
         {
            nextptr = valptr->next_.load(memory_order_acquire);
         } while (nextptr == maxptr_);
      
         count_.fetch_sub(1, memory_order_acq_rel);
         bottom_.store(nextptr, memory_order_release);
      }
      else
      {
         count_.fetch_sub(1, memory_order_acq_rel);
         bottom_.store(nullptr, memory_order_release);
         top_.store(nullptr, memory_order_release);
      }

      //delete ptr and return value
      auto&& retval = valptr->get();
      delete valptr;

      if (rethrow && exceptPtr_ != nullptr)
         rethrow_exception(exceptPtr_);

      return move(retval);
   }

   virtual void push_back(T&& obj)
   {
      //create object
      AtomicEntry<T>* newentry = new AtomicEntry<T>(move(obj));
      newentry->next_.store(maxptr_, memory_order_release);

      AtomicEntry<T>* nullentry = nullptr;

      auto topentry = top_.load(memory_order_acquire);

      do
      {
         while (topentry == maxptr_)
            topentry = top_.load(memory_order_acquire);
      } 
      while (!top_.compare_exchange_weak(topentry, maxptr_,
      memory_order_acq_rel, memory_order_acquire));

      if (topentry != nullptr)
         topentry->next_.store(newentry, memory_order_release);

      bottom_.compare_exchange_strong(nullentry, newentry,
         memory_order_acq_rel, memory_order_acquire);

      count_.fetch_add(1, memory_order_acq_rel);
      top_.store(newentry, memory_order_release);
   }

   virtual void clear()
   {
      //pop as long as possible
      try
      {
         while (1)
            pop_front(false);
      }
      catch (IsEmpty&)
      {
      }

      exceptPtr_ = nullptr;
   }

   size_t count(void) const
   {
      return count_.load(memory_order_acquire);
   }
};

////////////////////////////////////////////////////////////////////////////////
template<typename T, typename U> class TransactionalMap
{
   //locked writes, lockless reads
private:
   mutable mutex mu_;
   shared_ptr<map<T, U>> map_;
   atomic<size_t> count_;

public:

   TransactionalMap(void)
   {
      count_.store(0, memory_order_relaxed);
      map_ = make_shared<map<T, U>>();
   }

   void insert(pair<T, U>&& mv)
   {
      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      newMap->insert(move(mv));
      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);
   }

   void insert(const pair<T, U>& obj)
   {
      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      newMap->insert(obj);
      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);
   }

   void update(map<T, U> updatemap)
   {
      if (updatemap.size() == 0)
         return;

      auto newMap = make_shared<map<T, U>>( move(updatemap));

      unique_lock<mutex> lock(mu_);
      newMap->insert(map_->begin(), map_->end());

      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);
   }

   void erase(const T& id)
   {
      unique_lock<mutex> lock(mu_);

      auto iter = map_->find(id);
      if (iter == map_->end())
         return;

      auto newMap = make_shared<map<T, U>>();
      *newMap = *map_;

      newMap->erase(id);
      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);
   }

   void erase(const vector<T>& idVec)
   {
      if (idVec.size() == 0)
         return;

      auto newMap = make_shared<map<T, U>>();

      unique_lock<mutex> lock(mu_);
      *newMap = *map_;

      bool erased = false;
      for (auto& id : idVec)
      {
         if (newMap->erase(id) != 0)
            erased = true;
      }

      if (erased)
         map_ = newMap;

      count_.store(map_->size(), memory_order_relaxed);
   }

   shared_ptr<map<T, U>> pop_all(void)
   {
      auto newMap = make_shared<map<T, U>>();
      unique_lock<mutex> lock(mu_);
      
      auto retMap = map_;
      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);

      return retMap;
   }

   shared_ptr<map<T, U>> get(void) const
   {
      unique_lock<mutex> lock(mu_);
      return map_;
   }

   void clear(void)
   {
      auto newMap = make_shared<map<T, U>>();
      unique_lock<mutex> lock(mu_);

      map_ = newMap;
      count_.store(map_->size(), memory_order_relaxed);
   }

   size_t size(void) const
   {
      return count_.load(memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
template<typename T> class TransactionalSet
{
   //locked writes, lockless reads
private:
   mutable mutex mu_;
   shared_ptr<set<T>> set_;
   atomic<size_t> count_;

public:

   TransactionalSet(void)
   {
      count_.store(0, memory_order_relaxed);
      set_ = make_shared<set<T>>();
   }

   void insert(T&& mv)
   {
      auto newSet = make_shared<set<T>>();

      unique_lock<mutex> lock(mu_);
      *newSet = *set_;

      newSet->insert(move(mv));
      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   void insert(const T& obj)
   {
      auto newSet = make_shared<set<T>>();

      unique_lock<mutex> lock(mu_);
      *newSet = *set_;

      newSet->insert(obj);
      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   void insert(const set<T>& dataSet)
   {
      if (dataSet.size() == 0)
         return;

      auto newSet = make_shared<set<T>>();

      unique_lock<mutex> lock(mu_);
      *newSet = *set_;

      newSet->insert(dataSet.begin(), dataSet.end());
      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   void erase(const T& id)
   {
      unique_lock<mutex> lock(mu_);
      
      auto iter = set_->find(id);
      if (iter == set_->end())
         return;

      auto newSet = make_shared<set<T>>();
      *newSet = *set_;

      newSet->erase(id);
      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   void erase(const vector<T>& idVec)
   {
      if (idVec.size() == 0)
         return;

      auto newSet = make_shared<set<T>>();

      unique_lock<mutex> lock(mu_);
      *newSet = *set_;

      bool erased = false;
      for (auto& id : idVec)
      {
         if (newSet->erase(id) != 0)
            erased = true;
      }

      if (erased)
         set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   shared_ptr<set<T>> pop_all(void)
   {
      auto newSet = make_shared<set<T>>();
      unique_lock<mutex> lock(mu_);

      auto retSet = set_;
      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);

      return retSet;
   }

   shared_ptr<set<T>> get(void) const
   {
      unique_lock<mutex> lock(mu_);
      return set_;
   }

   void clear(void)
   {
      auto newSet = make_shared<set<T>>();
      unique_lock<mutex> lock(mu_);

      set_ = newSet;
      count_.store(set_->size(), memory_order_relaxed);
   }

   size_t size(void) const
   {
      return count_.load(memory_order_relaxed);
   }
};


////////////////////////////////////////////////////////////////////////////////
template <typename T> class TimedStack : public Stack<T>
{
   /***
   get() blocks as long as the container is empty
   ***/

private:
   atomic<int> waiting_;
   atomic<bool> terminate_;

public:
   TimedStack() : Stack<T>()
   {
      terminate_.store(false, memory_order_relaxed);
      waiting_.store(0, memory_order_relaxed);
   }

   T pop_front(chrono::milliseconds timeout = chrono::milliseconds(600000))
   {
      //block until timeout expires or data is available
      //return data or throw IsEmpty or StackTimedOutException

      waiting_.fetch_add(1, memory_order_relaxed);
      try
      {
         while (1)
         {
            auto terminate = terminate_.load(memory_order_relaxed);
            if (terminate)
               throw StopBlockingLoop();

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
            auto fut = Stack<T>::get_future();

            //try to grab data one more time before waiting on future
            try
            {
               auto&& retval = Stack<T>::pop_front();
               waiting_.fetch_sub(1, memory_order_relaxed);
               return move(retval);
            }
            catch (IsEmpty&)
            {
            }

            //TODO: figure out time left if we break before the timeout
            //but reenter the loop
            
            auto before = chrono::high_resolution_clock::now();
            auto status = fut.wait_for(timeout);

            if (status == future_status::timeout) //future timed out
               throw StackTimedOutException();

            auto after = chrono::high_resolution_clock::now();
            auto timediff = chrono::duration_cast<chrono::milliseconds>(after - before);
            if (timediff <= timeout)
               timeout -= timediff;
            else
               timeout = chrono::milliseconds(0);
         }
      }
      catch (...)
      {
         //loop stopped unexpectedly
         waiting_.fetch_sub(1, memory_order_relaxed);
         rethrow_exception(current_exception());
      }

      return T();
   }

   vector<T> pop_all(chrono::seconds timeout = chrono::seconds(600))
   {
      vector<T> vecT;

      vecT.push_back(move(pop_front(timeout)));
      
      try
      {
         while (1)
            vecT.push_back(move(Stack<T>::pop_front()));
      }
      catch (IsEmpty&)
      {}

      return move(vecT);
   }

   void push_back(T&& obj)
   {
      Stack<T>::push_back(move(obj));

      //pop promises
      if (waiting_.load(memory_order_relaxed) > 0)
         Stack<T>::pop_promise();
   }

   void terminate(exception_ptr exceptptr = nullptr)
   {
      if (exceptptr == nullptr)
      {
         try
         {
            throw(StopBlockingLoop());
         }
         catch (...)
         {
            exceptptr = current_exception();
         }
      }

      Stack<T>::exceptPtr_ = exceptptr;

      terminate_.store(true, memory_order_relaxed);
      while (waiting_.load(memory_order_relaxed) > 0)
         Stack<T>::pop_promise();
   }

   void reset(void)
   {
      Stack<T>::clear();

      terminate_.store(false, memory_order_relaxed);
   }

   bool isValid(void) const
   {
      auto val = terminate_.load(memory_order_relaxed);
      return !val;
   }

   int waiting(void) const
   {
      return waiting_.load(memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
template <typename T> class BlockingStack : public Stack<T>
{
   /***
   get() blocks as long as the container is empty

   terminate() halts all operations and returns on all waiting threads
   completed() lets the container serve it's remaining entries before halting
   ***/

private:
   atomic<int> waiting_;
   atomic<bool> terminated_;
   atomic<bool> completed_;
   
private:
   shared_future<bool> get_future()
   {
      auto completed = completed_.load(memory_order_acquire);
      if (completed)
      {
         if (Stack<T>::exceptPtr_ != nullptr)
            rethrow_exception(Stack<T>::exceptPtr_);
         else
            throw StopBlockingLoop();
      }

      return move(Stack<T>::get_future());
   }

public:
   BlockingStack() : Stack<T>()
   {
      terminated_.store(false, memory_order_relaxed);
      completed_.store(false, memory_order_relaxed);
      waiting_.store(0, memory_order_relaxed);
   }

   T pop_front(void)
   {
      //blocks as long as there is no data available in the chain.
      //run in loop until we get data or a throw

      waiting_.fetch_add(1, memory_order_acq_rel);

      try
      {
         while (1)
         {
            auto terminate = terminated_.load(memory_order_acquire);
            if (terminate)
            {
               if (Stack<T>::exceptPtr_ != nullptr)
                  rethrow_exception(Stack<T>::exceptPtr_);

               throw StopBlockingLoop();
            }

            //try to pop_front
            try
            {
               auto&& retval = Stack<T>::pop_front(false);
               waiting_.fetch_sub(1, memory_order_acq_rel);
               return move(retval);
            }
            catch (IsEmpty&)
            {}

            //if there are no items, create promise, push to promise pile
            auto fut = get_future();

            try
            {
               auto&& retval = Stack<T>::pop_front(false);
               waiting_.fetch_sub(1, memory_order_acq_rel);
               return move(retval);
            }
            catch (IsEmpty&)
            {
               if(completed_.load(memory_order_acquire) || 
                  terminated_.load(memory_order_acquire))
	            throw StopBlockingLoop();
            }

            try
            {
               fut.get();
            }
            catch (future_error&)
            {}
         }
      }
      catch (...)
      {
         //loop stopped
         waiting_.fetch_sub(1, memory_order_acq_rel);
         rethrow_exception(current_exception());
      }

      //to shut up the compiler warning
      return T();
   }

   void push_back(T&& obj)
   {
      auto completed = completed_.load(memory_order_acquire);
      if (completed)
         return;

      Stack<T>::push_back(move(obj));
      Stack<T>::pop_promise();
   }

   void terminate(exception_ptr exceptptr = nullptr)
   {
      if (exceptptr == nullptr)
      {
         try
         {
            throw StopBlockingLoop();
         }
         catch (...)
         {
            exceptptr = current_exception();
         }
      }

      Stack<T>::exceptPtr_ = exceptptr;
      terminated_.store(true, memory_order_release);
      completed_.store(true, memory_order_release);

      //while (waiting_.load(memory_order_acquire) > 0)
         Stack<T>::pop_promise();
   }

   void clear(void)
   {
      completed();

      Stack<T>::clear();

      terminated_.store(false, memory_order_relaxed);
      completed_.store(false, memory_order_relaxed);
   }

   void completed(exception_ptr exceptptr = nullptr)
   {
      if (exceptptr == nullptr)
      {
         try
         {
            throw StopBlockingLoop();
         }
         catch (...)
         {
            exceptptr = current_exception();
         }
      }

      Stack<T>::exceptPtr_ = exceptptr;
      completed_.store(true, memory_order_release);

      //while (waiting_.load(memory_order_acquire) > 0)
         Stack<T>::pop_promise();
   }

   int waiting(void) const
   {
      return waiting_.load(memory_order_relaxed);
   }
};



#endif
