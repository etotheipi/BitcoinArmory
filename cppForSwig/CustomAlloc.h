#ifndef CUSTOMALLOC
#define CUSTOMALLOC
   
#include "AtomicInt32.h"

#ifdef _MSC_VER
   #include <windows.h>
   #define mlock(p, n) VirtualLock((p), (n));
   #define munlock(p, n) VirtualUnlock((p), (n));
#else 
   #include <cstdint>
   #include <stdlib.h>
   #include <string.h>
   #include <sys/mman.h>
   #include <unistd.h>
   #include <sys/resource.h>
   typedef std::size_t size_t;
#endif

typedef uint8_t byte;
#include <limits>

namespace CustomAlloc
{  

   class Gap
   {
      public:
         size_t position, size, end;

         Gap(size_t p, size_t s)
         {
            position = p;
            size = s;
				end = position +s;
         }

			Gap& operator=(const Gap& rhs)
			{
				if(&rhs!=this)
					memcpy(this, &rhs, sizeof(Gap));
					
				return *this;
			}

         void reset();
   };

   class BufferHeader
   {
      public:
         void *offset;
	      unsigned int *pinuse, linuse;
	      size_t size;
	      void* (*copy)(void*, void*);
	      byte move;
         void *ref;
         int index;

	      /***
	      move is a flag for the defrag thread
		      -1: don't move this buffer
		      0: ready for move
		      1: being moved
	      ***/

         void reset();
   };

   class MemPool
   {
      private:
		   static const int BHstep = 50;
		   unsigned int totalBH;
		   void *pool;

         int ngaps, total_ngaps;
         Gap *gaps;
         AtomicInt32 acquireGap;
      
         void Alloc(size_t size);

         BufferHeader* GetBH(size_t size);
      
         int GetGap(size_t size);
         void ExtendGap();

         static AtomicInt32 lock;
         int passedQuota;

			unsigned int nBH;

      public:
         size_t reserved;
		   BufferHeader **BH;
		   static const size_t memsize; //multiple of system page size
		   size_t total;
         size_t freemem;
		   AtomicInt32 lockpool;
		   byte defrag;
         void *ref;
         
         static const int size_of_ptr = sizeof(void*);
         
         MemPool()
		   {
			   BH=0;
			   nBH=0; totalBH=0;
			   defrag=0;
			   pool=0;
			   freemem=0;
			   total=0;
			   lockpool=0;
			   reserved=0;
            acquireGap = 0;
            ref = 0;

            ngaps = total_ngaps = 0;
            gaps = 0;
            passedQuota = 0;
		   }

		   ~MemPool()
		   {
            if(pool)
               Free();
			
            if(BH)
            {
               for(unsigned int i=0; i<nBH; i+=BHstep)
				        free(BH[i]);
			      free(BH);
            }

            if(gaps) free(gaps);
		   }

         void AddGap(BufferHeader *bh);
         void* GetPool();
         void Free();

  		   BufferHeader* GetBuffer(size_t size, unsigned int *sema);
   };

   class CustomAllocator
   {
	   /*** allocates and recycles memory used to hold transactions' raw data
	   ***/
	   private:
		   unsigned int *order, *order2, *otmp, otmpS;
			unsigned int *pool_height, *pool_height2;
		
         MemPool **MP;
         MemPool **poolbatch;
		   unsigned int npools, total, nbatch;

		   static const int poolstep = 10;
		   static const int max_fetch = 10;

		   AtomicInt32 ab, ordering, clearpool;
		   AtomicInt32 orderlvl, bufferfetch;
		   AtomicInt32 getpoolflag;

  		   BufferHeader *GetBuffer(unsigned int size, unsigned int *sema);
         void ExtendPool();

         void UpdateOrder(unsigned int in);

	   public:
		
		   CustomAllocator()
		   {
			   MP=0;
			   otmp=0; otmpS=0;
			   npools=total=0;
			   order=order2=0;
			   ab=ordering=0;
			   orderlvl=0;
			   getpoolflag=0;
			   bufferfetch=0;
            clearpool=0;
            poolbatch=0;
            nbatch=0;
				pool_height=0;
				pool_height2=0;
		   }

		   ~CustomAllocator()
		   {
            for(unsigned int i=0; i<nbatch; i++)
               delete[] poolbatch[i];

            free(poolbatch);
			   free(MP);
			   free(otmp);
			   free(order);
			   free(order2);
				free(pool_height);
				free(pool_height2);
		   }

         void* customAlloc(size_t size);
         void customFree(void *buffer);
         void FreePool(MemPool* pool);

         void FillRate();
   };

   class CAllocStatic
   {
      private:
         static CustomAllocator CA;

      public:
         static void* alloc_(size_t size);
         static void  free_(void* buffer);
   };

   template <class T> class CAlloc
   {
      public:
         CAllocStatic CA;
      
         typedef T value_type;
         typedef std::size_t size_type;
         typedef std::ptrdiff_t difference_type;
      
         typedef T* pointer;
         typedef const T* const_pointer;
      
         typedef T& reference;
         typedef const T& const_reference;

         template <class U>
         struct rebind 
            { typedef CAlloc<U> other; };

         pointer address (reference value) const 
            { return &value; }
   
         const_pointer address (const_reference value) const 
            { return &value; }

         CAlloc() throw() {}
         CAlloc(const CAlloc&) throw() {}
         template <class U> CAlloc (const CAlloc<U>&) throw() {}
         ~CAlloc() throw() {}

         size_type max_size () const throw() 
            { return std::numeric_limits<std::size_t>::max() / sizeof(T); }

         pointer allocate (size_type num, const void* = 0) 
            { return (pointer)(CA.alloc_(num*sizeof(T))); }

         void construct (pointer p, const T& value) 
            { new((void*)p)T(value); }

          void destroy (pointer p) 
            { p->~T(); }

          void deallocate (pointer p, size_type num) 
            { CA.free_(p); }
   };

   template <class T> bool operator==( const CAlloc<T>& left, const CAlloc<T>& right )
   {
       return true;
   }
 
   template <class T> bool operator!=( const CAlloc<T>& left, const CAlloc<T>& right)
   {
       return false;
   }
}

#endif
