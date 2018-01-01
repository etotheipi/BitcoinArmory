////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef PROGRESS_H
#define PROGRESS_H

#include <cstdint>
#include <chrono>
#include <functional>
#include "bdmenums.h"

typedef std::function<void(BDMPhase, double, unsigned, unsigned)> ProgressCallback;

class ProgressReporter
{
public:
   virtual ~ProgressReporter() { }
   
   virtual void progress(
      double progress, unsigned secondsRemaining
   )=0;
};


class NullProgressReporter : public ProgressReporter
{
public:
   virtual void progress(double, unsigned)
   { }
};


class ProgressCalculator
{
   const uint64_t total_;
   
   std::chrono::milliseconds then_;
   uint64_t lastSample_=0;
   
   double avgSpeed_=0.0;
   
   
public:
   ProgressCalculator(uint64_t total);
   
   void init(uint64_t to);
   void advance(uint64_t to);

   uint64_t total() const { return total_; }

   double fractionCompleted() const 
   { 
      if (lastSample_ > total_)
         return 1.0;

      return lastSample_/double(total_); 
   }
   
   double unitsPerSecond() const { return avgSpeed_; }
   
   uint64_t remainingSeconds() const
   {
      if (lastSample_ > total_)
         return UINT32_MAX;

      return (total_-lastSample_)/unitsPerSecond();
   }
};

class ProgressReporterFilter : public ProgressReporter
{
   ProgressReporter *const to_;
   double progress_=0.0;
   unsigned secondsRemaining_=0;

public:
   ProgressReporterFilter(ProgressReporter *to);
   
   virtual void progress(
      double progress, unsigned secondsRemaining
   );
};

class ProgressFilter : public ProgressReporterFilter
{
   ProgressCalculator calc_;
   const int64_t offset_=0;
public:
   ProgressFilter(ProgressReporter *to, uint64_t total);
   // when advance(x) is called, offset is added to 'x'
   ProgressFilter(ProgressReporter *to, int64_t offset, uint64_t total);
   ~ProgressFilter();
   
   void advance(uint64_t to);
};


#endif
