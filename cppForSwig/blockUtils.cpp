#include "blockUtils.h"


BlockHeadersManager* BlockHeadersManager::theOnlyBHM_ = NULL;
sha2 BlockHeadersManager::sha256_ = sha2();
