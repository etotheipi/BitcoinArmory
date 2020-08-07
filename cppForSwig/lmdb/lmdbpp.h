////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef LMDBPP_H
#define LMDBPP_H

#include <string>
#include <stdexcept>
#include <vector>
#include <unordered_map>
#include <thread>
#include <mutex>
#include "lmdb.h"

struct MDB_env;
struct MDB_txn;
struct MDB_cursor;

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
   
   CharacterArrayRef(const size_t _len, const char *_data)
      : len(_len), data(_data)
   { }
   CharacterArrayRef(const size_t _len, const unsigned char *_data)
      : len(_len), data(reinterpret_cast<const char*>(_data))
   { }
   CharacterArrayRef(const std::string &_data)
      : len(_data.size()), data(&_data[0])
   { }
   CharacterArrayRef(const std::vector<char> &_data)
      : len(_data.size()), data(&_data.front())
   { }
};

class LMDBEnv;

//one mother-txn per thread
struct LMDBThreadTxInfo;


class LMDB
{
public:
   class Iterator;

   enum Mode
   {
      ReadWrite,
      ReadOnly
   };
   
private:
   LMDBEnv *env=nullptr;
   unsigned int dbi=0;
      
   friend class Iterator;   

public:
   // this class can be used like a C++ iterator,
   // or you can just use isValid() to test for "last item"

   class Iterator
   {
      friend class LMDBEnv;
      friend class LMDB;
      
      LMDB *db_=nullptr;
      mutable MDB_cursor *csr_=nullptr;
      
      mutable bool hasTx=true;
      bool has_=false;
      LMDBThreadTxInfo* txnPtr_=nullptr;
      MDB_val key_, val_;
         
      void reset();
      void checkHasDb() const;
      void checkOk() const;
      
      void openCursor();
      
      Iterator(LMDB *db);

      
   public:
      Iterator() { }
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
      const MDB_val& key() const { return key_; }
      
      // returns the value currently pointed to. Exceptions are thrown
      // under the same conditions as key()
      const MDB_val& value() const { return val_; }
   };
   
   LMDB() { }
   LMDB(LMDBEnv *_env, const std::string &name=std::string())
   {
      open(_env, name);
   }
   
   ~LMDB();
   
   void open(LMDBEnv *env, const std::string &name=std::string());
   
   void close();
   
   void drop();
      
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
   MDB_val value(const CharacterArrayRef& key) const;
   
   // read the value having the given key, without copying its
   // data even once. The return object has a pointer to the
   // location in memory
   CharacterArrayRef get_NoCopy(const CharacterArrayRef& key) const;
   
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
   Iterator cursor() const
      { return end(); }
private:

   LMDB(const LMDB &nocopy);
};

struct LMDBThreadTxInfo
{
   MDB_txn *txn_=nullptr;

   std::vector<LMDB::Iterator*> iterators_;
   unsigned transactionLevel_=0;
   LMDB::Mode mode_;
};


class LMDBEnv
{
public:
   class Transaction;

private:
   MDB_env *dbenv=nullptr;
   unsigned dbCount_ = 1;

   std::mutex threadTxMutex_;
   std::unordered_map<std::thread::id, LMDBThreadTxInfo> txForThreads_;
   
   friend class LMDB;

public:
   class Transaction
   {
      friend class LMDB;

      LMDBEnv *env=nullptr;
      bool began=false;
      LMDB::Mode mode_;
      
   public:
      
      Transaction() { }
      // begin a transaction
      Transaction(LMDBEnv *env, LMDB::Mode mode = LMDB::ReadWrite);
      // commit a transaction if it exists
      ~Transaction();

      Transaction& operator=(Transaction&& mv);
      
      // commit the current transaction, create a new one, and begin it
      void open(LMDBEnv *env, LMDB::Mode mode = LMDB::ReadWrite);
      
      // commit a transaction, if it exists, doing nothing otherwise.
      // after this function completes, no transaction exists
      void commit();
      // rollback the transaction, if it exists, doing nothing otherwise.
      // All modifications made since this transaction began are removed.
      // After this function completes, no transaction exists
      void rollback();
      // start a new transaction. If one already exists, do nothing
      void begin();

   private:
      Transaction(const Transaction&); // no copies
   };

   LMDBEnv() { }
   LMDBEnv(unsigned dbCount) { dbCount_ = dbCount; }
   ~LMDBEnv();
   
   // open a database by filename
   void open(const char *filename);
   void open(const std::string &filename)
      { open(filename.c_str()); }

   // close a database, doing nothing if one is presently not open
   void close();
   
private:
   LMDBEnv(const LMDBEnv&); // disallow copy
};


#endif
// kate: indent-width 3; replace-tabs on;

