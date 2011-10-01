#include "BtcUtils.h"

BinaryData BtcUtils::BadAddress_  = BinaryData::CreateFromHex("0000000000000000000000000000000000000000");
BinaryData BtcUtils::GenesisHash_ = BinaryData::CreateFromHex(GENESIS_HASH_HEX);
BinaryData BtcUtils::EmptyHash_   = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");
BinaryData BtcUtils::MagicBytes_  = BinaryData::CreateFromHex(MAGIC_BYTES);

