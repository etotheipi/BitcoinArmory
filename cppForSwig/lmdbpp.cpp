#include "lmdbpp.h"    

#include <lmdb.h>
#include <unistd.h>

#include <sstream>
#include <cstring>
#include <algorithm>

#ifndef _WIN32_
#include <sys/types.h>
#include <sys/stat.h>
#endif

//#define DISABLE_TRANSACTIONS

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
         const_cast<Iterator*>(this)->seek(key_);
         if (!has_)
            throw LMDBException("Cursor could not be regenerated");
      }
   }
   
}

void LMDB::Iterator::openCursor()
{
   int rc;
  
   rc = mdb_cursor_open(txnPtr_->txn_, db_->dbi, &csr_);
   if (rc != MDB_SUCCESS)
   {
      csr_=nullptr;
      LMDBException e("Failed to open cursor (" + errorString(rc) + ")");
      throw e;
   }
}

LMDB::Iterator::Iterator(LMDB *db)
: db_(db), csr_(nullptr), has_(false)
{
   const pthread_t tID = pthread_self();
   auto txnIter = db->txForThreads_.find(tID);

   if (txnIter == db->txForThreads_.end())
      throw std::runtime_error("Iterator must be created within Transaction");

   if (txnIter->second.transactionLevel_ == 0)
      throw std::runtime_error("Iterator must be created within Transaction");
   
   txnPtr_ = &txnIter->second;
   openCursor();

   txnPtr_->iterators_.push_front(this);
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
      std::deque<Iterator*>::iterator i =
         std::find(txnPtr_->iterators_.begin(), txnPtr_->iterators_.end(), this);
      if (i != txnPtr_->iterators_.end())
         txnPtr_->iterators_.erase(i);

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
   
   txnPtr_->iterators_.push_front(this);

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

   txnPtr_->iterators_.push_front(this);
   
   openCursor();
   
   if (copy.has_)
   {
      seek(copy.key_);
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
   
   return key() == other.key();
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
      key_ = std::string(static_cast<char*>(mkey.mv_data), mkey.mv_size);
      val_ = std::string(static_cast<char*>(mval.mv_data), mval.mv_size);
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
      key_ = std::string(static_cast<char*>(mkey.mv_data), mkey.mv_size);
      val_ = std::string(static_cast<char*>(mval.mv_data), mval.mv_size);
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
      key_ = std::string(static_cast<char*>(mkey.mv_data), mkey.mv_size);
      val_ = std::string(static_cast<char*>(mval.mv_data), mval.mv_size);
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
         key_ = std::string(static_cast<char*>(mkey.mv_data), mkey.mv_size);
         val_ = std::string(static_cast<char*>(mval.mv_data), mval.mv_size);
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
      key_ = std::string(static_cast<char*>(mkey.mv_data), mkey.mv_size);
      val_ = std::string(static_cast<char*>(mval.mv_data), mval.mv_size);
   }
}

LMDB::Transaction::Transaction()
: db(nullptr)
{}

LMDB::Transaction::Transaction(LMDB *db)
: db(db)
{
   begin();
}

LMDB::Transaction::~Transaction()
{
   commit();
}

void LMDB::Transaction::begin()
{
   if (began)
      return;
   
   began = true;

   const pthread_t tID = pthread_self();
   
   ThreadTxInfo& thTx = db->txForThreads_[tID];
   
   if (thTx.transactionLevel_++ != 0)
      return;
   
   int modef = 0;
   if (db->mode == ReadOnly)
      modef = MDB_RDONLY;
      
   int rc = mdb_txn_begin(db->env, nullptr, modef, &thTx.txn_);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to create transaction (" + errorString(rc) +")");
}

void LMDB::Transaction::commit()
{
   if (!began)
      return;

   began=false;

   //look for an existing transaction in this thread
   pthread_t tID = pthread_self();
   auto txnIter = db->txForThreads_.find(tID);

   if (txnIter == db->txForThreads_.end())
      throw LMDBException("Transaction bound to unknown thread");

   ThreadTxInfo& thTx = txnIter->second;

   if (thTx.transactionLevel_-- == 1)
   {
      int rc = mdb_txn_commit(thTx.txn_);
      
      for (Iterator *i : thTx.iterators_)
      {
         i->hasTx=false;
         i->csr_=nullptr;
      }
      
      if (rc != MDB_SUCCESS)
      {
         throw LMDBException("Failed to close db tx (" + errorString(rc) +")");
      }
      
      db->txForThreads_.erase(txnIter);
   }
   
   if (db->txForThreads_.empty())
      db->enlargeMap();
}

void LMDB::Transaction::rollback()
{
   throw std::runtime_error("unimplemented");
}


LMDB::LMDB()
{
   env = nullptr;
   dbi = 0;
}

LMDB::~LMDB()
{
   close();
}

void LMDB::open(const char *filename, Mode mode)
{
   if (env)
      throw std::logic_error("Database object already open (close it first)");

   dbi = 0;
   txForThreads_.clear();
   
   int rc;

   this->mode = mode;
   
   int modef = 0;
   if (mode == ReadOnly)
      modef = MDB_RDONLY;

   rc = mdb_env_create(&env);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to load mdb env (" + errorString(rc) + ")");
   
   rc = mdb_env_open(env, filename, modef|MDB_NOSYNC|MDB_NOSUBDIR, 0600);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to open db " + std::string(filename) + " (" + errorString(rc) + ")");

   enlargeMap();
   
   MDB_txn *txn;
   rc = mdb_txn_begin(env, nullptr, modef, &txn);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to create transaction (" + errorString(rc) +")");

   rc = mdb_dbi_open(txn, 0, 0, &dbi);
   rc = mdb_txn_commit(txn);
   if (rc != MDB_SUCCESS)
   {
      // cleanup here
      throw LMDBException("Failed to close db tx (" + errorString(rc) +")");
   }
}

void LMDB::close()
{
   if (env)
   {
      mdb_close(env, dbi);
      mdb_env_close(env);
      env = nullptr;
   }
}

void LMDB::insert(
   const CharacterArrayRef& key,
   const CharacterArrayRef& value
)
{
   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   MDB_val mval = { value.len, const_cast<char*>(value.data) };
   
   pthread_t tID = pthread_self();
   auto txnIter = txForThreads_.find(tID);

   if (txnIter == txForThreads_.end())
      throw LMDBException("Failed to insert: need transaction");
   
   int rc = mdb_put(txnIter->second.txn_, dbi, &mkey, &mval, 0);
   if (rc != MDB_SUCCESS)
      throw LMDBException("Failed to insert (" + errorString(rc) + ")");
}

void LMDB::erase(const CharacterArrayRef& key)
{
   pthread_t tID = pthread_self();
   auto txnIter = txForThreads_.find(tID);

   if (txnIter == txForThreads_.end())
      throw LMDBException("Failed to insert: need transaction");

   MDB_val mkey = { key.len, const_cast<char*>(key.data) };
   int rc = mdb_del(txnIter->second.txn_, dbi, &mkey, 0);
   if (rc != MDB_SUCCESS && rc != MDB_NOTFOUND)
      throw LMDBException("Failed to erase (" + errorString(rc) + ")");
}

std::string LMDB::value(const CharacterArrayRef& key) const
{
   Iterator c = find(key);
   if (!c.isValid())
      throw NoValue("No such value with specified key");
   
   return c.value();
}

void LMDB::enlargeMap()
{
   mdb_filehandle_t fd;
   mdb_env_get_fd(env,&fd);
   struct stat s;
   fstat(fd, &s);
   uint64_t v = s.st_size;
   if (v < 1024*1024*512)
   {
      v = 1024*1024*512;
   }
   else
   {
      v--;
      v = (v >> 1) | v;
      v = (v >> 2) | v;
      v = (v >> 4) | v;
      v = (v >> 8) | v;
      v = (v >> 16) | v;
      v = (v >> 32) | v;
   }
   v *= 2;
   mdb_env_set_mapsize(env, v);
}

// kate: indent-width 3; replace-tabs on;
