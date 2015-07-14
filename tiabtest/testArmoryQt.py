import sys
sys.path.append('..')
from tiabtest.Tiab import *

from armoryengine.ArmoryUtils import *
from armoryengine.ArmorySettings import *
from qtdialogs import *

from armoryd import ArmoryDaemon, ArmoryRPC, JSONtoAmount, \
   addMultWallets, addMultLockboxes, createFuncDict


TMP = 'settings.tmp'

class MockMain():

    def __init__(self):
        self.settings = SettingsFile(TMP)

    def createToolTipWidget(self, txt):
        return QLabel('test')

    def getSettingOrSetDefault(self, key, default):
        return default


class ClientTest(TiabTest):

    def setUp(self):
        # wallets
        self.fileA = os.path.join(self.armoryHomeDir, FIRST_WLT_FILE_NAME)
        self.fileB = os.path.join(self.armoryHomeDir, SECOND_WLT_FILE_NAME)
        self.fileC = os.path.join(self.armoryHomeDir, THIRD_WLT_FILE_NAME)

        inWltPaths = [self.fileA, self.fileB, self.fileC]
        inWltMap = addMultWallets(inWltPaths)
        self.wltA = inWltMap[FIRST_WLT_NAME]
        self.wltB = inWltMap[SECOND_WLT_NAME]
        self.wltC = inWltMap[THIRD_WLT_NAME]

        self.main = MockMain()

    def tearDown(self):
        pass

    def testDlgUnlockWallet(self):
        dlg = DlgUnlockWallet(self.wltA, main=self.main)
        dlg.btnShowOSD.setChecked(False)
        dlg.toggleOSD()
        self.assertEqual(str(dlg.btnShowOSD.text()), 'Show Keyboard >>>')
        dlg.btnShowOSD.setChecked(True)
        dlg.toggleOSD()
        self.assertEqual(str(dlg.btnShowOSD.text()), 'Hide Keyboard <<<')
