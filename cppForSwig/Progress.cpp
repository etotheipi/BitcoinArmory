#include "Progress.h"

ProgressCalculator::ProgressCalculator(uint64_t total)
   : total_(total)
{
   then_ = time(0);
}

void ProgressCalculator::advance(uint64_t to)
{
   static const double smoothingFactor=.10;
   
   if (to == lastSample_) return;
   const time_t now = time(0);
   if (now == then_) return;
   
   if (now < then_+10) return;
   
   double speed = (to-lastSample_)/double(now-then_);
   
   if (lastSample_ == 0)
      avgSpeed_ = speed;
   lastSample_ = to;

   avgSpeed_ = smoothingFactor*speed + (1-smoothingFactor)*avgSpeed_;
   
   then_ = now;
}

ProgressReporterFilter::ProgressReporterFilter(ProgressReporter *to, double scale)
   : to_(to), scale_(scale)
{ }

void ProgressReporterFilter::progress(
   double progress, unsigned secondsRemaining
)
{
   if (secondsRemaining == secondsRemaining_ && progress_ == progress)
      return;
   secondsRemaining_ = secondsRemaining;
   progress_ = progress;
   to_->progress(progress*scale_, secondsRemaining/scale_);
}


ProgressFilter::ProgressFilter(ProgressReporter *to, uint64_t total, double scale)
   : ProgressReporterFilter(to, scale), calc_(total)
{ }
ProgressFilter::~ProgressFilter()
{
   advance(calc_.total());
}
void ProgressFilter::advance(uint64_t to)
{
   calc_.advance(to);
   progress(calc_.fractionCompleted(), calc_.remainingSeconds());
}   


// kate: indent-width 3; replace-tabs on;
