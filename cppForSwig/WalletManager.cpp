////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "WalletManager.h"

#ifdef _WIN32
#include "leveldb_windows_port\win32_posix\dirent_win32.h"
#else
#include "dirent.h"
#endif

PythonSigner::~PythonSigner()
{}

////////////////////////////////////////////////////////////////////////////////
////
//// WalletManager
////
////////////////////////////////////////////////////////////////////////////////
void WalletManager::loadWallets()
{
   auto getBDVLambda = [this](void)->SwigClient::BlockDataViewer&
   {
      return this->getBDVObj();
   };

   //list .lmdb files in folder
   DIR *dir;
   dir = opendir(path_.c_str());
   if (dir == nullptr)
   {
      LOGERR << "invalid datadir path";
      throw runtime_error("invalid datadir path");
   }

   vector<string> walletPaths;

   struct dirent *ent;
   while ((ent = readdir(dir)) != nullptr)
   {
      auto dirname = ent->d_name;
      if (strlen(dirname) > 5)
      {
         auto endOfPath = ent->d_name + strlen(ent->d_name) - 5;
         if (strcmp(endOfPath, ".lmdb") == 0)
         {
            stringstream ss;
            ss << path_ << "/" << dirname;
            walletPaths.push_back(ss.str());
         }
      }
   }

   closedir(dir);

   unique_lock<mutex> lock(mu_);
   
   //read the files
   for (auto& wltPath : walletPaths)
   {
      try
      {
         auto wltPtr = AssetWallet::loadMainWalletFromFile(wltPath);
         WalletContainer wltCont(wltPtr->getID(), getBDVLambda);
         wltCont.wallet_ = wltPtr;

         wallets_.insert(make_pair(wltPtr->getID(), wltCont));
      }
      catch (exception& e)
      {
         stringstream ss;
         ss << "Failed to open wallet with error:" << endl << e.what();
         LOGERR << ss.str();
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void WalletManager::duplicateWOWallet(
   const SecureBinaryData& pubRoot,
   const SecureBinaryData& chainCode,
   unsigned chainLength)
{
   auto root = pubRoot;
   auto cc = chainCode;

   auto newWO = AssetWallet_Single::createFromPublicRoot_Armory135(
      path_, AddressEntryType_P2PKH, move(root), move(cc), chainLength);

   auto getBDVLambda = [this](void)->SwigClient::BlockDataViewer&
   {
      return this->getBDVObj();
   };

   WalletContainer wltCont(newWO->getID(), getBDVLambda);
   wltCont.wallet_ = newWO;

   unique_lock<mutex> lock(mu_);
   wallets_.insert(make_pair(newWO->getID(), wltCont));
}

////////////////////////////////////////////////////////////////////////////////
int WalletManager::getLastComputedIndex(const string& id) const
{
   {
      unique_lock<mutex> lock(mu_);

      auto wltIter = wallets_.find(id);
      if (wltIter == wallets_.end())
         throw runtime_error("invalid id");

      return wltIter->second.getLastComputedIndex();
   }
}

////////////////////////////////////////////////////////////////////////////////
void WalletManager::synchronizeWallet(const string& id, unsigned chainLength)
{
   WalletContainer* wltCtr;

   {
      unique_lock<mutex> lock(mu_);

      auto wltIter = wallets_.find(id);
      if (wltIter == wallets_.end())
         throw runtime_error("invalid id");

      wltCtr = &wltIter->second;
   }

   auto wltSingle = dynamic_pointer_cast<AssetWallet_Single>(wltCtr->wallet_);
   if (wltSingle == nullptr)
      throw runtime_error("invalid wallet ptr");

   wltSingle->extendChainTo(chainLength);
}

////////////////////////////////////////////////////////////////////////////////
SwigClient::BlockDataViewer& WalletManager::getBDVObj(void)
{
   if (!bdv_.isValid())
      throw runtime_error("bdv object is not valid");

   return bdv_;
}

////////////////////////////////////////////////////////////////////////////////
WalletContainer& WalletManager::getCppWallet(const string& id)
{
   unique_lock<mutex> lock(mu_);

   auto wltIter = wallets_.find(id);
   if (wltIter == wallets_.end())
      throw runtime_error("invalid id");

   return wltIter->second;
}

////////////////////////////////////////////////////////////////////////////////
bool WalletManager::setImport(
   string wltID, int importID, const SecureBinaryData& pubkey)
{
   auto wltIter = wallets_.find(wltID);
   if (wltIter == wallets_.end())
      throw WalletException("invalid wlt id");

   return wltIter->second.setImport(importID, pubkey);
}

////////////////////////////////////////////////////////////////////////////////
////
//// WalletContainer
////
////////////////////////////////////////////////////////////////////////////////
void WalletContainer::registerWithBDV(bool isNew)
{
   reset();

   auto wltSingle = dynamic_pointer_cast<AssetWallet_Single>(wallet_);
   if (wltSingle == nullptr)
      throw runtime_error("invalid wallet ptr");

   auto addrSet = wltSingle->getAddrHashSet();
   auto& bdv = getBDVlambda_();

   //convert set to vector
   vector<BinaryData> addrVec;
   addrVec.insert(addrVec.end(), addrSet.begin(), addrSet.end());

   auto&& swigWlt = bdv.registerWallet(wltSingle->getID(), addrVec, isNew);

   swigWallet_ = make_shared<SwigClient::BtcWallet>(swigWlt);
}

////////////////////////////////////////////////////////////////////////////////
int WalletContainer::detectHighestUsedIndex()
{
   int topIndex = 0;
   for (auto addrCountPair : countMap_)
   {
      auto& addr = addrCountPair.first;
      auto index = getAssetIndexForAddr(addr);
      if (index > topIndex)
         topIndex = index;
   }

   return topIndex;
}

////////////////////////////////////////////////////////////////////////////////
unsigned WalletContainer::getTopBlock(void)
{
   auto& bdv = getBDVlambda_();
   return bdv.getTopBlock();
}

////////////////////////////////////////////////////////////////////////////////
bool WalletContainer::setImport(int importID, const SecureBinaryData& pubkey)
{
   return wallet_->setImport(importID, pubkey);
}

////////////////////////////////////////////////////////////////////////////////
int WalletContainer::convertToImportIndex(int index)
{
   return AssetWallet::convertToImportIndex(index);
}

////////////////////////////////////////////////////////////////////////////////
int WalletContainer::convertFromImportIndex(int index)
{
   return AssetWallet::convertFromImportIndex(index);
}

////////////////////////////////////////////////////////////////////////////////
void WalletContainer::removeAddressBulk(const vector<BinaryData>& addrVec)
{
   //delete from AssetWallet
   wallet_->deleteImports(addrVec);

   //caller should register the wallet again to update the address list on
   //the db side
}

////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> WalletContainer::getScriptHashVectorForIndex(int index) const
{
   vector<BinaryData> hashVec;

   auto assetPtr = wallet_->getAssetForIndex(index);
   auto asset_single = dynamic_pointer_cast<AssetEntry_Single>(assetPtr);
   if (asset_single == nullptr)
      return hashVec;

   auto&& hashMap = asset_single->getScriptHashMap();
   for (auto hashRef : hashMap)
      hashVec.push_back(BinaryData(hashRef.second));

   return hashVec;
}

////////////////////////////////////////////////////////////////////////////////
////
//// CoinSelectionInstance
////
////////////////////////////////////////////////////////////////////////////////
CoinSelectionInstance::CoinSelectionInstance(
   WalletContainer* const walletContainer, 
   const vector<AddressBookEntry>& addrBook) :
   walletContainer_(walletContainer),
   cs_(getFetchLambdaFromWalletContainer(walletContainer), addrBook,
      walletContainer->getTopBlock(), walletContainer->spendableBalance_),
   spendableBalance_(walletContainer->spendableBalance_)
{}

////////////////////////////////////////////////////////////////////////////////
CoinSelectionInstance::CoinSelectionInstance(
   SwigClient::Lockbox* const lockbox, 
   unsigned M, unsigned N,
   unsigned blockHeight, uint64_t balance) :
   walletContainer_(nullptr),
   cs_(getFetchLambdaFromLockbox(lockbox, M, N), 
      vector<AddressBookEntry>(),
      blockHeight, balance),
   spendableBalance_(balance)
{}

////////////////////////////////////////////////////////////////////////////////
function<vector<UTXO>(uint64_t)> CoinSelectionInstance
   ::getFetchLambdaFromWalletContainer(WalletContainer* const walletContainer)
{
   if (walletContainer == nullptr)
      throw runtime_error("null wallet container ptr");

   auto fetchLbd = [walletContainer](uint64_t val)->vector<UTXO>
   {
      auto&& vecUtxo = walletContainer->getSpendableTxOutListForValue(val);
      decorateUTXOs(walletContainer, vecUtxo);

      return vecUtxo;
   };

   return fetchLbd;
}

////////////////////////////////////////////////////////////////////////////////
function<vector<UTXO>(uint64_t)> CoinSelectionInstance
   ::getFetchLambdaFromLockbox(  
      SwigClient::Lockbox* const lockbox, unsigned M, unsigned N)
{
   if (lockbox == nullptr)
      throw runtime_error("null lockbox ptr");

   auto fetchLbd = [lockbox, M, N](uint64_t val)->vector<UTXO>
   {
      auto&& vecUtxo = lockbox->getSpendableTxOutListForValue(val);

      unsigned sigSize = M * 73;
      unsigned scriptSize = N * 66 + 3;

      for (auto& utxo : vecUtxo)
      {
         utxo.witnessDataSizeBytes_ = 0;
         utxo.isInputSW_ = false;

         utxo.txinRedeemSizeBytes_ = sigSize;

         if (BtcUtils::getTxOutScriptType(utxo.getScript()) == TXOUT_SCRIPT_P2SH)
            utxo.txinRedeemSizeBytes_ += scriptSize;
      }

      return vecUtxo;
   };

   return fetchLbd;
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::decorateUTXOs(
   WalletContainer* const walletContainer, vector<UTXO>& vecUtxo)
{
   if (walletContainer == nullptr)
      throw runtime_error("null wallet container ptr");

   auto walletPtr = walletContainer->getWalletPtr();
   for (auto& utxo : vecUtxo)
   {
      auto&& scrAddr = utxo.getRecipientScrAddr();
      auto index = walletPtr->getAssetIndexForAddr(scrAddr);
      auto addrPtr = walletPtr->getAddressEntryForIndex(index);

      utxo.txinRedeemSizeBytes_ = addrPtr->getInputSize();

      try
      {
         utxo.witnessDataSizeBytes_ = addrPtr->getWitnessDataSize();
         utxo.isInputSW_ = true;
      }
      catch (runtime_error&)
      { }
   }
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::selectUTXOs(vector<UTXO>& vecUtxo, 
   uint64_t fee, float fee_byte, unsigned flags)
{
   uint64_t spendableVal = 0;
   for (auto& utxo : vecUtxo)
      spendableVal += utxo.getValue();

   //sanity check
   checkSpendVal(spendableVal);

   //decorate coin control selection
   decorateUTXOs(walletContainer_, vecUtxo);

   state_utxoVec_ = vecUtxo;

   PaymentStruct payStruct(recipients_, fee, fee_byte, flags);
   selection_ = move(
      cs_.getUtxoSelectionForRecipients(payStruct, vecUtxo));
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::selectUTXOs(uint64_t fee, float fee_byte, 
   unsigned flags)
{
   //sanity check
   checkSpendVal(spendableBalance_);

   state_utxoVec_.clear();
   PaymentStruct payStruct(recipients_, fee, fee_byte, flags);
   selection_ = move(
      cs_.getUtxoSelectionForRecipients(payStruct, vector<UTXO>()));
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::updateState(
   uint64_t fee, float fee_byte, unsigned flags)
{
   PaymentStruct payStruct(recipients_, fee, fee_byte, flags);
   selection_ = move(
      cs_.getUtxoSelectionForRecipients(payStruct, state_utxoVec_));
}

////////////////////////////////////////////////////////////////////////////////
unsigned CoinSelectionInstance::addRecipient(
   const BinaryData& hash, uint64_t value)
{
   unsigned id = 0;
   if (recipients_.size() != 0)
   {
      auto iter = recipients_.rbegin();
      id = iter->first + 1;
   }

   addRecipient(id, hash, value);
   return id;
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::addRecipient(
   unsigned id, const BinaryData& hash, uint64_t value)
{
   if (hash.getSize() == 0)
      throw CoinSelectionException("empty script hash");

   recipients_.insert(make_pair(id, createRecipient(hash, value)));
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> CoinSelectionInstance::createRecipient(
   const BinaryData& hash, uint64_t value)
{
   shared_ptr<ScriptRecipient> rec;
   auto scrType = *hash.getPtr();

   const auto p2pkh_byte = BlockDataManagerConfig::getPubkeyHashPrefix();
   const auto p2sh_byte = BlockDataManagerConfig::getScriptHashPrefix();

   if (scrType == p2pkh_byte)
   {
      rec = make_shared<Recipient_P2PKH>(
         hash.getSliceRef(1, hash.getSize() - 1), value);
   }
   else if (scrType == p2sh_byte)
   {
      rec = make_shared<Recipient_P2SH>(
         hash.getSliceRef(1, hash.getSize() - 1), value);
   }
   else
      throw CoinSelectionException("unexpected recipient script type");

   return rec;
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::updateRecipient(
   unsigned id, const BinaryData& hash, uint64_t value)
{
   recipients_.erase(id);
   
   addRecipient(id, hash, value);
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::updateOpReturnRecipient(
   unsigned id, const BinaryData& message)
{
   recipients_.erase(id);

   auto recipient = make_shared<Recipient_OPRETURN>(message);
   recipients_.insert(make_pair(id, recipient));
}


////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::removeRecipient(unsigned id)
{
   recipients_.erase(id);
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::resetRecipients()
{
   recipients_.clear();
}

////////////////////////////////////////////////////////////////////////////////
uint64_t CoinSelectionInstance::getSpendVal() const
{
   uint64_t total = 0;
   for (auto& recPair : recipients_)
      total += recPair.second->getValue();

   return total;
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::checkSpendVal(uint64_t spendableBalance) const
{
   auto total = getSpendVal();
   if (total == 0 || total > spendableBalance)
   {
      throw CoinSelectionException("Invalid spend value");
   }
}

////////////////////////////////////////////////////////////////////////////////
void CoinSelectionInstance::processCustomUtxoList(
   const vector<BinaryData>& serializedUtxos,
   uint64_t fee, float fee_byte, unsigned flags)
{
   if (serializedUtxos.size() == 0)
      throw CoinSelectionException("empty custom utxo list!");

   vector<UTXO> utxoVec;

   for (auto& serializedUtxo : serializedUtxos)
   {
      UTXO utxo;
      utxo.unserialize(serializedUtxo);
      utxoVec.push_back(move(utxo));
   }
   
   selectUTXOs(utxoVec, fee, fee_byte, flags);
}

////////////////////////////////////////////////////////////////////////////////
uint64_t CoinSelectionInstance::getFeeForMaxValUtxoVector(
   const vector<BinaryData>& serializedUtxos, float fee_byte)
{
   auto txoutsize = 0;
   for (auto& rec : recipients_)
      txoutsize += rec.second->getSize();

   vector<UTXO> utxoVec;
   if (serializedUtxos.size() > 0)
   {
      for (auto& rawUtxo : serializedUtxos)
      {
         UTXO utxo;
         utxo.unserialize(rawUtxo);
         utxoVec.push_back(move(utxo));
      }

      //decorate coin control selection
      decorateUTXOs(walletContainer_, utxoVec);
   }

   return cs_.getFeeForMaxVal(txoutsize, fee_byte, utxoVec);
}

////////////////////////////////////////////////////////////////////////////////
uint64_t CoinSelectionInstance::getFeeForMaxVal(float fee_byte)
{
   vector<BinaryData> utxos;
   return getFeeForMaxValUtxoVector(utxos, fee_byte);
}

////////////////////////////////////////////////////////////////////////////////
////
//// UniversalSigner
////
////////////////////////////////////////////////////////////////////////////////
UniversalSigner::UniversalSigner(const string& signerType)
{
   if (signerType != "Bcash")
      signer_ = make_unique<Signer>();
   else
      signer_ = make_unique<Signer_BCH>();

   signer_->setFlags(SCRIPT_VERIFY_SEGWIT);

   auto feed = make_shared<ResolverFeed_Universal>(this);
   signer_->setFeed(feed);
}

////////////////////////////////////////////////////////////////////////////////
UniversalSigner::~UniversalSigner()
{}


