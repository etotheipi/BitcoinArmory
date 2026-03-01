////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef BDM_MAINTHREAD_H
#define BDM_MAINTHREAD_H

#include <string>
#include <stdint.h>

#ifdef _MSC_VER
   #ifndef _WIN32_
      #define _WIN32_
   #endif
#endif

#include "UniversalTimer.h"
#include "bdmenums.h"
#include "BlockUtils.h"
#include "BDM_Server.h"

struct BlockDataManagerConfig;

class BinaryData;

class BDM_CallBack
{
public:
   virtual ~BDM_CallBack();
   virtual void run(BDMAction action, void* ptr, int block=0)=0;
   virtual void progress(
      BDMPhase phase,
      const vector<string> &walletIdVec,
      float progress, unsigned secondsRem,
      unsigned progressNumeric
   )=0;
};

// let an outsider call functions from the BDM thread

class BDMFailure : public std::exception
{
public:
   BDMFailure() { }
};

class BlockDataManager_LevelDB;
class BlockDataViewer;

inline void StartCppLogging(string fname, int lvl) { STARTLOGGING(fname, (LogLevel)lvl); }
inline void ChangeCppLogLevel(int lvl) { SETLOGLEVEL((LogLevel)lvl); }
inline void DisableCppLogging() { SETLOGLEVEL(LogLvlDisabled); }
inline void EnableCppLogStdOut() { LOGENABLESTDOUT(); }
inline void DisableCppLogStdOut() { LOGDISABLESTDOUT(); }



// kate: indent-width 3; replace-tabs on;

#endif
