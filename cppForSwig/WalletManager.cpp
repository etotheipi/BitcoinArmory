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
////
//// WalletContainer
////
////////////////////////////////////////////////////////////////////////////////
void WalletContainer::registerWithBDV(bool isNew)
{
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