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

////////////////////////////////////////////////////////////////////////////////
void WalletManager::loadWallets()
{
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
         WalletContainer wltCont(wltPtr->getID());
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
