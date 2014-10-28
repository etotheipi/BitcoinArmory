#ifndef UTIL_H
#define UTIL_H

#include <mutex>
#include <condition_variable>

template<class Container>
class IterateSecond
{
   Container &c;
public:
   typedef typename Container::value_type::second_type value_type;

   IterateSecond(Container &c) : c(c) { }

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
   std::mutex all_lock;
   unsigned num_readers=0, wants_writers=0;
   std::condition_variable no_readers, no_writers;
   
public:
   void lockRead()
   {
      unique_lock<mutex> rl(all_lock);
      while (wants_writers > 0)
         no_writers.wait(rl);
      num_readers++;
   }
   void unlockRead()
   {
      unique_lock<mutex> rl(all_lock);
      num_readers--;
      no_readers.notify_all();
   }
   
   void lockWrite()
   {
      unique_lock<mutex> rl(all_lock);
      wants_writers++;
      while (num_readers > 0)
         no_readers.wait(rl);
      wants_writers--;
      
      rl.release();
   }
   
   void unlockWrite()
   {
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
