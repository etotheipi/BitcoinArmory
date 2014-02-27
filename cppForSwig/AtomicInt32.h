#ifndef AINT32
#define AINT32

#ifdef _MSC_VER
	#include <Windows.h>
	#include <intrin.h>
	#include <stdint.h>
#else
	#include <atomic>
#endif

class AtomicInt32 
{
   public:
#ifdef _MSC_VER
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

      int32_t Fetch_Or(int32_t r)
      {
         return (int32_t)InterlockedOr((unsigned long long*)&this->i, r);
      }

      int32_t Fetch_Add(int32_t r)
      {
         return InterlockedExchangeAdd((long*)&this->i, r);
      }
#else
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

      int32_t Fetch_Or(int32_t r)
      {
         return i.fetch_or(r);
      }

      int32_t Fetch_Add(int32_t r)
      {
         return i.fetch_add(r); 
      }
#endif

		bool AtomicInt32::operator!=(int32_t in)
	   {
         return in - this->i;  
		}

  		bool AtomicInt32::operator==(int32_t in)
		{
         return !(in - this->i);
		}

      bool AtomicInt32::operator>(int32_t in)
      {
         return this->i > in;
      }

      bool AtomicInt32::operator<(int32_t in)
      {
         return this->i < in;
      }

      bool operator>=(int32_t in)
      {  
         return this->i >= in;
      }

      int32_t Get() { return i; }
};

#endif //AINT32
