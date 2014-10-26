#ifndef PROGRESS_H
#define PROGRESS_H

#include <cstdint>
#include <time.h>

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
   
   time_t then_;
   uint64_t lastSample_=0;
   
   double avgSpeed_=0.0;
   
   
public:
   ProgressCalculator(uint64_t total);
   
   void advance(uint64_t to);
   uint64_t total() const { return total_; }

   double fractionCompleted() const { return lastSample_/double(total_); }
   
   double unitsPerSecond() const { return avgSpeed_; }
   
   time_t remainingSeconds() const
   {
      return (total_-lastSample_)/unitsPerSecond();
   }
};

class ProgressReporterFilter : public ProgressReporter
{
   ProgressReporter *const to_;
   const double scale_;
   double progress_=0.0;
   unsigned secondsRemaining_=0;
   bool never_=true;

public:
   ProgressReporterFilter(ProgressReporter *to, double scale=1.0);
   
   virtual void progress(
      double progress, unsigned secondsRemaining
   );
};

class ProgressFilter : public ProgressReporterFilter
{
   ProgressCalculator calc_;
public:
   ProgressFilter(ProgressReporter *to, uint64_t total, double scale=1.0);
   ~ProgressFilter();
   
   void advance(uint64_t to);
};


#endif
