////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
//
// UniversalTimer
//
// This is a singleton class, meaning there can only ever be one of these in
// existence. It keeps a master list of time accumulations for whatever is
// being tracked.
//
// I used this class to profile itself. With 60 keys in the timer map, I timed
// 5,000,000 pairs of TIMER*START_GROUP/TIMER_STOP_GROUP tags, which ran in
// about 22s...
//
// Therefore, each timing adds about 4.5 microseconds of overhead to the code
//
// NOTE:  This class was originally used on a machine with no internet access
//        or USB ports.  The code had to be printed, scanned and OCR'd.  While
//        I have debugged the original code rigorously, there is no guarantees
//        that this version of it is bug-free (I don't feel like exhaustively
//        testing it again...)
//
////////////////////////////////////////////////////////////////////////////////
#ifndef _UNIVERSALTIMER_H_
#define _UNIVERSALTIMER_H_
#include <map>
#include <iostream>
#include <fstream>
#include <ctime>
#include <iomanip>
#include <string>

// Use these #define's to wrap code blocks, not just a single function
#define TIMER_START(NAME) UniversalTimer::instance().start(NAME)
#define TIMER_RESTART(NAME) UniversalTimer::instance().restart(NAME)
#define TIMER_STOP(NAME) UniversalTimer::instance().stop(NAME)

// Same as above, but include a group name, so to group like objects
#define TIMER_START_GROUP(GRPSTR,NAME) UniversalTimer::instance().start(NAME,GRPSTR)
#define TIMER_RESTART_GROUP(GRPSTR,NAME) UniversalTimer::instance().restart(NAME,GRPSTR)
#define TIMER_STOP_GROUP(GRPSTR,NAME) UniversalTimer::instance().stop(NAME,GRPSTR)

// WRAP ANY FUNCTION OR LINE WITH THIS METHOD — IT IS STORED BY ITS OWN NAME
#define TIMER_WRAP(LINE) \
   UniversalTimer::instance().start(std::string(#LINE)); \
   LINE; \
   UniversalTimer::instance().stop(std::string(#LINE));

// WRAP A FUNCTION OR LINE OF CODE, BUT YOU PROVIDE YOUR OWN NAME, NO GROUP
#define TIMER_WRAP_CUSTOM(NAME, LINE) \
   UniversalTimer::instance().start(NAME); \
   LINE; \
   UniversalTimer::instance().stop(NAME);

// USE THE FUNCTION NAME OR LINE AS THE BASE, BUT PROVIDE A GROUP STRING
#define TIMER_WRAP_GROUP(GRPSTR, LINE) \
   UniversalTimer::instance().start(std::string(#LINE),GRPSTR); \
   LINE; \
   UniversalTimer::instance().stop(std::string(#LINE),GRPSTR);

// PROVIDE YOUR OWN NAME AND GROUP STRING
#define TIMER_WRAP_CUSTOM_GROUP(GRPSTR, NAME, LINE) \
   UniversalTimer::instance().start(NAME,GRPSTR); \
   LINE; \
   UniversalTimer::instance().stop(NAME,GRPSTR);

#define TIMER_READ_SEC(NAME) UniversalTimer::instance().read(NAME)

// STARTS A TIMER THAT STOPS WHEN IT GOES OUT OF SCOPE
#define SCOPED_TIMER(NAME) TimerToken TT(NAME)

using namespace std;

class UniversalTimer
{
public:
   static UniversalTimer & instance(void);
   void init (string key, string grpstr="");
   void start (string key, string grpstr="");
   void restart (string key, string grpstr="");
   void stop (string key, string grpstr="");
   void reset (string key, string grpstr="");
   double read (string key, string grpstr="");
   string getLastKey(void) {return most_recent_key_;}
   double getLastTiming(void) {return call_timers_[most_recent_key_].getPrev();}
   void printCSV(ostream & os=cout, bool excludeZeros=false);
   void printCSV(string filename, bool excludeZeros=false);
   void print(ostream & os=cout, bool excludeZeros=false);
   void print(string filename, bool excludeZeros=false);
protected:
   UniversalTimer(void) : most_recent_key_("") { }
private:
   class timer
   {
   public:
      timer(void) :
         isRunning_(false),
         start_clock_(0),
         stop_clock_(0),
         start_time_(0),
         stop_time_(0),
         accum_time_(0) { }
      void start (void);
      void restart(void);
      void stop (void);
      double read (void);
      void reset (void);
      double getPrev(void) { return prev_elapsed_; }
   private:
      bool isRunning_;
      clock_t start_clock_;
      clock_t stop_clock_;
      time_t start_time_;
      time_t stop_time_;
      double prev_elapsed_;
      double accum_time_;
   };
   static UniversalTimer* theUT_;
   map<string, timer> call_timers_;
   map<string, int > call_count_;
   map<string, string> call_group_;
   string most_recent_key_;
};


// Create a token at the beginning of a function, and it will stop the timer
// when that token goes out of scope.
//
// The UniversalTimer is very fast, but not as fast as something things you 
// want to time.  It is recommended not to add a TimerToken to every method,
// unless you anticipate it will take more than 1 ms.  I think it operates 
// on the order of microsecs, so anything shorter than 1 ms may actually be
// inflated by the timer call itself.
class TimerToken
{
public:
   TimerToken(string name) 
   { 
      timerName_ = name; 
      UniversalTimer::instance().start(timerName_);

      #ifdef _DEBUG
         cout << "Executing " << timerName_.c_str() << endl;
      #endif
   }


   ~TimerToken(void)
   { 
      UniversalTimer::instance().stop(timerName_);
      lastTiming_ = UniversalTimer::instance().read(timerName_);
      #ifdef _DEBUG
         cout << "Finishing " << timerName_.c_str()
              << "(" << lastTiming_*1000.0 << " ms)" << endl;
      #endif
   }

private: 
   string timerName_;
   double lastTiming_;
};




#endif


