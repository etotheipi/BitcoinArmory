#include <limits.h>
#include <iostream>
#include <stdlib.h>

#include "../log.h"
#include "../BinaryData.h"
#include "../BtcUtils.h"
#include "../BlockObj.h"
#include "../StoredBlockObj.h"
#include "../PartialMerkle.h"
#include "../leveldb_wrapper.h"
#include "../BlockUtils.h"

#define READHEX BinaryData::CreateFromHex
#define TheBDM BlockDataManager_LevelDB::GetInstance()


int main(void)
{
   std::cout << "Running stub main function that does nothing!" << endl;

   // Setup the log file 
   STARTLOGGING("cppTestsLog.txt", LogLvlDebug2);

   uint32_t i;
   cout << "Enter anything to continue" << endl;
   cin >> i;

   return 0;
}






