##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from armoryengine.ArmoryUtils import LOGERROR, isASCII
from qrcodenative import QRCode, QRErrorCorrectLevel

################################################################################
def CreateQRMatrix(dataToEncode, errLevel=QRErrorCorrectLevel.L):
   dataLen = len(dataToEncode)
   baseSz = 4 if errLevel == QRErrorCorrectLevel.L else \
            5 if errLevel == QRErrorCorrectLevel.M else \
            6 if errLevel == QRErrorCorrectLevel.Q else \
            7 # errLevel = QRErrorCorrectLevel.H
   sz = baseSz if dataLen < 70 else  5 +  (dataLen - 70) / 30
   qrmtrx = [[]]
   while sz<20:
      try:
         errCorrectEnum = getattr(QRErrorCorrectLevel, errLevel.upper())
         qr = QRCode(sz, errCorrectEnum)
         qr.addData(dataToEncode)
         qr.make()
         success=True
         break
      except TypeError:
         sz += 1

   if not success:
      LOGERROR('Unsuccessful attempt to create QR code')
      LOGERROR('Data to encode: (Length: %s, isAscii: %s)', \
                     len(dataToEncode), isASCII(dataToEncode))
      return [[0]], 1

   qrmtrx = []
   modCt = qr.getModuleCount()
   for r in range(modCt):
      tempList = [0]*modCt
      for c in range(modCt):
         # The matrix is transposed by default, from what we normally expect
         tempList[c] = 1 if qr.isDark(c,r) else 0
      qrmtrx.append(tempList)

   return [qrmtrx, modCt]