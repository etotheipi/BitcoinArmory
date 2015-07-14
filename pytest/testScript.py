import sys
sys.path.append('..')
import unittest

from armoryengine.ALL import *

class ScriptTests(unittest.TestCase):

   def setUp(self):
      useMainnet()
      self.sp = PyScriptProcessor()

   def testUnimplemented(self):
      for op in (OP_IF, OP_NOTIF, OP_ELSE, OP_ENDIF):
         self.assertEqual(self.sp.executeOpCode(op, None, None, None),
                          OP_NOT_IMPLEMENTED)

   def testDisabled(self):
      for op in (OP_CAT, OP_SUBSTR, OP_LEFT, OP_RIGHT, OP_INVERT, OP_AND,
                 OP_OR, OP_XOR, OP_2MUL, OP_2DIV, OP_MUL, OP_DIV, OP_MOD,
                 OP_LSHIFT, OP_RSHIFT):
         self.assertEqual(self.sp.executeOpCode(op, None, None, None),
                          OP_DISABLED)

   def testOpFalse(self):
      stack = []
      self.sp.executeOpCode(OP_FALSE, None, stack, None)
      self.assertEqual(stack, [0])

   def testOpTrue(self):
      stack = []
      self.sp.executeOpCode(OP_TRUE, None, stack, None)
      self.assertEqual(stack, [1])

   def testOpData(self):
      stack = []
      data = BinaryUnpacker('hello')
      self.sp.executeOpCode(5, data, stack, None)
      self.assertEqual(stack, ['hello'])

   def testOpPushData1(self):
      stack = []
      data = BinaryUnpacker('\x01\x04')
      self.sp.executeOpCode(OP_PUSHDATA1, data, stack, None)
      self.assertEqual(stack, ['\x04'])

   def testOpPushData2(self):
      stack = []
      data = BinaryUnpacker('\x02\x00\x01\x00')
      self.sp.executeOpCode(OP_PUSHDATA2, data, stack, None)
      self.assertEqual(stack, ['\x01\x00'])

   def testOpPushData4(self):
      stack = []
      data = BinaryUnpacker('\x02\x00\x00\x00\x02\x00')
      self.sp.executeOpCode(OP_PUSHDATA4, data, stack, None)
      self.assertEqual(stack, ['\x02\x00'])

   def testOp1Negate(self):
      stack = []
      self.sp.executeOpCode(OP_1NEGATE, None, stack, None)
      self.assertEqual(stack, [-1])

   def testOpNum(self):
      stack = []
      self.sp.executeOpCode(OP_5, None, stack, None)
      self.assertEqual(stack, [5])

   def testOpNop(self):
      stack = []
      self.sp.executeOpCode(OP_NOP, None, stack, None)
      self.assertEqual(stack, [])

   def testOpVerify(self):
      stack = [1]
      self.sp.executeOpCode(OP_VERIFY, None, stack, None)
      self.assertEqual(stack, [])
      stack = [0]
      result = self.sp.executeOpCode(OP_VERIFY, None, stack, None)
      self.assertEqual(result, TX_INVALID)

   def testOpReturn(self):
      self.assertEqual(self.sp.executeOpCode(OP_RETURN, None, None, None),
                       TX_INVALID)

   def testOpToAltStack(self):
      stack = [1]
      alt = []
      self.sp.executeOpCode(OP_TOALTSTACK, None, stack, alt)
      self.assertEqual(stack, [])
      self.assertEqual(alt, [1])

   def testOpToAltStack(self):
      stack = []
      alt = [1]
      self.sp.executeOpCode(OP_FROMALTSTACK, None, stack, alt)
      self.assertEqual(stack, [1])
      self.assertEqual(alt, [])

   def testOpIfDup(self):
      stack = [7]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_IFDUP, None, stack, None)
      self.assertEqual(stack, [7, 7])
      stack = [0]
      self.sp.executeOpCode(OP_IFDUP, None, stack, None)
      self.assertEqual(stack, [0])

   def testOpDepth(self):
      stack = [0,0,0,0]
      self.sp.executeOpCode(OP_DEPTH, None, stack, None)
      self.assertEqual(stack, [0,0,0,0,4])

   def testOpDrop(self):
      stack = [0,0,0,0]
      self.sp.executeOpCode(OP_DROP, None, stack, None)
      self.assertEqual(stack, [0,0,0])
      
   def testOpDup(self):
      stack = [0,0,0,0]
      self.sp.executeOpCode(OP_DUP, None, stack, None)
      self.assertEqual(stack, [0,0,0,0,0])

   def testOpNip(self):
      stack = [1,2,3,4]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NIP, None, stack, None)
      self.assertEqual(stack, [1,2,4])

   def testOpOver(self):
      stack = [1,2,3,4]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_OVER, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,3])

   def testOpPick(self):
      stack = [1,2,3,4,1]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_PICK, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,4])

   def testOpRoll(self):
      stack = [1,2,3,4,2]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_ROLL, None, stack, None)
      self.assertEqual(stack, [1,3,4,2])

   def testOpRot(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_ROT, None, stack, None)
      self.assertEqual(stack, [1,2,4,5,3])

   def testOpSwap(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_SWAP, None, stack, None)
      self.assertEqual(stack, [1,2,3,5,4])

   def testOpTuck(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_TUCK, None, stack, None)
      self.assertEqual(stack, [1,2,3,5,4,5])

   def testOp2Dup(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_2DUP, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,4,5])

   def testOp3Dup(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_3DUP, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,3,4,5])

   def testOp2Over(self):
      stack = [1,2,3,4,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_2OVER, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,2,3])

   def testOp2Rot(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_2ROT, None, stack, None)
      self.assertEqual(stack, [3,4,5,6,1,2])

   def testOp2Swap(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_2SWAP, None, stack, None)
      self.assertEqual(stack, [1,2,5,6,3,4])

   def testOpSize(self):
      stack = [1,2,3,4,5,'hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_SIZE, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,'hello',5])

   def testOpEqual(self):
      stack = [1,2,3,4,5,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_EQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_EQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpEqualVerify(self):
      stack = [1,2,3,4,5,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_EQUALVERIFY, None, stack, None)
      self.assertEqual(stack, [1,2,3,4])
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      result = self.sp.executeOpCode(OP_EQUALVERIFY, None, stack, None)
      self.assertEqual(result, TX_INVALID)

   def testOp1Add(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_1ADD, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,7])

   def testOp1Sub(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_1SUB, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,5])

   def testOpNegate(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NEGATE, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,-6])

   def testOpAbs(self):
      stack = [1,2,3,4,5,-6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_ABS, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,6])

   def testOpNot(self):
      stack = [1,2,3,4,5,0]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NOT, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,1])
      self.sp.executeOpCode(OP_NOT, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,0])

   def testOp0NotEqual(self):
      stack = [1,2,3,4,5,0]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_0NOTEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,1])
      self.sp.executeOpCode(OP_0NOTEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,5,0])

   def testOpAdd(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_ADD, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,11])

   def testOpSub(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_SUB, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,-1])

   def testOpBoolAnd(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_BOOLAND, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,0,1]
      self.sp.executeOpCode(OP_BOOLAND, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpBoolOr(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_BOOLOR, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,0,0]
      self.sp.executeOpCode(OP_BOOLOR, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpNumEqual(self):
      stack = [1,2,3,4,5,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NUMEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,0,5]
      self.sp.executeOpCode(OP_NUMEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpNumEqualVerify(self):
      stack = [1,2,3,4,5,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NUMEQUALVERIFY, None, stack, None)
      self.assertEqual(stack, [1,2,3,4])
      stack = [1,2,3,4,0,5]
      result = self.sp.executeOpCode(OP_NUMEQUALVERIFY, None, stack, None)
      self.assertEqual(result, TX_INVALID)

   def testOpNumNotEqual(self):
      stack = [1,2,3,4,5,5]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_NUMNOTEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])
      stack = [1,2,3,4,0,5]
      self.sp.executeOpCode(OP_NUMNOTEQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])

   def testOpLessThan(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_LESSTHAN, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,6,5]
      self.sp.executeOpCode(OP_LESSTHAN, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpGreaterThan(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_GREATERTHAN, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])
      stack = [1,2,3,4,6,5]
      self.sp.executeOpCode(OP_GREATERTHAN, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])

   def testOpLessThanOrEqual(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_LESSTHANOREQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])
      stack = [1,2,3,4,6,5]
      self.sp.executeOpCode(OP_LESSTHANOREQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])

   def testOpGreaterThanOrEqual(self):
      stack = [1,2,3,4,5,6]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_GREATERTHANOREQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,0])
      stack = [1,2,3,4,6,5]
      self.sp.executeOpCode(OP_GREATERTHANOREQUAL, None, stack, None)
      self.assertEqual(stack, [1,2,3,4,1])

   def testOpMin(self):
      stack = [1,2]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_MIN, None, stack, None)
      self.assertEqual(stack, [1])

   def testOpMax(self):
      stack = [1,2]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_MAX, None, stack, None)
      self.assertEqual(stack, [2])

   def testOpWithin(self):
      stack = [4,1,7]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_WITHIN, None, stack, None)
      self.assertEqual(stack, [1])
      stack = [0,1,7]
      self.sp.stack = stack
      self.sp.executeOpCode(OP_WITHIN, None, stack, None)
      self.assertEqual(stack, [0])

   def testOpRIPEMD160(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_RIPEMD160, None, stack, None)
      self.assertEqual(len(stack[0]), 20)

   def testOpSHA1(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_SHA1, None, stack, None)
      self.assertEqual(len(stack[0]), 20)

   def testOpSHA256(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_SHA256, None, stack, None)
      self.assertEqual(len(stack[0]), 32)

   def testOpHASH160(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_HASH160, None, stack, None)
      self.assertEqual(len(stack[0]), 20)

   def testOpHASH256(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_HASH256, None, stack, None)
      self.assertEqual(len(stack[0]), 32)

   def testOpCodeSeparator(self):
      stack = ['hello']
      self.sp.stack = stack
      self.sp.executeOpCode(OP_CODESEPARATOR, BinaryUnpacker(''), stack, None)
      self.assertEqual(stack, ['hello'])

