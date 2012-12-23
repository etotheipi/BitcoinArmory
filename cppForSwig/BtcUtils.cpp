////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BtcUtils.h"

BinaryData BtcUtils::BadAddress_    = BinaryData::CreateFromHex("0000000000000000000000000000000000000000");
BinaryData BtcUtils::EmptyHash_     = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");

