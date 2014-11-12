#include "Progress.h"

ProgressCalculator::ProgressCalculator(uint64_t total)
   : total_(total)
{
   then_ = 0;
}

void ProgressCalculator::advance(uint64_t to)
{
   static const double smoothingFactor=.10;
   
   if (to == lastSample_) return;
   const time_t now = time(0);
   if (then_ == 0)
   {
      then_ = now;
      lastSample_ = to;
   }
   if (now == then_) return;
   
   if (now < then_+10) return;
   
   double speed = (to-lastSample_)/double(now-then_);
   
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
