#ifndef THREADSAFE_CONTAINER
#define THREADSAFE_CONTAINER

#include "AtomicInt32.h"

struct ObjectContainer
{
   AtomicInt32 counter_;
   void* object_;
   void* next_;
   unsigned long long id_;

   ObjectContainer(void) : counter_(0), object_(NULL), next_(NULL), id_(0) {}
};

template <typename T> class TSIterator;


template <typename T> class ThreadSafeSTL
{
   public:
      typedef typename T::iterator I;
      typedef typename iterator_traits<I>::value_type V;

   protected:
      ObjectContainer* current_;
      ObjectContainer* expire_;
      ObjectContainer* expireNext_;

      ObjectContainer*  toModify_;
      ObjectContainer*  lastModifyItem_;

      AtomicInt32 writeSema_;
      AtomicInt32 writeLock_;
      AtomicInt32 commitLock_;
      AtomicInt32 deleteLock_;
      AtomicInt32 updateLock_;

      T mainObject_;

      unsigned long long id_;

      void wipeToModify(void)
      {
         if(!toModify_) return;
         while(writeLock_.Fetch_Or(1));

         ObjectContainer* toDelete;

         writeSema_ = 0;
         while(toModify_->next_)
         {
            toDelete = toModify_;
            toModify_ = (ObjectContainer*)toModify_->next_;
            delete (V*)toDelete->object_;
            delete toDelete;
         }

         delete (V*)toModify_->object_;
         delete toModify_;

         toModify_ = NULL;
         lastModifyItem_ = NULL;

         writeLock_ = 0;
      }

      void Modify(V& input, int change)
      {
         ObjectContainer* addMod = new ObjectContainer;
         V* obj = new V;
         *obj = input;

         addMod->object_  = (void*)obj;
         addMod->counter_ = change;

         while(writeLock_.Fetch_Or(1));

         if(lastModifyItem_) lastModifyItem_->next_ = addMod;
         else toModify_ = addMod;
         lastModifyItem_ = addMod;

         writeLock_ = 0;
         writeSema_++;
         commitChanges();
      }

      void commitChanges()
      {
         if(writeSema_ == 0) return;
         if(commitLock_.Fetch_Or(1)) return;

         int addCounter = 0;
         while(writeSema_ != 0 && addCounter < maxMergePerThread_)
         {
            while(updateLock_.Fetch_Or(1));

            if(toModify_->counter_ == 1)
            {
               mainObject_.insert(mainObject_.end(), *(V*)toModify_->object_);
               
               writeSema_--;
               addCounter++;
               toModify_->counter_ = 0;
               id_++;
            }
            else if(toModify_->counter_ == -1)
            {
               I toErase = std::find(mainObject_.begin(), mainObject_.end(), *(V*)toModify_->object_);
               if(toErase != mainObject_.end())
                  mainObject_.erase(toErase);
               
               toModify_->counter_ = 0;
               writeSema_--;
               addCounter++;
               id_++;
            }

            toModify_->counter_ = 0;
            if(toModify_->next_)
            {
               delete (V*)toModify_->object_;
               toModify_ = (ObjectContainer*)toModify_->next_;
            }

            updateLock_ = 0;
         }

         commitLock_ = 0;
         DeleteExpired();
      }

      void DeleteExpired()
      {
         if(!expire_) return;
         if(deleteLock_.Fetch_Or(1)) return;

         ObjectContainer *expireSnapshot = expire_;
         ObjectContainer *lastDeleted    = expire_;
         ObjectContainer *prev;

         bool dontDelete = false;
         while(1)
         {
            if(!expireSnapshot->next_) break;
            
            prev = expireSnapshot;
            expireSnapshot = (ObjectContainer*)expireSnapshot->next_;

            if(expireSnapshot->counter_ == -1 && !dontDelete) 
            {
               lastDeleted = expireSnapshot;
               delete (T*)prev->object_;
               delete prev;
            }
            else if(!expireSnapshot->counter_.Compare_Exchange(0, -1)) 
               dontDelete = true;
         }

         expire_ = lastDeleted;
         deleteLock_ = 0;
      }

   public:
      static const unsigned int maxMergePerThread_ = 1000;

      ThreadSafeSTL(void)
      {
         current_    = NULL;
         expire_     = NULL;
         expireNext_ = NULL;
         
         toModify_       = NULL;
         lastModifyItem_ = NULL; 
         
         writeSema_  = 0; 
         writeLock_  = 0;
         commitLock_ = 0;
         deleteLock_ = 0;
         updateLock_ = 0;

         id_=0;
      }

      ~ThreadSafeSTL(void)
      {
         if(current_)
         {
            T* thelist = (T*)current_->object_;
            delete (T*)current_->object_;
            delete current_;
         }
         
         if(expire_)
         {
            ObjectContainer* toDelete;
            
            while(expire_->next_)
            {
               toDelete = expire_;
               expire_ = (ObjectContainer*)expire_->next_;

               delete (T*)toDelete->object_;
               delete toDelete;
            }

            delete (T*)expire_->object_;
            delete expire_;
         }

         wipeToModify();
      }

      void Add(V input)
      {
         Modify(input, 1);
      }

      void Remove(V input)
      {
         Modify(input, -1);
      }

      void RemoveAndWait(V input)
      {
      }

      ObjectContainer* GetCurrent()
      {
         commitChanges();

         while(1)
         {
            ObjectContainer *toIterate = NULL;

            if(current_)
            {
               if(current_->id_ == id_)
                  toIterate = current_;
            }

            if(toIterate==NULL)
            {
               toIterate = new ObjectContainer;
               T* snapshot = new T;

               while(updateLock_.Fetch_Or(1));
               std::copy(mainObject_.begin(), mainObject_.end(),
                      std::inserter(*snapshot, snapshot->begin()));
               toIterate->id_ = id_;
               updateLock_ = 0;

               toIterate->object_ = (void*)snapshot;

               if(current_)
               {
                  if(expire_) expireNext_->next_ = current_;
                  else expire_ = current_;
                  expireNext_ = current_;
               }

               current_ = toIterate;
            }

            if(toIterate->counter_.Fetch_Add(1) != -1)
            {
               return toIterate;
            }
            else 
            {
               toIterate->id_ = -1;
               toIterate->counter_ = -1;
            }
         }
      }

      virtual bool isInMap(const V& toFind)
      {
         ObjectContainer* toSearch = GetCurrent();
               
         bool found = false;
         T* theObject = (T*)toSearch->object_;
         I result = std::find(theObject->begin(), theObject->end(), toFind);
         if(result != theObject->end())
            found = true;

         toSearch->counter_--;
         return found;
      }

      void clear(void)
      {
         while(commitLock_.Fetch_Or(1));
         wipeToModify();

         while(updateLock_.Fetch_Or(1));
         mainObject_.clear();
         id_++;
         updateLock_ = 0;

         commitLock_ = 0;
         DeleteExpired();
      }
};

template <typename T> class TSIterator
{
   private:
      typedef typename T::iterator I;
      typedef typename iterator_traits<I>::value_type V;
      
      ObjectContainer* container_;

      I iter_;
      bool done;
      I end_;

   public:      
      TSIterator(ObjectContainer* toIterate)
      {
         done = false;
         container_ = toIterate;

         T* object = (T*)(toIterate->object_);
         iter_ = object->begin();
         end_  = object->end();
      }

      ~TSIterator()
      {
         if(!done) container_->counter_.Fetch_Add(-1);
      }

      const I& begin(void)
      {
         T* object = (T*)container_->object_;
         iter_ = object->begin();
         
         return iter_;
      }

      bool end(void)
      {
         bool result = !(iter_ != end_);
         if(result && !done) 
         {
            done = true;
            container_->counter_.Fetch_Add(-1);
         }
         return result;
      }

      I operator++(void)
      {
         return iter_++;
      }

      I operator++(int)
      {
         return iter_++;
      }

      const V& operator* (void)
      {
         return *iter_;
      }
};

template <typename T> class ThreadSafeSTLPair : 
                      public ThreadSafeSTL<T>
{
   private:
      typedef typename T::iterator I;
      typedef typename iterator_traits<I>::value_type V;

      typedef typename V::first_type F;
      typedef typename V::second_type S;

   public:

      typedef struct findResult
      {
         I iter;
         bool found;
      };


      I end_;

      ThreadSafeSTLPair(void) : ThreadSafeSTL() 
      {
         end_ = mainObject_.end();
      }

      void Add(F first, S second)
      {
         std::pair<F, S> toAdd(first, second);

         Modify(toAdd, 1);
      }

      void Remove(F first)
      {
         S second;
         std::pair<F, S> toRemove(first, second);

         Modify(toRemove, -1);
      }

      void Modify(V& input, int change)
      {
         ObjectContainer* addMod = new ObjectContainer;
         V* obj = new V(input.first, input.second);

         addMod->object_  = (void*)obj;
         addMod->counter_ = change;

         while(writeLock_.Fetch_Or(1));

         if(lastModifyItem_) lastModifyItem_->next_ = addMod;
         else toModify_ = addMod;
         lastModifyItem_ = addMod;

         writeLock_ = 0;
         writeSema_++;
         commitChanges();
      }

      void commitChanges()
      {
         if(writeSema_ == 0) return;
         if(commitLock_.Fetch_Or(1)) return;

         int addCounter = 0;
         while(writeSema_ != 0 && addCounter < maxMergePerThread_)
         {
            while(updateLock_.Fetch_Or(1));

            if(toModify_->counter_ == 1)
            {
               mainObject_.insert(mainObject_.end(), *(V*)toModify_->object_);
               
               writeSema_--;
               addCounter++;
               toModify_->counter_ = 0;
            }
            else if(toModify_->counter_ == -1)
            {
               V* toFind = (V*)toModify_->object_;
               I toErase = mainObject_.find(toFind->first);
               if(toErase != mainObject_.end())
                  mainObject_.erase(toErase);
               
               toModify_->counter_ = 0;
               writeSema_--;
               addCounter++;
            }

            toModify_->counter_ = 0;
            if(toModify_->next_)
            {
               delete (V*)toModify_->object_;
               toModify_ = (ObjectContainer*)toModify_->next_;
            }

            id_++;
            updateLock_ = 0;
         }

         commitLock_ = 0;
         DeleteExpired();
      }

      findResult find(const F& toFind)
      {
         ObjectContainer* lookIn = GetCurrent();
         T* lookInObj = (T*)lookIn->object_;

         findResult res;
         res.found = true;

         res.iter = lookInObj->find(toFind);
         if(res.iter == lookInObj->end())
            res.found = false;

         lookIn->counter_--;
         return res;
      }

      S Get(const F& toGet)
      {
         findResult findRes = find(toGet);
         S toReturn;

         if(findRes.found)
            toReturn = (*findRes.iter).second;

         return toReturn;
      }

      bool isInMap (const F& toFind)
      {
         ObjectContainer* toSearch = GetCurrent();
               
         bool found = false;
         T* theObject = (T*)toSearch->object_;
         I result = theObject->find(toFind);
         if(result != theObject->end())
            found = true;

         toSearch->counter_--;
         return found;
      }

      void Set(F& index, S& data)
      {
         while(updateLock_.Fetch_Or(1));

         mainObject_[index] = data;
         id_++;
         
         updateLock_ = 0;
      }
};

#endif