# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the locals() from ArmoryQt.py, which includes pretty
# much 100% of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.



def getTabToDisplay():

   tabScrollArea = QScrollArea()
   tabScrollArea.setWidgetResizable(True)
   #tabScrollArea.setWidget(theFrame)

   #scrollLayout = QVBoxLayout()
   #scrollLayout.addWidget(tabScrollArea)
   #tabOut = QWidget() 
   #tabOut.setLayout(scrollLayout)

   return tabScrollArea



newTxFuncs = [lambda: 
