#include "CustomAlloc.h"

namespace CustomAlloc
{  
   size_t getPageSize()
   {
      #ifdef _MSC_VER
         SYSTEM_INFO si;
	      GetSystemInfo(&si);   

         return si.dwPageSize;
      #else
         return sysconf(_SC_PAGE_SIZE);
      #endif
   }

   size_t getPoolSize()
   {
      //align the mempool size to the multiple of the pagesize closest to target
      size_t pageSize = getPageSize();
      size_t target = 512*1024;


      if(pageSize < target)
      {
         int mult = target / pageSize +1;
         pageSize *= mult;
      }

      return pageSize;
   }

   size_t memMinHardTop = 1024*1024*100;
   size_t memMaxHardTop = 1024*1024*1024;

   #ifdef _MSC_VER
      HANDLE processHandle = GetCurrentProcess();
   #endif

   int extendLockedMemQuota(int64_t quota)
   {
      /***
      Sets the quota for locked memory.
      This function is meant to allow the process to dynamically grow its
      mlockable memory base. A hard ceiling is set at 100mb.
      ***/

      int rt = 0;

   #ifdef _MSC_VER
      /***
      MSVC only approach: WinAPI's SetProcessWorkingSetSize:
      A few rules to follow with this API call:
      1) Windows requires 20 memory pages of overhead
      2) Your lockable memory is defined only by the minimum value
      3) The maximum value defines how much maximum RAM Windows will try to 
      reserve for this process in case of system wide memory shortage.
      Essentially this is just a guideline as memory is delivered on a first
      come first served basis. Set to 1GB for good measure.
      ***/
      size_t pageSize = getPageSize();

      //all values have to be a multiple of the system pagesize

      size_t mincurrent, maxcurrent;

      GetProcessWorkingSetSize(processHandle, (PSIZE_T)&mincurrent, (PSIZE_T)&maxcurrent);

      mincurrent /= pageSize;
      if(mincurrent<20) mincurrent = 20;

      quota = (int64_t)mincurrent + quota/(int64_t)pageSize +1;

      size_t mintop = memMinHardTop / pageSize;
      size_t maxtop = memMaxHardTop / pageSize;

      if(quota>mintop) 
      {
         quota = mintop;
         rt = -1;
      }

      if(!SetProcessWorkingSetSize(processHandle, (size_t)quota * pageSize, maxtop * pageSize)) rt = -1;

   #else
   //*nix code goes here
   #endif

      return rt;
   }

   const size_t MemPool::memsize = getPoolSize();
   AtomicInt32 MemPool::lock = 0;

   void Gap::reset()
   {
      position = 0;
      size = 0;
		end = 0;
   }

   void BufferHeader::reset()
   {
      memset(this, 0, sizeof(BufferHeader));
      pinuse = &linuse;
   }

   BufferHeader* MemPool::GetBH(unsigned int size)
   {
	   //check to see if a bh isn't already available
      BufferHeader *bhtmp = 0;
      unsigned int i;

	   if(size>0)
	   {
		   for(i=0; i<nBH; i++)
		   {
			   if(!BH[i]->pinuse || *BH[i]->pinuse==0)
			   {
               bhtmp = BH[i];
               break;
			   }
		   }
	   }
      else return 0;

		if(!bhtmp)
		{
			if(nBH==totalBH)
			{
				totalBH+=BHstep;
				BufferHeader **bht;

				while(!(bht = (BufferHeader**)malloc(sizeof(BufferHeader*)*totalBH)));
				while(!(bhtmp = (BufferHeader*)malloc(sizeof(BufferHeader)*BHstep)));
				memcpy(bht, BH, sizeof(BufferHeader*)*nBH);
				for(i=0; i<BHstep; i++)
					bht[nBH+i] = bhtmp +i;

				free(BH);
				BH = bht;
			}

			bhtmp = BH[nBH];
			bhtmp->reset();
			bhtmp->index = nBH;
			bhtmp->ref = (void*)this;
			nBH++;
		}

      bhtmp->size = size +size_of_ptr;
      bhtmp->offset = 0;
      bhtmp->pinuse = &bhtmp->linuse;
	   bhtmp->linuse = 1;

      return bhtmp;
   }
		
   void* MemPool::GetPool()
   {
      return (void*)pool;
   }

   void MemPool::Alloc(unsigned int size)
   {
      while(lock.Fetch_Or(1));
      passedQuota = !extendLockedMemQuota(size);
      lock = 0;

	   while(!pool)
		   pool = (byte*)malloc(size);

      if(passedQuota) mlock(pool, size);
				
      total = size;
	  freemem = size;
   }

   void MemPool::Free()
   {
      if(passedQuota)
      {
         munlock(pool, total);
         free(pool);

         while(lock.Fetch_Or(1));
         extendLockedMemQuota((int)total*-1);
         lock = 0;
      }
      else free(pool);

      total=0;
      reserved=0;

		ngaps = 0;
		freemem = 0;
		pool = 0;
   }

   void MemPool::ExtendGap()
   {
      gaps = (Gap*)realloc(gaps, sizeof(Gap)*(total_ngaps +BHstep));

      total_ngaps += BHstep;
   }

   void MemPool::AddGap(BufferHeader *bh)
   {
      while(acquireGap.Fetch_Or(1));

      if((size_t)bh->offset - (size_t)pool +bh->size -size_of_ptr == reserved)
		{
         reserved -= bh->size;
			size_t respos = (size_t)pool + reserved;
			for(int g=0; g<ngaps; g++)
			{
				if(gaps[g].end==respos)
				{
					reserved -= gaps[g].size;
					gaps[g] = gaps[ngaps-1];
					ngaps--;
					break;
				}
			}
		}
      else
      {
			int bf = -1, af = -1, g=0;
			size_t bhend = (size_t)bh->offset + bh->size -size_of_ptr;
			size_t bhstart = (size_t)bh->offset -size_of_ptr;

			for(g; g<ngaps; g++)
			{
				if(gaps[g].end==bhstart)
				{
					bf = g;
					if(af>-1) break;
				}
				else if(gaps[g].position==bhend)
				{
					af = g;
					if(bf>-1) break;
				}
			}

			if(bf>-1)
			{
				gaps[bf].end = bhend;

				if(af>-1)
				{
					gaps[bf].end = gaps[af].end;
					gaps[bf].size = gaps[bf].end - gaps[bf].position;
					
					gaps[af] = gaps[ngaps-1];
					ngaps--;
				}
				else gaps[bf].size += bh->size;
			}
			else if(af>-1)
			{
				gaps[af].position = bhstart;
				gaps[af].size += bh->size;
			}
			else
			{
				if(ngaps == total_ngaps) ExtendGap();
      
				gaps[ngaps].position = bhstart;
				gaps[ngaps].size = bh->size;
				gaps[ngaps].end = bhend;

				ngaps++;
			}
      }

      freemem += bh->size;

      acquireGap = 0;
   }

   int MemPool::GetGap(size_t size)
   {
      int offset = 0;
      while(acquireGap.Fetch_Or(1));

      int i, g=-1;
      Gap lgap(0, total);
   
      for(i=0; i<ngaps; i++)
      {
         if(gaps[i].size>=size && gaps[i].size<lgap.size)
         {
            lgap = gaps[i];
            g = i;

				if(lgap.size==size) break;
         }
      }

      if(g>-1)
      {
         offset = lgap.position;
      
         if(size<lgap.size)
         {
            gaps[g].position += size;
            gaps[g].size -= size;
         }
         else
         {
            gaps[g].reset();
            memcpy(gaps +g, gaps +g+1, sizeof(Gap)*(ngaps -g -1));
            ngaps--;
         }
      }
      else 
      {
         offset = (size_t)pool +reserved;
         reserved += size;
      }

      if((size_t)(offset -(size_t)pool +size) > total) 
      {
         offset = 0;
         reserved -= size;
      }
      else freemem -= size;

      acquireGap = 0;

      return offset;
   }
		
   BufferHeader* MemPool::GetBuffer(unsigned int size, unsigned int *sema) //needs fixing
   {
      size+=size_of_ptr; //extra bytes to point at the bh

	   if(lockpool.Fetch_Or(1)) return 0; //pools are meant to function as single threaded
	   if(!total) 
	   {
		   if(size<memsize) Alloc(memsize);
		   else Alloc(size);
	   }
	   else if(size>freemem) 
	   {
		   lockpool = 0;
		   return 0;
	   }

      int offset = GetGap(size);
      //int offset = (size_t)pool + reserved;
	   if(!offset)// || reserved+size>total)
      {
    	   lockpool = 0;
         return 0;
      }

      //reserved += size;
		//freemem -= size;

      BufferHeader *bhtmp = GetBH(size -size_of_ptr);

      if(!bhtmp) 
      {
         lockpool = 0;
         return 0;
      }

      bhtmp->offset = (byte*)offset +size_of_ptr;
      memcpy((void*)offset, &bhtmp, size_of_ptr);

	   if(sema) bhtmp->pinuse=sema;
	   bhtmp->move = 0;
	   lockpool = 0;
	   return bhtmp;
   }

   void* CustomAllocator::customAlloc(size_t size)
   {
      //returns mlocked buffer of lenght 'size' (in bytes)
      BufferHeader *bh = GetBuffer(size, 0);
      return (void*)bh->offset;
   }

   void CustomAllocator::customFree(void *buffer)
   {
      //Nulls a buffer previously allocated by customAlloc and marks it as unused
      //frees empty pools
      BufferHeader *bh = (BufferHeader*)*(size_t*)((size_t)buffer -MemPool::size_of_ptr);
      if(bh->linuse==1)
      {
         memset(bh->offset, 0, bh->size-MemPool::size_of_ptr);
         MemPool *mp = (MemPool*)bh->ref;
         mp->AddGap(bh);
         bh->offset = 0;
         *(bh->pinuse) = 0;

         if(mp->freemem==mp->total)
         {
            CustomAllocator *ca = (CustomAllocator*)mp->ref;
            if(ca) ca->FreePool(mp);
         }
      }
   }

   BufferHeader* CustomAllocator::GetBuffer(unsigned int size, unsigned int *sema)
   {
	   /*** set new lock system here ***/

	   unsigned int i;
	   MemPool *mp;
	   BufferHeader *bh;
			
	   fetchloop:
	   if(clearpool==0) getpoolflag++;
      else goto waithere;
   
      while((i=bufferfetch.Fetch_Add(1))<npools)
	   {
		   mp = MP[order[i]];

		   if(!mp->total || (mp->freemem>=size && (mp->reserved +size+4)<mp->total)) //look for available size
		   {
	         getpoolflag--;
			   bh = mp->GetBuffer(size, sema);
			   if(bh)
			   {
				   bufferfetch = 0;
				   UpdateOrder(order[i]);
				   return bh;
            }
			   else 
            {
               UpdateOrder(order[i]);
               if(clearpool==0) getpoolflag++;
               else goto waithere;
            }
		   }
	   }
						
	   getpoolflag--;

	   //either all pools are locked or they're full, add a new batch of pools
      while(getpoolflag!=0);


      if(!ab.Fetch_Or(1))
	   {
		   bufferfetch = npools;
		   ExtendPool();
		   bufferfetch = 0;
		   ab = 0;
	   }

      waithere:
	   while(ab!=0);
	   goto fetchloop;
   }

   void CustomAllocator::UpdateOrder(unsigned int in)
   {
		pool_height[in]++;
	   
		if(orderlvl.Fetch_Add(1)==poolstep*2)
	   {
		   while(ab!=0); //extendpool lock
		   ordering = 1;
				
		   unsigned int *ordtmp;

			unsigned int g=1, t;
			memcpy(order2, order, sizeof(int)*total);
			while(g)
			{
				g=0;
				for(t=1; t<total; t++)
				{
					if(pool_height[order2[t-1]] > pool_height[order2[t]])
					{
						g = order2[t-1];
						order2[t-1] = order2[t];
						order2[t] = g;

						g = 1;
					}
				}
			}
				
		   ordtmp = order;
		   order = order2;
		   order2 = ordtmp;
				
		   orderlvl = 0;
		   ordering = 0;
	   }
   }

   void CustomAllocator::ExtendPool()
   {
	   while(ordering!=0); //updateorder lock

	   unsigned int F, I;
      int T;
	   unsigned int S = npools +poolstep;

      T = S - total;
      if(T>0) 
      {
	      MemPool **mptmp = (MemPool**)malloc(sizeof(MemPool*)*S);
	      memcpy(mptmp, MP, sizeof(MemPool*)*total);

	      unsigned int *ordtmp = order2;
	      order2 = (unsigned int*)malloc(sizeof(int)*S);
	      memcpy(order2 +T, order, sizeof(int)*total);
			
	      MemPool **mptmp2 = MP;
	      MemPool *mptmp3 = new MemPool[T];
      
         poolbatch = (MemPool**)realloc(poolbatch, sizeof(MemPool*)*(nbatch+1));
         poolbatch[nbatch] = mptmp3;
         nbatch++;

			free(pool_height2);
			pool_height2 = (unsigned int*)malloc(sizeof(int)*S);
			memset(pool_height2, 0, sizeof(int)*S);

			unsigned int *phtmp = pool_height;
			pool_height = pool_height2;
			pool_height2 = phtmp;

	      for(I=total; I<S; I++)
	      {
		      F = I-total;
		      mptmp[I] = &mptmp3[F];
            mptmp[I]->ref = this;
		      order2[F] = I;

				int efg=0;
	      }

	      orderlvl=0;
   
         MP = mptmp;

	      free(ordtmp);
	      ordtmp = order;
	      order = order2;
			
	      order2 = (unsigned int*)malloc(sizeof(int)*S);
	      free(ordtmp);
	      free(mptmp2);
   
         total = S;
      }

	   npools = S;
   }

   void CustomAllocator::FreePool(MemPool *pool)
   {
      unsigned int i=0;
            
		while(ab.Fetch_Or(1));

      clearpool = 1;

      while(ordering!=0);
      while(getpoolflag!=0);
   
      for(i; i<npools; i++)
      {
         if(pool->GetPool()==MP[order[i]]->GetPool())
         {
            if(pool->freemem==pool->total)
            {
               MP[order[i]]->Free();
                  
               unsigned int iswap = order[i];
               order[i] = order[npools-1];
               order[npools-1] = iswap;

               npools--;
            }

            clearpool = 0;
            ab = 0;

            return;
         }
      }

		clearpool = 0;
      ab = 0;
   }
		
   void CustomAllocator::FillRate()
   {
	   unsigned int i, hd=0, ld=0, tfmem=0;
      //hd: high density
      //ld: low density
	   float c;
   
	   for(i=0; i<npools; i++)
	   {
		   c = (float)MP[i]->freemem/(float)MP[i]->total;
		   if(c<=0.2f) hd++;
		   else if(c>=0.8f) ld++;

         tfmem += MP[i]->freemem;
	   }

	   float fhd = (float)hd/(float)npools;
	   float fld = (float)ld/(float)npools;
   }

   CustomAllocator CAllocStatic::CA;

   void* CAllocStatic::alloc_(size_t size)
      {return CA.customAlloc(size);}
         
   void  CAllocStatic::free_(void* buffer)
      {CA.customFree(buffer);}

}
