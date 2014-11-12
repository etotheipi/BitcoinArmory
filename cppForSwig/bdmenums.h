#ifndef _BDM_ENUMS_H
#define _BDM_ENUMS_H

enum BDMPhase
{
   BDMPhase_DBHeaders=1,
   BDMPhase_OrganizingChain,
   BDMPhase_BlockHeaders,
   BDMPhase_BlockData,
   BDMPhase_Rescan
};

enum BDMAction
{
   BDMAction_Ready=1,
   BDMAction_NewBlock,
   BDMAction_ZC,
   BDMAction_Refresh,
   BDMAction_Exited,
   BDMAction_ErrorMsg
};

#endif
