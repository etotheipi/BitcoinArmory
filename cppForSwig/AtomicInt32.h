#ifndef AINT32
#define AINT32

#ifdef _MSC_VER
#include <Windows.h>
#include <intrin.h>
#include <stdint.h>

class AtomicInt32 {
	public:
		volatile int32_t i;

      AtomicInt32::AtomicInt32()
      {
         *this = 0;
      }


      AtomicInt32::AtomicInt32(int32_t init)
      {
         *this = init;
      }

		AtomicInt32 &AtomicInt32::operator=(int32_t in)
		{
			InterlockedExchange((long*)&this->i, (long)in);
			return *this;
		}

		AtomicInt32 &AtomicInt32::operator++(int32_t)
		{
			InterlockedIncrement((long*)&this->i);
			return *this;
		}

		AtomicInt32 &AtomicInt32::operator--(int32_t)
		{
			InterlockedDecrement((long*)&this->i);
			return *this;
		}

		bool AtomicInt32::operator!=(int32_t in)
		{
         if(this->i!=in) return true;
			return false;
		}

  		bool AtomicInt32::operator==(int32_t in)
		{
         if(this->i==in) return true;
			return false;
		}

		int32_t CompareExchange(int32_t exch, int32_t comp)
		{
			return InterlockedCompareExchange((long*)&this->i, exch, comp);
		}

      int32_t Fetch_Or(int32_t r)
      {
         return (int32_t)InterlockedOr((unsigned long long*)&this->i, r);
      }

      int32_t Fetch_Add(int32_t r)
      {
         return InterlockedExchangeAdd((long*)&this->i, r);
      }
};

#else
// AtomicInt based on <cstdatomic>
#endif
#endif //AINT32