from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from qtdefines import tr
from armoryengine.parseAnnounce import *


class VerifyOfflinePackageDialog(QDialog):
   def __init__(self, parent):
      super(QDialog, self).__init__(parent)

      layout = QVBoxLayout(self)
      
      load = QGroupBox(tr("Load Signed Package"), self)
      layout.addWidget(load)
      
      layoutload = QVBoxLayout()
      load.setLayout(layoutload)
      self.loadFileButton = QPushButton(tr("Select file to verify..."), load);
      layoutload.addWidget(self.loadFileButton)
      self.connect(self.loadFileButton, SIGNAL('clicked()'), self.load)
      
      save = QGroupBox(tr("Save Verified Package"), self)
      layout.addWidget(save)
      layoutsave = QVBoxLayout()
      save.setLayout(layoutsave)
      self.saveFileButton = QPushButton(tr("Select file to save to..."), load);
      self.saveFileButton.setEnabled(False)
      layoutsave.addWidget(self.saveFileButton)
      self.connect(self.saveFileButton, SIGNAL('clicked()'), self.save)
      
   def load(self):
      self.fileData = None
      fromfile = QFileDialog.getOpenFileName(self, tr("Load file to verify"), "", tr("Armory Signed Packages (*.signed)"))
      if len(fromfile)==0:
         return
         
      df = open(fromfile, "rb")
      allfile = df.read()
      df.close()
      magicstart="START_OF_SIGNATURE_SECTION"
      magicend="END_OF_SIGNATURE_SECTION"
      if 0 != allfile.find(magicstart, 0, 1024*1024*4): # don't search past 4MiB
         QMessageBox.warning(self, tr("Invalid File"), tr("This file is not a signed package"))
         return
      
      end = allfile.find(magicend, 0, 1024*1024*4) # don't search past 4MiB
      if -1 == end: # don't search past 4MiB
         QMessageBox.warning(self, tr("Invalid File"), tr("The end of the signature in the file could not be found"))
      
      signatureData = allfile[len(magicstart):end]
      fileData = allfile[end+len(magicend):]
      
      print "All:",end, end+len(magicend), len(fileData), len(allfile)
      
      allsigs = downloadLinkParser(filetext=signatureData).downloadMap
      
      res = binary_to_hex(sha256(fileData))
      
      good=False
      url=None
      print "have hash",res
      
      # simply check if any of the hashes match
      for pack in allsigs.itervalues():
         for packver in pack.itervalues():
            for packos in packver.itervalues():
               for packosver in packos.itervalues():
                  for packosarch in packosver.itervalues():
                     okhash = packosarch[1]
                     print "hash",okhash
                     if okhash == res:
                        url = packosarch[0]
                        good=True
      if good:
         self.saveFileButton.setEnabled(True)
         self.fileData = fileData
         self.fileName = os.path.basename(url)
      else:
         self.saveFileButton.setEnabled(False)
         QMessageBox.warning(self, tr("Signature Failure"),  tr("This file has an invalid signature"))
         
   def save(self):
      tofile = QFileDialog.getSaveFileName(self, tr("Save confirmed package"), QDir.homePath() + "/" + self.fileName)
      if len(tofile)==0:
         return
      df = open(tofile, "wb")
      df.write(self.fileData)
      df.close()
      
# kate: indent-width 3; replace-tabs on;
