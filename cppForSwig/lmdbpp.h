#ifndef LMDBPP_H
#define LMDBPP_H

#include <string>
#include <stdexcept>
#include <deque>
#include <vector>
#include <atomic>
#include <unordered_map>
#include "pthread.h"
#include <atomic>


struct MDB_env;
struct MDB_txn;
struct MDB_cursor;

enum TXN_MODE
{
   TXN_READONLY,
   TXN_READWRITE
};

// this exception is thrown for all errors from LMDB
class LMDBException : public std::runtime_error
{
public:
   LMDBException(const std::string &what)
      : std::runtime_error(what)
   { }
};

class NoValue : public LMDBException
{
public:
   NoValue(const std::string &what)
      : LMDBException(what)
   { }

};

// a class that stores a pointer to a memory block
class CharacterArrayRef
{
public:
   const size_t len;
   const char *data;
   
   CharacterArrayRef(const size_t len, const char *data)
      : len(len), data(data)
   { }
   CharacterArrayRef(const size_t len, const unsigned char *data)
      : len(len), data(reinterpret_cast<const char*>(data))
   { }
   CharacterArrayRef(const std::string &data)
      : len(data.size()), data(&data[0])
   { }
   CharacterArrayRef(const std::vector<char> &data)
      : len(data.size()), data(&data.front())
   { }
};


class LMDB
{
public:
   class Iterator;
   class Transaction;

   enum Mode
   {
      ReadOnly,
      ReadWrite
   };

private:
   MDB_env *env;
   // exists only with a Tx
   unsigned int dbi;

   //one mother-txn per thread
   struct ThreadTxInfo
   {
      MDB_txn *txn_=nullptr;

      std::deque<Iterator*> iterators_;
      unsigned transactionLevel_ = 0;
      Mode mode_ = ReadOnly;
   };
   
   std::unordered_map<pthread_t, ThreadTxInfo> txForThreads_;
      
   friend class Iterator;   

public:
   // this class can be used like a C++ iterator,
   // or you can just use isValid() to test for "last item"

   class Iterator
   {
      friend class LMDB;
      
      LMDB *db_=nullptr;
      mutable MDB_cursor *csr_=nullptr;
      
      mutable bool hasTx=true;
      bool has_=false;
      ThreadTxInfo* txnPtr_=nullptr;
      std::string key_, val_;
         
      void reset();
      void checkHasDb() const;
      void checkOk() const;
      
      void openCursor();
      
      Iterator(LMDB *db);

      
   public:
      Iterator() : txnPtr_(nullptr) { }
      ~Iterator();
      
      // copying permitted (encouraged!)
      Iterator(const Iterator &copy);
      Iterator(Iterator &&move);
      Iterator& operator=(Iterator &&move);
      Iterator& operator=(const Iterator &copy);
      
      // Returns true if the key pointed to is identical, or if both iterators
      // are invalid, and false otherwise.
      // returns true if the key pointed to is in different databases
      bool operator==(const Iterator &other) const;
      // the inverse
      bool operator!=(const Iterator &other) const
      {
         return !operator==(other);
      }
      
      enum SeekBy
      {
         Seek_EQ,
         Seek_GE,
         Seek_LE
      };
      
      // move this iterator such that, if the exact key is not found:
      // for e == Seek_EQ
      // The cursor is left as Invalid.
      // for e == Seek_GE
      // The cursor is left pointing to the smallest key in the database that is
      // larger than (key). If the database contains no keys larger than
      // (key), the cursor is left as Invalid.
      void seek(const CharacterArrayRef &key, SeekBy e = Seek_EQ);
      
      // is the cursor pointing to a valid location?
      bool isValid() const { return has_; }
      operator bool() const { return isValid(); }
      bool isEOF() const { return !isValid(); }

      // advance the cursor
      // the postfix increment operator is not defined for performance reasons
      Iterator& operator++() { advance(); return *this; }
      void advance();
      
      Iterator& operator--() { retreat(); return *this; }
      void retreat();
      
      // seek this iterator to the first sequence
      void toFirst();
      
      // returns the key currently pointed to, if no key is being pointed to
      // std::logic_error is returned (not LSMException). LSMException may
      // be thrown for other reasons. You can avoid logic_error by
      // calling isValid() first
      const std::string& key() const { return key_; }
      
      // returns the value currently pointed to. Exceptions are thrown
      // under the same conditions as key()
      const std::string& value() const { return val_; }
   };
   
   class Transaction
   {
      friend class LMDB;

      LMDB *db;
      bool began=false;

   public:
      
      Transaction();
      // begin a transaction
      Transaction(LMDB *db, TXN_MODE readWrite);
      // commit a transaction if it exists
      ~Transaction();
      
      // commit a transaction, if it exists, doing nothing otherwise.
      // after this function completes, no transaction exists
      void commit();
      // rollback the transaction, if it exists, doing nothing otherwise.
      // All modifications made since this transaction began are removed.
      // After this function completes, no transaction exists
      void rollback();
      // start a new transaction. If one already exists, do nothing
      void begin(TXN_MODE ReadWrite);
   private:
      Transaction(const Transaction&); // no copies
   };

   LMDB();
   ~LMDB();
      
   // open a database by filename
   void open(const char *filename, Mode mode=ReadWrite);
   void open(const std::string &filename, Mode mode=ReadWrite)
      { open(filename.c_str(), mode); }

   // close a database, doing nothing if one is presently not open
   void close();
   
   // insert a value into the database, replacing
   // the one with a matching key if it is already there
   void insert(
      const CharacterArrayRef& key,
      const CharacterArrayRef& value
   );
   
   // delete the entry with the given key, doing nothing
   // if such a key does not exist
   void erase(const CharacterArrayRef& key);

   // read the value having the given key
   std::string value(const CharacterArrayRef& key) const;
 
   // get a value having the given key, don't use an iterator
   std::string get(const CharacterArrayRef& key) const;

   // create a cursor for scanning the database that points to the first
   // item
   Iterator begin() const
   {
      Iterator c(const_cast<LMDB*>(this));
      c.toFirst();
      return c;
   }
   // creates a cursor that points to an invalid item
   Iterator end() const
   {
      Iterator c(const_cast<LMDB*>(this));
      return c;
   }
   
   template<class T>
   Iterator find(const T &t) const
   {
      Iterator c = cursor();
      c.seek(t);
      return c;
   }
   
   // Create an iterator that points to an invalid item.
   // like end(), the iterator can be repositioned to
   // become a valid entry
   Iterator cursor() const { 
      return end(); }
private:
   // grow the size of the map on-demand
   void enlargeMap();

   LMDB(const LMDB &nocopy);
   Mode mode;
   mutable std::atomic<int32_t> txMapLock_;
};

#endif
// kate: indent-width 3; replace-tabs on;

