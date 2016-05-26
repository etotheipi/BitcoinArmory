////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BDM_seder.h"

///////////////////////////////////////////////////////////////////////////////
const vector<LedgerEntryData>& LedgerEntryVector::toVector() const
{
   return leVec_;
}
