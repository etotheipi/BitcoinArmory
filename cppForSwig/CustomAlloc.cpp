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

   size_t memMinHardTop = 1024*1024*200;
   size_t memMaxHardTop = 1024*1024*1024;

   size_t extendLockedMemQuota()
   {
      /***
      Sets the quota for locked memory.
      This function is meant to allow the process to dynamically grow its
      mlockable memory base. A hard ceiling is set at 100mb.
      ***/

      int rt = 0;
	   
      size_t pageSize = getPageSize();
      size_t mintop = memMinHardTop / pageSize;
		size_t maxtop = memMaxHardTop / pageSize;

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

      //all values have to be a multiple of the system pagesize

      size_t mincurrent, maxcurrent;

      HANDLE processHandle = GetCurrentProcess();
      GetProcessWorkingSetSize(processHandle, (PSIZE_T)&mincurrent, (PSIZE_T)&maxcurrent);

      if(!SetProcessWorkingSetSize(processHandle, mintop * pageSize, maxtop * pageSize)) rt = mincurrent;

   #else
   //*nix code goes here
   
      rlimit rlm;
      getrlimit(RLIMIT_MEMLOCK, &rlm);
      size_t soft_limit = rlm.rlim_cur;

      rlm.rlim_cur = mintop * pageSize;
      rlm.rlim_max = mintop * pageSize;

      if(setrlimit(RLIMIT_MEMLOCK, &rlm)) rt = soft_limit;
      getrlimit(RLIMIT_MEMLOCK, &rlm);
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
   }

   BufferHeader* MemPool::GetBH(unsigned int size)
   {
	   //check to see if a bh isn't already available
      BufferHeader *bhtmp = 0;
      unsigned int i;

		for(i=0; i<nBH; i++)
		{
			if(BH[i]->linuse==0)
			{
            bhtmp = BH[i];
            break;
			}
	   }

		if(!bhtmp)
		{
			if(nBH==totalBH)
			{
				totalBH+=BHstep;
				BufferHeader **bht;

				while(!(bht=(BufferHeader**)malloc(sizeof(BufferHeader*)*totalBH)));
				while(!(bhtmp=(BufferHeader*)malloc(sizeof(BufferHeader)*BHstep)));				
            memcpy(bht, BH, sizeof(BufferHeader*)*nBH);
				for(i=0; i<BHstep; i++)
					bht[nBH+i] = bhtmp +i;

				free(BH);
				BH = bht;

            free(bhorder);
            while(!(bhorder=(int*)malloc(sizeof(int)*totalBH)));
			}

			bhtmp = BH[nBH];
			bhtmp->reset();
			bhtmp->index = nBH;
			bhtmp->ref = (void*)this;
			nBH++;
		}

      bhtmp->size = size;
      bhtmp->offset = 0;
	   bhtmp->linuse = 1;

      return bhtmp;
   }
		
   void* MemPool::GetPool()
   {
      return (void*)pool;
   }

   void MemPool::Alloc(unsigned int size)
   {
	   while(!pool)
		   pool = (byte*)malloc(size);

      passedQuota = !mlock(pool, size);
				
      total = size;
		freemem = size;
   }

   void MemPool::Free()
   {
      if(passedQuota)
         munlock(pool, total);
         
		free(pool);
      pool=0;
		passedQuota=0;

      total=0;
      reserved=0;

		ngaps = 0;
		freemem = 0;
		pool = 0;
   }

   void MemPool::ExtendGap()
   {
      gaps = (Gap*)realloc(gaps, sizeof(Gap)*(total_ngaps +BHstep));
		memset(gaps +total_ngaps, 0, sizeof(Gap)*BHstep);
      total_ngaps += BHstep;
   }

   void MemPool::AddGap(BufferHeader *bh)
   {
      if(acquireGap.Fetch_Or(1)) return;
      if(ngaps == total_ngaps) ExtendGap();
     
		gaps[ngaps].position = (size_t)bh->offset - size_of_ptr;
		gaps[ngaps].size = bh->size;
		gaps[ngaps].end = (size_t)bh->offset + bh->size - size_of_ptr;

      ngaps++;

      acquireGap = 0;
   }

   int MemPool::GetGap(size_t size)
   {
      int offset = 0;

      int i, g=-3, t, f;
      Gap lgap(0, total);
   
      while(g<-1 && ngaps)
      {
         if(g==-2)
         {
            f=0;
            if(nBH>0)
               int rrt = 0;

            for(i=0; i<nBH; i++)
            {
               if(BH[i]->linuse)
                  bhorder[f++] = i;
            }

            t=f;
            while(t)
            {
               t = 0;
               for(i=1; i<f; i++)
               {
                  if(BH[bhorder[i-1]]->offset>BH[bhorder[i]]->offset)
                  {
                     t = bhorder[i];
                     bhorder[i] = bhorder[i-1];
                     bhorder[i-1] = t;

                     t = 1; 
                  }
               }
            }

            size_t bpos  = (size_t)pool;
				size_t offs;

            while(acquireGap.Fetch_Or(1));
            ngaps = 0;

            for(i=0; i<f; i++)
            {
					offs = (size_t)BH[bhorder[i]]->offset - size_of_ptr; 
					if(offs > 0)
					{
						if(offs != bpos)
						{
							//add a gap
							if(ngaps >= total_ngaps) ExtendGap();
							gaps[ngaps].position = bpos;
							gaps[ngaps].end = offs;

							gaps[ngaps].size = gaps[ngaps].end - gaps[ngaps].position;
							ngaps++;
						}

						bpos = offs +BH[bhorder[i]]->size;  
					}
            } 
            
            acquireGap = 0;
            reserved = bpos - (size_t)pool;  
         }

         for(i=0; i<(int)ngaps; i++)
         {
            if(gaps[i].size>=size && gaps[i].size<lgap.size)
            {
               lgap = gaps[i];
               g = i-1;

				   if(lgap.size==size) break;
            }
         }

         g++;

         if(total - reserved > size) break;
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
      else freemem.Fetch_Add(-size);

      return offset;
   }
		
   BufferHeader* MemPool::GetBuffer(unsigned int size)
   {
	   if(lockpool.Fetch_Or(1)) return 0;
 
      size+=size_of_ptr; 
	   if(!total) 
	   {
		   if(size<memsize) Alloc(memsize);
		   else Alloc(size);
	   }
	   else if(freemem<size) 
	   {
		   lockpool--;
		   return 0;
	   }

      int offset = GetGap(size);
	   if(!offset)
      {
    	   lockpool--;
         return 0;
      }

      BufferHeader *bhtmp = GetBH(size);

      if(!bhtmp) 
      {
         lockpool--;
         return 0;
      }

      bhtmp->offset = (byte*)offset +size_of_ptr;
      memcpy((void*)offset, &bhtmp, size_of_ptr);

	   bhtmp->move = 0;
	   lockpool--;
	   return bhtmp;
   }

   void* CustomAllocator::customAlloc(size_t size)
   {
		if(!size) return 0;
      BufferHeader *bh = GetBuffer(size);
      return (void*)bh->offset;
   }

   void CustomAllocator::customFree(void *buffer)
   {
      BufferHeader *bh = (BufferHeader*)*(size_t*) \
                         ((size_t)buffer -MemPool::size_of_ptr);
      if(bh->linuse==1)
      {
         memset(bh->offset, 0, bh->size-MemPool::size_of_ptr);
         MemPool *mp = (MemPool*)bh->ref;
         mp->AddGap(bh);
         bh->offset = 0;
         mp->freemem.Fetch_Add(bh->size);
         bh->linuse = 0;

         if(mp->freemem==mp->total)
         {
            CustomAllocator *ca = (CustomAllocator*)mp->ref;
            if(ca) ca->FreePool(mp);
         }
      }
   }

   BufferHeader* CustomAllocator::GetBuffer(unsigned int size)
   {
	   unsigned int i;
	   MemPool *mp;
	   BufferHeader *bh;
			
	   fetchloop:
   
      while((i=bufferfetch.Fetch_Add(1))<npools)
	   {
		   mp = MP[order[i]];

		   if(!mp->total || mp->freemem.Get() + size < mp->total) 
		   {
			   bh = mp->GetBuffer(size);
			   if(bh)
			   {
				   bufferfetch = 0;
				   return bh;
            } 
            UpdateOrder(order[i]);
         }
	   }
		
      bufferfetch = 0;				
      ExtendPool(poolstep);
		   
	   goto fetchloop;
   }

   void CustomAllocator::UpdateOrder(unsigned int in)
   {
		pool_height[in]++;
	   
		if(orderlvl.Fetch_Add(1)==poolstep*2)
	   {
 			unsigned int g=1, t;
			
			while(g)
			{
				g=0;
				for(t=1; t<npools; t++)
				{
					if(pool_height[order[t-1]] > pool_height[order[t]])
					{
						g = order[t-1];
						order[t-1] = order[t];
						order[t] = g;

						g = 1;
					}
				}
			}
				
         orderlvl = 0;
	   }
   }

   void CustomAllocator::ExtendPool(unsigned int step)
   {
      if(ab.Fetch_Or(1)) return;

	   unsigned int I;
      int T, F;
	   int S = npools +step -clearpool.Get();

      T = step - clearpool.Get();
      F = clearpool.Get();
      if((int)step<F) F = step;
      
      if(F>-1)
      {
         clearpool.Fetch_Add(-F);         

         for(I=0; I<npools; I++)
         {
            if(MP[I]->lockpool>1)
            {
               MP[I]->lockpool.Fetch_Add(-2);
               F--;

               if(!F) break;
            }
         }
      }

      if(T>0) 
      {
         free(MP2);
	      MP2 = (MemPool**)malloc(sizeof(MemPool*)*S);
	      memcpy(MP2, MP, sizeof(MemPool*)*npools);

	      free(order2);
	      order2 = (unsigned int*)malloc(sizeof(int)*S);
	      for(I=0; I<npools; I++)
            order2[I+T] = I;
			
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

	      for(I=npools; I<S; I++)
	      {
		      F = I-npools;
		      MP2[I] = &mptmp3[F];
            MP2[I]->ref = this;
		      order2[F] = I;
	      }

	      MP = MP2;
         MP2 = mptmp2;

	      unsigned int *ordtmp = order;
	      order = order2;
         order2 = ordtmp;

   	   npools = S;
      }

	   ab = 0;
   }

   void CustomAllocator::FreePool(MemPool *pool)
   {
      unsigned int i = pool->lockpool.Fetch_Or(2);             
      
      if(i<2) clearpool++;

      if(!(i % 2))
      {
         if(canlock || !pool->passedQuota)
            pool->Free();
      }
   }
		
   void CustomAllocator::FillRate()
   {
	   unsigned int i, hd=0, ld=0, tfmem=0;
      //hd: high density
      //ld: low density
	   float c;
   
	   /*for(i=0; i<npools; i++)
	   {
		   c = (float)MP[i]->freemem/(float)MP[i]->total;
		   if(c<=0.2f) hd++;
		   else if(c>=0.8f) ld++;

         tfmem += MP[i]->freemem;
	   }

	   float fhd = (float)hd/(float)npools;
	   float fld = (float)ld/(float)npools;*/
   }

   CustomAllocator CAllocStatic::CA;

   void* CAllocStatic::alloc_(size_t size)
      {return CA.customAlloc(size);
		//return malloc(size);
	}
         
   void  CAllocStatic::free_(void* buffer)
      {CA.customFree(buffer);
		//free(buffer);
	}

}
