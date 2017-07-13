////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataMap.h"
#include "BtcUtils.h"

////////////////////////////////////////////////////////////////////////////////
void BlockData::deserialize(const uint8_t* data, size_t size,
   const shared_ptr<BlockHeader> blockHeader,
   function<unsigned int(const BinaryData&)> getID, 
   bool checkMerkle, bool keepHashes)
{
   headerPtr_ = blockHeader;

   //deser header from raw block and run a quick sanity check
   if (size < HEADER_SIZE)
      throw BlockDeserializingException(
      "raw data is smaller than HEADER_SIZE");

   BinaryDataRef bdr(data, HEADER_SIZE);
   BlockHeader bh(bdr);

   blockHash_ = bh.thisHash_;

   BinaryRefReader brr(data + HEADER_SIZE, size - HEADER_SIZE);
   auto numTx = (unsigned)brr.get_var_int();

   if (blockHeader != nullptr)
   {
      if (bh.getThisHashRef() != blockHeader->getThisHashRef())
         throw BlockDeserializingException(
         "raw data does not match expected block hash");

      if (numTx != blockHeader->getNumTx())
         throw BlockDeserializingException(
         "tx count mismatch in deser header");
   }

   for (unsigned i = 0; i < numTx; i++)
   {
      //light tx deserialization, just figure out the offset and size of
      //txins and txouts
      auto tx = BCTX::parse(brr);
      brr.advance(tx->size_);

      //move it to BlockData object vector
      txns_.push_back(move(tx));
   }

   data_ = data;
   size_ = size;

   if (!checkMerkle)
      return;

   //let's check the merkle root
   vector<BinaryData> allhashes;
   for (auto& txn : txns_)
   {
      if (!keepHashes)
      {
         auto txhash = txn->moveHash();
         allhashes.push_back(move(txhash));
      }
      else
      {
         txn->getHash();
         allhashes.push_back(txn->txHash_);
      }
   }

   auto&& merkleroot = BtcUtils::calculateMerkleRoot(allhashes);
   if (merkleroot != bh.getMerkleRoot())
   {
      LOGERR << "merkle root mismatch!";
      LOGERR << "   header has: " << bh.getMerkleRoot().toHexStr();
      LOGERR << "   block yields: " << merkleroot.toHexStr();
      throw BlockDeserializingException("invalid merkle root");
   }

   uniqueID_ = getID(bh.getThisHash());

   txFilter_ = move(computeTxFilter(allhashes));
}

/////////////////////////////////////////////////////////////////////////////
TxFilter<TxFilterType> 
BlockData::computeTxFilter(const vector<BinaryData>& allHashes) const
{
   TxFilter<TxFilterType> txFilter(uniqueID_, allHashes.size());
   txFilter.update(allHashes);

   return move(txFilter);
}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockHeader> BlockData::createBlockHeader(void) const
{
   if (headerPtr_ != nullptr)
      return headerPtr_;

   auto bhPtr = make_shared<BlockHeader>();
   auto& bh = *bhPtr;

   bh.dataCopy_ = move(BinaryData(data_, HEADER_SIZE));

   bh.difficultyDbl_ = BtcUtils::convertDiffBitsToDouble(
      BinaryDataRef(data_ + 72, 4));

   bh.isInitialized_ = true;
   bh.nextHash_ = BinaryData(0);
   bh.blockHeight_ = UINT32_MAX;
   bh.difficultySum_ = -1;
   bh.isMainBranch_ = false;
   bh.isOrphan_ = true;
   
   bh.numBlockBytes_ = size_;
   bh.numTx_ = txns_.size();

   bh.blkFileNum_ = fileID_;
   bh.blkFileOffset_ = offset_;
   bh.thisHash_ = blockHash_;
   bh.uniqueID_ = uniqueID_;

   return bhPtr;
}

/////////////////////////////////////////////////////////////////////////////
void BlockFiles::detectAllBlockFiles()
{
   if (folderPath_.size() == 0)
      throw runtime_error("empty block files folder path");

   unsigned numBlkFiles = filePaths_.size();

   while (numBlkFiles < UINT16_MAX)
   {
      string path = BtcUtils::getBlkFilename(folderPath_, numBlkFiles);
      uint64_t filesize = BtcUtils::GetFileSize(path);
      if (filesize == FILE_DOES_NOT_EXIST)
         break;

      filePaths_.insert(make_pair(numBlkFiles, path));

      totalBlockchainBytes_ += filesize;
      numBlkFiles++;
   }
}

/////////////////////////////////////////////////////////////////////////////
BlockDataLoader::BlockDataLoader(const string& path) :
   path_(path), prefix_("blk")
{}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataFileMap> BlockDataLoader::get(const string& filename)
{
   //convert to int ID
   auto intID = nameToIntID(filename);

   //get with int ID
   return get(intID);
}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataFileMap> BlockDataLoader::get(uint32_t fileid)
{
   //don't have this fileid yet, create it
   return getNewBlockDataMap(fileid);
}

/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataLoader::nameToIntID(const string& filename)
{
   if (filename.size() < 3 ||
      strncmp(prefix_.c_str(), filename.c_str(), 3))
      throw runtime_error("invalid filename");

   auto&& substr = filename.substr(3);
   return stoi(substr);
}

/////////////////////////////////////////////////////////////////////////////
string BlockDataLoader::intIDToName(uint32_t fileid)
{
   stringstream filename;

   filename << path_ << "/blk";
   filename << setw(5) << setfill('0') << fileid;
   filename << ".dat";

   return filename.str();
}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataFileMap>
   BlockDataLoader::getNewBlockDataMap(uint32_t fileid)
{
   string filename = move(intIDToName(fileid));

   return make_shared<BlockDataFileMap>(filename);
}

/////////////////////////////////////////////////////////////////////////////
BlockDataFileMap::BlockDataFileMap(const string& filename)
{
   //relaxed memory order for loads and stores, we only care about 
   //atomicity in these operations
   useCounter_.store(0, memory_order_relaxed);

   if (!DBUtils::fileExists(filename, 2))
      return;

   //check filename exists and open it, otherwise return nullptr fileMap_
   int fd;

   while (1)
   {
      try
      {
#ifdef _WIN32
         fd = _open(filename.c_str(), _O_RDONLY | _O_BINARY);
         if (fd == -1)
            throw runtime_error("failed to open file");

         size_ = _lseek(fd, 0, SEEK_END);

         if (size_ == 0)
         {
            stringstream ss;
            ss << "empty block file under path: " << filename;
            throw ss.str();
         }

         _lseek(fd, 0, SEEK_SET);
#else
         fd = open(filename.c_str(), O_RDONLY);
         if (fd == -1)
            throw runtime_error("failed to open file");

         size_ = lseek(fd, 0, SEEK_END);

         if (size_ == 0)
         {
            stringstream ss;
            ss << "empty block file under path: " << filename;
            throw ss.str();
         }

         lseek(fd, 0, SEEK_SET);
#endif

#ifdef _WIN32
         //create mmap
         auto fileHandle = (HANDLE)_get_osfhandle(fd);
         HANDLE mh;

         mh = CreateFileMapping(fileHandle, NULL, PAGE_READONLY,
            0, size_, NULL);
         if (!mh)
         {
            auto errorCode = GetLastError();
            stringstream errStr;
            errStr << "Failed to create map of file. Error Code: " <<
               errorCode << " (" << strerror(errorCode) << ")";
            throw runtime_error(errStr.str());
         }

         fileMap_ = (uint8_t*)MapViewOfFileEx(mh, FILE_MAP_READ, 0, 0, size_, NULL);
         if (fileMap_ == nullptr)
         {
            auto errorCode = GetLastError();
            stringstream errStr;
            errStr << "Failed to create map of file. Error Code: " <<
               errorCode << " (" << strerror(errorCode) << ")";
            throw runtime_error(errStr.str());
         }

         CloseHandle(mh);

         _close(fd);
#else
         fileMap_ = (uint8_t*)mmap(0, size_, PROT_READ, MAP_SHARED,
            fd, 0);
         if (fileMap_ == MAP_FAILED) {
            fileMap_ = NULL;
            stringstream errStr;
            errStr << "Failed to create map of file. Error Code: " << 
               errno << " (" << strerror(errno) << ")";
            cout << errStr.str() << endl;
            throw runtime_error(errStr.str());
         }

         close(fd);
#endif
         return;
      }
      catch (exception&)
      {
         if (fd > 0)
         {
#ifdef _WIN32
            _close(fd);
#else
            close(fd);
#endif
         }

         LOGWARN << "Failed to create BlockDataMap for file: " << filename;
         LOGWARN << "Trying again...";
      }
   }
}
