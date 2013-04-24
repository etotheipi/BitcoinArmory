
#include <iostream>
#include <vector>
#include "BinaryData.h"
#include "BtcUtils.h"



class PartialMerkleTree
{
public:
   class MerkleNode
   {
   public:
      BinaryData  nodeHash_;
      bool        isOnPath_;
      bool        isLeaf_;
      uint32_t    txIndex_;
      MerkleNode* ptrLeft_;
      MerkleNode* ptrRight_;

      MerkleNode(void) : nodeHash_(0), isOnPath_(false), isLeaf_(false),
                         ptrLeft_(NULL), ptrRight_(NULL) {}
   };

   /////////////////////////////////////////////////////////////////////////////
   ~PartialMerkleTree(void)
   {
      if(root_)
      {
         recurseDestroyTree(root_);
         delete root_;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   static void recurseDestroyTree(MerkleNode* node)
   {
      if(node->isLeaf_)
         return;

      if(ptrLeft_)  destroyTree(node->ptrLeft_);
      if(ptrRight_) destroyTree(node->ptrRight_);
      if(ptrLeft_)  delete ptrLeft_;
      if(ptrRight_) delete ptrRight_;
   }
   
   /////////////////////////////////////////////////////////////////////////////
   // In this function "bits" is just a linear list of size=numTx which says 
   // if we care about the hash or not.   Zero length if reconstructing
   // "hashes" is a vector... zero-length if we are reconstructing the tree,
   // which contains all the leaf nodes (size=numtx).
   PartialMerkleTree(uint32_t nTx, vector<bool> bits, vector<HashString> hashes)
   {
      numTx_ = nTx;
      static CryptoPP::SHA256 sha256_;
      BinaryData hashOut(32);
      uint32_t nLevel = nTx
      vector<MerkleNode*> levelH(nLevel)

      // Setup leaf nodes
      for(uint32_t i=0; i<nTx; i++)
      {
         levelH[i] = new MerkleNode;
         levelH[i]->txIndex_ = i;
         levelH[i]->isLeaf_ = true;
         if(bits.size()>0 && bits[i])
            levelH[i]->isOnPath_ = true;
         if(hashes.size()>0)
            levelH[i]->nodeHash_ = hashes[i];
      }

      while( nLevel > 1 )
      {
         vector<MerkleNode*> levelHp1( (nLevel+1)/2 )
         for(uint32_t i=0; i<nLevel; i+=2)
         {
            MerkleNode* newNode = new MerkleNode;
            if(levelH[i]->isOnPath_ || levelH[i+1]->isOnPath_ )
               newNode->isOnPath_ = true;

            newNode->ptrLeft_ = levelH[i];
            if(i != nLevel-1)
               newNode->ptrRight_ = levelH[i+1];

            if(hashes.size() > 0)
            {
               BinaryData combined = levelH[i]->nodeHash_;
               if(i==nLevel-1) combined = combined + levelH[i]->nodeHash_;
               else            combined = combined + levelH[i+1]->nodeHash_;

               newNode->resize(32);
               sha256_.CalculateDigest(newNode.getPtr(), combined.getPtr(), 64);
               sha256_.CalculateDigest(newNode.getPtr(),  newNode.getPtr(), 32);
            }
            levelHp1[i/2] = newNode;
         } 
         levelH = levelHp1;
         nLevel = (nLevel+1)/2;
      }
      root_ = levelH[0];
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      if( ! root->isOnPath_ )
         return BinaryData(0);

      BinaryReader br(serialized);
   
      list<bool> vBits;
      list<HashString> vHash;

      recurseSerializeTree(root_, vBits, vHash);

      BinaryWriter bw;
      
      // uint32_t - Num Tx
      bw.put_uint32_t(numTx)

      // var_int + vector<hash>  - Num Hash + HashList
      bw.put_var_int(vHash.size())
      for(list<HashString>::iterator iter=vHash.begin(); iter!=vHash.end(); iter++)
         bw.put_BinaryData(*vHash)

      // var_int + vector<bool>  - Num Bits + BitList
      bw.put_var_int(vBits.size())
      bw.put_BinaryData( BtcUtils::CompactBits(vBits) )

      return bw.getData();

   }

   PartialMerkleTree unserialize(BinaryData serialized)
   {
      if( ! root->isOnPath_ )
         return BinaryData(0);
   
      PartialMerkleTree pmt;
      list<bool> vBits;
      list<HashString> vHash;

      recurseUnserializeTree(pmt.root_, vBits, vHash);

      BinaryWriter bw;
      bw.put_uint32_t(numTx)
      bw.put_BinaryData( BtcUtils::CompactBits(vBits) )
      for(list<HashString>::iterator iter=vHash.begin(); iter!=vHash.end(); iter++)
         bw.put_BinaryData(*vHash)
   }

   static void recurseSerializeTree(MerkleNode* node, 
                                    list<bool> & vBits, 
                                    list<HashString> & vHash)
   {
      vBits.push_back(node->isOnPath_);
      if(!node->isOnPath_ || node->isLeaf_)
      {
         vHash.push_back(node->nodeHash_);
         return;
      }

      if(node->ptrLeft_)
         recurseSerializeTree(node->ptrLeft_, vBits, vHash);
       
      if(node->ptrRight_)
         recurseSerializeTree(node->ptrRight_, vBits, vHash);
   }

   static void recurseUnserializeTree( MerkleNode* node,
                                       list<bool> & vBits, 
                                       list<HashString> & vHash)
   {
      list<bool>::iterator bIter = vBits.begin();
      list<HashString>::iterator hIter = vHash.begin();
      node->isOnPath_ = *bIter;
      vBits.erase(bIter);
      if(!node->isOnPath_  || node->isLeaf_)
      {
         node->nodeHash_ = *hIter;
         vHash.erase(hIter);
      }

      if(node->ptrLeft_)
         recurseUnserializeTree(node->ptrLeft_, vBits, vHash);
       
      if(node->ptrRight_)
         recurseUnserializeTree(node->ptrRight_, vBits, vHash);
   }


private:
   MerkleNode root_;
   uint32_t numTx_;
};




