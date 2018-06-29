# -*- coding: UTF-8 -*-

################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import functools
import shutil
import socket
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from armoryengine.ALL import *
from armorycolors import Colors, htmlColor
from armorymodels import *
import qrc_img_resources
from qtdefines import *
from armoryengine.PyBtcAddress import calcWalletIDFromRoot
from armoryengine.MultiSigUtils import calcLockboxID, createLockboxEntryStr,\
   LBPREFIX, isBareLockbox, isP2SHLockbox
from ui.MultiSigModels import LockboxDisplayModel, LockboxDisplayProxy,\
   LOCKBOXCOLS
from armoryengine.PyBtcWalletRecovery import RECOVERMODE
from armoryengine.ArmoryUtils import BTC_HOME_DIR

from ui.TreeViewGUI import AddressTreeModel
from ui.QrCodeMatrix import CreateQRMatrix
from ui.SignerSelectDialog import SignerLabelFrame

NO_CHANGE = 'NoChange'
MIN_PASSWD_WIDTH = lambda obj: tightSizeStr(obj, '*' * 16)[0]
STRETCH = 'Stretch'
CLICKED = 'clicked()'
BACKUP_TYPE_135A = '1.35a'
BACKUP_TYPE_135C = '1.35c'
BACKUP_TYPE_0_TEXT = 'Version 0  (from script, 9 lines)'
BACKUP_TYPE_135a_TEXT = 'Version 1.35a (5 lines Unencrypted)'
BACKUP_TYPE_135a_SP_TEXT = u'Version 1.35a (5 lines + SecurePrint\u200b\u2122)'
BACKUP_TYPE_135c_TEXT = 'Version 1.35c (3 lines Unencrypted)'
BACKUP_TYPE_135c_SP_TEXT = u'Version 1.35c (3 lines + SecurePrint\u200b\u2122)'
MAX_QR_SIZE = 198
MAX_SATOSHIS = 2100000000000000

################################################################################
class DlgUnlockWallet(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None, unlockMsg='Unlock Wallet', \
                           returnResult=False, returnPassphrase=False):
      super(DlgUnlockWallet, self).__init__(parent, main)

      self.wlt = wlt
      self.returnResult = returnResult
      self.returnPassphrase = returnPassphrase

      ##### Upper layout
      lblDescr = QLabel(self.tr("Enter your passphrase to unlock this wallet"))
      lblPasswd = QLabel(self.tr("Passphrase:"))
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton(self.tr("Unlock"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.acceptPassphrase)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layoutUpper = QGridLayout()
      layoutUpper.addWidget(lblDescr, 1, 0, 1, 2)
      layoutUpper.addWidget(lblPasswd, 2, 0, 1, 1)
      layoutUpper.addWidget(self.edtPasswd, 2, 1, 1, 1)
      self.frmUpper = QFrame()
      self.frmUpper.setLayout(layoutUpper)

      ##### Lower layout
      # Add scrambled keyboard (EN-US only)

      ttipScramble = self.main.createToolTipWidget(\
         self.tr('Using a visual keyboard to enter your passphrase '
         'protects you against simple keyloggers.   Scrambling '
         'makes it difficult to use, but prevents even loggers '
         'that record mouse clicks.'))

      self.createKeyButtons()
      self.rdoScrambleNone = QRadioButton(self.tr('Regular Keyboard'))
      self.rdoScrambleLite = QRadioButton(self.tr('Scrambled (Simple)'))
      self.rdoScrambleFull = QRadioButton(self.tr('Scrambled (Dynamic)'))
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.rdoScrambleNone)
      btngrp.addButton(self.rdoScrambleLite)
      btngrp.addButton(self.rdoScrambleFull)
      btngrp.setExclusive(True)
      defaultScramble = self.main.getSettingOrSetDefault('ScrambleDefault', 0)
      if defaultScramble == 0:
         self.rdoScrambleNone.setChecked(True)
      elif defaultScramble == 1:
         self.rdoScrambleLite.setChecked(True)
      elif defaultScramble == 2:
         self.rdoScrambleFull.setChecked(True)
      self.connect(self.rdoScrambleNone, SIGNAL(CLICKED), self.changeScramble)
      self.connect(self.rdoScrambleLite, SIGNAL(CLICKED), self.changeScramble)
      self.connect(self.rdoScrambleFull, SIGNAL(CLICKED), self.changeScramble)
      btnRowFrm = makeHorizFrame([self.rdoScrambleNone, \
                                  self.rdoScrambleLite, \
                                  self.rdoScrambleFull, \
                                  STRETCH])

      self.layoutKeyboard = QGridLayout()
      self.frmKeyboard = QFrame()
      self.frmKeyboard.setLayout(self.layoutKeyboard)

      showOSD = self.main.getSettingOrSetDefault('KeybdOSD', False)
      self.layoutLower = QGridLayout()
      self.layoutLower.addWidget(btnRowFrm , 0, 0)
      self.layoutLower.addWidget(self.frmKeyboard , 1, 0)
      self.frmLower = QFrame()
      self.frmLower.setLayout(self.layoutLower)
      self.frmLower.setVisible(showOSD)


      ##### Expand button
      self.btnShowOSD = QPushButton(self.tr('Show Keyboard >>>'))
      self.btnShowOSD.setCheckable(True)
      self.btnShowOSD.setChecked(showOSD)
      if showOSD:
         self.toggleOSD()
      self.connect(self.btnShowOSD, SIGNAL('toggled(bool)'), self.toggleOSD)
      frmAccept = makeHorizFrame([self.btnShowOSD, ttipScramble, STRETCH, buttonBox])


      ##### Complete Layout
      layout = QVBoxLayout()
      layout.addWidget(self.frmUpper)
      layout.addWidget(frmAccept)
      layout.addWidget(self.frmLower)
      self.setLayout(layout)
      self.setWindowTitle(unlockMsg + ' - ' + wlt.uniqueIDB58)

      # Add scrambled keyboard
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.changeScramble()
      self.redrawKeys()


   #############################################################################
   def toggleOSD(self, *args):
      isChk = self.btnShowOSD.isChecked()
      self.main.settings.set('KeybdOSD', isChk)
      self.frmLower.setVisible(isChk)
      if isChk:
         self.btnShowOSD.setText(self.tr('Hide Keyboard <<<'))
      else:
         self.btnShowOSD.setText(self.tr('Show Keyboard >>>'))


   #############################################################################
   def createKeyboardKeyButton(self, keyLow, keyUp, defRow, special=None):
      theBtn = LetterButton(keyLow, keyUp, defRow, special, self.edtPasswd, self)
      self.connect(theBtn, SIGNAL(CLICKED), theBtn.insertLetter)
      theBtn.setMaximumWidth(40)
      return theBtn


   #############################################################################
   def redrawKeys(self):
      for btn in self.btnList:
         btn.setText(btn.upper if self.btnShift.isChecked() else btn.lower)
      self.btnShift.setText(self.tr('SHIFT'))
      self.btnSpace.setText(self.tr('SPACE'))
      self.btnDelete.setText(self.tr('DEL'))

   #############################################################################
   def deleteKeyboard(self):
      for btn in self.btnList:
         btn.setParent(None)
         del btn
      self.btnList = []
      self.btnShift.setParent(None)
      self.btnSpace.setParent(None)
      self.btnDelete.setParent(None)
      del self.btnShift
      del self.btnSpace
      del self.btnDelete
      del self.frmKeyboard
      del self.layoutKeyboard

   #############################################################################
   def createKeyButtons(self):
      # TODO:  Add some locale-agnostic method here, that could replace
      #        the letter arrays with something more appropriate for non en-us
      self.letLower = r"`1234567890-=qwertyuiop[]\asdfghjkl;'zxcvbnm,./"
      self.letUpper = r'~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'
      self.letRows = r'11111111111112222222222222333333333334444444444'
      self.letPairs = zip(self.letLower, self.letUpper, self.letRows)

      self.btnList = []
      for l, u, r in zip(self.letLower, self.letUpper, self.letRows):
         if l == '7':
            # Because QPushButtons interpret ampersands as special characters
            u = 2 * u

         if l.isdigit():
            self.btnList.append(self.createKeyboardKeyButton('#' + l, u, int(r)))
         else:
            self.btnList.append(self.createKeyboardKeyButton(l, u, int(r)))

      # Add shift and space keys
      self.btnShift = self.createKeyboardKeyButton('', '', 5, 'shift')
      self.btnSpace = self.createKeyboardKeyButton(' ', ' ', 5, 'space')
      self.btnDelete = self.createKeyboardKeyButton(' ', ' ', 5, 'delete')
      self.btnShift.setCheckable(True)
      self.btnShift.setChecked(False)

   #############################################################################
   def reshuffleKeys(self):
      if self.rdoScrambleFull.isChecked():
         self.changeScramble()

   #############################################################################
   def changeScramble(self):
      self.deleteKeyboard()
      self.frmKeyboard = QFrame()
      self.layoutKeyboard = QGridLayout()
      self.createKeyButtons()

      if self.rdoScrambleNone.isChecked():
         opt = 0
         prevRow = 1
         col = 0
         for btn in self.btnList:
            row = btn.defRow
            if not row == prevRow:
               col = 0
            if row > 3 and col == 0:
               col += 1
            prevRow = row
            self.layoutKeyboard.addWidget(btn, row, col)
            col += 1
         self.layoutKeyboard.addWidget(self.btnShift, self.btnShift.defRow, 0, 1, 3)
         self.layoutKeyboard.addWidget(self.btnSpace, self.btnSpace.defRow, 4, 1, 5)
         self.layoutKeyboard.addWidget(self.btnDelete, self.btnDelete.defRow, 11, 1, 2)
         self.btnShift.setMaximumWidth(1000)
         self.btnSpace.setMaximumWidth(1000)
         self.btnDelete.setMaximumWidth(1000)
      elif self.rdoScrambleLite.isChecked():
         opt = 1
         nchar = len(self.btnList)
         rnd = SecureBinaryData().GenerateRandom(2 * nchar).toBinStr()
         newBtnList = [[self.btnList[i], rnd[2 * i:2 * (i + 1)]] for i in range(nchar)]
         newBtnList.sort(key=lambda x: x[1])
         prevRow = 0
         col = 0
         for i, btn in enumerate(newBtnList):
            row = i / 12
            if not row == prevRow:
               col = 0
            prevRow = row
            self.layoutKeyboard.addWidget(btn[0], row, col)
            col += 1
         self.layoutKeyboard.addWidget(self.btnShift, self.btnShift.defRow, 0, 1, 3)
         self.layoutKeyboard.addWidget(self.btnSpace, self.btnSpace.defRow, 4, 1, 5)
         self.layoutKeyboard.addWidget(self.btnDelete, self.btnDelete.defRow, 10, 1, 2)
         self.btnShift.setMaximumWidth(1000)
         self.btnSpace.setMaximumWidth(1000)
         self.btnDelete.setMaximumWidth(1000)
      elif self.rdoScrambleFull.isChecked():
         opt = 2
         extBtnList = self.btnList[:]
         extBtnList.extend([self.btnShift, self.btnSpace])
         nchar = len(extBtnList)
         rnd = SecureBinaryData().GenerateRandom(2 * nchar).toBinStr()
         newBtnList = [[extBtnList[i], rnd[2 * i:2 * (i + 1)]] for i in range(nchar)]
         newBtnList.sort(key=lambda x: x[1])
         prevRow = 0
         col = 0
         for i, btn in enumerate(newBtnList):
            row = i / 12
            if not row == prevRow:
               col = 0
            prevRow = row
            self.layoutKeyboard.addWidget(btn[0], row, col)
            col += 1
         self.layoutKeyboard.addWidget(self.btnDelete, self.btnDelete.defRow - 1, 11, 1, 2)
         self.btnShift.setMaximumWidth(40)
         self.btnSpace.setMaximumWidth(40)
         self.btnDelete.setMaximumWidth(40)

      self.frmKeyboard.setLayout(self.layoutKeyboard)
      self.layoutLower.addWidget(self.frmKeyboard, 1, 0)
      self.main.settings.set('ScrambleDefault', opt)
      self.redrawKeys()


   #############################################################################
   def acceptPassphrase(self):

      self.securePassphrase = SecureBinaryData(str(self.edtPasswd.text()))
      self.edtPasswd.setText('')

      if self.returnResult:
         self.accept()
         return

      try:
         if self.returnPassphrase == False:
            unlockProgress = DlgProgress(self, self.main, HBar=1,
                                         Title=self.tr("Unlocking Wallet"))
            unlockProgress.exec_(self.wlt.unlock, securePassphrase=self.securePassphrase)
            self.securePassphrase.destroy()
         else:
            if self.wlt.verifyPassphrase(self.securePassphrase) == False:
               raise PassphraseError

         self.accept()
      except PassphraseError:
         QMessageBox.critical(self, self.tr('Invalid Passphrase'), \
           self.tr('That passphrase is not correct!'), QMessageBox.Ok)
         self.securePassphrase.destroy()
         self.edtPasswd.setText('')
         return


#############################################################################
class LetterButton(QPushButton):
   def __init__(self, Low, Up, Row, Spec, edtTarget, parent):
      super(LetterButton, self).__init__('')
      self.lower = Low
      self.upper = Up
      self.defRow = Row
      self.special = Spec
      self.target = edtTarget
      self.parent = parent

      if self.special:
         super(LetterButton, self).setFont(GETFONT('Var', 8))
      else:
         super(LetterButton, self).setFont(GETFONT('Fixed', 10))
      if self.special == 'space':
         self.setText(self.tr('SPACE'))
         self.lower = ' '
         self.upper = ' '
         self.special = 5
      elif self.special == 'shift':
         self.setText(self.tr('SHIFT'))
         self.special = 5
         self.insertLetter = self.pressShift
      elif self.special == 'delete':
         self.setText(self.tr('DEL'))
         self.special = 5
         self.insertLetter = self.pressBackspace

   def insertLetter(self):
      currPwd = str(self.parent.edtPasswd.text())
      insChar = self.upper if self.parent.btnShift.isChecked() else self.lower
      if len(insChar) == 2 and insChar.startswith('#'):
         insChar = insChar[1]

      self.parent.edtPasswd.setText(currPwd + insChar)
      self.parent.reshuffleKeys()

   def pressShift(self):
      self.parent.redrawKeys()

   def pressBackspace(self):
      currPwd = str(self.parent.edtPasswd.text())
      if len(currPwd) > 0:
         self.parent.edtPasswd.setText(currPwd[:-1])
      self.parent.redrawKeys()

################################################################################
class DlgGenericGetPassword(ArmoryDialog):
   def __init__(self, descriptionStr, parent=None, main=None):
      super(DlgGenericGetPassword, self).__init__(parent, main)


      lblDescr = QRichLabel(descriptionStr)
      lblPasswd = QRichLabel(self.tr("Password:"))
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton(self.tr("OK"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QGridLayout()
      layout.addWidget(lblDescr, 1, 0, 1, 2)
      layout.addWidget(lblPasswd, 2, 0, 1, 1)
      layout.addWidget(self.edtPasswd, 2, 1, 1, 1)
      layout.addWidget(buttonBox, 3, 1, 1, 2)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Enter Password'))
      self.setWindowIcon(QIcon(self.main.iconfile))

################################################################################
# Hack!  We need to replicate the DlgBugReport... but to be as safe as
# possible for 0.91.1, we simply duplicate the dialog and modify directly.
# TODO:  There's definitely a way to make DlgBugReport more generic so that
#        both these contexts can be handled by it.
class DlgInconsistentWltReport(ArmoryDialog):

   def __init__(self, parent, main, logPathList):
      super(DlgInconsistentWltReport, self).__init__(parent, main)


      QMessageBox.critical(self, self.tr('Inconsistent Wallet!'), self.tr(
         '<font color="%1" size=4><b><u>Important:</u>  Wallet Consistency'
         'Issues Detected!</b></font>'
         '<br><br>'
         'Armory now detects certain kinds of hardware errors, and one'
         'or more of your wallets'
         'was flagged.  The consistency logs need to be analyzed by the'
         'Armory team to determine if any further action is required.'
         '<br><br>'
         '<b>This warning will pop up every time you start Armory until'
         'the wallet is fixed</b>').arg(htmlColor('TextWarn')),
         QMessageBox.Ok)



      # logPathList is [wltID, corruptFolder] pairs
      self.logPathList = logPathList[:]
      walletList = [self.main.walletMap[wid] for wid,folder in logPathList]

      getWltStr = lambda w: '<b>Wallet "%s" (%s)</b>' % \
                                       (w.labelName, w.uniqueIDB58)

      if len(logPathList) == 1:
         wltDispStr = getWltStr(walletList[0]) + ' is'
      else:
         strList = [getWltStr(w) for w in walletList]
         wltDispStr = ', '.join(strList[:-1]) + ' and ' + strList[-1] + ' are '

      lblTopDescr = QRichLabel(self.tr(
         '<b><u><font color="%1" size=4>Submit Wallet Analysis Logs for '
         'Review</font></u></b><br>').arg(htmlColor('TextWarn')),
         hAlign=Qt.AlignHCenter)

      lblDescr = QRichLabel(self.tr(
         'Armory has detected that %1 is inconsistent, '
         'possibly due to hardware errors out of our control.  It <u>strongly '
         'recommended</u> you submit the wallet logs to the Armory developers '
         'for review.  Until you hear back from an Armory developer, '
         'it is recommended that you: '
         '<ul>'
         '<li><b>Do not delete any data in your Armory home directory</b></li> '
         '<li><b>Do not send or receive any funds with the affected wallet(s)</b></li> '
         '<li><b>Create a backup of the wallet analysis logs</b></li> '
         '</ul>').arg(wltDispStr))

      btnBackupLogs = QPushButton(self.tr("Save backup of log files"))
      self.connect(btnBackupLogs, SIGNAL('clicked()'), self.doBackupLogs)
      frmBackup = makeHorizFrame(['Stretch', btnBackupLogs, 'Stretch'])

      self.lblSubject = QRichLabel(self.tr('Subject:'))
      self.edtSubject = QLineEdit()
      self.edtSubject.setMaxLength(64)
      self.edtSubject.setText("Wallet Consistency Logs")

      self.txtDescr = QTextEdit()
      self.txtDescr.setFont(GETFONT('Fixed', 9))
      w,h = tightSizeNChar(self, 80)
      self.txtDescr.setMinimumWidth(w)
      self.txtDescr.setMinimumHeight(int(2.5*h))

      self.btnCancel = QPushButton(self.tr('Close'))
      self.btnbox = QDialogButtonBox()
      self.btnbox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self, SLOT('reject()'))

      layout = QGridLayout()
      i = -1

      i += 1
      layout.addWidget(lblTopDescr,      i,0, 1,2)

      i += 1
      layout.addWidget(lblDescr,         i,0, 1,2)

      i += 1
      layout.addWidget(frmBackup,        i,0, 1,2)

      i += 1
      layout.addWidget(HLINE(),          i,0, 1,2)

      i += 1
      layout.addWidget(self.btnbox,      i,0, 1,2)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Inconsistent Wallet'))
      self.setWindowIcon(QIcon(self.main.iconfile))

   #############################################################################
   def createZipfile(self, zfilePath=None, forceIncludeAllData=False):
      """
      If not forceIncludeAllData, then we will exclude wallet file and/or
      regular logs, depending on the user's checkbox selection.   For making
      a user backup, we always want to include everything, regardless of
      that selection.
      """

      # Should we include wallet files from logs directory?
      includeWlt = self.chkIncludeWOW.isChecked()
      includeReg = self.chkIncludeReg.isChecked()

      # Set to default save path if needed
      if zfilePath is None:
         zfilePath = os.path.join(ARMORY_HOME_DIR, 'wallet_analyze_logs.zip')

      # Remove a previous copy
      if os.path.exists(zfilePath):
         os.remove(zfilePath)

      LOGINFO('Creating archive: %s', zfilePath)
      zfile = ZipFile(zfilePath, 'w', ZIP_DEFLATED)

      # Iterate over all log directories (usually one)
      for wltID,logDir in self.logPathList:
         for fn in os.listdir(logDir):
            fullpath = os.path.join(logDir, fn)

            # If multiple dirs, will see duplicate armorylogs and multipliers
            if not os.path.isfile(fullpath):
               continue


            if not forceIncludeAllData:
               # Exclude any wallet files if the checkbox was not checked
               if not includeWlt and os.path.getsize(fullpath) >= 8:
                  # Don't exclude based on file extension, check leading bytes
                  with open(fullpath, 'rb') as tempopen:
                     if tempopen.read(8) == '\xbaWALLET\x00':
                        continue

               # Exclude regular logs as well, if desired
               if not includeReg and fn in ['armorylog.txt', 'armorycpplog.txt', 'dbLog.txt']:
                  continue


            # If we got here, add file to archive
            parentDir = os.path.basename(logDir)
            archiveName = '%s_%s_%s' % (wltID, parentDir, fn)
            LOGINFO('   Adding %s to archive' % archiveName)
            zfile.write(fullpath, archiveName)

      zfile.close()

      return zfilePath


   #############################################################################
   def doBackupLogs(self):
      saveTo = self.main.getFileSave(ffilter=['Zip files (*.zip)'],
                                     defaultFilename='wallet_analyze_logs.zip')
      if not saveTo:
         QMessageBox.critical(self, self.tr("Not saved"), self.tr(
            'You canceled the backup operation.  No backup was made.'),
            QMessageBox.Ok)
         return

      try:
         self.createZipfile(saveTo, forceIncludeAllData=True)
         QMessageBox.information(self, self.tr('Success'), self.tr(
            'The wallet logs were successfully saved to the following'
            'location:'
            '<br><br>'
            '%1'
            '<br><br>'
            'It is still important to complete the rest of this form'
            'and submit the data to the Armory team for review!').arg(saveTo), QMessageBox.Ok)

      except:
         LOGEXCEPT('Failed to create zip file')
         QMessageBox.warning(self, self.tr('Save Failed'), self.tr('There was an '
            'error saving a copy of your log files'), QMessageBox.Ok)




################################################################################
class DlgNewWallet(ArmoryDialog):

   def __init__(self, parent=None, main=None, initLabel=''):
      super(DlgNewWallet, self).__init__(parent, main)


      self.selectedImport = False

      # Options for creating a new wallet
      lblDlgDescr = QRichLabel(self.tr(
         'Create a new wallet for managing your funds.<br> '
         'The name and description can be changed at any time.'))
      lblDlgDescr.setWordWrap(True)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      self.edtName.setText(initLabel)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)


      self.edtDescr = QTextEdit()
      self.edtDescr.setMaximumHeight(75)
      lblDescr = QLabel("Wallet &description:")
      lblDescr.setAlignment(Qt.AlignVCenter)
      lblDescr.setBuddy(self.edtDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)



      # Advanced Encryption Options
      lblComputeDescr = QLabel(self.tr(
                  'Armory will test your system\'s speed to determine the most '
                  'challenging encryption settings that can be performed '
                  'in a given amount of time.  High settings make it much harder '
                  'for someone to guess your passphrase.  This is used for all '
                  'encrypted wallets, but the default parameters can be changed below.\n'))
      lblComputeDescr.setWordWrap(True)
      timeDescrTip = self.main.createToolTipWidget(self.tr(
                  'This is the amount of time it will take for your computer '
                  'to unlock your wallet after you enter your passphrase. '
                  '(the actual time used will be less than the specified '
                  'time, but more than one half of it).'))


      # Set maximum compute time
      self.edtComputeTime = QLineEdit()
      self.edtComputeTime.setText('250 ms')
      self.edtComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Target compute &time (s, ms):')
      memDescrTip = self.main.createToolTipWidget(self.tr(
                  'This is the <b>maximum</b> memory that will be '
                  'used as part of the encryption process.  The actual value used '
                  'may be lower, depending on your system\'s speed.  If a '
                  'low value is chosen, Armory will compensate by chaining '
                  'together more calculations to meet the target time.  High '
                  'memory target will make GPU-acceleration useless for '
                  'guessing your passphrase.'))
      lblComputeTime.setBuddy(self.edtComputeTime)


      # Set maximum memory usage
      self.edtComputeMem = QLineEdit()
      self.edtComputeMem.setText('32.0 MB')
      self.edtComputeMem.setMaxLength(12)
      lblComputeMem = QLabel(self.tr('Max &memory usage (kB, MB):'))
      lblComputeMem.setBuddy(self.edtComputeMem)

      self.edtComputeTime.setMaximumWidth(tightSizeNChar(self, 20)[0])
      self.edtComputeMem.setMaximumWidth(tightSizeNChar(self, 20)[0])

      # Fork watching-only wallet
      cryptoLayout = QGridLayout()
      cryptoLayout.addWidget(lblComputeDescr, 0, 0, 1, 3)

      cryptoLayout.addWidget(timeDescrTip, 1, 0, 1, 1)
      cryptoLayout.addWidget(lblComputeTime, 1, 1, 1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 2, 1, 1)

      cryptoLayout.addWidget(memDescrTip, 2, 0, 1, 1)
      cryptoLayout.addWidget(lblComputeMem, 2, 1, 1, 1)
      cryptoLayout.addWidget(self.edtComputeMem, 2, 2, 1, 1)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(STYLE_SUNKEN)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      self.chkUseCrypto = QCheckBox(self.tr("Use wallet &encryption"))
      self.chkUseCrypto.setChecked(True)
      usecryptoTooltip = self.main.createToolTipWidget(self.tr(
                  'Encryption prevents anyone who accesses your computer '
                  'or wallet file from being able to spend your money, as ' 
                  'long as they do not have the passphrase. '
                  'You can choose to encrypt your wallet at a later time '
                  'through the wallet properties dialog by double clicking '
                  'the wallet on the dashboard.'))

      # For a new wallet, the user may want to print out a paper backup
      self.chkPrintPaper = QCheckBox(self.tr("Print a paper-backup of this wallet"))
      self.chkPrintPaper.setChecked(True)
      paperBackupTooltip = self.main.createToolTipWidget(self.tr(
                  'A paper-backup allows you to recover your wallet/funds even '
                  'if you lose your original wallet file, any time in the future. '
                  'Because Armory uses "deterministic wallets," ' 
                  'a single backup when the wallet is first made is sufficient '
                  'for all future transactions (except ones to imported '
                  'addresses).\n\n'
                  'Anyone who gets hold of your paper backup will be able to spend '
                  'the money in your wallet, so please secure it appropriately.'))


      self.btnAccept = QPushButton(self.tr("Accept"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.btnAdvCrypto = QPushButton(self.tr("Advanced Encryption Options>>>"))
      self.btnAdvCrypto.setCheckable(True)
      self.btnbox = QDialogButtonBox()
      self.btnbox.addButton(self.btnAdvCrypto, QDialogButtonBox.ActionRole)
      self.btnbox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      self.btnbox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)

      self.connect(self.btnAdvCrypto, SIGNAL('toggled(bool)'), \
                   self.cryptoFrame, SLOT('setVisible(bool)'))
      self.connect(self.btnAccept, SIGNAL(CLICKED), \
                   self.verifyInputsBeforeAccept)
      self.connect(self.btnCancel, SIGNAL(CLICKED), \
                   self, SLOT('reject()'))


      self.btnImportWlt = QPushButton(self.tr("Import wallet..."))
      self.connect(self.btnImportWlt, SIGNAL("clicked()"), \
                    self.importButtonClicked)

      masterLayout = QGridLayout()
      masterLayout.addWidget(lblDlgDescr, 1, 0, 1, 2)
      # masterLayout.addWidget(self.btnImportWlt,  1, 2, 1, 1)
      masterLayout.addWidget(lblName, 2, 0, 1, 1)
      masterLayout.addWidget(self.edtName, 2, 1, 1, 2)
      masterLayout.addWidget(lblDescr, 3, 0, 1, 2)
      masterLayout.addWidget(self.edtDescr, 3, 1, 2, 2)
      masterLayout.addWidget(self.chkUseCrypto, 5, 0, 1, 1)
      masterLayout.addWidget(usecryptoTooltip, 5, 1, 1, 1)
      masterLayout.addWidget(self.chkPrintPaper, 6, 0, 1, 1)
      masterLayout.addWidget(paperBackupTooltip, 6, 1, 1, 1)
      masterLayout.addWidget(self.cryptoFrame, 8, 0, 3, 3)

      masterLayout.addWidget(self.btnbox, 11, 0, 1, 2)

      masterLayout.setVerticalSpacing(5)

      self.setLayout(masterLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame, SLOT("setEnabled(bool)"))

      self.setWindowTitle(self.tr('Create Armory wallet'))
      self.setWindowIcon(QIcon(self.main.iconfile))



   def importButtonClicked(self):
      self.selectedImport = True
      self.accept()

   def verifyInputsBeforeAccept(self):

      ### Confirm that the name and descr are within size limits #######
      wltName = self.edtName.text()
      wltDescr = self.edtDescr.toPlainText()
      if len(wltName) < 1:
         QMessageBox.warning(self, self.tr('Invalid wallet name'), \
                  self.tr('You must enter a name for this wallet, up to 32 characters.'), \
                  QMessageBox.Ok)
         return False

      if len(wltDescr) > 256:
         reply = QMessageBox.warning(self, self.tr('Input too long'), self.tr(
                  'The wallet description is limited to 256 characters.  Only the first '
                  '256 characters will be used.'), \
                  QMessageBox.Ok | QMessageBox.Cancel)
         if reply == QMessageBox.Ok:
            self.edtDescr.setText(wltDescr[:256])
         else:
            return False

      ### Check that the KDF inputs are well-formed ####################
      try:
         kdfT, kdfUnit = str(self.edtComputeTime.text()).strip().split(' ')
         if kdfUnit.lower() == 'ms':
            self.kdfSec = float(kdfT) / 1000.
         elif kdfUnit.lower() in ('s', 'sec', 'seconds'):
            self.kdfSec = float(kdfT)

         if not (self.kdfSec <= 20.0):
            QMessageBox.critical(self, self.tr('Invalid KDF Parameters'), self.tr(
               'Please specify a compute time no more than 20 seconds. '
               'Values above one second are usually unnecessary.'))
            return False

         kdfM, kdfUnit = str(self.edtComputeMem.text()).split(' ')
         if kdfUnit.lower() == 'mb':
            self.kdfBytes = round(float(kdfM) * (1024.0 ** 2))
         if kdfUnit.lower() == 'kb':
            self.kdfBytes = round(float(kdfM) * (1024.0))

         if not (2 ** 15 <= self.kdfBytes <= 2 ** 31):
            QMessageBox.critical(self, self.tr('Invalid KDF Parameters'), \
               self.tr('Please specify a maximum memory usage between 32 kB and 2048 MB.'))
            return False

         LOGINFO('KDF takes %0.2f seconds and %d bytes', self.kdfSec, self.kdfBytes)
      except:
         QMessageBox.critical(self, self.tr('Invalid Input'), self.tr(
            'Please specify time with units, such as '
            '"250 ms" or "2.1 s".  Specify memory as kB or MB, such as '
            '"32 MB" or "256 kB". '), QMessageBox.Ok)
         return False


      self.accept()


   def getImportWltPath(self):
      self.importFile = QFileDialog.getOpenFileName(self, self.tr('Import Wallet File'), \
          ARMORY_HOME_DIR, self.tr('Wallet files (*.wallet);; All files (*)'))
      if self.importFile:
         self.accept()




################################################################################
class DlgChangePassphrase(ArmoryDialog):
   def __init__(self, parent=None, main=None, noPrevEncrypt=True):
      super(DlgChangePassphrase, self).__init__(parent, main)



      layout = QGridLayout()
      if noPrevEncrypt:
         lblDlgDescr = QLabel(self.tr('Please enter an passphrase for wallet encryption.\n\n'
                              'A good passphrase consists of at least 8 or more\n'
                              'random letters, or 5 or more random words.\n'))
         lblDlgDescr.setWordWrap(True)
         layout.addWidget(lblDlgDescr, 0, 0, 1, 2)
      else:
         lblDlgDescr = QLabel(self.tr("Change your wallet encryption passphrase"))
         layout.addWidget(lblDlgDescr, 0, 0, 1, 2)
         self.edtPasswdOrig = QLineEdit()
         self.edtPasswdOrig.setEchoMode(QLineEdit.Password)
         self.edtPasswdOrig.setMinimumWidth(MIN_PASSWD_WIDTH(self))
         lblCurrPasswd = QLabel(self.tr('Current Passphrase:'))
         layout.addWidget(lblCurrPasswd, 1, 0)
         layout.addWidget(self.edtPasswdOrig, 1, 1)



      lblPwd1 = QLabel(self.tr("New Passphrase:"))
      self.edtPasswd1 = QLineEdit()
      self.edtPasswd1.setEchoMode(QLineEdit.Password)
      self.edtPasswd1.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      lblPwd2 = QLabel(self.tr("Again:"))
      self.edtPasswd2 = QLineEdit()
      self.edtPasswd2.setEchoMode(QLineEdit.Password)
      self.edtPasswd2.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      layout.addWidget(lblPwd1, 2, 0)
      layout.addWidget(lblPwd2, 3, 0)
      layout.addWidget(self.edtPasswd1, 2, 1)
      layout.addWidget(self.edtPasswd2, 3, 1)

      self.lblMatches = QLabel(' ' * 20)
      self.lblMatches.setTextFormat(Qt.RichText)
      layout.addWidget(self.lblMatches, 4, 1)


      self.chkDisableCrypt = QCheckBox(self.tr('Disable encryption for this wallet'))
      if not noPrevEncrypt:
         self.connect(self.chkDisableCrypt, SIGNAL('toggled(bool)'), \
                      self.disablePassphraseBoxes)
         layout.addWidget(self.chkDisableCrypt, 4, 0)


      self.btnAccept = QPushButton(self.tr("Accept"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      layout.addWidget(buttonBox, 5, 0, 1, 2)

      if noPrevEncrypt:
         self.setWindowTitle(self.tr("Set Encryption Passphrase"))
      else:
         self.setWindowTitle(self.tr("Change Encryption Passphrase"))

      self.setWindowIcon(QIcon(self.main.iconfile))

      self.setLayout(layout)

      self.connect(self.edtPasswd1, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)
      self.connect(self.edtPasswd2, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)

      self.connect(self.btnAccept, SIGNAL(CLICKED), \
                   self.checkPassphraseFinal)

      self.connect(self.btnCancel, SIGNAL(CLICKED), \
                   self, SLOT('reject()'))


   def disablePassphraseBoxes(self, noEncrypt=True):
      self.edtPasswd1.setEnabled(not noEncrypt)
      self.edtPasswd2.setEnabled(not noEncrypt)


   def checkPassphrase(self):
      if self.chkDisableCrypt.isChecked():
         return True
      p1 = self.edtPasswd1.text()
      p2 = self.edtPasswd2.text()
      goodColor = htmlColor('TextGreen')
      badColor = htmlColor('TextRed')
      if not isASCII(unicode(p1)) or \
         not isASCII(unicode(p2)):
         self.lblMatches.setText(self.tr('<font color=%1><b>Passphrase is non-ASCII!</b></font>').arg(badColor))
         return False
      if not p1 == p2:
         self.lblMatches.setText(self.tr('<font color=%1><b>Passphrases do not match!</b></font>').arg(badColor))
         return False
      if len(p1) < 5:
         self.lblMatches.setText(self.tr('<font color=%1><b>Passphrase is too short!</b></font>').arg(badColor))
         return False
      self.lblMatches.setText(self.tr('<font color=%1><b>Passphrases match!</b></font>').arg(goodColor))
      return True


   def checkPassphraseFinal(self):
      if self.chkDisableCrypt.isChecked():
         self.accept()
      else:
         if self.checkPassphrase():
            dlg = DlgPasswd3(self, self.main)
            if dlg.exec_():
               if not str(dlg.edtPasswd3.text()) == str(self.edtPasswd1.text()):
                  QMessageBox.critical(self, self.tr('Invalid Passphrase'), \
                     self.tr('You entered your confirmation passphrase incorrectly!'), QMessageBox.Ok)
               else:
                  self.accept()
            else:
               self.reject()



class DlgPasswd3(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgPasswd3, self).__init__(parent, main)


      lblWarnImgL = QLabel()
      lblWarnImgL.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImgL.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblWarnTxt1 = QRichLabel(\
         self.tr('<font color="red"><b>!!! DO NOT FORGET YOUR PASSPHRASE !!!</b></font>'), size=4)
      lblWarnTxt1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt2 = QRichLabel(self.tr(
        '<b>No one can help you recover you bitcoins if you forget the '
         'passphrase and don\'t have a paper backup!</b> Your wallet and '
         'any <u>digital</u> backups are useless if you forget it.  '
         '<br><br>'
         'A <u>paper</u> backup protects your wallet forever, against '
         'hard-drive loss and losing your passphrase.  It also protects you '
         'from theft, if the wallet was encrypted and the paper backup '
         'was not stolen with it.  Please make a paper backup and keep it in '
         'a safe place.'
         '<br><br>'
         '<b>Please enter your passphrase a third time to indicate that you '
         'are aware of the risks of losing your passphrase!</b>'), doWrap=True)


      self.edtPasswd3 = QLineEdit()
      self.edtPasswd3.setEchoMode(QLineEdit.Password)
      self.edtPasswd3.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      bbox = QDialogButtonBox()
      btnOk = QPushButton(self.tr('Accept'))
      btnNo = QPushButton(self.tr('Cancel'))
      self.connect(btnOk, SIGNAL(CLICKED), self.accept)
      self.connect(btnNo, SIGNAL(CLICKED), self.reject)
      bbox.addButton(btnOk, QDialogButtonBox.AcceptRole)
      bbox.addButton(btnNo, QDialogButtonBox.RejectRole)
      layout = QGridLayout()
      layout.addWidget(lblWarnImgL, 0, 0, 4, 1)
      layout.addWidget(lblWarnTxt1, 0, 1, 1, 1)
      layout.addWidget(lblWarnTxt2, 2, 1, 1, 1)
      layout.addWidget(self.edtPasswd3, 5, 1, 1, 1)
      layout.addWidget(bbox, 6, 1, 1, 2)
      self.setLayout(layout)
      self.setWindowTitle(self.tr('WARNING!'))



################################################################################
class DlgChangeLabels(ArmoryDialog):
   def __init__(self, currName='', currDescr='', parent=None, main=None):
      super(DlgChangeLabels, self).__init__(parent, main)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel(self.tr("Wallet &name:"))
      lblName.setBuddy(self.edtName)

      self.edtDescr = QTextEdit()
      tightHeight = tightSizeNChar(self.edtDescr, 1)[1]
      self.edtDescr.setMaximumHeight(tightHeight * 4.2)
      lblDescr = QLabel(self.tr("Wallet &description:"))
      lblDescr.setAlignment(Qt.AlignVCenter)
      lblDescr.setBuddy(self.edtDescr)

      self.edtName.setText(currName)
      self.edtDescr.setText(currDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(lblName, 1, 0, 1, 1)
      layout.addWidget(self.edtName, 1, 1, 1, 1)
      layout.addWidget(lblDescr, 2, 0, 1, 1)
      layout.addWidget(self.edtDescr, 2, 1, 2, 1)
      layout.addWidget(buttonBox, 4, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle(self.tr('Wallet Descriptions'))


   def accept(self, *args):
      if not isASCII(unicode(self.edtName.text())) or \
         not isASCII(unicode(self.edtDescr.toPlainText())):
         UnicodeErrorBox(self)
         return

      if len(str(self.edtName.text()).strip()) == 0:
         QMessageBox.critical(self, self.tr('Empty Name'), \
            self.tr('All wallets must have a name. '), QMessageBox.Ok)
         return
      super(DlgChangeLabels, self).accept(*args)


################################################################################
class DlgWalletDetails(ArmoryDialog):
   """ For displaying the details of a specific wallet, with options """

   #############################################################################
   def __init__(self, wlt, usermode=USERMODE.Standard, parent=None, main=None):
      super(DlgWalletDetails, self).__init__(parent, main)
      self.setAttribute(Qt.WA_DeleteOnClose)


      self.wlt = wlt
      self.usermode = usermode
      self.wlttype, self.typestr = determineWalletType(wlt, parent)
      if self.typestr == 'Encrypted':
         self.typestr = 'Encrypted (AES256)'

      self.labels = [wlt.labelName, wlt.labelDescr]
      self.passphrase = ''
      self.setMinimumSize(800, 400)

      w, h = relaxedSizeNChar(self, 60)
      viewWidth, viewHeight = w, 10 * h


      # Address view    
      self.wltAddrTreeModel = AddressTreeModel(self, wlt)
      self.wltAddrView = QTreeView()
      self.wltAddrView.setModel(self.wltAddrTreeModel)
      self.wltAddrView.setMinimumWidth(550)
      self.wltAddrView.setMinimumHeight(150)
      self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressView)
      
      # Now add all the options buttons, dependent on the type of wallet.

      lbtnChangeLabels = QLabelButton(self.tr('Change Wallet Labels'));
      self.connect(lbtnChangeLabels, SIGNAL(CLICKED), self.changeLabels)

      if not self.wlt.watchingOnly:
         s = ''
         if self.wlt.useEncryption:
            s = self.tr('Change or Remove Passphrase')
         else:
            s = self.tr('Encrypt Wallet')
         lbtnChangeCrypto = QLabelButton(s)
         self.connect(lbtnChangeCrypto, SIGNAL(CLICKED), self.changeEncryption)

      exportStr = 'Data' if self.wlt.watchingOnly else 'Copy'
      lbtnSendBtc = QLabelButton(self.tr('Send Bitcoins'))
      lbtnGenAddr = QLabelButton(self.tr('Receive Bitcoins'))
      lbtnImportA = QLabelButton(self.tr('Import/Sweep Private Keys'))
      lbtnDeleteA = QLabelButton(self.tr('Remove Imported Address'))
      # lbtnSweepA  = QLabelButton('Sweep Wallet/Address')
      lbtnExpWOWlt = QLabelButton(self.tr('Export Watching-Only %1').arg(exportStr))
      lbtnBackups = QLabelButton(self.tr('<b>Backup This Wallet</b>'))
      lbtnRemove = QLabelButton(self.tr('Delete/Remove Wallet'))
      #lbtnRecover = QLabelButton('Recover Password Wallet')

      # LOGERROR('remove me!')
      # fnfrag = lambda: DlgFragBackup(self, self.main, self.wlt).exec_()
      # LOGERROR('remove me!')

      self.connect(lbtnSendBtc, SIGNAL(CLICKED), self.execSendBtc)
      self.connect(lbtnGenAddr, SIGNAL(CLICKED), self.getNewAddress)
      self.connect(lbtnBackups, SIGNAL(CLICKED), self.execBackupDlg)
      # self.connect(lbtnBackups, SIGNAL(CLICKED), fnfrag)
      self.connect(lbtnRemove, SIGNAL(CLICKED), self.execRemoveDlg)
      self.connect(lbtnImportA, SIGNAL(CLICKED), self.execImportAddress)
      self.connect(lbtnDeleteA, SIGNAL(CLICKED), self.execDeleteAddress)
      self.connect(lbtnExpWOWlt, SIGNAL(CLICKED), self.execExpWOCopy)
      #self.connect(lbtnRecover, SIGNAL(CLICKED), self.recoverPwd)

      lbtnSendBtc.setToolTip(self.tr('Send bitcoins to other users, or transfer between wallets'))
      if self.wlt.watchingOnly:
         lbtnSendBtc.setToolTip(self.tr('If you have a full-copy of this wallet on another computer, you can prepare a '
                                'transaction, to be signed by that computer.'))
      lbtnGenAddr.setToolTip(self.tr('Get a new address from this wallet for receiving '
                             'bitcoins.  Right click on the address list below '
                             'to copy an existing address.'))
      lbtnImportA.setToolTip(self.tr('Import or "Sweep" an address which is not part '
                             'of your wallet.  Useful for VanityGen addresses '
                             'and redeeming Casascius physical bitcoins.'))
      lbtnDeleteA.setToolTip(self.tr('Permanently delete an imported address from '
                             'this wallet.  You cannot delete addresses that '
                             'were generated natively by this wallet.'))
      # lbtnSweepA .setToolTip('')
      lbtnExpWOWlt.setToolTip(self.tr('Export a copy of this wallet that can '
                             'only be used for generating addresses and '
                             'monitoring incoming payments.  A watching-only '
                             'wallet cannot spend the funds, and thus cannot '
                             'be compromised by an attacker'))
      lbtnBackups.setToolTip(self.tr('See lots of options for backing up your wallet '
                             'to protect the funds in it.'))
      lbtnRemove.setToolTip(self.tr('Permanently delete this wallet, or just delete '
                             'the private keys to convert it to a watching-only '
                             'wallet.'))
      #lbtnRecover.setToolTip('Attempt to recover a lost password using '
      #                      'details that you remember.')
      if not self.wlt.watchingOnly:
         lbtnChangeCrypto.setToolTip(self.tr('Add/Remove/Change wallet encryption settings.'))

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)
      optLayout = QVBoxLayout()

      hasPriv = not self.wlt.watchingOnly
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Expert))

      def createVBoxSeparator():
         frm = QFrame()
         frm.setFrameStyle(QFrame.HLine | QFrame.Plain)
         return frm

      if True:              optLayout.addWidget(lbtnSendBtc)
      if True:              optLayout.addWidget(lbtnGenAddr)
      if hasPriv:           optLayout.addWidget(lbtnChangeCrypto)
      if True:              optLayout.addWidget(lbtnChangeLabels)

      if True:              optLayout.addWidget(createVBoxSeparator())

      if hasPriv:           optLayout.addWidget(lbtnBackups)
      if adv:               optLayout.addWidget(lbtnExpWOWlt)
      if True:              optLayout.addWidget(lbtnRemove)
      # if True:              optLayout.addWidget(lbtnRecover)
      # Not sure yet that we want to include the password finer in here

      if adv:               optLayout.addWidget(createVBoxSeparator())

      if adv:   optLayout.addWidget(lbtnImportA)
      if hasPriv and adv:   optLayout.addWidget(lbtnDeleteA)
      # if hasPriv and adv:   optLayout.addWidget(lbtnSweepA)

      optLayout.addStretch()
      optFrame.setLayout(optLayout)


      self.frm = QFrame()
      self.setWltDetailsFrame()

      totalFunds = self.wlt.getBalance('Total')
      spendFunds = self.wlt.getBalance('Spendable')
      unconfFunds = self.wlt.getBalance('Unconfirmed')
      uncolor = htmlColor('MoneyNeg')  if unconfFunds > 0          else htmlColor('Foreground')
      btccolor = htmlColor('DisableFG') if spendFunds == totalFunds else htmlColor('MoneyPos')
      lblcolor = htmlColor('DisableFG') if spendFunds == totalFunds else htmlColor('Foreground')
      goodColor = htmlColor('TextGreen')

      self.lblTot = QRichLabel('', doWrap=False);
      self.lblSpd = QRichLabel('', doWrap=False);
      self.lblUnc = QRichLabel('', doWrap=False);

      self.lblTotalFunds = QRichLabel('', doWrap=False)
      self.lblSpendFunds = QRichLabel('', doWrap=False)
      self.lblUnconfFunds = QRichLabel('', doWrap=False)
      self.lblTotalFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpendFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUnconfFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      self.lblTot.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUnc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


      self.lblBTC1 = QRichLabel('', doWrap=False)
      self.lblBTC2 = QRichLabel('', doWrap=False)
      self.lblBTC3 = QRichLabel('', doWrap=False)

      ttipTot = self.main.createToolTipWidget(\
            self.tr('Total funds if all current transactions are confirmed. '
            'Value appears gray when it is the same as your spendable funds.'))
      ttipSpd = self.main.createToolTipWidget(\
            self.tr('Funds that can be spent <i>right now</i>'))
      ttipUcn = self.main.createToolTipWidget(\
            self.tr('Funds that have less than 6 confirmations'))

      self.setSummaryBalances()


      frmTotals = QFrame()
      frmTotals.setFrameStyle(STYLE_NONE)
      frmTotalsLayout = QGridLayout()
      frmTotalsLayout.addWidget(self.lblTot, 0, 0)
      frmTotalsLayout.addWidget(self.lblSpd, 1, 0)
      frmTotalsLayout.addWidget(self.lblUnc, 2, 0)

      frmTotalsLayout.addWidget(self.lblTotalFunds, 0, 1)
      frmTotalsLayout.addWidget(self.lblSpendFunds, 1, 1)
      frmTotalsLayout.addWidget(self.lblUnconfFunds, 2, 1)

      frmTotalsLayout.addWidget(self.lblBTC1, 0, 2)
      frmTotalsLayout.addWidget(self.lblBTC2, 1, 2)
      frmTotalsLayout.addWidget(self.lblBTC3, 2, 2)

      frmTotalsLayout.addWidget(ttipTot, 0, 3)
      frmTotalsLayout.addWidget(ttipSpd, 1, 3)
      frmTotalsLayout.addWidget(ttipUcn, 2, 3)

      frmTotals.setLayout(frmTotalsLayout)

      lblWltAddr = QRichLabel(self.tr('<b>Addresses in Wallet:</b>'), doWrap=False)

      btnGoBack = QPushButton(self.tr('<<< Go Back'))
      self.connect(btnGoBack, SIGNAL(CLICKED), self.accept)
      bottomFrm = makeHorizFrame([btnGoBack, STRETCH, frmTotals])

      layout = QGridLayout()
      layout.addWidget(self.frm, 0, 0)
      layout.addWidget(self.wltAddrView, 2, 0)
      layout.addWidget(bottomFrm, 3, 0)

      # layout.addWidget(QLabel("Available Actions:"), 0, 4)
      layout.addWidget(optFrame, 0, 1, 4, 1)
      layout.setRowStretch(0, 0)
      layout.setRowStretch(1, 0)
      layout.setRowStretch(2, 1)
      layout.setRowStretch(3, 0)
      layout.setColumnStretch(0, 1)
      layout.setColumnStretch(1, 0)
      self.setLayout(layout)

      self.setWindowTitle(self.tr('Wallet Properties'))

      #self.doFilterAddr()

      hexgeom = self.main.settings.get('WltPropGeometry')
      tblgeom = self.main.settings.get('WltPropAddrCols')
      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(tblgeom) > 0:
         restoreTableView(self.wltAddrView, tblgeom)

      def remindBackup():
         result = MsgBoxWithDNAA(self, self.main, MSGBOX.Warning, self.tr('Wallet Backup'), self.tr(
            '<b><font color="red" size=4>Please backup your wallet!</font></b> '
            '<br><br>'
            'Making a paper backup will guarantee you can recover your '
            'coins at <a>any time in the future</a>, even if your '
            'hard drive dies or you forget your passphrase.  Without it, '
            'you could permanently lose your coins!  '
            'The backup buttons are to the right of the address list.'
            '<br><br>'
            'A paper backup is recommended, '
            'and it can be copied by hand if you do not have a working printer. '
            'A digital backup only works if you remember the passphrase '
            'used at the time it was created.  If you have ever forgotten a '
            'password before, only rely on a digital backup if you store '
            'the password with it!'
            '<br><br>'
            '<a href="https://bitcointalk.org/index.php?topic=152151.0">'
            'Read more about Armory backups</a>'), None, yesStr='Ok', \
            dnaaStartChk=True)
         self.main.setWltSetting(wlt.uniqueIDB58, 'DNAA_RemindBackup', result[1])



      wltType = determineWalletType(wlt, main)[0]
      chkLoad = (self.main.getSettingOrSetDefault('Load_Count', 1) % 5 == 0)
      chkType = not wltType in (WLTTYPES.Offline, WLTTYPES.WatchOnly)
      chkDNAA = not self.main.getWltSetting(wlt.uniqueIDB58, 'DNAA_RemindBackup')
      chkDont = not self.main.getSettingOrSetDefault('DNAA_AllBackupWarn', False)
      if chkLoad and chkType and chkDNAA and chkDont:
         self.callLater(1, remindBackup)
         lbtnBackups.setText(self.tr('<font color="%1"><b>Backup This Wallet</b></font>').arg(htmlColor('TextWarn')))

   #############################################################################
   def doFilterAddr(self):
      self.wltAddrModel.setFilter(self.chkHideEmpty.isChecked(), \
                                  self.chkHideChange.isChecked(), \
                                  self.chkHideUnused.isChecked())
      self.wltAddrModel.reset()

   #############################################################################
   def setSummaryBalances(self):
      totalFunds = self.wlt.getBalance('Total')
      spendFunds = self.wlt.getBalance('Spendable')
      unconfFunds = self.wlt.getBalance('Unconfirmed')
      uncolor = htmlColor('MoneyNeg')  if unconfFunds > 0          else htmlColor('Foreground')
      btccolor = htmlColor('DisableFG') if spendFunds == totalFunds else htmlColor('MoneyPos')
      lblcolor = htmlColor('DisableFG') if spendFunds == totalFunds else htmlColor('Foreground')
      goodColor = htmlColor('TextGreen')

      self.lblTot.setText(self.tr('<b><font color="%1">Maximum Funds:</font></b>').arg(lblcolor))
      self.lblSpd.setText(self.tr('<b>Spendable Funds:</b>'))
      self.lblUnc.setText(self.tr('<b>Unconfirmed:</b>'))

      if TheBDM.getState() in (BDM_UNINITIALIZED, BDM_OFFLINE, BDM_SCANNING):
         totStr = '-' * 12
         spdStr = '-' * 12
         ucnStr = '-' * 12
      else:
         totStr = '<b><font color="%s">%s</font></b>' % (btccolor, coin2str(totalFunds))
         spdStr = '<b><font color="%s">%s</font></b>' % (goodColor, coin2str(spendFunds))
         ucnStr = '<b><font color="%s">%s</font></b>' % (uncolor, coin2str(unconfFunds))

      self.lblTotalFunds.setText(totStr)
      self.lblSpendFunds.setText(spdStr)
      self.lblUnconfFunds.setText(ucnStr)

      self.lblBTC1.setText('<b><font color="%s">BTC</font></b>' % lblcolor)
      self.lblBTC2.setText('<b>BTC</b>')
      self.lblBTC3.setText('<b>BTC</b>')


   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('WltPropGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('WltPropAddrCols', saveTableView(self.wltAddrView))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).reject(*args)

   #############################################################################
   def showContextMenu(self, pos):
      menu = QMenu(self.wltAddrView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:  actionCopyAddr = menu.addAction(self.tr("Copy Address"))
      if True:  actionShowQRCode = menu.addAction(self.tr("Display Address QR Code"))
      if True:  actionBlkChnInfo = menu.addAction(self.tr("View Address on %1").arg(BLOCKEXPLORE_NAME))
      if True:  actionReqPayment = menu.addAction(self.tr("Request Payment to this Address"))
      if dev:   actionCopyHash160 = menu.addAction(self.tr("Copy Hash160 (hex)"))
      if dev:   actionCopyPubKey  = menu.addAction(self.tr("Copy Raw Public Key (hex)"))
      if True:  actionCopyComment = menu.addAction(self.tr("Copy Comment"))
      if True:  actionCopyBalance = menu.addAction(self.tr("Copy Balance"))
      try:
         idx = self.wltAddrView.selectedIndexes()[0]
      except IndexError:
         # Nothing was selected for a context menu to act upon.  Return.
         return
      action = menu.exec_(QCursor.pos())


      # Get data on a given row, easily
      def getModelStr(col):
         model = self.wltAddrView.model()
         qstr = model.index(idx.row(), col).data().toString()
         return str(qstr).strip()


      addr = getModelStr(ADDRESSCOLS.Address)
      if action == actionCopyAddr:
         clippy = addr
      elif action == actionBlkChnInfo:
         blkchnURL = BLOCKEXPLORE_URL_ADDR % addr
         try:
            DlgBrowserWarn(blkchnURL).exec_()
         except:
            QMessageBox.critical(self, self.tr('Could not open browser'), self.tr(
               'Armory encountered an error opening your web browser.  To view '
               'this address on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>'
               '<a href="%1">%2</a>').arg(blkchnURL, blkchnURL), QMessageBox.Ok)
         return
      elif action == actionShowQRCode:
         wltstr = 'Wallet: %s (%s)' % (self.wlt.labelName, self.wlt.uniqueIDB58)
         DlgQRCodeDisplay(self, self.main, addr, addr, wltstr).exec_()
         return
      elif action == actionReqPayment:
         DlgRequestPayment(self, self.main, addr).exec_()
         return
      elif dev and action == actionCopyHash160:
         clippy = binary_to_hex(addrStr_to_hash160(addr)[1])
      elif dev and action == actionCopyPubKey:
         astr = getModelStr(ADDRESSCOLS.Address)
         addrObj = self.wlt.getAddrByHash160( addrStr_to_hash160(astr)[1] )
         clippy = addrObj.binPublicKey65.toHexStr()
      elif action == actionCopyComment:
         clippy = getModelStr(ADDRESSCOLS.Comment)
      elif action == actionCopyBalance:
         clippy = getModelStr(ADDRESSCOLS.Balance)
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(clippy).strip())

   #############################################################################
   def dblClickAddressView(self, index):
      from ui.TreeViewGUI import COL_TREE, COL_COMMENT
      
      nodeItem = self.wltAddrTreeModel.getNodeItem(index)
      try:
         if not nodeItem.treeNode.canDoubleClick():
            return
      except:
         return
            
      cppAddrObj = nodeItem.treeNode.getAddrObj()
      
      if index.column() == COL_COMMENT:
         # Update the address's comment. We apparently need to reset the model
         # to get an immediate comment update on OS X, unlike Linux or Windows.
         currComment = cppAddrObj.getComment()
         
         
         if not currComment:
            dialog = DlgSetComment(self, self.main, currComment, self.tr('Add Address Comment'))
         else:
            dialog = DlgSetComment(self, self.main, currComment, self.tr('Change Address Comment'))
         if dialog.exec_():
            newComment = str(dialog.edtComment.text())
            addr160 = cppAddrObj.getAddrHash()
            self.wlt.setComment(addr160[1:], newComment)
            cppAddrObj.setComment(newComment)
            
            if OS_MACOSX:
               self.wltAddrView.reset()

      else:
         dlg = DlgAddressInfo(self.wlt, cppAddrObj, self, self.main)
         dlg.exec_()


   #############################################################################
   def changeLabels(self):
      dlgLabels = DlgChangeLabels(self.wlt.labelName, self.wlt.labelDescr, self, self.main)
      if dlgLabels.exec_():
         # Make sure to use methods like this which not only update in memory,
         # but guarantees the file is updated, too
         newName = str(dlgLabels.edtName.text())[:32]
         newDescr = str(dlgLabels.edtDescr.toPlainText())[:256]
         self.wlt.setWalletLabels(newName, newDescr)

         self.labelValues[WLTFIELDS.Name].setText(newName)
         self.labelValues[WLTFIELDS.Descr].setText(newDescr)


   #############################################################################
   def changeEncryption(self):
      dlgCrypt = DlgChangePassphrase(self, self.main, not self.wlt.useEncryption)
      if dlgCrypt.exec_():
         self.disableEncryption = dlgCrypt.chkDisableCrypt.isChecked()
         newPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswd1.text()))
         dlgCrypt.edtPasswd1.clear()
         dlgCrypt.edtPasswd2.clear()

         if self.wlt.useEncryption:
            origPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswdOrig.text()))
            dlgCrypt.edtPasswdOrig.clear()
            if self.wlt.verifyPassphrase(origPassphrase):
               unlockProgress = DlgProgress(self, self.main, HBar=1,
                                            Title="Unlocking Wallet")
               unlockProgress.exec_(self.wlt.unlock, securePassphrase=origPassphrase)
            else:
               # Even if the wallet is already unlocked, enter pwd again to change it
               QMessageBox.critical(self, self.tr('Invalid Passphrase'), \
                     self.tr('Previous passphrase is not correct!  Could not unlock wallet.'), \
                     QMessageBox.Ok)


         if self.disableEncryption:
            unlockProgress = DlgProgress(self, self.main, HBar=1, 
                                         Title=self.tr("Changing Encryption"))
            unlockProgress.exec_(self.wlt.changeWalletEncryption)
            # self.accept()
            self.labelValues[WLTFIELDS.Secure].setText(self.tr('No Encryption'))
            self.labelValues[WLTFIELDS.Secure].setText('')
            self.labelValues[WLTFIELDS.Secure].setText('')
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            unlockProgress = DlgProgress(self, self.main, HBar=2, 
                                         Title=self.tr("Changing Encryption"))
            unlockProgress.exec_(self.wlt.changeWalletEncryption,
                                 securePassphrase=newPassphrase)
            self.labelValues[WLTFIELDS.Secure].setText(self.tr('Encrypted (AES256)'))
            # self.accept()


   def getNewAddress(self):
      if showRecvCoinsWarningIfNecessary(self.wlt, self, self.main):
         loading = LoadingDisp(self, self.main)
         loading.show()
         DlgNewAddressDisp(self.wlt, self, self.main, loading).exec_()
         self.resetTreeView()


   def execSendBtc(self):
      if TheBDM.getState() in (BDM_OFFLINE, BDM_UNINITIALIZED):
         QMessageBox.warning(self, self.tr('Offline Mode'), self.tr(
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br> '
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.'), QMessageBox.Ok)
         return
      if TheBDM.getState() == BDM_SCANNING:
         QMessageBox.warning(self, self.tr('Armory Not Ready'), self.tr(
           'Armory is currently scanning the blockchain to collect '
           'the information needed to create transactions.  This '
           'typically takes between one and five minutes.  Please '
           'wait until your balance appears on the main window, '
           'then try again.'), \
            QMessageBox.Ok)
         return

      self.accept()
      DlgSendBitcoins(self.wlt, self, self.main, onlyOfflineWallets=False).exec_()
      self.resetTreeView()

   def resetTreeView(self):
      self.wltAddrTreeModel.refresh()
      self.wltAddrView.reset()

   def changeKdf(self):
      """
      This is a low-priority feature.  I mean, the PyBtcWallet class has this
      feature implemented, but I don't have a GUI for it
      """
      pass


   def execBackupDlg(self):
      if self.main.usermode == USERMODE.Expert:
         DlgBackupCenter(self, self.main, self.wlt).exec_()
      else:
         DlgSimpleBackup(self, self.main, self.wlt).exec_()

   def execPrintDlg(self):
      if self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, self.tr('Create Paper Backup'))
         if not unlockdlg.exec_():
            return

      if not self.wlt.addrMap['ROOT'].hasPrivKey():
         QMessageBox.warning(self, self.tr('Move along...'), \
           self.tr('This wallet does not contain any private keys.  Nothing to backup!'), QMessageBox.Ok)
         return

      OpenPaperBackupWindow('Single', self, self.main, self.wlt)


   def execRemoveDlg(self):
      dlg = DlgRemoveWallet(self.wlt, self, self.main)
      if dlg.exec_():
         pass  # not sure that I don't handle everything in the dialog itself

   def execKeyList(self):
      if self.wlt.useEncryption and self.wlt.isLocked:
         dlg = DlgUnlockWallet(self.wlt, self, self.main, self.tr('Unlock Private Keys'))
         if not dlg.exec_():
            if self.main.usermode == USERMODE.Expert:
               QMessageBox.warning(self, self.tr('Unlock Failed'), self.tr(
                  'Wallet was not unlocked.  The public keys and addresses '
                  'will still be shown, but private keys will not be available '
                  'unless you reopen the dialog with the correct passphrase'), \
                  QMessageBox.Ok)
            else:
               QMessageBox.warning(self, self.tr('Unlock Failed'), self.tr(
                  'Wallet could not be unlocked to display individual keys.'), \
                  QMessageBox.Ok)
               return

      dlg = DlgShowKeyList(self.wlt, self, self.main)
      dlg.exec_()

   def execDeleteAddress(self):
      selectedList = self.wltAddrView.selectedIndexes()
      if len(selectedList) == 0:
         QMessageBox.warning(self, self.tr('No Selection'), \
               self.tr('You must select an address to remove!'), \
               QMessageBox.Ok)
         return

      nodeIndex = selectedList[0]
      nodeItem = self.wltAddrTreeModel.getNodeItem(nodeIndex)
      addrStr = nodeItem.treeNode.getName()
      atype, addr160 = addrStr_to_hash160(addrStr)
      if atype==P2SHBYTE:
         LOGWARN('Deleting P2SH address: %s' % addrStr)

      
      if self.wlt.cppWallet.getAssetIndexForAddr(addr160) < 0:
         dlg = DlgRemoveAddress(self.wlt, addr160, self, self.main)
         dlg.exec_()
      else:
         QMessageBox.warning(self, self.tr('Invalid Selection'), self.tr(
               'You cannot delete addresses generated by your wallet. '
               'Only imported addresses can be deleted.'), \
               QMessageBox.Ok)
         return


   def execImportAddress(self):
      if not self.main.getSettingOrSetDefault('DNAA_ImportWarning', False):
         result = MsgBoxWithDNAA(self, self.main, MSGBOX.Warning, \
            self.tr('Imported Address Warning'), self.tr(
            'Armory supports importing of external private keys into your '
            'wallet but imported addresses are <u>not</u> automatically '
            'protected by your backups.  If you do not plan to use the '
            'address again, it is recommended that you "Sweep" the private '
            'key instead of importing it. '
            '<br><br> '
            'Individual private keys, including imported ones, can be '
            'backed up using the "Export Key Lists" option in the wallet '
            'backup window.'), None)
         self.main.writeSetting('DNAA_ImportWarning', result[1])

      # Now we are past the [potential] warning box.  Actually open
      # the import dialog
      dlg = DlgImportAddress(self.wlt, self, self.main)
      dlg.exec_()

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         pass


   #############################################################################
   def execExpWOCopy(self):
      """
      Function executed when a user executes the \"Export Public Key & Chain
      Code\" option.
      """
      # This should never happen....
      if not self.wlt.addrMap['ROOT'].hasChainCode():
         QMessageBox.warning(self,
                             self.tr('Move along... This wallet does not have '
                             'a chain code. Backups are pointless!'), QMessageBox.Ok)
         return

      # Proceed to the actual export center.
      dlg = DlgExpWOWltData(self.wlt, self, self.main)
      if dlg.exec_():
         pass  # Once executed, we're done.

   #############################################################################
   def setWltDetailsFrame(self):
      dispCrypto = self.wlt.useEncryption and (self.usermode == USERMODE.Advanced or \
                                               self.usermode == USERMODE.Expert)
      self.wltID = self.wlt.uniqueIDB58

      if dispCrypto:
         mem = self.wlt.kdf.getMemoryReqtBytes()
         kdfmemstr = str(mem / 1024) + ' kB'
         if mem >= 1024 * 1024:
            kdfmemstr = str(mem / (1024 * 1024)) + ' MB'


      tooltips = [[]] * 10

      tooltips[WLTFIELDS.Name] = self.main.createToolTipWidget(self.tr(
            'This is the name stored with the wallet file.  Click on the '
            '"Change Labels" button on the right side of this '
            'window to change this field'))

      tooltips[WLTFIELDS.Descr] = self.main.createToolTipWidget(self.tr(
            'This is the description of the wallet stored in the wallet file. '
            'Press the "Change Labels" button on the right side of this '
            'window to change this field'))

      tooltips[WLTFIELDS.WltID] = self.main.createToolTipWidget(self.tr(
            'This is a unique identifier for this wallet, based on the root key. '
            'No other wallet can have the same ID '
            'unless it is a copy of this one, regardless of whether '
            'the name and description match.'))

      tooltips[WLTFIELDS.NumAddr] = self.main.createToolTipWidget(self.tr(
            'This is the number of addresses *used* by this wallet so far. '
            'If you recently restored this wallet and you do not see all the '
            'funds you were expecting, click on this field to increase it.'))

      if self.typestr == BDM_OFFLINE:
         tooltips[WLTFIELDS.Secure] = self.main.createToolTipWidget(self.tr(
            'Offline:  This is a "Watching-Only" wallet that you have identified '
            'belongs to you, but you cannot spend any of the wallet funds '
            'using this wallet.  This kind of wallet '
            'is usually stored on an internet-connected computer, to manage '
            'incoming transactions, but the private keys needed '
            'to spend the money are stored on an offline computer.'))
      elif self.typestr == 'Watching-Only':
         tooltips[WLTFIELDS.Secure] = self.main.createToolTipWidget(self.tr(
            'Watching-Only:  You can only watch addresses in this wallet '
            'but cannot spend any of the funds.'))
      elif self.typestr == 'No Encryption':
         tooltips[WLTFIELDS.Secure] = self.main.createToolTipWidget(self.tr(
            'No Encryption: This wallet contains private keys, and does not require '
            'a passphrase to spend funds available to this wallet.  If someone '
            'else obtains a copy of this wallet, they can also spend your funds! '
            '(You can click the "Change Encryption" button on the right side of this '
            'window to enabled encryption)'))
      elif self.typestr == 'Encrypted (AES256)':
         tooltips[WLTFIELDS.Secure] = self.main.createToolTipWidget(self.tr(
            'This wallet contains the private keys needed to spend this wallet\'s '
            'funds, but they are encrypted on your harddrive.  The wallet must be '
            '"unlocked" with the correct passphrase before you can spend any of the '
            'funds.  You can still generate new addresses and monitor incoming '
            'transactions, even with a locked wallet.'))

      tooltips[WLTFIELDS.BelongsTo] = self.main.createToolTipWidget(self.tr(
            'Declare who owns this wallet.  If you click on the field and select '
            '"This wallet is mine", it\'s balance will be included in your total '
            'Armory Balance in the main window'))

      tooltips[WLTFIELDS.Time] = self.main.createToolTipWidget(self.tr(
            'This is exactly how long it takes your computer to unlock your '
            'wallet after you have entered your passphrase.  If someone got '
            'ahold of your wallet, this is approximately how long it would take '
            'them to for each guess of your passphrase.'))

      tooltips[WLTFIELDS.Mem] = self.main.createToolTipWidget(self.tr(
            'This is the amount of memory required to unlock your wallet. '
            'Memory values above 64 kB pretty much guarantee that GPU-acceleration '
            'will be useless for guessing your passphrase'))

      tooltips[WLTFIELDS.Version] = self.main.createToolTipWidget(self.tr(
            'Wallets created with different versions of Armory, may have '
            'different wallet versions.  Not all functionality may be '
            'available with all wallet versions.  Creating a new wallet will '
            'always create the latest version.'))
      labelNames = [[]] * 10
      labelNames[WLTFIELDS.Name] = QLabel(self.tr('Wallet Name:'))
      labelNames[WLTFIELDS.Descr] = QLabel(self.tr('Description:'))

      labelNames[WLTFIELDS.WltID] = QLabel(self.tr('Wallet ID:'))
      labelNames[WLTFIELDS.NumAddr] = QLabel(self.tr('Addresses Used:'))
      labelNames[WLTFIELDS.Secure] = QLabel(self.tr('Security:'))
      labelNames[WLTFIELDS.Version] = QLabel(self.tr('Version:'))

      labelNames[WLTFIELDS.BelongsTo] = QLabel(self.tr('Belongs to:'))


      # TODO:  Add wallet path/location to this!

      if dispCrypto:
         labelNames[WLTFIELDS.Time] = QLabel(self.tr('Unlock Time:'))
         labelNames[WLTFIELDS.Mem] = QLabel(self.tr('Unlock Memory:'))

      self.labelValues = [[]] * 10
      self.labelValues[WLTFIELDS.Name] = QLabel(self.wlt.labelName)
      self.labelValues[WLTFIELDS.Descr] = QLabel(self.wlt.labelDescr)

      self.labelValues[WLTFIELDS.WltID] = QLabel(self.wlt.uniqueIDB58)
      self.labelValues[WLTFIELDS.Secure] = QLabel(self.typestr)
      self.labelValues[WLTFIELDS.BelongsTo] = QLabel('')
      self.labelValues[WLTFIELDS.Version] = QLabel(getVersionString(self.wlt.version))


      topUsed = max(self.wlt.highestUsedChainIndex, 0)
      self.labelValues[WLTFIELDS.NumAddr] = QLabelButton('%d' % topUsed)
      self.labelValues[WLTFIELDS.NumAddr].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      opendlgkeypool = lambda: DlgKeypoolSettings(self.wlt, self, self.main).exec_()
      self.connect(self.labelValues[WLTFIELDS.NumAddr], SIGNAL(CLICKED), opendlgkeypool)

      # Set the owner appropriately
      if self.wlt.watchingOnly:
         if self.main.getWltSetting(self.wltID, 'IsMine'):
            self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton(self.tr('You own this wallet'))
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         else:
            owner = self.main.getWltSetting(self.wltID, 'BelongsTo')
            if owner == '':
               self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton(self.tr('Someone else...'))
               self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            else:
               self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton(owner)
               self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         self.connect(self.labelValues[WLTFIELDS.BelongsTo], SIGNAL(CLICKED), \
                      self.execSetOwner)

      if dispCrypto:
         self.labelValues[WLTFIELDS.Time] = QLabelButton(self.tr('Click to Test'))
         self.labelValues[WLTFIELDS.Mem] = QLabel(kdfmemstr)

      for ttip in tooltips:
         try:
            ttip.setAlignment(Qt.AlignRight | Qt.AlignTop)
            w, h = relaxedSizeStr(ttip, '(?)')
            ttip.setMaximumSize(w, h)
         except AttributeError:
            pass

      for lbl in labelNames:
         try:
            lbl.setTextFormat(Qt.RichText)
            lbl.setText('<b>' + lbl.text() + '</b>')
            lbl.setContentsMargins(0, 0, 0, 0)
            w, h = tightSizeStr(lbl, '9' * 16)
            lbl.setMaximumSize(w, h)
         except AttributeError:
            pass


      for i, lbl in enumerate(self.labelValues):
         if i == WLTFIELDS.BelongsTo:
            lbl.setContentsMargins(10, 0, 10, 0)
            continue
         try:
            lbl.setText('<i>' + lbl.text() + '</i>')
            lbl.setContentsMargins(10, 0, 10, 0)
            # lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                        # Qt.TextSelectableByKeyboard)
         except AttributeError:
            pass

      # Not sure why this has to be connected downhere... it didn't work above it
      if dispCrypto:
         self.labelValues[WLTFIELDS.Time].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         self.connect(self.labelValues[WLTFIELDS.Time], SIGNAL(CLICKED), self.testKdfTime)

      labelNames[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.labelValues[WLTFIELDS.Descr].setWordWrap(True)
      self.labelValues[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)

      lblEmpty = QLabel(' ' * 20)

      layout = QGridLayout()

      layout.addWidget(tooltips[WLTFIELDS.WltID], 0, 0);
      layout.addWidget(labelNames[WLTFIELDS.WltID], 0, 1);
      layout.addWidget(self.labelValues[WLTFIELDS.WltID], 0, 2)

      layout.addWidget(tooltips[WLTFIELDS.Name], 1, 0);
      layout.addWidget(labelNames[WLTFIELDS.Name], 1, 1);
      layout.addWidget(self.labelValues[WLTFIELDS.Name], 1, 2)

      layout.addWidget(tooltips[WLTFIELDS.Descr], 2, 0);
      layout.addWidget(labelNames[WLTFIELDS.Descr], 2, 1);
      layout.addWidget(self.labelValues[WLTFIELDS.Descr], 2, 2, 4, 1)

      layout.addWidget(tooltips[WLTFIELDS.Version], 0, 3);
      layout.addWidget(labelNames[WLTFIELDS.Version], 0, 4);
      layout.addWidget(self.labelValues[WLTFIELDS.Version], 0, 5)

      i = 0
      if self.main.usermode == USERMODE.Expert:
         i += 1
         layout.addWidget(tooltips[WLTFIELDS.NumAddr], i, 3)
         layout.addWidget(labelNames[WLTFIELDS.NumAddr], i, 4)
         layout.addWidget(self.labelValues[WLTFIELDS.NumAddr], i, 5)

      i += 1
      layout.addWidget(tooltips[WLTFIELDS.Secure], i, 3);
      layout.addWidget(labelNames[WLTFIELDS.Secure], i, 4);
      layout.addWidget(self.labelValues[WLTFIELDS.Secure], i, 5)


      if self.wlt.watchingOnly:
         i += 1
         layout.addWidget(tooltips[WLTFIELDS.BelongsTo], i, 3);
         layout.addWidget(labelNames[WLTFIELDS.BelongsTo], i, 4);
         layout.addWidget(self.labelValues[WLTFIELDS.BelongsTo], i, 5)


      if dispCrypto:
         i += 1
         layout.addWidget(tooltips[WLTFIELDS.Time], i, 3);
         layout.addWidget(labelNames[WLTFIELDS.Time], i, 4);
         layout.addWidget(self.labelValues[WLTFIELDS.Time], i, 5)

         i += 1
         layout.addWidget(tooltips[WLTFIELDS.Mem], i, 3);
         layout.addWidget(labelNames[WLTFIELDS.Mem], i, 4);
         layout.addWidget(self.labelValues[WLTFIELDS.Mem], i, 5)


      self.frm = QFrame()
      self.frm.setFrameStyle(STYLE_SUNKEN)
      self.frm.setLayout(layout)



   def testKdfTime(self):
      kdftimestr = "%0.3f sec" % self.wlt.testKdfComputeTime()
      self.labelValues[WLTFIELDS.Time].setText(kdftimestr)


   def execSetOwner(self):
      dlg = self.dlgChangeOwner(self.wltID, self, self.main)
      if dlg.exec_():
         if dlg.chkIsMine.isChecked():
            self.main.setWltSetting(self.wltID, 'IsMine', True)
            self.main.setWltSetting(self.wltID, 'BelongsTo', '')
            self.labelValues[WLTFIELDS.BelongsTo].setText(self.tr('You own this wallet'))
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.labelValues[WLTFIELDS.Secure].setText(self.tr('<i>Offline</i>'))
         else:
            owner = unicode(dlg.edtOwnerString.text())
            self.main.setWltSetting(self.wltID, 'IsMine', False)
            self.main.setWltSetting(self.wltID, 'BelongsTo', owner)

            if len(owner) > 0:
               self.labelValues[WLTFIELDS.BelongsTo].setText(owner)
            else:
               self.labelValues[WLTFIELDS.BelongsTo].setText(self.tr('Someone else'))
            self.labelValues[WLTFIELDS.Secure].setText(self.tr('<i>Watching-Only</i>'))
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.labelValues[WLTFIELDS.Secure].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         self.main.changeWltFilter()


   class dlgChangeOwner(ArmoryDialog):
      def __init__(self, wltID, parent=None, main=None):
         super(parent.dlgChangeOwner, self).__init__(parent, main)


         layout = QGridLayout()
         self.chkIsMine = QCheckBox(self.tr('This wallet is mine'))
         self.edtOwnerString = QLineEdit()
         if parent.main.getWltSetting(wltID, 'IsMine'):
            lblDescr = QLabel(self.tr(
               'The funds in this wallet are currently identified as '
               'belonging to <b><i>you</i></b>.  As such, any funds '
               'available to this wallet will be included in the total '
               'balance displayed on the main screen.  \n\n '
               'If you do not actually own this wallet, or do not wish '
               'for its funds to be considered part of your balance, '
               'uncheck the box below.  Optionally, you can include the '
               'name of the person or organization that does own it.'))
            lblDescr.setWordWrap(True)
            layout.addWidget(lblDescr, 0, 0, 1, 2)
            layout.addWidget(self.chkIsMine, 1, 0)
            self.chkIsMine.setChecked(True)
            self.edtOwnerString.setEnabled(False)
         else:
            owner = parent.main.getWltSetting(wltID, 'BelongsTo')
            if owner == '':
               owner = 'someone else'
            else:
               self.edtOwnerString.setText(owner)
            lblDescr = QLabel(self.tr(
               'The funds in this wallet are currently identified as '
               'belonging to <i><b>%1</b></i>.  If these funds are actually '
               'yours, and you would like the funds included in your balance in '
               'the main window, please check the box below.\n\n').arg(owner))
            lblDescr.setWordWrap(True)
            layout.addWidget(lblDescr, 0, 0, 1, 2)
            layout.addWidget(self.chkIsMine, 1, 0)

            ttip = self.main.createToolTipWidget(self.tr(
               'You might choose this option if you keep a full '
               'wallet on a non-internet-connected computer, and use this '
               'watching-only wallet on this computer to generate addresses '
               'and monitor incoming transactions.'))
            layout.addWidget(ttip, 1, 1)


         slot = lambda b: self.edtOwnerString.setEnabled(not b)
         self.connect(self.chkIsMine, SIGNAL('toggled(bool)'), slot)

         layout.addWidget(QLabel(self.tr('Wallet owner (optional):')), 3, 0)
         layout.addWidget(self.edtOwnerString, 3, 1)
         bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                    QDialogButtonBox.Cancel)
         self.connect(bbox, SIGNAL('accepted()'), self.accept)
         self.connect(bbox, SIGNAL('rejected()'), self.reject)
         layout.addWidget(bbox, 4, 0)
         self.setLayout(layout)
         self.setWindowTitle(self.tr('Set Wallet Owner'))


def showRecvCoinsWarningIfNecessary(wlt, parent, main):

   numTimesOnline = main.getSettingOrSetDefault("SyncSuccessCount", 0)
   if numTimesOnline < 1 and not TheBDM.getState() == BDM_OFFLINE:
      result = QMessageBox.warning(main, main.tr('Careful!'), main.tr(
         'Armory is not online yet, and will eventually need to be online to '
         'access any funds sent to your wallet.  Please <u><b>do not</b></u> '
         'receive Bitcoins to your Armory wallets until you have successfully '
         'gotten online <i>at least one time</i>. '
         '<br><br> '
         'Armory is still beta software, and some users report difficulty '
         'ever getting online. '
         '<br><br> '
         'Do you wish to continue? '), QMessageBox.Cancel | QMessageBox.Ok)
      if not result == QMessageBox.Ok:
         return False

   wlttype = determineWalletType(wlt, main)[0]
   notMyWallet = (wlttype == WLTTYPES.WatchOnly)
   offlineWallet = (wlttype == WLTTYPES.Offline)
   dnaaPropName = 'Wallet_%s_%s' % (wlt.uniqueIDB58, 'DNAA_RecvOther')
   dnaaThisWallet = main.getSettingOrSetDefault(dnaaPropName, False)
   if notMyWallet and not dnaaThisWallet:
      result = MsgBoxWithDNAA(parent, main, MSGBOX.Warning, parent.tr('This is not your wallet!'), parent.tr(
            'You are getting an address for a wallet that '
            'does not appear to belong to you.  Any money sent to this '
            'address will not appear in your total balance, and cannot '
            'be spent from this computer. '
            '<br><br> '
            'If this is actually your wallet (perhaps you maintain the full '
            'wallet on a separate computer), then please change the '
            '"Belongs To" field in the wallet-properties for this wallet.'), \
            parent.tr('Do not show this warning again'), wCancel=True)
      main.writeSetting(dnaaPropName, result[1])
      return result[0]

   if offlineWallet and not dnaaThisWallet:
      result = MsgBoxWithDNAA(parent, main, MSGBOX.Warning, parent.tr('This is not your wallet!'), parent.tr(
            'You are getting an address for a wallet that '
            'you have specified belongs to you, but you cannot actually '
            'spend the funds from this computer.  This is usually the case when '
            'you keep the full wallet on a separate computer for security '
            'purposes.'
            '<br><br>'
            'If this does not sound right, then please do not use the following '
            'address.  Instead, change the wallet properties "Belongs To" field '
            'to specify that this wallet is not actually yours.'), \
            parent.tr('Do not show this warning again'), wCancel=True)
      main.writeSetting(dnaaPropName, result[1])
      return result[0]
   return True



################################################################################
class DlgKeypoolSettings(ArmoryDialog):
   """
   Let the user manually adjust the keypool for this wallet
   """
   def __init__(self, wlt, parent=None, main=None):
      super(DlgKeypoolSettings, self).__init__(parent, main)

      self.wlt = wlt

      self.addressesWereGenerated = False

      self.lblDescr = QRichLabel(self.tr(
         'Armory pre-computes a pool of addresses beyond the last address '
         'you have used, and keeps them in your wallet to "look-ahead."  One '
         'reason it does this is in case you have restored this wallet from '
         'a backup, and Armory does not know how many addresses you have actually '
         'used. '
         '<br><br>'
         'If this wallet was restored from a backup and was very active after '
         'it was backed up, then it is possible Armory did not pre-compute '
         'enough addresses to find your entire balance.  <b>This condition is '
         'rare</b>, but it can happen.  You may extend the keypool manually, '
         'below.'))

      self.lblAddrUsed = QRichLabel(self.tr('Addresses used: '), doWrap=False)
      self.lblAddrComp = QRichLabel(self.tr('Addresses computed: '), doWrap=False)
      self.lblAddrUsedVal = QRichLabel('%d' % max(0, self.wlt.highestUsedChainIndex))
      self.lblAddrCompVal = QRichLabel('%d' % self.wlt.lastComputedChainIndex)

      self.lblNumAddr = QRichLabel(self.tr('Compute this many more addresses: '))
      self.edtNumAddr = QLineEdit()
      self.edtNumAddr.setText('100')
      self.edtNumAddr.setMaximumWidth(relaxedSizeStr(self, '9999999')[0])

      self.lblWarnSpeed = QRichLabel(self.tr(
         'Address computation is very slow.  It may take up to one minute '
         'to compute 200-1000 addresses (system-dependent).  Only generate '
         'as many as you think you need.'))


      buttonBox = QDialogButtonBox()
      self.btnAccept = QPushButton(self.tr("Compute"))
      self.btnReject = QPushButton(self.tr("Done"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.clickCompute)
      self.connect(self.btnReject, SIGNAL(CLICKED), self.reject)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)


      frmLbl = makeVertFrame([self.lblAddrUsed, self.lblAddrComp   ])
      frmVal = makeVertFrame([self.lblAddrUsedVal, self.lblAddrCompVal])
      subFrm1 = makeHorizFrame([STRETCH, frmLbl, frmVal, STRETCH], STYLE_SUNKEN)

      subFrm2 = makeHorizFrame([STRETCH, \
                                self.lblNumAddr, \
                                self.edtNumAddr, \
                                STRETCH], STYLE_SUNKEN)

      layout = QVBoxLayout()
      layout.addWidget(self.lblDescr)
      layout.addWidget(subFrm1)
      layout.addWidget(self.lblWarnSpeed)
      layout.addWidget(subFrm2)
      layout.addWidget(buttonBox)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Extend Address Pool'))

   #############################################################################
   def clickCompute(self):
      # if TheBDM.getState()==BDM_SCANNING:
         # QMessageBox.warning(self, 'Armory is Busy', \
            # 'Armory is in the middle of a scan, and cannot add addresses to '
            # 'any of its wallets until the scan is finished.  Please wait until '
            # 'the dashboard says that Armory is "online."', QMessageBox.Ok)
         # return


      err = False
      try:
         naddr = int(self.edtNumAddr.text())
      except:
         err = True

      if err or naddr < 1:
         QMessageBox.critical(self, self.tr('Invalid input'), self.tr(
            'The value you entered is invalid.  Please enter a positive '
            'number of addresses to generate.'), QMessageBox.Ok)
         return

      if naddr >= 1000:
         confirm = QMessageBox.warning(self, self.tr('Are you sure?'), self.tr(
            'You have entered that you want to compute %1 more addresses'
            'for this wallet.  This operation will take a very long time, '
            'and Armory will become unresponsive until the computation is '
            'finished.  Armory estimates it will take about %2 minutes.'
            '<br><br>Do you want to continue?').arg(naddr, int(naddr / 750.)), \
            QMessageBox.Yes | QMessageBox.No)

         if not confirm == QMessageBox.Yes:
            return

      cred = htmlColor('TextRed')
      self.lblAddrCompVal.setText(self.tr('<font color="%1">Calculating...</font>').arg(cred))

      def doit():
         currPool = self.wlt.lastComputedChainIndex - \
                    self.wlt.highestUsedChainIndex
         fillAddressPoolProgress = DlgProgress(self, self.main, HBar=1, 
                                               Title=self.tr('Computing New Addresses'))
         fillAddressPoolProgress.exec_( \
               self.wlt.fillAddressPool, currPool + naddr,
                                        isActuallyNew=False)

         self.lblAddrCompVal.setText('<font color="%s">%d</font>' % \
                        (cred, self.wlt.lastComputedChainIndex))
         self.addressesWereGenerated = True
         self.main.forceNeedRescan = False

      doit()


class LoadingDisp(ArmoryDialog):
   def __init__(self, parent, main):
      super(LoadingDisp, self).__init__(parent, main)
      layout = QGridLayout()
      self.setLayout(layout)
      self.barLoading = QProgressBar(self)
      self.barLoading.setRange(0,100)
      self.barLoading.setFormat('%p%')
      self.barLoading.setValue(0)
      layout.addWidget(self.barLoading, 0, 0, 1, 1)
      self.setWindowTitle('Loading...')
      self.setFocus()

   def setValue(self, val):
      self.barLoading.setValue(val)

################################################################################
class DlgNewAddressDisp(ArmoryDialog):
   """
   We just generated a new address, let's show it to the user and let them
   a comment to it, if they want.
   """
   def __init__(self, wlt, parent, main, loading=None):
      super(DlgNewAddressDisp, self).__init__(parent, main)

      self.wlt = wlt
      if loading is not None:
         loading.setValue(20)
      self.addr = wlt.getNextUnusedAddress()
      if loading is not None:
         loading.setValue(80)

      self.addrStr = ""
      wlttype = determineWalletType(self.wlt, self.main)[0]
      notMyWallet = (wlttype == WLTTYPES.WatchOnly)

      lblDescr = QLabel(self.tr('The following address can be used to receive bitcoins:'))
      self.edtNewAddr = QLineEdit()
      self.edtNewAddr.setReadOnly(True)
      self.edtNewAddr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      btnClipboard = QPushButton(self.tr('Copy to Clipboard'))
      # lbtnClipboard.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.lblIsCopied = QLabel(self.tr(' or '))
      self.lblIsCopied.setTextFormat(Qt.RichText)
      self.connect(btnClipboard, SIGNAL(CLICKED), self.setClipboard)
      
      def openPaymentRequest():
         msgTxt = str(self.edtComm.toPlainText())
         msgTxt = msgTxt.split('\n')[0][:128]
         addrTxt = str(self.edtNewAddr.text())
         dlg = DlgRequestPayment(self, self.main, addrTxt, msg=msgTxt)
         dlg.exec_()

      btnLink = QPushButton(self.tr('Create Clickable Link'))
      self.connect(btnLink, SIGNAL(CLICKED), openPaymentRequest)


      tooltip1 = self.main.createToolTipWidget(self.tr(
            'You can securely use this address as many times as you want. '
            'However, all people to whom you give this address will '
            'be able to see the number and amount of bitcoins <b>ever</b> '
            'sent to it.  Therefore, using a new address for each transaction '
            'improves overall privacy, but there is no security issues '
            'with reusing any address.'))

      frmNewAddr = QFrame()
      frmNewAddr.setFrameStyle(STYLE_RAISED)
      frmNewAddrLayout = QGridLayout()
      frmNewAddrLayout.addWidget(lblDescr, 0, 0, 1, 2)
      frmNewAddrLayout.addWidget(self.edtNewAddr, 1, 0, 1, 1)
      frmNewAddrLayout.addWidget(tooltip1, 1, 1, 1, 1)

      if not notMyWallet:
         palette = QPalette()
         palette.setColor(QPalette.Base, Colors.TblWltMine)
         boldFont = self.edtNewAddr.font()
         boldFont.setWeight(QFont.Bold)
         self.edtNewAddr.setFont(boldFont)
         self.edtNewAddr.setPalette(palette);
         self.edtNewAddr.setAutoFillBackground(True);

      frmCopy = QFrame()
      frmCopy.setFrameShape(QFrame.NoFrame)
      frmCopyLayout = QHBoxLayout()
      frmCopyLayout.addStretch()
      frmCopyLayout.addWidget(btnClipboard)
      frmCopyLayout.addWidget(self.lblIsCopied)
      frmCopyLayout.addWidget(btnLink)
      frmCopyLayout.addStretch()
      frmCopy.setLayout(frmCopyLayout)

      frmNewAddrLayout.addWidget(frmCopy, 2, 0, 1, 2)
      frmNewAddr.setLayout(frmNewAddrLayout)
            
      lblCommDescr = QLabel(self.tr(
            '(Optional) Add a label to this address, which will '
            'be shown with any relevant transactions in the '
            '"Transactions" tab.'))
      lblCommDescr.setWordWrap(True)
      self.edtComm = QTextEdit()
      tightHeight = tightSizeNChar(self.edtComm, 1)[1]
      self.edtComm.setMaximumHeight(tightHeight * 3.2)

      frmComment = QFrame()
      frmComment.setFrameStyle(STYLE_RAISED)
      frmCommentLayout = QGridLayout()
      frmCommentLayout.addWidget(lblCommDescr, 0, 0, 1, 2)
      frmCommentLayout.addWidget(self.edtComm, 1, 0, 2, 2)
      frmComment.setLayout(frmCommentLayout)


      lblRecvWlt = QRichLabel(self.tr('Bitcoins sent to this address will '
            'appear in the wallet:'), doWrap=False)

      lblRecvWlt.setWordWrap(True)
      lblRecvWlt.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      lblRecvWlt.setMinimumWidth(tightSizeStr(lblRecvWlt, lblRecvWlt.text())[0])

      lblRecvWltID = QLabel(\
            '<b>"%s"</b>  (%s)' % (wlt.labelName, wlt.uniqueIDB58))
      lblRecvWltID.setWordWrap(True)
      lblRecvWltID.setTextFormat(Qt.RichText)
      lblRecvWltID.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      buttonBox = QDialogButtonBox()
      self.btnDone = QPushButton(self.tr("Done"))
      self.connect(self.btnDone, SIGNAL(CLICKED), self.accept)
      buttonBox.addButton(self.btnDone, QDialogButtonBox.AcceptRole)

      frmWlt = QFrame()
      frmWlt.setFrameShape(STYLE_RAISED)
      frmWltLayout = QGridLayout()
      frmWltLayout.addWidget(lblRecvWlt)
      frmWltLayout.addWidget(lblRecvWltID)
      frmWlt.setLayout(frmWltLayout)


      qrdescr = QRichLabel(self.tr('<b>Scan QR code with phone or other barcode reader</b>'
                           '<br><br><font size=2>(Double-click to expand)</font>'))
      qrdescr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.qrcode = QRCodeWidget(self.addrStr, parent=self)
      self.smLabel = QRichLabel('<font size=2>%s</font>' % self.addrStr)
      self.smLabel.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      frmQRsub2 = makeHorizFrame([STRETCH, self.qrcode, STRETCH ])
      frmQRsub3 = makeHorizFrame([STRETCH, self.smLabel, STRETCH ])
      frmQR = makeVertFrame([STRETCH, qrdescr, frmQRsub2, frmQRsub3, STRETCH ], STYLE_SUNKEN)


      def setAddressType(typeStr):
         self.addrType = typeStr
         if typeStr == 'P2PKH':
            self.addrStr = self.wlt.getP2PKHAddrForIndex(self.addr.chainIndex)
         elif typeStr == 'P2SH-P2WPKH':
            self.addrStr = self.wlt.getNestedSWAddrForIndex(self.addr.chainIndex)
         elif typeStr == 'P2SH-P2PK':
            self.addrStr = self.wlt.getNestedP2PKAddrForIndex(self.addr.chainIndex)
            
         self.edtNewAddr.setText(self.addrStr) 
         self.smLabel.setText('<font size=2>%s</font>' % self.addrStr)  
         self.qrcode.setAsciiData(self.addrStr)
         self.qrcode.repaint()       
  
      #addr type selection frame
      from ui.AddressTypeSelectDialog import AddressLabelFrame
      self.addrTypeFrame = AddressLabelFrame(main, setAddressType)
      self.addrType = \
         self.main.getSettingOrSetDefault('Default_ReceiveType', DEFAULT_RECEIVE_TYPE)
      self.addrTypeFrame.setType(self.addrType)
      setAddressType(self.addrType)

      layout = QGridLayout()
      layout.addWidget(frmNewAddr, 0, 0, 1, 1)
      layout.addWidget(self.addrTypeFrame.getFrame(), 2, 0, 1, 1)
      layout.addWidget(frmComment, 4, 0, 1, 1)
      layout.addWidget(frmWlt, 5, 0, 1, 1)
      layout.addWidget(buttonBox, 6, 0, 1, 2)
      layout.addWidget(frmQR, 0, 1, 6, 1)
      if loading is not None:
         loading.reject()
      self.setLayout(layout)
      self.setWindowTitle(self.tr('New Receiving Address'))
      self.setFocus()

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         # Sometimes this is called from a dialog that doesn't have an addr model
         pass


   def acceptNewAddr(self):
      comm = str(self.edtComm.toPlainText())
      if len(comm) > 0:
         self.wlt.setComment(self.addr.getAddr160(), comm)
      
   def accept(self):
      self.acceptNewAddr()
      super(DlgNewAddressDisp, self).accept()

   def reject(self):
      self.acceptNewAddr()
      super(DlgNewAddressDisp, self).reject()

   def setClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.addrStr)
      self.lblIsCopied.setText(self.tr('<i>Copied!</i>'))


#############################################################################
class DlgImportAddress(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgImportAddress, self).__init__(parent, main)

      self.wlt = wlt


      lblImportLbl = QRichLabel(self.tr('Enter:'))

      self.radioImportOne = QRadioButton(self.tr('One Key'))
      self.radioImportMany = QRadioButton(self.tr('Multiple Keys'))
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioImportOne)
      btngrp.addButton(self.radioImportMany)
      btngrp.setExclusive(True)
      self.radioImportOne.setChecked(True)
      self.connect(self.radioImportOne, SIGNAL(CLICKED), self.clickImportCount)
      self.connect(self.radioImportMany, SIGNAL(CLICKED), self.clickImportCount)

      frmTop = makeHorizFrame([lblImportLbl, self.radioImportOne, \
                                             self.radioImportMany, STRETCH])
      self.stackedImport = QStackedWidget()

      # Set up the single-key import widget
      lblDescrOne = QRichLabel(self.tr('The key can either be imported into your wallet, '
                     'or have its available balance "swept" to another address '
                     'in your wallet.  Only import private '
                     'key data if you are absolutely sure that no one else '
                     'has access to it.  Otherwise, sweep it to get '
                     'the funds out of it.  All standard private-key formats '
                     'are supported <i>except for private keys created by '
                     'Bitcoin Core version 0.6.0 and later (compressed)</i>.'))

      lblPrivOne = QRichLabel('Private Key')
      self.edtPrivData = QLineEdit()
      self.edtPrivData.setMinimumWidth(tightSizeStr(self.edtPrivData, 'X' * 60)[0])
      privTooltip = self.main.createToolTipWidget(self.tr(
                       'Supported formats are any hexadecimal or Base58 '
                       'representation of a 32-byte private key (with or '
                       'without checksums), and mini-private-key format '
                       'used on Casascius physical bitcoins.  Private keys '
                       'that use <i>compressed</i> public keys are not yet '
                       'supported by Armory.'))

      frmMid1 = makeHorizFrame([lblPrivOne, self.edtPrivData, privTooltip])
      stkOne = makeVertFrame([HLINE(), lblDescrOne, frmMid1, STRETCH])
      self.stackedImport.addWidget(stkOne)



      # Set up the multi-Sig import widget
      lblDescrMany = QRichLabel(self.tr(
                   'Enter a list of private keys to be "swept" or imported. '
                   'All standard private-key formats are supported.'))
      lblPrivMany = QRichLabel('Private Key List')
      lblPrivMany.setAlignment(Qt.AlignTop)
      ttipPrivMany = self.main.createToolTipWidget(self.tr(
                  'One private key per line, in any standard format. '
                  'Data may be copied directly from the "Export Key Lists" '
                  'dialog (all text on a line preceding '
                  'the key data, separated by a colon, will be ignored).'))
      self.txtPrivBulk = QTextEdit()
      w, h = tightSizeStr(self.edtPrivData, 'X' * 70)
      self.txtPrivBulk.setMinimumWidth(w)
      self.txtPrivBulk.setMinimumHeight(2.2 * h)
      self.txtPrivBulk.setMaximumHeight(4.2 * h)
      frmMid = makeHorizFrame([lblPrivMany, self.txtPrivBulk, ttipPrivMany])
      stkMany = makeVertFrame([HLINE(), lblDescrMany, frmMid])
      self.stackedImport.addWidget(stkMany)


      self.chkUseSP = QCheckBox(self.tr('This is from a backup with SecurePrint\x99'))
      self.edtSecurePrint = QLineEdit()
      self.edtSecurePrint.setFont(GETFONT('Fixed',9))
      self.edtSecurePrint.setEnabled(False)
      w, h = relaxedSizeStr(self.edtSecurePrint, 'X' * 12)
      self.edtSecurePrint.setMaximumWidth(w)

      def toggleSP():
         if self.chkUseSP.isChecked():
            self.edtSecurePrint.setEnabled(True)
         else:
            self.edtSecurePrint.setEnabled(False)

      self.chkUseSP.stateChanged.connect(toggleSP)
      frmSP = makeHorizFrame([self.chkUseSP, self.edtSecurePrint, 'Stretch'])
      #frmSP.setFrameStyle(STYLE_PLAIN)


      # Set up the Import/Sweep select frame
      # # Import option
      self.radioSweep = QRadioButton(self.tr('Sweep any funds owned by these addresses '
                                      'into your wallet\n'
                                      'Select this option if someone else gave you this key'))
      self.radioImport = QRadioButton(self.tr('Import these addresses to your wallet\n'
                                      'Only select this option if you are positive '
                                      'that no one else has access to this key'))


      # # Sweep option (only available when online)
      if TheBDM.getState() == BDM_BLOCKCHAIN_READY:
         self.radioSweep = QRadioButton(self.tr('Sweep any funds owned by this address '
                                         'into your wallet\n'
                                         'Select this option if someone else gave you this key'))
         if self.wlt.watchingOnly:
            self.radioImport.setEnabled(False)
         self.radioSweep.setChecked(True)
      else:
         if TheBDM.getState() in (BDM_OFFLINE, BDM_UNINITIALIZED):
            self.radioSweep = QRadioButton(self.tr('Sweep any funds owned by this address '
                                            'into your wallet\n'
                                            '(Not available in offline mode)'))
         elif TheBDM.getState() == BDM_SCANNING:
            self.radioSweep = QRadioButton(self.tr('Sweep any funds owned by this address into your wallet'))
         self.radioImport.setChecked(True)
         self.radioSweep.setEnabled(False)


      sweepTooltip = self.main.createToolTipWidget(self.tr(
         'You should never add an untrusted key to your wallet.  By choosing this '
         'option, you are only moving the funds into your wallet, but not the key '
         'itself.  You should use this option for Casascius physical bitcoins.'))

      importTooltip = self.main.createToolTipWidget(self.tr(
         'This option will make the key part of your wallet, meaning that it '
         'can be used to securely receive future payments.  <b>Never</b> select this '
         'option for private keys that other people may have access to.'))


      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioSweep)
      btngrp.addButton(self.radioImport)
      btngrp.setExclusive(True)

      frmWarn = QFrame()
      frmWarn.setFrameStyle(QFrame.Box | QFrame.Plain)
      frmWarnLayout = QGridLayout()
      frmWarnLayout.addWidget(self.radioSweep, 0, 0, 1, 1)
      frmWarnLayout.addWidget(self.radioImport, 1, 0, 1, 1)
      frmWarnLayout.addWidget(sweepTooltip, 0, 1, 1, 1)
      frmWarnLayout.addWidget(importTooltip, 1, 1, 1, 1)
      frmWarn.setLayout(frmWarnLayout)



      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.okayClicked)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)





      layout = QVBoxLayout()
      layout.addWidget(frmTop)
      layout.addWidget(self.stackedImport)
      layout.addWidget(frmSP)
      layout.addWidget(frmWarn)
      layout.addWidget(buttonbox)

      self.setWindowTitle(self.tr('Private Key Import'))
      self.setLayout(layout)




   #############################################################################
   def clickImportCount(self):
      isOne = self.radioImportOne.isChecked()
      if isOne:
         self.stackedImport.setCurrentIndex(0)
      else:
         self.stackedImport.setCurrentIndex(1)


   #############################################################################
   def okayClicked(self):
      securePrintCode = None
      if self.chkUseSP.isChecked():
         SECPRINT = HardcodedKeyMaskParams()
         securePrintCode = str(self.edtSecurePrint.text()).strip()
         self.edtSecurePrint.setText("")

         if not checkSecurePrintCode(self, SECPRINT, securePrintCode):
            return

      if self.radioImportOne.isChecked():
         self.processUserString(securePrintCode)
      else:
         self.processMultiSig(securePrintCode)


   #############################################################################
   def processUserString(self, pwd=None):
      theStr = str(self.edtPrivData.text()).strip().replace(' ', '')
      binKeyData, addr160, addrStr = '', '', ''

      try:
         binKeyData, keyType = parsePrivateKeyData(theStr)

         if pwd:
            SECPRINT = HardcodedKeyMaskParams()
            maskKey = SECPRINT['FUNC_KDF'](pwd)
            SBDbinKeyData = SECPRINT['FUNC_UNMASK'](SecureBinaryData(binKeyData), ekey=maskKey)
            binKeyData = SBDbinKeyData.toBinStr()
            SBDbinKeyData.destroy()

         zeroes32 = '\x00'*32
         if binKeyData==zeroes32:
            QMessageBox.critical(self, self.tr('Invalid Private Key'), self.tr(
               'You entered all zeros.  This is not a valid private key!'),
               QMessageBox.Ok)
            LOGERROR('User attempted import of private key 0x00*32')
            return

         if binary_to_int(binKeyData, BIGENDIAN) >= SECP256K1_ORDER:
            QMessageBox.critical(self, self.tr('Invalid Private Key'), self.tr(
               'The private key you have entered is actually not valid '
               'for the elliptic curve used by Bitcoin (secp256k1). '
               'Almost any 64-character hex is a valid private key '
               '<b>except</b> for those greater than: '
               '<br><br>'
               'fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141'
               '<br><br>'
               'Please try a different private key.'), QMessageBox.Ok)
            LOGERROR('User attempted import of invalid private key!')
            return

         addr160 = convertKeyDataToAddress(privKey=binKeyData)
         addrStr = hash160_to_addrStr(addr160)

      except InvalidHashError, e:
         QMessageBox.warning(self, self.tr('Entry Error'), self.tr(
            'The private key data you supplied appears to '
            'contain a consistency check.  This consistency '
            'check failed.  Please verify you entered the '
            'key data correctly.'), QMessageBox.Ok)
         LOGERROR('Private key consistency check failed.')
         return
      except BadInputError, e:
         QMessageBox.critical(self, self.tr('Invalid Data'), self.tr('Something went terribly '
            'wrong!  (key data unrecognized)'), QMessageBox.Ok)
         LOGERROR('Unrecognized key data!')
         return
      except CompressedKeyError, e:
         QMessageBox.critical(self, self.tr('Unsupported key type'), self.tr('You entered a key '
            'for an address that uses a compressed public key, usually produced '
            'in Bitcoin Core/bitcoind wallets created after version 0.6.0.  Armory '
            'does not yet support this key type.'))
         LOGERROR('Compressed key data recognized but not supported')
         return
      except:
         QMessageBox.critical(self, self.tr('Error Processing Key'), self.tr(
            'There was an error processing the private key data. '
            'Please check that you entered it correctly'), QMessageBox.Ok)
         LOGEXCEPT('Error processing the private key data')
         return



      if not 'mini' in keyType.lower():
         reply = QMessageBox.question(self, self.tr('Verify Address'), self.tr(
               'The key data you entered appears to correspond to '
               'the following Bitcoin address:\n\n %1 '
               '\n\nIs this the correct address?').arg(addrStr),
               QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
         if reply == QMessageBox.Cancel:
            return
         else:
            if reply == QMessageBox.No:
               binKeyData = binary_switchEndian(binKeyData)
               addr160 = convertKeyDataToAddress(privKey=binKeyData)
               addrStr = hash160_to_addrStr(addr160)
               reply = QMessageBox.question(self, self.tr('Try Again'), self.tr(
                     'It is possible that the key was supplied in a '
                     '"reversed" form.  When the data you provide is '
                     'reversed, the following address is obtained:\n\n '
                     '%1 \n\nIs this the correct address?').arg(addrStr), \
                     QMessageBox.Yes | QMessageBox.No)
               if reply == QMessageBox.No:
                  binKeyData = ''
                  return

      # Finally, let's add the address to the wallet, or sweep the funds
      if self.radioSweep.isChecked():
         if self.wlt.hasAddr(addr160):
            result = QMessageBox.warning(self, 'Duplicate Address', \
            'The address you are trying to sweep is already part of this '
            'wallet.  You can still sweep it to a new address, but it will '
            'have no effect on your overall balance (in fact, it might be '
            'negative if you have to pay a fee for the transfer)\n\n'
            'Do you still want to sweep this key?', \
            QMessageBox.Yes | QMessageBox.Cancel)
            if not result == QMessageBox.Yes:
               return

         else:
            wltID = self.main.getWalletForAddr160(addr160)
            if not wltID == '':
               addr = self.main.walletMap[wltID].addrMap[addr160]
               typ = 'Imported' if addr.chainIndex == -2 else 'Permanent'
               msg = ('The key you entered is already part of another wallet you '
                      'are maintaining:'
                     '<br><br>'
                     '<b>Address</b>: ' + addrStr + '<br>'
                     '<b>Wallet ID</b>: ' + wltID + '<br>'
                     '<b>Wallet Name</b>: ' + self.main.walletMap[wltID].labelName + '<br>'
                     '<b>Address Type</b>: ' + typ +
                     '<br><br>'
                     'The sweep operation will simply move bitcoins out of the wallet '
                     'above into this wallet.  If the network charges a fee for this '
                     'transaction, you balance will be reduced by that much.')
               result = QMessageBox.warning(self, 'Duplicate Address', msg, \
                     QMessageBox.Ok | QMessageBox.Cancel)
               if not result == QMessageBox.Ok:
                  return

         # Create the address object for the addr to be swept
         sweepAddrList = []
         sweepAddrList.append(PyBtcAddress().createFromPlainKeyData(SecureBinaryData(binKeyData)))
         self.wlt.sweepAddressList(sweepAddrList, self.main)

         # Regardless of the user confirmation, we're done here
         self.accept()

      elif self.radioImport.isChecked():
         if self.wlt.hasAddr(addr160):
            QMessageBox.critical(self, 'Duplicate Address', \
            'The address you are trying to import is already part of your '
            'wallet.  Address cannot be imported', QMessageBox.Ok)
            return

         wltID = self.main.getWalletForAddr160(addr160)
         if not wltID == '':
            addr = self.main.walletMap[wltID].addrMap[addr160]
            typ = 'Imported' if addr.chainIndex == -2 else 'Permanent'
            msg = self.tr('The key you entered is already part of another wallet you own:'
                   '<br><br>'
                   '<b>Address</b>: ' + addrStr + '<br>'
                   '<b>Wallet ID</b>: ' + wltID + '<br>'
                   '<b>Wallet Name</b>: ' + self.main.walletMap[wltID].labelName + '<br>'
                   '<b>Address Type</b>: ' + typ +
                   '<br><br>'
                   'Armory cannot properly display balances or create transactions '
                   'when the same address is in multiple wallets at once.  ')
            if typ == 'Imported':
               QMessageBox.critical(self, 'Duplicate Addresses', \
                  msg + 'To import this address to this wallet, please remove it from the '
                  'other wallet, then try the import operation again.', QMessageBox.Ok)
            else:
               QMessageBox.critical(self, 'Duplicate Addresses', \
                  msg + 'Additionally, this address is mathematically linked '
                  'to its wallet (permanently) and cannot be deleted or '
                  'imported to any other wallet.  The import operation cannot '
                  'continue.', QMessageBox.Ok)
            return

         if self.wlt.useEncryption and self.wlt.isLocked:
            dlg = DlgUnlockWallet(self.wlt, self, self.main, 'Encrypt New Address')
            if not dlg.exec_():
               reply = QMessageBox.critical(self, 'Wallet is locked',
                  'New private key data cannot be imported unless the wallet is '
                  'unlocked.  Please try again when you have the passphrase.', \
                  QMessageBox.Ok)
               return


         self.wlt.importExternalAddressData(privKey=SecureBinaryData(binKeyData))
         self.main.statusBar().showMessage('Successful import of address ' \
                                 + addrStr + ' into wallet ' + self.wlt.uniqueIDB58, 10000)

      try:
         self.parent.wltAddrModel.reset()
      except:
         pass

      self.accept()
      self.main.loadCppWallets()


   #############################################################################
   def processMultiSig(self, pwd=None):
      thisWltID = self.wlt.uniqueIDB58

      inputText = str(self.txtPrivBulk.toPlainText())
      inputLines = [s.strip().replace(' ', '') for s in inputText.split('\n')]
      binKeyData, addr160, addrStr = '', '', ''

      if pwd:
         SECPRINT = HardcodedKeyMaskParams()
         maskKey = SECPRINT['FUNC_KDF'](pwd)

      privKeyList = []
      addrSet = set()
      nLines = 0
      for line in inputLines:
         if 'PublicX' in line or 'PublicY' in line:
            continue
         lineend = line.split(':')[-1]
         try:
            nLines += 1
            binKeyData = SecureBinaryData(parsePrivateKeyData(lineend)[0])
            if pwd: binKeyData = SECPRINT['FUNC_UNMASK'](binKeyData, ekey=maskKey)

            addr160 = convertKeyDataToAddress(privKey=binKeyData.toBinStr())
            if not addr160 in addrSet:
               addrSet.add(addr160)
               addrStr = hash160_to_addrStr(addr160)
               privKeyList.append([addr160, addrStr, binKeyData])
         except:
            LOGWARN('Key line skipped, probably not a private key (key not shown for security)')
            continue

      if len(privKeyList) == 0:
         if nLines > 1:
            QMessageBox.critical(self, 'Invalid Data', \
               'No valid private key data was entered.', QMessageBox.Ok)
         return

      # privKeyList now contains:
      #  [ [A160, AddrStr, Priv],
      #    [A160, AddrStr, Priv],
      #    [A160, AddrStr, Priv], ... ]
      # Determine if any addresses are already part of some wallets
      addr_to_wltID = lambda a: self.main.getWalletForAddr160(a)
      allWltList = [ [addr_to_wltID(k[0]), k[1]] for k in privKeyList]
      # allWltList is now [ [WltID, AddrStr], [WltID, AddrStr], ... ]


      if self.radioSweep.isChecked():
         ##### SWEEPING #####
         dupeWltList = filter(lambda a: len(a[0]) > 0, allWltList)
         if len(dupeWltList) > 0:
            reply = QMessageBox.critical(self, self.tr('Duplicate Addresses!'), self.tr(
               'You are attempting to sweep %1 addresses, but %2 of them '
               'are already part of existing wallets.  That means that some or '
               'all of the bitcoins you sweep may already be owned by you. '
               '<br><br>'
               'Would you like to continue anyway?').arg(len(allWltList), len(dupeWltList)), \
               QMessageBox.Ok | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
               return


         #create address less to sweep
         addrList = []
         for addr160, addrStr, SecurePriv in privKeyList:
            pyAddr = PyBtcAddress().createFromPlainKeyData(SecurePriv)
            addrList.append(pyAddr)

         #get PyBtcWallet object
         self.wlt.sweepAddressList(addrList, self.main)

      else:
         ##### IMPORTING #####

         # allWltList is [ [WltID, AddrStr], [WltID, AddrStr], ... ]

         # Warn about addresses that would be duplicates.
         # Addresses already in the selected wallet will simply be skipped, no
         # need to do anything about that -- only addresses that would appear in
         # two wlts if we were to continue.
         dupeWltList = filter(lambda a: (len(a[0]) > 0 and a[0] != thisWltID), allWltList)
         if len(dupeWltList) > 0:
            dupeAddrStrList = [d[1] for d in dupeWltList]
            dlg = DlgDuplicateAddr(dupeAddrStrList, self, self.main)

            if not dlg.exec_():
               return

            privKeyList = filter(lambda x: (x[1] not in dupeAddrStrList), privKeyList)


         # Confirm import
         addrStrList = [k[1] for k in privKeyList]
         dlg = DlgConfirmBulkImport(addrStrList, thisWltID, self, self.main)
         if not dlg.exec_():
            return

         if self.wlt.useEncryption and self.wlt.isLocked:
            # Target wallet is encrypted...
            unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, self.tr('Unlock Wallet to Import'))
            if not unlockdlg.exec_():
               QMessageBox.critical(self, self.tr('Wallet is Locked'), self.tr(
                  'Cannot import private keys without unlocking wallet!'), \
                  QMessageBox.Ok)
               return


         nTotal = 0
         nImport = 0
         nAlready = 0
         nError = 0
         privKeyToImport = []
         for addr160, addrStr, sbdKey in privKeyList:
            nTotal += 1
            try:
               if not self.main.getWalletForAddr160(addr160) == thisWltID:
                  privKeyToImport.append([sbdKey, addr160])
                  nImport += 1
               else:
                  nAlready += 1
            except Exception, msg:
               # print '***ERROR importing:', addrStr
               # print '         Error Msg:', msg
               # nError += 1
               LOGERROR('Problem importing: %s: %s', addrStr, msg)
               raise

         self.wlt.importExternalAddressBatch(privKeyToImport)

         if nAlready == nTotal:
            MsgBoxCustom(MSGBOX.Warning, self.tr('Nothing Imported!'), self.tr('All addresses '
               'chosen to be imported are already part of this wallet. '
               'Nothing was imported.'))
            return
         elif nImport == 0 and nTotal > 0:
            MsgBoxCustom(MSGBOX.Error, self.tr('Error!'), self.tr(
               'Failed:  No addresses could be imported. '
               'Please check the logfile (ArmoryQt.exe.log) or the console output '
               'for information about why it failed.'))
            return
         else:
            if nError == 0:
               if nAlready > 0:
                  MsgBoxCustom(MSGBOX.Good, self.tr('Success!'), self.tr(
                     'Success: %1 private keys were imported into your wallet. '
                     '<br><br>'
                     'The other %2 private keys were skipped, because they were '
                     'already part of your wallet.').arg(nImport, nAlready))
               else:
                  MsgBoxCustom(MSGBOX.Good, self.tr('Success!'), self.tr(
                     'Success: %1 private keys were imported into your wallet.').arg(nImport))
            else:
               MsgBoxCustom(MSGBOX.Warning, self.tr('Partial Success!'), self.tr(
                  '%1 private keys were imported into your wallet, but there were '
                  'also %2 addresses that could not be imported (see console '
                  'or log file for more information).  It is safe to try this '
                  'operation again: all addresses previously imported will be '
                  'skipped.').arg(nImport, nError))

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         pass

      self.accept()
      self.main.loadCppWallets()
      

#############################################################################
class DlgVerifySweep(ArmoryDialog):
   def __init__(self, inputStr, outputStr, outVal, fee, parent=None, main=None):
      super(DlgVerifySweep, self).__init__(parent, main)


      lblQuestion = QRichLabel(self.tr(
            'You are about to <i>sweep</i> all funds from the specified address '
            'to your wallet.  Please confirm the action:'))


      outStr = coin2str(outVal, maxZeros=2)
      feeStr = ('') if (fee == 0) else (self.tr('(Fee: %1)').arg(coin2str(fee, maxZeros=0)))

      frm = QFrame()
      frm.setFrameStyle(STYLE_RAISED)
      frmLayout = QGridLayout()
      # frmLayout.addWidget(QRichLabel('Funds will be <i>swept</i>...'), 0,0, 1,2)
      frmLayout.addWidget(QRichLabel(self.tr('      From %1').arg(inputStr), doWrap=False), 1, 0, 1, 2)
      frmLayout.addWidget(QRichLabel(self.tr('      To %1').arg(outputStr), doWrap=False), 2, 0, 1, 2)
      frmLayout.addWidget(QRichLabel(self.tr('      Total <b>%1</b> BTC %2').arg(outStr, feeStr), doWrap=False), 3, 0, 1, 2)
      frm.setLayout(frmLayout)

      lblFinalConfirm = QLabel(self.tr('Are you sure you want to execute this transaction?'))

      bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                              QDialogButtonBox.Cancel)
      self.connect(bbox, SIGNAL('accepted()'), self.accept)
      self.connect(bbox, SIGNAL('rejected()'), self.reject)

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      layout = QHBoxLayout()
      layout.addWidget(lblWarnImg)
      layout.addWidget(makeLayoutFrame(VERTICAL, [lblQuestion, frm, lblFinalConfirm, bbox]))
      self.setLayout(layout)

      self.setWindowTitle(self.tr('Confirm Sweep'))




##############################################################################
class DlgConfirmBulkImport(ArmoryDialog):
   def __init__(self, addrList, wltID, parent=None, main=None):
      super(DlgConfirmBulkImport, self).__init__(parent, main)

      self.wltID = wltID

      if len(addrList) == 0:
         QMessageBox.warning(self, self.tr('No Addresses to Import'), self.tr(
           'There are no addresses to import!'), QMessageBox.Ok)
         self.reject()


      walletDescr = self.tr('a new wallet')
      if not wltID == None:
         wlt = self.main.walletMap[wltID]
         walletDescr = self.tr('wallet, <b>%1</b> (%2)').arg(wltID, wlt.labelName)
      lblDescr = QRichLabel(self.tr(
         'You are about to import <b>%1</b> addresses into %2.<br><br> '
         'The following is a list of addresses to be imported:').arg(len(addrList)).arg(walletDescr))

      fnt = GETFONT('Fixed', 10)
      w, h = tightSizeNChar(fnt, 100)
      txtDispAddr = QTextEdit()
      txtDispAddr.setFont(fnt)
      txtDispAddr.setReadOnly(True)
      txtDispAddr.setMinimumWidth(min(w, 700))
      txtDispAddr.setMinimumHeight(16.2 * h)
      txtDispAddr.setText('\n'.join(addrList))

      buttonBox = QDialogButtonBox()
      self.btnAccept = QPushButton(self.tr("Import"))
      self.btnReject = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnReject, SIGNAL(CLICKED), self.reject)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(txtDispAddr)
      dlgLayout.addWidget(buttonBox)
      self.setLayout(dlgLayout)

      self.setWindowTitle(self.tr('Confirm Import'))
      self.setWindowIcon(QIcon(self.main.iconfile))


#############################################################################
class DlgDuplicateAddr(ArmoryDialog):
   def __init__(self, addrList, wlt, parent=None, main=None):
      super(DlgDuplicateAddr, self).__init__(parent, main)

      self.wlt = wlt
      self.doCancel = True
      self.newOnly = False

      if len(addrList) == 0:
         QMessageBox.warning(self, self.tr('No Addresses to Import'), \
           self.tr('There are no addresses to import!'), QMessageBox.Ok)
         self.reject()

      lblDescr = QRichLabel(self.tr(
         '<font color=%1>Duplicate addresses detected!</font> The following '
         'addresses already exist in other Armory wallets:').arg(htmlColor('TextWarn')))

      fnt = GETFONT('Fixed', 8)
      w, h = tightSizeNChar(fnt, 50)
      txtDispAddr = QTextEdit()
      txtDispAddr.setFont(fnt)
      txtDispAddr.setReadOnly(True)
      txtDispAddr.setMinimumWidth(w)
      txtDispAddr.setMinimumHeight(8.2 * h)
      txtDispAddr.setText('\n'.join(addrList))

      lblWarn = QRichLabel(self.tr(
         'Duplicate addresses cannot be imported.  If you continue, '
         'the addresses above will be ignored, and only new addresses '
         'will be imported to this wallet.'))

      buttonBox = QDialogButtonBox()
      self.btnContinue = QPushButton(self.tr("Continue"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnContinue, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox.addButton(self.btnContinue, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(txtDispAddr)
      dlgLayout.addWidget(lblWarn)
      dlgLayout.addWidget(buttonBox)
      self.setLayout(dlgLayout)

      self.setWindowTitle(self.tr('Duplicate Addresses'))




#############################################################################
class DlgAddressInfo(ArmoryDialog):
   def __init__(self, wlt, cppAddr, parent=None, main=None, mode=None):
      super(DlgAddressInfo, self).__init__(parent, main)

      self.wlt = wlt
      self.cppAddr = cppAddr

      self.addr = self.wlt.getAddrByIndex(self.cppAddr.getIndex())
      addr160 = self.cppAddr.getAddrHash()[1:]

      self.ledgerTable = []

      self.mode = mode
      if mode == None:
         if main == None:
            self.mode = USERMODE.Standard
         else:
            self.mode = self.main.usermode


      dlgLayout = QGridLayout()
      addrStr = self.cppAddr.getScrAddr()

      frmInfo = QFrame()
      frmInfo.setFrameStyle(STYLE_RAISED)
      frmInfoLayout = QGridLayout()

      lbls = []

      # Hash160
      if mode in (USERMODE.Advanced, USERMODE.Expert):
         bin25 = base58_to_binary(addrStr)
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(\
                   self.tr('This is the computer-readable form of the address')))
         lbls[-1].append(QRichLabel(self.tr('<b>Public Key Hash</b>')))
         h160Str = binary_to_hex(bin25[1:-4])
         if mode == USERMODE.Expert:
            network = binary_to_hex(bin25[:1    ])
            hash160 = binary_to_hex(bin25[ 1:-4 ])
            addrChk = binary_to_hex(bin25[   -4:])
            h160Str += self.tr('%1 (Network: %2 / Checksum: %3)').arg(hash160, network, addrChk)
         lbls[-1].append(QLabel(h160Str))



      lbls.append([])
      lbls[-1].append(QLabel(''))
      lbls[-1].append(QRichLabel(self.tr('<b>Wallet:</b>')))
      lbls[-1].append(QLabel(self.wlt.labelName))

      lbls.append([])
      lbls[-1].append(QLabel(''))
      lbls[-1].append(QRichLabel(self.tr('<b>Address:</b>')))
      lbls[-1].append(QLabel(addrStr))


      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr(
         'Address type is either <i>Imported</i> or <i>Permanent</i>. '
         '<i>Permanent</i> '
         'addresses are part of the base wallet, and are protected by printed '
         'paper backups, regardless of when the backup was performed. '
         'Imported addresses are only protected by digital backups, or manually '
         'printing the individual keys list, and only if the wallet was backed up '
         '<i>after</i> the keys were imported.')))

      lbls[-1].append(QRichLabel(self.tr('<b>Address Type:</b>')))
      if self.addr.chainIndex == -2:
         lbls[-1].append(QLabel(self.tr('Imported')))
      else:
         lbls[-1].append(QLabel(self.tr('Permanent')))

      # TODO: fix for BIP-32
      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(
            self.tr('The index of this address within the wallet.')))
      lbls[-1].append(QRichLabel(self.tr('<b>Index:</b>')))
      if self.addr.chainIndex > -1:
         lbls[-1].append(QLabel(str(self.addr.chainIndex+1)))
      else:
         lbls[-1].append(QLabel(self.tr("Imported")))


      # Current Balance of address
      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr(
            'This is the current <i>spendable</i> balance of this address, '
            'not including zero-confirmation transactions from others.')))
      lbls[-1].append(QRichLabel(self.tr('<b>Current Balance</b>')))
      try:
         balCoin = self.cppAddr.getSpendableBalance()
         balStr = coin2str(balCoin, maxZeros=1)
         if balCoin > 0:
            goodColor = htmlColor('MoneyPos')
            lbls[-1].append(QRichLabel(\
               '<font color=' + goodColor + '>' + balStr.strip() + '</font> BTC'))
         else:
            lbls[-1].append(QRichLabel(balStr.strip() + ' BTC'))
      except:
         lbls[-1].append(QRichLabel("N/A"))


      lbls.append([])
      lbls[-1].append(QLabel(''))
      lbls[-1].append(QRichLabel(self.tr('<b>Comment:</b>')))
      if self.addr.chainIndex > -1:
         lbls[-1].append(QLabel(str(wlt.commentsMap[addr160]) if addr160 in wlt.commentsMap else ''))
      else:
         lbls[-1].append(QLabel(''))

      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(
            self.tr('The total number of transactions in which this address was involved')))
      lbls[-1].append(QRichLabel(self.tr('<b>Transaction Count:</b>')))
      #lbls[-1].append(QLabel(str(len(txHashes))))
      try:
         txnCount = self.cppAddr.getTxioCount()
         lbls[-1].append(QLabel(str(txnCount)))
      except:
         lbls[-1].append(QLabel("N/A"))


      for i in range(len(lbls)):
         for j in range(1, 3):
            lbls[i][j].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                                Qt.TextSelectableByKeyboard)
         for j in range(3):
            if (i, j) == (0, 2):
               frmInfoLayout.addWidget(lbls[i][j], i, j, 1, 2)
            else:
               frmInfoLayout.addWidget(lbls[i][j], i, j, 1, 1)

      qrcode = QRCodeWidget(addrStr, 80, parent=self)
      qrlbl = QRichLabel(self.tr('<font size=2>Double-click to expand</font>'))
      frmqr = makeVertFrame([qrcode, qrlbl])

      frmInfoLayout.addWidget(frmqr, 0, 4, len(lbls), 1)
      frmInfo.setLayout(frmInfoLayout)
      dlgLayout.addWidget(frmInfo, 0, 0, 1, 1)


      # ## Set up the address ledger
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self.main)
      try:
         self.ledgerModel.setLedgerDelegate(\
            TheBDM.bdv().getLedgerDelegateForScrAddr(self.wlt.uniqueIDB58, \
                                                     self.cppAddr.getAddrHash()))
      except:
         pass

      def ledgerToTableScrAddr(ledger):
         return self.main.convertLedgerToTable(ledger, \
                                               wltIDIn=self.wlt.uniqueIDB58)

      self.ledgerModel.setConvertLedgerMethod(ledgerToTableScrAddr)

      self.frmLedgUpDown = QFrame()
      self.ledgerView = ArmoryTableView(self, self.main, self.frmLedgUpDown)
      self.ledgerView.setModel(self.ledgerModel)
      self.ledgerView.setItemDelegate(LedgerDispDelegate(self))

      self.ledgerView.hideColumn(LEDGERCOLS.isOther)
      self.ledgerView.hideColumn(LEDGERCOLS.UnixTime)
      self.ledgerView.hideColumn(LEDGERCOLS.WltID)
      self.ledgerView.hideColumn(LEDGERCOLS.WltName)
      self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
      self.ledgerView.hideColumn(LEDGERCOLS.isCoinbase)
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
      self.ledgerView.hideColumn(LEDGERCOLS.optInRBF)

      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)
      self.ledgerView.horizontalHeader().setStretchLastSection(True)
      self.ledgerView.verticalHeader().setDefaultSectionSize(20)
      self.ledgerView.verticalHeader().hide()
      self.ledgerView.setMinimumWidth(650)

      dateWidth = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      initialColResize(self.ledgerView, [20, 0, dateWidth, 72, 0, 0.45, 0.3])

      ttipLedger = self.main.createToolTipWidget(self.tr(
            'Unlike the wallet-level ledger, this table shows every '
            'transaction <i>input</i> and <i>output</i> as a separate entry. '
            'Therefore, there may be multiple entries for a single transaction, '
            'which will happen if money was sent-to-self (explicitly, or as '
            'the change-back-to-self address).'))
      lblLedger = QLabel(self.tr('All Address Activity:'))

      lblstrip = makeLayoutFrame(HORIZONTAL, [lblLedger, ttipLedger, STRETCH])
      bottomRow = makeHorizFrame([STRETCH, self.frmLedgUpDown, STRETCH], condenseMargins=True)
      frmLedger = makeLayoutFrame(VERTICAL, [lblstrip, self.ledgerView, bottomRow])
      dlgLayout.addWidget(frmLedger, 1, 0, 1, 1)


      # Now add the right-hand-side option buttons
      lbtnCopyAddr = QLabelButton(self.tr('Copy Address to Clipboard'))
      lbtnViewKeys = QLabelButton(self.tr('View Address Keys'))
      # lbtnSweepA   = QLabelButton('Sweep Address')
      lbtnDelete = QLabelButton(self.tr('Delete Address'))

      self.connect(lbtnCopyAddr, SIGNAL(CLICKED), self.copyAddr)
      self.connect(lbtnViewKeys, SIGNAL(CLICKED), self.viewKeys)
      self.connect(lbtnDelete, SIGNAL(CLICKED), self.deleteAddr)

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)

      hasPriv = self.addr.hasPrivKey()
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Expert))
      watch = self.wlt.watchingOnly


      self.lblCopied = QRichLabel('')
      self.lblCopied.setMinimumHeight(tightSizeNChar(self.lblCopied, 1)[1])

      self.lblLedgerWarning = QRichLabel(self.tr(
         'NOTE:  The ledger shows each transaction <i><b>input</b></i> and '
         '<i><b>output</b></i> for this address.  There are typically many '
         'inputs and outputs for each transaction, therefore the entries '
         'represent only partial transactions.  Do not worry if these entries '
         'do not look familiar.'))


      optLayout = QVBoxLayout()
      if True:           optLayout.addWidget(lbtnCopyAddr)
      if adv:            optLayout.addWidget(lbtnViewKeys)

      if True:           optLayout.addStretch()
      if True:           optLayout.addWidget(self.lblCopied)

      optLayout.addWidget(self.lblLedgerWarning)

      optLayout.addStretch()
      optFrame.setLayout(optLayout)

      rightFrm = makeLayoutFrame(VERTICAL, [QLabel(self.tr('Available Actions:')), optFrame])
      dlgLayout.addWidget(rightFrm, 0, 1, 2, 1)

      btnGoBack = QPushButton(self.tr('<<< Go Back'))
      self.connect(btnGoBack, SIGNAL(CLICKED), self.reject)

      self.setLayout(dlgLayout)
      self.setWindowTitle(self.tr('Address Information'))

      self.ledgerModel.reset()

   def copyAddr(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.cppAddr.getScrAddr())
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.lblCopied.setText(self.tr('<i>Copied!</i>'))

   def makePaper(self):
      pass

   def viewKeys(self):
      if self.wlt.useEncryption and self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'View Private Keys')
         if not unlockdlg.exec_():
            QMessageBox.critical(self, self.tr('Wallet is Locked'), \
               self.tr('Key information will not include the private key data.'), \
               QMessageBox.Ok)

      addr = self.addr.copy()
      dlg = DlgShowKeys(addr, self.wlt, self, self.main)
      dlg.exec_()

   def deleteAddr(self):
      pass

#############################################################################
class DlgShowKeys(ArmoryDialog):

   def __init__(self, addr, wlt, parent=None, main=None):
      super(DlgShowKeys, self).__init__(parent, main)

      self.addr = addr
      self.wlt = wlt
      
      self.scrAddr = \
         self.wlt.cppWallet.getAddrObjByIndex(self.addr.chainIndex).getScrAddr() 


      lblWarn = QRichLabel('')
      plainPriv = False
      if addr.binPrivKey32_Plain.getSize() > 0:
         plainPriv = True
         lblWarn = QRichLabel(self.tr(
            '<font color=%1><b>Warning:</b> the unencrypted private keys '
            'for this address are shown below.  They are "private" because '
            'anyone who obtains them can spend the money held '
            'by this address.  Please protect this information the '
            'same as you protect your wallet.</font>').arg(htmlColor('TextWarn')))
      warnFrm = makeLayoutFrame(HORIZONTAL, [lblWarn])

      endianness = self.main.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = 'BE' if endianness == BIGENDIAN else 'LE'
      def formatBinData(binStr, endian=LITTLEENDIAN):
         binHex = binary_to_hex(binStr)
         if endian != LITTLEENDIAN:
            binHex = hex_switchEndian(binHex)
         binHexPieces = [binHex[i:i + 8] for i in range(0, len(binHex), 8)]
         return ' '.join(binHexPieces)


      lblDescr = QRichLabel(self.tr('Key Data for address: <b>%1</b>').arg(self.scrAddr))

      lbls = []

      lbls.append([])
      binKey = self.addr.binPrivKey32_Plain.toBinStr()
      lbls[-1].append(self.main.createToolTipWidget(self.tr(
            'The raw form of the private key for this address.  It is '
            '32-bytes of randomly generated data')))
      lbls[-1].append(QRichLabel(self.tr('Private Key (hex,%1):').arg(estr)))
      if not addr.hasPrivKey():
         lbls[-1].append(QRichLabel(self.tr('<i>[[ No Private Key in Watching-Only Wallet ]]</i>')))
      elif plainPriv:
         lbls[-1].append(QLabel(formatBinData(binKey)))
      else:
         lbls[-1].append(QRichLabel(self.tr('<i>[[ ENCRYPTED ]]</i>')))

      if plainPriv:
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(self.tr(
               'This is a more compact form of the private key, and includes '
               'a checksum for error detection.')))
         lbls[-1].append(QRichLabel(self.tr('Private Key (Base58):')))
         b58Key = encodePrivKeyBase58(binKey)
         lbls[-1].append(QLabel(' '.join([b58Key[i:i + 6] for i in range(0, len(b58Key), 6)])))



      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr(
               'The raw public key data.  This is the X-coordinate of '
               'the Elliptic-curve public key point.')))
      lbls[-1].append(QRichLabel(self.tr('Public Key X (%1):').arg(estr)))
      lbls[-1].append(QRichLabel(formatBinData(self.addr.binPublicKey65.toBinStr()[1:1 + 32])))


      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr(
               'The raw public key data.  This is the Y-coordinate of '
               'the Elliptic-curve public key point.')))
      lbls[-1].append(QRichLabel(self.tr('Public Key Y (%1):').arg(estr)))
      lbls[-1].append(QRichLabel(formatBinData(self.addr.binPublicKey65.toBinStr()[1 + 32:1 + 32 + 32])))


      bin25 = base58_to_binary(self.scrAddr)
      network = binary_to_hex(bin25[:1    ])
      hash160 = binary_to_hex(bin25[ 1:-4 ])
      addrChk = binary_to_hex(bin25[   -4:])
      h160Str = self.tr('%1 (Network: %2 / Checksum: %3)').arg(hash160, network, addrChk)

      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(\
               self.tr('This is the hexadecimal version if the address string')))
      lbls[-1].append(QRichLabel(self.tr('Public Key Hash:')))
      lbls[-1].append(QLabel(h160Str))

      frmKeyData = QFrame()
      frmKeyData.setFrameStyle(STYLE_RAISED)
      frmKeyDataLayout = QGridLayout()


      # Now set the label properties and jam them into an information frame
      for row, lbl3 in enumerate(lbls):
         lbl3[1].setFont(GETFONT('Var'))
         lbl3[2].setFont(GETFONT('Fixed'))
         lbl3[2].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                         Qt.TextSelectableByKeyboard)
         lbl3[2].setWordWrap(False)

         for j in range(3):
            frmKeyDataLayout.addWidget(lbl3[j], row, j)


      frmKeyData.setLayout(frmKeyDataLayout)

      bbox = QDialogButtonBox(QDialogButtonBox.Ok)
      self.connect(bbox, SIGNAL('accepted()'), self.accept)


      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblWarn)
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(frmKeyData)
      dlgLayout.addWidget(bbox)


      self.setLayout(dlgLayout)
      self.setWindowTitle(self.tr('Address Key Information'))

#############################################################################
class DlgEULA(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgEULA, self).__init__(parent, main)

      txtWidth, txtHeight = tightSizeNChar(self, 110)
      txtLicense = QTextEdit()
      txtLicense.sizeHint = lambda: QSize(txtWidth, 14 * txtHeight)
      txtLicense.setReadOnly(True)
      txtLicense.setCurrentFont(GETFONT('Fixed', 8))

      from LICENSE import licenseText
      txtLicense.setText(licenseText())

      self.chkAgree = QCheckBox(self.tr('I agree to all the terms of the license above'))

      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.btnAccept = QPushButton(self.tr("Accept"))
      self.btnAccept.setEnabled(False)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(self.chkAgree, SIGNAL('toggled(bool)'), self.toggleChkBox)
      btnBox = makeHorizFrame([STRETCH, self.btnCancel, self.btnAccept])


      lblPleaseAgree = QRichLabel(self.tr(
         '<b>Armory Bitcoin Client is licensed in part under the '
         '<i>Affero General Public License, Version 3 (AGPLv3)</i> '
         'and in part under the <i>MIT License</i></b> '
         '<br><br>'
         'Additionally, as a condition of receiving this software '
         'for free, you accept all risks associated with using it '
         'and the developers of Armory will not be held liable for any '
         'loss of money or bitcoins due to software defects. '
         '<br><br>'
         '<b>Please read the full terms of the license and indicate your '
         'agreement with its terms.</b>'))


      dlgLayout = QVBoxLayout()
      frmChk = makeHorizFrame([self.chkAgree, STRETCH])
      frmBtn = makeHorizFrame([STRETCH, self.btnCancel, self.btnAccept])
      frmAll = makeVertFrame([lblPleaseAgree, txtLicense, frmChk, frmBtn])

      dlgLayout.addWidget(frmAll)
      self.setLayout(dlgLayout)
      self.setWindowTitle(self.tr('Armory License Agreement'))
      self.setWindowIcon(QIcon(self.main.iconfile))


   def reject(self):
      self.main.abortLoad = True
      LOGERROR('User did not accept the EULA')
      super(DlgEULA, self).reject()

   def accept(self):
      self.main.writeSetting('Agreed_to_EULA', True)
      super(DlgEULA, self).accept()

   def toggleChkBox(self, isEnabled):
      self.btnAccept.setEnabled(isEnabled)

#############################################################################
class DlgIntroMessage(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgIntroMessage, self).__init__(parent, main)


      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap(':/MsgBox_info48.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      lblInfoImg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lblInfoImg.setMaximumWidth(50)

      lblWelcome = QRichLabel(self.tr('<b>Welcome to Armory!</b>'))
      lblWelcome.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWelcome.setFont(GETFONT('Var', 14))
      lblSlogan = QRichLabel(self.tr('<i>The most advanced Bitcoin Client on Earth!</i>'))
      lblSlogan.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblDescr = QRichLabel(self.tr(
         '<b>You are about to use the most secure and feature-rich Bitcoin client '
         'software available!</b>  But please remember, this software '
         'is still <i>Beta</i> - Armory developers will not be held responsible '
         'for loss of bitcoins resulting from the use of this software!'
         '<br><br>'))
      lblDescr.setOpenExternalLinks(True)

      spacer = lambda: QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)


      frmText = makeLayoutFrame(VERTICAL, [lblWelcome, spacer(), lblDescr])



      self.chkDnaaIntroDlg = QCheckBox(self.tr('Do not show this window again'))

      self.requestCreate = False
      self.requestImport = False
      buttonBox = QDialogButtonBox()
      frmIcon = makeLayoutFrame(VERTICAL, [lblInfoImg, STRETCH])
      frmIcon.setMaximumWidth(60)
      if len(self.main.walletMap) == 0:
         self.btnCreate = QPushButton(self.tr("Create Your First Wallet!"))
         self.btnImport = QPushButton(self.tr("Import Existing Wallet"))
         self.btnCancel = QPushButton(self.tr("Skip"))
         self.connect(self.btnCreate, SIGNAL(CLICKED), self.createClicked)
         self.connect(self.btnImport, SIGNAL(CLICKED), self.importClicked)
         self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
         buttonBox.addButton(self.btnCreate, QDialogButtonBox.AcceptRole)
         buttonBox.addButton(self.btnImport, QDialogButtonBox.AcceptRole)
         buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
         self.chkDnaaIntroDlg.setVisible(False)
         frmBtn = makeLayoutFrame(HORIZONTAL, [self.chkDnaaIntroDlg, \
                                            self.btnCancel, \
                                            STRETCH, \
                                            self.btnImport, \
                                            self.btnCreate])
      else:
         self.btnOkay = QPushButton(self.tr("OK!"))
         self.connect(self.btnOkay, SIGNAL(CLICKED), self.accept)
         buttonBox.addButton(self.btnOkay, QDialogButtonBox.AcceptRole)
         frmBtn = makeLayoutFrame(HORIZONTAL, [self.chkDnaaIntroDlg, \
                                            STRETCH, \
                                            self.btnOkay])



      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmIcon, 0, 0, 1, 1)
      dlgLayout.addWidget(frmText, 0, 1, 1, 1)
      dlgLayout.addWidget(frmBtn, 1, 0, 1, 2)

      self.setLayout(dlgLayout)
      self.setWindowTitle(self.tr('Greetings!'))
      self.setWindowIcon(QIcon(self.main.iconfile))
      self.setMinimumWidth(750)


   def createClicked(self):
      self.requestCreate = True
      self.accept()

   def importClicked(self):
      self.requestImport = True
      self.accept()

   def sizeHint(self):
      return QSize(750, 500)




#############################################################################
class DlgImportPaperWallet(ArmoryDialog):

   def __init__(self, parent=None, main=None):
      super(DlgImportPaperWallet, self).__init__(parent, main)

      self.wltDataLines = [[]] * 4
      self.prevChars = [''] * 4

      for i, edt in enumerate(self.lineEdits):
         # I screwed up the ref/copy, this loop only connected the last one...
         # theSlot = lambda: self.autoSpacerFunction(i)
         # self.connect(edt, SIGNAL('textChanged(QString)'), theSlot)
         edt.setMinimumWidth(tightSizeNChar(edt, 50)[0])

      # Just do it manually because it's guaranteed to work!
      slot = lambda: self.autoSpacerFunction(0)
      self.connect(self.lineEdits[0], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(1)
      self.connect(self.lineEdits[1], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(2)
      self.connect(self.lineEdits[2], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(3)
      self.connect(self.lineEdits[3], SIGNAL('textEdited(QString)'), slot)

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.verifyUserInput)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      self.labels = [QLabel() for i in range(4)]
      self.labels[0].setText(self.tr('Root Key:'))
      self.labels[1].setText('')
      self.labels[2].setText(self.tr('Chain Code:'))
      self.labels[3].setText('')

      lblDescr1 = QLabel(self.tr(
          'Enter the characters exactly as they are printed on the '
          'paper-backup page.  Alternatively, you can scan the QR '
          'code from another application, then copy&paste into the '
          'entry boxes below.'))
      lblDescr2 = QLabel(self.tr(
          'The data can be entered <i>with</i> or <i>without</i> '
          'spaces, and up to '
          'one character per line will be corrected automatically.'))
      for lbl in (lblDescr1, lblDescr2):
         lbl.setTextFormat(Qt.RichText)
         lbl.setWordWrap(True)

      layout = QGridLayout()
      layout.addWidget(lblDescr1, 0, 0, 1, 2)
      layout.addWidget(lblDescr2, 1, 0, 1, 2)
      for i, edt in enumerate(self.lineEdits):
         layout.addWidget(self.labels[i], i + 2, 0)
         layout.addWidget(self.lineEdits[i], i + 2, 1)

      self.chkEncrypt = QCheckBox(self.tr('Encrypt Wallet'))
      self.chkEncrypt.setChecked(True)

      bottomFrm = makeHorizFrame([self.chkEncrypt, buttonbox])
      layout.addWidget(bottomFrm, 6, 0, 1, 2)
      layout.setVerticalSpacing(10)
      self.setLayout(layout)


      self.setWindowTitle(self.tr('Recover Wallet from Paper Backup'))
      self.setWindowIcon(QIcon(self.main.iconfile))


   def autoSpacerFunction(self, i):
      currStr = str(self.lineEdits[i].text())
      rawStr = currStr.replace(' ', '')
      if len(rawStr) > 36:
         rawStr = rawStr[:36]

      if len(rawStr) == 36:
         quads = [rawStr[j:j + 4] for j in range(0, 36, 4)]
         self.lineEdits[i].setText(' '.join(quads))


   def verifyUserInput(self):
      def englishNumberList(nums):
         nums = map(str, nums)
         if len(nums) == 1:
            return nums[0]
         return ', '.join(nums[:-1]) + ' and ' + nums[-1]

      errorLines = []
      for i in range(4):
         hasError = False
         try:
            data, err = readSixteenEasyBytes(str(self.lineEdits[i].text()))
         except (KeyError, TypeError):
            data, err = ('', 'Exception')

         if data == '':
            reply = QMessageBox.critical(self, self.tr('Verify Wallet ID'), self.tr(
               'There is an error on line %1 of the data you '
               'entered, which could not be fixed automatically.  Please '
               'double-check that you entered the text exactly as it appears '
               'on the wallet-backup page.').arg(i + 1),
               QMessageBox.Ok)
            LOGERROR('Error in wallet restore field')
            self.labels[i].setText('<font color="red">' + str(self.labels[i].text()) + '</font>')
            return
         if err == 'Fixed_1' or err == 'No_Checksum':
            errorLines += [i + 1]

         self.wltDataLines[i] = data

      if errorLines:
         pluralChar = '' if len(errorLines) == 1 else 's'
         article = ' an' if len(errorLines) == 1 else ''
         QMessageBox.question(self, self.tr('Errors Corrected!'), self.tr(
            'Detected %n error(s) on line(s) %1 '
            'in the data you entered.  Armory attempted to fix the '
            'error(s) but it is not always right.  Be sure '
            'to verify the "Wallet Unique ID" closely on the next window.', "", len(errorLines)).arg(
               englishNumberList(errorLines)), QMessageBox.Ok)

      # If we got here, the data is valid, let's create the wallet and accept the dlg
      privKey = ''.join(self.wltDataLines[:2])
      chain = ''.join(self.wltDataLines[2:])

      root = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(privKey))
      root.chaincode = SecureBinaryData(chain)
      first = root.extendAddressChain()
      newWltID = binary_to_base58((ADDRBYTE + first.getAddr160()[:5])[::-1])

      if self.main.walletMap.has_key(newWltID):
         QMessageBox.question(self, self.tr('Duplicate Wallet!'), self.tr(
               'The data you entered is for a wallet with a ID: \n\n %1 '
               '\n\nYou already own this wallet! \n  '
               'Nothing to do...').arg(newWltID), QMessageBox.Ok)
         self.reject()
         return



      reply = QMessageBox.question(self, self.tr('Verify Wallet ID'), self.tr(
               'The data you entered corresponds to a wallet with a wallet ID: \n\n '
               '%1 \n\nDoes this ID match the "Wallet Unique ID" '
               'printed on your paper backup?  If not, click "No" and reenter '
               'key and chain-code data again.').arg(newWltID), \
               QMessageBox.Yes | QMessageBox.No)
      if reply == QMessageBox.No:
         return

      passwd = []
      if self.chkEncrypt.isChecked():
         dlgPasswd = DlgChangePassphrase(self, self.main)
         if dlgPasswd.exec_():
            passwd = SecureBinaryData(str(dlgPasswd.edtPasswd1.text()))
         else:
            QMessageBox.critical(self, self.tr('Cannot Encrypt'), self.tr(
               'You requested your restored wallet be encrypted, but no '
               'valid passphrase was supplied.  Aborting wallet recovery.'), \
               QMessageBox.Ok)
            return

      if passwd:
         self.newWallet = PyBtcWallet().createNewWallet(\
                                 plainRootKey=SecureBinaryData(privKey), \
                                 chaincode=SecureBinaryData(chain), \
                                 shortLabel=self.tr('PaperBackup - %1').arg(newWltID), \
                                 withEncrypt=True, \
                                 securePassphrase=passwd, \
                                 kdfTargSec=0.25, \
                                 kdfMaxMem=32 * 1024 * 1024, \
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)
      else:
         self.newWallet = PyBtcWallet().createNewWallet(\
                                 plainRootKey=SecureBinaryData(privKey), \
                                 chaincode=SecureBinaryData(chain), \
                                 shortLabel=self.tr('PaperBackup - %1').arg(newWltID), \
                                 withEncrypt=False, \
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)

      def fillAddrPoolAndAccept():
         progressBar = DlgProgress(self, self.main, None, HBar=1,
                                   Title=self.tr("Computing New Addresses"))
         progressBar.exec_(self.newWallet.fillAddressPool)
         self.accept()

      # Will pop up a little "please wait..." window while filling addr pool
      DlgExecLongProcess(fillAddrPoolAndAccept, self.tr("Recovering wallet..."), self, self.main).exec_()




################################################################################
class DlgSetComment(ArmoryDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, parent, main, currcomment='', clbl = QObject().tr("Add comment"),
                                                               maxChars=MAX_COMMENT_LENGTH):
      super(DlgSetComment, self).__init__(parent, main)


      self.setWindowTitle(self.tr('Modify Comment'))
      self.setWindowIcon(QIcon(self.main.iconfile))

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      lbl = QLabel('%s' % clbl)
      self.edtComment = QLineEdit()
      self.edtComment.setText(currcomment[:maxChars])
      h, w = relaxedSizeNChar(self, 50)
      self.edtComment.setMinimumSize(h, w)
      self.edtComment.setMaxLength(maxChars)
      layout.addWidget(lbl, 0, 0)
      layout.addWidget(self.edtComment, 1, 0)
      layout.addWidget(buttonbox, 2, 0)
      self.setLayout(layout)

   #############################################################################
   def accept(self):
      if not isASCII(unicode(self.edtComment.text())):
         UnicodeErrorBox(self)
         return
      else:
         super(DlgSetComment, self).accept()




################################################################################
class DlgRemoveWallet(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgRemoveWallet, self).__init__(parent, main)

      wltID = wlt.uniqueIDB58
      wltName = wlt.labelName
      wltDescr = wlt.labelDescr
      lblWarning = QLabel(self.tr('<b>!!! WARNING !!!</b>\n\n'))
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lblWarning2 = QLabel(self.tr('<i>You have requested that the following wallet '
                            'be removed from Armory:</i>'))
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setWordWrap(True)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lbls = []
      lbls.append([])
      lbls[0].append(QLabel(self.tr('Wallet Unique ID:')))
      lbls[0].append(QLabel(wltID))
      lbls.append([])
      lbls[1].append(QLabel(self.tr('Wallet Name:')))
      lbls[1].append(QLabel(wlt.labelName))
      lbls.append([])
      lbls[2].append(QLabel(self.tr('Description:')))
      lbls[2].append(QLabel(wlt.labelDescr))
      lbls[2][-1].setWordWrap(True)


      # TODO:  This should not *ever* require a blockchain scan, because all
      #        current wallets should already be registered and up-to-date.
      #        But I should verify that this is actually the case.
      wltEmpty = True
      if TheBDM.getState() == BDM_BLOCKCHAIN_READY:
         # Removed this line of code because it's part of the old BDM paradigm.
         # Leaving this comment here in case it needs to be replaced by anything
         # wlt.syncWithBlockchainLite()
         bal = wlt.getBalance('Full')
         lbls.append([])
         lbls[3].append(QLabel(self.tr('Current Balance (w/ unconfirmed):')))
         if bal > 0:
            lbls[3].append(QLabel('<font color="red"><b>' + coin2str(bal, maxZeros=1).strip() + ' BTC</b></font>'))
            lbls[3][-1].setTextFormat(Qt.RichText)
            wltEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      # Add the warning text and images to the top of the dialog
      layout = QGridLayout()
      layout.addWidget(lblWarning, 0, 1, 1, 1)
      layout.addWidget(lblWarning2, 1, 1, 1, 1)
      layout.addWidget(lblWarnImg, 0, 0, 2, 1)
      layout.addWidget(lblWarnImg2, 0, 2, 2, 1)

      frmInfo = QFrame()
      frmInfo.setFrameStyle(QFrame.Box | QFrame.Plain)
      frmInfo.setLineWidth(3)
      frmInfoLayout = QGridLayout()
      for i in range(len(lbls)):
         lbls[i][0].setText('<b>' + lbls[i][0].text() + '</b>')
         lbls[i][0].setTextFormat(Qt.RichText)
         frmInfoLayout.addWidget(lbls[i][0], i, 0)
         frmInfoLayout.addWidget(lbls[i][1], i, 1, 1, 2)

      frmInfo.setLayout(frmInfoLayout)
      layout.addWidget(frmInfo, 2, 0, 2, 3)
      hasWarningRow = False
      if not wlt.watchingOnly:
         if not wltEmpty:
            lbl = QRichLabel(self.tr('<b>WALLET IS NOT EMPTY.  Only delete this wallet if you '
                             'have a backup on paper or saved to a another location '
                             'outside your settings directory.</b>'))
            hasWarningRow = True
         elif wlt.isWltSigningAnyLockbox(self.main.allLockboxes):
            lbl = QRichLabel(self.tr('<b>WALLET IS PART OF A LOCKBOX.  Only delete this wallet if you '
                             'have a backup on paper or saved to a another location '
                             'outside your settings directory.</b>'))
            hasWarningRow = True
         if hasWarningRow:
            lbls.append(lbl)
            layout.addWidget(lbl, 4, 0, 1, 3)

      self.radioDelete = QRadioButton(self.tr('Permanently delete this wallet'))
      self.radioWatch = QRadioButton(self.tr('Delete private keys only, make watching-only'))

      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioDelete)
      if not self.main.usermode == USERMODE.Standard:
         btngrp.addButton(self.radioWatch)
      btngrp.setExclusive(True)

      ttipDelete = self.main.createToolTipWidget(self.tr(
         'This will delete the wallet file, removing '
         'all its private keys from your settings directory. '
         'If you intend to keep using addresses from this '
         'wallet, do not select this option unless the wallet '
         'is backed up elsewhere.'))
      ttipWatch = self.main.createToolTipWidget(self.tr(
         'This will delete the private keys from your wallet, '
         'leaving you with a watching-only wallet, which can be '
         'used to generate addresses and monitor incoming '
         'payments.  This option would be used if you created '
         'the wallet on this computer <i>in order to transfer '
         'it to a different computer or device and want to '
         'remove the private data from this system for security.</i>'))


      self.chkPrintBackup = QCheckBox(self.tr(
         'Print a paper backup of this wallet before deleting'))

      if wlt.watchingOnly:
         ttipDelete = self.main.createToolTipWidget(self.tr(
            'This will delete the wallet file from your system. '
            'Since this is a watching-only wallet, no private keys '
            'will be deleted.'))
         ttipWatch = self.main.createToolTipWidget(self.tr(
            'This wallet is already a watching-only wallet so this option '
            'is pointless'))
         self.radioWatch.setEnabled(False)
         self.chkPrintBackup.setEnabled(False)


      self.frm = []

      rdoFrm = QFrame()
      rdoFrm.setFrameStyle(STYLE_RAISED)
      rdoLayout = QGridLayout()

      startRow = 0
      for rdo, ttip in [(self.radioDelete, ttipDelete), \
                       (self.radioWatch, ttipWatch)]:
         self.frm.append(QFrame())
         # self.frm[-1].setFrameStyle(STYLE_SUNKEN)
         self.frm[-1].setFrameStyle(QFrame.NoFrame)
         frmLayout = QHBoxLayout()
         frmLayout.addWidget(rdo)
         ttip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         frmLayout.addWidget(ttip)
         frmLayout.addStretch()
         self.frm[-1].setLayout(frmLayout)
         rdoLayout.addWidget(self.frm[-1], startRow, 0, 1, 3)
         startRow += 1


      self.radioDelete.setChecked(True)
      rdoFrm.setLayout(rdoLayout)

      startRow = 6 if not hasWarningRow else 5
      layout.addWidget(rdoFrm, startRow, 0, 1, 3)

      if wlt.watchingOnly:
         self.frm[-1].setVisible(False)


      printTtip = self.main.createToolTipWidget(self.tr(
         'If this box is checked, you will have the ability to print off an '
         'unencrypted version of your wallet before it is deleted.  <b>If '
         'printing is unsuccessful, please press *CANCEL* on the print dialog '
         'to prevent the delete operation from continuing</b>'))
      printFrm = makeLayoutFrame(HORIZONTAL, [self.chkPrintBackup, \
                                              printTtip, \
                                              'Stretch'])
      startRow += 1
      layout.addWidget(printFrm, startRow, 0, 1, 3)

      if wlt.watchingOnly:
         printFrm.setVisible(False)


      rmWalletSlot = lambda: self.removeWallet(wlt)

      startRow += 1
      self.btnDelete = QPushButton(self.tr("Delete"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnDelete, SIGNAL(CLICKED), rmWalletSlot)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnDelete, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      layout.addWidget(buttonBox, startRow, 0, 1, 3)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Delete Wallet Options'))


   def removeWallet(self, wlt):

      # Open the print dialog.  If they hit cancel at any time, then
      # we go back to the primary wallet-remove dialog without any other action
      if self.chkPrintBackup.isChecked():
         if not OpenPaperBackupWindow('Single', self, self.main, wlt, \
                                                self.tr('Unlock Paper Backup')):
            QMessageBox.warning(self, self.tr('Operation Aborted'), self.tr(
              'You requested a paper backup before deleting the wallet, but '
              'clicked "Cancel" on the backup printing window.  So, the delete '
              'operation was canceled as well.'), QMessageBox.Ok)
            return


      # If they only want to exclude the wallet, we will add it to the excluded
      # list and remove it from the application.  The wallet files will remain
      # in the settings directory but will be ignored by Armory

      wltID = wlt.uniqueIDB58
      if wlt.watchingOnly:
         reply = QMessageBox.warning(self, self.tr('Confirm Delete'), \
         self.tr('You are about to delete a watching-only wallet.  Are you sure '
         'you want to do this?'), QMessageBox.Yes | QMessageBox.Cancel)
      elif self.radioDelete.isChecked():
         reply = QMessageBox.warning(self, self.tr('Are you absolutely sure?!?'), \
         self.tr('Are you absolutely sure you want to permanently delete '
         'this wallet?  Unless this wallet is saved on another device '
         'you will permanently lose access to all the addresses in this '
         'wallet.'), QMessageBox.Yes | QMessageBox.Cancel)
      elif self.radioWatch.isChecked():
         reply = QMessageBox.warning(self, self.tr('Are you absolutely sure?!?'), \
         self.tr('<i>This will permanently delete the information you need to spend '
         'funds from this wallet!</i>  You will only be able to receive '
         'coins, but not spend them.  Only do this if you have another copy '
         'of this wallet elsewhere, such as a paper backup or on an offline '
         'computer with the full wallet.'), QMessageBox.Yes | QMessageBox.Cancel)

      if reply == QMessageBox.Yes:

         thepath = wlt.getWalletPath()
         thepathBackup = wlt.getWalletPath('backup')

         if self.radioWatch.isChecked():
            LOGINFO('***Converting to watching-only wallet')
            newWltPath = wlt.getWalletPath('WatchOnly')
            wlt.forkOnlineWallet(newWltPath, wlt.labelName, wlt.labelDescr)
            self.main.removeWalletFromApplication(wltID)

            newWlt = PyBtcWallet().readWalletFile(newWltPath)
            self.main.addWalletToApplication(newWlt, True)
            # Removed this line of code because it's part of the old BDM paradigm.
            # Leaving this comment here in case it needs to be replaced by anything
            # newWlt.syncWithBlockchainLite()

            os.remove(thepath)
            os.remove(thepathBackup)
            self.main.statusBar().showMessage( \
               self.tr('Wallet %1 was replaced with a watching-only wallet.').arg(wltID), 10000)
         elif self.radioDelete.isChecked():
            LOGINFO('***Completely deleting wallet')
            os.remove(thepath)
            os.remove(thepathBackup)
            self.main.removeWalletFromApplication(wltID)
            self.main.statusBar().showMessage( \
               self.tr('Wallet %1 was deleted!').arg(wltID), 10000)

         self.parent.accept()
         self.accept()
      else:
         self.reject()


################################################################################
class DlgRemoveAddress(ArmoryDialog):
   def __init__(self, wlt, addr160, parent=None, main=None):
      super(DlgRemoveAddress, self).__init__(parent, main)


      if not wlt.hasScrAddr(addr160):
         raise WalletAddressError('Address does not exist in wallet!')

      addrIndex = wlt.cppWallet.getAssetIndexForAddr(addr160)
      self.cppAddrObj = wlt.cppWallet.getAddrObjByIndex(addrIndex)
      
      if addrIndex >= 0:
         raise WalletAddressError('Cannot delete regular chained addresses! '
                                   'Can only delete imported addresses.')

         
      importIndex = wlt.cppWallet.convertToImportIndex(addrIndex)

      self.wlt = wlt
      importStr = wlt.linearAddr160List[importIndex]
      self.addr = wlt.addrMap[importStr]
      self.comm = wlt.getCommentForAddress(addr160)

      lblWarning = QLabel(self.tr('<b>!!! WARNING !!!</b>\n\n'))
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lblWarning2 = QLabel(self.tr('<i>You have requested that the following address '
                            'be deleted from your wallet:</i>'))
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setWordWrap(True)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lbls = []
      lbls.append([])
      lbls[-1].append(QLabel(self.tr('Address:')))
      lbls[-1].append(QLabel(self.cppAddrObj.getScrAddr()))
      lbls.append([])
      lbls[-1].append(QLabel(self.tr('Comment:')))
      lbls[-1].append(QLabel(self.comm))
      lbls[-1][-1].setWordWrap(True)
      lbls.append([])
      lbls[-1].append(QLabel(self.tr('In Wallet:')))
      lbls[-1].append(QLabel('"%s" (%s)' % (wlt.labelName, wlt.uniqueIDB58)))

      addrEmpty = True
      if TheBDM.getState() == BDM_BLOCKCHAIN_READY:
         bal = wlt.getAddrBalance(addr160, 'Full')
         lbls.append([])
         lbls[-1].append(QLabel(self.tr('Address Balance (w/ unconfirmed):')))
         if bal > 0:
            lbls[-1].append(QLabel('<font color="red"><b>' + coin2str(bal, maxZeros=1) + ' BTC</b></font>'))
            lbls[-1][-1].setTextFormat(Qt.RichText)
            addrEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      # Add the warning text and images to the top of the dialog
      layout = QGridLayout()
      layout.addWidget(lblWarning, 0, 1, 1, 1)
      layout.addWidget(lblWarning2, 1, 1, 1, 1)
      layout.addWidget(lblWarnImg, 0, 0, 2, 1)
      layout.addWidget(lblWarnImg2, 0, 2, 2, 1)

      frmInfo = QFrame()
      frmInfo.setFrameStyle(QFrame.Box | QFrame.Plain)
      frmInfo.setLineWidth(3)
      frmInfoLayout = QGridLayout()
      for i in range(len(lbls)):
         lbls[i][0].setText('<b>' + lbls[i][0].text() + '</b>')
         lbls[i][0].setTextFormat(Qt.RichText)
         frmInfoLayout.addWidget(lbls[i][0], i, 0)
         frmInfoLayout.addWidget(lbls[i][1], i, 1, 1, 2)

      frmInfo.setLayout(frmInfoLayout)
      layout.addWidget(frmInfo, 2, 0, 2, 3)

      lblDelete = QLabel(\
            self.tr('Do you want to delete this address?  No other addresses in this '
            'wallet will be affected.'))
      lblDelete.setWordWrap(True)
      lblDelete.setTextFormat(Qt.RichText)
      layout.addWidget(lblDelete, 4, 0, 1, 3)

      bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                              QDialogButtonBox.Cancel)
      self.connect(bbox, SIGNAL('accepted()'), self.removeAddress)
      self.connect(bbox, SIGNAL('rejected()'), self.reject)
      layout.addWidget(bbox, 5, 0, 1, 3)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Confirm Delete Address'))


   def removeAddress(self):
      reply = QMessageBox.warning(self, self.tr('One more time...'), self.tr(
           'Simply deleting an address does not prevent anyone '
           'from sending money to it.  If you have given this address '
           'to anyone in the past, make sure that they know not to '
           'use it again, since any bitcoins sent to it will be '
           'inaccessible.\n\n '
           'If you are maintaining an external copy of this address '
           'please ignore this warning\n\n'
           'Are you absolutely sure you want to delete %1 ?').arg(self.cppAddrObj.getScrAddr()) , \
           QMessageBox.Yes | QMessageBox.Cancel)

      if reply == QMessageBox.Yes:
         self.wlt.deleteImportedAddress(self.addr.getAddr160())
         try:
            self.parent.wltAddrModel.reset()
            self.parent.setSummaryBalances()
         except AttributeError:
            pass
         self.accept()

      else:
         self.reject()

################################################################################
class DlgWalletSelect(ArmoryDialog):
   def __init__(self, parent=None, main=None, title='Select Wallet:',
                                              descr='',
                                              firstSelect=None,
                                              onlyMyWallets=False,
                                              wltIDList=None,
                                              atLeast=0):
      super(DlgWalletSelect, self).__init__(parent, main)


      self.balAtLeast = atLeast

      if self.main and len(self.main.walletMap) == 0:
         QMessageBox.critical(self, self.tr('No Wallets!'), \
            self.tr('There are no wallets to select from.  Please create or import '
            'a wallet first.'), QMessageBox.Ok)
         self.accept()
         return

      if wltIDList == None:
         wltIDList = list(self.main.walletIDList)

      # Start the layout
      layout = QVBoxLayout()
      # Expect to set selectedId
      wltFrame = SelectWalletFrame(self, main, HORIZONTAL, firstSelect, onlyMyWallets,
                                                  wltIDList, atLeast, self.selectWallet)
      layout.addWidget(wltFrame)
      self.selectedID = wltFrame.selectedID
      buttonBox = QDialogButtonBox()
      btnAccept = QPushButton('OK')
      btnCancel = QPushButton('Cancel')
      self.connect(btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox.addButton(btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(btnCancel, QDialogButtonBox.RejectRole)

      layout.addWidget(buttonBox)

      layout.setSpacing(15)
      self.setLayout(layout)

      self.setWindowTitle(self.tr('Select Wallet'))

   def selectWallet(self, wlt, isDoubleClick=False):
      self.selectedID = wlt.uniqueIDB58
      if isDoubleClick:
         self.accept()

#############################################################################
def excludeChange(outputPairs, wlt):
   """
   NOTE:  this method works ONLY because we always generate a new address
          whenever creating a change-output, which means it must have a
          higher chainIndex than all other addresses.  If you did something
          creative with this tx, this may not actually work.
   """
   maxChainIndex = -5
   nonChangeOutputPairs = []
   currentMaxChainPair = None
   for script,val in outputPairs:
      scrType = getTxOutScriptType(script)
      addr = ''
      if scrType in CPP_TXOUT_HAS_ADDRSTR:
         scrAddr = script_to_scrAddr(script)
         addr = wlt.getAddrByHash160(scrAddr_to_hash160(scrAddr)[1])

      # this logic excludes the pair with the maximum chainIndex from the
      # returned list
      if addr:
         if addr.chainIndex > maxChainIndex:
            maxChainIndex = addr.chainIndex
            if currentMaxChainPair:
               nonChangeOutputPairs.append(currentMaxChainPair)
            currentMaxChainPair = [script,val]
         else:
            nonChangeOutputPairs.append([script,val])
   return nonChangeOutputPairs


################################################################################
class DlgConfirmSend(ArmoryDialog):

   def __init__(self, wlt, scriptValPairs, fee, parent=None, main=None, \
                                          sendNow=False, pytxOrUstx=None):
      super(DlgConfirmSend, self).__init__(parent, main)
      layout = QGridLayout()
      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap(':/MsgBox_info48.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      changeRemoved = False
      sendPairs = []
      returnPairs = []
      for script,val in scriptValPairs:
         scrType = getTxOutScriptType(script)
         if scrType in CPP_TXOUT_HAS_ADDRSTR:
            scraddr = script_to_scrAddr(script)
            addr160 = scrAddr_to_hash160(scraddr)[1]
            if wlt.hasAddr(addr160):
               returnPairs.append([script,val])
            else:
               sendPairs.append([script,val])
         else:
            # We assume that anything without an addrStr is going external
            sendPairs.append([script,val])

      # If there are more than 3 return pairs then this is a 1%'er tx we should
      # not presume to know which pair is change. It's a weird corner case so
      # it's best to leave it alone.
      # 0 return is an exact change tx, no need to deal with it so this
      # chunk of code that removes change only cares about 1 and 2 return pairs.
      # if 1 remove it, if 2 remove the one with a higher index.
      # Exception: IF no send pairs, it's a tx for max to a single internal address

      if len(sendPairs)==1 and len(returnPairs)==0:
         # Exactly one output, exact change by definition
         doExcludeChange = False
         doShowAllMsg    = False
         doShowLeaveWlt  = False
      elif len(sendPairs)==0 and len(returnPairs)==1:
         doExcludeChange = False
         doShowAllMsg    = False
         doShowLeaveWlt  = True
      elif len(returnPairs)==0:
         # Exact change
         doExcludeChange = False
         doShowAllMsg    = False
         doShowLeaveWlt  = False
      elif len(returnPairs)==1:
         # There's a simple change output
         doExcludeChange = True
         doShowAllMsg    = False
         doShowLeaveWlt  = False
      elif len(sendPairs)==0 and len(returnPairs)==2:
         # Send-to-self within wallet, with change, no external recips
         doExcludeChange = True
         doShowAllMsg    = False
         doShowLeaveWlt  = True
      else:
         # Everything else just show everything
         doExcludeChange = False
         doShowAllMsg    = True
         doShowLeaveWlt  = True


      if doExcludeChange:
         returnPairs = excludeChange(returnPairs, wlt)


      # returnPairs now includes only the outputs to be displayed
      totalLeavingWlt = sum([val for script,val in sendPairs]) + fee
      totalSend       = sum([val for script,val in returnPairs]) + totalLeavingWlt
      sendFromWalletStr = coin2strNZS(totalLeavingWlt)
      totalSendStr      = coin2strNZS(totalSend)


      lblAfterBox = QRichLabel('')

      # Always include a way to review the tx when in expert mode.  Or whenever
      # we are showing the entire output list.
      # If we have a pytx or ustx, we can add a DlgDispTxInfo button
      showAllMsg = ''
      if doShowAllMsg or (pytxOrUstx and self.main.usermode==USERMODE.Expert):
         showAllMsg = self.tr('To see complete transaction details '
                             '<a href="None">click here</a></font>')

         def openDlgTxInfo(*args):
            DlgDispTxInfo(pytxOrUstx, wlt, self.parent, self.main).exec_()

         self.connect(lblAfterBox, SIGNAL('linkActivated(const QString &)'), openDlgTxInfo)


      lblMsg = QRichLabel(self.tr(
         'This transaction will spend <b>%1 BTC</b> from '
         '<font color="%2">Wallet "<b>%3</b>" (%4)</font> to the following '
         'recipients:').arg(totalSendStr, htmlColor('TextBlue'), wlt.labelName, wlt.uniqueIDB58))

      if doShowLeaveWlt:
         lblAfterBox.setText(self.tr(
            '<font size=3>* Starred '
            'outputs are going to the same wallet from which they came '
            'and do not affect the wallet\'s final balance. '
            'The total balance of the wallet will actually only decrease '
            '<b>%1 BTC</b> as a result of this transaction.  %2</font>').arg(sendFromWalletStr, showAllMsg))
      elif len(showAllMsg)>0:
         lblAfterBox.setText(showAllMsg)


      addrColWidth = 50

      recipLbls = []
      ffixBold = GETFONT('Fixed')
      ffixBold.setWeight(QFont.Bold)
      for script,val in sendPairs + returnPairs:
         displayInfo = self.main.getDisplayStringForScript(script, addrColWidth)
         dispStr = (' '+displayInfo['String']).ljust(addrColWidth)

         coinStr = coin2str(val, rJust=True, maxZeros=4)
         if [script,val] in returnPairs:
            dispStr = '*'+dispStr[1:]

         recipLbls.append(QLabel(dispStr + coinStr))
         recipLbls[-1].setFont(ffixBold)


      if fee > 0:
         recipLbls.append(QSpacerItem(10, 10))
         recipLbls.append(QLabel(' Transaction Fee : '.ljust(addrColWidth) +
                           coin2str(fee, rJust=True, maxZeros=4)))
         recipLbls[-1].setFont(GETFONT('Fixed'))


      recipLbls.append(HLINE(QFrame.Sunken))
      if doShowLeaveWlt:
         # We have a separate message saying "total amount actually leaving wlt is..."
         # We can just give the total of all the outputs in the table above
         recipLbls.append(QLabel(' Total: '.ljust(addrColWidth) +
                           coin2str(totalSend, rJust=True, maxZeros=4)))
      else:
         # The k
         recipLbls.append(QLabel(' Total Leaving Wallet: '.ljust(addrColWidth) +
                           coin2str(totalSend, rJust=True, maxZeros=4)))

      recipLbls[-1].setFont(GETFONT('Fixed'))

      if sendNow:
         self.btnAccept = QPushButton(self.tr('Send'))
         lblLastConfirm = QLabel(self.tr('Are you sure you want to execute this transaction?'))
      else:
         self.btnAccept = QPushButton(self.tr('Continue'))
         lblLastConfirm = QLabel(self.tr('Does the above look correct?'))

      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      
      self.signerType = SIGNER_DEFAULT
      def setSignerType(_type):
         self.signerType = _type
      
      isSigned = False
      if isinstance(pytxOrUstx, PyTx):
         ustx = UnsignedTransaction()
         ustx.createFromPyTx(pytxOrUstx)
         isSigned = pytxOrUstx.verifySigsAllInputs()
      else:
         isSigned = pytxOrUstx.verifySigsAllInputs(pytxOrUstx.signerType)
         
      if self.main.usermode == USERMODE.Expert and isSigned == False:
         self.signerSelect = SignerLabelFrame(self.main, pytxOrUstx, setSignerType)
         self.signerSelectFrame = self.signerSelect.getFrame()
      
         frmBtnSelect = makeHorizFrame([STRETCH, self.signerSelectFrame, buttonBox])
      else:
         frmBtnSelect = buttonBox

      frmTable = makeLayoutFrame(VERTICAL, recipLbls, STYLE_RAISED)
      frmRight = makeVertFrame([ lblMsg, \
                                  'Space(20)', \
                                  frmTable, \
                                  lblAfterBox, \
                                  'Space(10)', \
                                  lblLastConfirm, \
                                  'Space(10)', \
                                  frmBtnSelect ])

      frmAll = makeHorizFrame([ lblInfoImg, frmRight ])

      layout.addWidget(frmAll)

      self.setLayout(layout)
      self.setMinimumWidth(350)
      self.setWindowTitle(self.tr('Confirm Transaction'))
   
   #############################################################################   
   def getSignerType(self):
      return self.signerType


################################################################################
class DlgSendBitcoins(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None, 
                              wltIDList=None, onlyOfflineWallets=False,
                              spendFromLockboxID=None):
      super(DlgSendBitcoins, self).__init__(parent, main)
      layout = QVBoxLayout()

      self.spendFromLockboxID = spendFromLockboxID

      self.frame = SendBitcoinsFrame(self, main, self.tr('Send Bitcoins'),
                   wlt, wltIDList, onlyOfflineWallets=onlyOfflineWallets,
                   sendCallback=self.createTxAndBroadcast,
                   createUnsignedTxCallback=self.createUnsignedTxAndDisplay,
                   spendFromLockboxID=spendFromLockboxID)
      layout.addWidget(self.frame)
      self.setLayout(layout)
      self.sizeHint = lambda: QSize(850, 600)
      self.setMinimumWidth(700)
      # Update the any controls based on the initial wallet selection
      self.frame.fireWalletChange()



   #############################################################################
   def createUnsignedTxAndDisplay(self, ustx):
      self.accept()
      if self.spendFromLockboxID is None:
         dlg = DlgOfflineTxCreated(self.frame.wlt, ustx, self.parent, self.main)
         dlg.exec_()
      else:
         dlg = DlgMultiSpendReview(self.parent, self.main, ustx)
         dlg.exec_()


   #############################################################################
   def createTxAndBroadcast(self):
      self.accept()

   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('SendBtcGeometry', str(self.saveGeometry().toHex()))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).reject(*args)







################################################################################
class DlgOfflineTxCreated(ArmoryDialog):
   def __init__(self, wlt, ustx, parent=None, main=None):
      super(DlgOfflineTxCreated, self).__init__(parent, main)
      layout = QVBoxLayout()

      reviewOfflineTxFrame = ReviewOfflineTxFrame(self, main, self.tr("Review Offline Transaction"))
      reviewOfflineTxFrame.setWallet(wlt)
      reviewOfflineTxFrame.setUSTX(ustx)
      continueButton = QPushButton(self.tr('Continue'))
      self.connect(continueButton, SIGNAL(CLICKED), self.signBroadcastTx)
      doneButton = QPushButton(self.tr('Done'))
      self.connect(doneButton, SIGNAL(CLICKED), self.accept)

      ttipDone = self.main.createToolTipWidget(self.tr(
         'By clicking Done you will exit the offline transaction process for now. '
         'When you are ready to sign and/or broadcast the transaction, click the Offline '
         'Transactions button in the main window, then click the Sign and/or '
         'Broadcast Transaction button in the Select Offline Action dialog.'))

      ttipContinue = self.main.createToolTipWidget(self.tr(
         'By clicking Continue you will continue to the next step in the offline '
         'transaction process to sign and/or broadcast the transaction.'))

      bottomStrip = makeHorizFrame([doneButton,
                                    ttipDone,
                                    STRETCH,
                                    continueButton,
                                    ttipContinue])

      frame = makeVertFrame([reviewOfflineTxFrame, bottomStrip])
      layout.addWidget(frame)
      self.setLayout(layout)
      self.setWindowTitle(self.tr('Review Offline Transaction'))
      self.setWindowIcon(QIcon(self.main.iconfile))


   def signBroadcastTx(self):
      self.accept()
      DlgSignBroadcastOfflineTx(self.parent,self.main).exec_()



################################################################################
class DlgOfflineSelect(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgOfflineSelect, self).__init__(parent, main)


      self.do_review = False
      self.do_create = False
      self.do_broadc = False
      lblDescr = QRichLabel(self.tr(
         'In order to execute an offline transaction, three steps must '
         'be followed:'
         '<ol>'
         '<li><u>On</u>line Computer:  Create the unsigned transaction</li> '
         '<li><u>Off</u>line Computer: Get the transaction signed</li> '
         '<li><u>On</u>line Computer:  Broadcast the signed transaction</li></ol> '
         'You must create the transaction using a watch-only wallet on an online '
         'system, but watch-only wallets cannot sign it.  Only the offline system '
         'can create a valid signature.  The easiest way to execute all three steps '
         'is to use a USB key to move the data between computers.<br><br> '
         'All the data saved to the removable medium during all three steps are '
         'completely safe and do not reveal any private information that would benefit an '
         'attacker trying to steal your funds.  However, this transaction data does '
         'reveal some addresses in your wallet, and may represent a breach of '
         '<i>privacy</i> if not protected.'))

      btnCreate = QPushButton(self.tr('Create New Offline Transaction'))
      broadcastButton = QPushButton(self.tr('Sign and/or Broadcast Transaction'))
      if not TheBDM.getState() == BDM_BLOCKCHAIN_READY:
         btnCreate.setEnabled(False)
         if len(self.main.walletMap) == 0:
            broadcastButton = QPushButton(self.tr('No wallets available!'))
            broadcastButton.setEnabled(False)
         else:
            broadcastButton = QPushButton(self.tr('Sign Offline Transaction'))
      else:
         if len(self.main.getWatchingOnlyWallets()) == 0:
            btnCreate = QPushButton(self.tr('No watching-only wallets available!'))
            btnCreate.setEnabled(False)
         if len(self.main.walletMap) == 0 and self.main.netMode == NETWORKMODE.Full:
            broadcastButton = QPushButton('Broadcast Signed Transaction')

      btnCancel = QPushButton(self.tr('<<< Go Back'))

      def create():
         self.do_create = True; self.accept()
      def broadc():
         self.do_broadc = True; self.accept()

      self.connect(btnCreate, SIGNAL(CLICKED), create)
      self.connect(broadcastButton, SIGNAL(CLICKED), broadc)
      self.connect(btnCancel, SIGNAL(CLICKED), self.reject)

      lblCreate = QRichLabel(self.tr(
         'Create a transaction from an Offline/Watching-Only wallet '
         'to be signed by the computer with the full wallet '))

      lblReview = QRichLabel(self.tr(
         'Review an unsigned transaction and sign it if you have '
         'the private keys needed for it '))

      lblBroadc = QRichLabel(self.tr(
         'Send a pre-signed transaction to the Bitcoin network to finalize it'))

      lblBroadc.setMinimumWidth(tightSizeNChar(lblBroadc, 45)[0])

      frmOptions = QFrame()
      frmOptions.setFrameStyle(STYLE_PLAIN)
      frmOptionsLayout = QGridLayout()
      frmOptionsLayout.addWidget(btnCreate, 0, 0)
      frmOptionsLayout.addWidget(lblCreate, 0, 2)
      frmOptionsLayout.addWidget(HLINE(), 1, 0, 1, 3)
      frmOptionsLayout.addWidget(broadcastButton, 2, 0, 3, 1)
      frmOptionsLayout.addWidget(lblReview, 2, 2)
      frmOptionsLayout.addWidget(HLINE(), 3, 2, 1, 1)
      frmOptionsLayout.addWidget(lblBroadc, 4, 2)

      frmOptionsLayout.addItem(QSpacerItem(20, 20), 0, 1, 3, 1)
      frmOptions.setLayout(frmOptionsLayout)

      frmDescr = makeLayoutFrame(HORIZONTAL, ['Space(10)', lblDescr, 'Space(10)'], \
                                             STYLE_SUNKEN)
      frmCancel = makeLayoutFrame(HORIZONTAL, [btnCancel, STRETCH])

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmDescr, 0, 0, 1, 1)
      dlgLayout.addWidget(frmOptions, 1, 0, 1, 1)
      dlgLayout.addWidget(frmCancel, 2, 0, 1, 1)

      self.setLayout(dlgLayout)
      self.setWindowTitle('Select Offline Action')
      self.setWindowIcon(QIcon(self.main.iconfile))

################################################################################
class DlgSignBroadcastOfflineTx(ArmoryDialog):
   """
   We will make the assumption that this dialog is used ONLY for outgoing
   transactions from your wallet.  This simplifies the logic if we don't
   have to identify input senders/values, and handle the cases where those
   may not be specified
   """
   def __init__(self, parent=None, main=None):
      super(DlgSignBroadcastOfflineTx, self).__init__(parent, main)

      self.setWindowTitle(self.tr('Review Offline Transaction'))
      self.setWindowIcon(QIcon(self.main.iconfile))

      signBroadcastOfflineTxFrame = SignBroadcastOfflineTxFrame(
                           self, main, self.tr("Sign or Broadcast Transaction"))

      doneButton = QPushButton(self.tr('Done'))
      self.connect(doneButton, SIGNAL(CLICKED), self.accept)
      doneForm = makeLayoutFrame(HORIZONTAL, [STRETCH, doneButton])
      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(signBroadcastOfflineTxFrame)
      dlgLayout.addWidget(doneForm)
      self.setLayout(dlgLayout)
      signBroadcastOfflineTxFrame.processUSTX()

################################################################################
class DlgShowKeyList(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgShowKeyList, self).__init__(parent, main)

      self.wlt = wlt

      self.havePriv = ((not self.wlt.useEncryption) or not (self.wlt.isLocked))

      wltType = determineWalletType(self.wlt, self.main)[0]
      if wltType in (WLTTYPES.Offline, WLTTYPES.WatchOnly):
         self.havePriv = False


      # NOTE/WARNING:  We have to make copies (in RAM) of the unencrypted
      #                keys, or else we will have to type in our address
      #                every 10s if we want to modify the key list.  This
      #                isn't likely a big problem, but it's not ideal,
      #                either.  Not much I can do about, though...
      #                (at least:  once this dialog is closed, all the
      #                garbage should be collected...)
      self.addrCopies = []
      for addr in self.wlt.getLinearAddrList(withAddrPool=True):
         self.addrCopies.append(addr.copy())
      self.rootKeyCopy = self.wlt.addrMap['ROOT'].copy()

      backupVersion = BACKUP_TYPE_135A
      testChain = DeriveChaincodeFromRootKey(self.rootKeyCopy.binPrivKey32_Plain)
      self.needChaincode = (not testChain == self.rootKeyCopy.chaincode)
      if not self.needChaincode:
         backupVersion = BACKUP_TYPE_135C

      self.strDescrReg = (self.tr(
         'The textbox below shows all keys that are part of this wallet, '
         'which includes both permanent keys and imported keys.  If you '
         'simply want to backup your wallet and you have no imported keys '
         'then all data below is reproducible from a plain paper backup. '
         '<br><br> '
         'If you have imported addresses to backup, and/or you '
         'would like to export your private keys to another '
         'wallet service or application, then you can save this data '
         'to disk, or copy&paste it into the other application.'))
      self.strDescrWarn = (self.tr(
         '<br><br>'
         '<font color="red">Warning:</font> The text box below contains '
         'the plaintext (unencrypted) private keys for each of '
         'the addresses in this wallet.  This information can be used '
         'to spend the money associated with those addresses, so please '
         'protect it like you protect the rest of your wallet. '))

      self.lblDescr = QRichLabel('')
      self.lblDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)


      txtFont = GETFONT('Fixed', 8)
      self.txtBox = QTextEdit()
      self.txtBox.setReadOnly(True)
      self.txtBox.setFont(txtFont)
      w, h = tightSizeNChar(txtFont, 110)
      self.txtBox.setFont(txtFont)
      self.txtBox.setMinimumWidth(w)
      self.txtBox.setMaximumWidth(w)
      self.txtBox.setMinimumHeight(h * 3.2)
      self.txtBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

      # Create a list of checkboxes and then some ID word to identify what
      # to put there
      self.chkList = {}
      self.chkList['AddrStr'] = QCheckBox(self.tr('Address String'))
      self.chkList['PubKeyHash'] = QCheckBox(self.tr('Hash160'))
      self.chkList['PrivCrypt'] = QCheckBox(self.tr('Private Key (Encrypted)'))
      self.chkList['PrivHexBE'] = QCheckBox(self.tr('Private Key (Plain Hex)'))
      self.chkList['PrivB58'] = QCheckBox(self.tr('Private Key (Plain Base58)'))
      self.chkList['PubKey'] = QCheckBox(self.tr('Public Key (BE)'))
      self.chkList['ChainIndex'] = QCheckBox(self.tr('Chain Index'))

      self.chkList['AddrStr'   ].setChecked(True)
      self.chkList['PubKeyHash'].setChecked(False)
      self.chkList['PrivB58'   ].setChecked(self.havePriv)
      self.chkList['PrivCrypt' ].setChecked(False)
      self.chkList['PrivHexBE' ].setChecked(self.havePriv)
      self.chkList['PubKey'    ].setChecked(not self.havePriv)
      self.chkList['ChainIndex'].setChecked(False)

      namelist = ['AddrStr', 'PubKeyHash', 'PrivB58', 'PrivCrypt', \
                  'PrivHexBE', 'PubKey', 'ChainIndex']

      for name in self.chkList.keys():
         self.connect(self.chkList[name], SIGNAL('toggled(bool)'), \
                      self.rewriteList)


      self.chkImportedOnly = QCheckBox(self.tr('Imported Addresses Only'))
      self.chkWithAddrPool = QCheckBox(self.tr('Include Unused (Address Pool)'))
      self.chkDispRootKey = QCheckBox(self.tr('Include Paper Backup Root'))
      self.chkOmitSpaces = QCheckBox(self.tr('Omit spaces in key data'))
      self.chkDispRootKey.setChecked(True)
      self.connect(self.chkImportedOnly, SIGNAL('toggled(bool)'), self.rewriteList)
      self.connect(self.chkWithAddrPool, SIGNAL('toggled(bool)'), self.rewriteList)
      self.connect(self.chkDispRootKey, SIGNAL('toggled(bool)'), self.rewriteList)
      self.connect(self.chkOmitSpaces, SIGNAL('toggled(bool)'), self.rewriteList)
      # self.chkCSV = QCheckBox('Display in CSV format')

      if not self.havePriv:
         self.chkDispRootKey.setChecked(False)
         self.chkDispRootKey.setEnabled(False)


      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)
      if std:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['PrivCrypt' ].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)
      elif adv:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)

      # We actually just want to remove these entirely
      # (either we need to display all data needed for decryption,
      # besides passphrase,  or we shouldn't show any of it)
      self.chkList['PrivCrypt' ].setVisible(False)

      chkBoxList = [self.chkList[n] for n in namelist]
      chkBoxList.append('Line')
      chkBoxList.append(self.chkImportedOnly)
      chkBoxList.append(self.chkWithAddrPool)
      chkBoxList.append(self.chkDispRootKey)

      frmChks = makeLayoutFrame(VERTICAL, chkBoxList, STYLE_SUNKEN)


      btnGoBack = QPushButton(self.tr('<<< Go Back'))
      btnSaveFile = QPushButton(self.tr('Save to File...'))
      btnCopyClip = QPushButton(self.tr('Copy to Clipboard'))
      self.lblCopied = QRichLabel('')

      self.connect(btnGoBack, SIGNAL(CLICKED), self.accept)
      self.connect(btnSaveFile, SIGNAL(CLICKED), self.saveToFile)
      self.connect(btnCopyClip, SIGNAL(CLICKED), self.copyToClipboard)
      frmGoBack = makeLayoutFrame(HORIZONTAL, [btnGoBack, \
                                            STRETCH, \
                                            self.chkOmitSpaces, \
                                            STRETCH, \
                                            self.lblCopied, \
                                            btnCopyClip, \
                                            btnSaveFile])

      frmDescr = makeLayoutFrame(HORIZONTAL, [self.lblDescr], STYLE_SUNKEN)

      if not self.havePriv or (self.wlt.useEncryption and self.wlt.isLocked):
         self.chkList['PrivHexBE'].setEnabled(False)
         self.chkList['PrivHexBE'].setChecked(False)
         self.chkList['PrivB58'  ].setEnabled(False)
         self.chkList['PrivB58'  ].setChecked(False)

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmDescr, 0, 0, 1, 1)
      dlgLayout.addWidget(frmChks, 0, 1, 1, 1)
      dlgLayout.addWidget(self.txtBox, 1, 0, 1, 2)
      dlgLayout.addWidget(frmGoBack, 2, 0, 1, 2)
      dlgLayout.setRowStretch(0, 0)
      dlgLayout.setRowStretch(1, 1)
      dlgLayout.setRowStretch(2, 0)

      self.setLayout(dlgLayout)
      self.rewriteList()
      self.setWindowTitle(self.tr('All Wallet Keys'))

   def rewriteList(self, *args):
      """
      Write out all the wallet data
      """
      whitespace = '' if self.chkOmitSpaces.isChecked() else ' '

      def fmtBin(s, nB=4, sw=False):
         h = binary_to_hex(s)
         if sw:
            h = hex_switchEndian(h)
         return whitespace.join([h[i:i + nB] for i in range(0, len(h), nB)])

      L = []
      L.append('Created:       ' + unixTimeToFormatStr(RightNow(), self.main.getPreferredDateFormat()))
      L.append('Wallet ID:     ' + self.wlt.uniqueIDB58)
      L.append('Wallet Name:   ' + self.wlt.labelName)
      L.append('')

      if self.chkDispRootKey.isChecked():
         binPriv0 = self.rootKeyCopy.binPrivKey32_Plain.toBinStr()[:16]
         binPriv1 = self.rootKeyCopy.binPrivKey32_Plain.toBinStr()[16:]
         binChain0 = self.rootKeyCopy.chaincode.toBinStr()[:16]
         binChain1 = self.rootKeyCopy.chaincode.toBinStr()[16:]
         binPriv0Chk = computeChecksum(binPriv0, nBytes=2)
         binPriv1Chk = computeChecksum(binPriv1, nBytes=2)
         binChain0Chk = computeChecksum(binChain0, nBytes=2)
         binChain1Chk = computeChecksum(binChain1, nBytes=2)

         binPriv0 = binary_to_easyType16(binPriv0 + binPriv0Chk)
         binPriv1 = binary_to_easyType16(binPriv1 + binPriv1Chk)
         binChain0 = binary_to_easyType16(binChain0 + binChain0Chk)
         binChain1 = binary_to_easyType16(binChain1 + binChain1Chk)

         L.append('-' * 80)
         L.append('The following is the same information contained on your paper backup.')
         L.append('All NON-imported addresses in your wallet are backed up by this data.')
         L.append('')
         L.append('Root Key:     ' + ' '.join([binPriv0[i:i + 4]  for i in range(0, 36, 4)]))
         L.append('              ' + ' '.join([binPriv1[i:i + 4]  for i in range(0, 36, 4)]))
         if self.needChaincode:
            L.append('Chain Code:   ' + ' '.join([binChain0[i:i + 4] for i in range(0, 36, 4)]))
            L.append('              ' + ' '.join([binChain1[i:i + 4] for i in range(0, 36, 4)]))
         L.append('-' * 80)
         L.append('')

         # Cleanup all that sensitive data laying around in RAM
         binPriv0, binPriv1 = None, None
         binChain0, binChain1 = None, None
         binPriv0Chk, binPriv1Chk = None, None
         binChain0Chk, binChain1Chk = None, None

      self.havePriv = False
      topChain = self.wlt.highestUsedChainIndex
      extraLbl = ''

      for addr in self.addrCopies:
         try:
            cppAddrObj = self.wlt.cppWallet.getAddrObjByIndex(addr.chainIndex)
         except:
            addrIndex = self.wlt.cppWallet.getAssetIndexForAddr(addr.getAddr160())
            cppAddrObj = self.wlt.cppWallet.getAddrObjByIndex(addrIndex)
            
         # Address pool
         if self.chkWithAddrPool.isChecked():
            if addr.chainIndex > topChain:
               extraLbl = '   (Unused/Address Pool)'
         else:
            if addr.chainIndex > topChain:
               continue

         # Imported Addresses
         if self.chkImportedOnly.isChecked():
            if not addr.chainIndex == -2:
               continue
         else:
            if addr.chainIndex == -2:
               extraLbl = '   (Imported)'

         if self.chkList['AddrStr'   ].isChecked():
            L.append(cppAddrObj.getScrAddr() + extraLbl)
         if self.chkList['PubKeyHash'].isChecked():
            L.append('   Hash160   : ' + fmtBin(addr.getAddr160()))
         if self.chkList['PrivB58'   ].isChecked():
            pB58 = encodePrivKeyBase58(addr.binPrivKey32_Plain.toBinStr())
            pB58Stretch = whitespace.join([pB58[i:i + 6] for i in range(0, len(pB58), 6)])
            L.append('   PrivBase58: ' + pB58Stretch)
            self.havePriv = True
         if self.chkList['PrivCrypt' ].isChecked():
            L.append('   PrivCrypt : ' + fmtBin(addr.binPrivKey32_Encr.toBinStr()))
         if self.chkList['PrivHexBE' ].isChecked():
            L.append('   PrivHexBE : ' + fmtBin(addr.binPrivKey32_Plain.toBinStr()))
            self.havePriv = True
         if self.chkList['PubKey'    ].isChecked():
            L.append('   PublicX   : ' + fmtBin(addr.binPublicKey65.toBinStr()[1:33 ]))
            L.append('   PublicY   : ' + fmtBin(addr.binPublicKey65.toBinStr()[  33:]))
         if self.chkList['ChainIndex'].isChecked():
            L.append('   ChainIndex: ' + str(addr.chainIndex))

      self.txtBox.setText('\n'.join(L))
      if self.havePriv:
         self.lblDescr.setText(self.strDescrReg + self.strDescrWarn)
      else:
         self.lblDescr.setText(self.strDescrReg)

   def saveToFile(self):
      if self.havePriv:
         if not self.main.getSettingOrSetDefault('DNAA_WarnPrintKeys', False):
            result = MsgBoxWithDNAA(self, self.main, MSGBOX.Warning, title=self.tr('Plaintext Private Keys'), \
                  msg=self.tr('<font color="red"><b>REMEMBER:</b></font> The data you '
                  'are about to save contains private keys.  Please make sure '
                  'that only trusted persons will have access to this file. '
                  '<br><br>Are you sure you want to continue?'), \
                  dnaaMsg=None, wCancel=True)
            if not result[0]:
               return
            self.main.writeSetting('DNAA_WarnPrintKeys', result[1])

      wltID = self.wlt.uniqueIDB58
      fn = self.main.getFileSave(title=self.tr('Save Key List'), \
                                 ffilter=[self.tr('Text Files (*.txt)')], \
                                 defaultFilename=('keylist_%s_.txt' % wltID))
      if len(fn) > 0:
         fileobj = open(fn, 'w')
         fileobj.write(str(self.txtBox.toPlainText()))
         fileobj.close()



   def copyToClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtBox.toPlainText()))
      self.lblCopied.setText(self.tr('<i>Copied!</i>'))


   def cleanup(self):
      self.rootKeyCopy.binPrivKey32_Plain.destroy()
      for addr in self.addrCopies:
         addr.binPrivKey32_Plain.destroy()
      self.rootKeyCopy = None
      self.addrCopies = None

   def accept(self):
      self.cleanup()
      super(DlgShowKeyList, self).accept()

   def reject(self):
      self.cleanup()
      super(DlgShowKeyList, self).reject()

################################################################################
class DlgAddressProperties(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgAddressProperties, self).__init__(parent, main)

################################################################################
def extractTxInfo(pytx, rcvTime=None):
   ustx = None
   if isinstance(pytx, UnsignedTransaction):
      ustx = pytx
      pytx = ustx.pytxObj.copy()

   txHash = pytx.getHash()
   txSize, txWeight, sumTxIn, txTime, txBlk, txIdx = [None] * 6

   txOutToList = pytx.makeRecipientsList()
   sumTxOut = sum([t[1] for t in txOutToList])

   txcpp = Tx()
   if TheBDM.getState() == BDM_BLOCKCHAIN_READY:
      txcpp = TheBDM.bdv().getTxByHash(txHash)
      if txcpp.isInitialized():
         hgt = txcpp.getBlockHeight()
         txWeight = txcpp.getTxWeight()
         if hgt <= TheBDM.getTopBlockHeight():
            headref = TheBDM.bdv().blockchain().getHeaderByHeight(hgt)
            txTime = unixTimeToFormatStr(headref.getTimestamp())
            txBlk = headref.getBlockHeight()
            txIdx = txcpp.getBlockTxIndex()
            txSize = txcpp.getSize()
         else:
            if rcvTime == None:
               txTime = 'Unknown'
            elif rcvTime == -1:
               txTime = '[[Not broadcast yet]]'
            elif isinstance(rcvTime, basestring):
               txTime = rcvTime
            else:
               txTime = unixTimeToFormatStr(rcvTime)
            txBlk = UINT32_MAX
            txIdx = -1

   txinFromList = []
   if TheBDM.getState() == BDM_BLOCKCHAIN_READY and txcpp.isInitialized():
      # Use BDM to get all the info about the TxOut being spent
      # Recip, value, block-that-incl-tx, tx-that-incl-txout, txOut-index
      haveAllInput = True
      for i in range(txcpp.getNumTxIn()):
         txinFromList.append([])
         cppTxin = txcpp.getTxInCopy(i)
         prevTxHash = cppTxin.getOutPoint().getTxHash()
         prevTx = TheBDM.bdv().getTxByHash(prevTxHash)
         if prevTx.isInitialized():
            prevTxOut = prevTx.getTxOutCopy(cppTxin.getOutPoint().getTxOutIndex())
            txinFromList[-1].append(prevTxOut.getScrAddressStr())
            txinFromList[-1].append(prevTxOut.getValue())
            if prevTx.isInitialized():
               txinFromList[-1].append(prevTx.getBlockHeight())
               txinFromList[-1].append(prevTx.getThisHash())
               txinFromList[-1].append(prevTxOut.getIndex())
               txinFromList[-1].append(prevTxOut.getScript())
            else:
               LOGERROR('How did we get a bad parent pointer? (extractTxInfo)')
               #prevTxOut.pprint()
               txinFromList[-1].append('')
               txinFromList[-1].append('')
               txinFromList[-1].append('')
               txinFromList[-1].append('')
         else:
            haveAllInput = False
            txin = PyTxIn().unserialize(cppTxin.serialize())
            try:
               scraddr = addrStr_to_scrAddr(TxInExtractAddrStrIfAvail(txin))
            except:
               pass

            txinFromList[-1].append(scraddr)
            txinFromList[-1].append('')
            txinFromList[-1].append('')
            txinFromList[-1].append('')
            txinFromList[-1].append('')
            txinFromList[-1].append('')

   elif ustx is not None:
      haveAllInput = True
      for ustxi in ustx.ustxInputs:
         txinFromList.append([])
         txinFromList[-1].append(script_to_scrAddr(ustxi.txoScript))
         txinFromList[-1].append(ustxi.value)
         txinFromList[-1].append('')
         txinFromList[-1].append(hash256(ustxi.supportTx))
         txinFromList[-1].append(ustxi.outpoint.txOutIndex)
         txinFromList[-1].append(ustxi.txoScript)
   else:  # BDM is not initialized
      haveAllInput = False
      for i, txin in enumerate(pytx.inputs):
         scraddr = addrStr_to_scrAddr(TxInExtractAddrStrIfAvail(txin))
         txinFromList.append([])
         txinFromList[-1].append(scraddr)
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')

   if haveAllInput:
      sumTxIn = sum([x[1] for x in txinFromList])
   else:
      sumTxIn = None

   return [txHash, txOutToList, sumTxOut, txinFromList, sumTxIn, \
           txTime, txBlk, txIdx, txSize, txWeight]

################################################################################
class DlgDispTxInfo(ArmoryDialog):
   def __init__(self, pytx, wlt, parent, main, mode=None, \
                             precomputeIdxGray=None, precomputeAmt=None, txtime=None):
      """
      This got freakin' complicated, because I'm trying to handle
      wallet/nowallet, BDM/noBDM and Std/Adv/Dev all at once.

      We can override the user mode as an input argument, in case a std
      user decides they want to see the tx in adv/dev mode
      """
      super(DlgDispTxInfo, self).__init__(parent, main)
      self.mode = mode


      FIELDS = enum('Hash', 'OutList', 'SumOut', 'InList', 'SumIn', \
                    'Time', 'Blk', 'Idx', 'TxSize', 'TxWeight')
      self.data = extractTxInfo(pytx, txtime)

      # If this is actually a ustx in here...
      ustx = None
      if isinstance(pytx, UnsignedTransaction):
         ustx = pytx
         pytx = ustx.getPyTxSignedIfPossible(signer=ustx.signerType)


      self.pytx = pytx.copy()

      if self.mode == None:
         self.mode = self.main.usermode

      txHash = self.data[FIELDS.Hash]

      haveWallet = (wlt != None)
      haveBDM = TheBDM.getState() == BDM_BLOCKCHAIN_READY

      # Should try to identify what is change and what's not
      fee = None
      txAmt = self.data[FIELDS.SumOut]

      # Collect our own outputs only, and ID non-std tx
      svPairSelf = []
      svPairOther = []
      indicesSelf = []
      indicesOther = []
      indicesMakeGray = []
      idx = 0
      for scrType, amt, script, msInfo in self.data[FIELDS.OutList]:
         # If it's a multisig, pretend it's P2SH
         if scrType == CPP_TXOUT_MULTISIG:
            script = script_to_p2sh_script(script)
            scrType = CPP_TXOUT_P2SH

         if scrType in CPP_TXOUT_HAS_ADDRSTR:
            addrStr = script_to_addrStr(script)
            addr160 = addrStr_to_hash160(addrStr)[1]
            scrAddr = script_to_scrAddr(script)
            if haveWallet and wlt.hasAddr(addr160):
               svPairSelf.append([scrAddr, amt])
               indicesSelf.append(idx)
            else:
               svPairOther.append([scrAddr, amt])
               indicesOther.append(idx)
         else:
            indicesOther.append(idx)
         idx += 1

      txdir = None
      changeIndex = None
      svPairDisp = None
      
      if haveBDM and haveWallet and self.data[FIELDS.SumOut] and self.data[FIELDS.SumIn]:
         fee = self.data[FIELDS.SumOut] - self.data[FIELDS.SumIn]
         try:
            le = wlt.getLedgerEntryForTxHash(txHash)
            txAmt = le.getValue()
   
            if le.isSentToSelf():
               txdir = self.tr('Sent-to-Self')
               svPairDisp = []
               if len(self.pytx.outputs)==1:
                  txAmt = fee
                  triplet = self.data[FIELDS.OutList][0]
                  scrAddr = script_to_scrAddr(triplet[2])
                  svPairDisp.append([scrAddr, triplet[1]])
               else:
                  txAmt, changeIndex = determineSentToSelfAmt(le, wlt)
                  for i, triplet in enumerate(self.data[FIELDS.OutList]):
                     if not i == changeIndex:
                        scrAddr = script_to_scrAddr(triplet[2])
                        svPairDisp.append([scrAddr, triplet[1]])
                     else:
                        indicesMakeGray.append(i)
            else:
               if le.getValue() > 0:
                  txdir = self.tr('Received')
                  svPairDisp = svPairSelf
                  indicesMakeGray.extend(indicesOther)
               if le.getValue() < 0:
                  txdir = self.tr('Sent')
                  svPairDisp = svPairOther
                  indicesMakeGray.extend(indicesSelf)
         except:
            pass
      

      # If this is a USTX, the above calculation probably didn't do its job
      # It is possible, but it's also possible that this Tx has nothing to
      # do with our wallet, which is not the focus of the above loop/conditions
      # So we choose to pass in the amount we already computed based on extra
      # information available in the USTX structure
      if precomputeAmt:
         txAmt = precomputeAmt


      layout = QGridLayout()
      lblDescr = QLabel(self.tr('Transaction Information:'))

      layout.addWidget(lblDescr, 0, 0, 1, 1)

      frm = QFrame()
      frm.setFrameStyle(STYLE_RAISED)
      frmLayout = QGridLayout()
      lbls = []



      # Show the transaction ID, with the user's preferred endianness
      # I hate BE, but block-explorer requires it so it's probably a better default
      endianness = self.main.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = ''
      if self.mode in (USERMODE.Advanced, USERMODE.Expert):
         estr = ' (BE)' if endianness == BIGENDIAN else ' (LE)'

      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr('Unique identifier for this transaction')))
      lbls[-1].append(QLabel(self.tr('Transaction ID' )+ estr + ':'))


      # Want to display the hash of the Tx if we have a valid one:
      # A USTX does not have a valid hash until it's completely signed, though
      longTxt = self.tr('[[ Transaction ID cannot be determined without all signatures ]]')
      w, h = relaxedSizeStr(QRichLabel(''), longTxt)

      tempPyTx = self.pytx.copy()
      if ustx:
         finalTx = ustx.getBroadcastTxIfReady(verifySigs=False)
         if finalTx:
            tempPyTx = finalTx.copy()
         else:
            tempPyTx = None
            lbls[-1].append(QRichLabel(self.tr('<font color="gray"> '
               '[[ Transaction ID cannot be determined without all signatures ]] '
               '</font>')))

      if tempPyTx:
         txHash = binary_to_hex(tempPyTx.getHash(), endOut=endianness)
         lbls[-1].append(QLabel(txHash))


      lbls[-1][-1].setMinimumWidth(w)

      if self.mode in (USERMODE.Expert,):
         # Add protocol version and locktime to the display
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(self.tr('Bitcoin Protocol Version Number')))
         lbls[-1].append(QLabel(self.tr('Tx Version:')))
         lbls[-1].append(QLabel(str(self.pytx.version)))

         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
            self.tr('The time at which this transaction becomes valid.')))
         lbls[-1].append(QLabel(self.tr('Lock-Time:')))
         if self.pytx.lockTime == 0:
            lbls[-1].append(QLabel(self.tr('Immediate (0)')))
         elif self.pytx.lockTime < 500000000:
            lbls[-1].append(QLabel(self.tr('Block %1').arg(self.pytx.lockTime)))
         else:
            lbls[-1].append(QLabel(unixTimeToFormatStr(self.pytx.lockTime)))



      lbls.append([])
      lbls[-1].append(self.main.createToolTipWidget(self.tr('Comment stored for this transaction in this wallet')))
      lbls[-1].append(QLabel(self.tr('User Comment:')))
      txhash_bin = hex_to_binary(txHash, endOut=endianness)
      comment_tx = ''
      if haveWallet:
         comment_tx = wlt.getComment(txhash_bin)
         if not comment_tx: # and tempPyTx:
            comment_tx = wlt.getAddrCommentIfAvail(txhash_bin)
            #for txout in tempPyTx.outputs:
             #  script = script_to_scrAddr(txout.getScript())


      if comment_tx:
         lbls[-1].append(QRichLabel(comment_tx))
      else:
         lbls[-1].append(QRichLabel(self.tr('<font color="gray">[None]</font>')))


      if not self.data[FIELDS.Time] == None:
         lbls.append([])
         if self.data[FIELDS.Blk] >= 2 ** 32 - 1:
            lbls[-1].append(self.main.createToolTipWidget(
                  self.tr('The time that you computer first saw this transaction')))
         else:
            lbls[-1].append(self.main.createToolTipWidget(
                  self.tr('All transactions are eventually included in a "block."  The '
                  'time shown here is the time that the block entered the "blockchain."')))
         lbls[-1].append(QLabel('Transaction Time:'))
         lbls[-1].append(QLabel(self.data[FIELDS.Time]))

      if not self.data[FIELDS.Blk] == None:
         nConf = 0
         if self.data[FIELDS.Blk] >= 2 ** 32 - 1:
            lbls.append([])
            lbls[-1].append(self.main.createToolTipWidget(
                  self.tr('This transaction has not yet been included in a block. '
                  'It usually takes 5-20 minutes for a transaction to get '
                  'included in a block after the user hits the "Send" button.')))
            lbls[-1].append(QLabel('Block Number:'))
            lbls[-1].append(QRichLabel('<i>Not in the blockchain yet</i>'))
         else:
            idxStr = ''
            if not self.data[FIELDS.Idx] == None and self.mode == USERMODE.Expert:
               idxStr ='  (Tx #%d)' % self.data[FIELDS.Idx]
            lbls.append([])
            lbls[-1].append(self.main.createToolTipWidget(
                  self.tr('Every transaction is eventually included in a "block" which '
                  'is where the transaction is permanently recorded.  A new block '
                  'is produced approximately every 10 minutes.')))
            lbls[-1].append(QLabel('Included in Block:'))
            lbls[-1].append(QRichLabel(str(self.data[FIELDS.Blk]) + idxStr))
            if TheBDM.getState() == BDM_BLOCKCHAIN_READY:
               nConf = TheBDM.getTopBlockHeight() - self.data[FIELDS.Blk] + 1
               lbls.append([])
               lbls[-1].append(self.main.createToolTipWidget(
                     self.tr('The number of blocks that have been produced since '
                     'this transaction entered the blockchain.  A transaction '
                     'with 6 or more confirmations is nearly impossible to reverse.')))
               lbls[-1].append(QLabel(self.tr('Confirmations:')))
               lbls[-1].append(QRichLabel(str(nConf)))

      isRBF = self.pytx.isRBF()
      if isRBF:
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
               self.tr('This transaction can be replaced by another transaction that '
               'spends the same inputs if the replacement transaction has '
               'a higher fee.')))
         lbls[-1].append(QLabel(self.tr('Mempool Replaceable: ')))
         lbls[-1].append(QRichLabel(str(isRBF)))




      if svPairDisp == None and precomputeAmt == None:
         # Couldn't determine recip/change outputs
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
               self.tr('Most transactions have at least a recipient output and a '
               'returned-change output.  You do not have enough information '
               'to determine which is which, and so this fields shows the sum '
               'of <b>all</b> outputs.')))
         lbls[-1].append(QLabel(self.tr('Sum of Outputs:')))
         lbls[-1].append(QLabel(coin2str(txAmt, maxZeros=1).strip() + '  BTC'))
      else:
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
               self.tr('Bitcoins were either sent or received, or sent-to-self')))
         lbls[-1].append(QLabel('Transaction Direction:'))
         lbls[-1].append(QRichLabel(txdir))

         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
               self.tr('The value shown here is the net effect on your '
               'wallet, including transaction fee.')))
         lbls[-1].append(QLabel('Transaction Amount:'))
         lbls[-1].append(QRichLabel(coin2str(txAmt, maxZeros=1).strip() + '  BTC'))
         if txAmt < 0:
            lbls[-1][-1].setText('<font color="red">' + lbls[-1][-1].text() + '</font> ')
         elif txAmt > 0:
            lbls[-1][-1].setText('<font color="green">' + lbls[-1][-1].text() + '</font> ')


      if not self.data[FIELDS.TxSize] == None:
         txsize = unicode(self.data[FIELDS.TxSize])
         txsize_str = self.tr("%1 bytes").arg(txsize)
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
            self.tr('Size of the transaction in bytes')))
         lbls[-1].append(QLabel(self.tr('Tx Size: ')))
         lbls[-1].append(QLabel(txsize_str))

      if not self.data[FIELDS.SumIn] == None:
         fee = self.data[FIELDS.SumIn] - self.data[FIELDS.SumOut]
         lbls.append([])
         lbls[-1].append(self.main.createToolTipWidget(
            self.tr('Transaction fees go to users supplying the Bitcoin network with '
            'computing power for processing transactions and maintaining security.')))
         lbls[-1].append(QLabel('Tx Fee Paid:'))
         
         fee_str = coin2str(fee, maxZeros=0).strip() + '  BTC'
         if not self.data[FIELDS.TxWeight] == None:
            fee_byte = float(fee) / float(self.data[FIELDS.TxWeight])
            fee_str += ' (%d sat/B)' % fee_byte 
         
         lbls[-1].append(QLabel(fee_str))





      lastRow = 0
      for row, lbl3 in enumerate(lbls):
         lastRow = row
         for i in range(3):
            lbl3[i].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl3[i].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                            Qt.TextSelectableByKeyboard)
         frmLayout.addWidget(lbl3[0], row, 0, 1, 1)
         frmLayout.addWidget(lbl3[1], row, 1, 1, 1)
         frmLayout.addWidget(lbl3[2], row, 3, 1, 2)

      spacer = QSpacerItem(20, 20)
      frmLayout.addItem(spacer, 0, 2, len(lbls), 1)

      # Show the list of recipients, if possible
      numShow = 3
      rlbls = []
      if svPairDisp is not None:
         numRV = len(svPairDisp)
         for i, sv in enumerate(svPairDisp):
            rlbls.append([])
            if i == 0:
               rlbls[-1].append(self.main.createToolTipWidget(
                  self.tr('All outputs of the transaction <b>excluding</b> change-'
                  'back-to-sender outputs.  If this list does not look '
                  'correct, it is possible that the change-output was '
                  'detected incorrectly -- please check the complete '
                  'input/output list below.')))
               rlbls[-1].append(QLabel(self.tr('Recipients:')))
            else:
               rlbls[-1].extend([QLabel(), QLabel()])

            rlbls[-1].append(QLabel(scrAddr_to_addrStr(sv[0])))
            if numRV > 1:
               rlbls[-1].append(QLabel(coin2str(sv[1], maxZeros=1) + '  BTC'))
            else:
               rlbls[-1].append(QLabel(''))
            ffixBold = GETFONT('Fixed', 10)
            ffixBold.setWeight(QFont.Bold)
            rlbls[-1][-1].setFont(ffixBold)

            if numRV > numShow and i == numShow - 2:
               moreStr = self.tr('[%1 more recipients]').arg(numRV - numShow + 1)
               rlbls.append([])
               rlbls[-1].extend([QLabel(), QLabel(), QLabel(moreStr), QLabel()])
               break


         # ##
         for i, lbl4 in enumerate(rlbls):
            for j in range(4):
               lbl4[j].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                            Qt.TextSelectableByKeyboard)
            row = lastRow + 1 + i
            frmLayout.addWidget(lbl4[0], row, 0, 1, 1)
            frmLayout.addWidget(lbl4[1], row, 1, 1, 1)
            frmLayout.addWidget(lbl4[2], row, 3, 1, 1)
            frmLayout.addWidget(lbl4[3], row, 4, 1, 1)



      # TxIns/Senders
      wWlt = relaxedSizeStr(GETFONT('Var'), 'A' * 10)[0]
      wAddr = relaxedSizeStr(GETFONT('Var'), 'A' * 31)[0]
      wAmt = relaxedSizeStr(GETFONT('Fixed'), 'A' * 20)[0]
      if ustx:
         self.txInModel = TxInDispModel(ustx, self.data[FIELDS.InList], self.main)
      else:
         self.txInModel = TxInDispModel(pytx, self.data[FIELDS.InList], self.main)
      self.txInView = QTableView()
      self.txInView.setModel(self.txInModel)
      self.txInView.setSelectionBehavior(QTableView.SelectRows)
      self.txInView.setSelectionMode(QTableView.SingleSelection)
      self.txInView.horizontalHeader().setStretchLastSection(True)
      self.txInView.verticalHeader().setDefaultSectionSize(20)
      self.txInView.verticalHeader().hide()
      w, h = tightSizeNChar(self.txInView, 1)
      self.txInView.setMinimumHeight(2 * (1.4 * h))
      #self.txInView.setMaximumHeight(5 * (1.4 * h))
      self.txInView.hideColumn(TXINCOLS.OutPt)
      self.txInView.hideColumn(TXINCOLS.OutIdx)
      self.txInView.hideColumn(TXINCOLS.Script)
      self.txInView.hideColumn(TXINCOLS.AddrStr)

      if self.mode == USERMODE.Standard:
         initialColResize(self.txInView, [wWlt, wAddr, wAmt, 0, 0, 0, 0, 0, 0])
         self.txInView.hideColumn(TXINCOLS.FromBlk)
         self.txInView.hideColumn(TXINCOLS.ScrType)
         self.txInView.hideColumn(TXINCOLS.Sequence)
         # self.txInView.setSelectionMode(QTableView.NoSelection)
      elif self.mode == USERMODE.Advanced:
         initialColResize(self.txInView, [0.8 * wWlt, 0.6 * wAddr, wAmt, 0, 0, 0, 0.2, 0, 0])
         self.txInView.hideColumn(TXINCOLS.FromBlk)
         self.txInView.hideColumn(TXINCOLS.Sequence)
         # self.txInView.setSelectionMode(QTableView.NoSelection)
      elif self.mode == USERMODE.Expert:
         self.txInView.resizeColumnsToContents()

      self.txInView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.txInView.customContextMenuRequested.connect(self.showContextMenuTxIn)

      # List of TxOuts/Recipients
      if not precomputeIdxGray is None:
         indicesMakeGray = precomputeIdxGray[:]
      self.txOutModel = TxOutDispModel(self.pytx, self.main, idxGray=indicesMakeGray)
      self.txOutView = QTableView()
      self.txOutView.setModel(self.txOutModel)
      self.txOutView.setSelectionBehavior(QTableView.SelectRows)
      self.txOutView.setSelectionMode(QTableView.SingleSelection)
      self.txOutView.verticalHeader().setDefaultSectionSize(20)
      self.txOutView.verticalHeader().hide()
      self.txOutView.setMinimumHeight(2 * (1.3 * h))
      #self.txOutView.setMaximumHeight(5 * (1.3 * h))
      initialColResize(self.txOutView, [wWlt, 0.8 * wAddr, wAmt, 0.25, 0])
      self.txOutView.hideColumn(TXOUTCOLS.Script)
      self.txOutView.hideColumn(TXOUTCOLS.AddrStr)
      if self.mode == USERMODE.Standard:
         self.txOutView.hideColumn(TXOUTCOLS.ScrType)
         initialColResize(self.txOutView, [wWlt, wAddr, 0.25, 0, 0])
         self.txOutView.horizontalHeader().setStretchLastSection(True)
         # self.txOutView.setSelectionMode(QTableView.NoSelection)
      elif self.mode == USERMODE.Advanced:
         initialColResize(self.txOutView, [0.8 * wWlt, 0.6 * wAddr, wAmt, 0.25, 0])
         # self.txOutView.setSelectionMode(QTableView.NoSelection)
      elif self.mode == USERMODE.Expert:
         initialColResize(self.txOutView, [wWlt, wAddr, wAmt, 0.25, 0])
      # self.txOutView.resizeColumnsToContents()

      self.txOutView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.txOutView.customContextMenuRequested.connect(self.showContextMenuTxOut)

      self.lblTxioInfo = QRichLabel('')
      self.lblTxioInfo.setMinimumWidth(tightSizeNChar(self.lblTxioInfo, 30)[0])
      self.connect(self.txInView, SIGNAL('clicked(QModelIndex)'), \
                   lambda: self.dispTxioInfo('In'))
      self.connect(self.txOutView, SIGNAL('clicked(QModelIndex)'), \
                   lambda: self.dispTxioInfo('Out'))

      self.connect(self.txInView, SIGNAL('doubleClicked(QModelIndex)'), self.showTxInDialog)
      self.connect(self.txOutView, SIGNAL('doubleClicked(QModelIndex)'), self.showTxOutDialog)

      # scrFrm = QFrame()
      # scrFrm.setFrameStyle(STYLE_SUNKEN)
      # scrFrmLayout = Q


      self.scriptArea = QScrollArea()
      self.scriptArea.setWidget(self.lblTxioInfo)
      self.scriptFrm = makeLayoutFrame(HORIZONTAL, [self.scriptArea])
      # self.scriptFrm.setMaximumWidth(150)
      self.scriptArea.setMaximumWidth(200)

      self.frmIOList = QFrame()
      self.frmIOList.setFrameStyle(STYLE_SUNKEN)
      frmIOListLayout = QGridLayout()

      lblInputs = QLabel(self.tr('Transaction Inputs (Sending addresses):'))
      ttipText = (self.tr('All transactions require previous transaction outputs as inputs.'))
      if not haveBDM:
         ttipText += (self.tr('<b>Since the blockchain is not available, not all input '
                      'information is available</b>.  You need to view this '
                      'transaction on a system with an internet connection '
                      '(and blockchain) if you want to see the complete information.'))
      else:
         ttipText += (self.tr('Each input is like an X amount dollar bill.  Usually there are more inputs '
                      'than necessary for the transaction, and there will be an extra '
                      'output returning change to the sender'))
      ttipInputs = self.main.createToolTipWidget(ttipText)

      lblOutputs = QLabel(self.tr('Transaction Outputs (Receiving addresses):'))
      ttipOutputs = self.main.createToolTipWidget(
                  self.tr('Shows <b>all</b> outputs, including other recipients '
                  'of the same transaction, and change-back-to-sender outputs '
                  '(change outputs are displayed in light gray).'))

      self.lblChangeDescr = QRichLabel( self.tr('Some outputs might be "change."'), doWrap=False)
      self.lblChangeDescr.setOpenExternalLinks(True)



      inStrip = makeLayoutFrame(HORIZONTAL, [lblInputs, ttipInputs, STRETCH])
      outStrip = makeLayoutFrame(HORIZONTAL, [lblOutputs, ttipOutputs, STRETCH])

      frmIOListLayout.addWidget(inStrip, 0, 0, 1, 1)
      frmIOListLayout.addWidget(self.txInView, 1, 0, 1, 1)
      frmIOListLayout.addWidget(outStrip, 2, 0, 1, 1)
      frmIOListLayout.addWidget(self.txOutView, 3, 0, 1, 1)
      # frmIOListLayout.addWidget(self.lblTxioInfo, 0,1, 4,1)
      self.frmIOList.setLayout(frmIOListLayout)


      self.btnIOList = QPushButton('')
      self.btnCopy = QPushButton(self.tr('Copy Raw Tx (Hex)'))
      self.lblCopied = QRichLabel('')
      self.btnOk = QPushButton(self.tr('OK'))
      self.btnIOList.setCheckable(True)
      self.connect(self.btnIOList, SIGNAL(CLICKED), self.extraInfoClicked)
      self.connect(self.btnOk, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnCopy, SIGNAL(CLICKED), self.copyRawTx)

      btnStrip = makeHorizFrame([self.btnIOList,
                                 self.btnCopy,
                                 self.lblCopied,
                                 'Stretch',
                                 self.lblChangeDescr,
                                 'Stretch',
                                 self.btnOk])

      if not self.mode == USERMODE.Expert:
         self.btnCopy.setVisible(False)


      if self.mode == USERMODE.Standard:
         self.btnIOList.setChecked(False)
      else:
         self.btnIOList.setChecked(True)
      self.extraInfoClicked()


      frm.setLayout(frmLayout)
      layout.addWidget(frm, 2, 0, 1, 1)
      layout.addWidget(self.scriptArea, 2, 1, 1, 1)
      layout.addWidget(self.frmIOList, 3, 0, 1, 2)
      layout.addWidget(btnStrip, 4, 0, 1, 2)

      # bbox = QDialogButtonBox(QDialogButtonBox.Ok)
      # self.connect(bbox, SIGNAL('accepted()'), self.accept)
      # layout.addWidget(bbox, 6,0, 1,1)

      self.setLayout(layout)
      #self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.setWindowTitle(self.tr('Transaction Info'))



   def extraInfoClicked(self):
      if self.btnIOList.isChecked():
         self.frmIOList.setVisible(True)
         self.btnCopy.setVisible(True)
         self.lblCopied.setVisible(True)
         self.btnIOList.setText(self.tr('<<< Less Info'))
         self.lblChangeDescr.setVisible(True)
         self.scriptArea.setVisible(False) # self.mode == USERMODE.Expert)
         # Disabling script area now that you can double-click to get it
      else:
         self.frmIOList.setVisible(False)
         self.scriptArea.setVisible(False)
         self.btnCopy.setVisible(False)
         self.lblCopied.setVisible(False)
         self.lblChangeDescr.setVisible(False)
         self.btnIOList.setText(self.tr('Advanced >>>'))

   def dispTxioInfo(self, InOrOut):
      hexScript = None
      headStr = None
      if InOrOut == 'In':
         selection = self.txInView.selectedIndexes()
         if len(selection) == 0:
            return
         row = selection[0].row()
         hexScript = str(self.txInView.model().index(row, TXINCOLS.Script).data().toString())
         headStr = self.tr('TxIn Script:')
      elif InOrOut == 'Out':
         selection = self.txOutView.selectedIndexes()
         if len(selection) == 0:
            return
         row = selection[0].row()
         hexScript = str(self.txOutView.model().index(row, TXOUTCOLS.Script).data().toString())
         headStr = self.tr('TxOut Script:')


      if hexScript:
         binScript = hex_to_binary(hexScript)
         addrStr = None
         scrType = getTxOutScriptType(binScript)
         if scrType in CPP_TXOUT_HAS_ADDRSTR:
            addrStr = script_to_addrStr(binScript)

         oplist = convertScriptToOpStrings(hex_to_binary(hexScript))
         opprint = []
         prevOpIsPushData = False
         for op in oplist:

            if addrStr is None or not prevOpIsPushData:
               opprint.append(op)
            else:
               opprint.append(op + ' <font color="gray">(%s)</font>' % addrStr)
               prevOpIsPushData = False

            if 'pushdata' in op.lower():
               prevOpIsPushData = True

         lblScript = QRichLabel('')
         lblScript.setText('<b>Script:</b><br><br>' + '<br>'.join(opprint))
         lblScript.setWordWrap(False)
         lblScript.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                        Qt.TextSelectableByKeyboard)

         self.scriptArea.setWidget(makeLayoutFrame(VERTICAL, [lblScript]))
         self.scriptArea.setMaximumWidth(200)


   def copyRawTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      #print "Binscript: " + binary_to_hex(self.pytx.inputs[0].binScript)
      clipb.setText(binary_to_hex(self.pytx.serialize()))
      self.lblCopied.setText(self.tr('<i>Copied to Clipboard!</i>'))


   #############################################################################
   def showTxInDialog(self, *args):
      # I really should've just used a dictionary instead of list with enum indices
      FIELDS = enum('Hash', 'OutList', 'SumOut', 'InList', 'SumIn', 'Time', 'Blk', 'Idx')
      try:
         idx = self.txInView.selectedIndexes()[0].row()
         DlgDisplayTxIn(self, self.main, self.pytx, idx, self.data[FIELDS.InList]).exec_()
      except:
         LOGEXCEPT('Error showing TxIn')

   #############################################################################
   def showTxOutDialog(self, *args):
      # I really should've just used a dictionary instead of list with enum indices
      FIELDS = enum('Hash', 'OutList', 'SumOut', 'InList', 'SumIn', 'Time', 'Blk', 'Idx')
      try:
         idx = self.txOutView.selectedIndexes()[0].row()
         DlgDisplayTxOut(self, self.main, self.pytx, idx).exec_()
      except:
         LOGEXCEPT('Error showing TxOut')

   #############################################################################
   def showContextMenuTxIn(self, pos):
      menu = QMenu(self.txInView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:   actCopySender = menu.addAction(self.tr("Copy Sender Address"))
      if True:   actCopyWltID = menu.addAction(self.tr("Copy Wallet ID"))
      if True:   actCopyAmount = menu.addAction(self.tr("Copy Amount"))
      if True:   actMoreInfo = menu.addAction(self.tr("More Info"))
      idx = self.txInView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())

      if action == actMoreInfo:
         self.showTxInDialog()
      if action == actCopyWltID:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.WltID).data().toString())
      elif action == actCopySender:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.Sender).data().toString())
      elif action == actCopyAmount:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.Btc).data().toString())
      #elif dev and action == actCopyOutPt:
         #s1 = str(self.txInView.model().index(idx.row(), TXINCOLS.OutPt).data().toString())
         #s2 = str(self.txInView.model().index(idx.row(), TXINCOLS.OutIdx).data().toString())
         #s = s1 + ':' + s2
      #elif dev and action == actCopyScript:
         #s = str(self.txInView.model().index(idx.row(), TXINCOLS.Script).data().toString())
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(s.strip())

   #############################################################################
   def showContextMenuTxOut(self, pos):
      menu = QMenu(self.txOutView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:   actCopyRecip  = menu.addAction(self.tr("Copy Recipient Address"))
      if True:   actCopyWltID  = menu.addAction(self.tr("Copy Wallet ID"))
      if True:   actCopyAmount = menu.addAction(self.tr("Copy Amount"))
      if dev:    actCopyScript = menu.addAction(self.tr("Copy Raw Script"))
      idx = self.txOutView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())

      if action == actCopyWltID:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.WltID).data().toString()
      elif action == actCopyRecip:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.AddrStr).data().toString()
      elif action == actCopyAmount:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.Btc).data().toString()
      elif dev and action == actCopyScript:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.Script).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())



################################################################################
class DlgDisplayTxIn(ArmoryDialog):
   def __init__(self, parent, main, pytxOrUstx, txiIndex, txinListFromBDM=None):
      super(DlgDisplayTxIn, self).__init__(parent, main)

      lblDescr = QRichLabel(self.tr("<center><u><b>TxIn Information</b></u></center>"))

      edtBrowse = QTextBrowser()
      edtBrowse.setFont(GETFONT('Fixed', 9))
      edtBrowse.setReadOnly(True)
      edtBrowse.setLineWrapMode(QTextEdit.NoWrap)

      ustx = None
      pytx = pytxOrUstx
      if isinstance(pytx, UnsignedTransaction):
         ustx = pytx
         pytx = ustx.getPyTxSignedIfPossible()

      txin = pytx.inputs[txiIndex]
      scrType  = getTxInScriptType(txin)
      typeName = CPP_TXIN_SCRIPT_NAMES[scrType]
      txHashBE = binary_to_hex(txin.outpoint.txHash, BIGENDIAN)
      txIdxBE  = int_to_hex(txin.outpoint.txOutIndex, 4, BIGENDIAN)
      seqHexBE = int_to_hex(txin.intSeq, 4, BIGENDIAN)
      opStrings = convertScriptToOpStrings(txin.binScript)

      senderAddr = TxInExtractAddrStrIfAvail(txin)
      srcStr = ''
      if not senderAddr:
         senderAddr = self.tr('[[Cannot determine from TxIn Script]]')
      else:
         wltID  = self.main.getWalletForAddr160(addrStr_to_hash160(senderAddr)[1])
         if wltID:
            wlt = self.main.walletMap[wltID]
            srcStr = self.tr('Wallet "%1" (%2)').arg(wlt.labelName, wlt.uniqueIDB58)
         else:
            lbox = self.main.getLockboxByP2SHAddrStr(senderAddr)
            if lbox:
               srcStr = self.tr('Lockbox %1-of-%2 "%3" (%4)').arg(lbox.M, lbox.N, lbox.shortName, lbox.uniqueIDB58)



      dispLines = []
      dispLines.append(self.tr('<font size=4><u><b>Information on TxIn</b></u></font>:'))
      dispLines.append(self.tr('   <b>TxIn Index:</b>         %1').arg(txiIndex))
      dispLines.append(self.tr('   <b>TxIn Spending:</b>      %1:%2').arg(txHashBE, txIdxBE))
      dispLines.append(self.tr('   <b>TxIn Sequence</b>:      0x%1').arg(seqHexBE))
      if len(txin.binScript)>0:
         dispLines.append(self.tr('   <b>TxIn Script Type</b>:   %1').arg(typeName))
         dispLines.append(self.tr('   <b>TxIn Source</b>:        %1').arg(senderAddr))
         if srcStr:
            dispLines.append(self.tr('   <b>TxIn Wallet</b>:        %1').arg(srcStr))
         dispLines.append(self.tr('   <b>TxIn Script</b>:'))
         for op in opStrings:
            dispLines.append('      %s' % op)

      wltID = ''
      scrType = getTxInScriptType(txin)
      if txinListFromBDM and len(txinListFromBDM[txiIndex][0])>0:

         # We had a BDM to help us get info on each input -- use it
         scrAddr,val,blk,hsh,idx,script = txinListFromBDM[txiIndex]
         scrType = getTxOutScriptType(script)

         dispInfo = self.main.getDisplayStringForScript(script, 100, prefIDOverAddr=True)
         #print dispInfo
         addrStr = dispInfo['String']
         wltID   = dispInfo['WltID']
         if not wltID:
            wltID  = dispInfo['LboxID']
         if not wltID:
            wltID = ''

         wouldBeAddrStr = dispInfo['AddrStr']


         dispLines.append('')
         dispLines.append('')
         dispLines.append(self.tr('<font size=4><u><b>Information on TxOut being spent by this TxIn</b></u></font>:'))
         dispLines.append(self.tr('   <b>Tx Hash:</b>            %1').arg(txHashBE))
         dispLines.append(self.tr('   <b>Tx Out Index:</b>       %1').arg(txin.outpoint.txOutIndex))
         dispLines.append(self.tr('   <b>Tx in Block#:</b>       %1').arg(str(blk)))
         dispLines.append(self.tr('   <b>TxOut Value:</b>        %1').arg(coin2strNZS(val)))
         dispLines.append(self.tr('   <b>TxOut Script Type:</b>  %1').arg(CPP_TXOUT_SCRIPT_NAMES[scrType]))
         dispLines.append(self.tr('   <b>TxOut Address:</b>      %1').arg(wouldBeAddrStr))
         if wltID:
            dispLines.append(self.tr('   <b>TxOut Wallet:</b>       %1').arg(dispInfo['String']))
         dispLines.append(self.tr('   <b>TxOUt Script:</b>'))
         opStrings = convertScriptToOpStrings(script)
         for op in opStrings:
            dispLines.append('      %s' % op)

      u_string = u""
      for dline in dispLines:
         if isinstance(dline, QString):
            line_to_str = unicode(dline.toUtf8())
         else:
            line_to_str = unicode(dline)
         u_string = u_string + u"<br>" + line_to_str.replace(u' ', u'&nbsp;')
         
      edtBrowse.setHtml(u_string)
      btnDone = QPushButton(self.tr("Ok"))
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)

      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(edtBrowse)
      layout.addWidget(makeHorizFrame(['Stretch', btnDone]))
      self.setLayout(layout)
      w,h = tightSizeNChar(edtBrowse, 100)
      self.setMinimumWidth(max(w, 500))
      self.setMinimumHeight(max(20*h, 400))


################################################################################
class DlgDisplayTxOut(ArmoryDialog):
   def __init__(self, parent, main, pytxOrUstx, txoIndex):
      super(DlgDisplayTxOut, self).__init__(parent, main)

      lblDescr = QRichLabel(self.tr("<center><u><b>TxOut Information</b></u></center>"))

      edtBrowse = QTextBrowser()
      edtBrowse.setFont(GETFONT('Fixed', 9))
      edtBrowse.setReadOnly(True)
      edtBrowse.setLineWrapMode(QTextEdit.NoWrap)

      ustx = None
      pytx = pytxOrUstx
      if isinstance(pytx, UnsignedTransaction):
         ustx = pytx
         pytx = ustx.getPyTxSignedIfPossible()

      wltID = ''

      dispLines = []

      txout   = pytx.outputs[txoIndex]
      val     = txout.value
      script  = txout.binScript
      scrAddr = script_to_scrAddr(script)
      scrType = getTxOutScriptType(script)

      dispInfo = self.main.getDisplayStringForScript(script, 100, prefIDOverAddr=True)
      #print dispInfo
      addrStr = dispInfo['String']
      wltID   = dispInfo['WltID']
      if not wltID:
         wltID  = dispInfo['LboxID']
      if not wltID:
         wltID = ''

      wouldBeAddrStr = dispInfo['AddrStr']

      dispLines.append(self.tr('<font size=4><u><b>Information on TxOut</b></u></font>:'))
      dispLines.append(self.tr('   <b>Tx Out Index:</b>       %1').arg(txoIndex))
      dispLines.append(self.tr('   <b>TxOut Value:</b>        %1').arg(coin2strNZS(val)))
      dispLines.append(self.tr('   <b>TxOut Script Type:</b>  %1').arg(CPP_TXOUT_SCRIPT_NAMES[scrType]))
      dispLines.append(self.tr('   <b>TxOut Address:</b>      %1').arg(wouldBeAddrStr))
      if wltID:
         dispLines.append(self.tr('   <b>TxOut Wallet:</b>       %1').arg(dispInfo['String']))
      else:
         dispLines.append(self.tr('   <b>TxOut Wallet:</b>       [[Unrelated to any loaded wallets]]'))
      dispLines.append(self.tr('   <b>TxOut Script:</b>'))
      opStrings = convertScriptToOpStrings(script)
      for op in opStrings:
         dispLines.append('      %s' % op)

      u_string = u""
      for dline in dispLines:
         if isinstance(dline, QString):
            line_to_str = unicode(dline.toUtf8())
         else:
            line_to_str = unicode(dline)
         u_string = u_string + u"<br>" + line_to_str.replace(u' ', u'&nbsp;')
         
      edtBrowse.setHtml(u_string)
      btnDone = QPushButton(self.tr("Ok"))
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)

      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(edtBrowse)
      layout.addWidget(makeHorizFrame(['Stretch', btnDone]))
      self.setLayout(layout)
      w,h = tightSizeNChar(edtBrowse, 100)
      self.setMinimumWidth(max(w, 500))
      self.setMinimumHeight(max(20*h, 400))

class GfxViewPaper(QGraphicsView):
   def __init__(self, parent=None, main=None):
      super(GfxViewPaper, self).__init__(parent)
      self.setRenderHint(QPainter.TextAntialiasing)

class GfxItemText(QGraphicsTextItem):
   """
   So far, I'm pretty bad at setting the boundingRect properly.  I have
   hacked it to be usable for this specific situation, but it's not very
   reusable...
   """
   def __init__(self, text, position, scene, font=GETFONT('Courier', 8), lineWidth=None):
      super(GfxItemText, self).__init__(text)
      self.setFont(font)
      self.setPos(position)
      if lineWidth:
         self.setTextWidth(lineWidth)

      self.setDefaultTextColor(self.PAGE_TEXT_COLOR)

   def boundingRect(self):
      w, h = relaxedSizeStr(self, self.toPlainText())
      nLine = 1
      if self.textWidth() > 0:
         twid = self.textWidth()
         nLine = max(1, int(float(w) / float(twid) + 0.5))
      return QRectF(0, 0, w, nLine * (1.5 * h))


class GfxItemQRCode(QGraphicsItem):
   """
   Converts binary data to base58, and encodes the Base58 characters in
   the QR-code.  It seems weird to use Base58 instead of binary, but the
   QR-code has no problem with the size, instead, we want the data in the
   QR-code to match exactly what is human-readable on the page, which is
   in Base58.

   You must supply exactly one of "totalSize" or "modSize".  TotalSize
   guarantees that the QR code will fit insides box of a given size.
   ModSize is how big each module/pixel of the QR code is, which means
   that a bigger QR block results in a bigger physical size on paper.
   """
   def __init__(self, rawDataToEncode, maxSize=None):
      super(GfxItemQRCode, self).__init__()
      self.maxSize = maxSize
      self.updateQRData(rawDataToEncode)

   def boundingRect(self):
      return self.Rect

   def updateQRData(self, toEncode, maxSize=None):
      if maxSize == None:
         maxSize = self.maxSize
      else:
         self.maxSize = maxSize

      self.qrmtrx, self.modCt = CreateQRMatrix(toEncode, 'H')
      self.modSz = round(float(self.maxSize) / float(self.modCt) - 0.5)
      totalSize = self.modCt * self.modSz
      self.Rect = QRectF(0, 0, totalSize, totalSize)

   def paint(self, painter, option, widget=None):
      painter.setPen(Qt.NoPen)
      painter.setBrush(QBrush(QColor(0, 0, 0)))

      for r in range(self.modCt):
         for c in range(self.modCt):
            if self.qrmtrx[r][c] > 0:
               painter.drawRect(*[self.modSz * a for a in [r, c, 1, 1]])


class SimplePrintableGraphicsScene(object):


   def __init__(self, parent, main):
      """
      We use the following coordinates:

            -----> +x
            |
            |
            V +y

      """
      self.parent = parent
      self.main = main

      self.INCH = 72
      self.PAPER_A4_WIDTH = 8.5 * self.INCH
      self.PAPER_A4_HEIGHT = 11.0 * self.INCH
      self.MARGIN_PIXELS = 0.6 * self.INCH

      self.PAGE_BKGD_COLOR = QColor(255, 255, 255)
      self.PAGE_TEXT_COLOR = QColor(0, 0, 0)

      self.fontFix = GETFONT('Courier', 9)
      self.fontVar = GETFONT('Times', 10)

      self.gfxScene = QGraphicsScene(self.parent)
      self.gfxScene.setSceneRect(0, 0, self.PAPER_A4_WIDTH, self.PAPER_A4_HEIGHT)
      self.gfxScene.setBackgroundBrush(self.PAGE_BKGD_COLOR)

      # For when it eventually makes it to the printer
      # self.printer = QPrinter(QPrinter.HighResolution)
      # self.printer.setPageSize(QPrinter.Letter)
      # self.gfxPainter = QPainter(self.printer)
      # self.gfxPainter.setRenderHint(QPainter.TextAntialiasing)
      # self.gfxPainter.setPen(Qt.NoPen)
      # self.gfxPainter.setBrush(QBrush(self.PAGE_TEXT_COLOR))

      self.cursorPos = QPointF(self.MARGIN_PIXELS, self.MARGIN_PIXELS)
      self.lastCursorMove = (0, 0)


   def getCursorXY(self):
      return (self.cursorPos.x(), self.cursorPos.y())

   def getScene(self):
      return self.gfxScene

   def pageRect(self):
      marg = self.MARGIN_PIXELS
      return QRectF(marg, marg, self.PAPER_A4_WIDTH - marg, self.PAPER_A4_HEIGHT - marg)

   def insidePageRect(self, pt=None):
      if pt == None:
         pt = self.cursorPos

      return self.pageRect.contains(pt)

   def moveCursor(self, dx, dy, absolute=False):
      xOld, yOld = self.getCursorXY()
      if absolute:
         self.cursorPos = QPointF(dx, dy)
         self.lastCursorMove = (dx - xOld, dy - yOld)
      else:
         self.cursorPos = QPointF(xOld + dx, yOld + dy)
         self.lastCursorMove = (dx, dy)


   def resetScene(self):
      self.gfxScene.clear()
      self.resetCursor()

   def resetCursor(self):
      self.cursorPos = QPointF(self.MARGIN_PIXELS, self.MARGIN_PIXELS)


   def newLine(self, extra_dy=0):
      xOld, yOld = self.getCursorXY()
      xNew = self.MARGIN_PIXELS
      yNew = self.cursorPos.y() + self.lastItemSize[1] + extra_dy - 5
      self.moveCursor(xNew - xOld, yNew - yOld)


   def drawHLine(self, width=None, penWidth=1):
      if width == None:
         width = 3 * self.INCH
      currX, currY = self.getCursorXY()
      lineItem = QGraphicsLineItem(currX, currY, currX + width, currY)
      pen = QPen()
      pen.setWidth(penWidth)
      lineItem.setPen(pen)
      self.gfxScene.addItem(lineItem)
      rect = lineItem.boundingRect()
      self.lastItemSize = (rect.width(), rect.height())
      self.moveCursor(rect.width(), 0)
      return self.lastItemSize

   def drawRect(self, w, h, edgeColor=QColor(0, 0, 0), fillColor=None, penWidth=1):
      rectItem = QGraphicsRectItem(self.cursorPos.x(), self.cursorPos.y(), w, h)
      if edgeColor == None:
         rectItem.setPen(QPen(Qt.NoPen))
      else:
         pen = QPen(edgeColor)
         pen.setWidth(penWidth)
         rectItem.setPen(pen)

      if fillColor == None:
         rectItem.setBrush(QBrush(Qt.NoBrush))
      else:
         rectItem.setBrush(QBrush(fillColor))

      self.gfxScene.addItem(rectItem)
      rect = rectItem.boundingRect()
      self.lastItemSize = (rect.width(), rect.height())
      self.moveCursor(rect.width(), 0)
      return self.lastItemSize


   def drawText(self, txt, font=None, wrapWidth=None, useHtml=True):
      if font == None:
         font = GETFONT('Var', 9)
      txtItem = QGraphicsTextItem('')
      if useHtml:
         txtItem.setHtml(toUnicode(txt))
      else:
         txtItem.setPlainText(toUnicode(txt))
      txtItem.setDefaultTextColor(self.PAGE_TEXT_COLOR)
      txtItem.setPos(self.cursorPos)
      txtItem.setFont(font)
      if not wrapWidth == None:
         txtItem.setTextWidth(wrapWidth)
      self.gfxScene.addItem(txtItem)
      rect = txtItem.boundingRect()
      self.lastItemSize = (rect.width(), rect.height())
      self.moveCursor(rect.width(), 0)
      return self.lastItemSize

   def drawPixmapFile(self, pixFn, sizePx=None):
      pix = QPixmap(pixFn)
      if not sizePx == None:
         pix = pix.scaled(sizePx, sizePx)
      pixItem = QGraphicsPixmapItem(pix)
      pixItem.setPos(self.cursorPos)
      pixItem.setMatrix(QMatrix())
      self.gfxScene.addItem(pixItem)
      rect = pixItem.boundingRect()
      self.lastItemSize = (rect.width(), rect.height())
      self.moveCursor(rect.width(), 0)
      return self.lastItemSize

   def drawQR(self, qrdata, size=150):
      objQR = GfxItemQRCode(qrdata, size)
      objQR.setPos(self.cursorPos)
      objQR.setMatrix(QMatrix())
      self.gfxScene.addItem(objQR)
      rect = objQR.boundingRect()
      self.lastItemSize = (rect.width(), rect.height())
      self.moveCursor(rect.width(), 0)
      return self.lastItemSize


   def drawColumn(self, strList, rowHeight=None, font=None, useHtml=True):
      """
      This draws a bunch of left-justified strings in a column.  It returns
      a tight bounding box around all elements in the column, which can easily
      be used to start the next column.  The rowHeight is returned, and also
      an available input, in case you are drawing text/font that has a different
      height in each column, and want to make sure they stay aligned.

      Just like the other methods, this leaves the cursor sitting at the
      original y-value, but shifted to the right by the width of the column.
      """
      origX, origY = self.getCursorXY()
      maxColWidth = 0
      cumulativeY = 0
      for r in strList:
         szX, szY = self.drawText(r, font=font, useHtml=useHtml)
         prevY = self.cursorPos.y()
         if rowHeight == None:
            self.newLine()
            szY = self.cursorPos.y() - prevY
            self.moveCursor(origX - self.MARGIN_PIXELS, 0)
         else:
            self.moveCursor(-szX, rowHeight)
         maxColWidth = max(maxColWidth, szX)
         cumulativeY += szY

      if rowHeight == None:
         rowHeight = float(cumulativeY) / len(strList)

      self.moveCursor(origX + maxColWidth, origY, absolute=True)

      return [QRectF(origX, origY, maxColWidth, cumulativeY), rowHeight]



class DlgPrintBackup(ArmoryDialog):
   """
   Open up a "Make Paper Backup" dialog, so the user can print out a hard
   copy of whatever data they need to recover their wallet should they lose
   it.

   This method is kind of a mess, because it ended up having to support
   printing of single-sheet, imported keys, single fragments, multiple
   fragments, with-or-without SecurePrint.
   """
   def __init__(self, parent, main, wlt, printType='SingleSheet', \
                                    fragMtrx=[], fragMtrxCrypt=[], fragData=[],
                                    privKey=None, chaincode=None):
      super(DlgPrintBackup, self).__init__(parent, main)


      self.wlt = wlt
      self.binMask = SecureBinaryData(0)
      self.binPriv = wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
      self.binChain = wlt.addrMap['ROOT'].chaincode.copy()

      # This badBackup stuff was implemented to avoid making backups if there is
      # an inconsistency in the data.  Yes, this is like a goto!
      try:
         if privKey:
            if not chaincode:
               raise KeyDataError
            self.binPriv = privKey.copy()
            self.binChain = chaincode.copy()

         if self.binPriv.getSize() < 32:
            raise KeyDataError

      except:
         LOGEXCEPT("Problem with private key and/or chaincode.  Aborting.")
         QMessageBox.critical(self, self.tr("Error Creating Backup"), self.tr(
            'There was an error with the backup creator.  The operation is being '
            'canceled to avoid making bad backups!'), QMessageBox.Ok)
         return


      self.binImport = []
      self.fragMtrx = fragMtrx

      self.doPrintFrag = printType.lower().startswith('frag')
      self.fragMtrx = fragMtrx
      self.fragMtrxCrypt = fragMtrxCrypt
      self.fragData = fragData
      if self.doPrintFrag:
         self.doMultiFrag = len(fragData['Range']) > 1

      # A self-evident check of whether we need to print the chaincode.
      # If we derive the chaincode from the private key, and it matches
      # what's already in the wallet, we obviously don't need to print it!
      testChain = DeriveChaincodeFromRootKey(self.binPriv)
      self.noNeedChaincode = (testChain == self.binChain)

      # Save off imported addresses in case they need to be printed, too
      for a160, addr in self.wlt.addrMap.iteritems():
         if addr.chainIndex == -2:
            if addr.binPrivKey32_Plain.getSize() == 33 or addr.isCompressed():
               prv = addr.binPrivKey32_Plain.toBinStr()[:32]
               self.binImport.append([a160, SecureBinaryData(prv), 1])
               prv = None
            else:
               self.binImport.append([a160, addr.binPrivKey32_Plain.copy(), 0])


      # USE PRINTER MASK TO PREVENT NETWORK DEVICES FROM SEEING PRIVATE KEYS
      # Hardcode salt & IV because they should *never* change.
      # Rainbow tables aren't all that useful here because the user
      # is not creating the password -- it's *essentially* randomized
      # with 64-bits of real entropy. (though, it is deterministic
      # based on the private key, so that printing the backup multiple
      # times will produce the same password).
      SECPRINT = HardcodedKeyMaskParams()

      start = RightNow()
      self.randpass = SECPRINT['FUNC_PWD'](self.binPriv + self.binChain)
      self.binCrypt32 = SECPRINT['FUNC_KDF'](self.randpass)
      LOGINFO('Deriving SecurePrint code took %0.2f seconds' % (RightNow() - start))

      MASK = lambda x: SECPRINT['FUNC_MASK'](x, ekey=self.binCrypt32)

      self.binPrivCrypt = MASK(self.binPriv)
      self.binChainCrypt = MASK(self.binChain)

      self.binImportCrypt = []
      for i in range(len(self.binImport)):
         self.binImportCrypt.append([      self.binImport[i][0], \
                                      MASK(self.binImport[i][1]), \
                                           self.binImport[i][2]   ])

      # If there is data in the fragments matrix, also convert it
      if len(self.fragMtrx) > 0:
         self.fragMtrxCrypt = []
         for sbdX, sbdY in self.fragMtrx:
            self.fragMtrxCrypt.append([sbdX.copy(), MASK(sbdY)])

      self.binCrypt32.destroy()


      # We need to figure out how many imported keys fit on one page
      tempTxtItem = QGraphicsTextItem('')
      tempTxtItem.setPlainText(toUnicode('0123QAZjqlmYy'))
      tempTxtItem.setFont(GETFONT('Fix', 7))
      self.importHgt = tempTxtItem.boundingRect().height() - 5


      # Create the scene and the view.
      self.scene = SimplePrintableGraphicsScene(self, self.main)
      self.view = QGraphicsView()
      self.view.setRenderHint(QPainter.TextAntialiasing)
      self.view.setScene(self.scene.getScene())


      self.chkImportPrint = QCheckBox(self.tr('Print imported keys'))
      self.connect(self.chkImportPrint, SIGNAL(CLICKED), self.clickImportChk)

      self.lblPageStr = QRichLabel(self.tr('Page:'))
      self.comboPageNum = QComboBox()
      self.lblPageMaxStr = QRichLabel('')
      self.connect(self.comboPageNum, SIGNAL('activated(int)'), self.redrawBackup)

      # We enable printing of imported addresses but not frag'ing them.... way
      # too much work for everyone (developer and user) to deal with 2x or 3x
      # the amount of data to type
      self.chkImportPrint.setVisible(len(self.binImport) > 0 and not self.doPrintFrag)
      self.lblPageStr.setVisible(False)
      self.comboPageNum.setVisible(False)
      self.lblPageMaxStr.setVisible(False)

      self.chkSecurePrint = QCheckBox(self.trUtf8(u'Use SecurePrint\u200b\u2122 to prevent exposing keys to printer or other '
         'network devices'))

      if(self.doPrintFrag):
         self.chkSecurePrint.setChecked(self.fragData['Secure'])

      self.ttipSecurePrint = self.main.createToolTipWidget(self.trUtf8(
         u'SecurePrint\u200b\u2122 encrypts your backup with a code displayed on '
         'the screen, so that no other devices on your network see the sensitive '
         'data when you send it to the printer.  If you turn on '
         u'SecurePrint\u200b\u2122 <u>you must write the code on the page after '
         'it is done printing!</u>  There is no point in using this feature if '
         'you copy the data by hand.'))

      self.lblSecurePrint = QRichLabel(self.trUtf8(
         u'<b><font color="%1"><u>IMPORTANT:</u></b>  You must write the SecurePrint\u200b\u2122 '
         u'encryption code on each printed backup page!  Your SecurePrint\u200b\u2122 code is </font> '
         '<font color="%2">%3</font>.  <font color="%4">Your backup will not work '
         'if this code is lost!</font>').arg(htmlColor('TextWarn'), htmlColor('TextBlue'), self.randpass.toBinStr(), \
         htmlColor('TextWarn')))

      self.connect(self.chkSecurePrint, SIGNAL("clicked()"), self.redrawBackup)


      self.btnPrint = QPushButton('&Print...')
      self.btnPrint.setMinimumWidth(3 * tightSizeStr(self.btnPrint, 'Print...')[0])
      self.btnCancel = QPushButton('&Cancel')
      self.connect(self.btnPrint, SIGNAL(CLICKED), self.print_)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.accept)

      if self.doPrintFrag:
         M, N = self.fragData['M'], self.fragData['N']
         lblDescr = QRichLabel(self.tr(
            '<b><u>Print Wallet Backup Fragments</u></b><br><br> '
            'When any %1 of these fragments are combined, all <u>previous '
            '<b>and</b> future</u> addresses generated by this wallet will be '
            'restored, giving you complete access to your bitcoins.  The '
            'data can be copied by hand if a working printer is not '
            'available.  Please make sure that all data lines contain '
            '<b>9 columns</b> '
            'of <b>4 characters each</b> (excluding "ID" lines).').arg(M))
      else:
         withChain = '' if self.noNeedChaincode else 'and "Chaincode"'
         lblDescr = QRichLabel(self.tr(
            '<b><u>Print a Forever-Backup</u></b><br><br> '
            'Printing this sheet protects all <u>previous <b>and</b> future</u> addresses '
            'generated by this wallet!  You can copy the "Root Key" %1 '
            'by hand if a working printer is not available.  Please make sure that '
            'all data lines contain <b>9 columns</b> '
            'of <b>4 characters each</b>.').arg(withChain))

      lblDescr.setContentsMargins(5, 5, 5, 5)
      frmDescr = makeHorizFrame([lblDescr], STYLE_RAISED)

      self.redrawBackup()
      frmChkImport = makeHorizFrame([self.chkImportPrint, \
                                     STRETCH, \
                                     self.lblPageStr, \
                                     self.comboPageNum, \
                                     self.lblPageMaxStr])

      frmSecurePrint = makeHorizFrame([self.chkSecurePrint,
                                       self.ttipSecurePrint,
                                       STRETCH])

      frmButtons = makeHorizFrame([self.btnCancel, STRETCH, self.btnPrint])

      layout = QVBoxLayout()
      layout.addWidget(frmDescr)
      layout.addWidget(frmChkImport)
      layout.addWidget(self.view)
      layout.addWidget(frmSecurePrint)
      layout.addWidget(self.lblSecurePrint)
      layout.addWidget(frmButtons)
      setLayoutStretch(layout, 0, 1, 0, 0, 0)

      self.setLayout(layout)

      self.setWindowIcon(QIcon(':/printer_icon.png'))
      self.setWindowTitle('Print Wallet Backup')


      # Apparently I can't programmatically scroll until after it's painted
      def scrollTop():
         vbar = self.view.verticalScrollBar()
         vbar.setValue(vbar.minimum())
      self.callLater(0.01, scrollTop)

   def redrawBackup(self):
      cmbPage = 1
      if self.comboPageNum.count() > 0:
         cmbPage = int(str(self.comboPageNum.currentText()))

      if self.doPrintFrag:
         cmbPage -= 1
         if not self.doMultiFrag:
            cmbPage = self.fragData['Range'][0]
         elif self.comboPageNum.count() > 0:
            cmbPage = int(str(self.comboPageNum.currentText())) - 1

         self.createPrintScene('Fragmented Backup', cmbPage)
      else:
         pgSelect = cmbPage if self.chkImportPrint.isChecked() else 1
         if pgSelect == 1:
            self.createPrintScene('SingleSheetFirstPage', '')
         else:
            pg = pgSelect - 2
            nKey = self.maxKeysPerPage
            self.createPrintScene('SingleSheetImported', [pg * nKey, (pg + 1) * nKey])


      showPageCombo = self.chkImportPrint.isChecked() or \
                      (self.doPrintFrag and self.doMultiFrag)
      self.showPageSelect(showPageCombo)
      self.view.update()




   def clickImportChk(self):
      if self.numImportPages > 1 and self.chkImportPrint.isChecked():
         ans = QMessageBox.warning(self, self.tr('Lots to Print!'), self.tr(
            'This wallet contains <b>%1</b> imported keys, which will require '
            '<b>%2</b> pages to print.  Not only will this use a lot of paper, '
            'it will be a lot of work to manually type in these keys in the '
            'event that you need to restore this backup. It is recommended '
            'that you do <u>not</u> print your imported keys and instead make '
            'a digital backup, which can be restored instantly if needed. '
            '<br><br> Do you want to print the imported keys, anyway?').arg(len(self.binImport), self.numImportPages), \
            QMessageBox.Yes | QMessageBox.No)
         if not ans == QMessageBox.Yes:
            self.chkImportPrint.setChecked(False)

      showPageCombo = self.chkImportPrint.isChecked() or \
                      (self.doPrintFrag and self.doMultiFrag)
      self.showPageSelect(showPageCombo)
      self.comboPageNum.setCurrentIndex(0)
      self.redrawBackup()


   def showPageSelect(self, doShow=True):
      MARGIN = self.scene.MARGIN_PIXELS
      bottomOfPage = self.scene.pageRect().height() + MARGIN
      totalHgt = bottomOfPage - self.bottomOfSceneHeader
      self.maxKeysPerPage = int(totalHgt / (self.importHgt))
      self.numImportPages = (len(self.binImport) - 1) / self.maxKeysPerPage + 1
      if self.comboPageNum.count() == 0:
         if self.doPrintFrag:
            numFrag = len(self.fragData['Range'])
            for i in range(numFrag):
               self.comboPageNum.addItem(str(i + 1))
            self.lblPageMaxStr.setText(self.tr('of %1').arg(numFrag,))
         else:
            for i in range(self.numImportPages + 1):
               self.comboPageNum.addItem(str(i + 1))
            self.lblPageMaxStr.setText(self.tr('of %1').arg(self.numImportPages + 1,))


      self.lblPageStr.setVisible(doShow)
      self.comboPageNum.setVisible(doShow)
      self.lblPageMaxStr.setVisible(doShow)




   def print_(self):
      LOGINFO('Printing!')
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)

      if QPrintDialog(self.printer).exec_():
         painter = QPainter(self.printer)
         painter.setRenderHint(QPainter.TextAntialiasing)

         if self.doPrintFrag:
            for i in self.fragData['Range']:
               self.createPrintScene('Fragment', i)
               self.scene.getScene().render(painter)
               if not i == len(self.fragData['Range']) - 1:
                  self.printer.newPage()

         else:
            self.createPrintScene('SingleSheetFirstPage', '')
            self.scene.getScene().render(painter)

            if len(self.binImport) > 0 and self.chkImportPrint.isChecked():
               nKey = self.maxKeysPerPage
               for i in range(self.numImportPages):
                  self.printer.newPage()
                  self.createPrintScene('SingleSheetImported', [i * nKey, (i + 1) * nKey])
                  self.scene.getScene().render(painter)

         painter.end()

         # The last scene printed is what's displayed now.  Set the combo box
         self.comboPageNum.setCurrentIndex(self.comboPageNum.count() - 1)

         if self.chkSecurePrint.isChecked():
            QMessageBox.warning(self, self.tr('SecurePrint Code'), self.trUtf8(
               u'<br><b>You must write your SecurePrint\u200b\u2122 '
               'code on each sheet of paper you just printed!</b> '
               'Write it in the red box in upper-right corner '
               u'of each printed page. <br><br>SecurePrint\u200b\u2122 code: '
               '<font color="%1" size=5><b>%2</b></font> <br><br> '
               '<b>NOTE: the above code <u>is</u> case-sensitive!</b>').arg(htmlColor('TextBlue'), self.randpass.toBinStr()), \
               QMessageBox.Ok)
         if self.chkSecurePrint.isChecked():
            self.btnCancel.setText('Done')
         else:
            self.accept()


   def cleanup(self):
      self.binPriv.destroy()
      self.binChain.destroy()
      self.binPrivCrypt.destroy()
      self.binChainCrypt.destroy()
      self.randpass.destroy()
      for a160, priv, compr in self.binImport:
         priv.destroy()

      for x, y in self.fragMtrxCrypt:
         x.destroy()
         y.destroy()

   def accept(self):
      self.cleanup()
      super(DlgPrintBackup, self).accept()

   def reject(self):
      self.cleanup()
      super(DlgPrintBackup, self).reject()


   #############################################################################
   #############################################################################
   def createPrintScene(self, printType, printData):
      self.scene.gfxScene.clear()
      self.scene.resetCursor()

      pr = self.scene.pageRect()
      self.scene.drawRect(pr.width(), pr.height(), edgeColor=None, fillColor=QColor(255, 255, 255))
      self.scene.resetCursor()


      INCH = self.scene.INCH
      MARGIN = self.scene.MARGIN_PIXELS

      doMask = self.chkSecurePrint.isChecked()

      if USE_TESTNET or USE_REGTEST:
         self.scene.drawPixmapFile(':/armory_logo_green_h56.png')
      else:
         self.scene.drawPixmapFile(':/armory_logo_h36.png')
      self.scene.newLine()

      self.scene.drawText('Paper Backup for Armory Wallet', GETFONT('Var', 11))
      self.scene.newLine()

      self.scene.newLine(extra_dy=20)
      self.scene.drawHLine()
      self.scene.newLine(extra_dy=20)


      ssType = self.trUtf8(u' (SecurePrint\u200b\u2122)') if doMask else self.tr(' (Unencrypted)')
      if printType == 'SingleSheetFirstPage':
         bType = self.tr('Single-Sheet %1').arg(ssType)
      elif printType == 'SingleSheetImported':
         bType = self.tr('Imported Keys %1').arg(ssType)
      elif printType.lower().startswith('frag'):
         m_count = str(self.fragData['M'])
         n_count = str(self.fragData['N'])
         bstr = self.tr('Fragmented Backup (%1-of-%2)').arg(m_count, n_count)
         bType = bstr + ' ' + ssType

      if printType.startswith('SingleSheet'):
         colRect, rowHgt = self.scene.drawColumn(['Wallet Version:', 'Wallet ID:', \
                                                   'Wallet Name:', 'Backup Type:'])
         self.scene.moveCursor(15, 0)
         suf = 'c' if self.noNeedChaincode else 'a'
         colRect, rowHgt = self.scene.drawColumn(['1.35' + suf, self.wlt.uniqueIDB58, \
                                                   self.wlt.labelName, bType])
         self.scene.moveCursor(15, colRect.y() + colRect.height(), absolute=True)
      else:
         colRect, rowHgt = self.scene.drawColumn(['Wallet Version:', 'Wallet ID:', \
                                                   'Wallet Name:', 'Backup Type:', \
                                                   'Fragment:'])
         baseID = self.fragData['FragIDStr']
         fragNum = printData + 1
         fragID = '<b>%s-<font color="%s">#%d</font></b>' % (baseID, htmlColor('TextBlue'), fragNum)
         self.scene.moveCursor(15, 0)
         suf = 'c' if self.noNeedChaincode else 'a'
         colRect, rowHgt = self.scene.drawColumn(['1.35' + suf, self.wlt.uniqueIDB58, \
                                                   self.wlt.labelName, bType, fragID])
         self.scene.moveCursor(15, colRect.y() + colRect.height(), absolute=True)


      # Display warning about unprotected key data
      wrap = 0.9 * self.scene.pageRect().width()

      if self.doPrintFrag:
         warnMsg = self.tr(
            'Any subset of <font color="%1"><b>%2</b></font> fragments with this '
            'ID (<font color="%3"><b>%4</b></font>) are sufficient to recover all the '
            'coins contained in this wallet.  To optimize the physical security of '
            'your wallet, please store the fragments in different locations.').arg(htmlColor('TextBlue'), \
                           str(self.fragData['M']), htmlColor('TextBlue'), self.fragData['FragIDStr'])
      else:
         container = 'this wallet' if printType == 'SingleSheetFirstPage' else 'these addresses'
         warnMsg = self.tr(
            '<font color="#aa0000"><b>WARNING:</b></font> Anyone who has access to this '
            'page has access to all the bitcoins in %1!  Please keep this '
            'page in a safe place.').arg(container)

      self.scene.newLine()
      self.scene.drawText(warnMsg, GETFONT('Var', 9), wrapWidth=wrap)

      self.scene.newLine(extra_dy=20)
      self.scene.drawHLine()
      self.scene.newLine(extra_dy=20)

      if self.doPrintFrag:
         numLine = 'three' if self.noNeedChaincode else 'five'
      else:
         numLine = 'two' if self.noNeedChaincode else 'four'

      if printType == 'SingleSheetFirstPage':
         descrMsg = self.tr(
            'The following %1 lines backup all addresses '
            '<i>ever generated</i> by this wallet (previous and future). '
            'This can be used to recover your wallet if you forget your passphrase or '
            'suffer hardware failure and lose your wallet files.').arg(numLine)
      elif printType == 'SingleSheetImported':
         if self.chkSecurePrint.isChecked():
            descrMsg = self.trUtf8(
               'The following is a list of all private keys imported into your '
               'wallet before this backup was made.   These keys are encrypted '
               u'with the SecurePrint\u200b\u2122 code and can only be restored '
               'by entering them into Armory.  Print a copy of this backup without '
               u'the SecurePrint\u200b\u2122 option if you want to be able to import '
               'them into another application.')
         else:
            descrMsg = self.tr(
               'The following is a list of all private keys imported into your '
               'wallet before this backup was made.  Each one must be copied '
               'manually into the application where you wish to import them.')
      elif printType.lower().startswith('frag'):
         fragNum = printData + 1
         descrMsg = self.tr(
            'The following is fragment <font color="%1"><b>#%2</b></font> for this '
            'wallet.').arg(htmlColor('TextBlue'), str(printData + 1))


      self.scene.drawText(descrMsg, GETFONT('var', 8), wrapWidth=wrap)
      self.scene.newLine(extra_dy=10)

      ###########################################################################
      # Draw the SecurePrint box if needed, frag pie, then return cursor
      prevCursor = self.scene.getCursorXY()

      self.lblSecurePrint.setVisible(doMask)
      if doMask:
         self.scene.resetCursor()
         self.scene.moveCursor(4.0 * INCH, 0)
         spWid, spHgt = 2.75 * INCH, 1.5 * INCH,
         if doMask:
            self.scene.drawRect(spWid, spHgt, edgeColor=QColor(180, 0, 0), penWidth=3)

         self.scene.resetCursor()
         self.scene.moveCursor(4.07 * INCH, 0.07 * INCH)

         self.scene.drawText(self.trUtf8(
            '<b><font color="#770000">CRITICAL:</font>  This backup will not '
            u'work without the SecurePrint\u200b\u2122 '
            'code displayed on the screen during printing. '
            'Copy it here in ink:'), wrapWidth=spWid * 0.93, font=GETFONT('Var', 7))

         self.scene.newLine(extra_dy=8)
         self.scene.moveCursor(4.07 * INCH, 0)
         codeWid, codeHgt = self.scene.drawText('Code:')
         self.scene.moveCursor(0, codeHgt - 3)
         wid = spWid - codeWid
         w, h = self.scene.drawHLine(width=wid * 0.9, penWidth=2)



      # Done drawing other stuff, so return to the original drawing location
      self.scene.moveCursor(*prevCursor, absolute=True)
      ###########################################################################


      ###########################################################################
      # Finally, draw the backup information.

      # If this page is only imported addresses, draw them then bail
      self.bottomOfSceneHeader = self.scene.cursorPos.y()
      if printType == 'SingleSheetImported':
         self.scene.moveCursor(0, 0.1 * INCH)
         importList = self.binImport
         if self.chkSecurePrint.isChecked():
            importList = self.binImportCrypt

         for a160, priv, isCompr in importList[printData[0]:printData[1]]:
            comprByte = ('\x01' if isCompr == 1 else '')
            prprv = encodePrivKeyBase58(priv.toBinStr() + comprByte)
            toPrint = [prprv[i * 6:(i + 1) * 6] for i in range((len(prprv) + 5) / 6)]
            addrHint = '  (%s...)' % hash160_to_addrStr(a160)[:12]
            self.scene.drawText(' '.join(toPrint), GETFONT('Fix', 7))
            self.scene.moveCursor(0.02 * INCH, 0)
            self.scene.drawText(addrHint, GETFONT('Var', 7))
            self.scene.newLine(extra_dy=-3)
            prprv = None
         return


      if self.doPrintFrag:
         M = self.fragData['M']
         Lines = []
         Prefix = []
         fmtrx = self.fragMtrxCrypt if doMask else self.fragMtrx

         try:
            yBin = fmtrx[printData][1].toBinStr()
            binID = base58_to_binary(self.fragData['fragSetID'])
            IDLine = ComputeFragIDLineHex(M, printData, binID, doMask, addSpaces=True)
            if len(yBin) == 32:
               Prefix.append('ID:');  Lines.append(IDLine)
               Prefix.append('F1:');  Lines.append(makeSixteenBytesEasy(yBin[:16 ]))
               Prefix.append('F2:');  Lines.append(makeSixteenBytesEasy(yBin[ 16:]))
            elif len(yBin) == 64:
               Prefix.append('ID:');  Lines.append(IDLine)
               Prefix.append('F1:');  Lines.append(makeSixteenBytesEasy(yBin[:16       ]))
               Prefix.append('F2:');  Lines.append(makeSixteenBytesEasy(yBin[ 16:32    ]))
               Prefix.append('F3:');  Lines.append(makeSixteenBytesEasy(yBin[    32:48 ]))
               Prefix.append('F4:');  Lines.append(makeSixteenBytesEasy(yBin[       48:]))
            else:
               LOGERROR('yBin is not 32 or 64 bytes!  It is %s bytes', len(yBin))
         finally:
            yBin = None

      else:
         # Single-sheet backup
         if doMask:
            code12 = self.binPrivCrypt.toBinStr()
            code34 = self.binChainCrypt.toBinStr()
         else:
            code12 = self.binPriv.toBinStr()
            code34 = self.binChain.toBinStr()


         Lines = []
         Prefix = []
         Prefix.append('Root Key:');  Lines.append(makeSixteenBytesEasy(code12[:16]))
         Prefix.append('');           Lines.append(makeSixteenBytesEasy(code12[16:]))
         Prefix.append('Chaincode:'); Lines.append(makeSixteenBytesEasy(code34[:16]))
         Prefix.append('');           Lines.append(makeSixteenBytesEasy(code34[16:]))

         if self.noNeedChaincode:
            Prefix = Prefix[:2]
            Lines = Lines[:2]

      # Draw the prefix
      origX, origY = self.scene.getCursorXY()
      self.scene.moveCursor(20, 0)
      colRect, rowHgt = self.scene.drawColumn(['<b>' + l + '</b>' for l in Prefix])

      nudgeDown = 2  # because the differing font size makes it look unaligned
      self.scene.moveCursor(20, nudgeDown)
      self.scene.drawColumn(Lines,
                              font=GETFONT('Fixed', 8, bold=True), \
                              rowHeight=rowHgt,
                              useHtml=False)

      self.scene.moveCursor(MARGIN, colRect.y() - 2, absolute=True)
      width = self.scene.pageRect().width() - 2 * MARGIN
      self.scene.drawRect(width, colRect.height() + 7, edgeColor=QColor(0, 0, 0), fillColor=None)

      self.scene.newLine(extra_dy=30)
      self.scene.drawText(self.tr(
         'The following QR code is for convenience only.  It contains the '
         'exact same data as the %1 lines above.  If you copy this backup '
         'by hand, you can safely ignore this QR code.').arg(numLine), wrapWidth=4 * INCH)

      self.scene.moveCursor(20, 0)
      x, y = self.scene.getCursorXY()
      edgeRgt = self.scene.pageRect().width() - MARGIN
      edgeBot = self.scene.pageRect().height() - MARGIN

      qrSize = max(1.5 * INCH, min(edgeRgt - x, edgeBot - y, 2.0 * INCH))
      self.scene.drawQR('\n'.join(Lines), qrSize)
      self.scene.newLine(extra_dy=25)

      Lines = None

      # Finally, draw some pie slices at the bottom
      if self.doPrintFrag:
         M, N = self.fragData['M'], self.fragData['N']
         bottomOfPage = self.scene.pageRect().height() + MARGIN
         maxPieHeight = bottomOfPage - self.scene.getCursorXY()[1] - 8
         maxPieWidth = int((self.scene.pageRect().width() - 2 * MARGIN) / N) - 10
         pieSize = min(72., maxPieHeight, maxPieWidth)
         for i in range(N):
            startX, startY = self.scene.getCursorXY()
            drawSize = self.scene.drawPixmapFile(':/frag%df.png' % M, sizePx=pieSize)
            self.scene.moveCursor(10, 0)
            if i == printData:
               returnX, returnY = self.scene.getCursorXY()
               self.scene.moveCursor(startX, startY, absolute=True)
               self.scene.moveCursor(-5, -5)
               self.scene.drawRect(drawSize[0] + 10, \
                                   drawSize[1] + 10, \
                                   edgeColor=Colors.TextBlue, \
                                   penWidth=3)
               self.scene.newLine()
               self.scene.moveCursor(startX - MARGIN, 0)
               self.scene.drawText('<font color="%s">#%d</font>' % \
                        (htmlColor('TextBlue'), fragNum), GETFONT('Var', 10))
               self.scene.moveCursor(returnX, returnY, absolute=True)



      vbar = self.view.verticalScrollBar()
      vbar.setValue(vbar.minimum())
      self.view.update()



################################################################################
def OpenPaperBackupWindow(backupType, parent, main, wlt, unlockTitle=None):

   if wlt.useEncryption and wlt.isLocked:
      if unlockTitle == None:
         unlockTitle = parent.tr("Unlock Paper Backup")
      dlg = DlgUnlockWallet(wlt, parent, main, unlockTitle)
      if not dlg.exec_():
         QMessageBox.warning(parent, parent.tr('Unlock Failed'), parent.tr(
            'The wallet could not be unlocked.  Please try again with '
            'the correct unlock passphrase.'), QMessageBox.Ok)
         return False

   result = True
   verifyText = ''
   if backupType == 'Single':
      result = DlgPrintBackup(parent, main, wlt).exec_()
      verifyText = parent.trUtf8(
         u'If the backup was printed with SecurePrint\u200b\u2122, please '
         u'make sure you wrote the SecurePrint\u200b\u2122 code on the '
         'printed sheet of paper. Note that the code <b><u>is</u></b> '
         'case-sensitive!')
   elif backupType == 'Frag':
      result = DlgFragBackup(parent, main, wlt).exec_()
      verifyText = parent.trUtf8(
         u'If the backup was created with SecurePrint\u200b\u2122, please '
         u'make sure you wrote the SecurePrint\u200b\u2122 code on each '
         'fragment (or stored with each file fragment). The code is the '
         'same for all fragments.')

   doTest = MsgBoxCustom(MSGBOX.Warning, parent.tr('Verify Your Backup!'), parent.tr(
      '<b><u>Verify your backup!</u></b> '
      '<br><br>'
      'If you just made a backup, make sure that it is correct! '
      'The following steps are recommended to verify its integrity: '
      '<br>'
      '<ul>'
      '<li>Verify each line of the backup data contains <b>9 columns</b> '
      'of <b>4 letters each</b> (excluding any "ID" lines).</li> '
      '<li>%1</li>'
      '<li>Use Armory\'s backup tester to test the backup before you '
      'physiclly secure it.</li> '
      '</ul>'
      '<br>'
      'Armory has a backup tester that uses the exact same '
      'process as restoring your wallet, but stops before it writes any '
      'data to disk.  Would you like to test your backup now? '
      ).arg(verifyText), yesStr="Test Backup", noStr="Cancel")

   if doTest:
      if backupType == 'Single':
         DlgRestoreSingle(parent, main, True, wlt.uniqueIDB58).exec_()
      elif backupType == 'Frag':
         DlgRestoreFragged(parent, main, True, wlt.uniqueIDB58).exec_()

   return result

################################################################################
class DlgBadConnection(ArmoryDialog):
   def __init__(self, haveInternet, haveSatoshi, parent=None, main=None):
      super(DlgBadConnection, self).__init__(parent, main)


      layout = QGridLayout()
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      lblDescr = QLabel()
      if not haveInternet and not CLI_OPTIONS.offline:
         lblDescr = QRichLabel(self.tr(
            'Armory was not able to detect an internet connection, so Armory '
            'will operate in "Offline" mode.  In this mode, only wallet '
            '-management and unsigned-transaction functionality will be available. '
            '<br><br>'
            'If this is an error, please check your internet connection and '
            'restart Armory.<br><br>Would you like to continue in "Offline" mode?'))
      elif haveInternet and not haveSatoshi:
         lblDescr = QRichLabel(self.tr(
            'Armory was not able to detect the presence of Bitcoin Core or bitcoind '
            'client software (available at https://bitcoin.org).  Please make sure that '
            'the one of those programs is... <br> '
            '<br><b>(1)</b> ...open and connected to the network '
            '<br><b>(2)</b> ...on the same network as Armory (main-network or test-network) '
            '<br><b>(3)</b> ...synchronized with the blockchain before '
            'starting Armory<br><br>Without the Bitcoin Core or bitcoind open, you will only '
            'be able to run Armory in "Offline" mode, which will not have access '
            'to new blockchain data, and you will not be able to send outgoing '
            'transactions<br><br>If you do not want to be in "Offline" mode, please '
            'restart Armory after one of these programs is open and synchronized with '
            'the network'))
      else:
         # Nothing to do -- we shouldn't have even gotten here
         # self.reject()
         pass


      self.main.abortLoad = False
      def abortLoad():
         self.main.abortLoad = True
         self.reject()

      lblDescr.setMinimumWidth(500)
      self.btnAccept = QPushButton(self.tr("Continue in Offline Mode"))
      self.btnCancel = QPushButton(self.tr("Close Armory"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      self.connect(self.btnCancel, SIGNAL(CLICKED), abortLoad)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout.addWidget(lblWarnImg, 0, 1, 2, 1)
      layout.addWidget(lblDescr, 0, 2, 1, 1)
      layout.addWidget(buttonBox, 1, 2, 1, 1)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Network not available'))


################################################################################
def readSigBlock(parent, fullPacket):
   addrB58, messageStr, pubkey, sig = '', '', '', ''
   lines = fullPacket.split('\n')
   readingMessage, readingPub, readingSig = False, False, False
   for i in range(len(lines)):
      s = lines[i].strip()

      # ADDRESS
      if s.startswith('Addr'):
         addrB58 = s.split(':')[-1].strip()

      # MESSAGE STRING
      if s.startswith('Message') or readingMessage:
         readingMessage = True
         if s.startswith('Pub') or s.startswith('Sig') or ('END-CHAL' in s):
            readingMessage = False
         else:
            # Message string needs to be exact, grab what's between the
            # double quotes, no newlines
            iq1 = s.index('"') + 1
            iq2 = s.index('"', iq1)
            messageStr += s[iq1:iq2]

      # PUBLIC KEY
      if s.startswith('Pub') or readingPub:
         readingPub = True
         if s.startswith('Sig') or ('END-SIGNATURE-BLOCK' in s):
            readingPub = False
         else:
            pubkey += s.split(':')[-1].strip().replace(' ', '')

      # SIGNATURE
      if s.startswith('Sig') or readingSig:
         readingSig = True
         if 'END-SIGNATURE-BLOCK' in s:
            readingSig = False
         else:
            sig += s.split(':')[-1].strip().replace(' ', '')


   if len(pubkey) > 0:
      try:
         pubkey = hex_to_binary(pubkey)
         if len(pubkey) not in (32, 33, 64, 65):  raise
      except:
         QMessageBox.critical(parent, parent.tr('Bad Public Key'), \
             parent.tr('Public key data was not recognized'), QMessageBox.Ok)
         pubkey = ''

   if len(sig) > 0:
      try:
         sig = hex_to_binary(sig)
      except:
         QMessageBox.critical(parent, parent.tr('Bad Signature'), \
            parent.tr('Signature data is malformed!'), QMessageBox.Ok)
         sig = ''


   pubkeyhash = hash160(pubkey)
   if not pubkeyhash == addrStr_to_hash160(addrB58)[1]:
      QMessageBox.critical(parent, parent.tr('Address Mismatch'), \
         parent.tr('!!! The address included in the signature block does not '
         'match the supplied public key!  This should never happen, '
         'and may in fact be an attempt to mislead you !!!'), QMessageBox.Ok)
      sig = ''



   return addrB58, messageStr, pubkey, sig


################################################################################
def makeSigBlock(addrB58, MessageStr, binPubkey='', binSig=''):
   lineWid = 50
   s = '-----BEGIN-SIGNATURE-BLOCK'.ljust(lineWid + 13, '-') + '\n'

   ### Address ###
   s += 'Address:    %s\n' % addrB58

   ### Message ###
   chPerLine = lineWid - 2
   nMessageLines = (len(MessageStr) - 1) / chPerLine + 1
   for i in range(nMessageLines):
      cLine = 'Message:    "%s"\n' if i == 0 else '            "%s"\n'
      s += cLine % MessageStr[i * chPerLine:(i + 1) * chPerLine]

   ### Public Key ###
   if len(binPubkey) > 0:
      hexPub = binary_to_hex(binPubkey)
      nPubLines = (len(hexPub) - 1) / lineWid + 1
      for i in range(nPubLines):
         pLine = 'PublicKey:  %s\n' if i == 0 else '            %s\n'
         s += pLine % hexPub[i * lineWid:(i + 1) * lineWid]

   ### Signature ###
   if len(binSig) > 0:
      hexSig = binary_to_hex(binSig)
      nSigLines = (len(hexSig) - 1) / lineWid + 1
      for i in range(nSigLines):
         sLine = 'Signature:  %s\n' if i == 0 else '            %s\n'
         s += sLine % hexSig[i * lineWid:(i + 1) * lineWid]

   s += '-----END-SIGNATURE-BLOCK'.ljust(lineWid + 13, '-') + '\n'
   return s



class DlgExecLongProcess(ArmoryDialog):
   """
   Execute a processing that may require having the user to wait a while.
   Should appear like a splash screen, and will automatically close when
   the processing is done.  As such, you should have very little text, just
   in case it finishes immediately, the user won't have time to read it.

   DlgExecLongProcess(execFunc, 'Short Description', self, self.main).exec_()
   """
   def __init__(self, funcExec, msg='', parent=None, main=None):
      super(DlgExecLongProcess, self).__init__(parent, main)

      self.func = funcExec

      waitFont = GETFONT('Var', 14)
      descrFont = GETFONT('Var', 12)
      palette = QPalette()
      palette.setColor(QPalette.Window, QColor(235, 235, 255))
      self.setPalette(palette);
      self.setAutoFillBackground(True)

      if parent:
         qr = parent.geometry()
         x, y, w, h = qr.left(), qr.top(), qr.width(), qr.height()
         dlgW = relaxedSizeStr(waitFont, msg)[0]
         dlgW = min(dlgW, 400)
         dlgH = 150
         self.setGeometry(int(x + w / 2 - dlgW / 2), int(y + h / 2 - dlgH / 2), dlgW, dlgH)

      lblWaitMsg = QRichLabel(self.tr('Please Wait...'))
      lblWaitMsg.setFont(waitFont)
      lblWaitMsg.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      lblDescrMsg = QRichLabel(msg)
      lblDescrMsg.setFont(descrFont)
      lblDescrMsg.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      self.setWindowFlags(Qt.SplashScreen)

      layout = QVBoxLayout()
      layout.addWidget(lblWaitMsg)
      layout.addWidget(lblDescrMsg)
      self.setLayout(layout)


   def exec_(self):
      def execAndClose():
         self.func()
         self.accept()

      self.callLater(0.1, execAndClose)
      QDialog.exec_(self)






################################################################################
class DlgECDSACalc(ArmoryDialog):
   def __init__(self, parent=None, main=None, tabStart=0):
      super(DlgECDSACalc, self).__init__(parent, main)

      dispFont = GETFONT('Var', 8)
      w, h = tightSizeNChar(dispFont, 40)



      ##########################################################################
      ##########################################################################
      # TAB:  secp256k1
      ##########################################################################
      ##########################################################################
      # STUB: I'll probably finish implementing this eventually....
      eccWidget = QWidget()

      tabEccLayout = QGridLayout()
      self.txtScalarScalarA = QLineEdit()
      self.txtScalarScalarB = QLineEdit()
      self.txtScalarScalarC = QLineEdit()
      self.txtScalarScalarC.setReadOnly(True)

      self.txtScalarPtA = QLineEdit()
      self.txtScalarPtB_x = QLineEdit()
      self.txtScalarPtB_y = QLineEdit()
      self.txtScalarPtC_x = QLineEdit()
      self.txtScalarPtC_y = QLineEdit()
      self.txtScalarPtC_x.setReadOnly(True)
      self.txtScalarPtC_y.setReadOnly(True)

      self.txtPtPtA_x = QLineEdit()
      self.txtPtPtA_y = QLineEdit()
      self.txtPtPtB_x = QLineEdit()
      self.txtPtPtB_y = QLineEdit()
      self.txtPtPtC_x = QLineEdit()
      self.txtPtPtC_y = QLineEdit()
      self.txtPtPtC_x.setReadOnly(True)
      self.txtPtPtC_y.setReadOnly(True)

      eccTxtList = [ \
          self.txtScalarScalarA, self.txtScalarScalarB, \
          self.txtScalarScalarC, self.txtScalarPtA, self.txtScalarPtB_x, \
          self.txtScalarPtB_y, self.txtScalarPtC_x, self.txtScalarPtC_y, \
          self.txtPtPtA_x, self.txtPtPtA_y, self.txtPtPtB_x, \
          self.txtPtPtB_y, self.txtPtPtC_x, self.txtPtPtC_y]

      dispFont = GETFONT('Var', 8)
      w, h = tightSizeNChar(dispFont, 60)
      for txt in eccTxtList:
         txt.setMinimumWidth(w)
         txt.setFont(dispFont)


      self.btnCalcSS = QPushButton(self.tr('Multiply Scalars (mod n)'))
      self.btnCalcSP = QPushButton(self.tr('Scalar Multiply EC Point'))
      self.btnCalcPP = QPushButton(self.tr('Add EC Points'))
      self.btnClearSS = QPushButton(self.tr('Clear'))
      self.btnClearSP = QPushButton(self.tr('Clear'))
      self.btnClearPP = QPushButton(self.tr('Clear'))


      imgPlus = QRichLabel('<b>+</b>')
      imgTimes1 = QRichLabel('<b>*</b>')
      imgTimes2 = QRichLabel('<b>*</b>')
      imgDown = QRichLabel('')

      self.connect(self.btnCalcSS, SIGNAL(CLICKED), self.multss)
      self.connect(self.btnCalcSP, SIGNAL(CLICKED), self.multsp)
      self.connect(self.btnCalcPP, SIGNAL(CLICKED), self.addpp)


      ##########################################################################
      # Scalar-Scalar Multiply
      sslblA = QRichLabel('a', hAlign=Qt.AlignHCenter)
      sslblB = QRichLabel('b', hAlign=Qt.AlignHCenter)
      sslblC = QRichLabel('a*b mod n', hAlign=Qt.AlignHCenter)


      ssLayout = QGridLayout()
      ssLayout.addWidget(sslblA, 0, 0, 1, 1)
      ssLayout.addWidget(sslblB, 0, 2, 1, 1)

      ssLayout.addWidget(self.txtScalarScalarA, 1, 0, 1, 1)
      ssLayout.addWidget(imgTimes1, 1, 1, 1, 1)
      ssLayout.addWidget(self.txtScalarScalarB, 1, 2, 1, 1)

      ssLayout.addWidget(makeHorizFrame([STRETCH, self.btnCalcSS, STRETCH]), \
                                                  2, 0, 1, 3)
      ssLayout.addWidget(makeHorizFrame([STRETCH, sslblC, self.txtScalarScalarC, STRETCH]), \
                                                  3, 0, 1, 3)
      ssLayout.setVerticalSpacing(1)
      frmSS = QFrame()
      frmSS.setFrameStyle(STYLE_SUNKEN)
      frmSS.setLayout(ssLayout)

      ##########################################################################
      # Scalar-ECPoint Multiply
      splblA = QRichLabel('a', hAlign=Qt.AlignHCenter)
      splblB = QRichLabel('<b>B</b>', hAlign=Qt.AlignHCenter)
      splblBx = QRichLabel('<b>B</b><font size=2>x</font>', hAlign=Qt.AlignRight)
      splblBy = QRichLabel('<b>B</b><font size=2>y</font>', hAlign=Qt.AlignRight)
      splblC = QRichLabel('<b>C</b> = a*<b>B</b>', hAlign=Qt.AlignHCenter)
      splblCx = QRichLabel('(a*<b>B</b>)<font size=2>x</font>', hAlign=Qt.AlignRight)
      splblCy = QRichLabel('(a*<b>B</b>)<font size=2>y</font>', hAlign=Qt.AlignRight)
      spLayout = QGridLayout()
      spLayout.addWidget(splblA, 0, 0, 1, 1)
      spLayout.addWidget(splblB, 0, 2, 1, 1)

      spLayout.addWidget(self.txtScalarPtA, 1, 0, 1, 1)
      spLayout.addWidget(imgTimes2, 1, 1, 1, 1)
      spLayout.addWidget(self.txtScalarPtB_x, 1, 2, 1, 1)
      spLayout.addWidget(self.txtScalarPtB_y, 2, 2, 1, 1)

      spLayout.addWidget(makeHorizFrame([STRETCH, self.btnCalcSP, STRETCH]), \
                                                  3, 0, 1, 3)
      spLayout.addWidget(makeHorizFrame([STRETCH, splblCx, self.txtScalarPtC_x, STRETCH]), \
                                                  4, 0, 1, 3)
      spLayout.addWidget(makeHorizFrame([STRETCH, splblCy, self.txtScalarPtC_y, STRETCH]), \
                                                  5, 0, 1, 3)
      spLayout.setVerticalSpacing(1)
      frmSP = QFrame()
      frmSP.setFrameStyle(STYLE_SUNKEN)
      frmSP.setLayout(spLayout)

      ##########################################################################
      # ECPoint Addition
      pplblA = QRichLabel('<b>A</b>', hAlign=Qt.AlignHCenter)
      pplblB = QRichLabel('<b>B</b>', hAlign=Qt.AlignHCenter)
      pplblAx = QRichLabel('<b>A</b><font size=2>x</font>', hAlign=Qt.AlignHCenter)
      pplblAy = QRichLabel('<b>A</b><font size=2>y</font>', hAlign=Qt.AlignHCenter)
      pplblBx = QRichLabel('<b>B</b><font size=2>x</font>', hAlign=Qt.AlignHCenter)
      pplblBy = QRichLabel('<b>B</b><font size=2>y</font>', hAlign=Qt.AlignHCenter)
      pplblC = QRichLabel('<b>C</b> = <b>A</b>+<b>B</b>', hAlign=Qt.AlignHCenter)
      pplblCx = QRichLabel('(<b>A</b>+<b>B</b>)<font size=2>x</font>', hAlign=Qt.AlignRight)
      pplblCy = QRichLabel('(<b>A</b>+<b>B</b>)<font size=2>y</font>', hAlign=Qt.AlignRight)
      ppLayout = QGridLayout()
      ppLayout.addWidget(pplblA, 0, 0, 1, 1)
      ppLayout.addWidget(pplblB, 0, 2, 1, 1)
      ppLayout.addWidget(self.txtPtPtA_x, 1, 0, 1, 1)
      ppLayout.addWidget(self.txtPtPtA_y, 2, 0, 1, 1)
      ppLayout.addWidget(imgPlus, 1, 1, 2, 1)
      ppLayout.addWidget(self.txtPtPtB_x, 1, 2, 1, 1)
      ppLayout.addWidget(self.txtPtPtB_y, 2, 2, 1, 1)
      ppLayout.addWidget(makeHorizFrame([STRETCH, self.btnCalcPP, STRETCH]), \
                                                  3, 0, 1, 3)
      ppLayout.addWidget(makeHorizFrame([STRETCH, pplblCx, self.txtPtPtC_x, STRETCH]), \
                                                  4, 0, 1, 3)
      ppLayout.addWidget(makeHorizFrame([STRETCH, pplblCy, self.txtPtPtC_y, STRETCH]), \
                                                  5, 0, 1, 3)
      ppLayout.setVerticalSpacing(1)
      frmPP = QFrame()
      frmPP.setFrameStyle(STYLE_SUNKEN)
      frmPP.setLayout(ppLayout)

      gxstr = '79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798'
      gystr = '483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8'

      lblDescr = QRichLabel(self.tr(
         'Use this form to perform Bitcoin elliptic curve calculations.  All '
         'operations are performed on the secp256k1 elliptic curve, which is '
         'the one used for Bitcoin. '
         'Supply all values as 32-byte, big-endian, hex-encoded integers. '
         '<br><br>'
         'The following is the secp256k1 generator point coordinates (G): <br> '
         '<b>G</b><sub>x</sub>: %1 <br> '
         '<b>G</b><sub>y</sub>: %2').arg(gxstr, gystr))

      lblDescr.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                       Qt.TextSelectableByKeyboard)

      btnClear = QPushButton(self.tr('Clear'))
      btnClear.setMaximumWidth(2 * relaxedSizeStr(btnClear, 'Clear')[0])
      self.connect(btnClear, SIGNAL(CLICKED), self.eccClear)

      btnBack = QPushButton(self.tr('<<< Go Back'))
      self.connect(btnBack, SIGNAL(CLICKED), self.accept)
      frmBack = makeHorizFrame([btnBack, STRETCH])

      eccLayout = QVBoxLayout()
      eccLayout.addWidget(makeHorizFrame([lblDescr, btnClear]))
      eccLayout.addWidget(frmSS)
      eccLayout.addWidget(frmSP)
      eccLayout.addWidget(frmBack)

      eccWidget.setLayout(eccLayout)

      calcLayout = QHBoxLayout()
      calcLayout.addWidget(eccWidget)
      self.setLayout(calcLayout)

      self.setWindowTitle(self.tr('ECDSA Calculator'))
      self.setWindowIcon(QIcon(self.main.iconfile))


   #############################################################################
   def getBinary(self, widget, name):
      try:
         hexVal = str(widget.text())
         binVal = hex_to_binary(hexVal)
      except:
         QMessageBox.critical(self, self.tr('Bad Input'), self.tr('Value "%1" is invalid. '
            'Make sure the value is specified in hex, big-endian.').arg(name) , QMessageBox.Ok)
         return ''
      return binVal


   #############################################################################
   def multss(self):
      binA = self.getBinary(self.txtScalarScalarA, 'a')
      binB = self.getBinary(self.txtScalarScalarB, 'b')
      C = CryptoECDSA().ECMultiplyScalars(binA, binB)
      self.txtScalarScalarC.setText(binary_to_hex(C))

      for txt in [self.txtScalarScalarA, \
                  self.txtScalarScalarB, \
                  self.txtScalarScalarC]:
         txt.setCursorPosition(0)

   #############################################################################
   def multsp(self):
      binA = self.getBinary(self.txtScalarPtA, 'a')
      binBx = self.getBinary(self.txtScalarPtB_x, '<b>B</b><font size=2>x</font>')
      binBy = self.getBinary(self.txtScalarPtB_y, '<b>B</b><font size=2>y</font>')

      if not CryptoECDSA().ECVerifyPoint(binBx, binBy):
         QMessageBox.critical(self, self.tr('Invalid EC Point'), \
            self.tr('The point you specified (<b>B</b>) is not on the '
            'elliptic curve used in Bitcoin (secp256k1).'), QMessageBox.Ok)
         return

      C = CryptoECDSA().ECMultiplyPoint(binA, binBx, binBy)
      self.txtScalarPtC_x.setText(binary_to_hex(C[:32]))
      self.txtScalarPtC_y.setText(binary_to_hex(C[32:]))

      for txt in [self.txtScalarPtA, \
                  self.txtScalarPtB_x, self.txtScalarPtB_y, \
                  self.txtScalarPtC_x, self.txtScalarPtC_y]:
         txt.setCursorPosition(0)

   #############################################################################
   def addpp(self):
      binAx = self.getBinary(self.txtPtPtA_x, '<b>A</b><font size=2>x</font>')
      binAy = self.getBinary(self.txtPtPtA_y, '<b>A</b><font size=2>y</font>')
      binBx = self.getBinary(self.txtPtPtB_x, '<b>B</b><font size=2>x</font>')
      binBy = self.getBinary(self.txtPtPtB_y, '<b>B</b><font size=2>y</font>')

      if not CryptoECDSA().ECVerifyPoint(binAx, binAy):
         QMessageBox.critical(self, self.tr('Invalid EC Point'), \
            self.tr('The point you specified (<b>A</b>) is not on the '
            'elliptic curve used in Bitcoin (secp256k1).'), QMessageBox.Ok)
         return

      if not CryptoECDSA().ECVerifyPoint(binBx, binBy):
         QMessageBox.critical(self, self.tr('Invalid EC Point'), \
            self.tr('The point you specified (<b>B</b>) is not on the '
            'elliptic curve used in Bitcoin (secp256k1).'), QMessageBox.Ok)
         return

      C = CryptoECDSA().ECAddPoints(binAx, binAy, binBx, binBy)
      self.txtPtPtC_x.setText(binary_to_hex(C[:32]))
      self.txtPtPtC_y.setText(binary_to_hex(C[32:]))

      for txt in [self.txtPtPtA_x, self.txtPtPtA_y, \
                  self.txtPtPtB_x, self.txtPtPtB_y, \
                  self.txtPtPtC_x, self.txtPtPtC_y]:
         txt.setCursorPosition(0)


   #############################################################################
   def eccClear(self):
      self.txtScalarScalarA.setText('')
      self.txtScalarScalarB.setText('')
      self.txtScalarScalarC.setText('')

      self.txtScalarPtA.setText('')
      self.txtScalarPtB_x.setText('')
      self.txtScalarPtB_y.setText('')
      self.txtScalarPtC_x.setText('')
      self.txtScalarPtC_y.setText('')

      self.txtPtPtA_x.setText('')
      self.txtPtPtA_y.setText('')
      self.txtPtPtB_x.setText('')
      self.txtPtPtB_y.setText('')
      self.txtPtPtC_x.setText('')
      self.txtPtPtC_y.setText('')





################################################################################
class DlgAddressBook(ArmoryDialog):
   """
   This dialog is provided a widget which has a "setText()" method.  When the
   user selects the address, this dialog will enter the text into the widget
   and then close itself.
   """
   def __init__(self, parent, main, putResultInWidget=None, \
                                    defaultWltID=None, \
                                    actionStr='Select', \
                                    selectExistingOnly=False, \
                                    selectMineOnly=False, \
                                    getPubKey=False,
                                    showLockboxes=True):
      super(DlgAddressBook, self).__init__(parent, main)

      self.target = putResultInWidget
      self.actStr = self.tr('Select')
      self.returnPubKey = getPubKey

      self.isBrowsingOnly = (self.target == None)

      if defaultWltID == None:
         defaultWltID = self.main.walletIDList[0]

      self.wlt = self.main.walletMap[defaultWltID]

      lblDescr = QRichLabel(self.tr('Choose an address from your transaction history, '
                            'or your own wallet.  If you choose to send to one '
                            'of your own wallets, the next unused address in '
                            'that wallet will be used.'))

      if self.isBrowsingOnly or selectExistingOnly:
         lblDescr = QRichLabel(self.tr('Browse all receiving addresses in '
                               'this wallet, and all addresses to which this '
                               'wallet has sent bitcoins.'))

      lblToWlt = QRichLabel(self.tr('<b>Send to Wallet:</b>'))
      lblToAddr = QRichLabel(self.tr('<b>Send to Address:</b>'))
      if self.isBrowsingOnly:
         lblToWlt.setVisible(False)
         lblToAddr.setVisible(False)


      rowHeight = tightSizeStr(self.font(), 'XygjpHI')[1]

      self.wltDispModel = AllWalletsDispModel(self.main)
      self.wltDispView = QTableView()
      self.wltDispView.setModel(self.wltDispModel)
      self.wltDispView.setSelectionBehavior(QTableView.SelectRows)
      self.wltDispView.setSelectionMode(QTableView.SingleSelection)
      self.wltDispView.horizontalHeader().setStretchLastSection(True)
      self.wltDispView.verticalHeader().setDefaultSectionSize(20)
      self.wltDispView.setMaximumHeight(rowHeight * 7.7)
      self.wltDispView.hideColumn(WLTVIEWCOLS.Visible)
      initialColResize(self.wltDispView, [0.15, 0.30, 0.2, 0.20])
      self.connect(self.wltDispView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.wltTableClicked)
      
      def toggleAddrType(addrtype):
         self.addrType = addrtype
         self.wltTableClicked(self.wltDispView.selectionModel().currentIndex())
         
      from ui.AddressTypeSelectDialog import AddressLabelFrame
      self.addrTypeSelectFrame = AddressLabelFrame(self, toggleAddrType)
      self.addrType = self.main.getSettingOrSetDefault(\
                        'Default_ReceiveType', DEFAULT_RECEIVE_TYPE)
      self.addrTypeSelectFrame.setType(self.addrType)

      # DISPLAY sent-to addresses
      self.addrBookTxModel = None
      self.addrBookTxView = QTableView()
      self.addrBookTxView.setSortingEnabled(True)
      self.connect(self.addrBookTxView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressTx)
      self.addrBookTxView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.addrBookTxView.customContextMenuRequested.connect(self.showContextMenuTx)

      # DISPLAY receiving addresses
      self.addrBookRxModel = None
      self.addrBookRxView = QTableView()
      self.addrBookRxView.setSortingEnabled(True)
      self.connect(self.addrBookRxView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressRx)

      self.addrBookRxView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.addrBookRxView.customContextMenuRequested.connect(self.showContextMenuRx)


      self.tabWidget = QTabWidget()
      self.tabWidget.addTab(self.addrBookRxView, self.tr('Receiving (Mine)'))
      if not selectMineOnly:
         self.tabWidget.addTab(self.addrBookTxView, self.tr('Sending (Other\'s)'))
      # DISPLAY Lockboxes - Regardles off what showLockboxes says only show
      # Lockboxes in Expert mode
      if showLockboxes and self.main.usermode == USERMODE.Expert:
         self.lboxModel = LockboxDisplayModel(self.main, \
                                    self.main.allLockboxes, \
                                    self.main.getPreferredDateFormat())
         self.lboxProxy = LockboxDisplayProxy(self)
         self.lboxProxy.setSourceModel(self.lboxModel)
         self.lboxProxy.sort(LOCKBOXCOLS.CreateDate, Qt.DescendingOrder)
         self.lboxView = QTableView()
         self.lboxView.setModel(self.lboxProxy)
         self.lboxView.setSortingEnabled(True)
         self.lboxView.setSelectionBehavior(QTableView.SelectRows)
         self.lboxView.setSelectionMode(QTableView.SingleSelection)
         self.lboxView.verticalHeader().setDefaultSectionSize(18)
         self.lboxView.horizontalHeader().setStretchLastSection(True)
         #maxKeys = max([lb.N for lb in self.main.allLockboxes])
         for i in range(LOCKBOXCOLS.Key0, LOCKBOXCOLS.Key4+1):
            self.lboxView.hideColumn(i)
         self.lboxView.hideColumn(LOCKBOXCOLS.UnixTime)
         self.tabWidget.addTab(self.lboxView, 'Lockboxes')
         self.connect( self.lboxView,
            SIGNAL('doubleClicked(QModelIndex)'),
            self.dblClickedLockbox)
         self.connect(self.lboxView.selectionModel(), \
             SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
             self.clickedLockbox)
      else:
         self.lboxView = None
      self.connect(self.tabWidget, SIGNAL('currentChanged(int)'), self.tabChanged)
      self.tabWidget.setCurrentIndex(0)



      ttipSendWlt = self.main.createToolTipWidget(\
         self.tr('The next unused address in that wallet will be calculated and selected. '))
      ttipSendAddr = self.main.createToolTipWidget(\
         self.tr('Addresses that are in other wallets you own are <b>not showns</b>.'))


      self.lblSelectWlt = QRichLabel('', doWrap=False)
      self.btnSelectWlt = QPushButton(self.tr('No Wallet Selected'))
      self.useBareMultiSigCheckBox = QCheckBox(self.tr('Use Bare Multi-Sig (No P2SH)'))
      self.useBareMultiSigCheckBox.setVisible(False)
      self.ttipBareMS = self.main.createToolTipWidget( self.tr(
         'EXPERT OPTION:  Do not check this box unless you know what it means '
                         'and you need it!  Forces Armory to exposes public '
                         'keys to the blockchain before the funds are spent. '
                         'This is only needed for very specific use cases, '
                         'and otherwise creates blockchain bloat.'))


      self.ttipBareMS.setVisible(False)
      self.btnSelectAddr = QPushButton(self.tr('No Address Selected'))
      self.btnSelectWlt.setEnabled(False)
      self.btnSelectAddr.setEnabled(False)
      btnCancel = QPushButton(self.tr('Cancel'))

      if self.isBrowsingOnly:
         self.btnSelectWlt.setVisible(False)
         self.btnSelectAddr.setVisible(False)
         self.lblSelectWlt.setVisible(False)
         btnCancel = QPushButton(self.tr('<<< Go Back'))
         ttipSendAddr.setVisible(False)

      if selectExistingOnly:
         lblToWlt.setVisible(False)
         self.lblSelectWlt.setVisible(False)
         self.btnSelectWlt.setVisible(False)
         ttipSendWlt.setVisible(False)

      self.connect(self.btnSelectWlt, SIGNAL(CLICKED), self.acceptWltSelection)
      self.connect(self.btnSelectAddr, SIGNAL(CLICKED), self.acceptAddrSelection)
      self.connect(self.useBareMultiSigCheckBox, SIGNAL(CLICKED), self.useP2SHClicked)
      self.connect(btnCancel, SIGNAL(CLICKED), self.reject)


      dlgLayout = QGridLayout()
      dlgLayout.addWidget(lblDescr, 0, 0)
      dlgLayout.addWidget(HLINE(), 1, 0)
      dlgLayout.addWidget(lblToWlt, 2, 0)
      dlgLayout.addWidget(self.wltDispView, 3, 0)
      dlgLayout.addWidget(makeHorizFrame([self.lblSelectWlt, \
                                          self.addrTypeSelectFrame.getFrame(), \
                                          self.btnSelectWlt]), 4, 0)
      dlgLayout.addWidget(HLINE(), 6, 0)
      dlgLayout.addWidget(lblToAddr, 7, 0)
      dlgLayout.addWidget(self.tabWidget, 8, 0)
      dlgLayout.addWidget(makeHorizFrame([STRETCH, self.useBareMultiSigCheckBox, self.ttipBareMS, self.btnSelectAddr]), 9, 0)
      dlgLayout.addWidget(HLINE(), 10, 0)
      dlgLayout.addWidget(makeHorizFrame([btnCancel, STRETCH]), 11, 0)
      dlgLayout.setRowStretch(3, 1)
      dlgLayout.setRowStretch(8, 2)

      self.setLayout(dlgLayout)
      self.sizeHint = lambda: QSize(760, 500)

      # Auto-select the default wallet, if there is one
      rowNum = 0
      if defaultWltID and self.main.walletMap.has_key(defaultWltID):
         rowNum = self.main.walletIndices[defaultWltID]
      rowIndex = self.wltDispModel.index(rowNum, 0)
      self.wltDispView.setCurrentIndex(rowIndex)

      self.setWindowTitle('Address Book')
      self.setWindowIcon(QIcon(self.main.iconfile))

      self.setMinimumWidth(300)

      hexgeom = self.main.settings.get('AddrBookGeometry')
      wltgeom = self.main.settings.get('AddrBookWltTbl')
      rxgeom = self.main.settings.get('AddrBookRxTbl')
      txgeom = self.main.settings.get('AddrBookTxTbl')
      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(wltgeom) > 0:
         restoreTableView(self.wltDispView, wltgeom)
      if len(rxgeom) > 0:
         restoreTableView(self.addrBookRxView, rxgeom)
      if len(txgeom) > 0 and not selectMineOnly:
         restoreTableView(self.addrBookTxView, txgeom)

   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('AddrBookGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('AddrBookWltTbl', saveTableView(self.wltDispView))
      self.main.writeSetting('AddrBookRxTbl', saveTableView(self.addrBookRxView))
      self.main.writeSetting('AddrBookTxTbl', saveTableView(self.addrBookTxView))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).reject(*args)

   #############################################################################
   def setAddrBookTxModel(self, wltID):
      self.addrBookTxModel = SentToAddrBookModel(wltID, self.main)

      #
      self.addrBookTxProxy = SentAddrSortProxy(self)
      self.addrBookTxProxy.setSourceModel(self.addrBookTxModel)
      # self.addrBookTxProxy.sort(ADDRBOOKCOLS.Address)

      self.addrBookTxView.setModel(self.addrBookTxProxy)
      self.addrBookTxView.setSortingEnabled(True)
      self.addrBookTxView.setSelectionBehavior(QTableView.SelectRows)
      self.addrBookTxView.setSelectionMode(QTableView.SingleSelection)
      self.addrBookTxView.horizontalHeader().setStretchLastSection(True)
      self.addrBookTxView.verticalHeader().setDefaultSectionSize(20)
      freqSize = 1.3 * tightSizeStr(self.addrBookTxView, 'Times Used')[0]
      initialColResize(self.addrBookTxView, [0.3, 0.1, freqSize, 0.5])
      self.addrBookTxView.hideColumn(ADDRBOOKCOLS.WltID)
      self.connect(self.addrBookTxView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.addrTableTxClicked)

   #############################################################################
   def disableSelectButtons(self):
      self.btnSelectAddr.setText(self.tr('None Selected'))
      self.btnSelectAddr.setEnabled(False)
      self.useBareMultiSigCheckBox.setChecked(False)
      self.useBareMultiSigCheckBox.setEnabled(False)


   #############################################################################
   # Update the controls when the tab changes
   def tabChanged(self, index):
      if not self.isBrowsingOnly:
         if self.tabWidget.currentWidget() == self.lboxView:
            self.useBareMultiSigCheckBox.setVisible(self.btnSelectAddr.isVisible())
            self.ttipBareMS.setVisible(self.btnSelectAddr.isVisible())
            selectedLockBox = self.getSelectedLBID()
            self.btnSelectAddr.setEnabled(selectedLockBox != None)
            if selectedLockBox:
               self.btnSelectAddr.setText( createLockboxEntryStr(selectedLockBox,
                                                                 self.useBareMultiSigCheckBox.isChecked()))
               self.useBareMultiSigCheckBox.setEnabled(True)
            else:
               self.disableSelectButtons()
         elif self.tabWidget.currentWidget() == self.addrBookTxView:
            self.useBareMultiSigCheckBox.setVisible(False)
            self.ttipBareMS.setVisible(False)
            selection = self.addrBookTxView.selectedIndexes()
            if len(selection)==0:
               self.disableSelectButtons()
            else:
               self.addrTableTxClicked(selection[0])
         elif self.tabWidget.currentWidget() == self.addrBookRxView:
            self.useBareMultiSigCheckBox.setVisible(False)
            self.ttipBareMS.setVisible(False)
            selection = self.addrBookRxView.selectedIndexes()
            if len(selection)==0:
               self.disableSelectButtons()
            else:
               self.addrTableRxClicked(selection[0])


   #############################################################################
   def setAddrBookRxModel(self, wltID):
      wlt = self.main.walletMap[wltID]
      self.addrBookRxModel = WalletAddrDispModel(wlt, self)

      self.addrBookRxProxy = WalletAddrSortProxy(self)
      self.addrBookRxProxy.setSourceModel(self.addrBookRxModel)
      # self.addrBookRxProxy.sort(ADDRESSCOLS.Address)

      self.addrBookRxView.setModel(self.addrBookRxProxy)
      self.addrBookRxView.setSelectionBehavior(QTableView.SelectRows)
      self.addrBookRxView.setSelectionMode(QTableView.SingleSelection)
      self.addrBookRxView.horizontalHeader().setStretchLastSection(True)
      self.addrBookRxView.verticalHeader().setDefaultSectionSize(20)
      iWidth = tightSizeStr(self.addrBookRxView, 'Imp')[0]
      initialColResize(self.addrBookRxView, [iWidth * 1.3, 0.3, 0.35, 64, 0.3])
      self.connect(self.addrBookRxView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.addrTableRxClicked)

   #############################################################################
   def getAddrStr(self, wlt, addrObj):
      addrStr = ""
      
      cppwlt = wlt
      if isinstance(wlt, PyBtcWallet):
         cppwlt = wlt.cppWallet
         
      if self.addrType == 'P2PKH':
         addrStr = cppwlt.getP2PKHAddrForIndex(addrObj.chainIndex)
      elif self.addrType == 'P2SH-P2PK':
         addrStr = cppwlt.getNestedP2PKAddrForIndex(addrObj.chainIndex)
      elif self.addrType == 'P2SH-P2WPKH':
         addrStr = cppwlt.getNestedSWAddrForIndex(addrObj.chainIndex)
            
      return addrStr      
      
   #############################################################################
   def wltTableClicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      self.btnSelectWlt.setEnabled(True)
      row = currIndex.row()
      self.selectedWltID = str(currIndex.model().index(row, WLTVIEWCOLS.ID).data().toString())

      self.setAddrBookTxModel(self.selectedWltID)
      self.setAddrBookRxModel(self.selectedWltID)


      if not self.isBrowsingOnly:
         wlt = self.main.walletMap[self.selectedWltID]
         self.btnSelectWlt.setText(self.tr('%1 Wallet: %2').arg(self.actStr, self.selectedWltID))
         nextAddr = wlt.peekNextUnusedAddr()

         # If switched wallet selection, de-select address so it doesn't look
         # like the currently-selected address is for this different wallet
         if not self.tabWidget.currentWidget() == self.lboxView:
            self.disableSelectButtons()
            self.selectedAddr = ''
            self.selectedCmmt = ''
      self.addrBookTxModel.reset()


   #############################################################################
   def addrTableTxClicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      self.btnSelectAddr.setEnabled(True)
      row = currIndex.row()
      self.selectedAddr = str(currIndex.model().index(row, ADDRBOOKCOLS.Address).data().toString())
      self.selectedCmmt = str(currIndex.model().index(row, ADDRBOOKCOLS.Comment).data().toString())

      if not self.isBrowsingOnly:
         self.btnSelectAddr.setText(self.tr('%1 Address: %2...').arg(self.actStr, self.selectedAddr[:10]))


   #############################################################################
   def addrTableRxClicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      self.btnSelectAddr.setEnabled(True)
      row = currIndex.row()
      self.selectedAddr = str(currIndex.model().index(row, ADDRESSCOLS.Address).data().toString())
      self.selectedCmmt = str(currIndex.model().index(row, ADDRESSCOLS.Comment).data().toString())

      if not self.isBrowsingOnly:
         self.btnSelectAddr.setText(self.tr('%1 Address: %2...').arg(self.actStr, self.selectedAddr[:10]))

   #############################################################################
   def dblClickAddressRx(self, index):
      if index.column() != ADDRESSCOLS.Comment:
         self.acceptAddrSelection()
         return

      wlt = self.main.walletMap[self.selectedWltID]

      if not self.selectedCmmt:
         dialog = DlgSetComment(self, self.main, self.selectedCmmt, self.tr('Add Address Comment'))
      else:
         dialog = DlgSetComment(self, self.main, self.selectedCmmt, self.tr('Change Address Comment'))
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         addr160 = addrStr_to_hash160(self.selectedAddr)[1]
         wlt.setComment(addr160, newComment)

   #############################################################################
   def getSelectedLBID(self):
      selection = self.lboxView.selectedIndexes()
      if len(selection)==0:
         return None
      row = selection[0].row()
      idCol = LOCKBOXCOLS.ID
      return str(self.lboxView.model().index(row, idCol).data().toString())

   #############################################################################
   def dblClickedLockbox(self, index):
      self.acceptLockBoxSelection()

   #############################################################################
   def clickedLockbox(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      row = currIndex.row()

      if not self.isBrowsingOnly:
         self.btnSelectAddr.setEnabled(True)
         self.useBareMultiSigCheckBox.setEnabled(True)
         selectedLockBoxId = str(currIndex.model().index(row, LOCKBOXCOLS.ID).data().toString())
         self.btnSelectAddr.setText( createLockboxEntryStr(selectedLockBoxId,
                                      self.useBareMultiSigCheckBox.isChecked()))

         # Disable Bare multisig if mainnet and N>3
         lb = self.main.getLockboxByID(selectedLockBoxId)
         if lb.N>3 and not USE_TESTNET and not USE_REGTEST:
            self.useBareMultiSigCheckBox.setEnabled(False)
            self.useBareMultiSigCheckBox.setChecked(False)
            self.useBareMultiSigCheckBox.setToolTip(self.tr(
               'Bare multi-sig is not available for M-of-N lockboxes on the '
               'main Bitcoin network with N higher than 3.'))
         else:
            self.useBareMultiSigCheckBox.setEnabled(True)

   #############################################################################
   def dblClickAddressTx(self, index):
      if index.column() != ADDRBOOKCOLS.Comment:
         self.acceptAddrSelection()
         return

      wlt = self.main.walletMap[self.selectedWltID]

      if not self.selectedCmmt:
         dialog = DlgSetComment(self, self.main, self.selectedCmmt, self.tr('Add Address Comment'))
      else:
         dialog = DlgSetComment(self, self.main, self.selectedCmmt, self.tr('Change Address Comment'))
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         addr160 = addrStr_to_hash160(self.selectedAddr)[1]
         wlt.setComment(addr160, newComment)

   #############################################################################
   def acceptWltSelection(self):
      wltID = self.selectedWltID
      addrObj = self.main.walletMap[wltID].getNextUnusedAddress()
      if not self.returnPubKey:
         addrStr = self.getAddrStr(self.main.walletMap[wltID], addrObj)
         self.target.setText(addrStr)
      else:
         pubKeyHash = addrObj.getPubKey().toHexStr()
         if pubKeyHash is None:
            return
         self.target.setText(pubKeyHash)
      self.target.setCursorPosition(0)
      self.accept()

   #############################################################################
   def useP2SHClicked(self):
      self.btnSelectAddr.setText( createLockboxEntryStr(self.getSelectedLBID(),
                                                    self.useBareMultiSigCheckBox.isChecked()))

   #############################################################################
   def acceptAddrSelection(self):
      if isBareLockbox(str(self.btnSelectAddr.text())) or \
         isP2SHLockbox(str(self.btnSelectAddr.text())):
         self.acceptLockBoxSelection()
      else:
         atype,a160 = addrStr_to_hash160(self.selectedAddr)
         if atype==P2SHBYTE and self.returnPubKey:
            LOGERROR('Cannot select P2SH address when selecting a public key!')
            QMessageBox.critical(self, self.tr("P2SH Not Allowed"), self.tr(
               'This operation requires a public key, but you selected a '
               'P2SH address which does not have a public key (these addresses '
               'start with "2" or "3").  Please select a different address.'), \
               QMessageBox.Ok)
            return

         if self.target:
            if not self.returnPubKey:
               self.target.setText(self.selectedAddr)
            else:
               pubKeyHash = self.getPubKeyForAddr160(a160)
               if pubKeyHash is None:
                  return
               self.target.setText(pubKeyHash)

            self.target.setCursorPosition(0)
            self.accept()

   #############################################################################
   def acceptLockBoxSelection(self):
      if self.target:
         self.target.setText( createLockboxEntryStr(self.getSelectedLBID(),
                                                    self.useBareMultiSigCheckBox.isChecked()))
         self.target.setCursorPosition(0)
         self.accept()

   #############################################################################
   def getPubKeyForAddr160(self, addr160):
      if not self.returnPubKey:
         LOGERROR('Requested getPubKeyNotAddr, but looks like addr requested')

      wid = self.main.getWalletForAddr160(addr160)
      if not wid:
         QMessageBox.critical(self, self.tr('No Public Key'), self.tr(
            'This operation requires a full public key, not just an address. '
            'Unfortunately, Armory cannot find the public key for the address '
            'you selected.  In general public keys will only be available '
            'for addresses in your wallet.'), QMessageBox.Ok)
         return None

      wlt = self.main.walletMap[wid]
      return wlt.getAddrByHash160(addr160).binPublicKey65.toHexStr()




   #############################################################################
   def showContextMenuTx(self, pos):
      menu = QMenu(self.addrBookTxView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:  actionCopyAddr = menu.addAction(self.tr("Copy Address"))
      if dev:   actionCopyHash160 = menu.addAction(self.tr("Copy Hash160 (hex)"))
      if True:  actionCopyComment = menu.addAction(self.tr("Copy Comment"))
      idx = self.addrBookTxView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())

      if action == actionCopyAddr:
         s = self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Address).data().toString()
      elif dev and action == actionCopyHash160:
         s = str(self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Address).data().toString())
         atype, addr160 = addrStr_to_hash160(s)
         if atype==P2SHBYTE:
            LOGWARN('Copying Hash160 of P2SH address: %s' % s)
         s = binary_to_hex(addr160)
      elif action == actionCopyComment:
         s = self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Comment).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())


   #############################################################################
   def showContextMenuRx(self, pos):
      menu = QMenu(self.addrBookRxView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:  actionCopyAddr = menu.addAction(self.tr("Copy Address"))
      if dev:   actionCopyHash160 = menu.addAction(self.tr("Copy Hash160 (hex)"))
      if True:  actionCopyComment = menu.addAction(self.tr("Copy Comment"))
      idx = self.addrBookRxView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())

      if action == actionCopyAddr:
         s = self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString()
      elif dev and action == actionCopyHash160:
         s = str(self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString())
         atype, addr160 = addrStr_to_hash160(s)
         if atype==P2SHBYTE:
            LOGWARN('Copying Hash160 of P2SH address: %s' % s)
         s = binary_to_hex(addr160)
      elif action == actionCopyComment:
         s = self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Comment).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())


################################################################################
def createAddrBookButton(parent, targWidget, defaultWltID=None, actionStr="Select",
                         selectExistingOnly=False, selectMineOnly=False, getPubKey=False,
                         showLockboxes=True):
   action = parent.tr("Select");
   btn = QPushButton('')
   ico = QIcon(QPixmap(':/addr_book_icon.png'))
   btn.setIcon(ico)
   def execAddrBook():
      if len(parent.main.walletMap) == 0:
         QMessageBox.warning(parent, parent.tr('No wallets!'), parent.tr('You have no wallets so '
            'there is no address book to display.'), QMessageBox.Ok)
         return
      dlg = DlgAddressBook(parent, parent.main, targWidget, defaultWltID,
                    action, selectExistingOnly, selectMineOnly, getPubKey,
                           showLockboxes)
      dlg.exec_()

   btn.setMaximumWidth(24)
   btn.setMaximumHeight(24)
   parent.connect(btn, SIGNAL(CLICKED), execAddrBook)
   btn.setToolTip(parent.tr('Select from Address Book'))
   return btn


################################################################################
class DlgHelpAbout(ArmoryDialog):
   def __init__(self, putResultInWidget, defaultWltID=None, parent=None, main=None):
      super(DlgHelpAbout, self).__init__(parent, main)

      imgLogo = QLabel()
      imgLogo.setPixmap(QPixmap(':/armory_logo_h56.png'))
      imgLogo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      if BTCARMORY_BUILD != None:
         lblHead = QRichLabel(self.tr('Armory Bitcoin Wallet : Version %1-beta-%2').arg(getVersionString(BTCARMORY_VERSION), BTCARMORY_BUILD), doWrap=False)
      else:
         lblHead = QRichLabel(self.tr('Armory Bitcoin Wallet : Version %1-beta').arg(getVersionString(BTCARMORY_VERSION)), doWrap=False)

      lblOldCopyright = QRichLabel(self.tr( u'Copyright &copy; 2011-2015 Armory Technologies, Inc.'))
      lblCopyright = QRichLabel(self.tr( u'Copyright &copy; 2016 Goatpig'))
      lblOldLicense = QRichLabel(self.tr( u'Licensed to Armory Technologies, Inc. under the '
                              '<a href="http://www.gnu.org/licenses/agpl-3.0.html">'
                              'Affero General Public License, Version 3</a> (AGPLv3)'))
      lblOldLicense.setOpenExternalLinks(True)
      lblLicense = QRichLabel(self.tr( u'Licensed to Goatpig under the '
                              '<a href="https://opensource.org/licenses/mit-license.php">'
                              'MIT License'))
      lblLicense.setOpenExternalLinks(True)

      lblHead.setAlignment(Qt.AlignHCenter)
      lblCopyright.setAlignment(Qt.AlignHCenter)
      lblOldCopyright.setAlignment(Qt.AlignHCenter)
      lblLicense.setAlignment(Qt.AlignHCenter)
      lblOldLicense.setAlignment(Qt.AlignHCenter)

      dlgLayout = QHBoxLayout()
      dlgLayout.addWidget(makeVertFrame([imgLogo, lblHead, lblCopyright, lblOldCopyright, STRETCH, lblLicense, lblOldLicense]))
      self.setLayout(dlgLayout)

      self.setMinimumWidth(450)

      self.setWindowTitle(self.tr('About Armory'))


################################################################################
class DlgSettings(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgSettings, self).__init__(parent, main)



      ##########################################################################
      # bitcoind-management settings
      self.chkManageSatoshi = QCheckBox(self.tr(
         'Let Armory run Bitcoin Core/bitcoind in the background'))
      self.edtSatoshiExePath = QLineEdit()
      self.edtSatoshiHomePath = QLineEdit()
      self.edtSatoshiExePath.setMinimumWidth(tightSizeNChar(GETFONT('Fixed', 10), 40)[0])
      self.connect(self.chkManageSatoshi, SIGNAL(CLICKED), self.clickChkManage)
      self.startChk = self.main.getSettingOrSetDefault('ManageSatoshi', not OS_MACOSX)
      if self.startChk:
         self.chkManageSatoshi.setChecked(True)
      if OS_MACOSX:
         self.chkManageSatoshi.setEnabled(False)
         lblManageSatoshi = QRichLabel(\
            self.tr('Bitcoin Core/bitcoind management is not available on Mac/OSX'))
      else:
         if self.main.settings.hasSetting('SatoshiExe'):
            satexe = self.main.settings.get('SatoshiExe')

         sathome = BTC_HOME_DIR
         if self.main.settings.hasSetting('SatoshiDatadir'):
            sathome = self.main.settings.get('SatoshiDatadir')

         lblManageSatoshi = QRichLabel(
            self.tr('<b>Bitcoin Software Management</b>'
            '<br><br>'
            'By default, Armory will manage the Bitcoin engine/software in the '
            'background.  You can choose to manage it yourself, or tell Armory '
            'about non-standard installation configuration.'))
      if self.main.settings.hasSetting('SatoshiExe'):
         self.edtSatoshiExePath.setText(self.main.settings.get('SatoshiExe'))
         self.edtSatoshiExePath.home(False)
      if self.main.settings.hasSetting('SatoshiDatadir'):
         self.edtSatoshiHomePath.setText(self.main.settings.get('SatoshiDatadir'))
         self.edtSatoshiHomePath.home(False)

      lblDescrExe = QRichLabel(self.tr('Bitcoin Install Dir:'))
      lblDescrHome = QRichLabel(self.tr('Bitcoin Home Dir:'))
      lblDefaultExe = QRichLabel(self.tr('Leave blank to have Armory search default '
                                  'locations for your OS'), size=2)
      lblDefaultHome = QRichLabel(self.tr('Leave blank to use default datadir '
                                  '(%1)').arg(BTC_HOME_DIR), size=2)

      self.btnSetExe = createDirectorySelectButton(self, self.edtSatoshiExePath)
      self.btnSetHome = createDirectorySelectButton(self, self.edtSatoshiHomePath)

      layoutMgmt = QGridLayout()
      layoutMgmt.addWidget(lblManageSatoshi, 0, 0, 1, 3)
      layoutMgmt.addWidget(self.chkManageSatoshi, 1, 0, 1, 3)

      layoutMgmt.addWidget(lblDescrExe, 2, 0)
      layoutMgmt.addWidget(self.edtSatoshiExePath, 2, 1)
      layoutMgmt.addWidget(self.btnSetExe, 2, 2)
      layoutMgmt.addWidget(lblDefaultExe, 3, 1, 1, 2)

      layoutMgmt.addWidget(lblDescrHome, 4, 0)
      layoutMgmt.addWidget(self.edtSatoshiHomePath, 4, 1)
      layoutMgmt.addWidget(self.btnSetHome, 4, 2)
      layoutMgmt.addWidget(lblDefaultHome, 5, 1, 1, 2)
      frmMgmt = QFrame()
      frmMgmt.setLayout(layoutMgmt)

      self.clickChkManage()
      ##########################################################################


      lblDefaultUriTitle = QRichLabel(self.tr('<b>Set Armory as default URL handler</b>'))
      lblDefaultURI = QRichLabel(self.tr(
         'Set Armory to be the default when you click on "bitcoin:" '
         'links in your browser or in emails. '
         'You can test if your operating system is supported by clicking '
         'on a "bitcoin:" link right after clicking this button.'))
      btnDefaultURI = QPushButton(self.tr('Set Armory as Default'))
      frmBtnDefaultURI = makeHorizFrame([btnDefaultURI, 'Stretch'])

      self.chkAskURIAtStartup = QCheckBox(self.tr(
         'Check whether Armory is the default handler at startup'))
      askuriDNAA = self.main.getSettingOrSetDefault('DNAA_DefaultApp', False)
      self.chkAskURIAtStartup.setChecked(not askuriDNAA)

      def clickRegURI():
         self.main.setupUriRegistration(justDoIt=True)
         QMessageBox.information(self, self.tr('Registered'), self.tr(
            'Armory just attempted to register itself to handle "bitcoin:" '
            'links, but this does not work on all operating systems.'), QMessageBox.Ok)

      self.connect(btnDefaultURI, SIGNAL(CLICKED), clickRegURI)

      ###############################################################
      # Minimize on Close
      lblMinimizeDescr = QRichLabel(self.tr(
         '<b>Minimize to System Tray</b> '
         '<br>'
         'You can have Armory automatically minimize itself to your system '
         'tray on open or close.  Armory will stay open but run in the '
         'background, and you will still receive notifications.  Access Armory '
         'through the icon on your system tray. '
         '<br><br>'
         'If you select "Minimize on close", the \'x\' on the top window bar will '
         'minimize Armory instead of exiting the application.  You can always use '
         '<i>"File"</i> -> <i>"Quit Armory"</i> to actually close it.'))

      moo = self.main.getSettingOrSetDefault('MinimizeOnOpen', False)
      self.chkMinOnOpen = QCheckBox(self.tr('Minimize to system tray on open'))
      if moo:
         self.chkMinOnOpen.setChecked(True)

      moc = self.main.getSettingOrSetDefault('MinimizeOrClose', 'DontKnow')
      self.chkMinOrClose = QCheckBox(self.tr('Minimize to system tray on close'))

      if moc == 'Minimize':
         self.chkMinOrClose.setChecked(True)


      ###############################################################
      # System tray notifications. On OS X, notifications won't work on 10.7.
      # OS X's built-in notification system was implemented starting in 10.8.
      osxMinorVer = '0'
      if OS_MACOSX:
         osxMinorVer = OS_VARIANT[0].split(".")[1]

      lblNotify = QRichLabel(self.tr('<b>Enable notifications from the system-tray:</b>'))
      self.chkBtcIn = QCheckBox(self.tr('Bitcoins Received'))
      self.chkBtcOut = QCheckBox(self.tr('Bitcoins Sent'))
      self.chkDiscon = QCheckBox(self.tr('Bitcoin Core/bitcoind disconnected'))
      self.chkReconn = QCheckBox(self.tr('Bitcoin Core/bitcoind reconnected'))

      # FYI:If we're not on OS X, the if condition will never be hit.
      if (OS_MACOSX) and (int(osxMinorVer) < 7):
         lblNotify = QRichLabel(self.tr('<b>Sorry!  Notifications are not available ' \
                                'on your version of OS X.</b>'))
         self.chkBtcIn.setChecked(False)
         self.chkBtcOut.setChecked(False)
         self.chkDiscon.setChecked(False)
         self.chkReconn.setChecked(False)
         self.chkBtcIn.setEnabled(False)
         self.chkBtcOut.setEnabled(False)
         self.chkDiscon.setEnabled(False)
         self.chkReconn.setEnabled(False)
      else:
         notifyBtcIn = self.main.getSettingOrSetDefault('NotifyBtcIn', True)
         notifyBtcOut = self.main.getSettingOrSetDefault('NotifyBtcOut', True)
         notifyDiscon = self.main.getSettingOrSetDefault('NotifyDiscon', True)
         notifyReconn = self.main.getSettingOrSetDefault('NotifyReconn', True)
         self.chkBtcIn.setChecked(notifyBtcIn)
         self.chkBtcOut.setChecked(notifyBtcOut)
         self.chkDiscon.setChecked(notifyDiscon)
         self.chkReconn.setChecked(notifyReconn)

      ###############################################################
      # Date format preferences
      exampleTimeTuple = (2012, 4, 29, 19, 45, 0, -1, -1, -1)
      self.exampleUnixTime = time.mktime(exampleTimeTuple)
      exampleStr = unixTimeToFormatStr(self.exampleUnixTime, '%c')
      lblDateFmt = QRichLabel(self.tr('<b>Preferred Date Format<b>:<br>'))
      lblDateDescr = QRichLabel(self.tr(
                          'You can specify how you would like dates '
                          'to be displayed using percent-codes to '
                          'represent components of the date.  The '
                          'mouseover text of the "(?)" icon shows '
                          'the most commonly used codes/symbols.  '
                          'The text next to it shows how '
                          '"%1" would be shown with the '
                          'specified format.').arg(exampleStr))
      lblDateFmt.setAlignment(Qt.AlignTop)
      fmt = self.main.getPreferredDateFormat()
      ttipStr = self.tr('Use any of the following symbols:<br>')
      fmtSymbols = [x[0] + ' = ' + x[1] for x in FORMAT_SYMBOLS]
      ttipStr += '<br>'.join(fmtSymbols)

      fmtSymbols = [x[0] + '~' + x[1] for x in FORMAT_SYMBOLS]
      lblStk = QRichLabel('; '.join(fmtSymbols))

      self.edtDateFormat = QLineEdit()
      self.edtDateFormat.setText(fmt)
      self.ttipFormatDescr = self.main.createToolTipWidget(ttipStr)

      self.lblDateExample = QRichLabel('', doWrap=False)
      self.connect(self.edtDateFormat, SIGNAL('textEdited(QString)'), self.doExampleDate)
      self.doExampleDate()
      self.btnResetFormat = QPushButton(self.tr("Reset to Default"))

      def doReset():
         self.edtDateFormat.setText(DEFAULT_DATE_FORMAT)
         self.doExampleDate()
      self.connect(self.btnResetFormat, SIGNAL(CLICKED), doReset)

      # Make a little subframe just for the date format stuff... everything
      # fits nicer if I do this...
      frmTop = makeHorizFrame([self.lblDateExample, STRETCH, self.ttipFormatDescr])
      frmMid = makeHorizFrame([self.edtDateFormat])
      frmBot = makeHorizFrame([self.btnResetFormat, STRETCH])
      fStack = makeVertFrame([frmTop, frmMid, frmBot, STRETCH])
      lblStk = makeVertFrame([lblDateFmt, lblDateDescr, STRETCH])
      subFrm = makeHorizFrame([lblStk, STRETCH, fStack])


      # Save/Cancel Button
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.btnAccept = QPushButton(self.tr("Save"))
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)

      ################################################################
      # User mode selection
      self.cmbUsermode = QComboBox()
      self.cmbUsermode.clear()
      self.cmbUsermode.addItem(self.tr('Standard'))
      self.cmbUsermode.addItem(self.tr('Advanced'))
      self.cmbUsermode.addItem(self.tr('Expert'))

      self.usermodeInit = self.main.usermode

      if self.main.usermode == USERMODE.Standard:
         self.cmbUsermode.setCurrentIndex(0)
      elif self.main.usermode == USERMODE.Advanced:
         self.cmbUsermode.setCurrentIndex(1)
      elif self.main.usermode == USERMODE.Expert:
         self.cmbUsermode.setCurrentIndex(2)

      lblUsermode = QRichLabel(self.tr('<b>Armory user mode:</b>'))
      self.lblUsermodeDescr = QRichLabel('')
      self.setUsermodeDescr()

      self.connect(self.cmbUsermode, SIGNAL('activated(int)'), self.setUsermodeDescr)

      ###############################################################
      # Language preferences
      self.lblLang = QRichLabel(self.tr('<b>Preferred Language<b>:<br>'))
      self.lblLangDescr = QRichLabel(self.tr(
         'Specify which language you would like Armory to be displayed in.'))
      self.cmbLang = QComboBox()
      self.cmbLang.clear()
      for lang in LANGUAGES:
         self.cmbLang.addItem(QLocale(lang).nativeLanguageName() + " (" + lang + ")")
      self.cmbLang.setCurrentIndex(LANGUAGES.index(self.main.language))
      self.langInit = self.main.language

      frmLayout = QGridLayout()

      i = 0
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(frmMgmt, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(lblDefaultUriTitle, i, 0)
      i += 1
      frmLayout.addWidget(lblDefaultURI, i, 0, 1, 3)
      i += 1
      frmLayout.addWidget(frmBtnDefaultURI, i, 0, 1, 3)
      i += 1
      frmLayout.addWidget(self.chkAskURIAtStartup, i, 0, 1, 3)
      
      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(subFrm, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(lblMinimizeDescr, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkMinOnOpen, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkMinOrClose, i, 0, 1, 3)


      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(lblNotify, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkBtcIn, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkBtcOut, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkDiscon, i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.chkReconn, i, 0, 1, 3)


      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(lblUsermode, i, 0)
      frmLayout.addWidget(QLabel(''), i, 1)
      frmLayout.addWidget(self.cmbUsermode, i, 2)

      i += 1
      frmLayout.addWidget(self.lblUsermodeDescr, i, 0, 1, 3)


      i += 1
      frmLayout.addWidget(HLINE(), i, 0, 1, 3)

      i += 1
      frmLayout.addWidget(self.lblLang, i, 0)
      frmLayout.addWidget(QLabel(''), i, 1)
      frmLayout.addWidget(self.cmbLang, i, 2)

      i += 1
      frmLayout.addWidget(self.lblLangDescr, i, 0, 1, 3)


      frmOptions = QFrame()
      frmOptions.setLayout(frmLayout)
      
      self.settingsTab = QTabWidget()
      self.settingsTab.addTab(frmOptions, self.tr("General"))
      
      #FeeChange tab
      self.setupExtraTabs()      
      frmFeeChange = makeVertFrame([\
         self.frmFee, self.frmChange, self.frmAddrType, 'Stretch'])
      
      self.settingsTab.addTab(frmFeeChange, self.tr("Fee and Address Types"))
      
      self.scrollOptions = QScrollArea()
      self.scrollOptions.setWidget(self.settingsTab)



      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(self.scrollOptions)
      dlgLayout.addWidget(makeHorizFrame([STRETCH, self.btnCancel, self.btnAccept]))

      self.setLayout(dlgLayout)

      self.setMinimumWidth(650)
      self.setWindowTitle(self.tr('Armory Settings'))

   #############################################################################
   def setupExtraTabs(self):
      ##########
      #fee
      
      feeByte = self.main.getSettingOrSetDefault('Default_FeeByte', MIN_FEE_BYTE)
      txFee = self.main.getSettingOrSetDefault('Default_Fee', MIN_TX_FEE)
      adjustFee = self.main.getSettingOrSetDefault('AdjustFee', True)
      feeOpt = self.main.getSettingOrSetDefault('FeeOption', DEFAULT_FEE_TYPE)
      blocksToConfirm = self.main.getSettingOrSetDefault(\
         "Default_FeeByte_BlocksToConfirm", NBLOCKS_TO_CONFIRM)
      
      def feeRadio(strArg):
         self.radioAutoFee.setChecked(False)
         
         self.radioFeeByte.setChecked(False)
         self.leFeeByte.setEnabled(False)
         
         self.radioFlatFee.setChecked(False)
         self.leFlatFee.setEnabled(False)
         
         if strArg == 'Auto':
            self.radioAutoFee.setChecked(True)
         elif strArg == 'FeeByte':
            self.radioFeeByte.setChecked(True)
            self.leFeeByte.setEnabled(True)
         elif strArg == 'FlatFee':
            self.radioFlatFee.setChecked(True)
            self.leFlatFee.setEnabled(True)
            
         self.feeOpt = strArg
            
      def getCallbck(strArg):
         def callbck():
            return feeRadio(strArg)
         return callbck
      
      labelFee = QRichLabel(self.tr("<b>Fee<br></b>"))
      
      self.radioAutoFee = QRadioButton(self.tr("Auto fee/byte"))
      self.connect(self.radioAutoFee, SIGNAL('clicked()'), getCallbck('Auto'))
      self.sliderAutoFee = QSlider(Qt.Horizontal, self)
      self.sliderAutoFee.setMinimum(2)
      self.sliderAutoFee.setMaximum(6)
      self.sliderAutoFee.setValue(blocksToConfirm)
      self.lblSlider = QLabel()
      
      def getLblSliderText():
         blocksToConfirm = unicode(self.sliderAutoFee.value())
         return self.tr("Blocks to confirm: %1").arg(blocksToConfirm)
      
      def setLblSliderText():
         self.lblSlider.setText(getLblSliderText())
      
      setLblSliderText()
      self.sliderAutoFee.valueChanged.connect(setLblSliderText)
      
      toolTipAutoFee = self.main.createToolTipWidget(self.tr(
      'Fetch fee/byte from local Bitcoin node. '
      'Defaults to manual fee/byte on failure.'))
      
      self.radioFeeByte = QRadioButton(self.tr("Manual fee/byte"))
      self.connect(self.radioFeeByte, SIGNAL('clicked()'), getCallbck('FeeByte'))
      self.leFeeByte = QLineEdit(str(feeByte))
      toolTipFeeByte = self.main.createToolTipWidget(self.tr('Values in satoshis/byte'))
      
      self.radioFlatFee = QRadioButton(self.tr("Flat fee"))
      self.connect(self.radioFlatFee, SIGNAL('clicked()'), getCallbck('FlatFee'))
      self.leFlatFee = QLineEdit(coin2str(txFee, maxZeros=0))
      toolTipFlatFee = self.main.createToolTipWidget(self.tr('Values in BTC'))
      
      self.checkAdjust = QCheckBox(self.tr("Auto-adjust fee/byte for better privacy"))
      self.checkAdjust.setChecked(adjustFee)
      feeToolTip = self.main.createToolTipWidget(self.tr(
      'Auto-adjust fee may increase your total fee using the selected fee/byte rate '
      'as its basis in an attempt to align the amount of digits after the decimal '
      'point between your spend values and change value.'
      '<br><br>'
      'The purpose of this obfuscation technique is to make the change output '
      'less obvious. '
      '<br><br>'
      'The auto-adjust fee feature only applies to fee/byte options '
      'and does not inflate your fee by more that 10% of its original value.'))
      
      frmFeeLayout = QGridLayout()
      frmFeeLayout.addWidget(labelFee, 0, 0, 1, 1)
      
      frmAutoFee = makeHorizFrame([self.radioAutoFee, self.lblSlider, toolTipAutoFee])
      frmFeeLayout.addWidget(frmAutoFee, 1, 0, 1, 1)
      frmFeeLayout.addWidget(self.sliderAutoFee, 2, 0, 1, 2)
      
      frmFeeByte = makeHorizFrame([self.radioFeeByte, self.leFeeByte, \
                                   toolTipFeeByte, STRETCH, STRETCH])
      frmFeeLayout.addWidget(frmFeeByte, 3, 0, 1, 1)
      
      frmFlatFee = makeHorizFrame([self.radioFlatFee, self.leFlatFee, \
                                   toolTipFlatFee, STRETCH, STRETCH])
      frmFeeLayout.addWidget(frmFlatFee, 4, 0, 1, 1)     
      
      frmCheckAdjust = makeHorizFrame([self.checkAdjust, feeToolTip, STRETCH])
      frmFeeLayout.addWidget(frmCheckAdjust, 5, 0, 1, 2)
      
      feeRadio(feeOpt)

      self.frmFee = QFrame()
      self.frmFee.setFrameStyle(STYLE_RAISED)
      self.frmFee.setLayout(frmFeeLayout)
      
      #########
      #change

      def setChangeType(changeType):
         self.changeType = changeType
               
      from ui.AddressTypeSelectDialog import AddressLabelFrame
      changeType = self.main.getSettingOrSetDefault('Default_ChangeType', DEFAULT_CHANGE_TYPE)
      self.changeTypeFrame = AddressLabelFrame(self.main, setChangeType)
      
      def changeRadio(strArg):
         self.radioAutoChange.setChecked(False)
         self.radioForce.setChecked(False)
         self.changeTypeFrame.getFrame().setEnabled(False)
         
         if strArg == 'Auto':
            self.radioAutoChange.setChecked(True)
            self.changeType = 'Auto'
         elif strArg == 'Force':
            self.radioForce.setChecked(True)
            self.changeTypeFrame.getFrame().setEnabled(True)
            self.changeType = self.changeTypeFrame.getType()
         else:
            self.changeTypeFrame.setType(strArg)
            self.radioForce.setChecked(True)
            self.changeTypeFrame.getFrame().setEnabled(True)
            self.changeType = self.changeTypeFrame.getType()
         
      def changeCallbck(strArg):
         def callbck():
            return changeRadio(strArg)
         return callbck
      
      
      labelChange = QRichLabel(self.tr("<b>Change Address Type<br></b>"))

      self.radioAutoChange = QRadioButton(self.tr("Auto change"))
      self.connect(self.radioAutoChange, SIGNAL('clicked()'), changeCallbck('Auto'))
      toolTipAutoChange = self.main.createToolTipWidget(self.tr(
      "Change address type will match the address type of recipient "
      "addresses. <br>"
      
      "Favors P2SH when recipients are heterogenous. <br>"
      
      "Will create nested SegWit change if inputs are SegWit and " 
      "recipient are P2SH. <br><br>"
      
      "<b>Pre 0.96 Armory cannot spend from P2SH address types</b>"
      ))
      
      self.radioForce = QRadioButton(self.tr("Force a script type:"))
      self.connect(self.radioForce, SIGNAL('clicked()'), changeCallbck('Force'))

      changeRadio(changeType)
      
      frmChangeLayout = QGridLayout()
      frmChangeLayout.addWidget(labelChange, 0, 0, 1, 1)
      
      frmAutoChange = makeHorizFrame([self.radioAutoChange, \
                                      toolTipAutoChange, STRETCH])
      frmChangeLayout.addWidget(frmAutoChange, 1, 0, 1, 1)
      
      frmForce = makeHorizFrame([self.radioForce, self.changeTypeFrame.getFrame()])
      frmChangeLayout.addWidget(frmForce, 2, 0, 1, 1)
            
      self.frmChange = QFrame()    
      self.frmChange.setFrameStyle(STYLE_RAISED)
      self.frmChange.setLayout(frmChangeLayout)
      
      #########
      #receive addr type
      
      labelAddrType = QRichLabel(self.tr("<b>Preferred Receive Address Type</b>"))
      
      def setAddrType(addrType):
         self.addrType = addrType

      self.addrType = self.main.getSettingOrSetDefault('Default_ReceiveType', DEFAULT_RECEIVE_TYPE)
      self.addrTypeFrame = AddressLabelFrame(self.main, setAddrType)
      self.addrTypeFrame.setType(self.addrType)
      
      frmAddrLayout = QGridLayout()
      frmAddrLayout.addWidget(labelAddrType, 0, 0, 1, 1)
      
      frmAddrTypeSelect = makeHorizFrame([self.addrTypeFrame.getFrame()])
      
      frmAddrLayout.addWidget(frmAddrTypeSelect, 2, 0, 1, 1)
      
      self.frmAddrType = QFrame()
      self.frmAddrType.setFrameStyle(STYLE_RAISED)
      self.frmAddrType.setLayout(frmAddrLayout)

   #############################################################################
   def accept(self, *args):

      if self.chkManageSatoshi.isChecked():
         # Check valid path is supplied for bitcoin installation
         pathExe = unicode(self.edtSatoshiExePath.text()).strip()
         if len(pathExe) > 0:
            if not os.path.exists(pathExe):
               exeName = 'bitcoin-qt.exe' if OS_WINDOWS else 'bitcoin-qt'
               QMessageBox.warning(self, self.tr('Invalid Path'),self.tr(
                  'The path you specified for the Bitcoin software installation '
                  'does not exist.  Please select the directory that contains %1 '
                  'or leave it blank to have Armory search the default location '
                  'for your operating system').arg(exeName), QMessageBox.Ok)
               return
            if os.path.isfile(pathExe):
               pathExe = os.path.dirname(pathExe)
            self.main.writeSetting('SatoshiExe', pathExe)
         else:
            self.main.settings.delete('SatoshiExe')

         # Check valid path is supplied for bitcoind home directory
         pathHome = unicode(self.edtSatoshiHomePath.text()).strip()
         if len(pathHome) > 0:
            if not os.path.exists(pathHome):
               exeName = 'bitcoin-qt.exe' if OS_WINDOWS else 'bitcoin-qt'
               QMessageBox.warning(self, self.tr('Invalid Path'), self.tr(
                  'The path you specified for the Bitcoin software home directory '
                  'does not exist.  Only specify this directory if you use a '
                  'non-standard "-datadir=" option when running Bitcoin Core or '
                  'bitcoind.  If you leave this field blank, the following '
                  'path will be used: <br><br> %1').arg(BTC_HOME_DIR), QMessageBox.Ok)
               return
            self.main.writeSetting('SatoshiDatadir', pathHome)
         else:
            self.main.settings.delete('SatoshiDatadir')

      self.main.writeSetting('ManageSatoshi', self.chkManageSatoshi.isChecked())

      # Reset the DNAA flag as needed
      askuriDNAA = self.chkAskURIAtStartup.isChecked()
      self.main.writeSetting('DNAA_DefaultApp', not askuriDNAA)

      if not self.main.setPreferredDateFormat(str(self.edtDateFormat.text())):
         return

      if not self.usermodeInit == self.cmbUsermode.currentIndex():
         self.main.setUserMode(self.cmbUsermode.currentIndex())

      if not self.langInit == self.cmbLang.currentText()[-3:-1]:
         self.main.setLang(LANGUAGES[self.cmbLang.currentIndex()])

      if self.chkMinOrClose.isChecked():
         self.main.writeSetting('MinimizeOrClose', 'Minimize')
      else:
         self.main.writeSetting('MinimizeOrClose', 'Close')

      self.main.writeSetting('MinimizeOnOpen', self.chkMinOnOpen.isChecked())

      # self.main.writeSetting('LedgDisplayFee', self.chkInclFee.isChecked())
      self.main.writeSetting('NotifyBtcIn', self.chkBtcIn.isChecked())
      self.main.writeSetting('NotifyBtcOut', self.chkBtcOut.isChecked())
      self.main.writeSetting('NotifyDiscon', self.chkDiscon.isChecked())
      self.main.writeSetting('NotifyReconn', self.chkReconn.isChecked())
      
      
      #fee
      self.main.writeSetting('FeeOption', self.feeOpt)
      self.main.writeSetting('Default_FeeByte', str(self.leFeeByte.text()))
      self.main.writeSetting('Default_Fee', str2coin(str(self.leFlatFee.text())))
      self.main.writeSetting('AdjustFee', self.checkAdjust.isChecked())
      self.main.writeSetting('Default_FeeByte_BlocksToConfirm', 
                             self.sliderAutoFee.value())
      
      #change
      self.main.writeSetting('Default_ChangeType', self.changeType)      

      #addr type
      self.main.writeSetting('Default_ReceiveType', self.addrType)
      armoryengine.ArmoryUtils.DEFAULT_ADDR_TYPE = self.addrType

      try:
         self.main.createCombinedLedger()
      except:
         pass
      super(DlgSettings, self).accept(*args)


   #############################################################################
   def setUsermodeDescr(self):
      strDescr = ''
      modeIdx = self.cmbUsermode.currentIndex()
      if modeIdx == USERMODE.Standard:
         strDescr += \
            self.tr('"Standard" is for users that only need the core set of features '
             'to send and receive bitcoins.  This includes maintaining multiple '
             'wallets, wallet encryption, and the ability to make backups '
             'of your wallets.')
      elif modeIdx == USERMODE.Advanced:
         strDescr += \
            self.tr('"Advanced" mode provides '
             'extra Armory features such as private key '
             'importing & sweeping, message signing, and the offline wallet '
             'interface.  But, with advanced features come advanced risks...')
      elif modeIdx == USERMODE.Expert:
         strDescr += \
            self.tr('"Expert" mode is similar to "Advanced" but includes '
             'access to lower-level info about transactions, scripts, keys '
             'and network protocol.  Most extra functionality is geared '
             'towards Bitcoin software developers.')
      self.lblUsermodeDescr.setText(strDescr)


   #############################################################################
   def doExampleDate(self, qstr=None):
      fmtstr = str(self.edtDateFormat.text())
      try:
         self.lblDateExample.setText(self.tr('Sample: ') + unixTimeToFormatStr(self.exampleUnixTime, fmtstr))
         self.isValidFormat = True
      except:
         self.lblDateExample.setText(self.tr('Sample: [[invalid date format]]'))
         self.isValidFormat = False

   #############################################################################
   def clickChkManage(self):
      self.edtSatoshiExePath.setEnabled(self.chkManageSatoshi.isChecked())
      self.edtSatoshiHomePath.setEnabled(self.chkManageSatoshi.isChecked())
      self.btnSetExe.setEnabled(self.chkManageSatoshi.isChecked())
      self.btnSetHome.setEnabled(self.chkManageSatoshi.isChecked())


################################################################################
class DlgExportTxHistory(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgExportTxHistory, self).__init__(parent, main)

      self.reversedLBdict = {v:k for k,v in self.main.lockboxIDMap.items()}

      self.cmbWltSelect = QComboBox()
      self.cmbWltSelect.clear()
      self.cmbWltSelect.addItem(self.tr('My Wallets'))
      self.cmbWltSelect.addItem(self.tr('Offline Wallets'))
      self.cmbWltSelect.addItem(self.tr('Other Wallets'))

      self.cmbWltSelect.insertSeparator(4)
      self.cmbWltSelect.addItem(self.tr('All Wallets'))
      self.cmbWltSelect.addItem(self.tr('All Lockboxes'))
      self.cmbWltSelect.addItem(self.tr('All Wallets & Lockboxes'))

      self.cmbWltSelect.insertSeparator(8)
      for wltID in self.main.walletIDList:
         self.cmbWltSelect.addItem(self.main.walletMap[wltID].labelName)

      self.cmbWltSelect.insertSeparator(8 + len(self.main.walletIDList))
      for idx in self.reversedLBdict:
         self.cmbWltSelect.addItem(self.main.allLockboxes[idx].shortName)


      self.cmbSortSelect = QComboBox()
      self.cmbSortSelect.clear()
      self.cmbSortSelect.addItem(self.tr('Date (newest first)'))
      self.cmbSortSelect.addItem(self.tr('Date (oldest first)'))


      self.cmbFileFormat = QComboBox()
      self.cmbFileFormat.clear()
      self.cmbFileFormat.addItem(self.tr('Comma-Separated Values (*.csv)'))


      fmt = self.main.getPreferredDateFormat()
      ttipStr = self.tr('Use any of the following symbols:<br>')
      fmtSymbols = [x[0] + ' = ' + x[1] for x in FORMAT_SYMBOLS]
      ttipStr += '<br>'.join(fmtSymbols)

      self.edtDateFormat = QLineEdit()
      self.edtDateFormat.setText(fmt)
      self.ttipFormatDescr = self.main.createToolTipWidget(ttipStr)

      self.lblDateExample = QRichLabel('', doWrap=False)
      self.connect(self.edtDateFormat, SIGNAL('textEdited(QString)'), self.doExampleDate)
      self.doExampleDate()
      self.btnResetFormat = QPushButton(self.tr("Reset to Default"))

      def doReset():
         self.edtDateFormat.setText(DEFAULT_DATE_FORMAT)
         self.doExampleDate()
      self.connect(self.btnResetFormat, SIGNAL(CLICKED), doReset)



      # Add the usual buttons
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.btnAccept = QPushButton(self.tr("Export"))
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.accept)
      btnBox = makeHorizFrame([STRETCH, self.btnCancel, self.btnAccept])


      dlgLayout = QGridLayout()

      i = 0
      dlgLayout.addWidget(QRichLabel(self.tr('Export Format:')), i, 0)
      dlgLayout.addWidget(self.cmbFileFormat, i, 1)

      i += 1
      dlgLayout.addWidget(HLINE(), i, 0, 1, 2)

      i += 1
      dlgLayout.addWidget(QRichLabel(self.tr('Wallet(s) to export:')), i, 0)
      dlgLayout.addWidget(self.cmbWltSelect, i, 1)

      i += 1
      dlgLayout.addWidget(HLINE(), i, 0, 1, 2)

      i += 1
      dlgLayout.addWidget(QRichLabel(self.tr('Sort Table:')), i, 0)
      dlgLayout.addWidget(self.cmbSortSelect, i, 1)
      i += 1
      dlgLayout.addWidget(HLINE(), i, 0, 1, 2)

      i += 1
      dlgLayout.addWidget(QRichLabel(self.tr('Date Format:')), i, 0)
      fmtfrm = makeHorizFrame([self.lblDateExample, STRETCH, self.ttipFormatDescr])
      dlgLayout.addWidget(fmtfrm, i, 1)

      i += 1
      dlgLayout.addWidget(self.btnResetFormat, i, 0)
      dlgLayout.addWidget(self.edtDateFormat, i, 1)

      i += 1
      dlgLayout.addWidget(HLINE(), i, 0, 1, 2)

      i += 1
      dlgLayout.addWidget(HLINE(), i, 0, 1, 2)

      i += 1
      dlgLayout.addWidget(btnBox, i, 0, 1, 2)

      self.setLayout(dlgLayout)


   #############################################################################
   def doExampleDate(self, qstr=None):
      fmtstr = str(self.edtDateFormat.text())
      try:
         exampleDateStr = unixTimeToFormatStr(1030501970, fmtstr)
         self.lblDateExample.setText(self.tr('Example: %1').arg(exampleDateStr))
         self.isValidFormat = True
      except:
         self.lblDateExample.setText(self.tr('Example: [[invalid date format]]'))
         self.isValidFormat = False

   #############################################################################
   def accept(self, *args):
      if self.createFile_CSV():
         super(DlgExportTxHistory, self).accept(*args)


   #############################################################################
   def createFile_CSV(self):
      if not self.isValidFormat:
         QMessageBox.warning(self, self.tr('Invalid date format'), \
                  self.tr('Cannot create CSV without a valid format for transaction '
                  'dates and times'), QMessageBox.Ok)
         return False

      COL = LEDGERCOLS

      # This was pretty much copied from the createCombinedLedger method...
      # I rarely do this, but modularizing this piece is a non-trivial
      wltIDList = []
      typelist = [[wid, determineWalletType(self.main.walletMap[wid], self.main)[0]] \
                                                   for wid in self.main.walletIDList]
      currIdx = self.cmbWltSelect.currentIndex()
      if currIdx >= 8:
         idx = currIdx - 8
         if idx < len(self.main.walletIDList):
            #picked a single wallet
            wltIDList = [self.main.walletIDList[idx]]
         else:
            #picked a single lockbox
            idx -= len(self.main.walletIDList) +1
            wltIDList = [self.reversedLBdict[idx]]
      else:
         listOffline = [t[0] for t in filter(lambda x: x[1] == WLTTYPES.Offline, typelist)]
         listWatching = [t[0] for t in filter(lambda x: x[1] == WLTTYPES.WatchOnly, typelist)]
         listCrypt = [t[0] for t in filter(lambda x: x[1] == WLTTYPES.Crypt, typelist)]
         listPlain = [t[0] for t in filter(lambda x: x[1] == WLTTYPES.Plain, typelist)]
         lockboxIDList = [t for t in self.main.lockboxIDMap]

         if currIdx == 0:
            wltIDList = listOffline + listCrypt + listPlain
         elif currIdx == 1:
            wltIDList = listOffline
         elif currIdx == 2:
            wltIDList = listWatching
         elif currIdx == 4:
            wltIDList = self.main.walletIDList
         elif currIdx == 5:
            wltIDList = lockboxIDList
         elif currIdx == 6:
            wltIDList = self.main.walletIDList + lockboxIDList
         else:
            pass

      order = "ascending"
      sortTxt = str(self.cmbSortSelect.currentText())
      if 'newest' in sortTxt:
         order = "descending"

      totalFunds, spendFunds, unconfFunds = 0, 0, 0
      wltBalances = {}
      for wltID in wltIDList:
         if wltID in self.main.walletMap:
            wlt = self.main.walletMap[wltID]

            totalFunds += wlt.getBalance('Total')
            spendFunds += wlt.getBalance('Spendable')
            unconfFunds += wlt.getBalance('Unconfirmed')
            if order == "ascending":
               wltBalances[wltID] = 0   # will be accumulated
            else:
               wltBalances[wltID] = wlt.getBalance('Total')

         else:
            #lockbox
            cppwlt = self.main.cppLockboxWltMap[wltID]
            totalFunds += cppwlt.getFullBalance()
            spendFunds += cppwlt.getSpendableBalance(TheBDM.getTopBlockHeight(), IGNOREZC)
            unconfFunds += cppwlt.getUnconfirmedBalance(TheBDM.getTopBlockHeight(), IGNOREZC)
            if order == "ascending":
               wltBalances[wltID] = 0   # will be accumulated
            else:
               wltBalances[wltID] = cppwlt.getFullBalance()

      if order == "ascending":
         allBalances = 0
      else:
         allBalances = totalFunds


      #prepare csv file
      wltSelectStr = str(self.cmbWltSelect.currentText()).replace(' ', '_')
      timestampStr = unixTimeToFormatStr(RightNow(), '%Y%m%d_%H%M')
      filenamePrefix = 'ArmoryTxHistory_%s_%s' % (wltSelectStr, timestampStr)
      fmtstr = str(self.cmbFileFormat.currentText())
      if 'csv' in fmtstr:
         defaultName = filenamePrefix + '.csv'
         fullpath = self.main.getFileSave('Save CSV File', \
                                              ['Comma-Separated Values (*.csv)'], \
                                              defaultName)

         if len(fullpath) == 0:
            return

         f = open(fullpath, 'w')

         f.write(self.tr('Export Date: %1\n').arg(unixTimeToFormatStr(RightNow())))
         f.write(self.tr('Total Funds: %1\n').arg(coin2str(totalFunds, maxZeros=0).strip()))
         f.write(self.tr('Spendable Funds: %1\n').arg(coin2str(spendFunds, maxZeros=0).strip()))
         f.write(self.tr('Unconfirmed Funds: %1\n').arg(coin2str(unconfFunds, maxZeros=0).strip()))
         f.write('\n')

         f.write(self.tr('Included Wallets:\n'))
         for wltID in wltIDList:
            if wltID in self.main.walletMap:
               wlt = self.main.walletMap[wltID]
               f.write('%s,%s\n' % (wltID, wlt.labelName.replace(',', ';')))
            else:
               wlt = self.main.allLockboxes[self.main.lockboxIDMap[wltID]]
               f.write(self.tr('%1 (lockbox),%2\n').arg(wltID, wlt.shortName.replace(',', ';')))
         f.write('\n')


         headerRow = [self.tr('Date'), self.tr('Transaction ID'), self.tr('Number of Confirmations'), self.tr('Wallet ID'),
                      self.tr('Wallet Name'), self.tr('Credit'), self.tr('Debit'), self.tr('Fee (paid by this wallet)'),
                      self.tr('Wallet Balance'), self.tr('Total Balance'), self.tr('Label')]

         f.write(','.join(unicode(header) for header in headerRow) + '\n')

         #get history
         historyLedger = TheBDM.bdv().getHistoryForWalletSelection(wltIDList, order)

         # Each value in COL.Amount will be exactly how much the wallet balance
         # increased or decreased as a result of this transaction.
         ledgerTable = self.main.convertLedgerToTable(historyLedger,
                                                      showSentToSelfAmt=True)

         # Sort the data chronologically first, compute the running balance for
         # each row, then sort it the way that was requested by the user.
         for row in ledgerTable:
            if row[COL.toSelf] == False:
               rawAmt = str2coin(row[COL.Amount])
            else:
               #if SentToSelf, balance and total rolling balance should only take fee in account
               rawAmt, fee_byte = getFeeForTx(hex_to_binary(row[COL.TxHash]))
               rawAmt = -1 * rawAmt 

            if order == "ascending":
               wltBalances[row[COL.WltID]] += rawAmt
               allBalances += rawAmt

            row.append(wltBalances[row[COL.WltID]])
            row.append(allBalances)

            if order == "descending":
               wltBalances[row[COL.WltID]] -= rawAmt
               allBalances -= rawAmt


         for row in ledgerTable:
            vals = []

            fmtstr = str(self.edtDateFormat.text())
            unixTime = row[COL.UnixTime]
            vals.append(unixTimeToFormatStr(unixTime, fmtstr))
            vals.append(hex_switchEndian(row[COL.TxHash]))
            vals.append(row[COL.NumConf])
            vals.append(row[COL.WltID])
            if row[COL.WltID] in self.main.walletMap:
               vals.append(self.main.walletMap[row[COL.WltID]].labelName.replace(',', ';'))
            else:
               vals.append(self.main.allLockboxes[self.main.lockboxIDMap[row[COL.WltID]]].shortName.replace(',', ';'))

            wltEffect = row[COL.Amount]
            txFee, fee_byte = getFeeForTx(hex_to_binary(row[COL.TxHash]))
            if float(wltEffect) >= 0:
               if row[COL.toSelf] == False:
                  vals.append(wltEffect.strip())
                  vals.append('')
                  vals.append('')
               else:
                  vals.append(wltEffect.strip() + ' (STS)')
                  vals.append('')
                  vals.append(coin2str(txFee).strip())
            else:
               vals.append('')
               vals.append(wltEffect.strip()[1:]) # remove negative sign
               vals.append(coin2str(txFee).strip())

            vals.append(coin2str(row[-2]))
            vals.append(coin2str(row[-1]))
            vals.append(row[COL.Comment])

            f.write('%s,%s,%d,%s,%s,%s,%s,%s,%s,%s,"%s"\n' % tuple(vals))

      f.close()
      return True


################################################################################
class DlgRequestPayment(ArmoryDialog):
   def __init__(self, parent, main, recvAddr, amt=None, msg=''):
      super(DlgRequestPayment, self).__init__(parent, main)


      if isLikelyDataType(recvAddr, DATATYPE.Binary) and len(recvAddr) == 20:
         self.recvAddr = hash160_to_addrStr(recvAddr)
      elif isLikelyDataType(recvAddr, DATATYPE.Base58):
         self.recvAddr = recvAddr
      else:
         raise BadAddressError('Unrecognized address input')


      # Amount
      self.edtAmount = QLineEdit()
      self.edtAmount.setFont(GETFONT('Fixed'))
      self.edtAmount.setMaximumWidth(relaxedSizeNChar(GETFONT('Fixed'), 13)[0])
      if amt:
         self.edtAmount.setText(coin2str(amt, maxZeros=0))


      # Message:
      self.edtMessage = QLineEdit()
      self.edtMessage.setMaxLength(128)
      if msg:
         self.edtMessage.setText(msg[:128])

      self.edtMessage.setCursorPosition(0)



      # Address:
      self.edtAddress = QLineEdit()
      self.edtAddress.setText(self.recvAddr)

      # Link Text:
      self.edtLinkText = QLineEdit()
      defaultHex = binary_to_hex('Click here to pay for your order!')
      savedHex = self.main.getSettingOrSetDefault('DefaultLinkText', defaultHex)
      if savedHex.startswith('FFFFFFFF'):
         # An unfortunate hack until we change our settings storage mechanism
         # See comment in saveLinkText function for details
         savedHex = savedHex[8:]

      linkText = hex_to_binary(savedHex)
      self.edtLinkText.setText(linkText)
      self.edtLinkText.setCursorPosition(0)
      self.edtLinkText.setMaxLength(80)

      qpal = QPalette()
      qpal.setColor(QPalette.Text, Colors.TextBlue)
      self.edtLinkText.setPalette(qpal)
      edtFont = self.edtLinkText.font()
      edtFont.setUnderline(True)
      self.edtLinkText.setFont(edtFont)



      self.connect(self.edtMessage, SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtAddress, SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtAmount, SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtLinkText, SIGNAL('textChanged(QString)'), self.setLabels)

      self.connect(self.edtMessage, SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtAddress, SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtAmount, SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtLinkText, SIGNAL('editingFinished()'), self.updateQRCode)


      # This is the "output"
      self.lblLink = QRichLabel('')
      self.lblLink.setOpenExternalLinks(True)
      self.lblLink.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
      self.lblLink.setMinimumHeight(3 * tightSizeNChar(self, 1)[1])
      self.lblLink.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
      self.lblLink.setContentsMargins(10, 5, 10, 5)
      self.lblLink.setStyleSheet('QLabel { background-color : %s }' % htmlColor('SlightBkgdDark'))
      frmOut = makeHorizFrame([self.lblLink], QFrame.Box | QFrame.Raised)
      frmOut.setLineWidth(1)
      frmOut.setMidLineWidth(5)


      self.lblWarn = QRichLabel('')
      self.lblWarn.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      self.btnOtherOpt = QPushButton(self.tr('Other Options >>>'))
      self.btnCopyRich = QPushButton(self.tr('Copy to Clipboard'))
      self.btnCopyHtml = QPushButton(self.tr('Copy Raw HTML'))
      self.btnCopyRaw = QPushButton(self.tr('Copy Raw URL'))
      self.btnCopyAll = QPushButton(self.tr('Copy All Text'))

      # I never actally got this button working right...
      self.btnCopyRich.setVisible(True)
      self.btnOtherOpt.setCheckable(True)
      self.btnCopyAll.setVisible(False)
      self.btnCopyHtml.setVisible(False)
      self.btnCopyRaw.setVisible(False)
      frmCopyBtnStrip = makeHorizFrame([ \
                                        self.btnCopyRich, \
                                        self.btnOtherOpt, \
                                        self.btnCopyHtml, \
                                        self.btnCopyRaw, \
                                        STRETCH, \
                                        self.lblWarn])
                                        # self.btnCopyAll, \

      self.connect(self.btnCopyRich, SIGNAL(CLICKED), self.clickCopyRich)
      self.connect(self.btnOtherOpt, SIGNAL('toggled(bool)'), self.clickOtherOpt)
      self.connect(self.btnCopyRaw, SIGNAL(CLICKED), self.clickCopyRaw)
      self.connect(self.btnCopyHtml, SIGNAL(CLICKED), self.clickCopyHtml)
      self.connect(self.btnCopyAll, SIGNAL(CLICKED), self.clickCopyAll)

      lblDescr = QRichLabel(\
         self.tr('Create a clickable link that you can copy into email or webpage to '
         'request a payment.   If the user is running a Bitcoin program '
         'that supports "bitcoin:" links, that program will open with '
         'all this information pre-filled after they click the link.'))

      lblDescr.setContentsMargins(5, 5, 5, 5)
      frmDescr = makeHorizFrame([lblDescr], STYLE_SUNKEN)


      ttipPreview = self.main.createToolTipWidget(\
         self.tr('The following Bitcoin desktop applications <i>try</i> to '
         'register themselves with your computer to handle "bitcoin:" '
         'links: Armory, Multibit, Electrum'))
      ttipLinkText = self.main.createToolTipWidget(\
         self.tr('This is the text to be shown as the clickable link.  It should '
         'usually begin with "Click here..." to reaffirm to the user it is '
         'is clickable.'))
      ttipAmount = self.main.createToolTipWidget(\
         self.tr('All amounts are specifed in BTC'))
      ttipAddress = self.main.createToolTipWidget(\
         self.tr('The person clicking the link will be sending bitcoins to this address'))
      ttipMessage = self.main.createToolTipWidget(\
         self.tr('This will be pre-filled as the label/comment field '
         'after the user clicks the link. They '
         'can modify it if desired, but you can '
         'provide useful info such as contact details, order number, '
         'etc, as convenience to them.'))


      btnClose = QPushButton(self.tr('Close'))
      self.connect(btnClose, SIGNAL(CLICKED), self.accept)


      frmEntry = QFrame()
      frmEntry.setFrameStyle(STYLE_SUNKEN)
      layoutEntry = QGridLayout()
      i = 0
      layoutEntry.addWidget(QRichLabel(self.tr('<b>Link Text:</b>')), i, 0)
      layoutEntry.addWidget(self.edtLinkText, i, 1)
      layoutEntry.addWidget(ttipLinkText, i, 2)

      i += 1
      layoutEntry.addWidget(QRichLabel(self.tr('<b>Address (yours):</b>')), i, 0)
      layoutEntry.addWidget(self.edtAddress, i, 1)
      layoutEntry.addWidget(ttipAddress, i, 2)

      i += 1
      layoutEntry.addWidget(QRichLabel(self.tr('<b>Request (BTC):</b>')), i, 0)
      layoutEntry.addWidget(self.edtAmount, i, 1)

      i += 1
      layoutEntry.addWidget(QRichLabel(self.tr('<b>Label:</b>')), i, 0)
      layoutEntry.addWidget(self.edtMessage, i, 1)
      layoutEntry.addWidget(ttipMessage, i, 2)
      frmEntry.setLayout(layoutEntry)


      lblOut = QRichLabel(self.tr('Copy and paste the following text into email or other document:'))
      frmOutput = makeVertFrame([lblOut, frmOut, frmCopyBtnStrip], STYLE_SUNKEN)
      frmOutput.layout().setStretch(0, 1)
      frmOutput.layout().setStretch(1, 1)
      frmOutput.layout().setStretch(2, 0)
      frmClose = makeHorizFrame([STRETCH, btnClose])

      self.qrStackedDisplay = QStackedWidget()
      self.qrStackedDisplay.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
      self.qrWaitingLabel = QRichLabel(self.tr('Creating QR Code Please Wait'), doWrap=False, hAlign=Qt.AlignHCenter)
      self.qrStackedDisplay.addWidget(self.qrWaitingLabel)
      self.qrURI = QRCodeWidget('', parent=self)
      self.qrStackedDisplay.addWidget(self.qrURI)
      lblQRDescr = QRichLabel(self.tr('This QR code contains address <b>and</b> the '
                              'other payment information shown to the left.'), doWrap=True)

      lblQRDescr.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
      frmQR = makeVertFrame([self.qrStackedDisplay, STRETCH, lblQRDescr, STRETCH], STYLE_SUNKEN)
      frmQR.layout().setStretch(0, 0)
      frmQR.layout().setStretch(1, 0)
      frmQR.layout().setStretch(2, 1)

      frmQR.setMinimumWidth(MAX_QR_SIZE)
      self.qrURI.setMinimumHeight(MAX_QR_SIZE)

      dlgLayout = QGridLayout()

      dlgLayout.addWidget(frmDescr, 0, 0, 1, 2)
      dlgLayout.addWidget(frmEntry, 1, 0, 1, 1)
      dlgLayout.addWidget(frmOutput, 2, 0, 1, 1)
      dlgLayout.addWidget(HLINE(), 3, 0, 1, 2)
      dlgLayout.addWidget(frmClose, 4, 0, 1, 2)

      dlgLayout.addWidget(frmQR, 1, 1, 2, 1)

      dlgLayout.setRowStretch(0, 0)
      dlgLayout.setRowStretch(1, 0)
      dlgLayout.setRowStretch(2, 1)
      dlgLayout.setRowStretch(3, 0)
      dlgLayout.setRowStretch(4, 0)


      self.setLabels()
      self.prevURI = ''
      self.closed = False  # kind of a hack to end the update loop
      self.setLayout(dlgLayout)
      self.setWindowTitle(self.tr('Create Payment Request Link'))

      self.callLater(1, self.periodicUpdate)

      hexgeom = str(self.main.settings.get('PayReqestGeometry'))
      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      self.setMinimumSize(750, 500)


   def saveLinkText(self):
      linktext = str(self.edtLinkText.text()).strip()
      if len(linktext) > 0:
         # TODO:  We desperately need a new settings file format -- the one
         #        we use was more of an experiment in how quickly I could
         #        create a simple settings file, but it has quirky behavior
         #        that makes cryptic hacks like below necessary.  Simply put,
         #        if the hex of the text is all digits (no hex A-F), then
         #        the settings file will read the value as a long int instead
         #        of a string.  We add 8 F's to make sure it's interpretted
         #        as a hex string, but someone looking at the file wouldn't
         #        mistake it for meaningful data.  We remove it upon reading
         #        the value from the settings file.
         hexText = 'FFFFFFFF'+binary_to_hex(linktext)
         self.main.writeSetting('DefaultLinkText', hexText)


   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('PayReqestGeometry', str(self.saveGeometry().toHex()))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      self.saveLinkText()
      super(DlgRequestPayment, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      self.saveLinkText()
      super(DlgRequestPayment, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgRequestPayment, self).reject(*args)


   #############################################################################
   def setLabels(self):

      lastTry = ''
      try:
         # The
         lastTry = self.tr('Amount')
         amtStr = str(self.edtAmount.text()).strip()
         if len(amtStr) == 0:
            amt = None
         else:
            amt = str2coin(amtStr)

            if amt > MAX_SATOSHIS:
               amt = None

         lastTry = self.tr('Message')
         msgStr = str(self.edtMessage.text()).strip()
         if len(msgStr) == 0:
            msgStr = None

         lastTry = self.tr('Address')
         addr = str(self.edtAddress.text()).strip()
         if not checkAddrStrValid(addr):
            raise

         errorIn = self.tr('Inputs')
         # must have address, maybe have amount and/or message
         self.rawURI = createBitcoinURI(addr, amt, msgStr)
      except:
         self.lblWarn.setText(self.tr('<font color="red">Invalid %1</font>').arg(lastTry))
         self.btnCopyRaw.setEnabled(False)
         self.btnCopyHtml.setEnabled(False)
         self.btnCopyAll.setEnabled(False)
         # self.lblLink.setText('<br>'.join(str(self.lblLink.text()).split('<br>')[1:]))
         self.lblLink.setEnabled(False)
         self.lblLink.setTextInteractionFlags(Qt.NoTextInteraction)
         return

      self.lblLink.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                           Qt.TextSelectableByKeyboard)

      self.rawHtml = '<a href="%s">%s</a>' % (self.rawURI, str(self.edtLinkText.text()))
      self.lblWarn.setText('')
      self.dispText = self.rawHtml[:]
      self.dispText += '<br>'
      self.dispText += self.tr('If clicking on the line above does not work, use this payment info:')
      self.dispText += '<br>'
      self.dispText += self.tr('<b>Pay to</b>:\t%1<br>').arg(addr)
      if amt:
         self.dispText += self.tr('<b>Amount</b>:\t%1 BTC<br>').arg(coin2str(amt, maxZeros=0).strip())
      if msgStr:
         self.dispText += self.tr('<b>Message</b>:\t%1<br>').arg(msgStr)
      self.lblLink.setText(self.dispText)

      self.lblLink.setEnabled(True)
      self.btnCopyRaw.setEnabled(True)
      self.btnCopyHtml.setEnabled(True)
      self.btnCopyAll.setEnabled(True)

      # Plain text to copy to clipboard as "text/plain"
      self.plainText = str(self.edtLinkText.text()) + '\n'
      self.plainText += self.tr('If clicking on the line above does not work, use this payment info:\n')
      self.plainText += self.tr('Pay to:  %1').arg(addr)
      if amt:
         self.plainText += self.tr('\nAmount:  %1 BTC').arg(coin2str(amt, maxZeros=0).strip())
      if msgStr:
         self.plainText += self.tr('\nMessage: %1').arg(msgStr)
      self.plainText += '\n'

      # The rich-text to copy to the clipboard, as "text/html"
      self.clipText = self.tr('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
            '"http://www.w3.org/TR/REC-html40/strict.dtd"> '
            '<html><head><meta name="qrichtext" content="1" />'
            '<meta http-equiv="Content-Type" content="text/html; '
            'charset=utf-8" /><style type="text/css"> p, li '
            '{ white-space: pre-wrap; } </style></head><body>'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; '
            'margin-right:0px; -qt-block-indent:0; text-indent:0px;">'
            '<!--StartFragment--><a href="%1">'
            '<span style=" text-decoration: underline; color:#0000ff;">'
            '%2</span></a><br />'
            'If clicking on the line above does not work, use this payment info:'
            '<br /><span style=" font-weight:600;">Pay to</span>: %3').arg(self.rawURI, str(self.edtLinkText.text()), addr)
      if amt:
         self.clipText += self.tr('<br /><span style=" font-weight:600;">Amount'
                           '</span>: %1').arg(coin2str(amt, maxZeros=0))
      if msgStr:
         self.clipText += self.tr('<br /><span style=" font-weight:600;">Message'
                           '</span>: %1').arg(msgStr)
      self.clipText += '<!--EndFragment--></p></body></html>'

   def periodicUpdate(self, nsec=1):
      if not self.closed:
         self.updateQRCode()
         self.callLater(nsec, self.periodicUpdate)

   def updateQRCode(self, e=None):
      if not self.prevURI == self.rawURI:
         self.qrStackedDisplay.setCurrentWidget(self.qrWaitingLabel)
         self.repaint()
         self.qrURI.setAsciiData(self.rawURI)
         self.qrURI.setPreferredSize(MAX_QR_SIZE - 10, 'max')
         self.qrStackedDisplay.setCurrentWidget(self.qrURI)
         self.repaint()
      self.prevURI = self.rawURI

   def clickCopyRich(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      qmd = QMimeData()
      if OS_WINDOWS:
         qmd.setText(self.plainText)
         qmd.setHtml(self.clipText)
      else:
         prefix = '<meta http-equiv="content-type" content="text/html; charset=utf-8">'
         qmd.setText(self.plainText)
         qmd.setHtml(prefix + self.dispText)
      clipb.setMimeData(qmd)
      self.lblWarn.setText(self.tr('<i>Copied!</i>'))



   def clickOtherOpt(self, boolState):
      self.btnCopyHtml.setVisible(boolState)
      self.btnCopyRaw.setVisible(boolState)

      if boolState:
         self.btnOtherOpt.setText(self.tr('Hide Buttons <<<'))
      else:
         self.btnOtherOpt.setText(self.tr('Other Options >>>'))

   def clickCopyRaw(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.rawURI)
      self.lblWarn.setText(self.tr('<i>Copied!</i>'))

   def clickCopyHtml(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.rawHtml)
      self.lblWarn.setText(self.tr('<i>Copied!</i>'))

   def clickCopyAll(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      qmd = QMimeData()
      qmd.setHtml(self.dispText)
      clipb.setMimeData(qmd)
      self.lblWarn.setText(self.tr('<i>Copied!</i>'))

################################################################################
class DlgUriCopyAndPaste(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgUriCopyAndPaste, self).__init__(parent, main)

      self.uriDict = {}
      lblDescr = QRichLabel(self.tr('Copy and paste a raw bitcoin URL string here.  '
                            'A valid string starts with "bitcoin:" followed '
                            'by a bitcoin address.'
                            '<br><br>'
                            'You should use this feature if there is a "bitcoin:" '
                            'link in a webpage or email that does not load Armory '
                            'when you click on it.  Instead, right-click on the '
                            'link and select "Copy Link Location" then paste it '
                            'into the box below. '))

      lblShowExample = QLabel()
      lblShowExample.setPixmap(QPixmap(':/armory_rightclickcopy.png'))

      self.txtUriString = QLineEdit()
      self.txtUriString.setFont(GETFONT('Fixed', 8))

      self.btnOkay = QPushButton(self.tr('Done'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnOkay, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      self.connect(self.btnOkay, SIGNAL(CLICKED), self.clickedOkay)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)

      frmImg = makeHorizFrame([STRETCH, lblShowExample, STRETCH])


      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(HLINE())
      layout.addWidget(frmImg)
      layout.addWidget(HLINE())
      layout.addWidget(self.txtUriString)
      layout.addWidget(buttonBox)
      self.setLayout(layout)


   def clickedOkay(self):
      uriStr = str(self.txtUriString.text())
      self.uriDict = self.main.parseUriLink(uriStr, 'enter')
      if len(self.uriDict.keys()) > 0:
         self.accept()









################################################################################
class DlgQRCodeDisplay(ArmoryDialog):
   def __init__(self, parent, main, dataToQR, descrUp='', descrDown=''):
      super(DlgQRCodeDisplay, self).__init__(parent, main)

      btnDone = QPushButton('Close')
      self.connect(btnDone, SIGNAL(CLICKED), self.accept)
      frmBtn = makeHorizFrame([STRETCH, btnDone, STRETCH])

      qrDisp = QRCodeWidget(dataToQR, parent=self)
      frmQR = makeHorizFrame([STRETCH, qrDisp, STRETCH])

      lblUp = QRichLabel(descrUp)
      lblUp.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
      lblDn = QRichLabel(descrDown)
      lblDn.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)



      layout = QVBoxLayout()
      layout.addWidget(lblUp)
      layout.addWidget(frmQR)
      layout.addWidget(lblDn)
      layout.addWidget(HLINE())
      layout.addWidget(frmBtn)

      self.setLayout(layout)

      w1, h1 = relaxedSizeStr(lblUp, descrUp)
      w2, h2 = relaxedSizeStr(lblDn, descrDown)
      self.setMinimumWidth(1.2 * max(w1, w2))









################################################################################
# STUB STUB STUB STUB STUB
class ArmoryPref(object):
   """
   Create a class that will handle arbitrary preferences for Armory.  This
   means that I can just create maps/lists of preferences, and auto-include
   them in the preferences dialog, and know how to set/get them.  This will
   be subclassed for each unique/custom preference type that is needed.
   """
   def __init__(self, prefName, dispStr, setType, defaultVal, validRange, descr, ttip, usermodes=None):
      self.preference = prefName
      self.displayStr = dispStr
      self.preferType = setType
      self.defaultVal = defaultVal
      self.validRange = validRange
      self.description = descr
      self.ttip = ttip

      # Some options may only be displayed for certain usermodes
      self.users = usermodes
      if usermodes == None:
         self.users = set([USERMODE.Standard, USERMODE.Advanced, USERMODE.Expert])

      if self.preferType == 'str':
         self.entryObj = QLineEdit()
      elif self.preferType == 'num':
         self.entryObj = QLineEdit()
      elif self.preferType == 'file':
         self.entryObj = QLineEdit()
      elif self.preferType == 'bool':
         self.entryObj = QCheckBox()
      elif self.preferType == 'combo':
         self.entryObj = QComboBox()


   def setEntryVal(self):
      pass

   def readEntryVal(self):
      pass


   def setWidthChars(self, nChar):
      self.entryObj.setMinimumWidth(relaxedSizeNChar(self.entryObj, nChar)[0])

   def render(self):
      """
      Return a map of qt objects to insert into the frame
      """
      toDraw = []
      row = 0
      if len(self.description) > 0:
         toDraw.append([QRichLabel(self.description), row, 0, 1, 4])
         row += 1


################################################################################
class QRadioButtonBackupCtr(QRadioButton):
   def __init__(self, parent, txt, index):
      super(QRadioButtonBackupCtr, self).__init__(txt)
      self.parent = parent
      self.index = index


   def enterEvent(self, ev):
      pass
      # self.parent.setDispFrame(self.index)
      # self.setStyleSheet('QRadioButton { background-color : %s }' % \
                                          # htmlColor('SlightBkgdDark'))

   def leaveEvent(self, ev):
      pass
      # self.parent.setDispFrame(-1)
      # self.setStyleSheet('QRadioButton { background-color : %s }' % \
                                          # htmlColor('Background'))


################################################################################
class DlgBackupCenter(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, wlt):
      super(DlgBackupCenter, self).__init__(parent, main)

      self.wlt = wlt
      wltID = wlt.uniqueIDB58
      wltName = wlt.labelName

      self.walletBackupFrame = WalletBackupFrame(parent, main)
      self.walletBackupFrame.setWallet(wlt)
      self.btnDone = QPushButton(self.tr('Done'))
      self.connect(self.btnDone, SIGNAL(CLICKED), self.reject)
      frmBottomBtns = makeHorizFrame([STRETCH, self.btnDone])

      layoutDialog = QVBoxLayout()

      layoutDialog.addWidget(self.walletBackupFrame)

      layoutDialog.addWidget(frmBottomBtns)

      self.setLayout(layoutDialog)
      self.setWindowTitle(self.tr("Backup Center"))
      self.setMinimumSize(640, 350)

################################################################################
class DlgSimpleBackup(ArmoryDialog):
   def __init__(self, parent, main, wlt):
      super(DlgSimpleBackup, self).__init__(parent, main)

      self.wlt = wlt

      lblDescrTitle = QRichLabel(self.tr(
         '<b>Protect Your Bitcoins -- Make a Wallet Backup!</b>'))

      lblDescr = QRichLabel(self.tr(
         'A failed hard-drive or forgotten passphrase will lead to '
         '<u>permanent loss of bitcoins</u>!  Luckily, Armory wallets only '
         'need to be backed up <u>one time</u>, and protect you in both '
         'of these events.   If you\'ve ever forgotten a password or had '
         'a hardware failure, make a backup!'))

      # ## Paper
      lblPaper = QRichLabel(self.tr(
         'Use a printer or pen-and-paper to write down your wallet "seed."'))
      btnPaper = QPushButton(self.tr('Make Paper Backup'))

      # ## Digital
      lblDigital = QRichLabel(self.tr(
         'Create an unencrypted copy of your wallet file, including imported '
         'addresses.'))
      btnDigital = QPushButton(self.tr('Make Digital Backup'))

      # ## Other
      btnOther = QPushButton(self.tr('See Other Backup Options'))

      def backupDigital():
         if self.main.digitalBackupWarning():
            self.main.makeWalletCopy(self, self.wlt, 'Decrypt', 'decrypt')
            self.accept()

      def backupPaper():
         OpenPaperBackupWindow('Single', self, self.main, self.wlt)
         self.accept()

      def backupOther():
         self.accept()
         DlgBackupCenter(self, self.main, self.wlt).exec_()

      self.connect(btnPaper, SIGNAL(CLICKED), backupPaper)
      self.connect(btnDigital, SIGNAL(CLICKED), backupDigital)
      self.connect(btnOther, SIGNAL(CLICKED), backupOther)

      layout = QGridLayout()

      layout.addWidget(lblPaper, 0, 0)
      layout.addWidget(btnPaper, 0, 2)

      layout.addWidget(HLINE(), 1, 0, 1, 3)

      layout.addWidget(lblDigital, 2, 0)
      layout.addWidget(btnDigital, 2, 2)

      layout.addWidget(HLINE(), 3, 0, 1, 3)

      layout.addWidget(makeHorizFrame([STRETCH, btnOther, STRETCH]), 4, 0, 1, 3)

      # layout.addWidget( VLINE(),      0,1, 5,1)

      layout.setContentsMargins(10, 5, 10, 5)
      setLayoutStretchRows(layout, 1, 0, 1, 0, 0)
      setLayoutStretchCols(layout, 1, 0, 0)

      frmGrid = QFrame()
      frmGrid.setFrameStyle(STYLE_PLAIN)
      frmGrid.setLayout(layout)

      btnClose = QPushButton(self.tr('Done'))
      self.connect(btnClose, SIGNAL(CLICKED), self.accept)
      frmClose = makeHorizFrame([STRETCH, btnClose])

      frmAll = makeVertFrame([lblDescrTitle, lblDescr, frmGrid, frmClose])
      layoutAll = QVBoxLayout()
      layoutAll.addWidget(frmAll)
      self.setLayout(layoutAll)
      self.sizeHint = lambda: QSize(400, 250)

      self.setWindowTitle(self.tr('Backup Options'))


################################################################################
# Class that acts as a center where the user can decide what to do with the
# watch-only wallet. The data can be displayed, printed, or saved to a file as a
# wallet or as the watch-only data (i.e., root key & chain code).
class DlgExpWOWltData(ArmoryDialog):
   """
   This dialog will be used to export a wallet's root public key and chain code.
   """
   def __init__(self, wlt, parent, main):
      super(DlgExpWOWltData, self).__init__(parent, main)

      # Save a copy of the wallet.
      self.wlt = wlt
      self.main = main

      # Get the chain code and uncompressed public key of info from the wallet,
      # along with other useful info.
      wltRootIDConcat, pkccET16Lines = wlt.getRootPKCCBackupData(True)
      wltIDB58 = wlt.uniqueIDB58

      # Create the data export buttons.
      expWltButton = QPushButton(self.tr('Export Watching-Only Wallet File'))
      clipboardBtn = QPushButton(self.tr('Copy to clipboard'))
      clipboardLbl = QRichLabel('', hAlign=Qt.AlignHCenter)
      expDataButton = QPushButton(self.tr('Save to Text File'))
      printWODataButton = QPushButton(self.tr('Print Root Data'))


      self.connect(expWltButton, SIGNAL(CLICKED), self.clickedExpWlt)
      self.connect(expDataButton, SIGNAL(CLICKED), self.clickedExpData)
      self.connect(printWODataButton, SIGNAL(CLICKED), \
                   self.clickedPrintWOData)


      # Let's put the window together.
      layout = QVBoxLayout()

      self.dispText = self.tr(
         'Watch-Only Root ID:<br><b>%1</b>'
         '<br><br>'
         'Watch-Only Root Data:').arg(wltRootIDConcat)
      for j in pkccET16Lines:
         self.dispText += '<br><b>%s</b>' % (j)

      titleStr = self.tr('Watch-Only Wallet Export')

      self.txtLongDescr = QTextBrowser()
      self.txtLongDescr.setFont(GETFONT('Fixed', 9))
      self.txtLongDescr.setHtml(self.dispText)
      w,h = tightSizeNChar(self.txtLongDescr, 20)
      self.txtLongDescr.setMaximumHeight(9.5*h)

      def clippy():
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(str(self.txtLongDescr.toPlainText()))
         clipboardLbl.setText(self.tr('<i>Copied!</i>'))

      self.connect(clipboardBtn, SIGNAL('clicked()'), clippy)


      lblDescr = QRichLabel(self.tr(
         '<center><b><u><font size=4 color="%1">Export Watch-Only '
         'Wallet: %2</font></u></b></center> '
         '<br>'
         'Use a watching-only wallet on an online computer to distribute '
         'payment addresses, verify transactions and monitor balances, but '
         'without the ability to move the funds.').arg(htmlColor('TextBlue'), wlt.uniqueIDB58))

      lblTopHalf = QRichLabel(self.tr(
         '<center><b><u>Entire Wallet File</u></b></center> '
         '<br>'
         '<i><b><font color="%1">(Recommended)</font></b></i> '
         'An exact copy of your wallet file but without any of the private '
         'signing keys. All existing comments and labels will be carried '
         'with the file. Use this option if it is easy to transfer files '
         'from this system to the target system.').arg(htmlColor('TextBlue')))

      lblBotHalf = QRichLabel(self.tr(
         '<center><b><u>Only Root Data</u></b></center> '
         '<br>'
         'Same as above, but only five lines of text that are easy to '
         'print, email inline, or copy by hand.  Only produces the '
         'wallet addresses.   No comments or labels are carried with '
         'it.'))

      btnDone = QPushButton(self.tr('Done'))
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)


      frmButtons = makeVertFrame([clipboardBtn,
                                  expDataButton,
                                  printWODataButton,
                                  clipboardLbl,
                                  'Stretch'])
      layoutBottom = QHBoxLayout()
      layoutBottom.addWidget(frmButtons, 0)
      layoutBottom.addItem(QSpacerItem(5,5))
      layoutBottom.addWidget(self.txtLongDescr, 1)
      layoutBottom.setSpacing(5)


      layout.addWidget(lblDescr)
      layout.addItem(QSpacerItem(10, 10))
      layout.addWidget(HLINE())
      layout.addWidget(lblTopHalf, 1)
      layout.addWidget(makeHorizFrame(['Stretch', expWltButton, 'Stretch']))
      layout.addItem(QSpacerItem(20, 20))
      layout.addWidget(HLINE())
      layout.addWidget(lblBotHalf, 1)
      layout.addLayout(layoutBottom)
      layout.addItem(QSpacerItem(20, 20))
      layout.addWidget(HLINE())
      layout.addWidget(makeHorizFrame(['Stretch', btnDone]))
      layout.setSpacing(3)

      self.setLayout(layout)
      self.setMinimumWidth(600)

      # TODO:  Dear god this is terrible, but for my life I cannot figure
      #        out how to move the vbar, because you can't do it until
      #        the dialog is drawn which doesn't happen til after __init__.
      self.callLater(0.05, self.resizeEvent)

      self.setWindowTitle(titleStr)


   def resizeEvent(self, ev=None):
      super(DlgExpWOWltData, self).resizeEvent(ev)
      vbar = self.txtLongDescr.verticalScrollBar()
      vbar.setValue(vbar.minimum())


   # The function that is executed when the user wants to back up the full
   # watch-only wallet to a file.
   def clickedExpWlt(self):
      currPath = self.wlt.walletPath
      if not self.wlt.watchingOnly:
         pieces = os.path.splitext(currPath)
         currPath = pieces[0] + '_WatchOnly' + pieces[1]

      saveLoc = self.main.getFileSave('Save Watching-Only Copy', \
                                      defaultFilename=currPath)
      if not saveLoc.endswith('.wallet'):
         saveLoc += '.wallet'

      if not self.wlt.watchingOnly:
         self.wlt.forkOnlineWallet(saveLoc, self.wlt.labelName, \
                                '(Watching-Only) ' + self.wlt.labelDescr)
      else:
         self.wlt.writeFreshWalletFile(saveLoc)



   # The function that is executed when the user wants to save the watch-only
   # data to a file.
   def clickedExpData(self):
      self.main.makeWalletCopy(self, self.wlt, 'PKCC', 'rootpubkey')


   # The function that is executed when the user wants to print the watch-only
   # data.
   def clickedPrintWOData(self):
      self.result = DlgWODataPrintBackup(self, self.main, self.wlt).exec_()


################################################################################
# Class that handles the printing of the watch-only wallet data. The formatting
# is mostly the same as a normal paper backup. Note that neither fragmented
# backups nor SecurePrint are used.
class DlgWODataPrintBackup(ArmoryDialog):
   """
   Open up a "Make Paper Backup" dialog, so the user can print out a hard
   copy of whatever data they need to recover their wallet should they lose
   it.
   """
   def __init__(self, parent, main, wlt):
      super(DlgWODataPrintBackup, self).__init__(parent, main)

      self.wlt = wlt

      # Create the scene and the view.
      self.scene = SimplePrintableGraphicsScene(self, self.main)
      self.view = QGraphicsView()
      self.view.setRenderHint(QPainter.TextAntialiasing)
      self.view.setScene(self.scene.getScene())

      # Label displayed above the sheet to be printed.
      lblDescr = QRichLabel(self.tr(
         '<b><u>Print Watch-Only Wallet Root</u></b><br><br> '
         'The lines below are sufficient to calculate public keys '
         'for every private key ever produced by the full wallet. '
         'Importing this data to an online computer is sufficient '
         'to receive and verify transactions, and monitor balances, '
         'but without the ability to spend the funds.'))
      lblDescr.setContentsMargins(5, 5, 5, 5)
      frmDescr = makeHorizFrame([lblDescr], STYLE_RAISED)

      # Buttons shown below the sheet to be printed.
      self.btnPrint = QPushButton('&Print...')
      self.btnPrint.setMinimumWidth(3 * tightSizeStr(self.btnPrint, 'Print...')[0])
      self.btnCancel = QPushButton('&Cancel')
      self.connect(self.btnPrint, SIGNAL(CLICKED), self.print_)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      frmButtons = makeHorizFrame([self.btnCancel, STRETCH, self.btnPrint])

      # Draw the sheet for the first time.
      self.redrawBackup()

      # Lay out the dialog.
      layout = QVBoxLayout()
      layout.addWidget(frmDescr)
      layout.addWidget(self.view)
      layout.addWidget(frmButtons)
      setLayoutStretch(layout, 0, 1, 0)
      self.setLayout(layout)
      self.setWindowIcon(QIcon(':/printer_icon.png'))
      self.setWindowTitle('Print Watch-Only Root')

      # Apparently I can't programmatically scroll until after it's painted
      def scrollTop():
         vbar = self.view.verticalScrollBar()
         vbar.setValue(vbar.minimum())
      self.callLater(0.01, scrollTop)


   # Class called to redraw the print "canvas" when the data changes.
   def redrawBackup(self):
      self.createPrintScene()
      self.view.update()


   # Class that handles the actual printing code.
   def print_(self):
      LOGINFO('Printing!')
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)

      if QPrintDialog(self.printer).exec_():
         painter = QPainter(self.printer)
         painter.setRenderHint(QPainter.TextAntialiasing)

         self.createPrintScene()
         self.scene.getScene().render(painter)
         painter.end()
         self.accept()


   # Class that lays out the actual print "canvas" to be printed.
   def createPrintScene(self):
      # Do initial setup.
      self.scene.gfxScene.clear()
      self.scene.resetCursor()

      # Draw the background paper?
      pr = self.scene.pageRect()
      self.scene.drawRect(pr.width(), pr.height(), edgeColor=None, \
                          fillColor=QColor(255, 255, 255))
      self.scene.resetCursor()

      INCH = self.scene.INCH
      MARGIN = self.scene.MARGIN_PIXELS
      wrap = 0.9 * self.scene.pageRect().width()

      # Start drawing the page.
      if USE_TESTNET or USE_REGTEST:
         self.scene.drawPixmapFile(':/armory_logo_green_h56.png')
      else:
         self.scene.drawPixmapFile(':/armory_logo_h36.png')
      self.scene.newLine()

      warnMsg = self.tr(
         '<b><font size=4><font color="#aa0000">WARNING:</font>  <u>This is not '
         'a wallet backup!</u></font></b> '
         '<br><br>Please make a regular digital or paper backup of your wallet '
         'to keep it protected!  This data simply lets you '
         'monitor the funds in this wallet but gives you no ability to move any '
         'funds.')
      self.scene.drawText(warnMsg, GETFONT('Var', 9), wrapWidth=wrap)

      self.scene.newLine(extra_dy=20)
      self.scene.drawHLine()
      self.scene.newLine(extra_dy=20)

      # Print the wallet info.
      colRect, rowHgt = self.scene.drawColumn(['<b>Watch-Only Root Data</b>',
                                               'Wallet ID:',
                                               'Wallet Name:'])
      self.scene.moveCursor(15, 0)
      colRect, rowHgt = self.scene.drawColumn(['',
                                               self.wlt.uniqueIDB58,
                                               self.wlt.labelName])

      self.scene.moveCursor(15, colRect.y() + colRect.height(), absolute=True)

      # Display warning about unprotected key data.
      self.scene.newLine(extra_dy=20)
      self.scene.drawHLine()
      self.scene.newLine(extra_dy=20)

      # Draw the description of the data.
      descrMsg = self.tr(
         'The following five lines are sufficient to reproduce all public '
         'keys matching the private keys produced by the full wallet.')
      self.scene.drawText(descrMsg, GETFONT('var', 8), wrapWidth=wrap)
      self.scene.newLine(extra_dy=10)

      # Prepare the data.
      self.wltRootIDConcat, self.pkccET16Lines = \
                                            self.wlt.getRootPKCCBackupData(True)
      Lines = []
      Prefix = []
      Prefix.append('Watch-Only Root ID:');  Lines.append(self.wltRootIDConcat)
      Prefix.append('Watch-Only Root:');     Lines.append(self.pkccET16Lines[0])
      Prefix.append('');                     Lines.append(self.pkccET16Lines[1])
      Prefix.append('');                     Lines.append(self.pkccET16Lines[2])
      Prefix.append('');                     Lines.append(self.pkccET16Lines[3])

      # Draw the prefix data.
      origX, origY = self.scene.getCursorXY()
      self.scene.moveCursor(10, 0)
      colRect, rowHgt = self.scene.drawColumn(['<b>' + l + '</b>' \
                                               for l in Prefix])

      # Draw the data.
      nudgeDown = 2  # because the differing font size makes it look unaligned
      self.scene.moveCursor(10, nudgeDown)
      self.scene.drawColumn(Lines,
                              font=GETFONT('Fixed', 8, bold=True), \
                              rowHeight=rowHgt,
                              useHtml=False)

      # Draw the rectangle around the data.
      self.scene.moveCursor(MARGIN, colRect.y() - 2, absolute=True)
      width = self.scene.pageRect().width() - 2 * MARGIN
      self.scene.drawRect(width, colRect.height() + 7, \
                          edgeColor=QColor(0, 0, 0), fillColor=None)

      # Draw the QR-related text below the data.
      self.scene.newLine(extra_dy=30)
      self.scene.drawText(self.tr(
         'The following QR code is for convenience only.  It contains the '
         'exact same data as the five lines above.  If you copy this data '
         'by hand, you can safely ignore this QR code.'), wrapWidth=4 * INCH)

      # Draw the QR code.
      self.scene.moveCursor(20, 0)
      x, y = self.scene.getCursorXY()
      edgeRgt = self.scene.pageRect().width() - MARGIN
      edgeBot = self.scene.pageRect().height() - MARGIN
      qrSize = max(1.5 * INCH, min(edgeRgt - x, edgeBot - y, 2.0 * INCH))
      self.scene.drawQR('\n'.join(Lines), qrSize)
      self.scene.newLine(extra_dy=25)

      # Clear the data and create a vertical scroll bar.
      Lines = None
      vbar = self.view.verticalScrollBar()
      vbar.setValue(vbar.minimum())
      self.view.update()


################################################################################
class DlgFragBackup(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, wlt):
      super(DlgFragBackup, self).__init__(parent, main)

      self.wlt = wlt
      self.randpass = None
      self.binCrypt32 = None

      lblDescrTitle = QRichLabel(self.tr(
         '<b><u>Create M-of-N Fragmented Backup</u> of "%1" (%2)</b>').arg(wlt.labelName, wlt.uniqueIDB58), doWrap=False)
      lblDescrTitle.setContentsMargins(5, 5, 5, 5)

      self.lblAboveFrags = QRichLabel('')
      self.lblAboveFrags.setContentsMargins(10, 0, 10, 0)

      frmDescr = makeVertFrame([lblDescrTitle, self.lblAboveFrags], \
                                                            STYLE_RAISED)

      self.fragDisplayLastN = 0
      self.fragDisplayLastM = 0

      self.maxM = 5 if not self.main.usermode == USERMODE.Expert else 8
      self.maxN = 6 if not self.main.usermode == USERMODE.Expert else 12
      self.currMinN = 2
      self.maxmaxN = 12

      self.comboM = QComboBox()
      self.comboN = QComboBox()

      for M in range(2, self.maxM + 1):
         self.comboM.addItem(str(M))

      for N in range(self.currMinN, self.maxN + 1):
         self.comboN.addItem(str(N))

      self.comboM.setCurrentIndex(1)
      self.comboN.setCurrentIndex(2)

      def updateM():
         self.updateComboN()
         self.createFragDisplay()

      updateN = self.createFragDisplay

      self.connect(self.comboM, SIGNAL('activated(int)'), updateM)
      self.connect(self.comboN, SIGNAL('activated(int)'), updateN)
      self.comboM.setMinimumWidth(30)
      self.comboN.setMinimumWidth(30)

      btnAccept = QPushButton(self.tr('Close'))
      self.connect(btnAccept, SIGNAL(CLICKED), self.accept)
      frmBottomBtn = makeHorizFrame([STRETCH, btnAccept])

      # We will hold all fragments here, in SBD objects.  Destroy all of them
      # before the dialog exits
      self.secureRoot = self.wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
      self.secureChain = self.wlt.addrMap['ROOT'].chaincode.copy()
      self.secureMtrx = []

      testChain = DeriveChaincodeFromRootKey(self.secureRoot)
      if testChain == self.secureChain:
         self.noNeedChaincode = True
         self.securePrint = self.secureRoot
      else:
         self.securePrint = self.secureRoot + self.secureChain

      self.chkSecurePrint = QCheckBox(self.trUtf8(u'Use SecurePrint\u200b\u2122 '
         'to prevent exposing keys to printer or other devices'))

      self.scrollArea = QScrollArea()
      self.createFragDisplay()
      self.scrollArea.setWidgetResizable(True)

      self.ttipSecurePrint = self.main.createToolTipWidget(self.trUtf8(
         u'SecurePrint\u200b\u2122 encrypts your backup with a code displayed on '
         'the screen, so that no other devices or processes has access to the '
         'unencrypted private keys (either network devices when printing, or '
         'other applications if you save a fragment to disk or USB device). '
         u'<u>You must keep the SecurePrint\u200b\u2122 code with the backup!</u>'))
      self.lblSecurePrint = QRichLabel(self.trUtf8(
         '<b><font color="%1"><u>IMPORTANT:</u>  You must keep the '
         u'SecurePrint\u200b\u2122 encryption code with your backup! '
         u'Your SecurePrint\u200b\u2122 code is </font> '
         '<font color="%2">%3</font><font color="%4">. '
         'All fragments for a given wallet use the '
         'same code.</font>').arg(htmlColor('TextWarn'), htmlColor('TextBlue'), self.randpass.toBinStr(), \
          htmlColor('TextWarn')))
      self.connect(self.chkSecurePrint, SIGNAL(CLICKED), self.clickChkSP)
      self.chkSecurePrint.setChecked(False)
      self.lblSecurePrint.setVisible(False)
      frmChkSP = makeHorizFrame([self.chkSecurePrint, self.ttipSecurePrint, STRETCH])

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(frmDescr)
      dlgLayout.addWidget(self.scrollArea)
      dlgLayout.addWidget(frmChkSP)
      dlgLayout.addWidget(self.lblSecurePrint)
      dlgLayout.addWidget(frmBottomBtn)
      setLayoutStretch(dlgLayout, 0, 1, 0, 0, 0)

      self.setLayout(dlgLayout)
      self.setMinimumWidth(650)
      self.setMinimumHeight(450)
      self.setWindowTitle('Create Backup Fragments')


   #############################################################################
   def clickChkSP(self):
      self.lblSecurePrint.setVisible(self.chkSecurePrint.isChecked())
      self.createFragDisplay()


   #############################################################################
   def updateComboN(self):
      M = int(str(self.comboM.currentText()))
      oldN = int(str(self.comboN.currentText()))
      self.currMinN = M
      self.comboN.clear()

      for i, N in enumerate(range(self.currMinN, self.maxN + 1)):
         self.comboN.addItem(str(N))

      if M > oldN:
         self.comboN.setCurrentIndex(0)
      else:
         for i, N in enumerate(range(self.currMinN, self.maxN + 1)):
            if N == oldN:
               self.comboN.setCurrentIndex(i)



   #############################################################################
   def createFragDisplay(self):
      M = int(str(self.comboM.currentText()))
      N = int(str(self.comboN.currentText()))

      #only recompute fragments if M or N changed
      if self.fragDisplayLastN != N or \
         self.fragDisplayLastM != M:
         self.recomputeFragData()

      self.fragDisplayLastN = N
      self.fragDisplayLastM = M

      lblAboveM = QRichLabel(self.tr('<u><b>Required Fragments</b></u> '), hAlign=Qt.AlignHCenter, doWrap=False)
      lblAboveN = QRichLabel(self.tr('<u><b>Total Fragments</b></u> '), hAlign=Qt.AlignHCenter)
      frmComboM = makeHorizFrame([STRETCH, QLabel('M:'), self.comboM, STRETCH])
      frmComboN = makeHorizFrame([STRETCH, QLabel('N:'), self.comboN, STRETCH])

      btnPrintAll = QPushButton(self.tr('Print All Fragments'))
      self.connect(btnPrintAll, SIGNAL(CLICKED), self.clickPrintAll)
      leftFrame = makeVertFrame([STRETCH, \
                                 lblAboveM, \
                                 frmComboM, \
                                 lblAboveN, \
                                 frmComboN, \
                                 STRETCH, \
                                 HLINE(), \
                                 btnPrintAll, \
                                 STRETCH], STYLE_STYLED)

      layout = QHBoxLayout()
      layout.addWidget(leftFrame)

      for f in range(N):
         layout.addWidget(self.createFragFrm(f))


      frmScroll = QFrame()
      frmScroll.setFrameStyle(STYLE_SUNKEN)
      frmScroll.setStyleSheet('QFrame { background-color : %s  }' % \
                                                htmlColor('SlightBkgdDark'))
      frmScroll.setLayout(layout)
      self.scrollArea.setWidget(frmScroll)

      BLUE = htmlColor('TextBlue')
      self.lblAboveFrags.setText(self.tr(
         'Any <font color="%1"><b>%2</b></font> of these '
         '<font color="%1"><b>%3</b></font>'
         'fragments are sufficient to restore your wallet, and each fragment '
         'has the ID, <font color="%1"><b>%4</b></font>.  All fragments with the '
         'same fragment ID are compatible with each other!').arg(BLUE).arg(M).arg(N).arg(self.fragPrefixStr))


   #############################################################################
   def createFragFrm(self, idx):

      doMask = self.chkSecurePrint.isChecked()
      M = int(str(self.comboM.currentText()))
      N = int(str(self.comboN.currentText()))

      lblFragID = QRichLabel(self.tr('<b>Fragment ID:<br>%1-%2</b>').arg(\
                                    str(self.fragPrefixStr), str(idx + 1)))
      # lblWltID = QRichLabel('(%s)' % self.wlt.uniqueIDB58)
      lblFragPix = QImageLabel(self.fragPixmapFn, size=(72, 72))
      if doMask:
         ys = self.secureMtrxCrypt[idx][1].toBinStr()[:42]
      else:
         ys = self.secureMtrx[idx][1].toBinStr()[:42]

      easyYs1 = makeSixteenBytesEasy(ys[:16   ])
      easyYs2 = makeSixteenBytesEasy(ys[ 16:32])

      binID = base58_to_binary(self.uniqueFragSetID)
      ID = ComputeFragIDLineHex(M, idx, binID, doMask, addSpaces=True)

      fragPreview = 'ID: %s...<br>' % ID[:12]
      fragPreview += 'F1: %s...<br>' % easyYs1[:12]
      fragPreview += 'F2: %s...    ' % easyYs2[:12]
      lblPreview = QRichLabel(fragPreview)
      lblPreview.setFont(GETFONT('Fixed', 9))

      lblFragIdx = QRichLabel('#%d' % (idx + 1), size=4, color='TextBlue', \
                                                   hAlign=Qt.AlignHCenter)

      frmTopLeft = makeVertFrame([lblFragID, lblFragIdx, STRETCH])
      frmTopRight = makeVertFrame([lblFragPix, STRETCH])

      frmPaper = makeVertFrame([lblPreview])
      frmPaper.setStyleSheet('QFrame { background-color : #ffffff  }')

      fnPrint = lambda: self.clickPrintFrag(idx)
      fnSave = lambda: self.clickSaveFrag(idx)

      btnPrintFrag = QPushButton(self.tr('View/Print'))
      btnSaveFrag = QPushButton(self.tr('Save to File'))
      self.connect(btnPrintFrag, SIGNAL(CLICKED), fnPrint)
      self.connect(btnSaveFrag, SIGNAL(CLICKED), fnSave)
      frmButtons = makeHorizFrame([btnPrintFrag, btnSaveFrag])


      layout = QGridLayout()
      layout.addWidget(frmTopLeft, 0, 0, 1, 1)
      layout.addWidget(frmTopRight, 0, 1, 1, 1)
      layout.addWidget(frmPaper, 1, 0, 1, 2)
      layout.addWidget(frmButtons, 2, 0, 1, 2)
      layout.setSizeConstraint(QLayout.SetFixedSize)

      outFrame = QFrame()
      outFrame.setFrameStyle(STYLE_STYLED)
      outFrame.setLayout(layout)
      return outFrame


   #############################################################################
   def clickPrintAll(self):
      self.clickPrintFrag(range(int(str(self.comboN.currentText()))))

   #############################################################################
   def clickPrintFrag(self, zindex):
      if not isinstance(zindex, (list, tuple)):
         zindex = [zindex]
      fragData = {}
      fragData['M'] = int(str(self.comboM.currentText()))
      fragData['N'] = int(str(self.comboN.currentText()))
      fragData['FragIDStr'] = self.fragPrefixStr
      fragData['FragPixmap'] = self.fragPixmapFn
      fragData['Range'] = zindex
      fragData['Secure'] = self.chkSecurePrint.isChecked()
      fragData['fragSetID'] = self.uniqueFragSetID
      dlg = DlgPrintBackup(self, self.main, self.wlt, 'Fragments', \
                              self.secureMtrx, self.secureMtrxCrypt, fragData, \
                              self.secureRoot, self.secureChain)
      dlg.exec_()

   #############################################################################
   def clickSaveFrag(self, zindex):
      saveMtrx = self.secureMtrx;
      doMask = False
      if self.chkSecurePrint.isChecked():
         response = QMessageBox.question(self, self.tr('Secure Backup?'), self.trUtf8(
            u'You have selected to use SecurePrint\u200b\u2122 for the printed '
            'backups, which can also be applied to fragments saved to file. '
            u'Doing so will require you store the SecurePrint\u200b\u2122 '
            'code with the backup, but it will prevent unencrypted key data from '
            'touching any disks.  <br><br> Do you want to encrypt the fragment '
            u'file with the same SecurePrint\u200b\u2122 code?'), \
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

         if response == QMessageBox.Yes:
            saveMtrx = self.secureMtrxCrypt;
            doMask = True
         elif response == QMessageBox.No:
            pass
         else:
            return


      wid = self.wlt.uniqueIDB58
      pref = self.fragPrefixStr
      fnum = zindex + 1
      M = self.M
      sec = 'secure.' if doMask else ''
      defaultFn = 'wallet_%s_%s_num%d_need%d.%sfrag' % (wid, pref, fnum, M, sec)
      #print 'FragFN:', defaultFn
      savepath = self.main.getFileSave('Save Fragment', \
                                       ['Wallet Fragments (*.frag)'], \
                                       defaultFn)

      if len(toUnicode(savepath)) == 0:
         return

      fout = open(savepath, 'w')
      fout.write('Wallet ID:     %s\n' % wid)
      fout.write('Create Date:   %s\n' % unixTimeToFormatStr(RightNow()))
      fout.write('Fragment ID:   %s-#%d\n' % (pref, fnum))
      fout.write('Frag Needed:   %d\n' % M)
      fout.write('\n\n')

      try:
         yBin = saveMtrx[zindex][1].toBinStr()
         binID = base58_to_binary(self.uniqueFragSetID)
         IDLine = ComputeFragIDLineHex(M, zindex, binID, doMask, addSpaces=True)
         if len(yBin) == 32:
            fout.write('ID: ' + IDLine + '\n')
            fout.write('F1: ' + makeSixteenBytesEasy(yBin[:16 ]) + '\n')
            fout.write('F2: ' + makeSixteenBytesEasy(yBin[ 16:]) + '\n')
         elif len(yBin) == 64:
            fout.write('ID: ' + IDLine + '\n')
            fout.write('F1: ' + makeSixteenBytesEasy(yBin[:16       ]) + '\n')
            fout.write('F2: ' + makeSixteenBytesEasy(yBin[ 16:32    ]) + '\n')
            fout.write('F3: ' + makeSixteenBytesEasy(yBin[    32:48 ]) + '\n')
            fout.write('F4: ' + makeSixteenBytesEasy(yBin[       48:]) + '\n')
         else:
            LOGERROR('yBin is not 32 or 64 bytes!  It is %s bytes', len(yBin))
      finally:
         yBin = None

      fout.close()

      qmsg = self.tr(
         'The fragment was successfully saved to the following location: '
         '<br><br> %1 <br><br>').arg(savepath)

      if doMask:
         qmsg += self.trUtf8(
            '<b><u><font color="%1">Important</font</u></b>: '
            'The fragment was encrypted with the '
            u'SecurePrint\u200b\u2122 encryption code.  You must keep this '
            'code with the backup in order to use it!  The code <u>is</u> '
            'case-sensitive! '
            '<br><br> <font color="%2" size=5><b>%3</b></font>'
            '<br><br>'
            'The above code <u><b>is</b></u> case-sensitive!').arg(htmlColor('TextWarn'), htmlColor('TextBlue'), self.randpass.toBinStr())

      QMessageBox.information(self, self.tr('Success'), qmsg, QMessageBox.Ok)



   #############################################################################
   def destroyFrags(self):
      if len(self.secureMtrx) == 0:
         return

      if isinstance(self.secureMtrx[0], (list, tuple)):
         for sbdList in self.secureMtrx:
            for sbd in sbdList:
               sbd.destroy()
         for sbdList in self.secureMtrxCrypt:
            for sbd in sbdList:
               sbd.destroy()
      else:
         for sbd in self.secureMtrx:
            sbd.destroy()
         for sbd in self.secureMtrxCrypt:
            sbd.destroy()

      self.secureMtrx = []
      self.secureMtrxCrypt = []


   #############################################################################
   def destroyEverything(self):
      self.secureRoot.destroy()
      self.secureChain.destroy()
      self.securePrint.destroy()
      self.destroyFrags()

   #############################################################################
   def recomputeFragData(self):
      """
      Only M is needed, since N doesn't change
      """

      M = int(str(self.comboM.currentText()))
      N = int(str(self.comboN.currentText()))
      # Make sure only local variables contain non-SBD data
      self.destroyFrags()
      self.uniqueFragSetID = \
         binary_to_base58(SecureBinaryData().GenerateRandom(6).toBinStr())
      insecureData = SplitSecret(self.securePrint, M, self.maxmaxN)
      for x, y in insecureData:
         self.secureMtrx.append([SecureBinaryData(x), SecureBinaryData(y)])
      insecureData, x, y = None, None, None

      #####
      # Now we compute the SecurePrint(TM) versions of the fragments
      SECPRINT = HardcodedKeyMaskParams()
      MASK = lambda x: SECPRINT['FUNC_MASK'](x, ekey=self.binCrypt32)
      if not self.randpass or not self.binCrypt32:
         self.randpass = SECPRINT['FUNC_PWD'](self.secureRoot + self.secureChain)
         self.binCrypt32 = SECPRINT['FUNC_KDF'](self.randpass)
      self.secureMtrxCrypt = []
      for sbdX, sbdY in self.secureMtrx:
         self.secureMtrxCrypt.append([sbdX.copy(), MASK(sbdY)])
      #####

      self.M, self.N = M, N
      self.fragPrefixStr = ComputeFragIDBase58(self.M, \
                              base58_to_binary(self.uniqueFragSetID))
      self.fragPixmapFn = ':/frag%df.png' % M


   #############################################################################
   def accept(self):
      self.destroyEverything()
      super(DlgFragBackup, self).accept()

   #############################################################################
   def reject(self):
      self.destroyEverything()
      super(DlgFragBackup, self).reject()




################################################################################
class DlgUniversalRestoreSelect(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main):
      super(DlgUniversalRestoreSelect, self).__init__(parent, main)


      lblDescrTitle = QRichLabel(self.tr('<b><u>Restore Wallet from Backup</u></b>'))
      lblDescr = QRichLabel(self.tr('You can restore any kind of backup ever created by Armory using '
         'one of the options below.  If you have a list of private keys '
         'you should open the target wallet and select "Import/Sweep '
         'Private Keys."'))

      self.rdoSingle = QRadioButton(self.tr('Single-Sheet Backup (printed)'))
      self.rdoFragged = QRadioButton(self.tr('Fragmented Backup (incl. mix of paper and files)'))
      self.rdoDigital = QRadioButton(self.tr('Import digital backup or watching-only wallet'))
      self.rdoWOData = QRadioButton(self.tr('Import watching-only wallet data'))
      self.chkTest = QCheckBox(self.tr('This is a test recovery to make sure my backup works'))
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.rdoSingle)
      btngrp.addButton(self.rdoFragged)
      btngrp.addButton(self.rdoDigital)
      btngrp.addButton(self.rdoWOData)
      btngrp.setExclusive(True)

      self.rdoSingle.setChecked(True)
      self.connect(self.rdoSingle, SIGNAL(CLICKED), self.clickedRadio)
      self.connect(self.rdoFragged, SIGNAL(CLICKED), self.clickedRadio)
      self.connect(self.rdoDigital, SIGNAL(CLICKED), self.clickedRadio)
      self.connect(self.rdoWOData, SIGNAL(CLICKED), self.clickedRadio)

      self.btnOkay = QPushButton(self.tr('Continue'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnOkay, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      self.connect(self.btnOkay, SIGNAL(CLICKED), self.clickedOkay)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)


      layout = QVBoxLayout()
      layout.addWidget(lblDescrTitle)
      layout.addWidget(lblDescr)
      layout.addWidget(HLINE())
      layout.addWidget(self.rdoSingle)
      layout.addWidget(self.rdoFragged)
      layout.addWidget(self.rdoDigital)
      layout.addWidget(self.rdoWOData)
      layout.addWidget(HLINE())
      layout.addWidget(self.chkTest)
      layout.addWidget(buttonBox)
      self.setLayout(layout)
      self.setMinimumWidth(450)

   def clickedRadio(self):
      if self.rdoDigital.isChecked():
         self.chkTest.setChecked(False)
         self.chkTest.setEnabled(False)
      else:
         self.chkTest.setEnabled(True)

   def clickedOkay(self):
      # ## Test backup option

      doTest = self.chkTest.isChecked()

      if self.rdoSingle.isChecked():
         self.accept()
         dlg = DlgRestoreSingle(self.parent, self.main, doTest)
         if dlg.exec_():
            self.main.addWalletToApplication(dlg.newWallet)
            LOGINFO('Wallet Restore Complete!')

      elif self.rdoFragged.isChecked():
         self.accept()
         dlg = DlgRestoreFragged(self.parent, self.main, doTest)
         if dlg.exec_():
            self.main.addWalletToApplication(dlg.newWallet)
            LOGINFO('Wallet Restore Complete!')
      elif self.rdoDigital.isChecked():
         self.main.execGetImportWltName()
         self.accept()
      elif self.rdoWOData.isChecked():
         # Attempt to restore the root public key & chain code for a wallet.
         # When done, ask for a wallet rescan.
         self.accept()
         dlg = DlgRestoreWOData(self.parent, self.main, doTest)
         if dlg.exec_():
            LOGINFO('Watching-Only Wallet Restore Complete! Will ask for a' \
                    'rescan.')
            self.main.addWalletToApplication(dlg.newWallet)


################################################################################
# Create a special QLineEdit with a masked input
# Forces the cursor to start at position 0 whenever there is no input
class MaskedInputLineEdit(QLineEdit):

   def __init__(self, inputMask):
      super(MaskedInputLineEdit, self).__init__()
      self.setInputMask(inputMask)
      fixFont = GETFONT('Fix', 9)
      self.setFont(fixFont)
      self.setMinimumWidth(tightSizeStr(fixFont, inputMask)[0] + 10)
      self.connect(self, SIGNAL('cursorPositionChanged(int,int)'), self.controlCursor)

   def controlCursor(self, oldpos, newpos):
      if newpos != 0 and len(str(self.text()).strip()) == 0:
         self.setCursorPosition(0)


def checkSecurePrintCode(context, SECPRINT, securePrintCode):
   result = True
   try:
      if len(securePrintCode) < 9:
         QMessageBox.critical(context, context.tr('Invalid Code'), context.trUtf8(
            u'You didn\'t enter a full SecurePrint\u200b\u2122 code.  This '
            'code is needed to decrypt your backup file.'), QMessageBox.Ok)
         result = False
      elif not SECPRINT['FUNC_CHKPWD'](securePrintCode):
         QMessageBox.critical(context, context.trUtf8(u'Bad SecurePrint\u200b\u2122 Code'), context.trUtf8(
            u'The SecurePrint\u200b\u2122 code you entered has an error '
            'in it.  Note that the code is case-sensitive.  Please verify '
            'you entered it correctly and try again.'), QMessageBox.Ok)
         result = False
   except NonBase58CharacterError as e:
      QMessageBox.critical(context, context.trUtf8(u'Bad SecurePrint\u200b\u2122 Code'), context.trUtf8(
         u'The SecurePrint\u200b\u2122 code you entered has unrecognized characters '
         'in it.  %1 Only the following characters are allowed: %2').arg(e.message, BASE58CHARS), QMessageBox.Ok)
      result = False
   return result

################################################################################
class DlgRestoreSingle(ArmoryDialog):
   #############################################################################
   def __init__(self, parent, main, thisIsATest=False, expectWltID=None):
      super(DlgRestoreSingle, self).__init__(parent, main)

      self.thisIsATest = thisIsATest
      self.testWltID = expectWltID
      headerStr = ''
      if thisIsATest:
         lblDescr = QRichLabel(self.tr(
         '<b><u><font color="blue" size="4">Test a Paper Backup</font></u></b> '
         '<br><br>'
         'Use this window to test a single-sheet paper backup.  If your '
         'backup includes imported keys, those will not be covered by this test.'))
      else:
         lblDescr = QRichLabel(self.tr(
         '<b><u>Restore a Wallet from Paper Backup</u></b> '
         '<br><br>'
         'Use this window to restore a single-sheet paper backup. '
         'If your backup includes extra pages with '
         'imported keys, please restore the base wallet first, then '
         'double-click the restored wallet and select "Import Private '
         'Keys" from the right-hand menu.'))


      lblType = QRichLabel(self.tr('<b>Backup Type:</b>'), doWrap=False)

      self.version135Button = QRadioButton(self.tr('Version 1.35 (4 lines)'), self)
      self.version135aButton = QRadioButton(self.tr('Version 1.35a (4 lines Unencrypted)'), self)
      self.version135aSPButton = QRadioButton(self.trUtf8(u'Version 1.35a (4 lines + SecurePrint\u200b\u2122)'), self)
      self.version135cButton = QRadioButton(self.tr('Version 1.35c (2 lines Unencrypted)'), self)
      self.version135cSPButton = QRadioButton(self.trUtf8(u'Version 1.35c (2 lines + SecurePrint\u200b\u2122)'), self)
      self.backupTypeButtonGroup = QButtonGroup(self)
      self.backupTypeButtonGroup.addButton(self.version135Button)
      self.backupTypeButtonGroup.addButton(self.version135aButton)
      self.backupTypeButtonGroup.addButton(self.version135aSPButton)
      self.backupTypeButtonGroup.addButton(self.version135cButton)
      self.backupTypeButtonGroup.addButton(self.version135cSPButton)
      self.version135cButton.setChecked(True)
      self.connect(self.backupTypeButtonGroup, SIGNAL('buttonClicked(int)'), self.changeType)

      layoutRadio = QVBoxLayout()
      layoutRadio.addWidget(self.version135Button)
      layoutRadio.addWidget(self.version135aButton)
      layoutRadio.addWidget(self.version135aSPButton)
      layoutRadio.addWidget(self.version135cButton)
      layoutRadio.addWidget(self.version135cSPButton)
      layoutRadio.setSpacing(0)

      radioButtonFrame = QFrame()
      radioButtonFrame.setLayout(layoutRadio)

      frmBackupType = makeVertFrame([lblType, radioButtonFrame])

      self.lblSP = QRichLabel(self.trUtf8(u'SecurePrint\u200b\u2122 Code:'), doWrap=False)
      self.editSecurePrint = QLineEdit()
      self.prfxList = [QLabel(self.tr('Root Key:')), QLabel(''), QLabel(self.tr('Chaincode:')), QLabel('')]

      inpMask = '<AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA!'
      self.edtList = [MaskedInputLineEdit(inpMask) for i in range(4)]


      self.frmSP = makeHorizFrame([STRETCH, self.lblSP, self.editSecurePrint])

      frmAllInputs = QFrame()
      frmAllInputs.setFrameStyle(STYLE_RAISED)
      layoutAllInp = QGridLayout()
      layoutAllInp.addWidget(self.frmSP, 0, 0, 1, 2)
      for i in range(4):
         layoutAllInp.addWidget(self.prfxList[i], i + 1, 0)
         layoutAllInp.addWidget(self.edtList[i], i + 1, 1)
      frmAllInputs.setLayout(layoutAllInp)

      doItText = self.tr('Test Backup') if thisIsATest else self.tr('Restore Wallet')

      self.btnAccept = QPushButton(doItText)
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.verifyUserInput)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      self.chkEncrypt = QCheckBox(self.tr('Encrypt Wallet'))
      self.chkEncrypt.setChecked(True)
      bottomFrm = makeHorizFrame([self.chkEncrypt, buttonBox])

      walletRestoreTabs = QTabWidget()
      backupTypeFrame = makeVertFrame([frmBackupType, frmAllInputs])
      walletRestoreTabs.addTab(backupTypeFrame, self.tr("Backup"))
      self.advancedOptionsTab = AdvancedOptionsFrame(parent, main)
      walletRestoreTabs.addTab(self.advancedOptionsTab, self.tr("Advanced Options"))

      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(HLINE())
      layout.addWidget(walletRestoreTabs)
      layout.addWidget(bottomFrm)
      self.setLayout(layout)


      self.chkEncrypt.setChecked(not thisIsATest)
      self.chkEncrypt.setVisible(not thisIsATest)
      self.advancedOptionsTab.setEnabled(not thisIsATest)
      if thisIsATest:
         self.setWindowTitle(self.tr('Test Single-Sheet Backup'))
      else:
         self.setWindowTitle(self.tr('Restore Single-Sheet Backup'))
         self.connect(self.chkEncrypt, SIGNAL(CLICKED), self.onEncryptCheckboxChange)

      self.setMinimumWidth(500)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.changeType(self.backupTypeButtonGroup.checkedId())

   #############################################################################
   # Hide advanced options whenver the restored wallet is unencrypted
   def onEncryptCheckboxChange(self):
      self.advancedOptionsTab.setEnabled(self.chkEncrypt.isChecked())

   #############################################################################
   def changeType(self, sel):
      if   sel == self.backupTypeButtonGroup.id(self.version135Button):
         visList = [0, 1, 1, 1, 1]
      elif sel == self.backupTypeButtonGroup.id(self.version135aButton):
         visList = [0, 1, 1, 1, 1]
      elif sel == self.backupTypeButtonGroup.id(self.version135aSPButton):
         visList = [1, 1, 1, 1, 1]
      elif sel == self.backupTypeButtonGroup.id(self.version135cButton):
         visList = [0, 1, 1, 0, 0]
      elif sel == self.backupTypeButtonGroup.id(self.version135cSPButton):
         visList = [1, 1, 1, 0, 0]
      else:
         LOGERROR('What the heck backup type is selected?  %d', sel)
         return

      self.doMask = (visList[0] == 1)
      self.frmSP.setVisible(self.doMask)
      for i in range(4):
         self.prfxList[i].setVisible(visList[i + 1] == 1)
         self.edtList[ i].setVisible(visList[i + 1] == 1)

      self.isLongForm = (visList[-1] == 1)


   #############################################################################
   def verifyUserInput(self):
      inputLines = []
      nError = 0
      rawBin = None
      nLine = 4 if self.isLongForm else 2
      for i in range(nLine):
         hasError = False
         try:
            rawEntry = str(self.edtList[i].text())
            rawBin, err = readSixteenEasyBytes(rawEntry.replace(' ', ''))
            if err == 'Error_2+':
               hasError = True
            elif err == 'Fixed_1':
               nError += 1
         except:
            hasError = True

         if hasError:
            lineNumber = i+1
            reply = QMessageBox.critical(self, self.tr('Invalid Data'), self.tr(
               'There is an error in the data you entered that could not be '
               'fixed automatically.  Please double-check that you entered the '
               'text exactly as it appears on the wallet-backup page.  <br><br> '
               'The error occured on <font color="red">line #%1</font>.').arg(lineNumber), \
               QMessageBox.Ok)
            LOGERROR('Error in wallet restore field')
            self.prfxList[i].setText('<font color="red">' + str(self.prfxList[i].text()) + '</font>')
            return

         inputLines.append(rawBin)

      if self.chkEncrypt.isChecked() and self.advancedOptionsTab.getKdfSec() == -1:
            QMessageBox.critical(self, self.tr('Invalid Target Compute Time'), \
               self.tr('You entered Target Compute Time incorrectly.\n\nEnter: <Number> (ms, s)'), QMessageBox.Ok)
            return
      if self.chkEncrypt.isChecked() and self.advancedOptionsTab.getKdfBytes() == -1:
            QMessageBox.critical(self, self.tr('Invalid Max Memory Usage'), \
               self.tr('You entered Max Memory Usage incorrectly.\n\nEnter: <Number> (kB, MB)'), QMessageBox.Ok)
            return
      if nError > 0:
         pluralStr = 'error' if nError == 1 else 'errors'

         msg = self.tr(
            'Detected errors in the data you entered. '
            'Armory attempted to fix the errors but it is not '
            'always right.  Be sure to verify the "Wallet Unique ID" '
            'closely on the next window.')

         QMessageBox.question(self, self.tr('Errors Corrected'), msg, \
            QMessageBox.Ok)

      privKey = SecureBinaryData(''.join(inputLines[:2]))
      if self.isLongForm:
         chain = SecureBinaryData(''.join(inputLines[2:]))



      if self.doMask:
         # Prepare the key mask parameters
         SECPRINT = HardcodedKeyMaskParams()
         securePrintCode = str(self.editSecurePrint.text()).strip()
         if not checkSecurePrintCode(self, SECPRINT, securePrintCode):
            return


         maskKey = SECPRINT['FUNC_KDF'](securePrintCode)
         privKey = SECPRINT['FUNC_UNMASK'](privKey, ekey=maskKey)
         if self.isLongForm:
            chain = SECPRINT['FUNC_UNMASK'](chain, ekey=maskKey)

      if not self.isLongForm:
         chain = DeriveChaincodeFromRootKey(privKey)

      # If we got here, the data is valid, let's create the wallet and accept the dlg
      # Now we should have a fully-plaintext rootkey and chaincode
      root = PyBtcAddress().createFromPlainKeyData(privKey)
      root.chaincode = chain

      first = root.extendAddressChain()
      newWltID = binary_to_base58((ADDRBYTE + first.getAddr160()[:5])[::-1])

      # Stop here if this was just a test
      if self.thisIsATest:
         verifyRecoveryTestID(self, newWltID, self.testWltID)
         return

      dlgOwnWlt = None
      if self.main.walletMap.has_key(newWltID):
         dlgOwnWlt = DlgReplaceWallet(newWltID, self.parent, self.main)

         if (dlgOwnWlt.exec_()):
            if dlgOwnWlt.output == 0:
               return
         else:
            self.reject()
            return
      else:
         reply = QMessageBox.question(self, self.tr('Verify Wallet ID'), \
                  self.tr('The data you entered corresponds to a wallet with a wallet ID: \n\n'
                  '%1\n\nDoes this ID match the "Wallet Unique ID" '
                  'printed on your paper backup?  If not, click "No" and reenter '
                  'key and chain-code data again.').arg(newWltID), \
                  QMessageBox.Yes | QMessageBox.No)
         if reply == QMessageBox.No:
            return

      passwd = []
      if self.chkEncrypt.isChecked():
         dlgPasswd = DlgChangePassphrase(self, self.main)
         if dlgPasswd.exec_():
            passwd = SecureBinaryData(str(dlgPasswd.edtPasswd1.text()))
         else:
            QMessageBox.critical(self, self.tr('Cannot Encrypt'), \
               self.tr('You requested your restored wallet be encrypted, but no '
               'valid passphrase was supplied.  Aborting wallet recovery.'), \
               QMessageBox.Ok)
            return

      shortl = ''
      longl  = ''
      nPool  = 1000

      if dlgOwnWlt is not None:
         if dlgOwnWlt.Meta is not None:
            shortl = ' - %s' % (dlgOwnWlt.Meta['shortLabel'])
            longl  = dlgOwnWlt.Meta['longLabel']
            nPool = max(nPool, dlgOwnWlt.Meta['naddress'])

      self.newWallet = PyBtcWallet()

      if passwd:
         self.newWallet.createNewWallet( \
                                 plainRootKey=privKey, \
                                 chaincode=chain, \
                                 shortLabel='Restored - ' + newWltID +shortl, \
                                 longLabel=longl, \
                                 withEncrypt=True, \
                                 securePassphrase=passwd, \
                                 kdfTargSec = \
                                 self.advancedOptionsTab.getKdfSec(), \
                                 kdfMaxMem = \
                                 self.advancedOptionsTab.getKdfBytes(),
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)
      else:
         self.newWallet.createNewWallet( \
                                 plainRootKey=privKey, \
                                 chaincode=chain, \
                                 shortLabel='Restored - ' + newWltID +shortl, \
                                 longLabel=longl, \
                                 withEncrypt=False, \
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)

      fillAddrPoolProgress = DlgProgress(self, self.main, HBar=1,
                                         Title=self.tr("Computing New Addresses"))
      fillAddrPoolProgress.exec_(self.newWallet.fillAddressPool, nPool)

      if dlgOwnWlt is not None:
         if dlgOwnWlt.Meta is not None:
            from armoryengine.PyBtcWallet import WLT_UPDATE_ADD
            for n_cmt in range(0, dlgOwnWlt.Meta['ncomments']):
               entrylist = []
               entrylist = list(dlgOwnWlt.Meta[n_cmt])
               self.newWallet.walletFileSafeUpdate([[WLT_UPDATE_ADD,
                                                     entrylist[2],
                                                     entrylist[1],
                                                     entrylist[0]]])

         self.newWallet = PyBtcWallet().readWalletFile(self.newWallet.walletPath)
      self.accept()


# Class that will create the watch-only wallet data (root public key & chain
# code) restoration window.
################################################################################
class DlgRestoreWOData(ArmoryDialog):
   #############################################################################
   def __init__(self, parent, main, thisIsATest=False, expectWltID=None):
      super(DlgRestoreWOData, self).__init__(parent, main)

      self.thisIsATest = thisIsATest
      self.testWltID = expectWltID
      headerStr = ''
      lblDescr = ''

      # Write the text at the top of the window.
      if thisIsATest:
         lblDescr = QRichLabel(self.tr(
         '<b><u><font color="blue" size="4">Test a Watch-Only Wallet Restore '
         '</font></u></b><br><br>'
         'Use this window to test the restoration of a watch-only wallet using '
         'the wallet\'s data. You can either type the data on a root data '
         'printout or import the data from a file.'))
      else:
         lblDescr = QRichLabel(self.tr(
         '<b><u><font color="blue" size="4">Restore a Watch-Only Wallet '
         '</font></u></b><br><br>'
         'Use this window to restore a watch-only wallet using the wallet\'s '
         'data. You can either type the data on a root data printout or import '
         'the data from a file.'))

      # Create the line that will contain the imported ID.
      self.rootIDLabel = QRichLabel(self.tr('Watch-Only Root ID:'), doWrap=False)
      inpMask = '<AAAA\ AAAA\ AAAA\ AAAA\ AA!'
      self.rootIDLine = MaskedInputLineEdit(inpMask)
      self.rootIDLine.setFont(GETFONT('Fixed', 9))
      self.rootIDFrame = makeHorizFrame([STRETCH, self.rootIDLabel, \
                                         self.rootIDLine])

      # Create the lines that will contain the imported key/code data.
      self.pkccLList = [QLabel(self.tr('Data:')), QLabel(''), QLabel(''), QLabel('')]
      for y in self.pkccLList:
         y.setFont(GETFONT('Fixed', 9))
      inpMask = '<AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA!'
      self.pkccList = [MaskedInputLineEdit(inpMask) for i in range(4)]
      for x in self.pkccList:
         x.setFont(GETFONT('Fixed', 9))

      # Build the frame that will contain both the ID and the key/code data.
      frmAllInputs = QFrame()
      frmAllInputs.setFrameStyle(STYLE_RAISED)
      layoutAllInp = QGridLayout()
      layoutAllInp.addWidget(self.rootIDFrame, 0, 0, 1, 2)
      for i in range(4):
         layoutAllInp.addWidget(self.pkccLList[i], i + 1, 0)
         layoutAllInp.addWidget(self.pkccList[i], i + 1, 1)
      frmAllInputs.setLayout(layoutAllInp)

      # Put together the button code.
      doItText = self.tr('Test Backup') if thisIsATest else self.tr('Restore Wallet')
      self.btnLoad   = QPushButton(self.tr("Load From Text File"))
      self.btnAccept = QPushButton(doItText)
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnLoad, SIGNAL(CLICKED), self.loadWODataFile)
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.verifyUserInput)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnLoad, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      # Set the final window layout.
      finalLayout = QVBoxLayout()
      finalLayout.addWidget(lblDescr)
      finalLayout.addWidget(makeHorizFrame(['Stretch',self.btnLoad]))
      finalLayout.addWidget(HLINE())
      finalLayout.addWidget(frmAllInputs)
      finalLayout.addWidget(makeHorizFrame([self.btnCancel, 'Stretch', self.btnAccept]))
      finalLayout.setStretch(0, 0)
      finalLayout.setStretch(1, 0)
      finalLayout.setStretch(2, 0)
      finalLayout.setStretch(3, 0)
      finalLayout.setStretch(4, 0)
      finalLayout.setStretch(4, 1)
      finalLayout.setStretch(4, 2)
      self.setLayout(finalLayout)

      # Set window title.
      if thisIsATest:
         self.setWindowTitle(self.tr('Test Watch-Only Wallet Backup'))
      else:
         self.setWindowTitle(self.tr('Restore Watch-Only Wallet Backup'))

      # Set final window layout options.
      self.setMinimumWidth(550)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)


   #############################################################################
   def loadWODataFile(self):
      '''Function for loading a root public key/chain code (\"pkcc\") file.'''
      fn = self.main.getFileLoad(self.tr('Import Wallet File'),
                                 ffilter=[self.tr('Root Pubkey Text Files (*.rootpubkey)')])
      if not os.path.exists(fn):
         return

      # Read in the data.
      # Protip: readlines() leaves in '\n'. read().splitlines() nukes '\n'.
      loadFile = open(fn, 'rb')
      fileLines = loadFile.read().splitlines()
      loadFile.close()

      # Confirm that we have an actual PKCC file.
      pkccFileVer = int(fileLines[0], 10)
      if pkccFileVer != 1:
         return
      else:
         self.rootIDLine.setText(QString(fileLines[1]))
         for curLineNum, curLine in enumerate(fileLines[2:6]):
            self.pkccList[curLineNum].setText(QString(curLine))


   #############################################################################
   def verifyUserInput(self):
      '''Function that verifies the input for a root public key/chain code
         restoration validation.'''
      inRootChecked = ''
      inputLines = []
      nError = 0
      rawBin = None
      nLine = 4
      hasError = False

      # Read in the root ID data and handle any errors.
      try:
         rawID = easyType16_to_binary(str(self.rootIDLine.text()).replace(' ', ''))
         if len(rawID) != 9:
            raise ValueError('Must supply 9 byte input for the ID')

         # Grab the data and apply the checksum to make sure it's okay.
         inRootData = rawID[:7]   # 7 bytes
         inRootChksum = rawID[7:] # 2 bytes
         inRootChecked = verifyChecksum(inRootData, inRootChksum)
         if len(inRootChecked) != 7:
            hasError = True
         elif inRootChecked != inRootData:
            nError += 1
      except:
         hasError = True

      # If the root ID is busted, stop.
      if hasError:
         (errType, errVal) = sys.exc_info()[:2]
         reply = QMessageBox.critical(self, self.tr('Invalid Data'), self.tr(
               'There is an error in the root ID you entered that could not '
               'be fixed automatically.  Please double-check that you entered the '
               'text exactly as it appears on the wallet-backup page.<br><br>'),
               QMessageBox.Ok)
         LOGERROR('Error in root ID restore field')
         LOGERROR('Error Type: %s', errType)
         LOGERROR('Error Value: %s', errVal)
         return

      # Save the version/key byte and the root ID. For now, ignore the version.
      inRootVer = inRootChecked[0]  # 1 byte
      inRootID = inRootChecked[1:7] # 6 bytes

      # Read in the root data (public key & chain code) and handle any errors.
      for i in range(nLine):
         hasError = False
         try:
            rawEntry = str(self.pkccList[i].text())
            rawBin, err = readSixteenEasyBytes(rawEntry.replace(' ', ''))
            if err == 'Error_2+':  # 2+ bytes are wrong, so we need to stop.
               hasError = True
            elif err == 'Fixed_1': # 1 byte is wrong, so we may be okay.
               nError += 1
         except:
            hasError = True

         # If the root ID is busted, stop.
         if hasError:
            lineNumber = i+1
            reply = QMessageBox.critical(self, self.tr('Invalid Data'), self.tr(
               'There is an error in the root data you entered that could not be '
               'fixed automatically.  Please double-check that you entered the '
               'text exactly as it appears on the wallet-backup page.  <br><br>'
               'The error occured on <font color="red">line #%1</font>.').arg(lineNumber), QMessageBox.Ok)
            LOGERROR('Error in root data restore field')
            return

         # If we've gotten this far, save the incoming line.
         inputLines.append(rawBin)

      # Set up the root ID data.
      pkVer = binary_to_int(inRootVer) & PYROOTPKCCVERMASK  # Ignored for now.
      pkSignByte = ((binary_to_int(inRootVer) & PYROOTPKCCSIGNMASK) >> 7) + 2
      rootPKComBin = int_to_binary(pkSignByte) + ''.join(inputLines[:2])
      rootPubKey = CryptoECDSA().UncompressPoint(SecureBinaryData(rootPKComBin))
      rootChainCode = SecureBinaryData(''.join(inputLines[2:]))

      # Now we should have a fully-plaintext root key and chain code, and can
      # get some related data.
      root = PyBtcAddress().createFromPublicKeyData(rootPubKey)
      root.chaincode = rootChainCode
      first = root.extendAddressChain()
      newWltID = binary_to_base58(inRootID)

      # Stop here if this was just a test
      if self.thisIsATest:
         verifyRecoveryTestID(self, newWltID, self.testWltID)
         return

      # If we already have the wallet, don't replace it, otherwise proceed.
      dlgOwnWlt = None
      if self.main.walletMap.has_key(newWltID):
         QMessageBox.warning(self, self.tr('Wallet Already Exists'), self.tr(
                             'The wallet already exists and will not be '
                             'replaced.'), QMessageBox.Ok)
         self.reject()
         return
      else:
         # Make sure the user is restoring the wallet they want to restore.
         reply = QMessageBox.question(self, self.tr('Verify Wallet ID'), \
                  self.tr('The data you entered corresponds to a wallet with a wallet '
                  'ID: \n\n\t%1\n\nDoes this '
                  'ID match the "Wallet Unique ID" you intend to restore? '
                  'If not, click "No" and enter the key and chain-code data '
                  'again.').arg(binary_to_base58(inRootID)), QMessageBox.Yes | QMessageBox.No)
         if reply == QMessageBox.No:
            return

         # Create the wallet.
         self.newWallet = PyBtcWallet().createNewWalletFromPKCC(rootPubKey, \
                                                                rootChainCode)

         # Create some more addresses and show a progress bar while restoring.
         nPool = 1000
         fillAddrPoolProgress = DlgProgress(self, self.main, HBar=1,
                                            Title=self.tr("Computing New Addresses"))
         fillAddrPoolProgress.exec_(self.newWallet.fillAddressPool, nPool)

      self.accept()


################################################################################
class DlgRestoreFragged(ArmoryDialog):
   def __init__(self, parent, main, thisIsATest=False, expectWltID=None):
      super(DlgRestoreFragged, self).__init__(parent, main)

      self.thisIsATest = thisIsATest
      self.testWltID = expectWltID
      headerStr = ''
      if thisIsATest:
         headerStr = self.tr('<font color="blue" size="4">Testing a '
                     'Fragmented Backup</font>')
      else:
         headerStr = self.tr('Restore Wallet from Fragments')

      descr = self.trUtf8(
         '<b><u>%1</u></b> <br><br>'
         'Use this form to enter all the fragments to be restored.  Fragments '
         'can be stored on a mix of paper printouts, and saved files. '
         u'If any of the fragments require a SecurePrint\u200b\u2122 code, '
         'you will only have to enter it once, since that code is the same for '
         'all fragments of any given wallet.').arg(headerStr)

      if self.thisIsATest:
         descr += self.tr('<br><br>'
            '<b>For testing purposes, you may enter more fragments than needed '
            'and Armory will test all subsets of the entered fragments to verify '
            'that each one still recovers the wallet successfully.</b>')

      lblDescr = QRichLabel(descr)

      frmDescr = makeHorizFrame([lblDescr], STYLE_RAISED)

      # HLINE

      self.scrollFragInput = QScrollArea()
      self.scrollFragInput.setWidgetResizable(True)
      self.scrollFragInput.setMinimumHeight(150)

      lblFragList = QRichLabel(self.tr('Input Fragments Below:'), doWrap=False, bold=True)
      self.btnAddFrag = QPushButton(self.tr('+Frag'))
      self.btnRmFrag = QPushButton(self.tr('-Frag'))
      self.btnRmFrag.setVisible(False)
      self.connect(self.btnAddFrag, SIGNAL(CLICKED), self.addFragment)
      self.connect(self.btnRmFrag, SIGNAL(CLICKED), self.removeFragment)
      self.chkEncrypt = QCheckBox(self.tr('Encrypt Restored Wallet'))
      self.chkEncrypt.setChecked(True)
      frmAddRm = makeHorizFrame([self.chkEncrypt, STRETCH, self.btnRmFrag, self.btnAddFrag])

      self.fragDataMap = {}
      self.tableSize = 2
      self.wltType = UNKNOWN
      self.fragIDPrefix = UNKNOWN

      doItText = self.tr('Test Backup') if thisIsATest else self.tr('Restore from Fragments')

      btnExit = QPushButton(self.tr('Cancel'))
      self.btnRestore = QPushButton(doItText)
      self.connect(btnExit, SIGNAL(CLICKED), self.reject)
      self.connect(self.btnRestore, SIGNAL(CLICKED), self.processFrags)
      frmBtns = makeHorizFrame([btnExit, STRETCH, self.btnRestore])

      self.lblRightFrm = QRichLabel('', hAlign=Qt.AlignHCenter)
      self.lblSecureStr = QRichLabel(self.trUtf8(u'SecurePrint\u200b\u2122 Code:'), \
                                     hAlign=Qt.AlignHCenter,
                                     doWrap=False,
                                     color='TextWarn')
      self.displaySecureString = QLineEdit()
      self.imgPie = QRichLabel('', hAlign=Qt.AlignHCenter)
      self.imgPie.setMinimumWidth(96)
      self.imgPie.setMinimumHeight(96)
      self.lblReqd = QRichLabel('', hAlign=Qt.AlignHCenter)
      self.lblWltID = QRichLabel('', doWrap=False, hAlign=Qt.AlignHCenter)
      self.lblFragID = QRichLabel('', doWrap=False, hAlign=Qt.AlignHCenter)
      self.lblSecureStr.setVisible(False)
      self.displaySecureString.setVisible(False)
      self.displaySecureString.setMaximumWidth(relaxedSizeNChar(self.displaySecureString, 16)[0])
      # The Secure String is now edited in DlgEnterOneFrag, It is only displayed here
      self.displaySecureString.setEnabled(False)
      frmSecPair = makeVertFrame([self.lblSecureStr, self.displaySecureString])
      frmSecCtr = makeHorizFrame([STRETCH, frmSecPair, STRETCH])

      frmWltInfo = makeVertFrame([STRETCH,
                                   self.lblRightFrm,
                                   self.imgPie,
                                   self.lblReqd,
                                   self.lblWltID,
                                   self.lblFragID,
                                   HLINE(),
                                   frmSecCtr,
                                   'Strut(200)',
                                   STRETCH], STYLE_SUNKEN)


      fragmentsLayout = QGridLayout()
      fragmentsLayout.addWidget(frmDescr, 0, 0, 1, 2)
      fragmentsLayout.addWidget(frmAddRm, 1, 0, 1, 1)
      fragmentsLayout.addWidget(self.scrollFragInput, 2, 0, 1, 1)
      fragmentsLayout.addWidget(frmWltInfo, 1, 1, 2, 1)
      setLayoutStretchCols(fragmentsLayout, 1, 0)

      walletRestoreTabs = QTabWidget()
      fragmentsFrame = QFrame()
      fragmentsFrame.setLayout(fragmentsLayout)
      walletRestoreTabs.addTab(fragmentsFrame, self.tr("Fragments"))
      self.advancedOptionsTab = AdvancedOptionsFrame(parent, main)
      walletRestoreTabs.addTab(self.advancedOptionsTab, self.tr("Advanced Options"))

      self.chkEncrypt.setChecked(not thisIsATest)
      self.chkEncrypt.setVisible(not thisIsATest)
      self.advancedOptionsTab.setEnabled(not thisIsATest)
      if not thisIsATest:
         self.connect(self.chkEncrypt, SIGNAL(CLICKED), self.onEncryptCheckboxChange)

      layout = QVBoxLayout()
      layout.addWidget(walletRestoreTabs)
      layout.addWidget(frmBtns)
      self.setLayout(layout)
      self.setMinimumWidth(650)
      self.setMinimumHeight(500)
      self.sizeHint = lambda: QSize(800, 650)
      self.setWindowTitle(self.tr('Restore wallet from fragments'))

      self.makeFragInputTable()
      self.checkRestoreParams()

   #############################################################################
   # Hide advanced options whenver the restored wallet is unencrypted
   def onEncryptCheckboxChange(self):
      self.advancedOptionsTab.setEnabled(self.chkEncrypt.isChecked())

   def makeFragInputTable(self, addCount=0):

      self.tableSize += addCount
      newLayout = QGridLayout()
      newFrame = QFrame()
      self.fragsDone = []
      newLayout.addWidget(HLINE(), 0, 0, 1, 5)
      for i in range(self.tableSize):
         btnEnter = QPushButton(self.tr('Type Data'))
         btnLoad = QPushButton(self.tr('Load File'))
         btnClear = QPushButton(self.tr('Clear'))
         lblFragID = QRichLabel('', doWrap=False)
         lblSecure = QLabel('')
         if i in self.fragDataMap:
            M, fnum, wltID, doMask, fid = ReadFragIDLineBin(self.fragDataMap[i][0])
            self.fragsDone.append(fnum)
            lblFragID.setText('<b>' + fid + '</b>')
            if doMask:
               lblFragID.setText('<b>' + fid + '</b>', color='TextWarn')


         self.connect(btnEnter, SIGNAL(CLICKED), \
                      functools.partial(self.dataEnter, fnum=i))
         self.connect(btnLoad, SIGNAL(CLICKED), \
                      functools.partial(self.dataLoad, fnum=i))
         self.connect(btnClear, SIGNAL(CLICKED), \
                      functools.partial(self.dataClear, fnum=i))


         newLayout.addWidget(btnEnter, 2 * i + 1, 0)
         newLayout.addWidget(btnLoad, 2 * i + 1, 1)
         newLayout.addWidget(btnClear, 2 * i + 1, 2)
         newLayout.addWidget(lblFragID, 2 * i + 1, 3)
         newLayout.addWidget(lblSecure, 2 * i + 1, 4)
         newLayout.addWidget(HLINE(), 2 * i + 2, 0, 1, 5)

      btnFrame = QFrame()
      btnFrame.setLayout(newLayout)

      frmFinal = makeVertFrame([btnFrame, STRETCH], STYLE_SUNKEN)
      self.scrollFragInput.setWidget(frmFinal)

      self.btnAddFrag.setVisible(self.tableSize < 12)
      self.btnRmFrag.setVisible(self.tableSize > 2)


   #############################################################################
   def addFragment(self):
      self.makeFragInputTable(1)

   #############################################################################
   def removeFragment(self):
      self.makeFragInputTable(-1)
      toRemove = []
      for key, val in self.fragDataMap.iteritems():
         if key >= self.tableSize:
            toRemove.append(key)

      # Have to do this in a separate loop, cause you can't remove items
      # from a map while you are iterating over them
      for key in toRemove:
         self.dataClear(key)


   #############################################################################
   def dataEnter(self, fnum):
      dlg = DlgEnterOneFrag(self, self.main, self.fragsDone, self.wltType, self.displaySecureString.text())
      if dlg.exec_():
         LOGINFO('Good data from enter_one_frag exec! %d', fnum)
         self.displaySecureString.setText(dlg.editSecurePrint.text())
         self.addFragToTable(fnum, dlg.fragData)
         self.makeFragInputTable()


   #############################################################################
   def dataLoad(self, fnum):
      LOGINFO('Loading data for entry, %d', fnum)
      toLoad = unicode(self.main.getFileLoad('Load Fragment File', \
                                    ['Wallet Fragments (*.frag)']))

      if len(toLoad) == 0:
         return

      if not os.path.exists(toLoad):
         LOGERROR('File just chosen does not exist! %s', toLoad)
         QMessageBox.critical(self, self.tr('File Does Not Exist'), self.tr(
            'The file you select somehow does not exist...? '
            '<br><br>%1<br><br> Try a different file').arg(toLoad), \
            QMessageBox.Ok)

      fragMap = {}
      with open(toLoad, 'r') as fin:
         allData = [line.strip() for line in fin.readlines()]
         fragMap = {}
         for line in allData:
            if line[:2].lower() in ['id', 'x1', 'x2', 'x3', 'x4', \
                                         'y1', 'y2', 'y3', 'y4', \
                                         'f1', 'f2', 'f3', 'f4']:
               fragMap[line[:2].lower()] = line[3:].strip().replace(' ', '')


      cList, nList = [], []
      if len(fragMap) == 9:
         cList, nList = ['x', 'y'], ['1', '2', '3', '4']
      elif len(fragMap) == 5:
         cList, nList = ['f'], ['1', '2', '3', '4']
      elif len(fragMap) == 3:
         cList, nList = ['f'], ['1', '2']
      else:
         LOGERROR('Unexpected number of lines in the frag file, %d', len(fragMap))
         return

      fragData = []
      fragData.append(hex_to_binary(fragMap['id']))
      for c in cList:
         for n in nList:
            mapKey = c + n
            rawBin, err = readSixteenEasyBytes(fragMap[c + n])
            if err == 'Error_2+':
               QMessageBox.critical(self, self.tr('Fragment Error'), self.tr(
                  'There was an unfixable error in the fragment file: '
                  '<br><br> File: %1 <br> Line: %2 <br>').arg(toLoad, mapKey), \
                  QMessageBox.Ok)
               return
            fragData.append(SecureBinaryData(rawBin))
            rawBin = None

      self.addFragToTable(fnum, fragData)
      self.makeFragInputTable()


   #############################################################################
   def dataClear(self, fnum):
      if not fnum in self.fragDataMap:
         return

      for i in range(1, 3):
         self.fragDataMap[fnum][i].destroy()
      del self.fragDataMap[fnum]
      self.makeFragInputTable()
      self.checkRestoreParams()


   #############################################################################
   def checkRestoreParams(self):
      showRightFrm = False
      self.btnRestore.setEnabled(False)
      self.lblRightFrm.setText(self.tr(
         '<b>Start entering fragments into the table to left...</b>'))
      for row, data in self.fragDataMap.iteritems():
         showRightFrm = True
         M, fnum, setIDBin, doMask, idBase58 = ReadFragIDLineBin(data[0])
         self.lblRightFrm.setText(self.tr('<b><u>Wallet Being Restored:</u></b>'))
         self.imgPie.setPixmap(QPixmap(':/frag%df.png' % M).scaled(96,96))
         self.lblReqd.setText(self.tr('<b>Frags Needed:</b> %1').arg(M))
         self.lblFragID.setText(self.tr('<b>Fragments:</b> %1').arg(idBase58.split('-')[0]))
         self.btnRestore.setEnabled(len(self.fragDataMap) >= M)
         break

      anyMask = False
      for row, data in self.fragDataMap.iteritems():
         M, fnum, wltIDBin, doMask, idBase58 = ReadFragIDLineBin(data[0])
         if doMask:
            anyMask = True
            break
      # If all of the rows with a Mask have been removed clear the securePrintCode
      if  not anyMask:
         self.displaySecureString.setText('')
      self.lblSecureStr.setVisible(anyMask)
      self.displaySecureString.setVisible(anyMask)

      if not showRightFrm:
         self.fragIDPrefix = UNKNOWN
         self.wltType = UNKNOWN

      self.imgPie.setVisible(showRightFrm)
      self.lblReqd.setVisible(showRightFrm)
      self.lblWltID.setVisible(showRightFrm)
      self.lblFragID.setVisible(showRightFrm)


   #############################################################################
   def addFragToTable(self, tableIndex, fragData):

      if len(fragData) == 9:
         currType = '0'
      elif len(fragData) == 5:
         currType = BACKUP_TYPE_135A
      elif len(fragData) == 3:
         currType = BACKUP_TYPE_135C
      else:
         LOGERROR('How\'d we get fragData of size: %d', len(fragData))
         return

      if self.wltType == UNKNOWN:
         self.wltType = currType
      elif not self.wltType == currType:
         QMessageBox.critical(self, self.tr('Mixed fragment types'), self.tr(
            'You entered a fragment for a different wallet type.  Please check '
            'that all fragments are for the same wallet, of the same version, '
            'and require the same number of fragments.'), QMessageBox.Ok)
         LOGERROR('Mixing frag types!  How did that happen?')
         return


      M, fnum, wltIDBin, doMask, idBase58 = ReadFragIDLineBin(fragData[0])
      # If we don't know the Secure String Yet we have to get it
      if doMask and len(str(self.displaySecureString.text()).strip()) == 0:
         dlg = DlgEnterSecurePrintCode(self, self.main)
         if dlg.exec_():
            self.displaySecureString.setText(dlg.editSecurePrint.text())
         else:
            return

      if self.fragIDPrefix == UNKNOWN:
         self.fragIDPrefix = idBase58.split('-')[0]
      elif not self.fragIDPrefix == idBase58.split('-')[0]:
         QMessageBox.critical(self, self.tr('Multiple Wallets'), self.tr(
            'The fragment you just entered is actually for a different wallet '
            'than the previous fragments you entered.  Please double-check that '
            'all the fragments you are entering belong to the same wallet and '
            'have the "number of needed fragments" (M-value, in M-of-N).'), \
            QMessageBox.Ok)
         LOGERROR('Mixing fragments of different wallets! %s', idBase58)
         return


      if not self.verifyNonDuplicateFrag(fnum):
         QMessageBox.critical(self, self.tr('Duplicate Fragment'), self.tr(
            'You just input fragment #%1, but that fragment has already been '
            'entered!').arg(fnum), QMessageBox.Ok)
         return



      if currType == '0':
         X = SecureBinaryData(''.join([fragData[i].toBinStr() for i in range(1, 5)]))
         Y = SecureBinaryData(''.join([fragData[i].toBinStr() for i in range(5, 9)]))
      elif currType == BACKUP_TYPE_135A:
         X = SecureBinaryData(int_to_binary(fnum + 1, widthBytes=64, endOut=BIGENDIAN))
         Y = SecureBinaryData(''.join([fragData[i].toBinStr() for i in range(1, 5)]))
      elif currType == BACKUP_TYPE_135C:
         X = SecureBinaryData(int_to_binary(fnum + 1, widthBytes=32, endOut=BIGENDIAN))
         Y = SecureBinaryData(''.join([fragData[i].toBinStr() for i in range(1, 3)]))

      self.fragDataMap[tableIndex] = [fragData[0][:], X.copy(), Y.copy()]

      X.destroy()
      Y.destroy()
      self.checkRestoreParams()

   #############################################################################
   def verifyNonDuplicateFrag(self, fnum):
      for row, data in self.fragDataMap.iteritems():
         rowFrag = ReadFragIDLineBin(data[0])[1]
         if fnum == rowFrag:
            return False

      return True



   #############################################################################
   def processFrags(self):
      if self.chkEncrypt.isChecked() and self.advancedOptionsTab.getKdfSec() == -1:
            QMessageBox.critical(self, self.tr('Invalid Target Compute Time'), \
               self.tr('You entered Target Compute Time incorrectly.\n\nEnter: <Number> (ms, s)'), QMessageBox.Ok)
            return
      if self.chkEncrypt.isChecked() and self.advancedOptionsTab.getKdfBytes() == -1:
            QMessageBox.critical(self, self.tr('Invalid Max Memory Usage'), \
               self.tr('You entered Max Memory Usage incorrectly.\n\nEnter: <Number> (kB, MB)'), QMessageBox.Ok)
            return
      SECPRINT = HardcodedKeyMaskParams()
      pwd, ekey = '', ''
      if self.displaySecureString.isVisible():
         pwd = str(self.displaySecureString.text()).strip()
         maskKey = SECPRINT['FUNC_KDF'](pwd)

      fragMtrx, M = [], -1
      for row, trip in self.fragDataMap.iteritems():
         M, fnum, wltID, doMask, fid = ReadFragIDLineBin(trip[0])
         X, Y = trip[1], trip[2]
         if doMask:
            LOGINFO('Row %d needs unmasking' % row)
            Y = SECPRINT['FUNC_UNMASK'](Y, ekey=maskKey)
         else:
            LOGINFO('Row %d is already unencrypted' % row)
         fragMtrx.append([X.toBinStr(), Y.toBinStr()])

      typeToBytes = {'0': 64, BACKUP_TYPE_135A: 64, BACKUP_TYPE_135C: 32}
      nBytes = typeToBytes[self.wltType]


      if self.thisIsATest and len(fragMtrx) > M:
         self.testFragSubsets(fragMtrx, M)
         return


      SECRET = ReconstructSecret(fragMtrx, M, nBytes)
      for i in range(len(fragMtrx)):
         fragMtrx[i] = []

      LOGINFO('Final length of frag mtrx: %d', len(fragMtrx))
      LOGINFO('Final length of secret:    %d', len(SECRET))

      priv, chain = '', ''
      if len(SECRET) == 64:
         priv = SecureBinaryData(SECRET[:32 ])
         chain = SecureBinaryData(SECRET[ 32:])
      elif len(SECRET) == 32:
         priv = SecureBinaryData(SECRET)
         chain = DeriveChaincodeFromRootKey(priv)


      # If we got here, the data is valid, let's create the wallet and accept the dlg
      # Now we should have a fully-plaintext rootkey and chaincode
      root = PyBtcAddress().createFromPlainKeyData(priv)
      root.chaincode = chain

      first = root.extendAddressChain()
      newWltID = binary_to_base58((ADDRBYTE + first.getAddr160()[:5])[::-1])

      # If this is a test, then bail
      if self.thisIsATest:
         verifyRecoveryTestID(self, newWltID, self.testWltID)
         return

      dlgOwnWlt = None
      if self.main.walletMap.has_key(newWltID):
         dlgOwnWlt = DlgReplaceWallet(newWltID, self.parent, self.main)

         if (dlgOwnWlt.exec_()):
            if dlgOwnWlt.output == 0:
               return
         else:
            self.reject()
            return

      reply = QMessageBox.question(self, self.tr('Verify Wallet ID'), self.tr(
         'The data you entered corresponds to a wallet with the '
         'ID:<blockquote><b>{%1}</b></blockquote>Does this ID '
         'match the "Wallet Unique ID" printed on your paper backup? '
         'If not, click "No" and reenter key and chain-code data '
         'again.').arg(newWltID), QMessageBox.Yes | QMessageBox.No)
      if reply == QMessageBox.No:
         return


      passwd = []
      if self.chkEncrypt.isChecked():
         dlgPasswd = DlgChangePassphrase(self, self.main)
         if dlgPasswd.exec_():
            passwd = SecureBinaryData(str(dlgPasswd.edtPasswd1.text()))
         else:
            QMessageBox.critical(self, self.tr('Cannot Encrypt'), self.tr(
               'You requested your restored wallet be encrypted, but no '
               'valid passphrase was supplied.  Aborting wallet '
               'recovery.'), QMessageBox.Ok)
            return

      shortl = ''
      longl  = ''
      nPool  = 1000

      if dlgOwnWlt is not None:
         if dlgOwnWlt.Meta is not None:
            shortl = ' - %s' % (dlgOwnWlt.Meta['shortLabel'])
            longl  = dlgOwnWlt.Meta['longLabel']
            nPool = max(nPool, dlgOwnWlt.Meta['naddress'])

      if passwd:
         self.newWallet = PyBtcWallet().createNewWallet(\
                                 plainRootKey=priv, \
                                 chaincode=chain, \
                                 shortLabel='Restored - ' + newWltID + shortl, \
                                 longLabel=longl, \
                                 withEncrypt=True, \
                                 securePassphrase=passwd, \
                                 kdfTargSec=self.advancedOptionsTab.getKdfSec(), \
                                 kdfMaxMem=self.advancedOptionsTab.getKdfBytes(),
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)
      else:
         self.newWallet = PyBtcWallet().createNewWallet(\
                                 plainRootKey=priv, \
                                 chaincode=chain, \
                                 shortLabel='Restored - ' + newWltID +shortl, \
                                 longLabel=longl, \
                                 withEncrypt=False, \
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)


      # Will pop up a little "please wait..." window while filling addr pool
      fillAddrPoolProgress = DlgProgress(self, self.parent, HBar=1,
                                         Title=self.tr("Computing New Addresses"))
      fillAddrPoolProgress.exec_(self.newWallet.fillAddressPool, nPool)

      if dlgOwnWlt is not None:
         if dlgOwnWlt.Meta is not None:
            from armoryengine.PyBtcWallet import WLT_UPDATE_ADD
            for n_cmt in range(0, dlgOwnWlt.Meta['ncomments']):
               entrylist = []
               entrylist = list(dlgOwnWlt.Meta[n_cmt])
               self.newWallet.walletFileSafeUpdate([[WLT_UPDATE_ADD, entrylist[2], entrylist[1], entrylist[0]]])

         self.newWallet = PyBtcWallet().readWalletFile(self.newWallet.walletPath)
      self.accept()

   #############################################################################
   def testFragSubsets(self, fragMtrx, M):
      # If the user entered multiple fragments
      fragMap = {}
      for x, y in fragMtrx:
         fragMap[binary_to_int(x, BIGENDIAN) - 1] = [x, y]
      typeToBytes = {'0': 64, BACKUP_TYPE_135A: 64, BACKUP_TYPE_135C: 32}

      isRandom, results = testReconstructSecrets(fragMap, M, 100)
      def privAndChainFromRow(secret):
         priv, chain = None, None
         if len(secret) == 64:
            priv = SecureBinaryData(secret[:32 ])
            chain = SecureBinaryData(secret[ 32:])
            return (priv, chain)
         elif len(secret) == 32:
            priv = SecureBinaryData(secret)
            chain = DeriveChaincodeFromRootKey(priv)
            return (priv, chain)
         else:
            LOGERROR('Root secret is %s bytes ?!' % len(secret))
            raise KeyDataError

      results = [(row[0], privAndChainFromRow(row[1])) for row in results]
      subsAndIDs = [(row[0], calcWalletIDFromRoot(*row[1])) for row in results]

      DlgShowTestResults(self, isRandom, subsAndIDs, \
                                 M, len(fragMtrx), self.testWltID).exec_()


##########################################################################
class DlgShowTestResults(ArmoryDialog):
   #######################################################################
   def __init__(self, parent, isRandom, subsAndIDs, M, nFrag, expectID):
      super(DlgShowTestResults, self).__init__(parent, parent.main)

      accumSet = set()
      for sub, ID in subsAndIDs:
         accumSet.add(ID)

      allEqual = (len(accumSet) == 1)
      allCorrect = True
      testID = expectID
      if not testID:
         testID = subsAndIDs[0][1]

      allCorrect = testID == subsAndIDs[0][1]

      descr = ''
      nSubs = len(subsAndIDs)
      fact = lambda x: math.factorial(x)
      total = fact(nFrag) / (fact(M) * fact(nFrag - M))
      if isRandom:
         descr = self.tr(
            'The total number of fragment subsets (%1) is too high '
            'to test and display.  Instead, %2 subsets were tested '
            'at random.  The results are below ').arg(total, nSubs)
      else:
         descr = self.tr(
            'For the fragments you entered, there are a total of '
            '%1 possible subsets that can restore your wallet. '
            'The test results for all subsets are shown below').arg(total)

      lblDescr = QRichLabel(descr)

      lblWltIDDescr = QRichLabel(self.tr(
         'The wallet ID is computed from the first '
         'address in your wallet based on the root key data (and the '
         '"chain code").  Therefore, a matching wallet ID proves that '
         'the wallet will produce identical addresses.'))


      frmResults = QFrame()
      layout = QGridLayout()
      row = 0
      for sub, ID in subsAndIDs:
         subStrs = [str(s) for s in sub]
         subText = ', '.join(subStrs[:-1])
         dispTxt = self.tr(
            'Fragments <b>%1</b> and <b>%2</b> produce a '
            'wallet with ID "<b>%3</b>"').arg(subText, subStrs[-1], ID)

         chk = lambda: QPixmap(':/checkmark32.png').scaled(20, 20)
         _X_ = lambda: QPixmap(':/red_X.png').scaled(16, 16)

         lblTxt = QRichLabel(dispTxt)
         lblTxt.setWordWrap(False)
         lblPix = QLabel('')
         lblPix.setPixmap(chk() if ID == testID else _X_())
         layout.addWidget(lblTxt, row, 0)
         layout.addWidget(lblPix, row, 1)
         row += 1



      scrollResults = QScrollArea()
      frmResults = QFrame()
      frmResults.setLayout(layout)
      scrollResults.setWidget(frmResults)

      btnOkay = QPushButton(self.tr('Ok'))
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(btnOkay, QDialogButtonBox.AcceptRole)
      self.connect(btnOkay, SIGNAL(CLICKED), self.accept)

      mainLayout = QVBoxLayout()
      mainLayout.addWidget(lblDescr)
      mainLayout.addWidget(scrollResults)
      mainLayout.addWidget(lblWltIDDescr)
      mainLayout.addWidget(buttonBox)
      self.setLayout(mainLayout)

      self.setWindowTitle(self.tr('Fragment Test Results'))
      self.setMinimumWidth(500)

################################################################################
class DlgEnterSecurePrintCode(ArmoryDialog):

   def __init__(self, parent, main):
      super(DlgEnterSecurePrintCode, self).__init__(parent, main)

      lblSecurePrintCodeDescr = QRichLabel(self.trUtf8(
         u'This fragment file requires a SecurePrint\u200b\u2122 code. '
         'You will only have to enter this code once since it is the same '
         'on all fragments.'))
      lblSecurePrintCodeDescr.setMinimumWidth(440)
      self.lblSP = QRichLabel(self.trUtf8(u'SecurePrint\u200b\u2122 Code: '), doWrap=False)
      self.editSecurePrint = QLineEdit()
      spFrame = makeHorizFrame([self.lblSP, self.editSecurePrint, STRETCH])

      self.btnAccept = QPushButton(self.tr("Done"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.verifySecurePrintCode)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QVBoxLayout()
      layout.addWidget(lblSecurePrintCodeDescr)
      layout.addWidget(spFrame)
      layout.addWidget(buttonBox)
      self.setLayout(layout)
      self.setWindowTitle(self.tr('Enter Secure Print Code'))

   def verifySecurePrintCode(self):
      # Prepare the key mask parameters
      SECPRINT = HardcodedKeyMaskParams()
      securePrintCode = str(self.editSecurePrint.text()).strip()

      if not checkSecurePrintCode(self, SECPRINT, securePrintCode):
         return

      self.accept()

################################################################################
class DlgEnterOneFrag(ArmoryDialog):

   def __init__(self, parent, main, fragList=[], wltType=UNKNOWN, securePrintCode=None):
      super(DlgEnterOneFrag, self).__init__(parent, main)
      self.fragData = []
      BLUE = htmlColor('TextBlue')
      already = ''
      if len(fragList) > 0:
         strList = ['<font color="%s">%d</font>' % (BLUE, f) for f in fragList]
         replStr = '[' + ','.join(strList[:]) + ']'
         already = self.tr('You have entered fragments %1, so far.').arg(replStr)

      lblDescr = QRichLabel(self.trUtf8(
         '<b><u>Enter Another Fragment...</u></b> <br><br> %1 '
         'The fragments can be entered in any order, as long as you provide '
         'enough of them to restore the wallet.  If any fragments use a '
         u'SecurePrint\u200b\u2122 code, please enter it once on the '
         'previous window, and it will be applied to all fragments that '
         'require it.').arg(already))

      self.version0Button = QRadioButton(self.tr( BACKUP_TYPE_0_TEXT), self)
      self.version135aButton = QRadioButton(self.tr( BACKUP_TYPE_135a_TEXT), self)
      self.version135aSPButton = QRadioButton(self.trUtf8( BACKUP_TYPE_135a_SP_TEXT), self)
      self.version135cButton = QRadioButton(self.tr( BACKUP_TYPE_135c_TEXT), self)
      self.version135cSPButton = QRadioButton(self.trUtf8( BACKUP_TYPE_135c_SP_TEXT), self)
      self.backupTypeButtonGroup = QButtonGroup(self)
      self.backupTypeButtonGroup.addButton(self.version0Button)
      self.backupTypeButtonGroup.addButton(self.version135aButton)
      self.backupTypeButtonGroup.addButton(self.version135aSPButton)
      self.backupTypeButtonGroup.addButton(self.version135cButton)
      self.backupTypeButtonGroup.addButton(self.version135cSPButton)
      self.version135cButton.setChecked(True)
      self.connect(self.backupTypeButtonGroup, SIGNAL('buttonClicked(int)'), self.changeType)

      # This value will be locked after the first fragment is entered.
      if wltType == UNKNOWN:
         self.version135cButton.setChecked(True)
      elif wltType == '0':
         self.version0Button.setChecked(True)
         self.version135aButton.setEnabled(False)
         self.version135aSPButton.setEnabled(False)
         self.version135cButton.setEnabled(False)
         self.version135cSPButton.setEnabled(False)
      elif wltType == BACKUP_TYPE_135A:
            # Could be 1.35a with or without SecurePrintCode so remove the rest
         self.version0Button.setEnabled(False)
         self.version135cButton.setEnabled(False)
         self.version135cSPButton.setEnabled(False)
         if securePrintCode:
            self.version135aSPButton.setChecked(True)
         else:
            self.version135aButton.setChecked(True)
      elif wltType == BACKUP_TYPE_135C:
         # Could be 1.35c with or without SecurePrintCode so remove the rest
         self.version0Button.setEnabled(False)
         self.version135aButton.setEnabled(False)
         self.version135aSPButton.setEnabled(False)
         if securePrintCode:
            self.version135cSPButton.setChecked(True)
         else:
            self.version135cButton.setChecked(True)

      lblType = QRichLabel(self.tr('<b>Backup Type:</b>'), doWrap=False)

      layoutRadio = QVBoxLayout()
      layoutRadio.addWidget(self.version0Button)
      layoutRadio.addWidget(self.version135aButton)
      layoutRadio.addWidget(self.version135aSPButton)
      layoutRadio.addWidget(self.version135cButton)
      layoutRadio.addWidget(self.version135cSPButton)
      layoutRadio.setSpacing(0)

      radioButtonFrame = QFrame()
      radioButtonFrame.setLayout(layoutRadio)

      frmBackupType = makeVertFrame([lblType, radioButtonFrame])

      self.prfxList = ['x1:', 'x2:', 'x3:', 'x4:', \
                       'y1:', 'y2:', 'y3:', 'y4:', \
                       'F1:', 'F2:', 'F3:', 'F4:']
      self.prfxList = [QLabel(p) for p in self.prfxList]
      inpMask = '<AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA\ AAAA\ AAAA\ AAAA\ \ AAAA!'
      self.edtList = [MaskedInputLineEdit(inpMask) for i in range(12)]

      inpMaskID = '<HHHH\ HHHH\ HHHH\ HHHH!'
      self.lblID = QRichLabel('ID:')
      self.edtID = MaskedInputLineEdit(inpMaskID)

      frmAllInputs = QFrame()
      frmAllInputs.setFrameStyle(STYLE_RAISED)
      layoutAllInp = QGridLayout()

      # Add Secure Print row - Use supplied securePrintCode and
      # disable text entry if it is not None
      self.lblSP = QRichLabel(self.trUtf8(u'SecurePrint\u200b\u2122 Code:'), doWrap=False)
      self.editSecurePrint = QLineEdit()
      self.editSecurePrint.setEnabled(not securePrintCode)
      if (securePrintCode):
         self.editSecurePrint.setText(securePrintCode)
      self.frmSP = makeHorizFrame([STRETCH, self.lblSP, self.editSecurePrint])
      layoutAllInp.addWidget(self.frmSP, 0, 0, 1, 2)

      layoutAllInp.addWidget(self.lblID, 1, 0, 1, 1)
      layoutAllInp.addWidget(self.edtID, 1, 1, 1, 1)
      for i in range(12):
         layoutAllInp.addWidget(self.prfxList[i], i + 2, 0, 1, 2)
         layoutAllInp.addWidget(self.edtList[i], i + 2, 1, 1, 2)
      frmAllInputs.setLayout(layoutAllInp)

      self.btnAccept = QPushButton(self.tr("Done"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.connect(self.btnAccept, SIGNAL(CLICKED), self.verifyUserInput)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(HLINE())
      layout.addWidget(frmBackupType)
      layout.addWidget(frmAllInputs)
      layout.addWidget(buttonBox)
      self.setLayout(layout)


      self.setWindowTitle(self.tr('Restore Single-Sheet Backup'))
      self.setMinimumWidth(500)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.changeType(self.backupTypeButtonGroup.checkedId())


   #############################################################################
   def changeType(self, sel):
      #            |-- X --| |-- Y --| |-- F --|
      if sel == self.backupTypeButtonGroup.id(self.version0Button):
         visList = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
      elif sel == self.backupTypeButtonGroup.id(self.version135aButton) or \
           sel == self.backupTypeButtonGroup.id(self.version135aSPButton):
         visList = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
      elif sel == self.backupTypeButtonGroup.id(self.version135cButton) or \
           sel == self.backupTypeButtonGroup.id(self.version135cSPButton):
         visList = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0]
      else:
         LOGERROR('What the heck backup type is selected?  %d', sel)
         return

      self.frmSP.setVisible(sel == self.backupTypeButtonGroup.id(self.version135aSPButton) or \
                            sel == self.backupTypeButtonGroup.id(self.version135cSPButton))
      for i in range(12):
         self.prfxList[i].setVisible(visList[i] == 1)
         self.edtList[ i].setVisible(visList[i] == 1)



   #############################################################################
   def destroyFragData(self):
      for line in self.fragData:
         if not isinstance(line, basestring):
            # It's an SBD Object.  Destroy it.
            line.destroy()

   #############################################################################
   def isSecurePrintID(self):
      return hex_to_int(str(self.edtID.text()[:2])) > 127

   #############################################################################
   def verifyUserInput(self):
      self.fragData = []
      nError = 0
      rawBin = None

      sel = self.backupTypeButtonGroup.checkedId()
      rng = [-1]
      if   sel == self.backupTypeButtonGroup.id(self.version0Button):
         rng = range(8)
      elif sel == self.backupTypeButtonGroup.id(self.version135aButton) or \
           sel == self.backupTypeButtonGroup.id(self.version135aSPButton):
         rng = range(8, 12)
      elif sel == self.backupTypeButtonGroup.id(self.version135cButton) or \
           sel == self.backupTypeButtonGroup.id(self.version135cSPButton):
         rng = range(8, 10)


      if sel == self.backupTypeButtonGroup.id(self.version135aSPButton) or \
         sel == self.backupTypeButtonGroup.id(self.version135cSPButton):
         # Prepare the key mask parameters
         SECPRINT = HardcodedKeyMaskParams()
         securePrintCode = str(self.editSecurePrint.text()).strip()
         if not checkSecurePrintCode(self, SECPRINT, securePrintCode):
            return
      elif self.isSecurePrintID():
            QMessageBox.critical(self, 'Bad Encryption Code', self.tr(
               'The ID field indicates that this is a SecurePrint™ '
               'Backup Type. You have either entered the ID incorrectly or '
               'have chosen an incorrect Backup Type.'), QMessageBox.Ok)
            return
      for i in rng:
         hasError = False
         try:
            rawEntry = str(self.edtList[i].text())
            rawBin, err = readSixteenEasyBytes(rawEntry.replace(' ', ''))
            if err == 'Error_2+':
               hasError = True
            elif err == 'Fixed_1':
               nError += 1
         except KeyError:
            hasError = True

         if hasError:
            reply = QMessageBox.critical(self, self.tr('Verify Wallet ID'), self.tr(
               'There is an error in the data you entered that could not be '
               'fixed automatically.  Please double-check that you entered the '
               'text exactly as it appears on the wallet-backup page. <br><br> '
               'The error occured on the "%1" line.').arg(str(self.prfxList[i].text())), QMessageBox.Ok)
            LOGERROR('Error in wallet restore field')
            self.prfxList[i].setText('<font color="red">' + str(self.prfxList[i].text()) + '</font>')
            self.destroyFragData()
            return

         self.fragData.append(SecureBinaryData(rawBin))
         rawBin = None


      idLine = str(self.edtID.text()).replace(' ', '')
      self.fragData.insert(0, hex_to_binary(idLine))

      M, fnum, wltID, doMask, fid = ReadFragIDLineBin(self.fragData[0])

      reply = QMessageBox.question(self, self.tr('Verify Fragment ID'), self.tr(
         'The data you entered is for fragment: '
         '<br><br> <font color="%1" size=3><b>%2</b></font>  <br><br> '
         'Does this ID match the "Fragment:" field displayed on your backup? '
         'If not, click "No" and re-enter the fragment data.').arg(htmlColor('TextBlue'), fid), QMessageBox.Yes | QMessageBox.No)

      if reply == QMessageBox.Yes:
         self.accept()



################################################################################
def verifyRecoveryTestID(parent, computedWltID, expectedWltID=None):

   if expectedWltID == None:
      # Testing an arbitrary paper backup
      yesno = QMessageBox.question(parent, parent.tr('Recovery Test'), parent.tr(
         'From the data you entered, Armory calculated the following '
         'wallet ID: <font color="blue"><b>%1</b></font> '
         '<br><br>'
         'Does this match the wallet ID on the backup you are '
         'testing?').arg(computedWltID), QMessageBox.Yes | QMessageBox.No)

      if yesno == QMessageBox.No:
         QMessageBox.critical(parent, parent.tr('Bad Backup!'), parent.tr(
            'If this is your only backup and you are sure that you entered '
            'the data correctly, then it is <b>highly recommended you stop using '
            'this wallet!</b>  If this wallet currently holds any funds, '
            'you should move the funds to a wallet that <u>does</u> '
            'have a working backup. '
            '<br><br> <br><br>'
            'Wallet ID of the data you entered: %1 <br>').arg(computedWltID), \
            QMessageBox.Ok)
      elif yesno == QMessageBox.Yes:
         MsgBoxCustom(MSGBOX.Good, parent.tr('Backup is Good!'), parent.tr(
            '<b>Your backup works!</b> '
            '<br><br>'
            'The wallet ID is computed from a combination of the root '
            'private key, the "chaincode" and the first address derived '
            'from those two pieces of data.  A matching wallet ID '
            'guarantees it will produce the same chain of addresses as '
            'the original.'))
   else:  # an expected wallet ID was supplied
      if not computedWltID == expectedWltID:
         QMessageBox.critical(parent, parent.tr('Bad Backup!'), parent.tr(
            'If you are sure that you entered the backup information '
            'correctly, then it is <b>highly recommended you stop using '
            'this wallet!</b>  If this wallet currently holds any funds, '
            'you should move the funds to a wallet that <u>does</u> '
            'have a working backup.'
            '<br><br>'
            'Computed wallet ID: %1 <br>'
            'Expected wallet ID: %2 <br><br>'
            'Is it possible that you loaded a different backup than the '
            'one you just made?').arg(computedWltID, 'expectedWltID'), \
            QMessageBox.Ok)
      else:
         MsgBoxCustom(MSGBOX.Good, parent.tr('Backup is Good!'), parent.tr(
            'Your backup works! '
            '<br><br> '
            'The wallet ID computed from the data you entered matches '
            'the expected ID.  This confirms that the backup produces '
            'the same sequence of private keys as the original wallet! '
            '<br><br> '
            'Computed wallet ID: %1 <br> '
            'Expected wallet ID: %2 <br> '
            '<br>').arg(computedWltID, expectedWltID ))

################################################################################
class DlgReplaceWallet(ArmoryDialog):

   #############################################################################
   def __init__(self, WalletID, parent, main):
      super(DlgReplaceWallet, self).__init__(parent, main)

      lblDesc = QLabel(self.tr(
                       '<b>You already have this wallet loaded!</b><br>'
                       'You can choose to:<br>'
                       '- Cancel wallet restore operation<br>'
                       '- Set new password and fix any errors<br>'
                       '- Overwrite old wallet (delete comments & labels)<br>'))

      self.WalletID = WalletID
      self.main = main
      self.Meta = None
      self.output = 0

      self.wltPath = main.walletMap[WalletID].walletPath

      self.btnAbort = QPushButton(self.tr('Cancel'))
      self.btnReplace = QPushButton(self.tr('Overwrite'))
      self.btnSaveMeta = QPushButton(self.tr('Merge'))

      self.connect(self.btnAbort, SIGNAL('clicked()'), self.reject)
      self.connect(self.btnReplace, SIGNAL('clicked()'), self.Replace)
      self.connect(self.btnSaveMeta, SIGNAL('clicked()'), self.SaveMeta)

      layoutDlg = QGridLayout()

      layoutDlg.addWidget(lblDesc,          0, 0, 4, 4)
      layoutDlg.addWidget(self.btnAbort,    4, 0, 1, 1)
      layoutDlg.addWidget(self.btnSaveMeta, 4, 1, 1, 1)
      layoutDlg.addWidget(self.btnReplace,  4, 2, 1, 1)

      self.setLayout(layoutDlg)
      self.setWindowTitle('Wallet already exists')

   #########
   def Replace(self):
      self.main.removeWalletFromApplication(self.WalletID)

      datestr = RightNowStr('%Y-%m-%d-%H%M')
      homedir = os.path.dirname(self.wltPath)

      oldpath = os.path.join(homedir, self.WalletID, datestr)
      try:
         if not os.path.exists(oldpath):
            os.makedirs(oldpath)
      except:
         LOGEXCEPT('Cannot create new folder in dataDir! Missing credentials?')
         self.reject()
         return

      oldname = os.path.basename(self.wltPath)
      self.newname = os.path.join(oldpath, '%s_old.wallet' % (oldname[0:-7]))

      os.rename(self.wltPath, self.newname)

      backup = '%s_backup.wallet' % (self.wltPath[0:-7])
      if os.path.exists(backup):
         os.remove(backup)

      self.output =1
      self.accept()

   #########
   def SaveMeta(self):
      from armoryengine.PyBtcWalletRecovery import PyBtcWalletRecovery

      metaProgress = DlgProgress(self, self.main, Title=self.tr('Ripping Meta Data'))
      getMeta = PyBtcWalletRecovery()
      self.Meta = metaProgress.exec_(getMeta.ProcessWallet,
                                     WalletPath=self.wltPath,
                                     Mode=RECOVERMODE.Meta,
                                     Progress=metaProgress.UpdateText)
      self.Replace()


###############################################################################
class DlgWltRecoverWallet(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgWltRecoverWallet, self).__init__(parent, main)

      self.edtWalletPath = QLineEdit()
      self.edtWalletPath.setFont(GETFONT('Fixed', 9))
      edtW,edtH = tightSizeNChar(self.edtWalletPath, 50)
      self.edtWalletPath.setMinimumWidth(edtW)
      self.btnWalletPath = QPushButton(self.tr('Browse File System'))

      self.connect(self.btnWalletPath, SIGNAL('clicked()'), self.selectFile)

      lblDesc = QRichLabel(self.tr(
         '<b>Wallet Recovery Tool: '
         '</b><br>'
         'This tool will recover data from damaged or inconsistent '
         'wallets.  Specify a wallet file and Armory will analyze the '
         'wallet and fix any errors with it. '
         '<br><br>'
         '<font color="%1">If any problems are found with the specified '
         'wallet, Armory will provide explanation and instructions to '
         'transition to a new wallet.').arg(htmlColor('TextWarn')))
      lblDesc.setScaledContents(True)

      lblWalletPath = QRichLabel(self.tr('Wallet Path:'))

      self.selectedWltID = None

      def doWltSelect():
         dlg = DlgWalletSelect(self, self.main, self.tr('Select Wallet...'), '')
         if dlg.exec_():
            self.selectedWltID = dlg.selectedID
            wlt = self.parent.walletMap[dlg.selectedID]
            self.edtWalletPath.setText(wlt.walletPath)

      self.btnWltSelect = QPushButton(self.tr("Select Loaded Wallet"))
      self.connect(self.btnWltSelect, SIGNAL(CLICKED), doWltSelect)

      layoutMgmt = QGridLayout()
      wltSltQF = QFrame()
      wltSltQF.setFrameStyle(STYLE_SUNKEN)

      layoutWltSelect = QGridLayout()
      layoutWltSelect.addWidget(lblWalletPath,      0,0, 1, 1)
      layoutWltSelect.addWidget(self.edtWalletPath, 0,1, 1, 3)
      layoutWltSelect.addWidget(self.btnWltSelect,  1,0, 1, 2)
      layoutWltSelect.addWidget(self.btnWalletPath, 1,2, 1, 2)
      layoutWltSelect.setColumnStretch(0, 0)
      layoutWltSelect.setColumnStretch(1, 1)
      layoutWltSelect.setColumnStretch(2, 1)
      layoutWltSelect.setColumnStretch(3, 0)

      wltSltQF.setLayout(layoutWltSelect)

      layoutMgmt.addWidget(makeHorizFrame([lblDesc], STYLE_SUNKEN), 0,0, 2,4)
      layoutMgmt.addWidget(wltSltQF, 2, 0, 3, 4)

      self.rdbtnStripped = QRadioButton('', parent=self)
      self.connect(self.rdbtnStripped, SIGNAL('event()'), self.rdClicked)
      lblStripped = QLabel(self.tr('<b>Stripped Recovery</b><br>Only attempts to \
                            recover the wallet\'s rootkey and chaincode'))
      layout_StrippedH = QGridLayout()
      layout_StrippedH.addWidget(self.rdbtnStripped, 0, 0, 1, 1)
      layout_StrippedH.addWidget(lblStripped, 0, 1, 2, 19)

      self.rdbtnBare = QRadioButton('')
      lblBare = QLabel(self.tr('<b>Bare Recovery</b><br>Attempts to recover all private key related data'))
      layout_BareH = QGridLayout()
      layout_BareH.addWidget(self.rdbtnBare, 0, 0, 1, 1)
      layout_BareH.addWidget(lblBare, 0, 1, 2, 19)

      self.rdbtnFull = QRadioButton('')
      self.rdbtnFull.setChecked(True)
      lblFull = QLabel(self.tr('<b>Full Recovery</b><br>Attempts to recover as much data as possible'))
      layout_FullH = QGridLayout()
      layout_FullH.addWidget(self.rdbtnFull, 0, 0, 1, 1)
      layout_FullH.addWidget(lblFull, 0, 1, 2, 19)

      self.rdbtnCheck = QRadioButton('')
      lblCheck = QLabel(self.tr('<b>Consistency Check</b><br>Checks wallet consistency. Works with both full and watch only<br> wallets.'
                         ' Unlocking of encrypted wallets is not mandatory'))
      layout_CheckH = QGridLayout()
      layout_CheckH.addWidget(self.rdbtnCheck, 0, 0, 1, 1)
      layout_CheckH.addWidget(lblCheck, 0, 1, 3, 19)


      layoutMode = QGridLayout()
      layoutMode.addLayout(layout_StrippedH, 0, 0, 2, 4)
      layoutMode.addLayout(layout_BareH, 2, 0, 2, 4)
      layoutMode.addLayout(layout_FullH, 4, 0, 2, 4)
      layoutMode.addLayout(layout_CheckH, 6, 0, 3, 4)


      #self.rdnGroup = QButtonGroup()
      #self.rdnGroup.addButton(self.rdbtnStripped)
      #self.rdnGroup.addButton(self.rdbtnBare)
      #self.rdnGroup.addButton(self.rdbtnFull)
      #self.rdnGroup.addButton(self.rdbtnCheck)


      layoutMgmt.addLayout(layoutMode, 5, 0, 9, 4)
      """
      wltModeQF = QFrame()
      wltModeQF.setFrameStyle(STYLE_SUNKEN)
      wltModeQF.setLayout(layoutMode)

      layoutMgmt.addWidget(wltModeQF, 5, 0, 9, 4)
      wltModeQF.setVisible(False)


      btnShowAllOpts = QLabelButton(self.tr("All Recovery Options>>>"))
      frmBtn = makeHorizFrame(['Stretch', btnShowAllOpts, 'Stretch'], STYLE_SUNKEN)
      layoutMgmt.addWidget(frmBtn, 5, 0, 9, 4)

      def expandOpts():
         wltModeQF.setVisible(True)
         btnShowAllOpts.setVisible(False)
      self.connect(btnShowAllOpts, SIGNAL('clicked()'), expandOpts)

      if not self.main.usermode==USERMODE.Expert:
         frmBtn.setVisible(False)
      """

      self.btnRecover = QPushButton(self.tr('Recover'))
      self.btnCancel  = QPushButton(self.tr('Cancel'))
      layout_btnH = QHBoxLayout()
      layout_btnH.addWidget(self.btnRecover, 1)
      layout_btnH.addWidget(self.btnCancel, 1)

      def updateBtn(qstr):
         if os.path.exists(unicode(qstr).strip()):
            self.btnRecover.setEnabled(True)
            self.btnRecover.setToolTip('')
         else:
            self.btnRecover.setEnabled(False)
            self.btnRecover.setToolTip(self.tr('The entered path does not exist'))

      updateBtn('')
      self.connect(self.edtWalletPath, SIGNAL('textChanged(QString)'), updateBtn)


      layoutMgmt.addLayout(layout_btnH, 14, 1, 1, 2)

      self.connect(self.btnRecover, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel , SIGNAL('clicked()'), self.reject)

      self.setLayout(layoutMgmt)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.setWindowTitle(self.tr('Wallet Recovery Tool'))
      self.setMinimumWidth(550)

   def rdClicked(self):
      # TODO:  Why does this do nohting?  Was it a stub that was forgotten?
      LOGINFO("clicked")

   def promptWalletRecovery(self):
      """
      Prompts the user with a window asking for wallet path and recovery mode.
      Proceeds to Recover the wallet. Prompt for password if the wallet is locked
      """
      if self.exec_():
         path = unicode(self.edtWalletPath.text())
         mode = RECOVERMODE.Bare
         if self.rdbtnStripped.isChecked():
            mode = RECOVERMODE.Stripped
         elif self.rdbtnFull.isChecked():
            mode = RECOVERMODE.Full
         elif self.rdbtnCheck.isChecked():
            mode = RECOVERMODE.Check

         if mode==RECOVERMODE.Full and self.selectedWltID:
            # Funnel all standard, full recovery operations through the
            # inconsistent-wallet-dialog.
            wlt = self.main.walletMap[self.selectedWltID]
            dlgRecoveryUI = DlgCorruptWallet(wlt, [], self.main, self, False)
            dlgRecoveryUI.exec_(dlgRecoveryUI.doFixWallets())
         else:
            # This is goatpig's original behavior - preserved for any
            # non-loaded wallets or non-full recovery operations.
            if self.selectedWltID:
               wlt = self.main.walletMap[self.selectedWltID]
            else:
               wlt = path

            dlgRecoveryUI = DlgCorruptWallet(wlt, [], self.main, self, False)
            dlgRecoveryUI.exec_(dlgRecoveryUI.ProcessWallet(mode))
      else:
         return False

   def selectFile(self):
      # Had to reimplement the path selection here, because the way this was
      # implemented doesn't let me access self.main.getFileLoad
      ftypes = self.tr('Wallet files (*.wallet);; All files (*)')
      if not OS_MACOSX:
         pathSelect = unicode(QFileDialog.getOpenFileName(self, \
                                 self.tr('Recover Wallet'), \
                                 ARMORY_HOME_DIR, \
                                 ftypes))
      else:
         pathSelect = unicode(QFileDialog.getOpenFileName(self, \
                                 self.tr('Recover Wallet'), \
                                 ARMORY_HOME_DIR, \
                                 ftypes, \
                                 options=QFileDialog.DontUseNativeDialog))

      self.edtWalletPath.setText(pathSelect)


###############################################################################
class DlgProgress(ArmoryDialog):
   """
   Progress bar dialog. The dialog is guaranteed to be created from the main
   thread.

   The dialog is modal, meaning all other windows are barred from user
   interaction as long as this dialog is within its message loop.
   The message loop is entered either through exec_(side_thread), which will
   which will lock the main threa and the caller thread, and join on the
   side thread

   The dialog reject() signal is overloaded to render it useless. The dialog
   cannot be killed through regular means. To kill the Dialog, call Kill()
   or end the side thread. Either will release the main thread. The caller
   will still join on the side thread if you only call Kill()

   To make a progress dialog that can be killed by the user (before the process
   is complete), pass a string to Interrupt. It will add a push button with
   that text, that will kill the progress dialog on click. The caller will
   still be joining on the side thread.

   Passing a string to Title will draw a title.
   Passing an integer to HBar will draw a progress bar with a Max value set to
   that integer. It can be updated through UpdateHBar(int)
   Passing a string TProgress will draw a label with that string. It can be
   updated through UpdateText(str)
   """
   def __init__(self, parent=None, main=None, Interrupt=None, HBar=None,
                Title=None, TProgress=None):

      self.running = 1
      self.Done = 0
      self.status = 0
      self.main = main
      self.parent = parent
      self.Interrupt = Interrupt
      self.HBar = HBar
      self.Title = Title
      self.TProgress = None
      self.procressDone = False

      self.lock = threading.Lock()
      self.condVar = threading.Condition(self.lock)

      self.btnStop = None

      if main is not None:
         main.emit(SIGNAL('initTrigger'), self)
      else: return

      while self.status == 0:
         time.sleep(0.01)

      self.connectDlg()

   def connectDlg(self):
      self.connect(self, SIGNAL('Update'), self.UpdateDlg)
      self.connect(self, SIGNAL('PromptPassphrase'), self.PromptPassphrase)
      self.connect(self, SIGNAL('Exit'), self.Exit)

   def UpdateDlg(self, text=None, HBar=None, Title=None):
      if text is not None: self.lblDesc.setText(text)
      if HBar is not None: self.hbarProgress.setValue(HBar)

      if self.Done == 1:
         if self.btnStop is not None:
            self.btnStop.setText(self.tr('Close'))
         else: self.Kill()

   def UpdateText(self, updatedText, endProgress=False):
      self.Done = endProgress
      if self.main is None: return self.running

      self.emit(SIGNAL('Update'), updatedText, None)
      return self.running

   def UpdateHBar(self, value, maxVal, endProgress=False):
      self.Done = endProgress
      if self.main is None: return self.running

      progressVal = 100*value/maxVal

      self.emit(SIGNAL('Update'), None, self.HBarCount*100 +progressVal)
      if progressVal >= 100:
         self.HBarCount = self.HBarCount + 1
      return self.running

   def AskUnlock(self, wll):
      self.condVar.acquire()
      self.emit(SIGNAL('PromptPassphrase'), wll)
      self.condVar.wait()
      self.condVar.release()

      return self.Passphrase

   def PromptPassphrase(self, wll):
      self.condVar.acquire()
      dlg = DlgUnlockWallet(wll, self, self.main, self.tr("Enter Passphrase"),
                            returnPassphrase=True)

      self.Passphrase = None
      self.GotPassphrase = 0
      if dlg.exec_():
         #grab plain passphrase
         if dlg.Accepted == 1:
            self.Passphrase = dlg.securePassphrase.copy()
            dlg.securePassphrase.destroy()

      self.condVar.notify()
      self.condVar.release()

   def Kill(self):
      if self.main: self.emit(SIGNAL('Exit'))

   def Exit(self):
      self.running = 0
      self.done(0)

   def exec_(self, *args, **kwargs):
      '''
      If args[0] is a function, it will be called in exec_thread
      args[1:] is the argument list for that function
      will return the functions output in exec_thread.output, which is then
      returned by exec_
      '''
      exec_thread = PyBackgroundThread(self.exec_async, *args, **kwargs)
      exec_thread.start()

      self.main.emit(SIGNAL('execTrigger'), self)
      exec_thread.join()

      if exec_thread.didThrowError():
         exec_thread.raiseLastError()
      else:
         return exec_thread.output

   def exec_async(self, *args, **kwargs):
      if len(args) > 0 and hasattr(args[0], '__call__'):
         func = args[0]

         if not 'Progress' in kwargs:
            if self.HBar > 0: kwargs['Progress'] = self.UpdateHBar
            else: kwargs['Progress'] = self.UpdateText

         try:
            rt = func(*args[1:], **kwargs)
         except Exception as e:
            self.Kill()
            raise e
            pass

         self.Kill()

         return rt

   def reject(self):
      return

   def setup(self, parent=None):
      super(DlgProgress, self).__init__(parent, self.main)

      css = """
            QDialog{ border:1px solid rgb(0, 0, 0); }
            QProgressBar{ text-align: center; font-weight: bold; }
            """
      self.setStyleSheet(css)

      layoutMgmt = QVBoxLayout()
      self.lblDesc = QLabel('')

      if self.Title is not None:
         if not self.HBar:
            self.lblTitle = QLabel(self.Title)
            self.lblTitle.setAlignment(Qt.AlignCenter)
            layoutMgmt.addWidget(self.lblTitle)


      if self.HBar is not None:
         self.hbarProgress = QProgressBar(self)
         self.hbarProgress.setMaximum(self.HBar*100)
         self.hbarProgress.setMinimum(0)
         self.hbarProgress.setValue(0)
         self.hbarProgress.setMinimumWidth(250)
         layoutMgmt.addWidget(self.hbarProgress)
         self.HBarCount = 0

         if self.HBar:
            self.hbarProgress.setFormat("%s: %s%%" % (self.Title, "%p"))
      else:
         layoutMgmt.addWidget(self.lblDesc)

      if self.Interrupt is not None:
         self.btnStop = QPushButton(self.Interrupt)
         self.connect(self.btnStop, SIGNAL('clicked()'), self.Kill)

         layout_btnG = QGridLayout()
         layout_btnG.setColumnStretch(0, 1)
         layout_btnG.setColumnStretch(4, 1)
         layout_btnG.addWidget(self.btnStop, 0, 1, 1, 3)
         layoutMgmt.addLayout(layout_btnG)

      self.minimize = None
      self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
      self.setModal(True)

      self.setLayout(layoutMgmt)
      self.adjustSize()

      btmRight = self.parent.rect().bottomRight()
      topLeft = self.parent.rect().topLeft()
      globalbtmRight = self.parent.mapToGlobal((btmRight+topLeft)/2)

      self.move(globalbtmRight - QPoint(self.width()/2, self.height()))
      if self.Title:
         self.setWindowTitle(self.Title)
      else:
         self.setWindowTitle(self.tr('Progress Bar'))

      self.hide()


#################################################################################
class DlgCorruptWallet(DlgProgress):
   def __init__(self, wallet, status, main=None, parent=None, alreadyFailed=True):
      super(DlgProgress, self).__init__(parent, main)

      self.connectDlg()

      self.main = main
      self.walletList = []
      self.logDirs = []

      self.running = 1
      self.status = 1
      self.isFixing = False
      self.needToSubmitLogs = False
      self.checkMode = RECOVERMODE.NotSet

      self.lock = threading.Lock()
      self.condVar = threading.Condition(self.lock)

      mainLayout = QVBoxLayout()

      self.connect(self, SIGNAL('UCF'), self.UCF)
      self.connect(self, SIGNAL('Show'), self.show)
      self.connect(self, SIGNAL('Exec'), self.run_lock)
      self.connect(self, SIGNAL('SNP'), self.setNewProgress)
      self.connect(self, SIGNAL('LFW'), self.LFW)
      self.connect(self, SIGNAL('SRD'), self.SRD)

      if alreadyFailed:
         titleStr = self.tr('Wallet Consistency Check Failed!')
      else:
         titleStr = self.tr('Perform Wallet Consistency Check')

      lblDescr = QRichLabel(self.tr(
         '<font color="%1" size=5><b><u>%2</u></b></font> '
         '<br><br>'
         'Armory software now detects and prevents certain kinds of '
         'hardware errors that could lead to problems with your wallet. '
         '<br>').arg(htmlColor('TextWarn'), titleStr))

      lblDescr.setAlignment(Qt.AlignCenter)


      if alreadyFailed:
         self.lblFirstMsg = QRichLabel(self.tr(
            'Armory has detected that wallet file <b>Wallet "%1" (%2)</b> '
            'is inconsistent and should be further analyzed to ensure that your '
            'funds are protected. '
            '<br><br>'
            '<font color="%3">This error will pop up every time you start '
            'Armory until the wallet has been analyzed and fixed!</font>').arg(wallet.labelName, wallet.uniqueIDB58, htmlColor('TextWarn')))
      elif isinstance(wallet, PyBtcWallet):
         self.lblFirstMsg = QRichLabel(self.tr(
            'Armory will perform a consistency check on <b>Wallet "%1" (%2)</b> '
            'and determine if any further action is required to keep your funds '
            'protected.  This check is normally performed on startup on all '
            'your wallets, but you can click below to force another '
            'check.').arg(wallet.labelName, wallet.uniqueIDB58))
      else:
         self.lblFirstMsg = QRichLabel('')

      self.QDS = QDialog()
      self.lblStatus = QLabel('')
      self.addStatus(wallet, status)
      self.QDSlo = QVBoxLayout()
      self.QDS.setLayout(self.QDSlo)

      self.QDSlo.addWidget(self.lblFirstMsg)
      self.QDSlo.addWidget(self.lblStatus)

      self.lblStatus.setVisible(False)
      self.lblFirstMsg.setVisible(True)

      saStatus = QScrollArea()
      saStatus.setWidgetResizable(True)
      saStatus.setWidget(self.QDS)
      saStatus.setMinimumHeight(250)
      saStatus.setMinimumWidth(500)


      layoutButtons = QGridLayout()
      layoutButtons.setColumnStretch(0, 1)
      layoutButtons.setColumnStretch(4, 1)
      self.btnClose = QPushButton(self.tr('Hide'))
      self.btnFixWallets = QPushButton(self.tr('Run Analysis and Recovery Tool'))
      self.btnFixWallets.setDisabled(True)
      self.connect(self.btnFixWallets, SIGNAL('clicked()'), self.doFixWallets)
      self.connect(self.btnClose, SIGNAL('clicked()'), self.hide)
      layoutButtons.addWidget(self.btnClose, 0, 1, 1, 1)
      layoutButtons.addWidget(self.btnFixWallets, 0, 2, 1, 1)

      self.lblDescr2 = QRichLabel('')
      self.lblDescr2.setAlignment(Qt.AlignCenter)

      self.lblFixRdy = QRichLabel(self.tr(
         '<u>Your wallets will be ready to fix once the scan is over</u><br> '
         'You can hide this window until then<br>'))

      self.lblFixRdy.setAlignment(Qt.AlignCenter)

      self.frmBottomMsg = makeVertFrame(['Space(5)',
                                         HLINE(),
                                         self.lblDescr2,
                                         self.lblFixRdy,
                                         HLINE()])

      self.frmBottomMsg.setVisible(False)


      mainLayout.addWidget(lblDescr)
      mainLayout.addWidget(saStatus)
      mainLayout.addWidget(self.frmBottomMsg)
      mainLayout.addLayout(layoutButtons)

      self.setLayout(mainLayout)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.setWindowTitle(self.tr('Wallet Error'))

   def addStatus(self, wallet, status):
      if wallet:
         strStatus = ''.join(status) + str(self.lblStatus.text())
         self.lblStatus.setText(strStatus)

         self.walletList.append(wallet)

   def show(self):
      super(DlgCorruptWallet, self).show()
      self.activateWindow()

   def run_lock(self):
      self.btnClose.setVisible(False)
      self.hide()
      super(DlgProgress, self).exec_()
      self.walletList = None

   def UpdateCanFix(self, conditions, canFix=False):
      self.emit(SIGNAL('UCF'), conditions, canFix)

   def UCF(self, conditions, canFix=False):
      self.lblFixRdy.setText('')
      if canFix:
         self.btnFixWallets.setEnabled(True)
         self.btnClose.setText(self.tr('Close'))
         self.btnClose.setVisible(False)
         self.connect(self.btnClose, SIGNAL('clicked()'), self.reject)
         self.hide()

   def doFixWallets(self):
      self.lblFixRdy.hide()
      self.adjustSize()

      self.lblStatus.setVisible(True)
      self.lblFirstMsg.setVisible(False)
      self.frmBottomMsg.setVisible(False)

      from armoryengine.PyBtcWalletRecovery import FixWalletList
      self.btnClose.setDisabled(True)
      self.btnFixWallets.setDisabled(True)
      self.isFixing = True

      self.lblStatus.hide()
      self.QDSlo.removeWidget(self.lblStatus)

      for wlt in self.walletList:
         self.main.removeWalletFromApplication(wlt.uniqueIDB58)

      FixWalletList(self.walletList, self, Progress=self.UpdateText, async=True)
      self.adjustSize()

   def ProcessWallet(self, mode=RECOVERMODE.Full):
      '''
      Serves as the entry point for non processing wallets that arent loaded
      or fully processed. Only takes 1 wallet at a time
      '''
      if len(self.walletList) > 0:
         wlt = None
         wltPath = ''

         if isinstance(self.walletList[0], str) or \
            isinstance(self.walletList[0], unicode):
            wltPath = self.walletList[0]
         else:
            wlt = self.walletList[0]

      self.lblDesc = QLabel('')
      self.QDSlo.addWidget(self.lblDesc)

      self.lblFixRdy.hide()
      self.adjustSize()

      self.frmBottomMsg.setVisible(False)
      self.lblStatus.setVisible(True)
      self.lblFirstMsg.setVisible(False)

      from armoryengine.PyBtcWalletRecovery import ParseWallet
      self.btnClose.setDisabled(True)
      self.btnFixWallets.setDisabled(True)
      self.isFixing = True

      self.checkMode = mode
      ParseWallet(wltPath, wlt, mode, self,
                             Progress=self.UpdateText, async=True)

   def UpdateDlg(self, text=None, HBar=None, Title=None):
      if text is not None: self.lblDesc.setText(text)
      self.adjustSize()

   def accept(self):
      self.main.emit(SIGNAL('checkForNegImports'))
      super(DlgCorruptWallet, self).accept()

   def reject(self):
      if not self.isFixing:
         super(DlgProgress, self).reject()
         self.main.emit(SIGNAL('checkForNegImports'))

   def sigSetNewProgress(self, status):
      self.emit(SIGNAL('SNP'), status)

   def setNewProgress(self, status):
      self.lblDesc = QLabel('')
      self.QDSlo.addWidget(self.lblDesc)
      #self.QDS.adjustSize()
      status[0] = 1

   def setRecoveryDone(self, badWallets, goodWallets, fixedWallets, fixers):
      self.emit(SIGNAL('SRD'), badWallets, goodWallets, fixedWallets, fixers)

   def SRD(self, badWallets, goodWallets, fixedWallets, fixerObjs):
      self.btnClose.setEnabled(True)
      self.btnClose.setVisible(True)
      self.btnClose.setText(self.tr('Continue'))
      self.btnFixWallets.setVisible(False)
      self.btnClose.disconnect(self, SIGNAL('clicked()'), self.hide)
      self.btnClose.connect(self, SIGNAL('clicked()'), self.accept)
      self.isFixing = False
      self.frmBottomMsg.setVisible(True)

      anyNegImports = False
      for fixer in fixerObjs:
         if len(fixer.negativeImports) > 0:
            anyNegImports = True
            break


      if len(badWallets) > 0:
         self.lblDescr2.setText(self.tr(
            '<font size=4 color="%1"><b>Failed to fix wallets!</b></font>').arg(htmlColor('TextWarn')))
         self.main.statusBar().showMessage('Failed to fix wallets!', 150000)
      elif len(goodWallets) == len(fixedWallets) and not anyNegImports:
         self.lblDescr2.setText(self.tr(
            '<font size=4 color="%1"><b>Wallet(s) consistent, nothing to '
            'fix.</b></font>', "", len(goodWallets)).arg(htmlColor("TextBlue")))
         self.main.statusBar().showMessage( \
            self.tr("Wallet(s) consistent!", "", len(goodWallets)) % \
            15000)
      elif len(fixedWallets) > 0 or anyNegImports:
         if self.checkMode != RECOVERMODE.Check:
            self.lblDescr2.setText(self.tr(
               '<font color="%1"><b> '
               '<font size=4><b><u>There may still be issues with your '
               'wallet!</u></b></font> '
               '<br>'
               'It is important that you send us the recovery logs '
               'and an email address so the Armory team can check for '
               'further risk to your funds!</b></font>').arg(htmlColor('TextWarn')))
            #self.main.statusBar().showMessage('Wallets fixed!', 15000)
         else:
            self.lblDescr2.setText(self.tr('<h2 style="color: red;"> \
                                    Consistency check failed! </h2>'))
      self.adjustSize()


   def loadFixedWallets(self, wallets):
      self.emit(SIGNAL('LFW'), wallets)

   def LFW(self, wallets):
      for wlt in wallets:
         newWallet = PyBtcWallet().readWalletFile(wlt)
         self.main.addWalletToApplication(newWallet, False)

      self.main.emit(SIGNAL('checkForkedImport'))


   # Decided that we can just add all the logic to
   #def checkForkedSubmitLogs(self):
      #forkedImports = []
      #for wlt in self.walletMap:
         #if self.walletMap[wlt].hasForkedImports:
            #dlgIWR = DlgInconsistentWltReport(self, self.main, self.logDirs)
            #if dlgIWR.exec_():
            #return
         #return


#################################################################################
class DlgFactoryReset(ArmoryDialog):
   def __init__(self, main=None, parent=None):
      super(DlgFactoryReset, self).__init__(parent, main)

      lblDescr = QRichLabel(self.tr(
         '<b><u>Armory Factory Reset</u></b> '
         '<br><br>'
         'It is <i>strongly</i> recommended that you make backups of your '
         'wallets before continuing, though <b>wallet files will never be '
         'intentionally deleted!</b>  All Armory '
         'wallet files, and the wallet.dat file used by Bitcoin Core/bitcoind '
         'should remain untouched in their current locations.  All Armory '
         'wallets will automatically be detected and loaded after the reset. '
         '<br><br>'
         'If you are not sure which option to pick, try the "lightest option" '
         'first, and see if your problems are resolved before trying the more '
         'extreme options.'))



      self.rdoSettings = QRadioButton()
      self.lblSettingsText = QRichLabel(self.tr(
         '<b>Delete settings and rescan (lightest option)</b>'))
      self.lblSettings = QRichLabel(self.tr(
         'Only delete the settings file and transient network data.  The '
         'databases built by Armory will be rescanned (about 5-45 minutes)'))

      self.rdoArmoryDB = QRadioButton()
      self.lblArmoryDBText = QRichLabel(self.tr('<b>Also delete databases and rebuild</b>'))
      self.lblArmoryDB = QRichLabel(self.tr(
         'Will delete settings, network data, and delete Armory\'s databases. The databases '
         'will be rebuilt and rescanned (45 min to 3 hours)'))

      self.rdoBitcoinDB = QRadioButton()
      self.lblBitcoinDBText = QRichLabel(self.tr('<b>Also re-download the blockchain (extreme)</b>'))
      self.lblBitcoinDB = QRichLabel(self.tr(
         'This will delete settings, network data, Armory\'s databases, '
         '<b>and</b> Bitcoin Core\'s databases.  Bitcoin Core will '
         'have to download the blockchain again. This can take 8-72 hours depending on your '
         'system\'s speed and connection.  Only use this if you '
         'suspect blockchain corruption, such as receiving StdOut/StdErr errors '
         'on the dashboard.'))


      self.chkSaveSettings = QCheckBox(self.tr('Do not delete settings files'))


      optFrames = []
      for rdo,txt,lbl in [ \
            [self.rdoSettings,  self.lblSettingsText,  self.lblSettings], \
            [self.rdoArmoryDB,  self.lblArmoryDBText,  self.lblArmoryDB], \
            [self.rdoBitcoinDB, self.lblBitcoinDBText, self.lblBitcoinDB]]:

         optLayout = QGridLayout()
         txt.setWordWrap(False)
         optLayout.addWidget(makeHorizFrame([rdo, txt, 'Stretch']))
         optLayout.addWidget(lbl, 1,0, 1,3)
         if len(optFrames)==2:
            # Add option to disable deleting settings, on most extreme option
            optLayout.addWidget(self.chkSaveSettings, 2,0, 1,3)
         optFrames.append(QFrame())
         optFrames[-1].setLayout(optLayout)
         optFrames[-1].setFrameStyle(STYLE_RAISED)


      self.rdoSettings.setChecked(True)

      btngrp = QButtonGroup(self)
      btngrp.addButton(self.rdoSettings)
      btngrp.addButton(self.rdoArmoryDB)
      btngrp.addButton(self.rdoBitcoinDB)

      frmDescr = makeHorizFrame([lblDescr], STYLE_SUNKEN)
      frmOptions = makeVertFrame(optFrames, STYLE_SUNKEN)

      self.btnOkay = QPushButton(self.tr('Continue'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnOkay, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      self.connect(self.btnOkay, SIGNAL(CLICKED), self.clickedOkay)
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.reject)

      layout = QVBoxLayout()
      layout.addWidget(frmDescr)
      layout.addWidget(frmOptions)
      layout.addWidget(buttonBox)

      self.setLayout(layout)
      self.setMinimumWidth(600)
      self.setWindowTitle(self.tr('Factory Reset'))
      self.setWindowIcon(QIcon(self.main.iconfile))



   ###
   def clickedOkay(self):


      if self.rdoSettings.isChecked():
         reply = QMessageBox.warning(self, self.tr('Confirmation'), self.tr(
            'You are about to delete your settings and force Armory to rescan '
            'its databases.  Are you sure you want to do this?'), \
            QMessageBox.Cancel | QMessageBox.Ok)

         if not reply==QMessageBox.Ok:
            self.reject()
            return

         touchFile( os.path.join(ARMORY_HOME_DIR, 'rescan.flag') )
         touchFile( os.path.join(ARMORY_HOME_DIR, 'clearmempool.flag'))
         touchFile( os.path.join(ARMORY_HOME_DIR, 'delsettings.flag'))
         self.accept()

      elif self.rdoArmoryDB.isChecked():
         reply = QMessageBox.warning(self, self.tr('Confirmation'), self.tr(
            'You are about to delete your settings and force Armory to delete '
            'and rebuild its databases.  Are you sure you want to do this?'), \
            QMessageBox.Cancel | QMessageBox.Ok)

         if not reply==QMessageBox.Ok:
            self.reject()
            return

         touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )
         touchFile( os.path.join(ARMORY_HOME_DIR, 'clearmempool.flag'))
         touchFile( os.path.join(ARMORY_HOME_DIR, 'delsettings.flag'))
         self.accept()

      elif self.rdoBitcoinDB.isChecked():
         msg = 'delete your settings and '

         if self.chkSaveSettings.isChecked():
            msg = self.tr(
               'You are about to delete <b>all</b> '
               'blockchain databases on your system.  The Bitcoin software will '
               'have to redownload all of the blockchain data over the peer-to-peer '
               'network again. This can take from 8 to 72 hours depending on '
               'your system\'s speed and connection.  <br><br><b>Are you absolutely '
               'sure you want to do this?</b>')
         else:
            msg = self.tr(
               'You are about to delete your settings and delete <b>all</b> '
               'blockchain databases on your system.  The Bitcoin software will '
               'have to redownload all of the blockchain data over the peer-to-peer '
               'network again. This can take from 8 to 72 hours depending on '
               'your system\'s speed and connection.  <br><br><b>Are you absolutely '
               'sure you want to do this?</b>')

         reply = QMessageBox.warning(self, self.tr('Confirmation'), msg, \
            QMessageBox.Cancel | QMessageBox.Yes)

         if not reply==QMessageBox.Yes:
            QMessageBox.warning(self, self.tr('Aborted'), self.tr(
                  'You canceled the factory reset operation.  No changes were '
                  'made.'), QMessageBox.Ok)
            self.reject()
            return


         if not self.main.settings.get('ManageSatoshi'):
            # Must have user shutdown Bitcoin sw now, and delete DBs now
            reply = MsgBoxCustom(MSGBOX.Warning, self.tr('Restart Armory'), self.tr(
               '<b>Bitcoin Core (or bitcoind) must be closed to do the reset!</b> '
               'Please close all Bitcoin software, <u><b>right now</b></u>, '
               'before clicking "Continue". '
               '<br><br>'
               'Armory will now close.  Please restart Bitcoin Core/bitcoind '
               'first and wait for it to finish synchronizing before restarting '
               'Armory.'), wCancel=True, yesStr="Continue")

            if not reply:
               QMessageBox.warning(self, self.tr('Aborted'), self.tr(
                  'You canceled the factory reset operation.  No changes were '
                  'made.'), QMessageBox.Ok)
               self.reject()
               return

            # Do the delete operation now
            deleteBitcoindDBs()
         else:
            reply = QMessageBox.warning(self, self.tr('Restart Armory'), self.tr(
               'Armory will now close to apply the requested changes.  Please '
               'restart it when you are ready to start the blockchain download '
               'again.'), QMessageBox.Ok)

            if not reply == QMessageBox.Ok:
               QMessageBox.warning(self, self.tr('Aborted'), self.tr(
                  'You canceled the factory reset operation.  No changes were '
                  'made.'), QMessageBox.Ok)
               self.reject()
               return

            touchFile( os.path.join(ARMORY_HOME_DIR, 'redownload.flag') )

         #  Always flag the rebuild, and del mempool and settings
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )
         touchFile( os.path.join(ARMORY_HOME_DIR, 'clearmempool.flag'))
         if not self.chkSaveSettings.isChecked():
            touchFile( os.path.join(ARMORY_HOME_DIR, 'delsettings.flag'))
         self.accept()


      QMessageBox.information(self, self.tr('Restart Armory'), self.tr(
         'Armory will now close so that the requested changes can '
         'be applied.'), QMessageBox.Ok)
      self.accept()


#################################################################################
class DlgForkedImports(ArmoryDialog):
   def __init__(self, walletList, main=None, parent=None):
      super(DlgForkedImports, self).__init__(parent, main)

      descr1 = self.tr('<h2 style="color: red; text-align: center;">Forked imported addresses have been \
      detected in your wallets!!!</h2>')

      descr2 = self.tr('The following wallets have forked imported addresses: <br><br><b>') + \
      '<br>'.join(walletList) + '</b>'

      descr3 = self.tr('When you fix a corrupted wallet, any damaged private keys will be off \
      the deterministic chain. It means these private keys cannot be recreated \
      by your paper backup. If such private keys are encountered, Armory saves \
      them as forked imported private keys after it fixes the relevant wallets.')

      descr4 = self.tr('<h1 style="color: orange;"> - Do not accept payments to these wallets anymore<br>\
      - Do not delete or overwrite these wallets. <br> \
      - Transfer all funds to a fresh and backed up wallet</h1>')

      lblDescr1 = QRichLabel(descr1)
      lblDescr2 = QRichLabel(descr2)
      lblDescr3 = QRichLabel(descr3)
      lblDescr4 = QRichLabel(descr4)

      layout2 = QVBoxLayout()
      layout2.addWidget(lblDescr2)
      frame2 = QFrame()
      frame2.setLayout(layout2)
      frame2.setFrameStyle(QFrame.StyledPanel)

      layout4 = QVBoxLayout()
      layout4.addWidget(lblDescr4)
      frame4 = QFrame()
      frame4.setLayout(layout4)
      frame4.setFrameStyle(QFrame.StyledPanel)


      self.btnOk = QPushButton('Ok')
      self.connect(self.btnOk, SIGNAL('clicked()'), self.accept)


      layout = QVBoxLayout()
      layout.addWidget(lblDescr1)
      layout.addWidget(frame2)
      layout.addWidget(lblDescr3)
      layout.addWidget(frame4)
      layout.addWidget(self.btnOk)


      self.setLayout(layout)
      self.setMinimumWidth(600)
      self.setWindowTitle(self.tr('Forked Imported Addresses'))
###


################################################################################
class DlgBroadcastBlindTx(ArmoryDialog):
   def __init__(self, main=None, parent=None):
      super(DlgBroadcastBlindTx, self).__init__(parent, main)

      self.pytx = None

      lblDescr = QRichLabel(self.tr(
         'Copy a raw, hex-encoded transaction below to have Armory '
         'broadcast it to the Bitcoin network.  This function is '
         'provided as a convenience to expert users, and carries '
         'no guarantees of usefulness. '
         '<br><br>'
         'Specifically, be aware of the following limitations of '
         'this broadcast function: '
         '<ul>'
         '<li>The transaction will be "broadcast" by sending it '
         'to the connected Bitcon Core instance which will '
         'forward it to the rest of the Bitcoin network. '
         'However, if the transaction is non-standard or '
         'does not satisfy standard fee rules, Bitcoin Core '
         '<u>will</u> drop it and it '
         'will never be seen by the Bitcoin network. '
         '</li>'
         '<li>There will be no feedback as to whether the '
         'transaction succeeded.  You will have to verify the '
         'success of this operation via other means. '
         'However, if the transaction sends '
         'funds directly to or from an address in one of your '
         'wallets, it will still generate a notification and show '
         'up in your transaction history for that wallet. '
         '</li>'
         '</ul>'))

      self.txtRawTx = QPlainTextEdit()
      self.txtRawTx.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(self.txtRawTx, 90)
      self.txtRawTx.setMinimumWidth(w)
      self.txtRawTx.setMinimumHeight(h*5)
      self.connect(self.txtRawTx, SIGNAL('textChanged()'), self.txChanged)

      lblTxInfo = QRichLabel(self.tr('Parsed Transaction:'))

      self.txtTxInfo = QPlainTextEdit()
      self.txtTxInfo.setFont(GETFONT('Fixed', 9))
      self.txtTxInfo.setMinimumWidth(w)
      self.txtTxInfo.setMinimumHeight(h*7)
      self.txtTxInfo.setReadOnly(True)

      self.lblInvalid = QRichLabel('')

      self.btnCancel = QPushButton(self.tr("Cancel"))
      self.btnBroad  = QPushButton(self.tr("Broadcast"))
      self.btnBroad.setEnabled(False)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      self.connect(self.btnBroad, SIGNAL('clicked()'), self.doBroadcast)
      frmButtons = makeHorizFrame(['Stretch', self.btnCancel, self.btnBroad])

      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(self.txtRawTx)
      layout.addWidget(lblTxInfo)
      layout.addWidget(self.txtTxInfo)
      layout.addWidget(self.lblInvalid)
      layout.addWidget(HLINE())
      layout.addWidget(frmButtons)

      self.setLayout(layout)
      self.setWindowTitle(self.tr("Broadcast Raw Transaction"))


   #############################################################################
   def txChanged(self):
      try:
         txt = str(self.txtRawTx.toPlainText()).strip()
         txt = ''.join(txt.split())  # removes all whitespace
         self.pytx = PyTx().unserialize(hex_to_binary(txt))
         self.txtTxInfo.setPlainText(self.pytx.toString())
         LOGINFO('Valid tx entered:')
         LOGINFO(self.pytx.toString())
         self.setReady(True)
      except:
         LOGEXCEPT('Failed to parse tx')
         self.setReady(False)
         self.pytx = None


   #############################################################################
   def setReady(self, isTrue):
      self.btnBroad.setEnabled(isTrue)
      self.lblInvalid.setText("")
      if not isTrue:
         self.txtTxInfo.setPlainText('')
         if len(str(self.txtRawTx.toPlainText()).strip()) > 0:
            self.lblInvalid.setText(self.tr('<font color="%1"><b>Raw transaction '
            'is invalid!</font></b>').arg(htmlColor('TextWarn')))


   #############################################################################
   def doBroadcast(self):
      txhash = self.pytx.getHash()
      self.main.NetworkingFactory.sendTx(self.pytx)

      time.sleep(0.5)
      msg = PyMessage('getdata')
      msg.payload.invList.append( [MSG_INV_TX, txhash] )
      self.main.NetworkingFactory.sendMessage(msg)

      hexhash = binary_to_hex(txhash, endOut=BIGENDIAN)
      if USE_TESTNET:
         linkToExplorer = 'https://blockexplorer.com/testnet/tx/%s' % hexhash
         dispToExplorer = 'https://blockexplorer.com/testnet/tx/%s...' % hexhash[:16]
      elif USE_REGTEST:
         linkToExplorer = ''
         dispToExplorer = ''
      else:
         linkToExplorer = 'https://blockchain.info/search/%s' % hexhash
         dispToExplorer = 'https://blockchain.info/search/%s...' % hexhash[:16]

      QMessageBox.information(self, self.tr("Broadcast!"), self.tr(
         'Your transaction was successfully sent to the local Bitcoin '
         'Core instance, though there is no guarantees that it was '
         'forwarded to the rest of the network.   On testnet, just about '
         'every valid transaction will successfully propagate.  On the '
         'main Bitcoin network, this will fail unless it was a standard '
         'transaction type. '
         'The transaction '
         'had the following hash: '
         '<br><br> '
         '%1 '
         '<br><br>'
         'You can check whether it was seen by other nodes on the network '
         'with the link below: '
         '<br><br>'
         '<a href="%2">%3</a>').arg(hexhash, linkToExplorer, dispToExplorer), QMessageBox.Ok)

      self.accept()

#################################################################################
class ArmorySplashScreen(QSplashScreen):
   def __init__(self, pixLogo):
      super(ArmorySplashScreen, self).__init__(pixLogo)

      css = """
            QProgressBar{ text-align: center; font-size: 8px; }
            """
      self.setStyleSheet(css)

      self.progressBar = QProgressBar(self)
      self.progressBar.setMaximum(100)
      self.progressBar.setMinimum(0)
      self.progressBar.setValue(0)
      self.progressBar.setMinimumWidth(self.width())
      self.progressBar.setMaximumHeight(10)
      self.progressBar.setFormat(self.tr("Loading: %1%").arg("%p" ))

   def updateProgress(self, val):
      self.progressBar.setValue(val)

#############################################################################
class DlgRegAndTest(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgRegAndTest, self).__init__(parent, main)

      self.btcClose = QPushButton("Close")
      self.connect(self.btcClose, SIGNAL(CLICKED), self.close)
      btnBox = makeHorizFrame([STRETCH, self.btcClose])

      lblError = QRichLabel(self.tr('Error: You cannot run the Regression Test network and Bitcoin Test Network at the same time.'))

      dlgLayout = QVBoxLayout()
      frmBtn = makeHorizFrame([STRETCH, self.btcClose])
      frmAll = makeVertFrame([lblError, frmBtn])

      dlgLayout.addWidget(frmAll)
      self.setLayout(dlgLayout)
      self.setWindowTitle('Error')

   def close(self):
      self.main.abortLoad = True
      LOGERROR('User attempted to run regtest and testnet simultaneously')
      super(DlgRegAndTest, self).reject()

#############################################################################
class URLHandler(QObject):
   @pyqtSignature("QUrl")
   def handleURL(self, link):
      DlgBrowserWarn(link.toString()).exec_()

class DlgBrowserWarn(ArmoryDialog):
   def __init__(self, link, parent=None, main=None):
      super(DlgBrowserWarn, self).__init__(parent, main)

      self.link = link
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnCancel, SIGNAL(CLICKED), self.cancel)
      self.btnContinue = QPushButton("Continue")
      self.connect(self.btnContinue, SIGNAL(CLICKED), self.accept)
      btnBox = makeHorizFrame([STRETCH, self.btnCancel, self.btnContinue])

      lblWarn = QRichLabel(self.tr('Your default browser will now open and go to the following link: %1. Are you sure you want to proceed?').arg(self.link))

      dlgLayout = QVBoxLayout()
      frmAll = makeVertFrame([lblWarn, btnBox])

      dlgLayout.addWidget(frmAll)
      self.setLayout(dlgLayout)
      self.setWindowTitle('Warning: Opening Browser')

   def cancel(self):
      super(DlgBrowserWarn, self).reject()

   def accept(self):
     import webbrowser
     webbrowser.open(self.link)
     super(DlgBrowserWarn, self).accept() 

# Put circular imports at the end
from ui.WalletFrames import SelectWalletFrame, WalletBackupFrame,\
   AdvancedOptionsFrame
from ui.TxFrames import  SendBitcoinsFrame, SignBroadcastOfflineTxFrame,\
   ReviewOfflineTxFrame
from ui.MultiSigDialogs import DlgMultiSpendReview

# kate: indent-width 3; replace-tabs on;
