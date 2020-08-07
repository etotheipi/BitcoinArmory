////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <iostream>
#include <fstream>
#include "UniversalTimer.h"

using namespace std;

////////////////////////////////////////////////////////////////////////////////
// START UhiversalTimer::timer methods
////////////////////////////////////////////////////////////////////////////////
// START TIMER

atomic<int32_t> UniversalTimer::lock_;

void UniversalTimer::lock(void)
{
   while (lock_.fetch_or(1, memory_order_relaxed));
}

void UniversalTimer::unlock(void)
{
   lock_.store(0, memory_order_relaxed);
}

void UniversalTimer::timer::start(void)
{
   if (isRunning_)
      return;
   isRunning_ = true;
   start_clock_ = chrono::system_clock::now();
}

// RESTART TIMER
void UniversalTimer::timer::restart(void)
{
   isRunning_ = true;
   accum_time_ = 0;
   start_clock_ = chrono::system_clock::now();
}

// STOP TIMER
void UniversalTimer::timer::stop(void)
{
   if (isRunning_)
   {
      chrono::duration<double> acc_sec = 
         chrono::system_clock::now() - start_clock_;
      accum_time_ += acc_sec.count();
   }
   isRunning_ = false;
}

// STOP AND RESET TTMER
void UniversalTimer::timer::reset(void)
{
   isRunning_ = false;
   accum_time_ = 0;
}

// CALCULATE THE ELAPSED TIME BUT DON'T STOP TIMER
double UniversalTimer::timer::read(void)
{
   double accum = accum_time_; // if not running, this is correct
   if(isRunning_)
   {
      stop();
      accum = accum_time_;
      start();
   }
   return accum;
}
////////////////////////////////////////////////////////////////////////////////
// END UniversalTimer::timer methods
////////////////////////////////////////////////////////////////////////////////



// A pointer to the sole instance of UniversalTimer
UniversalTimer* UniversalTimer::theUT_ = NULL;

// Get THE UniversalTimer —- only one ever exists
UniversalTimer & UniversalTimer::instance(void)
{
   if (theUT_ == NULL)
   {
      theUT_ = new UniversalTimer;
      lock_.store(0);
   }
   return *theUT_;
}

//Cleanup the singleton
void UniversalTimer::cleanup(void)
{
   if (theUT_ != nullptr)
      delete theUT_;
   theUT_ = nullptr;
}

// Initialize a timer for the given string
void UniversalTimer::init(string key, string grpstr)
{
   string wholeKey = grpstr + key;
   if( call_timers_.find(wholeKey) == call_timers_.end() )
   {
      call_timers_[wholeKey] = timer();
      call_count_[wholeKey] = 0;
      call_group_[wholeKey] = grpstr;
   }
}

// Start a new or existing timer —— will accumulate time
void UniversalTimer::start(string key, string grpstr)
{
   lock();
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   call_timers_[most_recent_key_].start();
   call_count_[most_recent_key_]++;
   unlock();
}

// Start a new or existing timer —— will reset accumulated time to 0
void UniversalTimer::restart(string key, string grpstr)
{
   lock();
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   call_timers_[most_recent_key_].restart();
   call_count_[most_recent_key_]++;
   unlock();
}

// Stops an existing timer, which can then be read out
void UniversalTimer::stop(string key, string grpstr)
{
   lock();
   most_recent_key_ = grpstr + key;
   if( call_timers_.find(most_recent_key_) == call_timers_.end() )
   {
      cout << "***WARNING: attempting to stop a timer not prev started" << endl;
      cout << " KEY: " << most_recent_key_ << endl;
   }
   init(key,grpstr);
   call_timers_[most_recent_key_].stop();
   unlock();
}

// Stops an existing timer, which can then be read out ~
void UniversalTimer::reset(string key, string grpstr)
{
   lock();
   most_recent_key_ = grpstr + key;

   init(key,grpstr);
   call_timers_[most_recent_key_].reset();
   unlock();
}

// Get the value of the accumulated time on the given timer, IN SECONDS
double UniversalTimer::read(string key, string grpstr)
{
   lock();
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   double rt = call_timers_[most_recent_key_].read();
   unlock();
   return rt;
}

// Print complete timing results to a file of this name
void UniversalTimer::printCSV(string filename, bool excludeZeros)
{
   ofstream os(OS_TranslatePath(filename.c_str()), ios::out);
   printCSV(os, excludeZeros);
   os.close();
}

// Print complete timing results to a given output stream
void UniversalTimer::printCSV(ostream & os, bool excludeZeros)
{
   lock();
   os << "Individual timings:" << endl << endl;
   os << ",NCall,Tot,Avg,Name" << endl << endl;
   map<string, timer>::iterator itert;
   map<string, int>::iterator iteri;
   for(itert = call_timers_.begin(), iteri = call_count_.begin();
       itert != call_timers_.end();
       itert++, iteri++)
   {
      if(excludeZeros && itert->second.read() == 0)
         continue;
      os << "," << iteri->second;
      os << "," << itert->second.read();
      os << "," << itert->second.read()/(double)(iteri->second);
      os << "," << itert->first;
      os << endl;
   }

   os << endl;
   os << "Group Timings" << endl << endl;
   // Accumulate the timings for everything with the same group
   map<string, double> group_accum;
   map<string, string>::iterator iters;
   for(itert = call_timers_.begin(), iters = call_group_.begin();
      itert != call_timers_.end();
      itert++, iters++)
   {
      group_accum[iters->second] += itert->second.read();
   }
   // Now all timings have been accumulated for the individual groups
   map<string, double>::iterator iterd;
   for(iterd = group_accum.begin(); iterd != group_accum.end(); iterd++)
   {
      if(iterd->first.length() == 0)
         continue;
      os << ","; // no counting here
      os << "," << iterd->second;
      os << ","; // no count, so no avg
      os << "," << iterd->first;
      os << endl;
   }
   unlock();
}

// Print complete timing results to a file of this name
void UniversalTimer::print(string filename, bool excludeZeros)
{
   ofstream os(OS_TranslatePath(filename.c_str()), ios::out);
   print(os, excludeZeros);
   os.close();
}

// Print complete timing results to a given output stream
void UniversalTimer::print(ostream & os, bool excludeZeros)
{
   lock();
   os << "Individual timings:" << endl << endl;
   os << "\tNCall\tTot\tAvg\t\tName" << endl << endl;
   map<string, timer>::iterator itert;
   map<string, int>::iterator iteri;
   for(itert = call_timers_.begin(), iteri = call_count_.begin();
       itert != call_timers_.end();
       itert++, iteri++)
   {
      if(excludeZeros && itert->second.read() == 0)
         continue;
      printf("\t%d\t%0.3f\t%g\t\t%s\n", iteri->second, 
                                      itert->second.read(), 
                                      itert->second.read()/(double)(iteri->second),
                                      itert->first.c_str());
   }

   os << endl;
   os << "Group Timings" << endl << endl;
   // Accumulate the timings for everything with the same group
   map<string, double> group_accum;
   map<string, string>::iterator iters;
   for(itert = call_timers_.begin(), iters = call_group_.begin();
      itert != call_timers_.end();
      itert++, iters++)
   {
      group_accum[iters->second] += itert->second.read();
   }
   // Now all timings have been accumulated for the individual groups
   map<string, double>::iterator iterd;
   for(iterd = group_accum.begin(); iterd != group_accum.end(); iterd++)
   {
      if(iterd->first.length() == 0)
         continue;

      printf("\t%s\t%0.3f\t%s\t\t%s\n", string("     ").c_str(),
                                      iterd->second, 
                                      string("     ").c_str(),
                                      iterd->first.c_str());
   }
   unlock();
}
