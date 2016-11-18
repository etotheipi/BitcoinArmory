////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _WALLET_MANAGER_H
#define _WALLET_MANAGER_H

using namespace std;

#include <mutex>
#include <memory>
#include <string>
#include <map>
#include <iostream>

#include "log.h"
#include "Wallets.h"
#include "SwigClient.h"

////////////////////////////////////////////////////////////////////////////////
class WalletContainer
{
   friend class WalletManager;

private:
   const string id_;
   shared_ptr<AssetWallet> wallet_;
   shared_ptr<SwigClient::BtcWallet> swigWallet_;

public:
   WalletContainer(const string& id) :
      id_(id)
   {}

   shared_ptr<AssetWallet> getWalletPtr(void) const
   {
      return wallet_;
   }
};

////////////////////////////////////////////////////////////////////////////////
class WalletManager
{
private:
   mutable mutex mu_;

   const string path_;
   map<string, WalletContainer> wallets_;

private:
   void loadWallets();

public:
   WalletManager(const string& path) :
      path_(path)
   {
      loadWallets();
   }

   bool haveWallet(const string& id)
   {
      unique_lock<mutex> lock(mu_);
      auto wltIter = wallets_.find(id);
      
      return wltIter != wallets_.end();
   }

   void mirrorWatchOnlyWallet(
      const SecureBinaryData& pubRoot,
      const SecureBinaryData& chainCode,
      unsigned chainLength);

   void synchronizeWallet(const string& id, unsigned chainLength);

   shared_ptr<AssetWallet> getWalletPtr(const string& id) const
   {
      unique_lock<mutex> lock(mu_);

      auto iter = wallets_.find(id);
      if (iter == wallets_.end())
         throw runtime_error("invalid wallet id");

      return iter->second.getWalletPtr();
   }
};

#endif