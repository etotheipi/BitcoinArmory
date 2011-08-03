#include "blockUtils.h"



BlockHeadersManager* BlockHeadersManager::theOnlyBHM_ = NULL;
binaryData BlockHeaderRef::GenesisHash_ = binaryData.createFromHex(GENESIS_HASH_HEX);
binaryData BlockHeaderRef::EmptyHash_   = binaryData.createFromHex(
                "0000000000000000000000000000000000000000000000000000000000000000");
BlockHeaderRef* BlockHeaderRef::topBlockPtr_ = NULL;

CryptoPP::SHA256 BlockHeadersManager::sha256_ = CryptoPP::SHA256();


