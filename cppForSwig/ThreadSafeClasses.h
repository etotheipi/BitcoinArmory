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

using namespace std;

class IsEmpty
{};

template <typename T> class Entry
{
   T obj_;

public:
   Entry<T>* next_ = nullptr;

public:
   Entry<T>(const T& obj) :
      obj_(obj)
   {}

   ~Entry()
   {
      delete next_;
   }

   T&& getObj(void)
   {
      return move(obj_);
   }
};

template<typename T> class AtomicPile
{
   /***
   FILO unbounded pile, thread safe and lockless
   ***/
private:
   atomic<Entry<T>*> top_;

   atomic<size_t> count_;

public:
   AtomicPile()
   {
      top_.store(nullptr, memory_order_relaxed);
      count_.store(0, memory_order_relaxed);
   }

   ~AtomicPile()
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
      
      auto retval = move(topentry->getObj());
      delete topentry;

      count_.fetch_sub(1, memory_order_relaxed);

      return retval;
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
      auto topentry = top_.load(memory_order_acquire);
      while (!top_.compare_exchange_weak(topentry, nullptr));

      count_.store(0, memory_order_relaxed);
      delete topentry;
   }

   size_t size(void) const
   {
      return count_.load(memory_order_relaxed);
   }
};

#endif
