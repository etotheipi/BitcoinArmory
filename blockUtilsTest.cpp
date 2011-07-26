#include <iostream>
#include <fstream>
#include "sha2.h"
#include "blockUtils.h"




int main(void)
{
   BinaryData bd(80);
   for(int i=0; i<80; i++) bd[i] = i;

   BlockHeadersManager & bhm = BlockHeadersManager::GetInstance(); 


}
