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
const string BtcUtils::base58Chars_ = string("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz");

const map<char, uint8_t> BtcUtils::base58Vals_ = {
   { '1', 0 }, { '2', 1 }, { '3', 2 }, { '4', 3 }, { '5', 4 }, { '6', 5 },
   { '7', 6 }, { '8', 7 }, { '9', 8 }, { 'A', 9 }, { 'B', 10 }, { 'C', 11 },
   { 'D', 12 }, { 'E', 13 }, { 'F', 14 }, { 'G', 15 }, { 'H', 16 }, { 'J', 17 },
   { 'K', 18 }, { 'L', 19 }, { 'M', 20 }, { 'N', 21 }, { 'P', 22 }, { 'Q', 23 },
   { 'R', 24 }, { 'S', 25 }, { 'T', 26 }, { 'U', 27 }, { 'V', 28 }, { 'W', 29 },
   { 'X', 30 }, { 'Y', 31 }, { 'Z', 32 }, { 'a', 33 }, { 'b', 34 }, { 'c', 35 },
   { 'd', 36 }, { 'e', 37 }, { 'f', 38 }, { 'g', 39 }, { 'h', 40 }, { 'i', 41 },
   { 'j', 42 }, { 'k', 43 }, { 'm', 44 }, { 'n', 45 }, { 'o', 46 }, { 'p', 47 }, 
   { 'q', 48 }, { 'r', 49 }, { 's', 50 }, { 't', 51 }, { 'u', 52 }, { 'v', 53 }, 
   { 'w', 54 }, { 'x', 55 }, { 'y', 56 }, { 'z', 57 }
};

