#ifndef BDM_MAINTHREAD_H
#define BDM_MAINTHREAD_H

#include "BlockUtils.h"

class BDM_CallBack
{
public:
   virtual ~BDM_CallBack() {}
   virtual void run(int action, int arg)=0;
};

BlockDataManager_LevelDB *startBDM(int mode, BDM_CallBack *callback);


#endif
