////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "HistoryPager.h"

uint32_t HistoryPager::txnPerPage_ = 100;

////////////////////////////////////////////////////////////////////////////////
void HistoryPager::addPage(uint32_t count, uint32_t bottom, uint32_t top)
{
   Page newPage(count, bottom, top);
   pages_.push_back(newPage);
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, LedgerEntry>& HistoryPager::getPageLedgerMap(
   function< void(uint32_t, uint32_t, map<BinaryData, TxIOPair>&) > getTxio,
   function< void(map<BinaryData, LedgerEntry>&, 
                  const map<BinaryData, TxIOPair>&, uint32_t) > buildLedgers,
   uint32_t pageId,
   map<BinaryData, TxIOPair>* txioMap)
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   if (pageId >= pages_.size())
      return LedgerEntry::EmptyLedgerMap_;

   currentPage_ = pageId;
   Page& page = pages_[pageId];

   if (page.pageLedgers_.size() != 0)
   {
      //already loaded this page
      return page.pageLedgers_;
   }

   page.pageLedgers_.clear();

   //load page's block range from ssh and build ledgers
   if (txioMap != nullptr)
   {
      getTxio(page.blockStart_, page.blockEnd_, *txioMap);
      buildLedgers(page.pageLedgers_, *txioMap, page.blockStart_);
   }
   else
   {
      map<BinaryData, TxIOPair> txio; 
      getTxio(page.blockStart_, page.blockEnd_, txio);
      buildLedgers(page.pageLedgers_, txio, page.blockStart_);
   }

   return page.pageLedgers_;
}

////////////////////////////////////////////////////////////////////////////////
void HistoryPager::getPageLedgerMap(
   function< void(uint32_t, uint32_t, map<BinaryData, TxIOPair>&) > getTxio,
   function< void(map<BinaryData, LedgerEntry>&,
   const map<BinaryData, TxIOPair>&, uint32_t, uint32_t) > buildLedgers,
   uint32_t pageId,
   map<BinaryData, LedgerEntry>& leMap) const
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   const Page& page = pages_[pageId];

   //load page's block range from ssh and build ledgers
   map<BinaryData, TxIOPair> txio;
   getTxio(page.blockStart_, page.blockEnd_, txio);
   buildLedgers(leMap, txio, page.blockStart_, page.blockEnd_);
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, LedgerEntry>& HistoryPager::getPageLedgerMap(uint32_t pageId)
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   currentPage_ = pageId;
   Page& page = pages_[pageId];

   if (page.pageLedgers_.size() != 0)
   {
      //already loaded this page
      return page.pageLedgers_;
   }
   else return LedgerEntry::EmptyLedgerMap_;
}


////////////////////////////////////////////////////////////////////////////////
bool HistoryPager::mapHistory(
   function< map<uint32_t, uint32_t>(void)> getSSHsummary)
{
   //grab the ssh summary for the pager. This is a map, referencing the amount
   //of txio per block for the given address.
   
   map<uint32_t, uint32_t> newSummary;
   
   try
   {
      newSummary = move(getSSHsummary());
   }
   catch (AlreadyPagedException&)
   {
      return false;
   }

   reset();
   SSHsummary_.clear();
   
   SSHsummary_ = move(newSummary);
   
   if (SSHsummary_.size() == 0)
   {
      addPage(0, 0, UINT32_MAX);
      isInitialized_ = true;
      return true;
   }

   auto histIter = SSHsummary_.crbegin();
   uint32_t threshold = 0;
   uint32_t top = UINT32_MAX;

   while (histIter != SSHsummary_.crend())
   {
      threshold += histIter->second;

      if (threshold > txnPerPage_)
      {
         addPage(threshold, histIter->first, top);

         threshold = 0;
         top = histIter->first - 1;
      }

      ++histIter;
   }

   if (threshold != 0)
      addPage(threshold, 0, top);

   sortPages();

   isInitialized_ = true;
   return true;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t HistoryPager::getPageBottom(uint32_t id) const
{
   if (id < pages_.size())
      return pages_[id].blockStart_;

   return 0;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t HistoryPager::getRangeForHeightAndCount(
   uint32_t height, uint32_t count) const
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   uint32_t total = 0;
   uint32_t top = 0;

   for (const auto& page : pages_)
   {
      if (page.blockEnd_ > height)
      {
         total += page.count_;
         top = page.blockEnd_;

         if (total > count)
            break;
      }
   }

   return top;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t HistoryPager::getBlockInVicinity(uint32_t blk) const
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   uint32_t blkDiff = UINT32_MAX;
   uint32_t blkHeight = UINT32_MAX;

   for (auto& txioRange : SSHsummary_)
   {
      //look for txio summary with closest block
      uint32_t diff = abs(int(txioRange.first - blk));
      if (diff == 0)
         return txioRange.first;
      else if (diff < blkDiff)
      {
         blkHeight = txioRange.first;
         blkDiff = diff;
      }
   }

   return blkHeight;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t HistoryPager::getPageIdForBlockHeight(uint32_t blk) const
{
   if (!isInitialized_)
      throw std::runtime_error("Uninitialized history");

   for (int32_t i = 0; i < pages_.size(); i++)
   {
      auto& page = pages_[i];

      if (blk >= page.blockStart_ && blk <= page.blockEnd_)
         return i;
   }

   return 0;
}
