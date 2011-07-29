#include "blockUtils.h"



BlockHeadersManager* BlockHeadersManager::theOnlyBHM_ = NULL;

CryptoPP::SHA256 BlockHeadersManager::sha256_ = CryptoPP::SHA256();


