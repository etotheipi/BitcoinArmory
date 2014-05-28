/***
Thread safe STL container classes. Exposes top layer classes that attempt 
to respect STL container syntax while guaranteing the container soundness and
data over concurent read/write.

The class is split between sinlge and pair containers, to support the diverging
mechanics of single type containers (list, vector) and paired ones (map)

YOU CANNOT GET THE CONTAINED OBJECTS BY REFERENCE WITH THESE CLASSES

Get an iterator pointing at the contained object, or use operator[]
when it applies, modify the object, then reassign it to the container:

*with operator[]*
   ts_pair_container<std::map<int, myObj>> tsMap;

   *...populate the container...*

   ts_pair<std::map<int, myObj>> somePair = tsMap[someIndex];
   myObj theObj = somePair.get();

   *...update theObj...*

   somePair = theObj; //updates pair and container

*with snapshot and iterator*

   ts_pair_container<std::map<int, myObj>> tsMap;

   *...populate the container...*

   ts_pair_container<std::vector<int>>::snapshot mapSS(tsMap);
   ts_pair_container<std::vector<int>>::itertor  mapIter;

   mapIter = mapSS.find(someObj);

   if(mapIter != mapSS.end())
      mapIter = newObj; //updates iter, snapshot and container.

The classes function on a 3 layer basis:

1) The "container" class maintains the main object and updates it. It creates 
snapshots of the main object on demand. It can be used to directly insert or
delete objects, as with regular STL containers. The following code is valid:

   ts_container<std::vector<int>> ts_intvector;
   ts_intvector.push_back(1);
   ts_intvector.push_back(10);
   ts_intvector.erase(1)
   ts_intvector.clear();

You cannot iterate over the container class, only snapshots. It does not expose
begin() or end() methods. No find() is exposed either, for the same purpose.
Use a snapshot to find().

The container class exposes the type of its
snapshot and iterator:

   ts_container<T>::snapshot
   ts_container<T>::iterator

2) The "snapshot" class is meant to create snapshots, maintain changes, and
be iterated over. It does not have a void constructor. It will always be
initialized with a 'parent' container object, to which is holds reference:

ts_container<std::list<int>> ts_intlist;
ts_container<std::list<int>>::snapshot tssnapshot_intlist(ts_intlist);

The snapshot behaves like the original STL object it represents. It also 
exposes iterators, as well as begin() and end().

The snapshot primary function is to support iterators, but it is valid 
to grab a snapshot for modification. All changes done to the snapshot (add, 
modify, erase, clear) will be mirrored in its parent container class on the 
fly, so that the next snapshot grabbed from that container will have all 
changes.

Snapshots create the STL object snapshot from the container class by calling
its GetCurrent method. This method creates a copy of the containers main STL
object, and passes that in a ObjectContainer object, and increments its 
reference counter. Once the snapshot object goes out of scope, or destructor 
is called explicitly, the ObjectContainer's reference counter is decremented. 
When that reference counter is 0, the container's garbage collector will clean
it up.

3) The "iterator" class exposes the iterator for snapshots. The main purpose 
of this class is to overload operator= to link the iterator to the snapshot 
from which begin() was called. This allows for modification to each increment 
of the iterator to be mirrored in the snapshot and its container. This behavior
is only available with paired iterators. The following is valid:

   ts_pair_container<std::map<std::string, myobj>> myts_map;

   *...modify the object...*

   ts_pair_container<std::map<std::string, myobj>>::snapshot 
                                                    myts_snapshot(myts_map);

   ts_pair_container<std::map<std::string, myobj>>::iterator iter;

   for(iter = myts_snapshot.begin(); iter != myts_snapshot.end(); iter++)
   {
      myobj modded_obj = (*iter).second
      *...modify modded_obj...*
      iter = modded_obj
   }

This will not work with single containers. Syntax wise, the iterator class is
meant to behave like its STL counter part.

This file contains 2 other classes:

ObjectContainer: all purpose objects container. It comes with a void pointer, 
a reference counter, an id member and a reference to the object next to it.

This class is used to maintain reference and daisy chain objects. It is mainly 
used my the "container" classes, to maintain a list of STL object copies (that
are fed to the snapshots) and the list of modifications to be performed on the
main STL object.

ts_pair: this class is required to expose std::map's ability to modify objects
through operator[] and operator=.

ts_pair_container::operator[] will return a ts_pair object. The ts_pair object
holds a reference to its parent ts_pair_container, and exposes operator=. which
will perform the assignement operation in the parent container.

About cleanup:

The container class has a garbage collection method that runs through the chain
of STL object copies and deletes them when they are not refered to anymore.
The same operation takes place with the queue of modifications, as part of the 
change commiting process. 

This whole garbage collection mechanic could be replaced in favor of 
smart_pointer, but I'm gonna refrain from that for now.
***/

#ifndef THREADSAFE_CONTAINER
#define THREADSAFE_CONTAINER

#include <atomic>
#include <iterator>

struct ObjectContainer
{
   mutable std::atomic<int32_t> counter_;
   void* object_ = nullptr;
   void* next_ = nullptr;
   unsigned long long id_ = 0;
   bool readonly_=false;
};

template <typename T> class ts_pair;

template <typename T> class ts_snapshot;
template <typename T> class ts_pair_snapshot;

template <typename T> class ts_const_snapshot;
template <typename T> class ts_const_pair_snapshot;


template <typename T> class ts_iterator;
template <typename T> class ts_pair_iterator;

template <typename T> class ts_const_iterator;
template <typename T> class ts_const_pair_iterator;


template <typename T> class ts_container
{
   friend class ts_snapshot<T>;
   friend class ts_const_snapshot<T>;

   public:
      typedef typename T::iterator I;
      typedef typename T::const_iterator CI;
      typedef typename std::iterator_traits<I>::value_type obj_type;

   protected:
      
      struct findResult
      {
         CI iter;
         bool found;
      };

      mutable ObjectContainer* current_;
      mutable ObjectContainer* expire_;
      mutable ObjectContainer* expireNext_;

      ObjectContainer*  toModify_;
      ObjectContainer*  lastModifyItem_;

      std::atomic<int32_t> writeSema_;
      std::atomic<int32_t> writeLock_;
      std::atomic<int32_t> commitLock_;
      std::atomic<int32_t> deleteLock_;
      
      mutable std::atomic<int32_t> expireLock_;
      mutable std::atomic<int32_t> updateLock_;

      T mainObject_;

      unsigned long long id_;
      uint32_t nObjects_;

      void WipeToModify(void)
      {
         if(!toModify_) return;
         while(writeLock_.fetch_or(1, std::memory_order_consume));

         ObjectContainer* toDelete;

         writeSema_ = 0;
         while(toModify_->next_)
         {
            toDelete = toModify_;
            toModify_ = (ObjectContainer*)toModify_->next_;
            delete (obj_type*)toDelete->object_;
            delete toDelete;
         }

         delete (obj_type*)toModify_->object_;
         delete toModify_;

         toModify_ = NULL;
         lastModifyItem_ = NULL;

         writeLock_.store(0, std::memory_order_release);
      }

      void Modify(obj_type& input, int change)
      {
         ObjectContainer* addMod = new ObjectContainer;
         obj_type* obj = new obj_type;
         *obj = input;

         addMod->object_  = (void*)obj;
         addMod->counter_ = change;

         while(writeLock_.fetch_or(1, std::memory_order_consume));

         if(lastModifyItem_) lastModifyItem_->next_ = addMod;
         else toModify_ = addMod;
         lastModifyItem_ = addMod;

         writeLock_.store(0, std::memory_order_release);
         writeSema_.fetch_add(1, std::memory_order_release);
         CommitChanges();
      }

      void CommitChanges()
      {
         if(writeSema_ == 0) return;
         if(commitLock_.fetch_or(1, std::memory_order_consume)) return;

         unsigned addCounter = 0;
         while(writeSema_.load(std::memory_order_consume) != 0 \
               && addCounter < maxMergePerThread_)
         {
            while(updateLock_.fetch_or(1, std::memory_order_consume));

            if (toModify_->counter_ == 1)
            {
               mainObject_.insert(mainObject_.end(), 
                                  *(obj_type*)toModify_->object_);
               
               writeSema_--;
               addCounter++;
               toModify_->counter_ = 0;
               id_++;
            }
            else if (toModify_->counter_ == -1)
            {
               I toErase = std::find(mainObject_.begin(), mainObject_.end(), 
                                     *(obj_type*)toModify_->object_);
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
               delete (obj_type*)toModify_->object_;
               toModify_ = (ObjectContainer*)toModify_->next_;
            }

            updateLock_.store(0, std::memory_order_release);
         }

         commitLock_ = 0;
         DeleteExpired();
      }

      void DeleteExpired()
      {
         if(!expire_) return;
         if(deleteLock_.fetch_or(1, std::memory_order_consume)) return;

         ObjectContainer *expireSnapshot = expire_;
         ObjectContainer *lastDeleted    = expire_;
         ObjectContainer *prev;

         bool dontDelete = false;
         while(1)
         {
            if(!expireSnapshot->next_) break;
            
            prev = expireSnapshot;
            expireSnapshot = (ObjectContainer*)expireSnapshot->next_;

            if(expireSnapshot->counter_.load(std::memory_order_consume) == -1 \
               && !dontDelete) 
            {
               lastDeleted = expireSnapshot;
               delete (T*)prev->object_;
               delete prev;
            }
            else
            {
               int expected = 0;
               if (expireSnapshot->counter_.compare_exchange_strong(expected, 
                  -1, std::memory_order_release,
                  std::memory_order_consume))
                  dontDelete = true;
            }
         }

         expire_ = lastDeleted;
         deleteLock_.store(0, std::memory_order_release);
      }

      void Add(obj_type input)
      {
         Modify(input, 1);
      }

      void Remove(obj_type input)
      {
         Modify(input, -1);
      }

      void RemoveAndWait(obj_type input)
      {
         //not implemented yet
      }

      const ObjectContainer* GetConstCurrent(void) const
      {
         while (1)
         {
            ObjectContainer *toIterate = NULL;

            if (current_)
            {
               if (current_->readonly_ && current_->id_ == id_)
                  toIterate = current_;
            }

            if (toIterate == NULL)
            {
               toIterate = new ObjectContainer;
               toIterate->readonly_ = true;
               T* snapshot = new T;

               while (updateLock_.fetch_or(1, std::memory_order_consume));

               std::copy(mainObject_.begin(), mainObject_.end(),
                  std::inserter(*snapshot, snapshot->begin()));
               toIterate->id_ = id_;

               updateLock_.store(0, std::memory_order_release);

               toIterate->object_ = (void*)snapshot;

               while(expireLock_.fetch_or(1, std::memory_order_consume));
               if (current_)
               {
                  if (expire_) expireNext_->next_ = current_;
                  else expire_ = current_;
                  expireNext_ = current_;
               }
               expireLock_.store(0, std::memory_order_release);

               current_ = toIterate;
            }

            if (toIterate->counter_.fetch_add(1,
               std::memory_order_consume) != -1)
            {
               return toIterate;
            }
            else
            {
               toIterate->id_ = -1;
               toIterate->counter_.store(-1, std::memory_order_release);
            }
         }
      }

      ObjectContainer* GetCurrent(void)
      {
         CommitChanges();

         while (1)
         {
            ObjectContainer *toIterate = NULL;

            if (toIterate == NULL)
            {
               toIterate = new ObjectContainer;
               T* snapshot = new T;

               while (updateLock_.fetch_or(1, std::memory_order_consume));

               std::copy(mainObject_.begin(), mainObject_.end(),
                  std::inserter(*snapshot, snapshot->begin()));
               toIterate->id_ = id_;

               updateLock_.store(0, std::memory_order_release);

               toIterate->object_ = (void*)snapshot;

               while (expireLock_.fetch_or(1, std::memory_order_consume));
               if (current_)
               {
                  if (expire_) expireNext_->next_ = current_;
                  else expire_ = current_;
                  expireNext_ = current_;
               }
               expireLock_.store(0, std::memory_order_release);

               current_ = toIterate;
            }

            if (toIterate->counter_.fetch_add(1,
               std::memory_order_consume) != -1)
            {
               return toIterate;
            }
            else
            {
               toIterate->id_ = -1;
               toIterate->counter_.store(-1, std::memory_order_release);
            }
         }
      }

   public:
      typedef ts_snapshot<T> snapshot;
      typedef ts_iterator<T> iterator;

      typedef ts_const_snapshot<T> const_snapshot;
      typedef ts_const_iterator<T> const_iterator;

      //this can get in the way of consting GetCurrent
      static const unsigned int maxMergePerThread_ = 5000;

      ts_container(void)
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
         expireLock_ = 0;

         id_ = 0;
         nObjects_ = 0;
      }

      ~ts_container(void)
      {
         if(current_)
         {
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

         WipeToModify();
      }

      virtual bool contains(const obj_type& toFind) const
      {
         const ObjectContainer* toSearch = GetConstCurrent();
               
         bool found = false;
         T* theObject = (T*)toSearch->object_;
         CI result = std::find(theObject->begin(), theObject->end(), toFind);
         if(result != theObject->end())
            found = true;

         toSearch->counter_.fetch_sub(1, std::memory_order_release);
         return found;
      }

      void clear(void)
      {
         while(commitLock_.fetch_or(1, std::memory_order_consume));
         WipeToModify();

         while(updateLock_.fetch_or(1, std::memory_order_consume));
         mainObject_.clear();
         id_++;
         updateLock_.store(0, std::memory_order_release);

         commitLock_.store(0, std::memory_order_release);
         DeleteExpired();
      }

      void push_back(const obj_type& toAdd)
      {
         Add(toAdd);
      }

      void erase(const obj_type& toErase)
      {
         Remove(toErase);
      }

      void erase(const I& toErase)
      {
         Remove((*toErase));
      }

      uint32_t size(void) const
      {
         return nObjects_;
      }
};

template <typename T> class ts_pair_container :
public ts_container<T>
{
   friend class ts_pair_snapshot<T>;
   friend class ts_pair_iterator<T>;
   friend class ts_pair<T>;

   friend class ts_const_pair_snapshot<T>;
   friend class ts_const_pair_iterator<T>;
      
   public:
      typedef typename ts_container<T>::obj_type::first_type key_type;
      typedef typename ts_container<T>::obj_type::second_type mapped_type;

   private:
      void Add(const key_type& first, const mapped_type& second)
      {
         std::pair<key_type, mapped_type> toAdd(first, second);

         Modify(toAdd, 1);
      }

      void Remove(const key_type& first)
      {
         mapped_type second;
         std::pair<key_type, mapped_type> toRemove(first, second);

         Modify(toRemove, -1);
      }

      void Set(const key_type& index, const mapped_type& data)
      {
         while (this->updateLock_.fetch_or(1, std::memory_order_acquire));

         this->mainObject_[index] = data;
         this->id_++;

         this->updateLock_.store(0, std::memory_order_release);
      }

      void Modify(const typename ts_container<T>::obj_type& input, int change)
      {
         ObjectContainer* addMod = new ObjectContainer;
         typename ts_container<T>::obj_type* obj
            = new typename ts_container<T>::obj_type(input.first, input.second);

         addMod->object_ = obj;
         addMod->counter_ = change;

         while (this->writeLock_.fetch_or(1, std::memory_order_consume));

         if (this->lastModifyItem_) this->lastModifyItem_->next_ = addMod;
         else this->toModify_ = addMod;
         this->lastModifyItem_ = addMod;

         this->writeLock_.store(0, std::memory_order_release);
         this->writeSema_.fetch_add(1, std::memory_order_release);
         CommitChanges();
      }

      void CommitChanges()
      {
         if (this->writeSema_.load(std::memory_order_consume) == 0) return;
         if (this->commitLock_.fetch_or(1, std::memory_order_acquire)) return;

         unsigned addCounter = 0;
         while (this->writeSema_.load(std::memory_order_consume) != 0
            && addCounter < this->maxMergePerThread_)
         {
            while (this->updateLock_.fetch_or(1, std::memory_order_consume));

            if (this->toModify_->counter_ == 1)
            {
               this->mainObject_.insert(this->mainObject_.end(),
                  *static_cast<typename ts_container<T>::obj_type*>(this->toModify_->object_));

               this->toModify_->counter_ = 0;
               this->nObjects_++;
               
               this->writeSema_.fetch_sub(1, std::memory_order_release);
               addCounter++;
            }
            else if (this->toModify_->counter_ == -1)
            {
               typename ts_container<T>::obj_type* toFind = static_cast<typename ts_container<T>::obj_type*>(ts_container<T>::toModify_->object_);
               typename ts_container<T>::I toErase = this->mainObject_.find(toFind->first);
               if (toErase != this->mainObject_.end())
                  this->mainObject_.erase(toErase);

               this->toModify_->counter_ = 0;
               this->nObjects_--;
               
               this->writeSema_.fetch_sub(1, std::memory_order_release);
               addCounter++;
            }

            this->toModify_->counter_ = 0;
            if (this->toModify_->next_)
            {
               delete static_cast<typename ts_container<T>::obj_type*>(this->toModify_->object_);
               this->toModify_ = static_cast<ObjectContainer*>(this->toModify_->next_);
            }

            this->id_++;
            this->updateLock_.store(0, std::memory_order_release);
         }

         this->commitLock_ = 0;
         this->DeleteExpired();
      }

      typename ts_container<T>::findResult Find(const key_type& toFind) const
      {
         const ObjectContainer* lookIn = this->GetConstCurrent();
         T* lookInObj = static_cast<T*>(lookIn->object_);

         typename ts_container<T>::CI iter = lookInObj->find(toFind);

         typename ts_container<T>::findResult res;
         res.iter = iter;
         res.found = false;

         if (iter != lookInObj->end())
            res.found = true;

         lookIn->counter_.fetch_sub(1, std::memory_order_release);
         return res;
      }
      
      mapped_type Get(const key_type& toGet)
      {
         typename ts_container<T>::findResult findRes = this->Find(toGet);
         mapped_type toReturn;

         if (findRes.found)
            toReturn = (*findRes.iter).second;

         return toReturn;
      }

   public:

      typedef ts_pair_snapshot<T> snapshot;
      typedef ts_pair_iterator<T> iterator;
      typedef ts_pair<T> pair;

      typedef ts_const_pair_snapshot<T> const_snapshot;
      typedef ts_const_pair_iterator<T> const_iterator;
      
      bool contains(const key_type& toFind) const
      {
         const ObjectContainer* toSearch = this->GetConstCurrent();

         bool found = false;
         T* theObject = static_cast<T*>(toSearch->object_);
         typename ts_container<T>::CI result = theObject->find(toFind);
         if (result != theObject->end())
            found = true;

         toSearch->counter_.fetch_sub(1, std::memory_order_release);
         return found;
      }

      ts_pair<T> operator[] (const key_type& rhs)
      {
         typename ts_container<T>::findResult toFind = Find(rhs);
         if (toFind.found)
            return ts_pair<T>(toFind.iter, this);
         else
         {
            //default constructor spaghetti
            mapped_type* second = new mapped_type;

            this->Add(rhs, *second);
            
            ts_pair<T> returnPair(rhs, *second, this);
            delete second;

            return returnPair;
         }
      }

      const mapped_type& operator[] (const key_type& rhs) const
      {
         //const version, undefined if the key isnt in map
         typename ts_container<T>::findResult toFind = this->Find(rhs);

         return toFind.iter->second;
      }
};


template<typename T> class ts_snapshot
{
   friend class ts_iterator<T>;

   protected:
      typedef ts_iterator<T> iterator;
      typedef ts_const_iterator<T> const_iterator;
      typedef typename std::iterator_traits<typename T::iterator>::value_type obj_type;

      ts_container<T> *parent_;
      ObjectContainer *cont_;
      T *object_;

   public:
      ts_snapshot(ts_container<T>& parent)
      {
         parent_ = &parent;
         cont_ = parent.GetCurrent();
         object_ = (T*)cont_->object_;
      }

      ~ts_snapshot(void)
      {
         cont_->counter_.fetch_sub(1, std::memory_order_release);
      }

      iterator begin()
      {
         iterator iter;
         iter.Set(object_->begin(), this);
         return iter;
      }

      iterator end()
      {
         iterator iter;
         iter.Set(object_->end(), this);
         return iter;
      }
      
      const_iterator begin() const
      {
         const_iterator iter;
         iter.Set(object_->begin(), this);
         return iter;
      }

      const_iterator end() const
      {
         const_iterator iter;
         iter.Set(object_->end(), this);
         return iter;
      }

      ts_iterator<T> find(const obj_type& toFind)
      {
         ts_iterator<T> iter;
         iter.Set(object_->find(toFind), this);
         return iter;
      }
      
      void push_back(const obj_type& toAdd)
      {
         parent_->Add(toAdd);
         object_->push_back(toAdd);
      }

      void erase(const obj_type toErase)
      {
         parent_->erase(toErase);
         object_->erase(toErase);
      }

      void erase(const iterator& toErase)
      {
         parent_->erase(toErase);
         object_->erase(toErase);
      }
      
      bool contains(const obj_type& f) const
      {
         return find(f) != end();
      }

};

template<typename T> class ts_const_snapshot
{
   protected:
      typedef ts_const_iterator<T> const_iterator;
      typedef typename std::iterator_traits<typename T::const_iterator>::value_type value_type;
      
      const ts_container<T> &parent_;
      const ObjectContainer *const cont_;
      const T *const object_;

   public:
      ts_const_snapshot(const ts_container<T>& parent)
         : parent_(parent)
         , cont_(parent.GetConstCurrent())
         , object_(static_cast<const T*>(cont_->object_))
      { }

      ~ts_const_snapshot()
      {
         cont_->counter_.fetch_sub(1, std::memory_order_release);
      }

      const_iterator begin() const
      {
         const_iterator iter;
         iter.Set(object_->begin(), this);
         return iter;
      }

      const_iterator end() const
      {
         const_iterator iter;
         iter.Set(object_->end(), this);
         return iter;
      }

      const_iterator find(const value_type& toFind) const
      {
         return object_->find(toFind);
      }
      bool contains(const value_type& f) const
      {
         return find(f) != end();
      }
};

template<typename T> class ts_pair_snapshot : private ts_snapshot<T>
{
   friend class ts_pair_iterator<T>;

   private:
      typedef ts_pair_iterator<T> iterator;
      typedef ts_const_pair_iterator<T> const_iterator;
      typedef typename std::iterator_traits<typename T::iterator>::value_type obj_type;

      typedef typename obj_type::first_type key_type;
      typedef typename obj_type::second_type mapped_type;

      ts_pair_container<T> *parent_;

      void Set(key_type& first, const mapped_type& second)
      {
         parent_->Set(first, second);
         (*this->object_)[first] = second;
      }

   public:
      ts_pair_snapshot(ts_pair_container<T>& parent) : ts_snapshot<T>(parent) 
      {
         parent_ = &parent;
      }

      iterator begin()
      {
         iterator iter;
         iter.Set(this->object_->begin(), this);
         return iter;
      }

      iterator end()
      {
         iterator iter;
         iter.Set(this->object_->end(), this);
         return iter;
      }
      
      const_iterator begin() const
      {
         const_iterator iter;
         iter.Set(this->object_->begin(), this);
         return iter;
      }

      const_iterator end() const
      {
         const_iterator iter;
         iter.Set(this->object_->end(), this);
         return iter;
      }

      iterator find(const key_type& toFind)
      {
         iterator return_iter;
         return_iter.Set(this->object_->find(toFind), this);
         return return_iter;
      }
      const_iterator find(const key_type& toFind) const
      {
         const_iterator return_iter;
         return_iter.Set(this->object_->find(toFind), this);
         return return_iter;
      }
      bool contains(const key_type& f) const
      {
         return find(f) != end();
      }
};

template<typename T> class ts_const_pair_snapshot
   : private ts_const_snapshot<T>
{
   private:
      typedef ts_const_pair_iterator<T> const_iterator;
      typedef typename std::iterator_traits<typename T::const_iterator>::value_type value_type;

      typedef typename value_type::first_type key_type;
      typedef typename value_type::second_type mapped_type;

      const ts_pair_container<T> &parent_;

   public:
      ts_const_pair_snapshot(const ts_pair_container<T>& parent) 
         : ts_const_snapshot<T>(parent), parent_(parent)
      { }

      const_iterator begin() const
      {
         ts_const_pair_iterator<T> iter;
         iter.Set(this->object_->begin(), this);
         return iter;
      }

      const_iterator end() const
      {
         ts_const_pair_iterator<T> iter;
         iter.Set(this->object_->end(), this);
         return iter;
      }

      const_iterator find(const key_type& toFind) const
      {
         ts_const_pair_iterator<T> iter;
         iter.Set(this->object_->find(toFind), this);
         return iter;
      }
      bool contains(const key_type& f) const
      {
         return find(f) != end();
      }
};


template <typename T> class ts_iterator
{
   friend class ts_snapshot<T>;
   protected:
      typedef typename T::iterator I;
      typedef typename std::iterator_traits<I>::value_type obj_type;
      
      I iter_;
      ts_snapshot<T> *snapshot_;

      void Set(I iter, ts_snapshot<T>* snapshot)
      {
         iter_ = iter;
         snapshot_ = snapshot;
      }

   public:      
      ts_iterator() {}

      ts_iterator& operator++()
      {
          ++iter_;
          return *this;
      }


      auto operator* () -> decltype(*iter_)
      {
         return *iter_;
      }
      obj_type* operator-> ()
      {
         return &*iter_;
      }

      const obj_type& operator* () const
      {
         return *iter_;
      }
      const obj_type* operator-> () const
      {
         return &*iter_;
      }

      void operator= (const obj_type& rhs)
      {
         iter_ = snapshot_->Set(iter_, rhs);
      }

      bool operator!= (const ts_iterator& rhs) const
      {
         return (iter_ != rhs.iter_);
      }

      bool operator== (const ts_iterator& rhs) const
      {
         return iter_ == rhs.iter_;
      }
};

template <typename T> class ts_const_iterator
{
   friend class ts_const_snapshot<T>;

   protected:
      typedef typename T::const_iterator I;
      typedef typename std::iterator_traits<I>::value_type obj_type;

      I iter_;
      const ts_const_snapshot<T>* snapshot_=nullptr;
   
      void Set(I iter, const ts_const_snapshot<T>* snapshot)
      {
         iter_ = iter;
         snapshot_ = snapshot;
      }

   public:
      ts_const_iterator() {}

      ts_const_iterator operator++()
      {
         ++iter_;
         return *this;
      }

      const obj_type& operator* () const
      {
         return *iter_;
      }
      
      const obj_type* operator-> () const
      {
         return &*iter_;
      }

      bool operator!= (const ts_const_iterator& rhs) const
      {
         return (iter_ != rhs.iter_);
      }

      bool operator== (const ts_const_iterator& rhs) const
      {
         return iter_ == rhs.iter_;
      }
};


template <typename T> class ts_pair_iterator :
                      public ts_iterator<T>
{
   friend class ts_pair_snapshot<T>;

   private:
      typedef typename ts_iterator<T>::obj_type::first_type key_type;
      typedef typename ts_iterator<T>::obj_type::second_type mapped_type;

      ts_pair_snapshot<T> *snapshot_ = nullptr;

      void Set(const typename ts_iterator<T>::I& iter, ts_pair_snapshot<T>* snapshot)
      {
         snapshot_ = snapshot;
         this->iter_ = iter;
      }

   public:
      void operator= (const mapped_type& rhs)
      {
         T& object = *snapshot_->object_;

         object[this->iter_->first] = rhs;
         snapshot_->Set(this->iter_->first, rhs);
      }
};

template <typename T> class ts_const_pair_iterator :
public ts_const_iterator<T>
{
   friend class ts_const_pair_snapshot<T>;

   protected:
      const ts_const_pair_snapshot<T>* snapshot_=nullptr;

      void Set(const typename ts_const_iterator<T>::I& iter, const ts_const_pair_snapshot<T>* snapshot)
      {
         snapshot_ = snapshot;
         this->iter_ = iter;
      }

   public:
      bool operator!= (const ts_const_pair_iterator& rhs) const
      {
         return (this->iter_ != rhs.iter_);
      }
      bool operator== (const ts_const_pair_iterator& rhs) const
      {
         return (this->iter_ == rhs.iter_);
      }
};



template <typename T> class ts_pair
{
   private:
      typedef typename T::iterator I;
      typedef typename T::const_iterator CI;
      typedef typename std::iterator_traits<I>::value_type value_type;

      typedef typename value_type::first_type key_type;
      typedef typename value_type::second_type mapped_type;
   
      ts_pair_container<T> *container_;
      key_type first_;
      mapped_type second_;

   public:

      ts_pair(const key_type& f, const mapped_type& s,
         ts_pair_container<T> * const cont) :
         first_(f) 
      {
         second_ = s;
         container_ = cont;
      }

      ts_pair(const I &iter, ts_pair_container<T> *cont) :
         first_((*iter).first)
      {
         second_ = (*iter).second;
         container_ = cont;
      }

      ts_pair(const CI &iter, ts_pair_container<T> *cont) :
         first_((*iter).first)
      {
         second_ = (*iter).second;
         container_ = cont;
      }

      mapped_type& operator= (const mapped_type& rhs)
      {
         container_->Set(first_, rhs);
         second_ = rhs;

         return second_;
      }

      const mapped_type& get(void) const
      {
         return second_;
      }
};
#endif