////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "Progress.h"

ProgressCalculator::ProgressCalculator(uint64_t total)
   : total_(total)
{
   init(0);
}

void ProgressCalculator::init(uint64_t to)
{
   auto now = std::chrono::high_resolution_clock::now();
   auto duration = now.time_since_epoch();
   then_ = std::chrono::duration_cast<std::chrono::milliseconds>(duration);

   lastSample_ = to;
}

void ProgressCalculator::advance(uint64_t to)
{
   static const double smoothingFactor=.10;
   
   if (to == lastSample_) return;
   auto sysclock = std::chrono::high_resolution_clock::now();
   auto duration = sysclock.time_since_epoch();
   auto now = std::chrono::duration_cast<std::chrono::milliseconds>(duration);

   if (now == then_) return;
   auto diff = now - then_;
   double doubleDiff = double(diff.count()) / 1000.0;
      
   double speed = (to-lastSample_)/doubleDiff;
   
   if (lastSample_ == 0)
      avgSpeed_ = speed;
   lastSample_ = to;

   avgSpeed_ = smoothingFactor*speed + (1-smoothingFactor)*avgSpeed_;
   
   then_ = now;
}

ProgressReporterFilter::ProgressReporterFilter(ProgressReporter *to)
   : to_(to)
{ }

void ProgressReporterFilter::progress(
   double progress, unsigned secondsRemaining
)
{
   secondsRemaining_ = secondsRemaining;
   progress_ = progress;
   to_->progress(progress, secondsRemaining);
}


ProgressFilter::ProgressFilter(ProgressReporter *to, int64_t offset, uint64_t total)
   : ProgressReporterFilter(to), calc_(total), offset_(offset)
{
   advance(0);
}
ProgressFilter::ProgressFilter(ProgressReporter *to, uint64_t total)
   : ProgressReporterFilter(to), calc_(total)
{
   advance(0);
}

ProgressFilter::~ProgressFilter()
{
   advance(calc_.total());
}
void ProgressFilter::advance(uint64_t to)
{
   calc_.advance(to+offset_);
   progress(calc_.fractionCompleted(), calc_.remainingSeconds());
}   


// kate: indent-width 3; replace-tabs on;
