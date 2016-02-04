////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockchainScanner.h"

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::scan(uint32_t scanFrom)
{
   //determine which block file number we start scanning from
   auto startHeader = blockchain_->getHeaderByHeight(scanFrom);
   unsigned int startBlkFileNum = startHeader.getBlockFileNum();

   //start write thread

   while (1)
   {
      vector<BlockDataBatch> batchVec;
      batchVec.resize(totalThreadCount_);

      //start batch reader threads

      //start batch scanner threads

      //figure out top scanned block num

      //post to write thread

      startBlkFileNum += nBlockFilesPerBatch_;
   }
}