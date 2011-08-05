#include "blockUtils.h"



BlockHeadersManager* BlockHeadersManager::theOnlyBHM_ = NULL;
binaryData BlockHeaderRef::GenesisHash_ = binaryData::CreateFromHex(GENESIS_HASH_HEX);
binaryData BlockHeaderRef::EmptyHash_   = binaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");

CryptoPP::SHA256 BlockHeadersManager::sha256_ = CryptoPP::SHA256();


