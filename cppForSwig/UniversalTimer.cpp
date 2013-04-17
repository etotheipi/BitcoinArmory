////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
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
void UniversalTimer::timer::start(void)
{
   if (isRunning_)
      return;
   isRunning_ = true;
   start_clock_ = clock();
   start_time_ = time(0);
}

// RESTART TIMER
void UniversalTimer::timer::restart(void)
{
   isRunning_ = true;
   accum_time_ = 0;
   start_clock_ = clock();
   start_time_ = time(0);
}

// STOP TIMER
void UniversalTimer::timer::stop(void)
{
   if (isRunning_)
   {
      time_t acc_sec = time(0) - start_time_;
      if (acc_sec < 3600)
         prev_elapsed_ = (clock() - start_clock_) / (1.0 * CLOCKS_PER_SEC);
      else
         prev_elapsed_ = (1.0 * acc_sec);
      accum_time_ += prev_elapsed_;
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
   if(theUT_ == NULL)
      theUT_ = new UniversalTimer;
   return *theUT_;
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
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   call_timers_[most_recent_key_].start();
   call_count_[most_recent_key_]++;
}

// Start a new or existing timer —— will reset accumulated time to 0
void UniversalTimer::restart(string key, string grpstr)
{
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   call_timers_[most_recent_key_].restart();
   call_count_[most_recent_key_]++;
}

// Stops an existing timer, which can then be read out
void UniversalTimer::stop(string key, string grpstr)
{
   most_recent_key_ = grpstr + key;
   if( call_timers_.find(most_recent_key_) == call_timers_.end() )
   {
      cout << "***WARNING: attempting to stop a timer not prev started" << endl;
      cout << " KEY: " << most_recent_key_ << endl;
   }
   init(key,grpstr);
   call_timers_[most_recent_key_].stop();
}

// Stops an existing timer, which can then be read out ~
void UniversalTimer::reset(string key, string grpstr)
{
   most_recent_key_ = grpstr + key;
   if( call_timers_.find(most_recent_key_) == call_timers_.end() )
   {
      cout << "***WARNING: attempting to reset a timer not prev used" << endl;
      cout << " KEY: " << most_recent_key_ << endl;
   }
   init(key,grpstr);
   call_timers_[most_recent_key_].reset();
}

// Get the value of the accumulated time on the given timer, IN SECONDS
double UniversalTimer::read(string key, string grpstr)
{
   most_recent_key_ = grpstr + key;
   init(key,grpstr);
   return call_timers_[most_recent_key_].read();
}

// Print complete timing results to a file of this name
void UniversalTimer::printCSV(string filename, bool excludeZeros)
{
   ofstream os(filename.c_str(), ios::out);
   printCSV(os, excludeZeros);
   os.close();
}

// Print complete timing results to a given output stream
void UniversalTimer::printCSV(ostream & os, bool excludeZeros)
{
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
}

// Print complete timing results to a file of this name
void UniversalTimer::print(string filename, bool excludeZeros)
{
   ofstream os(filename.c_str(), ios::out);
   print(os, excludeZeros);
   os.close();
}

// Print complete timing results to a given output stream
void UniversalTimer::print(ostream & os, bool excludeZeros)
{
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
}
