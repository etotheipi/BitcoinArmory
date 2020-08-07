////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BDM_SERVER_H
#define _BDM_SERVER_H

#include <vector>
#include <map>
#include <mutex>
#include <thread>
#include <future>

#include "BitcoinP2p.h"
#include "./fcgi/include/fcgiapp.h"
#include "./fcgi/include/fcgios.h"

#include "BlockDataViewer.h"
#include "DataObject.h"
#include "BDM_seder.h"
#include "EncryptionUtils.h"
#include "LedgerEntry.h"
#include "DbHeader.h"
#include "FcgiMessage.h"

#define MAX_CONTENT_LENGTH 1024*1024*1024
#define CALLBACK_EXPIRE_COUNT 5

enum WalletType
{
   TypeWallet,
   TypeLockbox
};

///////////////////////////////////////////////////////////////////////////////
class SocketCallback : public Callback
{
private:
   mutex mu_;
   atomic<unsigned> count_;

   function<unsigned(void)> isReady_;

public:
   SocketCallback(function<unsigned(void)> isReady) :
      Callback(), isReady_(isReady)
   {
      count_.store(0, memory_order_relaxed);
   }

   void emit(void);
   Arguments respond(const string&);

   bool isValid(void)
   {
      unique_lock<mutex> lock(mu_, defer_lock);

      if (lock.try_lock())
      {
         auto count = count_.fetch_add(1, memory_order_relaxed) + 1;
         if (count >= CALLBACK_EXPIRE_COUNT)
            return false;
      }

      return true;
   }

   ~SocketCallback(void)
   {
      Callback::shutdown();

      //after signaling shutdown, grab the mutex to make sure 
      //all responders threads have terminated
      unique_lock<mutex> lock(mu_);
   }

   void resetCounter(void)
   {
      count_.store(0, memory_order_relaxed);
   }
};

///////////////////////////////////////////////////////////////////////////////
class BDV_Server_Object : public BlockDataViewer
{
   friend class Clients;

private:
   map<string, function<Arguments(
      const vector<string>&, Arguments&)>> methodMap_;
   
   thread tID_, initT_;
   shared_ptr<SocketCallback> cb_;

   string bdvID_;
   BlockDataManagerThread* bdmT_;

   map<string, LedgerDelegate> delegateMap_;

   struct walletRegStruct
   {
      vector<BinaryData> scrAddrVec;
      string IDstr;
      bool isNew;
      WalletType type_;
   };

   mutex registerWalletMutex_;
   map<string, walletRegStruct> wltRegMap_;

   shared_ptr<promise<bool>> isReadyPromise_;
   shared_future<bool> isReadyFuture_;

public:

   BlockingStack<shared_ptr<BDV_Notification>> notificationStack_;

private:
   BDV_Server_Object(BDV_Server_Object&) = delete; //no copies
   
   void registerCallback();
   
   void buildMethodMap(void);
   void startThreads(void);

   bool registerWallet(
      vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew);
   bool registerLockbox(
      vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew);
   void registerAddrVec(const string&, vector<BinaryData> const& scrAddrVec);

   void pushNotification(unique_ptr<BDV_Notification> notifPtr)
   {
      notificationStack_.push_back(move(notifPtr));
   }

   void resetCounter(void) const
   {
      if (cb_ != nullptr)
         cb_->resetCounter();
   }

public:
   BDV_Server_Object(BlockDataManagerThread *bdmT);
   ~BDV_Server_Object(void) 
   { 
      haltThreads(); 
   }

   const string& getID(void) const { return bdvID_; }
   void maintenanceThread(void);
   void init(void);

   Arguments executeCommand(const string& method, 
                              const vector<string>& ids, 
                              Arguments& args);
  
   void zcCallback(
      map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> zcMap);
   void progressCallback(BDMPhase phase, double progress,
      unsigned time, unsigned numericProgress);
   void zcErrorCallback(string&, string&);

   void haltThreads(void);
};

///////////////////////////////////////////////////////////////////////////////
class Clients
{
private:
   TransactionalMap<string, shared_ptr<BDV_Server_Object>> BDVs_;
   mutable BlockingStack<bool> gcCommands_;
   BlockDataManagerThread* bdmT_;

   function<void(void)> fcgiShutdownCallback_;

   atomic<bool> run_;

   thread mainteThr_;
   thread gcThread_;

private:
   void maintenanceThread(void) const;
   void garbageCollectorThread(void);
   void unregisterAllBDVs(void);

public:

   Clients(BlockDataManagerThread* bdmT,
      function<void(void)> shutdownLambda) :
      bdmT_(bdmT), fcgiShutdownCallback_(shutdownLambda)
   {
      run_.store(true, memory_order_relaxed);

      auto mainthread = [this](void)->void
      {
         maintenanceThread();
      };

      auto gcThread = [this](void)->void
      {
         garbageCollectorThread();
      };

      mainteThr_ = thread(mainthread);

      //no gc for unit tests
      if (bdmT_->bdm()->config().nodeType_ == Node_UnitTest)
         return;

      gcThread_ = thread(gcThread);
   }

   const shared_ptr<BDV_Server_Object>& get(const string& id) const;
   Arguments runCommand(const string& cmd);
   Arguments processShutdownCommand(Command&);
   Arguments registerBDV(Arguments& arg);
   void unregisterBDV(const string& bdvId);
   void shutdown(void);
   void exitRequestLoop(void);
};

///////////////////////////////////////////////////////////////////////////////
class FCGI_Server
{
   /***
   Figure if it should use a socket or a named pipe.
   Force it to listen only to localhost if we use a socket 
   (both in *nix and win32 code files)
   ***/

private:
   SOCKET sockfd_ = -1;
   mutex mu_;
   int run_ = true;
   atomic<uint32_t> liveThreads_;

   const string port_;
   const string ip_;

   Clients clients_;

private:
   function<void(void)> getShutdownCallback(void)
   {
      auto shutdownCallback = [this](void)->void
      {
         this->haltFcgiLoop();
      };

      return shutdownCallback;
   }

public:
   FCGI_Server(BlockDataManagerThread* bdmT, string port, bool listen_all) :
      clients_(bdmT, getShutdownCallback()),
      ip_(listen_all ? "" : "127.0.0.1"), port_(port)
   {
      LOGINFO << "Listening on port " << port;
      if (listen_all)
         LOGWARN << "Listening to all incoming connections";

      liveThreads_.store(0, memory_order_relaxed);
   }

   void init(void);
   void enterLoop(void);
   void processRequest(FCGX_Request* req);
   void haltFcgiLoop(void);
   void shutdown(void) { clients_.shutdown(); }
   void checkSocket(void) const;
};

#endif
