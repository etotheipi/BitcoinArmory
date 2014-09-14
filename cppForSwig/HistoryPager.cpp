#include "HistoryPager.h"

uint32_t HistoryPager::txnPerPage_ = 10;

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
   currentPage_ = pageId;
   Page& page = pages_[pageId];

   if (page.pageLedgers_.size() != 0)
   {
      //already loaded this page
      return page.pageLedgers_;
   }

   page.pageLedgers_.clear();

   //load page's block range from SSH and build ledgers
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
   const Page& page = pages_[pageId];

   //load page's block range from SSH and build ledgers
   map<BinaryData, TxIOPair> txio;
   getTxio(page.blockStart_, page.blockEnd_, txio);
   buildLedgers(leMap, txio, page.blockStart_, page.blockEnd_);
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, LedgerEntry>& HistoryPager::getPageLedgerMap(uint32_t pageId)
{
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
void HistoryPager::mapHistory(
   function< map<uint32_t, uint32_t>(void) > getSSHsummary)
{
   //grab the SSH summary for the pager. This is a map, referencing the amount
   //of txio per block for the given address.
   
   reset();
   SSHsummary_.clear();
   
   SSHsummary_ = getSSHsummary();
   
   if (SSHsummary_.size() == 0)
   {
      addPage(0, 0, UINT32_MAX);
      return;
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

