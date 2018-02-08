////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "lmdbpp.h"    

#include <lmdb.h>
#include <unistd.h>

#include <sstream>
#include <cstring>
#include <algorithm>
#include <iostream>

#ifndef _WIN32_
#include <sys/types.h>
#include <sys/stat.h>
#endif

static std::string errorString(int rc)
{
   return mdb_strerror(rc);
}

inline void LMDB::Iterator::checkHasDb() const
{
   if (!db_)
   {
      throw std::logic_error("Iterator is not associated with a db");
   }
}


inline void LMDB::Iterator::checkOk() const
{
   if (!isValid())
   {
      throw std::logic_error("Tried to use invalid LMDB Iterator");
   }
   
   if (!hasTx)
   {
      const_cast<Iterator*>(this)->openCursor();
      
      hasTx=true;
      
      if (has_)
      {
         CharacterArrayRef keydata(
            key_.mv_size,
            (const char*)key_.mv_data);

         const_cast<Iterator*>(this)->seek(keydata);
         if (!has_)
            throw LMDBException("Cursor could not be regenerated");
      }
   }
   
}

void LMDB::Iterator::openCursor()
{
   auto tID = std::this_thread::get_id();
   LMDBEnv *const _env = db_->env;
   std::unique_lock<std::mutex> lock(_env->threadTxMutex_);
   
   auto txnIter = _env->txForThreads_.find(tID);
   if (txnIter == _env->txForThreads_.end())
      throw std::runtime_error("Iterator must be created within Transaction");
   
   lock.unlock();
   
   if (txnIter->second.transactionLevel_ == 0)
      throw std::runtime_error("Iterator must be created within Transaction");
   
   txnPtr_ = &txnIter->second;
  
   int rc = mdb_cursor_open(txnPtr_->txn_, db_->dbi, &csr_);
   if (rc != MDB_SUCCESS)
   {
      csr_=nullptr;
      LMDBException e("Failed to open cursor (" + errorString(rc) + ")");
      throw e;
   }
   txnPtr_->iterators_.push_back(this);
}

LMDB::Iterator::Iterator(LMDB *db)
   : db_(db), csr_(nullptr), has_(false)
{
   openCursor();
}

LMDB::Iterator::Iterator(const Iterator &copy)
   : db_(copy.db_), csr_(nullptr), has_(copy.has_), txnPtr_(copy.txnPtr_)
{
   if (copy.txnPtr_ == nullptr)
      throw std::runtime_error("Iterator must be created within Transaction");

   if (copy.txnPtr_->transactionLevel_ == 0)
      throw std::runtime_error("Iterator must be created within Transaction");

   operator=(copy);
}

inline void LMDB::Iterator::reset()
{
   if (csr_)
      mdb_cursor_close(csr_);
   csr_ = nullptr;

   if (txnPtr_)
   {
      std::vector<Iterator*>::reverse_iterator i =
         std::find(txnPtr_->iterators_.rbegin(), txnPtr_->iterators_.rend(), this);
      // below has a silly workaround to delete reverse_iterators
      if (i != txnPtr_->iterators_.rend())
         txnPtr_->iterators_.erase(std::next(i).base());

      txnPtr_ = nullptr;
   }
}

LMDB::Iterator::~Iterator()
{
   reset();
}

LMDB::Iterator::Iterator(Iterator &&move)
{
   operator=(std::move(move));
}

LMDB::Iterator& LMDB::Iterator::operator=(Iterator &&move)
{
   reset();
   
   txnPtr_ = move.txnPtr_;
   std::swap(csr_, move.csr_);
   std::swap(has_, move.has_);
   std::swap(key_, move.key_);
   std::swap(val_, move.val_);
   std::swap(hasTx, move.hasTx);
   std::swap(db_, move.db_);
   
   move.reset();
   
   txnPtr_->iterators_.push_back(this);

   return *this;
}

LMDB::Iterator& LMDB::Iterator::operator=(const Iterator &copy)
{
   if (&copy == this)
      return *this;
   reset();
   
   db_ = copy.db_;
   has_ = copy.has_;
   txnPtr_ = copy.txnPtr_;

   txnPtr_->iterators_.push_back(this);
   
   openCursor();
   
   if (copy.has_)
   {
      CharacterArrayRef keydata(
         copy.key_.mv_size, 
         (const char*)copy.key_.mv_data);

      seek(keydata);
      if (!has_)
         throw LMDBException("Cursor could not be copied");
   }
   return *this;
}

bool LMDB::Iterator::operator==(const Iterator &other) const
{
   if (this == &other)
      return true;

   {
      bool a = isEOF();
      bool b = other.isEOF();
      if (a && b) return true;
      if (a || b) return false;
   }
   
   //make sure this is a proper check
   return key().mv_data == other.key().mv_data &&
      key().mv_size == key().mv_size;
}

void LMDB::Iterator::advance()
{
   checkOk();
   
   MDB_val mkey;
   MDB_val mval;
   
   int rc = mdb_cursor_get(csr_, &mkey, &mval, MDB_NEXT);

   if (rc == MDB_NOTFOUND)
      has_ = false;
   else if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to seek (" + errorString(rc) +")");
   else
   {
      has_ = true;
      key_ = mkey;
      val_ = mval;
   }
}

void LMDB::Iterator::retreat()
{
   checkOk();
   
   MDB_val mkey;
   MDB_val mval;
   
   int rc = mdb_cursor_get(csr_, &mkey, &mval, MDB_PREV);

   if (rc == MDB_NOTFOUND)
      has_ = false;
   else if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to seek (" + errorString(rc) +")");
   else
   {
      has_ = true;
      key_ = mkey;
      val_ = mval;
   }
}


void LMDB::Iterator::toFirst()
{
   checkHasDb();
   
   MDB_val mkey;
   MDB_val mval;
   
   int rc = mdb_cursor_get(csr_, &mkey, &mval, MDB_FIRST);

   if (rc == MDB_NOTFOUND)
      has_ = false;
   else if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to seek (" + errorString(rc) +")");
   else
   {
      has_ = true;
      key_ = mkey;
      val_ = mval;
   }
}

void LMDB::Iterator::seek(const CharacterArrayRef &key, SeekBy e)
{
   checkHasDb();
   
   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   MDB_val mval = {0, 0};

   MDB_cursor_op op=MDB_SET;
   if (e == Seek_GE)
      op = MDB_SET_RANGE;
   else if (e == Seek_LE)
      op = MDB_SET_RANGE;

   int rc = mdb_cursor_get(csr_, &mkey, &mval, op);
   if (e == Seek_LE)
   {
      if (rc == MDB_NOTFOUND)
         rc = mdb_cursor_get(csr_, &mkey, &mval, MDB_LAST);
      // now make sure mkey is less than key
      if (rc == MDB_NOTFOUND)
      {
         has_ = false;
         return;
      }
      else if (rc != MDB_SUCCESS)
         throw LMDBException("Failed to seek (" + errorString(rc) +")");
      
      if (mkey.mv_size > key.len)
      {
         // mkey can't possibly be before key if it's longer than key
         has_ = false;
         return;
      }
      const int cmp = std::memcmp(mkey.mv_data, key.data, key.len);
      if (cmp <= 0)
      {
         // key is longer and the earlier bytes are the same,
         // therefor, mkey is before key
         has_ = true;
         key_ = mkey;
         val_ = mval;
         return;
      }
      else
      {
         has_ = false;
         return;
      }
   }
   
   if (rc == MDB_NOTFOUND)
      has_ = false;
   else if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to seek (" + errorString(rc) +")");
   else
   {
      has_ = true;
      key_ = mkey;
      val_ = mval;
   }
}

LMDBEnv::~LMDBEnv()
{
   close();
}

void LMDBEnv::open(const char *filename)
{
   if (dbenv)
      throw std::logic_error("Database environment already open (close it first)");

   txForThreads_.clear();
   
   int rc;

   rc = mdb_env_create(&dbenv);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to load mdb env (" + errorString(rc) + ")");
   
   rc = mdb_env_set_maxdbs(dbenv, dbCount_);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to set max dbs (" + errorString(rc) + ")");
   
   rc = mdb_env_open(dbenv, filename, MDB_NOSYNC|MDB_NOSUBDIR, 0600);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to open db " + std::string(filename) + " (" + errorString(rc) + ")");
}

void LMDBEnv::close()
{
   if (dbenv)
   {
      mdb_env_close(dbenv);
      dbenv = nullptr;
   }
}

LMDBEnv::Transaction::Transaction(LMDBEnv *_env, LMDB::Mode mode)
   : env(_env), mode_(mode)
{
   begin();
}

LMDBEnv::Transaction& LMDBEnv::Transaction::operator=(Transaction&& mv)
{
   if (this == &mv)
      return *this;

   this->env = mv.env;
   this->mode_ = mv.mode_;
   this->began = mv.began;

   mv.began = false;

   return *this;
}

LMDBEnv::Transaction::~Transaction()
{
   commit();
}

void LMDBEnv::Transaction::begin()
{
   if (began)
      return;
   
   began = true;

   auto tID = std::this_thread::get_id();
   
   std::unique_lock<std::mutex> lock(env->threadTxMutex_);
   LMDBThreadTxInfo& thTx = env->txForThreads_[tID];
   lock.unlock();
   
   if (thTx.transactionLevel_ != 0 && mode_ == LMDB::ReadWrite && thTx.mode_ == LMDB::ReadOnly)
      throw LMDBException("Cannot access ReadOnly Transaction in ReadWrite mode");
   
   if (thTx.transactionLevel_++ != 0)
      return;
      
   if (!env->dbenv)
      throw LMDBException("Cannot start transaction without db env");
      
   int modef = MDB_RDONLY;
   thTx.mode_ = LMDB::ReadOnly;
   
   if (mode_ == LMDB::ReadWrite)
   {
      modef = 0;
      thTx.mode_ = LMDB::ReadWrite;
   }

   int rc = mdb_txn_begin(env->dbenv, nullptr, modef, &thTx.txn_);
   if (rc != MDB_SUCCESS)
   {
      lock.lock();
      env->txForThreads_.erase(tID);
      lock.unlock();
      
      began = false;
      throw LMDBException("Failed to create transaction (" + errorString(rc) +")");
   }
}

void LMDBEnv::Transaction::open(LMDBEnv *_env, LMDB::Mode mode)
{
   if (env)
      commit();
   
   this->env = _env;
   this->mode_ = mode;
   
   begin();
}

void LMDBEnv::Transaction::commit()
{
   if (!began)
      return;

   began=false;

   //look for an existing transaction in this thread
   auto tID = std::this_thread::get_id();
   std::unique_lock<std::mutex> lock(env->threadTxMutex_);
   auto txnIter = env->txForThreads_.find(tID);

   if (txnIter == env->txForThreads_.end())
      throw LMDBException("Transaction bound to unknown thread");
   lock.unlock();

   LMDBThreadTxInfo& thTx = txnIter->second;

   if (thTx.transactionLevel_-- == 1)
   {
      int rc = mdb_txn_commit(thTx.txn_);
      
      for (LMDB::Iterator *i : thTx.iterators_)
      {
         i->hasTx=false;
         i->csr_=nullptr;
      }
      
      if (rc != MDB_SUCCESS)
      {
         throw LMDBException("Failed to close env tx (" + errorString(rc) +")");
      }
      
      lock.lock();
      env->txForThreads_.erase(txnIter);
   }
}

void LMDBEnv::Transaction::rollback()
{
   throw std::runtime_error("unimplemented");
}


LMDB::~LMDB()
{
   try
   {
      close();
   }
   catch(std::exception &e)
   {
      std::cerr << "Error: " << e.what() << std::endl;
   }
}


void LMDB::close()
{
   if (dbi != 0)
   {
      {
         std::unique_lock<std::mutex> lock(env->threadTxMutex_);
         if (!env->txForThreads_.empty())
            throw std::runtime_error("Tried to close database with open txes");
      }
      mdb_dbi_close(env->dbenv, dbi);
      dbi=0;
      
      env=nullptr;
   }
}

void LMDB::open(LMDBEnv *_env, const std::string &name)
{
   if (this->env)
   {
      throw std::runtime_error("LMDB already open");
   }
   this->env = _env;
   
   LMDBEnv::Transaction tx(_env);
   auto tID = std::this_thread::get_id();
   std::unique_lock<std::mutex> lock(_env->threadTxMutex_);
   auto txnIter = _env->txForThreads_.find(tID);

   if (txnIter == _env->txForThreads_.end())
      throw LMDBException("Failed to insert: need transaction");
   lock.unlock();
      
   int rc = mdb_open(txnIter->second.txn_, name.c_str(), MDB_CREATE, &dbi);
   if (rc != MDB_SUCCESS)
   {
      // cleanup here
      throw LMDBException("Failed to open dbi (" + errorString(rc) +")");
   }
}

void LMDB::insert(
   const CharacterArrayRef& key,
   const CharacterArrayRef& value
)
{
   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   MDB_val mval = { value.len, const_cast<char*>(value.data) };
   
   auto tID = std::this_thread::get_id();

   std::unique_lock<std::mutex> lock(env->threadTxMutex_);
   
   auto txnIter = env->txForThreads_.find(tID);

   if (txnIter == env->txForThreads_.end())
      throw LMDBException("Failed to insert: need transaction");
   lock.unlock();
   
   int rc = mdb_put(txnIter->second.txn_, dbi, &mkey, &mval, 0);
   if (rc != MDB_SUCCESS)
   {
      std::cout << "failed to insert data, returned following error string: " << errorString(rc) << std::endl;
      throw LMDBException("Failed to insert (" + errorString(rc) + ")");
   }
}

void LMDB::erase(const CharacterArrayRef& key)
{
   auto tID = std::this_thread::get_id();
   std::unique_lock<std::mutex> lock(env->threadTxMutex_);
   auto txnIter = env->txForThreads_.find(tID);

   if (txnIter == env->txForThreads_.end())
      throw LMDBException("Failed to insert: need transaction");
   lock.unlock();
      
   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   int rc = mdb_del(txnIter->second.txn_, dbi, &mkey, 0);
   if (rc != MDB_SUCCESS && rc != MDB_NOTFOUND)
   {
      std::cout << "failed to erase data, returned following error string: " << errorString(rc) << std::endl;
      throw LMDBException("Failed to erase (" + errorString(rc) + ")");
   }
}

MDB_val LMDB::value(const CharacterArrayRef& key) const
{
   Iterator c = find(key);
   if (!c.isValid())
      throw NoValue("No such value with specified key");
   
   return c.value();
}

CharacterArrayRef LMDB::get_NoCopy(const CharacterArrayRef& key) const
{
   //simple get without the use of iterators

   auto tID = std::this_thread::get_id();
   std::unique_lock<std::mutex> lock(env->threadTxMutex_);
   
   auto txnIter = env->txForThreads_.find(tID);
   if (txnIter == env->txForThreads_.end())
      throw std::runtime_error("Need transaction to get data");
   
   lock.unlock();

   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   MDB_val mdata = { 0, 0 };

   int rc = mdb_get(txnIter->second.txn_, dbi, &mkey, &mdata);
   if (rc == MDB_NOTFOUND)
      return CharacterArrayRef(0, (char*)nullptr);
   
   CharacterArrayRef ref(
      mdata.mv_size,
      static_cast<uint8_t*>(mdata.mv_data)
   );
   return ref;
}

void LMDB::drop(void)
{
   auto tID = std::this_thread::get_id();
   std::unique_lock<std::mutex> lock(env->threadTxMutex_);

   auto txnIter = env->txForThreads_.find(tID);
   if (txnIter == env->txForThreads_.end())
      throw std::runtime_error("Need transaction to get data");

   lock.unlock();

   if (mdb_drop(txnIter->second.txn_, dbi, 0) != MDB_SUCCESS)
      throw std::runtime_error("Failed to drop DB!");
}

// kate: indent-width 3; replace-tabs on;
