################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
################################################################################
################################################################################
#
# SelectCoins algorithms
#
#   The following methods define multiple ways that one could select coins
#   for a given transaction.  However, the "best" solution is extremely
#   dependent on the variety of unspent outputs, and also the preferences
#   of the user.  Things to take into account when selecting coins:
#
#     - Number of inputs:  If we have a lot of inputs in this transaction
#                          from different addresses, then all those addresses
#                          have now been linked together.  We want to use
#                          as few outputs as possible
#
#     - Tx Fess/Size:      The bigger the transaction, in bytes, the more
#                          fee we're going to have to pay to the miners
#
#     - Priority:          Low-priority transactions might require higher
#                          fees and/or take longer to make it into the
#                          blockchain.  Priority is the sum of TxOut
#                          priorities:  (NumConfirm * NumBTC / SizeKB)
#                          We especially want to avoid 0-confirmation txs
#
#     - Output values:     In almost every transaction, we must return
#                          change to ourselves.  This means there will
#                          be two outputs, one to the recipient, one to
#                          us.  We prefer that both outputs be about the
#                          same size, so that it's not clear which is the
#                          recipient, which is the change.  But we don't
#                          want to use too many inputs to do this.
#
#     - Sustainability:    We should pick a strategy that tends to leave our
#                          wallet containing a variety of TxOuts that are
#                          well-suited for future transactions to benefit.
#                          For instance, always favoring the single TxOut
#                          with a value close to the target, will result
#                          in a future wallet full of tiny TxOuts.  This
#                          guarantees that in the future, we're going to
#                          have to do 10+ inputs for a single Tx.
#
#
#   The strategy is to execute a half dozen different types of SelectCoins
#   algorithms, each with a different goal in mind.  Then we examine each
#   of the results and evaluate a "select-score."  Use the one with the
#   best score.  In the future, we could make the scoring algorithm based
#   on user preferences.  We expect that depending on what the availble
#   list looks like, some of these algorithms could produce perfect results,
#   and in other instances *terrible* results.
#
################################################################################
################################################################################
import math
import random

from armoryengine.ArmoryUtils import CheckHash160, binary_to_hex, coin2str, \
   hash160_to_addrStr, ONE_BTC, CENT, int_to_binary, MIN_RELAY_TX_FEE, MIN_TX_FEE
from armoryengine.Timer import TimeThisFunction
from armoryengine.Transaction import *


################################################################################
# These would normally be defined by C++ and fed in, but I've recreated
# the C++ class here... it's really just a container, anyway
#
# TODO:  LevelDB upgrade: had to upgrade this class to use arbitrary 
#        ScrAddress "notation", even though everything else on the python
#        side expects pure hash160 values.  For now, it looks like it can
#        handle arbitrary scripts, but the CheckHash160() calls will 
#        (correctly) throw errors if you don't.  We can upgrade this in
#        the future.
class PyUnspentTxOut(object):
   def __init__(self, scrAddr=None, txHash=None, txoIdx=None, val=None, 
                                             numConf=None, fullScript=None):

      self.initialize(scrAddr, txHash, txoIdx, val, numConf, fullScript)


   #############################################################################
   def createFromCppUtxo(self, cppUtxo):
      scrAddr= cppUtxo.getRecipientScrAddr()
      val    = cppUtxo.getValue()
      conf   = cppUtxo.getNumConfirm()
      txHash = cppUtxo.getTxHash()
      txoIdx = cppUtxo.getTxOutIndex()
      script = cppUtxo.getScript()

      self.initialize(scrAddr, txHash, txoIdx, val, conf, script)
      return self

   #############################################################################
   def initialize(self, scrAddr=None, txHash=None, txoIdx=None, val=None, 
                                              numConf=None, fullScript=None):
      self.scrAddr    = scrAddr
      self.txHash     = txHash
      self.txOutIndex = txoIdx
      self.val        = val
      self.conf       = numConf

      if self.scrAddr and fullScript is None:
         self.binScript = scrAddr_to_script(self.scrAddr)
      else:
         self.binScript = fullScript

   def getTxHash(self):
      return self.txHash

   def getTxOutIndex(self):
      return self.txOutIndex

   def getValue(self):
      return self.val

   def getNumConfirm(self):
      return self.conf

   def getScript(self):
      return self.binScript

   def getRecipientScrAddr(self):
      return self.scrAddr

   def getRecipientHash160(self):
      return CheckHash160(self.scrAddr)

   def prettyStr(self, indent=''):
      pstr = [indent]
      pstr.append(binary_to_hex(self.scrAddr[:8]))
      pstr.append(coin2str(self.val))
      pstr.append(str(self.conf).rjust(8,' '))
      return '  '.join(pstr)

   def pprint(self, indent=''):
      print self.prettyStr(indent)


################################################################################
def sumTxOutList(txoutList):
   return sum([u.getValue() for u in txoutList])

################################################################################
# This is really just for viewing a TxOut list -- usually for debugging
def pprintUnspentTxOutList(utxoList, headerLine='Coin Selection: '):
   totalSum = sum([u.getValue() for u in utxoList])
   print headerLine, '(Total = %s BTC)' % coin2str(totalSum)
   print '   ','Owner Address'.ljust(34),
   print '   ','TxOutValue'.rjust(18),
   print '   ','NumConf'.rjust(8),
   print '   ','PriorityFactor'.rjust(16)
   for utxo in utxoList:
      a160 = CheckHash160(utxo.getRecipientScrAddr())
      print '   ',hash160_to_addrStr(a160).ljust(34),
      print '   ',(coin2str(utxo.getValue()) + ' BTC').rjust(18),
      print '   ',str(utxo.getNumConfirm()).rjust(8),
      print '   ', ('%0.2f' % (utxo.getValue()*utxo.getNumConfirm()/(ONE_BTC*144.))).rjust(16)


################################################################################
# Sorting currently implemented in C++, but we implement a different kind, here
def PySortCoins(unspentTxOutInfo, sortMethod=1):
   """
   Here we define a few different ways to sort a list of unspent TxOut objects.
   Most of them are simple, some are more complex.  In particular, the last
   method (4) tries to be intelligent, by grouping together inputs from the
   same address.

   The goal is not to do the heavy lifting for SelectCoins... we simply need
   a few different ways to sort coins so that the SelectCoins algorithms has
   a variety of different inputs to play with.  Each sorting method is useful
   for some types of unspent-TxOut lists, so as long as we have one good
   sort, the PyEvalCoinSelect method will pick it out.

   As a precaution we send all the zero-confirmation UTXO's to the back
   of the list, so that they will only be used if absolutely necessary.
   """
   zeroConfirm = []

   if sortMethod==0:
      priorityFn = lambda a: a.getValue() * a.getNumConfirm()
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==1:
      priorityFn = lambda a: (a.getValue() * a.getNumConfirm())**(1/3.)
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==2:
      priorityFn = lambda a: (math.log(a.getValue()*a.getNumConfirm()+1)+4)**4
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==3:
      priorityFn = lambda a: a.getValue() if a.getNumConfirm()>0 else 0
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==4:
      addrMap = {}
      zeroConfirm = []
      for utxo in unspentTxOutInfo:
         if utxo.getNumConfirm() == 0:
            zeroConfirm.append(utxo)
         else:
            scrType = getTxOutScriptType(utxo.getScript())
            if scrType in CPP_TXOUT_HAS_ADDRSTR:
               addr = script_to_addrStr(utxo.getScript())
            else:
               addr = script_to_scrAddr(utxo.getScript())

            if not addrMap.has_key(addr):
               addrMap[addr] = [utxo]
            else:
               addrMap[addr].append(utxo)

      priorityUTXO = (lambda a: (a.getNumConfirm()*a.getValue()**0.333))
      for addr,txoutList in addrMap.iteritems():
         txoutList.sort(key=priorityUTXO, reverse=True)

      priorityGrp = lambda a: max([priorityUTXO(utxo) for utxo in a])
      finalSortedList = []
      for utxo in sorted(addrMap.values(), key=priorityGrp, reverse=True):
         finalSortedList.extend(utxo)

      finalSortedList.extend(zeroConfirm)
      return finalSortedList
   if sortMethod in (5, 6, 7):
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      # Rotate the top 1,2 or 3 elements to the bottom of the list
      for i in range(sortMethod-4):
         utxoSorted.append(utxoSorted[0])
         del utxoSorted[0]
      return utxoSorted

   # TODO:  Add a semi-random sort method:  it will favor putting high-priority
   #        outputs at the front of the list, but will not be deterministic
   #        This should give us some high-fitness variation compared to sorting
   #        uniformly
   if sortMethod==8:
      utxosNoZC = filter(lambda a: a.getNumConfirm()!=0, unspentTxOutInfo)
      random.shuffle(utxosNoZC)
      utxosNoZC.extend(filter(lambda a: a.getNumConfirm()==0, unspentTxOutInfo))
      return utxosNoZC
   if sortMethod==9:
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      sz = len(filter(lambda a: a.getNumConfirm()!=0, utxoSorted))
      # swap 1/3 of the values at random
      topsz = int(min(max(round(sz/3), 5), sz))
      for i in range(topsz):
         pick1 = int(random.uniform(0,topsz))
         pick2 = int(random.uniform(0,sz-topsz))
         utxoSorted[pick1], utxoSorted[pick2] = utxoSorted[pick2], utxoSorted[pick1]
      return utxoSorted




################################################################################
# Now we try half a dozen different selection algorithms
################################################################################



################################################################################
def PySelectCoins_SingleInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   bestMatchVal  = 2**64
   bestMatchUtxo = None
   for utxo in unspentTxOutInfo:
      if target <= utxo.getValue() < bestMatchVal:
         bestMatchVal = utxo.getValue()
         bestMatchUtxo = utxo

   closeness = bestMatchVal - target
   if 0 < closeness <= CENT:
      # If we're going to have a change output, make sure it's above CENT
      # to avoid a mandatory fee
      try2Val  = 2**64
      try2Utxo = None
      for utxo in unspentTxOutInfo:
         if target+CENT < utxo.getValue() < try2Val:
            try2Val = utxo.getValue()
            try2Val = utxo
      if not try2Utxo==None:
         bestMatchUtxo = try2Utxo


   if bestMatchUtxo==None:
      return []
   else:
      return [bestMatchUtxo]

################################################################################
def PySelectCoins_MultiInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   outList = []
   sumVal = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      if sumVal>=target:
         break

   return outList



################################################################################
def PySelectCoins_SingleInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   We will look for a single input that is within 30% of the target
   In case the tx value is tiny rel to the fee: the minTarget calc
   may fail to exceed the actual tx size needed, so we add an extra

   We restrain the search to 25%.  If there is no one output in this
   range, then we will return nothing, and the SingleInput_SingleValue
   method might return a usable result
   """
   idealTarget    = 2*targetOutVal + minFee

   # check to make sure we're accumulating enough
   minTarget   = long(0.75 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   maxTarget   = long(1.25 * idealTarget)

   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   bestMatch = 2**64-1
   bestUTXO   = None
   for txout in unspentTxOutInfo:
      if minTarget <= txout.getValue() <= maxTarget:
         if abs(txout.getValue()-idealTarget) < bestMatch:
            bestMatch = abs(txout.getValue()-idealTarget)
            bestUTXO = txout

   if bestUTXO==None:
      return []
   else:
      return [bestUTXO]

################################################################################
def PySelectCoins_MultiInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):

   idealTarget = 2.0 * targetOutVal
   minTarget   = long(0.80 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   outList   = []
   lastDiff  = 2**64-1
   sumVal    = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      currDiff = abs(sumVal - idealTarget)
      # should switch from decreasing to increasing when best match
      if sumVal>=minTarget and currDiff>lastDiff:
         del outList[-1]
         break
      lastDiff = currDiff

   return outList




################################################################################
def getSelectCoinsScores(utxoSelectList, targetOutVal, minFee):
   """
   Define a metric for scoring the output of SelectCoints.  The output of
   this method is a tuple of scores which identify a few different factors
   of a txOut selection that users might care about in a selectCoins algorithm.

   This method only returns an absolute score, usually between 0 and 1 for
   each factor.  It is up to the person calling this method to decide how
   much "weight" they want to give each one.  You could even use the scores
   as multiplicative factors if you wanted, though they were designed with
   the following equation in mind:   finalScore = sum(WEIGHT[i] * SCORE[i])

   TODO:  I need to recalibrate some of these factors, and modify them to
          represent more directly what the user would be concerned about --
          such as PayFeeFactor, AnonymityFactor, etc.  The information is
          indirectly available with the current set of factors here
   """

   # Need to calculate how much the change will be returned to sender on this tx
   totalIn = sum([utxo.getValue() for utxo in utxoSelectList])
   totalChange = totalIn - (targetOutVal+minFee)

   # Abort if this is an empty list (negative score) or not enough coins
   if len(utxoSelectList)==0 or totalIn<targetOutVal+minFee:
      return -1


   ##################
   # -- Does this selection include any zero-confirmation tx?
   # -- How many addresses are linked together by this tx?
   addrSet = set()
   noZeroConf = 1
   for utxo in utxoSelectList:
      
      addrSet.add(script_to_scrAddr(utxo.getScript()))
      if utxo.getNumConfirm() == 0:
         noZeroConf = 0
   numAddr = len(addrSet)
   numAddrFactor = 4.0/(numAddr+1)**2  # values in the range (0, 1]



   ##################
   # Evaluate output anonanymity
   # One good measure of anonymity is look at trailiing zeros of the value.
   # If one output is like 50.0, and nother if 27.383291, then it's fairly
   # obvious which one is the change.  Can measure that by seeing that 50.0
   # in satoshis has 9 trailing zeros, where as 27.383291 only has 2
   #
   # If the diff is negative, the wrong answer starts to look like the
   # correct one (about which output is recipient and which is change)
   # We should give "extra credit" for those cases
   def countTrailingZeros(btcVal):
      for i in range(1,20):
         if btcVal % 10**i != 0:
            return i-1
      return 0  # not sure how we'd get here, but let's be safe
   tgtTrailingZeros =  countTrailingZeros(targetOutVal)
   chgTrailingZeros =  countTrailingZeros(totalChange)
   zeroDiff = tgtTrailingZeros - chgTrailingZeros
   outAnonFactor = 0
   if totalChange==0:
      outAnonFactor = 1
   else:
      if zeroDiff==2:
         outAnonFactor = 0.2
      elif zeroDiff==1:
         outAnonFactor = 0.7
      elif zeroDiff<1:
         outAnonFactor = abs(zeroDiff) + 1


   ##################
   # Equal inputs are anonymous-- but no point in doing this if the
   # trailing zeros count is way different -- i.e. does it matter if
   # outputs a and b are close, if a=51.000, and b=47.283?  It's
   # still pretty obvious which one is the change. (so: only execute
   # the following block if outAnonFactor > 0)
   #
   # On the other hand, if we have 1.832 and 10.00, and the 10.000 is the
   # change, we don't really care that they're not close, it's still
   # damned good/deceptive output anonymity  (so: only execute
   # the following block if outAnonFactor <= 1)
   if 0 < outAnonFactor <= 1 and not totalChange==0:
      outValDiff = abs(totalChange - targetOutVal)
      diffPct = (outValDiff / max(totalChange, targetOutVal))
      if diffPct < 0.20:
         outAnonFactor *= 1
      elif diffPct < 0.50:
         outAnonFactor *= 0.7
      elif diffPct < 1.0:
         outAnonFactor *= 0.3
      else:
         outAnonFactor = 0


   ##################
   # Tx size:  we don't have signatures yet, but we assume that each txin is
   #           about 180 Bytes, TxOuts are 35, and 10 other bytes in the Tx
   numBytes  =  10
   numBytes += 180 * len(utxoSelectList)
   numBytes +=  35 * (1 if totalChange==0 else 2)
   txSizeFactor = 0
   numKb = int(numBytes / 1000)
   # Will compute size factor after we see this tx priority and AllowFree
   # results.  If the tx qualifies for free, we don't need to penalize
   # a 3 kB transaction vs one that is 0.5 kB


   ##################
   # Priority:  If our priority is above the 1-btc-after-1-day threshold
   #            then we might be allowed a free tx.  But, if its priority
   #            isn't much above this thresh, it might take a couple blocks
   #            to be included
   dPriority = 0
   anyZeroConfirm = False
   for utxo in utxoSelectList:
      if utxo.getNumConfirm() == 0:
         anyZeroConfirm = True
      else:
         dPriority += utxo.getValue() * utxo.getNumConfirm()

   dPriority = dPriority / numBytes
   priorityThresh = ONE_BTC * 144 / 250
   if dPriority < priorityThresh:
      priorityFactor = 0
   elif dPriority < 10.0*priorityThresh:
      priorityFactor = 0.7
   elif dPriority < 100.0*priorityThresh:
      priorityFactor = 0.9
   else:
      priorityFactor = 1.0


   ##################
   # AllowFree:  If three conditions are met, then the tx can be sent safely
   #             without a tx fee.  Granted, it may not be included in the
   #             current block if the free space is full, but definitely in
   #             the next one
   isFreeAllowed = 0
   haveDustOutputs = (0<totalChange<CENT or targetOutVal<CENT)
   if ((not haveDustOutputs) and \
       dPriority >= priorityThresh and \
       numBytes <= 10000):
      isFreeAllowed = 1


   ##################
   # Finish size-factor calculation -- if free is allowed, kB is irrelevant
   txSizeFactor = 0
   if isFreeAllowed or numKb<1:
      txSizeFactor = 1
   else:
      if numKb < 2:
         txSizeFactor=0.2
      elif numKb<3:
         txSizeFactor=0.1
      elif numKb<4:
         txSizeFactor=0
      else:
         txSizeFactor=-1  #if this is huge, actually subtract score

   return (isFreeAllowed, noZeroConf, priorityFactor, numAddrFactor, txSizeFactor, outAnonFactor)


################################################################################
# We define default preferences for weightings.  Weightings are used to
# determine the "priorities" for ranking various SelectCoins results
# By setting the weights to different orders of magnitude, you are essentially
# defining a sort-order:  order by FactorA, then sub-order by FactorB...
################################################################################
# TODO:  ADJUST WEIGHTING!
IDX_ALLOWFREE   = 0
IDX_NOZEROCONF  = 1
IDX_PRIORITY    = 2
IDX_NUMADDR     = 3
IDX_TXSIZE      = 4
IDX_OUTANONYM   = 5
WEIGHTS = [None]*6
WEIGHTS[IDX_ALLOWFREE]  =  100000
WEIGHTS[IDX_NOZEROCONF] = 1000000  # let's avoid zero-conf if possible
WEIGHTS[IDX_PRIORITY]   =      50
WEIGHTS[IDX_NUMADDR]    =  100000
WEIGHTS[IDX_TXSIZE]     =     100
WEIGHTS[IDX_OUTANONYM]  =      30


################################################################################
def PyEvalCoinSelect(utxoSelectList, targetOutVal, minFee, weights=WEIGHTS):
   """
   Use a specified set of weightings and sub-scores for a unspentTxOut list,
   to assign an absolute "fitness" of this particular selection.  The goal of
   getSelectCoinsScores() is to produce weighting-agnostic subscores -- then
   this method applies the weightings to these scores to get a final answer.

   If list A has a higher score than list B, then it's a better selection for
   that transaction.  If you the two scores don't look right to you, then you
   probably just need to adjust the weightings to your liking.

   These weightings may become user-configurable in the future -- likely as an
   option of coin-selection profiles -- such as "max anonymity", "min fee",
   "balanced", etc).
   """
   scores = getSelectCoinsScores(utxoSelectList, targetOutVal, minFee)
   if scores==-1:
      return -1

   # Combine all the scores
   theScore  = 0
   theScore += weights[IDX_NOZEROCONF] * scores[IDX_NOZEROCONF]
   theScore += weights[IDX_PRIORITY]   * scores[IDX_PRIORITY]
   theScore += weights[IDX_NUMADDR]    * scores[IDX_NUMADDR]
   theScore += weights[IDX_TXSIZE]     * scores[IDX_TXSIZE]
   theScore += weights[IDX_OUTANONYM]  * scores[IDX_OUTANONYM]

   # If we're already paying a fee, why bother including this weight?
   if minFee < 0.0005:
      theScore += weights[IDX_ALLOWFREE]  * scores[IDX_ALLOWFREE]

   return theScore


################################################################################
# https://bitcointalk.org/index.php?topic=92496.msg1126310#msg1126310 contains a
# description (possibly out-of-date?) of how this function works.
@TimeThisFunction
def PySelectCoins(unspentTxOutInfo, targetOutVal, minFee=0, numRand=10, margin=CENT):
   """
   Intense algorithm for coin selection:  computes about 30 different ways to
   select coins based on the desired target output and the min tx fee.  Then
   ranks the various solutions and picks the best one
   """

   if sum([u.getValue() for u in unspentTxOutInfo]) < targetOutVal:
      return []

   targExact  = targetOutVal
   targMargin = targetOutVal+margin

   selectLists = []

   # Start with the intelligent solutions with different sortings
   for sortMethod in range(8):
      diffSortList = PySortCoins(unspentTxOutInfo, sortMethod)
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targMargin, minFee ))

   # Throw in a couple random solutions, maybe we get lucky
   # But first, make a copy before in-place shuffling
   # NOTE:  using list[:] like below, really causes a swig::vector<type> to freak out!
   #utxos = unspentTxOutInfo[:]
   #utxos = list(unspentTxOutInfo)
   for method in range(8,10):
      for i in range(numRand):
         utxos = PySortCoins(unspentTxOutInfo, method)
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targMargin, minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targMargin, minFee))

   # Now we define PyEvalCoinSelect as our sorting metric, and find the best solution
   scoreFunc = lambda ulist: PyEvalCoinSelect(ulist, targetOutVal, minFee)
   finalSelection = max(selectLists, key=scoreFunc)
   SCORES = getSelectCoinsScores(finalSelection, targetOutVal, minFee)
   if len(finalSelection)==0:
      return []

   # If we selected a list that has only one or two inputs, and we have
   # other, tiny, unspent outputs from the same addresses, we should
   # throw one or two of them in to help clear them out.  However, we
   # only do so if a plethora of conditions exist:
   #
   # First, we only consider doing this if the tx has <5 inputs already.
   # Also, we skip this process if the current tx doesn't have excessive
   # priority already -- we don't want to risk de-prioritizing a tx for
   # this purpose.
   #
   # Next we sort by LOWEST value, because we really benefit from this most
   # by clearing out tiny outputs.  Along those lines, we don't even do
   # unless it has low priority -- don't want to take a high-priority utxo
   # and convert it to one that will be low-priority to start.
   #
   # Finally, we shouldn't do this if a high score was assigned to output
   # anonymity: this extra output may cause a tx with good output anonymity
   # to no longer possess this property
   IDEAL_NUM_INPUTS = 5
   if len(finalSelection) < IDEAL_NUM_INPUTS and \
          SCORES[IDX_OUTANONYM] == 0:

      utxoToScrAddr = lambda a: a.getRecipientScrAddr()
      getPriority   = lambda a: a.getValue() * a.getNumConfirm()
      getUtxoID     = lambda a: a.getTxHash() + int_to_binary(a.getTxOutIndex())

      alreadyUsedAddr = set( [utxoToScrAddr(utxo) for utxo in finalSelection] )
      utxoSmallToLarge = sorted(unspentTxOutInfo, key=getPriority)
      utxoSmToLgIDs = [getUtxoID(utxo) for utxo in utxoSmallToLarge]
      finalSelectIDs = [getUtxoID(utxo) for utxo in finalSelection]
      
      for other in utxoSmallToLarge:
         
         # Skip it if it is already selected
         if getUtxoID(other) in finalSelectIDs:
            continue

         # We only consider UTXOs that won't link any new addresses together
         if not utxoToScrAddr(other) in alreadyUsedAddr:
            continue
         
         # Avoid zero-conf inputs altogether
         if other.getNumConfirm() == 0:
            continue

         # Don't consider any inputs that are high priority already
         if getPriority(other) > ONE_BTC*144:
            continue

         finalSelection.append(other) 
         if len(finalSelection)>=IDEAL_NUM_INPUTS:
            break
   return finalSelection

################################################################################
def calcMinSuggestedFeesHackMS(selectCoinsResult, targetOutVal, preSelectedFee, 
                                                         numRecipients):
   """
   This is a hack, because the calcMinSuggestedFees below assumes standard
   P2PKH inputs and outputs, not allowing us a way to modify it if we ne know
   that the inputs will be much larger, or the outputs.

   we just copy the original method with an update to the computation
   """
   paid = targetOutVal + preSelectedFee
   change = sum([u.getValue() for u in selectCoinsResult]) - paid

   numBytes = 0
   msInfo = [getMultisigScriptInfo(utxo.getScript()) for utxo in selectCoinsResult]
   for m,n,As,Ps in msInfo:
      numBytes += m*70 + 40

   numBytes += 200*numRecipients  # assume large lockbox outputs
   numKb = int(numBytes / 1000)

   if numKb>10:
      return [(1+numKb)*MIN_RELAY_TX_FEE, (1+numKb)*MIN_TX_FEE]

   # Compute raw priority of tx
   prioritySum = 0
   for utxo in selectCoinsResult:
      prioritySum += utxo.getValue() * utxo.getNumConfirm()
   prioritySum = prioritySum / numBytes

   # Any tiny/dust outputs?
   haveDustOutputs = (0<change<CENT or targetOutVal<CENT)

   if((not haveDustOutputs) and \
      prioritySum >= ONE_BTC * 144 / 250. and \
      numBytes < 10000):
      return [0,0]

   # This cannot be a free transaction.
   minFeeMultiplier = (1 + numKb)

   # At the moment this condition never triggers
   if minFeeMultiplier<1.0 and haveDustOutputs:
      minFeeMultiplier = 1.0


   return [minFeeMultiplier * MIN_RELAY_TX_FEE, \
           minFeeMultiplier * MIN_TX_FEE]
   
      

################################################################################
def calcMinSuggestedFees(selectCoinsResult, targetOutVal, preSelectedFee,
                         numRecipients):
   """
   Returns two fee options:  one for relay, one for include-in-block.
   In general, relay fees are required to get your block propagated
   (since most nodes are Satoshi clients), but there's no guarantee
   it will be included in a block -- though I'm sure there's plenty
   of miners out there will include your tx for sub-standard fee.
   However, it's virtually guaranteed that a miner will accept a fee
   equal to the second return value from this method.

   We have to supply the fee that was used in the selection algorithm,
   so that we can figure out how much change there will be.  Without
   this information, we might accidentally declare a tx to be freeAllow
   when it actually is not.
   """

   # TODO: this should be updated to accommodate the non-constant 
   #       TxOut/TxIn size given that it now accepts P2SH and Multisig

   if len(selectCoinsResult)==0:
      return [-1,-1]

   paid = targetOutVal + preSelectedFee
   change = sum([u.getValue() for u in selectCoinsResult]) - paid

   # Calc approx tx size
   numBytes  =  10
   numBytes += 180 * len(selectCoinsResult)
   numBytes +=  35 * (numRecipients + (1 if change>0 else 0))
   numKb = int(numBytes / 1000)

   if numKb>10:
      return [(1+numKb)*MIN_RELAY_TX_FEE, (1+numKb)*MIN_TX_FEE]

   # Compute raw priority of tx
   prioritySum = 0
   for utxo in selectCoinsResult:
      prioritySum += utxo.getValue() * utxo.getNumConfirm()
   prioritySum = prioritySum / numBytes

   # Any tiny/dust outputs?
   haveDustOutputs = (0<change<CENT or targetOutVal<CENT)

   if((not haveDustOutputs) and \
      prioritySum >= ONE_BTC * 144 / 250. and \
      numBytes < 10000):
      return [0,0]

   # This cannot be a free transaction.
   minFeeMultiplier = (1 + numKb)

   # At the moment this condition never triggers
   if minFeeMultiplier<1.0 and haveDustOutputs:
      minFeeMultiplier = 1.0


   return [minFeeMultiplier * MIN_RELAY_TX_FEE, \
           minFeeMultiplier * MIN_TX_FEE]




################################################################################
def approxTxInSizeForTxOut(utxoScript, lboxList=None):
   """
   Since this is always used for fee estimation, we overestimate the size to
   be conservative.  However, if this is P2SH, we won't have a clue what the
   hashed script is, so unless we find it in our lockbox map, we assume the 
   max-max which is 1,650 bytes.

   Otherwise the TxIn is always:
      PrevTxHash(32), PrevTxOutIndex(4), Script(_), Sequence(4)
   """

   scrType = getTxOutScriptType(utxoScript)
   if scrType == CPP_TXOUT_STDHASH160:
      return 180
   elif scrType in [CPP_TXOUT_STDPUBKEY33, CPP_TXOUT_STDPUBKEY65]:
      return 110
   elif scrType == CPP_TXOUT_MULTISIG:
      M,N,a160s,pubs = getMultisigScriptInfo(utxoScript)
      return M*70 + 40
   elif scrType == CPP_TXOUT_P2SH and not lboxList is None:
      scrAddr = script_to_scrAddr(utxoScript)
      for lbox in lboxList:
         if scrAddr == lbox.p2shScrAddr:
            M,N,a160s,pubs = getMultisigScriptInfo(lbox.binScript)
            return M*70 + 40

   # If we got here, we didn't identify it at all.  Assume max for TxIn
   return 1650



################################################################################
# I needed a new function that was going to be as accurate as possible for
# arbitrary coin selections (and recipient lists).  However, this doesn't
# work in all places tat the old coin selection algo was used, so I am 
# leaving those calls alone and simply defining this for new methods that
# have access to full UTXOs scripts and scriptValPairs.
def calcMinSuggestedFeesNew(selectCoinsResult, scriptValPairs, preSelectedFee,
                                          changeScript=None):
   """
   Returns two fee options:  one for relay, one for include-in-block.
   In general, relay fees are required to get your block propagated
   (since most nodes are Satoshi clients), but there's no guarantee
   it will be included in a block -- though I'm sure there's plenty
   of miners out there will include your tx for sub-standard fee.
   However, it's virtually guaranteed that a miner will accept a fee
   equal to the second return value from this method.

   We have to supply the fee that was used in the selection algorithm,
   so that we can figure out how much change there will be.  Without
   this information, we might accidentally declare a tx to be freeAllow
   when it actually is not.
   """

   # TODO: this should be updated to accommodate the non-constant 
   #       TxOut/TxIn size given that it now accepts P2SH and Multisig

   targetOutVal = long( sum([rv[1] for rv in scriptValPairs]) )
   if len(selectCoinsResult)==0:
      return [-1,-1]
   paid = targetOutVal + preSelectedFee
   change = sum([u.getValue() for u in selectCoinsResult]) - paid


   # Calc approx tx size
   numBytes  =  10
   numBytes +=  sum([len(sv[0])+9 for sv in scriptValPairs])
   if change>0:
      # If no changeScript is provided, we assume P2PKH or P2SH: approx 35 bytes
      numBytes += len(changeScript) if changeScript else 35

   numKb = int(numBytes / 1000)

   if numKb>10:
      return [(1+numKb)*MIN_RELAY_TX_FEE, (1+numKb)*MIN_TX_FEE]

   # Compute raw priority of tx
   prioritySum = 0
   for utxo in selectCoinsResult:
      prioritySum += utxo.getValue() * utxo.getNumConfirm()
   prioritySum = prioritySum / numBytes

   # Any tiny/dust outputs?
   haveDustOutputs = (0<change<CENT or targetOutVal<CENT)

   if((not haveDustOutputs) and \
      prioritySum >= ONE_BTC * 144 / 250. and \
      numBytes < 10000):
      return [0,0]

   # This cannot be a free transaction.
   minFeeMultiplier = (1 + numKb)

   # At the moment this condition never triggers
   if minFeeMultiplier<1.0 and haveDustOutputs:
      minFeeMultiplier = 1.0


   return [minFeeMultiplier * MIN_RELAY_TX_FEE, \
           minFeeMultiplier * MIN_TX_FEE]

