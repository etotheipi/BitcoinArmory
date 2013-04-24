
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

      if(node->ptrLeft_)  recurseDestroyTree(node->ptrLeft_);
      if(node->ptrRight_) recurseDestroyTree(node->ptrRight_);
      if(node->ptrLeft_)  delete node->ptrLeft_;
      if(node->ptrRight_) delete node->ptrRight_;
   }

   
   PartialMerkleTree(uint32_t nTx, 
                     vector<bool> const * bits=NULL, 
                     vector<HashString> const * hashes=NULL)
   {
      createTreeNodes(nTx, bits, hashes);
   }
   
   /////////////////////////////////////////////////////////////////////////////
   // "bits" and "hashes" are vectors of size=numTx
   void createTreeNodes(uint32_t nTx, 
                        vector<bool> const * bits=NULL, 
                        vector<HashString> const * hashes=NULL)
   {
      numTx_ = nTx;
      static CryptoPP::SHA256 sha256_;
      BinaryData hashOut(32);
      uint32_t nLevel = nTx;
      vector<MerkleNode*> levelLower(nLevel);

      // Setup leaf nodes
      for(uint32_t i=0; i<nTx; i++)
      {
         levelLower[i] = new MerkleNode;
         levelLower[i]->txIndex_ = i;
         levelLower[i]->isLeaf_ = true;
         if(bits && (*bits)[i])
            levelLower[i]->isOnPath_ = true;
         if(hashes)
            levelLower[i]->nodeHash_ = (*hashes)[i];
      }

      while( nLevel > 1 )
      {
         vector<MerkleNode*> levelUpper( (nLevel+1)/2 );
         for(uint32_t i=0; i<nLevel; i+=2)
         {
            MerkleNode* newNode = new MerkleNode;
            if(levelLower[i]->isOnPath_ || levelLower[i+1]->isOnPath_ )
               newNode->isOnPath_ = true;

            newNode->ptrLeft_ = levelLower[i];
            if(i != nLevel-1)
               newNode->ptrRight_ = levelLower[i+1];

            if(hashes)
               newNode->nodeHash_ = recurseCalcHash(newNode);

            levelUpper[i/2] = newNode;
         } 
         levelLower = levelUpper;
         nLevel = (nLevel+1)/2;
      }
      root_ = levelLower[0];
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      if( ! root_->isOnPath_ )
         return BinaryData(0);

      BinaryWriter bw;
   
      list<bool> vBits;
      list<HashString> vHash;

      recurseSerializeTree(root_, vBits, vHash);

      // uint32_t - Num Tx
      bw.put_uint32_t(numTx_);

      // var_int + vector<hash>  - Num Hash + HashList
      bw.put_var_int(vHash.size());
      list<HashString>::iterator iter;
      for(iter = vHash.begin(); iter != vHash.end(); iter++)
         bw.put_BinaryData(*iter);

      // var_int + vector<bool>  - Num Bits + BitList
      bw.put_var_int(vBits.size());
      bw.put_BinaryData( BtcUtils::PackBits(vBits) );

      return bw.getData();
   }


   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryData serialized)
   {
      if( ! root_->isOnPath_ )
         return;
   
      // Destroy the tree if it already exists
      recurseDestroyTree(root_);

      list<HashString> vHash;

      // Read numTx
      BinaryReader br(serialized);
      uint32_t numTx = br.get_uint32_t();
      
      // Create all the nodes in the tree
      createTreeNodes(numTx);

      // Read and prepare vBits for depth-first search
      uint32_t numBits = (uint32_t)br.get_var_int();
      BinaryData vBytes;
      br.get_BinaryData(vBytes, (numBits+7)/8);
      list<bool> vBits = BtcUtils::UnpackBits(vBytes, numBits);
      
      // Read and prepare vHash for depth-first search
      uint32_t numHash = (uint32_t)br.get_var_int();
      BinaryData hash(32);
      for(uint32_t i=0; i<numHash; i++)
      {
         br.get_BinaryData( hash, 32);
         vHash.push_back(hash);
      }

      recurseUnserializeTree(root_, vBits, vHash);
      recurseCalcHash(root_);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData recurseCalcHash(MerkleNode* node)
   {
      static CryptoPP::SHA256 sha256_;
      if(node->nodeHash_.getSize() > 0)
         return node->nodeHash_;

      if(node->isLeaf_)
         cout << "ERROR:  leaf node without hash?" << endl;

      BinaryData combined(64);
      BinaryData left(32);

      left = recurseCalcHash(node->ptrLeft_);
      left.copyTo(combined.getPtr(), 32);
      if(node->ptrRight_)
         recurseCalcHash(node->ptrRight_).copyTo(combined.getPtr()+32, 32);
      else
         left.copyTo(combined.getPtr()+32, 32);

      BinaryData finalHash(32);
      sha256_.CalculateDigest(finalHash.getPtr(),  combined.getPtr(), 64);
      sha256_.CalculateDigest(finalHash.getPtr(), finalHash.getPtr(), 32);
      return finalHash; 
   }

   /////////////////////////////////////////////////////////////////////////////
   static void recurseSerializeTree(MerkleNode* node, 
                                    list<bool> & vBits, 
                                    list<HashString> & vHash)
   {
      cout << "Pushing bit: " << (node->isOnPath_) << endl;
      vBits.push_back(node->isOnPath_);
      if(!node->isOnPath_ || node->isLeaf_)
      {
         cout << "Pushing hash: " << node->nodeHash_.toHexStr() << endl;
         vHash.push_back(node->nodeHash_);
         return;
      }

      if(node->ptrLeft_)
         recurseSerializeTree(node->ptrLeft_, vBits, vHash);
       
      if(node->ptrRight_)
         recurseSerializeTree(node->ptrRight_, vBits, vHash);
   }

   /////////////////////////////////////////////////////////////////////////////
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
   MerkleNode* root_;
   uint32_t numTx_;
};




