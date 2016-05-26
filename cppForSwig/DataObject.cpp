////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "DataObject.h"

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const ErrorType& et)
{
   os << et.err_;

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, ErrorType& et)
{
   is >> et.err_;

   return is;
}

///////////////////////////////////////////////////////////////////////////////
const vector<shared_ptr<DataMeta>> DataMeta::iTypeIDs_ = {
   make_shared<DataObject<int>>(),
   make_shared<DataObject<unsigned int>>(),
   make_shared<DataObject<uint64_t>>(),
   make_shared<DataObject<size_t>>(),
   make_shared<DataObject<string>>(),
   make_shared<DataObject<BinaryDataObject>>(),
   make_shared<DataObject<BinaryDataVector>>(),
   make_shared<DataObject<LedgerEntryVector>>(),
   make_shared<DataObject<UtxoVector>>(),
   make_shared<DataObject<ErrorType>>()
};

map<string, uint32_t> DataMeta::strTypeIDs_;

///////////////////////////////////////////////////////////////////////////////
void DataMeta::initTypeMap()
{
   auto iter = iTypeIDs_.begin();

   while (iter != iTypeIDs_.end())
   {
      auto id = iter - iTypeIDs_.begin();
      strTypeIDs_[(*iter)->getTypeName()] = id;

      iter++;
   }
}
