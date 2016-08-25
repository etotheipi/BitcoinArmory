////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include <iostream>
#include <stdlib.h>
#include <stdint.h>
#include <thread>
#include "gtest.h"

#include "../ThreadSafeClasses.h"

using namespace std;

#ifdef _MSC_VER
#ifdef _DEBUG
//#define _CRTDBG_MAP_ALLOC
#include <stdlib.h>
#include <crtdbg.h>

#ifndef DBG_NEW
#define DBG_NEW new ( _NORMAL_BLOCK , __FILE__ , __LINE__ )
#define new DBG_NEW
#endif
#endif
#endif


////////////////////////////////////////////////////////////////////////////////
class ContainerTests : public ::testing::Test
{
protected:

   uint64_t threadCount_;

   virtual void SetUp()
   {
      threadCount_ = thread::hardware_concurrency() * 2;
   }

   virtual void TearDown()
   {}
};

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, TransactionalMap)
{
   unsigned iterations = 200;
   TransactionalMap<unsigned, unsigned> theMap;

   auto insert_thread = [&theMap, &iterations](unsigned id)
   {
      for (auto i = id * iterations; i < (id + 1) * iterations; i++)
      {
         theMap.insert(make_pair(i, i));
      }
   };

   auto find_thread = [&theMap, &iterations](unsigned id, uint32_t* tally)
   {
      auto mapptr = theMap.get();

      for (auto i = id * iterations; i < (id + 1) * iterations; i++)
      {
         auto iter = mapptr->find(i);
         if (iter != mapptr->end())
            *tally += iter->second;
      }
   };

   vector<thread> vecthr;
   for (unsigned i = 0; i < threadCount_; i++)
      vecthr.push_back(thread(insert_thread, i));

   for (auto& thr : vecthr)
      if (thr.joinable())
         thr.join();

   vecthr.clear();
   vector<uint32_t> tallies(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      vecthr.push_back(thread(find_thread, i, &tallies[0] + i));

   for (auto& thr : vecthr)
      if (thr.joinable())
         thr.join();

   uint32_t total = 0;
   for (auto& tally : tallies)
      total += tally;

   uint32_t maxtotal = threadCount_ * iterations - 1;
   uint32_t calctotal = (maxtotal + 1) * maxtotal;
   calctotal /= 2;

   EXPECT_EQ(total, calctotal);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, PileTest_Sequential)
{
   Pile<uint64_t> thePile;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         thePile.push_back(move(val));
      }
   };

   auto pop_thread = [&thePile](uint64_t* tally)
   {
      //pop from pile, increment tally

      while (1)
      {
         try
         {
            *tally += thePile.pop_back();
         }
         catch (IsEmpty&)
         {
            break;
         }
      }
   };

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (auto& pushthr : push_threads)
      if (pushthr.joinable())
         pushthr.join();

   EXPECT_EQ(thePile.count(), threadCount_ * iterCount);

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& popthr : pop_threads)
      if (popthr.joinable())
         popthr.join();

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(thePile.count(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, PileTest_Concurrent)
{
   Pile<uint64_t> thePile;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         thePile.push_back(move(val));
      }
   };

   auto pop_thread = [&thePile](uint64_t* tally, shared_ptr<atomic<bool>> done)
   {
      //pop from pile, increment tally

      while (!done->load(memory_order_acquire))
      {
         try
         {
            while (1)
            {
               *tally += thePile.pop_back();
            }
         }
         catch (IsEmpty&)
         {
         }
      }
   };

   auto stop_pop_threads = make_shared<atomic<bool>>();
   stop_pop_threads->store(false, memory_order_relaxed);

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y, stop_pop_threads));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   stop_pop_threads->store(true, memory_order_release);

   for (auto& popthr : pop_threads)
   {
      if (popthr.joinable())
         popthr.join();
   }

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(thePile.count(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, StackTest_Sequential)
{
   Stack<uint64_t> theStack;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         theStack.push_back(move(val));
      }
   };

   auto pop_thread = [&theStack](uint64_t* tally)
   {
      //pop from pile, increment tally

      while (1)
      {
         try
         {
            *tally += theStack.pop_front();
         }
         catch (IsEmpty&)
         {
            break;
         }
      }
   };

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));


   for (auto& pushthr : push_threads)
      if (pushthr.joinable())
         pushthr.join();

   EXPECT_EQ(theStack.count(), threadCount_ * iterCount);

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& popthr : pop_threads)
      if (popthr.joinable())
         popthr.join();

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, StackTest_Concurrent)
{
   Stack<uint64_t> theStack;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         theStack.push_back(move(val));
      }
   };

   auto pop_thread = [&theStack](uint64_t* tally, shared_ptr<atomic<bool>> done)
   {
      //pop from pile, increment tally

      while (!done->load(memory_order_acquire))
      {
         try
         {
            while (1)
            {
               *tally += theStack.pop_front();
            }
         }
         catch (IsEmpty&)
         {
         }
      }
   };

   auto stop_pop_threads = make_shared<atomic<bool>>();
   stop_pop_threads->store(false, memory_order_relaxed);

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y, stop_pop_threads));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   stop_pop_threads->store(true, memory_order_release);

   for (auto& popthr : pop_threads)
   {
      if (popthr.joinable())
         popthr.join();
   }

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, BlockingStackTest_Sequential)
{
   BlockingStack<uint64_t> theStack;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         theStack.push_back(move(val));
      }
   };

   auto pop_thread = [&theStack](uint64_t* tally)
   {
      //pop from pile, increment tally

      try
      {
         while (1)
         {
            *tally += theStack.pop_front();
         }
      }
      catch (StopBlockingLoop&)
      {
      }
   };

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));


   for (auto& pushthr : push_threads)
      if (pushthr.joinable())
         pushthr.join();

   theStack.completed();
   EXPECT_EQ(theStack.count(), threadCount_ * iterCount);

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& popthr : pop_threads)
      if (popthr.joinable())
         popthr.join();

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);
   EXPECT_EQ(theStack.waiting(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, BlockingStackTest_Concurrent)
{
   BlockingStack<uint64_t> theStack;
   unsigned iterCount = 100000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      //tally = 0;

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         theStack.push_back(move(val));
      }
   };

   auto pop_thread = [&theStack](uint64_t* tally)
   {
      //pop from pile, increment tally
      try
      {
         while (1)
         {
            *tally += theStack.pop_front();
         }
      }
      catch (StopBlockingLoop&)
      {}
   };

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   theStack.completed();

   for (auto& popthr : pop_threads)
   {
      if (popthr.joinable())
         popthr.join();
   }

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(theStack.waiting(), 0);
   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);

   theStack.clear();

   push_threads.clear();
   pop_threads.clear();

   push_tallies.clear(); push_tallies.resize(threadCount_);
   pop_tallies.clear(); pop_tallies.resize(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   theStack.terminate();

   for (auto& popthr : pop_threads)
   {
      if (popthr.joinable())
         popthr.join();
   }

   EXPECT_NE(theStack.count(), 0);
   theStack.clear();
   EXPECT_EQ(theStack.count(), 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(ContainerTests, TimedStackTest_Concurrent)
{
   TimedStack<uint64_t> theStack;
   unsigned iterCount = 35000;

   auto push_thread = [&](uint64_t* tally)
   {
      //create random numbers, push to pile, increment tally
      srand(time(0));

      uint64_t val;
      for (unsigned i = 0; i < iterCount; i++)
      {
         val = rand();

         *tally += val;
         theStack.push_back(move(val));
      }
   };

   auto pop_thread = [&theStack](uint64_t* tally)
   {
      //pop from pile, increment tally
      auto timeout = chrono::seconds(2);
      try
      {
         while (1)
         {
            *tally += theStack.pop_front(timeout);
         }
      }
      catch (StackTimedOutException&)
      {
      }
   };

   vector<thread> push_threads, pop_threads;
   vector<uint64_t> push_tallies(threadCount_), pop_tallies(threadCount_);

   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (unsigned y = 0; y < threadCount_; y++)
      pop_threads.push_back(thread(pop_thread, &pop_tallies[0] + y));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   push_threads.clear();
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   push_threads.clear();
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }

   for (auto& popthr : pop_threads)
   {
      if (popthr.joinable())
         popthr.join();
   }

   uint64_t pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   uint64_t poptally = 0;
   for (auto& tally : pop_tallies)
      poptally += tally;

   EXPECT_EQ(theStack.waiting(), 0);
   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);

   push_threads.clear();
   push_tallies.clear(); push_tallies.resize(threadCount_);
   for (unsigned i = 0; i < threadCount_; i++)
      push_threads.push_back(thread(push_thread, &push_tallies[0] + i));

   for (auto& pushthr : push_threads)
   {
      if (pushthr.joinable())
         pushthr.join();
   }
   auto&& values = theStack.pop_all();

   pushtally = 0;
   for (auto& tally : push_tallies)
      pushtally += tally;

   poptally = 0;
   for (auto& val : values)
      poptally += val;

   EXPECT_EQ(theStack.waiting(), 0);
   EXPECT_EQ(pushtally, poptally);
   EXPECT_EQ(theStack.count(), 0);
}


////////////////////////////////////////////////////////////////////////////////
GTEST_API_ int main(int argc, char **argv)
{
#ifdef _MSC_VER
   _CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);
#endif

   testing::InitGoogleTest(&argc, argv);
   int exitCode = RUN_ALL_TESTS();

   return exitCode;
}
