#include "blockUtils.h"



BlockDataManager* BlockDataManager::theOnlyBDM_ = NULL;
BinaryData TxOut::badAddress_ = BinaryData(0);
BinaryData BlockHeader::GenesisHash_ = BinaryData::CreateFromHex(GENESIS_HASH_HEX);
BinaryData BlockHeader::EmptyHash_   = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");

CryptoPP::SHA256 BlockHeader::sha256_ = CryptoPP::SHA256();



