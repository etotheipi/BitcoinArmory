<?xml version="1.0" ?><!DOCTYPE TS><TS language="el" sourcelanguage="" version="2.0">
<context>
    <name>@default</name>
    <message>
        <location filename="ArmoryQt.py" line="577"/>
        <source>Not Online</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1324"/>
        <source>Copy or load a transaction from file into the text box below.  If the transaction is unsigned and you have the correct wallet, you will have the opportunity to sign it.  If it is already signed you will have the opportunity to broadcast it to the Bitcoin network to make it final.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1387"/>
        <source>A unique string that identifies an &lt;i&gt;unsigned&lt;/i&gt; transaction.  This is different than the ID that the transaction will have when it is finally broadcast, because the broadcast ID cannot be calculated without all the signatures</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="894"/>
        <source>Protects Imported Addresses</source>
        <translation>Προστατεύει τις Εισηγμένες Διευθύνσεις</translation>
    </message>
</context>
<context>
    <name>AddressTreeModel</name>
    <message>
        <location filename="TreeViewGUI.py" line="602"/>
        <source>Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="603"/>
        <source>Comment</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="604"/>
        <source>Tx Count</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="605"/>
        <source>Balance</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>AddressTypeSelectDialog</name>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="24"/>
        <source>P2PKH Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="25"/>
        <source>Legacy Armory address type. Backwards compatible.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="40"/>
        <source>P2SH-P2WPKH address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="41"/>
        <source>P2WPKH (SegWit script) nested in P2SH script. Any wallet can pay to this address. Only wallets supporting SegWit can spend from it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="61"/>
        <source>P2SH-P2PK address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="62"/>
        <source>Compressed P2PK script nested in P2SH output. Any wallet can pay to this address. Only Armory 0.96+ can spend from it.&lt;br&gt;&lt;br&gt;This format allow for more efficient transaction space use, resulting in smaller inputs and lower fees.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="86"/>
        <source>Apply</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="87"/>
        <source>Cancel</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="96"/>
        <source>Select Address Type</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>AdvancedOptionsFrame</name>
    <message>
        <location filename="WalletFrames.py" line="413"/>
        <source>Armory will test your system's speed to determine the most challenging encryption settings that can be applied in a given amount of time.  High settings make it much harder for someone to guess your passphrase.  This is used for all encrypted wallets, but the default parameters can be changed below.
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="420"/>
        <source>This is the amount of time it will take for your computer to unlock your wallet after you enter your passphrase. (the actual time used will be less than the specified time, but more than one half of it).  </source>
        <translation>Αυτό είναι το χρονικό διάστημα που θα χρειαστεί ώστε ο υπολογιστής σας να ξεκλειδώσει το πορτοφόλι σας, μετά που θα εισαγάγετε τη φράση πρόσβασης. (Ο πραγματικός χρόνος που χρησιμοποιείται θα είναι μικρότερος από τον καθορισμένο χρόνο, αλλά περισσότερο από το μισό από αυτόν).</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="430"/>
        <source>Target compute &amp;time (s, ms):</source>
        <translation>Στόχος Υπολογισμού &amp;χρόνου (s, ms):</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="431"/>
        <source>This is the &lt;b&gt;maximum&lt;/b&gt; memory that will be used as part of the encryption process.  The actual value used may be lower, depending on your system&apos;s speed.  If a low value is chosen, Armory will compensate by chaining together more calculations to meet the target time.  High memory target will make GPU-acceleration useless for guessing your passphrase.</source>
        <translation>Αυτή είναι η &lt;b&gt;μέγιστη&lt;/b&gt; μνήμης που θα χρησιμοποιηθεί ως μέρος της διαδικασίας κρυπτογράφησης. Η πραγματική τιμή που χρησιμοποιείται μπορεί να είναι μικρότερη, ανάλογα με την ταχύτητα του συστήματός σας. Εάν έχει επιλεγεί μια χαμηλή τιμή, το Armory θα σας αποζημιώσει με την αλυσιδωτή σύνδεση μαζί με περισσότερους υπολογισμούς για να καλύψουμε το χρόνο-στόχο. Ο στόχος υψηλής μνήμης θα κάνει την επιτάχυνση με Κάρτα Γραφικών άχρηστη για την εικασία της συνθηματικής φράσης σας.</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="445"/>
        <source>Max &amp;memory usage (kB, MB):</source>
        <translation>Μέγιστη χρήση &amp;memory μνήμης (kB, MB):</translation>
    </message>
</context>
<context>
    <name>AllWalletsDispModel</name>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>ID</source>
        <translation>Ταυτότητα</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Wallet Name</source>
        <translation>Όνομα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Security</source>
        <translation>Ασφάλεια</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Balance</source>
        <translation>Υπόλοιπο</translation>
    </message>
</context>
<context>
    <name>ArmoryDialog</name>
    <message>
        <location filename="qtdefines.py" line="786"/>
        <source>Armory - Bitcoin Wallet Management [TESTNET] </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="789"/>
        <source>Armory - Bitcoin Wallet Management [REGTEST] </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="792"/>
        <source>Armory - Bitcoin Wallet Management</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>ArmoryMainWindow</name>
    <message>
        <location filename="ArmoryQt.py" line="293"/>
        <source>&lt;font color=%1&gt;Offline&lt;/font&gt; </source>
        <translation>&lt;font color=%1&gt;Εκτός Σύνδεσης&lt;/font&gt; </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="344"/>
        <source>Create Wallet</source>
        <translation>Δημιουργία Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="345"/>
        <source>Import or Restore Wallet</source>
        <translation>Εισαγωγή ή Επαναφορά Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="350"/>
        <source>&lt;b&gt;Available Wallets:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Διαθέσιμα Πορτοφόλια:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="380"/>
        <source>&lt;b&gt;Maximum Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Μέγιστα Ποσά:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="381"/>
        <source>&lt;b&gt;Spendable Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ελεύθερα Ποσά:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="382"/>
        <source>&lt;b&gt;Unconfirmed:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ανεπιβεβαίωτα:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="398"/>
        <source>
            Funds if all current transactions are confirmed.  
            Value appears gray when it is the same as your spendable funds. </source>
        <translation>
Υπόλοιπο όταν όλες οι συναλλαγές έχουν επιβεβαιωθεί.
Η αξία εμφανίζετε με γκρί όταν είναι η ίδια με τα ποσά που μπορούν να ξοδευτούν.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="401"/>
        <source>Funds that can be spent &lt;i&gt;right now&lt;/i&gt;</source>
        <translation>Ποσά που μπορούν να ξοδευτούν &lt;i&gt;άμεσα&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="402"/>
        <source>
            Funds that have less than 6 confirmations, and thus should not 
            be considered &lt;i&gt;yours&lt;/i&gt;, yet.</source>
        <translation>
Ποσά που έχουν λιγότερες απο 6 επιβεβαιώσεις, και δεν θεωρούνται
&lt;i&gt;δικές σου&lt;/i&gt;, ακόμα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="430"/>
        <source>Dashboard</source>
        <translation>Πίνακας Ελέγχου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1319"/>
        <source>Send Bitcoins</source>
        <translation>Αποστολή Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1320"/>
        <source>Receive Bitcoins</source>
        <translation>Παραλαβή Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="446"/>
        <source>Wallet Properties</source>
        <translation>Ιδιότητες Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="447"/>
        <source>Offline Transactions</source>
        <translation>Αποσυνδεδεμένες Συναλλαγές</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="448"/>
        <source>Lockboxes (Multi-Sig)</source>
        <translation>Κουτιά (Πολλαπλών-Υπογραφών)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="505"/>
        <source>&amp;File</source>
        <translation>&amp;Αρχείο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="506"/>
        <source>&amp;User</source>
        <translation>&amp;Χρήστης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="507"/>
        <source>&amp;Tools</source>
        <translation>&amp;Εργαλεία</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="508"/>
        <source>&amp;Addresses</source>
        <translation>&amp;Διευθύνσεις</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="509"/>
        <source>&amp;Wallets</source>
        <translation>&amp;Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="510"/>
        <source>&amp;MultiSig</source>
        <translation>&amp;Πολλαπλές-Υπογραφές</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="511"/>
        <source>&amp;Help</source>
        <translation>&amp;Βοήθεια</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="517"/>
        <source>Transactions Unavailable</source>
        <translation>Συναλλαγές Μη Διαθέσιμες</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="517"/>
        <source>Transaction history cannot be collected until Armory is
               in online mode.  Please try again when Armory is online. </source>
        <translation>Το ιστορικό συναλλαγών δεν μπορεί να συλλεχθεί μέχρι το Armory να είναι
σε λειτουργία σύνδεσης. Δοκιμάστε ξανά όταν το Armory είναι συνδεδεμένο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="577"/>
        <source>
               Bitcoin Core is not available, so Armory will not be able
               to broadcast any transactions for you.</source>
        <translation>
Το Bitcoin Core δεν είναι διαθέσιμο, έτσι το Armory δεν θα μπορεί
να στείλει συναλλαγές για εσάς.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="585"/>
        <source>&amp;Message Signing/Verification...</source>
        <translation>&amp;Υπογραφή Μυνήματος/Πιστοποίηση...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="587"/>
        <source>&amp;EC Calculator...</source>
        <translation>&amp;Υπολογισμός...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="588"/>
        <source>&amp;Broadcast Raw Transaction...</source>
        <translation>&amp;Μετάδοση Ωμής Συναλλαγής...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4978"/>
        <source>Offline</source>
        <translation>Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="597"/>
        <source>
               Armory is currently offline, and cannot determine what funds are
               available for simulfunding.  Please try again when Armory is in
               online mode.</source>
        <translation>
Το Armory είναι αυτή τη στιγμή αποσυνδεδεμένο, και δεν μπορεί να καθορίσει ποιά ποσά
είναι διαθέσιμα για την χρηματοδότηση. Παρακαλώ δοκιμάστε ξανά όταν το Armory θα
είναι συνδεδεμένο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="606"/>
        <source>Import Multi-Spend Transaction</source>
        <translation>Εισαγωγή Συναλλαγής Πολλαπλών-Εξόδων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="607"/>
        <source>
            Import a signature-collector text block for review and signing.
            It is usually a block of text with &quot;TXSIGCOLLECT&quot; in the first line,
            or a &lt;i&gt;*.sigcollect.tx&lt;/i&gt; file.</source>
        <translation>
Εισάγετε ένα μπλόκ κειμένου συλλογής υπογραφών για αναθεώση και υπογραφή.
Συνήθως είναι ένα μπλόκ με το κείμενο &quot;TXSIGCOLLECT&quot; στην πρώτη γραμμή,
ή ένα αρχείο &lt;i&gt;*.sigcollect.tx&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="620"/>
        <source>Simulfund &amp;Promissory Note</source>
        <translation>Simulfund &amp;Γραμμάτιο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="621"/>
        <source>Simulfund &amp;Collect &amp;&amp; Merge</source>
        <translation>Simulfund &amp;Συλλογή &amp;&amp;Συγχώνευση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="622"/>
        <source>Simulfund &amp;Review &amp;&amp; Sign</source>
        <translation>Simulfund &amp;Αναθεώρηση &amp;&amp;Υπογραφή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="629"/>
        <source>View &amp;Address Book...</source>
        <translation>Δείτε το &amp;Βιβλίο Διευθύνσεων...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="630"/>
        <source>&amp;Sweep Private Key/Address...</source>
        <translation>&amp;Σαρώστε το Ιδιωτικό Κλειδί/Διεύθυνση...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="631"/>
        <source>&amp;Import Private Key/Address...</source>
        <translation>&amp;Εισάγετε το Ιδιωτικό Κλειδί/Διεύθυνση...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="638"/>
        <source>&amp;Create New Wallet</source>
        <translation>&amp;Δημιουργία Νέου Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="639"/>
        <source>&amp;Import or Restore Wallet</source>
        <translation>&amp;Εισαγωγή ή Επαναφορά Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="640"/>
        <source>View &amp;Address Book</source>
        <translation>Δείτε το &amp;Βιβλίο Διευθύνσεων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="641"/>
        <source>&amp;Fix Damaged Wallet</source>
        <translation>&amp;Επιδιόρθωση Χαλασμένου Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="658"/>
        <source>&amp;About Armory...</source>
        <translation>&amp;Σχετικά με το Armory...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="661"/>
        <source>Verify Signed Package...</source>
        <translation>Πιστοποίηση Υπογεγραμμένου Πακέτου...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="664"/>
        <source>Clear All Unconfirmed</source>
        <translation>Διαγραφή όλων των Ανεπιβεβαίωτων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="665"/>
        <source>Rescan Databases</source>
        <translation>Επανασάρωση Βάσεων Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="666"/>
        <source>Rebuild and Rescan Databases</source>
        <translation>Αναδόμηση και Επανασάρωση Βάσεων Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="667"/>
        <source>Rescan Balance</source>
        <translation>Επανασάρωση Υπολοίπου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="668"/>
        <source>Factory Reset</source>
        <translation>Επαναφορά στις Εργοστασιακές Ρυθμίσεις</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="690"/>
        <source>Multi-Sig Lockboxes</source>
        <translation>Κουτιά Πολλαπλών Υπογραφών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="691"/>
        <source>Lockbox &amp;Manager...</source>
        <translation>Διαχειριστής &amp;Κουτιών...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="739"/>
        <source>Default Data Directory</source>
        <translation>Προεπιλεγμένος Κατάλογος Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="739"/>
        <source>
            Armory is using the default data directory because
            the data directory specified in the command line could
            not be found nor created.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="746"/>
        <source>Default Database Directory</source>
        <translation>Προεπιλεγμένος Κατάλογος Βάσης Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="746"/>
        <source>
            Armory is using the default database directory because
            the database directory specified in the command line could
            not be found nor created.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="753"/>
        <source>Bitcoin Directory</source>
        <translation>Φάκελος του Bitcoin </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="765"/>
        <source>
            Armory is using the default Bitcoin directory because
            the Bitcoin director specified in the command line could
            not be found.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="760"/>
        <source>Delete Old DB Directory</source>
        <translation>Διαγραφή Παλαιών Δεδομένων της Βάσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="760"/>
        <source>Armory detected an older version Database.
                  Do you want to delete the old database? Choose yes if 
                  do not think that you will revert to an older version of Armory.</source>
        <translation>Το Armory εντόπισε μια παλιά έκδοση της Βάσης.
Θέλετε να διαγράψετε την παλιά βάση; Επιλέξτε ναι αν
δεν νομίζετε οτι θα επιστρέψετε σε μια παλαιότερη έκδοση του Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1509"/>
        <source>Do not ask this question again</source>
        <translation>Να μην ξαναγίνει αυτή η ερώτηση ξανά</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="958"/>
        <source>Bad Module</source>
        <translation>Κακό Πρόσθετο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="863"/>
        <source>
               The module you attempted to load (%1) is malformed.  It is
               missing attributes that are needed for Armory to load it.
               It will be skipped.</source>
        <translation>
Το πρόσθετο που προσπαθήσατε να φορτώσετε (%1) είναι παραποιημένο. Λείπουν
στοιχεία του που χρειάζεται το Armory για την φόρτωση του.
Θα παραλειφθεί.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="967"/>
        <source>Outdated Module</source>
        <translation>Παλαιό Πρόσθετο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="872"/>
        <source>
               Module &quot;%1&quot; is only specified to work up to Armory version %2.
               You are using Armory version %3.  Please remove the module if
               you experience any problems with it, or contact the maintainer
               for a new version.
               &lt;br&gt;&lt;br&gt;
               Do you want to continue loading the module?</source>
        <translation>
Το πρόσθετο &quot;%1&quot; δουλεύει μόνο με το Armory έκδοση %2.
Χρησιμοποιείτε το Armory έκδοση %3. Παρακαλώ αφαιρέστε το πρόσθετο αν
έχετε προβλήματα με αυτό, ή επικοινωνήστε με τον διαχειριστή του
για μια νέα έκδοση.
&lt;br&gt;&lt;br&gt;
Θέλετε να συνεχίσετε την φόρτωση του πρόσθετου;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="929"/>
        <source>Invalid Module</source>
        <translation>Λάθος Πρόσθετο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="929"/>
        <source>
                  Armory detected the following module which is
                  &lt;font color=%1&gt;&lt;b&gt;invalid&lt;/b&gt;&lt;/font&gt;:
                  &lt;br&gt;&lt;br&gt;
                     &lt;b&gt;Module Name:&lt;/b&gt; %2&lt;br&gt;
                     &lt;b&gt;Module Path:&lt;/b&gt; %3&lt;br&gt;
                  &lt;br&gt;&lt;br&gt;
                  Armory will only run a module from a zip file that
                  has the required stucture.</source>
        <translation>
Το Armory εντόπισε το ακόλουθο πρόσθετο που είναι
&lt;font color=%1&gt;&lt;b&gt;εσφαλμένο&lt;/b&gt;&lt;/font&gt;:
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Όνομα Πρόσθετου:&lt;/b&gt; %2&lt;br&gt;
&lt;b&gt;Διαδρομή Πρόσθετου:&lt;/b&gt; %3&lt;br&gt;
&lt;br&gt;&lt;br&gt;
Το Armory θα εκτελέσει ένα πρόσθετο απο ένα αρχείο zip το οποίο
θα έχει την απαιτούμενη δομή.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="939"/>
        <source>UNSIGNED Module</source>
        <translation>ΑΝΥΠΟΓΡΑΦΟ Πρόσθετο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="939"/>
        <source>
                  Armory detected the following module which
                  &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;has not been signed by Armory&lt;/b&gt;&lt;/font&gt; and may be dangerous:
                  &lt;br&gt;&lt;br&gt;
                     &lt;b&gt;Module Name:&lt;/b&gt; %2&lt;br&gt;
                     &lt;b&gt;Module Path:&lt;/b&gt; %3&lt;br&gt;
                  &lt;br&gt;&lt;br&gt;
                  Armory will not allow you to run this module.</source>
        <translation>
Το Armory ανίχνευσε το ακόλουθο πρόσθετο που
&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;δεν έχει υπογραφεί απο το Armory&lt;/b&gt;&lt;/font&gt; και μπορεί
να είναι επικίνδυνο:
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Όνομα Πρόσθετου:&lt;/b&gt; %2&lt;br&gt;
&lt;b&gt;Διαδρομή Πρόσθετου:&lt;/b&gt; %3&lt;br&gt;
&lt;br&gt;&lt;br&gt;
Το Armory δεν θα επιτρέψει την εκτέλεση αυτού του πρόσθετου.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="958"/>
        <source>
                     The module you attempted to load (%1) is malformed.  It is
                     missing attributes that are needed for Armory to load it.
                     It will be skipped.</source>
        <translation>
Το πρόσθετο που προσπαθήσατε να φορτώσετε (%1) είναι παραποιημένο. Λείπουν
στοιχεία του που χρειάζεται το Armory για την φόρτωση του.
Θα παραλειφθεί.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="967"/>
        <source>
                     Module %1 is only specified to work up to Armory version %2.
                     You are using Armory version %3.  Please remove the module if
                     you experience any problems with it, or contact the maintainer
                     for a new version.
                     &lt;br&gt;&lt;br&gt;
                     Do you want to continue loading the module?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1032"/>
        <source>
         The next time you restart Armory, all unconfirmed transactions will
         be cleared allowing you to retry any stuck transactions.</source>
        <translation>
Την επόμενη φορά που θα κάνετε επανεκκίνηση του Armory, όλες οι ανεπιβεβαίωτες 
συναλλαγές θα καθαριστούν επιτρέποντάς σας να προσπαθήσετε ξανά τυχόν κολλήμένες συναλλαγές.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1036"/>
        <source>
         &lt;br&gt;&lt;br&gt;Make sure you also restart Bitcoin Core
         (or bitcoind) and let it synchronize again before you restart
         Armory.  Doing so will clear its memory pool, as well</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1040"/>
        <source>Memory Pool</source>
        <translation>Μνήμη Πισίνας</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1170"/>
        <source>Queue Rescan?</source>
        <translation>Επανασάρωση Ουράς;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1170"/>
        <source>
         The next time you restart Armory, it will rescan the blockchain
         database, and reconstruct your wallet histories from scratch.
         The rescan will take 10-60 minutes depending on your system.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a rescan on the next Armory restart?</source>
        <translation>
Την επόμενη φορά που θα κάνετε επανεκκίνηση του Armory, θα επανεξετάσει την
αλυσίδα συναλλαγών και θα ανακατασκευάσει το ιστορικό του πορτοφολιού σας από το 
μηδέν. Η επανάληψη της σάρωσης θα πάρει 10-60 λεπτά, ανάλογα με σύστημά 
σας. &lt;br&gt;&lt;br&gt;
Θέλετε να αναγκάσετε μια επανάληψη της σάρωσης για την επόμενη φορά που το Armory θα κάνει επανεκκίνηση;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1182"/>
        <source>Queue Rebuild?</source>
        <translation>Ανακατασκευή Ουράς;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1194"/>
        <source>
         The next time you restart Armory, it will rebuild and rescan
         the entire blockchain database.  This operation can take between
         30 minutes and 4 hours depending on you system speed.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a rebuild on the next Armory restart?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1194"/>
        <source>Queue Balance Rescan?</source>
        <translation>Επανασάρωση Υπόλοιπου Ουράς; </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1206"/>
        <source>
         The next time you restart Armory, it will rescan the balance of
         your wallets. This operation typically takes less than a minute
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a balance rescan on the next Armory restart?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1234"/>
        <source>Select Wallet</source>
        <translation>Επιλογή Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1220"/>
        <source>You must import an address into a specific wallet.  If you do not want to import the key into any available wallet, it is recommeneded you make a new wallet for this purpose.&lt;br&gt;&lt;br&gt;Double-click on the desired wallet from the main window, then click on &quot;Import/Sweep Private Keys&quot; on the bottom-right of the properties window.&lt;br&gt;&lt;br&gt;Keys cannot be imported into watching-only wallets, only full wallets.</source>
        <translation>Πρέπει να επιλέξετε ένα πορτοφόλι μέσα στο οποίο η σάρωση θα τοποθετήσει τα ποσά. Κάντε διπλό κλικ στο επιθυμητό πορτοφόλι από το κύριο παράθυρο, και στη συνέχεια, κάντε κλικ στο &quot;Εισαγωγή/Σάρωση Ιδιωτικών Κλειδιών&quot; στο κάτω δεξιά μέρος του παραθύρου ιδιοτήτων για να σαρώσετε σε αυτό το πορτοφόλι. &lt;br&gt;&lt;br&gt; Τα κλειδιά δεν μπορεί να σαρωθούν σε πορτοφόλια που είναι μόνο για παρακολούθηση, παρα μόνο σε πλήρη πορτοφόλια.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1234"/>
        <source>You must select a wallet into which funds will be swept. Double-click on the desired wallet from the main window, then click on &quot;Import/Sweep Private Keys&quot; on the bottom-right of the properties window to sweep to that wallet.&lt;br&gt;&lt;br&gt;Keys cannot be swept into watching-only wallets, only full wallets.</source>
        <translation>Πρέπει να επιλέξετε ένα πορτοφόλι μέσα στο οποίο η σάρωση θα τοποθετήσει τα ποσά. Κάντε διπλό κλικ στο επιθυμητό πορτοφόλι από το κύριο παράθυρο, και στη συνέχεια, κάντε κλικ στο &quot;Εισαγωγή/Σάρωση Ιδιωτικών Κλειδιών&quot; στο κάτω δεξιά μέρος του παραθύρου ιδιοτήτων για να σαρώσετε σε αυτό το πορτοφόλι. &lt;br&gt; Τα κλειδιά δεν μπορεί να σαρωθούν σε πορτοφόλια που είναι μόνο για παρακολούθηση, παρα μόνο σε πλήρη πορτοφόλια.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1318"/>
        <source>Show Armory</source>
        <translation>Εμφάνιση του Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1321"/>
        <source>Quit Armory</source>
        <translation>Έξοδος απο το Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1509"/>
        <source>Default URL Handler</source>
        <translation>Προεπιλεγμένο Πρόγραμμα Χειρισμού URL</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1438"/>
        <source>Armory is not set as your default application for handling
                  &quot;bitcoin:&quot; links.  Would you like to use Armory as the 
                  default?</source>
        <translation>Το Armory δεν έχει οριστεί ως η προεπιλεγμένη εφαρμογή για διαχείριση
&quot;Bitcoin:&quot; συνδέσεων. Θα θέλατε να χρησιμοποιήσετε το Armory σαν
προεπιλογή;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1509"/>
        <source>Armory is not set as your default application for handling
               &quot;bitcoin:&quot; links.  Would you like to use Armory as the 
               default?</source>
        <translation>Το Armory δεν έχει οριστεί ως η προεπιλεγμένη εφαρμογή για διαχείριση
&quot;bitcoin:&quot; συνδέσεων. Θα θέλατε να χρησιμοποιήσετε το Armory σαν
προεπιλογή;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1562"/>
        <source>Version Warning</source>
        <translation>Προειδοποίηση Έκδοσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1562"/>
        <source>
            Since Armory version 0.92 the formats for offline transaction
            operations has changed to accommodate multi-signature
            transactions.  This format is &lt;u&gt;not&lt;/u&gt; compatible with
            versions of Armory before 0.92.
            &lt;br&gt;&lt;br&gt;
            To continue, the other system will need to be upgraded to
            to version 0.92 or later.  If you cannot upgrade the other
            system, you will need to reinstall an older version of Armory
            on this system.</source>
        <translation>
Από το Armory έκδοση 0.92 οι μορφές για τις συναλλαγές εκτός
σύνδεσης έχουν αλλάξει για να φιλοξενήσουν πολλές-υπογραφές
και συναλλαγές. Αυτή η μορφή είναι &lt;u&gt; δεν &lt;/u&gt; είναι συμβατή με
εκδόσεις του Armory πριν την 0.92.
&lt;br&gt;&lt;br&gt;
Για να συνεχίσετε, το άλλο σύστημα θα πρέπει να αναβαθμιστεί
στην έκδοση 0.92 ή σε νεότερη. Εάν δεν μπορείτε να αναβαθμίσετε το άλλο
σύστημα, θα χρειαστεί να επανεγκαταστήσετε μια παλαιότερη έκδοση του Armory
σε αυτό το σύστημα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1562"/>
        <source>Do not show this warning again</source>
        <translation>Να μήν εμφανίζεται το μύνημα προειδοποίησης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1596"/>
        <source>No Tools Yet!</source>
        <translation>Δεν Υπάρχουν Εργαλεία Ακόμα!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1596"/>
        <source>The developer tools are not available yet, but will be added
         soon.  Regardless, developer-mode still offers lots of 
         extra information and functionality that is not available in 
         Standard or Advanced mode.</source>
        <translation>Τα εργαλεία προγραμματισμού δεν είναι ακόμη διαθέσιμα, αλλά θα προστεθούν
σύντομα. Ανεξάρτητα απο αυτό, η λειτουργία προγραμματιστή προσφέρει ακόμα πολλές
πρόσθετες πληροφορίες και λειτουργίες που δεν είναι διαθέσιμες στον
Πρότυπο ή τον Προχωρημένο τρόπο λειτουργίας.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1636"/>
        <source>Root Pubkey Text Files (*.rootpubkey)</source>
        <translation>Αρχεία Κειμένου Root Pubkey (*.rootpubkey)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1656"/>
        <source>Aborted</source>
        <translation>Ακυρώθηκε</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1668"/>
        <source>
                  No passphrase was selected for the encrypted backup.
                  No backup was created</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1668"/>
        <source>Backup Complete</source>
        <translation>Ολοκληρώθηκε το Αντίγραφο Ασφαλείας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1668"/>
        <source>
         Your wallet was successfully backed up to the following
         location:&lt;br&gt;&lt;br&gt;%1</source>
        <translation>
Το πορτοφόλι σας έφτιαξε αντίγραφο ασφαλείας επιτυχώς στην ακόλουθη
θέση:&lt;br&gt;&lt;br&gt;%1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1731"/>
        <source>Restart Armory</source>
        <translation>Επανεκκίνηση του Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1716"/>
        <source>You may have to restart Armory for all aspects of
         the new usermode to go into effect.</source>
        <translation>Μπορεί να χρειάζετε επανεκκίνηση του Armory ώστε όλες οι πτυχές
του νέου χρήστη να μπούν σε λειτουργία.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1731"/>
        <source>You will have to restart Armory for the new language to go into effect</source>
        <translation>Θα πρέπει να επανεκκινήσετε το Armory ώστε η νέα γλώσσα να τεθεί σε ισχύ</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1752"/>
        <source>Invalid Date Format</source>
        <translation>Λάθος Μορφή Ημερομηνίας</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1752"/>
        <source>The date format you specified was not valid.  Please re-enter
            it using only the strftime symbols shown in the help text.</source>
        <translation>Η μορφή της ημερομηνίας που εισάγατε δεν είναι σωστή. Παρακαλώ εισάγετε
την πάλι χρησιμοποιώντας τα σύμβολα strftime όπως εμφανίζονται στο κείμενο βοήθειας.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1779"/>
        <source>Already Open</source>
        <translation>Ήδη Ανοικτό</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1779"/>
        <source>
               Armory is already running!  You can only have one Armory open
               at a time.  Exiting...</source>
        <translation>
Το Armory εκτελείται! Μπορείτε να έχετε το Armory ανοιχτό
μόνο μια φορά. Έξοδος...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1926"/>
        <source>No URL String</source>
        <translation>Δεν Υπάρχει Διεύθυνση URL </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1926"/>
        <source>You have not entered a URL String yet.
               Please go back and enter a URL String.</source>
        <translation>Δεν έχετε εισάγει Διεύθυνση URL ακόμα.
Παρακαλώ πάτε πίσω και εισάγετε URL Διεύθυνση.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2027"/>
        <source>clicked</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1937"/>
        <source>entered</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3335"/>
        <source>Offline Mode</source>
        <translation>Λειτουργία Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1948"/>
        <source>You %1 on a &quot;bitcoin:&quot; link, but Armory is in
            offline mode, and is not capable of creating transactions. 
            Using links will only work if Armory is connected 
            to the Bitcoin network!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1957"/>
        <source>It looks like you just %1 a &quot;bitcoin:&quot; link, but
                    that link is malformed.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1960"/>
        <source>Please check the source of the link and enter the
                        transaction manually.</source>
        <translation>Παρακαλώ δείτε την πηγή του συνδέσμου και εισάγετε την
συναλλαγή χειροκίνητα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1963"/>
        <source>The raw URI string is:

</source>
        <translation>Το νέο κείμενο URI είναι:

</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1964"/>
        <source>Invalid URI</source>
        <translation>Λάθος URI</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1969"/>
        <source>The &quot;bitcoin:&quot; link you just %1
            does not even contain an address!  There is nothing that 
            Armory can do with this link!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1981"/>
        <source>Wrong Network!</source>
        <translation>Λάθος Δίκτυο!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1981"/>
        <source>The address for the &quot;bitcoin:&quot; link you just %1 is
            for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
            and the address you supplied is for the 
            &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1994"/>
        <source>Unsupported URI</source>
        <translation>Μη υποστηριζόμενο URI</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1994"/>
        <source>The &quot;bitcoin:&quot; link
               you just %1 contains fields that are required but not
               recognized by Armory.  This may be an older version of Armory,
               or the link you %2 on uses an exotic, unsupported format.
               &lt;br&gt;&lt;br&gt;The action cannot be completed.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2011"/>
        <source>You just clicked on a &quot;bitcoin:&quot; link, but Armory is offline
            and cannot send transactions.  Please click the link 
            again when Armory is online.</source>
        <translation>Πατήσατε πάνω σε ένα σύνδεσμο &quot;bitcoin:&quot;, αλλά το Armory είναι εκτός σύνδεσης
και δεν μπορεί να στείλει συναλλαγές. Παρακαλώ κάντε κλίκ στο σύνδεσμο
όταν το Armory θα είναι συνδεδεμένο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2254"/>
        <source>All files (*)</source>
        <translation>Όλα τα αρχεία (*)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2397"/>
        <source>Contributor &quot;%1&quot; (%2)</source>
        <translation>Συνεισφέρων &quot;%1&quot; (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2399"/>
        <source>Contributor %1</source>
        <translation>Συνεισφέρων %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2402"/>
        <source>Contributor &quot;%1&quot;</source>
        <translation>Συνεισφέρων &quot;%1&quot;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2404"/>
        <source>Unknown Contributor</source>
        <translation>Άγνωστος Συντελεστής</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2469"/>
        <source>Blockchain loaded, wallets sync&apos;d!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2475"/>
        <source>Blockchain Loaded!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2475"/>
        <source>Blockchain loading is complete.
            Your balances and transaction history are now available 
            under the &quot;Transactions&quot; tab.  You can also send and 
            receive bitcoins.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2475"/>
        <source>Do not show me this notification again </source>
        <translation>Να μήν εμφανίζεται το μύνημα προειδοποίησης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2562"/>
        <source>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Maximum Funds:&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Μέγιστα Ποσά:&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2655"/>
        <source>***MEMPOOL REPLACEABLE*** </source>
        <translation>***ΕΝΑΛΛΑΓΗ ΜΝΗΜΗΣ ΠΙΣΙΝΑΣ***</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2696"/>
        <source>My Wallets</source>
        <translation>Τα Πορτοφόλια μου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2697"/>
        <source>Offline Wallets</source>
        <translation>Εκτός Σύνδεσης Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2698"/>
        <source>Other&apos;s wallets</source>
        <translation>Άλλα Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2699"/>
        <source>All Wallets</source>
        <translation>Όλα τα Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2700"/>
        <source>Custom Filter</source>
        <translation>Ειδικά Φίλτρα</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3442"/>
        <source>No Wallets!</source>
        <translation>Δεν υπάρχουν πορτοφόλια!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2711"/>
        <source>You currently do not have any wallets.  Would you like to
            create one, now?</source>
        <translation>Δεν έχετε πορτοφόλια. Θα θέλατε να
δημιουργήσετε ένα, τώρα;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2724"/>
        <source>Select a Wallet</source>
        <translation>Επιλέξτε ένα Πορτοφόλι</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2724"/>
        <source>Please select a wallet on the right, to see its properties.</source>
        <translation>Παρακαλώ επιλέξτε ενα πορτοφόλι στα δεξιά, για να δείτε τις ιδιότητες του.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2760"/>
        <source>Transaction</source>
        <translation>Συναλλαγή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2775"/>
        <source>Address</source>
        <translation>Διεύθυνση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2936"/>
        <source>Already Sweeping</source>
        <translation>Ήδη Σαρώνεται</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2936"/>
        <source>You are already in the process of scanning the blockchain for
            the purposes of sweeping other addresses.  You cannot initiate 
            sweeping new addresses until the current operation completes. 
            &lt;br&gt;&lt;br&gt;
            In the future, you may select &quot;Multiple Keys&quot; when entering 
            addresses to sweep.  There is no limit on the number that can be 
            specified, but they must all be entered at once.</source>
        <translation>Είστε ήδη στη διαδικασία της σάρωσης της αλυσίδας για
τους σκοπούς της σάρωσης άλλων διευθύνσεων. Δεν μπορείτε να ξεκινήσει
νέα σάρωση διευθύνσεων μέχρι να ολοκληρωθεί η τρέχουσα λειτουργία. 
&lt;br&gt;&lt;br&gt;
Στο μέλλον, μπορείτε να επιλέξετε &quot;Πολλαπλά Κλειδιά&quot; κατά την είσοδο
διευθύνσεων προς σάρωση. Δεν υπάρχει όριο στον αριθμό που
διευκρινίζεται, αλλά πρέπει όλοι να εισαχθούν ταυτόχρονα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3017"/>
        <source>addresses</source>
        <translation>διευθύνσεις</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3017"/>
        <source>address</source>
        <translation>διεύθυνση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2958"/>
        <source>Armory is Offline</source>
        <translation>Το Armory είναι Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2958"/>
        <source>You have chosen to sweep %1 %2, but Armory is currently
            in offline mode.  The sweep will be performed the next time you 
            go into online mode.  You can initiate online mode (if available) 
            from the dashboard in the main window.</source>
        <translation>Έχετε επιλέξει να σαρώσετε %1%2, αλλά το Armory είναι σε λειτουργία
χωρίς σύνδεση. Η σάρωση θα πραγματοποιηθεί την επόμενη φορά που θα είναι σε
λειτουργία σύνδεσης. Μπορείτε να ξεκινήσετε σε λειτουργία σύνδεσης (εάν είναι διαθέσιμη)
από το ταμπλό στο κύριο παράθυρο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2966"/>
        <source>Armory must scan the global transaction history in order to
            find any bitcoins associated with the %1 you supplied.
            Armory will go into offline mode temporarily while the scan 
            is performed, and you will not have access to balances or be 
            able to create transactions.  The scan may take several minutes.
            &lt;br&gt;&lt;br&gt;</source>
        <translation>Το Armory πρέπει να σαρώσει την παγκόσμια ιστορία των συναλλαγών, προκειμένου να
βρούμε τα bitcoin που συνδέονται με το %1 που μας δώσατε.
Το Armory θα μεταβεί σε κατάσταση εκτός σύνδεσης προσωρινά, όσο γίνεται η σάρωση
και δεν θα έχετε πρόσβαση στα υπόλοιπα και δεν θα είστε σε θέση να δημιουργήσετε συναλλαγές. Η σάρωση μπορεί να διαρκέσει αρκετά λεπτά.
&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2975"/>
        <source>There is currently another scan operation being performed.
               Would you like to start the sweep operation after it completes? </source>
        <translation>Υπάρχει ήδη μια άλλη λειτουργία σάρωσης σε εξέλιξη.
Θα θέλατε να ξεκινήσετε τη λειτουργία σάρωσης μετά την ολοκλήρωση;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2979"/>
        <source>&lt;b&gt;Would you like to start the scan operation right now?&lt;/b&gt;</source>
        <translation>&lt;b&gt;Θα θέλατε να ξεκινήσει η λειτουργία σάρωσης τώρα;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2982"/>
        <source>&lt;br&gt;&lt;br&gt;Clicking &quot;No&quot; will abort the sweep operation</source>
        <translation>&lt;br&gt;&lt;br&gt;Πατώντας &quot;Όχι&quot; θα ακυρώσει την διαδικασία σάρωσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2984"/>
        <source>Confirm Rescan</source>
        <translation>Επιβεβαίωση Επανασάρωσης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3011"/>
        <source>Nothing to do</source>
        <translation>Δεν υπάρχει κάτι να γίνει</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3023"/>
        <source>The private %1 you have provided does not appear to contain
               any funds.  There is nothing to sweep.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3023"/>
        <source>keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3023"/>
        <source>key</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3018"/>
        <source>Cannot sweep</source>
        <translation>Δεν μπορεί να σαρωθεί</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3033"/>
        <source>multiple addresses</source>
        <translation>πολλαπλές διευθύνσεις</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3035"/>
        <source>address &lt;b&gt;%1&lt;/b&gt;</source>
        <translation>διεύθυνση &lt;b&gt;%1&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3037"/>
        <source>wallet &lt;b&gt;&quot;%1&quot;&lt;/b&gt; (%2) </source>
        <translation>πορτοφόλι &lt;b&gt;&quot;%1&quot;&lt;/b&gt; (%2) </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3080"/>
        <source>Broadcast failed</source>
        <translation>Η Μετάδοση απέτυχε</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3080"/>
        <source>
                  The broadcast process failed unexpectedly. Report this error to
                  the development team if this issue occurs repeatedly
                  </source>
        <translation>
Η μετάδοση απέτυχε απρόσμενα. Αναφέρεται αυτό το
σφάλμα στην ομάδα ανάπτυξης αν σας συμβαίνει συχνά</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3102"/>
        <source>Transaction Not Accepted</source>
        <translation>Η Συναλλαγή Δεν Έγινε Δεκτή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3102"/>
        <source>
                  The transaction that you just executed failed with 
                  the following error message: &lt;br&gt;&lt;br&gt;
                  &lt;b&gt;%1&lt;/b&gt;
                  &lt;br&gt;&lt;br&gt;
                  
                  
                  &lt;br&gt;&lt;br&gt;On time out errors, the transaction may have actually succeed
                  and this message is displayed prematurely.  To confirm whether the
                  the transaction actually succeeded, you can try this direct link
                  to %2:
                  &lt;br&gt;&lt;br&gt;
                  &lt;a href=&quot;%3&quot;&gt;%4...&lt;/a&gt;
                  &lt;br&gt;&lt;br&gt;
                  If you do not see the
                  transaction on that webpage within one minute, it failed and you
                  should attempt to re-send it.
                  If it &lt;i&gt;does&lt;/i&gt; show up, then you do not need to do anything
                  else -- it will show up in Armory as soon as it receives one
                  confirmation.
                  &lt;br&gt;&lt;br&gt;If the transaction did fail, it is likely because the fee
                  is too low. Try again with a higher fee.

                  If the problem persists, go to &quot;&lt;i&gt;File&lt;/i&gt;&quot; -&gt;
                  &quot;&lt;i&gt;Export Log File&lt;/i&gt;&quot; and then attach it to a support
                  ticket at
                  &lt;a href=&quot;%5&quot;&gt;%5&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3138"/>
        <source>In the future, you may avoid scanning twice by starting Armory in offline mode (--offline), and perform the import before switching to online mode.</source>
        <translation>Στο μέλλον, μπορείτε να αποφύγετε τη σάρωση δύο φορές με την έναρξη του Armory σε λειτουργία εκτός σύνδεσης (--offline), και να εκτελέσετε την εισαγωγή πριν από τη μετάβαση στη λειτουργία σύνδεσης.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3142"/>
        <source>Armory is Busy</source>
        <translation>Το Armory είναι Απασχολημένο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3142"/>
        <source>Wallets and addresses cannot be imported while Armory is in the middle of an existing blockchain scan.  Please wait for the scan to finish.  </source>
        <translation>Τα πορτοφόλια και οι διευθύνσεις δεν μπορούν να εισαχθούν όσο το Armory κάνει ανάγνωση της αλυσίδας συναλλαγών. Παρακαλώ περιμένετε να τελειώσει η ανάγνωση.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3156"/>
        <source>Scanning</source>
        <translation>Ανάγνωση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3156"/>
        <source>
            Armory is currently in the middle of scanning the blockchain for
            your existing wallets.  New wallets cannot be imported until this
            operation is finished.</source>
        <translation>
</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3176"/>
        <source>Duplicate Wallet!</source>
        <translation>Διπλό Πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3176"/>
        <source>
            You selected a wallet that has the same ID as one already 
            in your wallet (%1)!  If you would like to import it anyway,
            please delete the duplicate wallet in Armory, first.</source>
        <translation>
Επιλέξατε ένα πορτοφόλι που έχει την ίδια ταυτότητα με ένα
που είναι ήδη στο πορτοφόλι σας (%1)! Αν θέλετε να κάνετε εισαγωγή ούτως ή άλλως,
παρακαλώ διαγράψτε το διπλό πορτοφόλι απο το Armory, πρώτα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3195"/>
        <source>Be Careful!</source>
        <translation>Προσοχή!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3195"/>
        <source>
        &lt;font color=&quot;red&quot;&gt;&lt;b&gt;WARNING:&lt;/b&gt;&lt;/font&gt; You are about to make an
        &lt;u&gt;unencrypted&lt;/u&gt; backup of your wallet.  It is highly recommended
        that you do &lt;u&gt;not&lt;/u&gt; ever save unencrypted wallets to your regular
        hard drive.  This feature is intended for saving to a USB key or
        other removable media.</source>
        <translation>
&lt;font color=&quot;red&quot;&gt;&lt;b&gt;ΠΡΟΣΟΧΗ:&lt;/b&gt;&lt;/font&gt; Πρόκειτε να φτιάξεις ένα
&lt;u&gt;μη κρυπτογραφημένο&lt;/u&gt; αντίγραφο ασφαλείας του πορτοφολιού. Προτείνεται
να &lt;u&gt;μην&lt;/u&gt; αποθηκεύεις μη κρυπτογραφημένα αντίγραφα πορτοφολιών
στον κανονικό σκληρό σου δίσκο. Αυτή η λειτουργία προορίζεται για συσκευές USB
ή άλλα αφαιρούμενα μέσα.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3212"/>
        <source>Blockchain Not Ready</source>
        <translation>Η Αλυσίδα Συναλλαγών Δεν Είναι Έτοιμη</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3207"/>
        <source>
            The address book is created from transaction data available in 
            the blockchain, which has not finished loading.  The address 
            book will become available when Armory is online.</source>
        <translation>
Το βιβλίο διευθύνσεων δημιουργείται από τα δεδομένα των συναλλαγών που 
είναι διαθέσιμα στην αλυσίδα, της οποίας η φόρτωση δεν έχει ολοκληρωθεί. Το βιβλίο
διευθύνσεων θα γίνει διαθέσιμο όταν το Armory είναι σε λειτουργία σύνδεσης.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3212"/>
        <source>
            The address book is created from transaction data available in 
            the blockchain, but Armory is currently offline.  The address 
            book will become available when Armory is online.</source>
        <translation>
Το βιβλίο διευθύνσεων δημιουργείται από τα δεδομένα των συναλλαγών διαθέσιμα στην
αλυσίδα, αλλά το Armory είναι τώρα εκτός σύνδεσης. Το βιβλίο
διευθύνσεων θα γίνει διαθέσιμο όταν το Armory είναι σε λειτουργία σύνδεσης.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3218"/>
        <source>No wallets!</source>
        <translation>Δεν υπάρχουν πορτοφόλια!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3218"/>
        <source>You have no wallets so
               there is no address book to display.</source>
        <translation>Δεν έχετε πορτοφόλι οπότε
δεν υπάρχει βιβλίο διευθύνσεων προς εμφάνιση.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3270"/>
        <source>Invalid Tx</source>
        <translation>Λάθος Συναλλαγή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3270"/>
        <source>
         The transaction you requested be displayed does not exist in 
         Armory&apos;s database.  This is unusual...</source>
        <translation>
Η συναλλαγή που θέλετε να εμφανιστεί δεν υπάρχει στη 
βάση δεδομένων του Armory. Αυτό είναι ασυνήθιστο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3292"/>
        <source>View Details</source>
        <translation>Δείτε Λεπτομέρειες</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3293"/>
        <source>View on %1</source>
        <translation>Δείτε το %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3294"/>
        <source>Change Comment</source>
        <translation>Αλλαγή Σχολίου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3295"/>
        <source>Copy Transaction ID</source>
        <translation>Αντιγραφή Ταυτότητας Συναλλαγής</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3296"/>
        <source>Open Relevant Wallet</source>
        <translation>Ανοίξτε το Σχετικό Πορτοφόλι</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3306"/>
        <source>Could not open browser</source>
        <translation>Δεν μπορέσαμε να ανοίξουμε τον Φυλλομετρητή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3306"/>
        <source>
               Armory encountered an error opening your web browser.  To view 
               this transaction on blockchain.info, please copy and paste 
               the following URL into your browser: 
               &lt;br&gt;&lt;br&gt;%1</source>
        <translation>
Το Armory αντιμετώπισε ένα πρόβλημα στο άνοιγμα του φυλλομετρητή σας. Για να
δείτε την συναλλαγή στο blockchain.info, παρακαλώ αντιγράψτε τον παρακάτω
σύνδεσμο στον φυλλομετρητή σας:
&lt;br&gt;&lt;br&gt;%1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3335"/>
        <source>
           Armory is currently running in offline mode, and has no 
           ability to determine balances or create transactions. 
           &lt;br&gt;&lt;br&gt;
           In order to send coins from this wallet you must use a 
           full copy of this wallet from an online computer, 
           or initiate an &quot;offline transaction&quot; using a watching-only 
           wallet on an online computer.</source>
        <translation>
Το Armory εκτελείται σε λειτουργία εκτός σύνδεσης, και δεν έχει
την δυνατότητα να καθορίσει τα ποσά ή να δημιουργήσει συναλλαγές.
 &lt;br&gt;&lt;br&gt;
Για να στείλετε νομίσματα από αυτό το πορτοφόλι θα πρέπει να χρησιμοποιήσετε ένα
πλήρες αντίγραφο αυτού του πορτοφολιού από ένα ηλεκτρονικό υπολογιστή,
ή να ξεκινήσετε μια &quot;συναλλαγή εκτός σύνδεσης&quot; χρησιμοποιώντας ένα πορτοφόλι
παρατήρησης σε έναν συνδεδεμένο με το διαδίκτυο υπολογιστή.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3345"/>
        <source>Armory Not Ready</source>
        <translation>Το Armory Δεν Είναι Έτοιμο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3345"/>
        <source>
           Armory is currently scanning the blockchain to collect 
           the information needed to create transactions.  This typically 
           takes between one and five minutes.  Please wait until your 
           balance appears on the main window, then try again.</source>
        <translation>
Το Armory κάνει σάρωση της αλυσίδας για να συλλέξει
τις πληροφορίες που απαιτούνται για τη δημιουργία των συναλλαγών. Αυτό συνήθως
παίρνει μεταξύ ενός και πέντε λεπτών. Παρακαλώ περιμένετε μέχρι
το υπόλοιπο σας να εμφανιστεί στο κύριο παράθυρο, και στη συνέχεια, δοκιμάστε ξανά.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3355"/>
        <source>
            You cannot send any bitcoins until you create a wallet and 
            receive some coins.  Would you like to create a wallet?</source>
        <translation>
Δεν μπορείτε να στείλετε bitcoin μέχρι να δημιουργήσετε ένα πορτοφόλι και
να λάβετε κάποια νομίσματα. Θα θέλατε να δημιουργήσετε ένα πορτοφόλι;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3386"/>
        <source>You just clicked on a &quot;bitcoin:&quot; link requesting bitcoins
                to be sent to the following address:&lt;br&gt; </source>
        <translation>Μόλις κάνατε κλίκ πάνω σε ένα σύνδεσμο &quot;bitcoin:&quot; ζητώντας bitcoin
να αποσταλούν στην ακόλουθη διεύθυνση:&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3389"/>
        <source>&lt;br&gt;--&lt;b&gt;Address&lt;/b&gt;:<byte value="x9"/>%1 </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3401"/>
        <source>&lt;br&gt;--&lt;b&gt;Amount&lt;/b&gt;:<byte value="x9"/>%1 BTC</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3406"/>
        <source>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3408"/>
        <source>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3413"/>
        <source>&lt;br&gt;&lt;br&gt;There is no amount specified in the link, so
            you can decide the amount after selecting a wallet to use 
            for this transaction. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3417"/>
        <source>&lt;br&gt;&lt;br&gt;&lt;b&gt;The specified amount &lt;u&gt;can&lt;/u&gt; be changed&lt;/b&gt; on the
            next screen before hitting the &quot;Send&quot; button. </source>
        <translation>&lt;br&gt;&lt;br&gt;&lt;b&gt;Το καθορισμένο ποσό &lt;u&gt;μπορεί&lt;/u&gt; να αλλάξει&lt;/b&gt; στην επόμενη
οθόνη πριν πατήσετε το κουμπί &quot;Αποστολή&quot;. </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3423"/>
        <source>
            You just clicked on a &quot;bitcoin:&quot; link to send money, but you 
            urrently have no wallets!  Would you like to create a wallet 
            now?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3442"/>
        <source>
            You have not created any wallets which means there is
            nowhere to store you bitcoins!  Would you like to
            create a wallet now?</source>
        <translation>
Δεν έχετε δημιουργήσει κανένα πορτοφόλι που σημαίνει ότι δεν υπάρχει
μέρος για να αποθηκευθούν τα bitcoin σας! Θέλετε να φτιάξετε ένα πορτοφόλι τώρα;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3459"/>
        <source>Receive coins with wallet...</source>
        <translation>Λάβετε νομίσματα με το πορτοφόλι...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3561"/>
        <source>Privacy Warning</source>
        <translation>Προειδοποίηση Ιδιωτικότητας</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3525"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Wallet Analysis Log Files&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         The wallet analysis logs contain no personally-identifiable
         information, only a record of errors and inconsistencies
         found in your wallet file.  No private keys or even public
         keys are included.
         &lt;br&gt;&lt;br&gt;

         &lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Regular Log Files&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         The regular log files do not contain any &lt;u&gt;security&lt;/u&gt;-sensitive
         information, but some users may consider the information to be
         &lt;u&gt;privacy&lt;/u&gt;-sensitive.  The log files may identify some addresses
         and transactions that are related to your wallets.  It is always
         recommended you include your log files with any request to the
         Armory team, unless you are uncomfortable with the privacy
         implications.
         &lt;br&gt;&lt;br&gt;

         &lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Watching-only Wallet&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         A watching-only wallet is a copy of a regular wallet that does not
         contain any signing keys.  This allows the holder to see the balance
         and transaction history of the wallet, but not spend any of the funds.
         &lt;br&gt;&lt;br&gt;
         You may be requested to submit a watching-only copy of your wallet
         to make sure that there is no
         risk to the security of your funds.  You should not even consider
         sending your
         watching-only wallet unless it was specifically requested by an
         Armory representative.</source>
        <translation>
&lt;B&gt; &lt;u&gt; &lt;font size = 3&gt; Πορτοφόλι Ανάλυση αρχείων καταγραφής &lt;/ font&gt; &lt;/ u&gt; &lt;/ b&gt; 
&lt;br&gt; Η 
Οι κορμοί ανάλυση πορτοφόλι δεν περιέχουν προσωπικές αναγνωριστικές
πληροφορίες, μόνο μια καταγραφή των λαθών και εκτροπές
που βρέθηκαν στο αρχείο του πορτοφολιού σας. Τα ιδιωτικά κλειδιά που ακόμα δεν είναι δημόσια δεν συμπεριλαμβάνονται.
&lt;br&gt;&lt;br&gt;

&lt;b&gt; &lt;u&gt; &lt;font size=3&gt; Κανονικά αρχεία καταγραφής &lt;/font&gt; &lt;/u&gt; &lt;/b&gt; 
&lt;br&gt;&lt;br&gt;
Οι τακτικές αρχεία καταγραφής δεν περιέχουν &lt;u&gt; ασφάλειας &lt;/u&gt; ευαίσθητων
πληροφοριών, αλλά ορισμένοι χρήστες μπορεί να εξετάσει τις πληροφορίες που be
&lt;u&gt; Απόρρητο &lt;/u&gt; ευαίσθητου. Τα αρχεία καταγραφής μπορεί να εντοπίσει κάποιες addresses
και τις συναλλαγές που σχετίζονται με τα πορτοφόλια σας. Είναι always
Συνιστάται να περιλαμβάνουν τα αρχεία καταγραφής σας με οποιοδήποτε αίτημα για the
Οπλοστάσιο της ομάδας, εκτός αν είστε άβολα με την ιδιοτικότητα.
&lt;br&gt;&lt;br&gt;

&lt;b&gt; &lt;u&gt; &lt;font size=3&gt; Βλέποντας μόνο Πορτοφόλι &lt;/font&gt; &lt;/u&gt; &lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Μια παρατήρηση μόνο για το πορτοφόλι είναι ένα αντίγραφο ενός κανονικού πορτοφόλι που περιέχει τα κλειδιά υπογραφής. Αυτό επιτρέπει στον κάτοχο να δείτε το υπόλοιπο
και το ιστορικό συναλλαγών του πορτοφολιού, αλλά δεν μπορεί να ξοδέψει κάποιο από τα ποσά.
&lt;br&gt;&lt;br&gt;
Μπορεί να σας ζητηθεί να υποβάλετε μια παρατήρηση μόνο για το αντίγραφο του
πορτοφολιού σας για να βεβαιωθείτε ότι δεν υπάρχει
κίνδυνος για την ασφάλεια των κεφαλαίων σας. Δεν θα έπρεπε καν να σκεφτείται την
αποστολή τους
βλέποντας μόνο το πορτοφόλι, αν σας είχε ζητηθεί ειδικά από έναν εκπρόσωπος του 
Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3561"/>
        <source>

         Armory log files do not contain any &lt;u&gt;security&lt;/u&gt;-sensitive
         information, but some users may consider the information to be
         &lt;u&gt;privacy&lt;/u&gt;-sensitive.  The log files may identify some addresses
         and transactions that are related to your wallets.
         &lt;br&gt;&lt;br&gt;

         &lt;b&gt;No signing-key data is ever written to the log file&lt;/b&gt;.
         Only enough data is there to help the Armory developers
         track down bugs in the software, but it may still be considered
         sensitive information to some users.
         &lt;br&gt;&lt;br&gt;

         Please do not send the log file to the Armory developers if you
         are not comfortable with the privacy implications!  However, if you
         do not send the log file, it may be very difficult or impossible
         for us to help you with your problem. </source>
        <translation>
Τα αρχέια καταγραφής του Armory δεν περιέχουν &lt;u&gt; ασφαλείς &lt;/u&gt; -ευαίσθητες
πληροφορίες, αλλά ορισμένοι χρήστες μπορεί να θεωρήσουν τις πληροφορίες 
&lt;u&gt; απόρρητα &lt;/u&gt; ευαίσθητες. Τα αρχεία καταγραφής μπορεί να εντοπίσουν κάποιες διευθύνσεις και τις συναλλαγές που σχετίζονται με τα πορτοφόλια.&lt;br&gt;&lt;br&gt;


&lt;b&gt; Δεν γράφονται δεδομένα υπογραφής κλειδιών ποτέ στο αρχείο καταγραφής &lt;/b&gt;.
Μόνο αρκετά δεδομένα είναι εκεί για να βοηθήσει τους προγραμματιστές του Armory 
να εντοπίσουν σφάλματα στο λογισμικό, αλλά μπορεί ακόμα και να θεωρηθούν 
ευαίσθητες πληροφορίες για κάποιους χρήστες.

&lt;br&gt;&lt;br&gt;


Παρακαλούμε μην στείλετε το αρχείο καταγραφής του Armory στους δημιουργούς του
αν δεν είστε άνετα με τις επιπτώσεις στην ιδιωτική ζωή! Ωστόσο, εάν 
δεν στείλετε το αρχείο καταγραφής, μπορεί να είναι πολύ δύσκολο ή αδύνατο
να σας βοηθήσουμε με το πρόβλημά σας.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3632"/>
        <source>Already running!</source>
        <translation>Ήδη εκτελείται</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3632"/>
        <source>
               The Bitcoin software appears to be installed now, but it
               needs to be closed for Armory to work.  Would you like Armory
               to close it for you?</source>
        <translation>
Το λογισμικό του Bitcoin φαίνεται να είναι εγκατεστημένο τώρα, αλλά
χρειάζεται να κλείσει ώστε το Armory να λειτουργήσει. Θέλετε το Armory
να το κλείσει για εσάς;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3640"/>
        <source>Still Missing</source>
        <translation>Ακόμα Λείπει</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3640"/>
        <source>
               The Bitcoin software still appears to be missing.  If you
               just installed it, then please adjust your settings to point
               to the installation directory.</source>
        <translation>
Το λογισμικό του Bitcoin φαίνεται ακόμα να λείπει. Αν μόλις
εγκαταστάθηκε, τότε παρακαλούμε να προσαρμόσετε τις ρυθμίσεις σας για να δείχνουν 
στον κατάλογο εγκατάστασης.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3647"/>
        <source>Still Running</source>
        <translation>Ακόμα Τρέχει</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3647"/>
        <source>
               Bitcoin Core is still running.  Armory cannot start until
               it is closed.  Do you want Armory to close it for you?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3761"/>
        <source>Close Bitcoin Process</source>
        <translation>Κλείσιμο της Διεργασίας του Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3762"/>
        <source>Download Bitcoin</source>
        <translation>Λήψη Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3763"/>
        <source>Open https://bitcoin.org</source>
        <translation>Ανοίξτε το https://bitcoin.org</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3764"/>
        <source>Installation Instructions</source>
        <translation>Οδηγίες Εγκατάστασης</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3765"/>
        <source>Change Settings</source>
        <translation>Αλλαγή Ρυθμίσεων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3769"/>
        <source>Preparing to shut down..</source>
        <translation>Προετοιμασία για τερματισμό..</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3801"/>
        <source>Stop existing Bitcoin processes so that Armory can open its own</source>
        <translation>Σταμάτημα των διεργασιών του Bitcoin ώστε το Armory να μπορεί να ανοίξει τις δικές του</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3803"/>
        <source>Open browser to Bitcoin webpage to download and install Bitcoin software</source>
        <translation>Ανοίξτε το πρόγραμμα περιήγησης στην ιστοσελίδα του Bitcoin για να κατεβάσετε και να εγκαταστήσετε το λογισμικό Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3805"/>
        <source>Instructions for manually installing Bitcoin for operating system</source>
        <translation>Οδηγίες για μη αυτόματη εγκατάσταση του Bitcoin για το λειτουργικό σας σύστημα</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3807"/>
        <source>Open Armory settings window to change Bitcoin software management</source>
        <translation>Ανοίξτε τις ρυθμίσεις του Armory για να αλλάξετε το λογισμικό διαχείρησης του Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3811"/>
        <source>
           Will open your default browser to https://bitcoin.org where you can 
           download the latest version of Bitcoin Core, and get other information
           and links about Bitcoin, in general.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3815"/>
        <source>
           Instructions are specific to your operating system and include 
           information to help you verify you are installing the correct software</source>
        <translation>
Οι οδηγίες είναι συγκεκριμένες για το λειτουργικό σας και περιλαμβάνουν
πληροφορίες που θα σας βοηθήσουν να πιστοποιήσετε οτι εγκαθιστάται την σωστή έκδοση λογισμικού</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3818"/>
        <source>
           Change Bitcoin Core/bitcoind management settings or point Armory to
           a non-standard Bitcoin installation</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3821"/>
        <source>
           Armory has detected a running Bitcoin Core or bitcoind instance and
           will force it to exit</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3827"/>
        <source>This option is not yet available yet!</source>
        <translation>Αυτή η επιλογή δεν είναι διαθέσιμη ακόμα!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3834"/>
        <source>Securely download Bitcoin software for Windows %1</source>
        <translation>Ασφαλής λήψη του λογισμικού του Bitcoin για τα Windows %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3836"/>
        <source>
            The downloaded files are cryptographically verified.  
            Using this option will start the installer, you will 
            have to click through it to complete installation.</source>
        <translation>
Τα αρχεία λήψεως είναι πιστοποιήσιμα μέσω κρυπτογράφησης.
Χρησιμοποιώντας την επιλογή θα ξεκινήσει η εγκατάσταση στην
οποία θα χρειαστεί να κάνετε κλίκ για να την ολοκληρώσετε.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3852"/>
        <source>
               Download and Install Bitcoin Core for Ubuntu/Debian</source>
        <translation>
Κάντε λήψη και Εγκαταστήστε το Bitcoin Core για Ubuntu/Debian</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3866"/>
        <source>
               Will download and Bitcoin software and cryptographically verify it</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4265"/>
        <source>Not Found</source>
        <translation>Δεν Βρέθηκε</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4265"/>
        <source>
         Attempted to kill the running Bitcoin Core/bitcoind instance,
         but it was not found.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4336"/>
        <source>Loading Database Headers</source>
        <translation>Φόρτωση Κεφαλίδων Βάσης Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4345"/>
        <source>Organizing Blockchain</source>
        <translation>Οργάνωση Αλυσίδας Συναλλαγών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5090"/>
        <source>Scan Transaction History</source>
        <translation>Σάρωση Ιστορικού Συναλλαγών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4356"/>
        <source>Reading New Block Headers</source>
        <translation>Ανάγνωση Νέων Κεφαλίδων Μπλόκ</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4364"/>
        <source>Building Databases</source>
        <translation>Κατασκευή Βάσεων Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5024"/>
        <source>Build Databases</source>
        <translation>Κατασκευή Βάσεων Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4374"/>
        <source>Scanning Transaction History</source>
        <translation>Σάρωση Ιστορικού Συναλλαγών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4384"/>
        <source>Computing Balances</source>
        <translation>Υπολογισμός Υπολοίπου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4394"/>
        <source>Parsing Tx Hashes</source>
        <translation>Εισαγωγή Κατακερματισμών Συναλλαγών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4408"/>
        <source>Resolving Tx Hashes</source>
        <translation>Επίλυση Κατακερματισμών Συναλλαγών</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4496"/>
        <source>The following functionality is available while scanning in offline mode:&lt;ul&gt;&lt;li&gt;Create new wallets&lt;/li&gt;&lt;li&gt;Generate receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign transactions created from an online system&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, even if you are offline.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4512"/>
        <source>The following functionality is available in offline mode:&lt;ul&gt;&lt;li&gt;Create, import or recover wallets&lt;/li&gt;&lt;li&gt;Generate new receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Import private keys to wallets&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Sign transactions created from an online system&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, regardless of whether you are online.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4517"/>
        <source>&lt;ul&gt;&lt;li&gt;Create, import or recover Armory wallets&lt;/li&gt;&lt;li&gt;Generate new addresses to receive coins&lt;/li&gt;&lt;li&gt;Send bitcoins to other people&lt;/li&gt;&lt;li&gt;Create one-time backups of your wallets (in printed or digital form)&lt;/li&gt;&lt;li&gt;Click on &quot;bitcoin:&quot; links in your web browser (not supported on all operating systems)&lt;/li&gt;&lt;li&gt;Import private keys to wallets&lt;/li&gt;&lt;li&gt;Monitor payments to watching-only wallets and create unsigned transactions&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Create transactions with watching-only wallets, to be signed by an offline wallets&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4543"/>
        <source>
         For more information about Armory, and even Bitcoin itself, you should
         visit the &lt;a href=&quot;https://bitcointalk.org/index.php?board=97.0&quot;&gt;Armory Forum&lt;/a&gt;
<byte value="x9"/> and &lt;a href=&quot;https://bitcoin.org&quot;&gt;Bitcoin.org&lt;/a&gt;.  If
         you are experiencing problems using this software, please visit the
         &lt;a href=&quot;https://bitcointalk.org/index.php?board=97.0&quot;&gt;Armory Forum&lt;/a&gt;. Users
<byte value="x9"/> there will help you with any issues that you have.
         &lt;br&gt;&lt;br&gt;
         &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;&lt;/b&gt; Make a backup of your wallet(s)!  Paper
         backups protect you &lt;i&gt;forever&lt;/i&gt; against forgotten passwords,
         hard-drive failure, and make it easy for your family to recover
         your funds if something terrible happens to you.  &lt;i&gt;Each wallet
         only needs to be backed up once, ever!&lt;/i&gt;  Without it, you are at
         risk of losing all of your Bitcoins!
         &lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4559"/>
        <source>&lt;p&gt;&lt;b&gt;You now have access to all the features Armory has to offer!&lt;/b&gt;&lt;br&gt;To see your balances and transaction history, please click on the &quot;Transactions&quot; tab above this text.  &lt;br&gt;Here&apos;s some things you can do with Armory Bitcoin Client:&lt;br&gt;</source>
        <translation>&lt;p&gt;&lt;b&gt;Τώρα έχετε πρόσβαση σε όλες τις δυνατότητες που το Armory μπορεί να προσφέρει!&lt;/b&gt;&lt;br&gt;Για να δείτε τα ποσά σας και το ιστορικό συναλλαγών σας, παρακαλώ πατήστε στην καρτέλα &quot;Συναλλαγές&quot; πάνω απο αυτό το κείμενο.&lt;br&gt;Εδώ είναι μερικά πράγματα που μπορείτε να κάνετε με το Armory:&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4566"/>
        <source>If you experience any performance issues with Armory, please confirm that Bitcoin Core is running and &lt;i&gt;fully synchronized with the Bitcoin network&lt;/i&gt;.  You will see a green checkmark in the bottom right corner of the Bitcoin Core window if it is synchronized.  If not, it is recommended you close Armory and restart it only when you see that checkmark.&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4566"/>
        <source>&lt;b&gt;Please backup your wallets!&lt;/b&gt;  Armory wallets are &quot;deterministic&quot;, meaning they only need to be backed up one time (unless you have imported external addresses/keys). Make a backup and keep it in a safe place!  All funds from Armory-generated addresses will always be recoverable with a paper backup, any time in the future.  Use the &quot;Backup Individual Keys&quot; option for each wallet to backup imported keys.&lt;/p&gt;</source>
        <translation>&lt;b&gt; Παρακαλώ πάρτε αντίγραφα ασφαλείας των πορτοφόλια σας! &lt;/b&gt; Τα πορτοφόλια του  Armory είναι &quot;ντετερμινιστικά&quot;, που σημαίνει ότι πρέπει να ληφθεί αντίγραφο ασφαλείας μία φορά (εκτός και αν έχετε εισάγει εξωτερικές διευθύνσεις/κλειδιά). Δημιουργήστε ένα αντίγραφο ασφαλείας και φυλάξτε το σε ασφαλές μέρος! Όλα τα κεφάλαια του Armory που δημιουργούνται από διευθύνσεις του πάντα θα μπορούν να ανακτηθούν με ένα αντίγραφο ασφαλείας σε χαρτί, οποιαδήποτε στιγμή στο μέλλον. Χρησιμοποιήστε την επιλογή &quot;Ατομικά Αντίγραφα Ασφαλείας Ιδιωτικών Κλειδιών&quot; για κάθε πορτοφόλι για να πάρετε αντίγραφο απο τα τα εισαγόμενα κλειδιά.&lt;/p&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4596"/>
        <source>Armory is currently online, but you have requested a sweep operation on one or more private keys.  This requires searching the global transaction history for the available balance of the keys to be swept. &lt;br&gt;&lt;br&gt;Press the button to start the blockchain scan, which will also put Armory into offline mode for a few minutes until the scan operation is complete</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4594"/>
        <source>&lt;b&gt;Wallet balances may be incorrect until the rescan operation is performed!&lt;/b&gt;&lt;br&gt;&lt;br&gt;Armory is currently online, but addresses/keys have been added without rescanning the blockchain.  You may continue using Armory in online mode, but any transactions associated with the new addresses will not appear in the ledger. &lt;br&gt;&lt;br&gt;Pressing the button above will put Armory into offline mode for a few minutes until the scan operation is complete.</source>
        <translation>&lt;b&gt; Τα υπόλοιπα των πορτοφολιών ενδέχεται να είναι εσφαλμένα μέχρι να εκτελεστεί η επανάληψη της λειτουργίας σάρωσης! &lt;/b&gt; &lt;br&gt; Η οπλοστάσιο είναι επί του παρόντος σε απευθείας σύνδεση, αλλά οι διευθύνσεις / τα κλειδιά έχουν προστεθεί χωρίς να επαναλάβετε τη σάρωση της αλυσίδας. Μπορείτε να συνεχίσετε να χρησιμοποιείτε το οπλοστάσιο σε λειτουργία σύνδεσης, αλλά οποιεσδήποτε συναλλαγές σχετίζονται με τις νέες διευθύνσεις δεν θα εμφανίζονται στην αλυσίδα. &lt;br&gt;Πατώντας πάνω στο το κουμπί θα βάλει το Armory σε κατάσταση εκτός σύνδεσης για λίγα λεπτά, μέχρι η λειτουργία σάρωσης έχει ολοκληρωθεί.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4606"/>
        <source>There is no connection to the internet, and there is no other Bitcoin software running.  Most likely you are here because this is a system dedicated to manage offline wallets! &lt;br&gt;&lt;br&gt;&lt;b&gt;If you expected Armory to be in online mode&lt;/b&gt;, please verify your internet connection is active, then restart Armory.  If you think the lack of internet connection is in error (such as if you are using Tor), then you can restart Armory with the &quot;--skip-online-check&quot; option, or change it in the Armory settings.&lt;br&gt;&lt;br&gt;If you do not have Bitcoin Core installed, you can download it from &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4629"/>
        <source>You are currently in offline mode, but can switch to online mode by pressing the button above.  However, it is not recommended that you switch until Bitcoin Core/bitcoind is fully synchronized with the bitcoin network.  You will see a green checkmark in the bottom-right corner of the Bitcoin Core window when it is finished.&lt;br&gt;&lt;br&gt;Switching to online mode will give you access to more Armory functionality, including sending and receiving bitcoins and viewing the balances and transaction histories of each of your wallets.&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4643"/>
        <source>You are currently in offline mode because Bitcoin Core is not running.  To switch to online mode, start Bitcoin Core and let it synchronize with the network -- you will see a green checkmark in the bottom-right corner when it is complete.  If Bitcoin Core is already running and you believe the lack of connection is an error (especially if using proxies), please see &lt;a href=&quot;https://bitcointalk.org/index.php?topic=155717.msg1719077#msg1719077&quot;&gt;this link&lt;/a&gt; for options.&lt;br&gt;&lt;br&gt;&lt;b&gt;If you prefer to have Armory do this for you&lt;/b&gt;, then please check &quot;Let Armory run Bitcoin Core in the background&quot; under &quot;File&quot;-&gt;&quot;Settings.&quot;&lt;br&gt;&lt;br&gt;If you already know what you&apos;re doing and simply need to fetch the latest version of Bitcoin Core, you can download it from &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4662"/>
        <source>You are currently in offline mode because Armory could not detect an internet connection.  If you think this is in error, then restart Armory using the &quot; --skip-online-check&quot; option, or adjust the Armory settings.  Then restart Armory.&lt;br&gt;&lt;br&gt;If this is intended to be an offline computer, note that it is not necessary to have Bitcoin Core or bitcoind running.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4673"/>
        <source>You are currently in offline mode because Armory could not find the blockchain files produced by Bitcoin Core.  Do you run Bitcoin Core (or bitcoind) from a non-standard directory?   Armory expects to find the blkXXXX.dat files in &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt; If you know where they are located, please restart Armory using the &quot; --satoshi-datadir=[path]&quot; to notify Armory where to find them.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4683"/>
        <source>Armory was previously online, but the connection to Bitcoin Core/bitcoind was interrupted.  You will not be able to send bitcoins or confirm receipt of bitcoins until the connection is reestablished.  &lt;br&gt;&lt;br&gt;Please check that Bitcoin Core is open and synchronized with the network.  Armory will &lt;i&gt;try to reconnect&lt;/i&gt; automatically when the connection is available again.  If Bitcoin Core is available again, and reconnection does not happen, please restart Armory.&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4693"/>
        <source>Please wait while the global transaction history is scanned. Armory will go into online mode automatically, as soon as the scan is complete.</source>
        <translation>Παρακαλώ περιμένετε ενώ το παγκόσμιο ιστορικό συναλλαγών σαρώνεται. Το Armory θα πάει σε απευθείας σύνδεση και λειτουργία αυτόματα, μόλις ολοκληρωθεί η σάρωση.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4698"/>
        <source>Armory is scanning the global transaction history to retrieve information about your wallets.  The &quot;Transactions&quot; tab will be updated with wallet balance and history as soon as the scan is complete.  You may manage your wallets while you wait.&lt;br&gt;&lt;br&gt;</source>
        <translation>Το Armory σαρώνει το παγκόσμιο ιστορικό συναλλαγών για να ανακτήσετε πληροφορίες σχετικά με τα πορτοφόλια σας. Η καρτέλα &quot;Συναλλαγές&quot; θα ενημερωθεί με τα ποσά του πορτοφολιού σας και το ιστορικό σας μόλις ολοκληρωθεί η σάρωση. Μπορείτε να διαχειριστείτε τα πορτοφόλια σας ενώ περιμένετε. &lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4710"/>
        <source>It appears you are already running Bitcoin software (Bitcoin Core or bitcoind). Unlike previous versions of Armory, you should &lt;u&gt;not&lt;/u&gt; run this software yourself --  Armory will run it in the background for you.  Either close the Bitcoin application or adjust your settings.  If you change your settings, then please restart Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4719"/>
        <source>&lt;b&gt;Only one more step to getting online with Armory!&lt;/b&gt;   You must install the Bitcoin software from https://bitcoin.org in order for Armory to communicate with the Bitcoin network.  If the Bitcoin software is already installed and/or you would prefer to manage it yourself, please adjust your settings and restart Armory.</source>
        <translation>&lt;b&gt; Μόνο ένα ακόμη βήμα για να έρθει σε απευθείας σύνδεση το Armory! &lt;/b&gt; Θα πρέπει να εγκαταστήσετε το λογισμικό Bitcoin από https://bitcoin.org προκειμένου το Armory να επικοινωνήσει με το δίκτυο του Bitcoin. Εάν το λογισμικό του Bitcoin είναι ήδη εγκατεστημένο και/ή θα προτιμούσατε να το διαχειριστείτε μόνοι σας, παρακαλούμε να προσαρμόσετε τις ρυθμίσεις σας και κάντε επανεκκίνηση του Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4727"/>
        <source>
            &lt;b&gt;To maximize your security, the Bitcoin engine is downloading
            and verifying the global transaction ledger.  &lt;u&gt;This will take
            several hours, but only needs to be done once&lt;/u&gt;!&lt;/b&gt;  It is
            usually best to leave it running over night for this
            initialization process.  Subsequent loads will only take a few
            minutes.
            &lt;br&gt;&lt;br&gt;
            &lt;b&gt;Please Note:&lt;/b&gt; Between Armory and the underlying Bitcoin
            engine, you need to have 40-50 GB of spare disk space available
            to hold the global transaction history.
            &lt;br&gt;&lt;br&gt;
            While you wait, you can manage your wallets.  Make new wallets,
            make digital or paper backups, create Bitcoin addresses to receive
            payments,
            sign messages, and/or import private keys.  You will always
            receive Bitcoin payments regardless of whether you are online,
            but you will have to verify that payment through another service
            until Armory is finished this initialization.</source>
        <translation>
&lt;b&gt; Για τη μεγιστοποίηση της ασφάλειάς σας, ο κινητήρας του Bitcoin θα κατεβάσει
και θα πιστοποιήσει τις παγκόσμιες καθολικές συναλλαγές. &lt;u&gt; Αυτό θα πάρει
αρκετές ώρες, αλλά χρειάζεται να γίνει μόνο μία φορά &lt;/ u&gt;! &lt;/ b&gt; Είναι 
συνήθως καλύτερα να το αφήσετε σε λειτουργία μέσα σε μια νύχτα για την
διαδικασία προετοιμασίας. Οι επόμενες αποστολές θα πάρουν μόνο μερικά
λεπτά.

&lt;br&gt;&lt;br&gt;

&lt;b&gt; Σημείωση: &lt;/b&gt; Μεταξύ του Armory και του υποκείμενου Bitcoin
κινητήρα, θα πρέπει να έχετε 40-50 GB χώρου στο δίσκο διαθέσιμο για να κρατήσει το 
παγκόσμιο ιστορικό συναλλαγών.

&lt;br&gt;&lt;br&gt;

Ενώ περιμένετε, μπορείτε να διαχειριστείτε τα πορτοφόλια σας. Να κάνετε νέα πορτοφόλια, να κάνετε ψηφιακά ή αντίγραφα ασφαλείας σε χαρτί, να δημιουργήσετε Bitcoin που απευθύνονται σε πληρωμές παραλαβής, Να υπογράψετε μηνύματα και / ή να εισάγετε ιδιωτικά κλειδιά. Πάντα θα λαμβάνετε πληρωμές σε Bitcoin, ανεξάρτητα από το αν είστε συνδεδεμένοι. Αλλά θα πρέπει να βεβαιώσετε την πληρωμή μέσω μιας άλλης υπηρεσίας μέχρι το οπλοστάσιο να τελειώσει αυτή την προετοιμασία.</translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="4763"/>
        <source>The software is downloading and processing the latest activity on the network related to your wallet.  This should take only a few minutes.  While you wait, you can manage your wallets.  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</source>
        <comment>The software is downloading and processing the latest activity on the network related to your wallets.  This should take only a few minutes.  While you wait, you can manage your wallets.  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallets if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</comment>
        <translation type="obsolete">
            <numerusform>The software is downloading and processing the latest activity on the network related to your wallet.  This should take only a few minutes.  While you wait, you can manage your wallets.  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</numerusform>
            <numerusform/>
        </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4760"/>
        <source>Armory&apos;s communication with the Bitcoin network was interrupted. This usually does not happen unless you closed the process that Armory was using to communicate with the network. Armory requires %1 to be running in the background, and this error pops up if it disappears.&lt;br&gt;&lt;br&gt;You may continue in offline mode, or you can close all Bitcoin processes and restart Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4769"/>
        <source>Armory has experienced an issue trying to communicate with the Bitcoin software.  The software is running in the background, but Armory cannot communicate with it through RPC as it expects to be able to.  If you changed any settings in the Bitcoin home directory, please make sure that RPC is enabled and that it is accepting connections from localhost.  &lt;br&gt;&lt;br&gt;If you have not changed anything, please export the log file (from the &quot;File&quot; menu) and open an issue at https://github.com/goatpig/BitcoinArmory/issues</source>
        <translation>Το Armory έχει βιώσει ένα θέμα προσπαθώντας να επικοινωνήσει με το λογισμικό του Bitcoin. Το λογισμικό τρέχει στο παρασκήνιο, αλλά το Armory δεν μπορεί να επικοινωνήσει μαζί του μέσω του RPC, καθώς αναμένει να μπορεί. Αν έχετε αλλάξει τις ρυθμίσεις στον αρχικό κατάλογο του Bitcoin, βεβαιωθείτε ότι το RPC είναι ενεργοποιημένο και ότι δέχεται συνδέσεις από το localhost. &lt;br&gt;&lt;br&gt; Αν δεν έχετε αλλάξει τίποτα, παρακαλούμε να εξαγάγετε το αρχείο καταγραφής (από το μενού &quot;Αρχείο&quot;) και να ανοίξετε ένα θέμα στο https://github.com/goatpig/BitcoinArmory/issues</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4780"/>
        <source>Armory does not detect internet access, but it does detect running Bitcoin software.  Armory is in offline-mode. &lt;br&gt;&lt;br&gt;If you are intending to run an offline system, you will not need to have the Bitcoin software installed on the offline computer.  It is only needed for the online computer. If you expected to be online and the absence of internet is an error, please restart Armory using the &quot;--skip-online-check&quot; option.  </source>
        <translation>Το Armory δεν ανιχνεύει πρόσβαση στο internet, αλλά δεν ανιχνεύει και να τρέχει το λογισμικό του Bitcoin. Το Armory είναι σε λειτουργία εκτός σύνδεσης. &lt;br&gt;&lt;br&gt; Αν σκοπεύετε να εκτελέσετε το σύστημα χωρίς σύνδεση, δεν θα πρέπει να έχετε το λογισμικό του Bitcoin εγκατεστημένο στον υπολογιστή σας χωρίς σύνδεση. Είναι απαραίτητο μόνο για τον συνδεδεμένο υπολογιστή. Εάν αναμένετε να είναι σε απευθείας σύνδεση και η απουσία του διαδικτύου είναι ένα λάθος, παρακαλούμε κάντε επανεκκίνηση του Armory χρησιμοποιώντας την επιλογή &quot;--skip-online-check&quot;.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4790"/>
        <source>Armory was started in offline-mode, but detected you are running Bitcoin software.  If you are intending to run an offline system, you will &lt;u&gt;not&lt;/u&gt; need to have the Bitcoin software installed or running on the offline computer.  It is only required for being online. </source>
        <translation>Το Armory ξεκίνησε εκτός σύνδεσης, αλλά ανίχνευσε οτι τρέχετε το λογισμικό Bitcoin. Αν σκοπεύετε να εκτελέσετε ένα σύστημα χωρίς σύνδεση, δεν &lt;u&gt;θα&lt;/u&gt; πρέπει να έχετε το λογισμικό Bitcoin εγκατεστημένο ή να εκτελείται εκτός σύνδεσης στον υπολογιστή. 
Απαιτείται μόνο για απευθείας σύνδεση.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4809"/>
        <source>The Bitcoin software indicates there is a problem with its databases.  This can occur when Bitcoin Core/bitcoind is upgraded or downgraded, or sometimes just by chance after an unclean shutdown.&lt;br&gt;&lt;br&gt;You can either revert your installed Bitcoin software to the last known working version (but not earlier than version 0.8.1) or delete everything &lt;b&gt;except&lt;/b&gt; &quot;wallet.dat&quot; from the your Bitcoin home directory:&lt;br&gt;&lt;br&gt;&lt;font face=&quot;courier&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;If you choose to delete the contents of the Bitcoin home directory, you will have to do a fresh download of the blockchain again, which will require a few hours the first time.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4821"/>
        <source>
               There was an error starting the underlying Bitcoin engine.
               This should not normally happen.  Usually it occurs when you
               have been using Bitcoin Core prior to using Armory, especially
               if you have upgraded or downgraded Bitcoin Core recently.
               Output from bitcoind:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4830"/>
        <source>
                  There was an error starting the underlying Bitcoin engine.
                  This should not normally happen.  Usually it occurs when you
                  have been using Bitcoin Core prior to using Armory, especially
                  if you have upgraded or downgraded Bitcoin Core recently.
                  &lt;br&gt;&lt;br&gt;
                  Unfortunately, this error is so strange, Armory does not
                  recognize it.  Please go to &quot;Export Log File&quot; from the &quot;File&quot;
                  menu and submit an issue at https://github.com/goatpig/BitcoinArmory/issues.
                  We apologize for the inconvenience!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4985"/>
        <source>Armory is &lt;u&gt;offline&lt;/u&gt;</source>
        <translation>Το Armory είναι &lt;u&gt;εκτός σύνδεσης&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4969"/>
        <source>In case you actually do have internet access, you can use the following links to get Armory installed.  Or change your settings.</source>
        <translation>Σε περίπτωση που στην πραγματικότητα έχετε πρόσβαση στο διαδίκτυο, μπορείτε να χρησιμοποιήσετε τους παρακάτω συνδέσμους για να εγκατασταθεί το Armory. Ή μπορείτε να αλλάξετε τις ρυθμίσεις σας.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4989"/>
        <source>Cannot find Bitcoin Home Directory</source>
        <translation>Δεν μπορεί να βρεθεί ο Φάκελος Λειτουργίας του Bitcoin </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4997"/>
        <source>Check Again</source>
        <translation>Ελέξτε Ξανά</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5019"/>
        <source>Initializing Bitcoin Engine</source>
        <translation>Ενεργοποίηση Μηχανής του Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5078"/>
        <source>Synchronizing with Network</source>
        <translation>Συγχρονισμός με το Δίκτυο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5033"/>
        <source>Since version 0.88, Armory runs bitcoind in the background.  You can switch back to the old way in the Settings dialog. </source>
        <translation>Απο την έκδοση 0.88, το Armory τρέχει το bitcoind σαν κρυμμένη διεργασία παρασκηνίου. Μπορείτε να το φέρετε στην παλαιά κατάσταση απο το πλαίσιο Ρυθμίσεις.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5051"/>
        <source>Armory is disconnected</source>
        <translation>Το Armory είναι αποσυνδεδεμένο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5058"/>
        <source>Armory is online!</source>
        <translation>Το Armory είναι συνδεδεμένο!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5086"/>
        <source>Preparing Databases</source>
        <translation>Προετοιμασία Βάσεων Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5253"/>
        <source>&lt;font color=%1&gt;Connected (%2 blocks)&lt;/font&gt; </source>
        <translation>&lt;font color=%1&gt;Συνδεδεμένο σε (%2 μπλόκ)&lt;/font&gt; </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5259"/>
        <source>Last block received %1 ago</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5265"/>
        <source>&lt;font color=%1&gt;Node offline (%2 blocks)&lt;/font&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5270"/>
        <source>Disconnected from Bitcoin Node, cannot update history &lt;br&gt;&lt;br&gt;Last known block: %1 &lt;br&gt;Received %2 ago</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5408"/>
        <source>BDM error!</source>
        <translation>Σφάλμα BDM!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5402"/>
        <source>Rebuild and rescan on next start</source>
        <translation>αναδόμηση και επανασάρωση στην επόμενη εκκίνηση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5408"/>
        <source>Factory reset on next start</source>
        <translation>Επαναφορά Εργοστασιακών Ρυθμίσεων στην επόμενη εκκίνηση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5414"/>
        <source>BlockDataManager Warning</source>
        <translation>Προειδοποίηση του BlockDataManager </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5463"/>
        <source>Disconnected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5463"/>
        <source>Connection to Bitcoin Core client lost!  Armory cannot send nor receive bitcoins until connection is re-established.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5469"/>
        <source>Connected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5469"/>
        <source>Connection to Bitcoin Core re-established</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6152"/>
        <source>Database Error</source>
        <translation>Σφάλμα Βάσης Δεδομένων</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5514"/>
        <source>
                           The DB has returned the following
                           error: &lt;br&gt;&lt;br&gt;
                           &lt;b&gt; %1 &lt;/b&gt; &lt;br&gt;&lt;br&gt;
                           Armory will now shutdown. </source>
        <translation>
Η Βάση Δεδομένων επέστρεψε το ακόλουθο
σφάλμα: &lt;br&gt;&lt;br&gt;
&lt;b&gt; %1 &lt;/b&gt; &lt;br&gt;&lt;br&gt;
Το Armory θα κλείσει.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5612"/>
        <source>Wallet %1 (%2)</source>
        <translation>Πορτοφόλι %1 (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5619"/>
        <source>Lockbox %1 (%2)</source>
        <translation>Κουτί %1 (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5713"/>
        <source>Bitcoins Received!</source>
        <translation>Τα Bitcoin Ελήφθησαν!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5732"/>
        <source>Amount:  %1 BTC</source>
        <translation>Ποσόν: %1 BTC</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5629"/>
        <source>Recipient:  %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5731"/>
        <source>Bitcoins Sent!</source>
        <translation>Τα Bitcoin Στάλθηκαν!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5634"/>
        <source>Sender:  %1</source>
        <translation>Αποστολέας: %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5685"/>
        <source>Wallet &quot;%1&quot; (%2)</source>
        <translation>Πορτοφόλι &quot;%1&quot; (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5693"/>
        <source>Lockbox %1-of-%2 &quot;%3&quot; (%4)</source>
        <translation>Κουτί %1-of-%2 &quot;%3&quot; (%4)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5704"/>
        <source>Your bitcoins just did a lap!</source>
        <translation>Τα bitcoin σας έκαναν ένα γύρο!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5704"/>
        <source>%1 just sent some BTC to itself!</source>
        <translation>%1 έστειλε μερικά BTC στον εαυτό του!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5715"/>
        <source>From:    %2</source>
        <translation>Από: %2</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5729"/>
        <source>&lt;Multiple Recipients&gt;</source>
        <translation>&lt;Πολλαπλοί Παραλήπτες&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5733"/>
        <source>From:    %1</source>
        <translation>Από: %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5734"/>
        <source>To:      %1</source>
        <translation>Πρός: %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5750"/>
        <source>Minimize or Close</source>
        <translation>Ελαχιστοποίηση ή Κλείσιμο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5750"/>
        <source>Would you like to minimize Armory to the system tray instead of closing it?</source>
        <translation>Θα θέλατε το Armory θα κρυφτεί στην μπάρα εργασιών αντί να κλείσει;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5750"/>
        <source>Remember my answer</source>
        <translation>Να θυμάσαι την απάντηση μου</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5750"/>
        <source>Minimize</source>
        <translation>Ελαχιστοποίηση</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5750"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5953"/>
        <source>All wallets are consistent</source>
        <translation>Όλα τα πορτοφόλια έχουν συνοχή</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5957"/>
        <source>Consistency Check Failed!</source>
        <translation>Ο Έλεγχος Συνοχής Απέτυχε!</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5969"/>
        <source>
               The wallet analysis tool will become available
               as soon as Armory is done loading.   You can close this
               window and it will reappear when ready.</source>
        <translation>
Το εργαλείο ανάλυσης θα γίνει διαθέσιμο
όταν φορτώσει το Armory. Μπορείτε να κλείσειτε αυτό
το παράθυρο το οποίο θα ξανανοίξει όταν είναι έτοιμο.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6002"/>
        <source>
                  &lt;b&gt;The following dialogs need closed before you can
                  run the wallet analysis tool:&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Τα ακόλουθα παράθυρα διαλόγων πρέπει να κλείσουν πριν να μπορείτε
να τρέξετε το εργαλείο ανάλυσης πορτοφολιού:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6026"/>
        <source>Wallet Consistency Check: %p%</source>
        <translation>Έλεγχος Συνοχής: %p%</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6152"/>
        <source>
                           Armory failed to spawn the DB!&lt;br&gt; 
                           Continuing operations in offline mode instead. &lt;br&gt;
                           Refer to the dbLog.txt for more information.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6270"/>
        <source>Filter:</source>
        <translation>Φίλτρο:</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="6288"/>
        <source>Transactions</source>
        <translation>Συναλλαγές</translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="3018"/>
        <source>You cannot sweep the funds from the address(es) you specified, because
               the transaction fee would be equal to or greater than the amount 
               swept.
               &lt;br&gt;&lt;br&gt;
               &lt;b&gt;Balance of address(es):&lt;/b&gt; %1&lt;br&gt;
               &lt;b&gt;Fee to sweep address(es):&lt;/b&gt; %2
               &lt;br&gt;&lt;br&gt;The sweep operation has been canceled.</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="4763"/>
        <source>The software is downloading and processing the latest activity on the network related to your wallet(s).  This should take only a few minutes.  While you wait, you can manage your wallet(s).  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet(s) if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever! %n</source>
        <translation type="obsolete">
            <numerusform>The software is downloading and processing the latest activity on the network related to your wallet.  This should take only a few minutes.  While you wait, you can manage your wallet(s).  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</numerusform>
            <numerusform>The software is downloading and processing the latest activity on the network related to your wallets.  This should take only a few minutes.  While you wait, you can manage your wallets.  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallets if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="4747"/>
        <source>The software is downloading and processing the latest activity on the network related to your wallet(s).  This should take only a few minutes.  While you wait, you can manage your wallet(s).  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet(s) if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="3011"/>
        <source>The private key(s) you have provided does not appear to contain
               any funds.  There is nothing to sweep.</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4484"/>
        <source>The following functionalities are available while scanning in offline mode:&lt;ul&gt;&lt;li&gt;Create new wallets&lt;/li&gt;&lt;li&gt;Generate receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign transactions created from an online system&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, even if you are offline.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4500"/>
        <source>The following functionalities are available in offline mode:&lt;ul&gt;&lt;li&gt;Create, import or recover wallets&lt;/li&gt;&lt;li&gt;Generate new receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Import private keys to wallets&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Sign transactions created from an online system&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, regardless of whether you are online.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="753"/>
        <source>
            Armory is using the default Bitcoin directory because
            the Bitcoin directory specified in the command line could
            not be found.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1182"/>
        <source>
         The next time you restart Armory, it will rebuild and rescan
         the entire blockchain database.  This operation can take between
         30 minutes and 4 hours depending on your system speed.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a rebuild on the next Armory restart?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1194"/>
        <source>
         The next time you restart Armory, it will rescan the balance of
         your wallets. This operation typically takes less than a minute.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a balance rescan on the next Armory restart?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1656"/>
        <source>
                  No passphrase was selected for the encrypted backup.
                  No backup was created.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4584"/>
        <source>Armory is currently online, but you have requested a sweep operation on one or more private keys.  This requires searching the global transaction history for the available balance of the keys to be swept. &lt;br&gt;&lt;br&gt;Press the button to start the blockchain scan, which will also put Armory into offline mode for a few minutes until the scan operation is complete.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3854"/>
        <source>
               Will download, cryptographically verify, and install Bitcoin Core.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4797"/>
        <source>The Bitcoin software indicates there is a problem with its databases.  This can occur when Bitcoin Core/bitcoind is upgraded or downgraded, or sometimes just by chance after an unclean shutdown.&lt;br&gt;&lt;br&gt;You can either revert your installed Bitcoin software to the last known working version (but not earlier than version 0.8.1) or delete everything &lt;b&gt;except&lt;/b&gt; &quot;wallet.dat&quot; from your Bitcoin home directory &lt;font face=&quot;courier&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;If you choose to delete the contents of the Bitcoin home directory, you will have to do a fresh download of the blockchain again, which will require a few hours the first time.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3423"/>
        <source>
            You just clicked on a &quot;bitcoin:&quot; link to send money, but you 
            currently have no wallets!  Would you like to create a wallet 
            now?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>ArmorySplashScreen</name>
    <message>
        <location filename="qtdialogs.py" line="15092"/>
        <source>%1: %2%</source>
        <translation>%1: %2%</translation>
    </message>
</context>
<context>
    <name>BareSignatureVerificationWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="265"/>
        <source>Signing Address:</source>
        <translation>Διεύθυνση Υπογραφής:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="274"/>
        <source>Signed Message:</source>
        <translation>Υπογεγραμμένο Μύνημα:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="281"/>
        <source>Signature:</source>
        <translation>Υπογραφή:</translation>
    </message>
</context>
<context>
    <name>CardDeckFrame</name>
    <message>
        <location filename="WalletFrames.py" line="499"/>
        <source>Please shuffle a deck of cards and enter the first 40 cards in order below to get at least 192 bits of entropy to properly randomize.

</source>
        <translation>Παρακαλείστε να ανακατέψετε την τράπουλα και να πληκτρολογήστε τα πρώτα 40 φύλλα για να υπάρξουν τουλάχιστον 192 μπίτς εντροπίας για την ορθή γενίκευση.
</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="534"/>
        <source>Entropy: %1 bits</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>CoinControlDlg</name>
    <message>
        <location filename="CoinControlUI.py" line="27"/>
        <source>By default, transactions are created using any available coins from all addresses in this wallet.  You can control the source addresses used for this transaction by selecting them below, and unchecking all other addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="33"/>
        <source>Use all selected UTXOs</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="34"/>
        <source>
      By default, Armory will pick a a subset of the UTXOs you pick 
      explicitly through the coin control feature to best suit the
      total spend value of the transaction you are constructing.
      
      &lt;br&gt;&lt;br&gt;
      Checking 'Use all selected UTXOs' forces the construction of a
      transaction that will redeem the exact list of UTXOs you picked 
      instead 
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="51"/>
        <source>Accept</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="52"/>
        <source>Cancel</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="75"/>
        <source>Coin Control (Expert)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>CoinControlTreeModel</name>
    <message>
        <location filename="TreeViewGUI.py" line="671"/>
        <source>Address/ID</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="672"/>
        <source>Comment</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="673"/>
        <source>Balance</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>CoinControlUtxoItem</name>
    <message>
        <location filename="TreeViewGUI.py" line="63"/>
        <source>Block: #%1 | Tx: #%2 | TxOut: #%3</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>CreateTxPage</name>
    <message>
        <location filename="Wizards.py" line="407"/>
        <source>Step 1: Create Transaction</source>
        <translation>Βήμα 1: Δημιουργία Συναλλαγής</translation>
    </message>
</context>
<context>
    <name>DlgAddressBook</name>
    <message>
        <location filename="qtdialogs.py" line="8064"/>
        <source>Select</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8074"/>
        <source>Choose an address from your transaction history,
                            or your own wallet.  If you choose to send to one
                            of your own wallets, the next unused address in
                            that wallet will be used.</source>
        <translation>Επιλέξτε μια διεύθυνση από το ιστορικό συναλλαγών σας,
ή το δικό σας πορτοφόλι. Εάν επιλέξετε να στείλετε σε ενα
από τα δικά σας πορτοφόλια, η επόμενη αχρησιμοποίητη διεύθυνση
σε αυτό το πορτοφόλι θα χρησιμοποιηθεί.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8080"/>
        <source>Browse all receiving addresses in
                               this wallet, and all addresses to which this
                               wallet has sent bitcoins.</source>
        <translation>Ψάξτε όλες τις διευθύνσεις που λαμβάνουν σε
αυτό το πορτοφόλι, και όλες τις διευθύνσεις στις οποίες αυτό
το πορτοφόλι έχει στείλει bitcoin.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8084"/>
        <source>&lt;b&gt;Send to Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αποστολή στο Πορτοφόλι:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8085"/>
        <source>&lt;b&gt;Send to Address:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αποστολή στην Διεύθυνση:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8136"/>
        <source>Receiving (Mine)</source>
        <translation>Λήψη (Δική Μου)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8138"/>
        <source>Sending (Other&apos;s)</source>
        <translation>Αποστολή (Σε Άλλους)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8173"/>
        <source>The next unused address in that wallet will be calculated and selected. </source>
        <translation>Η επόμενη αχρησιμοποίητη διεύθυνση σε αυτό το πορτοφόλι, θα υπολογιστεί και θα επιλεχθεί.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8175"/>
        <source>Addresses that are in other wallets you own are &lt;b&gt;not showns&lt;/b&gt;.</source>
        <translation>Διευθύνσεις που βρίσκονται σε άλλα πορτοφόλια που έχετε στην κατοχή σας &lt;b&gt;δεν εμφανίζονται&lt;/b&gt;.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8180"/>
        <source>No Wallet Selected</source>
        <translation>Κανένα Πορτοφόλι Δεν Έχει Επιλεχθεί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8181"/>
        <source>Use Bare Multi-Sig (No P2SH)</source>
        <translation>Χρήση Σκέτης Πολλαπλής Υπογραφής (Χωρίς P2SH)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8183"/>
        <source>
         EXPERT OPTION:  Do not check this box unless you know what it means
                         and you need it!  Forces Armory to exposes public
                         keys to the blockchain before the funds are spent.
                         This is only needed for very specific use cases,
                         and otherwise creates blockchain bloat.</source>
        <translation>
ΣΥΜΒΟΥΛΗ ΤΟΥ ΕΙΔΙΚΟΥ: Μην επιλέξετε αυτό το πλαίσιο, εκτός αν ξέρετε τι σημαίνει
και το χρειάζεστε! Αναγκάζει το Armory να εκθέσει το δημόσιο
κλειδί στην αλυδίδα συναλλαγών πριν τα κεφάλαια ξορευτούν.
Αυτό είναι απαραίτητο μόνο για πολύ συγκεκριμένες περιπτώσεις χρήσης,
αλλιώς δημιουργεί φόρτο στην αλυσίδα συναλλαγών.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8192"/>
        <source>No Address Selected</source>
        <translation>Καμία Διεύθυνση Δεν Έχει Επιλεχθεί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8195"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8201"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Πίσω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8308"/>
        <source>None Selected</source>
        <translation>Καμία Επιλογή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8396"/>
        <source>%1 Wallet: %2</source>
        <translation>%1 Πορτοφόλι: %2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8438"/>
        <source>%1 Address: %2...</source>
        <translation>%1 Διεύθυνση: %2...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8486"/>
        <source>
               Bare multi-sig is not available for M-of-N lockboxes on the
               main Bitcoin network with N higher than 3.</source>
        <translation>
Η γυμνή πολλαπλή υπογραφή δεν είναι διαθέσιμη για M-απο τα-N κουτιά κλειδώματος στο
βασικό δίκτυο του Bitcoin με το Ν να έιναι μεγαλύτερο απο 3.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8535"/>
        <source>P2SH Not Allowed</source>
        <translation>P2SH Δεν Επιτρέπεται</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8534"/>
        <source>
               This operation requires a public key, but you selected a
               P2SH address which does not have a public key (these addresses
               start with &quot;2&quot; or &quot;3&quot;).  Please select a different address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8569"/>
        <source>No Public Key</source>
        <translation>Δεν Υπάρχει Δημόσιο Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8569"/>
        <source>
            This operation requires a full public key, not just an address.
            Unfortunately, Armory cannot find the public key for the address
            you selected.  In general public keys will only be available
            for addresses in your wallet.</source>
        <translation>
Αυτή η λειτουργία απαιτεί ένα πλήρες δημόσιο κλειδί, όχι μόνο μια διεύθυνση.
Δυστυχώς, το Armory δεν μπορεί να βρει το δημόσιο κλειδί για την διεύθυνση
που έχετε επιλέξει. Σε γενικές γραμμές τα δημόσια κλειδιά είναι διαθέσιμα
μόνο για τις διευθύνσεις στο πορτοφόλι σας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8620"/>
        <source>Copy Address</source>
        <translation>Αντιγραφή Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8621"/>
        <source>Copy Hash160 (hex)</source>
        <translation>Αντιγραφή του Hash160 (hex)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8622"/>
        <source>Copy Comment</source>
        <translation>Αντιγραφή Σχόλιου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8535"/>
        <source>
               This operation requires a public key, but you selected a
               P2SH address which does not have a public key (these addresses
               start with &quot;2&quot; or &quot;3&quot;).  Please select a different address.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8400"/>
        <source>Will create new address: %1...</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgAddressInfo</name>
    <message>
        <location filename="qtdialogs.py" line="3564"/>
        <source>Information for address:  %1</source>
        <translation>Πληροφορίες για τη διεύθυνση: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3576"/>
        <source>This is the computer-readable form of the address</source>
        <translation>Αυτή είναι η μορφή αναγνώσιμη από υπολογιστή για τη διεύθυνση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3578"/>
        <source>&lt;b&gt;Public Key Hash&lt;/b&gt;</source>
        <translation>&lt;b&gt;Κώδικας Δημοσίου Κλειδιού&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3584"/>
        <source>%1 (Network: %2 / Checksum: %3)</source>
        <translation>%1 (Δίκτυο: %2 / Άθροισμα Ελέγχου: %3)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3591"/>
        <source>&lt;b&gt;Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Πορτοφόλι:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3596"/>
        <source>&lt;b&gt;Address:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Διεύθυνση:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3601"/>
        <source>
         Address type is either &lt;i&gt;Imported&lt;/i&gt; or &lt;i&gt;Permanent&lt;/i&gt;.
         &lt;i&gt;Permanent&lt;/i&gt;
         addresses are part of the base wallet, and are protected by printed
         paper backups, regardless of when the backup was performed.
         Imported addresses are only protected by digital backups, or manually
         printing the individual keys list, and only if the wallet was backed up
         &lt;i&gt;after&lt;/i&gt; the keys were imported.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3610"/>
        <source>&lt;b&gt;Address Type:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Τύπος Διεύθυνσης:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3624"/>
        <source>Imported</source>
        <translation>Εισήχθη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3614"/>
        <source>Permanent</source>
        <translation>Μόνιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3618"/>
        <source>The index of this address within the wallet.</source>
        <translation>Ο δείκτης αυτής της διεύθυνσης είναι μέσα στο πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3620"/>
        <source>&lt;b&gt;Index:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Δείκτης:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3629"/>
        <source>
            This is the current &lt;i&gt;spendable&lt;/i&gt; balance of this address,
            not including zero-confirmation transactions from others.</source>
        <translation>
Αυτό είναι το ποσό &lt;i&gt;που μπορεί να ξοδευτεί&lt;/i&gt; απο αυτή την διεύθυνση,
και δεν περιλαμβάνει συναλλαγές με μηδενικές-επιβεβαιώσεις απο άλλους.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3632"/>
        <source>&lt;b&gt;Current Balance&lt;/b&gt;</source>
        <translation>&lt;b&gt;Υπάρχων Ποσόν&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3648"/>
        <source>&lt;b&gt;Comment:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Σχόλιο:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3660"/>
        <source>The total number of transactions in which this address was involved</source>
        <translation>Ο συνολικός αριθμός των συναλλαγών στις οποίες συμμετείχε η διεύθυνση αυτή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3662"/>
        <source>&lt;b&gt;Transaction Count:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αριθμός Συναλλαγών:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3682"/>
        <source>&lt;font size=2&gt;Double-click to expand&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3726"/>
        <source>
            Unlike the wallet-level ledger, this table shows every
            transaction &lt;i&gt;input&lt;/i&gt; and &lt;i&gt;output&lt;/i&gt; as a separate entry.
            Therefore, there may be multiple entries for a single transaction,
            which will happen if money was sent-to-self (explicitly, or as
            the change-back-to-self address).</source>
        <translation>
Σε αντίθεση με το καθολικό επίπεδο-πορτοφόλι, ο πίνακας αυτός δείχνει κάθε
συναλλαγή &lt;i&gt;εισόδου&lt;/i&gt; και &lt;i&gt;εξόδου&lt;/i&gt; ως ξεχωριστή είσοδο.
Ως εκ τούτου, μπορεί να υπάρχουν πολλαπλές εγγραφές για την ίδια συναλλαγή,
το οποίο θα συμβεί αν τα χρήματα εστάλησαν προς αυτο (ρητά ή ως
διεύθυνση αλλαγή-πίσω-σε-σένα).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3732"/>
        <source>All Address Activity:</source>
        <translation>Δραστηριότητα όλων των Διευθύνσεων:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3741"/>
        <source>Copy Address to Clipboard</source>
        <translation>Αντιγραφή Διεύθυνσης στο Πρόχειρο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3742"/>
        <source>View Address Keys</source>
        <translation>Δείτε τα Κλειδιά των Διευθύνσεων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3744"/>
        <source>Delete Address</source>
        <translation>Διαγραφή Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3761"/>
        <source>
         NOTE:  The ledger shows each transaction &lt;i&gt;&lt;b&gt;input&lt;/b&gt;&lt;/i&gt; and
         &lt;i&gt;&lt;b&gt;output&lt;/b&gt;&lt;/i&gt; for this address.  There are typically many
         inputs and outputs for each transaction, therefore the entries
         represent only partial transactions.  Do not worry if these entries
         do not look familiar.</source>
        <translation>
ΣΗΜΕΙΩΣΗ: Το καθολικό δείχνει κάθε συναλλαγή &lt;i&gt; &lt;b&gt; εισαγωγής&lt;/b&gt; &lt;/i&gt; και
&lt;I&gt; &lt;b&gt; εξαγωγής&lt;/b&gt; &lt;/i&gt; για αυτή τη διεύθυνση. Υπάρχουν συνήθως πολλές
εισόδοι και εξόδοι για κάθε συναλλαγή, ως εκ τούτου, οι εγγραφές
αντιπροσωπεύουν μόνο μερικές συναλλαγές. Μην ανησυχείτε αν αυτές οι εγγραφές
δεν σας φαίνονται γνωστές.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3781"/>
        <source>Available Actions:</source>
        <translation>Διαθέσιμες Ενέργειες:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3784"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Πίσω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3788"/>
        <source>Address Information</source>
        <translation>Πληροφορίες Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3797"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3806"/>
        <source>Wallet is Locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3806"/>
        <source>Key information will not include the private key data.</source>
        <translation>Οι πληροφορίες κλειδιού δεν θα περιλαμβάνουν το ιδιωτικό κλειδί δεδομένων.</translation>
    </message>
</context>
<context>
    <name>DlgBackupCenter</name>
    <message>
        <location filename="qtdialogs.py" line="11163"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11174"/>
        <source>Backup Center</source>
        <translation>Κέντρο Αντιγράφων Ασφαλείας</translation>
    </message>
</context>
<context>
    <name>DlgBadConnection</name>
    <message>
        <location filename="qtdialogs.py" line="7533"/>
        <source>
            Armory was not able to detect an internet connection, so Armory
            will operate in &quot;Offline&quot; mode.  In this mode, only wallet
            -management and unsigned-transaction functionality will be available.
            &lt;br&gt;&lt;br&gt;
            If this is an error, please check your internet connection and
            restart Armory.&lt;br&gt;&lt;br&gt;Would you like to continue in &quot;Offline&quot; mode? </source>
        <translation>

Το Armory δεν ήταν σε θέση να εντοπίσει μια σύνδεση στο internet, έτσι το Armory
θα λειτουργεί σε κατάσταση λειτουργίας &quot;χωρίς σύνδεση&quot;. Σε αυτή τη λειτουργία, μόνο 
-διαχείριση του πορτοφολιού και ανυπόγραφες συναλλαγές θα είναι διαθέσιμες. 
&lt;br&gt;&lt;br&gt;
Εάν αυτό είναι λάθος, ελέγξτε την σύνδεση του διαδικτύου σας και
επανεκκίνηστε το Armory. &lt;br&gt;&lt;br&gt;Θέλετε να συνεχίσετε σε λειτουργία &quot;χωρίς σύνδεση&quot;;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7541"/>
        <source>
            Armory was not able to detect the presence of Bitcoin Core or bitcoind
            client software (available at https://bitcoin.org).  Please make sure that
            the one of those programs is... &lt;br&gt;
            &lt;br&gt;&lt;b&gt;(1)&lt;/b&gt; ...open and connected to the network
            &lt;br&gt;&lt;b&gt;(2)&lt;/b&gt; ...on the same network as Armory (main-network or test-network)
            &lt;br&gt;&lt;b&gt;(3)&lt;/b&gt; ...synchronized with the blockchain before
            starting Armory&lt;br&gt;&lt;br&gt;Without the Bitcoin Core or bitcoind open, you will only
            be able to run Armory in &quot;Offline&quot; mode, which will not have access
            to new blockchain data, and you will not be able to send outgoing
            transactions&lt;br&gt;&lt;br&gt;If you do not want to be in &quot;Offline&quot; mode, please
            restart Armory after one of these programs is open and synchronized with
            the network</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7566"/>
        <source>Continue in Offline Mode</source>
        <translation>Συνέχεια σε Λειτουργία Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7567"/>
        <source>Close Armory</source>
        <translation>Κλείσιμο του Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7579"/>
        <source>Network not available</source>
        <translation>Δίκτυο μή διαθέσιμο</translation>
    </message>
</context>
<context>
    <name>DlgBroadcastBlindTx</name>
    <message>
        <location filename="qtdialogs.py" line="14850"/>
        <source>
         Copy a raw, hex-encoded transaction below to have Armory
         broadcast it to the Bitcoin network.  This function is
         provided as a convenience to expert users, and carries
         no guarantees of usefulness.
         &lt;br&gt;&lt;br&gt;
         Specifically, be aware of the following limitations of
         this broadcast function:
         &lt;ul&gt;
            &lt;li&gt;The transaction will be &quot;broadcast&quot; by sending it
                to the connected Bitcon Core instance which will
                forward it to the rest of the Bitcoin network.
                However, if the transaction is non-standard or
                does not satisfy standard fee rules, Bitcoin Core
                &lt;u&gt;will&lt;/u&gt; drop it and it
                will never be seen by the Bitcoin network.
            &lt;/li&gt;
            &lt;li&gt;There will be no feedback as to whether the
                transaction succeeded.  You will have to verify the
                success of this operation via other means.
                However, if the transaction sends
                funds directly to or from an address in one of your
                wallets, it will still generate a notification and show
                up in your transaction history for that wallet.
            &lt;/li&gt;
         &lt;/ul&gt;</source>
        <translation>
Αντιγράψτε μια ακατέργαστη, κωδικοποιημένη με δεκαεξαδικό συναλλαγή παρακάτω για 
να κάνετε το Armory να την μεταδόσει στο δίκτυο του Bitcoin. Αυτή η λειτουργία
παρέχεται ως διευκόλυνση στους έμπειρους χρήστες και δεν έχει εγγυήσεις για την
χρησιμότητα του.
&lt;br&gt;&lt;br&gt;
Συγκεκριμένα, πρέπει να γνωρίζετε τους εξής περιορισμούς της
λειτουργίας εκπομπής:
&lt;ul&gt;
&lt;li&gt;
Η συναλλαγή θα &quot;μεταδοθεί&quot; με την αποστολή της
στο συνδεδεμένο Bitcon Core που θα
το διαβιβάζει στο υπόλοιπο του δικτύου του Bitcoin.
Ωστόσο, εάν η συναλλαγή είναι μη τυποποιημένη ή
δεν πληρεί τους συνήθεις κανόνες αμοιβής,το Bitcoin Core
&lt;u&gt; θα &lt;/u&gt; την ρίξει και
δεν πρόκειται ποτέ να φανεί στο δίκτυο του Bitcoin.
&lt;/li&gt;
&lt;li&gt;
Δεν θα υπάρξει καμία ανατροφοδότηση ως προς το αν η
συναλλαγή πέτυχε. Θα πρέπει να επαληθεύσετε την
επιτυχία της επιχείρησης αυτής μέσω άλλων μέσων.
Ωστόσο, εάν η συναλλαγή στείλει
κεφάλαια απευθείας από ή προς μια διεύθυνση σε ένα από τα
πορτοφόλια σας, θα εξακολουθεί να παράγει μια ειδοποίηση και θα εμφανιστεί
στο ιστορικό συναλλαγών σας για το συγκεκριμένο πορτοφόλι.
&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14884"/>
        <source>Parsed Transaction:</source>
        <translation>Αναλυμένη Συναλλαγή:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14894"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14895"/>
        <source>Broadcast</source>
        <translation>Μετάδοση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14911"/>
        <source>Broadcast Raw Transaction</source>
        <translation>Μετάδοση Ωμής Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14937"/>
        <source>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;Raw transaction
            is invalid!&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;Η Ωμή Συναλλαγή
είναι εσφαλμένη!&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14964"/>
        <source>Broadcast!</source>
        <translation>Μετάδοση!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14964"/>
        <source>
         Your transaction was successfully sent to the local Bitcoin
         Core instance, though there is no guarantees that it was
         forwarded to the rest of the network.   On testnet, just about
         every valid transaction will successfully propagate.  On the
         main Bitcoin network, this will fail unless it was a standard
         transaction type.

         The transaction
         had the following hash:
         &lt;br&gt;&lt;br&gt;
         %1
         &lt;br&gt;&lt;br&gt;
         You can check whether it was seen by other nodes on the network
         with the link below:
         &lt;br&gt;&lt;br&gt;
         &lt;a href=&quot;%2&quot;&gt;%3&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgChangeLabels</name>
    <message>
        <location filename="qtdialogs.py" line="1434"/>
        <source>Wallet &amp;name:</source>
        <translation>&amp;Όνομα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1440"/>
        <source>Wallet &amp;description:</source>
        <translation>&amp;Περιγραφή Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1460"/>
        <source>Wallet Descriptions</source>
        <translation>Περιγραφή Πορτοφολιών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1470"/>
        <source>Empty Name</source>
        <translation>Άδειο Όνομα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1470"/>
        <source>All wallets must have a name. </source>
        <translation>Όλα τα πορτοφόλια πρέπει να έχουν όνομα.</translation>
    </message>
</context>
<context>
    <name>DlgChangePassphrase</name>
    <message>
        <location filename="qtdialogs.py" line="1263"/>
        <source>Please enter an passphrase for wallet encryption.


                              A good passphrase consists of at least 8 or more

                              random letters, or 5 or more random words.
</source>
        <translation>Παρακαλώ εισάγετε μια συνθηματική φράση για την κρυπτογράφηση του πορτοφολιού.


Μια καλή φράση πρόσβασης αποτελείται από τουλάχιστον 8 ή παραπάνω

τυχαία γράμματα, με 5 ή περισσότερες τυχαίες λέξεις.
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1269"/>
        <source>Change your wallet encryption passphrase</source>
        <translation>Αλλάξτε τη φράση κρυπτογράφησης πρόσβασης του πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1274"/>
        <source>Current Passphrase:</source>
        <translation>Υπάρχουσα Λέξη Κλειδί:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1280"/>
        <source>New Passphrase:</source>
        <translation>Νέα Λέξη Κλειδί:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1285"/>
        <source>Again:</source>
        <translation>Ξανά:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1300"/>
        <source>Disable encryption for this wallet</source>
        <translation>Απενεργοποίηση κρυπτογράφησης για αυτό το πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1307"/>
        <source>Accept</source>
        <translation>Αποδοχή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1308"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1315"/>
        <source>Set Encryption Passphrase</source>
        <translation>Ορισμός Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1317"/>
        <source>Change Encryption Passphrase</source>
        <translation>Αλλάξτε τη Φράση Κρυπτογράφησης Πρόσβασης του Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1349"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is non-ASCII!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξη κλειδί δεν είναι ASCII!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1352"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases do not match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξεις κλειδιά δεν ταιριάζουν!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1355"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is too short!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξη κλειδί είναι πολύ μικρή!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1357"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξεις κλειδιά ταιριάζουν!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1369"/>
        <source>Invalid Passphrase</source>
        <translation>Λάθος Λέξη Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1369"/>
        <source>You entered your confirmation passphrase incorrectly!</source>
        <translation>Έχετε εισάγει λάθος συνθηματική φράση επιβεβαίωσης!</translation>
    </message>
</context>
<context>
    <name>DlgConfirmBulkImport</name>
    <message>
        <location filename="qtdialogs.py" line="3447"/>
        <source>No Addresses to Import</source>
        <translation>Δεν Υπάρχουν Διευθύνσεις για Εισαγωγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3447"/>
        <source>
           There are no addresses to import!</source>
        <translation>
Δεν Υπάρχουν Διευθύνσεις για Εισαγωγή!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3452"/>
        <source>a new wallet</source>
        <translation>ένα νέο πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3455"/>
        <source>wallet, &lt;b&gt;%1&lt;/b&gt; (%2)</source>
        <translation>Πορτοφόλι, &lt;b&gt;%1&lt;/b&gt; (%2)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3456"/>
        <source>
         'You are about to import &lt;b&gt;%1&lt;/b&gt; addresses into %2.&lt;br&gt;&lt;br&gt; '
         &apos;The following is a list of addresses to be imported:</source>
        <translation>
&apos;Θα εισάγετε τις &lt;b&gt;%1&lt;/b&gt; διευθύνσεις στο %2.&lt;br&gt;&lt;br&gt; &apos;
&apos;Οι ακόλουθες διευθύνσεις θα εισαχθούν:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3471"/>
        <source>Import</source>
        <translation>Εισαγωγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3472"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3484"/>
        <source>Confirm Import</source>
        <translation>Επιβεβαίωση Εισαγωγής</translation>
    </message>
</context>
<context>
    <name>DlgConfirmSend</name>
    <message>
        <location filename="qtdialogs.py" line="4899"/>
        <source> To see complete transaction details
                             &lt;a href=&quot;None&quot;&gt;click here&lt;/a&gt;&lt;/font&gt;</source>
        <translation>Για να δείτε τις λεπτομέρειες όλων των συναλλαγών
 &lt;a href=&quot;None&quot;&gt;κάντε κλίκ εδώ&lt;/a&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4908"/>
        <source>
         This transaction will spend &lt;b&gt;%1 BTC&lt;/b&gt; from
         &lt;font color=&quot;%2&quot;&gt;Wallet &quot;&lt;b&gt;%3&lt;/b&gt;&quot; (%4)&lt;/font&gt; to the following
         recipients:</source>
        <translation>
Η συναλλαγή θα ξοδέψει &lt;b&gt;%1 BTC&lt;/b&gt; από
&lt;font color=&quot;%2&quot;&gt;Πορτοφόλι &quot;&lt;b&gt;%3&lt;/b&gt;&quot; (%4)&lt;/font&gt; στους ακόλουθους
παραλήπτες:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4914"/>
        <source>
            &lt;font size=3&gt;* Starred
            outputs are going to the same wallet from which they came
            and do not affect the wallet's final balance.
            The total balance of the wallet will actually only decrease
            &lt;b&gt;%1 BTC&lt;/b&gt; as a result of this transaction.  %2&lt;/font&gt;</source>
        <translation>

&lt;font size=3&gt;* Οι έξοδοι
με αστέρι πηγαίνουν στο ίδιο πορτοφόλι από το οποίο ήρθαν
και δεν επηρεάζουν τα τελικά ποσά.
Το συνολικό υπόλοιπο του πορτοφολιού θα μειωθεί μόνο όταν
τα &lt;b&gt;%1 BTC&lt;/b&gt; θα είναι αποτέλεσμα αυτής της συναλλαγής. %2&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4962"/>
        <source>Send</source>
        <translation>Αποστολή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4963"/>
        <source>Are you sure you want to execute this transaction?</source>
        <translation>Είστε σίγουροι ότι θέλετε να εκτελέσετε αυτή τη συναλλαγή;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4965"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4966"/>
        <source>Does the above look correct?</source>
        <translation>Τα παραπάνω φαίνονται σωστά;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4968"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4992"/>
        <source>Confirm Transaction</source>
        <translation>Επιβεβαίωση Συναλλαγής</translation>
    </message>
</context>
<context>
    <name>DlgCorruptWallet</name>
    <message>
        <location filename="qtdialogs.py" line="14308"/>
        <source>Wallet Consistency Check Failed!</source>
        <translation>Ο Έλεγχος Συνοχής Πορτοφολιού Απέτυχε!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14310"/>
        <source>Perform Wallet Consistency Check</source>
        <translation>Έλεγχος Συνοχής Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14312"/>
        <source>
         &lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;&lt;u&gt;%2&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
         &lt;br&gt;&lt;br&gt;
         Armory software now detects and prevents certain kinds of
         hardware errors that could lead to problems with your wallet.
         &lt;br&gt; </source>
        <translation>

&lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;&lt;u&gt;%2&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
&lt;br&gt;&lt;br&gt;
Το λογισμικό του Armory εντόπισε και απέτρεψε συγκεκριμένα κομμάτια υλικού
που μπορούσαν να οδηγήσουν σε προβλήματα με το πορτοφόλι
&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14323"/>
        <source>
            Armory has detected that wallet file &lt;b&gt;Wallet &quot;%1&quot; (%2)&lt;/b&gt;
            is inconsistent and should be further analyzed to ensure that your
            funds are protected.
            &lt;br&gt;&lt;br&gt;
            &lt;font color=&quot;%3&quot;&gt;This error will pop up every time you start
            Armory until the wallet has been analyzed and fixed!&lt;/font&gt;</source>
        <translation>
Το Armory εντόπισε ότι το αρχείο πορτοφολιού &lt;b&gt; Πορτοφόλι &quot;%1&quot; (%2) &lt;/b&gt;
είναι ασυνεπές και θα πρέπει να αναλυθεί περαιτέρω για να εξασφαλιστεί ότι τα
κεφάλαια είναι προστατευμένα.
&lt;br&gt;&lt;br&gt;
&lt;font color=&quot;%3&quot;&gt; Αυτό το σφάλμα θα εμφανιστεί κάθε φορά που ξεκινά
το Armory μέχρι το πορτοφόλι να έχει αναλυθεί και να είναι σταθερό! &lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14331"/>
        <source>
            Armory will perform a consistency check on &lt;b&gt;Wallet &quot;%1&quot; (%2)&lt;/b&gt;
            and determine if any further action is required to keep your funds
            protected.  This check is normally performed on startup on all
            your wallets, but you can click below to force another
            check.</source>
        <translation>
Το Armory θα διενεργήσει έλεγχο συνέπειας στο &lt;b&gt;Πορτοφόλι &quot;%1&quot; (%2) &lt;/b&gt;
και να καθορίσει εάν απαιτείται περαιτέρω δράση για να κρατήσει τα χρήματα σας
προστατεύμένα. Αυτός ο έλεγχος εκτελείται κανονικά κατά την εκκίνηση των
πορτοφολιών σας, αλλά μπορείτε να κάνετε κλικ παρακάτω για να αναγκάσετε άλλον ένα έλεγχο.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14362"/>
        <source>Hide</source>
        <translation>Απόκρυψη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14363"/>
        <source>Run Analysis and Recovery Tool</source>
        <translation>Εκτελέστε το Εργαλείο Ανάλυσης και Ανάκτησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14373"/>
        <source>
         &lt;u&gt;Your wallets will be ready to fix once the scan is over&lt;/u&gt;&lt;br&gt;
         You can hide this window until then&lt;br&gt;</source>
        <translation>
&lt;u&gt;Τα πορτοφόλια θα είναι έτοιμα μόλις τελειώσει η σάρωση&lt;/u&gt;&lt;br&gt;
Μπορείτε να κρύψετε το παράθυρο μέχρι τότε&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14395"/>
        <source>Wallet Error</source>
        <translation>Σφάλμα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14421"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14510"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14525"/>
        <source>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Failed to fix wallets!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="14529"/>
        <source>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Wallet consistent, nothing to
            fix.&lt;/b&gt;&lt;/font&gt;</source>
        <comment>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Wallets consistent, nothing to
            fix.&lt;/b&gt;&lt;/font&gt;</comment>
        <translation type="obsolete">
            <numerusform>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Wallet consistent, nothing to
            fix.&lt;/b&gt;&lt;/font&gt;</numerusform>
            <numerusform/>
        </translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="14532"/>
        <source>Wallet consistent!</source>
        <comment>Wallets consistent!</comment>
        <translation type="obsolete">
            <numerusform>Wallet consistent!</numerusform>
            <numerusform/>
        </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14537"/>
        <source>
               &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;
               &lt;font size=4&gt;&lt;b&gt;&lt;u&gt;There may still be issues with your
               wallet!&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
               &lt;br&gt;
               It is important that you send us the recovery logs
               and an email address so the Armory team can check for
               further risk to your funds!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;
&lt;font size=4&gt;&lt;b&gt;&lt;u&gt;Μπορεί να υπάρχουν θέματα με το
πορτοφόλι σας!&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
&lt;br&gt;
Είναι σημαντικό να μας στείλετε τα αρχεία ανάκαμψης
και μια διεύθυνση ηλεκτρονικού ταχυδρομείου, ώστε η ομάδα του Armory να μπορεί να ελέγξει για
περαιτέρω κινδύνους για τα χρήματά σας!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14547"/>
        <source>&lt;h2 style=&quot;color: red;&quot;&gt;                                     Consistency check failed! &lt;/h2&gt;</source>
        <translation>&lt;h2 style=&quot;color: red;&quot;&gt; Ο έλεγχος συνέπειας απέτυχε! &lt;/h2&gt;</translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="14529"/>
        <source>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Wallet(s) consistent, nothing to
            fix.&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="14532"/>
        <source>Wallet(s) consistent!</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
</context>
<context>
    <name>DlgCreatePromNote</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3127"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Create Simulfunding Promissory Note
         &lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Δημιουργήστε μια Simulfunding Υποσχετική Σημείωση
&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3132"/>
        <source>
         Use this form to create a
         &quot;promissory note&quot; which can be combined with notes from other 
         parties to fund an address or lockbox simultaneously
         (&lt;i&gt;&quot;simulfunding&quot;&lt;/i&gt;).  This funding
         transaction will not be valid until all promissory notes are 
         merged into a single transaction, then all funding parties 
         will review and sign it.  
         &lt;br&gt;&lt;br&gt;
         If this lockbox is being funded by only one party, using this
         interface is unnecessary.  Have the funding party send Bitcoins 
         to the destination address or lockbox in the normal way.</source>
        <translation>
Χρησιμοποιήστε αυτή τη φόρμα για να δημιουργήσετε ένα
&quot;Γραμμάτιο&quot;, το οποίο μπορεί να συνδυαστεί με σημειώσεις από άλλα
μέρη για να χρηματοδοτήσει μια διεύθυνση ή ένα κουτί ταυτόχρονα
(&lt;i&gt;&quot;simulfunding&quot;&lt;/i&gt;). Αυτή η συναλλαγή χρηματοδότησης δεν θα ισχύει έως ότου όλα τα γραμμάτια είναι
συγχωνεύμένα σε μία ενιαία συναλλαγή, τότε όλα τα μέρη χρηματοδότησης
θα την επανεξετάσουν και θα την υπογράψουν.
&lt;br&gt;&lt;br&gt;
Εάν αυτό το κουτί χρηματοδοτείται από ένα μόνο μέρος, χρησιμοποιώντας αυτό
το περιβάλλον είναι περιττό. Να κάνετε το κόμμα χρηματοδότησης να στείλει Bitcoin
στη διεύθυνση προορισμού ή στο κουτί με κανονικό τρόπο.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3145"/>
        <source>
         &lt;b&gt;NOTE:&lt;/b&gt; At the moment, simulfunding is restricted to using
         single-signature wallets/addresses for funding.    More
         complex simulfunding transactions will be possible in a future 
         version of Armory.</source>
        <translation>
&lt;b&gt; Σημείωση: &lt;/b&gt; Αυτή τη στιγμή, το simulfunding περιορίζεται στη χρήση
πορτοφολιού μόνο υπογραφής/διευθύνσεις για χρηματοδότηση. Περισσότερο
σύνθετες συναλλαγές simulfunding θα είναι δυνατόν σε μια μελλοντική
έκδοση του Armory.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3167"/>
        <source>Address:</source>
        <translation>Διεύθυνση:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3168"/>
        <source>Amount:</source>
        <translation>Ποσόν:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3169"/>
        <source>Add fee:</source>
        <translation>Προσθέστε χρέωση:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3171"/>
        <source>BTC</source>
        <translation>BTC</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3205"/>
        <source>
         This label will be attached to the promissory note to help identify
         who is committing these funds.  If you do not fill this in, each
         other party signing will see &lt;i&gt;[[Unknown Signer]]&lt;/i&gt; for the ID.</source>
        <translation>
Αυτή η ετικέτα θα προστεθεί στο υποσχετήριο σημείωμα για να βοηθήσει στην
ταυτοποίηση των ποσών. Αν δεν το συμπληρώσετε, κάθε
άλλο μέλος που θα το υπογράψει θα δεί &lt;i&gt;[[Άγνωστος Υπογράφων]]&lt;/i&gt; στην Ταυτότητα.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3213"/>
        <source>Source of Funding</source>
        <translation>Πηγή Χρηματοδότησης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3220"/>
        <source>Funding Destination</source>
        <translation>Χρηματοδοτούμενος Προορισμός</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3243"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3244"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3309"/>
        <source>Blockchain Not Available</source>
        <translation>Η Αλυσίδα Συναλλαγών Δεν Είναι Έτοιμη</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3309"/>
        <source>
            The blockchain has become unavailable since you opened this
            window.  Creation of the promissory note cannot continue.  If 
            you think you should be online, please try again in a minute,
            or after restarting Armory</source>
        <translation>
Η αλυσίδα έχει γίνει με διαθέσιμη από τη στιγμή που άνοιξε αυτό το
παράθυρο. Η δημιουργία του υποσχετηρίου γραμμάτιο δεν μπορεί να συνεχιστεί. Αν
νομίζετε ότι θα πρέπει να είστε σε απευθείας σύνδεση, δοκιμάστε ξανά σε ένα λεπτό,
ή μετά την επανεκκίνηση του Armory</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3321"/>
        <source>Lockbox Selected</source>
        <translation>Το Κουτί Επιλέχθηκε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3321"/>
        <source>
            Currently, Armory does not implement simulfunding with lockbox
            inputs.  Please choose a regular wallet as your input</source>
        <translation>
Τώρα, το Armory δεν υλοποιεί το simulfunding στις εισόδους για τα κουτιά.
Παρακαλώ επιλέξτε κάποιο κανονικό πορτοφόλι σαν είσοδο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3328"/>
        <source>No Wallet Selected</source>
        <translation>Κανένα Πορτοφόλι Δεν Έχει Επιλεχθεί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3328"/>
        <source>
            The wallet selected is not available.  Select another wallet.</source>
        <translation>
Το πορτοφόλι που επιλέξατε δεν είναι διαθέσιμο. Επιλέξτε ένα άλλο πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3338"/>
        <source>Zero Amount</source>
        <translation>Μηδενικό Ποσόν</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3338"/>
        <source>
               You cannot promise 0 BTC.   &lt;br&gt;Please enter 
               a positive amount.</source>
        <translation>
Δεν μπορείτε να υποσχεθείτε 0 BTC. &lt;br&gt;Παρακαλώ εισάγετε ένα
θετικό αριθμό.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3343"/>
        <source>Negative Value</source>
        <translation>Αρνητική Αξία</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3369"/>
        <source>
            You have specified a negative amount. &lt;br&gt;Only
            positive values are allowed!</source>
        <translation>
Έχετε καθορίσει μια αρνητική αξία. &lt;br&gt;Μόνο
θετικές αξίες επιτρέπονται!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3374"/>
        <source>Too much precision</source>
        <translation>Πάρα πολύ ακρίβεια</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3374"/>
        <source>
            Bitcoins can only be specified down to 8 decimal places. 
            The smallest value that can be sent is  0.0000 0001 BTC. 
            Please enter a new amount</source>
        <translation>
Τα Bitcoin μπορούν να καθοριστούν μέχρι τα 8 δεκαδικά ψηφία.
Το χαμηλότερο ποσό που μπορεί να σταλεί είναι 0.00000001 BTC.
Παρακαλώ εισάγετε νέο ποσό</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3380"/>
        <source>Missing amount</source>
        <translation>Λείπει ποσόν</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3354"/>
        <source>
            You did not specify an amount to promise!</source>
        <translation>
Δεν προσδιορίσατε το ποσό υπόσχεσης!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3358"/>
        <source>Invalid Value String</source>
        <translation>Λάθος Μορφή Τιμής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3384"/>
        <source>
            The amount you specified is invalid (%1).</source>
        <translation>
Το ποσό που καθορίστηκε είναι λάθος (%1).</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3369"/>
        <source>Negative Fee</source>
        <translation>Αρνητικά Τέλη</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3380"/>
        <source>
            &apos;You did not specify an amount to promise!</source>
        <translation>
&apos;Δεν καθορίσατε ποσόν υπόσχεσης!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3384"/>
        <source>Invalid Fee String</source>
        <translation>Λάθος Μορφή Χρέωσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3394"/>
        <source>Not enough funds!</source>
        <translation>Δεν υπάρχουν αρκετά κεφάλαια!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3394"/>
        <source>
            You specified &lt;b&gt;%1&lt;/b&gt; BTC (amount + fee), but the selected wallet
            only has &lt;b&gt;%2&lt;/b&gt; BTC spendable.</source>
        <translation>
Καθορίσατε &lt;b&gt;%1&lt;/b&gt; BTC (ποσόν + φόρος), αλλά το επιλεγμένο πορτοφόλι
έχει μόνο &lt;b&gt;%2&lt;/b&gt; BTC προς χρήση.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3404"/>
        <source>Coin Selection Error</source>
        <translation>Σφάλμα Επιλογής Νομισμάτων</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3404"/>
        <source>
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions.</source>
        <translation>
Παρουσιάστηκε σφάλμα κατασκευής της συναλλαγής σας, που οφείλεται σε μια
ιδιορρυθμία στον τρόπο εργασίας των Bitcoin συναλλαγών. Αν δείτε αυτό
το λάθος περισσότερες από μία φορά, δοκιμάστε να στείλετε τα BTC σας σε δύο ή περισσότερες χωριστές συναλλαγές.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3436"/>
        <source>Transaction Not Found</source>
        <translation>Η Συναλλαγή Δεν Βρέθηκε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3436"/>
        <source>
               There was an error creating the promissory note -- the selected
               coins were not found in the blockchain.  Please go to 
               &quot;&lt;i&gt;Help&lt;/i&gt;&quot;â&quot;&lt;i&gt;Submit Bug Report&lt;/i&gt;&quot; from 
               the main window and submit your log files so the Armory team
               can review this error.</source>
        <translation>
Υπήρξε ένα σφάλμα κατά τη δημιουργία του γραμμάτιου - τα επιλεγμένα
νομίσματα δεν βρέθηκαν στην αλυσίδα. Παρακαλώ πηγαίνετε στο &quot;&lt;i&gt; Βοήθεια &lt;/i&gt;&quot;â&lt;i&gt;
Και κάντε Υποβολή Αναφοράς Σφάλματος &lt;/i&gt;&quot; από
το κύριο παράθυρο και υποβάλετε τα αρχεία καταγραφής σας, έτσι ώστε η ομάδα του
οπλοστασίου να μπορεί να επανεξετάσει αυτό το σφάλμα.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3460"/>
        <source>Export Promissory Note</source>
        <translation>Εξαγωγή Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3461"/>
        <source>
            The text below includes all the data needed to represent your
            contribution to a simulfunding transaction.  Your money cannot move
            because you have not signed anything, yet.  Once all promissory
            notes are collected, you will be able to review the entire funding 
            transaction before signing.</source>
        <translation>
Το παρακάτω κείμενο περιλαμβάνει όλα τα στοιχεία που απαιτούνται για να 
εκπροσωπήσετε την συμβολή σας σε μια simulfunding συναλλαγή. Τα χρήματά σας δεν μπορούν να κινηθούν γιατί δεν έχετε υπογράψει τίποτα, ακόμα. Όταν όλα τα υποσχετήρια
και οι σημειώσεις συλλέχθούν, θα είστε σε θέση να επανεξετάσετε το σύνολο της χρηματοδότησης της συναλλαγής πριν από την υπογραφή.</translation>
    </message>
</context>
<context>
    <name>DlgDispTxInfo</name>
    <message>
        <location filename="qtdialogs.py" line="5740"/>
        <source>Sent-to-Self</source>
        <translation>Ιδία-Αποστολή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5757"/>
        <source>Received</source>
        <translation>Ελήφθησαν</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5761"/>
        <source>Sent</source>
        <translation>Εστάλη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5778"/>
        <source>Transaction Information:</source>
        <translation>Πληροφορίες Συναλλαγής:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5798"/>
        <source>Unique identifier for this transaction</source>
        <translation>Μοναδικό Αναγνωριστικό για αυτή τη συναλλαγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5799"/>
        <source>Transaction ID</source>
        <translation>Ταυτότητα Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5804"/>
        <source>[[ Transaction ID cannot be determined without all signatures ]]</source>
        <translation>[[ Η Ταυτότητα της Συναλλαγής δεν μπορεί να προσδιοριστεί χωρίς όλες τις υπογραφές ]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5814"/>
        <source>&lt;font color=&quot;gray&quot;&gt;
               [[ Transaction ID cannot be determined without all signatures ]]
               &lt;/font&gt;</source>
        <translation>&lt;font color=&quot;gray&quot;&gt;
[[ Η ταυτότητα της συναλλαγής δεν μπορεί να προσδιοριστεί χωρίς όλες τις υπογραφές ]]
&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5828"/>
        <source>Bitcoin Protocol Version Number</source>
        <translation>Αριθμός Έκδοσης πρωτοκόλλου Bitcoin</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5829"/>
        <source>Tx Version:</source>
        <translation>Έκδοση Συναλλαγής:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5833"/>
        <source>The time at which this transaction becomes valid.</source>
        <translation>Ο χρόνος κατά τον οποίο αυτή η συναλλαγή γίνεται έγκυρη.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5835"/>
        <source>Lock-Time:</source>
        <translation>Χρόνος-Κλειδώματος:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5837"/>
        <source>Immediate (0)</source>
        <translation>Άμεση (0)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5839"/>
        <source>Block %1</source>
        <translation>Μπλόκ %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5846"/>
        <source>Comment stored for this transaction in this wallet</source>
        <translation>Σχόλιο που αποθηκεύεται για αυτή τη συναλλαγή σε αυτό το πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5847"/>
        <source>User Comment:</source>
        <translation>Σχόλιο Χρήστη:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5851"/>
        <source>&lt;font color=&quot;gray&quot;&gt;[None]&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;gray&quot;&gt;[Καμία]&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5857"/>
        <source>The time that you computer first saw this transaction</source>
        <translation>Ο χρόνος που ο υπολογιστής σας είδε για πρώτη φορά αυτή τη συναλλαγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5860"/>
        <source>All transactions are eventually included in a &quot;block.&quot;  The
                  time shown here is the time that the block entered the &quot;blockchain.&quot;</source>
        <translation>Όλες οι συναλλαγές τελικά περιλαμβάνονται σε ένα &quot;μπλόκ&quot;. Ο χρόνος
που παρουσιάζεται εδώ είναι ο χρόνος που το μπλοκ μπήκε στην &quot;αλυσίδα.&quot;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5870"/>
        <source>This transaction has not yet been included in a block.
                  It usually takes 5-20 minutes for a transaction to get
                  included in a block after the user hits the &quot;Send&quot; button.</source>
        <translation>Η συναλλαγή αυτή δεν έχει ακόμη περιληφθεί σε μπλόκ.
Συνήθως χρειάζονται 5-20 λεπτά για μια συναλλαγή να
συμπεριληφθεί σε ένα μπλοκ αφού ο χρήστης πατήσει το κουμπί &quot;Αποστολή&quot;.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5882"/>
        <source>Every transaction is eventually included in a &quot;block&quot; which
                  is where the transaction is permanently recorded.  A new block
                  is produced approximately every 10 minutes.</source>
        <translation>Κάθε συναλλαγή τελικά περιλαμβάνετε σε ένα &quot;μπλοκ&quot; το οποίο
είναι εκεί που έχει καταχωρηθεί μόνιμα. Ένα νέο μπλόκ
παράγεται περίπου κάθε 10 λεπτά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5891"/>
        <source>The number of blocks that have been produced since
                     this transaction entered the blockchain.  A transaction
                     with 6 or more confirmations is nearly impossible to reverse.</source>
        <translation>Ο αριθμός των μπλοκ που έχουν παραχθεί απο τη στιγμή
που αυτή η συναλλαγή έχει εισέλθει στην αλυσίδα. Μια συναλλαγή
με 6 ή περισσότερες επιβεβαιώσεις είναι σχεδόν αδύνατο να αντιστραφεί.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5895"/>
        <source>Confirmations:</source>
        <translation>Επιβεβαιώσεις:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5901"/>
        <source>This transaction can be replaced by another transaction that
               spends the same inputs if the replacement transaction has
               a higher fee.</source>
        <translation>Αυτή η συναλλαγή μπορεί να αντικατασταθεί από μια άλλη συναλλαγή που
ξοδεύει τα ίδια έσοδα, αν η συναλλαγή αντικατάστασης έχει
μια υψηλότερη αμοιβή.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5905"/>
        <source>Mempool Replaceable: </source>
        <translation>Αναπληρώσιμη Μνήμη Πισίνας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5914"/>
        <source>Most transactions have at least a recipient output and a
               returned-change output.  You do not have enough information
               to determine which is which, and so this fields shows the sum
               of &lt;b&gt;all&lt;/b&gt; outputs.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5919"/>
        <source>Sum of Outputs:</source>
        <translation>Σύνολο των Εξόδων:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5923"/>
        <source>Bitcoins were either sent or received, or sent-to-self</source>
        <translation>Τα Bitcoin είτε απεστάλησαν ή ελήφθησαν ή αποστέλλονται στον ίδιο τον χρήστη.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5929"/>
        <source>The value shown here is the net effect on your
               wallet, including transaction fee.</source>
        <translation>Η τιμή που εμφανίζεται εδώ είναι το καθαρό αποτέλεσμα για το
πορτοφόλι σας, συμπεριλαμβανομένων των τελών συναλλαγής.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5943"/>
        <source>Transaction fees go to users supplying the Bitcoin network with
            computing power for processing transactions and maintaining security.</source>
        <translation>Οι αμοιβές συναλλαγής πηγαίνουν στους χρήστες για την παροχή στο δίκτυο του Bitcoin
της υπολογιστικής ισχύς τους για την επεξεργασία συναλλαγών και τη διατήρηση της ασφάλειας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5975"/>
        <source>All outputs of the transaction &lt;b&gt;excluding&lt;/b&gt; change-
                  back-to-sender outputs.  If this list does not look
                  correct, it is possible that the change-output was
                  detected incorrectly -- please check the complete
                  input/output list below.</source>
        <translation>Όλες οι έξοδοι της συναλλαγής &lt;b&gt;εξαιρουμένων&lt;/b&gt; των υπολοίπων
του ιδίου χρήστη. Αν ο κατάλογος αυτός δεν σωστός
είναι πιθανό ότι τα υπόλοιπα δεν
ανιχνεύτηκαν σωστά - παρακαλούμε να ελέγξετε ολόκληρη τη λίστα
με τον κατάλογο συναλλαγών εισόδου / εξόδου παρακάτω.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5981"/>
        <source>Recipients:</source>
        <translation>Παραλήπτες:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5995"/>
        <source>[%1 more recipients]</source>
        <translation>[%1 περισσότεροι παραλήπτες]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6109"/>
        <source>Transaction Inputs (Sending addresses):</source>
        <translation>Είσοδοι Συναλλαγής (Διευθύνσεις Αποστολής):</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6110"/>
        <source>All transactions require previous transaction outputs as
                  inputs.  </source>
        <translation>Όλες οι συναλλαγές απαιτούν τις προηγούμενες συναλλαγές εξάγωγής ως
εισόδους.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6113"/>
        <source>&lt;b&gt;Since the blockchain is not available, not all input
                      information is available&lt;/b&gt;.  You need to view this
                      transaction on a system with an internet connection
                      (and blockchain) if you want to see the complete information.</source>
        <translation>&lt;b&gt; Δεδομένου ότι η αλυσίδα δεν είναι διαθέσιμη, δεν είναι όλες οι πληροφορίες 
εισαγωγής διαθέσιμες &lt;/b&gt;. Θα πρέπει να δείτε αυτή την συναλλαγή σε ένα σύστημα μια 
σύνδεση στο Ίντερνετ (και την αλυσίδα), εάν θέλετε να δείτε τις πλήρεις πληροφορίες.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6118"/>
        <source>Each input is like an X amount dollar bill.  Usually there are more inputs
                      than necessary for the transaction, and there will be an extra
                      output returning change to the sender</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6123"/>
        <source>Transaction Outputs (Receiving addresses):</source>
        <translation>Εξόδοι Συναλλαγής (Διευθύνσεις Παραλαβής):</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6124"/>
        <source>Shows &lt;b&gt;all&lt;/b&gt; outputs, including other recipients
                  of the same transaction, and change-back-to-sender outputs
                  (change outputs are displayed in light gray).</source>
        <translation>Δείχνει &lt;b&gt;όλες&lt;/b&gt; τις εξόδους, συμπεριλαμβανομένων άλλων παραληπτών
της ίδιας συναλλαγής, και τις εξόδους για τα ρέστα
(Οι έξοδοι για τα ρέστα εμφανίζονται με ανοιχτό γκρι).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6129"/>
        <source>Some outputs might be &quot;change.&quot;
         </source>
        <translation>Μερικές εξόδοι μπορεί να είναι &quot;υπόλοιπα.&quot;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6148"/>
        <source>Copy Raw Tx (Hex)</source>
        <translation>Αντιγραφή Ωμής Συναλλαγής (Hex)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6150"/>
        <source>OK</source>
        <translation>Εντάξει</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6187"/>
        <source>Transaction Info</source>
        <translation>Πληροφορίες Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6196"/>
        <source>&lt;&lt;&lt; Less Info</source>
        <translation>&lt;&lt;&lt; Λιγότερες Πληροφορίες</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6206"/>
        <source>Advanced &gt;&gt;&gt;</source>
        <translation>Προχωρημένα &gt;&gt;&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6217"/>
        <source>TxIn Script:</source>
        <translation>TxIn Κώδικας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6224"/>
        <source>TxOut Script:</source>
        <translation>TxOut Κώδικας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6263"/>
        <source>&lt;i&gt;Copied to Clipboard!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε στο Πρόχειρο!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6293"/>
        <source>Copy Sender Address</source>
        <translation>Αντιγραφή Διεύθυνσης Αποστολέα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6329"/>
        <source>Copy Wallet ID</source>
        <translation>Αντιγραφή Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6330"/>
        <source>Copy Amount</source>
        <translation>Αντιγραφή Ποσού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6296"/>
        <source>More Info</source>
        <translation>Περισσότερες Πληροφορίες</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6328"/>
        <source>Copy Recipient Address</source>
        <translation>Αντιγραφή Διεύθυνσης Παραλήπτη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6331"/>
        <source>Copy Raw Script</source>
        <translation>Αντιγραφή Ωμού Κώδικα</translation>
    </message>
</context>
<context>
    <name>DlgDisplayTxIn</name>
    <message>
        <location filename="qtdialogs.py" line="6357"/>
        <source>&lt;center&gt;&lt;u&gt;&lt;b&gt;TxIn Information&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</source>
        <translation>&lt;center&gt;&lt;u&gt;&lt;b&gt;Πληροφορίες TxIn&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6382"/>
        <source>[[Cannot determine from TxIn Script]]</source>
        <translation>[[Δεν μπορεί να καθοριστεί ο κώδικας TxIn]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6387"/>
        <source>Wallet &quot;%1&quot; (%2)</source>
        <translation>Πορτοφόλι &quot;%1&quot; (%2)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6391"/>
        <source>Lockbox %1-of-%2 &quot;%3&quot; (%4)</source>
        <translation>Κουτί %1-of-%2 &quot;%3&quot; (%4)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6396"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Πληροφορίες για το TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6397"/>
        <source>   &lt;b&gt;TxIn Index:&lt;/b&gt;         %1</source>
        <translation> &lt;b&gt;Δείκτης TxIn:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6398"/>
        <source>   &lt;b&gt;TxIn Spending:&lt;/b&gt;      %1:%2</source>
        <translation> &lt;b&gt;TxIn Δαπάνη:&lt;/b&gt; %1:%2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6399"/>
        <source>   &lt;b&gt;TxIn Sequence&lt;/b&gt;:      0x%1</source>
        <translation> &lt;b&gt;TxIn Ακολουθία&lt;/b&gt;: 0x%1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6401"/>
        <source>   &lt;b&gt;TxIn Script Type&lt;/b&gt;:   %1</source>
        <translation> &lt;b&gt;TxIn Τύπος Κώδικα&lt;/b&gt;: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6402"/>
        <source>   &lt;b&gt;TxIn Source&lt;/b&gt;:        %1</source>
        <translation> &lt;b&gt;TxIn Πηγή&lt;/b&gt;: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6404"/>
        <source>   &lt;b&gt;TxIn Wallet&lt;/b&gt;:        %1</source>
        <translation> &lt;b&gt;TxIn Πορτοφόλι&lt;/b&gt;: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6405"/>
        <source>   &lt;b&gt;TxIn Script&lt;/b&gt;:</source>
        <translation> &lt;b&gt;TxIn Κώδικας&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6433"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxOut being spent by this TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Πληροφορίες για το TxOut που ξοδεύτηκε απο αυτό το TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6434"/>
        <source>   &lt;b&gt;Tx Hash:&lt;/b&gt;            %1</source>
        <translation> &lt;b&gt;Tx Κατατεματισμού:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6435"/>
        <source>   &lt;b&gt;Tx Out Index:&lt;/b&gt;       %1</source>
        <translation> &lt;b&gt;Tx Out Δείκτης:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6436"/>
        <source>   &lt;b&gt;Tx in Block#:&lt;/b&gt;       %1</source>
        <translation> &lt;b&gt;Tx στο μπλόκ#:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6437"/>
        <source>   &lt;b&gt;TxOut Value:&lt;/b&gt;        %1</source>
        <translation> &lt;b&gt;TxOut Τιμή:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6438"/>
        <source>   &lt;b&gt;TxOut Script Type:&lt;/b&gt;  %1</source>
        <translation> &lt;b&gt;TxOut Τύπος Κώδικα:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6439"/>
        <source>   &lt;b&gt;TxOut Address:&lt;/b&gt;      %1</source>
        <translation> &lt;b&gt;TxOut Διεύθυνση:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6441"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       %1</source>
        <translation> &lt;b&gt;TxOut Πορτοφόλι:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6442"/>
        <source>   &lt;b&gt;TxOUt Script:&lt;/b&gt;</source>
        <translation> &lt;b&gt;TxOUt Κώδικας:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6449"/>
        <source>Ok</source>
        <translation>Εντάξει</translation>
    </message>
</context>
<context>
    <name>DlgDisplayTxOut</name>
    <message>
        <location filename="qtdialogs.py" line="6467"/>
        <source>&lt;center&gt;&lt;u&gt;&lt;b&gt;TxOut Information&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</source>
        <translation>&lt;center&gt;&lt;u&gt;&lt;b&gt;TxOut Πληροφορίες&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6503"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxOut&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Πληροφορίες για το TxOut&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6504"/>
        <source>   &lt;b&gt;Tx Out Index:&lt;/b&gt;       %1</source>
        <translation> &lt;b&gt;Tx Out Δείκτης:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6505"/>
        <source>   &lt;b&gt;TxOut Value:&lt;/b&gt;        %1</source>
        <translation> &lt;b&gt;TxOut Τιμή:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6506"/>
        <source>   &lt;b&gt;TxOut Script Type:&lt;/b&gt;  %1</source>
        <translation> &lt;b&gt;TxOut Τύπος Κώδικα:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6507"/>
        <source>   &lt;b&gt;TxOut Address:&lt;/b&gt;      %1</source>
        <translation> &lt;b&gt;TxOut Διεύθυνση:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6509"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       %1</source>
        <translation> &lt;b&gt;TxOut Πορτοφόλι:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6511"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       [[Unrelated to any loaded wallets]]</source>
        <translation> &lt;b&gt;TxOut Πορτοφόλι:&lt;/b&gt; [[Άσχετο με οποιαδήποτε φορτωμένο πορτοφόλι]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6512"/>
        <source>   &lt;b&gt;TxOut Script:&lt;/b&gt;</source>
        <translation> &lt;b&gt;TxOut Κώδικας:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6519"/>
        <source>Ok</source>
        <translation>Εντάξει</translation>
    </message>
</context>
<context>
    <name>DlgDuplicateAddr</name>
    <message>
        <location filename="qtdialogs.py" line="3498"/>
        <source>No Addresses to Import</source>
        <translation>Δεν Υπάρχουν Διευθύνσεις για Εισαγωγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3498"/>
        <source>There are no addresses to import!</source>
        <translation>Δεν Υπάρχουν Διευθύνσεις για Εισαγωγή!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3502"/>
        <source>
         &lt;font color=%1&gt;Duplicate addresses detected!&lt;/font&gt; The following
         addresses already exist in other Armory wallets:</source>
        <translation>
&lt;font color=%1&gt;Διπλές διευθύνσεις ανιχνέυτηκαν!&lt;/font&gt; Η ακόλουθες
διευθύνσεις ήδη υπάρχουν σε άλλα πορτοφόλια Armory:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3515"/>
        <source>
         Duplicate addresses cannot be imported.  If you continue,
         the addresses above will be ignored, and only new addresses
         will be imported to this wallet.</source>
        <translation>
Διπλές διευθύνσεις δεν μπορούν να εισαχθούν. Αν συνεχίσετε,
οι διευθύνσεις παραπάνω θα πρέπει να αγνοηθούν, και μόνο οι νέες διεθύνσεις
θα εισαχθούν σε αυτό το πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3521"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3522"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3535"/>
        <source>Duplicate Addresses</source>
        <translation>Διπλές Διευθύνσεις</translation>
    </message>
</context>
<context>
    <name>DlgECDSACalc</name>
    <message>
        <location filename="qtdialogs.py" line="7808"/>
        <source>Multiply Scalars (mod n)</source>
        <translation>Πολλαπλασιάστε Βαθμωτές Μεταβλητές (mod n)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7809"/>
        <source>Scalar Multiply EC Point</source>
        <translation>Κλιμακωτός Πολλαπλασιασμός Σημείου EC </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7810"/>
        <source>Add EC Points</source>
        <translation>Προσθέστε σημεία EC </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7925"/>
        <source>Clear</source>
        <translation>Εκκαθάριση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7912"/>
        <source>
         Use this form to perform Bitcoin elliptic curve calculations.  All
         operations are performed on the secp256k1 elliptic curve, which is
         the one used for Bitcoin.
         Supply all values as 32-byte, big-endian, hex-encoded integers.
         &lt;br&gt;&lt;br&gt;
         The following is the secp256k1 generator point coordinates (G): &lt;br&gt;
            &lt;b&gt;G&lt;/b&gt;&lt;sub&gt;x&lt;/sub&gt;: %1 &lt;br&gt;
            &lt;b&gt;G&lt;/b&gt;&lt;sub&gt;y&lt;/sub&gt;: %2</source>
        <translation>
Κάντε αυτή τη φόρμα να φτιάχνει ελλιπτικής καμπύλης πράξεις. Όλες οι δράσεις
που γίνονται με την secp256k1 ελλιπτική καμπύλη, που είναι
αυτό που χρησιμοποιείτε απο το Bitcoin.
Δώστε όλες τις αξίες σαν 32-μπάιτ, big-endian, δεκαεξαδικούς ακεραίους.
&lt;br&gt;&lt;br&gt;
Η ακόλουθη γεννήτρια secp256k1 δείχνει στις συντεταγμένες (G): &lt;br&gt;
&lt;b&gt;G&lt;/b&gt;&lt;sub&gt;x&lt;/sub&gt;: %1 &lt;br&gt;
&lt;b&gt;G&lt;/b&gt;&lt;sub&gt;y&lt;/sub&gt;: %2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7929"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Πίσω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7945"/>
        <source>ECDSA Calculator</source>
        <translation>Υπολογιστής ECDSA </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7955"/>
        <source>Bad Input</source>
        <translation>Κακή Είσοδος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7955"/>
        <source>Value &quot;%1&quot; is invalid.  Make sure the value is specified in
            hex, big-endian</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8009"/>
        <source>Invalid EC Point</source>
        <translation>Λάθος Σημείο EC</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7981"/>
        <source>The point you specified (&lt;b&gt;B&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8003"/>
        <source>The point you specified (&lt;b&gt;A&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8009"/>
        <source>'The point you specified (&lt;b&gt;B&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgEULA</name>
    <message>
        <location filename="qtdialogs.py" line="3956"/>
        <source>I agree to all the terms of the license above</source>
        <translation>Συμφωνώ με όλους τους όρους της άδειας παραπάνω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3958"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3959"/>
        <source>Accept</source>
        <translation>Αποδοχή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3967"/>
        <source>
         &lt;b&gt;Armory Bitcoin Client is licensed in part under the
         &lt;i&gt;Affero General Public License, Version 3 (AGPLv3)&lt;/i&gt;
         and in part under the &lt;i&gt;MIT License&lt;/i&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Additionally, as a condition of receiving this software
         for free, you accept all risks associated with using it
         and the developers of Armory will not be held liable for any
         loss of money or bitcoins due to software defects.
         &lt;br&gt;&lt;br&gt;
         &lt;b&gt;Please read the full terms of the license and indicate your
         agreement with its terms.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3988"/>
        <source>Armory License Agreement</source>
        <translation>Άδεια Χρήσης Armory </translation>
    </message>
</context>
<context>
    <name>DlgEnterOneFrag</name>
    <message>
        <location filename="qtdialogs.py" line="13462"/>
        <source> You have entered fragments %1, so far.  </source>
        <translation>Έχετε εισάγει θραύσματα %1, μέχρι στιγμής.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13464"/>
        <source>
         &lt;b&gt;&lt;u&gt;Enter Another Fragment...&lt;/u&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt; %1
         The fragments can be entered in any order, as long as you provide
         enough of them to restore the wallet.  If any fragments use a
         SecurePrintâ¢ code, please enter it once on the
         previous window, and it will be applied to all fragments that
         require it.</source>
        <translation>
&lt;b&gt; &lt;u&gt; Εισαγωγή Άλλου Θραύσματος... &lt;/u&gt; &lt;/b&gt; &lt;br&gt; %1
Τα θραύσματα μπορούν να εισαχθούν σε οποιαδήποτε σειρά, εφ &apos;όσον παρέχουν
αρκετά από αυτά για να αποκατασταθεί το πορτοφόλι. Αν τα θραύσματα χρησιμοποιούν
ένα SecurePrintâ¢ κώδικα, παρακαλούμε να τον εισάγετε μία φορά στο
προηγούμενο παράθυρο, και θα εφαρμοστεί σε όλα τα θραύσματα που το
απαιτούν αυτό.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13514"/>
        <source>&lt;b&gt;Backup Type:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Τύπος Αντιγράφου Ασφαλείας:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13546"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation>SecurePrintâ¢ Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13561"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13562"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13578"/>
        <source>Restore Single-Sheet Backup</source>
        <translation>Επαναφορά Μονόφυλλου Αντιγράφου Ασφαλείας σε Χαρτί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13644"/>
        <source>
               The ID field indicates that this is a SecurePrintâ¢
               Backup Type. You have either entered the ID incorrectly or
               have chosen an incorrect Backup Type.</source>
        <translation>
Το πεδίο ταυτότητας υποδηλώνει ότι αυτό είναι ένα SecurePrintâ¢
Τύπου Αντίγραφο. Είτε έχετε πληκτρολογήσει λανθασμένα το αναγνωριστικό ή
επιλέξατε ένα λανθασμένο Τύπο Αντιγράφου Ασφαλέιας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13662"/>
        <source>Verify Wallet ID</source>
        <translation>Πιστοποίηση Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13662"/>
        <source>
               There is an error in the data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page. &lt;br&gt;&lt;br&gt;
               The error occured on the &quot;%1&quot; line.</source>
        <translation>
Υπάρχει ένα λάθος στα δεδομένα που έχετε εισαγάγει που δεν μπορούσε να
διορθωθεί αυτόματα. Ελέγξτε ξανά ότι έχετε εισάγει το
κείμενο ακριβώς όπως εμφανίζεται στη σελίδα του πορτοφολιού για τα αντίγραφα ασφαλέιας. &lt;br&gt;&lt;br&gt;
Το σφάλμα είναι στη &quot;%1&quot; γραμμή.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13681"/>
        <source>Verify Fragment ID</source>
        <translation>Πιστοποίηση Ταυτότητας Θραύσματος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13681"/>
        <source>
         The data you entered is for fragment:
         &lt;br&gt;&lt;br&gt; &lt;font color=&quot;%1 size=3&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt;  &lt;br&gt;&lt;br&gt;
         Does this ID match the &quot;Fragment:&quot; field displayed on your backup?
         If not, click &quot;No&quot; and re-enter the fragment data.</source>
        <translation>
Τα δεδομένα που έχετε εισαγάγει είναι για το κομμάτι:
&lt;br&gt;&lt;br&gt; &lt;font color=&quot;%1 size=3&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; &lt;br&gt;&lt;br&gt;
Αυτή η Ταυτότητα ταιριάζει με το &quot;Θραύσμα:&quot; πεδίου που εμφανίζεται στο αντίγραφο ασφαλείας σας
Αν όχι, κάντε κλικ στο κουμπί &quot;Όχι&quot; και εισαγάγετε ξανά τα θράυσματα δεδομένων.</translation>
    </message>
</context>
<context>
    <name>DlgEnterSecurePrintCode</name>
    <message>
        <location filename="qtdialogs.py" line="13416"/>
        <source>
         This fragment file requires a SecurePrintâ¢ code.
         You will only have to enter this code once since it is the same
         on all fragments.</source>
        <translation>
Αυτο το θραύσμα αρχείου απαιτεί ένα κωδικό SecurePrintâ¢.
Χρειάζετε να βάλετε τον κωδικό αυτό μόνο μια φορά για όλα τα θραύσματα.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13421"/>
        <source>SecurePrintâ¢ Code: </source>
        <translation>SecurePrintâ¢ Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13425"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13426"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13438"/>
        <source>Enter Secure Print Code</source>
        <translation>Εισάγετε τον Secure Print Κωδικό</translation>
    </message>
</context>
<context>
    <name>DlgExecLongProcess</name>
    <message>
        <location filename="qtdialogs.py" line="7723"/>
        <source>Please Wait...</source>
        <translation>Παρακαλώ Περιμένετε...</translation>
    </message>
</context>
<context>
    <name>DlgExpWOWltData</name>
    <message>
        <location filename="qtdialogs.py" line="11284"/>
        <source>Export Watching-Only Wallet File</source>
        <translation>Εξαγωγή Αρχείου Πορτοφολιού Παρακολούθησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11285"/>
        <source>Copy to clipboard</source>
        <translation>Αντιγραφή στο πρόχειρο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11287"/>
        <source>Save to Text File</source>
        <translation>Αποθήκευση σε Αρχείο Κειμένου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11288"/>
        <source>Print Root Data</source>
        <translation>Εκτύπωση Δεδομένων Root</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11300"/>
        <source>
         Watch-Only Root ID:&lt;br&gt;&lt;b&gt;%1&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Watch-Only Root Data:</source>
        <translation>
Ταυτότητα Μόνο Παρακολούθησης Root:&lt;br&gt;&lt;b&gt;%1&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Μόνο Παρακολούθησης Root Δεδομένα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11307"/>
        <source>Watch-Only Wallet Export</source>
        <translation>Εξαγωγή Πορτοφολιού Παρακολούθησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11319"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11324"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;&lt;font size=4 color=&quot;%1&quot;&gt;Export Watch-Only
         Wallet: %2&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Use a watching-only wallet on an online computer to distribute
         payment addresses, verify transactions and monitor balances, but
         without the ability to move the funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11332"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Entire Wallet File&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         &lt;i&gt;&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;(Recommended)&lt;/font&gt;&lt;/b&gt;&lt;/i&gt;
         An exact copy of your wallet file but without any of the private
         signing keys. All existing comments and labels will be carried
         with the file. Use this option if it is easy to transfer files
         from this system to the target system.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11341"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Only Root Data&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Same as above, but only five lines of text that are easy to
         print, email inline, or copy by hand.  Only produces the
         wallet addresses.   No comments or labels are carried with
         it.</source>
        <translation>
&lt;center&gt;&lt;b&gt;&lt;u&gt;Μόνο Δεδομένα Root&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
&lt;br&gt;
Ίδια όπως παραπάνω, αλλά μόνο πέντε γραμμές κειμένου που είναι εύκολο στην
εκτύπωση, μέσα σε e-mail, ή αντίγραφο με το χέρι. Παράγει τις
διευθύνσεις πορτοφολιού. Δεν υπάρχουν σχόλια ή επισημάνσεις που θα πραγματοποιηθούν για αυτό.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11349"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
</context>
<context>
    <name>DlgExportAsciiBlock</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2321"/>
        <source>Copy to Clipboard</source>
        <translation>Αντιγραφή στο πρόχειρο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2322"/>
        <source>Save to File</source>
        <translation>Αποθήκευση σε Αρχείο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2323"/>
        <source>Send Email</source>
        <translation>Αποστολή Email</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2324"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2346"/>
        <source>Export ASCII Block</source>
        <translation>Εξαγωγή ASCII Μπλόκ</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2378"/>
        <source>Email Triggered</source>
        <translation>Το Email Ενεργοποιήθηκε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2378"/>
        <source>
            Armory attempted to execute a &quot;mailto:&quot; link which should trigger
            your email application or web browser to open a compose-email window.
            This does not work in all environments, and you might have to 
            manually copy and paste the text in the box into an email.
            </source>
        <translation>
Το Armory προσπάθησε να εκτελέσει ένα &quot;mailto:&quot; σύνδεσμο που θα πρέπει ενεργοποιήσει 
την εφαρμογή email σας ή το πρόγραμμα περιήγησης στο Web για να ανοίξει ένα 
παράθυρο σύνταξης email Αυτό δεν λειτουργεί σε όλα τα περιβάλλοντα, και ίσως 
χρειαστεί να το κάνετε χειροκίνητα και να αντιγράψετε και να επικολλήσετε το κείμενο 
στο πλαίσιο σε ένα email.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2378"/>
        <source>Do not show this message again</source>
        <translation>Να μήν εμφανίζεται το μύνημα ξανά</translation>
    </message>
</context>
<context>
    <name>DlgExportTxHistory</name>
    <message>
        <location filename="qtdialogs.py" line="9487"/>
        <source>My Wallets</source>
        <translation>Τα Πορτοφόλια μου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9488"/>
        <source>Offline Wallets</source>
        <translation>Εκτός Σύνδεσης Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9489"/>
        <source>Other Wallets</source>
        <translation>Άλλα Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9492"/>
        <source>All Wallets</source>
        <translation>Όλα τα Πορτοφόλια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9493"/>
        <source>All Lockboxes</source>
        <translation>Κουτιά Πολλαπλών Υπογραφών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9494"/>
        <source>All Wallets &amp; Lockboxes</source>
        <translation>Όλα τα Πορτοφόλια και τα Κουτιά Πολλαπλών Υπογραφών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9507"/>
        <source>Date (newest first)</source>
        <translation>Ημερομηνία (πιο πρόσφατα πρώτα)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9508"/>
        <source>Date (oldest first)</source>
        <translation>Ημερομηνία (τα παλαιότερα πρώτα)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9513"/>
        <source>Comma-Separated Values (*.csv)</source>
        <translation>Τιμές Διαχωρισμένες με Κόμμα (*.csv)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9517"/>
        <source>Use any of the following symbols:&lt;br&gt;</source>
        <translation>Χρησιμοποιήστε οποιαδήποτε από τα παρακάτω σύμβολα:&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9528"/>
        <source>Reset to Default</source>
        <translation>Επαναφορά στις Προεπιλογές</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9538"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9539"/>
        <source>Export</source>
        <translation>Εξαγωγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9548"/>
        <source>Export Format:</source>
        <translation>Μορφή Εξαγωγής:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9555"/>
        <source>Wallet(s) to export:</source>
        <translation>Πορτοφόλι(α) για εξαγωγή:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9562"/>
        <source>Sort Table:</source>
        <translation>Ταξινόμηση Πίνακα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9568"/>
        <source>Date Format:</source>
        <translation>Μορφή Ημερομηνίας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9593"/>
        <source>Example: %1</source>
        <translation>Παράδειγμα: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9596"/>
        <source>Example: [[invalid date format]]</source>
        <translation>Παράδειγμα: [[Μη έγκυρη μορφή ημερομηνίας]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9608"/>
        <source>Invalid date format</source>
        <translation>Λάθος μορφή ημερομηνίας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9608"/>
        <source>Cannot create CSV without a valid format for transaction dates and times</source>
        <translation>Δεν είναι δυνατή η δημιουργία CSV χωρίς έγκυρη μορφή για τις ημερομηνίες των συναλλαγών και τις ώρες</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9663"/>
        <source>Total</source>
        <translation>Σύνολο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9664"/>
        <source>Spendable</source>
        <translation>Δαπανήσιμα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9665"/>
        <source>Unconfirmed</source>
        <translation>Ανεπιβεβαίωτα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9704"/>
        <source>Export Date: %1
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9705"/>
        <source>Total Funds: %1
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9706"/>
        <source>Spendable Funds: %1
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9707"/>
        <source>Unconfirmed Funds: %1
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9710"/>
        <source>Included Wallets:
</source>
        <translation>Πορτοφόλια που Περιλαμβάνονται:
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9717"/>
        <source>%1 (lockbox),%2
</source>
        <translation>%1 (κουτί),%2
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9721"/>
        <source>Date</source>
        <translation>Ημερομηνία</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9721"/>
        <source>Transaction ID</source>
        <translation>Ταυτότητα Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9721"/>
        <source>Number of Confirmations</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9721"/>
        <source>Wallet ID</source>
        <translation>Ταυτότητα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9722"/>
        <source>Wallet Name</source>
        <translation>Όνομα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9722"/>
        <source>Credit</source>
        <translation>Πίστωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9722"/>
        <source>Debit</source>
        <translation>Χρέωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9722"/>
        <source>Fee (paid by this wallet)</source>
        <translation>Χρέωση (που καταβάλλεται από αυτό το πορτοφόλι)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9723"/>
        <source>Wallet Balance</source>
        <translation>Υπόλοιπο Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9723"/>
        <source>Total Balance</source>
        <translation>Συνολικό Υπόλοιπο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9723"/>
        <source>Label</source>
        <translation>Ετικέτα</translation>
    </message>
</context>
<context>
    <name>DlgFactoryReset</name>
    <message>
        <location filename="qtdialogs.py" line="14579"/>
        <source>
         &lt;b&gt;&lt;u&gt;Armory Factory Reset&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         It is &lt;i&gt;strongly&lt;/i&gt; recommended that you make backups of your
         wallets before continuing, though &lt;b&gt;wallet files will never be
         intentionally deleted!&lt;/b&gt;  All Armory
         wallet files, and the wallet.dat file used by Bitcoin Core/bitcoind
         should remain untouched in their current locations.  All Armory
         wallets will automatically be detected and loaded after the reset.
         &lt;br&gt;&lt;br&gt;
         If you are not sure which option to pick, try the &quot;lightest option&quot;
         first, and see if your problems are resolved before trying the more
         extreme options.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14597"/>
        <source>
         &lt;b&gt;Delete settings and rescan (lightest option)&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Διαγραφή ρυθμίσεων και επαναληψη σάρωσης (ελαφρύτερη επιλογή) &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14599"/>
        <source>
         Only delete the settings file and transient network data.  The
         databases built by Armory will be rescanned (about 5-45 minutes)</source>
        <translation>
Διαγράψετε μόνο το αρχείο ρυθμίσεων και των δεδομένων παροδικού δικτύου. Οι
βάσεις δεδομένων που χτίστηκαν από το Armory θα επανασαρωθούν (περίπου 5-45 λεπτά)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14604"/>
        <source>
         &lt;b&gt;Also delete databases and rebuild&lt;/b&gt;</source>
        <translation>
 &lt;b&gt;Επίσης διαγράψτε τις βάσεις και κάντε αναδόμηση&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14606"/>
        <source>
         Will delete settings, network data, and delete Armory's databases. The databases
         will be rebuilt and rescanned (45 min to 3 hours)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14611"/>
        <source>
         &lt;b&gt;Also re-download the blockchain (extreme)&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14613"/>
        <source>
         This will delete settings, network data, Armory's databases,
         &lt;b&gt;and&lt;/b&gt; Bitcoin Core's databases.  Bitcoin Core will
         have to download the blockchain again. This can take 8-72 hours depending on your 
         system's speed and connection.  Only use this if you
         suspect blockchain corruption, such as receiving StdOut/StdErr errors
         on the dashboard.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14622"/>
        <source>Do not delete settings files</source>
        <translation>Μην διαγράφετε τα αρχεία ρυθμίσεων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14653"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14654"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14668"/>
        <source>Factory Reset</source>
        <translation>Επαναφορά στις Εργοστασιακές Ρυθμίσεις</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14727"/>
        <source>Confirmation</source>
        <translation>Επιβεβαίωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14678"/>
        <source>
            You are about to delete your settings and force Armory to rescan
            its databases.  Are you sure you want to do this?</source>
        <translation>
Πρόκειται να διαγράψετε τις ρυθμίσεις σας και να αναγκάσετε το Armory να σαρώσει πάλι
τις βάσεις δεδομένων του. Είστε σίγουροι ότι θέλετε να το κάνετε αυτό;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14693"/>
        <source>
            You are about to delete your settings and force Armory to delete
            and rebuild its databases.  Are you sure you want to do this?</source>
        <translation>
Πρόκειται να διαγράψετε τις ρυθμίσεις σας και να αναγκάσετε το Armory να διαγράψει και να ανακατασκευάσει πάλι τις βάσεις δεδομένων του. Είστε σίγουροι ότι θέλετε να το κάνετε αυτό;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14711"/>
        <source>
               You are about to delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload of blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14719"/>
        <source>
               You are about to delete your settings and delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload of blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14765"/>
        <source>Aborted</source>
        <translation>Ακυρώθηκε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14765"/>
        <source>
                  You canceled the factory reset operation.  No changes were
                  made.</source>
        <translation>
Ακυρώσατε τη λειτουργία επαναφορά των εργοστασιακών ρυθμίσεων. Δεν υπάρχουν 
αλλαγές που έγιναν.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14781"/>
        <source>Restart Armory</source>
        <translation>Επανεκκίνηση του Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14740"/>
        <source>
               &lt;b&gt;Bitcoin Core (or bitcoind) must be closed to do the reset!&lt;/b&gt;
               Please close all Bitcoin software, &lt;u&gt;&lt;b&gt;right now&lt;/b&gt;&lt;/u&gt;,
               before clicking &quot;Continue&quot;.
               &lt;br&gt;&lt;br&gt;
               Armory will now close.  Please restart Bitcoin Core/bitcoind
               first and wait for it to finish synchronizing before restarting
               Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14750"/>
        <source>
                  You canceled the factory-reset operation.  No changes were
                  made.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14759"/>
        <source>
               Armory will now close to apply the requested changes.  Please
               restart it when you are ready to start the blockchain download
               again.</source>
        <translation>
Το Armory τώρα θα κλείσει για να εφαρμόσει τις αιτούμενες τροποποιήσεις. Παρακαλώ 
κάντε επανεκκίνηση όταν είστε έτοιμοι να ξεκινήσετε την λήψη της αλυσίδας
ξανά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14781"/>
        <source>
         Armory will now close so that the requested changes can
         be applied.</source>
        <translation>
Το Armory τώρα θα κλείσει για να εφαρμόσει τις
αιτούμενες τροποποιήσεις.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14711"/>
        <source>
               You are about to delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload all of the blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14719"/>
        <source>
               You are about to delete your settings and delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload all of the blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgForkedImports</name>
    <message>
        <location filename="qtdialogs.py" line="14792"/>
        <source>&lt;h2 style=&quot;color: red; text-align: center;&quot;&gt;Forked imported addresses have been       detected in your wallets!!!&lt;/h2&gt;</source>
        <translation>&lt;h2 style=&quot;color: red; text-align: center;&quot;&gt;Διαχαλωτές εισαγώμενες διευθύνσεις έχουν ανιχνευθεί στο πορτοφόλι σας!!!&lt;/h2&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14795"/>
        <source>The following wallets have forked imported addresses: &lt;br&gt;&lt;br&gt;&lt;b&gt;</source>
        <translation>Τα ακόλουθα πορτοφόλια έχουν διχαλωτές διευθύνσεις εισαγωγής: &lt;br&gt;&lt;br&gt;&lt;b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14798"/>
        <source>When you fix a corrupted wallet, any damaged private keys will be off       the deterministic chain. It means these private keys cannot be recreated       by your paper backup. If such private keys are encountered, Armory saves       them as forked imported private keys after it fixes the relevant wallets.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14803"/>
        <source>&lt;h1 style=&quot;color: orange;&quot;&gt; - Do not accept payments to these wallets anymore&lt;br&gt;      - Do not delete or overwrite these wallets. &lt;br&gt;       - Transfer all funds to a fresh and backed up wallet&lt;h1&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14839"/>
        <source>Forked Imported Addresses</source>
        <translation>Διχαλωτές Εισηγμένες Διευθύνσεις</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14803"/>
        <source>&lt;h1 style=&quot;color: orange;&quot;&gt; - Do not accept payments to these wallets anymore&lt;br&gt;      - Do not delete or overwrite these wallets. &lt;br&gt;       - Transfer all funds to a fresh and backed up wallet&lt;/h1&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgFragBackup</name>
    <message>
        <location filename="qtdialogs.py" line="11637"/>
        <source>
         &lt;b&gt;&lt;u&gt;Create M-of-N Fragmented Backup&lt;/u&gt; of &quot;%1&quot; (%2)&lt;/b&gt;</source>
        <translation>
 &lt;b&gt;&lt;u&gt;Δημιουργία ενός M-απο-N Κατακερματισμένο Αντίγραφο Ασφαλείας&lt;/u&gt; of &quot;%1&quot; (%2)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11676"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11693"/>
        <source> Use SecurePrintâ¢
         to prevent exposing keys to printer or other devices</source>
        <translation>Κάντε χρήση του SecurePrintâ¢
για να αποφύγετε την έκθεση των κλειδιών σας σε εκτυπωτές και άλλες συσκευές</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11700"/>
        <source>
         SecurePrintâ¢ encrypts your backup with a code displayed on
         the screen, so that no other devices or processes has access to the
         unencrypted private keys (either network devices when printing, or
         other applications if you save a fragment to disk or USB device).
         &lt;u&gt;You must keep the SecurePrintâ¢ code with the backup!&lt;/u&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11706"/>
        <source>
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;  You must keep the
         SecurePrintâ¢ encryption code with your backup!
         Your SecurePrintâ¢ code is &lt;/font&gt;
         &lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;&lt;font color=&quot;%4&quot;&gt;.
         All fragments for a given wallet use the
         same code.&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11766"/>
        <source>&lt;u&gt;&lt;b&gt;Required Fragments&lt;/b&gt;&lt;/u&gt; </source>
        <translation>&lt;u&gt;&lt;b&gt;Απαιτούμενα θραύσματα&lt;/b&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11767"/>
        <source>&lt;u&gt;&lt;b&gt;Total Fragments&lt;/b&gt;&lt;/u&gt; </source>
        <translation>&lt;u&gt;&lt;b&gt;Συνολικά Θραύσματα&lt;/b&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11771"/>
        <source>Print All Fragments</source>
        <translation>Εκτυπώστε όλα τα θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11798"/>
        <source>
         Any &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; of these
             &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt;
         fragments are sufficient to restore your wallet, and each fragment
         has the ID, &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt;.  All fragments with the
         same fragment ID are compatible with each other!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11813"/>
        <source>&lt;b&gt;Fragment ID:&lt;br&gt;%1-%2&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ταυτότητα Θράυσματος:&lt;br&gt;%1-%2&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11845"/>
        <source>View/Print</source>
        <translation>Προβολή / Εκτύπωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11846"/>
        <source>Save to File</source>
        <translation>Αποθήκευση σε Αρχείο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11880"/>
        <source>Fragments</source>
        <translation>Θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11890"/>
        <source>Secure Backup?</source>
        <translation>Ασφαλές Αντίγραφο Ασφαλείας;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11890"/>
        <source>
            You have selected to use SecurePrintâ¢ for the printed
            backups, which can also be applied to fragments saved to file.
            Doing so will require you store the SecurePrintâ¢
            code with the backup, but it will prevent unencrypted key data from
            touching any disks.  &lt;br&gt;&lt;br&gt; Do you want to encrypt the fragment
            file with the same SecurePrintâ¢ code?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11916"/>
        <source>Save Fragment</source>
        <translation>Αποθήκευση Θραύσματος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11916"/>
        <source>Wallet Fragments (*.frag)</source>
        <translation>Θραύσματα Πορτοφολιού (* .frag)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11951"/>
        <source>
         The fragment was successfully saved to the following location:
         &lt;br&gt;&lt;br&gt; %1 &lt;br&gt;&lt;br&gt; </source>
        <translation>
Το θράυσμα αποθηκεύτηκε στην ακόλουθη θέση:
&lt;br&gt;&lt;br&gt; %1 &lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11956"/>
        <source>
            &lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot;&gt;Important&lt;/font&lt;/u&gt;&lt;/b&gt;:
            The fragment was encrypted with the
            SecurePrintâ¢ encryption code.  You must keep this
            code with the backup in order to use it!  The code &lt;u&gt;is&lt;/u&gt;
            case-sensitive!
            &lt;br&gt;&lt;br&gt; &lt;font color=&quot;%2&quot; size=5&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt;
            &lt;br&gt;&lt;br&gt;
            The above code &lt;u&gt;&lt;b&gt;is&lt;/b&gt;&lt;/u&gt; case-sensitive!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11966"/>
        <source>Success</source>
        <translation>Επιτυχία</translation>
    </message>
</context>
<context>
    <name>DlgFundLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1847"/>
        <source>
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1853"/>
        <source>
         I am creating a new proposed spending transaction and will pass
         it to each party or device that needs to sign it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1857"/>
        <source>
         Another party or device created the transaction, I just need 
         to review and sign it.</source>
        <translation>
Ένα άλλο μέρος ή συσκευή δημιούργησε τη συναλλαγή, απλά πρέπει
να επανεξετάστει και να υπογραφεί.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1861"/>
        <source>Create Transaction</source>
        <translation>Δημιουργία Συναλλαγής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1862"/>
        <source>Review and Sign</source>
        <translation>Επανεξέταση και Υπογραφή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1863"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
</context>
<context>
    <name>DlgGenericGetPassword</name>
    <message>
        <location filename="qtdialogs.py" line="387"/>
        <source>Password:</source>
        <translation>Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="393"/>
        <source>OK</source>
        <translation>Εντάξει</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="394"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="408"/>
        <source>Enter Password</source>
        <translation>Εισαγωγή Κωδικού</translation>
    </message>
</context>
<context>
    <name>DlgHelpAbout</name>
    <message>
        <location filename="qtdialogs.py" line="8678"/>
        <source>Armory Bitcoin Wallet : Version %1-beta-%2</source>
        <translation>Armory Bitcoin Wallet : Έκδοση %1-βήτα-%2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8681"/>
        <source>Copyright &amp;copy; 2011-2015 Armory Technologies, Inc.</source>
        <translation>Πνευματική ιδιοκτησία &amp;copy; 2011-2015 Armory Technologies, Inc.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8682"/>
        <source>Copyright &amp;copy; 2016 Goatpig</source>
        <translation>Πνευματική ιδιοκτησία &amp;copy; 2016 Goatpig</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8683"/>
        <source>Licensed to Armory Technologies, Inc. under the &lt;a href=&quot;http://www.gnu.org/licenses/agpl-3.0.html&quot;&gt;Affero General Public License, Version 3&lt;/a&gt; (AGPLv3)</source>
        <translation>Σε άδεια προς το Armory Technologies, Inc. υπό τους όρους του &lt;a href=&quot;http://www.gnu.org/licenses/agpl-3.0.html&quot;&gt;Affero General Public License, Version 3&lt;/a&gt; (AGPLv3)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8687"/>
        <source>Licensed to Goatpig under the &lt;a href=&quot;https://opensource.org/licenses/mit-license.php&quot;&gt;MIT License</source>
        <translation>Σε άδεια προς τον Goatpig υπό τους όρους της άδειας του &lt;a href=&quot;https://opensource.org/licenses/mit-license.php&quot;&gt;MIT</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8705"/>
        <source>About Armory</source>
        <translation>Σχετικά με το Armory</translation>
    </message>
</context>
<context>
    <name>DlgImportAddress</name>
    <message>
        <location filename="qtdialogs.py" line="2845"/>
        <source>Enter:</source>
        <translation>Εισαγωγή:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2847"/>
        <source>One Key</source>
        <translation>Ένα Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2848"/>
        <source>Multiple Keys</source>
        <translation>Πολλαπλά Κλειδιά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2862"/>
        <source>The key can either be imported into your wallet, 
                     or have its available balance &quot;swept&quot; to another address 
                     in your wallet.  Only import private 
                     key data if you are absolutely sure that no one else 
                     has access to it.  Otherwise, sweep it to get 
                     the funds out of it.  All standard private-key formats 
                     are supported &lt;i&gt;except for private keys created by 
                     Bitcoin Core version 0.6.0 and later (compressed)&lt;/i&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2874"/>
        <source>
                       Supported formats are any hexadecimal or Base58 
                       representation of a 32-byte private key (with or 
                       without checksums), and mini-private-key format 
                       used on Casascius physical bitcoins.  Private keys 
                       that use &lt;i&gt;compressed&lt;/i&gt; public keys are not yet 
                       supported by Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2889"/>
        <source>
                   Enter a list of private keys to be &quot;swept&quot; or imported. 
                   All standard private-key formats are supported.  </source>
        <translation>
Πληκτρολογήστε μια λίστα με τα ιδιωτικά κλειδιά που πρέπει να &quot;σάρωσετε&quot; ή να εισάγετε
Υποστηρίζονται όλες τα τυποποιημένα ιδιωτικά κλειδιά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2894"/>
        <source>
                  One private key per line, in any standard format. 
                  Data may be copied directly from the &quot;Export Key Lists&quot; 
                  dialog (all text on a line preceding 
                  the key data, separated by a colon, will be ignored).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2909"/>
        <source>
         This is from a backup with SecurePrintâ¢</source>
        <translation>
Αυτό είναι από ένα αντίγραφο ασφαλείας με SecurePrintâ¢</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2930"/>
        <source>Sweep any funds owned by these addresses 
                                      into your wallet

                                      Select this option if someone else gave you this key</source>
        <translation>Σαρώστε οποιαδήποτε κεφάλαια ανήκουν σε αυτές τις διευθύνσεις
στο πορτοφόλι σας

Επιλέξτε αυτήν την επιλογή αν κάποιος άλλος σας έδωσε αυτό το κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2933"/>
        <source>Import these addresses to your wallet

                                      Only select this option if you are positive 
                                      that no one else has access to this key</source>
        <translation>Εισαγάγετε αυτές τις διευθύνσεις στο πορτοφόλι σας

αυτή την επιλογή μόνο αν είστε θετικοί
ότι κανένας άλλος δεν έχει πρόσβαση σε αυτό το κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2940"/>
        <source>Sweep any funds owned by this address
                                         into your wallet

                                         Select this option if someone else gave you this key</source>
        <translation>Σαρώστε οποιαδήποτε κεφάλαια ανήκουν σε αυτή την διεύθυνση
στο πορτοφόλι σας

Επιλέξτε αυτήν την επιλογή αν κάποιος άλλος σας έδωσε αυτό το κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2948"/>
        <source>Sweep any funds owned by this address
                                            into your wallet

                                            (Not available in offline mode)</source>
        <translation>Σαρώστε οποιαδήποτε κεφάλαια ανήκουν σε αυτή την διεύθυνση
στο πορτοφόλι σας

(Δεν είναι διαθέσιμο σε λειτουργία εκτός σύνδεσης)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2952"/>
        <source>
               Sweep any funds owned by this address into your wallet</source>
        <translation>
Σαρώστε οποιαδήποτε κεφάλαια ανήκουν σε αυτή την διεύθυνση
στο πορτοφόλι σας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2958"/>
        <source>
         You should never add an untrusted key to your wallet.  By choosing this
         option, you are only moving the funds into your wallet, but not the key
         itself.  You should use this option for Casascius physical bitcoins.</source>
        <translation>
Δεν πρέπει ποτέ να προσθέσετε ένα μη έμπιστο κλειδί στο πορτοφόλι σας. Επιλέγοντας 
αυτή την επιλογή, θα μετακινήσετε μόνο τα χρήματα στο πορτοφόλι σας, αλλά όχι το ίδιο το κλειδί.
Θα πρέπει να χρησιμοποιήσετε αυτήν την επιλογή για τα Casascius bitcoin.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2963"/>
        <source>
         This option will make the key part of your wallet, meaning that it
         can be used to securely receive future payments.  &lt;b&gt;Never&lt;/b&gt; select this
         option for private keys that other people may have access to.</source>
        <translation>
Αυτή η επιλογή θα κάνει το βασικό μέρος του πορτοφολιού σας, πράγμα που σημαίνει ότι αυτό
μπορεί να χρησιμοποιηθεί για να λάβετε με ασφάλεια μελλοντικές πληρωμές. &lt;b&gt;Ποτέ&lt;/b&gt;
μην επιλέξτε αυτή
την επιλογή για τα ιδιωτικά κλειδιά που άλλοι άνθρωποι μπορούν να έχουν πρόσβαση.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3002"/>
        <source>Private Key Import</source>
        <translation>Εισαγωγή Ιδιωτικού Κλειδιού!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3059"/>
        <source>Invalid Private Key</source>
        <translation>Λάθος Ιδιωτικό Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3052"/>
        <source>
               You entered all zeros.  This is not a valid private key!</source>
        <translation>
Βάλατε μόνο μηδενικά. Αυτό δεν είναι ένα σωστό ιδιωτικό κλειδί!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3059"/>
        <source>The private key you have entered is actually not valid for the elliptic curve used by Bitcoin (secp256k1). Almost any 64-character hex is a valid private key &lt;b&gt;except&lt;/b&gt; for those greater than: &lt;br&gt;&lt;br&gt;fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141&lt;br&gt;&lt;br&gt;Please try a different private key.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3075"/>
        <source>Entry Error</source>
        <translation>Σφάλμα Εισαγωγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3075"/>
        <source>
            The private key data you supplied appears to
            contain a consistency check.  This consistency
            check failed.  Please verify you entered the
            key data correctly.</source>
        <translation>
Το ιδιωτικό κλειδί δεδομένων που παρέχετε φαίνεται οτι
περιέχει έναν έλεγχο συνέπειας. Αυτός ο έλεγχος συνέπειας
απέτυχε. Παρακαλούμε επιβεβαιώστε οτι έχετε εισαγάγει τα
βασικά δεδομένα σωστά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3083"/>
        <source>Invalid Data</source>
        <translation>Λάθος Δεδομένα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3083"/>
        <source>Something went terribly
            wrong!  (key data unrecognized)</source>
        <translation>Κάτι πήγε τελείως
στραβά! (δεδομένα κλειδιού μη αναγνωρισμένα)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3088"/>
        <source>Unsupported key type</source>
        <translation>Μη υποστηριζόμενος τύπος κλειδιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3088"/>
        <source>You entered a key
            for an address that uses a compressed public key, usually produced
            in Bitcoin Core/bitcoind wallets created after version 0.6.0.  Armory
            does not yet support this key type.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3095"/>
        <source>Error Processing Key</source>
        <translation>Σφάλμα κατά την Επεξεργασία Κλειδιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3095"/>
        <source>
            There was an error processing the private key data.
            Please check that you entered it correctly</source>
        <translation>
Υπήρξε ένα σφάλμα κατά την επεξεργασία του ιδιωτικού κλειδιού δεδομένων.
Παρακαλώ ελέγξτε ότι το έχετε εισαγάγει σωστά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3104"/>
        <source>Verify Address</source>
        <translation>Πιστοποίηση Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3104"/>
        <source>
               The key data you entered appears to correspond to
               the following Bitcoin address:

<byte value="x9"/>' %1
               

Is this the correct address?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3116"/>
        <source>Try Again</source>
        <translation>Δοκιμάστε Ξανά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3116"/>
        <source>
                     It is possible that the key was supplied in a
                     &quot;reversed&quot; form.  When the data you provide is
                     reversed, the following address is obtained:

<byte value="x9"/>
                     %1 

Is this the correct address?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3180"/>
        <source>The key you entered is already part of another wallet you own:&lt;br&gt;&lt;br&gt;&lt;b&gt;Address&lt;/b&gt;: </source>
        <translation>Το κλειδί που έχετε εισάγει είναι ήδη μέρος ενός άλλου πορτοφολιού που σας ανήκει:&lt;br&gt;&lt;br&gt;&lt;b&gt;Address&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3278"/>
        <source>Duplicate Addresses!</source>
        <translation>Διπλές Διευθύνσεις</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3278"/>
        <source>You are attempting to sweep %1 addresses, but %2 of them are already part of existing wallets.  That means that some or all of the bitcoins you sweep may already be owned by you. &lt;br&gt;&lt;br&gt;Would you like to continue anyway?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3326"/>
        <source>Unlock Wallet to Import</source>
        <translation>Ξεκλείδωμα Πορτοφολιού για Εισαγωγή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3328"/>
        <source>Wallet is Locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3328"/>
        <source>
                  Cannot import private keys without unlocking wallet!</source>
        <translation>
Δεν είναι δυνατή η εισαγωγή των ιδιωτικών κλειδιών χωρίς να ξεκλειδώσετε το πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3357"/>
        <source>Nothing Imported!</source>
        <translation>Τίποτα δεν Εισήχθη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3357"/>
        <source>All addresses
               chosen to be imported are already part of this wallet.
               Nothing was imported.</source>
        <translation>Όλες οι διευθύνσεις που
επιλεχθηκαν για να εισαχθούν είναι ήδη μέρος αυτού του πορτοφολιού.
Τίποτα δεν έχει εισαχθεί.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3362"/>
        <source>Error!</source>
        <translation>Σφάλμα!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3362"/>
        <source>
               Failed:  No addresses could be imported.
               Please check the logfile (ArmoryQt.exe.log) or the console output
               for information about why it failed. </source>
        <translation>
Αποτυχία: Οι διευθύνσεις δεν μπορούσαν να εισαχθούν.
Παρακαλώ ελέγξτε το αρχείο καταγραφής (Armory Qt.exe.log) ή την έξοδο της κονσόλας
για πληροφορίες σχετικά με το γιατί απέτυχε.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3376"/>
        <source>Success!</source>
        <translation>Επιτυχία!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3370"/>
        <source>Success: %1 private keys were imported into your wallet. &lt;br&gt;&lt;br&gt;The other %2 private keys were skipped, because they were already part of your wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3376"/>
        <source>
                     Success: %1 private keys were imported into your wallet.</source>
        <translation>
Επιτυχία: %1 ιδιωτικά κλειδιά εισήχθησαν στο πορτοφόλι σας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3379"/>
        <source>Partial Success!</source>
        <translation>Μερική Επιτυχία!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3379"/>
        <source>
                  %1 private keys were imported into your wallet, but there were
                  also %2 addresses that could not be imported (see console
                  or log file for more information).  It is safe to try this
                  operation again: all addresses previously imported will be
                  skipped.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3104"/>
        <source>
               The key data you entered appears to correspond to
               the following Bitcoin address:

<byte value="x9"/> %1
               

Is this the correct address?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgImportAsciiBlock</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2094"/>
        <source>Load from file</source>
        <translation>Φόρτωση απο αρχείο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2095"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2096"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2117"/>
        <source>Load Data</source>
        <translation>Φόρτωση Δεδομένων</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2133"/>
        <source>Error</source>
        <translation>Σφάλμα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2133"/>
        <source>
            There was an error reading the ASCII block entered.  Please
            make sure it was entered/copied correctly, and that you have
            copied the header and footer lines that start with &quot;=====&quot;. </source>
        <translation>
Υπήρξε ένα σφάλμα κατά την ανάγνωση του μπλοκ ASCII. Παρακαλώ
βεβαιωθείτε ότι ενεγράφη/αντιγράφηκε σωστά, και ότι έχετε
αντιγράψει τις γραμμές κεφαλίδας και υποσέλιδου που ξεκινούν με &quot;=====&quot;.</translation>
    </message>
</context>
<context>
    <name>DlgImportLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2397"/>
        <source>
         &lt;b&gt;&lt;u&gt;Import Lockbox&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Copy the lockbox text block from file or email into the box 
         below.  If you have a file with the lockbox in it, you can
         load it using the &quot;Load Lockbox&quot; button at the bottom.</source>
        <translation>
&lt;b&gt;&lt;u&gt;Εισαγωγή Κουτιού&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Αντιγράψτε το κείμενο του κουτιού από το αρχείο ή απο το e-mail στο πλαίσιο
παρακάτω. Εάν έχετε ένα αρχείο με ένα κουτί ε αυτό, μπορείτε να λάβετε
το φορτίο αυτό, χρησιμοποιώντας το κουμπί &quot;Φόρτωση Κουτιού&quot; στο κάτω μέρος.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2408"/>
        <source>Load from file</source>
        <translation>Φόρτωση απο αρχείο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2409"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2410"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2426"/>
        <source>Import Lockbox</source>
        <translation>Εισάγετε το Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2432"/>
        <source>Load Lockbox</source>
        <translation>Φόρτωση του Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2449"/>
        <source>Non-lockbox</source>
        <translation>Όχι Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2449"/>
        <source>
               You are attempting to load something that is not a Lockbox.
               Please clear the display and try again.</source>
        <translation>
Προσπαθείτε να φορτώσετε κάτι που δεν είναι Κουτί.
Παρακαλείστε να καθαρίσετε την οθόνη και να δοκιμάσετε ξανά.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2455"/>
        <source>Duplicate Lockbox</source>
        <translation>Διπλό Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2455"/>
        <source>
               You just attempted to import a lockbox with ID, %1.  This
               lockbox is already in your available list of lockboxes.
               &lt;br&gt;&lt;br&gt;
               Even with the same ID, the lockbox information 
               may be different.  Would you like to overwrite the lockbox
               information already stored for %2?</source>
        <translation>
Προσπαθήσατε να εισάγετε ένα κουτί με Ταυτότητα, %1. Αυτό
το κουτί είναι ήδη διαθέσιμο στην λίστα των κουτιών.
&lt;br&gt;&lt;br&gt;
Ακόμη και με το ίδιο αναγνωριστικό, τα στοιχεία των κουτιών
μπορεί να είναι διαφορετικά. Θέλετε να αντικαταστήσετε το κουτί που είναι
ήδη αποθηκευμένες οι πληροφορίες για %2;</translation>
    </message>
</context>
<context>
    <name>DlgImportPaperWallet</name>
    <message>
        <location filename="qtdialogs.py" line="4129"/>
        <source>Root Key:</source>
        <translation>Κλειδί Root:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4131"/>
        <source>Chain Code:</source>
        <translation>Κωδικός Αλυσίδας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4134"/>
        <source>
          Enter the characters exactly as they are printed on the
          paper-backup page.  Alternatively, you can scan the QR
          code from another application, then copy&amp;paste into the
          entry boxes below.</source>
        <translation>
Πληκτρολογήστε τους χαρακτήρες όπως ακριβώς φαινονται στο
χαρτί αντιγράφων ασφαλείας. Εναλλακτικά, μπορείτε να σαρώσετε τον QR
κώδικα από μια άλλη εφαρμογή, και στη συνέχεια να αντιγράψετε και να επικολλήσετε στα κουτιά εισόδου παρακάτω.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4139"/>
        <source>
          The data can be entered &lt;i&gt;with&lt;/i&gt; or &lt;i&gt;without&lt;/i&gt;
          spaces, and up to
          one character per line will be corrected automatically.</source>
        <translation>
Τα δεδομένα μπορούν να εισαχθούν &lt;i&gt;με&lt;/i&gt; ή &lt;i&gt;χωρίς&lt;/i&gt;
κενά, και μέχρι
ένα χαρακτήρα ανα γραμμή θα διορθωθούν αυτόματα.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4154"/>
        <source>Encrypt Wallet</source>
        <translation>Κρυπτογράφηση Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4163"/>
        <source>Recover Wallet from Paper Backup</source>
        <translation>Ανάκτηση πορτοφολιού απο Χάρτινο Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4238"/>
        <source>Verify Wallet ID</source>
        <translation>Πιστοποίηση Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4194"/>
        <source>
               There is an error on line %1 of the data you
               entered, which could not be fixed automatically.  Please
               double-check that you entered the text exactly as it appears
               on the wallet-backup page.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4212"/>
        <source>Errors Corrected!</source>
        <translation>Τα Σφάλματα Διορθώθηκαν!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4229"/>
        <source>Duplicate Wallet!</source>
        <translation>Διπλό Πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4229"/>
        <source>
               The data you entered is for a wallet with a ID: 

 <byte value="x9"/> %1
               

You already own this wallet! 
  
               Nothing to do...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4238"/>
        <source>
               The data you entered corresponds to a wallet with a wallet ID: 

 <byte value="x9"/>
               %1 

Does this ID match the &quot;Wallet Unique ID&quot;
               printed on your paper backup?  If not, click &quot;No&quot; and reenter
               key and chain-code data again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4253"/>
        <source>Cannot Encrypt</source>
        <translation>Δεν μπορεί να Κρυπτογραφηθεί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4253"/>
        <source>
               You requested your restored wallet be encrypted, but no
               valid passphrase was supplied.  Aborting wallet recovery.</source>
        <translation>
Ζητήσατε το αποκατασταθέν πορτοφόλι να είναι κρυπτογραφημένο, αλλά δεν
δόθηκε έγκυρη φράση πρόσβασης. Ματαίωση της επαναφοράς του πορτοφολιού.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4271"/>
        <source>PaperBackup - %1</source>
        <translation>Χάρτινο Αντίγραφο Ασφαλείας - %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4280"/>
        <source>Computing New Addresses</source>
        <translation>Υπολογισμός Νέας Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4286"/>
        <source>Recovering wallet...</source>
        <translation>Ανακτώντας το πορτοφόλι ...</translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="4212"/>
        <source>
            Detected %n error(s) on line(s) %1
            in the data you entered.  Armory attempted to fix the
            error(s) but it is not always right.  Be sure
            to verify the &quot;Wallet Unique ID&quot; closely on the next window.</source>
        <translation type="unfinished"><numerusform></numerusform><numerusform></numerusform></translation>
    </message>
</context>
<context>
    <name>DlgInconsistentWltReport</name>
    <message>
        <location filename="qtdialogs.py" line="691"/>
        <source>Inconsistent Wallet!</source>
        <translation>Ασυνεπές Πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="691"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Important:&lt;/u&gt;  Wallet ConsistencyIssues Detected!&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;Armory now detects certain kinds of hardware errors, and oneor more of your walletswas flagged.  The consistency logs need to be analyzed by theArmory team to determine if any further action is required.&lt;br&gt;&lt;br&gt;&lt;b&gt;This warning will pop up every time you start Armory untilthe wallet is fixed&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="719"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot; size=4&gt;Submit Wallet Analysis Logs for
         Review&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;</source>
        <translation>
&lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot; size=4&gt;Υποβολή Ανάλυσης Πορτοφολιού για
Κριτική&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="724"/>
        <source>
         Armory has detected that %1 is finconsistent,
         possibly due to hardware errors out of our control.  It &lt;u&gt;strongly
         recommended&lt;/u&gt; you submit the wallet logs to the Armory developers
         for review.  Until you hear back from an Armory developer,
         it is recommended that you:
         &lt;ul&gt;
         &lt;li&gt;&lt;b&gt;Do not delete any data in your Armory home directory&lt;/b&gt;&lt;/li&gt;
         &lt;li&gt;&lt;b&gt;Do not send or receive any funds with the affected
                wallet(s)&lt;/b&gt;&lt;/li&gt;
         &lt;li&gt;&lt;b&gt;Create a backup of the wallet analysis logs&lt;/b&gt;&lt;/li&gt;
         &lt;/ul&gt;
         </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="738"/>
        <source>Save backup of log files</source>
        <translation>Αποθήκευση αντιγράφων ασφαλείας των αρχείων καταγραφής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="742"/>
        <source>Subject:</source>
        <translation>Θέμα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="753"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="777"/>
        <source>Inconsistent Wallet</source>
        <translation>Ασυνεπές Πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="992"/>
        <source>Not saved</source>
        <translation>Δεν αποθηκεύτηκε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="992"/>
        <source>
            You canceled the backup operation.  No backup was made.</source>
        <translation>
Ακυρώσατε τη λειτουργία δημιουργίας αντιγράφων ασφαλείας. Δεν ελήφθησαν αντίγραφα ασφαλείας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="999"/>
        <source>Success</source>
        <translation>Επιτυχία</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="999"/>
        <source>The wallet logs were successfully saved to the followinglocation:&lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt;It is still important to complete the rest of this formand submit the data to the Armory team for review!</source>
        <translation>Τα αρχεία καταγραφής του πορτοφολιού με επιτυχία αποθηκεύθηκαν στην ακόλουθη θέση:&lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt;Είναι σημαντικό να ολοκληρωθεί το υπόλοιπο αυτής της φόρμας και να υποβληθούν τα δεδομένα στην ομάδα του Armory για την αναθεώρηση!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1010"/>
        <source>Save Failed</source>
        <translation>Η Αποθήκευση Απέτυχε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1010"/>
        <source>There was an
            error saving a copy of your log files</source>
        <translation>Υπήρξε ένα σφάλμα
στην αποθήκευση των αρχείων καταγραφής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="724"/>
        <source>
         Armory has detected that %1 is inconsistent,
         possibly due to hardware errors out of our control.  It &lt;u&gt;strongly
         recommended&lt;/u&gt; you submit the wallet logs to the Armory developers
         for review.  Until you hear back from an Armory developer,
         it is recommended that you:
         &lt;ul&gt;
         &lt;li&gt;&lt;b&gt;Do not delete any data in your Armory home directory&lt;/b&gt;&lt;/li&gt;
         &lt;li&gt;&lt;b&gt;Do not send or receive any funds with the affected
                wallet(s)&lt;/b&gt;&lt;/li&gt;
         &lt;li&gt;&lt;b&gt;Create a backup of the wallet analysis logs&lt;/b&gt;&lt;/li&gt;
         &lt;/ul&gt;
         </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgInflatedQR</name>
    <message>
        <location filename="qtdefines.py" line="905"/>
        <source>&lt;b&gt;Double-click or press ESC to close&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgInstallLinux</name>
    <message>
        <location filename="qtdialogs.py" line="10622"/>
        <source>If you have manually installed Bitcoin Core or bitcoind on this system before, it is recommended you use the method here you previously used.  If you get errors using this option, try using the manual instructions below.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10627"/>
        <source>Install from bitcoin.org PPA (Ubuntu only)</source>
        <translation>Εγκατάσταση από το bitcoin.org PPA (για το Ubuntu μόνο)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10628"/>
        <source>Download and unpack binaries (All Linux)</source>
        <translation>Κατεβάστε και αποσυμπιέστε τα εκτελέσιμα (Για όλες τις εκδόσεις Linux)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10639"/>
        <source>&lt;b&gt;Install PPA for me (Ubuntu only):&lt;/b&gt;</source>
        <translation>&lt;b&gt;Εγκατάσταση απο το PPA για μένα (μόνο για Ubuntu):&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10640"/>
        <source>Have Armory install the PPA for you.  The does not work on all systems, so try the manual instructions below, if it fails.  Using the PPA will install the Bitcoin software using your system&apos;s package manager, and you will be notified of updates along with other software on your system.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10646"/>
        <source>Install Bitcoin PPA</source>
        <translation>Εγκατάσταση του Bitcoin PPA</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10648"/>
        <source>Click to install the Bitcoin PPA for Ubuntu</source>
        <translation>Κάντε κλικ για να εγκαταστήσετε το Bitcoin PPA για το Ubuntu</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10655"/>
        <source>&lt;b&gt;Manual PPA Installation:</source>
        <translation>&lt;b&gt;Χειροκίνητη εγκατάσταση του PPA:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10656"/>
        <source>Open a terminal window and copy the following three commands one-by-one, pressing [ENTER] after each one.  You can open a terminal by hitting Alt-F2 and typing &quot;terminal&quot; (without quotes), or in the &quot;Applications&quot; menu under &quot;Accessories&quot;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10687"/>
        <source>&lt;b&gt;Download and set it up for me!  (All Linux):&lt;/b&gt;&lt;br&gt;&lt;br&gt;Armory will download and verify the binaries from https://bitcoin.org.  Your Armory settings will automatically be adjusted to point to that as the installation directory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10693"/>
        <source>Install for me!</source>
        <translation>Εγκαταστήστε για μένα!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10695"/>
        <source>Select custom download location</source>
        <translation>Επιλέξτε προσαρμοσμένη τοποθεσία λήψης</translation>
    </message>
</context>
<context>
    <name>DlgIntroMessage</name>
    <message>
        <location filename="qtdialogs.py" line="4016"/>
        <source>&lt;b&gt;Welcome to Armory!&lt;/b&gt;</source>
        <translation>&lt;b&gt;Καλώς ήρθατε στο Armory!&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4019"/>
        <source>&lt;i&gt;The most advanced Bitcoin Client on Earth!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Τον πιο προηγμένο πελάτη Bitcoin στη Γη!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4022"/>
        <source>&lt;b&gt;You are about to use the most secure and feature-rich Bitcoin clientsoftware available!&lt;/b&gt;  But please remember, this softwareis still &lt;i&gt;Beta&lt;/i&gt; - Armory developers will not be held responsiblefor loss of bitcoins resulting from the use of this software!&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4037"/>
        <source>Do not show this window again</source>
        <translation>Να μήν εμφανίζεται το παράθυρο ξανά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4045"/>
        <source>Create Your First Wallet!</source>
        <translation>Δημιουργία του Πρώτου σας Πορτοφολιού!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4046"/>
        <source>Import Existing Wallet</source>
        <translation>Εισαγωγή Υπάρχοντος Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4047"/>
        <source>Skip</source>
        <translation>Παράλειψη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4061"/>
        <source>OK!</source>
        <translation>Εντάξει!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4076"/>
        <source>Greetings!</source>
        <translation>Χαιρετίσματα!</translation>
    </message>
</context>
<context>
    <name>DlgKeypoolSettings</name>
    <message>
        <location filename="qtdialogs.py" line="2516"/>
        <source>Armory pre-computes a pool of addresses beyond the last address you have used, and keeps them in your wallet to &quot;look-ahead.&quot;  One reason it does this is in case you have restored this wallet from a backup, and Armory does not know how many addresses you have actually used. &lt;br&gt;&lt;br&gt;If this wallet was restored from a backup and was very active after it was backed up, then it is possible Armory did not pre-compute enough addresses to find your entire balance.  &lt;b&gt;This condition is rare&lt;/b&gt;, but it can happen.  You may extend the keypool manually, below.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2529"/>
        <source>Addresses used: </source>
        <translation>Διευθύνσεις που χρησιμοποιήθηκαν:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2530"/>
        <source>Addresses computed: </source>
        <translation>Διευθύνσεις που υπολογίστηκαν:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2534"/>
        <source>Compute this many more addresses: </source>
        <translation>Υπολογισμός τόσων νέων διευθύνσεων:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2539"/>
        <source>Address computation is very slow.  It may take up to one minute to compute 200-1000 addresses (system-dependent).  Only generate as many as you think you need.</source>
        <translation>Ο υπολογισμός διεύθυνσης είναι πολύ αργός. Μπορεί να χρειαστεί έως και ένα λεπτό για να υπολογίσει 200-1000 διευθύνσεις (εξαρτάται από το σύστημα). Παράξτε μόνο όσες νομίζετε ότι χρειάζεστε.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2546"/>
        <source>Compute</source>
        <translation>Υπολογισμός</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2547"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2571"/>
        <source>Extend Address Pool</source>
        <translation>Επεκτείνετε την Πισίνα Διευθύνσεων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2590"/>
        <source>Invalid input</source>
        <translation>Λάθος Είσοδος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2590"/>
        <source>
            The value you entered is invalid.  Please enter a positive 
            number of addresses to generate.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2596"/>
        <source>Are you sure?</source>
        <translation>Είστε σίγουρος;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2596"/>
        <source>You have entered that you want to compute %1 more addressesfor this wallet.  This operation will take a very long time, and Armory will become unresponsive until the computation is finished.  Armory estimates it will take about %2 minutes.&lt;br&gt;&lt;br&gt;Do you want to continue?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2608"/>
        <source>&lt;font color=&quot;%1&quot;&gt;Calculating...&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;%1&quot;&gt;Υπολογισμός...&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2613"/>
        <source>Computing New Addresses</source>
        <translation>Υπολογισμός Νέας Διεύθυνσης</translation>
    </message>
</context>
<context>
    <name>DlgLockboxEditor</name>
    <message>
        <location filename="MultiSigDialogs.py" line="35"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font size=5 color=&quot;%1&quot;&gt;Create Multi-signature Lockbox&lt;/font&gt;&lt;/u&gt;
         </source>
        <translation>
&lt;b&gt;&lt;u&gt;&lt;font size=5 color=&quot;%1&quot;&gt;Δημιουργία Κουτιού Πολλαπλών-υπογραφών&lt;/font&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="39"/>
        <source>
         Create a &quot;lockbox&quot; to hold coins that have signing authority split 
         between multiple devices for personal funds, or split between 
         multiple parties for escrow.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="44"/>
        <source>
         &lt;b&gt;&lt;u&gt;NOTE:&lt;/u&gt; Multi-sig &quot;lockboxes&quot; require &lt;u&gt;public keys&lt;/u&gt;, not 
         the address strings most Bitcoin users are familiar with.&lt;/b&gt;
         &lt;a href=&quot;None&quot;&gt;Click for more info&lt;/a&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="50"/>
        <source>Public Key Information</source>
        <translation>Πληροφορίες Δημοσίου Κλειδιού</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="50"/>
        <source>
            A public key is much longer than an
            address string, and always starts with &quot;02&quot;, &quot;03&quot; or &quot;04&quot;. 
            Most wallet applications do not provide an easy way to access  
            a public key associated with a given address.  This is easiest
            if everyone is using Armory. 
            &lt;br&gt;&lt;br&gt;
            The address book buttons next to each input box below will show you 
            normal address strings, but will enter the correct public 
            key of the address you select.  
            &lt;br&gt;&lt;br&gt;
            If you are creating this lockbox with other
            Armory users, they can use the &quot;Select Public Key&quot; button
            from the Lockbox Manager dashboard to pick a key and enter
            their contact info.  You can use the &quot;Import&quot; button
            on each public key line to import the data they send you.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="112"/>
        <source>
            Public Key #&lt;font size=4 color=&quot;%1&quot;&gt;%2&lt;/font&gt;:</source>
        <translation>
Δημόσιο Κλειδί #&lt;font size=4 color=&quot;%1&quot;&gt;%2&lt;/font&gt;:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="114"/>
        <source>Name or ID:</source>
        <translation>Όνομα ή Ταυτότητα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="125"/>
        <source>Edit</source>
        <translation>Τροποποίηση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="126"/>
        <source>Import</source>
        <translation>Εισαγωγή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="164"/>
        <source>Exit</source>
        <translation>Έξοδος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="165"/>
        <source>Save Lockbox</source>
        <translation>Αποθήκευση του Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="177"/>
        <source>Set extended info</source>
        <translation>Ορισμός επιπλέον πληροφοριών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="236"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Create
         Multi-Sig Lockbox&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Δημιουργία
Κουτιού Πολλαπλών-υπογραφών&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="240"/>
        <source>&lt;b&gt;Required Signatures (M)&lt;/b&gt; </source>
        <translation>&lt;b&gt;Απαιτούμενες Υπογραφές (M)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="242"/>
        <source>&lt;b&gt;Total Signers (N)&lt;/b&gt; </source>
        <translation>&lt;b&gt;Συνολικοί Υπογράφοντες (N)&lt;/b&gt; </translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="245"/>
        <source> - OF - </source>
        <translation> - ΑΠΟ - </translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="248"/>
        <source>Clear All</source>
        <translation>Εκκαθάριση Όλων</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="303"/>
        <source>Import Public Key Block</source>
        <translation>Εισαγωγή Μπλόκ Δημοσίου Κλειδιού</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="304"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Import Public Key Block&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Copy and paste a PUBLICKEY block into the text field below, 
         or load it from file.  PUBLICKEY files usually have the 
         extension &lt;i&gt;*.lockbox.pub&lt;/i&gt;.  If you were given a chunk of hex
         characters starting with &quot;02&quot;, &quot;03&quot; or &quot;04&quot;, that is a raw public 
         key and can be entered directly into the public key field in the
         lockbox creation window.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgLockboxManager</name>
    <message>
        <location filename="MultiSigDialogs.py" line="652"/>
        <source>&lt;br&gt;Double-click on a lockbox to edit</source>
        <translation>&lt;br&gt;Πατήστε διπλό κλίκ στο κουτί για να το επεξεργαστείτε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="654"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Manage Multi-Sig Lockboxes&lt;/b&gt;&lt;/font&gt;
         %2</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Διαχείριση Κουτιών Πολλαπλών Υπογραφών&lt;/b&gt;&lt;/font&gt;
%2</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="699"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="765"/>
        <source>Dashboard</source>
        <translation>Πίνακας Ελέγχου</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="766"/>
        <source>Info</source>
        <translation>Πληροφορίες</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="767"/>
        <source>Transactions</source>
        <translation>Συναλλαγές</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="820"/>
        <source>Create Lockbox</source>
        <translation>Δημιουργία Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="823"/>
        <source>Collect public keys</source>
        <translation>Συλλογή δημοσίων κλειδιών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="824"/>
        <source>Create a lockbox by collecting public keys
                                from each device or person that will be 
                                a signing authority over the funds.  Once
                                created you will be given a chunk of text
                                to send to each party so they can recognize
                                and sign transactions related to the 
                                lockbox.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="835"/>
        <source>Select Public Key</source>
        <translation>Επιλογή Δημοσίου Κλειδιού</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="838"/>
        <source>Send to organizer</source>
        <translation>Αποστολή στον διοργανωτή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="839"/>
        <source>In order to create a lockbox all devices 
                                and/or parties need to provide a public key 
                                that they control to be merged by the 
                                organizer.  Once all keys are collected,
                                the organizer will send you the final
                                lockbox definition to import.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="849"/>
        <source>Export Lockbox</source>
        <translation>Εξαγωγή Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="852"/>
        <source>Send to other devices or parties</source>
        <translation>Αποστολή σε άλλες συσκευές ή μέλη</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="853"/>
        <source>Export a lockbox definition to be imported
                                by other devices or parties.  Normally the 
                                lockbox organizer will do this after all public
                                keys are collected, but any participant who 
                                already has it can send it, such as if one 
                                party/device accidentally deletes it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="859"/>
        <source>Select lockbox to export</source>
        <translation>Επιλογή του κουτιού για εξαγωγή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="863"/>
        <source>Import Lockbox</source>
        <translation>Εισαγωγή Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="866"/>
        <source>From organizer or other device</source>
        <translation>Απο τον οργανωτή σε άλλη συσκευή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="867"/>
        <source>Import a lockbox definition to begin
                                tracking its funds and to be able to
                                sign related transactions.
                                Normally, the organizer will send you 
                                the data to import after you
                                provide a public key from one of your
                                wallets.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="878"/>
        <source>Edit Lockbox</source>
        <translation>Επεξεργασία Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="882"/>
        <source>Edit an existing lockbox</source>
        <translation>Επεξεργασία υπάρχοντος κουτιού</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="883"/>
        <source>Select lockbox to edit</source>
        <translation>Επιλογή του κουτιού για επεξεργασία</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="910"/>
        <source>Merge Promissory Notes</source>
        <translation>Συγχώνευση Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="914"/>
        <source>Collect promissory notes from all funders
                                of a simulfunding transaction.  Use this to
                                merge them into a single transaction that 
                                the funders can review and sign.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="922"/>
        <source>Create Promissory Note</source>
        <translation>Δημιουργία Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="925"/>
        <source>Make a funding commitment to a lockbox</source>
        <translation>Κάντε μια δέσμευση χρηματοδότησης σε ένα κουτί κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="926"/>
        <source>A &quot;promissory note&quot; provides blockchain
                                information about how your wallet will 
                                contribute funds to a simulfunding transaction.
                                A promissory note does &lt;b&gt;not&lt;/b&gt;
                                move any money in your wallet.  The organizer
                                will create a single transaction that includes
                                all promissory notes and you will be able to 
                                review it in its entirety before signing.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="934"/>
        <source>Select lockbox to commit funds to</source>
        <translation>Επιλογή του κουτιού για την πίστωση των ποσών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="935"/>
        <source>Must be online to create</source>
        <translation>Πρέπει να είστε συνδεδεμένοι για να δημιουργηθεί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="938"/>
        <source>Review and Sign</source>
        <translation>Επανεξέταση και Υπογραφή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="941"/>
        <source>Multi-sig spend or simulfunding</source>
        <translation>Ξόδεμα πολλαπλής υπογραφής ή simulfunding</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="942"/>
        <source>Review and sign any lockbox-related
                                transaction that requires multiple 
                                signatures.  This includes spending 
                                transactions from a regular lockbox,
                                as well as completing a simulfunding
                                transaction.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="952"/>
        <source>Create Spending Tx</source>
        <translation>Δημιουργία Συναλλαγής για ξόδεμα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="955"/>
        <source>Send bitcoins from lockbox</source>
        <translation>Αποστολή Bitcoin απο το κουτί κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="956"/>
        <source>Create a proposed transaction sending bitcoins
                                to an address, wallet or another lockbox.  
                                The transaction will not be final until enough
                                signatures have been collected and then 
                                broadcast from an online computer.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="961"/>
        <source>Select lockbox to spend from</source>
        <translation>Επιλογή του κουτιού για ξόδεμα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="962"/>
        <source>Must be online to spend</source>
        <translation>Πρέπει να είστε συνδεδεμένοι για να ξοδέψετε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="966"/>
        <source>Collect Sigs &amp;&amp; Broadcast</source>
        <translation>Συλλογή Υπογραφών &amp;&amp; Μετάδοση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="969"/>
        <source>Merge signatures to finalize</source>
        <translation>Συγχώνευση υπογραφών για την οριστικοποίηση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="970"/>
        <source>Merge signatures and broadcast transaction</source>
        <translation>Συγχώνευση υπογραφών και μετάδοση συναλλαγών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="972"/>
        <source>(must be online to broadcast)</source>
        <translation>(πρέπει να είστε συνδεδεμένοι για να εκπεμφθεί)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="982"/>
        <source>SimulFund</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="986"/>
        <source>
         If this lockbox will be funded by multiple parties and not all
         parties are fully trusted, use &quot;simulfunding&quot; to ensure that funds 
         are committed at the same time.  Check the &quot;Simul&quot; box to show 
         simulfunding options in the table.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1133"/>
        <source>Fund from Wallet</source>
        <translation>Κεφάλαια από το Πορτοφόλι</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1134"/>
        <source>QR Code</source>
        <translation>Κώδικας QR </translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1135"/>
        <source>Request Payment</source>
        <translation>Ζητήστε Πληρωμή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1172"/>
        <source>Copy Address</source>
        <translation>Αντιγραφή Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1187"/>
        <source>
               Anyone can send funds to this lockbox using this
               Bitcoin address: &lt;br&gt;&lt;b&gt;%1&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1322"/>
        <source>Invalid Tx</source>
        <translation>Λάθος Συναλλαγή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1322"/>
        <source>The transaction you requested be displayed does not exist in Armory&apos;s database.  This is unusual...</source>
        <translation>Η συναλλαγή που ζητήσατε δεν υπάρχει στη βάση δεδομένων του Armory. Αυτό είναι ασυνήθιστο...</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1353"/>
        <source>View on blockexplorer.com</source>
        <translation>Δείτε το στο blockexplorer.com</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1356"/>
        <source>View on blockchain.info</source>
        <translation>Δείτε το στο blockchain.info</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1360"/>
        <source>View Details</source>
        <translation>Δείτε Λεπτομέρειες</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1362"/>
        <source>Change Comment</source>
        <translation>Αλλαγή Σχολίου</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1363"/>
        <source>Copy Transaction ID</source>
        <translation>Αντιγραφή Ταυτότητας Συναλλαγής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1435"/>
        <source>Could not open browser</source>
        <translation>Δεν μπορέσαμε να ανοίξουμε τον Φυλλομετρητή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1374"/>
        <source>Armory encountered an error opening your web browser.  To view this transaction on blockchain.info, please copy and paste the following URL into your browser: &lt;br&gt;&lt;br&gt;%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1396"/>
        <source>Copy P2SH address</source>
        <translation>Αντιγραφή Διεύθυνσης P2SH</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1397"/>
        <source>Display address QR code</source>
        <translation>Εμφάνιση του κωδικού QR της διεύθυνσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1399"/>
        <source>View address on %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1402"/>
        <source>Request payment to this lockbox</source>
        <translation>Ζητήστε πληρωμή σε αυτό το κουτί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1403"/>
        <source>Copy hash160 value (hex)</source>
        <translation>Αντιγραφή του Hash160 (hex)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1404"/>
        <source>Copy balance</source>
        <translation>Αντιγραφή υπολοίπου</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1405"/>
        <source>Delete Lockbox</source>
        <translation>Διαγραφή Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1407"/>
        <source>Rescan Lockbox</source>
        <translation>Επανασάρωση Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1435"/>
        <source>
                  Armory encountered an error opening your web browser.  To view 
                  this address on %1, please copy and paste
                  the following URL into your browser: 
                  &lt;br&gt;&lt;br&gt;
                  &lt;a href=&quot;%2&quot;&gt;%3&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1450"/>
        <source>Compatibility Warning</source>
        <translation>Προειδοποίηση Συμβατότητας</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1450"/>
        <source>You are about to request payment to a &quot;P2SH&quot; address
                  which is the format used for receiving to multi-signature
                  addresses/lockboxes.  &quot;P2SH&quot; are like regular Bitcoin 
                  addresses but start with %1 instead of %2.
                  &lt;br&gt;&lt;br&gt;
                  Unfortunately, not all software and services support sending 
                  to P2SH addresses.  If the sender or service indicates   
                  an error sending to this address, you might have to request
                  payment to a regular wallet address and then send the funds
                  from that wallet to the lockbox once it is confirmed.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1450"/>
        <source>Do not show this message again</source>
        <translation>Να μήν εμφανίζεται το μύνημα ξανά</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1713"/>
        <source>Confirm Delete</source>
        <translation>Επιβεβαίωση Διαγραφής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1474"/>
        <source>
               &quot;Removing&quot; a lockbox does not delete any signing keys, so you 
               maintain signing authority for any coins that are sent there.     
               However, it will remove it from the list of lockboxes, and you
               will have to re-import it later in order to send any funds
               to or from the lockbox.
               &lt;br&gt;&lt;br&gt;
               You are about to remove the following lockbox:
               &lt;br&gt;&lt;br&gt;
               &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1494"/>
        <source>Confirm Rescan</source>
        <translation>Επιβεβαίωση Επανασάρωσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1494"/>
        <source>
               Rescaning a Lockbox will make it unavailable for the duration
               of the process
               &lt;br&gt;&lt;br&gt;
               You are about to rescan the following lockbox:
               &lt;br&gt;&lt;br&gt;
               &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1534"/>
        <source> &lt;br&gt;&lt;br&gt;&lt;font color=&quot;%1&quot;&gt;&lt;center&gt;&lt;b&gt;
            Select a lockbox from the table above to view its info&lt;/b&gt;&lt;/center&gt;
            &lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1589"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;center&gt;&lt;u&gt;Lockbox Information for
         &lt;b&gt;%2&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1591"/>
        <source>&lt;b&gt;Multisig:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1-of-%2</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1592"/>
        <source>&lt;b&gt;Lockbox ID:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1593"/>
        <source>&lt;b&gt;P2SH Address:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1594"/>
        <source>&lt;b&gt;Lockbox Name:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1595"/>
        <source>&lt;b&gt;Created:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1596"/>
        <source>&lt;b&gt;Extended Info:&lt;/b&gt;&lt;hr&gt;&lt;blockquote&gt;%1&lt;/blockquote&gt;&lt;hr&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1597"/>
        <source>&lt;b&gt;Stored Key Details&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αποθηκευμένες Λεπτομέρειες Κλειδιού&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1607"/>
        <source>&amp;nbsp;&amp;nbsp;&lt;b&gt;Key #%1&lt;/b&gt;</source>
        <translation>&amp;nbsp;&amp;nbsp;&lt;b&gt;Κλειδί #%1&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1608"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Name/ID:&lt;/b&gt;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Όνομα/Ταυτότητα:&lt;/b&gt;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1609"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Address:&lt;/b&gt;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Διεύθυνση:&lt;/b&gt;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1610"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;PubKey:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Δημόσιο Κλειδί:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1612"/>
        <source>&lt;/font&gt;</source>
        <translation>&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1781"/>
        <source>Import Signature Collector</source>
        <translation>Εισαγωγή Συλλέκτη Υπογραφών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1692"/>
        <source>
         Import a &lt;i&gt;Signature Collector&lt;/i&gt; block to review and
         sign the lockbox-spend or simulfunding transaction.  This text block 
         is produced by the organizer and will contain
         &quot;=====TXSIGCOLLECT&quot; on the first line.   Or you can import it from
         a file, which is saved by default with a
         &lt;i&gt;*.sigcollect.tx&lt;/i&gt; extension.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1713"/>
        <source>
         &quot;Removing&quot; a lockbox does not delete any signing keys, so you 
         maintain signing authority for any coins that are sent there.     
         However, Armory will stop tracking its history and balance, and you
         will have to re-import it later in order to sign any transactions.
         &lt;br&gt;&lt;br&gt;
         You are about to remove the following lockbox:
         &lt;br&gt;&lt;br&gt;
         &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1736"/>
        <source>[WARNING]</source>
        <translation>[ΠΡΟΕΙΔΟΠΟΙΗΣΗ]</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1736"/>
        <source>
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;WARNING:&lt;/font&gt; &lt;/b&gt;
         If this lockbox is being used to hold escrow for multiple parties, and
         requires being funded by multiple participants, you &lt;u&gt;must&lt;/u&gt; use
         a special funding process to ensure simultaneous funding.  Otherwise,
         one of the other parties may be able to scam you!  
         &lt;br&gt;&lt;br&gt;
         It is safe to continue if any of the following conditions are true:
         &lt;ul&gt;
            &lt;li&gt;You are the only one expected to fund this lockbox/escrow&lt;/li&gt;
            &lt;li&gt;All other parties in the lockbox/escrow are fully trusted&lt;/li&gt;
            &lt;li&gt;This lockbox is being used for personal savings&lt;/li&gt;
         &lt;/ul&gt;
         If the above does not apply to you, please press &quot;Cancel&quot; and 
         select the &quot;Simul&quot; checkbox on the lockbox dashboard.
         </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1761"/>
        <source>Funding %1-of-%2</source>
        <translation>Χρηματοδότηση %1-of-%2</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1782"/>
        <source>
            Import a &lt;i&gt;Signature Collector&lt;/i&gt; text block to review and
            sign the simulfunding transaction.  This text block is produced
            by the party that collected and merged all the promissory notes.
            Files containing signature-collecting data usually end with
            &lt;i&gt;*.sigcollect.tx&lt;/i&gt;.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgMergePromNotes</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3505"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Merge Promissory Notes
         &lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Συγχώνευση Υποσχετικού Σημειώματος
&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3510"/>
        <source>
         Collect promissory notes from two or more parties
         to combine them into a single &lt;i&gt;simulfunding&lt;/i&gt; transaction.  Once
         all notes are collected you will be able to
         send it to each contributing party for review and signing.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3523"/>
        <source>Lockbox Being Funded</source>
        <translation>Το Κουτί Χρηματοδοτείται</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3526"/>
        <source>Address Being Funded</source>
        <translation>Η Διεύθυνση Χρηματοδοτείται</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3563"/>
        <source>Loaded Promissory Notes</source>
        <translation>Φόρτωση Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3564"/>
        <source>
         &lt;font size=4&gt;&lt;b&gt;No Promissory Notes Have Been Added&lt;/b&gt;&lt;/font&gt;</source>
        <translation> &lt;font size=4&gt;&lt;b&gt;Δεν Έχουν Προστεθεί Υποσχετικές Σημειώσεις&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3638"/>
        <source>Import Promissory Note</source>
        <translation>Εισαγωγή Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3587"/>
        <source>Create &amp;&amp; Add Promissory Note</source>
        <translation>Δημιουργία &amp;&amp; Εισαγωγή Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3592"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3593"/>
        <source>Use bare multisig (no P2SH)</source>
        <translation>Χρήση Σκέτης Πολλαπλής Υπογραφής (Χωρίς P2SH)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3594"/>
        <source>
         EXPERT OPTION:  Do not check this box unless you know what it means
                         and you need it!  Forces Armory to exposes public 
                         keys to the blockchain before the funds are spent.  
                         This is only needed for very specific use cases, 
                         and otherwise creates blockchain bloat.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3600"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3639"/>
        <source>
         Import a promissory note to add to this simulfunding transaction</source>
        <translation>
Χρήση υποσχετικού σημειώματος για την προσθήκη της συναλλαγής simulfunding</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3651"/>
        <source>Invalid Promissory Note</source>
        <translation>Λανθασμένο Γραμμάτιο Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3651"/>
        <source>
            No promissory note was loaded.</source>
        <translation>
Δεν φορτώθηκε γραμμάτιο υπόσχεσης.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3662"/>
        <source>Not Online</source>
        <translation>Αποσυνδεδεμένο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3662"/>
        <source>
            Armory is currently in offline mode and cannot create any 
            transactions or promissory notes.  You can only merge 
            pre-existing promissory notes at this time.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3690"/>
        <source>Already Loaded</source>
        <translation>Ήδη Φορτωμένο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3690"/>
        <source> This 
            promissory note has already been loaded!</source>
        <translation>Αυτό
το υποσχετικό σημείωμα έχει ήδη φορτωθεί!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3729"/>
        <source>Mismatched Funding Target</source>
        <translation>Ασυμφωνία Στόχου Χρηματοδότησης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3729"/>
        <source>
            The promissory note you loaded is for a different funding target. 
            Please make sure that all promissory notes are for the target
            specified on the previous window</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3771"/>
        <source>Nothing Loaded</source>
        <translation>Τίποτα Δεν Φορτώθηκε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3771"/>
        <source>
            No promissory notes were loaded.  Cannot create simulfunding 
            transaction.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3777"/>
        <source>Merging One Note</source>
        <translation>Συνχώνευση Μοναδικής Σημείωσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3777"/>
        <source>
            Only one promissory note was entered, so there
            is nothing to merge.  
            &lt;br&gt;&lt;br&gt;
            The simulfunding interface is intended to merge promissory notes
            from multiple parties to ensure simultaneous funding 
            for escrow.  If only person is funding, they 
            can simply send money to the address or lockbox like they would 
            any other transaction, without going through the simulfunding 
            interface.
            &lt;br&gt;&lt;br&gt;
            Click &quot;Ok&quot; to continue to the multi-signing interface, but there
            will only be one input to sign.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3823"/>
        <source>Export Simulfunding Transaction</source>
        <translation>Εξαγωγή  Simulfunding Συναλλαγής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3824"/>
        <source>
         The text block below contains the simulfunding transaction to be
         signed by all parties funding this lockbox.  Copy the text block
         into an email to all parties contributing funds.  Each party can
         review the final simulfunding transaction, add their signature(s),
         then send back to you to finalize it.  
         &lt;br&gt;&lt;br&gt;
         When you click &quot;Done&quot;, you will be taken to a window that you can
         use to merge the TXSIGCOLLECT blocks from all parties and broadcast
         the final transaction.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgMultiSpendReview</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2483"/>
        <source>
         The following transaction is a proposed spend of funds controlled
         by multiple parties.  The keyholes next to each input represent 
         required signatures for the tx to be valid.  White
         means it has not yet been signed, and cannot be signed by you.  Green
         represents signatures that can be added by one of your wallets.
         Gray keyholes are already signed.
         &lt;br&gt;&lt;br&gt;
         Change outputs have been hidden where it is obvious (such as coins
         returning to the same lockbox from where it came).  If there is 
         any ambiguity, Armory will display all outputs.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgNewAddressDisp</name>
    <message>
        <location filename="qtdialogs.py" line="2667"/>
        <source>The following address can be used to receive bitcoins:</source>
        <translation>Η ακόλουθη διεύθυνση μπορεί να χρησιμοποιηθεί για να λάβετε bitcoins:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2672"/>
        <source>Copy to Clipboard</source>
        <translation>Αντιγραφή στο Πρόχειρο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2674"/>
        <source> or </source>
        <translation>ή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2685"/>
        <source>Create Clickable Link</source>
        <translation>Δημιουργία Συνδέσμου Για Κλίκ</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2689"/>
        <source>
            You can securely use this address as many times as you want. 
            However, all people to whom you give this address will 
            be able to see the number and amount of bitcoins &lt;b&gt;ever&lt;/b&gt; 
            sent to it.  Therefore, using a new address for each transaction 
            improves overall privacy, but there is no security issues 
            with reusing any address.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2726"/>
        <source>(Optional) Add a label to this address, which will be shown with any relevant transactions in the &quot;Transactions&quot; tab.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2743"/>
        <source>Bitcoins sent to this address will 
            appear in the wallet:</source>
        <translation>Bitcoin που αποστέλλονται στη διεύθυνση αυτή θα
εμφανίζονται στο πορτοφόλι:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2757"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2769"/>
        <source>&lt;b&gt;Scan QR code with phone or other barcode reader&lt;/b&gt;&lt;br&gt;&lt;br&gt;&lt;font size=2&gt;(Double-click to expand)&lt;/font&gt;</source>
        <translation>&lt;b&gt;Κάντε σάρωση του κώδικα QR με το τηλέφωνο σας ή κάποια άλλη συσκευή ανάγνωσης barcode&lt;/b&gt;&lt;br&gt;&lt;br&gt;&lt;font size=2&gt;(Πατήστε διπλό-κλίκ για επέκταση)&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2806"/>
        <source>New Receiving Address</source>
        <translation>Νέα Διεύθυνση Παραλαβής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2834"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
</context>
<context>
    <name>DlgNewWallet</name>
    <message>
        <location filename="qtdialogs.py" line="1026"/>
        <source>
         Create a new wallet for managing your funds.&lt;br&gt;
         The name and description can be changed at any time.</source>
        <translation>
Δημιουργήστε ένα νέο πορτοφόλι για τη διαχείριση των χρημάτων σας.&lt;br&gt;
Το όνομα και η περιγραφή μπορεί να αλλάξει ανά πάσα στιγμή.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1050"/>
        <source>
                  Armory will test your system's speed to determine the most 
                  challenging encryption settings that can be performed '
                  in a given amount of time.  High settings make it much harder 
                  for someone to guess your passphrase.  This is used for all 
                  encrypted wallets, but the default parameters can be changed below.
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1058"/>
        <source>
                  This is the amount of time it will take for your computer 
                  to unlock your wallet after you enter your passphrase. 
                  (the actual time used will be less than the specified 
                  time, but more than one half of it).  </source>
        <translation>
Αυτό είναι το χρονικό διάστημα που θα χρειαστεί ώστε ο υπολογιστή σας
για να ξεκλειδώσει το πορτοφόλι σας, μετά που θα εισαγάγετε τη φράση πρόσβασης.
(Ο πραγματικός χρόνος που χρησιμοποιείται θα είναι μικρότερος από τον καθορισμένο
χρόνο, αλλά περισσότερο από το μισό από αυτό).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1070"/>
        <source>
                  This is the &lt;b&gt;maximum&lt;/b&gt; memory that will be 
                  used as part of the encryption process.  The actual value used 
                  may be lower, depending on your system's speed.  If a 
                  low value is chosen, Armory will compensate by chaining 
                  together more calculations to meet the target time.  High 
                  memory target will make GPU-acceleration useless for 
                  guessing your passphrase.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1085"/>
        <source>Max &amp;memory usage (kB, MB):</source>
        <translation>Μέγιστη χρήση &amp;memory μνήμης (kB, MB):</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1108"/>
        <source>Use wallet &amp;encryption</source>
        <translation>Χρήση &amp;κρυπτογράφησης πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1110"/>
        <source>
                  Encryption prevents anyone who accesses your computer 
                  or wallet file from being able to spend your money, as  
                  long as they do not have the passphrase.
                  You can choose to encrypt your wallet at a later time 
                  through the wallet properties dialog by double clicking 
                  the wallet on the dashboard.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1119"/>
        <source>Print a paper-backup of this wallet</source>
        <translation>Εκτύπωση ενός χάρτινου αντιγράφου ασφαλείας για το πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1121"/>
        <source>
                  A paper-backup allows you to recover your wallet/funds even 
                  if you lose your original wallet file, any time in the future. 
                  Because Armory uses &quot;deterministic wallets,&quot; 
                  a single backup when the wallet is first made is sufficient 
                  for all future transactions (except ones to imported 
                  addresses).


                  Anyone who gets ahold of your paper backup will be able to spend 
                  the money in your wallet, so please secure it appropriately.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1132"/>
        <source>Accept</source>
        <translation>Αποδοχή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1133"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1134"/>
        <source>Adv. Encrypt Options&gt;&gt;&gt;</source>
        <translation>Προχ. Επιλογές Κρυπτογράφησης&gt;&gt;&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1149"/>
        <source>Import wallet...</source>
        <translation>Εισαγωγή πορτοφολιού...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1177"/>
        <source>Create Armory wallet</source>
        <translation>Δημιουργία Πορτοφολιού Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1192"/>
        <source>Invalid wallet name</source>
        <translation>Λάθος όνομα πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1192"/>
        <source>You must enter a name for this wallet, up to 32 characters.</source>
        <translation>Πρέπει να εισάγετε ένα όνομα για αυτό το πορτοφόλι, έως 32 χαρακτήρες.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1198"/>
        <source>Input too long</source>
        <translation>Είσοδος πολύ μεγάλη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1198"/>
        <source>
                  The wallet description is limited to 256 characters.  Only the first 
                  256 characters will be used.</source>
        <translation>
Η περιγραφή του πορτοφολιού περιορίζεται σε 256 χαρακτήρες. Μόνο οι πρώτοι
256 χαρακτήρες θα χρησιμοποιηθούν.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1228"/>
        <source>Invalid KDF Parameters</source>
        <translation>Λάθος KDF Παράμετροι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1216"/>
        <source>
               Please specify a compute time no more than 20 seconds.  
               Values above one second are usually unnecessary.</source>
        <translation>
Παρακαλείστε να προσδιορίσετε μια φορά υπολογιστικό χρόνο όχι περισσότερο από 20 δευτερόλεπτα.
Τιμές πάνω από το ένα δευτερόλεπτο είναι συνήθως περιττές.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1228"/>
        <source>Please specify a maximum memory usage between 32 kB 
               and 2048 MB.</source>
        <translation>Παρακαλείστε να προσδιορίσετε μέγιστη χρήση μνήμης μεταξύ 32 kB 
και 2048 MB.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1235"/>
        <source>Invalid Input</source>
        <translation>Λάθος Είσοδος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1235"/>
        <source>
            Please specify time with units, such as 
            &quot;250 ms&quot; or &quot;2.1 s&quot;.  Specify memory as kB or MB, such as 
            &quot;32 MB&quot; or &quot;256 kB&quot;. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1246"/>
        <source>Import Wallet File</source>
        <translation>Εισαγωγή Αρχείου Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1246"/>
        <source>Wallet files (*.wallet);; All files (*)</source>
        <translation>Αρχεία πορτοφολιού (*.wallet);; Όλα τα αρχεία (*)</translation>
    </message>
</context>
<context>
    <name>DlgOfflineSelect</name>
    <message>
        <location filename="qtdialogs.py" line="5111"/>
        <source>In order to execute an offline transaction, three steps mustbe followed: &lt;br&gt;&lt;br&gt;<byte value="x9"/>(1) &lt;u&gt;On&lt;/u&gt;line Computer:  Create the unsigned transaction&lt;br&gt;<byte value="x9"/>(2) &lt;u&gt;Off&lt;/u&gt;line Computer: Get the transaction signed&lt;br&gt;<byte value="x9"/>(3) &lt;u&gt;On&lt;/u&gt;line Computer:  Broadcast the signed transaction&lt;br&gt;&lt;br&gt;You must create the transaction using a watch-only wallet on an onlinesystem, but watch-only wallets cannot sign it.  Only the offline systemcan create a valid signature.  The easiest way to execute all three stepsis to use a USB key to move the data between computers.&lt;br&gt;&lt;br&gt;All the data saved to the removable medium during all three steps arecompletely safe and do not reveal any private information that would benefit anattacker trying to steal your funds.  However, this transaction data doesreveal some addresses in your wallet, and may represent a breach of&lt;i&gt;privacy&lt;/i&gt; if not protected.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5127"/>
        <source>Create New Offline Transaction</source>
        <translation>Δημιουργία Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5128"/>
        <source>Sign and/or Broadcast Transaction</source>
        <translation>Υπόγραφή και/ή Μετάδοση Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5132"/>
        <source>No wallets available!</source>
        <translation>Δεν υπάρχουν πορτοφόλια διαθέσιμα!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5135"/>
        <source>Sign Offline Transaction</source>
        <translation>Υπόγραφή Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5138"/>
        <source>No watching-only wallets available!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5143"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Πίσω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5154"/>
        <source>
         Create a transaction from an Offline/Watching-Only wallet
         to be signed by the computer with the full wallet </source>
        <translation>
Δημιουργήστε μια συναλλαγή από ένα Αποσυνδεδεμένο/Μόνο για Προβολή πορτοφόλι
πρέπει να υπογράψετε από τον υπολογιστή με το πλήρες πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5158"/>
        <source>
         Review an unsigned transaction and sign it if you have
         the private keys needed for it </source>
        <translation>
Εξετάστε μια ανυπόγραφη συναλλαγή και υπογράψτε αν έχετε
τα ιδιωτικά κλειδιά που απαιτούνται για αυτό</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5162"/>
        <source>
         Send a pre-signed transaction to the Bitcoin network to finalize it</source>
        <translation>
Στείλτε μια προ-υπογεγραμμένη συναλλαγή στο δίκτυο του Bitcoin για να την οριστικοποιήσετε</translation>
    </message>
</context>
<context>
    <name>DlgOfflineTxCreated</name>
    <message>
        <location filename="qtdialogs.py" line="5092"/>
        <source>Review Offline Transaction</source>
        <translation>Αναθεώρηση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5068"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5070"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5073"/>
        <source>
         By clicking Done you will exit end the offline transaction process for now.
         When you are ready to sign and/or broadcast the transaction, click the Offline
         Transactions button in the main window, then click the Sign and/or
         Broadcast Transaction button in the Select Offline Action dialog.</source>
        <translation>
Κάνοντας κλικ στο Έγινε θα βγείτε απο την εκτός σύνδεσης συναλλαγή για τώρα.
Όταν είστε έτοιμοι να υπογράψετε και/ή να μεταδώσετε τη συναλλαγή, κάντε κλικ στο κουμπί Εκτός Σύνδεσης Συναλλαγές στο κύριο παράθυρο, και στη συνέχεια, κάντε κλικ στο κουμπί Υπογραφή και/ή Μετάδοση Συναλλαγής στο παράθυρο διαλόγου Επιλογή Δράσης Εκτός Σύνδεσης.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5079"/>
        <source>
         By clicking Continue you will continue to the next step in the offline
         transaction process to sign and/or broadcast the transaction.</source>
        <translation>
Κάνοντας κλικ στο Συνέχεια θα συνεχίσετε με το επόμενο βήμα στην διαδικασία της συναλλαγής εκτός σύνδεσης για να υπογράψετε και/ή να μεταδοθεί η συναλλαγή.</translation>
    </message>
</context>
<context>
    <name>DlgPasswd3</name>
    <message>
        <location filename="qtdialogs.py" line="1387"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! DO NOT FORGET YOUR PASSPHRASE !!!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! ΜΗΝ ΞΕΧΑΣΕΤΕ ΤΗΝ ΦΡΑΣΗ ΠΡΟΣΒΑΣΗΣ !!!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1390"/>
        <source>&lt;b&gt;No one can help you recover you bitcoins if you forget the passphrase and don&apos;t have a paper backup!&lt;/b&gt; Your wallet and any &lt;u&gt;digital&lt;/u&gt; backups are useless if you forget it.  &lt;br&gt;&lt;br&gt;A &lt;u&gt;paper&lt;/u&gt; backup protects your wallet forever, against hard-drive loss and losing your passphrase.  It also protects you from theft, if the wallet was encrypted and the paper backup was not stolen with it.  Please make a paper backup and keep it in a safe place.&lt;br&gt;&lt;br&gt;Please enter your passphrase a third time to indicate that you are aware of the risks of losing your passphrase!&lt;/b&gt;</source>
        <translation>&lt;b&gt; Κανείς δεν μπορεί να σας βοηθήσει να ανακτήσετε τα bitcoin σας αν ξεχάσετε τη φράση πρόσβασης και δεν έχετε ένα αντίγραφο σε χαρτί! &lt;/b&gt; το πορτοφόλι σας και κάθε &lt;u&gt;ψηφιακό&lt;/u&gt; αντίγραφο ασφαλείας είναι άχρηστο αν το ξεχάσετε. &lt;br&gt;&lt;br&gt; Ένα &lt;u&gt; χάρτινο &lt;/u&gt; αντίγραφο ασφαλείας προστατεύει το πορτοφόλι σας για πάντα, από την απώλεια του σκληρού δίσκου και την απώλεια της φράσης πρόσβασης. Θα σας προστατεύει επίσης από την κλοπή, αν το πορτοφόλι σας ήταν κρυπτογραφημένο και το αντίγραφο ασφαλείας σε χαρτί δεν είχε κλαπεί μαζί. Παρακαλώ πάρτε ένα αντίγραφο ασφαλείας σε χαρτί και φυλάξτε το σε ασφαλές μέρος. &lt;br&gt;&lt;br&gt; Παρακαλούμε, εισάγετε τη φράση πρόσβασης για τρίτη φορά για να δείξετε ότι είστε ενήμεροι για τους κινδύνους της απώλειας της φράσης πρόσβασης σας! &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1410"/>
        <source>Accept</source>
        <translation>Αποδοχή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1411"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1423"/>
        <source>WARNING!</source>
        <translation>ΠΡΟΕΙΔΟΠΟΙΗΣΗ!</translation>
    </message>
</context>
<context>
    <name>DlgPrintBackup</name>
    <message>
        <location filename="qtdialogs.py" line="6834"/>
        <source>Error Creating Backup</source>
        <translation>Σφάλμα Δημιουργία Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6834"/>
        <source>
            There was an error with the backup creator.  The operation is being
            canceled to avoid making bad backups!</source>
        <translation>Παρουσιάστηκε σφάλμα με το δημιουργό αντιγράφου ασφαλείας . Η λειτουργία
ακυρώθηκε για την αποφυγή ενός κακού αντιγράφου ασφαλείας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6915"/>
        <source>Print imported keys</source>
        <translation>Εκτύπωση Εισηγμένων Κλειδιών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6918"/>
        <source>Page:</source>
        <translation>Σελίδα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6931"/>
        <source>
         Use SecurePrintâ¢ to prevent exposing keys to printer or other
         network devices</source>
        <translation>
Κάντε χρήση του SecurePrintâ¢ για να αποφύγετε την έκθεση των κλειδιών σας σε
εκτυπωτές και άλλες συσκευές δικτύου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6938"/>
        <source>
         SecurePrintâ¢ encrypts your backup with a code displayed on
         the screen, so that no other devices on your network see the sensitive
         data when you send it to the printer.  If you turn on
         SecurePrintâ¢ &lt;u&gt;you must write the code on the page after
         it is done printing!&lt;/u&gt;  There is no point in using this feature if
         you copy the data by hand.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6946"/>
        <source>
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;  You must write the SecurePrintâ¢
         encryption code on each printed backup page!  Your SecurePrintâ¢ code is &lt;/font&gt;
         &lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;.  &lt;font color=&quot;%4&quot;&gt;Your backup will not work
         if this code is lost!&lt;/font&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6964"/>
        <source>
            &lt;b&gt;&lt;u&gt;Print Wallet Backup Fragments&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
            When any %1 of these fragments are combined, all &lt;u&gt;previous
            &lt;b&gt;and&lt;/b&gt; future&lt;/u&gt; addresses generated by this wallet will be
            restored, giving you complete access to your bitcoins.  The
            data can be copied by hand if a working printer is not
            available.  Please make sure that all data lines contain
            &lt;b&gt;9 columns&lt;/b&gt;
            of &lt;b&gt;4 characters each&lt;/b&gt; (excluding &quot;ID&quot; lines).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6975"/>
        <source>
            &lt;b&gt;&lt;u&gt;Print a Forever-Backup&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
            Printing this sheet protects all &lt;u&gt;previous &lt;b&gt;and&lt;/b&gt; future&lt;/u&gt; addresses
            generated by this wallet!  You can copy the &quot;Root Key&quot; %1
            by hand if a working printer is not available.  Please make sure that
            all data lines contain &lt;b&gt;9 columns&lt;/b&gt;
            of &lt;b&gt;4 characters each&lt;/b&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7058"/>
        <source>Lots to Print!</source>
        <translation>Πολλά προς Εκτύπωση!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7058"/>
        <source>
            This wallet contains &lt;b&gt;%1&lt;/b&gt; imported keys, which will require
            &lt;b&gt;%2&lt;/b&gt; pages to print.  Not only will this use a lot of paper,
            it will be a lot of work to manually type in these keys in the
            event that you need to restore this backup. It is recommended
            that you do &lt;u&gt;not&lt;/u&gt; print your imported keys and instead make
            a digital backup, which can be restored instantly if needed.
            &lt;br&gt;&lt;br&gt; Do you want to print the imported keys, anyway?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7092"/>
        <source>of %1</source>
        <translation>από το %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7135"/>
        <source>SecurePrint Code</source>
        <translation>SecurePrint Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7135"/>
        <source>
               &lt;br&gt;&lt;b&gt;You must write your SecurePrintâ¢
               code on each sheet of paper you just printed!&lt;/b&gt;
               Write it in the red box in upper-right corner
               of each printed page. &lt;br&gt;&lt;br&gt;SecurePrintâ¢ code:
               &lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; &lt;br&gt;&lt;br&gt;
               &lt;b&gt;NOTE: the above code &lt;u&gt;is&lt;/u&gt; case-sensitive!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7203"/>
        <source>Single-Sheet </source>
        <translation>Μονόφυλλο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7205"/>
        <source>Imported Keys </source>
        <translation>Εισηγμένα Κλειδιά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7207"/>
        <source>Fragmented Backup (%1-of-%2)</source>
        <translation>Κατακερματισμένο Αντίγραφο Ασφαλείας (%1-of-%2)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7224"/>
        <source>&lt;b&gt;%1-&lt;font color=&quot;%2&quot;&gt;#%2&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;%1-&lt;font color=&quot;%2&quot;&gt;#%2&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7236"/>
        <source>
            Any subset of &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; fragments with this
            ID (&lt;font color=&quot;%3&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt;) are sufficient to recover all the
            coins contained in this wallet.  To optimize the physical security of
            your wallet, please store the fragments in different locations.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7244"/>
        <source>
            &lt;font color=&quot;#aa0000&quot;&gt;&lt;b&gt;WARNING:&lt;/b&gt;&lt;/font&gt; Anyone who has access to this
            page has access to all the bitcoins in %1!  Please keep this
            page in a safe place.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7262"/>
        <source>
            The following %1 lines backup all addresses
            &lt;i&gt;ever generated&lt;/i&gt; by this wallet (previous and future).
            This can be used to recover your wallet if you forget your passphrase or
            suffer hardware failure and lose your wallet files. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7269"/>
        <source>
               The following is a list of all private keys imported into your
               wallet before this backup was made.   These keys are encrypted
               with the SecurePrintâ¢ code and can only be restored
               by entering them into Armory.  Print a copy of this backup without
               the SecurePrintâ¢ option if you want to be able to import
               them into another application.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7277"/>
        <source>
               The following is a list of all private keys imported into your
               wallet before this backup was made.  Each one must be copied
               manually into the application where you wish to import them.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7283"/>
        <source>
            The following is fragment &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;#%2&lt;/b&gt;&lt;/font&gt; for this
            wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7306"/>
        <source>
            &lt;b&gt;&lt;font color=&quot;#770000&quot;&gt;CRITICAL:&lt;/font&gt;  This backup will not
            work without the SecurePrintâ¢
            code displayed on the screen during printing.
            Copy it here in ink:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7413"/>
        <source>
         The following QR code is for convenience only.  It contains the
         exact same data as the %1 lines above.  If you copy this backup
         by hand, you can safely ignore this QR code. </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgProgress</name>
    <message>
        <location filename="qtdialogs.py" line="14123"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14154"/>
        <source>Enter Passphrase</source>
        <translation>Εισαγωγή Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14244"/>
        <source>%1: %2%%</source>
        <translation>%1: %2%%</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14273"/>
        <source>Progress Bar</source>
        <translation>Μπάρα Προόδου</translation>
    </message>
</context>
<context>
    <name>DlgRegAndTest</name>
    <message>
        <location filename="qtdialogs.py" line="15106"/>
        <source>Error: You cannot run the Regression Test network and Bitcoin Test Network at the same time.</source>
        <translation>Σφάλμα: Δεν μπορείτε να εκτελέσετε το Δίκτυο Παλινδρόμησης Δοκιμής και το Δοκιμαστικό Δίκτυο του Bitcoin ταυτόχρονα.</translation>
    </message>
</context>
<context>
    <name>DlgRemoveAddress</name>
    <message>
        <location filename="qtdialogs.py" line="4628"/>
        <source>&lt;b&gt;!!! WARNING !!!&lt;/b&gt;

</source>
        <translation>&lt;b&gt;!!! ΠΡΟΣΟΧΗ !!!&lt;/b&gt;

</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4632"/>
        <source>&lt;i&gt;You have requested that the following address
                            be deleted from your wallet:&lt;/i&gt;</source>
        <translation>&lt;i&gt; Ζητήσατε ότι οι ακόλουθες διευθύνσεις
να διαγραφούν από το πορτοφόλι σας: &lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4640"/>
        <source>Address:</source>
        <translation>Διεύθυνση:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4643"/>
        <source>Comment:</source>
        <translation>Σχόλιο:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4647"/>
        <source>In Wallet:</source>
        <translation>Στο Πορτοφόλι:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4654"/>
        <source>Address Balance (w/ unconfirmed):</source>
        <translation>Υπόλοιπο Διεύθυνσης (με ανεπιβεβαίωτα):</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4691"/>
        <source>Do you want to delete this address?  No other addresses in this
            wallet will be affected.</source>
        <translation>Θέλετε να διαγράψετε αυτή τη διεύθυνση; Δεν υπάρχουν άλλες διευθύνσεις στο
πορτοφόλι αυτό που θα επηρεαστούν.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4705"/>
        <source>Confirm Delete Address</source>
        <translation>Επιβεβαίωση Διαγραφής Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4709"/>
        <source>One more time...</source>
        <translation>Άλλη μια φορά...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4709"/>
        <source>
           Simply deleting an address does not prevent anyone
           from sending money to it.  If you have given this address
           to anyone in the past, make sure that they know not to
           use it again, since any bitcoins sent to it will be
           inaccessible.


           If you are maintaining an external copy of this address
           please ignore this warning


           Are you absolutely sure you want to delete %1 ?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRemoveWallet</name>
    <message>
        <location filename="qtdialogs.py" line="4344"/>
        <source>&lt;b&gt;!!! WARNING !!!&lt;/b&gt;

</source>
        <translation>&lt;b&gt;!!! ΠΡΟΣΟΧΗ !!!&lt;/b&gt;



</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4348"/>
        <source>&lt;i&gt;You have requested that the following wallet
                            be removed from Armory:&lt;/i&gt;</source>
        <translation>&lt;i&gt; Ζητήσατε τις ακόλουθες διευθύνσεις
να διαγραφούν από το πορτοφόλι Armory σας: &lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4356"/>
        <source>Wallet Unique ID:</source>
        <translation>Μοναδική Ταυτότητα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4359"/>
        <source>Wallet Name:</source>
        <translation>Όνομα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4362"/>
        <source>Description:</source>
        <translation>Περιγραφή:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4377"/>
        <source>Current Balance (w/ unconfirmed):</source>
        <translation>Υπόλοιπο Διεύθυνσης (με ανεπιβεβαίωτα):</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4416"/>
        <source>&lt;b&gt;WALLET IS NOT EMPTY.  Only delete this wallet if you
                             have a backup on paper or saved to a another location
                             outside your settings directory.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4421"/>
        <source>&lt;b&gt;WALLET IS PART OF A LOCKBOX.  Only delete this wallet if you
                             have a backup on paper or saved to a another location
                             outside your settings directory.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4429"/>
        <source>Permanently delete this wallet</source>
        <translation>Μόνιμη διαγραφή πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4430"/>
        <source>Delete private keys only, make watching-only</source>
        <translation>Διαγραφή μόνο των ιδιωτικών κλειδιών, κάνωντας το μόνο για παρακολούθηση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4439"/>
        <source>
         This will delete the wallet file, removing
         all its private keys from your settings directory.
         If you intend to keep using addresses from this
         wallet, do not select this option unless the wallet
         is backed up elsewhere.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4445"/>
        <source>
         This will delete the private keys from your wallet,
         leaving you with a watching-only wallet, which can be
         used to generate addresses and monitor incoming
         payments.  This option would be used if you created
         the wallet on this computer &lt;i&gt;in order to transfer
         it to a different computer or device and want to
         remove the private data from this system for security.&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4455"/>
        <source>
         Print a paper backup of this wallet before deleting</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4459"/>
        <source>
            This will delete the wallet file from your system.
            Since this is a watching-only wallet, no private keys
            will be deleted.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4463"/>
        <source>
            This wallet is already a watching-only wallet so this option
            is pointless</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4502"/>
        <source>
         If this box is checked, you will have the ability to print off an
         unencrypted version of your wallet before it is deleted.  &lt;b&gt;If
         printing is unsuccessful, please press *CANCEL* on the print dialog
         to prevent the delete operation from continuing&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4520"/>
        <source>Delete</source>
        <translation>Διαγραφή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4521"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4530"/>
        <source>Delete Wallet Options</source>
        <translation>Διαγραφή Επιλογών Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4538"/>
        <source>Unlock Paper Backup</source>
        <translation>Ξεκλείδωμα Χάρτινου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4540"/>
        <source>Operation Aborted</source>
        <translation>Ενέργεια Ακυρώθηκε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4540"/>
        <source>
              You requested a paper backup before deleting the wallet, but
              clicked &quot;Cancel&quot; on the backup printing window.  So, the delete
              operation was canceled as well.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4553"/>
        <source>Confirm Delete</source>
        <translation>Επιβεβαίωση Διαγραφής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4553"/>
        <source>You are about to delete a watching-only wallet.  Are you sure
         you want to do this?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4563"/>
        <source>Are you absolutely sure?!?</source>
        <translation>Είστε απόλυτα σίγουρος;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4557"/>
        <source>Are you absolutely sure you want to permanently delete
         this wallet?  Unless this wallet is saved on another device
         you will permanently lose access to all the addresses in this
         wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4563"/>
        <source>&lt;i&gt;This will permanently delete the information you need to spend
         funds from this wallet!&lt;/i&gt;  You will only be able to receive
         coins, but not spend them.  Only do this if you have another copy
         of this wallet elsewhere, such as a paper backup or on an offline
         computer with the full wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4589"/>
        <source>Wallet %1 was replaced with a watching-only wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4596"/>
        <source>Wallet %1 was deleted!</source>
        <translation>Το πορτοφόλι %1 διαγράφηκε!</translation>
    </message>
</context>
<context>
    <name>DlgReplaceWallet</name>
    <message>
        <location filename="qtdialogs.py" line="13773"/>
        <source>
                       &lt;b&gt;You already have this wallet loaded!&lt;/b&gt;&lt;br&gt;
                       You can choose to:&lt;br&gt;
                       - Cancel wallet restore operation&lt;br&gt;
                       - Set new password and fix any errors&lt;br&gt;
                       - Overwrite old wallet (delete comments &amp; labels)&lt;br&gt;
                       </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13788"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13789"/>
        <source>Overwrite</source>
        <translation>Αντικατάσταση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13790"/>
        <source>Merge</source>
        <translation>Συγχώνευση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13838"/>
        <source>Ripping Meta Data</source>
        <translation>Εξαγωγή μεταδεδομένων</translation>
    </message>
</context>
<context>
    <name>DlgRequestPayment</name>
    <message>
        <location filename="qtdialogs.py" line="10202"/>
        <source>Other Options &gt;&gt;&gt;</source>
        <translation>Άλλες Επιλογές &gt;&gt;&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9888"/>
        <source>Copy to Clipboard</source>
        <translation>Αντιγραφή στο Πρόχειρο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9889"/>
        <source>Copy Raw HTML</source>
        <translation>Αντιγραφή Ωμού Κώδικα HTML</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9890"/>
        <source>Copy Raw URL</source>
        <translation>Αντιγραφή Ωμού URL</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9891"/>
        <source>Copy All Text</source>
        <translation>Αντιγραφή Όλου του Κειμένου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9914"/>
        <source>Create a clickable link that you can copy into email or webpage to request a payment.   If the user is running a Bitcoin program that supports &quot;bitcoin:&quot; links, that program will open with all this information pre-filled after they click the link.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9924"/>
        <source>The following Bitcoin desktop applications &lt;i&gt;try&lt;/i&gt; to register themselves with your computer to handle &quot;bitcoin:&quot; links: Armory, Multibit, Electrum</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9928"/>
        <source>This is the text to be shown as the clickable link.  It should usually begin with &quot;Click here...&quot; to reaffirm to the user it is is clickable.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9932"/>
        <source>All amounts are specifed in BTC</source>
        <translation>Όλα τα ποσά ορίζονται σε BTC</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9934"/>
        <source>The person clicking the link will be sending bitcoins to this address</source>
        <translation>Το πρόσωπο κάνοντας κλικ στο σύνδεσμο θα στείλει bitcoins σε αυτή τη διεύθυνση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9936"/>
        <source>This will be pre-filled as the label/comment field after the user clicks the link. They can modify it if desired, but you can provide useful info such as contact details, order number, etc, as convenience to them.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9944"/>
        <source>Close</source>
        <translation>Κλείσιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9952"/>
        <source>&lt;b&gt;Link Text:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Σύνδεση Κειμένου:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9957"/>
        <source>&lt;b&gt;Address (yours):&lt;/b&gt;</source>
        <translation>&lt;b&gt;Διεύθυνση (δική σας):&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9962"/>
        <source>&lt;b&gt;Request (BTC):&lt;/b&gt;</source>
        <translation>&lt;b&gt;Aίτηση (BTC):&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9966"/>
        <source>&lt;b&gt;Label:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ετικέτα:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9972"/>
        <source>Copy and paste the following text into email or other document:</source>
        <translation>Αντιγράψτε και επικολλήστε το ακόλουθο κείμενο στο μήνυμα ηλεκτρονικού ταχυδρομείου ή σε άλλο έγγραφο:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9981"/>
        <source>Creating QR Code Please Wait</source>
        <translation>Δημιουργία Κώδικα QR Παρακαλώ Περιμένετε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9985"/>
        <source>This QR code contains address &lt;b&gt;and&lt;/b&gt; the other payment information shown to the left.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10019"/>
        <source>Create Payment Request Link</source>
        <translation>Δημιουργία Συνδέσμου Αίτησης Πληρωμής </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10077"/>
        <source>Amount</source>
        <translation>Ποσό</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10087"/>
        <source>Message</source>
        <translation>Μύνημα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10092"/>
        <source>Address</source>
        <translation>Διεύθυνση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10097"/>
        <source>Inputs</source>
        <translation>Είσοδοι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10101"/>
        <source>&lt;font color=&quot;red&quot;&gt;Invalid %1&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;red&quot;&gt;Εσφαλμένο %1&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10117"/>
        <source>If clicking on the line above does not work, use this payment info:</source>
        <translation>Αν κάνετε κλικ στη γραμμή παραπάνω και δεν λειτουργεί, χρησιμοποιήστε αυτές τις πληροφορίες πληρωμής:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10119"/>
        <source>&lt;b&gt;Pay to&lt;/b&gt;:<byte value="x9"/>%1&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10121"/>
        <source>&lt;b&gt;Amount&lt;/b&gt;:<byte value="x9"/>%1 BTC&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10123"/>
        <source>&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10133"/>
        <source>If clicking on the line above does not work, use this payment info:
</source>
        <translation>Αν κάνετε κλικ στη γραμμή παραπάνω δεν λειτουργεί, χρησιμοποιήστε αυτές τις πληροφορίες πληρωμής:
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10134"/>
        <source>Pay to:  %1</source>
        <translation>Πληρωμή στο: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10136"/>
        <source>
Amount:  %1 BTC</source>
        <translation>
 Ποσόν: %1 BTC</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10138"/>
        <source>
Message: %1</source>
        <translation>
 Μύνημα: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10142"/>
        <source>&lt;!DOCTYPE HTML PUBLIC &quot;-//W3C//DTD HTML 4.0//EN&quot; &quot;http://www.w3.org/TR/REC-html40/strict.dtd&quot;&gt; &lt;html&gt;&lt;head&gt;&lt;meta name=&quot;qrichtext&quot; content=&quot;1&quot; /&gt;&lt;meta http-equiv=&quot;Content-Type&quot; content=&quot;text/html; charset=utf-8&quot; /&gt;&lt;style type=&quot;text/css&quot;&gt; p, li { white-space: pre-wrap; } &lt;/style&gt;&lt;/head&gt;&lt;body&gt;&lt;p style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;!--StartFragment--&gt;&lt;a href=&quot;%1&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;%2&lt;/span&gt;&lt;/a&gt;&lt;br /&gt;If clicking on the line above does not work, use this payment info:&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay to&lt;/span&gt;: %3</source>
        <translation>&lt;!DOCTYPE HTML PUBLIC &quot;-//W3C//DTD HTML 4.0//EN&quot; &quot;http://www.w3.org/TR/REC-html40/strict.dtd&quot;&gt; &lt;html&gt;&lt;head&gt;&lt;meta name=&quot;qrichtext&quot; content=&quot;1&quot; /&gt;&lt;meta http-equiv=&quot;Content-Type&quot; content=&quot;text/html; charset=utf-8&quot; /&gt;&lt;style type=&quot;text/css&quot;&gt; p, li { white-space: pre-wrap; } &lt;/style&gt;&lt;/head&gt;&lt;body&gt;&lt;p style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;!--StartFragment--&gt;&lt;a href=&quot;%1&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;%2&lt;/span&gt;&lt;/a&gt;&lt;br /&gt;Αν το κλίκ στην παραπάνω γραμμή δεν λειτουργεί, χρησιμοποιήστε τις παρακάτω πληροφορίες πληρωμής:&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay to&lt;/span&gt;: %3</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10156"/>
        <source>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Amount&lt;/span&gt;: %1</source>
        <translation>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Ποσό&lt;/span&gt;: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10159"/>
        <source>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Message&lt;/span&gt;: %1</source>
        <translation>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Μύνημα&lt;/span&gt;: %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10222"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10200"/>
        <source>Hide Buttons &lt;&lt;&lt;</source>
        <translation>Απόκρυψη Κουμπιών &lt;&lt;&lt;</translation>
    </message>
</context>
<context>
    <name>DlgRestoreFragged</name>
    <message>
        <location filename="qtdialogs.py" line="12759"/>
        <source>&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Testing a
                     Fragmented Backup&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Δοκιμάζουμε ένα
Κατακερματισμένο Αντίγραφο Ασφαλείας&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12762"/>
        <source>Restore Wallet from Fragments</source>
        <translation>Επαναφορά Πορτοφολιού Από Θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12764"/>
        <source>
         &lt;b&gt;&lt;u&gt;%1&lt;/u&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt;
         Use this form to enter all the fragments to be restored.  Fragments
         can be stored on a mix of paper printouts, and saved files.
         If any of the fragments require a SecurePrintâ¢ code,
         you will only have to enter it once, since that code is the same for
         all fragments of any given wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12773"/>
        <source> &lt;br&gt;&lt;br&gt;
            &lt;b&gt;For testing purposes, you may enter more fragments than needed
            and Armory will test all subsets of the entered fragments to verify
            that each one still recovers the wallet successfully.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12788"/>
        <source>Input Fragments Below:</source>
        <translation>Εισάγετε Το Θράυσμα Παρακάτω:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12789"/>
        <source>+Frag</source>
        <translation>+Θραύσμα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12790"/>
        <source>-Frag</source>
        <translation>-Θραύσμα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12794"/>
        <source>Encrypt Restored Wallet</source>
        <translation>Κρυπτογράφηση Πορτοφολιού Επαναφοράς</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12803"/>
        <source>Test Backup</source>
        <translation>Δοκιμαστικό Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12803"/>
        <source>Restore from Fragments</source>
        <translation>Επαναφορά από Θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12805"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12812"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation>SecurePrintâ¢ Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12853"/>
        <source>Fragments</source>
        <translation>Θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12855"/>
        <source>Advanced Options</source>
        <translation>Προχωρημένες Επιλογές</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12870"/>
        <source>Restore wallet from fragments</source>
        <translation>Επαναφορά πορτοφολιού από θραύσματα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12888"/>
        <source>Type Data</source>
        <translation>Τύπος Δεδομένων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12889"/>
        <source>Load File</source>
        <translation>Φόρτωση αρχείου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12890"/>
        <source>Clear</source>
        <translation>Εκκαθάριση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12957"/>
        <source>Load Fragment File</source>
        <translation>Φόρτωση Αρχείου Θραύσματος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12957"/>
        <source>Wallet Fragments (*.frag)</source>
        <translation>Θραύσματα Πορτοφολιού (*.frag)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12965"/>
        <source>File Does Not Exist</source>
        <translation>Το Αρχείο Δεν Υπάρχει</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12965"/>
        <source>
            The file you select somehow does not exist...?
            &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt; Try a different file</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12999"/>
        <source>Fragment Error</source>
        <translation>Σφάλμα Θραύσματος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12999"/>
        <source>
                  There was an unfixable error in the fragment file:
                  &lt;br&gt;&lt;br&gt; File: %1 &lt;br&gt; Line: %2 &lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13027"/>
        <source>
         &lt;b&gt;Start entering fragments into the table to left...&lt;/b&gt;</source>
        <translation>
 &lt;b&gt;Ξεκινήστε να εισάγετε θραύσματα στον πίνακα στα αριστερά...&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13032"/>
        <source>&lt;b&gt;&lt;u&gt;Wallet Being Restored:&lt;/u&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;u&gt;Το Πορτοφόλι Επαναφέρεται:&lt;/u&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13034"/>
        <source>&lt;b&gt;Frags Needed:&lt;/b&gt; %1</source>
        <translation>&lt;b&gt;Θραύσματα Χρειάζονται:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13035"/>
        <source>&lt;b&gt;Wallet:&lt;/b&gt; %1</source>
        <translation>&lt;b&gt;Πορτοφόλι:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13036"/>
        <source>&lt;b&gt;Fragments:&lt;/b&gt; %1</source>
        <translation>&lt;b&gt;Θραύσματα:&lt;/b&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13078"/>
        <source>Mixed fragment types</source>
        <translation>Μεικτός τύπος θραυσμάτων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13078"/>
        <source>
            You entered a fragment for a different wallet type.  Please check
            that all fragments are for the same wallet, of the same version,
            and require the same number of fragments.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13097"/>
        <source>Multiple Walletss</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13098"/>
        <source>
            The fragment you just entered is actually for a different wallet
            than the previous fragments you entered.  Please double-check that
            all the fragments you are entering belong to the same wallet and
            have the &quot;number of needed fragments&quot; (M-value, in M-of-N).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13109"/>
        <source>Duplicate Fragment</source>
        <translation>Διπλό Θραύσμα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13109"/>
        <source>
            You just input fragment #%1, but that fragment has already been
            entered!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13146"/>
        <source>Invalid Target Compute Time</source>
        <translation>Λάθος Στόχος Χρόνος Υπολογισμού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13146"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13150"/>
        <source>Invalid Max Memory Usage</source>
        <translation>Λάθος Μέγεθος Χρήσης Μνήμης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13150"/>
        <source>You entered Max Memory Usage incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation>Εισάγατε Λάθος Μέγεθος Χρήσης Μνήμης

Εισάγετε: &lt;Αριθμό&gt; (kb, mb)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13221"/>
        <source>Verify Wallet ID</source>
        <translation>Πιστοποίηση Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13221"/>
        <source>
         The data you entered corresponds to a wallet with a wallet
         ID:&lt;blockquote&gt;&lt;b&gt;{}&lt;/b&gt;&lt;/blockquote&gt;Does this ID
         match the &quot;Wallet Unique ID&quot; printed on your paper backup?
         If not, click &quot;No&quot; and reenter key and chain-code data
         again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13237"/>
        <source>Cannot Encrypt</source>
        <translation>Δεν Μπορεί να Κρυπτογραφηθεί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13237"/>
        <source>
               You requested your restored wallet be encrypted, but no
               valid passphrase was supplied.  Aborting wallet
               recovery.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13279"/>
        <source>Computing New Addresses</source>
        <translation>Υπολογισμός Νέας Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13098"/>
        <source>Multiple Wallets</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRestoreSingle</name>
    <message>
        <location filename="qtdialogs.py" line="12191"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Test a Paper Backup&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Use this window to test a single-sheet paper backup.  If your
         backup includes imported keys, those will not be covered by this test.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12197"/>
        <source>
         &lt;b&gt;&lt;u&gt;Restore a Wallet from Paper Backup&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Use this window to restore a single-sheet paper backup.
         If your backup includes extra pages with
         imported keys, please restore the base wallet first, then
         double-click the restored wallet and select &quot;Import Private
         Keys&quot; from the right-hand menu. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12207"/>
        <source>&lt;b&gt;Backup Type:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Τύπος Αντιγράφου Ασφαλείας:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12209"/>
        <source>Version 1.35 (4 lines)</source>
        <translation>Έκδοση 1.35 (4 γραμμές)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12210"/>
        <source>Version 1.35a (4 lines Unencrypted)</source>
        <translation>Έκδοση 1.35a (4 γραμμές Χωρίς Κρυπτογράφηση)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12211"/>
        <source>Version 1.35a (4 lines + SecurePrintâ¢)</source>
        <translation>Έκδοση 1.35a (4 γραμμές +SecurePrintâ¢)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12212"/>
        <source>Version 1.35c (2 lines Unencrypted)</source>
        <translation>Έκδοση 1.35c (2 γραμμές Χωρίς Κρυπτογράφηση)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12213"/>
        <source>Version 1.35c (2 lines + SecurePrintâ¢)</source>
        <translation>Έκδοση 1.35c (2 γραμμές + SecurePrintâ¢)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12236"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation>SecurePrintâ¢ Κωδικός:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12238"/>
        <source>Root Key:</source>
        <translation>Κλειδί Root:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12238"/>
        <source>Chaincode:</source>
        <translation>Κώδικας Αλυσίδας:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12255"/>
        <source>Test Backup</source>
        <translation>Δοκιμαστικό Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12255"/>
        <source>Restore Wallet</source>
        <translation>Επαναφορά Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12258"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12265"/>
        <source>Encrypt Wallet</source>
        <translation>Κρυπτογράφηση Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12271"/>
        <source>Backup</source>
        <translation>Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12273"/>
        <source>Advanced Options</source>
        <translation>Προχωρημένες Επιλογές</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12287"/>
        <source>Test Single-Sheet Backup</source>
        <translation>Δοκιμή Μονόφυλλου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12289"/>
        <source>Restore Single-Sheet Backup</source>
        <translation>Επαναφορά Μονόφυλλου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12346"/>
        <source>Invalid Data</source>
        <translation>Λάθος Δεδομένα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12346"/>
        <source>
               There is an error in the data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.  &lt;br&gt;&lt;br&gt;
               The error occured on &lt;font color=&quot;red&quot;&gt;line #%1&lt;/font&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12359"/>
        <source>Invalid Target Compute Time</source>
        <translation>Λάθος Στόχος Χρόνος Υπολογισμού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12359"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation>Εισάγατε Λάθος Στόχο Χρόνο Υπολογισμού.

Εισάγετε: &lt;Αριθμό&gt; (ms, s)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12363"/>
        <source>Invalid Max Memory Usage</source>
        <translation>Λάθος Μέγεθος Χρήσης Μνήμης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12362"/>
        <source>You entered Max Memory Usage incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12369"/>
        <source>
            Detected errors in the data you entered.
            Armory attempted to fix the errors but it is not
            always right.  Be sure to verify the &quot;Wallet Unique ID&quot;
            closely on the next window.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12376"/>
        <source>Errors Corrected</source>
        <translation>Σφάλματα Διορθώθηκαν</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12425"/>
        <source>Verify Wallet ID</source>
        <translation>Πιστοποίηση Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12425"/>
        <source>The data you entered corresponds to a wallet with a wallet ID: 

 <byte value="x9"/>
                  %1

Does this ID match the &quot;Wallet Unique ID&quot; 
                  printed on your paper backup?  If not, click &quot;No&quot; and reenter 
                  key and chain-code data again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12440"/>
        <source>Cannot Encrypt</source>
        <translation>Δεν Μπορεί να Κρυπτογραφηθεί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12440"/>
        <source>You requested your restored wallet be encrypted, but no valid passphrase was supplied.  Aborting wallet recovery.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12484"/>
        <source>Computing New Addresses</source>
        <translation>Υπολογισμός Νέας Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12363"/>
        <source>You entered Max Memory Usage incorrectly.

Enter: &lt;Number&gt; (kb, mb)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRestoreWOData</name>
    <message>
        <location filename="qtdialogs.py" line="12520"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Test a Watch-Only Wallet Restore
         &lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
         Use this window to test the restoration of a watch-only wallet using
         the wallet's data. You can either type the data on a root data
         printout or import the data from a file.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12527"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Restore a Watch-Only Wallet
         &lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
         Use this window to restore a watch-only wallet using the wallet's
         data. You can either type the data on a root data printout or import
         the data from a file.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12535"/>
        <source>Watch-Only Root ID:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12543"/>
        <source>Data:</source>
        <translation>Δεδομένα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12562"/>
        <source>Test Backup</source>
        <translation>Δοκιμή Του Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12562"/>
        <source>Restore Wallet</source>
        <translation>Επαναφορά Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12563"/>
        <source>Load From Text File</source>
        <translation>Φόρτωση Από Αρχείο Κειμένου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12565"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12592"/>
        <source>Test Watch-Only Wallet Backup</source>
        <translation>Δοκιμή Πορτοφολιού Παρακολούθησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12594"/>
        <source>Restore Watch-Only Wallet Backup</source>
        <translation>Επαναφορά Πορτοφολιού Παρακολούθησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12604"/>
        <source>Import Wallet File</source>
        <translation>Εισαγωγή Αρχείου Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12604"/>
        <source>Root Pubkey Text Files (*.rootpubkey)</source>
        <translation>Αρχεία Κειμένου Root Pubkey (*.rootpubkey)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12687"/>
        <source>Invalid Data</source>
        <translation>Λάθος Δεδομένα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12657"/>
        <source>
               There is an error in the root ID you entered that could not
               be fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12687"/>
        <source>
               There is an error in the root data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.  &lt;br&gt;&lt;br&gt;
               The error occured on &lt;font color=&quot;red&quot;&gt;line #%1&lt;/font&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12720"/>
        <source>Wallet Already Exists</source>
        <translation>Το Πορτοφόλι Υπάρχει Ήδη</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12720"/>
        <source>The
                             wallet already exists and will not be
                             replaced.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12727"/>
        <source>Verify Wallet ID</source>
        <translation>Πιστοποίηση Ταυτότητας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12727"/>
        <source>The data you entered corresponds to a wallet with a wallet ID: 

<byte value="x9"/>%1

Does this ID match the &quot;Wallet Unique ID&quot; you intend to restore? If not, click &quot;No&quot; and enter the key and chain-code data again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12742"/>
        <source>Computing New Addresses</source>
        <translation>Υπολογισμός Νέων Διευθύνσεων</translation>
    </message>
</context>
<context>
    <name>DlgSelectMultiSigOption</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3849"/>
        <source>Create/Manage lockboxes</source>
        <translation>Δημιουργία/Διαχείρηση κουτιών κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3851"/>
        <source>Fund a lockbox</source>
        <translation>Χρηματοδότηση του κουτιού κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3852"/>
        <source>Spend from a lockbox</source>
        <translation>Ξοδέψτε απο ένα κουτί κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3854"/>
        <source>
         &lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;Multi-Sig Lockboxes
         [EXPERIMENTAL]&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;Κουτιά Πολλαπλών Υπογραφών
[ΔΟΚΙΜΑΣΤΙΚΟ]&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3859"/>
        <source>
         The buttons below link you to all the functionality needed to 
         create, fund and spend from multi-sig &quot;lockboxes.&quot;  This 
         includes turning multiple wallets into a multi-factor lock-box
         for your personal coins, or can be used for escrow between
         multiple parties, using the Bitcoin network itself to hold the
         escrow.
         &lt;br&gt;&lt;br&gt;
         &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;&lt;/b&gt;  If you are using an lockbox that requires
         being funded by multiple parties simultaneously, you should 
         &lt;b&gt;&lt;u&gt;not&lt;/u&gt; &lt;/b&gt; use regular transactions to do the funding.  
         You should use the third button labeled &quot;Fund a multi-sig lockbox&quot; 
         to collect funding promises into a single transaction, to limit 
         the ability of any party to scam you.  Read more about it by
         clicking [NO LINK YET]  (if the above doesn't hold, you can use
         the regular &quot;Send Bitcoins&quot; dialog to fund the lockbox).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3877"/>
        <source>
         Collect public keys to create an &quot;address&quot; that can be used 
         to send funds to the multi-sig container</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3883"/>
        <source>
         Send money to an lockbox simultaneously with other 
         parties involved in the lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3886"/>
        <source>
         Collect signatures to authorize transferring money out of 
         a multi-sig lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3939"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3950"/>
        <source>Multi-Sig Lockboxes</source>
        <translation>Κουτιά Πολλαπλών Υπογραφών</translation>
    </message>
</context>
<context>
    <name>DlgSelectPublicKey</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2148"/>
        <source>
         &lt;center&gt;&lt;font size=4&gt;&lt;b&gt;&lt;u&gt;Select Public Key for Lockbox 
         Creation&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;&lt;/center&gt;
         &lt;br&gt;
         Lockbox creation requires &lt;b&gt;public keys&lt;/b&gt; not the regular Bitcoin
         addresses most users are accustomed to.  A public key is much longer
         than a regular bitcoin address, usually starting with &quot;02&quot;, &quot;03&quot; or
         &quot;04&quot;.  Once you have selected a public key, send it to the lockbox 
         organizer (person or device).  The organizer will create the lockbox 
         which then must be imported by all devices that will track the funds
         and/or sign transactions.
         &lt;br&gt;&lt;br&gt;
         It is recommended that you select a &lt;i&gt;new&lt;/i&gt; key from one of your
         wallets that will not be used for any other purpose.
         You &lt;u&gt;can&lt;/u&gt; use a public key from a watching-only wallet (for 
         an offline wallet), but you will have to sign the transactions the
         same way you would a regular offline transaction.  Additionally the 
         offline computer will need to have Armory version 0.92 or later.
         &lt;br&gt;&lt;br&gt;
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;BACKUP WARNING&lt;/b&gt;&lt;/b&gt;:
         It is highly recommended that you select a public key from a
         wallet for which you have good backups!  If you are creating a lockbox
         requiring the same number of signatures as there are authorities 
         (such as 2-of-2 or 3-of-3), the loss of the wallet &lt;u&gt;will&lt;/u&gt; lead 
         to loss of lockbox funds!  
         </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2175"/>
        <source>Select Public Key:</source>
        <translation>Επιλογή Δημοσίου Κλειδιού:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2176"/>
        <source>Notes or Contact Info:</source>
        <translation>Σημειώσεις ή Πληροφορίες Επαφής:</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2177"/>
        <source>
         If multiple people will be part of this lockbox, you should 
         specify name and contact info in the box below, which will be
         available to all parties that import the finalized lockbox.
         &lt;br&gt;&lt;br&gt;
         If this lockbox will be shared among devices you own (such as for
         personal savings), specify information that helps you identify which
         device is associated with this public key.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2222"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2223"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2237"/>
        <source>Select Public Key for Lockbox</source>
        <translation>Επιλογή Δημοσίου Κλειδιού για το Κουτ΄΄ι</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2255"/>
        <source>Invalid Public Key</source>
        <translation>Λανθασμένο Δημόσιο Κλειδί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2255"/>
        <source>
            You must enter a public key into the box, &lt;b&gt;not&lt;/b&gt; a regular 
            Bitcoin address that most users are accustomed to.  A public key 
            is much longer than a Bitcoin address, and always starts with 
            &quot;02&quot;, &quot;03&quot; or &quot;04&quot;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2276"/>
        <source>Export Public Key for Lockbox</source>
        <translation>Επιλογή Δημοσίου Κλειδιού για το Κουτί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2277"/>
        <source>
         The text below includes both the public key and the notes/contact info
         you entered.  Please send this text to the organizer (person or device) 
         to be used to create the lockbox.  This data is &lt;u&gt;not&lt;/u&gt; sensitive 
         and it is appropriate be sent via email or transferred via USB storage.
         </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSendBitcoins</name>
    <message>
        <location filename="qtdialogs.py" line="5005"/>
        <source>Send Bitcoins</source>
        <translation>Αποστολή Bitcoin</translation>
    </message>
</context>
<context>
    <name>DlgSetComment</name>
    <message>
        <location filename="qtdialogs.py" line="4301"/>
        <source>Modify Comment</source>
        <translation>Τροποποίηση Σχολίου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4311"/>
        <source>Change %1 %2:</source>
        <translation>Αλλαγή %1 %2:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4312"/>
        <source>Change %1:</source>
        <translation>Αλλαγή %1:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4313"/>
        <source>Add %2 %2:</source>
        <translation>Προσθήκη %2 %2:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4314"/>
        <source>Add %1:</source>
        <translation>Προσθήκη %1:</translation>
    </message>
</context>
<context>
    <name>DlgSetLongDescr</name>
    <message>
        <location filename="MultiSigDialogs.py" line="336"/>
        <source>
               &lt;b&gt;&lt;u&gt;Set Extended Lockbox Details&lt;/u&gt;&lt;/b&gt;
               &lt;br&gt;&lt;br&gt;
               Use this space to store any extended information about this
               multi-sig lockbox, such as contact information of other
               parties, references to contracts, etc.  Keep in mind that this
               field will be included when this lockbox is shared with others,
               so you should include your own contact information, as well as
               avoid putting any sensitive data in here</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="348"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="356"/>
        <source>Edit Lockbox Description</source>
        <translation>Επεξεργασία Περιγραφής Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="393"/>
        <source>
            Using the &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; public keys above,
            a multi-sig lockbox will be created requiring
            &lt;font color=&quot;%3&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt; signatures to spend
            money.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="488"/>
        <source>Missing Name</source>
        <translation>Λείπει Όνομα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="488"/>
        <source>
            Lockboxes cannot be saved without a name (at the top of 
            the public key list).  It is also recommended to set the
            extended information next to it, for documenting the purpose
            of the lockbox.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="502"/>
        <source>Not Enough Keys</source>
        <translation>Δεν Υπάρχουν Αρκετά Κλειδιά!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="502"/>
        <source>
               You specified less than &lt;b&gt;%1&lt;/b&gt; public keys.  Please enter
               a public key into every field before continuing.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="517"/>
        <source>Invalid Public Key</source>
        <translation>Λανθασμένο Δημόσιο Κλειδί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="517"/>
        <source>
               The data specified for public key &lt;b&gt;%1&lt;/b&gt; is not valid.
               Please double-check the data was entered correctly.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="533"/>
        <source>Empty Name/ID Field</source>
        <translation>Άδειο Όνομα/Πεδίο Ταυτότητας</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="533"/>
        <source> 
               You did not specify a comment/label for one or more 
               public keys.  Other devices/parties may not be able to 
               identify them.  If this is a multi-party
               lockbox, it is recommended you put in contact information
               for each party, such as name, email and/or phone number.
               &lt;br&gt;&lt;br&gt;
               Continue with some fields blank?
               &lt;br&gt;(click &quot;No&quot; to go back and finish filling in the form)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="562"/>
        <source>Different Lockbox</source>
        <translation>Διαφορετικό Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="562"/>
        <source>
               You originally loaded lockbox (%1) but the edits you made
               have caused it to become a new/different lockbox (%2).
               Changing the M-value, N-value, or any of the public keys 
               will result in a new lockbox, unrelated to the original.
               &lt;br&gt;&lt;br&gt;
               &lt;b&gt;If you click &quot;Ok&quot; a new lockbox will be created&lt;/b&gt; instead
               of replacing the original.  If you do not need the original,
               you can go the lockbox browser and manually remove it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="577"/>
        <source>Non-Standard to Spend</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="577"/>
        <source>
            If you are running any Bitcoin Core version earlier than 0.9.3
            all spending transactions from this lockbox
            will be rejected as non-standard.  There will be no problem sending coins  
            &lt;u&gt;to&lt;/u&gt; the lockbox, but subsequent spends &lt;u&gt;from&lt;/u&gt; the 
            lockbox will require you to upgrade Bitcoin Core to at least 0.9.3 or later.  
            &lt;br&gt;&lt;br&gt;
            Do you wish to continue creating the lockbox, anyway?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSettings</name>
    <message>
        <location filename="qtdialogs.py" line="8717"/>
        <source>
         Let Armory run Bitcoin Core/bitcoind in the background</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8728"/>
        <source>Bitcoin Core/bitcoind management is not available on Mac/OSX</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8738"/>
        <source>&lt;b&gt;Bitcoin Software Management&lt;/b&gt;&lt;br&gt;&lt;br&gt;By default, Armory will manage the Bitcoin engine/software in the background.  You can choose to manage it yourself, or tell Armory about non-standard installation configuration.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8751"/>
        <source>Bitcoin Install Dir:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8752"/>
        <source>Bitcoin Home Dir:</source>
        <translation>Φάκελος του Bitcoin</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8753"/>
        <source>Leave blank to have Armory search default locations for your OS</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8755"/>
        <source>Leave blank to use default datadir (%1)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8782"/>
        <source>
         Skip online check on startup (assume internet is available, do
         not check)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8798"/>
        <source>&lt;b&gt;Privacy Settings&lt;/b&gt;</source>
        <translation>&lt;b&gt;Επιλογές Ιδιωτικότητας&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8805"/>
        <source>
         If you are going to use Armory and Bitcoin Core with a proxy (such
         as Tor), you should disable all Armory communications that might operate
         outside the proxy.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8813"/>
        <source>
         Enable settings for proxies/Tor</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8825"/>
        <source>
         &lt;b&gt;Set Armory as default URL handler&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8827"/>
        <source>
         Set Armory to be the default when you click on &quot;bitcoin:&quot;
         links in your browser or in emails.
         You can test if your operating system is supported by clicking
         on a &quot;bitcoin:&quot; link right after clicking this button.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8833"/>
        <source>Set Armory as Default</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8836"/>
        <source>
         Check whether Armory is the default handler at startup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8843"/>
        <source>Registered</source>
        <translation>Καταχωρήθηκε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8843"/>
        <source>
            Armory just attempted to register itself to handle &quot;bitcoin:&quot;
            links, but this does not work on all operating systems.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8851"/>
        <source>
         &lt;b&gt;Default fee to include with transactions:&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8853"/>
        <source>
         Fees go to users that contribute computing power to keep the
         Bitcoin network secure.  It also increases the priority of your
         transactions so they confirm faster (%1 BTC is standard).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8857"/>
        <source>
         NOTE: some transactions will require a certain fee
         regardless of your settings -- in such cases
         you will be prompted to include the correct
         value or cancel the transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8872"/>
        <source>
         &lt;b&gt;Minimize to System Tray&lt;/b&gt;
         &lt;br&gt;
         You can have Armory automatically minimize itself to your system
         tray on open or close.  Armory will stay open but run in the
         background, and you will still receive notifications.  Access Armory
         through the icon on your system tray.
         &lt;br&gt;&lt;br&gt;
         If select &quot;Minimize on close&quot;, the 'x' on the top window bar will
         minimize Armory instead of exiting the application.  You can always use
         &lt;i&gt;&quot;File&quot;&lt;/i&gt; -&gt; &lt;i&gt;&quot;Quit Armory&quot;&lt;/i&gt; to actually close it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8886"/>
        <source>Minimize to system tray on open</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8891"/>
        <source>Minimize to system tray on close</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8904"/>
        <source>&lt;b&gt;Enable notifications from the system-tray:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8905"/>
        <source>Bitcoins Received</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8906"/>
        <source>Bitcoins Sent</source>
        <translation>Τα Bitcoin Στάλθηκαν</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8907"/>
        <source>Bitcoin Core/bitcoind disconnected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8908"/>
        <source>Bitcoin Core/bitcoind reconnected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8912"/>
        <source>&lt;b&gt;Sorry!  Notifications are not available on your version of OS X.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8937"/>
        <source>&lt;b&gt;Preferred Date Format&lt;b&gt;:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8938"/>
        <source>You can specify how you would like dates to be displayed using percent-codes to represent components of the date.  The mouseover text of the &quot;(?)&quot; icon shows the most commonly used codes/symbols.  The text next to it shows how &quot;%1&quot; would be shown with the specified format.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8949"/>
        <source>Use any of the following symbols:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8963"/>
        <source>Reset to Default</source>
        <translation>Επαναφορά στις Προεπιλογές</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8981"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8982"/>
        <source>Save</source>
        <translation>Αποθήκευση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9003"/>
        <source>&lt;b&gt;Armory user mode:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Χρήστης του Armory:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9011"/>
        <source>&lt;b&gt;Preferred Language&lt;b&gt;:&lt;br&gt;</source>
        <translation>&lt;b&gt;Προτιμώμενη Γλώσσα&lt;b&gt;:&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9012"/>
        <source>Specify which language you would like Armory to be displayed in.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9133"/>
        <source>General</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9139"/>
        <source>Fee &amp; Change</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9153"/>
        <source>Armory Settings</source>
        <translation>Ρυθμίσεις του Armory </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9190"/>
        <source>&lt;b&gt;Fee&lt;br&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9192"/>
        <source>Auto fee/byte</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9194"/>
        <source>
      Fetch fee/byte from local Bitcoin node. 
      Defaults to manual fee/byte on failure. 
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9199"/>
        <source>Manual fee/byte</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9202"/>
        <source>
      Values in satoshis/byte
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9206"/>
        <source>Flat fee</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9209"/>
        <source>
      Values in BTC
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9213"/>
        <source>Auto-adjust fee/byte for better privacy</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9215"/>
        <source>
      Auto-adjust fee may increase your total fee using the selected fee/byte rate
      as its basis in an attempt to align the amount of digits after the decimal
      point between your spend values and change value.
      
      &lt;br&gt;&lt;br&gt;
      The purpose of this obfuscation technique is to make the change output
      less obvious. 
      
      &lt;br&gt;&lt;br&gt;
      The auto-adjust fee feature only applies to fee/byte options
      and does not inflate your fee by more that 10% of its original value.    
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9279"/>
        <source>&lt;b&gt;Change Address Type&lt;br&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9281"/>
        <source>Auto change</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9283"/>
        <source>
      Change address type will match the address type of recipient
      addresses. &lt;br&gt;
      
      Favors P2SH when recipients are heterogenous. &lt;br&gt;
      
      Will create nested SegWit change if inputs are SegWit and 
      recipient are P2SH. &lt;br&gt;&lt;br&gt;
      
      &lt;b&gt;Pre 0.96 Armory cannot spend from P2SH address types&lt;/b&gt;
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9295"/>
        <source>Force P2PKH</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9298"/>
        <source>Force P2SH-P2PK</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9301"/>
        <source>Force P2SH-P2WPKH</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9303"/>
        <source>
      Defaults back to P2SH-P2PK if SegWit is not enabled
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9359"/>
        <source>Invalid Path</source>
        <translation>Λάθος Μονοπάτι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9342"/>
        <source>The path you specified for the Bitcoin software installation does not exist.  Please select the directory that contains %1 or leave it blank to have Armory search the default location for your operating system</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9359"/>
        <source>The path you specified for the Bitcoin software home directory does not exist.  Only specify this directory if you use a non-standard &quot;-datadir=&quot; option when running Bitcoin Core or bitcoind.  If you leave this field blank, the following path will be used: &lt;br&gt;&lt;br&gt; %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9382"/>
        <source>Invalid Amount</source>
        <translation>Λάθος Ποσό</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9382"/>
        <source>The default fee specified could not be understood.  Please specify in BTC with no more than 8 decimal places.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9441"/>
        <source>&quot;Standard&quot; is for users that only need the core set of features to send and receive bitcoins.  This includes maintaining multiple wallets, wallet encryption, and the ability to make backups of your wallets.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9447"/>
        <source>&quot;Advanced&quot; mode provides extra Armory features such as private key importing &amp; sweeping, message signing, and the offline wallet interface.  But, with advanced features come advanced risks...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9453"/>
        <source>&quot;Expert&quot; mode is similar to &quot;Advanced&quot; but includes access to lower-level info about transactions, scripts, keys and network protocol.  Most extra functionality is geared towards Bitcoin software developers.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9464"/>
        <source>Sample: </source>
        <translation>Δείγμα:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9467"/>
        <source>Sample: [[invalid date format]]</source>
        <translation>Δείγμα: [[Μη έγκυρη μορφή ημερομηνίας]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8858"/>
        <source>
         NOTE: Some transactions will require a certain fee
         regardless of your settings -- in such cases
         you will be prompted to include the correct
         value or cancel the transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8873"/>
        <source>
         &lt;b&gt;Minimize to System Tray&lt;/b&gt;
         &lt;br&gt;
         You can have Armory automatically minimize itself to your system
         tray on open or close.  Armory will stay open but run in the
         background, and you will still receive notifications.  Access Armory
         through the icon on your system tray.
         &lt;br&gt;&lt;br&gt;
         If you select &quot;Minimize on close&quot;, the 'x' on the top window bar will
         minimize Armory instead of exiting the application.  You can always use
         &lt;i&gt;&quot;File&quot;&lt;/i&gt; -&gt; &lt;i&gt;&quot;Quit Armory&quot;&lt;/i&gt; to actually close it.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgShowKeyList</name>
    <message>
        <location filename="qtdialogs.py" line="5252"/>
        <source>The textbox below shows all keys that are part of this wallet,which includes both permanent keys and imported keys.  If yousimply want to backup your wallet and you have no imported keysthen all data below is reproducible from a plain paper backup.&lt;br&gt;&lt;br&gt;If you have imported addresses to backup, and/or youwould like to export your private keys to anotherwallet service or application, then you can save this datato disk, or copy&amp;paste it into the other application.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5262"/>
        <source>&lt;br&gt;&lt;br&gt;&lt;font color=&quot;red&quot;&gt;Warning:&lt;/font&gt; The text box below containsthe plaintext (unencrypted) private keys for each ofthe addresses in this wallet.  This information can be usedto spend the money associated with those addresses, so pleaseprotect it like you protect the rest of your wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5288"/>
        <source>Address String</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5289"/>
        <source>Hash160</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5290"/>
        <source>Private Key (Encrypted)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5291"/>
        <source>Private Key (Plain Hex)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5292"/>
        <source>Private Key (Plain Base58)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5293"/>
        <source>Public Key (BE)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5294"/>
        <source>Chain Index</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5312"/>
        <source>Imported Addresses Only</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5313"/>
        <source>Include Unused (Address Pool)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5314"/>
        <source>Include Paper Backup Root</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5315"/>
        <source>Omit spaces in key data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5353"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5354"/>
        <source>Save to File...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5355"/>
        <source>Copy to Clipboard</source>
        <translation>Αντιγραφή στο Πρόχειρο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5388"/>
        <source>All Wallet Keys</source>
        <translation>Όλα τα Κλειδιά Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5493"/>
        <source>Plaintext Private Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5493"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;REMEMBER:&lt;/b&gt;&lt;/font&gt; The data youare about to save contains private keys.  Please make surethat only trusted persons will have access to this file.&lt;br&gt;&lt;br&gt;Are you sure you want to continue?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5504"/>
        <source>Save Key List</source>
        <translation>Αποθήκευση Λίστας Κλειδιών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5504"/>
        <source>Text Files (*.txt)</source>
        <translation>Αρχεία Κειμένου (*.txt)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5504"/>
        <source>keylist_%1_.txt</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5518"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
</context>
<context>
    <name>DlgShowKeys</name>
    <message>
        <location filename="qtdialogs.py" line="3830"/>
        <source>
            &lt;font color=%1&gt;&lt;b&gt;Warning:&lt;/b&gt; the unencrypted private keys
            for this address are shown below.  They are &quot;private&quot; because
            anyone who obtains them can spend the money held
            by this address.  Please protect this information the
            same as you protect your wallet.&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3848"/>
        <source>Key Data for address: &lt;b&gt;%1&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3859"/>
        <source>
            The raw form of the private key for this address.  It is
            32-bytes of randomly generated data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3862"/>
        <source>Private Key (hex,%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3864"/>
        <source>&lt;i&gt;[[ No Private Key in Watching-Only Wallet ]]&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3868"/>
        <source>&lt;i&gt;[[ ENCRYPTED ]]&lt;/i&gt;</source>
        <translation>&lt;i&gt;[[ ΚΡΥΠΤΟΓΡΑΦΗΜΕΝΟ ]]&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3872"/>
        <source>
               This is a more compact form of the private key, and includes
               a checksum for error detection.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3875"/>
        <source>Private Key (Base58):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3882"/>
        <source>
               The raw public key data.  This is the X-coordinate of
               the Elliptic-curve public key point.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3885"/>
        <source>Public Key X (%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3890"/>
        <source>
               The raw public key data.  This is the Y-coordinate of
               the Elliptic-curve public key point.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3893"/>
        <source>Public Key Y (%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3901"/>
        <source>%1 (Network: %2 / Checksum: %3)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3904"/>
        <source>This is the hexadecimal version if the address string</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3906"/>
        <source>Public Key Hash:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3940"/>
        <source>Address Key Information</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgShowTestResults</name>
    <message>
        <location filename="qtdialogs.py" line="13348"/>
        <source>
            The total number of fragment subsets (%1) is too high
            to test and display.  Instead, %2 subsets were tested
            at random.  The results are below </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13353"/>
        <source>
            For the fragments you entered, there are a total of
            %1 possible subsets that can restore your wallet.
            The test results for all subsets are shown below</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13360"/>
        <source>
         The wallet ID is computed from the first
         address in your wallet based on the root key data (and the
         &quot;chain code&quot;).  Therefore, a matching wallet ID proves that
         the wallet will produce identical addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13373"/>
        <source>
            Fragments &lt;b&gt;%1&lt;/b&gt; and &lt;b&gt;%2&lt;/b&gt; produce a
            wallet with ID &quot;&lt;b&gt;%3&lt;/b&gt;&quot; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13395"/>
        <source>Ok</source>
        <translation>Εντάξει</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13407"/>
        <source>Fragment Test Results</source>
        <translation>Κατακερματισμένα Αποτελέσματα Δοκιμής</translation>
    </message>
</context>
<context>
    <name>DlgSignBroadcastOfflineTx</name>
    <message>
        <location filename="qtdialogs.py" line="5205"/>
        <source>Review Offline Transaction</source>
        <translation>Αναθεώρηση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5208"/>
        <source>Sign or Broadcast Transaction</source>
        <translation>Υπόγραφή ή Μετάδοση Συναλλαγής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5211"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
</context>
<context>
    <name>DlgSimpleBackup</name>
    <message>
        <location filename="qtdialogs.py" line="11184"/>
        <source>
         &lt;b&gt;Protect Your Bitcoins -- Make a Wallet Backup!&lt;/b&gt;</source>
        <translation>
&lt;b&gt; Προστατέψτε Bitcoin σας! - Πάρτε Αντίγραφο Ασφαλείας του Πορτοφολιού! &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11187"/>
        <source>
         A failed hard-drive or forgotten passphrase will lead to
         &lt;u&gt;permanent loss of bitcoins&lt;/u&gt;!  Luckily, Armory wallets only
         need to be backed up &lt;u&gt;one time&lt;/u&gt;, and protect you in both
         of these events.   If you've ever forgotten a password or had
         a hardware failure, make a backup! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11195"/>
        <source>
         Use a printer or pen-and-paper to write down your wallet &quot;seed.&quot; </source>
        <translation>
Χρησιμοποιήστε έναν εκτυπωτή ή ένα στυλό και ένα χαρτί για να γράψετε το &quot;σπόρο&quot; του πορτοφολιού σας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11197"/>
        <source>Make Paper Backup</source>
        <translation>Δημιουργία Χάρτινου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11200"/>
        <source>
         Create an unencrypted copy of your wallet file, including imported
         addresses.</source>
        <translation>
Δημιουργήστε ένα μη κρυπτογραφημένο αντίγραφο του αρχείου του πορτοφολιού σας, συμπεριλαμβανομένων των εισηγμένων
διευθύνσεων.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11203"/>
        <source>Make Digital Backup</source>
        <translation>Δημιουργία Ψηφιακού Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11206"/>
        <source> </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11207"/>
        <source>See Other Backup Options</source>
        <translation>Δείτε Άλλες Επιλογές Αντιγράφων Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11250"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11260"/>
        <source>Backup Options</source>
        <translation>Επιλογές Αντιγράφων Ασφαλείας</translation>
    </message>
</context>
<context>
    <name>DlgSimulfundSelect</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1986"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Simultaneous Lockbox
         Funding&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Ταυτόχρονη Χρηματοδότηση Κουτιού&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1990"/>
        <source>
         To have multiple parties simultaneously fund a lockbox, each party
         will need to create a &quot;promissory note,&quot; and any other party will
         collect all of them to create a single simulfunding transaction.
         This transaction will be signed by all parties after reviewing that
         it meets their expectations.  This process guarantees that either 
         all parties commit funds simultaneously, or no one does.  The
         signature that you provide using this interface is only valid if 
         all the other funding commitments are also signed.
         &lt;br&gt;&lt;br&gt;
         If you are both creating a promissory note and merging all the 
         notes together, you should first create the promissory note and
         save it to disk or copy it to your clipboard.  Once all other 
         funding commitments have been received, open this dialog again 
         and load all of them at once.  Sign for your contribution and
         send the result to all the other parties.
         &lt;br&gt;&lt;br&gt;
         You are currently handling a simulfunding operation for lockbox:
         &lt;br&gt;%1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2011"/>
        <source>Create Promissory Note</source>
        <translation>Δημιουργία Γραμμάτιου Υπόσχεσης</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2012"/>
        <source>Collect and Merge Notes</source>
        <translation>Συλλέξτε και Συγχωνεύστε Σημειώσεις</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2013"/>
        <source>Sign Simulfunding Transaction</source>
        <translation>Υπόγραφή Simulfunding Συναλλαγής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2014"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2017"/>
        <source>
            Create a commitment to a simulfunding transaction</source>
        <translation>
Χρήση υποσχετικού σημειώματος για μια συναλλαγή simulfunding</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2021"/>
        <source>
            Note creation is not available when offline.</source>
        <translation>
Η δημιουργία σημειώματος δεν είναι διαθέσιμη όταν είστε εκτός σύνδεσης.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2024"/>
        <source>
         Collect multiple promissory notes into a single simulfunding
         transaction</source>
        <translation>
Συλλογή πολλαπλών υποσχετικών σημειωμάτων σε μια συναλλαγή
simulfunding</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2028"/>
        <source>
         Review and signed a simulfunding transaction (after all promissory
         notes have been collected)</source>
        <translation>
Επανεξέταση και υπογραφή μιας συναλλαγής simulfunding (μετά που όλες οι υποσχετικές
θα έχουν συλλεχθεί)</translation>
    </message>
</context>
<context>
    <name>DlgSpendFromLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1911"/>
        <source>
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1917"/>
        <source>Create Transaction</source>
        <translation>Δημιουργία Συναλλαγής</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1918"/>
        <source>Review and Sign</source>
        <translation>Επανεξέταση και Υπογραφή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1919"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1922"/>
        <source>
            I am creating a new proposed spending transaction and will pass
            it to each party or device that needs to sign it</source>
        <translation>
Δημιουργώ μια νέα προτεινόμενη συναλλαγή δαπανών και θα την περάσω σε κάθε
μέρος ή συσκευή που χρειάζεται να το υπογράψει</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1927"/>
        <source>
            Transaction creation is not available when offline.</source>
        <translation>
Η δημιουργία συναλλαγής δεν είναι διαθέσιμη όταν είστε εκτός σύνδεσης.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1930"/>
        <source>
         Another party or device created the transaction, I just need 
         to review and sign it.</source>
        <translation>
Ένα άλλο μέρος ή συσκευή δημιούργησε τη συναλλαγή, απλά πρέπει 
να την επανεξετάσω και να την υπογράψω.</translation>
    </message>
</context>
<context>
    <name>DlgTxFeeOptions</name>
    <message>
        <location filename="qtdialogs.py" line="5543"/>
        <source>
         Transaction fees go to people who contribute processing power to
         the Bitcoin network to process transactions and keep it secure.</source>
        <translation>
Οι αμοιβές συναλλαγής πηγαίνουν στους χρήστες για την παροχή στο δίκτυο του Bitcoin
της υπολογιστικής ισχύς τους για την επεξεργασία συναλλαγών και τη διατήρηση της ασφάλειας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5546"/>
        <source>
         Nearly all transactions are guaranteed to be
         processed if a fee of 0.0005 BTC is included (less than $0.01 USD).  You
         will be prompted for confirmation if a higher fee amount is required for
         your transaction.</source>
        <translation>
Σχεδόν όλες οι συναλλαγές είναι εγγυημένο οτι θα επεξεργαστούν εάν η προμήθεια των 0,0005 BTC περιλαμβάνεται (λιγότερο από $ 0.01 USD). Θα σας
ζητηθεί επιβεβαίωση εάν ένα υψηλότερο ποσό αμοιβής απαιτείται για
τη συναλλαγή σας.</translation>
    </message>
</context>
<context>
    <name>DlgUniversalRestoreSelect</name>
    <message>
        <location filename="qtdialogs.py" line="12052"/>
        <source>
         &lt;b&gt;&lt;u&gt;Restore Wallet from Backup&lt;/u&gt;&lt;/b&gt;</source>
        <translation>
 &lt;b&gt;&lt;u&gt;Επαναφορά Πορτοφολιού απο Αντίγραφο Ασφαλείας&lt;/u&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12054"/>
        <source>You can restore any kind of backup ever created by Armory using
         one of the options below.  If you have a list of private keys
         you should open the target wallet and select &quot;Import/Sweep
         Private Keys.&quot;  </source>
        <translation>Μπορείτε να επαναφέρετε οποιοδήποτε είδος αντιγράφου ασφαλείας που δημιουργήθηκε ποτέ από το Armory χρησιμοποιώντας
μία από τις παρακάτω επιλογές. Εάν έχετε μια λίστα των ιδιωτικών κλειδιών
θα πρέπει να ανοίξετε το πορτοφόλι στόχο και να επιλέξτε &quot;Εισαγωγή / Σάρωση
Ιδιωτικών Κλειδιών. &quot;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12059"/>
        <source>I am restoring a...</source>
        <translation>Αποκαθιστώ ένα...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12061"/>
        <source>Single-Sheet Backup (printed)</source>
        <translation>Μονόφυλλο Αντίγραφο Ασφαλείας (εκτυπωμένο)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12062"/>
        <source>Fragmented Backup (incl. mix of paper and files)</source>
        <translation>Κατακερματισμένο Αντίγραφο Ασφαλείας (συμπεριλαμβανομένου χαρτιού και αρχείων)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12063"/>
        <source>Import digital backup or watching-only wallet</source>
        <translation>Εισαγωγή ψηφιακών αντιγράφων ασφαλείας ή πορτοφόλι προβολής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12064"/>
        <source>Import watching-only wallet data</source>
        <translation>Εισαγωγή δεδομένων πορτοφολιού προβολής</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12065"/>
        <source>This is a test recovery to make sure my backup works</source>
        <translation>Πρόκειται για μια δοκιμή για να βεβαιωθώ ότι τα αντίγραφα ασφαλείας λειτουργούν</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12079"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12080"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
</context>
<context>
    <name>DlgUnlockWallet</name>
    <message>
        <location filename="qtdialogs.py" line="63"/>
        <source>Enter your passphrase to unlock this wallet</source>
        <translation>Εισάγετε τη φράση πρόσβασης για να ξεκλειδώσετε αυτό το πορτοφόλι</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="64"/>
        <source>Passphrase:</source>
        <translation>Λέξη Κλειδί:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="70"/>
        <source>Unlock</source>
        <translation>Ξεκλείδωμα </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="71"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="88"/>
        <source>Using a visual keyboard to enter your passphrase protects you against simple keyloggers.   Scrambling makes it difficult to use, but prevents even loggers that record mouse clicks.</source>
        <translation>Χρησιμοποιώντας ένα εικονικό πληκτρολόγιο για να εισάγετε τη φράση πρόσβασης σας, σας προστατεύει από απλούς καταχωρητές πλήκτρων. Το μπέρδεμα καθιστά δύσκολη τη χρήση, αλλά αποτρέπει ακόμη και καταγραφείς των κλικ του ποντικιού να λειτουργήσουν.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="95"/>
        <source>Regular Keyboard</source>
        <translation>Κανονικό Πληκτρολόγιο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="96"/>
        <source>Scrambled (Simple)</source>
        <translation>Μπέρδεμα (Απλό)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="97"/>
        <source>Scrambled (Dynamic)</source>
        <translation>Μπέρδεμα (Δυναμικό)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="163"/>
        <source>Show Keyboard &gt;&gt;&gt;</source>
        <translation>Εμφάνιση Πληκτρολογίου &gt;&gt;&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="161"/>
        <source>Hide Keyboard &lt;&lt;&lt;</source>
        <translation>Απόκρυψη Πληκτρολογίου &lt;&lt;&lt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="178"/>
        <source>SHIFT</source>
        <translation>SHIFT</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="179"/>
        <source>SPACE</source>
        <translation>SPACE</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="180"/>
        <source>DEL</source>
        <translation>DEL</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="316"/>
        <source>Unlocking Wallet</source>
        <translation>Ξεκλειδωμα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="326"/>
        <source>Invalid Passphrase</source>
        <translation>Λάθος Λέξη Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="326"/>
        <source>That passphrase is not correct!</source>
        <translation>Αυτή η συνθηματική φράση δεν είναι σωστή!</translation>
    </message>
</context>
<context>
    <name>DlgUriCopyAndPaste</name>
    <message>
        <location filename="qtdialogs.py" line="10465"/>
        <source>Copy and paste a raw bitcoin URL string here.  A valid string starts with &quot;bitcoin:&quot; followed by a bitcoin address.&lt;br&gt;&lt;br&gt;You should use this feature if there is a &quot;bitcoin:&quot; link in a webpage or email that does not load Armory when you click on it.  Instead, right-click on the link and select &quot;Copy Link Location&quot; then paste it into the box below. </source>
        <translation>Αντιγραφή και επικόλληση μιας ωμής συμβολοσειράς URL bitcoin εδώ. Μια έγκυρη συμβολοσειρά αρχίζει με &quot;bitcoin:&quot; και ακολουθείται από μια διεύθυνση bitcoin.&lt;br&gt;&lt;br&gt; Θα πρέπει να χρησιμοποιήσετε αυτήν τη λειτουργία, εάν υπάρχει ένας &quot;bitcoin:&quot; σύνδεσμος σε μια ιστοσελίδα ή ένα e-mail που δεν φορτώνει το Armory όταν κάνετε κλικ σε αυτό . Αντ &apos;αυτού, κάντε δεξί κλικ στο σύνδεσμο και επιλέξτε &quot;Αντιγραφή Τοποθεσίας Συνδέσμου&quot;, και στη συνέχεια, να το επικολλήσετε στο παρακάτω πλαίσιο.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10481"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10482"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
</context>
<context>
    <name>DlgVerifySweep</name>
    <message>
        <location filename="qtdialogs.py" line="3401"/>
        <source>
            You are about to &lt;i&gt;sweep&lt;/i&gt; all funds from the specified address
            to your wallet.  Please confirm the action:</source>
        <translation>
Είστε έτοιμοι να &lt;i&gt;σαρώσετε&lt;/i&gt; όλα τα κεφάλαια από την καθορισμένη διεύθυνση
στο πορτοφόλι σας. Παρακαλούμε να επιβεβαιώσετε την ενέργεια:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3407"/>
        <source>(Fee: %1)</source>
        <translation>(Φόρος: %1)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3413"/>
        <source>      From %1</source>
        <translation>Από %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3414"/>
        <source>      To %1</source>
        <translation>Πρός %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3415"/>
        <source>      Total &lt;b&gt;%1&lt;/b&gt; BTC %2</source>
        <translation> Συνολικά &lt;b&gt;%1&lt;/b&gt; BTC %2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3418"/>
        <source>Are you sure you want to execute this transaction?</source>
        <translation>Είστε σίγουροι ότι θέλετε να εκτελέσετε αυτή τη συναλλαγή;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3434"/>
        <source>Confirm Sweep</source>
        <translation>Επιβεβαίωση Σάρωσης</translation>
    </message>
</context>
<context>
    <name>DlgWODataPrintBackup</name>
    <message>
        <location filename="qtdialogs.py" line="11452"/>
        <source>
         &lt;b&gt;&lt;u&gt;Print Watch-Only Wallet Root&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
         The lines below are sufficient to calculate public keys
         for every private key ever produced by the full wallet.
         Importing this data to an online computer is sufficient
         to receive and verify transactions, and monitor balances,
         but without the ability to spend the funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11536"/>
        <source>
         &lt;b&gt;&lt;font size=4&gt;&lt;font color=&quot;#aa0000&quot;&gt;WARNING:&lt;/font&gt;  &lt;u&gt;This is not
         a wallet backup!&lt;/u&gt;&lt;/font&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;Please make a regular digital or paper backup of your wallet
         of your wallet to keep it protected!  This data simply lets you
         monitor the funds in this wallet but gives you no ability to move any
         funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11566"/>
        <source>
         The following five lines are sufficient to reproduce all public
         keys matching the private keys produced by the full wallet.</source>
        <translation>
Οι παρακάτω πέντε γραμμές αρκούν για να παράγει όλα τα δημόσια
κλειδιά που ταιριάζουν με τα ιδιωτικά κλειδιά που παράγονται από το πλήρες πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11605"/>
        <source>
         The following QR code is for convenience only.  It contains the
         exact same data as the five lines above.  If you copy this data
         by hand, you can safely ignore this QR code. </source>
        <translation>
Ο παρακάτω κώδικας QR είναι μόνο για ευκολία. Περιέχει ακριβώς 
τα ίδια στοιχεία με τις πέντε γραμμές παραπάνω. Αν αντιγράψετε αυτά τα δεδομένα
με το χέρι, μπορείτε να αγνοήσετε αυτό τον κωδικό QR.</translation>
    </message>
</context>
<context>
    <name>DlgWalletDetails</name>
    <message>
        <location filename="qtdialogs.py" line="1512"/>
        <source>Change Wallet Labels</source>
        <translation>Αλλαγή Ετικετών Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1519"/>
        <source>Change or Remove Passphrase</source>
        <translation>Αλλάξτε ή Αφαιρέστε την Φράση Κρυπτογράφησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1521"/>
        <source>Encrypt Wallet</source>
        <translation>Κρυπτογράφηση Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1526"/>
        <source>Send Bitcoins</source>
        <translation>Αποστολή Bitcoin</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1527"/>
        <source>Receive Bitcoins</source>
        <translation>Παραλαβή Bitcoin</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1528"/>
        <source>Import/Sweep Private Keys</source>
        <translation>Εισάγετε/Σαρώστε Ιδιωτικά Κλειδιά</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1529"/>
        <source>Remove Imported Address</source>
        <translation>Κατάργηση Εισηγμένων Διευθύνσεων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1531"/>
        <source>Export Watching-Only %1</source>
        <translation>Εξαγωγή Μόνο Παρακολούθησης %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1532"/>
        <source>&lt;b&gt;Backup This Wallet&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αντίγραφο Ασφαλείας του Πορτοφολιού&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1533"/>
        <source>Delete/Remove Wallet</source>
        <translation>Διαγραφή/Αφαίρεση Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1550"/>
        <source>&lt;u&gt;&lt;/u&gt;Send bitcoins to other users, or transfer 
                             between wallets</source>
        <translation>&lt;u&gt;&lt;/u&gt;Στείλτε τα bitcoin σε άλλο χρήστη ή μεταφέρτε τα
ανάμεσα σε πορτοφόλια</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1553"/>
        <source>&lt;u&gt;&lt;/u&gt;If you have a full-copy of this wallet 
                                on another computer, you can prepare a 
                                transaction, to be signed by that computer.</source>
        <translation>&lt;u&gt;&lt;/u&gt;Αν έχετε ένα πλήρες αντίγραφο αυτού του πορτοφολιού
σε έναν άλλο υπολογιστή, μπορείτε να προετοιμάσετε μια
συναλλαγή, ώστε να υπογραφεί απο εκείνον τον υπολογιστή.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1556"/>
        <source>&lt;u&gt;&lt;/u&gt;Get a new address from this wallet for receiving 
                             bitcoins.  Right click on the address list below 
                             to copy an existing address.</source>
        <translation>&lt;u&gt;&lt;/u&gt; Πάρτε μια νέα διεύθυνση από αυτό το πορτοφόλι για την παραλαβή
bitcoin. Κάντε δεξί κλικ στη λίστα διευθύνσεων παρακάτω
για να αντιγράψετε μια υπάρχουσα διεύθυνση.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1559"/>
        <source>&lt;u&gt;&lt;/u&gt;Import or &quot;Sweep&quot; an address which is not part 
                             of your wallet.  Useful for VanityGen addresses 
                             and redeeming Casascius physical bitcoins.</source>
        <translation>&lt;u&gt; &lt;/u&gt; Εισάγετε ή &quot;Σαρώστε&quot; μια διεύθυνση η οποία δεν αποτελεί μέρος
του πορτοφολιού σας. Χρήσιμο για διευθύνσεις VanityGen
και εξαργύρωση Casascius φυσικής μορφής bitcoin.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1562"/>
        <source>&lt;u&gt;&lt;/u&gt;Permanently delete an imported address from 
                             this wallet.  You cannot delete addresses that 
                             were generated natively by this wallet.</source>
        <translation>&lt;u&gt; &lt;/u&gt; Οριστική διαγραφή μιας εισαγόμενης διεύθυνσης από
αυτό το πορτοφόλι. Δεν μπορείτε να διαγράψετε τις διευθύνσεις που
παρήχθησαν εγγενώς με αυτό το πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1566"/>
        <source>&lt;u&gt;&lt;/u&gt;Export a copy of this wallet that can 
                             only be used for generating addresses and 
                             monitoring incoming payments.  A watching-only 
                             wallet cannot spend the funds, and thus cannot 
                             be compromised by an attacker</source>
        <translation>&lt;u&gt; &lt;/u&gt; Εξαγωγή ενός αντιγράφου αυτού του πορτοφόλι που μπορεί να
χρησιμοποιηθεί μόνο για την παραγωγή διευθύνσεων και
να παρακολουθεί τις εισερχόμενες πληρωμές. Ένα πορτοφόλι μόνο για παρατήρηση
δεν μπορούν να ξοδέψει κεφάλαια, και, επομένως, δεν μπορεί
να τεθεί σε κίνδυνο από έναν εισβολέα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1571"/>
        <source>&lt;u&gt;&lt;/u&gt;See lots of options for backing up your wallet 
                             to protect the funds in it.</source>
        <translation>&lt;u&gt;&lt;/u&gt; Δείτε πολλές επιλογές για τη δημιουργία αντιγράφων ασφαλείας στο πορτοφόλι 
σας για την προστασία των κεφαλαίων σε αυτό.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1573"/>
        <source>&lt;u&gt;&lt;/u&gt;Permanently delete this wallet, or just delete 
                            the private keys to convert it to a watching-only 
                            wallet.</source>
        <translation>&lt;u&gt;&lt;/u&gt; Οριστική διαγραφή αυτού του πορτοφολιού, ή απλή διαγραφή
των ιδιωτικών κλειδιών για να μετατραπεί σε ένα πορτοφόλι παρατήρησης.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1579"/>
        <source>&lt;u&gt;&lt;/u&gt;Add/Remove/Change wallet encryption settings.</source>
        <translation>&lt;u&gt; &lt;/u&gt; Προσθήκη/Αφαίρεση/Αλλαγή ρυθμίσεων κρυπτογράφησης του πορτοφολιού.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1647"/>
        <source>Total funds if all current transactions are confirmed.  
            Value appears gray when it is the same as your spendable funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1650"/>
        <source>Funds that can be spent &lt;i&gt;right now&lt;/i&gt;</source>
        <translation>Κεφάλαια που μπορούν να ξοδευτούν &lt;i&gt;άμεσα&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1652"/>
        <source>Funds that have less than 6 confirmations</source>
        <translation>Κεφάλαια που έχουν λιγότερο από 6 επιβεβαιώσεις</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1679"/>
        <source>&lt;b&gt;Addresses in Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt; Διευθύνσεις στο Πορτοφόλι: &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1681"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Πίσω</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1700"/>
        <source>Wallet Properties</source>
        <translation>Ιδιότητες Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1713"/>
        <source>Wallet Backup</source>
        <translation>Αντίγραφο Ασφαλείας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1713"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot; size=4&gt;Please backup your wallet!&lt;/font&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt;Making a paper backup will guarantee you can recover your coins at &lt;a&gt;any time in the future&lt;/a&gt;, even if your hard drive dies or you forget your passphrase.  Without it, you could permanently lose your coins!  The backup buttons are to the right of the address list.&lt;br&gt;&lt;br&gt;A paper backup is recommended, and it can be copied by hand if you do not have a working printer. A digital backup only works if you remember the passphrase used at the time it was created.  If you have ever forgotten a password before, only rely on a digital backup if you store the password with it!&lt;br&gt;&lt;br&gt;&lt;a href=&quot;https://bitcointalk.org/index.php?topic=152151.0&quot;&gt;Read more about Armory backups&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1744"/>
        <source>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;Backup This Wallet&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Δημιουργία Αντιγράφου Ασφαλείας αυτού του Πορτοφολιού&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1763"/>
        <source>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Maximum Funds:&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Μέγιστα Ποσά:&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1764"/>
        <source>&lt;b&gt;Spendable Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Δαπανήσιμα Ποσά:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1765"/>
        <source>&lt;b&gt;Unconfirmed:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ανεπιβεβαίωτα:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1812"/>
        <source>Copy Address</source>
        <translation>Αντιγραφή Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1813"/>
        <source>Display Address QR Code</source>
        <translation>Εμφάνιση του Κωδικού QR της Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1814"/>
        <source>View Address on %1</source>
        <translation>Δείτε τη Διεύθυνση στο %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1815"/>
        <source>Request Payment to this Address</source>
        <translation>Ζητήστε Πληρωμή σε αυτή τη Διεύθυνση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1816"/>
        <source>Copy Hash160 (hex)</source>
        <translation>Αντιγραφή του Hash160 (hex)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1817"/>
        <source>Copy Raw Public Key (hex)</source>
        <translation>Αντιγραφή Κλειδιού Ωμής Συναλλαγής (Hex)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1818"/>
        <source>Copy Comment</source>
        <translation>Αντιγραφή Σχολίου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1819"/>
        <source>Copy Balance</source>
        <translation>Αντιγραφή Υπολοίπου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1844"/>
        <source>Could not open browser</source>
        <translation>Δεν μπορέσαμε να ανοίξουμε τον φυλλομετρητή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1844"/>
        <source>Armory encountered an error opening your web browser.  To viewthis address on blockchain.info, please copy and pastethe following URL into your browser:&lt;br&gt;&lt;br&gt;&lt;a href=&quot;%1&quot;&gt;%2&lt;/a&gt;</source>
        <translation>Το Armory αντιμετώπισε ένα πρόβλημα κατα το άνοιγμα του φυλλομετρητή. Για να δείτε αυτή τη διεύθυνση στο blockchain.info, παρακαλώ κάντε αντιγραφή και επικόλληση του ακόλουθου συνδέσμου στον φυλλομετρητή σας:&lt;br&gt;&lt;br&gt;&lt;a href=&quot;%1&quot;&gt;%2&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1940"/>
        <source>Invalid Passphrase</source>
        <translation>Λάθος Λέξη Κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1940"/>
        <source>Previous passphrase is not correct!  Could not unlock wallet.</source>
        <translation>Η προηγούμενη φράση πρόσβασης δεν είναι σωστή! Δεν θα μπορέσουμε να ξεκλειδώσουμε το πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1957"/>
        <source>Changing Encryption</source>
        <translation>Αλλαγή Κρυπτογράφησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1950"/>
        <source>No Encryption</source>
        <translation>Χωρίς Κρυπτογράφηση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1961"/>
        <source>Encrypted (AES256)</source>
        <translation>Κρυπτογραφημένο (AES256)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1975"/>
        <source>Offline Mode</source>
        <translation>Λειτουργία Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1975"/>
        <source>Armory is currently running in offline mode, and has noability to determine balances or create transactions.&lt;br&gt;&lt;br&gt;In order to send coins from this wallet you must use afull copy of this wallet from an online computer,or initiate an &quot;offline transaction&quot; using a watching-onlywallet on an online computer.</source>
        <translation>Το Armory εκτελείται σε λειτουργία εκτός σύνδεσης, και δεν έχει
την δυνατότητα να καθορίσει τα ποσά ή να δημιουργήσει συναλλαγές.
 &lt;br&gt;&lt;br&gt;Για να στείλετε νομίσματα από αυτό το πορτοφόλι θα πρέπει να χρησιμοποιήσετε ένα πλήρες αντίγραφο αυτού του πορτοφολιού από ένα ηλεκτρονικό υπολογιστή, ή να ξεκινήσετε μια &quot;συναλλαγή εκτός σύνδεσης&quot; χρησιμοποιώντας ένα πορτοφόλι παρατήρησης σε έναν συνδεδεμένο με το διαδίκτυο υπολογιστή.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1985"/>
        <source>Armory Not Ready</source>
        <translation>Το Armory Δεν Είναι Έτοιμο</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1985"/>
        <source>
           Armory is currently scanning the blockchain to collect
           the information needed to create transactions.  This
           typically takes between one and five minutes.  Please
           wait until your balance appears on the main window,
           then try again.</source>
        <translation>
Το Armory κάνει σάρωση της αλυσίδας για να συλλέξει
τις πληροφορίες που απαιτούνται για τη δημιουργία των συναλλαγών. Αυτό συνήθως
παίρνει μεταξύ ενός και πέντε λεπτών. Παρακαλώ περιμένετε μέχρι
το υπόλοιπο σας να εμφανιστεί στο κύριο παράθυρο, και στη συνέχεια, δοκιμάστε ξανά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2016"/>
        <source>Create Paper Backup</source>
        <translation>Δημιουργία Χάρτινου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2021"/>
        <source>Move along...</source>
        <translation>Προχωρήστε...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2021"/>
        <source>This wallet does not contain any private keys.  Nothing to backup!</source>
        <translation>Αυτό το πορτοφόλι δεν περιέχει ιδιωτικά κλειδιά. Δεν υπάρχει κάτι να ληφθεί σαν αντίγραφο ασφαλείας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2035"/>
        <source>Unlock Private Keys</source>
        <translation>Ξεκλείδωμα Ιδιωτικών Κλειδιών</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2044"/>
        <source>Unlock Failed</source>
        <translation>Το Ξεκλείδωμα Απέτυχε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2038"/>
        <source>
                  Wallet was not be unlocked.  The public keys and addresses
                  will still be shown, but private keys will not be available
                  unless you reopen the dialog with the correct passphrase</source>
        <translation>
Το πορτοφόλι δεν ξεκλειδώθηκε. Τα δημόσια κλειδιά και οι διευθύνσεις
θα εμφανίζονται, αλλά τα ιδιωτικά κλειδιά δεν θα είναι διαθέσιμα
εκτός και αν ξανα ανοίξετε το πλαίσιο διαλόγου με την σωστή λέξη κλειδί.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2044"/>
        <source>
                  Wallet could not be unlocked to display individual keys.</source>
        <translation>
Το πορτοφόλι δεν μπορούσε να ξεκλειδωθεί με τα ξεχωριστά κλειδιά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2055"/>
        <source>No Selection</source>
        <translation>Καμία Επιλογή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2055"/>
        <source>You must select an address to remove!</source>
        <translation>Πρέπει να επιλέξετε μία διεύθυνση για να αφαιρεθεί!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2072"/>
        <source>Invalid Selection</source>
        <translation>Λάθος Επιλογή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2072"/>
        <source>
               You cannot delete addresses generated by your wallet.
               Only imported addresses can be deleted.</source>
        <translation>
Δεν μπορείτε να διαγράψετε διευθύνσεις που δημιουργούνται από το πορτοφόλι σας
Μόνο οι διευθύνσεις που εισάγονται μπορούν να διαγραφούν.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2081"/>
        <source>Imported Address Warning</source>
        <translation>Προειδοποίηση Εισαγόμενης Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2081"/>
        <source>Armory supports importing of external private keys into yourwallet but imported addresses are &lt;u&gt;not&lt;/u&gt; automaticallyprotected by your backups.  If you do not plan to use theaddress again, it is recommended that you &quot;Sweep&quot; the privatekey instead of importing it.&lt;br&gt;&lt;br&gt;Individual private keys, including imported ones, can bebacked up using the &quot;Export Key Lists&quot; option in the walletbackup window.</source>
        <translation>Το Armory υποστηρίζει την εισαγωγή και την εξαγωγή ιδιωτικών κλειδιών στο πορτοφόλι σας αλλά οι εισαγόμενες διευθύνσεις &lt;u&gt;δεν&lt;/u&gt; προστατεύουν αυτόματα τα αντίγραφα ασφαλείας σας. Αν σχεδιάζετε να μην κάνετε χρήση της διεύθυνσης ξανά, προτείνετε να &quot;Σαρώσετε&quot; το ιδιωτικό κλειδί αντί να το εισάγετε.&lt;br&gt;&lt;br&gt; Μοναδικά ιδιωτικά κλειδιά συμπεριλαμβανομένων και αυτών που έχουν εισαχθεί μπορούν να παρθούν σε αντίγραφο ασφαλείας με την χρήση του &quot;Εξαγωγή Λίστας Κλειδιών&quot; στο παράθυρο των αντιγράφων ασφαλείας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2113"/>
        <source>Move along... This wallet does not have
                             a chain code. Backups are pointless!</source>
        <translation>Προχωρήστε... Αυτό το πορτοφόλι δεν έχει
έναν κωδικό αλυσίδας. Τα αντίγραφα ασφαλείας είναι άχρηστα!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2138"/>
        <source>
            This is the name stored with the wallet file.  Click on the
            &quot;Change Labels&quot; button on the right side of this
            window to change this field</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2143"/>
        <source>
            This is the description of the wallet stored in the wallet file.
            Press the &quot;Change Labels&quot; button on the right side of this
            window to change this field</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2148"/>
        <source>
            This is a unique identifier for this wallet, based on the root key.
            No other wallet can have the same ID
            unless it is a copy of this one, regardless of whether
            the name and description match.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2154"/>
        <source>
            This is the number of addresses *used* by this wallet so far.
            If you recently restored this wallet and you do not see all the
            funds you were expecting, click on this field to increase it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2160"/>
        <source>
            Offline:  This is a &quot;Watching-Only&quot; wallet that you have identified
            belongs to you, but you cannot spend any of the wallet funds
            using this wallet.  This kind of wallet
            is usually stored on an internet-connected computer, to manage
            incoming transactions, but the private keys needed
            to spend the money are stored on an offline computer.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2168"/>
        <source>
            Watching-Only:  You can only watch addresses in this wallet
            but cannot spend any of the funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2172"/>
        <source>
            No Encryption: This wallet contains private keys, and does not require
            a passphrase to spend funds available to this wallet.  If someone
            else obtains a copy of this wallet, they can also spend your funds!
            (You can click the &quot;Change Encryption&quot; button on the right side of this
            window to enabled encryption)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2179"/>
        <source>
            This wallet contains the private keys needed to spend this wallet's
            funds, but they are encrypted on your harddrive.  The wallet must be
            &quot;unlocked&quot; with the correct passphrase before you can spend any of the
            funds.  You can still generate new addresses and monitor incoming
            transactions, even with a locked wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2186"/>
        <source>
            Declare who owns this wallet.  If you click on the field and select
            &quot;This wallet is mine&quot;, it's balance will be included in your total
            Armory Balance in the main window</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2191"/>
        <source>
            This is exactly how long it takes your computer to unlock your
            wallet after you have entered your passphrase.  If someone got
            ahold of your wallet, this is approximately how long it would take
            them to for each guess of your passphrase.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2197"/>
        <source>
            This is the amount of memory required to unlock your wallet.
            Memory values above 64 kB pretty much guarantee that GPU-acceleration
            will be useless for guessing your passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2202"/>
        <source>
            Wallets created with different versions of Armory, may have
            different wallet versions.  Not all functionality may be
            available with all wallet versions.  Creating a new wallet will
            always create the latest version.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2208"/>
        <source>Wallet Name:</source>
        <translation>Όνομα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2209"/>
        <source>Description:</source>
        <translation>Περιγραφή:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2211"/>
        <source>Wallet ID:</source>
        <translation>Ταυτότητα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2212"/>
        <source>Addresses Used:</source>
        <translation>Διευθύνσεις που Χρησιμοποιήθηκαν:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2213"/>
        <source>Security:</source>
        <translation>Ασφάλεια:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2214"/>
        <source>Version:</source>
        <translation>Έκδοση:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2216"/>
        <source>Belongs to:</source>
        <translation>Ανήκει στο:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2222"/>
        <source>Unlock Time:</source>
        <translation>Χρόνος Ξεκλειδώματος:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2223"/>
        <source>Unlock Memory:</source>
        <translation>Ξεκλειδώστε τη Μνήμη:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2371"/>
        <source>You own this wallet</source>
        <translation>Είστε κάτοχος αυτού του πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2249"/>
        <source>Someone else...</source>
        <translation>Κάποιος άλλος...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2259"/>
        <source>Click to Test</source>
        <translation>Κάντε κλικ για να Δοκιμάσετε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2373"/>
        <source>&lt;i&gt;Offline&lt;/i&gt;</source>
        <translation>&lt;i&gt;Εκτός Σύνδεσης&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2382"/>
        <source>Someone else</source>
        <translation>Κάποιος άλλος</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2383"/>
        <source>&lt;i&gt;Watching-Only&lt;/i&gt;</source>
        <translation>&lt;i&gt;Μόνο για Παρακολούθηση&lt;/i&gt;</translation>
    </message>
</context>
<context>
    <name>DlgWalletSelect</name>
    <message>
        <location filename="qtdialogs.py" line="4746"/>
        <source>No Wallets!</source>
        <translation>Δεν υπάρχουν πορτοφόλια!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4746"/>
        <source>There are no wallets to select from.  Please create or import
            a wallet first.</source>
        <translation>Δεν υπάρχουν πορτοφόλια απο τα οποία να επιλέξετε από. Παρακαλείστε να δημιουργήσετε ή να εισάγετε ένα πορτοφόλι πρώτα.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4775"/>
        <source>Select Wallet</source>
        <translation>Επιλογή Πορτοφολιού</translation>
    </message>
</context>
<context>
    <name>DlgWltRecoverWallet</name>
    <message>
        <location filename="qtdialogs.py" line="13856"/>
        <source>Browse File System</source>
        <translation>Περιηγηθείτε στο Σύστημα Αρχείων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13860"/>
        <source>
         &lt;b&gt;Wallet Recovery Tool:
         &lt;/b&gt;&lt;br&gt;
         This tool will recover data from damaged or inconsistent
         wallets.  Specify a wallet file and Armory will analyze the
         wallet and fix any errors with it.
         &lt;br&gt;&lt;br&gt;
         &lt;font color=&quot;%1&quot;&gt;If any problems are found with the specified
         wallet, Armory will provide explanation and instructions to
         transition to a new wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13872"/>
        <source>Wallet Path:</source>
        <translation>Διαδρομή Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13877"/>
        <source>Select Wallet...</source>
        <translation>Επιλογή Πορτοφολιού...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13883"/>
        <source>Select Loaded Wallet</source>
        <translation>Επιλέξτε Πορτοφόλι Φόρτωσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13907"/>
        <source>&lt;b&gt;Stripped Recovery&lt;/b&gt;&lt;br&gt;Only attempts to                             recover the wallet&apos;s rootkey and chaincode</source>
        <translation>&lt;b&gt;Απογυμνωμένη Ανάκτηση&lt;/b&gt; &lt;br&gt; Επιχειρεί να ανακτήσει μόνο το rootkey και την αλυσίδα κώδικα</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13914"/>
        <source>&lt;b&gt;Bare Recovery&lt;/b&gt;&lt;br&gt;Attempts to recover all private key related data</source>
        <translation>&lt;b&gt;Γυμνή Ανάκτηση&lt;/b&gt;&lt;/br&gt; Προσπαθεί να ανακτήσει όλα τα προσωπικά δεδομένα που σχετίζονται με το κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13921"/>
        <source>&lt;b&gt;Full Recovery&lt;/b&gt;&lt;br&gt;Attempts to recover as much data as possible</source>
        <translation>&lt;b&gt;Πλήρης Ανάκτηση&lt;/b&gt;&lt;/br&gt; Προσπαθεί να ανακτήσει όσα περισσότερα δεδομένα είναι δυνατόν</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13927"/>
        <source>&lt;b&gt;Consistency Check&lt;/b&gt;&lt;br&gt;Checks wallet consistency. Works with both full and watch only&lt;br&gt; wallets. Unlocking of encrypted wallets is not mandatory</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13971"/>
        <source>Recover</source>
        <translation>Ανάκτηση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13972"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13983"/>
        <source>The entered path does not exist</source>
        <translation>Η εισηγμένη διαδρομή δεν υπάρχει</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13996"/>
        <source>Wallet Recovery Tool</source>
        <translation>Εργαλείο Ανάκτησης Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14040"/>
        <source>Wallet files (*.wallet);; All files (*)</source>
        <translation>Αρχεία πορτοφολιού (*.wallet);; Όλα τα αρχεία (*)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14047"/>
        <source>Recover Wallet</source>
        <translation>Ανάκτηση Πορτοφολιού</translation>
    </message>
</context>
<context>
    <name>FeeSelectionDialog</name>
    <message>
        <location filename="FeeSelectUI.py" line="53"/>
        <source>Flat Fee (BTC)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="75"/>
        <source>Fee/Byte (Satoshi/Byte)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="97"/>
        <source>Auto Fee/Byte (Satoshi/Byte)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="105"/>
        <source>Fetch fee/byte from your network node</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="107"/>
        <source>Failed to fetch fee/byte from node</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="121"/>
        <source>Close</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="124"/>
        <source>Adjust fee/byte for privacy</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="145"/>
        <source>Select Fee Type</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>LedgerDispModelSimple</name>
    <message>
        <location filename="armorymodels.py" line="254"/>
        <source>Transaction confirmed!
(%d confirmations)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="259"/>
        <source>%d/120 confirmations</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="260"/>
        <source>

This is a &quot;generation&quot; transaction from
Bitcoin mining.  These transactions take
120 confirmations (approximately one day)
before they are available to be spent.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="265"/>
        <source>This is a mempool replaceable transaction. Do not consider you have been sent these coins until this transaction has at least 1 confirmation.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="269"/>
        <source>%d/6 confirmations</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="270"/>
        <source>

For small transactions, 2 or 3 confirmations is usually acceptable. For larger transactions, you should wait for 6 confirmations before trusting that the transaction is valid.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="280"/>
        <source>Bitcoins sent and received by the same wallet</source>
        <translation>Bitcoins αποστέλλονται και λαμβάνονται από το ίδιο πορτοφόλι</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="285"/>
        <source>You mined these Bitcoins!</source>
        <translation>Εσείς κάνατε εξόρυξη αυτών των Bitcoin!</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="287"/>
        <source>Bitcoins sent</source>
        <translation>Τα Bitcoin στάλθηκαν</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="289"/>
        <source>Bitcoins received</source>
        <translation>Τα Bitcoin Ελήφθησαν</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="292"/>
        <source>The net effect on the balance of this wallet &lt;b&gt;not including transaction fees.&lt;/b&gt;  You can change this behavior in the Armory preferences window.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="297"/>
        <source>The net effect on the balance of this wallet, including transaction fees.</source>
        <translation>Η τιμή που εμφανίζεται εδώ είναι το αποτέλεσμα για το
πορτοφόλι σας, συμπεριλαμβανομένων των τελών συναλλαγής.</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="307"/>
        <source>Date</source>
        <translation>Ημερομηνία</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="308"/>
        <source>Lockbox</source>
        <translation>Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="308"/>
        <source>Wallet</source>
        <translation>Πορτοφόλι</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="309"/>
        <source>Comments</source>
        <translation>Σχόλια</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="311"/>
        <source>Amount</source>
        <translation>Ποσό</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="312"/>
        <source>Other Owner</source>
        <translation>Άλλος Ιδιοκτήτης</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="313"/>
        <source>Wallet ID</source>
        <translation>Ταυτότητα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="314"/>
        <source>Tx Hash (LE)</source>
        <translation>Tx Hash (LE)</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="254"/>
        <source>Transaction confirmed!
(%1 confirmations)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="259"/>
        <source>%1/120 confirmations</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="269"/>
        <source>%1/6 confirmations</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>LetterButton</name>
    <message>
        <location filename="qtdialogs.py" line="349"/>
        <source>SPACE</source>
        <translation>SPACE</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="354"/>
        <source>SHIFT</source>
        <translation>SHIFT</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="358"/>
        <source>DEL</source>
        <translation>DEL</translation>
    </message>
</context>
<context>
    <name>LockboxDisplayModel</name>
    <message>
        <location filename="MultiSigModels.py" line="90"/>
        <source>Scanning: %1%%</source>
        <translation>Ανάγνωση: %1%%</translation>
    </message>
</context>
<context>
    <name>LockboxSelectFrame</name>
    <message>
        <location filename="WalletFrames.py" line="28"/>
        <source>Invalid Lockbox</source>
        <translation>Λανθασμένο Κουτί Κλειδώματος</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="28"/>
        <source> There was 
         an error loading the specified lockbox (%1).</source>
        <translation>Υπήρξε ένα σφάλμα
στην φόρτωση του συγκεκριμένου κουτιού (%1).</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="34"/>
        <source> &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Lockbox
         %2 (%3-of-%4)&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;</source>
        <translation> &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Κουτί
%2 (%3-of-%4)&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="39"/>
        <source>Lockbox ID:</source>
        <translation>Ταυτότητα Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="40"/>
        <source>Name:</source>
        <translation>Όνομα:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="41"/>
        <source>Description:</source>
        <translation>Περιγραφή:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="42"/>
        <source>Spendable BTC:</source>
        <translation>Δαπανήσιμα BTC:</translation>
    </message>
</context>
<context>
    <name>MessageSigningVerificationDialog</name>
    <message>
        <location filename="toolsDialogs.py" line="24"/>
        <source>Message Signing/Verification</source>
        <translation>Υπογραφή Μυνήματος/Πιστοποίηση</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="32"/>
        <source>Sign Message</source>
        <translation>Υπογραφή Μυνήματος</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="33"/>
        <source>Verify Bare Signature</source>
        <translation>Πιστοποίηση Γυμνής Υπογραφής</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="34"/>
        <source>Verify Signed Message Block</source>
        <translation>Βεβαίωση Υπογραφής Μπλόκ Μηνυμάτων</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="37"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
</context>
<context>
    <name>MessageSigningWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="63"/>
        <source>Sign with Address:</source>
        <translation> Υπογραφή με Διεύθυνση:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="72"/>
        <source>Message to sign:</source>
        <translation>Μύνημα προς υπογραφή:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="82"/>
        <source>Bare Signature (Bitcoin Core Compatible)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="83"/>
        <source>Base64 Signature</source>
        <translation>Base64 Υπογραφή</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="84"/>
        <source>Clearsign Signature</source>
        <translation>Clearsign Υπογραφή</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="92"/>
        <source>Message Signature:</source>
        <translation>Μύνημα Υπογραφής:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="99"/>
        <source>Copy Signature</source>
        <translation>Αντιγραφή Υπογραφής</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="100"/>
        <source>Clear All</source>
        <translation>Εκκαθάριση Όλων</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="125"/>
        <source>Unlock Wallet to Import</source>
        <translation>Ξεκλείδωμα Πορτοφολιού για Εισαγωγή</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="127"/>
        <source>Wallet is Locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="127"/>
        <source>Cannot import private keys without unlocking wallet!</source>
        <translation>
Δεν είναι δυνατή η εισαγωγή των ιδιωτικών κλειδιών χωρίς να ξεκλειδώσετε το πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="168"/>
        <source>Non ASCII Text</source>
        <translation>Μη ASCII Κείμενο</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="168"/>
        <source>Message to sign must be ASCII</source>
        <translation>Το μήνυμα προς υπογραφή πρέπει να είναι σε ASCII</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="179"/>
        <source>Private Key Not Known</source>
        <translation>Το Ιδιωτικό Κλειδί δεν είναι Γνωστό</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="179"/>
        <source>The private key is not known for this address.</source>
        <translation>Το ιδιωτικό κλειδί δεν είναι γνωστό για αυτή την διεύθυνση.</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="173"/>
        <source>Invalid Address</source>
        <translation>Λάθος Διεύθυνση</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="173"/>
        <source>The signing address is invalid.</source>
        <translation>Η διεύθυνση υπογραφής δεν είναι έγκυρη.</translation>
    </message>
</context>
<context>
    <name>MirrorWalletsDialog</name>
    <message>
        <location filename="WalletMirrorDialog.py" line="119"/>
        <source>
      Starting v0.96, Armory needs to mirror Python
      wallets into C++ wallets in order to operate. Mirrored C++ wallets
      are watching only (they do not hold any private keys).&lt;br&gt;&lt;br&gt;
            
      Mirrored wallets are used to interface with the database and perform
      operations that aren't available to the legacy Python wallets, such
      support for compressed public keys and Segregated Witness transactions.
      &lt;br&gt;&lt;br&gt;
      
      Mirroring only needs to happen once per wallet. Synchronization
      will happen every time the Python wallet address chain is ahead of the 
      mirrored Cpp wallet address chain (this typically rarely happens).
      &lt;br&gt;&lt;br&gt;
      
      This process can take up to a few minutes per wallet.&lt;br&gt;&lt;br&gt;
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletMirrorDialog.py" line="154"/>
        <source>Mirroring Wallets</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>NewWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="352"/>
        <source>Wallet &amp;name:</source>
        <translation> Πορτοφόλι $όνομα:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="359"/>
        <source>Wallet &amp;description:</source>
        <translation>&amp;Περιγραφή Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="364"/>
        <source>Add Manual &amp;Entropy</source>
        <translation>Προσθήκη Χειροκίνητης &amp;Εντροπίας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="381"/>
        <source>Configure</source>
        <translation>Ρύθμιση</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="385"/>
        <source>Advanced Options</source>
        <translation>Προχωρημένες Επιλογές</translation>
    </message>
</context>
<context>
    <name>OutputBundle</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2630"/>
        <source>Unrelated Multi-Spend</source>
        <translation>Ασύνδετο Πολλαπλό-Ξόδεμα</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2630"/>
        <source>
               The signature-collector you loaded appears to be
               unrelated to any of the wallets or lockboxes that you have
               available.  If you were expecting to be able to sign for a
               lockbox input, you need to import the lockbox definition    
               first.  Any other person or device with the lockbox loaded
               can export it to be imported by this device.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2638"/>
        <source>Cannot Sign</source>
        <translation>Δεν Μπορεί να Υπογραφεί</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2638"/>
        <source>
               The signature-collector you loaded is sending money to one
               of your wallets or lockboxes, but does not have any inputs
               for which you can sign.  
               If you were expecting to be able to sign for a
               lockbox input, you need to import the lockbox definition    
               first.  Any other person or device with the lockbox loaded
               can export it to be imported by this device.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2676"/>
        <source>
               &lt;b&gt;&lt;u&gt;Spending:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
 &lt;b&gt;&lt;u&gt;Ξοδεύοντας:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2681"/>
        <source>
               &lt;b&gt;&lt;u&gt;Contributor:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;%3&lt;/font&gt;</source>
        <translation>
 &lt;b&gt;&lt;u&gt;Συνεισφέρων:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;%3&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2757"/>
        <source>[[Unknown Signer]]</source>
        <translation>[[Άγνωστος Υπογράφων]]</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2810"/>
        <source>
            &lt;b&gt;&lt;u&gt;Receiving:&lt;/u&gt;  &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt;&lt;/b&gt;</source>
        <translation> 
&lt;b&gt;&lt;u&gt;Παραλαβή:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2858"/>
        <source>Import/Merge</source>
        <translation>Εισαγωγή/Συγχώνευση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2861"/>
        <source>Broadcast</source>
        <translation>Μετάδοση</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2862"/>
        <source>Export</source>
        <translation>Εξαγωγή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2863"/>
        <source>Done</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2900"/>
        <source>Review and Sign</source>
        <translation>Επανεξέταση και Υπογραφή</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2919"/>
        <source>Sign Lockbox</source>
        <translation>Υπογραφή Κουτιού Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2921"/>
        <source>Wallet is locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2921"/>
        <source>Cannot sign without unlocking wallet!</source>
        <translation>Δεν είναι δυνατή η υπογραφή χωρίς να ξεκλειδώσετε το πορτοφόλι!</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2974"/>
        <source>Done!</source>
        <translation>Έγινε</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3014"/>
        <source>
            from any online computer (you are currently offline)</source>
        <translation>
από οποιοδήποτε συνδεδεμένο ηλεκτρονικό υπολογιστή (τώρα είστε εκτός σύνδεσης)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3019"/>
        <source>
         &lt;font color=&quot;%1&quot;&gt;This transaction has enough signatures and
         can be broadcast %2&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot;&gt;Η συναλλαγή αυτή έχει αρκετές υπογραφές και
μπορεί να μεταδοθεί %2&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3028"/>
        <source>
            &lt;font color=&quot;%1&quot;&gt;This transaction is incomplete.  You can
            add signatures then export and give to other parties or
            devices to sign.&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3043"/>
        <source>Export Signature Collector</source>
        <translation>Εξαγωγή Συλλέκτη Υπογραφών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3044"/>
        <source>
         The text below includes all data about this multi-sig transaction, 
         including all the signatures already made to it.  It contains 
         everything needed to securely review and sign it, including offline 
         devices/wallets.  
         &lt;br&gt;&lt;br&gt;
         If this transaction requires signatures from multiple parties, it is
         safe to send this data via email or USB key.  No data is included 
         that would compromise the security of any of the signing devices.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3061"/>
        <source>Import Signature Collector</source>
        <translation>Εισαγωγή Συλλέκτη Υπογραφών</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3062"/>
        <source>
         Load a multi-sig transaction for review, signing and/or broadcast.  
         If any of your loaded wallets can sign for any transaction inputs,
         you will be able to execute the signing for each one.  If your 
         signature completes the transaction, you can then broadcast it to
         finalize it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3093"/>
        <source>Invalid Signatures</source>
        <translation>Λανθασμένες Υπογραφές</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3093"/>
        <source>
            Somehow not all inputs have valid sigantures!  You can choose  
            to attempt to broadcast anyway, in case you think Armory is
            not evaluating the transaction state correctly.  
            &lt;br&gt;&lt;br&gt;
            Otherwise, please confirm that you have created signatures 
            from the correct wallets.  Perhaps try collecting signatures
            again...?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>PromissoryCollectModel</name>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Note ID</source>
        <translation>Σημείωση Ταυτότητας</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Label</source>
        <translation>Ετικέτα</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Funding</source>
        <translation>Χρηματοδότηση</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Fee</source>
        <translation>Φόρος</translation>
    </message>
</context>
<context>
    <name>ReviewOfflineTxFrame</name>
    <message>
        <location filename="TxFrames.py" line="1174"/>
        <source>There is no security-sensitive information in this data below, so it is perfectly safe to copy-and-paste it into an email message, or save it to a borrowed USB key.</source>
        <translation>Δεν υπάρχει καμία ασφάλεια ευαίσθητων πληροφοριών σε αυτά τα δεδομένα, έτσι είναι απόλυτα ασφαλές να αντιγράψετε και να το επικολλήσετε σε ένα μήνυμα ηλεκτρονικού ταχυδρομείου, ή να το αποθηκεύσετε σε ένα δανεικό κλειδί USB.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1179"/>
        <source>Save as file...</source>
        <translation>Αποθήκευση ως αρχείο...</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1181"/>
        <source>Save this data to a USB key or other device, to be transferred to a computer that contains the private keys for this wallet.</source>
        <translation>Αποθηκεύστε τα δεδομένα σε ένα κλειδί USB ή σε άλλη συσκευή, για να μεταφερθούν σε έναν υπολογιστή που περιέχει τα ιδιωτικά κλειδιά για αυτό το πορτοφόλι.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1185"/>
        <source>Copy to clipboard</source>
        <translation>Αντιγραφή στο πρόχειρο</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1190"/>
        <source>Copy the transaction data to the clipboard, so that it can be pasted into an email or a text document.</source>
        <translation>Αντιγράψτε τα δεδομένα συναλλαγών στο πρόχειρο, έτσι ώστε να μπορεί να επικολληθεί σε ένα μήνυμα ηλεκτρονικού ταχυδρομείου ή ένα έγγραφο κειμένου.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1194"/>
        <source>&lt;b&gt;Instructions for completing this transaction:&lt;/b&gt;</source>
        <translation>&lt;b&gt; Οδηγίες για την ολοκλήρωση αυτής της συναλλαγής: &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1252"/>
        <source>&lt;b&gt;Transaction Data&lt;/b&gt; <byte value="x9"/> (Unsigned ID: %1)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1259"/>
        <source>
            The block of data shown below is the complete transaction you 
            just requested, but is invalid because it does not contain any
            signatures.  You must take this data to the computer with the 
            full wallet to get it signed, then bring it back here to be
            broadcast to the Bitcoin network.
            &lt;br&gt;&lt;br&gt;
            Use &quot;Save as file...&quot; to save an &lt;i&gt;*.unsigned.tx&lt;/i&gt; 
            file to USB drive or other removable media.  
            On the offline computer, click &quot;Offline Transactions&quot; on the main 
            window.  Load the transaction, &lt;b&gt;review it&lt;/b&gt;, then sign it 
            (the filename now end with &lt;i&gt;*.signed.tx&lt;/i&gt;).  Click &quot;Continue&quot; 
            below when you have the signed transaction on this computer.  
            &lt;br&gt;&lt;br&gt;
            &lt;b&gt;NOTE:&lt;/b&gt; The USB drive only ever holds public transaction
            data that will be broadcast to the network.  This data may be 
            considered privacy-sensitive, but does &lt;u&gt;not&lt;/u&gt; compromise
            the security of your wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1278"/>
        <source>
            You have chosen to create the previous transaction but not sign 
            it or broadcast it, yet.  You can save the unsigned 
            transaction to file, or copy&amp;paste from the text box.  
            You can use the following window (after clicking &quot;Continue&quot;) to 
            sign and broadcast the transaction when you are ready</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>ReviewOfflineTxPage</name>
    <message>
        <location filename="Wizards.py" line="423"/>
        <source>Review Offline Transaction</source>
        <translation>Αναθεώρηση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="425"/>
        <source>Step 2: Review Offline Transaction</source>
        <translation>Βήμα 2: Αναθεώρηση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
</context>
<context>
    <name>SelectWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="115"/>
        <source>No Wallets!</source>
        <translation>Δεν υπάρχουν πορτοφόλια!</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="115"/>
        <source>There are no wallets to select from.  Please create or import a wallet first.</source>
        <translation>Δεν υπάρχουν πορτοφόλια απο τα οποία να επιλέξετε από. Παρακαλείστε να δημιουργήσετε ή να εισάγετε ένα πορτοφόλι πρώτα.</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="159"/>
        <source>Wallet ID:</source>
        <translation>Ταυτότητα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="160"/>
        <source>Name:</source>
        <translation>Όνομα:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="161"/>
        <source>Description:</source>
        <translation>Περιγραφή:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="162"/>
        <source>Spendable BTC:</source>
        <translation>Δαπανήσιμα BTC:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="302"/>
        <source>Source: All addresses</source>
        <translation>Πηγή: Όλες οι διευθύνσεις</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="199"/>
        <source>Coin Control</source>
        <translation>Ελέγχος Νομισμάτων</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="256"/>
        <source>Source: None selected</source>
        <translation>Πηγή: Καμία επιλογή</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="260"/>
        <source>Source: %1...</source>
        <translation>Πηγή: %1...</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="262"/>
        <source>Source: %1 Outputs</source>
        <translation>Πηγή: %1 Εξόδων</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="302"/>
        <source>Source: 0 addresses</source>
        <translation>Πηγή: 0 διευθύνσεις</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="322"/>
        <source>*Coin Control Subset*</source>
        <translation>&quot;Υποσέτ Ελέγχου Νομισμάτων&quot;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="329"/>
        <source>(available when online)</source>
        <translation>(διαθέσιμο σε απευθείας σύνδεση)</translation>
    </message>
</context>
<context>
    <name>SendBitcoinsFrame</name>
    <message>
        <location filename="TxFrames.py" line="56"/>
        <source>Transaction fees go to users who contribute computing power to keep the Bitcoin network secure, and in return they get your transaction included in the blockchain faster.  &lt;b&gt;Most transactions do not require a fee&lt;/b&gt; but it is recommended anyway since it guarantees quick processing and helps the network.</source>
        <translation>Οι αμοιβές συναλλαγής πάνε για τους χρήστες που συνεισφέρουν την υπολογιστική δύναμη για να κρατήσει το δίκτυο του Bitcoin ασφαλές, και σε αντάλλαγμα να συμπεριλάβουν την συναλλαγή σας στην αλυσίδα συναλλαγών γρηγορότερα. &lt;b&gt; Οι περισσότερες συναλλαγές δεν απαιτούν την καταβολή τέλους &lt;/b&gt;, αλλά συνιστάται ούτως ή άλλως δεδομένου ότι εγγυάται γρήγορη επεξεργασία και βοηθά το δίκτυο.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="74"/>
        <source>Use an existing address for change</source>
        <translation>Χρησιμοποιήστε μια υπάρχουσα διεύθυνση για τα ρέστα</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="75"/>
        <source>Send change to first input address</source>
        <translation>Αποστολή ρέστων στην πρώτη διεύθυνση εισόδου</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="76"/>
        <source>Specify a change address</source>
        <translation>Καθορίστε μια διεύθυνση για τα ρέστα</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="77"/>
        <source>Change:</source>
        <translation>Αλλαγή:</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="86"/>
        <source>Remember for future transactions</source>
        <translation>Θυμηθείτε το για τις μελλοντικές συναλλαγές</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="89"/>
        <source>Most transactions end up with oversized inputs and Armory will send the change to the next address in this wallet.  You may change this behavior by checking this box.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="93"/>
        <source>Guarantees that no new addresses will be created to receive change. This reduces anonymity, but is useful if you created this wallet solely for managing imported addresses, and want to keep all funds within existing addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="98"/>
        <source>You can specify any valid Bitcoin address for the change.  &lt;b&gt;NOTE:&lt;/b&gt; If the address you specify is not in this wallet, Armory will not be able to distinguish the outputs when it shows up in your ledger.  The change will look like a second recipient, and the total debit to your wallet will be equal to the amount you sent to the recipient &lt;b&gt;plus&lt;/b&gt; the change.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="105"/>
        <source>Check this box to create an unsigned transaction to be signed and/or broadcast later.</source>
        <translation>Επιλέξτε αυτό το πλαίσιο για να δημιουργήσετε μια ανυπόγραφη συναλλαγή που πρόκειται να υπογραφεί ή/και να μεταδοθεί αργότερα.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="108"/>
        <source>Create Unsigned</source>
        <translation>Δημιουργία Ανυπόγραφης</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="282"/>
        <source>Send!</source>
        <translation>Αποστολή!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="110"/>
        <source>Cancel</source>
        <translation>Ακύρωση</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="152"/>
        <source>Manually Enter &quot;bitcoin:&quot; Link</source>
        <translation>Χειροκίνητη Εισαγωγή Συνδέσμου &quot;bitcoin:&quot;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="153"/>
        <source>
         Armory does not always succeed at registering itself to handle 
         URL links from webpages and email.  
         Click this button to copy a &quot;bitcoin:&quot; link directly into Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="218"/>
        <source>&lt;b&gt;Sending from Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αποστολή από το Πορτοφόλι:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="233"/>
        <source>Send Bitcoins</source>
        <translation>Αποστολή Bitcoin</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="279"/>
        <source>Continue</source>
        <translation>Συνέχεια</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="280"/>
        <source>Click to create an unsigned transaction!</source>
        <translation>Κάντε Κλίκ για τη δημιουργία συναλλαγής εκτός σύνδεσης!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="283"/>
        <source>Click to send bitcoins!</source>
        <translation>Κάντε κλικ για να στείλετε bitcoin!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="898"/>
        <source>Invalid Address</source>
        <translation>Λάθος Διεύθυνση</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="505"/>
        <source>You have entered an invalid address. The error has been highlighted on the entrry screen.</source>
        <comment>You have entered %1 invalid addresses. The errors have been highlighted on the entry screen</comment>
        <translation>Έχετε εισάγει μια μη έγκυρη διεύθυνση. Το σφάλμα έχει επισημανθεί στην οθόνη εισαγωγής.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="516"/>
        <source>Wrong Network!</source>
        <translation>Λάθος Δίκτυο!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="516"/>
        <source>
                     Address %1 is for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
                     and the address you supplied is for the the &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="533"/>
        <source>Zero Amount</source>
        <translation>Μηδενικό Ποσόν</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="533"/>
        <source>You cannot send 0 BTC to any recipients.  &lt;br&gt;Please enter a positive amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="539"/>
        <source>Negative Value</source>
        <translation>Αρνητική Αξία</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="539"/>
        <source>You have specified a negative amount for recipient %1. &lt;br&gt;Only positive values are allowed!.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="544"/>
        <source>Too much precision</source>
        <translation>Πάρα πολύ ακρίβεια</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="544"/>
        <source>Bitcoins can only be specified down to 8 decimal places. The smallest value that can be sent is  0.0000 0001 BTC. Please enter a new amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="550"/>
        <source>Missing recipient amount</source>
        <translation>Λείπει ποσόν παραλήπτη</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="550"/>
        <source>You did not specify an amount to send!</source>
        <translation>Δεν προσδιορίσατε το ποσό αποστολής!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="554"/>
        <source>Invalid Value String</source>
        <translation>Λάθος Μορφή Τιμής</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="554"/>
        <source>The amount you specified to send to address %1 is invalid (%2).</source>
        <translation>Το ποσό που καθορίστηκε να σταλεί στην διεύθυνση %1 είναι λάθος (%2).</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="576"/>
        <source>Non-Standard to Spend</source>
        <translation>Μη-Τυπικό Ξόδεμα</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="576"/>
        <source>
                  Due to the Lockbox size (%1-of-%2) of recipient %3, spending
                  funds from this Lockbox is valid but non-standard for versions
                  of Bitcoin prior to 0.10.0. This means if your version of
                  Bitcoin is 0.9.x or below, and you try to broadcast a
                  transaction that spends from this Lockbox the transaction
                  will not be accepted. If you have version 0.10.0, but all
                  of your peers have an older version your transaction will
                  not be forwarded to the rest of the network. If you deposit
                  Bitcoins into this Lockbox you may have to wait until you
                  and at least some of your peers have upgraded to 0.10.0
                  before those Bitcoins can be spent. Alternatively, if you
                  have enough computing power to mine your own transactions,
                  or know someone who does, you can arrange to have any valid
                  but non-standard transaction included in the block chain.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="603"/>
        <source>Excessive Fee</source>
        <translation>Υπερβολικοί Φόροι</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="603"/>
        <source>
            Your specified fee results in a rate of &lt;b&gt;%1 satoshis per byte/b&gt;. 
            This is much higher than the median satoshi/byte rate of &lt;b&gt;%2 BTC&lt;/b&gt;.
            Are you &lt;i&gt;absolutely sure&lt;/i&gt; that you want to send with this
            fee?  
            &lt;br&gt;&lt;br&gt;
            If you do not want this fee, click &quot;No&quot; and then change the fee
            at the bottom of the &quot;Send Bitcoins&quot; window before trying 
            again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="617"/>
        <source>Insufficient Fee</source>
        <translation>Ανεπαρκείς Φόροι</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="617"/>
        <source>
            Your specified fee results in a rate of &lt;b&gt;%d satoshis per byte/b&gt;. 
            This is much lower than the median satoshi/byte rate of &lt;b&gt;%s BTC&lt;/b&gt;.
            Are you &lt;i&gt;absolutely sure&lt;/i&gt; that you want to send with this
            fee?  
            &lt;br&gt;&lt;br&gt;
            If you do not want this fee, click &quot;No&quot; and then change the fee
            at the bottom of the &quot;Send Bitcoins&quot; window before trying 
            again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="632"/>
        <source>Coin Selection Error</source>
        <translation>Σφάλμα Επιλογής Νομισμάτων</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="632"/>
        <source>
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="754"/>
        <source>Wallet is Locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="754"/>
        <source>Cannot sign transaction while your wallet is locked. </source>
        <translation>Δεν μπορείτε να υπογράψετε τη συναλλαγή, ενώ το πορτοφόλι σας είναι κλειδωμένο.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="898"/>
        <source>
                     You specified an invalid change address for this 
                     transcation.</source>
        <translation>
Καθορίσατε μια άκυρη διεύθυνση για τα ρέστα για αυτή
τη συναλλαγή.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="941"/>
        <source>Invalid Input</source>
        <translation>Λάθος Είσοδος</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="941"/>
        <source>Cannot compute the maximum amount because there is an error in the amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="950"/>
        <source>Insufficient funds</source>
        <translation>Ανεπαρκείς Πόροι</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="950"/>
        <source>You have specified more than your spendable balance to the other recipients and the transaction fee.  Therefore, the maximum amount for this recipient would actually be negative.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="965"/>
        <source>&lt;u&gt;&lt;/u&gt;Fills in the maximum spendable amount minus the amounts specified for other recipients and the transaction fee </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1074"/>
        <source>+ Recipient</source>
        <translation>+ Παραλήπτης</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1076"/>
        <source>- Recipient</source>
        <translation>- Αποστολέας</translation>
    </message>
</context>
<context>
    <name>SentToAddrBookModel</name>
    <message>
        <location filename="armorymodels.py" line="1408"/>
        <source>Address</source>
        <translation>Διεύθυνση</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1409"/>
        <source>Ownership</source>
        <translation>Ιδιοκτησία</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1410"/>
        <source>Times Used</source>
        <translation>Φορές Χρήσης</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1411"/>
        <source>Comment</source>
        <translation>Σχόλιο</translation>
    </message>
</context>
<context>
    <name>SetPassphraseFrame</name>
    <message>
        <location filename="WalletFrames.py" line="562"/>
        <source>Please enter a passphrase for wallet encryption.

A good passphrase consists of at least 10 or more
random letters, or 6 or more random words.
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="567"/>
        <source>New Passphrase:</source>
        <translation>Νέα Λέξη Κλειδί:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="572"/>
        <source>Again:</source>
        <translation>Ξανά:</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="607"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is non-ASCII!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξη κλειδί δεν είναι ASCII!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="611"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases do not match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξεις κλειδιά δεν ταιριάζουν!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="615"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is too short!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξη κλειδί είναι πολύ μικρή!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="619"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Η λέξεις κλειδιά ταιριάζουν!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
</context>
<context>
    <name>SignBroadcastOfflineTxFrame</name>
    <message>
        <location filename="TxFrames.py" line="1339"/>
        <source>Sign</source>
        <translation>Υπογραφή</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1340"/>
        <source>Broadcast</source>
        <translation>Μετάδοση</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1341"/>
        <source>Save file...</source>
        <translation>Αποθήκευση αρχείου...</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1342"/>
        <source>Load file...</source>
        <translation>Φόρτωση αρχείου...</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1343"/>
        <source>Copy Text</source>
        <translation>Αντιγραφή Κειμένου</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1344"/>
        <source>Copy Raw Tx (Hex)</source>
        <translation>Αντιγραφή Ωμής Συναλλαγής (Hex)</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1363"/>
        <source>Signature is Invalid!</source>
        <translation>Η υπογραφή είναι εσφαλμένη!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1374"/>
        <source>This is wallet from which the offline transaction spends bitcoins</source>
        <translation>Αυτό είναι το πορτοφόλι από το οποίο η συναλλαγή εκτός σύνδεσης ξοδεύει bitcoin</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1381"/>
        <source>The name of the wallet</source>
        <translation>Το όνομα του πορτοφολιού</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1382"/>
        <source>&lt;b&gt;Wallet Label:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Ετικέτα Πορτοφολιού:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1392"/>
        <source>&lt;b&gt;Pre-Broadcast ID:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1397"/>
        <source>Net effect on this wallet&apos;s balance</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1399"/>
        <source>&lt;b&gt;Transaction Amount:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Αριθμός Συναλλαγών:&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1402"/>
        <source>Click here for more&lt;br&gt; information about &lt;br&gt;this transaction</source>
        <translation>Κάντε κλικ εδώ για περισσότερες&lt;br&gt; πληροφορίες &lt;br&gt;σχετικά με αυτή τη συναλλαγή</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1473"/>
        <source>Inconsistent Data!</source>
        <translation>Ασυνεπή Δεδομένα!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1473"/>
        <source>This transaction contains inconsistent information.  This is probably not your fault...</source>
        <translation>Αυτή η συναλλαγή περιέχει ασυνεπείς πληροφορίες. Αυτό πιθανώς δεν είναι δικό σας σφάλμα...</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1479"/>
        <source>Wrong Network!</source>
        <translation>Λάθος Δίκτυο!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1479"/>
        <source>This transaction is actually for a different network!  Did you load the correct transaction?</source>
        <translation>Η συναλλαγή αυτή είναι στην πραγματικότητα για ένα διαφορετικό δίκτυο! Μήπως δεν φορτώσατε τη σωστή συναλλαγή;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1495"/>
        <source>No connection to Bitcoin network!</source>
        <translation>Δεν υπάρχει σύνδεση με το δίκτυο του Bitcoin!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1506"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Unrecognized!&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Μη Αναγνωρισμένο!&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1516"/>
        <source>Offline Warning</source>
        <translation>Αποσυνδεδεμένος Προειδοποίηση</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1516"/>
        <source>&lt;b&gt;Please review your transaction carefully before signing and broadcasting it!&lt;/b&gt;  The extra security of using offline wallets is lost if you do not confirm the transaction is correct!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1522"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Unsigned&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Ανυπόγραφη&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1526"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Bad Signature!&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Κακή Υπογραφή!&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1530"/>
        <source>&lt;b&gt;&lt;font color=&quot;green&quot;&gt;All Signatures Valid!&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Όλες οι Υπογραφές είναι Ορθές!&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1549"/>
        <source>Multiple Input Wallets</source>
        <translation>Πορτοφόλια Πολλαπλής Εισαγωγής</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1549"/>
        <source>Somehow, you have obtained a transaction that actually pulls from more than one wallet.  The support for handling multi-wallet signatures is not currently implemented (this also could have happened if you imported the same private key into two different wallets).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1557"/>
        <source>Unrelated Transaction</source>
        <translation>Άσχετη Συναλλαγή</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1557"/>
        <source>This transaction appears to have no relationship to any of the wallets stored on this computer.  Did you load the correct transaction?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1617"/>
        <source>[[ Unrelated ]]</source>
        <translation>[[ Άσχετο ]]</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1637"/>
        <source>Invalid Transaction</source>
        <translation>Λάθος Συναλλαγή</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1637"/>
        <source>Transaction data is invalid and cannot be shown!</source>
        <translation>Τα δεδομένα συναλλαγής είναι άκυρα και δεν μπορούν να εμφανιστούν!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1650"/>
        <source>Cannot Sign</source>
        <translation>Δεν Μπορεί να Υπογραφεί</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1650"/>
        <source>This transaction is not relevant to any of your wallets.Did you load the correct transaction?</source>
        <translation>Η συναλλαγή αυτή δεν σχετίζεται με κανένα από τα πορτοφόλια σας. Φορτώσατε τη σωστή συναλλαγή;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1656"/>
        <source>Not Signable</source>
        <translation>Μη Υπογράψιμο</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1656"/>
        <source>This is not a valid transaction, and thus it cannot be signed. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1661"/>
        <source>Already Signed</source>
        <translation>Ήδη Υπογεγραμένο</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1661"/>
        <source>This transaction has already been signed!</source>
        <translation>Η ανωτέρω συναλλαγή έχει ήδη υπογραφεί!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1667"/>
        <source>No Private Keys!</source>
        <translation>Δεν Υπάρχουν Ιδιωτικά Κλειδιά!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1667"/>
        <source>This transaction refers one of your wallets, but that wallet is a watching-only wallet.  Therefore, private keys are not available to sign this transaction.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1690"/>
        <source>Missing Change</source>
        <translation>Λείπουν Ρέστα</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1690"/>
        <source>
            This transaction has %1 recipients, and none of them
            are addresses in this wallet (for receiving change).  
            This can happen if you specified a custom change address 
            for this transaction, or sometimes happens solely by 
            chance with a multi-recipient transaction.  It could also 
            be the result of someone tampering with the transaction. 
            &lt;br&gt;&lt;br&gt;The transaction is valid and ready to be signed.  
            Please verify the recipient and amounts carefully before 
            confirming the transaction on the next screen.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1710"/>
        <source>Send Transaction</source>
        <translation>Αποστολή Συναλλαγής</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1717"/>
        <source>Wallet is Locked</source>
        <translation>Το Πορτοφόλι είναι Κλειδωμένο</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1717"/>
        <source>Cannot sign transaction while your wallet is locked. </source>
        <translation>Δεν μπορείτε να υπογράψετε τη συναλλαγή, ενώ το πορτοφόλι σας είναι κλειδωμένο.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1743"/>
        <source>No Internet!</source>
        <translation>Δεν Υπάρχει Ίντερνετ!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1736"/>
        <source>Armory lost its connection to , and cannot broadcast any transactions until it is reconnected. Please verify that  (or bitcoind) is open and synchronized with the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1743"/>
        <source>You do not currently have a connection to the Bitcoin network. If this does not seem correct, verify that  is open and synchronized with the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1754"/>
        <source>Signature Error</source>
        <translation>Σφάλμα Υπογραφής</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1754"/>
        <source>
            Not all signatures are valid.  This transaction
            cannot be broadcast.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1758"/>
        <source>Error</source>
        <translation>Σφάλμα</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1758"/>
        <source>
            There was an error processing this transaction, for reasons 
            that are probably not your fault...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1784"/>
        <source>File Remove Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1784"/>
        <source>The file could not be deleted.  If you want to delete it, please do so manually.  The file was loaded from: &lt;br&gt;&lt;br&gt;%1: </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1822"/>
        <source>Formatting Error</source>
        <translation>Σφάλμα Διαμόρφωσης</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1822"/>
        <source>The transaction data was not in a format recognized by Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1814"/>
        <source>Transaction Saved!</source>
        <translation>Η Συναλλαγή Αποθηκεύτηκε!</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1814"/>
        <source>Your transaction has been saved to the following location:

%1

It can now be broadcast from any computer running Armory in online mode.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1853"/>
        <source>Load Transaction</source>
        <translation>Φόρτωση Συναλλαγής</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1875"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Αντιγράφηκε!&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1324"/>
        <source>Copy or load a transaction from file into the text box below.  If the transaction is unsigned and you have the correct wallet, you will have the opportunity to sign it.  If it is already signed you will have the opportunity to broadcast it to the Bitcoin network to make it final.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1387"/>
        <source>A unique string that identifies an &lt;i&gt;unsigned&lt;/i&gt; transaction.  This is different than the ID that the transaction will have when it is finally broadcast, because the broadcast ID cannot be calculated without all the signatures</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1736"/>
        <source>Armory lost its connection to Bitcoin Core, and cannot broadcast any transactions until it is reconnected. Please verify that Bitcoin Core (or bitcoind) is open and synchronized with the network.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SignBroadcastOfflineTxPage</name>
    <message>
        <location filename="Wizards.py" line="430"/>
        <source>Sign/Broadcast Offline Transaction</source>
        <translation>Υπόγραφή / Μετάδοση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="432"/>
        <source>Step 3: Sign/Broadcast Offline Transaction</source>
        <translation>Βήμα 3: Υπόγραφή / Μετάδοση Συναλλαγής Εκτός Σύνδεσης</translation>
    </message>
</context>
<context>
    <name>SignatureVerificationWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="200"/>
        <source>Verify Signature</source>
        <translation>Πιστοποίηση Υπογραφής</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="201"/>
        <source>Clear All</source>
        <translation>Εκκαθάριση Όλων</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="222"/>
        <source>
      The owner of the following Bitcoin address...
      &lt;br&gt;
      &lt;blockquote&gt;
      &lt;font face=&quot;Courier&quot; size=4 color=&quot;#000060&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;
      &lt;/blockquote&gt;
      &lt;br&gt;
      ... has produced a &lt;b&gt;&lt;u&gt;valid&lt;/u&gt;&lt;/b&gt; signature for
      the following message:&lt;br&gt;
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="239"/>
        <source>Verified!</source>
        <translation>Πιστοποιήθηκε!</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="239"/>
        <source>
            %`
            &lt;hr&gt;
            &lt;blockquote&gt;
            &lt;font face=&quot;Courier&quot; color=&quot;#000060&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;
            &lt;/blockquote&gt;
            &lt;hr&gt;&lt;br&gt;
            &lt;b&gt;Please&lt;/b&gt; make sure that the address above (%2...) matches the
            exact address you were expecting.  A valid signature is meaningless 
            unless it is made
            from a recognized address!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="256"/>
        <source>Invalid Signature!</source>
        <translation>Λανθασμένη Υπογραφή!</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="256"/>
        <source>The supplied signature &lt;b&gt;is not valid&lt;/b&gt;!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="258"/>
        <source>&lt;font color=&quot;red&quot;&gt;Invalid Signature!&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SignedMessageBlockVerificationWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="312"/>
        <source>Signed Message Block:</source>
        <translation>Μπλόκ Υπογραφής Μηνυμάτων:</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="320"/>
        <source>Message:</source>
        <translation>Μύνημα:</translation>
    </message>
</context>
<context>
    <name>TreeStructure_CoinControl</name>
    <message>
        <location filename="TreeViewGUI.py" line="460"/>
        <source>Unspent Outputs</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="461"/>
        <source>RBF Eligible</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="462"/>
        <source>CPFP Outputs</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>TxInDispModel</name>
    <message>
        <location filename="armorymodels.py" line="1216"/>
        <source>Wallet ID</source>
        <translation>Ταυτότητα Πορτοφολιού:</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1217"/>
        <source>Sender</source>
        <translation>Αποστολέας</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1218"/>
        <source>Amount</source>
        <translation>Ποσό</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1219"/>
        <source>Prev. Tx Hash</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1220"/>
        <source>Index</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1221"/>
        <source>From Block#</source>
        <translation>Απο το Μπλόκ#</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1222"/>
        <source>Script Type</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1223"/>
        <source>Sequence</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1224"/>
        <source>Script</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>TxOutDispModel</name>
    <message>
        <location filename="armorymodels.py" line="1310"/>
        <source>Wallet ID</source>
        <translation>Ταυτότητα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1311"/>
        <source>Recipient</source>
        <translation>Παραλήπτης</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1312"/>
        <source>Amount</source>
        <translation>Ποσό</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1313"/>
        <source>Script Type</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>TxWizard</name>
    <message>
        <location filename="Wizards.py" line="337"/>
        <source>Offline Transaction Wizard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="381"/>
        <source>Create Unsigned Transaction</source>
        <translation>Δημιουργία Ανυπόγραφης Συναλλαγής</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="355"/>
        <source>Send!</source>
        <translation>Εστάλη!</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="369"/>
        <source>Next</source>
        <translation>Επόμενο</translation>
    </message>
</context>
<context>
    <name>VerifyPassphraseFrame</name>
    <message>
        <location filename="WalletFrames.py" line="634"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! DO NOT FORGET YOUR PASSPHRASE !!!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! ΜΗΝ ΞΕΧΑΣΕΤΕ ΤΗΝ ΦΡΑΣΗ ΠΡΟΣΒΑΣΗΣ !!!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="637"/>
        <source>&lt;b&gt;No one can help you recover you bitcoins if you forget the passphrase and don&apos;t have a paper backup!&lt;/b&gt; Your wallet and any &lt;u&gt;digital&lt;/u&gt; backups are useless if you forget it.  &lt;br&gt;&lt;br&gt;A &lt;u&gt;paper&lt;/u&gt; backup protects your wallet forever, against hard-drive loss and losing your passphrase.  It also protects you from theft, if the wallet was encrypted and the paper backup was not stolen with it.  Please make a paper backup and keep it in a safe place.&lt;br&gt;&lt;br&gt;Please enter your passphrase a third time to indicate that you are aware of the risks of losing your passphrase!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>VerifyPassphrasePage</name>
    <message>
        <location filename="Wizards.py" line="297"/>
        <source>Invalid Passphrase</source>
        <translation>Λάθος Λέξη Κλειδί</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="297"/>
        <source>You entered your confirmation passphrase incorrectly!</source>
        <translation>Έχετε εισάγει λάθος συνθηματική φράση επιβεβαίωσης!</translation>
    </message>
</context>
<context>
    <name>WalletAddrDispModel</name>
    <message>
        <location filename="armorymodels.py" line="1031"/>
        <source>&lt;u&gt;&lt;/u&gt;This is an imported address. Imported 
                               addresses are not protected by regular paper 
                               backups.  You must use the &quot;Backup Individual 
                               Keys&quot; option to protect it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1036"/>
        <source>&lt;u&gt;&lt;/u&gt;The order that this address was 
                               generated in this wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1040"/>
        <source>This address was created by Armory to 
                            receive change-back-to-self from an oversized 
                            transaction.</source>
        <translation>Αυτή η διεύθυνση δημιουργήθηκε απο το Armory για
να λάβει ρέστα απο μεγάλες
συναλλαγές.</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1061"/>
        <source>Address</source>
        <translation>Διεύθυνση</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1062"/>
        <source>Comment</source>
        <translation>Σχόλιο</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1063"/>
        <source>#Tx</source>
        <translation>#Συναλλαγή</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1064"/>
        <source>Balance</source>
        <translation>Υπόλοιπο</translation>
    </message>
</context>
<context>
    <name>WalletBackupFrame</name>
    <message>
        <location filename="WalletFrames.py" line="679"/>
        <source>&lt;b&gt;Backup Options&lt;/b&gt;</source>
        <translation>&lt;b&gt; Επιλογές αντιγράφων ασφαλείας &lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="680"/>
        <source>
         Armory wallets only need to be backed up &lt;u&gt;one time, ever.&lt;/u&gt;
         The backup is good no matter how many addresses you use. </source>
        <translation>
Για τα πορτοφόλια Armory χρειάζεται να πάρετε αντίγραφα ασφαλείας μόνο &lt;u&gt; μία φορά &lt;/u&gt;
Το αντίγραφο είναι καλό και δεν έχει σημασία πόσες διευθύνσεις χρησιμοποιείτε.</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="686"/>
        <source>Printable Paper Backup</source>
        <translation>Εκτυπώσιμο Αντίγραφο Ασφαλείας σε Χαρτί</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="688"/>
        <source>Single-Sheet (Recommended)</source>
        <translation>Ενιαίο-Φύλλο (Συνιστάται)</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="690"/>
        <source>Fragmented Backup (M-of-N)</source>
        <translation>Κατακερματισμένο Αντίγραφο Ασφαλείας (M-απο-N)</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="693"/>
        <source>Digital Backup</source>
        <translation>Ψηφιακό Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="695"/>
        <source>Unencrypted</source>
        <translation>Μη Κρυπτογραφημένο</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="697"/>
        <source>Encrypted</source>
        <translation>Κρυπτογραφημένο</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1035"/>
        <source>Export Key Lists</source>
        <translation>Εξαγωγή Λίστας Κλειδιών</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="767"/>
        <source>
         Every time you click &quot;Receive Bitcoins,&quot; a new address is generated.
         All of these addresses are generated from a single seed value, which
         is included in all backups.   Therefore, all addresses that you have
         generated so far &lt;b&gt;and&lt;/b&gt; will ever be generated with this wallet, 
         are protected by this backup! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="774"/>
        <source>
         &lt;i&gt;This wallet &lt;u&gt;does not&lt;/u&gt; currently have any imported
         addresses, so you can safely ignore this feature!&lt;/i&gt;
         When imported addresses are present, backups only protects those
         imported before the backup was made.  You must replace that
         backup if you import more addresses! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="781"/>
        <source>
         Lost/forgotten passphrases are, &lt;b&gt;by far&lt;/b&gt;, the most common
         reason for users losing bitcoins.  It is critical you have
         at least one backup that works if you forget your wallet
         passphrase. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="787"/>
        <source>
         USB drives and CD/DVD disks are not intended for long-term storage.
         They will &lt;i&gt;probably&lt;/i&gt; last many years, but not guaranteed
         even for 3-5 years.   On the other hand, printed text on paper will
         last many decades, and useful even when thoroughly faded. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="793"/>
        <source>
         The ability to look at a backup and determine if
         it is still usable.   If a digital backup is stored in a safe
         deposit box, you have no way to verify its integrity unless
         you take a secure computer/device with you.  A simple glance at
         a paper backup is enough to verify that it is still intact. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="800"/>
        <source>
         If multiple pieces/fragments are required to restore this wallet.
         For instance, encrypted backups require the backup
         &lt;b&gt;and&lt;/b&gt; the passphrase.  This feature is only needed for those
         concerned about physical security, not just online security.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="808"/>
        <source>Protects All Future Addresses</source>
        <translation>Προστατεύει Όλες τις Μελλοντικές Διευθύνσεις</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="809"/>
        <source>Protects Imported Addresses</source>
        <translation>Προστατεύει τις Εισηγμένες Διευθύνσεις</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="810"/>
        <source>Forgotten Passphrase</source>
        <translation>Ξεχασμένη Φράση Πρόσβασης</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="811"/>
        <source>Long-term Durability</source>
        <translation>Μακροχρόνια Αντοχή</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="812"/>
        <source>Visual Integrity</source>
        <translation>Οπτική Ακεραιότητα</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="813"/>
        <source>Multi-Point Protection</source>
        <translation>Πολλαπλό Σημείο Προστασίας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="841"/>
        <source>Create Backup</source>
        <translation>Δημιουργία Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="876"/>
        <source>
            When imported addresses are present, backups only protects those
            imported before the backup was made!  You must replace that
            backup if you import more addresses!
            &lt;i&gt;Your wallet &lt;u&gt;does&lt;/u&gt; contain imported addresses&lt;i&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="884"/>
        <source>
         &lt;b&gt;Backup Options for Wallet &quot;%1&quot; (%2)&lt;/b&gt;</source>
        <translation>
 &lt;b&gt;Επιλογές Αντιγράφου για το πορτοφόλι &quot;%1&quot; (%2)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="897"/>
        <source>
               Paper backups protect every address ever generated by your
               wallet. It is unencrypted, which means it needs to be stored
               in a secure place, but it will help you recover your wallet
               if you forget your encryption passphrase!
               &lt;br&gt;&lt;br&gt;
               &lt;b&gt;You don't need a printer to make a paper backup!
               The data can be copied by hand with pen and paper.&lt;/b&gt;
               Paper backups are preferred to digital backups, because you
               know the paper backup will work no matter how many years (or
               decades) it sits in storage.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="908"/>
        <source>
               Digital backups can be saved to an external hard-drive or
               USB removable media.  It is recommended you make a few
               copies to protect against &quot;bit rot&quot; (degradation). &lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="912"/>
        <source>
               &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt; Do not save an unencrypted digital
               backup to your primary hard drive!&lt;/b&gt;
               Please save it &lt;i&gt;directly&lt;/i&gt; to the backup device.
               Deleting the file does not guarantee the data is actually
               gone!  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="918"/>
        <source>
               &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt; It is critical that you have at least
               one unencrypted backup!&lt;/b&gt;  Without it, your bitcoins will
               be lost forever if you forget your passphrase!  This is &lt;b&gt;
               by far&lt;/b&gt; the most common reason users lose coins!  Having
               at least one paper backup is recommended.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="924"/>
        <source>
               View and export invidivual addresses strings,
               public keys and/or private keys contained in your wallet.
               This is useful for exporting your private keys to be imported into
               another wallet app or service.
               &lt;br&gt;&lt;br&gt;
               You can view/backup imported keys, as well as unused keys in your
               keypool (pregenerated addresses protected by your backup that
               have not yet been used). </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="938"/>
        <source>Single-Sheet Paper Backup</source>
        <translation>Μονόφυλλο Αντίγραφο Ασφαλείας σε Χαρτί</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="947"/>
        <source>Fragmented Paper Backup</source>
        <translation>Κατακερματισμένο Χάρτινο Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="956"/>
        <source>Unencrypted Digital Backup</source>
        <translation>Μη κρυπτογραφημένο Ψηφιακό Αντίγραφο Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="965"/>
        <source>Encrypted Digital Backup</source>
        <translation>Κρυπτογράφηση Ψηφιακού Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1014"/>
        <source>Create Paper Backup</source>
        <translation>Δημιουργία Χάρτινου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1023"/>
        <source>Create Digital Backup</source>
        <translation>Δημιουργία Ψηφιακού Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1046"/>
        <source>Unlocking Wallet</source>
        <translation>Ξεκλειδωμα Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1073"/>
        <source>Unlock Failed</source>
        <translation>Το Ξεκλείδωμα Απέτυχε</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1067"/>
        <source>
                     Wallet was not be unlocked.  The public keys and addresses
                     will still be shown, but private keys will not be available
                     unless you reopen the dialog with the correct passphrase.</source>
        <translation>
Το πορτοφόλι δεν ξεκλειδώθηκε. Τα δημόσια κλειδιά και οι διευθύνσεις
θα εμφανίζονται, αλλά τα ιδιωτικά κλειδιά δεν θα είναι διαθέσιμα
εκτός και αν ξανα ανοίξετε το πλαίσιο διαλόγου με την σωστή λέξη κλειδί.</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1073"/>
        <source>
                     &apos;Wallet could not be unlocked to display individual keys.</source>
        <translation>
Το πορτοφόλι δεν μπορούσε να ξεκλειδωθεί με τα ξεχωριστά κλειδιά.</translation>
    </message>
</context>
<context>
    <name>WalletComparisonClass</name>
    <message>
        <location filename="WalletMirrorDialog.py" line="73"/>
        <source>Mirroring wallet %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletMirrorDialog.py" line="84"/>
        <source>Synchronizing wallet %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletMirrorDialog.py" line="91"/>
        <source>Checking imports for wallet %s</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>WalletCreationPage</name>
    <message>
        <location filename="Wizards.py" line="247"/>
        <source>Invalid Target Compute Time</source>
        <translation>Λάθος Στόχος Χρόνος Υπολογισμού.</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="247"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation>Εισάγατε Λάθος Στόχο Χρόνο Υπολογισμού.

Εισάγετε: &lt;Αριθμό&gt; (ms, s)</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="251"/>
        <source>Invalid Max Memory Usage</source>
        <translation>Λάθος Μέγεθος Χρήσης Μνήμης</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="251"/>
        <source>You entered Max Memory Usag incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation>Εισάγατε Λάθος Μέγεθος Χρήσης Μνήμης

Εισάγετε: &lt;Αριθμό&gt; (ms, s)</translation>
    </message>
</context>
<context>
    <name>WalletWizard</name>
    <message>
        <location filename="Wizards.py" line="80"/>
        <source>Wallet Creation Wizard</source>
        <translation>Οδηγός Δημιουργίας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="148"/>
        <source>Wallet Backup Warning</source>
        <translation>Προειδοποίηση Αντιγράφου Ασφαλείας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="148"/>
        <source>&lt;qt&gt;
               You have not made a backup for your new wallet.  You only have 
               to make a backup of your wallet &lt;u&gt;one time&lt;/u&gt; to protect 
               all the funds held by this wallet &lt;i&gt;any time in the future&lt;/i&gt;
               (it is a backup of the signing keys, not the coins themselves).
               &lt;br&gt;&lt;br&gt;
               If you do not make a backup, you will &lt;u&gt;permanently&lt;/u&gt; lose
               the money in this wallet if you ever forget your password, or 
               suffer from hardware failure.
               &lt;br&gt;&lt;br&gt;
               Are you sure that you want to leave this wizard without backing 
               up your wallet?&lt;/qt&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="186"/>
        <source>Creating Wallet</source>
        <translation>Δημιουργείτε το Πορτοφόλι</translation>
    </message>
</context>
<context>
    <name>WizardCreateWatchingOnlyWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="1091"/>
        <source>
               Your wallet has been created and is ready to be used.  It will
               appear in the &quot;&lt;i&gt;Available Wallets&lt;/i&gt;&quot; list in the main window.  
               You may click &quot;&lt;i&gt;Finish&lt;/i&gt;&quot; if you do not plan to use this 
               wallet on any other computer.
               &lt;br&gt;&lt;br&gt;
               A &lt;b&gt;watching-only wallet&lt;/b&gt; behaves exactly like a a regular 
               wallet, but does not contain any signing keys.  You can generate 
               addresses and confirm receipt of payments, but not spend or move 
               the funds in the wallet.  To move the funds, 
               use the &quot;&lt;i&gt;Offline Transactions&lt;/i&gt;&quot; button on the main 
               window for directions (which involves bringing the transaction 
               to this computer for a signature).  Or you can give the
               watching-only wallet to someone who needs to monitor the wallet
               but should not be able to move the money.
               &lt;br&gt;&lt;br&gt;
               Click the button to save a watching-only copy of this wallet.
               Use the &quot;&lt;i&gt;Import or Restore Wallet&lt;/i&gt;&quot; button in the
               upper-right corner</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>context</name>
    <message>
        <location filename="qtdialogs.py" line="12163"/>
        <source>Invalid Code</source>
        <translation>Λάθος Κωδικός</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12163"/>
        <source>
            You didn't enter a full SecurePrintâ¢ code.  This
            code is needed to decrypt your backup file.</source>
        <translation>
Δεν εισάγατε έναν πλήρη SecurePrintâ¢ κωδικό. Αυτός
ο κωδικός χρειάζεται για την αποκρυπτογράφηση του αρχείου με το αντίγραφο ασφαλείας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12174"/>
        <source>Bad SecurePrintâ¢ Code</source>
        <translation>Κακός SecurePrintâ¢ Κωδικός</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12168"/>
        <source>
            The SecurePrintâ¢ code you entered has an error
            in it.  Note that the code is case-sensitive.  Please verify
            you entered it correctly and try again.</source>
        <translation>
Ο κωδικός SecurePrintââ¢ που εισάγατε έχει ένα λάθος.
Σημειώστε οτι ο κωδικός έιναι ευαίσθητος σε μικρά-κεφαλαία. Παρακαλώ
πιστοποιήστε οτι τον εισάγατε σωστά και προσπαθήστε ξανά.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12174"/>
        <source>
         The SecurePrintâ¢ code you entered has unrecognized characters
         in it.  %1 Only the following characters are allowed: %2</source>
        <translation>
Ο κωδικός SecurePrintâ¢ που εισάγατε έχει μη αναγνωρισμένους χαρακτήρες.
Μόνο %1 των ακόλουθων χαρακτήρων επιτρέπεται: %2</translation>
    </message>
</context>
<context>
    <name>dlgChangeOwner</name>
    <message>
        <location filename="qtdialogs.py" line="2396"/>
        <source>This wallet is mine</source>
        <translation>Το πορτοφόλι είναι δικό μου</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2399"/>
        <source>
               The funds in this wallet are currently identified as
               belonging to &lt;b&gt;&lt;i&gt;you&lt;/i&gt;&lt;/b&gt;.  As such, any funds
               available to this wallet will be included in the total
               balance displayed on the main screen.  


               If you do not actually own this wallet, or do not wish
               for its funds to be considered part of your balance,
               uncheck the box below.  Optionally, you can include the
               name of the person or organization that does own it.</source>
        <translation>
Τα χρήματα σε αυτό το πορτοφόλι χαρακτηρίζονται ώς
δικά &lt;b&gt;&lt;i&gt;σας&lt;/i&gt;&lt;/b&gt;. Έτσι ότι ποσά
είναι διαθέσιμα στο πορτοφόλι αυτό θα συμπεριληφθούν στο σύνολο
των χρημάτων που εμφανίζονται στην αρχική οθόνη.


Αν δέν σας ανήκει αυτό το πορτοφόλι, η δεν θέλετε
τα χρήματα του να θεωρούνται κομμάτι του συνόλου,
αποεπιλέξτε το παρακάτω κουτί. Εναλλακτικά, μπορείτε να συμπεριλάβετε το
όνομα του ατόμου ή του οργανισμού στον οποίο ανήκει.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2419"/>
        <source>
               The funds in this wallet are currently identified as
               belonging to &lt;i&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/i&gt;.  If these funds are actually
               yours, and you would like the funds included in your balance in
               the main window, please check the box below.

</source>
        <translation>
Τα χρήματα σε αυτό το πορτοφόλι ανήκουν 
στον &lt;i&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/i&gt;. Αν αυτά τα ποσά έιναι δικά
σας, και θέλετε να συμπεριληφθούν στα χρηματά σας στο
κεντρικό παράθυρο, παρακαλώ πατήστε το παρακάτω κουμπί.

</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2428"/>
        <source>
               You might choose this option if you keep a full
               wallet on a non-internet-connected computer, and use this
               watching-only wallet on this computer to generate addresses
               and monitor incoming transactions.</source>
        <translation>
Μπορείτε να επιλέξετε αυτή την επιλογή αν έχετε ένα πλήρες
πορτοφόλι σε έναν υπολογιστή εκτός του διαδικτύου και χρησιμοποιείτε αυτό
το πορτοφόλι μόνο για προβολή και δημιουργία διευθύνσεων
και την παρακολούθηση εισερχόμενων συναλλαγών.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2439"/>
        <source>Wallet owner (optional):</source>
        <translation>Κάτοχος Πορτοφολιού (προαιρετικό)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2447"/>
        <source>Set Wallet Owner</source>
        <translation>Καθορίστε τον Κάτοχο του Πορτοφολιού</translation>
    </message>
</context>
<context>
    <name>dlgWarn</name>
    <message>
        <location filename="qtdefines.py" line="510"/>
        <source>&amp;Yes</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="511"/>
        <source>&amp;No</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="519"/>
        <source>&amp;Cancel</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="521"/>
        <source>&amp;OK</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="572"/>
        <source>Do not show this message again</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="575"/>
        <source>Do not ask again</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="578"/>
        <source>Do not show this warning again</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="qtdialogs.py" line="2454"/>
        <source>Careful!</source>
        <translation>Προσοχή!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2454"/>
        <source>Armory is not online yet, and will eventually need to be online toaccess any funds sent to your wallet.  Please &lt;u&gt;&lt;b&gt;do not&lt;/b&gt;&lt;/u&gt;receive Bitcoins to your Armory wallets until you have successfullygotten online &lt;i&gt;at least one time&lt;/i&gt;.&lt;br&gt;&lt;br&gt;Armory is still beta software, and some users report difficultyever getting online.&lt;br&gt;&lt;br&gt;Do you wish to continue?</source>
        <translation>Το Armory δεν έχει συνδεθεί ακόμα, και θα χρειαστεί να συνδεθεί πρίν μπορέσετε να προσπελάσετε τα χρήματα που έχουν σταλει στο πορτοφόλι σας. Παρακαλώ &lt;u&gt;&lt;b&gt;μην&lt;/b&gt;&lt;/u&gt; λάβετε Bitcoins στο Armory πορτοφόλι σας αν δεν έχετε συνδεθεί επιτυχώς &lt;i&gt;τουλάχιστον μια φορά&lt;/i&gt;.&lt;br&gt;&lt;br&gt; Το Armory είναι ακόμα σε δοκιμαστική έκδοση και κάποιοι χρήστες δηλώνουν δυσκολία στην σύνδεση.&lt;br&gt;&lt;br&gt;Θέλετε να συνεχίσετε;</translation>
    </message>
</context>
<context>
    <name>parent</name>
    <message>
        <location filename="qtdefines.py" line="185"/>
        <source>Standard User</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="187"/>
        <source>Advanced User</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="189"/>
        <source>Expert User</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2487"/>
        <source>This is not your wallet!</source>
        <translation>Αυτό δεν είναι το πορτοφόλι σας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2473"/>
        <source>You are getting an address for a wallet thatdoes not appear to belong to you.  Any money sent to thisaddress will not appear in your total balance, and cannotbe spent from this computer.&lt;br&gt;&lt;br&gt;If this is actually your wallet (perhaps you maintain the fullwallet on a separate computer), then please change the&quot;Belongs To&quot; field in the wallet-properties for this wallet.</source>
        <translation>Παίρνετε μια διεύθυνση για ένα πορτοφόλι που πιθανότατα δεν ανήκει σε σας, Τα ποσά που περιέχει δεν θα φανούν στο σύνολο της διευθυνσης σας και δεν μπορείτε να τα ξοδέψετε από αυτόν τον υπολογιστή. &lt;br&gt;&lt;br&gt;Αν αυτό είναι το πορτοφόλι σας (μπορεί εσείς απλά να διατηρείτε το πορτοφόλι σε έναν άλλο υπολογιστή), τότε παρακαλώ αλλάξτε την επιλογή &quot;Ανήκει στον&quot; στις ιδιότητες του πορτοφολιού.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2487"/>
        <source>Do not show this warning again</source>
        <translation>Να μήν εμφανίζεται το μύνημα προειδοποίησης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2487"/>
        <source>You are getting an address for a wallet that you have specified belongs to you, but you cannot actually spend the funds from this computer.  This is usually the case when you keep the full wallet on a separate computer for security purposes.&lt;br&gt;&lt;br&gt;If this does not sound right, then please do not use the following address.  Instead, change the wallet properties &quot;Belongs To&quot; field to specify that this wallet is not actually yours.</source>
        <translation>Παίρνετε μια διεύθυνση για ένα πορτοφόλι που έχετε ορίσει οτι ανήκει σε σας, αλλά δεν μπορείτε να ξοδέψετε τα χρήματα από αυτόν τον υπολογιστή. Αυτό συνήθως συμβαίνει όταν κρατάτε το πλήρες πορτοφόλι σε ένα ξεχωριστό υπολογιστή για λόγους ασφαλείας. &lt;br&gt;&lt;br&gt; Αν αυτό δεν ακούγεται σωστό, τότε παρακαλούμε να μην χρησιμοποιήσετε την ακόλουθη διεύθυνση. Αντ &apos;αυτού, να αλλάξετε τις ιδιότητες του πορτοφολιού &quot;Σε Ποιον Ανήκει&quot; για να καθορίσετε ότι αυτό το πορτοφόλι δεν είναι πραγματικά δικό σας.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7467"/>
        <source>Unlock Paper Backup</source>
        <translation>Ξεκλείδωμα Χάρτινου Αντιγράφου Ασφαλείας</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7470"/>
        <source>Unlock Failed</source>
        <translation>Το Ξεκλείδωμα Απέτυχε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7470"/>
        <source>
            The wallet could not be unlocked.  Please try again with
            the correct unlock passphrase.</source>
        <translation>
Το πορτοφόλι δεν μπορούσε να ξεκλειδωθεί. Παρακαλώ δοκιμάστε ξανά
με τη σωστή φράση ξεκλειδώματος.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7480"/>
        <source>
         If the backup was printed with SecurePrintâ¢, please
         make sure you wrote the SecurePrintâ¢ code on the
         printed sheet of paper. Note that the code &lt;b&gt;&lt;u&gt;is&lt;/u&gt;&lt;/b&gt;
         case-sensitive!</source>
        <translation>
Αν το αντίγραφο ασφαλείας δημιουργήθηκε με το SecurePrintâ¢, παρακαλώ
να βεβαιωθείτε ότι γράψατε τον κωδικό SecurePrintâ¢ στο
εκτυπωμένο χαρτί. Σημειώστε οτι ο κωδικός &lt;b&gt;&lt;u&gt;is&lt;/u&gt;&lt;/b&gt;
είναι ευαίσθητος σε μικρά-κεφαλαία!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7487"/>
        <source>
         If the backup was created with SecurePrintâ¢, please
         make sure you wrote the SecurePrintâ¢ code on each
         fragment (or stored with each file fragment). The code is the
         same for all fragments.</source>
        <translation>
Αν το αντίγραφο ασφαλείας δημιουργήθηκε με το SecurePrintâ¢, παρακαλώ
να βεβαιωθείτε ότι γράψατε τον σωστό κωδικό SecurePrintâ¢ για κάθε
κομμάτι (ή αποθηκευμένο κομμάτι αρχείου). Ο κώδικας είναι
ο ίδιος για όλα τα κομμάτια.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7493"/>
        <source>Verify Your Backup!</source>
        <translation>Πιστοποιήστε Tο Εφεδρικό Aντίγραφο Ασφαλείας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7493"/>
        <source>
      &lt;b&gt;&lt;u&gt;Verify your backup!&lt;/u&gt;&lt;/b&gt;
      &lt;br&gt;&lt;br&gt;
      If you just made a backup, make sure that it is correct!
      The following steps are recommended to verify its integrity:
      &lt;br&gt;
      &lt;ul&gt;
         &lt;li&gt;Verify each line of the backup data contains &lt;b&gt;9 columns&lt;/b&gt;
         of &lt;b&gt;4 letters each&lt;/b&gt; (excluding any &quot;ID&quot; lines).&lt;/li&gt;
         &lt;li&gt;%1&lt;/li&gt;
         &lt;li&gt;Use Armory's backup tester to test the backup before you
             physically secure it.&lt;/li&gt;
      &lt;/ul&gt;
      &lt;br&gt;
      Armory has a backup tester that uses the exact same
      process as restoring your wallet, but stops before it writes any
      data to disk.  Would you like to test your backup now?
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7629"/>
        <source>Bad Public Key</source>
        <translation>Κακό δημόσιο κλειδί</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7629"/>
        <source>Public key data was not recognized</source>
        <translation>Το δημόσιο κλειδί δεν αναγνωρίστηκε</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7638"/>
        <source>Bad Signature</source>
        <translation>Κακή Υπογραφή</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7638"/>
        <source>Signature data is malformed!</source>
        <translation>Τα δεδομένα υπογραφής είναι εσφαλμένα!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7646"/>
        <source>Address Mismatch</source>
        <translation>Ασυμφωνία Διεύθυνσης</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7646"/>
        <source>!!! The address included in the signature block does not
         match the supplied public key!  This should never happen,
         and may in fact be an attempt to mislead you !!!</source>
        <translation>!!! Η διεύθυνση που περιλαμβάνεται με το μπλόκ που έχει υπογραφεί δεν
ταιριάζει με το δημόσιο κλειδί! Αυτό δεν πρέπει να συμβαίνει,
και μπορεί να αποτελεί μια προσπάθεια εξαπάτησης !!!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8648"/>
        <source>Select</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8654"/>
        <source>No wallets!</source>
        <translation>Δεν υπάρχουν πορτοφόλια!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8654"/>
        <source>You have no wallets so
            there is no address book to display.</source>
        <translation>Δεν έχετε πορτοφόλι οπότε
δεν υπάρχει βιβλίο διευθύνσεων προς εμφάνιση.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8665"/>
        <source>Select from Address Book</source>
        <translation>Επιλογή απο το Βιβλίο Διευθύνσεων</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13697"/>
        <source>Recovery Test</source>
        <translation>Δοκιμή Επαναφοράς</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13697"/>
        <source>
         From the data you entered, Armory calculated the following
         wallet ID: &lt;font color=&quot;blue&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;
         &lt;br&gt;&lt;br&gt;
         Does this match the wallet ID on the backup you are
         testing?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13725"/>
        <source>Bad Backup!</source>
        <translation>Κακό Αντίγραφο Ασφαλείας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13705"/>
        <source>
            If this is your only backup and you are sure that you entered
            the data correctly, then it is &lt;b&gt;highly recommended you stop using
            this wallet!&lt;/b&gt;  If this wallet currently holds any funds,
            you should move the funds to a wallet that &lt;u&gt;does&lt;/u&gt;
            have a working backup.
            &lt;br&gt;&lt;br&gt; &lt;br&gt;&lt;br&gt;
            Wallet ID of the data you entered: %1 &lt;br&gt; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13738"/>
        <source>Backup is Good!</source>
        <translation>Το Αντίγραφο Ασφαλείας σας είναι Καλό!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13715"/>
        <source>
            &lt;b&gt;Your backup works!&lt;/b&gt;
            &lt;br&gt;&lt;br&gt;
            The wallet ID is computed from a combination of the root
            private key, the &quot;chaincode&quot; and the first address derived
            from those two pieces of data.  A matching wallet ID
            guarantees it will produce the same chain of addresses as
            the original.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13725"/>
        <source>
            If you are sure that you entered the backup information
            correctly, then it is &lt;b&gt;highly recommended you stop using
            this wallet!&lt;/b&gt;  If this wallet currently holds any funds,
            you should move the funds to a wallet that &lt;u&gt;does&lt;/u&gt;
            have a working backup.
            &lt;br&gt;&lt;br&gt;
            Computed wallet ID: %1 &lt;br&gt;
            Expected wallet ID: %2 &lt;br&gt;&lt;br&gt;
            Is it possible that you loaded a different backup than the
            one you just made? </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13738"/>
        <source>
            Your backup works!
            &lt;br&gt;&lt;br&gt;
            The wallet ID computed from the data you entered matches
            the expected ID.  This confirms that the backup produces
            the same sequence of private keys as the original wallet!
            &lt;br&gt;&lt;br&gt;
            Computed wallet ID: %1 &lt;br&gt;
            Expected wallet ID: %2 &lt;br&gt;
            &lt;br&gt;
            </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13753"/>
        <source>
         Please make sure that any printed backups you create  (excluding any &quot;ID&quot; lines) have &lt;b&gt;nine
         columns&lt;/b&gt; of four letters each
         each.
         If you just made a paper backup, it is important that you test it
         to make sure that it was printed or copied correctly.  Most importantly,
         </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13762"/>
        <source>Test Your Backup!</source>
        <translation>Δοκιμή Του Αντιγράφου Ασφαλείας σας!</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13762"/>
        <source>
      </source>
        <translation> 
 </translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="613"/>
        <source>Export Lockbox Definition</source>
        <translation>Εξάγετε τους Ορισμούς Κλειδώματος</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="614"/>
        <source>
      &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;IMPORTANT:&lt;/font&gt;
      All labels and descriptions you have entered for 
      this lockbox are included in this text block below!&lt;/b&gt;  
      &lt;br&gt;&lt;br&gt;
      Before you send this to any other parties, &lt;em&gt;please&lt;/em&gt; confirm
      that you have not entered any sensitive or embarassing information 
      into any of the lockbox fields.  Each lockbox has a name and 
      extended information, as well as a comment for each public key.
      &lt;br&gt;&lt;br&gt;
      All parties or devices that have [partial] signing authority
      over this lockbox need to import this data into their local 
      lockbox manager in order to use it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13754"/>
        <source>
         Please make sure that any printed backups you create  (excluding any &quot;ID&quot; lines) have &lt;b&gt;nine
         columns&lt;/b&gt; of four letters each.
         If you just made a paper backup, it is important that you test it
         to make sure that it was printed or copied correctly.  Most importantly,
         </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>self.main</name>
    <message>
        <location filename="armorymodels.py" line="496"/>
        <source>&lt;a href=edtBlock&gt;Block:&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="502"/>
        <source>&lt;a href=edtDate&gt;Date:&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="508"/>
        <source>&lt;a href=goToTop&gt;Top&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="128"/>
        <source>Address Type: </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="142"/>
        <source>&lt;u&gt;&lt;font color=&apos;blue&apos;&gt;%1&lt;/font&gt;&lt;/u&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>self.parent_qobj</name>
    <message>
        <location filename="TreeViewGUI.py" line="350"/>
        <source>Used Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="351"/>
        <source>Change Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="352"/>
        <source>Unused Addresses</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>wizard</name>
    <message>
        <location filename="Wizards.py" line="218"/>
        <source>Shuffle a deck of cards</source>
        <translation>Ανακάτεμα αριθμητικών καρτών</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="221"/>
        <source>Step 1: Add Manual Entropy</source>
        <translation>Βήμα 1: Προσθήκη Χειροκίνητης Εντροπίας</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="222"/>
        <source>
            Use a deck of cards to get a new random number for your wallet.
            </source>
        <translation>
Χρήση αριθμητικών καρτών για να λάβετε ένα νέο τυχαίο αριθμό για το πορτοφόλι σας.</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="238"/>
        <source>Step 1: Create Wallet</source>
        <translation>Βήμα 1: Δημιουργία Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="239"/>
        <source>
            Create a new wallet for managing your funds.
            The name and description can be changed at any time.</source>
        <translation>
Δημιουργήστε ένα νέο πορτοφόλι για την διαχείρηση των κεφαλαίων σας.
Το όνομα και η περιγραφή μπορεί να αλλάξει ανα πάσα στιγμή.</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="267"/>
        <source>Set Passphrase</source>
        <translation>Ορισμός Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="270"/>
        <source>Step 2: Set Passphrase</source>
        <translation>Βήμα 2: Ορισμός Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="285"/>
        <source>Verify Passphrase</source>
        <translation>Επιβεβαίωση Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="289"/>
        <source>Step 3: Verify Passphrase</source>
        <translation>Βήμα 3: Επιβεβαίωση Λέξης Κλειδιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="306"/>
        <source>Backup Wallet</source>
        <translation>Αντίγραφο Ασφαλείας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="310"/>
        <source>Step 4: Backup Wallet</source>
        <translation>Βήμα 4: Αντίγραφο Ασφαλείας Πορτοφολιού</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="321"/>
        <source>Create Watching-Only Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="324"/>
        <source>Step 5: Create Watching-Only Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="402"/>
        <source>Create Transaction</source>
        <translation>Δημιουργία Συναλλαγής</translation>
    </message>
</context>
<context>
    <name>wndw</name>
    <message>
        <location filename="qtdefines.py" line="248"/>
        <source>Offline</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="250"/>
        <source>Watching-Only</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="252"/>
        <source>Encrypted</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="254"/>
        <source>No Encryption</source>
        <translation type="unfinished"/>
    </message>
</context>
</TS>