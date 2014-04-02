from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from armoryengine.parseAnnounce import *

class UpgradeDownloader:
   def __init__(self, parent, main):
      self.finishedCB = lambda : None
      self.startedCB = lambda : None
      self.url = None
      self.filesha = None
      self.downloadFile = None
      self.progressBar = None
      self.frame = None
      self.parent = parent
      self.main = main
      self.packageName = ''

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

   def setPackageName(self, pkgName):
      self.packageName = pkgName

   def createDownloaderWidget(self, parent):
      if self.frame:
         raise RuntimeError("already created a downloader widget")

      self.frame = QWidget(parent)

      bottomRowLayout = QHBoxLayout(self.frame)

      self.progressBar = QProgressBar(self.frame)
      bottomRowLayout.addWidget(self.progressBar, +1)

      self.downloadButton = QPushButton(tr("Download"), self.frame)
      self.frame.connect(self.downloadButton, SIGNAL('clicked()'), \
                                                      self.startOrStopDownload)
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

   #############################################################################
   def downloadFinished(self):
      if not self.downloadButton is None:
         self.downloadButton.setText(tr("Download"))

      # We will ask the user if they want us to unpack it for them
      # Only if linux, only if satoshi, only if not offline-pkg-signed
      linuxUnpackFile = None

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
               QMessageBox.warning(self.frame, tr("Verification failed"), tr("""
                  The download completed but its cryptographic signature is invalid.
                  Please try the download again.  If you get another error, please
                  report the problem to support@bitcoinarmory.com.
                  <br><br>
                  The downloaded data has been discarded.  """))
            else:
               defaultFN = os.path.basename(self.url)
               if self.downloadLinkFile:
                  defaultFN += ".signed"

               dest = self.main.getFileSave(tr("Save File"), 
                  [tr('Installers (*.exe, *.app, *.deb, *.tar.gz)')], 
                  defaultFilename=defaultFN)

               if len(dest)!=0:
                  df = open(dest, "wb")
                  if self.downloadLinkFile:
                     df.write("START_OF_SIGNATURE_SECTION")
                     df.write(self.downloadLinkFile)
                     df.write("END_OF_SIGNATURE_SECTION")
                  df.write(self.receivedData)
                  df.close()

                  if self.downloadLinkFile:
                     QMessageBox.warning(self.frame, tr("Download complete"), tr("""
                        The package has the
                        signature from <font color="%s"><b>Armory Technologies, 
                        Inc.</b></font> bundled with it, so it can be verified
                        by an offline computer before installation.  To use this 
                        feature, the offline system must be running Armory 
                        0.91-beta or higher.  Go to 
                        <i>"Help"</i>\xe2\x86\x92<i>"Verify Signed Package"</i>
                        and load the <i>*.signed</i> file.  The file was saved
                        to:
                        <br><br> 
                        %s
                        <br><br> 
                        <b>There is no special procedure to update a previous
                        installation.</b>  The installer will update existing
                        versions without touching your wallets or settings.""") % \
                        (htmlColor("TextGreen"), dest), \
                        QMessageBox.Ok)
                  else:
                     if OS_LINUX and \
                        self.packageName=='Satoshi' and \
                        dest.endswith('tar.gz'):
                        linuxUnpackFile = dest
                     else:
                        QMessageBox.warning(self.frame, tr("Download complete"), tr("""
                           The file downloaded successfully, and carries a valid 
                           signature from <font color="%s"><b>Armory Technologies, 
                           Inc.</b></font> You can now use it to install the 
                           software.  The file was saved to:
                           <br><br> %s <br><br>
                           <b>There is no special procedure to update a previous
                           installation.</b>  The installer will update existing
                           versions without touching your wallets or settings.""") % \
                           (htmlColor("TextGreen"), dest), QMessageBox.Ok)



      if linuxUnpackFile is not None:
         reply = QMessageBox.warning(self.frame, tr('Unpack Download'), tr("""
            You just downloaded the Bitcoin Core software for Linux.  
            Would you like Armory to extract it for you and adjust your 
            settings to use it automatically?
            <br><br>
            If you modified your settings to run Bitcoin Core manually, 
            click "No" then extract the downloaded file and manually start
            bitcoin-qt or bitcoind in from the extracted "bin/%d" 
            directory.""") % (64 if SystemSpecs.IsX64 else 32), \
            QMessageBox.Yes | QMessageBox.No)

         if reply==QMessageBox.Yes:
            finalDir = self.main.unpackLinuxTarGz(dest, changeSettings=True)
            if finalDir is None:
               QMessageBox.critical(self.frame, tr('Error Unpacking'), tr("""
                  There was an error unpacking the Bitcoin Core file.  To use
                  it, you need to go to where the file was saved, right-click
                  on it and select "Extract Here", then adjust your settings
                  (<i>"File"</i>\xe2\x86\x92<i>"Settings"</i> from the main 
                  window) to point "Bitcoin Install Dir" to the extracted 
                  directory.
                  <br><br>
                  You saved the installer to:
                  <br><br>
                  %s""") % dest, QMessageBox.Ok)
            else:
               QMessageBox.warning(self.frame, tr('Finished!'), tr("""
                  The operation was successful.  Restart Armory to use the
                  newly-downloaded Bitcoin Core software"""), QMessageBox.Ok)

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

      totalStr = bytesToHumanSize(size)
      sofarStr = bytesToHumanSize(len(self.receivedData))
      s = tr("{0} / {1} downloaded").format(sofarStr, totalStr)
      self.progressBar.setFormat(s)

      QTimer.singleShot(250, self.progressTimer)


class UpgradeDownloaderDialog(ArmoryDialog):
   # parent: QWidget
   # showPackage: automatically select this package name, if available, for the current OS
   # downloadText: the text *WITH SIGNATURE* of the downloaded text data
   # changeLog: the text of the downloaded changelogs
   def __init__(self, parent, main, showPackage, downloadText, changeLog):
      super(UpgradeDownloaderDialog, self).__init__(parent, main)

      self.downloader = UpgradeDownloader(parent, main)
      self.bitsColor = htmlColor('Foreground')

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
         "Satoshi" : tr("Bitcoin Core"), \
         "ArmoryTesting" : tr("Armory Testing (unstable)"), \
         "ArmoryOffline" : tr("Offline Armory Wallet") \
      }


      oslabel = QLabel(tr("OS:"), self)
      self.os = QComboBox(self)
      self.osver = QComboBox(self)
      self.osarch = QComboBox(self)

      packages = QTreeWidget(self)
      self.packages = packages
      packages.setRootIsDecorated(False)
      packages.sortByColumn(0, Qt.AscendingOrder)
      packages.setSortingEnabled(True)

      headerItem = QTreeWidgetItem()
      headerItem.setText(0,tr("Package"))
      headerItem.setText(1,tr("Version"))
      packages.setHeaderItem(headerItem)
      packages.setMaximumHeight(int(7*tightSizeStr(packages, "Abcdefg")[1]))
      packages.header().setResizeMode(0, QHeaderView.Stretch)
      packages.header().setResizeMode(1, QHeaderView.Stretch)

      self.connect(self.os, SIGNAL("activated(int)"), self.cascadeOsVer)
      self.connect(self.osver, SIGNAL("activated(int)"), self.cascadeOsArch)
      self.connect(self.osarch, SIGNAL("activated(int)"), self.displayPackages)

      self.connect(packages, \
         SIGNAL('currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)'), \
         self.useSelectedPackage)

      self.changelogView = QTextBrowser(self)
      self.changelogView.setOpenExternalLinks(True)

      self.saveAsOfflinePackage = QCheckBox(tr("Save with offline-verifiable signature"))
      self.closeButton = QPushButton(tr("Close"), self)
      self.connect(self.closeButton, SIGNAL('clicked()'), self.accept)

      self.btnDLInfo = QLabelButton('Download Info')
      self.btnDLInfo.setVisible(False)
      self.connect(self.btnDLInfo, SIGNAL('clicked()'), self.popupPackageInfo)


      self.lblSelectedSimple = QRichLabel(tr('No download selected'),
                                       doWrap=False, hAlign=Qt.AlignHCenter)
      self.lblSelectedSimpleMore = QRichLabel(tr(''), doWrap=False)
      self.lblSelectedComplex = QRichLabel(tr('No download selected'))
      self.lblCurrentVersion = QRichLabel('', hAlign=Qt.AlignHCenter)

      # At the moment, not sure we actually need this label
      self.lblSelectedComplex.setVisible(False)


      self.btnShowComplex = QLabelButton(tr('Show all downloads for all OS'))
      self.connect(self.btnShowComplex, SIGNAL('clicked()'), self.showComplex)

      frmDisp = makeHorizFrame(['Stretch', self.lblSelectedSimpleMore, 'Stretch'])
      frmBtnShowComplex = makeHorizFrame(['Stretch', self.btnShowComplex])
      layoutSimple = QVBoxLayout()
      layoutSimple.addWidget(self.lblSelectedSimple)
      layoutSimple.addWidget(frmDisp)
      layoutSimple.addWidget(self.lblCurrentVersion)
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


      frmTopComplex.setFrameStyle(STYLE_SUNKEN)
      frmTopSimple.setFrameStyle(STYLE_SUNKEN)

      self.stackedDisplay = QStackedWidget()
      self.stackedDisplay.addWidget(frmTopSimple)
      self.stackedDisplay.addWidget(frmTopComplex)

      layout = QGridLayout()
      layout.addWidget(self.stackedDisplay,       0,0,  1,3)
      layout.addWidget(self.changelogView,        1,0,  1,3)
      layout.addWidget(self.saveAsOfflinePackage, 2,0)
      layout.addWidget(self.btnDLInfo,            2,2)
      layout.addWidget(self.downloader.createDownloaderWidget(self), \
                                                  3,0,  1,3)
      layout.addWidget(self.closeButton,          4,2)
      layout.setRowStretch(0, 1)
      layout.setColumnStretch(1, 1)


      self.cascadeOs()
      self.selectMyOs()
      self.useSelectedPackage()
      self.cascadeOs()
      # I have no clue why we have to call these things so many times!
      self.selectMyOs()
      self.cascadeOs()


      # Above we had to select *something*, we should check that the
      # architecture actually matches our system.  If not, warn
      #trueBits = '64' if SystemSpecs.IsX64 else '32'
      #selectBits = self.itemData(self.osarch)[:2]
      #if showPackage and not trueBits==selectBits:
         #QMessageBox.warning(self, tr("Wrong Architecture"), tr("""
            #You appear to be on a %s-bit architecture, but the only
            #available download is for %s-bit systems.  It is unlikely
            #that this download will work on this operating system.
            #<br><br>
            #Please make sure that the correct operating system is
            #selected before attempting to download and install any
            #packages.""") % (trueBits, selectBits), QMessageBox.Ok)
         #self.bitsColor = htmlColor('TextRed')


      if showPackage == 'Armory':
         expectVer = self.main.armoryVersions[1]
      elif showPackage == 'Satoshi':
         expectVer = self.main.satoshiVersions[1]

      # This is currently broken... will have to fix later
      #if showPackage:
         #for n in range(0, packages.topLevelItemCount()):
            #row = packages.topLevelItem(n)
            #if str(row.data(0, 32).toString())==showPackage:
               #packages.setCurrentItem(row)
               #if not expectVer or str(row.data(1, 32).toString())==expectVer:
                  #break
            #self.useSelectedPackage()
         #else:
            #foundPackage = False

      self.stackedDisplay.setCurrentIndex(1)
      QMessageBox.warning(self, tr("Not Found"), tr("""
         Armory could not determine an appropriate download for
         your operating system.  You will have to manually select
         the correct download on the next window."""), QMessageBox.Ok)
      #else:
         #self.stackedDisplay.setCurrentIndex(1)


      self.setLayout(layout)
      self.setMinimumWidth(600)
      self.setWindowTitle(tr('Secure Downloader'))


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
            d2 = self.findCmbData(self.os, tr('Ubuntu'))
            osIndex = max(d1,d2)
         elif osVar.lower() == "ubuntu":
            osIndex = self.findCmbData(self.os, tr('Ubuntu'))
         else:
            osIndex = self.findCmbData(self.os, tr('Ubuntu'))
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

      archIndex = 0
      if platform.machine() == "x86_64":
         archIndex = self.findCmbData(self.osarch, tr('64'))
      else:
         archIndex = self.findCmbData(self.osarch, tr('32'))

      self.osarch.setCurrentIndex(archIndex)


   def useSelectedPackage(self):
      if self.packages.currentItem() is None:
         self.changelogView.setHtml("<html>" + tr("""
            There is no version information to be shown here.""") +"</html>")
         self.downloader.setFile(None, None)
      else:
         packagename = str(self.packages.currentItem().data(0, 32).toString())
         packagever  = str(self.packages.currentItem().data(1, 32).toString())
         packageurl  = str(self.packages.currentItem().data(2, 32).toString())
         packagehash = str(self.packages.currentItem().data(3, 32).toString())

         self.downloader.setFile(packageurl, packagehash)
         self.selectedDLInfo = [packagename,packagever,packageurl,packagehash]
         self.btnDLInfo.setVisible(True)

         self.downloader.setPackageName(packagename)

         # Figure out where to bound the changelog information
         startIndex = -1
         if self.changelog is not None:
            for i,triplet in enumerate(self.changelog):
               if triplet[0]==packagever:
                  startIndex = i
                  break

            stopIndex = len(self.changelog)
            if len(self.main.armoryVersions[0])>0:
               for i,triplet in enumerate(self.changelog):
                  currVer = getVersionInt(readVersionString(self.main.armoryVersions[0]))
                  thisVer = getVersionInt(readVersionString(triplet[0]))
                  if thisVer <= currVer:
                     stopIndex = i
                     break



         if startIndex > -1:

            logHtml = "<html><body>"
            if startIndex >= stopIndex:
               logHtml = tr("Release notes are not available for this package")
            else:
               for i in range(startIndex, stopIndex):
                  block = self.changelog[i]
                  logHtml += "<h2>" + tr("Version {0}").format(block[0]) + "</h2>\n"
                  logHtml += "<em>" + tr("Released on {0}").format(block[1]) + "</em>\n"
   
                  features = block[2]
                  logHtml += "<ul>"
                  for f in features:
                     logHtml += "<li>" + tr("<b>{0}</b>: {1}").format(f[0], f[1]) + "</li>\n"
                  logHtml += "</ul>\n\n"
         else:
            if packagename == "Satoshi":
               logHtml = tr("""
                  No version information is available here for any of the
                  core Bitcoin software downloads. You can find the
                  information at:
                  <a href='https://bitcoin.org/en/version-history'>https://bitcoin.org/en/version-history</a>""")
            else:
               logHtml = tr("Release notes are not available for this package")


         #logHtml += tr("""
            #<br><br>
            #-----
            #<br><br>
            #<u>Package</u>: <b>%s version %s</b><br>
            #<u>Download URL</u>:  <b>%s</b><br>
            #<u>Verified sha256sum</u>:  <b>%s</b>""") % \
            #(packagename, packagever, packageurl, packagehash)

         self.changelogView.setHtml(logHtml)
         self.updateLabels(packagename, packagever,
                              self.itemData(self.os),
                              self.itemData(self.osver),
                              self.itemData(self.osarch))



   def popupPackageInfo(self):
      pkgname,pkgver,pkgurl,pkghash = self.selectedDLInfo
      pkgname= tr(pkgname)
      pkgver = tr(pkgver)
      osname = tr(self.itemData(self.os))
      osver  = tr(self.itemData(self.osver))
      osarch = self.itemData(self.osarch)
      inst   = os.path.basename(pkgurl)
      QMessageBox.information(self, tr('Package Information'), tr("""
         Download information for <b>%(pkgname)s version %(pkgver)s:</b>
         <br>
         <ul>
            <li><u><b>Operating System</b></u>:</li>  
            <ul>
               <li>%(osname)s %(osver)s %(osarch)s-bit</li>
            </ul>
            <li><u><b>Installer Filename</b></u>:</li>  
            <ul>
               <li>%(inst)s</li>
            </ul>
            <li><u><b>Download URL</b></u>:</li>  
            <ul>
               <li>%(pkgurl)s</li>
            </ul>
            <li><u><b>Verified sha256sum</b></u>:</li>  
            <ul>
               <li>%(pkghash)s</li>
            </ul>
         </ul>""") % locals(), QMessageBox.Ok)
            
         
         


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

      # We use a list here because we need to sort the subvers
      allVers = sorted([x for x in allVers])
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
                                    self.itemData(self.os),
                                    self.itemData(self.osver),
                                    self.itemData(self.osarch))


   def updateLabels(self, pkgName, pkgVer, osName, osVer, osArch):
      if not pkgName:
         self.lblSelectedComplex.setText(tr("""No package currently selected"""))
         self.lblSelectedSimple.setText(tr("""No package currently selected"""))
         self.lblSelectedSimpleMore.setText(tr(""))
      else:
         self.lblSelectedComplex.setText(tr("""
            <font size=4><b>Selected Package:</b> {} {} for {} {} {}</font>"""). \
            format(tr(pkgName), tr(pkgVer), tr(osName), tr(osVer), tr(osArch)))

         self.lblSelectedSimple.setText(tr(""" <font size=4><b>Securely
            download latest version of <u>%s</u></b></font>""") % pkgName)

         self.lblCurrentVersion.setText('')
         currVerStr = ''
         if pkgName=='Satoshi':
            if self.main.satoshiVersions[0]:
               self.lblCurrentVersion.setText(tr("""
                  You are currently using Bitcoin Core version %s""") % \
                  self.main.satoshiVersions[0])
         elif pkgName=='Armory':
            if self.main.armoryVersions[0]:
               self.lblCurrentVersion.setText(tr("""
                  You are currently using Armory version %s""") % \
                  self.main.armoryVersions[0])

         self.lblSelectedSimpleMore.setText(tr("""
            <b>Software Download:</b>  %s version %s<br>
            <b>Operating System:</b>  %s %s <br>
            <b>System Architecture:</b> <font color="%s">%s</font> """) % \
            (tr(pkgName), tr(pkgVer), tr(osName), tr(osVer), self.bitsColor, tr(osArch)))

   # get the untranslated name from the combobox specified
   def itemData(self, combobox):
      return str(combobox.itemData(combobox.currentIndex()).toString())

   def localized(self, v):
      if v in self.localizedData:
         return str(self.localizedData[v])
      else:
         return str(v)


# kate: indent-width 3; replace-tabs on;
