////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BtcUtils.h"

const BinaryData BtcUtils::BadAddress_ = BinaryData::CreateFromHex("0000000000000000000000000000000000000000");
const BinaryData BtcUtils::EmptyHash_  = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");

