#ifndef AINT32
#define AINT32

#ifdef _MSC_VER
#include <Windows.h>
#include <intrin.h>
#include <stdint.h>

class AtomicInt32 
{
   public:
      volatile int32_t i;

      AtomicInt32::AtomicInt32()
      {
         i = 0;
      }


      AtomicInt32::AtomicInt32(int32_t init)
      {
         i = init;
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
// AtomicInt based on <atomic>
#include <atomic>

class AtomicInt32 
{
   public:
      std::atomic_int_fast32_t i;

      AtomicInt32()
      {
         i.store(0);
      }

      AtomicInt32(const AtomicInt32& in_)
      {
         i.store(in_.i.load());
      }

      AtomicInt32(int32_t init)
      {
         i.store(init);
      }

      AtomicInt32& operator=(int32_t in)
      {
         this->i.store(in);
         return *this;
      }

      AtomicInt32& operator=(const AtomicInt32& rhs)
      {
         this->i.store(rhs.i.load());
         return *this;
      }

		AtomicInt32& operator++(int32_t)
		{
			this->i.fetch_add(1);
			return *this;
		}

		AtomicInt32 &operator--(int32_t)
		{
			this->i.fetch_sub(1);
			return *this;
		}

		bool operator!=(int32_t in)
		{
         if(this->i!=in) return true;
			return false;
		}

  		bool operator==(int32_t in)
		{
         if(this->i==in) return true;
			return false;
		}

		int32_t CompareExchange(int32_t exch, int32_t comp)
		{
			return i.compare_exchange_weak(comp, exch);
		}

      int32_t Fetch_Or(int32_t r)
      {
         return i.fetch_or(r);
      }

      int32_t Fetch_Add(int32_t r)
      {
         return i.fetch_add(r); 
      }
};


#endif
#endif //AINT32
