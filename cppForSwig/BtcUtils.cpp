#include "BtcUtils.h"

BinaryData BtcUtils::badAddress_ = BinaryData(0);
BinaryData BtcUtils::GenesisHash_ = BinaryData::CreateFromHex(GENESIS_HASH_HEX);
BinaryData BtcUtils::EmptyHash_   = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");

//CryptoPP::SHA256 BtcUtils::sha256_ = CryptoPP::SHA256();
