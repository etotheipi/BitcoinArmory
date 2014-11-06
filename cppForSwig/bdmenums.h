#ifndef _BDM_ENUMS_H
#define _BDM_ENUMS_H

typedef enum
{
   BDMPhase_BlockHeaders,
   BDMPhase_BlockData,
   BDMPhase_Rescan
}BDMPhase;

typedef enum
{
   BDMAction_Ready,
   BDMAction_NewBlock,
   BDMAction_ZC,
   BDMAction_Refresh,
   BDMAction_Exited,
   BDMAction_ErrorMsg
}BDMAction;

#endif