////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef UTIL_H
#define UTIL_H

#include <mutex>
#include <condition_variable>
#include <thread>

template<class Container>
class IterateSecond
{
   Container &c;
public:
   typedef typename Container::value_type::second_type value_type;

   IterateSecond(Container &_c) : c(_c) { }

   class Iterator
   {
      friend class IterateSecond;
      typename Container::iterator i;
   public:
      Iterator(const Iterator &copy)
         : i(copy.i)
      { }
      Iterator()
      { }
   
      value_type& operator*() { return i->second; }
      const value_type& operator*() const { return i->second; }
      
      Iterator& operator++()
      {
         ++i;
         return *this;
      }
      Iterator operator++(int)
      {
         Iterator x;
         x.i = i;
         ++x.i;
         return x;
      }
      
      bool operator==(const Iterator &other) const { return i == other.i; }
      bool operator!=(const Iterator &other) const { return i != other.i; }
   };

   class ConstIterator
   {
      friend class IterateSecond;
      typename Container::const_iterator i;
   public:
      ConstIterator(const Iterator &copy)
         : i(copy.i)
      { }
      ConstIterator(const ConstIterator &copy)
         : i(copy.i)
      { }
      ConstIterator()
      { }
      const value_type& operator*() const { return i->second; }
      
      ConstIterator& operator++()
      {
         ++i;
         return *this;
      }
      ConstIterator operator++(int)
      {
         ConstIterator x;
         x.i = i;
         ++x.i;
         return x;
      }
      bool operator==(const ConstIterator &other) const { return i == other.i; }
      bool operator!=(const ConstIterator &other) const { return i != other.i; }
   };
   
   Iterator begin() { Iterator x; x.i = c.begin(); return x; }
   Iterator end() { Iterator x; x.i = c.end(); return x; }

   ConstIterator begin() const  { ConstIterator x; x.i = c.begin(); return x; }
   ConstIterator end() const  { ConstIterator x; x.i = c.end(); return x; }
};

template<class Container>
inline IterateSecond<Container> values(Container &c)
   { return IterateSecond<Container>(c); }

template<class Container>
inline const IterateSecond<const Container> values(const Container &c)
   { return IterateSecond<const Container>(c); }

class ReadWriteLock
{
   /***
   You have to make sure a read lock request from a thread already holding
   a read lock ignores write lock requests, otherwise you could end up in
   a deadlock where a write lock is requested before a child read lock is.

   Example:
   T1 creates a read lock. T2 requests a write lock. At this point no new
   read locks can be created, until the write lock is fulfilled. The
   write lock can only be fulfilled if all current read locks are released.

   Within T1's first read lock, a new read lock is requested. This new lock
   will never be acquired, waiting forever on T2's write lock to be
   fulfilled first.

   T2's write lock will never be fulfilled, as it is waiting on T1's
   currently held read lock to be released. T1's current lock won't be
   released as it will never exist its scope, waiting for T1's second
   lock to be acquired.

   Incidentally, in the scope of a same thread, requesting a write lock
   within a read lock will always deadlock. The condition should be tested
   and thrown. Requesting a read lock within a write lock can and should
   be accomodated.
   ***/

   std::mutex all_lock;
   unsigned num_readers = 0;
   bool has_writer=false;
   std::condition_variable no_readers, no_writers;

   std::map<std::thread::id, unsigned> thread_ids_;
   
public:
   void lockRead()
   {
      unique_lock<mutex> rl(all_lock);
      
      std::thread::id this_thread_id = std::this_thread::get_id();
      auto idIter = thread_ids_.find(this_thread_id);

      if (idIter != thread_ids_.end())
      {
         idIter->second++;
      }


      if (idIter == thread_ids_.end())
      {
         while (has_writer)
            no_writers.wait(rl);
         
         thread_ids_.insert(make_pair(this_thread_id, 1));
      }

      num_readers++;
   }
   void unlockRead()
   {
      unique_lock<mutex> rl(all_lock);
      std::thread::id this_thread_id = std::this_thread::get_id();
      auto idIter = thread_ids_.find(this_thread_id);

      if (idIter == thread_ids_.end())
         throw runtime_error("unregistered thread attempted to release a lock");

      idIter->second--;
      if (idIter->second == 0)
         thread_ids_.erase(idIter);

      num_readers--;
      if (num_readers == 0)
         no_readers.notify_all();
   }
   
   void lockWrite()
   {
      unique_lock<mutex> rl(all_lock);

      std::thread::id this_thread_id = std::this_thread::get_id();
      auto idIter = thread_ids_.find(this_thread_id);
      if (idIter != thread_ids_.end())
         throw runtime_error("ReadWriteLock deadlock: requested write lock"
         "within a thread already holding a read lock");

      has_writer = true;
      while (num_readers > 0)
         no_readers.wait(rl);

      rl.release();
   }
   
   void unlockWrite()
   {
      has_writer = false;
      no_writers.notify_all();
      all_lock.unlock();
   }

   class ReadLock
   {
      ReadWriteLock *const l;
      bool locked=true;
   public:
      ReadLock(ReadWriteLock &rwl)
         : l(&rwl)
      {
         l->lockRead();
      }
      void unlock()
      {
         locked=false;
         l->unlockRead();
      }
      ~ReadLock()
      {
         if (locked)
            l->unlockRead();
      }
   };
   class WriteLock
   {
      ReadWriteLock *const l;
      bool locked=true;
   public:
      WriteLock(ReadWriteLock &rwl)
         : l(&rwl)
      {
         l->lockWrite();
      }
      void unlock()
      {
         locked=false;
         l->unlockRead();
      }
      ~WriteLock()
      {
         if (locked)
            l->unlockWrite();
      }
   };
   
};

#endif

// kate: indent-width 3; replace-tabs on;
