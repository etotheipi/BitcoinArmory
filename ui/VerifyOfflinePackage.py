from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from qtdefines import tr, QRichLabel, ArmoryDialog
from armoryengine.parseAnnounce import *
from armorycolors import htmlColor


class VerifyOfflinePackageDialog(ArmoryDialog):
   def __init__(self, parent, main):
      super(VerifyOfflinePackageDialog, self).__init__(parent)
      self.main = main

      layout = QVBoxLayout(self)
      
      load = QGroupBox(tr("Load Signed Package"), self)
      layout.addWidget(load)
      
      layoutload = QVBoxLayout()
      load.setLayout(layoutload)
      self.loadFileButton = QPushButton(tr("Select file to verify..."), load);
      layoutload.addWidget(self.loadFileButton)
      self.connect(self.loadFileButton, SIGNAL('clicked()'), self.load)

      self.lblVerified = QRichLabel('', hAlign=Qt.AlignHCenter, doWrap=False)
      layout.addWidget(self.lblVerified)

      
      save = QGroupBox(tr("Save Verified Package"), self)
      layout.addItem(QSpacerItem(10,10))
      layout.addWidget(save)
      layoutsave = QVBoxLayout()
      save.setLayout(layoutsave)
      self.saveFileButton = QPushButton(tr("Select file to save to..."), load);
      self.saveFileButton.setEnabled(False)
      layoutsave.addWidget(self.saveFileButton)
      self.connect(self.saveFileButton, SIGNAL('clicked()'), self.save)
      self.setWindowTitle('Verify Signed Package')

      
   def load(self):
      self.fileData = None
      #self.fromfile = QFileDialog.getOpenFileName(self, tr("Load file to verify"), "", tr("Armory Signed Packages (*.signed)"))
      self.fromfile = self.main.getFileLoad(tr('Load file to Verify'),\
                                       ['Armory Signed Packages (*.signed)'])
      if len(self.fromfile)==0:
         return
         
      df = open(self.fromfile, "rb")
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
      print "Hash of package file: ", res
      
      # simply check if any of the hashes match
      for pack in allsigs.itervalues():
         for packver in pack.itervalues():
            for packos in packver.itervalues():
               for packosver in packos.itervalues():
                  for packosarch in packosver.itervalues():
                     okhash = packosarch[1]
                     if okhash == res:
                        url = packosarch[0]
                        good=True

      if good:
         self.saveFileButton.setEnabled(True)
         self.fileData = fileData
         self.fileName = os.path.basename(url)
         self.lblVerified.setText(tr("""<font color="%s"><b>Signature is 
            Valid!</b></font>""") % htmlColor('TextGreen'))
         reply = QMessageBox.warning(self, tr("Signature Valid"),  tr("""
            The downloaded file has a <b>valid</b> signature from 
            <font color="%s"><b>Armory Technologies, Inc.</b></font>, and is 
            safe to install.  
            <br><br>
            Would you like to overwrite the original file with the extracted
            installer?  If you would like to save it to a new location, click 
            "No" and then use the "Save Verified Package" button to select
            a new save location.""") % htmlColor('TextGreen'), \
            QMessageBox.Yes | QMessageBox.No)

         if reply==QMessageBox.Yes:
            newFile = self.fromfile
            if newFile.endswith('.signed'):
               newFile = self.fromfile[:-7]

            LOGINFO('Saving installer to: ' + newFile)

            with open(newFile, 'wb') as df:
               df.write(self.fileData)

            if os.path.exists(newFile):
               LOGINFO('Removing original file: ' + self.fromfile)
               os.remove(self.fromfile)

            QMessageBox.warning(self, tr('Saved!'), tr("""
               The installer was successfully extracted and saved to the
               following location:
               <br><br>
               %s""") % newFile, QMessageBox.Ok)
         
            
      else:
         self.saveFileButton.setEnabled(False)
         self.lblVerified.setText(tr("""<font color="%s">Invalid signature
            on loaded file!</font>""") % htmlColor('TextRed'))
         QMessageBox.warning(self, tr("Signature failure"),  \
                        tr("This file has an invalid signature"))
         
   def save(self):
      tofile = QFileDialog.getSaveFileName(self, tr("Save confirmed package"), \
                        QDir.homePath() + "/" + self.fileName)
      if len(tofile)==0:
         return
      df = open(tofile, "wb")
      df.write(self.fileData)
      df.close()
      
# kate: indent-width 3; replace-tabs on;
