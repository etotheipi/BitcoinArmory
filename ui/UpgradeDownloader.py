from PyQt4.Qt import *
from PyQt4.QtGui import *
from qtdefines import *
from armoryengine.parseAnnounce import *

class UpgradeDownloader:
   def __init__(self):
      self.finishedCB = lambda : None
      self.startedCB = lambda : None
      self.url = None
      self.filesha = None
      self.downloadFile = None
      self.progressBar = None
      self.frame = None

      self.networkAccess = QNetworkAccessManager()

   # downloadLinkFile
   def setFile(self, url, filehash):
      self.url = url
      self.filesha = filehash

      if self.downloadButton:
         if url and not self.downloadFile:
            self.downloadButton.setEnabled(True)
         else:
            self.downloadButton.setEnabled(False)

   def useDownloadLinkFileAndSignature(self, linkfile):
      self.downloadLinkFile = linkfile

   def setFinishedCallback(self, callback):
      self.finishedCB = callback

   def setStartedCallback(self, callback):
      self.startedCB = callback

   def createDownloaderWidget(self, parent):
      if self.frame:
         raise RuntimeError("already created a downloader widget")

      self.frame = QWidget(parent)

      bottomRowLayout = QHBoxLayout(self.frame)

      self.progressBar = QProgressBar(self.frame)
      bottomRowLayout.addWidget(self.progressBar, +1)

      self.downloadButton = QPushButton(tr("Download"), self.frame)
      self.frame.connect(self.downloadButton, SIGNAL('clicked()'), self.startOrStopDownload)
      bottomRowLayout.addWidget(self.downloadButton)

      return self.frame

   def startOrStopDownload(self):
      if self.downloadFile:
         o = self.downloadFile
         self.downloadFile = None
         o.close()
      else:
         self.startDownload()

   def startDownload(self):
      req = QNetworkRequest(QUrl.fromEncoded(self.url))
      self.receivedData = ""
      self.downloadFile = self.networkAccess.get(req)
      QObject.connect(self.downloadFile, SIGNAL('readyRead()'), self.readMoreDownloadData)
      QObject.connect(self.downloadFile, SIGNAL('finished()'), self.downloadFinished)

      if not self.downloadButton is None:
         self.downloadButton.setText(tr("Cancel"))

      self.progressTimer()
      self.startedCB()

   def downloadFinished(self):
      if not self.downloadButton is None:
         self.downloadButton.setText(tr("Download"))

      # downloadFile will be removed on cancel
      if not self.downloadFile is None:
         status = self.downloadFile.attribute(QNetworkRequest.HttpStatusCodeAttribute).toInt()[0]
         if len(self.receivedData)==0:
            if status == 404:
               status = tr("File not found")
            QMessageBox.warning(self.frame, tr("Download failed"), \
               tr("There was a failure downloading this file: {}").format(str(status)))
         else:
            res = binary_to_hex(sha256(self.receivedData))
            LOGINFO("Downloaded package has hash " + res)
            if res != self.filesha:
               QMessageBox.warning(self.frame, tr("Verification failed"), \
                  tr("""The download completed but its cryptographic signature failed to verify.
                  This may or may not be malicious interference and you should report
                  the problem to support@bitcoinarmory.com after trying once more.
                  <br><br>
                  The downloaded data has been discarded.
                  """))
            else:
               suffix = ""
               if self.downloadLinkFile:
                  suffix = ".signed"
               dest = QFileDialog.getSaveFileName(self.frame, tr("Save file"), QDir.homePath() + "/" + os.path.basename(self.url) + suffix)
               if len(dest)!=0:
                  df = open(dest, "wb")
                  if self.downloadLinkFile:
                     df.write("START_OF_SIGNATURE_SECTION")
                     df.write(self.downloadLinkFile)
                     df.write("END_OF_SIGNATURE_SECTION")
                  df.write(self.receivedData)
                  df.close()

      self.receivedData = None
      self.downloadFile = None
      self.downloadButton.setEnabled(True)
      self.progressBar.setFormat("")

      if self.finishedCB:
         self.finishedCB()

   def readMoreDownloadData(self):
      if not self.receivedData is None:
         self.receivedData = self.receivedData + self.downloadFile.readAll()

   def progressTimer(self):
      if not self.downloadFile:
         self.progressBar.reset()
         self.progressBar.setRange(0, 100)
         self.progressBar.setValue(0)
         return

      size = self.downloadFile.header(QNetworkRequest.ContentLengthHeader).toInt()[0]
      self.progressBar.setRange(0, size)
      self.progressBar.setValue(len(self.receivedData))

      if size >= 1024*1024*10:
         total = size/1024/1024.
         sofar = len(self.receivedData)/1024/1024.
         s = tr("%0.1f / %0.1f MiB downloaded") % (sofar, total)
         self.progressBar.setFormat(s)
      else:
         total = size/1024
         sofar = len(self.receivedData)/1024
         s = tr("{0}/{1} KiB downloaded").format(sofar, total)
         self.progressBar.setFormat(s)

      QTimer.singleShot(250, self.progressTimer)


class UpgradeDownloaderDialog(ArmoryDialog):
   # parent: QWidget
   # showPackage: automatically select this package name, if available, for the current OS
   # downloadText: the text *WITH SIGNATURE* of the downloaded text data
   # changeLog: the text of the downloaded changelogs
   def __init__(self, parent, main, showPackage, downloadText, changeLog):
      super(UpgradeDownloaderDialog, self).__init__(parent, main)

      self.downloader = UpgradeDownloader()

      def enableOrDisable(e):
         self.os.setEnabled(e)
         self.osver.setEnabled(e)
         self.osarch.setEnabled(e)
         self.packages.setEnabled(e)
         self.closeButton.setEnabled(e)

      self.downloader.setFinishedCallback(lambda : enableOrDisable(True))

      def onStart():
         enableOrDisable(False)
         downloadText=None
         if self.saveAsOfflinePackage.isChecked():
            downloadText = self.downloadText
         self.downloader.useDownloadLinkFileAndSignature(downloadText)

      self.downloader.setStartedCallback(onStart)

      self.downloadText = downloadText
      self.nestedDownloadMap = downloadLinkParser(filetext=downloadText).downloadMap
      self.changelog = changelogParser().parseChangelogText(changeLog)

      self.localizedData = { \
         "Ubuntu" : tr("Ubuntu/Debian"), \
         "Windows" : tr("Windows"), \
         "MacOSX" : tr("MacOSX"), \
         "32" : tr("32-bit"), \
         "64" : tr("64-bit"), \
         "Satoshi" : tr("Bitcoin-Qt"), \
         "ArmoryOffline" : tr("Offline Armory Wallet") \
      }


      oslabel = QLabel(tr("OS:"), self)
      self.os = QComboBox(self)
      self.osver = QComboBox(self)
      self.osarch = QComboBox(self)

      packages = QTreeWidget(self)
      self.packages = packages
      packages.setRootIsDecorated(False)

      headerItem = QTreeWidgetItem()
      headerItem.setText(0,tr("Package"))
      headerItem.setText(1,tr("Version"))
      packages.setHeaderItem(headerItem)
      packages.setMaximumHeight(int(7*tightSizeStr(packages, "Abcdefg")[1]))

      self.connect(self.os, SIGNAL("activated(int)"), self.cascadeOsVer)
      self.connect(self.osver, SIGNAL("activated(int)"), self.cascadeOsArch)
      self.connect(self.osarch, SIGNAL("activated(int)"), self.displayPackages)

      self.connect(packages, \
         SIGNAL('currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)'), \
         self.useSelectedPackage)

      self.changelogView = QTextBrowser(self)
      self.changelogView.setOpenExternalLinks(True)

      self.saveAsOfflinePackage = QCheckBox(tr("Saved as offline-signed package"), self)
      self.closeButton = QPushButton(tr("Close"), self)
      self.connect(self.closeButton, SIGNAL('clicked()'), self.accept)


      self.lblSelectedSimple = QRichLabel(tr('No download selected'), 
                                       doWrap=False, hAlign=Qt.AlignHCenter)
      self.lblSelectedSimpleMore = QRichLabel(tr(''), doWrap=False)
      self.lblSelectedComplex = QRichLabel(tr('No download selected'))


      self.btnShowComplex = QLabelButton(tr('Show all downloads for all OS'))
      self.connect(self.btnShowComplex, SIGNAL('clicked()'), self.showComplex)

      frmDisp = makeHorizFrame(['Stretch', self.lblSelectedSimpleMore, 'Stretch'])
      frmBtnShowComplex = makeHorizFrame(['Stretch', self.btnShowComplex])
      layoutSimple = QVBoxLayout()
      layoutSimple.addWidget(self.lblSelectedSimple)
      layoutSimple.addWidget(frmDisp)
      layoutSimple.addWidget(frmBtnShowComplex)
      frmTopSimple = QFrame()
      frmTopSimple.setLayout(layoutSimple)


      layoutComplex = QGridLayout()
      layoutComplex.addWidget(oslabel,    0,0)
      layoutComplex.addWidget(self.os,    0,1)
      layoutComplex.addWidget(self.osver, 0,2)
      layoutComplex.addWidget(self.osarch,0,3)
      layoutComplex.addWidget(packages,   1,0, 1,4)
      layoutComplex.addWidget(self.lblSelectedComplex, 2,0, 1,4)
      layoutComplex.setColumnStretch(0,0)
      layoutComplex.setColumnStretch(1,2)
      layoutComplex.setColumnStretch(2,2)
      layoutComplex.setColumnStretch(3,1)
      frmTopComplex = QFrame()
      frmTopComplex.setLayout(layoutComplex)


      frmTopComplex.setFrameStyle(STYLE_RAISED)
      frmTopSimple.setFrameStyle(STYLE_RAISED)

      self.stackedDisplay = QStackedWidget()
      self.stackedDisplay.addWidget(frmTopSimple)
      self.stackedDisplay.addWidget(frmTopComplex)

      layout = QVBoxLayout(self)
      layout.addWidget(self.stackedDisplay)
      layout.addWidget(self.changelogView, +1)
      layout.addWidget(self.saveAsOfflinePackage)
      layout.addWidget(self.downloader.createDownloaderWidget(self))

      closeButtonRowLayout = QHBoxLayout(None)
      layout.addLayout(closeButtonRowLayout)
      closeButtonRowLayout.addStretch(1)
      closeButtonRowLayout.addWidget(self.closeButton)


      if showPackage:
         for n in range(0, packages.topLevelItemCount()):
            row = packages.topLevelItem(n)
            if row.data(0, 32)==showPackage:
               packages.setCurrentItem(row)
               break

      self.cascadeOs()
      self.selectMyOs()
      self.useSelectedPackage()
      self.cascadeOs()
      self.selectMyOs()
      self.cascadeOs()
      self.useSelectedPackage()

      self.setMinimumWidth(600)
      self.setWindowTitle(tr('Secure Download Bitcoin Software'))


   def showSimple(self):
      self.stackedDisplay.setCurrentIndex(0)

   def showComplex(self):
      self.stackedDisplay.setCurrentIndex(1)


   def findCmbData(self, cmb, findStr, last=False):
      """
      So I ran into some issues with finding python strings in comboboxes
      full of QStrings.  I confirmed that 
         self.os.itemText(i)==tr("Ubuntu/Debian")
      but not
         self.os.findData(tr("Ubuntu/Debian"))
      I'm probably being stupid, I thought I saw this work before...

      Return zero if failed so we just select the first item in the list 
      if we don't find it.
      """
      for i in range(cmb.count()):
         if cmb.itemText(i)==findStr:
            return i

      return 0 if not last else cmb.count()-1


   def selectMyOs(self):
      osVar = OS_VARIANT
      if isinstance(osVar, (list,tuple)):
         osVar = osVar[0]

      osIndex = 0
      if OS_WINDOWS:
         osIndex = self.findCmbData(self.os, tr("Windows"))
      elif OS_LINUX:
         if osVar.lower() in ['debian', 'linuxmint']:
            d1 = self.findCmbData(self.os, tr('Debian'))
            d2 = self.findCmbData(self.os, tr('Ubuntu/Debian'))
            osIndex = max(d1,d2)
         elif osVar.lower() == "ubuntu":
            osIndex = self.findCmbData(self.os, tr('Ubuntu/Debian'))
         else:
            osIndex = self.findCmbData(self.os, tr('Ubuntu/Debian'))
      elif OS_MACOSX:
         osIndex = self.findCmbData(self.osver, tr('MacOSX'))

      self.os.setCurrentIndex(osIndex)
      self.cascadeOsVer() # signals don't go through for some reason

      osverIndex = 0
      if OS_WINDOWS:
         osverIndex = self.findCmbData(self.osver, platform.win32_ver(), True)
      elif OS_LINUX:
         osverIndex = self.findCmbData(self.osver, OS_VARIANT[1], True)
      elif OS_MACOSX:
         osverIndex = self.findCmbData(self.osver, platform.mac_ver()[0], True)
      self.osver.setCurrentIndex(osverIndex)

      self.cascadeOsArch()
      if platform.machine() == "x86_64":
         self.osarch.setCurrentIndex(self.osarch.findData("64"))
      else:
         self.osarch.setCurrentIndex(self.osarch.findData("32"))



   def useSelectedPackage(self):
      if self.packages.currentItem() is None:
         self.changelogView.setHtml("<html>" + tr("The changelog for the selected package will be visible here") +"</html>")
         self.downloader.setFile(None, None)
      else:
         packagename = str(self.packages.currentItem().data(0, 32).toString())
         packagever = str(self.packages.currentItem().data(1, 32).toString())
         packageurl = str(self.packages.currentItem().data(2, 32).toString())
         packagehash = str(self.packages.currentItem().data(3, 32).toString())

         self.downloader.setFile(packageurl, packagehash)

         if packagename in self.changelog:
            chpackage = self.changelog[packagename]
            index=0
            for p in chpackage:
               if p[0] == packagever:
                  break
               index+=1

            html = "<html><body>"
            for p in range(index, len(chpackage)):
               block = chpackage[p]
               html += "<h2>" + tr("Version {0}").format(block[0]) + "</h2>\n"
               html += "<em>" + tr("Released on {0}").format(block[1]) + "</em>\n"

               features = block[2]
               html += "<ul>"
               for f in features:
                  html += "<li>" + tr("<b>{0}</b>: {1}").format(f[0], f[1]) + "</li>\n"
               html += "</ul>\n\n"

            self.changelogView.setHtml(html)
         else:
            if packagename == "Satoshi":
               self.changelogView.setHtml(tr("""
                  No version information is available here for any of the
                  core Bitcoin software downloads. You can find the
                  information at:
                  <a href='https://bitcoin.org/en/version-history'>https://bitcoin.org/en/version-history</a>"""))
            else:
               self.changelogView.setHtml(tr("Release notes are not available for this package"))

         self.updateLabels(packagename, packagever, 
                              self.os.currentText(), 
                              self.osver.currentText(), 
                              self.osarch.currentText())
                                    

   def cascade(self, combobox, valuesfrom, nextToCascade):
      combobox.blockSignals(True)
      current = combobox.currentText()
      combobox.clear()
      for v in valuesfrom:
         combobox.addItem(self.localized(v), QVariant(v))
      at = combobox.findText(current)
      if at != -1:
         combobox.setCurrentIndex(at)

      nextToCascade()
      combobox.blockSignals(False)


   # pass the combobox (self.os, osver, ...) and the part of nestedDownloadMap
   # to look into
   def cascadeOs(self):
      allOSes = set()
      for pack in self.nestedDownloadMap.itervalues():
         for packver in pack.itervalues():
            for os in packver.iterkeys():
               allOSes.add(os)
      self.cascade(self.os, allOSes, self.cascadeOsVer)

   def cascadeOsVer(self):
      chosenos = str(self.os.itemData(self.os.currentIndex()).toString())
      if len(chosenos)==0:
         return

      allVers = set()
      for pack in self.nestedDownloadMap.itervalues():
         for packver in pack.itervalues():
            if chosenos in packver:
               for osver in packver[chosenos].iterkeys():
                  allVers.add(osver)

      self.cascade(self.osver, allVers, self.cascadeOsArch)

   def cascadeOsArch(self):
      chosenos = str(self.os.itemData(self.os.currentIndex()).toString())
      chosenosver = str(self.osver.itemData(self.osver.currentIndex()).toString())
      if len(chosenosver)==0:
         return

      allArchs = set()
      for pack in self.nestedDownloadMap.itervalues():
         for packver in pack.itervalues():
            if chosenos in packver and chosenosver in packver[chosenos]:
               for osarch in packver[chosenos][chosenosver].iterkeys():
                  allArchs.add(osarch)
      self.cascade(self.osarch, allArchs, self.displayPackages)

   def displayPackages(self):
      packages = self.packages
      packages.clear()
      chosenos = str(self.os.itemData(self.os.currentIndex()).toString())
      chosenosver = str(self.osver.itemData(self.osver.currentIndex()).toString())
      chosenosarch = str(self.osarch.itemData(self.osarch.currentIndex()).toString())
      if len(chosenosarch)==0:
         return

      for packname,pack in self.nestedDownloadMap.iteritems():
         for packvername,packver in pack.iteritems():
            if chosenos in packver \
               and chosenosver in packver[chosenos] \
               and chosenosarch in packver[chosenos][chosenosver]:

               row = QTreeWidgetItem()
               row.setText(0, self.localized(packname))
               row.setData(0, 32, packname) # not localized
               row.setText(1, self.localized(packvername))
               row.setData(1, 32, packvername)
               row.setData(2, 32, packver[chosenos][chosenosver][chosenosarch][0])
               row.setData(3, 32, packver[chosenos][chosenosver][chosenosarch][1])
               packages.addTopLevelItem(row)


               self.updateLabels(packname, packvername, 
                                     self.os.currentText(), 
                                     self.osver.currentText(), 
                                     self.osarch.currentText())



   def updateLabels(self, pkgName, pkgVer, osName, osVer, osArch):
      if pkgName=='Satoshi':
         pkgName = 'Bitcoin Core'

      if not pkgName:
         self.lblSelectedComplex.setText(tr("""No package currently selected"""))
         self.lblSelectedSimple.setText(tr("""No package currently selected"""))
         self.lblSelectedSimpleMore.setText(tr(""))
      else:
         self.lblSelectedComplex.setText(tr("""
            <font size=4><b>Selected Package:</b> %s %s for %s %s %s</font>""") % \
            (pkgName, pkgVer, osName, osVer, osArch))
   
         self.lblSelectedSimple.setText(tr(""" <font size=4><b>Securely 
            download latest version of <u>%s</u></b></font>""") % pkgName)
   
         self.lblSelectedSimpleMore.setText(tr("""
            <b>Software Download:</b>  %s version %s<br>
            <b>Operating System:</b>  %s %s <br>
            <b>System Architecture:</b> %s """) % \
            (pkgName, pkgVer, osName, osVer, osArch))



   def localized(self, v):
      if v in self.localizedData:
         return str(self.localizedData[v])
      else:
         return str(v)


# kate: indent-width 3; replace-tabs on;
