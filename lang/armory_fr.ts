<?xml version="1.0" ?><!DOCTYPE TS><TS language="fr" sourcelanguage="" version="2.0">
<context>
    <name>@default</name>
    <message>
        <location filename="ArmoryQt.py" line="565"/>
        <source>Not Online</source>
        <translation>N&apos;est pas en ligne</translation>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="63"/>
        <source>Block: #%1 | Tx: #%2 | TxOut: #%3</source>
        <translation>Bloc : no %1 | Transac. : no %2 | Sortie transac. : no %3</translation>
    </message>
    <message>
        <location filename="WalletMirrorDialog.py" line="73"/>
        <source>Mirroring wallet %1</source>
        <translation>Copie miroir du porte-monnaie %1</translation>
    </message>
    <message>
        <location filename="WalletMirrorDialog.py" line="84"/>
        <source>Synchronizing wallet %1</source>
        <translation>Synchronisation du porte-monnaie %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3880"/>
        <source>Add comment</source>
        <translation>Ajouter un commentaire</translation>
    </message>
</context>
<context>
    <name>AddressTreeModel</name>
    <message>
        <location filename="TreeViewGUI.py" line="605"/>
        <source>Address</source>
        <translation>Adresse</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="606"/>
        <source>Comment</source>
        <translation>Commentaire</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="607"/>
        <source>Tx Count</source>
        <translation>Nombre de transactions</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="608"/>
        <source>Balance</source>
        <translation>Solde</translation>
    </message>
</context>
<context>
    <name>AddressTypeSelectDialog</name>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="24"/>
        <source>P2PKH Address</source>
        <translation>Adresse P2PKH</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="25"/>
        <source>Legacy Armory address type. Backwards compatible.</source>
        <translation>Type d&apos;adresse Armory hérité. Rétrocompatible.</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="40"/>
        <source>P2SH-P2WPKH address</source>
        <translation>Adresse P2SH-P2WPKH</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="41"/>
        <source>P2WPKH (SegWit script) nested in P2SH script. Any wallet can pay to this address. Only wallets supporting SegWit can spend from it.</source>
        <translation>P2WPKH (script SegWit) intégré dans un script P2SH. N&apos;importe quel porte-monnaie peut payer vers cette adresse. Seuls les porte-monnaie prenant en charge SegWit peuvent l&apos;utiliser pour une dépense.</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="61"/>
        <source>P2SH-P2PK address</source>
        <translation>Adresse P2SH-P2PK</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="62"/>
        <source>Compressed P2PK script nested in P2SH output. Any wallet can pay to this address. Only Armory 0.96+ can spend from it.&lt;br&gt;&lt;br&gt;This format allow for more efficient transaction space use, resulting in smaller inputs and lower fees.</source>
        <translation>Un script P2PK compressé intégré dans une sortie P2SH. N&apos;importe quel porte-monnaie peut payer vers cette adresse. Seul Armory 0.96+ peut l&apos;utiliser pour une dépense.&lt;br&gt;&lt;br&gt;Ce format permet une utilisation plus efficace de l&apos;espace transactionnel, permettant des entrées plus petites et des frais moindres.</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="86"/>
        <source>Apply</source>
        <translation>Appliquer</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="87"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="96"/>
        <source>Select Address Type</source>
        <translation>Sélectionner le type d&apos;adresse</translation>
    </message>
</context>
<context>
    <name>AdvancedOptionsFrame</name>
    <message>
        <location filename="WalletFrames.py" line="412"/>
        <source>Armory will test your system's speed to determine the most challenging encryption settings that can be applied in a given amount of time.  High settings make it much harder for someone to guess your passphrase.  This is used for all encrypted wallets, but the default parameters can be changed below.
</source>
        <translation>Armory testera la vitesse de votre système afin de déterminer les paramètres de chiffrement les plus exigeants qui peuvent être utilisés dans un temps donné. Des paramètres élevés rendent la tâche encore plus difficile pour quelqu&apos;un qui tenterait de deviner votre phrase de passe. Ils sont utilisés pour tous les porte-monnaie chiffrés, mais les paramètres par défaut peuvent être changés ci-dessous.
</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="419"/>
        <source>This is the amount of time it will take for your computer to unlock your wallet after you enter your passphrase. (the actual time used will be less than the specified time, but more than one half of it).  </source>
        <translation>C&apos;est le temps que prendra votre ordinateur pour déverrouiller votre portefeuille après saisie de votre phrase de passe. (La durée effective sera inférieure à la durée spécifiée, mais plus de la moitié de celle-ci.)</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="429"/>
        <source>Target compute &amp;time (s, ms):</source>
        <translation>&amp;Durée de calcul cible (s, ms) :</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="430"/>
        <source>This is the &lt;b&gt;maximum&lt;/b&gt; memory that will be used as part of the encryption process.  The actual value used may be lower, depending on your system&apos;s speed.  If a low value is chosen, Armory will compensate by chaining together more calculations to meet the target time.  High memory target will make GPU-acceleration useless for guessing your passphrase.</source>
        <translation>C&apos;est la quantité &lt;b&gt;maximale&lt;/b&gt; de mémoire qui sera utilisée par le processus de chiffrement. La valeur utilisée pourrait en fait être plus faible selon la vitesse de votre système. Si une valeur faible est choisie, Armory compensera en enchaînant plus de calculs afin d&apos;atteindre le délai prévu. Une valeur de mémoire élevée rendra l&apos;accélération par l&apos;unité de traitement graphique inutile pour deviner votre phrase de passe.</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="444"/>
        <source>Max &amp;memory usage (kB, MB):</source>
        <translation>Utilisation maximale de la &amp;mémoire (Ko, Mo) :</translation>
    </message>
</context>
<context>
    <name>AllWalletsDispModel</name>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>ID</source>
        <translation>ID</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Wallet Name</source>
        <translation>Nom du porte-monnaie</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Security</source>
        <translation>Sécurité</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="114"/>
        <source>Balance</source>
        <translation>Solde</translation>
    </message>
</context>
<context>
    <name>ArmoryDialog</name>
    <message>
        <location filename="qtdefines.py" line="719"/>
        <source>Armory - Bitcoin Wallet Management [TESTNET] </source>
        <translation>Armory - Gestion des porte-monnaie Bitcoin [TESTNET]</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="722"/>
        <source>Armory - Bitcoin Wallet Management [REGTEST] </source>
        <translation>Armory - Gestion des porte-monnaie Bitcoin [REGTEST]</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="725"/>
        <source>Armory - Bitcoin Wallet Management</source>
        <translation>Armory - Gestion des porte-monnaie Bitcoin</translation>
    </message>
</context>
<context>
    <name>ArmoryMainWindow</name>
    <message>
        <location filename="ArmoryQt.py" line="281"/>
        <source>&lt;font color=%1&gt;Offline&lt;/font&gt; </source>
        <translation>&lt;font color=%1&gt;Hors ligne&lt;/font&gt; </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="332"/>
        <source>Create Wallet</source>
        <translation>Créer un porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="333"/>
        <source>Import or Restore Wallet</source>
        <translation>Importer ou restaurer un porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="338"/>
        <source>&lt;b&gt;Available Wallets:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Porte-monnaie disponibles :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="368"/>
        <source>&lt;b&gt;Maximum Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Fonds maximaux :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="369"/>
        <source>&lt;b&gt;Spendable Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Fonds disponibles :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="370"/>
        <source>&lt;b&gt;Unconfirmed:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Non confirmés :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="386"/>
        <source>
            Funds if all current transactions are confirmed.  
            Value appears gray when it is the same as your spendable funds. </source>
        <translation>
Les fonds, si toutes les transactions actuelles sont confirmées.
La valeur apparaît en gris quand elle est identique aux fonds disponibles.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="389"/>
        <source>Funds that can be spent &lt;i&gt;right now&lt;/i&gt;</source>
        <translation>Les fonds qui peuvent être dépensés &lt;i&gt;maintenant&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="390"/>
        <source>
            Funds that have less than 6 confirmations, and thus should not 
            be considered &lt;i&gt;yours&lt;/i&gt;, yet.</source>
        <translation>
Les fonds qui ont moins de six confirmations et qui ne devraient pas encore être considérés comme les &lt;i&gt;vôtres&lt;/i&gt;.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="418"/>
        <source>Dashboard</source>
        <translation>Tableau de bord</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1291"/>
        <source>Send Bitcoins</source>
        <translation>Envoyer des bitcoins</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1292"/>
        <source>Receive Bitcoins</source>
        <translation>Recevoir des bitcoins</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="434"/>
        <source>Wallet Properties</source>
        <translation>Propriétés du porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="435"/>
        <source>Offline Transactions</source>
        <translation>Transactions hors ligne</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="436"/>
        <source>Lockboxes (Multi-Sig)</source>
        <translation>Coffres (multisignatures)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="493"/>
        <source>&amp;File</source>
        <translation>&amp;Fichier</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="494"/>
        <source>&amp;User</source>
        <translation>&amp;Utilisateur</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="495"/>
        <source>&amp;Tools</source>
        <translation>&amp;Outils</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="496"/>
        <source>&amp;Addresses</source>
        <translation>&amp;Adresses</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="497"/>
        <source>&amp;Wallets</source>
        <translation>&amp;Porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="498"/>
        <source>&amp;MultiSig</source>
        <translation>&amp;Multisignatures</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="499"/>
        <source>&amp;Help</source>
        <translation>&amp;Aide</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="505"/>
        <source>Transactions Unavailable</source>
        <translation>Transactions indisponibles</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="505"/>
        <source>Transaction history cannot be collected until Armory is
               in online mode.  Please try again when Armory is online. </source>
        <translation>L&apos;historique transactionnel ne peut pas être recueilli tant qu&apos;Armory n&apos;est pas en mode en ligne. Veuillez ressayer quand Armory sera en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="565"/>
        <source>
               Bitcoin Core is not available, so Armory will not be able
               to broadcast any transactions for you.</source>
        <translation>
Bitcoin Core n&apos;est pas disponible et Armory ne pourra diffuser aucune transaction pour vous.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="573"/>
        <source>&amp;Message Signing/Verification...</source>
        <translation>Signature ou vérification de &amp;messages...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="575"/>
        <source>&amp;EC Calculator...</source>
        <translation>Calculateur de courbes &amp;elliptiques...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="576"/>
        <source>&amp;Broadcast Raw Transaction...</source>
        <translation>&amp;Diffuser une transaction brute...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2005"/>
        <source>Offline</source>
        <translation>Hors ligne</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="585"/>
        <source>
               Armory is currently offline, and cannot determine what funds are
               available for simulfunding.  Please try again when Armory is in
               online mode.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="594"/>
        <source>Import Multi-Spend Transaction</source>
        <translation>Importer une transaction multidépense</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="595"/>
        <source>
            Import a signature-collector text block for review and signing.
            It is usually a block of text with &quot;TXSIGCOLLECT&quot; in the first line,
            or a &lt;i&gt;*.sigcollect.tx&lt;/i&gt; file.</source>
        <translation>
Importer un bloc de texte « Collecteur de signatures » pour l&apos;examen et la signature. C&apos;est habituellement un bloc de texte avec « TXSIGCOLLECT » en première ligne ou un fichier &lt;i&gt;*.sigcollect.tx&lt;/i&gt;.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="608"/>
        <source>Simulfund &amp;Promissory Note</source>
        <translation> SimulFund - &amp;Billet à ordre</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="609"/>
        <source>Simulfund &amp;Collect &amp;&amp; Merge</source>
        <translation> SimulFund - &amp;Recouvrer et fusionner</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="610"/>
        <source>Simulfund &amp;Review &amp;&amp; Sign</source>
        <translation> SimulFund - &amp;Examen et signature</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="617"/>
        <source>View &amp;Address Book...</source>
        <translation>Voir le carnet d&apos;adresses...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="618"/>
        <source>&amp;Sweep Private Key/Address...</source>
        <translation>&amp;Balayer une clé privée ou une adresse...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="619"/>
        <source>&amp;Import Private Key/Address...</source>
        <translation>&amp;Importer une clé privée ou une adresse...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="626"/>
        <source>&amp;Create New Wallet</source>
        <translation>&amp;Créer un nouveau porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="627"/>
        <source>&amp;Import or Restore Wallet</source>
        <translation>&amp;Importer ou restaurer un porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="628"/>
        <source>View &amp;Address Book</source>
        <translation>Voir le carnet d&apos;&amp;adresses</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="629"/>
        <source>&amp;Fix Damaged Wallet</source>
        <translation>&amp;Réparer un porte-monnaie endommagé</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="640"/>
        <source>&amp;About Armory...</source>
        <translation>&amp;À propos d&apos;Armory...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="641"/>
        <source>Verify Signed Package...</source>
        <translation>Vérifier un paquet signé...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="642"/>
        <source>Clear All Unconfirmed</source>
        <translation>Effacer tous les non confirmés</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="643"/>
        <source>Rescan Databases</source>
        <translation>Réanalyser les bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="644"/>
        <source>Rebuild and Rescan Databases</source>
        <translation>Reconstruire et réanalyser les bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="645"/>
        <source>Rescan Balance</source>
        <translation>Réanalyser le solde</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="646"/>
        <source>Factory Reset</source>
        <translation>Réinitialisation générale</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="662"/>
        <source>Multi-Sig Lockboxes</source>
        <translation>Coffres multisignatures</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="663"/>
        <source>Lockbox &amp;Manager...</source>
        <translation>&amp;Gestionnaire de coffres...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="711"/>
        <source>Default Data Directory</source>
        <translation>Répertoire par défaut des données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="711"/>
        <source>
            Armory is using the default data directory because
            the data directory specified in the command line could
            not be found nor created.</source>
        <translation>
Armory utilise le répertoire de données par défaut, car le répertoire de données précisé dans la ligne de commande est introuvable et n&apos;a pas pu être créé.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="718"/>
        <source>Default Database Directory</source>
        <translation>Répertoire par défaut de la base de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="718"/>
        <source>
            Armory is using the default database directory because
            the database directory specified in the command line could
            not be found nor created.</source>
        <translation>
Armory utilise le répertoire de base de données par défaut, car le répertoire de base de données précisé dans la ligne de commande est introuvable et n&apos;a pas pu être créé.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="725"/>
        <source>Bitcoin Directory</source>
        <translation>Répertoire Bitcoin</translation>
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
        <location filename="ArmoryQt.py" line="732"/>
        <source>Delete Old DB Directory</source>
        <translation>Supprimer l&apos;ancien répertoire de base de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="732"/>
        <source>Armory detected an older version Database.
                  Do you want to delete the old database? Choose yes if 
                  do not think that you will revert to an older version of Armory.</source>
        <translation>Armory a détecté une base de données de l&apos;ancienne version. Souhaitez-vous supprimer l&apos;ancienne base de données ? Choisissez Oui si vous ne pensez pas revenir à une ancienne version d&apos;Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1481"/>
        <source>Do not ask this question again</source>
        <translation>Ne plus poser cette question</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="930"/>
        <source>Bad Module</source>
        <translation>Mauvais module</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="835"/>
        <source>
               The module you attempted to load (%1) is malformed.  It is
               missing attributes that are needed for Armory to load it.
               It will be skipped.</source>
        <translation>
Le module que vous avez tenté de charger (%1) est mal formé. Il lui manque des attributs afin qu&apos;Armory puisse le charger. Il sera ignoré.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="939"/>
        <source>Outdated Module</source>
        <translation>Module périmé</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="844"/>
        <source>
               Module &quot;%1&quot; is only specified to work up to Armory version %2.
               You are using Armory version %3.  Please remove the module if
               you experience any problems with it, or contact the maintainer
               for a new version.
               &lt;br&gt;&lt;br&gt;
               Do you want to continue loading the module?</source>
        <translation>
Le module « %«1 » n&apos;est sensé fonctionner que jusqu&apos;à la version %2 d&apos;Armory. Vous utilisez la version %3 d&apos;Armory. Veuillez supprimer le module s&apos;il vous pose des problèmes, ou contacter le mainteneur pour obtenir une nouvelle version.
&lt;br&gt;&lt;br&gt;
Souhaitez-vous poursuivre le chargement du module ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="901"/>
        <source>Invalid Module</source>
        <translation>Module invalide</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="901"/>
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

Armory a détecté le module suivant qui est &lt;font color=%1&gt;&lt;b&gt;invalide&lt;/b&gt;&lt;/font&gt; :
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Nom du module :&lt;/b&gt; %2&lt;br&gt;
&lt;b&gt;Chemin du module :&lt;/b&gt; %3&lt;br&gt;
&lt;br&gt;&lt;br&gt;
Armory exécutera seulement un module à partir d&apos;un fichier zip ayant la structure exigée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="911"/>
        <source>UNSIGNED Module</source>
        <translation>Module NON SIGNÉ</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="911"/>
        <source>
                  Armory detected the following module which
                  &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;has not been signed by Armory&lt;/b&gt;&lt;/font&gt; and may be dangerous:
                  &lt;br&gt;&lt;br&gt;
                     &lt;b&gt;Module Name:&lt;/b&gt; %2&lt;br&gt;
                     &lt;b&gt;Module Path:&lt;/b&gt; %3&lt;br&gt;
                  &lt;br&gt;&lt;br&gt;
                  Armory will not allow you to run this module.</source>
        <translation>

Armory a détecté le module suivant qui &lt;font color=%1&gt;&lt;b&gt; n&apos;a pas été signé par Armory&lt;/b&gt;&lt;/font&gt; et pourrait être dangereux :
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Nom du module :&lt;/b&gt; %2&lt;br&gt;
&lt;b&gt;Chemin du module :&lt;/b&gt; %3&lt;br&gt;
&lt;br&gt;&lt;br&gt;
Armory ne vous permettra pas d&apos;exécuter ce module.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="930"/>
        <source>
                     The module you attempted to load (%1) is malformed.  It is
                     missing attributes that are needed for Armory to load it.
                     It will be skipped.</source>
        <translation>
Le module que vous avez tenté de charger (%1) est mal formé. Il lui manque des attributs afin qu&apos;Armory puisse le charger. Il sera ignoré.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="939"/>
        <source>
                     Module %1 is only specified to work up to Armory version %2.
                     You are using Armory version %3.  Please remove the module if
                     you experience any problems with it, or contact the maintainer
                     for a new version.
                     &lt;br&gt;&lt;br&gt;
                     Do you want to continue loading the module?</source>
        <translation>
Le module %1 n&apos;est prévu pour fonctionner que jusqu&apos;à la version %2.
Vous utilisez Armory version %3. Veuillez supprimer le module si vous éprouvez des problèmes avec ce dernier, ou contactez le mainteneur afin d&apos;obtenir une nouvelle version.
&lt;br&gt;&lt;br&gt;
Souhaitez-vous poursuivre le chargement du module ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1004"/>
        <source>
         The next time you restart Armory, all unconfirmed transactions will
         be cleared allowing you to retry any stuck transactions.</source>
        <translation>
La prochaine fois que vous redémarrerez Armory, toutes les transactions non confirmées seront effacées, vous permettant de ressayer toute transaction bloquée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1008"/>
        <source>
         &lt;br&gt;&lt;br&gt;Make sure you also restart Bitcoin Core
         (or bitcoind) and let it synchronize again before you restart
         Armory.  Doing so will clear its memory pool, as well</source>
        <translation>
&lt;br&gt;&lt;br&gt;Assurez-vous de redémarrer aussi Bitcoin Core (ou bitcoind) et laissez-le se synchroniser de nouveau avant de redémarrer Armory. Cela effacera aussi sa réserve de mémoire.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1012"/>
        <source>Memory Pool</source>
        <translation>Réserve de mémoire</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1142"/>
        <source>Queue Rescan?</source>
        <translation>Mettre en file d&apos;attente la réanalyse ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1142"/>
        <source>
         The next time you restart Armory, it will rescan the blockchain
         database, and reconstruct your wallet histories from scratch.
         The rescan will take 10-60 minutes depending on your system.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a rescan on the next Armory restart?</source>
        <translation>
La prochaine fois que vous redémarrez Armory, elle réanalysera la base de données de la chaîne de blocs et reconstruira l&apos;historique de votre porte-monnaie de zéro. La nouvelle analyse prendra de 10 à 60 minutes selon votre système.&lt;br&gt;&lt;br&gt;
Souhaitez-vous forcer une réanalyse lors du prochain redémarrage d&apos;Armory ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1154"/>
        <source>Queue Rebuild?</source>
        <translation>Mettre en file d&apos;attente  la reconstruction ?</translation>
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
        <location filename="ArmoryQt.py" line="1166"/>
        <source>Queue Balance Rescan?</source>
        <translation>Mettre en file d&apos;attente la réanalyse du solde ?</translation>
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
        <location filename="ArmoryQt.py" line="1206"/>
        <source>Select Wallet</source>
        <translation>Sélectionner un porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1192"/>
        <source>You must import an address into a specific wallet.  If you do not want to import the key into any available wallet, it is recommeneded you make a new wallet for this purpose.&lt;br&gt;&lt;br&gt;Double-click on the desired wallet from the main window, then click on &quot;Import/Sweep Private Keys&quot; on the bottom-right of the properties window.&lt;br&gt;&lt;br&gt;Keys cannot be imported into watching-only wallets, only full wallets.</source>
        <translation>Vous devez importer une adresse dans un porte-monnaie précis. Si vous ne voulez pas importer la clé dans un porte-monnaie proposé, il est recommandé de créer un nouveau porte-monnaie pour ce faire.&lt;br&gt;&lt;br&gt;Double-cliquez sur le porte-monnaie désiré dans la fenêtre principale, puis cliquez sur « Importer/balayer des clés privées » en bas à droite de la fenêtre des propriétés.&lt;br&gt;&lt;br&gt;Les clés ne peuvent pas être importées dans des porte-monnaie juste-regarder, seulement dans les porte-monnaie complets.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1206"/>
        <source>You must select a wallet into which funds will be swept. Double-click on the desired wallet from the main window, then click on &quot;Import/Sweep Private Keys&quot; on the bottom-right of the properties window to sweep to that wallet.&lt;br&gt;&lt;br&gt;Keys cannot be swept into watching-only wallets, only full wallets.</source>
        <translation>Vous devez sélectionner un porte-monnaie vers lequel les fonds seront balayés. Double-cliquez sur le porte-monnaie désiré dans la fenêtre principale, puis cliquez sur « Importer/balayer des clés privées » en bas à droite dans la fenêtre des propriétés pour balayer vers ce porte-monnaie.&lt;br&gt;&lt;br&gt;Les clés ne peuvent pas être balayées vers des porte-monnaie juste-regarder, seulement vers les porte-monnaie complets.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1290"/>
        <source>Show Armory</source>
        <translation>Afficher Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1293"/>
        <source>Quit Armory</source>
        <translation>Quitter Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1481"/>
        <source>Default URL Handler</source>
        <translation>Gestionnaire d&apos;URL par défaut</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1410"/>
        <source>Armory is not set as your default application for handling
                  &quot;bitcoin:&quot; links.  Would you like to use Armory as the 
                  default?</source>
        <translation>Armory n&apos;est pas définie comme application par défaut pour la gestion des liens « bitcoin: ». Souhaitez-vous utiliser Armory comme application par défaut ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1481"/>
        <source>Armory is not set as your default application for handling
               &quot;bitcoin:&quot; links.  Would you like to use Armory as the 
               default?</source>
        <translation>Armory n&apos;est pas définie comme application par défaut pour la gestion des liens « bitcoin: ». Souhaitez-vous utiliser Armory comme application par défaut ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1534"/>
        <source>Version Warning</source>
        <translation>Avertissement de version</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1534"/>
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
Depuis la version 0. 92 d&apos;Armory, les formats des opérations transactionnelles hors ligne a changé pour permettre les transactions multisignatures. Ce format n&apos;est &lt;u&gt;pas&lt;/u&gt; compatible avec les versions antérieures à 0.92.
&lt;br&gt;&lt;br&gt;
Pour poursuivre, l&apos;autre système devra être mis à niveau vers la version 0. 92 ou ultérieure. Si vous ne pouvez pas mettre à niveau l&apos;autre système, vous devrez réinstaller une ancienne version d&apos;Armory sur ce système.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1534"/>
        <source>Do not show this warning again</source>
        <translation>Ne plus afficher cet avertissement</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1568"/>
        <source>No Tools Yet!</source>
        <translation>Pas encore d&apos;outils !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1568"/>
        <source>The developer tools are not available yet, but will be added
         soon.  Regardless, developer-mode still offers lots of 
         extra information and functionality that is not available in 
         Standard or Advanced mode.</source>
        <translation>Les outils pour développeurs ne sont pas encore proposés, mais ils seront ajoutés bientôt. Malgré tout, le mode développeur offre quand même de nombreuses informations et fonctions qui ne sont pas proposées en mode Normal ou Avancé.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1608"/>
        <source>Root Pubkey Text Files (*.rootpubkey)</source>
        <translation>Fichier texte Root Pubkey (*.rootpubkey)
</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1628"/>
        <source>Aborted</source>
        <translation>Interrompu</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1668"/>
        <source>
                  No passphrase was selected for the encrypted backup.
                  No backup was created</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1640"/>
        <source>Backup Complete</source>
        <translation>La sauvegarde est terminée</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1640"/>
        <source>
         Your wallet was successfully backed up to the following
         location:&lt;br&gt;&lt;br&gt;%1</source>
        <translation>
Votre porte-monnaie a été sauvegardé avec succès à l&apos;emplacement suivant :&lt;br&gt;&lt;br&gt;%1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1703"/>
        <source>Restart Armory</source>
        <translation>Redémarrer Armory</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1688"/>
        <source>You may have to restart Armory for all aspects of
         the new usermode to go into effect.</source>
        <translation>Vous devrez peut-être redémarrer Armory pour que tous les aspects du nouveau mode utilisateur entrent en fonction.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1703"/>
        <source>You will have to restart Armory for the new language to go into effect</source>
        <translation>Vous devrez redémarrer Armory pour que la nouvelle langue soit utilisée</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1724"/>
        <source>Invalid Date Format</source>
        <translation>Format de date invalide</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1724"/>
        <source>The date format you specified was not valid.  Please re-enter
            it using only the strftime symbols shown in the help text.</source>
        <translation>Le format de date que vous avez spécifié n&apos;est pas valide. Veuillez le saisir de nouveau en n&apos;utilisant que les symboles strftime affichés dans le texte d&apos;aide.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1751"/>
        <source>Already Open</source>
        <translation>Déjà ouvert</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1751"/>
        <source>
               Armory is already running!  You can only have one Armory open
               at a time.  Exiting...</source>
        <translation>
Armory est déjà en fonction ! Vous ne pouvez avoir qu&apos;une instance d&apos;Armory ouverte à la fois. Sortie...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1901"/>
        <source>No URL String</source>
        <translation>Pas de chaîne URL</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1901"/>
        <source>You have not entered a URL String yet.
               Please go back and enter a URL String.</source>
        <translation>N&apos;avez pas encore saisi de chaîne URL.
Veuillez revenir en arrière et saisir une chaîne URL.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2021"/>
        <source>clicked</source>
        <translation>avez cliqué</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1912"/>
        <source>entered</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3332"/>
        <source>Offline Mode</source>
        <translation>Mode hors ligne</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1923"/>
        <source>You %1 on a &quot;bitcoin:&quot; link, but Armory is in
            offline mode, and is not capable of creating transactions. 
            Using links will only work if Armory is connected 
            to the Bitcoin network!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1932"/>
        <source>It looks like you just %1 a &quot;bitcoin:&quot; link, but
                    that link is malformed.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1935"/>
        <source>Please check the source of the link and enter the
                        transaction manually.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1940"/>
        <source>The raw URI string is:

</source>
        <translation>La chaîne URI brute est :

</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1941"/>
        <source>Invalid URI</source>
        <translation>URI invalide</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1944"/>
        <source>The &quot;bitcoin:&quot; link you just %1
            does not even contain an address!  There is nothing that 
            Armory can do with this link!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1970"/>
        <source>Wrong Network!</source>
        <translation>Mauvais réseau !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1956"/>
        <source>The address for the &quot;bitcoin:&quot; link you just %1 is
            for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
            and the address you supplied is for the 
            &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1989"/>
        <source>Unsupported URI</source>
        <translation>URI non prise en charge</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1969"/>
        <source>The &quot;bitcoin:&quot; link
               you just %1 contains fields that are required but not
               recognized by Armory.  This may be an older version of Armory,
               or the link you %2 on uses an exotic, unsupported format.
               &lt;br&gt;&lt;br&gt;The action cannot be completed.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2005"/>
        <source>You just clicked on a &quot;bitcoin:&quot; link, but Armory is offline
            and cannot send transactions.  Please click the link 
            again when Armory is online.</source>
        <translation>Vous venez de cliquer sur un lien « bitcoin: », mais Armory est hors ligne et ne peut pas envoyer de transactions. Veuillez cliquer sur le lien de nouveau quand Armory sera en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2254"/>
        <source>All files (*)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2391"/>
        <source>Contributor &quot;%1&quot; (%2)</source>
        <translation>Contributeur « %1 » (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2393"/>
        <source>Contributor %1</source>
        <translation>Contributeur %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2396"/>
        <source>Contributor &quot;%1&quot;</source>
        <translation>Contributeur « %1 »</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2398"/>
        <source>Unknown Contributor</source>
        <translation>Contributeur inconnu</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2463"/>
        <source>Blockchain loaded, wallets sync&apos;d!</source>
        <translation>La chaîne de blocs a été chargée, les porte-monnaie sont synchronisés !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2469"/>
        <source>Blockchain Loaded!</source>
        <translation>La chaîne de blocs est chargée !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2469"/>
        <source>Blockchain loading is complete.
            Your balances and transaction history are now available 
            under the &quot;Transactions&quot; tab.  You can also send and 
            receive bitcoins.</source>
        <translation>Le chargement de la chaîne de blocs est terminé.
Vos soldes et l&apos;historique transactionnel se trouvent maintenant dans l&apos;onglet «Transactions ». Vous pouvez aussi envoyer et recevoir des bitcoins.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2469"/>
        <source>Do not show me this notification again </source>
        <translation>Ne plus afficher cette notification</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2555"/>
        <source>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Maximum Funds:&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Fonds maximaux :&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2648"/>
        <source>***MEMPOOL REPLACEABLE*** </source>
        <translation>***REMPLAÇABLE DANS LE RÉSERVE DE MÉMOIRE*** </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2689"/>
        <source>My Wallets</source>
        <translation>Mes porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2690"/>
        <source>Offline Wallets</source>
        <translation>Porte-monnaie hors ligne</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2691"/>
        <source>Other&apos;s wallets</source>
        <translation>Autres porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2692"/>
        <source>All Wallets</source>
        <translation>Tout les porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2693"/>
        <source>Custom Filter</source>
        <translation>Filtre personnalisé</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3435"/>
        <source>No Wallets!</source>
        <translation>Aucun porte-monnaie !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2704"/>
        <source>You currently do not have any wallets.  Would you like to
            create one, now?</source>
        <translation>Vous n&apos;avez actuellement aucun porte-monnaie. Souhaitez-vous en créer un maintenant ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2717"/>
        <source>Select a Wallet</source>
        <translation>Sélectionner un porte-monnaie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2717"/>
        <source>Please select a wallet on the right, to see its properties.</source>
        <translation>Veuillez sélectionner un porte-monnaie sur la droite pour en voir les propriétés.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2753"/>
        <source>Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2768"/>
        <source>Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2935"/>
        <source>Already Sweeping</source>
        <translation>Un balayage est déjà en cours</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2935"/>
        <source>You are already in the process of scanning the blockchain for
            the purposes of sweeping other addresses.  You cannot initiate 
            sweeping new addresses until the current operation completes. 
            &lt;br&gt;&lt;br&gt;
            In the future, you may select &quot;Multiple Keys&quot; when entering 
            addresses to sweep.  There is no limit on the number that can be 
            specified, but they must all be entered at once.</source>
        <translation>Vous êtes déjà en train d&apos;analyser la chaîne de blocs dans le but de balayer d&apos;autres adresses. Vous ne pouvez pas lancer le balayage de nouvelles adresses tant que les opérations en cours ne sont pas terminées.
&lt;br&gt;&lt;br&gt;
À l&apos;avenir, vous pourrez sélectionner « Plusieurs clés » lors de la saisie des adresses à balayer. Il n&apos;y a pas de limite de nombre, mais elles doivent être saisies en une seule fois.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3016"/>
        <source>addresses</source>
        <translation>adresses</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3016"/>
        <source>address</source>
        <translation>adresse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2957"/>
        <source>Armory is Offline</source>
        <translation>Armory est hors ligne</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2957"/>
        <source>You have chosen to sweep %1 %2, but Armory is currently
            in offline mode.  The sweep will be performed the next time you 
            go into online mode.  You can initiate online mode (if available) 
            from the dashboard in the main window.</source>
        <translation>Vous avez choisi de balayer %1 %2, mais Armory est actuellement en mode hors ligne. Le balayage sera effectué la prochaine fois que vous utiliserez le mode en ligne. Vous pouvez lancer le mode en ligne (s&apos;il est disponible) dans le tableau de bord de la fenêtre principale.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2965"/>
        <source>Armory must scan the global transaction history in order to
            find any bitcoins associated with the %1 you supplied.
            Armory will go into offline mode temporarily while the scan 
            is performed, and you will not have access to balances or be 
            able to create transactions.  The scan may take several minutes.
            &lt;br&gt;&lt;br&gt;</source>
        <translation>Armory doit analyser l&apos;historique transactionnel global afin de trouver des bitcoins associés avec le %1 vous avez fourni. Armory passera temporairement en mode en ligne pendant l&apos;analyse. Vous n&apos;aurez pas accès aux soldes ni ne pourrez créer de transactions. L&apos;analyse prendra plusieurs minutes.
&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2974"/>
        <source>There is currently another scan operation being performed.
               Would you like to start the sweep operation after it completes? </source>
        <translation>Une autre analyse est en cours.
Souhaitez-vous lancer l&apos;opération de balayage après cette analyse ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2978"/>
        <source>&lt;b&gt;Would you like to start the scan operation right now?&lt;/b&gt;</source>
        <translation>&lt;b&gt;Souhaitez-vous lancer l&apos;opération d&apos;analyse maintenant ?&lt;/b&gt;
</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2981"/>
        <source>&lt;br&gt;&lt;br&gt;Clicking &quot;No&quot; will abort the sweep operation</source>
        <translation>&lt;br&gt;&lt;br&gt;Cliquer sur « Non » interrompra l&apos;opération de balayage</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2983"/>
        <source>Confirm Rescan</source>
        <translation>Confirmer la réanalyse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3010"/>
        <source>Nothing to do</source>
        <translation>Rien à faire</translation>
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
        <location filename="ArmoryQt.py" line="3017"/>
        <source>Cannot sweep</source>
        <translation>Balayage impossible</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3032"/>
        <source>multiple addresses</source>
        <translation>plusieurs adresses</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3034"/>
        <source>address &lt;b&gt;%1&lt;/b&gt;</source>
        <translation>adresse &lt;b&gt;%1&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3036"/>
        <source>wallet &lt;b&gt;&quot;%1&quot;&lt;/b&gt; (%2) </source>
        <translation>porte-monnaie &lt;b&gt;« %1 »&lt;/b&gt; (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3079"/>
        <source>Broadcast failed</source>
        <translation>Échec de diffusion</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3079"/>
        <source>
                  The broadcast process failed unexpectedly. Report this error to
                  the development team if this issue occurs repeatedly
                  </source>
        <translation>
Le processus de diffusion a échoué de manière inattendue. Si cela se reproduit, veuillez signaler ce problème à l&apos;équipe de développement.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3101"/>
        <source>Transaction Not Accepted</source>
        <translation>La transaction n&apos;a pas été acceptée</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3101"/>
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
        <translation>
La transaction que vous venez d&apos;effectuer a échoué avec le message d&apos;erreur suivant : &lt;br&gt;&lt;br&gt;
&lt;b&gt;%1&lt;/b&gt;
&lt;br&gt;&lt;br&gt;


&lt;br&gt;&lt;br&gt;Pour les erreurs de temporisation, la transaction pourrait avoir réussi et ce message avoir été affiché prématurément. Pour confirmer si la transaction a en fait réussi, vous pouvez utiliser ce lien direct vers %2 :
&lt;br&gt;&lt;br&gt;
&lt;a href=&quot;%3&quot;&gt;%4...&lt;/a&gt;
&lt;br&gt;&lt;br&gt;
Si vous ne voyez pas la transaction sur cette page Web dans la minute qui suit, elle a échoué et vous devriez tenter de la renvoyer.
Si elle y &lt;i&gt;est présente&lt;/i&gt;, vous n&apos;avez alors rien à faire. Elle apparaîtra dans Armory dès qu&apos;elle aura reçu une confirmation.
&lt;br&gt;&lt;br&gt; Si la transaction a effectivement échoué, cela provient  certainement de frais trop bas. Ressayez avec des frais plus élevés.

Si le problème persiste, allez à « &lt;i&gt;Fichier&lt;/i&gt; » =&gt;« &lt;i&gt;Exporter le fichier journal&lt;/i&gt; » et joignez-le à une demande d&apos;assistance à &lt;a href=&quot;%5&quot;&gt;%5&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3137"/>
        <source>In the future, you may avoid scanning twice by starting Armory in offline mode (--offline), and perform the import before switching to online mode.</source>
        <translation>À l&apos;avenir, vous pouvez éviter d&apos;analyser deux fois en démarrant Armory en mode hors ligne (--offline), puis en effectuant l&apos;importation avant de passer au mode en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3141"/>
        <source>Armory is Busy</source>
        <translation>Armory est occupé</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3141"/>
        <source>Wallets and addresses cannot be imported while Armory is in the middle of an existing blockchain scan.  Please wait for the scan to finish.  </source>
        <translation>Les porte-monnaie et les adresses ne peuvent pas être importés pendant qu&apos;Armory effectue une analyse de la chaîne de blocs. Veuillez attendre la fin de l&apos;analyse.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3155"/>
        <source>Scanning</source>
        <translation>Analyse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3155"/>
        <source>
            Armory is currently in the middle of scanning the blockchain for
            your existing wallets.  New wallets cannot be imported until this
            operation is finished.</source>
        <translation>
Armory analyse actuellement la chaîne de blocs pour les porte-monnaie existants. Les nouveaux porte-monnaie ne pourront pas être importés tant que cette opération ne sera pas terminée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3175"/>
        <source>Duplicate Wallet!</source>
        <translation>Porte-monnaie en double !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3175"/>
        <source>
            You selected a wallet that has the same ID as one already 
            in your wallet (%1)!  If you would like to import it anyway,
            please delete the duplicate wallet in Armory, first.</source>
        <translation>
Vous avez sélectionné un porte-monnaie qui a le même ID qu&apos;un de ceux de votre porte-monnaie (%1) ! Si vous souhaitez quand même l&apos;importer, veuillez d&apos;abord supprimer d&apos;Armory le porte-monnaie dupliqué.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3194"/>
        <source>Be Careful!</source>
        <translation>Faites attention !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3194"/>
        <source>
        &lt;font color=&quot;red&quot;&gt;&lt;b&gt;WARNING:&lt;/b&gt;&lt;/font&gt; You are about to make an
        &lt;u&gt;unencrypted&lt;/u&gt; backup of your wallet.  It is highly recommended
        that you do &lt;u&gt;not&lt;/u&gt; ever save unencrypted wallets to your regular
        hard drive.  This feature is intended for saving to a USB key or
        other removable media.</source>
        <translation>
&lt;font color=&quot;red&quot;&gt;&lt;b&gt;AVERTISSEMENT :&lt;/b&gt;&lt;/font&gt;Vous allez faire une sauvegarde &lt;u&gt;non chiffrée&lt;/u&gt; de votre porte-monnaie. Il est fortement recommandé de ne &lt;u&gt; jamais&lt;/u&gt; enregistrer des porte-monnaie non chiffrés sur votre disque dur habituel. Le but de cette fonction est l&apos;enregistrement vers une clé USB ou un support amovible.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3211"/>
        <source>Blockchain Not Ready</source>
        <translation>La chaîne de blocs n&apos;est pas prête</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3206"/>
        <source>
            The address book is created from transaction data available in 
            the blockchain, which has not finished loading.  The address 
            book will become available when Armory is online.</source>
        <translation>
Le carnet d&apos;adresses est créé à partir de données transactionnelles disponibles dans la chaîne de blocs dont le chargement n&apos;est pas terminé. Le carnet d&apos;adresses sera accessible quand Armory sera en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3211"/>
        <source>
            The address book is created from transaction data available in 
            the blockchain, but Armory is currently offline.  The address 
            book will become available when Armory is online.</source>
        <translation>
Le carnet d&apos;adresses est créé à partir de données transactionnelles disponibles dans la chaîne de blocs, mais Armory est actuellement hors ligne. Le carnet d&apos;adresses sera accessible quand Armory sera en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3217"/>
        <source>No wallets!</source>
        <translation>Aucun porte-monnaie !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3217"/>
        <source>You have no wallets so
               there is no address book to display.</source>
        <translation>Vous n&apos;avez aucun porte-monnaie et il n&apos;y a donc aucun carnet d&apos;adresses à afficher.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3269"/>
        <source>Invalid Tx</source>
        <translation>Transaction invalide</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3269"/>
        <source>
         The transaction you requested be displayed does not exist in 
         Armory&apos;s database.  This is unusual...</source>
        <translation>
La transaction dont vous avez demandé l&apos;affichage n&apos;existe pas dans la base de données d&apos;Armory. C&apos;est inhabituel...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3289"/>
        <source>View Details</source>
        <translation>Voir les détails</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3290"/>
        <source>View on %1</source>
        <translation>Visualiser sur %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3291"/>
        <source>Change Comment</source>
        <translation>Modifier le commentaire</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3292"/>
        <source>Copy Transaction ID</source>
        <translation>Copier l&apos;ID de la transaction</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3293"/>
        <source>Open Relevant Wallet</source>
        <translation>Ouvrir le porte-monnaie pertinent</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3303"/>
        <source>Could not open browser</source>
        <translation>Impossible d&apos;ouvrir le navigateur</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3303"/>
        <source>
               Armory encountered an error opening your web browser.  To view 
               this transaction on blockchain.info, please copy and paste 
               the following URL into your browser: 
               &lt;br&gt;&lt;br&gt;%1</source>
        <translation>
Une erreur est survenue lors de l&apos;ouverture de votre navigateur Web par Armory. Pour visualiser cette transaction sur blockchain.info, veuillez copier-coller l&apos;URL suivante dans votre navigateur :
&lt;br&gt;&lt;br&gt;%1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3332"/>
        <source>
           Armory is currently running in offline mode, and has no 
           ability to determine balances or create transactions. 
           &lt;br&gt;&lt;br&gt;
           In order to send coins from this wallet you must use a 
           full copy of this wallet from an online computer, 
           or initiate an &quot;offline transaction&quot; using a watching-only 
           wallet on an online computer.</source>
        <translation>
Armory fonctionne actuellement en mode hors ligne et ne peut pas déterminer les soldes ni créer de transactions.
&lt;br&gt;&lt;br&gt;
Afin d&apos;envoyer des pièces de ce porte-monnaie, vous devez utiliser une copie complète de ce porte-monnaie sur un ordinateur en ligne, ou commencer une « transaction hors ligne » en utilisant un porte-monnaie juste-regarder sur un ordinateur en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3342"/>
        <source>Armory Not Ready</source>
        <translation>Armory n&apos;est pas prêt</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3342"/>
        <source>
           Armory is currently scanning the blockchain to collect 
           the information needed to create transactions.  This typically 
           takes between one and five minutes.  Please wait until your 
           balance appears on the main window, then try again.</source>
        <translation>
Armory analyse actuellement la chaîne de blocs pour recueillir les informations nécessaires à la création de transactions. Cela prend habituellement d&apos;une à cinq minutes. Veuillez attendre que votre solde apparaisse sur la fenêtre principale et ressayer.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3351"/>
        <source>
            You cannot send any bitcoins until you create a wallet and 
            receive some coins.  Would you like to create a wallet?</source>
        <translation>
Vous ne pouvez pas envoyer de bitcoins tant que vous n&apos;avez pas créé un porte-monnaie et reçu des pièces. Souhaitez-vous créer un porte-monnaie ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3380"/>
        <source>You just clicked on a &quot;bitcoin:&quot; link requesting bitcoins
                to be sent to the following address:&lt;br&gt; </source>
        <translation>Vous venez de cliquer sur un lien « bitcoin: »  demandant d&apos;envoyer des bitcoins à l&apos;adresse suivante :&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3383"/>
        <source>&lt;br&gt;--&lt;b&gt;Address&lt;/b&gt;:<byte value="x9"/>%1 </source>
        <translation>&lt;br&gt;--&lt;b&gt;Adresse&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1 </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3395"/>
        <source>&lt;br&gt;--&lt;b&gt;Amount&lt;/b&gt;:<byte value="x9"/>%1 BTC</source>
        <translation>&lt;br&gt;--&lt;b&gt;Montant&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1 BTC</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3400"/>
        <source>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1...</source>
        <translation>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3402"/>
        <source>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1</source>
        <translation>&lt;br&gt;--&lt;b&gt;Message&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3407"/>
        <source>&lt;br&gt;&lt;br&gt;There is no amount specified in the link, so
            you can decide the amount after selecting a wallet to use 
            for this transaction. </source>
        <translation>&lt;br&gt;&lt;br&gt;Aucun montant n&apos;est précisé dans le lien et vous pourrez déterminer le montant après avoir choisi un porte-monnaie à utiliser pour cette transaction.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3411"/>
        <source>&lt;br&gt;&lt;br&gt;&lt;b&gt;The specified amount &lt;u&gt;can&lt;/u&gt; be changed&lt;/b&gt; on the
            next screen before hitting the &quot;Send&quot; button. </source>
        <translation>&lt;br&gt;&lt;br&gt;&lt;b&gt;Le montant précisé &lt;u&gt;pourra&lt;/u&gt; être changé&lt;/b&gt;sur le prochain écran avant de cliquer sur le bouton « Envoyer ».</translation>
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
        <location filename="ArmoryQt.py" line="3435"/>
        <source>
            You have not created any wallets which means there is
            nowhere to store you bitcoins!  Would you like to
            create a wallet now?</source>
        <translation>
Vous n&apos;avez créé aucun porte-monnaie, ce qui signifie que vos bitcoins ne peuvent être stockés nulle part ! Souhaitez-vous créer un porte-monnaie maintenant ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3452"/>
        <source>Receive coins with wallet...</source>
        <translation>Recevoir des pièces avec un porte-monnaie...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3544"/>
        <source>Privacy Warning</source>
        <translation>Avertissement sur la protection des données personnelles</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3508"/>
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
&lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Les fichiers journaux d&apos;analyse des porte-monnaie&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Les journaux d&apos;analyse des porte-monnaie ne contiennent aucune information qui permettrait de vous identifier personnellement, seulement un enregistrement des erreurs et des incohérences trouvées dans votre fichier de porte-monnaie. Aucune clé privée ni même publique n’est incluse.
&lt;br&gt;&lt;br&gt;

&lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Les fichiers journaux ordinaires&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Les fichiers journaux ordinaires ne contiennent aucune information délicate en matière de &lt;u&gt;sécurité&lt;/u&gt;, mais certains utilisateurs pourraient considérer que les informations sont à caractère &lt;u&gt;privé&lt;/u&gt;. Les fichiers journaux peuvent identifier des adresses et des transactions associées à vos porte-monnaie. Il est toujours recommandé d&apos;inclure les fichiers journaux avec toute demande faite à l&apos;équipe Armory, à moins que vous soyez mal à l&apos;aise avec les implications en matière de confidentialité.
&lt;br&gt;&lt;br&gt;

&lt;b&gt;&lt;u&gt;&lt;font size=3&gt;Les porte-monnaie juste-regarder&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Un porte-monnaie juste-regarder est une copie d&apos;un porte-monnaie ordinaire qui ne contient aucune clé de signature. Cela permet au détenteur de voir le solde et l&apos;historique transactionnel du porte-monnaie, mais de ne dépenser aucun fonds.
&lt;br&gt;&lt;br&gt;
On pourrait vous demander d&apos;envoyer une copie juste-regarder de votre porte-monnaie pour garantir que rien ne met en danger la sécurité de vos fonds. Vous ne devriez même pas envisager d&apos;envoyer un porte-monnaie juste-regarder, à moins que cela n&apos;ait été expressément demandé par un représentant d&apos;Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3544"/>
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

Les fichiers journaux d&apos;Armory ne contiennent aucune d&apos;information sensible en matière de &lt;u&gt;sécurité&lt;/u&gt;, mais certains utilisateurs pourraient considérer que les informations sont à caractère &lt;u&gt;privé&lt;/u&gt;. Les fichiers journaux peuvent révéler des adresses et des transactions associées à vos porte-monnaie.
&lt;br&gt;&lt;br&gt;

&lt;b&gt;Aucune donnée de clé de signature n&apos;est écrite dans le fichier journal&lt;/b&gt;.
On y trouve juste assez de données pour aider les développeurs à exposer les bogues du logiciel, mais certains utilisateurs pourraient quand même considérer ces informations comment délicates.
&lt;br&gt;&lt;br&gt;

Veuillez ne pas envoyer le fichier journal aux développeurs d&apos;Armory si  vous êtes mal à l&apos;aise avec les implications en matière de confidentialité ! Cependant, si vous n&apos;envoyez pas le fichier journal, il pourrait nous être difficile, voire impossible, de vous aider avec votre problème.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3615"/>
        <source>Already running!</source>
        <translation>Déjà en fonction !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3615"/>
        <source>
               The Bitcoin software appears to be installed now, but it
               needs to be closed for Armory to work.  Would you like Armory
               to close it for you?</source>
        <translation>
Le logiciel Bitcoin semble maintenant être installé, mais il doit être fermé pour qu&apos;Armory fonctionne. Souhaitez-vous qu&apos;Armory le ferme pour vous ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3623"/>
        <source>Still Missing</source>
        <translation>Toujours manquant</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3623"/>
        <source>
               The Bitcoin software still appears to be missing.  If you
               just installed it, then please adjust your settings to point
               to the installation directory.</source>
        <translation>
Il semble que le logiciel n&apos;est toujours pas installé. Si vous venez juste de le faire, veuillez ajuster vos paramètres afin qu&apos;ils prennent en compte le répertoire d&apos;installation.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3630"/>
        <source>Still Running</source>
        <translation>Toujours en fonction</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3630"/>
        <source>
               Bitcoin Core is still running.  Armory cannot start until
               it is closed.  Do you want Armory to close it for you?</source>
        <translation>
Bitcoin Core est encore en fonction. Armory ne peut pas démarrer tant qu&apos;il ne sera pas fermé. Souhaitez-vous qu&apos;Armory le ferme pour vous ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3744"/>
        <source>Close Bitcoin Process</source>
        <translation>Fermer le processus Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3756"/>
        <source>Download Bitcoin</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3745"/>
        <source>Open https://bitcoin.org</source>
        <translation>Ouvrir https://bitcoin.org</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3758"/>
        <source>Installation Instructions</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3746"/>
        <source>Change Settings</source>
        <translation>Modifier les paramètres</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3750"/>
        <source>Preparing to shut down..</source>
        <translation>Préparation à l&apos;extinction...</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3778"/>
        <source>Stop existing Bitcoin processes so that Armory can open its own</source>
        <translation>Fermer les processus Bitcoin existants afin qu&apos;Armory puisse ouvrir les siens</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3780"/>
        <source>Open browser to Bitcoin webpage to download and install Bitcoin software</source>
        <translation>Ouvrir le navigateur sur la page Web Bitcoin pour télécharger et installer le logiciel Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3799"/>
        <source>Instructions for manually installing Bitcoin for operating system</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3782"/>
        <source>Open Armory settings window to change Bitcoin software management</source>
        <translation>Ouvrir la fenêtre des paramètres d&apos;Armory pour changer la gestion du logiciel Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3786"/>
        <source>
           Will open your default browser to https://bitcoin.org where you can 
           download the latest version of Bitcoin Core, and get other information
           and links about Bitcoin, in general.</source>
        <translation>
Ouvrira votre navigateur par défaut sur https://bitcoin.org où vous pourrez télécharger la dernière version de Bitcoin Core et obtenir d&apos;autres informations et liens sur Bitcoin en général.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3809"/>
        <source>
           Instructions are specific to your operating system and include 
           information to help you verify you are installing the correct software</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3790"/>
        <source>
           Change Bitcoin Core/bitcoind management settings or point Armory to
           a non-standard Bitcoin installation</source>
        <translation>
Changer les paramètres de gestion de Bitcoin Core/bitcoind, ou diriger Armory vers une installation Bitcoin non standard</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3793"/>
        <source>
           Armory has detected a running Bitcoin Core or bitcoind instance and
           will force it to exit</source>
        <translation>
Armory à détecter un processus Bitcoin Core ou bitcoind en cours d&apos;exécution et forcera son extinction</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3821"/>
        <source>This option is not yet available yet!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3828"/>
        <source>Securely download Bitcoin software for Windows %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3830"/>
        <source>
            The downloaded files are cryptographically verified.  
            Using this option will start the installer, you will 
            have to click through it to complete installation.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3846"/>
        <source>
               Download and Install Bitcoin Core for Ubuntu/Debian</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3866"/>
        <source>
               Will download and Bitcoin software and cryptographically verify it</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3845"/>
        <source>Not Found</source>
        <translation>Introuvable</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3845"/>
        <source>
         Attempted to kill the running Bitcoin Core/bitcoind instance,
         but it was not found.  </source>
        <translation>
Nous avons tenté de tuer le processus Bitcoin Core ou bitcoind en cours d&apos;exécution, mais il était introuvable.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3898"/>
        <source>Loading Database Headers</source>
        <translation>Chargement des en-têtes des bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3907"/>
        <source>Organizing Blockchain</source>
        <translation>Organisation de la chaîne de blocs</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4628"/>
        <source>Scan Transaction History</source>
        <translation>Analyser l&apos;historique transactionnel</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3918"/>
        <source>Reading New Block Headers</source>
        <translation>Lecture des en-têtes des nouveaux blocs</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3926"/>
        <source>Building Databases</source>
        <translation>Construction des bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4561"/>
        <source>Build Databases</source>
        <translation>Construire les bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3936"/>
        <source>Scanning Transaction History</source>
        <translation>Analyse de l&apos;historique transactionnel</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3946"/>
        <source>Computing Balances</source>
        <translation>Calcul des soldes</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3956"/>
        <source>Parsing Tx Hashes</source>
        <translation>Analyse des hachages transactionnels</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3970"/>
        <source>Resolving Tx Hashes</source>
        <translation>Résolution des hachages transactionnels</translation>
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
        <location filename="ArmoryQt.py" line="4079"/>
        <source>&lt;ul&gt;&lt;li&gt;Create, import or recover Armory wallets&lt;/li&gt;&lt;li&gt;Generate new addresses to receive coins&lt;/li&gt;&lt;li&gt;Send bitcoins to other people&lt;/li&gt;&lt;li&gt;Create one-time backups of your wallets (in printed or digital form)&lt;/li&gt;&lt;li&gt;Click on &quot;bitcoin:&quot; links in your web browser (not supported on all operating systems)&lt;/li&gt;&lt;li&gt;Import private keys to wallets&lt;/li&gt;&lt;li&gt;Monitor payments to watching-only wallets and create unsigned transactions&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Create transactions with watching-only wallets, to be signed by an offline wallets&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt;</source>
        <translation>&lt;ul&gt;&lt;li&gt;Créer, importer ou récupérer des porte-monnaie&lt;/li&gt;&lt;li&gt;Générer de nouvelles adresses pour recevoir des pièces&lt;/li&gt;&lt;li&gt;Envoyer des pièces à d&apos;autres personnes&lt;/li&gt;&lt;li&gt;Créer des sauvegardes uniques de vos porte-monnaie (imprimées ou numériques)&lt;/li&gt;&lt;li&gt;Cliquer sur des liens « bitcoin: » dans votre navigateur Web (n&apos;est pas pris en charge sur tous les systèmes d&apos;exploitation)&lt;/li&gt;&lt;li&gt;Importer des clés privées dans les porte-monnaie&lt;/li&gt;&lt;li&gt;Surveiller les paiements vers des porte-monnaie juste-regarder et créer des transactions non signées&lt;/li&gt;&lt;li&gt;Signer des messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Créer des transactions avec des porte-monnaie juste-regarder, à signer avec des porte-monnaie hors ligne&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt; </translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4105"/>
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
        <translation>
Pour plus d&apos;informations sur Armory ou Bitcoin, vous devriez visiter le &lt;a href=&quot;https://bitcointalk.org/index.php?board=97.0&quot;&gt;forum Armory&lt;/a&gt;
&lt;byte value=&quot;x9&quot;/&gt; et &lt;a href=&quot;https://bitcoin.org&quot;&gt;Bitcoin.org&lt;/a&gt;. Si vous éprouvez des problèmes lors de l&apos;utilisation de ce logiciel, veuillez visiter le &lt;a href=&quot;https://bitcointalk.org/index.php?board=97.0&quot;&gt;forum Armory&lt;/a&gt;. Des utilisateurs
&lt;byte value=&quot;x9&quot;/&gt; vous y assisteront.
&lt;br&gt;&lt;br&gt;
&lt;b&gt;&lt;u&gt;IMPORTANT :&lt;/u&gt;&lt;/b&gt; Faites une sauvegarde de vos porte-monnaie ! Les sauvegardes papier vous protègent &lt;i&gt;à jamais&lt;/i&gt; contre les mots de passe oubliés, les défaillances de disque dur et facilitent la récupération de vos fonds par votre famille si quelque chose de terrible vous arrive. &lt;i&gt; Chaque porte-monnaie ne doit être sauvegardé qu&apos;une fois, sans savoir à renouveler la sauvegarde&lt;/i&gt; Sans elle, vous risquez de perdre tous vos bitcoins !
&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4121"/>
        <source>&lt;p&gt;&lt;b&gt;You now have access to all the features Armory has to offer!&lt;/b&gt;&lt;br&gt;To see your balances and transaction history, please click on the &quot;Transactions&quot; tab above this text.  &lt;br&gt;Here&apos;s some things you can do with Armory Bitcoin Client:&lt;br&gt;</source>
        <translation>&lt;p&gt;&lt;b&gt;Vous pouvez maintenant accéder à toutes les fonctions qu&apos;Armory offre !&lt;/b&gt;&lt;br&gt;Pour visualiser vos soldes et l&apos;historique transactionnel, veuillez cliquer sur l&apos;onglet « Transactions » ci-dessus. &lt;br&gt;Voici différentes choses que vous pouvez faire avec le client Armory Bitcoin :&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4128"/>
        <source>If you experience any performance issues with Armory, please confirm that Bitcoin Core is running and &lt;i&gt;fully synchronized with the Bitcoin network&lt;/i&gt;.  You will see a green checkmark in the bottom right corner of the Bitcoin Core window if it is synchronized.  If not, it is recommended you close Armory and restart it only when you see that checkmark.&lt;br&gt;&lt;br&gt;</source>
        <translation>Si vous éprouvez des problèmes de performances avec Armory, veuillez vous assurer que Bitcoin Core est en cours d&apos;exécution et &lt;i&gt;est complètement synchronisé avec le réseau Bitcoin/&lt;i&gt;. Vous verrez une coche verte en bas à droite de la fenêtre Bitcoin Core s&apos;il est synchronisé. Dans le cas contraire, il est recommandé de fermer Armory et de le redémarrer seulement lorsque vous verrez la coche verte.&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4128"/>
        <source>&lt;b&gt;Please backup your wallets!&lt;/b&gt;  Armory wallets are &quot;deterministic&quot;, meaning they only need to be backed up one time (unless you have imported external addresses/keys). Make a backup and keep it in a safe place!  All funds from Armory-generated addresses will always be recoverable with a paper backup, any time in the future.  Use the &quot;Backup Individual Keys&quot; option for each wallet to backup imported keys.&lt;/p&gt;</source>
        <translation>&lt;b&gt;Veuillez sauvegarder vos porte-monnaie !&lt;/b&gt; Les porte-monnaie Armory sont « déterministes », ce qui signifie qu&apos;ils n&apos;ont besoin d&apos;être sauvegardés qu&apos;une seule fois (à moins que vous n&apos;ayez importé des adresses ou des clés externes). Effectuez une sauvegarde et conservez-la en lieu sûr ! Tous les fonds provenant d&apos;adresses générées par Armory seront toujours récupérables avec une sauvegarde papier, n&apos;importe quand à l&apos;avenir. Utilisez l&apos;option « Sauvegarder les clés individuels » pour chaque porte-monnaie afin de sauvegarder les clés importées.&lt;/p&gt;
</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4596"/>
        <source>Armory is currently online, but you have requested a sweep operation on one or more private keys.  This requires searching the global transaction history for the available balance of the keys to be swept. &lt;br&gt;&lt;br&gt;Press the button to start the blockchain scan, which will also put Armory into offline mode for a few minutes until the scan operation is complete</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4156"/>
        <source>&lt;b&gt;Wallet balances may be incorrect until the rescan operation is performed!&lt;/b&gt;&lt;br&gt;&lt;br&gt;Armory is currently online, but addresses/keys have been added without rescanning the blockchain.  You may continue using Armory in online mode, but any transactions associated with the new addresses will not appear in the ledger. &lt;br&gt;&lt;br&gt;Pressing the button above will put Armory into offline mode for a few minutes until the scan operation is complete.</source>
        <translation>&lt;b&gt;Les soldes des porte-monnaie pourraient être erronés tant que la réanalyse n&apos;est pas effectuée !&lt;/b&gt;&lt;br&gt;&lt;br&gt;Armory est actuellement hors ligne, mais des adresses ou des clés ont été ajoutées sans réanalyser la chaîne de blocs. Vous pouvez continuer à utiliser Armory en mode en ligne, mais toute transaction associée aux nouvelles adresses n&apos;apparaîtra pas dans le grand livre. &lt;br&gt;&lt;br&gt;Appuyer sur le bouton ci-dessus basculera Armory en mode hors ligne pendant quelques minutes jusqu&apos;à la fin de l&apos;opération d&apos;analyse.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4168"/>
        <source>There is no connection to the internet, and there is no other Bitcoin software running.  Most likely you are here because this is a system dedicated to manage offline wallets! &lt;br&gt;&lt;br&gt;&lt;b&gt;If you expected Armory to be in online mode&lt;/b&gt;, please verify your internet connection is active, then restart Armory.  If you think the lack of internet connection is in error (such as if you are using Tor), then you can restart Armory with the &quot;--skip-online-check&quot; option, or change it in the Armory settings.&lt;br&gt;&lt;br&gt;If you do not have Bitcoin Core installed, you can download it from &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</source>
        <translation>Il n&apos;y a aucune connexion à Internet et aucun autre logiciel Bitcoin n’est en cours d&apos;exécution. Vous êtes probablement ici, car c&apos;est un système consacré à la gestion des porte-monnaie hors ligne ! &lt;br&gt;&lt;br&gt;&lt;b&gt;Si vous vous attendiez à ce qu&apos;Armory soit en mode en ligne, veuillez vérifier si votre connexion Internet est active, puis redémarrez Armory. Si vous pensez que l&apos;absence d&apos;Internet est une erreur (par exemple si vous utilisez Tor), vous pouvez redémarrer Armory avec l&apos;option « --skip-online-check », ou la changer dans les paramètres d&apos;Armory.&lt;br&gt;&lt;br&gt;Si Bitcoin Core n&apos;est pas installé, vous pouvez le télécharger de &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4191"/>
        <source>You are currently in offline mode, but can switch to online mode by pressing the button above.  However, it is not recommended that you switch until Bitcoin Core/bitcoind is fully synchronized with the bitcoin network.  You will see a green checkmark in the bottom-right corner of the Bitcoin Core window when it is finished.&lt;br&gt;&lt;br&gt;Switching to online mode will give you access to more Armory functionality, including sending and receiving bitcoins and viewing the balances and transaction histories of each of your wallets.&lt;br&gt;&lt;br&gt;</source>
        <translation>Vous êtes actuellement en mode hors ligne, mais vous pouvez basculer en mode en ligne en appuyant sur le bouton ci-dessus. Cependant, il n&apos;est pas recommandé de basculer tant que Bitcoin Core ou bitcoind n&apos;est pas complètement synchronisé avec le réseau Bitcoin. Vous apercevrez une coche verte en bas à droite de la fenêtre Bitcoin Core quand la synchronisation sera terminée.&lt;br&gt;&lt;br&gt; En basculant en mode hors ligne, vous aurez accès à plus de fonctions d&apos;Armory, incluant l&apos;envoie et la réception de bitcoins, la visualisation des soldes et des historiques transactionnels de chacun de vos porte-monnaie.&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4205"/>
        <source>You are currently in offline mode because Bitcoin Core is not running.  To switch to online mode, start Bitcoin Core and let it synchronize with the network -- you will see a green checkmark in the bottom-right corner when it is complete.  If Bitcoin Core is already running and you believe the lack of connection is an error (especially if using proxies), please see &lt;a href=&quot;https://bitcointalk.org/index.php?topic=155717.msg1719077#msg1719077&quot;&gt;this link&lt;/a&gt; for options.&lt;br&gt;&lt;br&gt;&lt;b&gt;If you prefer to have Armory do this for you&lt;/b&gt;, then please check &quot;Let Armory run Bitcoin Core in the background&quot; under &quot;File&quot;-&gt;&quot;Settings.&quot;&lt;br&gt;&lt;br&gt;If you already know what you&apos;re doing and simply need to fetch the latest version of Bitcoin Core, you can download it from &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</source>
        <translation>Vous êtes actuellement en mode hors ligne, car Bitcoin Core n&apos;est pas en cours d&apos;exécution. Pour basculer en mode en ligne, démarrez Bitcoin Core laissez-le se synchroniser avec le réseau. Vous apercevrez une coche verte en bas à droite quand la synchronisation sera terminée. 
Si Bitcoin Core est déjà en cours d&apos;exécution et que vous pensez que le manque de connexion à Internet est une erreur (particulièrement si vous utilisez des serveurs mandataires), veuillez consulter &lt;a href=&quot;https://bitcointalk.org/index.php?topic=155717.msg1719077#msg1719077&quot;&gt;ce lien&lt;/a&gt; pour obtenir plus d&apos;options.&lt;br&gt;&lt;br&gt;&lt;b&gt;Si vous préférez qu&apos;Armory le fasse pour vous, veuillez cocher « Laisser Armory exécuter Bitcoin Core en arrière-plan sous « Fichier » - « Paramètres ».&lt;br&gt;&lt;br&gt;Si vous savez déjà ce que vous faites et qu&apos;il vous suffit d&apos;aller récupérer la dernière version de Bitcoin Core, vous pouvez la télécharger de &lt;a href=&quot;https://bitcoin.org&quot;&gt;https://bitcoin.org&lt;/a&gt;.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4224"/>
        <source>You are currently in offline mode because Armory could not detect an internet connection.  If you think this is in error, then restart Armory using the &quot; --skip-online-check&quot; option, or adjust the Armory settings.  Then restart Armory.&lt;br&gt;&lt;br&gt;If this is intended to be an offline computer, note that it is not necessary to have Bitcoin Core or bitcoind running.</source>
        <translation>Vous êtes actuellement en mode hors ligne, car Armory n&apos;a pas pu détecter une connexion Internet. Si vous pensez que c&apos;est une erreur, redémarrez Armory en utilisant l&apos;option « --skip-online-check », ou ajustez les paramètres d&apos;Armory. Redémarrez ensuite Armory.&lt;br&gt;&lt;br&gt;Si cet ordinateur est censé être un ordinateur hors ligne, veuillez prendre note qu&apos;il n&apos;est pas nécessaire d&apos;exécuter Bitcoin Core ou bitcoind.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4235"/>
        <source>You are currently in offline mode because Armory could not find the blockchain files produced by Bitcoin Core.  Do you run Bitcoin Core (or bitcoind) from a non-standard directory?   Armory expects to find the blkXXXX.dat files in &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt; If you know where they are located, please restart Armory using the &quot; --satoshi-datadir=[path]&quot; to notify Armory where to find them.</source>
        <translation>Vous êtes actuellement en mode hors ligne, car Armory n&apos;a pas trouvé les fichiers de la chaîne de blocs produit par Bitcoin Core. Exécutez-vous Bitcoin Core (ou bitcoind) à partir d&apos;un répertoire non standard ? Armory s&apos;attend à trouver les fichiers blkXXXX.dat &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt;. Si vous savez où ils se situent, veuillez redémarrer en utilisant l&apos;option « --satoshi-datadir=[path] » pour indiquer à Armory où les trouver.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4245"/>
        <source>Armory was previously online, but the connection to Bitcoin Core/bitcoind was interrupted.  You will not be able to send bitcoins or confirm receipt of bitcoins until the connection is reestablished.  &lt;br&gt;&lt;br&gt;Please check that Bitcoin Core is open and synchronized with the network.  Armory will &lt;i&gt;try to reconnect&lt;/i&gt; automatically when the connection is available again.  If Bitcoin Core is available again, and reconnection does not happen, please restart Armory.&lt;br&gt;&lt;br&gt;</source>
        <translation>Armory était en ligne auparavant, mais la connexion vers Bitcoin Core/bitcoind a été interrompue. Vous ne pourrez pas envoyer de bitcoins ou confirmer la réception de bitcoins tant que la connexion ne sera pas rétablie. &lt;br&gt;&lt;br&gt;Veuillez vous assurer que Bitcoin Core est ouvert et synchronisé avec le réseau. Armory &lt;i&gt;essaiera de se reconnecter&lt;/i&gt; automatiquement quand la connexion sera rétablie. Si Bitcoin Core est disponible de nouveau et que la connexion n&apos;a pas lieu, veuillez redémarrer Armory.&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4255"/>
        <source>Please wait while the global transaction history is scanned. Armory will go into online mode automatically, as soon as the scan is complete.</source>
        <translation>Veuillez patienter pendant que l&apos;historique transactionnel global est analysé. Armory basculera automatiquement en mode en ligne quand l&apos;analyse sera terminée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4260"/>
        <source>Armory is scanning the global transaction history to retrieve information about your wallets.  The &quot;Transactions&quot; tab will be updated with wallet balance and history as soon as the scan is complete.  You may manage your wallets while you wait.&lt;br&gt;&lt;br&gt;</source>
        <translation>Armory analyse l&apos;historique transactionnel global afin de récupérer des informations sur vos porte-monnaie. L&apos;onglet « Transactions » sera mis à jour avec les soldes et l&apos;historique des porte-monnaie dès que l&apos;analyse sera terminée. Vous pouvez gérer vos porte-monnaie en attendant.&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4272"/>
        <source>It appears you are already running Bitcoin software (Bitcoin Core or bitcoind). Unlike previous versions of Armory, you should &lt;u&gt;not&lt;/u&gt; run this software yourself --  Armory will run it in the background for you.  Either close the Bitcoin application or adjust your settings.  If you change your settings, then please restart Armory.</source>
        <translation>Il semble que le logiciel Bitcoin est déjà en cours d&apos;exécution (Bitcoin Core ou bitcoind). Contrairement aux anciennes versions d&apos;Armory, vous &lt;u&gt;ne devriez pas&lt;/u&gt; exécuter ce logiciel vous-même. Armory l&apos;exécutera pour vous en arrière-plan. Si vous modifiez vos paramètres, veuillez alors redémarrer Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4281"/>
        <source>&lt;b&gt;Only one more step to getting online with Armory!&lt;/b&gt;   You must install the Bitcoin software from https://bitcoin.org in order for Armory to communicate with the Bitcoin network.  If the Bitcoin software is already installed and/or you would prefer to manage it yourself, please adjust your settings and restart Armory.</source>
        <translation>&lt;b&gt;Plus qu&apos;une étape avant de passer en ligne avec Armory !&lt;/b&gt; Vous devez installer le logiciel Bitcoin de https://bitcoin.org afin qu&apos;Armory puisse communiquer avec le réseau Bitcoin. Si le logiciel Bitcoin est déjà installé ou si vous préférez le gérer vous-même, veuillez ajuster vos paramètres et redémarrer Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4289"/>
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
        <translation>&lt;b&gt;Afin de maximiser votre sécurité, le moteur Bitcoin est en train de télécharger et de vérifier le grand livre des transactions globales.&lt;u&gt;Cela prendra plusieurs heures, mais ne doit être fait qu&apos;une seule fois&lt;/u&gt;!&lt;/b&gt; Il est habituellement préférable de le laisser tourner toute la nuit pour ce processus d&apos;initialisation. Les chargements suivants ne prendront quelque quelques minutes.
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Veuillez noter :&lt;/b&gt; entre Armory et le moteur Bitcoin, il vous faudra de 40 à 50 Go d&apos;espace disque libre pour contenir l&apos;historique transactionnel global.
&lt;br&gt;&lt;br&gt;
Pendant que vous patientez, vous pouvez gérer vos porte-monnaie : créer de nouveaux porte-monnaie, faire des sauvegardes papier ou numériques, créer des adresses Bitcoin pour recevoir des paiements, signer des messages ou importer des clés privées. Vous recevrez toujours vos paiements en bitcoins, que vous soyez en ligne ou non, mais vous devrez vérifier ces paiements par le biais d&apos;un autre service tant qu&apos;Armory n&apos;aura pas terminé son processus d&apos;initialisation.</translation>
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
        <location filename="ArmoryQt.py" line="4322"/>
        <source>Armory&apos;s communication with the Bitcoin network was interrupted. This usually does not happen unless you closed the process that Armory was using to communicate with the network. Armory requires %1 to be running in the background, and this error pops up if it disappears.&lt;br&gt;&lt;br&gt;You may continue in offline mode, or you can close all Bitcoin processes and restart Armory.</source>
        <translation>La communication d&apos;Armory avec le réseau Bitcoin a été interrompue. Cela n&apos;arrive habituellement pas, à moins que vous n&apos;ayez fermé le processus qu&apos;Armory utilisait pour communiquer avec le réseau. Armory exige que %1 fonctionne en arrière-plan et cette erreur surgit si ce processus disparaît.&lt;br&gt;&lt;br&gt; Vous pouvez continuer en mode hors ligne, ou  fermer tous les processus Bitcoin et redémarrer Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4331"/>
        <source>Armory has experienced an issue trying to communicate with the Bitcoin software.  The software is running in the background, but Armory cannot communicate with it through RPC as it expects to be able to.  If you changed any settings in the Bitcoin home directory, please make sure that RPC is enabled and that it is accepting connections from localhost.  &lt;br&gt;&lt;br&gt;If you have not changed anything, please export the log file (from the &quot;File&quot; menu) and open an issue at https://github.com/goatpig/BitcoinArmory/issues</source>
        <translation>Armory a rencontré une difficulté en tentant de communiquer avec le logiciel Bitcoin. Le logiciel est en cours d&apos;exécution en arrière-plan, mais  Armory ne peut pas communiquer avec lui par RPC comme il s&apos;attend à pouvoir le faire. Si vous avez modifié des paramètres dans votre répertoire Bitcoin personnel, veuillez vous assurer que RPC est activé et accepte les connexions de l&apos;hôte local. &lt;br&gt;&lt;br&gt; Si vous n&apos;avez rien changé, veuillez exporter le fichier journal (dans le menu « Fichier ») et signaler le problème sur https://github.com/goatpig/BitcoinArmory/issues</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4342"/>
        <source>Armory does not detect internet access, but it does detect running Bitcoin software.  Armory is in offline-mode. &lt;br&gt;&lt;br&gt;If you are intending to run an offline system, you will not need to have the Bitcoin software installed on the offline computer.  It is only needed for the online computer. If you expected to be online and the absence of internet is an error, please restart Armory using the &quot;--skip-online-check&quot; option.  </source>
        <translation>Armory ne détecte aucun accès à Internet, mais détecte un logiciel Bitcoin en cours d&apos;exécution. Armory est en mode hors ligne. &lt;br&gt;&lt;br&gt; S&apos;il est de votre intention d&apos;avoir un système hors ligne, il est inutile d&apos;installer le logiciel Bitcoin sur l&apos;ordinateur hors ligne. Seul un ordinateur en ligne en a besoin. Si vous vous attendiez à être en ligne et que l&apos;absence de connexion à Internet est une erreur, veuillez redémarrer Armory en utilisant l&apos;option « --skip-online-check».</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4352"/>
        <source>Armory was started in offline-mode, but detected you are running Bitcoin software.  If you are intending to run an offline system, you will &lt;u&gt;not&lt;/u&gt; need to have the Bitcoin software installed or running on the offline computer.  It is only required for being online. </source>
        <translation>Armory a été démarré en mode hors ligne, mais a détecté que le logiciel Bitcoin est en cours d&apos;exécution. S&apos;il est de votre intention d&apos;avoir un système hors ligne, il est &lt;u&gt;inutile&lt;/u&gt; d&apos;installer ou d&apos;exécuter le logiciel Bitcoin sur l&apos;ordinateur hors ligne. Il est seulement exigé pour être en ligne.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4809"/>
        <source>The Bitcoin software indicates there is a problem with its databases.  This can occur when Bitcoin Core/bitcoind is upgraded or downgraded, or sometimes just by chance after an unclean shutdown.&lt;br&gt;&lt;br&gt;You can either revert your installed Bitcoin software to the last known working version (but not earlier than version 0.8.1) or delete everything &lt;b&gt;except&lt;/b&gt; &quot;wallet.dat&quot; from the your Bitcoin home directory:&lt;br&gt;&lt;br&gt;&lt;font face=&quot;courier&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;If you choose to delete the contents of the Bitcoin home directory, you will have to do a fresh download of the blockchain again, which will require a few hours the first time.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4383"/>
        <source>
               There was an error starting the underlying Bitcoin engine.
               This should not normally happen.  Usually it occurs when you
               have been using Bitcoin Core prior to using Armory, especially
               if you have upgraded or downgraded Bitcoin Core recently.
               Output from bitcoind:&lt;br&gt;</source>
        <translation>
Une erreur est survenue lors du démarrage du moteur Bitcoin sous-jacent. Cela ne devrait pas arriver normalement et se produit habituellement quand vous avez utilisé Bitcoin Core avant d&apos;utiliser Armory, particulièrement si vous avez appliqué une mise à niveau supérieure ou inférieure de Bitcoin Core récemment. La sortie de bitcoind est :&lt;b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4392"/>
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
        <translation>
Une erreur est survenue lors du démarrage du moteur Bitcoin sous-jacent. Cela ne devrait pas arriver normalement et se produit habituellement quand vous avez utilisé Bitcoin Core avant d&apos;utiliser Armory, particulièrement si vous avez appliqué une mise à niveau supérieure ou inférieure de Bitcoin Core récemment.
&lt;br&gt;&lt;br&gt;
Malheureusement, cette erreur est tellement étrange qu&apos;Armory ne la reconnaît pas. Veuillez aller dans « Exporter le fichier journal » du menu « Fichier »  signaler un problème à https://github.com/goatpig/BitcoinArmory/issues.
Nous sommes désolés de cet inconvénient !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4522"/>
        <source>Armory is &lt;u&gt;offline&lt;/u&gt;</source>
        <translation>Armory est &lt;u&gt;hors ligne&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4507"/>
        <source>In case you actually do have internet access, you can use the following links to get Armory installed.  Or change your settings.</source>
        <translation>Au cas où vous avez effectivement accès à Internet, vous pouvez utiliser les liens suivants pour installer Armory, ou changez vos paramètres.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4526"/>
        <source>Cannot find Bitcoin Home Directory</source>
        <translation>Impossible de trouver le répertoire Bitcoin personnel</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4534"/>
        <source>Check Again</source>
        <translation>Revérifier</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4556"/>
        <source>Initializing Bitcoin Engine</source>
        <translation>Initialisation du moteur Bitcoin</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4616"/>
        <source>Synchronizing with Network</source>
        <translation>Synchronisation avec le réseau</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4570"/>
        <source>Since version 0.88, Armory runs bitcoind in the background.  You can switch back to the old way in the Settings dialog. </source>
        <translation>Depuis la version 0.88, Armory exécute bitcoind en arrière-plan. Vous pouvez revenir à l&apos;ancienne méthode dans la boîte de dialogue Paramètres.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4588"/>
        <source>Armory is disconnected</source>
        <translation>Armory est déconnecté</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4595"/>
        <source>Armory is online!</source>
        <translation>Armory est en ligne !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4624"/>
        <source>Preparing Databases</source>
        <translation>Préparation des bases de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4793"/>
        <source>&lt;font color=%1&gt;Connected (%2 blocks)&lt;/font&gt; </source>
        <translation>&lt;font color=%1&gt;Connecté (%2 blocs)&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4799"/>
        <source>Last block received %1 ago</source>
        <translation>Le dernier bloc a été reçu il y a %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4805"/>
        <source>&lt;font color=%1&gt;Node offline (%2 blocks)&lt;/font&gt; </source>
        <translation>&lt;font color=%1&gt;Le nœud est hors ligne (%2 blocs)&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4810"/>
        <source>Disconnected from Bitcoin Node, cannot update history &lt;br&gt;&lt;br&gt;Last known block: %1 &lt;br&gt;Received %2 ago</source>
        <translation>Armory est déconnecté du nœud Bitcoin. Impossible de mettre l&apos;historique à jour &lt;br&gt;&lt;br&gt;Dernier bloc connu : %1 &lt;br&gt;Reçu il y a %2</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4947"/>
        <source>BDM error!</source>
        <translation>Erreur GDB !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4941"/>
        <source>Rebuild and rescan on next start</source>
        <translation>Reconstruire et réanalyser lors du prochain démarrage</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4947"/>
        <source>Factory reset on next start</source>
        <translation>Reinitialisation générale lors du prochain démarrage</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4953"/>
        <source>BlockDataManager Warning</source>
        <translation>Avertissement du gestionnaire des données de blocs</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5002"/>
        <source>Disconnected</source>
        <translation>Déconnecté</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5002"/>
        <source>Connection to Bitcoin Core client lost!  Armory cannot send nor receive bitcoins until connection is re-established.</source>
        <translation>La connexion au client Bitcoin Core a été perdue ! Armory ne peut ni envoyer ni recevoir de bitcoins tant que la connexion n&apos;est pas rétablie.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5008"/>
        <source>Connected</source>
        <translation>Connecté</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5008"/>
        <source>Connection to Bitcoin Core re-established</source>
        <translation>La connexion à Bitcoin Core a été rétablie</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5689"/>
        <source>Database Error</source>
        <translation>Erreur de base de données</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5469"/>
        <source>
                           The DB has returned the following
                           error: &lt;br&gt;&lt;br&gt;
                           &lt;b&gt; %1 &lt;/b&gt; &lt;br&gt;&lt;br&gt;
                           Armory will now shutdown. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5149"/>
        <source>Wallet %1 (%2)</source>
        <translation>Porte-monnaie %1 (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5156"/>
        <source>Lockbox %1 (%2)</source>
        <translation>Coffre %1 (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5250"/>
        <source>Bitcoins Received!</source>
        <translation>Des bitcoins ont été reçus !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5269"/>
        <source>Amount:  %1 BTC</source>
        <translation>Montant : %1 BTC</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5166"/>
        <source>Recipient:  %1</source>
        <translation>Destinataire : %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5268"/>
        <source>Bitcoins Sent!</source>
        <translation>Des bitcoins ont été envoyés !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5171"/>
        <source>Sender:  %1</source>
        <translation>Expéditeur :  %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5222"/>
        <source>Wallet &quot;%1&quot; (%2)</source>
        <translation>Porte-monnaie « %1  » (%2)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5230"/>
        <source>Lockbox %1-of-%2 &quot;%3&quot; (%4)</source>
        <translation>Coffre %1-de-%2 « %3 » (%4)</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5241"/>
        <source>Your bitcoins just did a lap!</source>
        <translation>Vos bitcoins viennent de faire une boucle !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5241"/>
        <source>%1 just sent some BTC to itself!</source>
        <translation>%1 vient de s&apos;envoyer des BTC !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5252"/>
        <source>From:    %2</source>
        <translation>De : %2</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5266"/>
        <source>&lt;Multiple Recipients&gt;</source>
        <translation>&lt;Plusieurs destinataires&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5270"/>
        <source>From:    %1</source>
        <translation>De : %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5271"/>
        <source>To:      %1</source>
        <translation>À : %1</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5287"/>
        <source>Minimize or Close</source>
        <translation>Minimiser ou fermer</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5287"/>
        <source>Would you like to minimize Armory to the system tray instead of closing it?</source>
        <translation>Souhaitez-vous minimiser Armory vers la barre de notification plutôt que de le fermer ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5287"/>
        <source>Remember my answer</source>
        <translation>Mémoriser ma réponse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5287"/>
        <source>Minimize</source>
        <translation>Minimiser</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5287"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5490"/>
        <source>All wallets are consistent</source>
        <translation>Tous les porte-monnaie sont cohérents</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5494"/>
        <source>Consistency Check Failed!</source>
        <translation>Échec du contrôle de cohérence !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5506"/>
        <source>
               The wallet analysis tool will become available
               as soon as Armory is done loading.   You can close this
               window and it will reappear when ready.</source>
        <translation>
L&apos;outil d&apos;analyse des porte-monnaie sera disponible dès qu&apos;Armory aura fini de charger. Vous pouvez fermer cette fenêtre et elle réapparaîtra quand l&apos;outil sera prêt.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5539"/>
        <source>
                  &lt;b&gt;The following dialogs need closed before you can
                  run the wallet analysis tool:&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Les boîtes de dialogue suivantes doivent être fermées avant de pouvoir exécuter l&apos;outil d&apos;analyse des porte-monnaie :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5563"/>
        <source>Wallet Consistency Check: %p%</source>
        <translation>Contrôle de cohérence du porte-monnaie : %p%</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5689"/>
        <source>
                           Armory failed to spawn the DB!&lt;br&gt; 
                           Continuing operations in offline mode instead. &lt;br&gt;
                           Refer to the dbLog.txt for more information.</source>
        <translation>
Échec de mise en place de la BD par Armory !&lt;br&gt;
Poursuite des opérations en mode hors ligne. &lt;br&gt;
Consulter dbLog.txt pour plus d&apos;informations.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5807"/>
        <source>Filter:</source>
        <translation>Filtre :</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5825"/>
        <source>Transactions</source>
        <translation>Transactions</translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="3017"/>
        <source>You cannot sweep the funds from the address(es) you specified, because
               the transaction fee would be equal to or greater than the amount 
               swept.
               &lt;br&gt;&lt;br&gt;
               &lt;b&gt;Balance of address(es):&lt;/b&gt; %1&lt;br&gt;
               &lt;b&gt;Fee to sweep address(es):&lt;/b&gt; %2
               &lt;br&gt;&lt;br&gt;The sweep operation has been canceled.</source>
        <translation><numerusform>Vous ne pouvez pas balayer les fonds de l&apos;adresse que vous avez indiquée, car les frais de transaction seraient égaux ou supérieurs au
montant récupéré.
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Solde de l&apos;adresse :&lt;/b&gt; %1&lt;br&gt;
&lt;b&gt;Frais pour balayer l&apos;adresse :&lt;/b&gt; %2
&lt;br&gt;&lt;br&gt;L&apos;opération de balayage a été annulée.</numerusform><numerusform>Vous ne pouvez pas balayer les fonds des adresses que vous avez indiquées, car les frais de transaction seraient égaux ou supérieurs au
montant récupéré.
&lt;br&gt;&lt;br&gt;
&lt;b&gt;Solde des adresses :&lt;/b&gt; %1&lt;br&gt;
&lt;b&gt;Frais pour balayer les adresses :&lt;/b&gt; %2
&lt;br&gt;&lt;br&gt;L&apos;opération de balayage a été annulée.</numerusform></translation>
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
        <location filename="ArmoryQt.py" line="4309"/>
        <source>The software is downloading and processing the latest activity on the network related to your wallet(s).  This should take only a few minutes.  While you wait, you can manage your wallet(s).  &lt;br&gt;&lt;br&gt;Now would be a good time to make paper (or digital) backups of your wallet(s) if you have not done so already!  You are protected &lt;i&gt;forever&lt;/i&gt; from hard-drive loss, or forgetting you password. If you do not have a backup, you could lose all of your Bitcoins forever!</source>
        <translation><numerusform>Le logiciel télécharge et traite la dernière activité reliée à votre porte-monnaie sur le réseau. Cela ne devrait prendre que quelques minutes. En attendant, vous pouvez gérer votre porte-monnaie. &lt;br&gt;&lt;br&gt;Il serait bon de faire une sauvegarde papier (ou numérique) de votre porte-monnaie si ce n&apos;est pas déjà fait ! Vous serez ainsi protégé &lt;i&gt;à jamais&lt;/i&gt; contre la perte de disque dur ou l&apos;oubli de mot de passe. Si vous ne possédez pas de sauvegarde, vous pourriez perdre irrémédiablement tous vos bitcoins !</numerusform><numerusform>Le logiciel télécharge et traite la dernière activité reliée à vos porte-monnaie sur le réseau. Cela ne devrait prendre que quelques minutes. En attendant, vous pouvez gérer vos porte-monnaie. &lt;br&gt;&lt;br&gt;Il serait bon de faire des sauvegardes papier (ou numériques) de vos porte-monnaie si ce n&apos;est pas déjà fait ! Vous serez ainsi protégé &lt;i&gt;à jamais&lt;/i&gt; contre la perte de disque dur ou l&apos;oubli de mot de passe. Si vous ne possédez pas de sauvegarde, vous pourriez perdre irrémédiablement tous vos bitcoins !</numerusform></translation>
    </message>
    <message numerus="yes">
        <location filename="ArmoryQt.py" line="3010"/>
        <source>The private key(s) you have provided does not appear to contain
               any funds.  There is nothing to sweep.</source>
        <translation><numerusform>La clé privée que vous avez fournie ne semble pas contenir de fonds. Il n&apos;y a rien à balayer.</numerusform><numerusform>Les clés privées que vous avez fournies ne semblent pas contenir de fonds. Il n&apos;y a rien à balayer.</numerusform></translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4046"/>
        <source>The following functionalities are available while scanning in offline mode:&lt;ul&gt;&lt;li&gt;Create new wallets&lt;/li&gt;&lt;li&gt;Generate receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign transactions created from an online system&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, even if you are offline.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation>Les fonctions suivantes sont proposées lors de l&apos;analyse en mode hors ligne : &lt;ul&gt;&lt;li&gt;Créer de nouveaux porte-monnaie&lt;/li&gt;&lt;li&gt;Générer des adresses de réception pour vos porte-monnaie&lt;/li&gt;&lt;li&gt;Créer des sauvegardes de vos porte-monnaie (imprimées ou numériques)&lt;/li&gt;&lt;li&gt;Changer les paramètres de chiffrement d&apos;un porte-monnaie&lt;/li&gt;&lt;li&gt;Signer des transactions créées à partir d&apos;un système en ligne&lt;/li&gt;&lt;li&gt;Signer des messages&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE :&lt;/b&gt; le réseau Bitcoin traitera les transactions vers vos adresses, même si vous êtes hors ligne. Il est tout à fait possible de créer et de distribuer des adresses de paiement alors qu&apos;Armory est hors ligne. Vous ne pourrez juste pas vérifier ses paiements jusqu&apos;à la prochaine mise en ligne d&apos;Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4062"/>
        <source>The following functionalities are available in offline mode:&lt;ul&gt;&lt;li&gt;Create, import or recover wallets&lt;/li&gt;&lt;li&gt;Generate new receiving addresses for your wallets&lt;/li&gt;&lt;li&gt;Create backups of your wallets (printed or digital)&lt;/li&gt;&lt;li&gt;Import private keys to wallets&lt;/li&gt;&lt;li&gt;Change wallet encryption settings&lt;/li&gt;&lt;li&gt;Sign messages&lt;/li&gt;&lt;li&gt;&lt;b&gt;Sign transactions created from an online system&lt;/b&gt;&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE:&lt;/b&gt;  The Bitcoin network &lt;u&gt;will&lt;/u&gt; process transactions to your addresses, regardless of whether you are online.  It is perfectly okay to create and distribute payment addresses while Armory is offline, you just won&apos;t be able to verify those payments until the next time Armory is online.</source>
        <translation>Les fonctions suivantes sont proposées en mode hors ligne : &lt;ul&gt;&lt;li&gt;Créer, importer ou récupérer des porte-monnaie&lt;/li&gt;&lt;li&gt;Générer de nouvelles adresses de réception pour vos porte-monnaie&lt;/li&gt;&lt;li&gt;Créer des sauvegardes de vos porte-monnaie (imprimées ou numériques)&lt;/li&gt;&lt;li&gt;Importer des clés privées dans les porte-monnaie&lt;/li&gt;&lt;li&gt;Changer les paramètres de chiffrement d&apos;un porte-monnaie&lt;/li&gt;&lt;li&gt;Signer des messages&lt;/li&gt;&lt;li&gt;Signer des transactions créées à partir d&apos;un système en ligne&lt;/li&gt;&lt;li&gt;Signer des messages&lt;/li&gt;&lt;/ul&gt;&lt;br&gt;&lt;br&gt;&lt;b&gt;NOTE :&lt;/b&gt; le réseau Bitcoin &lt;u&gt;traitera&lt;/u&gt; les transactions vers vos adresses, que vous soyez en ligne ou pas. Il est tout à fait possible de créer et de distribuer des adresses de paiement alors qu&apos;Armory est hors ligne. Vous ne pourrez juste pas vérifier ses paiements jusqu&apos;à la prochaine mise en ligne d&apos;Armory.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="725"/>
        <source>
            Armory is using the default Bitcoin directory because
            the Bitcoin directory specified in the command line could
            not be found.</source>
        <translation>
Armory utilise le répertoire Bitcoin par défaut, car le répertoire Bitcoin précisé dans la ligne de commande est introuvable.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1154"/>
        <source>
         The next time you restart Armory, it will rebuild and rescan
         the entire blockchain database.  This operation can take between
         30 minutes and 4 hours depending on your system speed.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a rebuild on the next Armory restart?</source>
        <translation>
La prochaine fois que vous redémarrez Armory, elle reconstruira et réanalysera l&apos;intégralité de la base de données de la chaîne de blocs. Cette opération peut prendre entre 30 minutes et 4 heures selon la vitesse de votre système.&lt;br&gt;&lt;br&gt;
Souhaitez-vous forcer une reconstruction lors du prochain redémarrage d&apos;Armory ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1166"/>
        <source>
         The next time you restart Armory, it will rescan the balance of
         your wallets. This operation typically takes less than a minute.
         &lt;br&gt;&lt;br&gt;
         Do you wish to force a balance rescan on the next Armory restart?</source>
        <translation>
La prochaine fois que vous redémarrez Armory, elle réanalysera le solde de vos porte-monnaie. Cette opération prend habituellement moins d&apos;un minute.&lt;br&gt;&lt;br&gt;
Souhaitez-vous forcer une réanalyse du solde lors du prochain redémarrage d&apos;Armory ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1628"/>
        <source>
                  No passphrase was selected for the encrypted backup.
                  No backup was created.</source>
        <translation>
Aucune phrase de passe n&apos;a été choisie pour la sauvegarde chiffrée.
Aucune sauvegarde n&apos;a été créée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4146"/>
        <source>Armory is currently online, but you have requested a sweep operation on one or more private keys.  This requires searching the global transaction history for the available balance of the keys to be swept. &lt;br&gt;&lt;br&gt;Press the button to start the blockchain scan, which will also put Armory into offline mode for a few minutes until the scan operation is complete.</source>
        <translation>Armory est actuellement en ligne, mais vous avez demandé une opération de balayage sur une ou plusieurs clé privées. Le solde disponible des clés à balayer doit être recherché dans l&apos;historique transactionnel global.&lt;br&gt;&lt;br&gt;Appuyez sur le bouton pour lancer l&apos;analyse de la chaîne de blocs, ce qui fera aussi basculer Armory en mode hors ligne pendant quelques minutes jusqu&apos;à la fin de l&apos;opération d&apos;analyse.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="4359"/>
        <source>The Bitcoin software indicates there is a problem with its databases.  This can occur when Bitcoin Core/bitcoind is upgraded or downgraded, or sometimes just by chance after an unclean shutdown.&lt;br&gt;&lt;br&gt;You can either revert your installed Bitcoin software to the last known working version (but not earlier than version 0.8.1) or delete everything &lt;b&gt;except&lt;/b&gt; &quot;wallet.dat&quot; from your Bitcoin home directory &lt;font face=&quot;courier&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;If you choose to delete the contents of the Bitcoin home directory, you will have to do a fresh download of the blockchain again, which will require a few hours the first time.</source>
        <translation>Le logiciel Bitcoin indique qu&apos;il y a un problème avec ses bases de données. Cela peut arriver quand Bitcoin Core/bitcoind a reçu une mise à niveau supérieure ou inférieure, ou parfois juste au hasard après une mauvaise fermeture.&lt;br&gt;&lt;br&gt;Vous pouvez soit ramener le logiciel Bitcoin à la dernière version fonctionnelle connue (mais pas antérieure à 0.8.1) ou tout supprimer de votre répertoire Bitcoin personnel &lt;font face=&quot;courier&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt; &lt;b&gt;sauf&lt;/b&gt; « wallet.dat ».&lt;br&gt;&lt;br&gt;Si vous choisissez de supprimer le contenu de votre répertoire Bitcoin personnel, vous devrez entièrement retélécharger la chaîne de blocs, ce qui exigera plusieurs heures la première fois.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="3416"/>
        <source>
            You just clicked on a &quot;bitcoin:&quot; link to send money, but you 
            currently have no wallets!  Would you like to create a wallet 
            now?</source>
        <translation>
Vous venez de cliquer sur un lien « bitcoin: » pour envoyer des pièces, mais vous n&apos;avez actuellement aucun porte-monnaie ! Souhaitez-vous créer un porte-monnaie maintenant ?</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="5053"/>
        <source>
                           The DB has returned the following error: &lt;br&gt;&lt;br&gt;
                           &lt;b&gt; %1 &lt;/b&gt; &lt;br&gt;&lt;br&gt; Armory will now shutdown.</source>
        <translation>
La BD a retourné l&apos;erreur suivante : &lt;br&gt;&lt;br&gt;
&lt;b&gt; %1 &lt;/b&gt; &lt;br&gt;&lt;br&gt;
Armory va se fermer maintenant.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1919"/>
        <source>You clicked on a &quot;bitcoin:&quot; link, but Armory is in
               offline mode, and is not capable of creating transactions. 
               Using links will only work if Armory is connected 
               to the Bitcoin network!</source>
        <translation>Vous avez cliqué sur un lien « bitcoin: », mais Armory est en mode hors ligne et ne peut pas créer de transactions. Les liens ne peuvent être utilisés que si Armory est connecté au réseau Bitcoin !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1925"/>
        <source>You entered a &quot;bitcoin:&quot; link, but Armory is in
               offline mode, and is not capable of creating transactions. 
               Using links will only work if Armory is connected 
               to the Bitcoin network!</source>
        <translation>Vous avez saisi un lien « bitcoin: », mais Armory est en mode hors ligne et ne peut pas créer de transactions. Les liens ne peuvent être utilisés que si Armory est connecté au réseau Bitcoin !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1934"/>
        <source>It looks like you just clicked a &quot;bitcoin:&quot; link, but that link is malformed.</source>
        <translation>Il semble que vous venez de cliquer sur un lien « bitcoin: », mais le lien est mal formé.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1936"/>
        <source>It looks like you just entered a &quot;bitcoin:&quot; link, but that link is malformed.</source>
        <translation>Il semble que vous venez de saisir un lien « bitcoin: », mais le lien est mal formé.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1938"/>
        <source>Please check the source of the link and enter the transaction manually.</source>
        <translation>Veuillez vérifier la source du lien et saisir la transaction manuellement.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1947"/>
        <source>The &quot;bitcoin:&quot; link you just clicked
               does not even contain an address!  There is nothing that 
               Armory can do with this link!</source>
        <translation>Le lien « bitcoin: » sur lequel vous venez de cliquer ne contient même pas une adresse. Armory ne peut pas l&apos;utiliser !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1951"/>
        <source>The &quot;bitcoin:&quot; link you just entered
               does not even contain an address!  There is nothing that 
               Armory can do with this link!</source>
        <translation>Le lien « bitcoin: » que vous venez de saisir ne contient même pas une adresse. Armory ne peut pas l&apos;utiliser !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1964"/>
        <source>The address for the &quot;bitcoin:&quot; link you just clicked is
               for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
               and the address you supplied is for the 
               &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation>L&apos;adresse du lien « bitcoin: » sur lequel vous venez de cliquer est pour le mauvais réseau ! Vous êtes sur &lt;b&gt;%2&lt;/b&gt; et l&apos;adresse fournie est pour &lt;b&gt;%3&lt;/b&gt; !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1970"/>
        <source>The address for the &quot;bitcoin:&quot; link you just entered is
               for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
               and the address you supplied is for the 
               &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation>L&apos;adresse du lien « bitcoin: » que vous venez de saisir est pour le mauvais réseau ! Vous êtes sur &lt;b&gt;%2&lt;/b&gt; et l&apos;adresse fournie est pour &lt;b&gt;%3&lt;/b&gt; !</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1983"/>
        <source>The &quot;bitcoin:&quot; link
                  you just clicked contains fields that are required but not
                  recognized by Armory.  This may be an older version of Armory,
                  or the link you clicked on uses an exotic, unsupported format.
                  &lt;br&gt;&lt;br&gt;The action cannot be completed.</source>
        <translation>Le lien « bitcoin: » sur lequel vous venez de cliquer contient des champs qui sont exigés, mais qui ne sont pas reconnus par Armory. Cette version d&apos;Armory est peut-être ancienne, ou le lien sur lequel vous avez cliqué utilise un format exotique non pris en charge. L&apos;action ne peut pas être effectuée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="1989"/>
        <source>The &quot;bitcoin:&quot; link
                  you just entered contains fields that are required but not
                  recognized by Armory.  This may be an older version of Armory,
                  or the link you entered on uses an exotic, unsupported format.
                  &lt;br&gt;&lt;br&gt;The action cannot be completed.</source>
        <translation>Le lien « bitcoin: » que vous venez de saisir contient des champs qui sont exigés, mais qui ne sont pas reconnus par Armory. Cette version d&apos;Armory est peut-être ancienne, ou le lien sur lequel vous avez cliqué utilise un format exotique non pris en charge. L&apos;action ne peut pas être effectuée.</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2754"/>
        <source>Add Transaction Comment</source>
        <translation>Ajouter un commentaire de transaction</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2756"/>
        <source>Change Transaction Comment</source>
        <translation>Modifier le commentaire de transaction</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2772"/>
        <source>Add Address Comment</source>
        <translation>Ajouter un commentaire d&apos;adresse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="2774"/>
        <source>Change Address Comment</source>
        <translation>Modifier un commentaire d&apos;adresse</translation>
    </message>
    <message>
        <location filename="ArmoryQt.py" line="585"/>
        <source>
               Armory is currently offline, and cannot determine what funds are
               available for Simulfunding.  Please try again when Armory is in
               online mode.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>ArmorySplashScreen</name>
    <message>
        <location filename="qtdialogs.py" line="13801"/>
        <source>%1: %2%</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13776"/>
        <source>Loading: %1%</source>
        <translation>Chargement : %1%</translation>
    </message>
</context>
<context>
    <name>BareSignatureVerificationWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="265"/>
        <source>Signing Address:</source>
        <translation>Adresse de signature :</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="274"/>
        <source>Signed Message:</source>
        <translation>Message signé :</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="281"/>
        <source>Signature:</source>
        <translation>Signature :</translation>
    </message>
</context>
<context>
    <name>CardDeckFrame</name>
    <message>
        <location filename="WalletFrames.py" line="498"/>
        <source>Please shuffle a deck of cards and enter the first 40 cards in order below to get at least 192 bits of entropy to properly randomize.

</source>
        <translation>Veuillez mélanger un jeu de cartes et saisir les 40 premières cartes ci-dessous afin d&apos;obtenir au moins 192 bits d&apos;entropie pour aléer adéquatement.

</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="533"/>
        <source>Entropy: %1 bits</source>
        <translation>Entropie : %1 bits</translation>
    </message>
</context>
<context>
    <name>CoinControlDlg</name>
    <message>
        <location filename="CoinControlUI.py" line="26"/>
        <source>By default, transactions are created using any available coins from all addresses in this wallet.  You can control the source addresses used for this transaction by selecting them below, and unchecking all other addresses.</source>
        <translation>Par défaut, les transactions sont créées en utilisant les pièces disponibles dans toutes les adresses de ce porte-monnaie. Vous pouvez contrôler les adresses sources utilisées pour cette transaction en les sélectionnant ci-dessous et en décochant toutes les autres adresses.</translation>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="32"/>
        <source>Use all selected UTXOs</source>
        <translation>Utiliser toutes les UTXO sélectionnées</translation>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="33"/>
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
        <location filename="CoinControlUI.py" line="50"/>
        <source>Accept</source>
        <translation>Accepter</translation>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="51"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="74"/>
        <source>Coin Control (Expert)</source>
        <translation>Contrôle des pièces (expert)</translation>
    </message>
    <message>
        <location filename="CoinControlUI.py" line="33"/>
        <source>
      By default, Armory will pick a subset of the UTXOs you chose 
      explicitly through the coin control feature to best suit the
      total spend value of the transaction you are constructing.
      
      &lt;br&gt;&lt;br&gt;
      Checking 'Use all selected UTXOs' forces the construction of a
      transaction that will redeem the exact list of UTXOs you picked 
      instead 
      </source>
        <translation>
Par défaut, Armory choisira un sous-ensemble des UTXO que vous sélectionnez explicitement par le biais de la fonction de contrôle des pièces afin de s&apos;adapter au mieux à la valeur totale de dépense de la transaction que vous construisez.
&lt;br&gt;&lt;br&gt;
Cocher l&apos;option « Utiliser toutes les UTXO sélectionnées » force la construction d&apos;une transaction qui traitera plutôt la liste exacte des UTXO que vous avez choisies</translation>
    </message>
</context>
<context>
    <name>CoinControlTreeModel</name>
    <message>
        <location filename="TreeViewGUI.py" line="674"/>
        <source>Address/ID</source>
        <translation>Adresse/ID</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="675"/>
        <source>Comment</source>
        <translation>Commentaire</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="676"/>
        <source>Balance</source>
        <translation>Solde</translation>
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
        <translation>Étape 1 : créer une transaction</translation>
    </message>
</context>
<context>
    <name>DlgAddressBook</name>
    <message>
        <location filename="qtdialogs.py" line="7627"/>
        <source>Select</source>
        <translation>Sélectionner</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7637"/>
        <source>Choose an address from your transaction history,
                            or your own wallet.  If you choose to send to one
                            of your own wallets, the next unused address in
                            that wallet will be used.</source>
        <translation>Choisissez une adresse de votre historique transactionnel ou de votre propre porte-monnaie. Si vous choisissez d&apos;envoyer à l&apos;un de vos propres porte-monnaie, la prochaine adresse inutilisée dans votre porte-monnaie sera utilisée.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7643"/>
        <source>Browse all receiving addresses in
                               this wallet, and all addresses to which this
                               wallet has sent bitcoins.</source>
        <translation>Parcourir toutes les adresses de réception de ce porte-monnaie et toutes les adresses vers lesquelles ce porte-monnaie a envoyé des bitcoins.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7647"/>
        <source>&lt;b&gt;Send to Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Envoyer au porte-monnaie :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7648"/>
        <source>&lt;b&gt;Send to Address:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Envoyer à l&apos;adresse :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7699"/>
        <source>Receiving (Mine)</source>
        <translation>Réception (minage)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7701"/>
        <source>Sending (Other&apos;s)</source>
        <translation>Envoi (aux autres)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7736"/>
        <source>The next unused address in that wallet will be calculated and selected. </source>
        <translation>La prochaine adresse inutilisée dans ce porte-monnaie sera calculée et sélectionnée.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7738"/>
        <source>Addresses that are in other wallets you own are &lt;b&gt;not showns&lt;/b&gt;.</source>
        <translation>Les adresses qui se trouvent dans d&apos;autres porte-monnaie que vous possédez &lt;b&gt;n&apos;apparaissent pas&lt;/b&gt;.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7743"/>
        <source>No Wallet Selected</source>
        <translation>Aucun porte-monnaie n&apos;est sélectionné</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7744"/>
        <source>Use Bare Multi-Sig (No P2SH)</source>
        <translation>Utiliser des multisignatures nues (pas de P2SH)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7746"/>
        <source>
         EXPERT OPTION:  Do not check this box unless you know what it means
                         and you need it!  Forces Armory to exposes public
                         keys to the blockchain before the funds are spent.
                         This is only needed for very specific use cases,
                         and otherwise creates blockchain bloat.</source>
        <translation>
OPTION EXPERT : ne cochez cette case que si vous savez ce qu&apos;elle signifie et que vous en avez besoin ! Elle force Armory à exposer les clés publiques à la chaîne de blocs avant que les fonds ne soient dépensés. Elle n&apos;est nécessaire que pour certains cas d&apos;usage très précis et autrement encombre la chaîne de blocs.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7755"/>
        <source>No Address Selected</source>
        <translation>Aucune adresse n&apos;est sélectionnée</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7758"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7764"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Retour</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7871"/>
        <source>None Selected</source>
        <translation>Rien n&apos;est sélectionné</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7959"/>
        <source>%1 Wallet: %2</source>
        <translation>%1 le porte-monnaie : %2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8000"/>
        <source>%1 Address: %2...</source>
        <translation>%1 l&apos;adresse : %2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8051"/>
        <source>
               Bare multi-sig is not available for M-of-N lockboxes on the
               main Bitcoin network with N higher than 3.</source>
        <translation>
Les multisignatures nues ne sont pas proposées pour les coffres M de N sur le réseau principal Bitcoin si N est supérieur à 3.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8103"/>
        <source>P2SH Not Allowed</source>
        <translation>P2SH n&apos;est pas autorisé</translation>
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
        <location filename="qtdialogs.py" line="8137"/>
        <source>No Public Key</source>
        <translation>Aucune clé publique</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8137"/>
        <source>
            This operation requires a full public key, not just an address.
            Unfortunately, Armory cannot find the public key for the address
            you selected.  In general public keys will only be available
            for addresses in your wallet.</source>
        <translation>
Cette opération exige une clé publique complète, pas juste une adresse. Malheureusement, Armory ne peut pas trouver de clé publique pour l&apos;adresse que vous avez sélectionnée. En général, des clés publiques ne sont proposées que pour les adresses dans votre porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8188"/>
        <source>Copy Address</source>
        <translation>Copier l&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8189"/>
        <source>Copy Hash160 (hex)</source>
        <translation>Copier Hash160 (hexadécimal)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8190"/>
        <source>Copy Comment</source>
        <translation>Copier le commentaire</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8103"/>
        <source>
               This operation requires a public key, but you selected a
               P2SH address which does not have a public key (these addresses
               start with &quot;2&quot; or &quot;3&quot;).  Please select a different address.</source>
        <translation>
Cette opération exige une clé publique, mais vous avez sélectionné une adresse P2SH qui ne contient aucune clé publique (ces adresses commencent par « 2 » ou « 3 »). Veuillez sélectionner une adresse différente.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8066"/>
        <source>Add Address Comment</source>
        <translation>Ajouter un commentaire d&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8068"/>
        <source>Change Address Comment</source>
        <translation>Modifier un commentaire d&apos;adresse</translation>
    </message>
</context>
<context>
    <name>DlgAddressInfo</name>
    <message>
        <location filename="qtdialogs.py" line="3148"/>
        <source>Information for address:  %1</source>
        <translation>Informations pour l&apos;adresse : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3160"/>
        <source>This is the computer-readable form of the address</source>
        <translation>Cela est la forme lisible par les ordinateurs de l&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3162"/>
        <source>&lt;b&gt;Public Key Hash&lt;/b&gt;</source>
        <translation>&lt;b&gt;Hachage de clé publique&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3168"/>
        <source>%1 (Network: %2 / Checksum: %3)</source>
        <translation>%1 (réseau : %2 / somme de contrôle : %3)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3175"/>
        <source>&lt;b&gt;Wallet:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Porte-monnaie :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3180"/>
        <source>&lt;b&gt;Address:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Adresse :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3185"/>
        <source>
         Address type is either &lt;i&gt;Imported&lt;/i&gt; or &lt;i&gt;Permanent&lt;/i&gt;.
         &lt;i&gt;Permanent&lt;/i&gt;
         addresses are part of the base wallet, and are protected by printed
         paper backups, regardless of when the backup was performed.
         Imported addresses are only protected by digital backups, or manually
         printing the individual keys list, and only if the wallet was backed up
         &lt;i&gt;after&lt;/i&gt; the keys were imported.</source>
        <translation>
Le type d&apos;adresse est soit &lt;i&gt;Importée&lt;/i&gt;, soit &lt;i&gt;Permanente&lt;/i&gt;.
Les adresses &lt;i&gt;permanentes&lt;/i&gt; font partie du porte-monnaie de base et sont protégées par des sauvegardes papier imprimées, indépendamment de quand elles ont été effectuées. 
Les adresses importées sont seulement protégées par des sauvegardes numériques ou en imprimant manuellement la liste des clés individuelles, et seulement si le porte-monnaie a été sauvegardé &lt;i&gt;après&lt;/i&gt; l&apos;importation des clés.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3194"/>
        <source>&lt;b&gt;Address Type:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Type d&apos;adresse :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3208"/>
        <source>Imported</source>
        <translation>Importée</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3198"/>
        <source>Permanent</source>
        <translation>Permanente</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3202"/>
        <source>The index of this address within the wallet.</source>
        <translation>L&apos;index de cette adresse dans le porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3204"/>
        <source>&lt;b&gt;Index:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Index :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3213"/>
        <source>
            This is the current &lt;i&gt;spendable&lt;/i&gt; balance of this address,
            not including zero-confirmation transactions from others.</source>
        <translation>
Le solde actuel &lt;i&gt;disponible&lt;/i&gt; pour cette adresse, sans inclure les transactions sans confirmation des autres.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3216"/>
        <source>&lt;b&gt;Current Balance&lt;/b&gt;</source>
        <translation>&lt;b&gt;Solde actuel&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3232"/>
        <source>&lt;b&gt;Comment:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Commentaire :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3244"/>
        <source>The total number of transactions in which this address was involved</source>
        <translation>Le nombre total de transactions impliquant cette adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3246"/>
        <source>&lt;b&gt;Transaction Count:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Nombre de transactions :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3266"/>
        <source>&lt;font size=2&gt;Double-click to expand&lt;/font&gt;</source>
        <translation>&lt;font size=2&gt;Double-cliquer pour développer&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3310"/>
        <source>
            Unlike the wallet-level ledger, this table shows every
            transaction &lt;i&gt;input&lt;/i&gt; and &lt;i&gt;output&lt;/i&gt; as a separate entry.
            Therefore, there may be multiple entries for a single transaction,
            which will happen if money was sent-to-self (explicitly, or as
            the change-back-to-self address).</source>
        <translation>
Contrairement au grand livre de niveau porte-monnaie, ce tableau affiche toutes les transactions &lt;i&gt;entrantes&lt;/i&gt; et &lt;i&gt;sortantes&lt;/i&gt; comme des entrées séparées. Par conséquent, une seule transaction pourrait apparaître en plusieurs entrées, ce qui arrivera si les pièces ont été envoyées-à-soi (explicitement ou comme adresse monnaie-rendue-à-soi).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3316"/>
        <source>All Address Activity:</source>
        <translation>Activité de toutes les adresses :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3325"/>
        <source>Copy Address to Clipboard</source>
        <translation>Copier l&apos;adresse dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3326"/>
        <source>View Address Keys</source>
        <translation>Visualiser les clés des adresses</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3328"/>
        <source>Delete Address</source>
        <translation>Supprimer l&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3345"/>
        <source>
         NOTE:  The ledger shows each transaction &lt;i&gt;&lt;b&gt;input&lt;/b&gt;&lt;/i&gt; and
         &lt;i&gt;&lt;b&gt;output&lt;/b&gt;&lt;/i&gt; for this address.  There are typically many
         inputs and outputs for each transaction, therefore the entries
         represent only partial transactions.  Do not worry if these entries
         do not look familiar.</source>
        <translation>
NOTE : le grand livre affiche chaque transaction &lt;i&gt;&lt;b&gt;entrante&lt;/b&gt;&lt;/i&gt; et &lt;i&gt;&lt;b&gt;sortante&lt;/b&gt;&lt;/i&gt; pour cette adresse. Il y a habituellement de nombreuses entrées et sorties pour chaque transaction. Par conséquent, les entrées ne représentent que des transactions partielles. Ne vous inquiétez pas si vous ne reconnaissez pas ses entrées.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3365"/>
        <source>Available Actions:</source>
        <translation>Actions proposées :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3368"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Retour</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3372"/>
        <source>Address Information</source>
        <translation>Informations sur l&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3381"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Copié !&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3390"/>
        <source>Wallet is Locked</source>
        <translation>Le porte-monnaie est verrouillé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3390"/>
        <source>Key information will not include the private key data.</source>
        <translation>Les informations sur la clé n’incluront pas les données confidentielles de la clé.</translation>
    </message>
</context>
<context>
    <name>DlgBackupCenter</name>
    <message>
        <location filename="qtdialogs.py" line="9959"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9970"/>
        <source>Backup Center</source>
        <translation>Centre des sauvegardes</translation>
    </message>
</context>
<context>
    <name>DlgBadConnection</name>
    <message>
        <location filename="qtdialogs.py" line="7096"/>
        <source>
            Armory was not able to detect an internet connection, so Armory
            will operate in &quot;Offline&quot; mode.  In this mode, only wallet
            -management and unsigned-transaction functionality will be available.
            &lt;br&gt;&lt;br&gt;
            If this is an error, please check your internet connection and
            restart Armory.&lt;br&gt;&lt;br&gt;Would you like to continue in &quot;Offline&quot; mode? </source>
        <translation>
Armory n&apos;a pas réussi à détecter une connexion Internet et fonctionnera donc en mode « hors ligne ». Dans ce mode, seules la gestion des porte-monnaie et les fonctions relatives aux transactions non signées seront proposées.
&lt;br&gt;&lt;br&gt;
Si cela est une erreur, veuillez vérifier votre connexion Internet et redémarrer Armory.&lt;br&gt;&lt;br&gt; Souhaitez-vous poursuivre en mode « hors ligne » ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7104"/>
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
        <translation>
Armory n&apos;a pas réussi à détecter la présence des logiciels clients Bitcoin Core ou bitcoind (proposés sur https://bitcoin.org). Veuillez vous assurer que l&apos;un de ces programmes est...&lt;br&gt;
&lt;br&gt;&lt;b&gt;(1)&lt;/b&gt;...ouvert et connecté au réseau
&lt;br&gt;&lt;b&gt;(2)&lt;/b&gt;...sur le même réseau qu&apos;Armory (réseau principal ou réseau de test)
&lt;br&gt;&lt;b&gt;(3)&lt;/b&gt;...synchronisé avec la chaîne de blocs avant de démarrer Armory&lt;br&gt;&lt;br&gt;Si Bitcoin Core ou bitcoind n&apos;est pas ouvert, vous ne pourrez exécuter Armory qu&apos;en mode « hors ligne », qui n&apos;aura pas accès aux nouvelles données de la chaîne de blocs, et vous ne pourrez pas envoyer de transactions sortantes&lt;br&gt;&lt;br&gt;Si vous ne souhaitez pas être en mode « hors ligne », veuillez redémarrer Armory après que l&apos;un de ces programmes est ouvert et synchronisé avec le réseau.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7129"/>
        <source>Continue in Offline Mode</source>
        <translation>Poursuivre en mode hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7130"/>
        <source>Close Armory</source>
        <translation>Fermer Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7142"/>
        <source>Network not available</source>
        <translation>Le réseau n&apos;est pas disponible</translation>
    </message>
</context>
<context>
    <name>DlgBroadcastBlindTx</name>
    <message>
        <location filename="qtdialogs.py" line="13626"/>
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
Copier ci-dessous une transaction brute encodée en hexadécimal pour qu&apos;Armory la diffuse au réseau Bitcoin. Cette fonction est proposée au bénéfice des utilisateurs experts et sans aucune garantie d&apos;utilité.
&lt;br&gt;&lt;br&gt;
Être particulièrement conscient des restrictions suivantes de la fonction de diffusion :
&lt;ul&gt;
&lt;li&gt;
La transaction sera « diffusée » en l&apos;envoyant à  l&apos;instance connectée de Bitcoin Core qui l&apos;acheminera au reste du réseau Bitcoin. Cependant, si la transaction n&apos;est pas habituelle ou ne remplit pas les règles de frais standards, Bitcoin Core &lt;u&gt;l&apos;abandonnera &lt;/u&gt; et elle ne sera jamais vue par le réseau Bitcoin.
&lt;/li&gt;
&lt;li&gt;Il n&apos;y aura aucune rétroaction pour confirmer si la transaction est réussie. Il faudra vérifier le succès de cette opération par d&apos;autres moyens. Cependant, si la transaction envoie des fonds directement vers ou d&apos;une adresse d&apos;un de vos porte-monnaie, une notification sera quand même générée et apparaîtra dans l&apos;historique transactionnel de ce porte-monnaie.
&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13660"/>
        <source>Parsed Transaction:</source>
        <translation>Transaction analysée :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13670"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13671"/>
        <source>Broadcast</source>
        <translation>Diffuser</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13687"/>
        <source>Broadcast Raw Transaction</source>
        <translation>Diffuser la transaction brute</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13713"/>
        <source>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;Raw transaction
            is invalid!&lt;/font&gt;&lt;/b&gt;</source>
        <translation>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;La transaction brute est invalide !&lt;/font&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13740"/>
        <source>Broadcast!</source>
        <translation>Diffusée !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13740"/>
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
        <translation>
Votre transaction a été envoyé avec succès au Bitcoin Core local, bien qu&apos;il n&apos;y ait aucune garantie qu&apos;elle soit acheminée vers le reste du réseau. Sur le réseau de test (testnet), presque toutes les transactions valides seront propagées avec succès. Sur le réseau Bitcoin principal, elle échouera à moins d&apos;être un type de transaction standard.

Le hachage de la transaction était comme suit :
&lt;br&gt;&lt;br&gt;
%1
&lt;br&gt;&lt;br&gt;
Vous pouvez vérifier si elle a été vue par les autres nœuds du réseau grâce au lien ci-dessous :
&lt;br&gt;&lt;br&gt;
&lt;a href=&quot;%2&quot;&gt;%3&lt;/a&gt;</translation>
    </message>
</context>
<context>
    <name>DlgChangeLabels</name>
    <message>
        <location filename="qtdialogs.py" line="1014"/>
        <source>Wallet &amp;name:</source>
        <translation>&amp;Nom du porte-monnaie :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1020"/>
        <source>Wallet &amp;description:</source>
        <translation>&amp;Description du porte-monnaie :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1040"/>
        <source>Wallet Descriptions</source>
        <translation>Descriptions des porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1050"/>
        <source>Empty Name</source>
        <translation>Le nom est vide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1050"/>
        <source>All wallets must have a name. </source>
        <translation>Tous les porte-monnaie doivent avoir un nom.</translation>
    </message>
</context>
<context>
    <name>DlgChangePassphrase</name>
    <message>
        <location filename="qtdialogs.py" line="843"/>
        <source>Please enter an passphrase for wallet encryption.


                              A good passphrase consists of at least 8 or more

                              random letters, or 5 or more random words.
</source>
        <translation>Veuillez saisir une phrase de passe pour le chiffrement du porte-monnaie.


Une bonne phrase de passe comporte au moins huit lettres ou cinq mots choisis au hasard.
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="849"/>
        <source>Change your wallet encryption passphrase</source>
        <translation>Changer la phrase de passe de chiffrement de votre porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="854"/>
        <source>Current Passphrase:</source>
        <translation>Phrase de passe actuelle :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="860"/>
        <source>New Passphrase:</source>
        <translation>Nouvelle phrase de passe :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="865"/>
        <source>Again:</source>
        <translation>De nouveau :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="880"/>
        <source>Disable encryption for this wallet</source>
        <translation>Désactiver le chiffrement pour ce porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="887"/>
        <source>Accept</source>
        <translation>Accepter</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="888"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="895"/>
        <source>Set Encryption Passphrase</source>
        <translation>Définir une phrase de passe de chiffrement</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="897"/>
        <source>Change Encryption Passphrase</source>
        <translation>Changer la phrase de passe de chiffrement</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="929"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is non-ASCII!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;La phrase de passe n&apos;est pas ASCII !&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="932"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases do not match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Les phrases de passe ne correspondent pas !&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="935"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is too short!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;La phrase de base est trop courte !&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="937"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=%1&gt;&lt;b&gt;Les phrases de passe correspondent !&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="949"/>
        <source>Invalid Passphrase</source>
        <translation>Phrase de passe invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="949"/>
        <source>You entered your confirmation passphrase incorrectly!</source>
        <translation>La phrase de passe de confirmation n&apos;a pas été saisie correctement !</translation>
    </message>
</context>
<context>
    <name>DlgConfirmBulkImport</name>
    <message>
        <location filename="qtdialogs.py" line="3031"/>
        <source>No Addresses to Import</source>
        <translation>Aucune adresse à importer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3031"/>
        <source>
           There are no addresses to import!</source>
        <translation>
 Il n&apos;y a aucune adresse à importer !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3036"/>
        <source>a new wallet</source>
        <translation>un nouveau porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3039"/>
        <source>wallet, &lt;b&gt;%1&lt;/b&gt; (%2)</source>
        <translation>porte-monnaie, &lt;b&gt;%1&lt;/b&gt; (%2)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3040"/>
        <source>
         'You are about to import &lt;b&gt;%1&lt;/b&gt; addresses into %2.&lt;br&gt;&lt;br&gt; '
         &apos;The following is a list of addresses to be imported:</source>
        <translation>
Vous allez importer &lt;b&gt;%1&lt;/b&gt; adresses dans %2.&lt;br&gt;&lt;br&gt;
Voici une liste des adresses à importer :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3055"/>
        <source>Import</source>
        <translation>Importer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3056"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3068"/>
        <source>Confirm Import</source>
        <translation>Confirmer l&apos;importation</translation>
    </message>
</context>
<context>
    <name>DlgConfirmSend</name>
    <message>
        <location filename="qtdialogs.py" line="4479"/>
        <source> To see complete transaction details
                             &lt;a href=&quot;None&quot;&gt;click here&lt;/a&gt;&lt;/font&gt;</source>
        <translation>Pour voir les détails de la transaction, &lt;a href=&quot;None&quot;&gt;cliquer ici&lt;/a&gt;&lt;/font&gt;
  </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4488"/>
        <source>
         This transaction will spend &lt;b&gt;%1 BTC&lt;/b&gt; from
         &lt;font color=&quot;%2&quot;&gt;Wallet &quot;&lt;b&gt;%3&lt;/b&gt;&quot; (%4)&lt;/font&gt; to the following
         recipients:</source>
        <translation>
Cette transaction dépensera &lt;b&gt;%1 BTC&lt;/b&gt; du &lt;font color=&quot;%2&quot;&gt;porte-monnaie « &lt;b&gt;%3&lt;/b&gt; » (%4)&lt;/font&gt; vers les destinataires suivants :
  </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4494"/>
        <source>
            &lt;font size=3&gt;* Starred
            outputs are going to the same wallet from which they came
            and do not affect the wallet's final balance.
            The total balance of the wallet will actually only decrease
            &lt;b&gt;%1 BTC&lt;/b&gt; as a result of this transaction.  %2&lt;/font&gt;</source>
        <translation>
&lt;font size=3&gt;* Les sorties étoilées retournent dans le même porte-monnaie dont elles proviennent et n&apos;affectent pas le solde final du porte-monnaie.
Le solde du porte-monnaie diminuera en fait de &lt;b&gt;%1 BTC&lt;/b&gt; à la suite de cette transaction.  %2&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4542"/>
        <source>Send</source>
        <translation>Envoyer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4543"/>
        <source>Are you sure you want to execute this transaction?</source>
        <translation>Voulez-vous vraiment exécuter cette transaction ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4545"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4546"/>
        <source>Does the above look correct?</source>
        <translation>Ce qui est ci-dessus semble-t-il correct ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4548"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4572"/>
        <source>Confirm Transaction</source>
        <translation>Confirmer la transaction</translation>
    </message>
</context>
<context>
    <name>DlgCorruptWallet</name>
    <message>
        <location filename="qtdialogs.py" line="13084"/>
        <source>Wallet Consistency Check Failed!</source>
        <translation>Échec du contrôle de cohérence du porte-monnaie !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13086"/>
        <source>Perform Wallet Consistency Check</source>
        <translation>Effectuer le contrôle de cohérence du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13088"/>
        <source>
         &lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;&lt;u&gt;%2&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
         &lt;br&gt;&lt;br&gt;
         Armory software now detects and prevents certain kinds of
         hardware errors that could lead to problems with your wallet.
         &lt;br&gt; </source>
        <translation>
&lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;&lt;u&gt;%2&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
&lt;br&gt;&lt;br&gt;
Armory détecte et empêche maintenant certaines sortes d&apos;erreurs matérielles qui pourraient causer des problèmes à votre porte-monnaie.&lt;br&gt; </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13099"/>
        <source>
            Armory has detected that wallet file &lt;b&gt;Wallet &quot;%1&quot; (%2)&lt;/b&gt;
            is inconsistent and should be further analyzed to ensure that your
            funds are protected.
            &lt;br&gt;&lt;br&gt;
            &lt;font color=&quot;%3&quot;&gt;This error will pop up every time you start
            Armory until the wallet has been analyzed and fixed!&lt;/font&gt;</source>
        <translation>
Armory a détecté que le fichier du &lt;b&gt;porte-monnaie « %1 » (%2)&lt;/b&gt; est incohérent et devrait être analysé davantage pour garantir que les fonds sont protégés.
&lt;br&gt;&lt;br&gt;
&lt;font color=&quot;%3&quot;&gt;Cette erreur surgira chaque fois que vous démarrerez Armory tant que le porte-monnaie n&apos;aura pas été analysé et réparé !&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13107"/>
        <source>
            Armory will perform a consistency check on &lt;b&gt;Wallet &quot;%1&quot; (%2)&lt;/b&gt;
            and determine if any further action is required to keep your funds
            protected.  This check is normally performed on startup on all
            your wallets, but you can click below to force another
            check.</source>
        <translation>
Armory effectuera un contrôle de cohérence sur le &lt;b&gt;porte-monnaie « %1 » (%2)&lt;/b&gt; et déterminera si des actions complémentaires sont exigées pour assurer la protection de vos fonds. Cette vérification est habituellement effectuée sur tous les porte-monnaie lors du démarrage, mais vous pouvez cliquer ci-dessous pour forcer une vérification.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13138"/>
        <source>Hide</source>
        <translation>Cacher</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13139"/>
        <source>Run Analysis and Recovery Tool</source>
        <translation>Exécuter l&apos;outil d&apos;analyse et de récupération</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13149"/>
        <source>
         &lt;u&gt;Your wallets will be ready to fix once the scan is over&lt;/u&gt;&lt;br&gt;
         You can hide this window until then&lt;br&gt;</source>
        <translation>
&lt;u&gt;Vos porte-monnaie pourront être réparés dès que l&apos;analyse sera terminée. Vous pouvez cacher cette fenêtre en attendant&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13171"/>
        <source>Wallet Error</source>
        <translation>Erreur de porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13197"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13286"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13301"/>
        <source>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Failed to fix wallets!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Échec de réparation des porte-monnaie !&lt;/b&gt;&lt;/font&gt;</translation>
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
        <location filename="qtdialogs.py" line="13313"/>
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
&lt;font size=4&gt;&lt;b&gt;&lt;u&gt;Il pourrait encore y avoir des problèmes avec votre porte-monnaie !&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;
&lt;br&gt;
Il est important que vous nous envoyiez les journaux de récupération ainsi qu&apos;une adresse courriel afin que l&apos;équipe d&apos;Armory puisse évaluer les risques possibles qu&apos;encourent vos fonds !&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13323"/>
        <source>&lt;h2 style=&quot;color: red;&quot;&gt;                                     Consistency check failed! &lt;/h2&gt;</source>
        <translation>&lt;h2 style=&quot;color: red;&quot;&gt;Échec du contrôle de cohérence !&lt;/h2&gt;</translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="13305"/>
        <source>
            &lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Wallet(s) consistent, nothing to
            fix.&lt;/b&gt;&lt;/font&gt;</source>
        <translation><numerusform>&lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Le porte-monnaie est cohérent, il n&apos;y a rien à corriger.&lt;/b&gt;&lt;/font&gt;</numerusform><numerusform>&lt;font size=4 color=&quot;%1&quot;&gt;&lt;b&gt;Les porte-monnaie sont cohérents, il n&apos;y a rien à corriger.&lt;/b&gt;&lt;/font&gt;</numerusform></translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="13308"/>
        <source>Wallet(s) consistent!</source>
        <translation><numerusform>Le porte-monnaie est cohérent !</numerusform><numerusform>Les porte-monnaie sont cohérents !</numerusform></translation>
    </message>
</context>
<context>
    <name>DlgCreatePromNote</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3131"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Create Simulfunding Promissory Note
         &lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Créer un billet à ordre de financement simultané&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3136"/>
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
Utilisez ce formulaire pour créer un billet à ordre qui peut être combiné aux billets à ordre de tiers pour financer une adresse ou un coffre simultanément (&lt;i&gt;« financement simultané »&lt;/i&gt;). Cette transaction de financement ne sera valide que lorsque tous les billets à ordre seront fusionnés en une seule transaction. Alors, tous les bailleurs de fonds pourront l&apos;examiner et la signer.
&lt;br&gt;&lt;br&gt;
Si ce coffre est financé par une seule partie, il est inutile d&apos;utiliser cette interface. Demandez au bailleur de fonds d&apos;envoyer des bitcoins à l&apos;adresse ou au coffre de destination de façon habituelle.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3149"/>
        <source>
         &lt;b&gt;NOTE:&lt;/b&gt; At the moment, simulfunding is restricted to using
         single-signature wallets/addresses for funding.    More
         complex simulfunding transactions will be possible in a future 
         version of Armory.</source>
        <translation>
&lt;b&gt;NOTE :&lt;/b&gt; pour l&apos;instant, seuls les porte-monnaie et adresses à une seule signature peuvent être utilisés pour le financement simultané.  Des transactions de financement simultané plus compliquées seront possibles dans une version future d&apos;Armory.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3171"/>
        <source>Address:</source>
        <translation>Adresse :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3172"/>
        <source>Amount:</source>
        <translation>Montant :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3173"/>
        <source>Add fee:</source>
        <translation>Ajouter des frais :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3175"/>
        <source>BTC</source>
        <translation>BTC</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3209"/>
        <source>
         This label will be attached to the promissory note to help identify
         who is committing these funds.  If you do not fill this in, each
         other party signing will see &lt;i&gt;[[Unknown Signer]]&lt;/i&gt; for the ID.</source>
        <translation>
Cette étiquette sera jointe au billet à ordre pour aider à identifier qui engage les fonds. Si vous ne remplissez pas ce champ, les autres parties qui signeront verront &lt;i&gt;[[Signataire inconnu]]&lt;/i&gt; comme ID.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3217"/>
        <source>Source of Funding</source>
        <translation>Source du financement</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3224"/>
        <source>Funding Destination</source>
        <translation>Destination du financement</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3247"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3248"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3313"/>
        <source>Blockchain Not Available</source>
        <translation>La chaîne de blocs n&apos;est pas disponible</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3313"/>
        <source>
            The blockchain has become unavailable since you opened this
            window.  Creation of the promissory note cannot continue.  If 
            you think you should be online, please try again in a minute,
            or after restarting Armory</source>
        <translation>
La chaîne de blocs est devenue non disponible depuis que vous avez ouvert cette fenêtre. Il est impossible de poursuivre la création d&apos;un billet à ordre. Si vous pensez que vous devriez être en ligne, veuillez ressayer dans une minute ou après avoir redémarré Armory.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3325"/>
        <source>Lockbox Selected</source>
        <translation>Un coffre a été sélectionné</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3325"/>
        <source>
            Currently, Armory does not implement simulfunding with lockbox
            inputs.  Please choose a regular wallet as your input</source>
        <translation>
Actuellement, Armory ne met pas en œuvre le financement simultané avec des entrées de coffre. Veuillez choisir un porte-monnaie ordinaire comme entrée.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3332"/>
        <source>No Wallet Selected</source>
        <translation>Aucun porte-monnaie n&apos;a été sélectionné</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3332"/>
        <source>
            The wallet selected is not available.  Select another wallet.</source>
        <translation>
Le porte-monnaie sélectionné n&apos;est pas disponible. Veuillez en choisir un autre.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3342"/>
        <source>Zero Amount</source>
        <translation>Le montant est à zéro</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3342"/>
        <source>
               You cannot promise 0 BTC.   &lt;br&gt;Please enter 
               a positive amount.</source>
        <translation>
Vous ne pouvez pas promettre 0 BTC. &lt;br&gt;Veuillez saisir un montant positif.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3347"/>
        <source>Negative Value</source>
        <translation>La valeur est négative</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3373"/>
        <source>
            You have specified a negative amount. &lt;br&gt;Only
            positive values are allowed!</source>
        <translation>
Vous avez indiqué une valeur négative. &lt;br&gt;Seules les valeurs positives sont autorisées !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3378"/>
        <source>Too much precision</source>
        <translation>Il y a trop de précision</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3378"/>
        <source>
            Bitcoins can only be specified down to 8 decimal places. 
            The smallest value that can be sent is  0.0000 0001 BTC. 
            Please enter a new amount</source>
        <translation>
Les bitcoins ne peuvent être précisés que jusqu&apos;à 8 décimales.
La plus petite valeur qui peut être envoyée est 0,0000 0001 BTC. 
Veuillez saisir à nouveau montant.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3384"/>
        <source>Missing amount</source>
        <translation>Le montant est absent</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3358"/>
        <source>
            You did not specify an amount to promise!</source>
        <translation>
Vous n&apos;avez indiqué aucun montant à promettre !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3362"/>
        <source>Invalid Value String</source>
        <translation>La chaîne de valeur est invalide</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3388"/>
        <source>
            The amount you specified is invalid (%1).</source>
        <translation>
Le montant que vous avez indiqué est invalide (%1).</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3373"/>
        <source>Negative Fee</source>
        <translation>Les frais sont négatifs</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3384"/>
        <source>
            &apos;You did not specify an amount to promise!</source>
        <translation>
Vous n&apos;avez indiqué aucun montant à promettre !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3388"/>
        <source>Invalid Fee String</source>
        <translation>La chaîne de frais est invalide</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3398"/>
        <source>Not enough funds!</source>
        <translation>Les fonds sont insuffisants !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3398"/>
        <source>
            You specified &lt;b&gt;%1&lt;/b&gt; BTC (amount + fee), but the selected wallet
            only has &lt;b&gt;%2&lt;/b&gt; BTC spendable.</source>
        <translation>
Vous avez indiqué &lt;b&gt;%1&lt;/b&gt; BTC (montant + frais), mais le porte-monnaie sélectionné n&apos;a que &lt;b&gt;%2&lt;/b&gt; BTC disponibles.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3408"/>
        <source>Coin Selection Error</source>
        <translation>Erreur de sélection des pièces</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3408"/>
        <source>
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions.</source>
        <translation>
Une erreur est survenue lors de la construction de votre transaction en raison d&apos;une bizarrerie dans la façon dont les transactions Bitcoin fonctionnent. Si cette erreur apparaît plus d&apos;une fois, essayez d&apos;envoyer vos BTC en deux transactions séparées ou plus.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3440"/>
        <source>Transaction Not Found</source>
        <translation>La transaction est introuvable</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3440"/>
        <source>
               There was an error creating the promissory note -- the selected
               coins were not found in the blockchain.  Please go to 
               &quot;&lt;i&gt;Help&lt;/i&gt;&quot;â&quot;&lt;i&gt;Submit Bug Report&lt;/i&gt;&quot; from 
               the main window and submit your log files so the Armory team
               can review this error.</source>
        <translation>
Une erreur est survenue lors de la création du billet d&apos;ordre. Les pièces sélectionnées n&apos;ont pas été trouvées dans la chaîne de blocs. Veuillez aller dans « &lt;i&gt;Aide&lt;/i&gt; » → « &lt;i&gt;Signaler un rapport de bogue&lt;/i&gt; » à partir de la fenêtre principale et envoyez vos fichiers journaux afin que l&apos;équipe d&apos;Armory puisse examiner cette erreur.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3464"/>
        <source>Export Promissory Note</source>
        <translation>Exporter le billet à ordre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3465"/>
        <source>
            The text below includes all the data needed to represent your
            contribution to a simulfunding transaction.  Your money cannot move
            because you have not signed anything, yet.  Once all promissory
            notes are collected, you will be able to review the entire funding 
            transaction before signing.</source>
        <translation>
Le texte ci-dessous inclut toutes les données nécessaires pour représenter votre participation à une transaction de financement simultanée. Vos pièces ne peuvent pas être déplacées, car vous n&apos;avez encore rien signé. Une fois que tous les billets à ordre seront recueillis, vous pourrez examiner la transaction de financement complète avant de signer.</translation>
    </message>
</context>
<context>
    <name>DlgDispTxInfo</name>
    <message>
        <location filename="qtdialogs.py" line="5303"/>
        <source>Sent-to-Self</source>
        <translation>Envoyé-à-soi</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5320"/>
        <source>Received</source>
        <translation>Reçus</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5324"/>
        <source>Sent</source>
        <translation>Envoyés</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5341"/>
        <source>Transaction Information:</source>
        <translation>Informations sur la transaction :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5361"/>
        <source>Unique identifier for this transaction</source>
        <translation>Identifiant unique de cette transaction</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5362"/>
        <source>Transaction ID</source>
        <translation>ID de la transaction</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5367"/>
        <source>[[ Transaction ID cannot be determined without all signatures ]]</source>
        <translation>[[ L&apos;ID de la transaction ne peut pas être déterminé sans toutes les signatures ]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5377"/>
        <source>&lt;font color=&quot;gray&quot;&gt;
               [[ Transaction ID cannot be determined without all signatures ]]
               &lt;/font&gt;</source>
        <translation>&lt;font color=&quot;gray&quot;&gt;[[ L&apos;ID de la transaction ne peut pas être déterminé sans toutes les signatures ]]&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5391"/>
        <source>Bitcoin Protocol Version Number</source>
        <translation>Numéro de version du protocole Bitcoin</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5392"/>
        <source>Tx Version:</source>
        <translation>Version de la transaction :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5396"/>
        <source>The time at which this transaction becomes valid.</source>
        <translation>L&apos;heure de validité de cette transaction.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5398"/>
        <source>Lock-Time:</source>
        <translation>Heure de verrouillage :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5400"/>
        <source>Immediate (0)</source>
        <translation>Immédiate (0)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5402"/>
        <source>Block %1</source>
        <translation>Bloc %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5409"/>
        <source>Comment stored for this transaction in this wallet</source>
        <translation>Le commentaire enregistré pour cette transaction dans ce portefeuille</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5410"/>
        <source>User Comment:</source>
        <translation>Commentaires de l&apos;utilisateur :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5414"/>
        <source>&lt;font color=&quot;gray&quot;&gt;[None]&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;gray&quot;&gt;[Aucun]&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5420"/>
        <source>The time that you computer first saw this transaction</source>
        <translation>L&apos;heure à laquelle votre ordinateur a vu cette transaction la première fois</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5423"/>
        <source>All transactions are eventually included in a &quot;block.&quot;  The
                  time shown here is the time that the block entered the &quot;blockchain.&quot;</source>
        <translation>Toutes les transactions finissent par être incluses dans un bloc. L&apos;heure qui apparaît ici est l&apos;heure d&apos;entrée du bloc dans la « chaîne de blocs ».</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5433"/>
        <source>This transaction has not yet been included in a block.
                  It usually takes 5-20 minutes for a transaction to get
                  included in a block after the user hits the &quot;Send&quot; button.</source>
        <translation>Cette transaction n&apos;a pas encore été incluse dans un bloc.
Il faut habituellement de 5 à 20 minutes pour qu&apos;une transaction soit incluse dans un bloc après que l&apos;utilisateur a cliqué sur le bouton « Envoyer ».</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5445"/>
        <source>Every transaction is eventually included in a &quot;block&quot; which
                  is where the transaction is permanently recorded.  A new block
                  is produced approximately every 10 minutes.</source>
        <translation>Chaque transaction est finalement incluse dans un bloc où la transaction est inscrite de façon permanente. Un nouveau bloc est produit approximativement toutes les 10 minutes.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5454"/>
        <source>The number of blocks that have been produced since
                     this transaction entered the blockchain.  A transaction
                     with 6 or more confirmations is nearly impossible to reverse.</source>
        <translation>Le nombre de blocs produits depuis que cette transaction fait partie de la chaîne de blocs. Il est quasiment impossible d&apos;annuler une transaction ayant six confirmations ou plus.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5458"/>
        <source>Confirmations:</source>
        <translation>Confirmations :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5464"/>
        <source>This transaction can be replaced by another transaction that
               spends the same inputs if the replacement transaction has
               a higher fee.</source>
        <translation>Cette transaction peut être remplacée par une autre transaction qui dépense les mêmes entrées, si la transaction de remplacement a des frais plus élevés.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5468"/>
        <source>Mempool Replaceable: </source>
        <translation>Remplaçables dans la réserve de mémoire  :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5477"/>
        <source>Most transactions have at least a recipient output and a
               returned-change output.  You do not have enough information
               to determine which is which, and so this fields shows the sum
               of &lt;b&gt;all&lt;/b&gt; outputs.</source>
        <translation>La plupart des transactions ont au moins une sortie de destinataire et une sortie de monnaie rendue. Vous n&apos;avez pas assez d&apos;informations pour déterminer laquelle est laquelle et par conséquent ces champs affichent la somme de &lt;b&gt;toutes&lt;/b&gt; les sorties.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5482"/>
        <source>Sum of Outputs:</source>
        <translation>Sommes des sorties :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5486"/>
        <source>Bitcoins were either sent or received, or sent-to-self</source>
        <translation>Des bitcoins ont été reçus ou envoyés ou encore envoyés-à-soi</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5492"/>
        <source>The value shown here is the net effect on your
               wallet, including transaction fee.</source>
        <translation>La valeur apparaissant ici est l&apos;effet net sur votre porte-monnaie, incluant les frais de transaction.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5506"/>
        <source>Transaction fees go to users supplying the Bitcoin network with
            computing power for processing transactions and maintaining security.</source>
        <translation>Les frais de transaction sont versés aux utilisateurs qui fournissent au réseau la puissance de calcul pour traiter les transactions et assurer la sécurité.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5538"/>
        <source>All outputs of the transaction &lt;b&gt;excluding&lt;/b&gt; change-
                  back-to-sender outputs.  If this list does not look
                  correct, it is possible that the change-output was
                  detected incorrectly -- please check the complete
                  input/output list below.</source>
        <translation>Toutes les sorties de la transaction &lt;b&gt;excluant&lt;/b&gt; les sorties monnaie-rendue-à-l&apos;expéditeur. Si cette liste semble incorrecte, il est possible que la sortie « monnaie » ait été détectée incorrectement. Veuillez vérifier la liste complète des entrées et sorties ci-dessous.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5544"/>
        <source>Recipients:</source>
        <translation>Destinataires :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5558"/>
        <source>[%1 more recipients]</source>
        <translation>[%1 autres destinataires]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5672"/>
        <source>Transaction Inputs (Sending addresses):</source>
        <translation>Entrées transactionnelles (adresses d&apos;expédition ) :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5673"/>
        <source>All transactions require previous transaction outputs as
                  inputs.  </source>
        <translation>Toutes les transactions exigent les sorties transactionnelles précédentes comme entrées.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5676"/>
        <source>&lt;b&gt;Since the blockchain is not available, not all input
                      information is available&lt;/b&gt;.  You need to view this
                      transaction on a system with an internet connection
                      (and blockchain) if you want to see the complete information.</source>
        <translation>&lt;b&gt;Dans la mesure où la chaîne de blocs n&apos;est pas disponible, toutes les informations d&apos;entrée ne sont pas disponibles.&lt;/b&gt;. Vous devez visualiser cette transaction sur un système possédant une connexion à Internet (et la chaîne de blocs) si vous souhaitez voir l&apos;intégralité des informations.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5681"/>
        <source>Each input is like an X amount dollar bill.  Usually there are more inputs
                      than necessary for the transaction, and there will be an extra
                      output returning change to the sender</source>
        <translation>Chaque entrée est comme un billet d&apos;un montant de X $. Il y a habituellement plus d&apos;entrées que requis pour la transaction et il y aura une sortie supplémentaire pour rendre la monnaie à l&apos;expéditeur</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5686"/>
        <source>Transaction Outputs (Receiving addresses):</source>
        <translation>Sorties transactionnelles (adresses de réception) :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5687"/>
        <source>Shows &lt;b&gt;all&lt;/b&gt; outputs, including other recipients
                  of the same transaction, and change-back-to-sender outputs
                  (change outputs are displayed in light gray).</source>
        <translation>Affiche &lt;b&gt;toutes&lt;/b&gt; les sorties, incluant les autres destinataires de la même transaction et les sorties monnaie-rendue-à-l&apos;expéditeur (les sorties de monnaie sont affichées en gris clair).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5692"/>
        <source>Some outputs might be &quot;change.&quot;
         </source>
        <translation>Certaines sorties pourraient être de la monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5711"/>
        <source>Copy Raw Tx (Hex)</source>
        <translation>Copier la transaction brute (hexadécimal)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5713"/>
        <source>OK</source>
        <translation>OK</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5750"/>
        <source>Transaction Info</source>
        <translation>Infos transactionnelles</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5759"/>
        <source>&lt;&lt;&lt; Less Info</source>
        <translation>&lt;&lt;&lt; Moins d&apos;infos</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5769"/>
        <source>Advanced &gt;&gt;&gt;</source>
        <translation>Avancé &gt;&gt;&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5780"/>
        <source>TxIn Script:</source>
        <translation>Script de l&apos;entrée transactionnelle :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5787"/>
        <source>TxOut Script:</source>
        <translation>Script de la sortie transactionnelle :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5826"/>
        <source>&lt;i&gt;Copied to Clipboard!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Copié dans le presse-papiers !&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5856"/>
        <source>Copy Sender Address</source>
        <translation>Copier l&apos;adresse de l&apos;expéditeur</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5892"/>
        <source>Copy Wallet ID</source>
        <translation>Copier l&apos;ID du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5893"/>
        <source>Copy Amount</source>
        <translation>Copier le montant</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5859"/>
        <source>More Info</source>
        <translation>Plus d&apos;infos.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5891"/>
        <source>Copy Recipient Address</source>
        <translation>Copier l&apos;adresse du destinataire</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5894"/>
        <source>Copy Raw Script</source>
        <translation>Copier le script brut</translation>
    </message>
</context>
<context>
    <name>DlgDisplayTxIn</name>
    <message>
        <location filename="qtdialogs.py" line="5920"/>
        <source>&lt;center&gt;&lt;u&gt;&lt;b&gt;TxIn Information&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</source>
        <translation>&lt;center&gt;&lt;u&gt;&lt;b&gt;Informations sur l&apos;entrée transactionnelle&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5945"/>
        <source>[[Cannot determine from TxIn Script]]</source>
        <translation>[[Impossible à déterminer à partir du script de l&apos;entrée transactionnelle]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5950"/>
        <source>Wallet &quot;%1&quot; (%2)</source>
        <translation>Porte-monnaie « %1 » (%2)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5954"/>
        <source>Lockbox %1-of-%2 &quot;%3&quot; (%4)</source>
        <translation>Coffre %1-de-%2 « %3 » (%4)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5959"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Informations sur l&apos;entrée transactionnelle&lt;/b&gt;&lt;/u&gt;&lt;/font&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5960"/>
        <source>   &lt;b&gt;TxIn Index:&lt;/b&gt;         %1</source>
        <translation>&lt;b&gt;Index de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5961"/>
        <source>   &lt;b&gt;TxIn Spending:&lt;/b&gt;      %1:%2</source>
        <translation>&lt;b&gt;Dépense de l&apos;entrée transactionnelle&lt;/b&gt; %1:%2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5962"/>
        <source>   &lt;b&gt;TxIn Sequence&lt;/b&gt;:      0x%1</source>
        <translation>&lt;b&gt;Séquence de l&apos;entrée transactionnelle&lt;/b&gt; : 0x%1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5964"/>
        <source>   &lt;b&gt;TxIn Script Type&lt;/b&gt;:   %1</source>
        <translation>&lt;b&gt;Type de script de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5965"/>
        <source>   &lt;b&gt;TxIn Source&lt;/b&gt;:        %1</source>
        <translation>&lt;b&gt;Source de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5967"/>
        <source>   &lt;b&gt;TxIn Wallet&lt;/b&gt;:        %1</source>
        <translation>&lt;b&gt;Porte-monnaie de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5968"/>
        <source>   &lt;b&gt;TxIn Script&lt;/b&gt;:</source>
        <translation>&lt;b&gt;Script de l&apos;entrée transactionnelle&lt;/b&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5996"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxOut being spent by this TxIn&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Informations sur la sortie transactionnelle dépensée par cette entrée transactionnelle&lt;/b&gt;&lt;/u&gt;&lt;/font&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5997"/>
        <source>   &lt;b&gt;Tx Hash:&lt;/b&gt;            %1</source>
        <translation>&lt;b&gt;Hachage de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5998"/>
        <source>   &lt;b&gt;Tx Out Index:&lt;/b&gt;       %1</source>
        <translation>&lt;b&gt;Index de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5999"/>
        <source>   &lt;b&gt;Tx in Block#:&lt;/b&gt;       %1</source>
        <translation>&lt;b&gt;No de bloc de l&apos;entrée transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6000"/>
        <source>   &lt;b&gt;TxOut Value:&lt;/b&gt;        %1</source>
        <translation>&lt;b&gt;Valeur de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6001"/>
        <source>   &lt;b&gt;TxOut Script Type:&lt;/b&gt;  %1</source>
        <translation>&lt;b&gt;Type de script de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6002"/>
        <source>   &lt;b&gt;TxOut Address:&lt;/b&gt;      %1</source>
        <translation>&lt;b&gt;Adresse de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6004"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       %1</source>
        <translation>&lt;b&gt;Porte-monnaie de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6005"/>
        <source>   &lt;b&gt;TxOUt Script:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Script de la sortie transactionnelle &lt;/b&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6012"/>
        <source>Ok</source>
        <translation>OK</translation>
    </message>
</context>
<context>
    <name>DlgDisplayTxOut</name>
    <message>
        <location filename="qtdialogs.py" line="6030"/>
        <source>&lt;center&gt;&lt;u&gt;&lt;b&gt;TxOut Information&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</source>
        <translation>&lt;center&gt;&lt;u&gt;&lt;b&gt;Informations sur la sortie transactionnelle&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6066"/>
        <source>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Information on TxOut&lt;/b&gt;&lt;/u&gt;&lt;/font&gt;:</source>
        <translation>&lt;font size=4&gt;&lt;u&gt;&lt;b&gt;Informations sur la sortie transactionnelle&lt;/b&gt;&lt;/u&gt;&lt;/font&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6067"/>
        <source>   &lt;b&gt;Tx Out Index:&lt;/b&gt;       %1</source>
        <translation>&lt;b&gt;Index de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6068"/>
        <source>   &lt;b&gt;TxOut Value:&lt;/b&gt;        %1</source>
        <translation>&lt;b&gt;Valeur de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6069"/>
        <source>   &lt;b&gt;TxOut Script Type:&lt;/b&gt;  %1</source>
        <translation>&lt;b&gt;Type de script de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6070"/>
        <source>   &lt;b&gt;TxOut Address:&lt;/b&gt;      %1</source>
        <translation>&lt;b&gt;Adresse de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6072"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       %1</source>
        <translation>&lt;b&gt;Porte-monnaie de la sortie transactionnelle&lt;/b&gt; : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6074"/>
        <source>   &lt;b&gt;TxOut Wallet:&lt;/b&gt;       [[Unrelated to any loaded wallets]]</source>
        <translation>&lt;b&gt;Porte-monnaie de la sortie transactionnelle&lt;/b&gt; : [[sans relation avec aucun porte-monnaie chargé]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6075"/>
        <source>   &lt;b&gt;TxOut Script:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Script de la sortie transactionnelle&lt;/b&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6082"/>
        <source>Ok</source>
        <translation>OK</translation>
    </message>
</context>
<context>
    <name>DlgDuplicateAddr</name>
    <message>
        <location filename="qtdialogs.py" line="3082"/>
        <source>No Addresses to Import</source>
        <translation>Aucune adresse à importer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3082"/>
        <source>There are no addresses to import!</source>
        <translation>Il n&apos;y a aucune adresse à importer !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3086"/>
        <source>
         &lt;font color=%1&gt;Duplicate addresses detected!&lt;/font&gt; The following
         addresses already exist in other Armory wallets:</source>
        <translation>
&lt;font color=%1&gt;Des doublons d&apos;adresse ont été détectés !&lt;/font&gt; Les adresses suivantes existent déjà dans d&apos;autres porte-monnaie Armory :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3099"/>
        <source>
         Duplicate addresses cannot be imported.  If you continue,
         the addresses above will be ignored, and only new addresses
         will be imported to this wallet.</source>
        <translation>
Les doublons d&apos;adresse ne peuvent pas être importés. Si vous poursuivez, les adresses ci-dessus seront ignorées et seules les nouvelles adresses seront importées dans ce porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3105"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3106"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3119"/>
        <source>Duplicate Addresses</source>
        <translation>Adresses en double</translation>
    </message>
</context>
<context>
    <name>DlgECDSACalc</name>
    <message>
        <location filename="qtdialogs.py" line="7371"/>
        <source>Multiply Scalars (mod n)</source>
        <translation>Multiplier par les scalaires (mod n)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7372"/>
        <source>Scalar Multiply EC Point</source>
        <translation>Scalaire multiplier par le point de CE</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7373"/>
        <source>Add EC Points</source>
        <translation>Additionner des points de courbe elliptique</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7488"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7475"/>
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
Utiliser ce formulaire pour effectuer des calculs de courbes elliptiques Bitcoin. Toutes les opérations sont effectuées sur la courbe elliptique secp256k1 qui est celle utilisée pour Bitcoin.
Fournir toutes les valeurs en entiers 32 octets, gros-boutistes, encodées en hexadécimal.
&lt;br&gt;&lt;br&gt;
Voici les coordonnées du point générateur secp256k1 (G) : &lt;br&gt;
&lt;b&gt;G&lt;/b&gt;&lt;sub&gt;x&lt;/sub&gt; : %1 &lt;br&gt;
&lt;b&gt;G&lt;/b&gt;&lt;sub&gt;y&lt;/sub&gt; : %2
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7492"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Retour</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7508"/>
        <source>ECDSA Calculator</source>
        <translation>Calculateur ECDSA</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7518"/>
        <source>Bad Input</source>
        <translation>Entrée erronée</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7518"/>
        <source>Value &quot;%1&quot; is invalid.  Make sure the value is specified in
            hex, big-endian</source>
        <translation>S&apos;assurer que la valeur %1 est indiquée en hexadécimal, gros-boutiste</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7572"/>
        <source>Invalid EC Point</source>
        <translation>Point de CE invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7544"/>
        <source>The point you specified (&lt;b&gt;B&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation>Le point que vous avez spécifié (&lt;b&gt;B&lt;/b&gt;) n&apos;est pas sur la courbe elliptique utilisée dans Bitcoin (secp256k1). </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7566"/>
        <source>The point you specified (&lt;b&gt;A&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation>Le point que vous avez spécifié (&lt;b&gt;A&lt;/b&gt;) n&apos;est pas sur la courbe elliptique utilisée dans Bitcoin (secp256k1).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7572"/>
        <source>'The point you specified (&lt;b&gt;B&lt;/b&gt;) is not on the
            elliptic curve used in Bitcoin (secp256k1).</source>
        <translation>Le point que vous avez spécifié (&lt;b&gt;B&lt;/b&gt;) n&apos;est pas sur la courbe elliptique utilisée dans Bitcoin (secp256k1).</translation>
    </message>
</context>
<context>
    <name>DlgEULA</name>
    <message>
        <location filename="qtdialogs.py" line="3540"/>
        <source>I agree to all the terms of the license above</source>
        <translation>J&apos;accepte toutes les conditions de la licence ci-dessus</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3542"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3543"/>
        <source>Accept</source>
        <translation>Accepter</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3551"/>
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
        <translation>
&lt;b&gt;Le client Armory Bitcoin est distribué en partie sous &lt;i&gt;licence publique générale GNU Affero, version 3 (AGPLv3)&lt;/i&gt; et en partie sous &lt;i&gt;licence MIT&lt;/i&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;De plus, en tant que condition pour recevoir ce logiciel gratuitement, vous acceptez tous les risques associés à son utilisation et que les développeurs d&apos;Armory ne pourront être tenus responsables d&apos;aucune perte d&apos;argent ou de bitcoins en raison de défaillances du logiciel.&lt;br&gt;&lt;br&gt;
&lt;b&gt;Veuillez lire l&apos;intégralité des conditions générales de la licence et indiquez que vous acceptez ses conditions.&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3572"/>
        <source>Armory License Agreement</source>
        <translation>Licence d&apos;utilisation d&apos;Armory</translation>
    </message>
</context>
<context>
    <name>DlgEnterOneFrag</name>
    <message>
        <location filename="qtdialogs.py" line="12255"/>
        <source> You have entered fragments %1, so far.  </source>
        <translation>Vous avez jusqu&apos;à présent saisi les fragments %1.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12257"/>
        <source>
         &lt;b&gt;&lt;u&gt;Enter Another Fragment...&lt;/u&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt; %1
         The fragments can be entered in any order, as long as you provide
         enough of them to restore the wallet.  If any fragments use a
         SecurePrintâ¢ code, please enter it once on the
         previous window, and it will be applied to all fragments that
         require it.</source>
        <translation>
&lt;b&gt;&lt;u&gt;Saisir un autre fragment...&lt;/u&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt; %1
Les fragments peuvent être saisis dans n&apos;importe quel ordre, tant que vous en fournissez assez pour récupérer le porte-monnaie. Si un des fragments utilise un code SecurePrint™, veuillez le saisir une fois dans la fenêtre précédente et il sera appliqué pour tous les fragments qui l&apos;exigent.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12307"/>
        <source>&lt;b&gt;Backup Type:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Type de sauvegarde :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12339"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation>Code SecurePrint™ :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12354"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12355"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12371"/>
        <source>Restore Single-Sheet Backup</source>
        <translation>Restaurer une sauvegarde d&apos;une seule feuille</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12437"/>
        <source>
               The ID field indicates that this is a SecurePrintâ¢
               Backup Type. You have either entered the ID incorrectly or
               have chosen an incorrect Backup Type.</source>
        <translation>
Le champ ID indique qu&apos;il s&apos;agit d&apos;un type de sauvegarde SecurePrint™. Soit l&apos;ID a été saisi incorrectement, soit vous avez choisi un type de sauvegarde incorrecte.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12455"/>
        <source>Verify Wallet ID</source>
        <translation>Vérifier l&apos;ID du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12455"/>
        <source>
               There is an error in the data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page. &lt;br&gt;&lt;br&gt;
               The error occured on the &quot;%1&quot; line.</source>
        <translation>
Les données que vous avez saisies comportent une erreur qui n&apos;a pas pu être corrigée automatiquement. Veuillez vous assurer d&apos;avoir saisi le texte exactement comme il apparaît sur la page de sauvegarde du porte-monnaie.&lt;br&gt;&lt;br&gt;
L&apos;erreur se trouve sur la ligne « %1 ».</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12474"/>
        <source>Verify Fragment ID</source>
        <translation>Vérifier l&apos;ID du fragment</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12474"/>
        <source>
         The data you entered is for fragment:
         &lt;br&gt;&lt;br&gt; &lt;font color=&quot;%1 size=3&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt;  &lt;br&gt;&lt;br&gt;
         Does this ID match the &quot;Fragment:&quot; field displayed on your backup?
         If not, click &quot;No&quot; and re-enter the fragment data.</source>
        <translation>
Les données que vous avez saisies sont pour le fragment :
&lt;br&gt;&lt;br&gt; &lt;font color=&quot;%1 size=3&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt;  &lt;br&gt;&lt;br&gt;
Cet ID correspond-il au champ « Fragment: » qui apparaît sur votre sauvegarde ? Sinon, cliquez sur Non et saisissez les données du fragment de nouveau.</translation>
    </message>
</context>
<context>
    <name>DlgEnterSecurePrintCode</name>
    <message>
        <location filename="qtdialogs.py" line="12209"/>
        <source>
         This fragment file requires a SecurePrintâ¢ code.
         You will only have to enter this code once since it is the same
         on all fragments.</source>
        <translation>
Ce fichier fragment exige un code SecurePrint™. Vous n&apos;aurez à saisir à ce code qu&apos;une seule fois, car il est identique pour tous les fragments.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12214"/>
        <source>SecurePrintâ¢ Code: </source>
        <translation>Code SecurePrint™ :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12218"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12219"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12231"/>
        <source>Enter Secure Print Code</source>
        <translation>Saisir le code SecurePrint™</translation>
    </message>
</context>
<context>
    <name>DlgExecLongProcess</name>
    <message>
        <location filename="qtdialogs.py" line="7286"/>
        <source>Please Wait...</source>
        <translation>Veuillez patienter...</translation>
    </message>
</context>
<context>
    <name>DlgExpWOWltData</name>
    <message>
        <location filename="qtdialogs.py" line="10079"/>
        <source>Export Watching-Only Wallet File</source>
        <translation>Exporter le fichier du porte-monnaie juste-regarder</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10080"/>
        <source>Copy to clipboard</source>
        <translation>Copier dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10082"/>
        <source>Save to Text File</source>
        <translation>Enregistrer vers un fichier texte</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10083"/>
        <source>Print Root Data</source>
        <translation>Imprimer les données racines</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10095"/>
        <source>
         Watch-Only Root ID:&lt;br&gt;&lt;b&gt;%1&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Watch-Only Root Data:</source>
        <translation>
ID racine regarder-seulement :&lt;br&gt;&lt;b&gt;%1&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Données racines regarder-seulement :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10102"/>
        <source>Watch-Only Wallet Export</source>
        <translation>Exportation du porte-monnaie juste-regarder</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10114"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;A été Copié !&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10119"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;&lt;font size=4 color=&quot;%1&quot;&gt;Export Watch-Only
         Wallet: %2&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Use a watching-only wallet on an online computer to distribute
         payment addresses, verify transactions and monitor balances, but
         without the ability to move the funds.</source>
        <translation>
&lt;center&gt;&lt;b&gt;&lt;u&gt;&lt;font size=4 color=&quot;%1&quot;&gt;Exporter le porte-monnaie juste-regarder : %2&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
&lt;br&gt;
Utilisez un porte-monnaie juste-regarder sur un ordinateur en ligne pour
répartir les adresses de paiement, vérifier les transactions et surveiller les
soldes, mais sans possibilité de transférer des fonds.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10127"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Entire Wallet File&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         &lt;i&gt;&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;(Recommended)&lt;/font&gt;&lt;/b&gt;&lt;/i&gt;
         An exact copy of your wallet file but without any of the private
         signing keys. All existing comments and labels will be carried
         with the file. Use this option if it is easy to transfer files
         from this system to the target system.</source>
        <translation>
&lt;center&gt;&lt;b&gt;&lt;u&gt;Fichier de votre porte-monnaie entier&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
&lt;br&gt;
&lt;i&gt;&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;(Recommandé)&lt;/font&gt;&lt;/b&gt;&lt;/i&gt;
Une copie exacte du fichier de votre porte-monnaie, mais sans clé privée de signature. Tous les commentaires et étiquettes existants seront inclus dans le fichier. Utilisez cette option s&apos;il est facile de transférer des fichiers de ce système vers le système cible.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10136"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Only Root Data&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Same as above, but only five lines of text that are easy to
         print, email inline, or copy by hand.  Only produces the
         wallet addresses.   No comments or labels are carried with
         it.</source>
        <translation>
&lt;center&gt;&lt;b&gt;&lt;u&gt;Seulement les données racines&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
&lt;br&gt;
Comme ci-dessus, mais seulement 5 lignes de texte qui sont faciles à imprimer, à envoyer dans un courriel ou à copier à la main. Cela ne produit que les adresses des porte-monnaie et ne contient aucun commentaire ni étiquette.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10144"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
</context>
<context>
    <name>DlgExportAsciiBlock</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2325"/>
        <source>Copy to Clipboard</source>
        <translation>Copier dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2326"/>
        <source>Save to File</source>
        <translation>Enregistrer dans un fichier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2327"/>
        <source>Send Email</source>
        <translation>Envoyer un courriel</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2328"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2350"/>
        <source>Export ASCII Block</source>
        <translation>Exporter le bloc ASCII</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2382"/>
        <source>Email Triggered</source>
        <translation>Le courriel a été déclenché</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2382"/>
        <source>
            Armory attempted to execute a &quot;mailto:&quot; link which should trigger
            your email application or web browser to open a compose-email window.
            This does not work in all environments, and you might have to 
            manually copy and paste the text in the box into an email.
            </source>
        <translation>
Armory a tenté d&apos;exécuter un lien de courriel « mailto: » qui devrait déclencher une application de courriel ou l&apos;ouverture d&apos;une page de rédaction de courriel dans un navigateur. Cela ne fonctionne pas dans tous les environnements et vous pourriez devoir copier-coller manuellement le texte contenu dans la boîte dans un courriel.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2382"/>
        <source>Do not show this message again</source>
        <translation>Ne plus afficher ce message</translation>
    </message>
</context>
<context>
    <name>DlgExportTxHistory</name>
    <message>
        <location filename="qtdialogs.py" line="9039"/>
        <source>My Wallets</source>
        <translation>Mes porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9040"/>
        <source>Offline Wallets</source>
        <translation>Porte-monnaie hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9041"/>
        <source>Other Wallets</source>
        <translation>Autres porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9044"/>
        <source>All Wallets</source>
        <translation>Tous les porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9045"/>
        <source>All Lockboxes</source>
        <translation>Tous les coffres</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9046"/>
        <source>All Wallets &amp; Lockboxes</source>
        <translation>Tous les porte-monnaie et coffres</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9059"/>
        <source>Date (newest first)</source>
        <translation>Date (plus récente en premier)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9060"/>
        <source>Date (oldest first)</source>
        <translation>Date (plus ancienne en premier)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9065"/>
        <source>Comma-Separated Values (*.csv)</source>
        <translation>Valeurs séparées par des virgules (*.csv)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9069"/>
        <source>Use any of the following symbols:&lt;br&gt;</source>
        <translation>Utiliser un des symboles suivants :&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9080"/>
        <source>Reset to Default</source>
        <translation>Rétablir les valeurs par défaut </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9090"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9091"/>
        <source>Export</source>
        <translation>Exporter</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9100"/>
        <source>Export Format:</source>
        <translation>Format d&apos;exportation :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9107"/>
        <source>Wallet(s) to export:</source>
        <translation>Porte-monnaie à exporter :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9114"/>
        <source>Sort Table:</source>
        <translation>Trier le tableau :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9120"/>
        <source>Date Format:</source>
        <translation>Format de date :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9145"/>
        <source>Example: %1</source>
        <translation>Exemple : %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9148"/>
        <source>Example: [[invalid date format]]</source>
        <translation>Exemple : [[format de date invalide]]</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9160"/>
        <source>Invalid date format</source>
        <translation>Format de date invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9160"/>
        <source>Cannot create CSV without a valid format for transaction dates and times</source>
        <translation>Il est impossible de créer un fichier CSV sans un format valide pour les dates et heures des transactions.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9215"/>
        <source>Total</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9216"/>
        <source>Spendable</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9217"/>
        <source>Unconfirmed</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9256"/>
        <source>Export Date: %1
</source>
        <translation>Date d&apos;exportation : %1
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9257"/>
        <source>Total Funds: %1
</source>
        <translation>Total des fonds : %1
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9258"/>
        <source>Spendable Funds: %1
</source>
        <translation>Fonds disponibles : %1
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9259"/>
        <source>Unconfirmed Funds: %1
</source>
        <translation>Fonds non confirmés : %1
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9262"/>
        <source>Included Wallets:
</source>
        <translation>Porte-monnaie inclus :
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9269"/>
        <source>%1 (lockbox),%2
</source>
        <translation>%1 (coffre),%2
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9273"/>
        <source>Date</source>
        <translation>Date </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9273"/>
        <source>Transaction ID</source>
        <translation>ID de la transaction</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9273"/>
        <source>Number of Confirmations</source>
        <translation>Nombre de confirmations</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9273"/>
        <source>Wallet ID</source>
        <translation>ID du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9274"/>
        <source>Wallet Name</source>
        <translation>Nom du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9274"/>
        <source>Credit</source>
        <translation>Crédit</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9274"/>
        <source>Debit</source>
        <translation>Débit</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9274"/>
        <source>Fee (paid by this wallet)</source>
        <translation>Frais (payés par ce porte-monnaie)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9275"/>
        <source>Wallet Balance</source>
        <translation>Solde du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9275"/>
        <source>Total Balance</source>
        <translation>Solde total</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9275"/>
        <source>Label</source>
        <translation>Étiquette</translation>
    </message>
</context>
<context>
    <name>DlgFactoryReset</name>
    <message>
        <location filename="qtdialogs.py" line="13355"/>
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
        <translation>
&lt;b&gt;&lt;u&gt;Réinitialisation générale d&apos;Armory&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Il vous est &lt;i&gt;fortement&lt;/i&gt; recommandé de faire des sauvegardes de vos porte-monnaie avant de poursuivre, bien qu&apos;&lt;b&gt;aucun fichier de porte-monnaie ne sera jamais supprimé intentionnellement !&lt;/b&gt; Tous les fichiers de porte-monnaie d&apos;Armory et le fichier wallet.dat utilisé par Bitcoin Core/bitcoind devraient rester intacts dans leur emplacement actuel. Tous les porte-monnaie d&apos;Armory seront détectés et rechargés automatiquement après la réinitialisation.
&lt;br&gt;&lt;br&gt;
Si vous ne savez pas quelle option choisir, essayez l&apos;option « la plus légère » en premier et voyez si vos problèmes sont résolus avant de tenter les options extrêmes.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13373"/>
        <source>
         &lt;b&gt;Delete settings and rescan (lightest option)&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Supprimer les paramètres et réanalyser (option la plus légère)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13375"/>
        <source>
         Only delete the settings file and transient network data.  The
         databases built by Armory will be rescanned (about 5-45 minutes)</source>
        <translation>
Supprimer seulement le fichier des paramètres et les données réseau transitoires. Les bases de données construites par Armory seront réanalysées (de 4 à 45 minutes)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13380"/>
        <source>
         &lt;b&gt;Also delete databases and rebuild&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Supprimer aussi les bases de données et les reconstruire&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13382"/>
        <source>
         Will delete settings, network data, and delete Armory's databases. The databases
         will be rebuilt and rescanned (45 min to 3 hours)</source>
        <translation>
Supprimera les paramètres, les données réseau et les bases de données d&apos;Armory. Les bases de données seront reconstruites et réanalysées (de 45 minutes à 3 heures).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13387"/>
        <source>
         &lt;b&gt;Also re-download the blockchain (extreme)&lt;/b&gt;</source>
        <translation>
&lt;b&gt;Retélécharger aussi la chaîne de blocs (extrême)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13389"/>
        <source>
         This will delete settings, network data, Armory's databases,
         &lt;b&gt;and&lt;/b&gt; Bitcoin Core's databases.  Bitcoin Core will
         have to download the blockchain again. This can take 8-72 hours depending on your 
         system's speed and connection.  Only use this if you
         suspect blockchain corruption, such as receiving StdOut/StdErr errors
         on the dashboard.</source>
        <translation>
Cela supprimera les paramètres, les données réseau, les bases de données d&apos;Armory &lt;b&gt;et&lt;/b&gt; les bases de données du logiciel Bitcoin Core. Bitcoin Core devra retélécharger la chaîne de blocs. Cela peut prendre de 8 à 72 heures selon la vitesse et la connexion de votre système. N&apos;utilisez cette option que si vous soupçonnez une corruption de la chaîne de blocs, par exemple des erreurs « StdOut/StdErr » dans le tableau de bord.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13398"/>
        <source>Do not delete settings files</source>
        <translation>Ne pas effacer les fichiers de configuration</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13429"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13430"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13444"/>
        <source>Factory Reset</source>
        <translation>Réinitialisation générale</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13503"/>
        <source>Confirmation</source>
        <translation>Confirmation</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13454"/>
        <source>
            You are about to delete your settings and force Armory to rescan
            its databases.  Are you sure you want to do this?</source>
        <translation>
Vous êtes sur le point de supprimer vos paramètres et de forcer Armory à réanalyser ses bases de données. Voulez-vous vraiment le faire ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13469"/>
        <source>
            You are about to delete your settings and force Armory to delete
            and rebuild its databases.  Are you sure you want to do this?</source>
        <translation>
Vous êtes sur le point de supprimer vos paramètres et de forcer Armory  à supprimer et à réanalyser ses bases de données. Voulez-vous vraiment le faire ?</translation>
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
        <location filename="qtdialogs.py" line="13541"/>
        <source>Aborted</source>
        <translation>Interrompu</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13541"/>
        <source>
                  You canceled the factory reset operation.  No changes were
                  made.</source>
        <translation>
Vous avez annulé la réinitialisation générale. Aucun changement n&apos;a été apporté.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13557"/>
        <source>Restart Armory</source>
        <translation>Redémarrer Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13516"/>
        <source>
               &lt;b&gt;Bitcoin Core (or bitcoind) must be closed to do the reset!&lt;/b&gt;
               Please close all Bitcoin software, &lt;u&gt;&lt;b&gt;right now&lt;/b&gt;&lt;/u&gt;,
               before clicking &quot;Continue&quot;.
               &lt;br&gt;&lt;br&gt;
               Armory will now close.  Please restart Bitcoin Core/bitcoind
               first and wait for it to finish synchronizing before restarting
               Armory.</source>
        <translation>
&lt;b&gt;Bitcoin Core (ou bitcoind) doit être fermé pour exécuter la réinitialisation !&lt;/b&gt;
Veuillez fermer &lt;u&gt;&lt;b&gt;immédiatement&lt;/b&gt;&lt;/u&gt; tous les logiciels Bitcoin, avant de cliquer sur « Poursuivre ».
&lt;br&gt;&lt;br&gt;
Armory va maintenant se fermer. Veuillez d&apos;abord relancer Bitcoin Core/bitcoind et attendre la fin de sa synchronisation avant de redémarrer Armory.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14750"/>
        <source>
                  You canceled the factory-reset operation.  No changes were
                  made.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13535"/>
        <source>
               Armory will now close to apply the requested changes.  Please
               restart it when you are ready to start the blockchain download
               again.</source>
        <translation>
Armory va maintenant se fermer pour appliquer les changements demandés. Veuillez la relancer quand vous serez prêt à lancer le nouveau téléchargement de la chaîne de blocs.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13557"/>
        <source>
         Armory will now close so that the requested changes can
         be applied.</source>
        <translation>
Armory va maintenant se fermer afin d&apos;appliquer les changements demandés.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13487"/>
        <source>
               You are about to delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload all of the blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation>
Vous êtes sur le point de supprimer &lt;b&gt;toutes&lt;/b&gt; les bases de données de la chaîne de blocs se trouvant sur votre système. Le logiciel Bitcoin devra retélécharger toutes les données de la chaîne de blocs par le réseau de pair à pair. Cela peut prendre de 8 à 72 heures selon la vitesse et la connexion de votre système. &lt;br&gt;&lt;br&gt;&lt;b&gt;Voulez-vous absolument le faire ?&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13495"/>
        <source>
               You are about to delete your settings and delete &lt;b&gt;all&lt;/b&gt;
               blockchain databases on your system.  The Bitcoin software will
               have to redownload all of the blockchain data over the peer-to-peer
               network again. This can take from 8 to 72 hours depending on
               your system's speed and connection.  &lt;br&gt;&lt;br&gt;&lt;b&gt;Are you absolutely
               sure you want to do this?&lt;/b&gt;</source>
        <translation>
Vous êtes sur le point de supprimer vos paramètres et &lt;b&gt;toutes&lt;/b&gt; les bases de données de la chaîne de blocs se trouvant sur votre système. Le logiciel Bitcoin devra retélécharger toutes les données de la chaîne de blocs par le réseau de pair à pair. Cela peut prendre de 8 à 72 heures selon la vitesse et la connexion de votre système. &lt;br&gt;&lt;br&gt;&lt;b&gt;Voulez-vous absolument le faire ?&lt;/b&gt;</translation>
    </message>
</context>
<context>
    <name>DlgForkedImports</name>
    <message>
        <location filename="qtdialogs.py" line="13568"/>
        <source>&lt;h2 style=&quot;color: red; text-align: center;&quot;&gt;Forked imported addresses have been       detected in your wallets!!!&lt;/h2&gt;</source>
        <translation>&lt;h2 style=&quot;color: red; text-align: center;&quot;&gt;Des adresses importées dérivées ont été détectées dans vos porte-monnaie !!!&lt;/h2&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13571"/>
        <source>The following wallets have forked imported addresses: &lt;br&gt;&lt;br&gt;&lt;b&gt;</source>
        <translation>Les portefeuilles suivants comportent des adresses importées dérivées : &lt;br&gt;&lt;br&gt;&lt;b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13574"/>
        <source>When you fix a corrupted wallet, any damaged private keys will be off       the deterministic chain. It means these private keys cannot be recreated       by your paper backup. If such private keys are encountered, Armory saves       them as forked imported private keys after it fixes the relevant wallets.</source>
        <translation>Quand vous corrigez un porte-monnaie corrompu, toute clé privée endommagée est retirée de la chaîne déterministe. Cela signifie que ces clés privées ne peuvent pas être recréées par votre sauvegarde papier. Si de telles clés privées sont présentes, Armory les enregistre en tant que clés privées importées dérivées après avoir corrigé les porte-monnaie concernés.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="14803"/>
        <source>&lt;h1 style=&quot;color: orange;&quot;&gt; - Do not accept payments to these wallets anymore&lt;br&gt;      - Do not delete or overwrite these wallets. &lt;br&gt;       - Transfer all funds to a fresh and backed up wallet&lt;h1&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13615"/>
        <source>Forked Imported Addresses</source>
        <translation>Adresses importées dérivées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13579"/>
        <source>&lt;h1 style=&quot;color: orange;&quot;&gt; - Do not accept payments to these wallets anymore&lt;br&gt;      - Do not delete or overwrite these wallets. &lt;br&gt;       - Transfer all funds to a fresh and backed up wallet&lt;/h1&gt;</source>
        <translation>&lt;h1 style=&quot;color: orange;&quot;&gt; - Ne plus accepter de paiements vers ces porte-monnaie&lt;br&gt; - Ne pas supprimer ou écraser ces porte-monnaie. &lt;br&gt; - Transférer tous les fonds vers un nouveau porte-monnaie sauvegardé&lt;/h1&gt;</translation>
    </message>
</context>
<context>
    <name>DlgFragBackup</name>
    <message>
        <location filename="qtdialogs.py" line="10432"/>
        <source>
         &lt;b&gt;&lt;u&gt;Create M-of-N Fragmented Backup&lt;/u&gt; of &quot;%1&quot; (%2)&lt;/b&gt;</source>
        <translation>
&lt;b&gt;&lt;u&gt;Créer une sauvegarde fragmentée M de N&lt;/u&gt; de « %1 » (%2)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10471"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10488"/>
        <source> Use SecurePrintâ¢
         to prevent exposing keys to printer or other devices</source>
        <translation>Utiliser SecurePrint™ pour empêcher de divulguer les clés à l&apos;imprimante ou aux autres périphériques</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10495"/>
        <source>
         SecurePrintâ¢ encrypts your backup with a code displayed on
         the screen, so that no other devices or processes has access to the
         unencrypted private keys (either network devices when printing, or
         other applications if you save a fragment to disk or USB device).
         &lt;u&gt;You must keep the SecurePrintâ¢ code with the backup!&lt;/u&gt;</source>
        <translation>
SecurePrint™ chiffre votre sauvegarde avec un code affiché à l&apos;écran, afin qu&apos;aucun autres périphérique ou processus n&apos;accède aux clés privées non chiffrées (soit les périphériques réseau lors de l&apos;impression, soit les autres applications si vous enregistrez un fragment vers un disque ou un périphérique USB).
&lt;u&gt;Vous devez conserver le code SecurePrint™ avec la sauvegarde !&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10501"/>
        <source>
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;  You must keep the
         SecurePrintâ¢ encryption code with your backup!
         Your SecurePrintâ¢ code is &lt;/font&gt;
         &lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;&lt;font color=&quot;%4&quot;&gt;.
         All fragments for a given wallet use the
         same code.&lt;/font&gt;</source>
        <translation>
&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT :&lt;/u&gt; Vous devez conserver le code de chiffrement SecurePrint™ avec votre sauvegarde !
Votre code SecurePrint™ est &lt;/font&gt;&lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;&lt;font color=&quot;%4&quot;&gt;.
Tous les fragments d&apos;un porte-monnaie donné utilisent le même code.&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10561"/>
        <source>&lt;u&gt;&lt;b&gt;Required Fragments&lt;/b&gt;&lt;/u&gt; </source>
        <translation>&lt;u&gt;&lt;b&gt;Fragments exigés&lt;/b&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10562"/>
        <source>&lt;u&gt;&lt;b&gt;Total Fragments&lt;/b&gt;&lt;/u&gt; </source>
        <translation>&lt;u&gt;&lt;b&gt;Total des fragments&lt;/b&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10566"/>
        <source>Print All Fragments</source>
        <translation>Imprimer tous les fragments</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10593"/>
        <source>
         Any &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; of these
             &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt;
         fragments are sufficient to restore your wallet, and each fragment
         has the ID, &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt;.  All fragments with the
         same fragment ID are compatible with each other!</source>
        <translation>
N&apos;importe quel &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; de ces &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt; suffisent pour restaurer votre porte-monnaie et chaque fragment à son ID, &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt;. Tous les fragments ayant le même ID de fragment sont compatibles les uns les autres.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10608"/>
        <source>&lt;b&gt;Fragment ID:&lt;br&gt;%1-%2&lt;/b&gt;</source>
        <translation>&lt;b&gt;ID de fragment :&lt;br&gt;%1-%2&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10640"/>
        <source>View/Print</source>
        <translation>Visualiser/Imprimer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10641"/>
        <source>Save to File</source>
        <translation>Enregistrer dans un fichier</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10675"/>
        <source>Fragments</source>
        <translation>Fragments</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10685"/>
        <source>Secure Backup?</source>
        <translation>Sécuriser la sauvegarde ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10685"/>
        <source>
            You have selected to use SecurePrintâ¢ for the printed
            backups, which can also be applied to fragments saved to file.
            Doing so will require you store the SecurePrintâ¢
            code with the backup, but it will prevent unencrypted key data from
            touching any disks.  &lt;br&gt;&lt;br&gt; Do you want to encrypt the fragment
            file with the same SecurePrintâ¢ code?</source>
        <translation>
Vous avez choisi d&apos;utiliser SecurePrint™ pour les sauvegardes imprimées, qui peut aussi être appliqué aux fragments enregistrés dans un fichier. Pour ce faire, vous devrez enregistrer le code SecurePrint™ avec la sauvegarde, mais cela empêchera que des données de clé non chiffrées atteignent un disque. &lt;br&gt;&lt;br&gt; Souhaitez-vous chiffrer le fichier fragment avec le même code SecurePrint™ ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10711"/>
        <source>Save Fragment</source>
        <translation>Enregistrer le fragment</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10711"/>
        <source>Wallet Fragments (*.frag)</source>
        <translation>Fragments de porte-monnaie (*.frag)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10746"/>
        <source>
         The fragment was successfully saved to the following location:
         &lt;br&gt;&lt;br&gt; %1 &lt;br&gt;&lt;br&gt; </source>
        <translation>
Le fragment a été enregistré avec succès dans l&apos;emplacement suivant : &lt;br&gt;&lt;br&gt; %1 &lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10751"/>
        <source>
            &lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot;&gt;Important&lt;/font&lt;/u&gt;&lt;/b&gt;:
            The fragment was encrypted with the
            SecurePrintâ¢ encryption code.  You must keep this
            code with the backup in order to use it!  The code &lt;u&gt;is&lt;/u&gt;
            case-sensitive!
            &lt;br&gt;&lt;br&gt; &lt;font color=&quot;%2&quot; size=5&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt;
            &lt;br&gt;&lt;br&gt;
            The above code &lt;u&gt;&lt;b&gt;is&lt;/b&gt;&lt;/u&gt; case-sensitive!</source>
        <translation>
&lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot;&gt;Important&lt;/font&lt;/u&gt;&lt;/b&gt; :
Le fragment a été chiffré avec le code de chiffrement SecurePrint™. Vous devez conserver ce code avec la sauvegarde afin de l&apos;utiliser ! Le code &lt;u&gt;est&lt;/u&gt; sensible à la casse !
&lt;br&gt;&lt;br&gt; &lt;font color=&quot;%2&quot; size=5&gt;&lt;b&gt;%3&lt;/b&gt;&lt;/font&gt;
&lt;br&gt;&lt;br&gt;
Le code ci-dessus &lt;u&gt;&lt;b&gt;est&lt;/b&gt;&lt;/u&gt; sensible à la casse !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10761"/>
        <source>Success</source>
        <translation>Réussite</translation>
    </message>
</context>
<context>
    <name>DlgFundLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1852"/>
        <source>
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network.</source>
        <translation>
Pour dépenser d&apos;un coffre multisignature, un des tiers ou appareils doit créer une proposition de transaction de dépense que tous les autres tiers ou appareils doivent examiner et signer. Après avoir obtenu suffisamment de signatures, n&apos;importe quel appareil peut diffuser la transaction vers le réseau.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1858"/>
        <source>
         I am creating a new proposed spending transaction and will pass
         it to each party or device that needs to sign it.</source>
        <translation>
Je suis en train de créer une nouvelle proposition de transaction de dépense et la transmettrai à chaque tiers ou appareil qui doit la signer.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1862"/>
        <source>
         Another party or device created the transaction, I just need 
         to review and sign it.</source>
        <translation>
Un autre tiers ou appareil a créer la transaction, je dois juste l&apos;examiner et la signer.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1866"/>
        <source>Create Transaction</source>
        <translation>Créer une transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1867"/>
        <source>Review and Sign</source>
        <translation>Examiner et signer</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1868"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
</context>
<context>
    <name>DlgGenericGetPassword</name>
    <message>
        <location filename="qtdialogs.py" line="385"/>
        <source>Password:</source>
        <translation>Mot de passe :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="391"/>
        <source>OK</source>
        <translation>OK</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="392"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="406"/>
        <source>Enter Password</source>
        <translation>Saisir le mot de passe</translation>
    </message>
</context>
<context>
    <name>DlgHelpAbout</name>
    <message>
        <location filename="qtdialogs.py" line="8246"/>
        <source>Armory Bitcoin Wallet : Version %1-beta-%2</source>
        <translation>Porte-monnaie Armory Bitcoin : version %1-bêta-%2</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8249"/>
        <source>Copyright &amp;copy; 2011-2015 Armory Technologies, Inc.</source>
        <translation>Tous droits réservés &amp;copy; 2011-2015 Armory Technologies, Inc.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8250"/>
        <source>Copyright &amp;copy; 2016 Goatpig</source>
        <translation>Tous droits réservés &amp;copy; 2016 Goatpig</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8251"/>
        <source>Licensed to Armory Technologies, Inc. under the &lt;a href=&quot;http://www.gnu.org/licenses/agpl-3.0.html&quot;&gt;Affero General Public License, Version 3&lt;/a&gt; (AGPLv3)</source>
        <translation>Autorisation Armory Technologies, Inc. sous &lt;a href=&quot;https://www.gnu.org/licenses/agpl-3.0.fr.html&quot;&gt;licence publique générale GNU Affero, version 3&lt;/a&gt; (AGPLv3)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8255"/>
        <source>Licensed to Goatpig under the &lt;a href=&quot;https://opensource.org/licenses/mit-license.php&quot;&gt;MIT License</source>
        <translation>Autorisation Goatpig sous &lt;a href=&quot;https://opensource.org/licenses/mit-license.php&quot;&gt;licence MIT</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8273"/>
        <source>About Armory</source>
        <translation>À propos d&apos;Armory</translation>
    </message>
</context>
<context>
    <name>DlgImportAddress</name>
    <message>
        <location filename="qtdialogs.py" line="2429"/>
        <source>Enter:</source>
        <translation>Saisir :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2431"/>
        <source>One Key</source>
        <translation>Une clé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2432"/>
        <source>Multiple Keys</source>
        <translation>Plusieurs clés</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2446"/>
        <source>The key can either be imported into your wallet, 
                     or have its available balance &quot;swept&quot; to another address 
                     in your wallet.  Only import private 
                     key data if you are absolutely sure that no one else 
                     has access to it.  Otherwise, sweep it to get 
                     the funds out of it.  All standard private-key formats 
                     are supported &lt;i&gt;except for private keys created by 
                     Bitcoin Core version 0.6.0 and later (compressed)&lt;/i&gt;.</source>
        <translation>La clé peut être importée dans votre porte-monnaie, ou son solde peut être « balayé » vers une autre adresse de votre porte-monnaie. N&apos;importez les données d&apos;une clé privée que si vous êtes absolument certain que personne d&apos;autre n&apos;y a accès. Autrement, balayez-la pour en extraire les fonds. Tous les formats normaux de clés privées sont pris en charge &lt;i&gt;sauf pour les clés privées créées par Bitcoin Core version 0.6.0 et ultérieure (compressées)&lt;/i&gt;.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2458"/>
        <source>
                       Supported formats are any hexadecimal or Base58 
                       representation of a 32-byte private key (with or 
                       without checksums), and mini-private-key format 
                       used on Casascius physical bitcoins.  Private keys 
                       that use &lt;i&gt;compressed&lt;/i&gt; public keys are not yet 
                       supported by Armory.</source>
        <translation>
Les formats pris en charge sont n&apos;importe quelle représentation hexadécimale ou Base58 d&apos;une clé privée de 32 octets (avec ou sans somme de contrôle) et le format mini-clé-privée utilisé pour les bitcoins physiques Casascius. Les clés privées qui utilisent des clés publiques &lt;i&gt;compressées&lt;/i&gt; ne sont pas encore prises en charge par Armory.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2473"/>
        <source>
                   Enter a list of private keys to be &quot;swept&quot; or imported. 
                   All standard private-key formats are supported.  </source>
        <translation>
Saisir une liste de clés privées à « balayer » ou à importer.
Tous les formats normaux de clés privées sont pris en charge.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2478"/>
        <source>
                  One private key per line, in any standard format. 
                  Data may be copied directly from the &quot;Export Key Lists&quot; 
                  dialog (all text on a line preceding 
                  the key data, separated by a colon, will be ignored).</source>
        <translation>
Une clé privée par ligne, dans n&apos;importe quel format normalisé. Les données peuvent être copiées directement à partir de la boîte de dialogue « Exporter les listes de clés » (tout le texte se trouvant sur la ligne précédente à celle des données de la clé, séparé par deux-points, sera ignoré).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2493"/>
        <source>
         This is from a backup with SecurePrintâ¢</source>
        <translation>
Ceci provient d&apos;une sauvegarde avec SecurePrint™</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2514"/>
        <source>Sweep any funds owned by these addresses 
                                      into your wallet

                                      Select this option if someone else gave you this key</source>
        <translation>Balayer vers votre porte-monnaie les fonds dont ces adresses sont propriétaires

Sélectionnez cette option si quelqu&apos;un d&apos;autre vous a donné cette clé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2517"/>
        <source>Import these addresses to your wallet

                                      Only select this option if you are positive 
                                      that no one else has access to this key</source>
        <translation>Importer ses adresses dans votre porte-monnaie

Ne sélectionnez cette option que si vous êtes absolument sûr que personne d&apos;autre n&apos;a accès à cette clé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2524"/>
        <source>Sweep any funds owned by this address
                                         into your wallet

                                         Select this option if someone else gave you this key</source>
        <translation>Balayer vers votre porte-monnaie les fonds dont cette adresse est propriétaire

Sélectionnez cette option si quelqu&apos;un d&apos;autre vous a donné cette clé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2532"/>
        <source>Sweep any funds owned by this address
                                            into your wallet

                                            (Not available in offline mode)</source>
        <translation>Balayer vers votre porte-monnaie les fonds dont cette adresse est propriétaire

(N&apos;est pas proposé en mode hors ligne)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2536"/>
        <source>
               Sweep any funds owned by this address into your wallet</source>
        <translation>
Balayer vers votre porte-monnaie les fonds dont cette adresse est propriétaire</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2542"/>
        <source>
         You should never add an untrusted key to your wallet.  By choosing this
         option, you are only moving the funds into your wallet, but not the key
         itself.  You should use this option for Casascius physical bitcoins.</source>
        <translation>
Vous ne devriez jamais ajouter à votre porte-monnaie une clé en laquelle vous n&apos;avez pas confiance. En choisissant cette option, vous déplacez seulement les fonds vers votre porte-monnaie, mais pas la clé même. Vous devriez utiliser cette option pour les bitcoins physiques Casascius.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2547"/>
        <source>
         This option will make the key part of your wallet, meaning that it
         can be used to securely receive future payments.  &lt;b&gt;Never&lt;/b&gt; select this
         option for private keys that other people may have access to.</source>
        <translation>
Cette option intégrera la clé à votre porte-monnaie, ce qui signifie qu’elle pourra être utilisée pour recevoir en toute sécurité des paiements futurs. Ne &lt;b&gt;jamais&lt;/b&gt; sélectionner cette option pour les clés privées auxquelles d&apos;autres personnes pourraient avoir accès.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2586"/>
        <source>Private Key Import</source>
        <translation>Importer des clés privées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2643"/>
        <source>Invalid Private Key</source>
        <translation>Clé privée invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2636"/>
        <source>
               You entered all zeros.  This is not a valid private key!</source>
        <translation>
Vous n&apos;avez saisi que des zéros. Ce n&apos;est pas une clé privée valide !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2643"/>
        <source>The private key you have entered is actually not valid for the elliptic curve used by Bitcoin (secp256k1). Almost any 64-character hex is a valid private key &lt;b&gt;except&lt;/b&gt; for those greater than: &lt;br&gt;&lt;br&gt;fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141&lt;br&gt;&lt;br&gt;Please try a different private key.</source>
        <translation>La clé privée que vous avez saisie n&apos;est en fait pas valide pour la courbe elliptique utilisée par Bitcoin (secp256k1). Presque toutes les valeurs hexadécimales de 64 caractères sont des clés privées valides &lt;b&gt;sauf&lt;/b&gt; celles supérieures à : &lt;br&gt;&lt;br&gt;fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141&lt;br&gt;&lt;br&gt;Veuillez essayer une clé privée différente.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2659"/>
        <source>Entry Error</source>
        <translation>Erreur de saisie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2659"/>
        <source>
            The private key data you supplied appears to
            contain a consistency check.  This consistency
            check failed.  Please verify you entered the
            key data correctly.</source>
        <translation>
Les données de la clé privée que vous avez fournies semblent contenir un contrôle de cohérence. Ce contrôle de cohérence a échoué. Veuillez vérifier que vous avez saisi correctement les données de la clé.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2667"/>
        <source>Invalid Data</source>
        <translation>Données invalides</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2667"/>
        <source>Something went terribly
            wrong!  (key data unrecognized)</source>
        <translation>Quelque chose a terriblement mal tourné ! (les données de la clé ne sont pas reconnues)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2672"/>
        <source>Unsupported key type</source>
        <translation>Le type de clé n&apos;est pas pris en charge</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2672"/>
        <source>You entered a key
            for an address that uses a compressed public key, usually produced
            in Bitcoin Core/bitcoind wallets created after version 0.6.0.  Armory
            does not yet support this key type.</source>
        <translation>Vous avez saisi une clé pour une adresse qui utilise une clé publique compressée, habituellement produite dans les porte-monnaie Bitcoin Core/bitcoind créés après la version 0.6.0. Armory ne prend pas encore en charge ce type de clé.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2679"/>
        <source>Error Processing Key</source>
        <translation>Erreur de traitement de la clé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2679"/>
        <source>
            There was an error processing the private key data.
            Please check that you entered it correctly</source>
        <translation>
Une erreur est survenue lors du traitement des données de la clé privée.
Veuillez vous assurer de l&apos;avoir saisie correctement.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2688"/>
        <source>Verify Address</source>
        <translation>Vérifier l&apos;adresse</translation>
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
        <location filename="qtdialogs.py" line="2700"/>
        <source>Try Again</source>
        <translation>Ressayer </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2700"/>
        <source>
                     It is possible that the key was supplied in a
                     &quot;reversed&quot; form.  When the data you provide is
                     reversed, the following address is obtained:

<byte value="x9"/>
                     %1 

Is this the correct address?</source>
        <translation>
Il est possible que la clé ait été fournie sous une forme « inversée ». Quand les données que vous avez fournies sont inversées, on obtient l&apos;adresse suivante :

&lt;byte value=&quot;x9&quot;/&gt; %1

Est-ce la bonne adresse ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2764"/>
        <source>The key you entered is already part of another wallet you own:&lt;br&gt;&lt;br&gt;&lt;b&gt;Address&lt;/b&gt;: </source>
        <translation>La clé que vous avez saisie fait déjà partie d&apos;un autre porte-monnaie dont vous êtes le propriétaire :&lt;br&gt;&lt;br&gt;&lt;b&gt;adresse&lt;/b&gt; :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2862"/>
        <source>Duplicate Addresses!</source>
        <translation>Adresses en double !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2862"/>
        <source>You are attempting to sweep %1 addresses, but %2 of them are already part of existing wallets.  That means that some or all of the bitcoins you sweep may already be owned by you. &lt;br&gt;&lt;br&gt;Would you like to continue anyway?</source>
        <translation>Vous tentez de balayer %1 adresses, mais %2 d&apos;entre elles font déjà partie de porte-monnaie existants. Cela signifie que certains ou tous les bitcoins que vous balayez pourraient déjà être les vôtres.&lt;br&gt;&lt;br&gt;Souhaitez-vous poursuivre quand même ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2910"/>
        <source>Unlock Wallet to Import</source>
        <translation>Déverrouiller le porte-monnaie pour importer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2912"/>
        <source>Wallet is Locked</source>
        <translation>Le porte-monnaie est verrouillé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2912"/>
        <source>
                  Cannot import private keys without unlocking wallet!</source>
        <translation>
Il est impossible d&apos;importer des clés privées sans déverrouiller le porte-monnaie !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2941"/>
        <source>Nothing Imported!</source>
        <translation>Rien n&apos;a été importé !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2941"/>
        <source>All addresses
               chosen to be imported are already part of this wallet.
               Nothing was imported.</source>
        <translation>Toutes les adresses choisies pour être importées font déjà partie de ce porte-monnaie.
Il n&apos;y a rien à importer.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2946"/>
        <source>Error!</source>
        <translation>Erreur !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2946"/>
        <source>
               Failed:  No addresses could be imported.
               Please check the logfile (ArmoryQt.exe.log) or the console output
               for information about why it failed. </source>
        <translation>
Échec : aucune adresse n&apos;a pu être apportée.
Le journal (ArmoryQt.exe.log) ou la console de sortie contiennent des informations sur l&apos;échec. Veuillez les consulter.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2960"/>
        <source>Success!</source>
        <translation>Réussite !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2954"/>
        <source>Success: %1 private keys were imported into your wallet. &lt;br&gt;&lt;br&gt;The other %2 private keys were skipped, because they were already part of your wallet.</source>
        <translation>Réussite : %1 clés privées ont été importées dans votre porte-monnaie.&lt;br&gt;&lt;br&gt;Les %2 autres clés privées ont été ignorées, car elles font déjà partie de votre porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2960"/>
        <source>
                     Success: %1 private keys were imported into your wallet.</source>
        <translation>
Réussite : %1 clés privées ont été importées dans votre porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2963"/>
        <source>Partial Success!</source>
        <translation>Réussite partielle !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2963"/>
        <source>
                  %1 private keys were imported into your wallet, but there were
                  also %2 addresses that could not be imported (see console
                  or log file for more information).  It is safe to try this
                  operation again: all addresses previously imported will be
                  skipped.</source>
        <translation>
%1 clés privées ont été importées dans votre porte-monnaie, mais %2 adresses n&apos;ont pas pu être importées (voir la console ou le journal pour plus d&apos;informations). Cette opération peut être retentée sans danger ; toutes les adresses importées précédemment seront ignorées.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2688"/>
        <source>
               The key data you entered appears to correspond to
               the following Bitcoin address:

<byte value="x9"/> %1
               

Is this the correct address?</source>
        <translation>
Les données de clé que vous avez saisies semblent correspondre à l&apos;adresse Bitcoin suivante :

&lt;byte value=&quot;x9&quot;/&gt; %1

Est-ce la bonne adresse ?</translation>
    </message>
</context>
<context>
    <name>DlgImportAsciiBlock</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2098"/>
        <source>Load from file</source>
        <translation>Charger d&apos;un fichier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2099"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2100"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2121"/>
        <source>Load Data</source>
        <translation>Charger des données</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2137"/>
        <source>Error</source>
        <translation>Erreur</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2137"/>
        <source>
            There was an error reading the ASCII block entered.  Please
            make sure it was entered/copied correctly, and that you have
            copied the header and footer lines that start with &quot;=====&quot;. </source>
        <translation>
Une erreur est survenue lors de la lecture du bloc ASCII saisi. Assurez-vous qu&apos;il a été saisi ou copier correctement et que vous avez aussi copier les lignes d&apos;en-tête et de fin commençant par « ===== ».</translation>
    </message>
</context>
<context>
    <name>DlgImportLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2401"/>
        <source>
         &lt;b&gt;&lt;u&gt;Import Lockbox&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Copy the lockbox text block from file or email into the box 
         below.  If you have a file with the lockbox in it, you can
         load it using the &quot;Load Lockbox&quot; button at the bottom.</source>
        <translation>
&lt;b&gt;&lt;u&gt;Importer un coffre&lt;/u&gt;&lt;/b&gt;
&lt;br&gt;&lt;br&gt;
Le bloc de texte du coffre doit être copié des fichier ou courriel vers la boîte ci-dessous. Si vous avez un fichier qui contient le coffre, vous pouvez le charger en utilisant le bouton « Charger un coffre » situé en bas.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2412"/>
        <source>Load from file</source>
        <translation>Charger d&apos;un fichier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2413"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2414"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2430"/>
        <source>Import Lockbox</source>
        <translation>Importer un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2436"/>
        <source>Load Lockbox</source>
        <translation>Charger un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2453"/>
        <source>Non-lockbox</source>
        <translation>N&apos;est pas un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2453"/>
        <source>
               You are attempting to load something that is not a Lockbox.
               Please clear the display and try again.</source>
        <translation>
Vous essayez de charger quelque chose qui n&apos;est pas un coffre.
Veuillez effacer l&apos;affichage et ressayer.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2459"/>
        <source>Duplicate Lockbox</source>
        <translation>Coffre en double</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2459"/>
        <source>
               You just attempted to import a lockbox with ID, %1.  This
               lockbox is already in your available list of lockboxes.
               &lt;br&gt;&lt;br&gt;
               Even with the same ID, the lockbox information 
               may be different.  Would you like to overwrite the lockbox
               information already stored for %2?</source>
        <translation>
Vous venez de tenter d&apos;importer un coffre portant l&apos;ID %1. Ce coffre fait déjà partie de votre liste de coffres.
&lt;br&gt;&lt;br&gt;
Même avec un ID identique, les informations de coffre peuvent être différentes. Souhaitez-vous écraser les informations de coffre déjà enregistrées pour %2 ?</translation>
    </message>
</context>
<context>
    <name>DlgImportPaperWallet</name>
    <message>
        <location filename="qtdialogs.py" line="3713"/>
        <source>Root Key:</source>
        <translation>Clé racine :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3715"/>
        <source>Chain Code:</source>
        <translation>Code de chaîne :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3718"/>
        <source>
          Enter the characters exactly as they are printed on the
          paper-backup page.  Alternatively, you can scan the QR
          code from another application, then copy&amp;paste into the
          entry boxes below.</source>
        <translation>
Saisissez les caractères exactement comme ils sont imprimés sur la page de la sauvegarde papier. Vous pouvez autrement lire le code QR d&apos;une autre application, puis le copier-coller dans les boîtes d&apos;entrée ci-dessous.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3723"/>
        <source>
          The data can be entered &lt;i&gt;with&lt;/i&gt; or &lt;i&gt;without&lt;/i&gt;
          spaces, and up to
          one character per line will be corrected automatically.</source>
        <translation>
Les données peuvent être saisies &lt;i&gt;avec&lt;/i&gt; ou &lt;i&gt;sans&lt;/i&gt; espace et l&apos;on corrigera automatiquement jusqu&apos;à un caractère par ligne.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3738"/>
        <source>Encrypt Wallet</source>
        <translation>Chiffrer le porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3747"/>
        <source>Recover Wallet from Paper Backup</source>
        <translation>Récupérer un porte-monnaie d&apos;une sauvegarde papier</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3822"/>
        <source>Verify Wallet ID</source>
        <translation>Vérifier l&apos;ID du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3778"/>
        <source>
               There is an error on line %1 of the data you
               entered, which could not be fixed automatically.  Please
               double-check that you entered the text exactly as it appears
               on the wallet-backup page.</source>
        <translation>
Il y a une erreur sur la ligne %1 des données que vous avez saisies, qui n&apos;a pas pu être corrigée automatiquement. Veuillez vérifier que vous avez saisi le texte exactement comme il apparaît sur la page de la sauvegarde papier.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3796"/>
        <source>Errors Corrected!</source>
        <translation>Les erreurs ont été corrigées !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3813"/>
        <source>Duplicate Wallet!</source>
        <translation>Porte-monnaie en double !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3813"/>
        <source>
               The data you entered is for a wallet with a ID: 

 <byte value="x9"/> %1
               

You already own this wallet! 
  
               Nothing to do...</source>
        <translation>
Les données que vous avez saisies sont pour un porte-monnaie dont l&apos;ID est :

&lt;byte value=&quot;x9&quot;/&gt; %1

Vous en êtes déjà le propriétaire !

Il n&apos;y a rien à faire...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3822"/>
        <source>
               The data you entered corresponds to a wallet with a wallet ID: 

 <byte value="x9"/>
               %1 

Does this ID match the &quot;Wallet Unique ID&quot;
               printed on your paper backup?  If not, click &quot;No&quot; and reenter
               key and chain-code data again.</source>
        <translation>
Les données que vous avez saisies correspondent à un porte-monnaie dont l&apos;ID est :

&lt;byte value=&quot;x9&quot;/&gt; %1

Cet ID correspond-il à l&apos;« ID unique du porte-monnaie » imprimé sur votre sauvegarde papier ? Si ce n&apos;est pas le cas, cliquez sur « Non » et saisissez de nouveau la clé et les données code-chaîne.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3837"/>
        <source>Cannot Encrypt</source>
        <translation>Impossible de chiffrer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3837"/>
        <source>
               You requested your restored wallet be encrypted, but no
               valid passphrase was supplied.  Aborting wallet recovery.</source>
        <translation>
Vous avez demandé que votre porte-monnaie restauré soit chiffré, mais aucune phrase de passe valide n&apos;a été fournie. Annulation de la récupération du porte-monnaie.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3855"/>
        <source>PaperBackup - %1</source>
        <translation>Sauvegarde papier - %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3864"/>
        <source>Computing New Addresses</source>
        <translation>Calcul des nouvelle adresses</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3870"/>
        <source>Recovering wallet...</source>
        <translation>Récupération du porte-monnaie...</translation>
    </message>
    <message numerus="yes">
        <location filename="qtdialogs.py" line="3796"/>
        <source>
            Detected %n error(s) on line(s) %1
            in the data you entered.  Armory attempted to fix the
            error(s) but it is not always right.  Be sure
            to verify the &quot;Wallet Unique ID&quot; closely on the next window.</source>
        <translation><numerusform>%n erreur a été détectée sur la ligne %1 des données que vous avez saisies. Armory a essayé de corriger l&apos;erreur, mais n&apos;a pas toujours raison. Assurez-vous de vérifier minutieusement l&apos;« ID unique du porte-monnaie » sur la fenêtre suivante</numerusform><numerusform>%n erreurs ont été détectées sur la ligne %1 des données que vous avez saisies. Armory a essayé de corriger les erreurs, mais n&apos;a pas toujours raison. Assurez-vous de vérifier minutieusement l&apos;« ID unique du porte-monnaie » sur la fenêtre suivante</numerusform></translation>
    </message>
</context>
<context>
    <name>DlgInconsistentWltReport</name>
    <message>
        <location filename="qtdialogs.py" line="420"/>
        <source>Inconsistent Wallet!</source>
        <translation>Le porte-monnaie est incohérent !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="420"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Important:&lt;/u&gt;  Wallet ConsistencyIssues Detected!&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;Armory now detects certain kinds of hardware errors, and oneor more of your walletswas flagged.  The consistency logs need to be analyzed by theArmory team to determine if any further action is required.&lt;br&gt;&lt;br&gt;&lt;b&gt;This warning will pop up every time you start Armory untilthe wallet is fixed&lt;/b&gt;</source>
        <translation>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Important :&lt;/u&gt; Des problèmes de cohérence du porte-monnaie ont été détectés !&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;br&gt;Armory détecte maintenant certains types d&apos;erreurs matérielles et un ou plusieurs de vos porte-monnaie ont été signalés. Les journaux de cohérence doivent être analysés par l&apos;équipe Armory afin de déterminer si des mesures additionnelles sont requises.&lt;br&gt;&lt;br&gt;&lt;b&gt;Cet avertissement apparaîtra chaque fois que vous démarrerez Armory jusqu&apos;à ce que le porte-monnaie soit corrigé&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="448"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot; size=4&gt;Submit Wallet Analysis Logs for
         Review&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;</source>
        <translation>
&lt;b&gt;&lt;u&gt;&lt;font color=&quot;%1&quot; size=4&gt;Envoyer les journaux d&apos;analyse du porte-monnaie pour qu&apos;ils soient examinés&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;</translation>
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
        <location filename="qtdialogs.py" line="467"/>
        <source>Save backup of log files</source>
        <translation>Enregistrer la sauvegarde des fichiers journaux</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="471"/>
        <source>Subject:</source>
        <translation>Objet :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="482"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="506"/>
        <source>Inconsistent Wallet</source>
        <translation>Portefeuille incohérent</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="572"/>
        <source>Not saved</source>
        <translation>N&apos;a pas été enregistré</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="572"/>
        <source>
            You canceled the backup operation.  No backup was made.</source>
        <translation>
Vous avez annulé l&apos;opération de sauvegarde. Aucune sauvegarde n&apos;a été faite.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="579"/>
        <source>Success</source>
        <translation>Réussite</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="579"/>
        <source>The wallet logs were successfully saved to the followinglocation:&lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt;It is still important to complete the rest of this formand submit the data to the Armory team for review!</source>
        <translation>Les journaux du porte-monnaie ont été enregistrés avec succès dans l&apos;emplacement suivant : &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt;Il est quand même important de compléter le reste de ce formulaire et d&apos;envoyer les données à l&apos;équipe Armory pour examen !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="590"/>
        <source>Save Failed</source>
        <translation>Échec d&apos;enregistrement</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="590"/>
        <source>There was an
            error saving a copy of your log files</source>
        <translation>Une erreur est survenue lors de la copie de vos fichiers</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="453"/>
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
        <translation>
Armory a détecté que %1 est incohérent, peut-être en raison d&apos;erreurs matérielles hors de notre contrôle. Il vous est &lt;u&gt;fortement recommandé&lt;/u&gt; d&apos;envoyer les journaux du porte-monnaie aux développeurs d&apos;Armory pour examen. Tant que vous n&apos;aurez pas été contacté par un développeur d&apos;Armory, il vous est recommandé de :
&lt;ul&gt;
&lt;li&gt;&lt;b&gt;Ne supprimer aucune donnée de votre répertoire Armory personnel&lt;/b&gt;&lt;/li&gt;
&lt;li&gt;&lt;b&gt;N&apos;envoyer ni recevoir aucun fonds avec les porte-monnaie affectés&lt;/b&gt;&lt;/li&gt;
&lt;li&gt;&lt;b&gt;Créer une sauvegarde des journaux d&apos;analyse des porte-monnaie&lt;/b&gt;&lt;/li&gt;
&lt;/ul&gt;</translation>
    </message>
</context>
<context>
    <name>DlgInflatedQR</name>
    <message>
        <location filename="qtdefines.py" line="838"/>
        <source>&lt;b&gt;Double-click or press ESC to close&lt;/b&gt;</source>
        <translation>&lt;b&gt;Double-cliquer ou appuyer sur Échap pour fermer&lt;/b&gt;</translation>
    </message>
</context>
<context>
    <name>DlgInstallLinux</name>
    <message>
        <location filename="qtdialogs.py" line="10621"/>
        <source>If you have manually installed Bitcoin Core or bitcoind on this system before, it is recommended you use the method here you previously used.  If you get errors using this option, try using the manual instructions below.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10626"/>
        <source>Install from bitcoin.org PPA (Ubuntu only)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10627"/>
        <source>Download and unpack binaries (All Linux)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10638"/>
        <source>&lt;b&gt;Install PPA for me (Ubuntu only):&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10639"/>
        <source>Have Armory install the PPA for you.  The does not work on all systems, so try the manual instructions below, if it fails.  Using the PPA will install the Bitcoin software using your system&apos;s package manager, and you will be notified of updates along with other software on your system.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10645"/>
        <source>Install Bitcoin PPA</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10647"/>
        <source>Click to install the Bitcoin PPA for Ubuntu</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10654"/>
        <source>&lt;b&gt;Manual PPA Installation:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10655"/>
        <source>Open a terminal window and copy the following three commands one-by-one, pressing [ENTER] after each one.  You can open a terminal by hitting Alt-F2 and typing &quot;terminal&quot; (without quotes), or in the &quot;Applications&quot; menu under &quot;Accessories&quot;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10686"/>
        <source>&lt;b&gt;Download and set it up for me!  (All Linux):&lt;/b&gt;&lt;br&gt;&lt;br&gt;Armory will download and verify the binaries from https://bitcoin.org.  Your Armory settings will automatically be adjusted to point to that as the installation directory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10692"/>
        <source>Install for me!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10694"/>
        <source>Select custom download location</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgIntroMessage</name>
    <message>
        <location filename="qtdialogs.py" line="3600"/>
        <source>&lt;b&gt;Welcome to Armory!&lt;/b&gt;</source>
        <translation>&lt;b&gt;Bienvenue à Armory !&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3603"/>
        <source>&lt;i&gt;The most advanced Bitcoin Client on Earth!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Le client Bitcoin le plus perfectionné sur terre !&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3606"/>
        <source>&lt;b&gt;You are about to use the most secure and feature-rich Bitcoin clientsoftware available!&lt;/b&gt;  But please remember, this softwareis still &lt;i&gt;Beta&lt;/i&gt; - Armory developers will not be held responsiblefor loss of bitcoins resulting from the use of this software!&lt;br&gt;&lt;br&gt;</source>
        <translation>&lt;b&gt;Vous êtes sur le point d&apos;utiliser le logiciel client Bitcoin le plus sûr et le plus riche en fonctions qu&apos;il soit !&lt;/b&gt; Mais gardez à l&apos;esprit que ce logiciel est encore en &lt;i&gt;bêta&lt;/i&gt; - Les développeurs d&apos;Armory ne pourront être tenus responsables d&apos;aucune perte de bitcoins résultant de l&apos;utilisation de ce logiciel !&lt;br&gt;&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3621"/>
        <source>Do not show this window again</source>
        <translation>Ne plus afficher cette fenêtre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3629"/>
        <source>Create Your First Wallet!</source>
        <translation>Créez votre premier porte-monnaie !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3630"/>
        <source>Import Existing Wallet</source>
        <translation>Importer un porte-monnaie existant</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3631"/>
        <source>Skip</source>
        <translation>Ignorer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3645"/>
        <source>OK!</source>
        <translation>OK !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3660"/>
        <source>Greetings!</source>
        <translation>Bonjour !</translation>
    </message>
</context>
<context>
    <name>DlgKeypoolSettings</name>
    <message>
        <location filename="qtdialogs.py" line="2100"/>
        <source>Armory pre-computes a pool of addresses beyond the last address you have used, and keeps them in your wallet to &quot;look-ahead.&quot;  One reason it does this is in case you have restored this wallet from a backup, and Armory does not know how many addresses you have actually used. &lt;br&gt;&lt;br&gt;If this wallet was restored from a backup and was very active after it was backed up, then it is possible Armory did not pre-compute enough addresses to find your entire balance.  &lt;b&gt;This condition is rare&lt;/b&gt;, but it can happen.  You may extend the keypool manually, below.</source>
        <translation>Armory précalcule une réserve d&apos;adresses au-delà de la dernière adresse que vous avez utilisée et les conserve dans votre portefeuille pour « anticiper ». Une des raisons est qu&apos;en cas de restauration de ce porte-monnaie d&apos;une sauvegarde, Armory ne sait pas combien d&apos;adresses vous avez en fait utilisées.&lt;br&gt;&lt;br&gt;Si ce porte-monnaie a été restauré d&apos;une sauvegarde, devenant très actif par la suite, il est alors possible qu&apos;Armory n&apos;ait pas précalculé suffisamment d&apos;adresses pour découvrir votre solde entier. &lt;b&gt;Bien que cette situation soit rare&lt;/b&gt;, cela peut arriver. Vous pouvez étendre la réserve de clés manuellement ci-dessous.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2113"/>
        <source>Addresses used: </source>
        <translation>Adresses utilisées :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2114"/>
        <source>Addresses computed: </source>
        <translation>Adresses calculées :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2118"/>
        <source>Compute this many more addresses: </source>
        <translation>Calculer ce nombre d&apos;adresses en plus :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2123"/>
        <source>Address computation is very slow.  It may take up to one minute to compute 200-1000 addresses (system-dependent).  Only generate as many as you think you need.</source>
        <translation>Le calcul d&apos;adresses est très lent. Le calcul de 200 à 1 000 adresses peut prendre jusqu&apos;à une minute (en fonction du système). N&apos;en générez que le nombre nécessaire.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2130"/>
        <source>Compute</source>
        <translation>Calculer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2131"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2155"/>
        <source>Extend Address Pool</source>
        <translation>Étendre la réserve d&apos;adresses</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2174"/>
        <source>Invalid input</source>
        <translation>Entrée invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2174"/>
        <source>
            The value you entered is invalid.  Please enter a positive 
            number of addresses to generate.</source>
        <translation>
La valeur que vous avez saisie est invalide. Veuillez saisir un nombre positif d&apos;adresses à générer.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2180"/>
        <source>Are you sure?</source>
        <translation>Êtes-vous certain ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2180"/>
        <source>You have entered that you want to compute %1 more addressesfor this wallet.  This operation will take a very long time, and Armory will become unresponsive until the computation is finished.  Armory estimates it will take about %2 minutes.&lt;br&gt;&lt;br&gt;Do you want to continue?</source>
        <translation>Vous avez saisi que vous voulez calculer %1 adresses supplémentaires pour ce porte-monnaie. Cette opération prendra beaucoup de temps et Armory cessera de répondre tant que le calcul ne sera pas terminé. Armory estime que cela prendra environ %2 minutes.&lt;br&gt;&lt;br&gt;Souhaitez-vous poursuivre ?</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2192"/>
        <source>&lt;font color=&quot;%1&quot;&gt;Calculating...&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;%1&quot;&gt;Calcul...&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2197"/>
        <source>Computing New Addresses</source>
        <translation>Calcul des nouvelle adresses</translation>
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
&lt;b&gt;&lt;u&gt;&lt;font size=5 color=&quot;%1&quot;&gt;Créer un coffre multisignature&lt;/font&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="39"/>
        <source>
         Create a &quot;lockbox&quot; to hold coins that have signing authority split 
         between multiple devices for personal funds, or split between 
         multiple parties for escrow.</source>
        <translation>
Créer un « coffre » pour contenir les pièces dont l&apos;autorité de signature est partagée entre plusieurs appareils pour les fonds personnels, ou partagés entre plusieurs tiers pour les entiercements.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="44"/>
        <source>
         &lt;b&gt;&lt;u&gt;NOTE:&lt;/u&gt; Multi-sig &quot;lockboxes&quot; require &lt;u&gt;public keys&lt;/u&gt;, not 
         the address strings most Bitcoin users are familiar with.&lt;/b&gt;
         &lt;a href=&quot;None&quot;&gt;Click for more info&lt;/a&gt;.</source>
        <translation>
&lt;b&gt;&lt;u&gt;NOTE :&lt;/u&gt;Les coffres multisignature exigent des &lt;u&gt;clés publiques&lt;/u&gt; et non les chaînes d&apos;adresse avec lesquelles la plupart des utilisateurs sont familiers.&lt;/b&gt;
&lt;a href=&quot;None&quot;&gt;Cliquer ici pour pour plus d&apos;infos&lt;/a&gt;.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="50"/>
        <source>Public Key Information</source>
        <translation>Informations sur la clé publique</translation>
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
        <translation>
Une clé publique est beaucoup plus longue qu&apos;une chaîne d&apos;adresse et commence toujours par « 02 », « 03 » ou « 04 ». La plupart des applications de porte-monnaie ne fournissent pas de moyen simple d&apos;accéder à la clé publique associée à une adresse donnée. Cela est grandement facilité si tous utilisent Armory.
&lt;br&gt;&lt;br&gt;
Les boutons de carnet d&apos;adresses situés à côté de chaque boîte d&apos;entrée ci-dessous vous montreront les chaînes d&apos;adresses normales, mais saisiront la bonne clé publique de l&apos;adresse que vous sélectionnez.
&lt;br&gt;&lt;br&gt;
Si vous créez ce coffre avec d&apos;autres utilisateurs d&apos;Armory, ils peuvent utiliser le bouton « Sélectionner la clé publique » dans le tableau de bord du gestionnaire de coffres afin de choisir une clé et saisir leurs coordonnées. Vous pouvez utiliser le bouton « Importer » sur chaque ligne de clé publique pour importer les données qu&apos;ils vous ont envoyées.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="112"/>
        <source>
            Public Key #&lt;font size=4 color=&quot;%1&quot;&gt;%2&lt;/font&gt;:</source>
        <translation>
Clé publique no &lt;font size=4 color=&quot;%1&quot;&gt;%2&lt;/font&gt; :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="114"/>
        <source>Name or ID:</source>
        <translation>Nom ou ID :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="125"/>
        <source>Edit</source>
        <translation>Modifier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="126"/>
        <source>Import</source>
        <translation>Importer</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="164"/>
        <source>Exit</source>
        <translation>Quitter</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="165"/>
        <source>Save Lockbox</source>
        <translation>Enregistrer le coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="177"/>
        <source>Set extended info</source>
        <translation>Définir les infos étendues</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="236"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Create
         Multi-Sig Lockbox&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Créer un coffre multisignature&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="240"/>
        <source>&lt;b&gt;Required Signatures (M)&lt;/b&gt; </source>
        <translation>&lt;b&gt;Signatures exigées (M)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="242"/>
        <source>&lt;b&gt;Total Signers (N)&lt;/b&gt; </source>
        <translation>&lt;b&gt;Total des signataires (N)&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="245"/>
        <source> - OF - </source>
        <translation> - DE - </translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="248"/>
        <source>Clear All</source>
        <translation>Tout effacer</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="305"/>
        <source>Import Public Key Block</source>
        <translation>Importer le bloc d&apos;une clé publique</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="306"/>
        <source>
         &lt;center&gt;&lt;b&gt;&lt;u&gt;Import Public Key Block&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
         &lt;br&gt;
         Copy and paste a PUBLICKEY block into the text field below, 
         or load it from file.  PUBLICKEY files usually have the 
         extension &lt;i&gt;*.lockbox.pub&lt;/i&gt;.  If you were given a chunk of hex
         characters starting with &quot;02&quot;, &quot;03&quot; or &quot;04&quot;, that is a raw public 
         key and can be entered directly into the public key field in the
         lockbox creation window.</source>
        <translation>
&lt;center&gt;&lt;b&gt;&lt;u&gt;Importer le bloc d&apos;une clé publique&lt;/u&gt;&lt;/b&gt;&lt;/center&gt;
&lt;br&gt;
Copiez et collez le bloc d&apos;une clé publique dans la zone de texte ci-dessous, ou chargez-le d&apos;un fichier. Les fichiers de clé publique portent habituellement l&apos;extension &lt;i&gt;*.lockbox.pub&lt;/i&gt;. Si l&apos;on vous a remis un fragment de caractères hexadécimaux commençant par « 02 », « 03 » ou « 04 », c&apos;est une clé publique brute qui peut être saisie directement dans le champ de clé publique de la fenêtre de création de coffres.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="295"/>
        <source>Add public key ID or contact info</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="297"/>
        <source>Change public key ID or contact info</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgLockboxManager</name>
    <message>
        <location filename="MultiSigDialogs.py" line="654"/>
        <source>&lt;br&gt;Double-click on a lockbox to edit</source>
        <translation>&lt;br&gt;Double-cliquer sur un coffre pour le modifier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="656"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Manage Multi-Sig Lockboxes&lt;/b&gt;&lt;/font&gt;
         %2</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Gérer des coffres multisignatures&lt;/b&gt;&lt;/font&gt;
%2</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="701"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="767"/>
        <source>Dashboard</source>
        <translation>Tableau de bord</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="768"/>
        <source>Info</source>
        <translation>Infos</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="769"/>
        <source>Transactions</source>
        <translation>Transactions</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="822"/>
        <source>Create Lockbox</source>
        <translation>Créer un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="825"/>
        <source>Collect public keys</source>
        <translation>Recueillir des clés publiques</translation>
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
        <location filename="MultiSigDialogs.py" line="837"/>
        <source>Select Public Key</source>
        <translation>Sélectionner la clé publique</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="840"/>
        <source>Send to organizer</source>
        <translation>Envoyer à l&apos;organisateur</translation>
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
        <location filename="MultiSigDialogs.py" line="851"/>
        <source>Export Lockbox</source>
        <translation>Exporter le coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="854"/>
        <source>Send to other devices or parties</source>
        <translation>Envoyer aux autres appareils ou tiers</translation>
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
        <location filename="MultiSigDialogs.py" line="861"/>
        <source>Select lockbox to export</source>
        <translation>Sélectionner un coffre à exporter</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="865"/>
        <source>Import Lockbox</source>
        <translation>Importer un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="868"/>
        <source>From organizer or other device</source>
        <translation>D&apos;un organisateur ou d&apos;un autre appareil</translation>
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
        <location filename="MultiSigDialogs.py" line="880"/>
        <source>Edit Lockbox</source>
        <translation>Modifier un coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="884"/>
        <source>Edit an existing lockbox</source>
        <translation>Modifier un coffre existant</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="885"/>
        <source>Select lockbox to edit</source>
        <translation>Sélectionner le coffre à modifier</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="912"/>
        <source>Merge Promissory Notes</source>
        <translation>Fusionner des billets à ordre</translation>
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
        <location filename="MultiSigDialogs.py" line="924"/>
        <source>Create Promissory Note</source>
        <translation>Créer un billet à ordre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="927"/>
        <source>Make a funding commitment to a lockbox</source>
        <translation>S&apos;engager dans le financement d&apos;un coffre</translation>
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
        <location filename="MultiSigDialogs.py" line="936"/>
        <source>Select lockbox to commit funds to</source>
        <translation>Sélectionner un coffre vers lequel engager des fonds</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="937"/>
        <source>Must be online to create</source>
        <translation>Il faut être en ligne pour créer</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="940"/>
        <source>Review and Sign</source>
        <translation>Examiner et signer</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="943"/>
        <source>Multi-sig spend or simulfunding</source>
        <translation>Dépense ou financement simultané multisignature</translation>
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
        <location filename="MultiSigDialogs.py" line="954"/>
        <source>Create Spending Tx</source>
        <translation>Créer une transaction de dépense</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="957"/>
        <source>Send bitcoins from lockbox</source>
        <translation>Envoyer des bitcoins d&apos;un coffre</translation>
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
        <location filename="MultiSigDialogs.py" line="963"/>
        <source>Select lockbox to spend from</source>
        <translation>Sélectionner le coffre source de la dépense</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="964"/>
        <source>Must be online to spend</source>
        <translation>Il faut être en ligne pour dépenser</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="968"/>
        <source>Collect Sigs &amp;&amp; Broadcast</source>
        <translation>Recueillir les signatures et diffuser</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="971"/>
        <source>Merge signatures to finalize</source>
        <translation>Fusionner les signatures pour finaliser</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="972"/>
        <source>Merge signatures and broadcast transaction</source>
        <translation>Fusionner les signatures et diffuser la transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="974"/>
        <source>(must be online to broadcast)</source>
        <translation>(il faut être en ligne pour diffuser)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="982"/>
        <source>SimulFund</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="988"/>
        <source>
         If this lockbox will be funded by multiple parties and not all
         parties are fully trusted, use &quot;simulfunding&quot; to ensure that funds 
         are committed at the same time.  Check the &quot;Simul&quot; box to show 
         simulfunding options in the table.</source>
        <translation>
Si ce coffre est financé par plusieurs tiers dont certains ne sont pas entièrement fiables, utilisez le financement simultané pour garantir que les fonds sont engagés en même temps. Cochez la boîte « Simulfund » pour afficher les options de financement simultané dans le tableau.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1135"/>
        <source>Fund from Wallet</source>
        <translation>Financer d&apos;un porte-monnaie</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1136"/>
        <source>QR Code</source>
        <translation>Code QR</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1137"/>
        <source>Request Payment</source>
        <translation>Demander un paiement</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1174"/>
        <source>Copy Address</source>
        <translation>Copier l&apos;adresse</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1189"/>
        <source>
               Anyone can send funds to this lockbox using this
               Bitcoin address: &lt;br&gt;&lt;b&gt;%1&lt;/b&gt;</source>
        <translation>
N&apos;importe qui peut envoyer des fonds vers ce coffre en utilisant l&apos;adresse Bitcoin : &lt;br&gt;&lt;b&gt;%1&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1327"/>
        <source>Invalid Tx</source>
        <translation>Transaction invalide</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1327"/>
        <source>The transaction you requested be displayed does not exist in Armory&apos;s database.  This is unusual...</source>
        <translation>La transaction dont vous avez demandé l&apos;affichage n&apos;existe pas dans la base de données Armory. Cela est inhabituel...</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1358"/>
        <source>View on blockexplorer.com</source>
        <translation>Visualiser sur blockexplorer.com</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1361"/>
        <source>View on blockchain.info</source>
        <translation>Visualiser sur blockchain.info</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1365"/>
        <source>View Details</source>
        <translation>Visualiser les détails</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1367"/>
        <source>Change Comment</source>
        <translation>Modifier le commentaire</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1368"/>
        <source>Copy Transaction ID</source>
        <translation>Copier l&apos;ID de transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1440"/>
        <source>Could not open browser</source>
        <translation>Impossible d&apos;ouvrir le navigateur</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1379"/>
        <source>Armory encountered an error opening your web browser.  To view this transaction on blockchain.info, please copy and paste the following URL into your browser: &lt;br&gt;&lt;br&gt;%1</source>
        <translation>Une erreur est survenue lors de l&apos;ouverture de votre navigateur Web par Armory. Pour visualiser cette transaction sur blockchain.info, veuillez copier-coller l&apos;URL suivante dans votre navigateur : &lt;br&gt;&lt;br&gt;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1401"/>
        <source>Copy P2SH address</source>
        <translation>Copier l&apos;adresse P2SH</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1402"/>
        <source>Display address QR code</source>
        <translation>Afficher le code QR de l&apos;adresse</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1404"/>
        <source>View address on %1</source>
        <translation>Visualiser l&apos;adresse sur %1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1407"/>
        <source>Request payment to this lockbox</source>
        <translation>Demander un paiement vers ce coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1408"/>
        <source>Copy hash160 value (hex)</source>
        <translation>Copier la valeur hash160 (hexadécimal)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1409"/>
        <source>Copy balance</source>
        <translation>Copier le solde</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1410"/>
        <source>Delete Lockbox</source>
        <translation>Supprimer le coffre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1407"/>
        <source>Rescan Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1440"/>
        <source>
                  Armory encountered an error opening your web browser.  To view 
                  this address on %1, please copy and paste
                  the following URL into your browser: 
                  &lt;br&gt;&lt;br&gt;
                  &lt;a href=&quot;%2&quot;&gt;%3&lt;/a&gt;</source>
        <translation>
Une erreur est survenue lors de l&apos;ouverture de votre navigateur Web par Armory. Pour visualiser cette transaction sur %1, veuillez copier-coller l&apos;URL suivante dans votre navigateur : &lt;br&gt;&lt;br&gt;
&lt;a href=&quot;%2&quot;&gt;%3&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1455"/>
        <source>Compatibility Warning</source>
        <translation>Avertissement de compatibilité</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1455"/>
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
        <translation>Vous êtes sur le point de demander un paiement vers une adresse P2SH qui est le format utilisé pour recevoir vers des adresses ou coffres multisignatures. Les adresses P2SH sont semblables aux adresses Bitcoin ordinaires, mais commencent par %1 au lieu de %2.
&lt;br&gt;&lt;br&gt;
Malheureusement, tous les logiciels et services ne prennent pas en charge l&apos;envoi vers des adresses P2SH. Si l&apos;expéditeur ou le service indique une erreur d&apos;envoi vers cette adresse, vous aurez à demander un paiement vers une adresse de porte-monnaie ordinaire et envoyer ensuite les fonds de ce porte-monnaie vers le coffre une fois que le paiement aura été confirmé.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1455"/>
        <source>Do not show this message again</source>
        <translation>Ne plus afficher ce message</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1718"/>
        <source>Confirm Delete</source>
        <translation>Confirmer la suppression</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1479"/>
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
        <translation>
Supprimer un coffre ne supprime aucune clé de signature et vous conservez donc l&apos;autorité de signature pour les pièces qui en proviennent. Cependant, cela le supprimera de la liste des coffres et vous devrez le réimporter ultérieurement afin d&apos;envoyer des fonds à partir ou vers le coffre.
&lt;br&gt;&lt;br&gt;
Vous êtes sur le point de supprimer le coffre suivant :
&lt;br&gt;&lt;br&gt;
&lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1494"/>
        <source>Confirm Rescan</source>
        <translation type="unfinished"/>
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
        <location filename="MultiSigDialogs.py" line="1539"/>
        <source> &lt;br&gt;&lt;br&gt;&lt;font color=&quot;%1&quot;&gt;&lt;center&gt;&lt;b&gt;
            Select a lockbox from the table above to view its info&lt;/b&gt;&lt;/center&gt;
            &lt;/font&gt;</source>
        <translation> &lt;br&gt;&lt;br&gt;&lt;font color=&quot;%1&quot;&gt;&lt;center&gt;&lt;b&gt;Sélectionner un coffre dans le tableau ci-dessus pour en visualiser les informations&lt;/b&gt;&lt;/center&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1594"/>
        <source>&lt;font color=&quot;%1&quot; size=4&gt;&lt;center&gt;&lt;u&gt;Lockbox Information for
         &lt;b&gt;%2&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;%1&quot; size=4&gt;&lt;center&gt;&lt;u&gt;Informations sur le coffre de &lt;b&gt;%2&lt;/b&gt;&lt;/u&gt;&lt;/center&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1596"/>
        <source>&lt;b&gt;Multisig:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1-of-%2</source>
        <translation>&lt;b&gt;Multisignatures :&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1-de-%2</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1597"/>
        <source>&lt;b&gt;Lockbox ID:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&lt;b&gt;ID du coffre :&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1598"/>
        <source>&lt;b&gt;P2SH Address:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&lt;b&gt;Adresse P2SH :&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1599"/>
        <source>&lt;b&gt;Lockbox Name:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&lt;b&gt;Nom du coffre :&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1600"/>
        <source>&lt;b&gt;Created:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&lt;b&gt;Créé le :&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1601"/>
        <source>&lt;b&gt;Extended Info:&lt;/b&gt;&lt;hr&gt;&lt;blockquote&gt;%1&lt;/blockquote&gt;&lt;hr&gt;</source>
        <translation>&lt;b&gt;Infos étendues :&lt;/b&gt;&lt;hr&gt;&lt;blockquote&gt;%1&lt;/blockquote&gt;&lt;hr&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1602"/>
        <source>&lt;b&gt;Stored Key Details&lt;/b&gt;</source>
        <translation>&lt;b&gt;Détails de clé enregistrés&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1612"/>
        <source>&amp;nbsp;&amp;nbsp;&lt;b&gt;Key #%1&lt;/b&gt;</source>
        <translation>&amp;nbsp;&amp;nbsp;&lt;b&gt;Clé no %1&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1613"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Name/ID:&lt;/b&gt;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Nom/ID :&lt;/b&gt;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1614"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Address:&lt;/b&gt;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Adresse :&lt;/b&gt;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1615"/>
        <source>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;PubKey:&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</source>
        <translation>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;Clé publique :&lt;/b&gt;&amp;nbsp;&amp;nbsp;%1</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1617"/>
        <source>&lt;/font&gt;</source>
        <translation>&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1786"/>
        <source>Import Signature Collector</source>
        <translation>Importer le collecteur de signatures</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1697"/>
        <source>
         Import a &lt;i&gt;Signature Collector&lt;/i&gt; block to review and
         sign the lockbox-spend or simulfunding transaction.  This text block 
         is produced by the organizer and will contain
         &quot;=====TXSIGCOLLECT&quot; on the first line.   Or you can import it from
         a file, which is saved by default with a
         &lt;i&gt;*.sigcollect.tx&lt;/i&gt; extension.</source>
        <translation>
Importer un bloc de texte &lt;i&gt;Collecteur de signatures&lt;/i&gt; pour examiner et signer la transaction de dépense d&apos;un coffre ou de financement simultané. Ce bloc de texte est produit par l&apos;organisateur et contiendra « =====TXSIGCOLLECT » sur la première ligne. Vous pouvez aussi importer d&apos;un fichier qui est enregistré par défaut avec l&apos;extension &lt;i&gt;*.sigcollect.tx&lt;/i&gt;.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1718"/>
        <source>
         &quot;Removing&quot; a lockbox does not delete any signing keys, so you 
         maintain signing authority for any coins that are sent there.     
         However, Armory will stop tracking its history and balance, and you
         will have to re-import it later in order to sign any transactions.
         &lt;br&gt;&lt;br&gt;
         You are about to remove the following lockbox:
         &lt;br&gt;&lt;br&gt;
         &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt; </source>
        <translation>
Supprimer un coffre ne supprime aucune clé de signature et vous conservez donc l&apos;autorité de signature pour les pièces qui en proviennent. Cependant, Armory arrêtera de suivre son historique ainsi que son solde et vous devrez le réimporter ultérieurement afin de signer des transactions.
&lt;br&gt;&lt;br&gt;
Vous êtes sur le point de supprimer le coffre suivant :
&lt;br&gt;&lt;br&gt;
&lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt;
</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1741"/>
        <source>[WARNING]</source>
        <translation>[AVERTISSEMENT]</translation>
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
        <location filename="MultiSigDialogs.py" line="1766"/>
        <source>Funding %1-of-%2</source>
        <translation>Approvisionnement %1-de-%2</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1787"/>
        <source>
            Import a &lt;i&gt;Signature Collector&lt;/i&gt; text block to review and
            sign the simulfunding transaction.  This text block is produced
            by the party that collected and merged all the promissory notes.
            Files containing signature-collecting data usually end with
            &lt;i&gt;*.sigcollect.tx&lt;/i&gt;.</source>
        <translation>
Importer un bloc de texte &lt;i&gt;Collecteur de signatures&lt;/i&gt; pour examiner et signer la transaction de financement simultané. Ce bloc de texte est produit par le tiers qui a recueilli et fusionné tous les billets à ordre. Les fichiers contenant des données de collection de signatures se terminent habituellement par &lt;i&gt;*.sigcollect.tx&lt;/i&gt;.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="826"/>
        <source>Create a lockbox by collecting public keys from each device or person that will be a signing authority over the funds.  Once created you will be given a chunk of text to send to each party so they can recognize and sign transactions related to the lockbox.</source>
        <translation>Créer un coffre en recueillant les clés publiques de chaque appareil ou personne qui sera une autorité de signature pour ces fonds. Une fois que le coffre sera créé, vous obtiendrez un fragment de texte à envoyer   à chaque tiers afin qu&apos;il puisse reconnaître et signer les transactions liées à ce coffre.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="841"/>
        <source>In order to create a lockbox all devices and/or parties need to provide a public key that they control to be merged by the organizer.  Once all keys are collected, the organizer will send you the final lockbox definition to import.</source>
        <translation>Afin de créer un coffre, chaque appareil ou tiers doit fournir une clé publique qu&apos;il contrôle afin qu&apos;elle soit fusionnée par l&apos;organisateur. Une fois que toutes les clés seront recueillies, l&apos;organisateur vous enverra la définition du coffre final pour que vous l&apos;importiez.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="855"/>
        <source>Export a lockbox definition to be imported by other devices or parties.  Normally the lockbox organizer will do this after all public keys are collected, but any participant who already has it can send it, such as if one party/device accidentally deletes it.</source>
        <translation>Exporter une définition de coffre devant être importée par les autres appareils ou tiers. Habituellement, l&apos;organisateur du coffre le fera une fois que toutes les clés publiques auront été recueillies, mais tout participant la possédant déjà peut l&apos;envoyer, par exemple si un appareil ou tiers la supprime par accident.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="869"/>
        <source>Import a lockbox definition to begin tracking its funds and to be able to sign related transactions. Normally, the organizer will send you the data to import after you provide a public key from one of your wallets.</source>
        <translation>Importer une définition de coffre pour commencer à suivre ses fonds et afin de signer les transactions qui y sont reliées. Normalement, l&apos;organisateur vous enverra les données à importer après que vous lui aurez fourni une clé publique d&apos;un de vos porte-monnaie.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="916"/>
        <source>Collect promissory notes from all funders of a simulfunding transaction.  Use this to merge them into a single transaction that the funders can review and sign.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="944"/>
        <source>Review and sign any lockbox-related transaction that requires multiple signatures.  This includes spending transactions from a regular lockbox, as well as completing a simulfunding transaction.</source>
        <translation>Examiner et signer des transactions reliées à un coffre et qui exigent plusieurs signatures. Cela inclut les transactions de dépense d&apos;un coffre ordinaire, ainsi que la réalisation d&apos;une transaction simultanée.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="958"/>
        <source>Create a proposed transaction sending bitcoins to an address, wallet or another lockbox. The transaction will not be final until enough signatures have been collected and then broadcast from an online computer.</source>
        <translation>Créer une proposition de transaction qui envoie des bitcoins à une adresse, un porte-monnaie ou un autre coffre. Suffisamment de signatures devront être recueillies puis diffusées d&apos;un ordinateur en ligne afin de finaliser la transaction.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1741"/>
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
         select the &quot;SimulFund&quot; checkbox on the lockbox dashboard.
         </source>
        <translation>
&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Avertissement :&lt;/font&gt; &lt;/b&gt;
Si ce coffre est utilisé pour conserver un entiercement pour plusieurs tiers et doit être approvisionné par plusieurs participants, vous &lt;u&gt;devez&lt;/u&gt; utiliser un processus particulier d&apos;approvisionnement pour garantir le financement simultané. Autrement, l&apos;un des tiers pourrait vous escroquer !
&lt;br&gt;&lt;br&gt;
Vous pouvez continuer en toute sécurité si l&apos;une des conditions suivantes s&apos;applique :
&lt;ul&gt;
&lt;li&gt;Il est entendu que vous êtes le seul à approvisionner ce coffre ou entiercement&lt;/li&gt;
&lt;li&gt;Tous les tiers de ce coffre ou entiercement sont entièrement fiables&lt;/li&gt;
&lt;li&gt;Ce coffre est utilisé pour des épargnes personnelles&lt;/li&gt;
&lt;/ul&gt;

Si les conditions ci-dessus ne s&apos;appliquent pas à vous, veuillez appuyer sur « Annuler » ou sélectionner la case à cocher « SimulFund » sur le tableau de bord du coffre.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1292"/>
        <source>Add Transaction Comment</source>
        <translation>Ajouter un commentaire de transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1294"/>
        <source>Change Transaction Comment</source>
        <translation>Modifier le commentaire de transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="928"/>
        <source>A &quot;promissory note&quot; provides blockchain information about how your wallet will contribute funds to a simulfunding transaction. A promissory note does &lt;b&gt;not&lt;/b&gt; move any money in your wallet.  The organizer will create a single transaction that includes all promissory notes and you will be able to  review it in its entirety before signing.</source>
        <translation>Un billet à ordre fournit des informations de la chaîne de blocs sur la manière dans votre porte-monnaie engagera des fonds dans une transaction simultanée. Un billet à ordre &lt;b&gt;ne déplace pas&lt;/b&gt; d&apos;argent vers votre porte-monnaie. L&apos;organisateur créera une seule transaction qui inclura tous les billets à ordre et vous pourrez l&apos;examiner complètement avant de la signer.</translation>
    </message>
</context>
<context>
    <name>DlgMergePromNotes</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3509"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Merge Promissory Notes
         &lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Fusionner les billets à ordre&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3514"/>
        <source>
         Collect promissory notes from two or more parties
         to combine them into a single &lt;i&gt;simulfunding&lt;/i&gt; transaction.  Once
         all notes are collected you will be able to
         send it to each contributing party for review and signing.</source>
        <translation>
Recueillez les billets à ordre de deux tiers ou plus pour les combiner en une seule transaction de &lt;i&gt;financement simultanée&lt;/i&gt;. Une fois que tous les billets à ordre seront recueillis, vous pourrez envoyer la transaction à chacun des tiers pour révision et signature.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3527"/>
        <source>Lockbox Being Funded</source>
        <translation>Le coffre est en cours d&apos;approvisionnement</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3530"/>
        <source>Address Being Funded</source>
        <translation>L&apos;adresse est en cours d&apos;approvisionnement</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3567"/>
        <source>Loaded Promissory Notes</source>
        <translation>Les billets à ordre sont chargés</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3568"/>
        <source>
         &lt;font size=4&gt;&lt;b&gt;No Promissory Notes Have Been Added&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font size=4&gt;&lt;b&gt;Aucun billet à ordre n&apos;a été ajouté&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3642"/>
        <source>Import Promissory Note</source>
        <translation>Importer un billet à ordre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3591"/>
        <source>Create &amp;&amp; Add Promissory Note</source>
        <translation>Créer et ajouter un billet à ordre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3596"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3597"/>
        <source>Use bare multisig (no P2SH)</source>
        <translation>Utiliser des multisignatures nues (pas de P2SH)</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3598"/>
        <source>
         EXPERT OPTION:  Do not check this box unless you know what it means
                         and you need it!  Forces Armory to exposes public 
                         keys to the blockchain before the funds are spent.  
                         This is only needed for very specific use cases, 
                         and otherwise creates blockchain bloat.</source>
        <translation>
OPTION EXPERT : ne cochez cette case que si vous savez ce qu&apos;elle signifie et que vous en avez besoin ! Elle force Armory à exposer les clés publiques à la chaîne de blocs avant que les fonds ne soient dépensés. Elle n&apos;est nécessaire que pour certains cas d&apos;usage très précis et autrement encombre la chaîne de blocs.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3604"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3643"/>
        <source>
         Import a promissory note to add to this simulfunding transaction</source>
        <translation>
Importer un billet à ordre pour l&apos;ajouter à cette transaction de financement simultané</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3655"/>
        <source>Invalid Promissory Note</source>
        <translation>Le billet à ordre est invalide</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3655"/>
        <source>
            No promissory note was loaded.</source>
        <translation>
Aucun billet à ordre n&apos;a été chargé.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3666"/>
        <source>Not Online</source>
        <translation>N&apos;est pas en ligne</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3666"/>
        <source>
            Armory is currently in offline mode and cannot create any 
            transactions or promissory notes.  You can only merge 
            pre-existing promissory notes at this time.</source>
        <translation>
Armory est actuellement hors ligne et ne peut pas créer de transactions ou de billets à ordre. Vous pouvez seulement pour l&apos;instant fusionner des billets à ordre préexistants.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3694"/>
        <source>Already Loaded</source>
        <translation>Déjà chargé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3694"/>
        <source> This 
            promissory note has already been loaded!</source>
        <translation>Ce billet à ordre a déjà été chargé !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3733"/>
        <source>Mismatched Funding Target</source>
        <translation>La cible d&apos;approvisionnement ne correspond pas</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3733"/>
        <source>
            The promissory note you loaded is for a different funding target. 
            Please make sure that all promissory notes are for the target
            specified on the previous window</source>
        <translation>
Le billet à ordre que vous avez chargé est pour une cible d&apos;approvisionnement différente. Veuillez vous assurer que tous les billets à ordre correspondent aux cibles indiquées dans la fenêtre précédente</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3775"/>
        <source>Nothing Loaded</source>
        <translation>Rien n&apos;a été chargé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3775"/>
        <source>
            No promissory notes were loaded.  Cannot create simulfunding 
            transaction.</source>
        <translation>
Aucun billet à ordre n&apos;a été chargé. Il est impossible de créer une transaction de financement simultanée.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3781"/>
        <source>Merging One Note</source>
        <translation>Fusion d&apos;un billet à ordre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3781"/>
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
        <translation>
Un seul billet à ordre a été entré et il n&apos;y a donc à rien à fusionner.
&lt;br&gt;&lt;br&gt;
L&apos;interface de financement simultané est destinée à fusionner des billets à ordre provenant de plusieurs tiers afin de garantir le financement simultané d&apos;un entiercement. Si une seule personne assure le financement, elle peut simplement envoyer l&apos;argent à l&apos;adresse ou au coffre comme elle le ferait pour toute autre transaction sans passer par l&apos;interface de financement simultané.
&lt;br&gt;&lt;br&gt;
Cliquez sur OK pour accéder à l&apos;interface multisignatures, mais il n&apos;y aura qu&apos;une entrée à signer.</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3827"/>
        <source>Export Simulfunding Transaction</source>
        <translation>Exporter une transaction de financement simultané</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3828"/>
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
        <translation>
Le bloc de texte ci-dessous contient la transaction de financement simultané devant être signée par tous les tiers approvisionnant ce coffre. Copiez le bloc de texte dans un courriel à envoyer aux tiers participant au financement. Chaque tiers peut réviser la transaction finale de financement simultané, ajouter sa signature et vous la renvoyer pour la finaliser.
&lt;br&gt;&lt;br&gt;
Après avoir cliqué sur Terminé, on vous présentera une fenêtre que vous pourrez utiliser pour fusionner les blocs TXSIGCOLLECT des autres tiers et diffuser la transaction finale.</translation>
    </message>
</context>
<context>
    <name>DlgMultiSpendReview</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2487"/>
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
        <translation>
La transaction suivante est une dépense proposée de fonds contrôlés par plusieurs tiers. Les couleurs à côté de chaque entrée représentent les signatures exigées pour que la transaction soit valide. Blanc signifie qu&apos;elle n&apos;a pas encore été signée et ne peut pas être signée par vous. Vert représente des signatures qui peuvent être ajoutées par l&apos;un de vos porte-monnaie. Gris signifie qu&apos;il y a déjà une signature.
&lt;br&gt;&lt;br&gt;
Les sorties de monnaie on était masquées quand elles sont évidentes (p. ex. des pièces retournant dans le coffre dont elles proviennent). S&apos;il y a ambiguïté, Armory affichera toutes les sorties.</translation>
    </message>
</context>
<context>
    <name>DlgNewAddressDisp</name>
    <message>
        <location filename="qtdialogs.py" line="2251"/>
        <source>The following address can be used to receive bitcoins:</source>
        <translation>L&apos;adresse suivante peut être utilisée pour recevoir des bitcoins :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2256"/>
        <source>Copy to Clipboard</source>
        <translation>Copier dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2258"/>
        <source> or </source>
        <translation>ou</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2269"/>
        <source>Create Clickable Link</source>
        <translation>Créer un lien cliquable</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2273"/>
        <source>
            You can securely use this address as many times as you want. 
            However, all people to whom you give this address will 
            be able to see the number and amount of bitcoins &lt;b&gt;ever&lt;/b&gt; 
            sent to it.  Therefore, using a new address for each transaction 
            improves overall privacy, but there is no security issues 
            with reusing any address.</source>
        <translation>
Vous pouvez utiliser cette adresse en toute sécurité autant de fois que vous le souhaitez. Cependant, toutes les personnes à qui vous donnerez cette adresse pourront voir tous les montants en bitcoins qui lui ont été envoyés. Par conséquent, l&apos;utilisation d&apos;une nouvelle adresse pour chaque transaction améliore la confidentialité générale, mais la réutilisation d&apos;une adresse ne pose aucun problème lié à la sécurité. </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2310"/>
        <source>(Optional) Add a label to this address, which will be shown with any relevant transactions in the &quot;Transactions&quot; tab.</source>
        <translation>(Facultatif) Ajouter une étiquette à cette adresse, qui sera affichée avec les transactions pertinentes dans l&apos;onglet « Transactions ».</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2327"/>
        <source>Bitcoins sent to this address will 
            appear in the wallet:</source>
        <translation>Les bitcoins envoyés à cette adresse apparaîtront dans le porte-monnaie :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2341"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2353"/>
        <source>&lt;b&gt;Scan QR code with phone or other barcode reader&lt;/b&gt;&lt;br&gt;&lt;br&gt;&lt;font size=2&gt;(Double-click to expand)&lt;/font&gt;</source>
        <translation>&lt;b&gt;Lire le code QR avec votre téléphone ou un autre lecteur de code à barres&lt;/b&gt;&lt;br&gt;&lt;br&gt;&lt;font size=2&gt;(Double-cliquer pour développer)&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2390"/>
        <source>New Receiving Address</source>
        <translation>Nouvelle adresse de réception</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2418"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation>&lt;i&gt;Copiée !&lt;/i&gt;</translation>
    </message>
</context>
<context>
    <name>DlgNewWallet</name>
    <message>
        <location filename="qtdialogs.py" line="606"/>
        <source>
         Create a new wallet for managing your funds.&lt;br&gt;
         The name and description can be changed at any time.</source>
        <translation>
Créer un nouveau porte-monnaie pour gérer vos fonds.&lt;br&gt;Le nom et la description peuvent être modifiés en tout temps.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="630"/>
        <source>
                  Armory will test your system's speed to determine the most 
                  challenging encryption settings that can be performed '
                  in a given amount of time.  High settings make it much harder 
                  for someone to guess your passphrase.  This is used for all 
                  encrypted wallets, but the default parameters can be changed below.
</source>
        <translation>
Armory testera la vitesse de votre système afin de déterminer les paramètres de chiffrement les plus exigeants qui peuvent être effectués dans un temps donné. Des paramètres élevés entravent encore plus la tâche de quelqu&apos;un qui tenterait de deviner votre phrase de passe. Ils peuvent être utilisés pour tous les porte-monnaie chiffrés, mais les paramètres par défaut peuvent être changés ci-dessous.
</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="638"/>
        <source>
                  This is the amount of time it will take for your computer 
                  to unlock your wallet after you enter your passphrase. 
                  (the actual time used will be less than the specified 
                  time, but more than one half of it).  </source>
        <translation>
C&apos;est le temps que prendra votre ordinateur pour déverrouiller votre portefeuille après saisie de votre phrase de passe. (La durée effective sera inférieure à la durée spécifiée, mais plus de la moitié de celle-ci.)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="650"/>
        <source>
                  This is the &lt;b&gt;maximum&lt;/b&gt; memory that will be 
                  used as part of the encryption process.  The actual value used 
                  may be lower, depending on your system's speed.  If a 
                  low value is chosen, Armory will compensate by chaining 
                  together more calculations to meet the target time.  High 
                  memory target will make GPU-acceleration useless for 
                  guessing your passphrase.</source>
        <translation>
C&apos;est la quantité &lt;b&gt;maximale&lt;/b&gt; de mémoire qui sera utilisée par le processus de chiffrement. La valeur utilisée pourrait en fait être plus faible selon la vitesse de votre système. Si une valeur faible est choisie, Armory compensera en enchaînant plus de calculs afin d&apos;atteindre le délai prévu. Une valeur de mémoire élevée rendra l&apos;accélération par l&apos;unité de traitement graphique inutile pour deviner votre phrase de passe.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="665"/>
        <source>Max &amp;memory usage (kB, MB):</source>
        <translation>Utilisation maximale de la &amp;mémoire (Ko, Mo) :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="688"/>
        <source>Use wallet &amp;encryption</source>
        <translation>Utiliser le &amp;chiffrement du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="690"/>
        <source>
                  Encryption prevents anyone who accesses your computer 
                  or wallet file from being able to spend your money, as  
                  long as they do not have the passphrase.
                  You can choose to encrypt your wallet at a later time 
                  through the wallet properties dialog by double clicking 
                  the wallet on the dashboard.</source>
        <translation>
Le chiffrement empêche quiconque accède à votre ordinateur ou fichier de porte-monnaie de dépenser votre argent, tant que cette personne n&apos;a pas votre phrase de passe. Vous pourrez choisir de chiffrer votre porte-monnaie ultérieurement grâce à la boîte de dialogue des propriétés du porte-monnaie en double-cliquant sur le porte-monnaie dans le tableau de bord.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="699"/>
        <source>Print a paper-backup of this wallet</source>
        <translation>Imprimer une sauvegarde papier de ce porte-monnaie</translation>
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
        <location filename="qtdialogs.py" line="712"/>
        <source>Accept</source>
        <translation>Accepter</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="713"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1134"/>
        <source>Adv. Encrypt Options&gt;&gt;&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="729"/>
        <source>Import wallet...</source>
        <translation>Importer le porte-monnaie...</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="757"/>
        <source>Create Armory wallet</source>
        <translation>Créer un porte-monnaie Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="772"/>
        <source>Invalid wallet name</source>
        <translation>Le nom du porte-monnaie est invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="772"/>
        <source>You must enter a name for this wallet, up to 32 characters.</source>
        <translation>Vous devez saisir un nom pour ce porte-monnaie, jusqu&apos;à 32 caractères.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="778"/>
        <source>Input too long</source>
        <translation>L&apos;entrée est trop longue</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="778"/>
        <source>
                  The wallet description is limited to 256 characters.  Only the first 
                  256 characters will be used.</source>
        <translation>
La description du porte-monnaie est limitée à 256 caractères. Seuls les 256 premiers caractères seront utilisés.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="808"/>
        <source>Invalid KDF Parameters</source>
        <translation>Les paramètres KDF sont invalides</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="796"/>
        <source>
               Please specify a compute time no more than 20 seconds.  
               Values above one second are usually unnecessary.</source>
        <translation>
Veuillez indiquer un temps de calcul inférieur ou égal à 20 secondes. Les valeurs supérieures à 1 seconde sont habituellement inutiles.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="808"/>
        <source>Please specify a maximum memory usage between 32 kB 
               and 2048 MB.</source>
        <translation>Veuillez indiquer une utilisation maximale de la mémoire entre 32 Ko et 2048 Mo.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="815"/>
        <source>Invalid Input</source>
        <translation>L&apos;entrée est invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="815"/>
        <source>
            Please specify time with units, such as 
            &quot;250 ms&quot; or &quot;2.1 s&quot;.  Specify memory as kB or MB, such as 
            &quot;32 MB&quot; or &quot;256 kB&quot;. </source>
        <translation>
Veuillez indiquer le temps avec des unités, p.ex. « 250 ms » ou « 2.1 s ». Pour la mémoire en Ko ou Mo, p.ex. « 32 Mo » ou « 256 Ko ».</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="826"/>
        <source>Import Wallet File</source>
        <translation>Importer un fichier de porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="826"/>
        <source>Wallet files (*.wallet);; All files (*)</source>
        <translation>Fichiers de porte-monnaie (*.wallet) ; tous les fichiers (*)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="701"/>
        <source>
                  A paper-backup allows you to recover your wallet/funds even 
                  if you lose your original wallet file, any time in the future. 
                  Because Armory uses &quot;deterministic wallets,&quot; 
                  a single backup when the wallet is first made is sufficient 
                  for all future transactions (except ones to imported 
                  addresses).


                  Anyone who gets hold of your paper backup will be able to spend 
                  the money in your wallet, so please secure it appropriately.</source>
        <translation>
Une sauvegarde papier vous permet de récupérer vos porte-monnaie ou fonds même si vous perdez votre fichier original de porte-monnaie, à tout moment dans le futur.
Dans la mesure où Armory utilise des « porte-monnaie déterministes », une seule sauvegarde effectuée lors de la création du porte-monnaie suffit pour toutes les transactions à venir (sauf celles vers des adresses importées).

Quiconque prendra possession de votre sauvegarde papier pourra dépenser l&apos;argent dans votre porte-monnaie. Veuillez la sécuriser de manière appropriée.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="714"/>
        <source>Advanced Encryption Options&gt;&gt;&gt;</source>
        <translation>Options avancées de chiffrement &gt;&gt;&gt;</translation>
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
        <location filename="qtdialogs.py" line="4707"/>
        <source>Create New Offline Transaction</source>
        <translation>Créer une nouvelle transaction hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4708"/>
        <source>Sign and/or Broadcast Transaction</source>
        <translation>Signer ou diffuser une transaction</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4712"/>
        <source>No wallets available!</source>
        <translation>Aucun porte-monnaie n&apos;est disponible !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4715"/>
        <source>Sign Offline Transaction</source>
        <translation>Signer une transaction hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4718"/>
        <source>No watching-only wallets available!</source>
        <translation>Aucun porte-monnaie juste-regarder n&apos;est disponible ! </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4723"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation>&lt;&lt;&lt; Retour</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4734"/>
        <source>
         Create a transaction from an Offline/Watching-Only wallet
         to be signed by the computer with the full wallet </source>
        <translation>
Créer une transaction d&apos;un porte-monnaie hors ligne ou juste-regarder, devant être signée par l&apos;ordinateur abritant le porte-monnaie complet</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4738"/>
        <source>
         Review an unsigned transaction and sign it if you have
         the private keys needed for it </source>
        <translation>
Réviser une transaction non signée et la signer si vous détenez les clés privées nécessaires pour le faire</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4742"/>
        <source>
         Send a pre-signed transaction to the Bitcoin network to finalize it</source>
        <translation>
Envoyer une transaction préalablement signée vers le réseau Bitcoin pour la finaliser</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4691"/>
        <source>In order to execute an offline transaction, three steps must be followed: &lt;br&gt;&lt;br&gt;<byte value="x9"/>(1) &lt;u&gt;On&lt;/u&gt;line Computer:  Create the unsigned transaction&lt;br&gt; <byte value="x9"/>(2) &lt;u&gt;Off&lt;/u&gt;line Computer: Get the transaction signed&lt;br&gt; <byte value="x9"/>(3) &lt;u&gt;On&lt;/u&gt;line Computer:  Broadcast the signed transaction&lt;br&gt;&lt;br&gt; You must create the transaction using a watch-only wallet on an online system, but watch-only wallets cannot sign it.  Only the offline system can create a valid signature.  The easiest way to execute all three steps is to use a USB key to move the data between computers.&lt;br&gt;&lt;br&gt; All the data saved to the removable medium during all three steps are completely safe and do not reveal any private information that would benefit an attacker trying to steal your funds.  However, this transaction data does reveal some addresses in your wallet, and may represent a breach of &lt;i&gt;privacy&lt;/i&gt; if not protected.</source>
        <translation>Afin d&apos;effectuer une transaction hors ligne, il faut suivre trois étapes :&lt;br&gt;&lt;br&gt;&lt;byte value=&quot;x9&quot;/&gt;(1) Ordinateur &lt;u&gt;en ligne&lt;/u&gt; : créer la transaction non signée&lt;br&gt;&lt;byte value=&quot;x9&quot;/&gt;(2) Ordinateur &lt;u&gt;hors ligne&lt;/u&gt; : faire signer la transaction&lt;br&gt;&lt;byte value=&quot;x9&quot;/&gt;(3) Ordinateur &lt;u&gt;en ligne&lt;/u&gt; : diffuser la transaction signée&lt;br&gt;&lt;br&gt;Vous devez créer la transaction en utilisant un porte-monnaie juste-regarder sur un système en ligne, mais les porte-monnaie juste-regarder ne peuvent pas la signer. Seul le système hors ligne peut créer une signature valide. La façon la plus facile d&apos;exécuter les trois étapes est d&apos;utiliser une clé USB pour déplacer les données entre les ordinateurs.&lt;br&gt;&lt;br&gt;Toutes les données enregistrées sur le support amovible au cours des trois étapes sont complètement en sécurité et ne révèlent aucun renseignement personnel qu&apos;un attaquant essayant de voler vos fonds pourrait utiliser. Cependant, ces données transactionnelles révèlent certaines adresses dans votre porte-monnaie et pourraient représenter une atteinte à la &lt;i&gt;confidentialité&lt;/i&gt; des renseignements personnels si elles ne sont pas protégées.</translation>
    </message>
</context>
<context>
    <name>DlgOfflineTxCreated</name>
    <message>
        <location filename="qtdialogs.py" line="4672"/>
        <source>Review Offline Transaction</source>
        <translation>Examiner la transaction hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4648"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4650"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5073"/>
        <source>
         By clicking Done you will exit end the offline transaction process for now.
         When you are ready to sign and/or broadcast the transaction, click the Offline
         Transactions button in the main window, then click the Sign and/or
         Broadcast Transaction button in the Select Offline Action dialog.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4659"/>
        <source>
         By clicking Continue you will continue to the next step in the offline
         transaction process to sign and/or broadcast the transaction.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4653"/>
        <source>
         By clicking Done you will exit the offline transaction process for now.
         When you are ready to sign and/or broadcast the transaction, click the Offline
         Transactions button in the main window, then click the Sign and/or
         Broadcast Transaction button in the Select Offline Action dialog.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgPasswd3</name>
    <message>
        <location filename="qtdialogs.py" line="967"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! DO NOT FORGET YOUR PASSPHRASE !!!&lt;/b&gt;&lt;/font&gt;</source>
        <translation>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! N&apos;OUBLIEZ PAS VOTRE PHRASE DE PASSE !!!&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1390"/>
        <source>&lt;b&gt;No one can help you recover you bitcoins if you forget the passphrase and don&apos;t have a paper backup!&lt;/b&gt; Your wallet and any &lt;u&gt;digital&lt;/u&gt; backups are useless if you forget it.  &lt;br&gt;&lt;br&gt;A &lt;u&gt;paper&lt;/u&gt; backup protects your wallet forever, against hard-drive loss and losing your passphrase.  It also protects you from theft, if the wallet was encrypted and the paper backup was not stolen with it.  Please make a paper backup and keep it in a safe place.&lt;br&gt;&lt;br&gt;Please enter your passphrase a third time to indicate that you are aware of the risks of losing your passphrase!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="990"/>
        <source>Accept</source>
        <translation>Accepter</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="991"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1003"/>
        <source>WARNING!</source>
        <translation>AVERTISSEMENT !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="970"/>
        <source>&lt;b&gt;No one can help you recover you bitcoins if you forget the passphrase and don&apos;t have a paper backup!&lt;/b&gt; Your wallet and any &lt;u&gt;digital&lt;/u&gt; backups are useless if you forget it.  &lt;br&gt;&lt;br&gt;A &lt;u&gt;paper&lt;/u&gt; backup protects your wallet forever, against hard-drive loss and losing your passphrase.  It also protects you from theft, if the wallet was encrypted and the paper backup was not stolen with it.  Please make a paper backup and keep it in a safe place.&lt;br&gt;&lt;br&gt;&lt;b&gt;Please enter your passphrase a third time to indicate that you are aware of the risks of losing your passphrase!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgPrintBackup</name>
    <message>
        <location filename="qtdialogs.py" line="6397"/>
        <source>Error Creating Backup</source>
        <translation>Erreur de création de la sauvegarde</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6397"/>
        <source>
            There was an error with the backup creator.  The operation is being
            canceled to avoid making bad backups!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6478"/>
        <source>Print imported keys</source>
        <translation>Imprimer les clés importées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6481"/>
        <source>Page:</source>
        <translation>Page :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6494"/>
        <source>
         Use SecurePrintâ¢ to prevent exposing keys to printer or other
         network devices</source>
        <translation>Utiliser SecurePrint™ pour empêcher de divulguer les clés à l&apos;imprimante ou aux autres périphériques réseau</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6501"/>
        <source>
         SecurePrintâ¢ encrypts your backup with a code displayed on
         the screen, so that no other devices on your network see the sensitive
         data when you send it to the printer.  If you turn on
         SecurePrintâ¢ &lt;u&gt;you must write the code on the page after
         it is done printing!&lt;/u&gt;  There is no point in using this feature if
         you copy the data by hand.</source>
        <translation>
SecurePrint™ chiffre votre sauvegarde avec un code affiché à l&apos;écran, afin qu&apos;aucun autre périphérique de votre réseau ne voie l&apos;information délicate quand vous l&apos;envoyez vers l&apos;imprimante. Si vous activez SecurePrint™, &lt;u&gt;vous devez prendre le code en note sur la page après l’impression !&lt;/u&gt; Il est inutile d&apos;utiliser cette fonction si vous copiez les données manuellement.</translation>
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
        <location filename="qtdialogs.py" line="6527"/>
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
        <location filename="qtdialogs.py" line="6538"/>
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
        <location filename="qtdialogs.py" line="6621"/>
        <source>Lots to Print!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6621"/>
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
        <location filename="qtdialogs.py" line="6655"/>
        <source>of %1</source>
        <translation>de %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6698"/>
        <source>SecurePrint Code</source>
        <translation>Code SecurePrint™</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6698"/>
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
        <location filename="qtdialogs.py" line="6766"/>
        <source>Single-Sheet </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6768"/>
        <source>Imported Keys </source>
        <translation>Clés importées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6770"/>
        <source>Fragmented Backup (%1-of-%2)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6787"/>
        <source>&lt;b&gt;%1-&lt;font color=&quot;%2&quot;&gt;#%2&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6799"/>
        <source>
            Any subset of &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; fragments with this
            ID (&lt;font color=&quot;%3&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt;) are sufficient to recover all the
            coins contained in this wallet.  To optimize the physical security of
            your wallet, please store the fragments in different locations.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6807"/>
        <source>
            &lt;font color=&quot;#aa0000&quot;&gt;&lt;b&gt;WARNING:&lt;/b&gt;&lt;/font&gt; Anyone who has access to this
            page has access to all the bitcoins in %1!  Please keep this
            page in a safe place.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6825"/>
        <source>
            The following %1 lines backup all addresses
            &lt;i&gt;ever generated&lt;/i&gt; by this wallet (previous and future).
            This can be used to recover your wallet if you forget your passphrase or
            suffer hardware failure and lose your wallet files. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6832"/>
        <source>
               The following is a list of all private keys imported into your
               wallet before this backup was made.   These keys are encrypted
               with the SecurePrintâ¢ code and can only be restored
               by entering them into Armory.  Print a copy of this backup without
               the SecurePrintâ¢ option if you want to be able to import
               them into another application.</source>
        <translation>
La liste suivante répertorie toutes les clés privées importées vers votre porte-monnaie avant que cette sauvegarde n&apos;ait été effectuée. Les clés sont chiffrées avec le code SecurePrint™ et ne peuvent être restaurées quand les saisissants dans Armory. Imprimez une copie de sauvegarde sans l&apos;option SecurePrint™ si vous souhaitez être en mesure de les importer dans une autre application.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6840"/>
        <source>
               The following is a list of all private keys imported into your
               wallet before this backup was made.  Each one must be copied
               manually into the application where you wish to import them.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6846"/>
        <source>
            The following is fragment &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;#%2&lt;/b&gt;&lt;/font&gt; for this
            wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6869"/>
        <source>
            &lt;b&gt;&lt;font color=&quot;#770000&quot;&gt;CRITICAL:&lt;/font&gt;  This backup will not
            work without the SecurePrintâ¢
            code displayed on the screen during printing.
            Copy it here in ink:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6976"/>
        <source>
         The following QR code is for convenience only.  It contains the
         exact same data as the %1 lines above.  If you copy this backup
         by hand, you can safely ignore this QR code. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="6509"/>
        <source>
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt;&lt;/b&gt;  You must write the SecurePrintâ¢
         encryption code on each printed backup page!  Your SecurePrintâ¢ code is &lt;/font&gt;
         &lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;.  &lt;font color=&quot;%4&quot;&gt;Your backup will not work
         if this code is lost!&lt;/font&gt; </source>
        <translation>
&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;&lt;u&gt;IMPORTANT :&lt;/u&gt; Vous devez écrire le code de chiffrement SecurePrint™ sur chaque page de la sauvegarde imprimée !
Votre code SecurePrint™ est &lt;/font&gt;&lt;font color=&quot;%2&quot;&gt;%3&lt;/font&gt;. &lt;font color=&quot;%4&quot;&gt;Votre sauvegarde ne fonctionnera pas si le code est perdu !&lt;/font&gt;</translation>
    </message>
</context>
<context>
    <name>DlgProgress</name>
    <message>
        <location filename="qtdialogs.py" line="12899"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12930"/>
        <source>Enter Passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13020"/>
        <source>%1: %2%%</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13049"/>
        <source>Progress Bar</source>
        <translation>Barre de progression</translation>
    </message>
</context>
<context>
    <name>DlgRegAndTest</name>
    <message>
        <location filename="qtdialogs.py" line="13790"/>
        <source>Error: You cannot run the Regression Test network and Bitcoin Test Network at the same time.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRemoveAddress</name>
    <message>
        <location filename="qtdialogs.py" line="4208"/>
        <source>&lt;b&gt;!!! WARNING !!!&lt;/b&gt;

</source>
        <translation>&lt;b&gt;!!! AVERTISSEMENT !!!&lt;/b&gt;

</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4212"/>
        <source>&lt;i&gt;You have requested that the following address
                            be deleted from your wallet:&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4220"/>
        <source>Address:</source>
        <translation>Adresse :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4223"/>
        <source>Comment:</source>
        <translation>Commentaire :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4227"/>
        <source>In Wallet:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4234"/>
        <source>Address Balance (w/ unconfirmed):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4271"/>
        <source>Do you want to delete this address?  No other addresses in this
            wallet will be affected.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4285"/>
        <source>Confirm Delete Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4289"/>
        <source>One more time...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4289"/>
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
        <location filename="qtdialogs.py" line="3924"/>
        <source>&lt;b&gt;!!! WARNING !!!&lt;/b&gt;

</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3928"/>
        <source>&lt;i&gt;You have requested that the following wallet
                            be removed from Armory:&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3936"/>
        <source>Wallet Unique ID:</source>
        <translation>ID unique du porte-monnaie :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3939"/>
        <source>Wallet Name:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3942"/>
        <source>Description:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3957"/>
        <source>Current Balance (w/ unconfirmed):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3996"/>
        <source>&lt;b&gt;WALLET IS NOT EMPTY.  Only delete this wallet if you
                             have a backup on paper or saved to a another location
                             outside your settings directory.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4001"/>
        <source>&lt;b&gt;WALLET IS PART OF A LOCKBOX.  Only delete this wallet if you
                             have a backup on paper or saved to a another location
                             outside your settings directory.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4009"/>
        <source>Permanently delete this wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4010"/>
        <source>Delete private keys only, make watching-only</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4019"/>
        <source>
         This will delete the wallet file, removing
         all its private keys from your settings directory.
         If you intend to keep using addresses from this
         wallet, do not select this option unless the wallet
         is backed up elsewhere.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4025"/>
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
        <location filename="qtdialogs.py" line="4035"/>
        <source>
         Print a paper backup of this wallet before deleting</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4039"/>
        <source>
            This will delete the wallet file from your system.
            Since this is a watching-only wallet, no private keys
            will be deleted.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4043"/>
        <source>
            This wallet is already a watching-only wallet so this option
            is pointless</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4082"/>
        <source>
         If this box is checked, you will have the ability to print off an
         unencrypted version of your wallet before it is deleted.  &lt;b&gt;If
         printing is unsuccessful, please press *CANCEL* on the print dialog
         to prevent the delete operation from continuing&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4100"/>
        <source>Delete</source>
        <translation>Supprimer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4101"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4110"/>
        <source>Delete Wallet Options</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4118"/>
        <source>Unlock Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4120"/>
        <source>Operation Aborted</source>
        <translation>L&apos;opération a été interrompue</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4120"/>
        <source>
              You requested a paper backup before deleting the wallet, but
              clicked &quot;Cancel&quot; on the backup printing window.  So, the delete
              operation was canceled as well.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4133"/>
        <source>Confirm Delete</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4133"/>
        <source>You are about to delete a watching-only wallet.  Are you sure
         you want to do this?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4143"/>
        <source>Are you absolutely sure?!?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4137"/>
        <source>Are you absolutely sure you want to permanently delete
         this wallet?  Unless this wallet is saved on another device
         you will permanently lose access to all the addresses in this
         wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4143"/>
        <source>&lt;i&gt;This will permanently delete the information you need to spend
         funds from this wallet!&lt;/i&gt;  You will only be able to receive
         coins, but not spend them.  Only do this if you have another copy
         of this wallet elsewhere, such as a paper backup or on an offline
         computer with the full wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4169"/>
        <source>Wallet %1 was replaced with a watching-only wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4176"/>
        <source>Wallet %1 was deleted!</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgReplaceWallet</name>
    <message>
        <location filename="qtdialogs.py" line="12549"/>
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
        <location filename="qtdialogs.py" line="12564"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12565"/>
        <source>Overwrite</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12566"/>
        <source>Merge</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12614"/>
        <source>Ripping Meta Data</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRequestPayment</name>
    <message>
        <location filename="qtdialogs.py" line="9749"/>
        <source>Other Options &gt;&gt;&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9435"/>
        <source>Copy to Clipboard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9436"/>
        <source>Copy Raw HTML</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9437"/>
        <source>Copy Raw URL</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9438"/>
        <source>Copy All Text</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9461"/>
        <source>Create a clickable link that you can copy into email or webpage to request a payment.   If the user is running a Bitcoin program that supports &quot;bitcoin:&quot; links, that program will open with all this information pre-filled after they click the link.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9471"/>
        <source>The following Bitcoin desktop applications &lt;i&gt;try&lt;/i&gt; to register themselves with your computer to handle &quot;bitcoin:&quot; links: Armory, Multibit, Electrum</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9475"/>
        <source>This is the text to be shown as the clickable link.  It should usually begin with &quot;Click here...&quot; to reaffirm to the user it is is clickable.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9479"/>
        <source>All amounts are specifed in BTC</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9481"/>
        <source>The person clicking the link will be sending bitcoins to this address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9483"/>
        <source>This will be pre-filled as the label/comment field after the user clicks the link. They can modify it if desired, but you can provide useful info such as contact details, order number, etc, as convenience to them.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9491"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9499"/>
        <source>&lt;b&gt;Link Text:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9504"/>
        <source>&lt;b&gt;Address (yours):&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9509"/>
        <source>&lt;b&gt;Request (BTC):&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9513"/>
        <source>&lt;b&gt;Label:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Étiquette :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9519"/>
        <source>Copy and paste the following text into email or other document:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9528"/>
        <source>Creating QR Code Please Wait</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9532"/>
        <source>This QR code contains address &lt;b&gt;and&lt;/b&gt; the other payment information shown to the left.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9566"/>
        <source>Create Payment Request Link</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9624"/>
        <source>Amount</source>
        <translation>Montant</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9634"/>
        <source>Message</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9639"/>
        <source>Address</source>
        <translation>Adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9644"/>
        <source>Inputs</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9648"/>
        <source>&lt;font color=&quot;red&quot;&gt;Invalid %1&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9664"/>
        <source>If clicking on the line above does not work, use this payment info:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9666"/>
        <source>&lt;b&gt;Pay to&lt;/b&gt;:<byte value="x9"/>%1&lt;br&gt;</source>
        <translation>&lt;b&gt;Payer à&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9668"/>
        <source>&lt;b&gt;Amount&lt;/b&gt;:<byte value="x9"/>%1 BTC&lt;br&gt;</source>
        <translation>&lt;b&gt;Montant&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1 BTC&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9670"/>
        <source>&lt;b&gt;Message&lt;/b&gt;:<byte value="x9"/>%1&lt;br&gt;</source>
        <translation>&lt;b&gt;Message&lt;/b&gt; :&lt;byte value=&quot;x9&quot;/&gt;%1&lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9680"/>
        <source>If clicking on the line above does not work, use this payment info:
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9681"/>
        <source>Pay to:  %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9683"/>
        <source>
Amount:  %1 BTC</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9685"/>
        <source>
Message: %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9689"/>
        <source>&lt;!DOCTYPE HTML PUBLIC &quot;-//W3C//DTD HTML 4.0//EN&quot; &quot;http://www.w3.org/TR/REC-html40/strict.dtd&quot;&gt; &lt;html&gt;&lt;head&gt;&lt;meta name=&quot;qrichtext&quot; content=&quot;1&quot; /&gt;&lt;meta http-equiv=&quot;Content-Type&quot; content=&quot;text/html; charset=utf-8&quot; /&gt;&lt;style type=&quot;text/css&quot;&gt; p, li { white-space: pre-wrap; } &lt;/style&gt;&lt;/head&gt;&lt;body&gt;&lt;p style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;!--StartFragment--&gt;&lt;a href=&quot;%1&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;%2&lt;/span&gt;&lt;/a&gt;&lt;br /&gt;If clicking on the line above does not work, use this payment info:&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay to&lt;/span&gt;: %3</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9703"/>
        <source>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Amount&lt;/span&gt;: %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9706"/>
        <source>&lt;br /&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Message&lt;/span&gt;: %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9769"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9747"/>
        <source>Hide Buttons &lt;&lt;&lt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRestoreFragged</name>
    <message>
        <location filename="qtdialogs.py" line="11552"/>
        <source>&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Testing a
                     Fragmented Backup&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11555"/>
        <source>Restore Wallet from Fragments</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11557"/>
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
        <location filename="qtdialogs.py" line="11566"/>
        <source> &lt;br&gt;&lt;br&gt;
            &lt;b&gt;For testing purposes, you may enter more fragments than needed
            and Armory will test all subsets of the entered fragments to verify
            that each one still recovers the wallet successfully.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11581"/>
        <source>Input Fragments Below:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11582"/>
        <source>+Frag</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11583"/>
        <source>-Frag</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11587"/>
        <source>Encrypt Restored Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11596"/>
        <source>Test Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11596"/>
        <source>Restore from Fragments</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11598"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11605"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11646"/>
        <source>Fragments</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11648"/>
        <source>Advanced Options</source>
        <translation>Options avancées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11663"/>
        <source>Restore wallet from fragments</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11681"/>
        <source>Type Data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11682"/>
        <source>Load File</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11683"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11750"/>
        <source>Load Fragment File</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11750"/>
        <source>Wallet Fragments (*.frag)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11758"/>
        <source>File Does Not Exist</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11758"/>
        <source>
            The file you select somehow does not exist...?
            &lt;br&gt;&lt;br&gt;%1&lt;br&gt;&lt;br&gt; Try a different file</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11792"/>
        <source>Fragment Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11792"/>
        <source>
                  There was an unfixable error in the fragment file:
                  &lt;br&gt;&lt;br&gt; File: %1 &lt;br&gt; Line: %2 &lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11820"/>
        <source>
         &lt;b&gt;Start entering fragments into the table to left...&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11825"/>
        <source>&lt;b&gt;&lt;u&gt;Wallet Being Restored:&lt;/u&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11827"/>
        <source>&lt;b&gt;Frags Needed:&lt;/b&gt; %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11828"/>
        <source>&lt;b&gt;Wallet:&lt;/b&gt; %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11829"/>
        <source>&lt;b&gt;Fragments:&lt;/b&gt; %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11871"/>
        <source>Mixed fragment types</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11871"/>
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
        <location filename="qtdialogs.py" line="11891"/>
        <source>
            The fragment you just entered is actually for a different wallet
            than the previous fragments you entered.  Please double-check that
            all the fragments you are entering belong to the same wallet and
            have the &quot;number of needed fragments&quot; (M-value, in M-of-N).</source>
        <translation>
Le fragment que vous venez de saisir est en fait pour un porte-monnaie différent des fragments saisis précédemment. Veuillez vérifier que tous les fragments que vous saisissez appartiennent au même porte-monnaie et ont le « nombre de fragments requis » (valeur M, dans M de N).</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11902"/>
        <source>Duplicate Fragment</source>
        <translation>Fragment en double !</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11902"/>
        <source>
            You just input fragment #%1, but that fragment has already been
            entered!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11939"/>
        <source>Invalid Target Compute Time</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11939"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11943"/>
        <source>Invalid Max Memory Usage</source>
        <translation>L&apos;utilisation maximale de la mémoire est invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13149"/>
        <source>You entered Max Memory Usage incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12014"/>
        <source>Verify Wallet ID</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12014"/>
        <source>
         The data you entered corresponds to a wallet with a wallet
         ID:&lt;blockquote&gt;&lt;b&gt;{}&lt;/b&gt;&lt;/blockquote&gt;Does this ID
         match the &quot;Wallet Unique ID&quot; printed on your paper backup?
         If not, click &quot;No&quot; and reenter key and chain-code data
         again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12030"/>
        <source>Cannot Encrypt</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12030"/>
        <source>
               You requested your restored wallet be encrypted, but no
               valid passphrase was supplied.  Aborting wallet
               recovery.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12072"/>
        <source>Computing New Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11891"/>
        <source>Multiple Wallets</source>
        <translation>Plusieurs porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11943"/>
        <source>You entered Max Memory Usage incorrectly.

Enter: &lt;Number&gt; (kB, MB)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRestoreSingle</name>
    <message>
        <location filename="qtdialogs.py" line="10984"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Test a Paper Backup&lt;/font&gt;&lt;/u&gt;&lt;/b&gt;
         &lt;br&gt;&lt;br&gt;
         Use this window to test a single-sheet paper backup.  If your
         backup includes imported keys, those will not be covered by this test.  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10990"/>
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
        <location filename="qtdialogs.py" line="11000"/>
        <source>&lt;b&gt;Backup Type:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11002"/>
        <source>Version 1.35 (4 lines)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11003"/>
        <source>Version 1.35a (4 lines Unencrypted)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11004"/>
        <source>Version 1.35a (4 lines + SecurePrintâ¢)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11005"/>
        <source>Version 1.35c (2 lines Unencrypted)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11006"/>
        <source>Version 1.35c (2 lines + SecurePrintâ¢)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11029"/>
        <source>SecurePrintâ¢ Code:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11031"/>
        <source>Root Key:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11031"/>
        <source>Chaincode:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11048"/>
        <source>Test Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11048"/>
        <source>Restore Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11051"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11058"/>
        <source>Encrypt Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11064"/>
        <source>Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11066"/>
        <source>Advanced Options</source>
        <translation>Options avancées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11080"/>
        <source>Test Single-Sheet Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11082"/>
        <source>Restore Single-Sheet Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11139"/>
        <source>Invalid Data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11139"/>
        <source>
               There is an error in the data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.  &lt;br&gt;&lt;br&gt;
               The error occured on &lt;font color=&quot;red&quot;&gt;line #%1&lt;/font&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11152"/>
        <source>Invalid Target Compute Time</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11152"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11156"/>
        <source>Invalid Max Memory Usage</source>
        <translation>L&apos;utilisation maximale de la mémoire est invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12362"/>
        <source>You entered Max Memory Usage incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11162"/>
        <source>
            Detected errors in the data you entered.
            Armory attempted to fix the errors but it is not
            always right.  Be sure to verify the &quot;Wallet Unique ID&quot;
            closely on the next window.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11169"/>
        <source>Errors Corrected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11218"/>
        <source>Verify Wallet ID</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11218"/>
        <source>The data you entered corresponds to a wallet with a wallet ID: 

 <byte value="x9"/>
                  %1

Does this ID match the &quot;Wallet Unique ID&quot; 
                  printed on your paper backup?  If not, click &quot;No&quot; and reenter 
                  key and chain-code data again.</source>
        <translation>
Les données que vous avez saisies correspondent à un porte-monnaie dont l&apos;ID est :

&lt;byte value=&quot;x9&quot;/&gt;%1

Cet ID correspond-il à l&apos;« ID unique du porte-monnaie » imprimé sur votre sauvegarde papier ? Si ce n&apos;est pas le cas, cliquez sur « Non » et saisissez de nouveau la clé et les données code-chaîne.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11233"/>
        <source>Cannot Encrypt</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11233"/>
        <source>You requested your restored wallet be encrypted, but no valid passphrase was supplied.  Aborting wallet recovery.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11277"/>
        <source>Computing New Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11156"/>
        <source>You entered Max Memory Usage incorrectly.

Enter: &lt;Number&gt; (kB, MB)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgRestoreWOData</name>
    <message>
        <location filename="qtdialogs.py" line="11313"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Test a Watch-Only Wallet Restore
         &lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
         Use this window to test the restoration of a watch-only wallet using
         the wallet's data. You can either type the data on a root data
         printout or import the data from a file.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11320"/>
        <source>
         &lt;b&gt;&lt;u&gt;&lt;font color=&quot;blue&quot; size=&quot;4&quot;&gt;Restore a Watch-Only Wallet
         &lt;/font&gt;&lt;/u&gt;&lt;/b&gt;&lt;br&gt;&lt;br&gt;
         Use this window to restore a watch-only wallet using the wallet's
         data. You can either type the data on a root data printout or import
         the data from a file.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11328"/>
        <source>Watch-Only Root ID:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11336"/>
        <source>Data:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11355"/>
        <source>Test Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11355"/>
        <source>Restore Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11356"/>
        <source>Load From Text File</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11358"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11385"/>
        <source>Test Watch-Only Wallet Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11387"/>
        <source>Restore Watch-Only Wallet Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11397"/>
        <source>Import Wallet File</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11397"/>
        <source>Root Pubkey Text Files (*.rootpubkey)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11480"/>
        <source>Invalid Data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11450"/>
        <source>
               There is an error in the root ID you entered that could not
               be fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.&lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11480"/>
        <source>
               There is an error in the root data you entered that could not be
               fixed automatically.  Please double-check that you entered the
               text exactly as it appears on the wallet-backup page.  &lt;br&gt;&lt;br&gt;
               The error occured on &lt;font color=&quot;red&quot;&gt;line #%1&lt;/font&gt;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11513"/>
        <source>Wallet Already Exists</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11513"/>
        <source>The
                             wallet already exists and will not be
                             replaced.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11520"/>
        <source>Verify Wallet ID</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11520"/>
        <source>The data you entered corresponds to a wallet with a wallet ID: 

<byte value="x9"/>%1

Does this ID match the &quot;Wallet Unique ID&quot; you intend to restore? If not, click &quot;No&quot; and enter the key and chain-code data again.</source>
        <translation>
Les données que vous avez saisies correspondent à un porte-monnaie dont l&apos;ID est :

&lt;byte value=&quot;x9&quot;/&gt;%1

Cet ID correspond-il à l&apos;« ID unique du porte-monnaie »que vous avez l&apos;intention de restaurer ? Si ce n&apos;est pas le cas, cliquez sur « Non » et saisissez de nouveau la clé et les données code-chaîne.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="11535"/>
        <source>Computing New Addresses</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSelectMultiSigOption</name>
    <message>
        <location filename="MultiSigDialogs.py" line="3853"/>
        <source>Create/Manage lockboxes</source>
        <translation>Créer ou gérer des coffres</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3855"/>
        <source>Fund a lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3856"/>
        <source>Spend from a lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3858"/>
        <source>
         &lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;Multi-Sig Lockboxes
         [EXPERIMENTAL]&lt;/b&gt;&lt;/font&gt;</source>
        <translation>
&lt;font color=&quot;%1&quot; size=5&gt;&lt;b&gt;Coffres multisignatures [EXPÉRIMENTAL]&lt;/b&gt;&lt;/font&gt;</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3863"/>
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
        <location filename="MultiSigDialogs.py" line="3881"/>
        <source>
         Collect public keys to create an &quot;address&quot; that can be used 
         to send funds to the multi-sig container</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3887"/>
        <source>
         Send money to an lockbox simultaneously with other 
         parties involved in the lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3890"/>
        <source>
         Collect signatures to authorize transferring money out of 
         a multi-sig lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3943"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3954"/>
        <source>Multi-Sig Lockboxes</source>
        <translation>Coffres multisignatures</translation>
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
        <location filename="MultiSigDialogs.py" line="2179"/>
        <source>Select Public Key:</source>
        <translation>Sélectionner la clé publique :</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2180"/>
        <source>Notes or Contact Info:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2181"/>
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
        <location filename="MultiSigDialogs.py" line="2226"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2227"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2241"/>
        <source>Select Public Key for Lockbox</source>
        <translation>Sélectionner la clé publique</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2259"/>
        <source>Invalid Public Key</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2259"/>
        <source>
            You must enter a public key into the box, &lt;b&gt;not&lt;/b&gt; a regular 
            Bitcoin address that most users are accustomed to.  A public key 
            is much longer than a Bitcoin address, and always starts with 
            &quot;02&quot;, &quot;03&quot; or &quot;04&quot;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2280"/>
        <source>Export Public Key for Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2281"/>
        <source>
         The text below includes both the public key and the notes/contact info
         you entered.  Please send this text to the organizer (person or device) 
         to be used to create the lockbox.  This data is &lt;u&gt;not&lt;/u&gt; sensitive 
         and it is appropriate be sent via email or transferred via USB storage.
         </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2152"/>
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
         &lt;b&gt;&lt;font color=&quot;%1&quot;&gt;BACKUP WARNING&lt;/font&gt;&lt;/b&gt;:
         It is highly recommended that you select a public key from a
         wallet for which you have good backups!  If you are creating a lockbox
         requiring the same number of signatures as there are authorities 
         (such as 2-of-2 or 3-of-3), the loss of the wallet &lt;u&gt;will&lt;/u&gt; lead 
         to loss of lockbox funds!  
         </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSendBitcoins</name>
    <message>
        <location filename="qtdialogs.py" line="4585"/>
        <source>Send Bitcoins</source>
        <translation>Envoyer des bitcoins</translation>
    </message>
</context>
<context>
    <name>DlgSetComment</name>
    <message>
        <location filename="qtdialogs.py" line="3885"/>
        <source>Modify Comment</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3892"/>
        <source>Change %1 %2:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3894"/>
        <source>Change %1:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4313"/>
        <source>Add %2 %2:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3898"/>
        <source>Add %1:</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSetLongDescr</name>
    <message>
        <location filename="MultiSigDialogs.py" line="338"/>
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
        <location filename="MultiSigDialogs.py" line="350"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="358"/>
        <source>Edit Lockbox Description</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="395"/>
        <source>
            Using the &lt;font color=&quot;%1&quot;&gt;&lt;b&gt;%2&lt;/b&gt;&lt;/font&gt; public keys above,
            a multi-sig lockbox will be created requiring
            &lt;font color=&quot;%3&quot;&gt;&lt;b&gt;%4&lt;/b&gt;&lt;/font&gt; signatures to spend
            money.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="490"/>
        <source>Missing Name</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="490"/>
        <source>
            Lockboxes cannot be saved without a name (at the top of 
            the public key list).  It is also recommended to set the
            extended information next to it, for documenting the purpose
            of the lockbox.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="504"/>
        <source>Not Enough Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="504"/>
        <source>
               You specified less than &lt;b&gt;%1&lt;/b&gt; public keys.  Please enter
               a public key into every field before continuing.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="519"/>
        <source>Invalid Public Key</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="519"/>
        <source>
               The data specified for public key &lt;b&gt;%1&lt;/b&gt; is not valid.
               Please double-check the data was entered correctly.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="535"/>
        <source>Empty Name/ID Field</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="535"/>
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
        <location filename="MultiSigDialogs.py" line="564"/>
        <source>Different Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="564"/>
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
        <location filename="MultiSigDialogs.py" line="579"/>
        <source>Non-Standard to Spend</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="579"/>
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
        <location filename="qtdialogs.py" line="8285"/>
        <source>
         Let Armory run Bitcoin Core/bitcoind in the background</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8296"/>
        <source>Bitcoin Core/bitcoind management is not available on Mac/OSX</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8306"/>
        <source>&lt;b&gt;Bitcoin Software Management&lt;/b&gt;&lt;br&gt;&lt;br&gt;By default, Armory will manage the Bitcoin engine/software in the background.  You can choose to manage it yourself, or tell Armory about non-standard installation configuration.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8319"/>
        <source>Bitcoin Install Dir:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8320"/>
        <source>Bitcoin Home Dir:</source>
        <translation>Répertoire Bitcoin personnel :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8321"/>
        <source>Leave blank to have Armory search default locations for your OS</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8323"/>
        <source>Leave blank to use default datadir (%1)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8350"/>
        <source>
         Skip online check on startup (assume internet is available, do
         not check)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8360"/>
        <source>&lt;b&gt;Privacy Settings&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8361"/>
        <source>
         If you are going to use Armory and Bitcoin Core with a proxy (such
         as Tor), you should disable all Armory communications that might operate
         outside the proxy.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8812"/>
        <source>
         Enable settings for proxies/Tor</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8377"/>
        <source>
         &lt;b&gt;Set Armory as default URL handler&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8379"/>
        <source>
         Set Armory to be the default when you click on &quot;bitcoin:&quot;
         links in your browser or in emails.
         You can test if your operating system is supported by clicking
         on a &quot;bitcoin:&quot; link right after clicking this button.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8385"/>
        <source>Set Armory as Default</source>
        <translation>Définir Armory comme application par défaut</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8388"/>
        <source>
         Check whether Armory is the default handler at startup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8395"/>
        <source>Registered</source>
        <translation>Enregistré</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8395"/>
        <source>
            Armory just attempted to register itself to handle &quot;bitcoin:&quot;
            links, but this does not work on all operating systems.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8403"/>
        <source>
         &lt;b&gt;Default fee to include with transactions:&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8405"/>
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
        <location filename="qtdialogs.py" line="8438"/>
        <source>Minimize to system tray on open</source>
        <translation>Minimiser vers la zone de notification lors du lancement</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8443"/>
        <source>Minimize to system tray on close</source>
        <translation>Minimiser vers la zone de notification lors de la fermeture</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8456"/>
        <source>&lt;b&gt;Enable notifications from the system-tray:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8457"/>
        <source>Bitcoins Received</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8458"/>
        <source>Bitcoins Sent</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8459"/>
        <source>Bitcoin Core/bitcoind disconnected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8460"/>
        <source>Bitcoin Core/bitcoind reconnected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8464"/>
        <source>&lt;b&gt;Sorry!  Notifications are not available on your version of OS X.&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8489"/>
        <source>&lt;b&gt;Preferred Date Format&lt;b&gt;:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8490"/>
        <source>You can specify how you would like dates to be displayed using percent-codes to represent components of the date.  The mouseover text of the &quot;(?)&quot; icon shows the most commonly used codes/symbols.  The text next to it shows how &quot;%1&quot; would be shown with the specified format.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8501"/>
        <source>Use any of the following symbols:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8515"/>
        <source>Reset to Default</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8533"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8534"/>
        <source>Save</source>
        <translation>Enregistrer</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8555"/>
        <source>&lt;b&gt;Armory user mode:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8563"/>
        <source>&lt;b&gt;Preferred Language&lt;b&gt;:&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8564"/>
        <source>Specify which language you would like Armory to be displayed in.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8685"/>
        <source>General</source>
        <translation>Général</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8691"/>
        <source>Fee &amp; Change</source>
        <translation>Frais et monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8705"/>
        <source>Armory Settings</source>
        <translation>Paramètres d&apos;Armory</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8742"/>
        <source>&lt;b&gt;Fee&lt;br&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;Frais&lt;br&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8744"/>
        <source>Auto fee/byte</source>
        <translation>Frais/octet automatiques</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8746"/>
        <source>
      Fetch fee/byte from local Bitcoin node. 
      Defaults to manual fee/byte on failure. 
      </source>
        <translation>
Récupérer les frais/octet du nœud Bitcoin local.
Utilise les frais/octet manuels en cas d&apos;échec.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8751"/>
        <source>Manual fee/byte</source>
        <translation>Frais/octet manuels</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8754"/>
        <source>
      Values in satoshis/byte
      </source>
        <translation>
Valeurs en satoshis/octet
      </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8758"/>
        <source>Flat fee</source>
        <translation>Frais fixes</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8761"/>
        <source>
      Values in BTC
      </source>
        <translation>
Valeurs en BTC
      </translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8765"/>
        <source>Auto-adjust fee/byte for better privacy</source>
        <translation>Ajuster automatiquement les frais/octet pour une protection accrue des données personnelles</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8767"/>
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
        <location filename="qtdialogs.py" line="8831"/>
        <source>&lt;b&gt;Change Address Type&lt;br&gt;&lt;/b&gt;</source>
        <translation>&lt;b&gt;Changer le type d&apos;adresse&lt;br&gt;&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8833"/>
        <source>Auto change</source>
        <translation>Changement automatique</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8835"/>
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
        <location filename="qtdialogs.py" line="8847"/>
        <source>Force P2PKH</source>
        <translation>Forcer P2PKH</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8850"/>
        <source>Force P2SH-P2PK</source>
        <translation>Forcer P2SH-P2PK</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8853"/>
        <source>Force P2SH-P2WPKH</source>
        <translation>Forcer P2SH-P2WPKH</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8855"/>
        <source>
      Defaults back to P2SH-P2PK if SegWit is not enabled
      </source>
        <translation>
Revient à P2SH-P2PK si SegWit n&apos;est pas activé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8911"/>
        <source>Invalid Path</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8894"/>
        <source>The path you specified for the Bitcoin software installation does not exist.  Please select the directory that contains %1 or leave it blank to have Armory search the default location for your operating system</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8911"/>
        <source>The path you specified for the Bitcoin software home directory does not exist.  Only specify this directory if you use a non-standard &quot;-datadir=&quot; option when running Bitcoin Core or bitcoind.  If you leave this field blank, the following path will be used: &lt;br&gt;&lt;br&gt; %1</source>
        <translation>Le chemin que vous avez indiqué comme répertoire personnel du logiciel Bitcoin n&apos;existe pas. N&apos;indiquez ce répertoire que si vous utilisez une option « -datadir= » non standard lorsque vous exécutez Bitcoin Core ou bitcoind. Si vous laissez ce champ vide, le chemin suivant sera utilisé :&lt;br&gt;&lt;br&gt; %1</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8934"/>
        <source>Invalid Amount</source>
        <translation>Montant invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8934"/>
        <source>The default fee specified could not be understood.  Please specify in BTC with no more than 8 decimal places.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8993"/>
        <source>&quot;Standard&quot; is for users that only need the core set of features to send and receive bitcoins.  This includes maintaining multiple wallets, wallet encryption, and the ability to make backups of your wallets.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8999"/>
        <source>&quot;Advanced&quot; mode provides extra Armory features such as private key importing &amp; sweeping, message signing, and the offline wallet interface.  But, with advanced features come advanced risks...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9005"/>
        <source>&quot;Expert&quot; mode is similar to &quot;Advanced&quot; but includes access to lower-level info about transactions, scripts, keys and network protocol.  Most extra functionality is geared towards Bitcoin software developers.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9016"/>
        <source>Sample: </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9019"/>
        <source>Sample: [[invalid date format]]</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8410"/>
        <source>
         NOTE: Some transactions will require a certain fee
         regardless of your settings -- in such cases
         you will be prompted to include the correct
         value or cancel the transaction</source>
        <translation>
NOTE : certaines transactions exigeront des frais particuliers, quels que soient vos paramètres. Dans de tels cas, vous serez invité à inclure la bonne valeur ou à annuler la transaction</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8425"/>
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
        <translation>
&lt;b&gt;Minimiser vers la zone de notification&lt;/b&gt;
&lt;br&gt;
Armory peut se minimiser automatiquement dans la zone de notification lors du lancement ou de la fermeture. Armory restera ouverte mais fonctionnera en arrière-plan et vous recevrez toujours les notifications. Accédez à Armory grâce à l&apos;icône de la zone de notification.
&lt;br&gt;&lt;br&gt;
Si vous sélectionnez « Minimiser lors de la fermeture », le x de la barre supérieure de la fenêtre minimisera Armory au lieu de fermer l&apos;application. Vous pouvez toujours utiliser &lt;i&gt;« Fichier » &lt;/i&gt; -&gt; &lt;i&gt;« Quitter Armory »&lt;/i&gt; pour effectivement fermer Armory.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8366"/>
        <source>Enable settings for proxies/Tor</source>
        <translation>Activer les paramètres de mandataires ou de Tor</translation>
    </message>
</context>
<context>
    <name>DlgShowKeyList</name>
    <message>
        <location filename="qtdialogs.py" line="4832"/>
        <source>The textbox below shows all keys that are part of this wallet,which includes both permanent keys and imported keys.  If yousimply want to backup your wallet and you have no imported keysthen all data below is reproducible from a plain paper backup.&lt;br&gt;&lt;br&gt;If you have imported addresses to backup, and/or youwould like to export your private keys to anotherwallet service or application, then you can save this datato disk, or copy&amp;paste it into the other application.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4842"/>
        <source>&lt;br&gt;&lt;br&gt;&lt;font color=&quot;red&quot;&gt;Warning:&lt;/font&gt; The text box below containsthe plaintext (unencrypted) private keys for each ofthe addresses in this wallet.  This information can be usedto spend the money associated with those addresses, so pleaseprotect it like you protect the rest of your wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4868"/>
        <source>Address String</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4869"/>
        <source>Hash160</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4870"/>
        <source>Private Key (Encrypted)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4871"/>
        <source>Private Key (Plain Hex)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4872"/>
        <source>Private Key (Plain Base58)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4873"/>
        <source>Public Key (BE)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4874"/>
        <source>Chain Index</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4892"/>
        <source>Imported Addresses Only</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4893"/>
        <source>Include Unused (Address Pool)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4894"/>
        <source>Include Paper Backup Root</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4895"/>
        <source>Omit spaces in key data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4933"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4934"/>
        <source>Save to File...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4935"/>
        <source>Copy to Clipboard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4968"/>
        <source>All Wallet Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5073"/>
        <source>Plaintext Private Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5073"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;REMEMBER:&lt;/b&gt;&lt;/font&gt; The data youare about to save contains private keys.  Please make surethat only trusted persons will have access to this file.&lt;br&gt;&lt;br&gt;Are you sure you want to continue?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5084"/>
        <source>Save Key List</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5084"/>
        <source>Text Files (*.txt)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5084"/>
        <source>keylist_%1_.txt</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5098"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4832"/>
        <source>The textbox below shows all keys that are part of this wallet, which includes both permanent keys and imported keys.  If you simply want to backup your wallet and you have no imported keys then all data below is reproducible from a plain paper backup. &lt;br&gt;&lt;br&gt; If you have imported addresses to backup, and/or you would like to export your private keys to another wallet service or application, then you can save this data to disk, or copy&amp;paste it into the other application.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4842"/>
        <source>&lt;br&gt;&lt;br&gt;&lt;font color=&quot;red&quot;&gt;Warning:&lt;/font&gt; The text box below contains the plaintext (unencrypted) private keys for each of the addresses in this wallet.  This information can be used to spend the money associated with those addresses, so please protect it like you protect the rest of your wallet. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5073"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;REMEMBER:&lt;/b&gt;&lt;/font&gt; The data you are about to save contains private keys.  Please make sure that only trusted persons will have access to this file. &lt;br&gt;&lt;br&gt;Are you sure you want to continue?</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgShowKeys</name>
    <message>
        <location filename="qtdialogs.py" line="3414"/>
        <source>
            &lt;font color=%1&gt;&lt;b&gt;Warning:&lt;/b&gt; the unencrypted private keys
            for this address are shown below.  They are &quot;private&quot; because
            anyone who obtains them can spend the money held
            by this address.  Please protect this information the
            same as you protect your wallet.&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3432"/>
        <source>Key Data for address: &lt;b&gt;%1&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3443"/>
        <source>
            The raw form of the private key for this address.  It is
            32-bytes of randomly generated data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3446"/>
        <source>Private Key (hex,%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3448"/>
        <source>&lt;i&gt;[[ No Private Key in Watching-Only Wallet ]]&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3452"/>
        <source>&lt;i&gt;[[ ENCRYPTED ]]&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3456"/>
        <source>
               This is a more compact form of the private key, and includes
               a checksum for error detection.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3459"/>
        <source>Private Key (Base58):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3466"/>
        <source>
               The raw public key data.  This is the X-coordinate of
               the Elliptic-curve public key point.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3469"/>
        <source>Public Key X (%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3474"/>
        <source>
               The raw public key data.  This is the Y-coordinate of
               the Elliptic-curve public key point.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3477"/>
        <source>Public Key Y (%1):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3485"/>
        <source>%1 (Network: %2 / Checksum: %3)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3488"/>
        <source>This is the hexadecimal version if the address string</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3490"/>
        <source>Public Key Hash:</source>
        <translation>Hachage de clé publique :</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3524"/>
        <source>Address Key Information</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgShowTestResults</name>
    <message>
        <location filename="qtdialogs.py" line="12141"/>
        <source>
            The total number of fragment subsets (%1) is too high
            to test and display.  Instead, %2 subsets were tested
            at random.  The results are below </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12146"/>
        <source>
            For the fragments you entered, there are a total of
            %1 possible subsets that can restore your wallet.
            The test results for all subsets are shown below</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12153"/>
        <source>
         The wallet ID is computed from the first
         address in your wallet based on the root key data (and the
         &quot;chain code&quot;).  Therefore, a matching wallet ID proves that
         the wallet will produce identical addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12166"/>
        <source>
            Fragments &lt;b&gt;%1&lt;/b&gt; and &lt;b&gt;%2&lt;/b&gt; produce a
            wallet with ID &quot;&lt;b&gt;%3&lt;/b&gt;&quot; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12188"/>
        <source>Ok</source>
        <translation>OK</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12200"/>
        <source>Fragment Test Results</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSignBroadcastOfflineTx</name>
    <message>
        <location filename="qtdialogs.py" line="4785"/>
        <source>Review Offline Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4788"/>
        <source>Sign or Broadcast Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4791"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
</context>
<context>
    <name>DlgSimpleBackup</name>
    <message>
        <location filename="qtdialogs.py" line="9980"/>
        <source>
         &lt;b&gt;Protect Your Bitcoins -- Make a Wallet Backup!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9983"/>
        <source>
         A failed hard-drive or forgotten passphrase will lead to
         &lt;u&gt;permanent loss of bitcoins&lt;/u&gt;!  Luckily, Armory wallets only
         need to be backed up &lt;u&gt;one time&lt;/u&gt;, and protect you in both
         of these events.   If you've ever forgotten a password or had
         a hardware failure, make a backup! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9991"/>
        <source>
         Use a printer or pen-and-paper to write down your wallet &quot;seed.&quot; </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9993"/>
        <source>Make Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9996"/>
        <source>
         Create an unencrypted copy of your wallet file, including imported
         addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9999"/>
        <source>Make Digital Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10007"/>
        <source> </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10002"/>
        <source>See Other Backup Options</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10045"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10055"/>
        <source>Backup Options</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSimulfundSelect</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1991"/>
        <source>
         &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;Simultaneous Lockbox
         Funding&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1995"/>
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
        <location filename="MultiSigDialogs.py" line="2016"/>
        <source>Create Promissory Note</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2017"/>
        <source>Collect and Merge Notes</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2018"/>
        <source>Sign Simulfunding Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2019"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2022"/>
        <source>
            Create a commitment to a simulfunding transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2026"/>
        <source>
            Note creation is not available when offline.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2029"/>
        <source>
         Collect multiple promissory notes into a single simulfunding
         transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2033"/>
        <source>
         Review and signed a simulfunding transaction (after all promissory
         notes have been collected)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2029"/>
        <source>
         Collect multiple promissory notes into a single simulfunding transaction</source>
        <translation>
Recueillir plusieurs billets à ordre en une seule transaction de financement simultané</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2032"/>
        <source>
         Review and sign a simulfunding transaction (after all promissory
         notes have been collected)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgSpendFromLockbox</name>
    <message>
        <location filename="MultiSigDialogs.py" line="1916"/>
        <source>
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1922"/>
        <source>Create Transaction</source>
        <translation>Créer une transaction</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1923"/>
        <source>Review and Sign</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1924"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1927"/>
        <source>
            I am creating a new proposed spending transaction and will pass
            it to each party or device that needs to sign it</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1932"/>
        <source>
            Transaction creation is not available when offline.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="1935"/>
        <source>
         Another party or device created the transaction, I just need 
         to review and sign it.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgTxFeeOptions</name>
    <message>
        <location filename="qtdialogs.py" line="5123"/>
        <source>
         Transaction fees go to people who contribute processing power to
         the Bitcoin network to process transactions and keep it secure.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="5126"/>
        <source>
         Nearly all transactions are guaranteed to be
         processed if a fee of 0.0005 BTC is included (less than $0.01 USD).  You
         will be prompted for confirmation if a higher fee amount is required for
         your transaction.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgUniversalRestoreSelect</name>
    <message>
        <location filename="qtdialogs.py" line="10847"/>
        <source>
         &lt;b&gt;&lt;u&gt;Restore Wallet from Backup&lt;/u&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10849"/>
        <source>You can restore any kind of backup ever created by Armory using
         one of the options below.  If you have a list of private keys
         you should open the target wallet and select &quot;Import/Sweep
         Private Keys.&quot;  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10877"/>
        <source>I am restoring a...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10854"/>
        <source>Single-Sheet Backup (printed)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10855"/>
        <source>Fragmented Backup (incl. mix of paper and files)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10856"/>
        <source>Import digital backup or watching-only wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10857"/>
        <source>Import watching-only wallet data</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10858"/>
        <source>This is a test recovery to make sure my backup works</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10872"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10873"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
</context>
<context>
    <name>DlgUnlockWallet</name>
    <message>
        <location filename="qtdialogs.py" line="61"/>
        <source>Enter your passphrase to unlock this wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="62"/>
        <source>Passphrase:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="68"/>
        <source>Unlock</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="69"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="86"/>
        <source>Using a visual keyboard to enter your passphrase protects you against simple keyloggers.   Scrambling makes it difficult to use, but prevents even loggers that record mouse clicks.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="93"/>
        <source>Regular Keyboard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="94"/>
        <source>Scrambled (Simple)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="95"/>
        <source>Scrambled (Dynamic)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="161"/>
        <source>Show Keyboard &gt;&gt;&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="159"/>
        <source>Hide Keyboard &lt;&lt;&lt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="176"/>
        <source>SHIFT</source>
        <translation>Maj</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="177"/>
        <source>SPACE</source>
        <translation>ESPACE</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="178"/>
        <source>DEL</source>
        <translation>Suppr</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="314"/>
        <source>Unlocking Wallet</source>
        <translation>Déverrouillage du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="324"/>
        <source>Invalid Passphrase</source>
        <translation>Phrase de passe invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="324"/>
        <source>That passphrase is not correct!</source>
        <translation>Cette phrase de passe est erronée !</translation>
    </message>
</context>
<context>
    <name>DlgUriCopyAndPaste</name>
    <message>
        <location filename="qtdialogs.py" line="9777"/>
        <source>Copy and paste a raw bitcoin URL string here.  A valid string starts with &quot;bitcoin:&quot; followed by a bitcoin address.&lt;br&gt;&lt;br&gt;You should use this feature if there is a &quot;bitcoin:&quot; link in a webpage or email that does not load Armory when you click on it.  Instead, right-click on the link and select &quot;Copy Link Location&quot; then paste it into the box below. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9793"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="9794"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
</context>
<context>
    <name>DlgVerifySweep</name>
    <message>
        <location filename="qtdialogs.py" line="2985"/>
        <source>
            You are about to &lt;i&gt;sweep&lt;/i&gt; all funds from the specified address
            to your wallet.  Please confirm the action:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2991"/>
        <source>(Fee: %1)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2997"/>
        <source>      From %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2998"/>
        <source>      To %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2999"/>
        <source>      Total &lt;b&gt;%1&lt;/b&gt; BTC %2</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3002"/>
        <source>Are you sure you want to execute this transaction?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="3018"/>
        <source>Confirm Sweep</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgWODataPrintBackup</name>
    <message>
        <location filename="qtdialogs.py" line="10247"/>
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
        <location filename="qtdialogs.py" line="10354"/>
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
        <location filename="qtdialogs.py" line="10361"/>
        <source>
         The following five lines are sufficient to reproduce all public
         keys matching the private keys produced by the full wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10400"/>
        <source>
         The following QR code is for convenience only.  It contains the
         exact same data as the five lines above.  If you copy this data
         by hand, you can safely ignore this QR code. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10331"/>
        <source>&lt;b&gt;&lt;font size=4&gt;&lt;font color=&quot;#aa0000&quot;&gt;WARNING:&lt;/font&gt;  &lt;u&gt;This is not a wallet backup!&lt;/u&gt;&lt;/font&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt;Please make a regular digital or paper backup of your wallet to keep it protected!  This data simply lets you monitor the funds in this wallet but gives you no ability to move any funds.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgWalletDetails</name>
    <message>
        <location filename="qtdialogs.py" line="1092"/>
        <source>Change Wallet Labels</source>
        <translation>Changer les étiquettes du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1099"/>
        <source>Change or Remove Passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1101"/>
        <source>Encrypt Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1106"/>
        <source>Send Bitcoins</source>
        <translation>Envoyer des bitcoins</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1107"/>
        <source>Receive Bitcoins</source>
        <translation>Recevoir des bitcoins</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1108"/>
        <source>Import/Sweep Private Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1109"/>
        <source>Remove Imported Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1111"/>
        <source>Export Watching-Only %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1112"/>
        <source>&lt;b&gt;Backup This Wallet&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1113"/>
        <source>Delete/Remove Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1550"/>
        <source>&lt;u&gt;&lt;/u&gt;Send bitcoins to other users, or transfer 
                             between wallets</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1553"/>
        <source>&lt;u&gt;&lt;/u&gt;If you have a full-copy of this wallet 
                                on another computer, you can prepare a 
                                transaction, to be signed by that computer.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1556"/>
        <source>&lt;u&gt;&lt;/u&gt;Get a new address from this wallet for receiving 
                             bitcoins.  Right click on the address list below 
                             to copy an existing address.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1559"/>
        <source>&lt;u&gt;&lt;/u&gt;Import or &quot;Sweep&quot; an address which is not part 
                             of your wallet.  Useful for VanityGen addresses 
                             and redeeming Casascius physical bitcoins.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1562"/>
        <source>&lt;u&gt;&lt;/u&gt;Permanently delete an imported address from 
                             this wallet.  You cannot delete addresses that 
                             were generated natively by this wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1566"/>
        <source>&lt;u&gt;&lt;/u&gt;Export a copy of this wallet that can 
                             only be used for generating addresses and 
                             monitoring incoming payments.  A watching-only 
                             wallet cannot spend the funds, and thus cannot 
                             be compromised by an attacker</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1571"/>
        <source>&lt;u&gt;&lt;/u&gt;See lots of options for backing up your wallet 
                             to protect the funds in it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1573"/>
        <source>&lt;u&gt;&lt;/u&gt;Permanently delete this wallet, or just delete 
                            the private keys to convert it to a watching-only 
                            wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1579"/>
        <source>&lt;u&gt;&lt;/u&gt;Add/Remove/Change wallet encryption settings.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1227"/>
        <source>Total funds if all current transactions are confirmed.  
            Value appears gray when it is the same as your spendable funds.</source>
        <translation>Total des fonds si toutes les transactions actuelles sont confirmées.
La valeur est grisée si elle est identique aux fonds disponibles.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1230"/>
        <source>Funds that can be spent &lt;i&gt;right now&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1232"/>
        <source>Funds that have less than 6 confirmations</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1259"/>
        <source>&lt;b&gt;Addresses in Wallet:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1261"/>
        <source>&lt;&lt;&lt; Go Back</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1280"/>
        <source>Wallet Properties</source>
        <translation>Propriétés du porte-monnaie</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1293"/>
        <source>Wallet Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1293"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot; size=4&gt;Please backup your wallet!&lt;/font&gt;&lt;/b&gt; &lt;br&gt;&lt;br&gt;Making a paper backup will guarantee you can recover your coins at &lt;a&gt;any time in the future&lt;/a&gt;, even if your hard drive dies or you forget your passphrase.  Without it, you could permanently lose your coins!  The backup buttons are to the right of the address list.&lt;br&gt;&lt;br&gt;A paper backup is recommended, and it can be copied by hand if you do not have a working printer. A digital backup only works if you remember the passphrase used at the time it was created.  If you have ever forgotten a password before, only rely on a digital backup if you store the password with it!&lt;br&gt;&lt;br&gt;&lt;a href=&quot;https://bitcointalk.org/index.php?topic=152151.0&quot;&gt;Read more about Armory backups&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1324"/>
        <source>&lt;font color=&quot;%1&quot;&gt;&lt;b&gt;Backup This Wallet&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1343"/>
        <source>&lt;b&gt;&lt;font color=&quot;%1&quot;&gt;Maximum Funds:&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1344"/>
        <source>&lt;b&gt;Spendable Funds:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Fonds disponibles :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1345"/>
        <source>&lt;b&gt;Unconfirmed:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1392"/>
        <source>Copy Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1393"/>
        <source>Display Address QR Code</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1394"/>
        <source>View Address on %1</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1395"/>
        <source>Request Payment to this Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1396"/>
        <source>Copy Hash160 (hex)</source>
        <translation>Copier Hash160 (hexadécimal)</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1397"/>
        <source>Copy Raw Public Key (hex)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1398"/>
        <source>Copy Comment</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1399"/>
        <source>Copy Balance</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1424"/>
        <source>Could not open browser</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1424"/>
        <source>Armory encountered an error opening your web browser.  To viewthis address on blockchain.info, please copy and pastethe following URL into your browser:&lt;br&gt;&lt;br&gt;&lt;a href=&quot;%1&quot;&gt;%2&lt;/a&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1524"/>
        <source>Invalid Passphrase</source>
        <translation>Phrase de passe invalide</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1524"/>
        <source>Previous passphrase is not correct!  Could not unlock wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1541"/>
        <source>Changing Encryption</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1534"/>
        <source>No Encryption</source>
        <translation>Pas de chiffrement</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1545"/>
        <source>Encrypted (AES256)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1559"/>
        <source>Offline Mode</source>
        <translation>Mode hors ligne</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1559"/>
        <source>Armory is currently running in offline mode, and has noability to determine balances or create transactions.&lt;br&gt;&lt;br&gt;In order to send coins from this wallet you must use afull copy of this wallet from an online computer,or initiate an &quot;offline transaction&quot; using a watching-onlywallet on an online computer.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1569"/>
        <source>Armory Not Ready</source>
        <translation>Armory n&apos;est pas prêt</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1569"/>
        <source>
           Armory is currently scanning the blockchain to collect
           the information needed to create transactions.  This
           typically takes between one and five minutes.  Please
           wait until your balance appears on the main window,
           then try again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1600"/>
        <source>Create Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1605"/>
        <source>Move along...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1605"/>
        <source>This wallet does not contain any private keys.  Nothing to backup!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1619"/>
        <source>Unlock Private Keys</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1628"/>
        <source>Unlock Failed</source>
        <translation>Échec de déverrouillage</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1622"/>
        <source>
                  Wallet was not be unlocked.  The public keys and addresses
                  will still be shown, but private keys will not be available
                  unless you reopen the dialog with the correct passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1628"/>
        <source>
                  Wallet could not be unlocked to display individual keys.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1639"/>
        <source>No Selection</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1639"/>
        <source>You must select an address to remove!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1656"/>
        <source>Invalid Selection</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1656"/>
        <source>
               You cannot delete addresses generated by your wallet.
               Only imported addresses can be deleted.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1665"/>
        <source>Imported Address Warning</source>
        <translation>Avertissement d&apos;adresse importée</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1665"/>
        <source>Armory supports importing of external private keys into yourwallet but imported addresses are &lt;u&gt;not&lt;/u&gt; automaticallyprotected by your backups.  If you do not plan to use theaddress again, it is recommended that you &quot;Sweep&quot; the privatekey instead of importing it.&lt;br&gt;&lt;br&gt;Individual private keys, including imported ones, can bebacked up using the &quot;Export Key Lists&quot; option in the walletbackup window.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1697"/>
        <source>Move along... This wallet does not have
                             a chain code. Backups are pointless!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1722"/>
        <source>
            This is the name stored with the wallet file.  Click on the
            &quot;Change Labels&quot; button on the right side of this
            window to change this field</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1727"/>
        <source>
            This is the description of the wallet stored in the wallet file.
            Press the &quot;Change Labels&quot; button on the right side of this
            window to change this field</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1732"/>
        <source>
            This is a unique identifier for this wallet, based on the root key.
            No other wallet can have the same ID
            unless it is a copy of this one, regardless of whether
            the name and description match.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1738"/>
        <source>
            This is the number of addresses *used* by this wallet so far.
            If you recently restored this wallet and you do not see all the
            funds you were expecting, click on this field to increase it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1744"/>
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
        <location filename="qtdialogs.py" line="1752"/>
        <source>
            Watching-Only:  You can only watch addresses in this wallet
            but cannot spend any of the funds.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1756"/>
        <source>
            No Encryption: This wallet contains private keys, and does not require
            a passphrase to spend funds available to this wallet.  If someone
            else obtains a copy of this wallet, they can also spend your funds!
            (You can click the &quot;Change Encryption&quot; button on the right side of this
            window to enabled encryption)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1763"/>
        <source>
            This wallet contains the private keys needed to spend this wallet's
            funds, but they are encrypted on your harddrive.  The wallet must be
            &quot;unlocked&quot; with the correct passphrase before you can spend any of the
            funds.  You can still generate new addresses and monitor incoming
            transactions, even with a locked wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1770"/>
        <source>
            Declare who owns this wallet.  If you click on the field and select
            &quot;This wallet is mine&quot;, it's balance will be included in your total
            Armory Balance in the main window</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1775"/>
        <source>
            This is exactly how long it takes your computer to unlock your
            wallet after you have entered your passphrase.  If someone got
            ahold of your wallet, this is approximately how long it would take
            them to for each guess of your passphrase.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1781"/>
        <source>
            This is the amount of memory required to unlock your wallet.
            Memory values above 64 kB pretty much guarantee that GPU-acceleration
            will be useless for guessing your passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1786"/>
        <source>
            Wallets created with different versions of Armory, may have
            different wallet versions.  Not all functionality may be
            available with all wallet versions.  Creating a new wallet will
            always create the latest version.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1792"/>
        <source>Wallet Name:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1793"/>
        <source>Description:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1795"/>
        <source>Wallet ID:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1796"/>
        <source>Addresses Used:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1797"/>
        <source>Security:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1798"/>
        <source>Version:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1800"/>
        <source>Belongs to:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1806"/>
        <source>Unlock Time:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1807"/>
        <source>Unlock Memory:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1955"/>
        <source>You own this wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1833"/>
        <source>Someone else...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1843"/>
        <source>Click to Test</source>
        <translation>Cliquer pour tester</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1957"/>
        <source>&lt;i&gt;Offline&lt;/i&gt;</source>
        <translation>&lt;i&gt;Hors ligne&lt;/i&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1966"/>
        <source>Someone else</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1967"/>
        <source>&lt;i&gt;Watching-Only&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1130"/>
        <source>Send bitcoins to other users, or transfer 
                             between wallets</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1133"/>
        <source>If you have a full-copy of this wallet 
                                on another computer, you can prepare a 
                                transaction, to be signed by that computer.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1136"/>
        <source>Get a new address from this wallet for receiving 
                             bitcoins.  Right click on the address list below 
                             to copy an existing address.</source>
        <translation>Obtenir une nouvelle adresse de ce porte-monnaie pour recevoir des bitcoins. Cliquer à droite sur la liste d&apos;adresses ci-dessous pour copier une adresse existante.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1139"/>
        <source>Import or &quot;Sweep&quot; an address which is not part 
                             of your wallet.  Useful for VanityGen addresses 
                             and redeeming Casascius physical bitcoins.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1142"/>
        <source>Permanently delete an imported address from 
                             this wallet.  You cannot delete addresses that 
                             were generated natively by this wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1146"/>
        <source>Export a copy of this wallet that can 
                             only be used for generating addresses and 
                             monitoring incoming payments.  A watching-only 
                             wallet cannot spend the funds, and thus cannot 
                             be compromised by an attacker</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1151"/>
        <source>See lots of options for backing up your wallet 
                             to protect the funds in it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1153"/>
        <source>Permanently delete this wallet, or just delete 
                            the private keys to convert it to a watching-only 
                            wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1159"/>
        <source>Add/Remove/Change wallet encryption settings.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1475"/>
        <source>Add Address Comment</source>
        <translation>Ajouter un commentaire d&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1477"/>
        <source>Change Address Comment</source>
        <translation>Modifier un commentaire d&apos;adresse</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1424"/>
        <source>Armory encountered an error opening your web browser.  To view this address on blockchain.info, please copy and paste the following URL into your browser: &lt;br&gt;&lt;br&gt;&lt;a href=&quot;%1&quot;&gt;%2&lt;/a&gt;</source>
        <translation>Une erreur est survenue lors de l&apos;ouverture de votre navigateur Web par Armory. Pour visualiser cette adresse sur blockchain.info, veuillez copier-coller l&apos;URL suivante dans votre navigateur : &lt;br&gt;&lt;br&gt;&lt;a href=&quot;%1&quot;&gt;%2&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1559"/>
        <source>Armory is currently running in offline mode, and has no ability to determine balances or create transactions. &lt;br&gt;&lt;br&gt; In order to send coins from this wallet you must use a full copy of this wallet from an online computer, or initiate an &quot;offline transaction&quot; using a watching-only wallet on an online computer.</source>
        <translation>Armory fonctionne actuellement en mode hors ligne et ne peut pas déterminer les soldes ni créer de transactions. &lt;br&gt;&lt;br&gt; Afin d&apos;envoyer des pièces de ce porte-monnaie, vous devez utiliser une copie complète de ce porte-monnaie sur un ordinateur en ligne, ou commencer une « transaction hors ligne » en utilisant un porte-monnaie juste-regarder sur un ordinateur en ligne.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1569"/>
        <source>Armory is currently scanning the blockchain to collect the information needed to create transactions.  This typically takes between one and five minutes.  Please wait until your balance appears on the main window, then try again.</source>
        <translation>Armory analyse actuellement la chaîne de blocs pour recueillir les informations nécessaires à la création de transactions. Cela prend habituellement d&apos;une à cinq minutes. Veuillez attendre que votre solde apparaisse sur la fenêtre principale et ressayer.</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1665"/>
        <source>Armory supports importing of external private keys into your wallet but imported addresses are &lt;u&gt;not&lt;/u&gt; automatically protected by your backups.  If you do not plan to use the address again, it is recommended that you &quot;Sweep&quot; the private key instead of importing it. &lt;br&gt;&lt;br&gt; Individual private keys, including imported ones, can be backed up using the &quot;Export Key Lists&quot; option in the wallet backup window.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgWalletSelect</name>
    <message>
        <location filename="qtdialogs.py" line="4326"/>
        <source>No Wallets!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4326"/>
        <source>There are no wallets to select from.  Please create or import
            a wallet first.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="4355"/>
        <source>Select Wallet</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>DlgWltRecoverWallet</name>
    <message>
        <location filename="qtdialogs.py" line="12632"/>
        <source>Browse File System</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12636"/>
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
        <location filename="qtdialogs.py" line="12648"/>
        <source>Wallet Path:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12653"/>
        <source>Select Wallet...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12659"/>
        <source>Select Loaded Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12683"/>
        <source>&lt;b&gt;Stripped Recovery&lt;/b&gt;&lt;br&gt;Only attempts to                             recover the wallet&apos;s rootkey and chaincode</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12690"/>
        <source>&lt;b&gt;Bare Recovery&lt;/b&gt;&lt;br&gt;Attempts to recover all private key related data</source>
        <translation>&lt;b&gt;Récupération nue&lt;/b&gt;&lt;br&gt;Tente de récupérer toutes les données connexes aux clés privées</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12697"/>
        <source>&lt;b&gt;Full Recovery&lt;/b&gt;&lt;br&gt;Attempts to recover as much data as possible</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12703"/>
        <source>&lt;b&gt;Consistency Check&lt;/b&gt;&lt;br&gt;Checks wallet consistency. Works with both full and watch only&lt;br&gt; wallets. Unlocking of encrypted wallets is not mandatory</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12747"/>
        <source>Recover</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12748"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12759"/>
        <source>The entered path does not exist</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12772"/>
        <source>Wallet Recovery Tool</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12816"/>
        <source>Wallet files (*.wallet);; All files (*)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12823"/>
        <source>Recover Wallet</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>FeeSelectionDialog</name>
    <message>
        <location filename="FeeSelectUI.py" line="53"/>
        <source>Flat Fee (BTC)</source>
        <translation>Frais fixes (BTC)</translation>
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
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="124"/>
        <source>Adjust fee/byte for privacy</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="FeeSelectUI.py" line="145"/>
        <source>Select Fee Type</source>
        <translation>Sélectionner le type de frais</translation>
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
        <translation>

Pour les petites transactions, deux ou trois confirmations suffisent habituellement. Pour des transactions plus importantes, vous devriez attendre six confirmations avant d&apos;avoir confiance en la validité de la transaction.</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="280"/>
        <source>Bitcoins sent and received by the same wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="285"/>
        <source>You mined these Bitcoins!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="287"/>
        <source>Bitcoins sent</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="289"/>
        <source>Bitcoins received</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="292"/>
        <source>The net effect on the balance of this wallet &lt;b&gt;not including transaction fees.&lt;/b&gt;  You can change this behavior in the Armory preferences window.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="297"/>
        <source>The net effect on the balance of this wallet, including transaction fees.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="307"/>
        <source>Date</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="308"/>
        <source>Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="308"/>
        <source>Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="309"/>
        <source>Comments</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="311"/>
        <source>Amount</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="312"/>
        <source>Other Owner</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="313"/>
        <source>Wallet ID</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="314"/>
        <source>Tx Hash (LE)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="254"/>
        <source>Transaction confirmed!
(%1 confirmations)</source>
        <translation>La transaction a été confirmée !
(%1 confirmations)</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="259"/>
        <source>%1/120 confirmations</source>
        <translation>%1/120 confirmations</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="269"/>
        <source>%1/6 confirmations</source>
        <translation>%1/6 confirmations</translation>
    </message>
</context>
<context>
    <name>LetterButton</name>
    <message>
        <location filename="qtdialogs.py" line="347"/>
        <source>SPACE</source>
        <translation>ESPACE</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="352"/>
        <source>SHIFT</source>
        <translation>Maj</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="356"/>
        <source>DEL</source>
        <translation>Suppr</translation>
    </message>
</context>
<context>
    <name>LockboxDisplayModel</name>
    <message>
        <location filename="MultiSigModels.py" line="90"/>
        <source>Scanning: %1%%</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>LockboxSelectFrame</name>
    <message>
        <location filename="WalletFrames.py" line="28"/>
        <source>Invalid Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="28"/>
        <source> There was 
         an error loading the specified lockbox (%1).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="34"/>
        <source> &lt;font color=&quot;%1&quot; size=4&gt;&lt;b&gt;&lt;u&gt;Lockbox
         %2 (%3-of-%4)&lt;/u&gt;&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="39"/>
        <source>Lockbox ID:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="40"/>
        <source>Name:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="41"/>
        <source>Description:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="42"/>
        <source>Spendable BTC:</source>
        <translation>BTC disponibles :</translation>
    </message>
</context>
<context>
    <name>MessageSigningVerificationDialog</name>
    <message>
        <location filename="toolsDialogs.py" line="24"/>
        <source>Message Signing/Verification</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="32"/>
        <source>Sign Message</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="33"/>
        <source>Verify Bare Signature</source>
        <translation>Vérifier la signature nue</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="34"/>
        <source>Verify Signed Message Block</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="37"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
</context>
<context>
    <name>MessageSigningWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="63"/>
        <source>Sign with Address:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="72"/>
        <source>Message to sign:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="82"/>
        <source>Bare Signature (Bitcoin Core Compatible)</source>
        <translation>Signature nue (compatible avec Bitcoin Core)</translation>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="83"/>
        <source>Base64 Signature</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="84"/>
        <source>Clearsign Signature</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="92"/>
        <source>Message Signature:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="99"/>
        <source>Copy Signature</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="100"/>
        <source>Clear All</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="125"/>
        <source>Unlock Wallet to Import</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="127"/>
        <source>Wallet is Locked</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="127"/>
        <source>Cannot import private keys without unlocking wallet!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="168"/>
        <source>Non ASCII Text</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="168"/>
        <source>Message to sign must be ASCII</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="179"/>
        <source>Private Key Not Known</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="179"/>
        <source>The private key is not known for this address.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="173"/>
        <source>Invalid Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="173"/>
        <source>The signing address is invalid.</source>
        <translation type="unfinished"/>
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
        <translation>Copie miroir des porte-monnaie</translation>
    </message>
</context>
<context>
    <name>NewWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="351"/>
        <source>Wallet &amp;name:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="358"/>
        <source>Wallet &amp;description:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="363"/>
        <source>Add Manual &amp;Entropy</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="380"/>
        <source>Configure</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="384"/>
        <source>Advanced Options</source>
        <translation>Options avancées</translation>
    </message>
</context>
<context>
    <name>OutputBundle</name>
    <message>
        <location filename="MultiSigDialogs.py" line="2634"/>
        <source>Unrelated Multi-Spend</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2634"/>
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
        <location filename="MultiSigDialogs.py" line="2642"/>
        <source>Cannot Sign</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2642"/>
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
        <location filename="MultiSigDialogs.py" line="2680"/>
        <source>
               &lt;b&gt;&lt;u&gt;Spending:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2685"/>
        <source>
               &lt;b&gt;&lt;u&gt;Contributor:&lt;/u&gt; &lt;font color=&quot;%1&quot;&gt;%2&lt;/b&gt;%3&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2761"/>
        <source>[[Unknown Signer]]</source>
        <translation>[[Signataire inconnu]]</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2814"/>
        <source>
            &lt;b&gt;&lt;u&gt;Receiving:&lt;/u&gt;  &lt;font color=&quot;%1&quot;&gt;%2&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2862"/>
        <source>Import/Merge</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2865"/>
        <source>Broadcast</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2866"/>
        <source>Export</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2867"/>
        <source>Done</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2904"/>
        <source>Review and Sign</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2923"/>
        <source>Sign Lockbox</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2925"/>
        <source>Wallet is locked</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2925"/>
        <source>Cannot sign without unlocking wallet!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="2978"/>
        <source>Done!</source>
        <translation>Terminé !</translation>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3018"/>
        <source>
            from any online computer (you are currently offline)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3023"/>
        <source>
         &lt;font color=&quot;%1&quot;&gt;This transaction has enough signatures and
         can be broadcast %2&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3032"/>
        <source>
            &lt;font color=&quot;%1&quot;&gt;This transaction is incomplete.  You can
            add signatures then export and give to other parties or
            devices to sign.&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3047"/>
        <source>Export Signature Collector</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3048"/>
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
        <location filename="MultiSigDialogs.py" line="3065"/>
        <source>Import Signature Collector</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3066"/>
        <source>
         Load a multi-sig transaction for review, signing and/or broadcast.  
         If any of your loaded wallets can sign for any transaction inputs,
         you will be able to execute the signing for each one.  If your 
         signature completes the transaction, you can then broadcast it to
         finalize it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3097"/>
        <source>Invalid Signatures</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="3097"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Label</source>
        <translation>Étiquette</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Funding</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1493"/>
        <source>Fee</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>ReviewOfflineTxFrame</name>
    <message>
        <location filename="TxFrames.py" line="1147"/>
        <source>There is no security-sensitive information in this data below, so it is perfectly safe to copy-and-paste it into an email message, or save it to a borrowed USB key.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1152"/>
        <source>Save as file...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1154"/>
        <source>Save this data to a USB key or other device, to be transferred to a computer that contains the private keys for this wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1158"/>
        <source>Copy to clipboard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1163"/>
        <source>Copy the transaction data to the clipboard, so that it can be pasted into an email or a text document.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1167"/>
        <source>&lt;b&gt;Instructions for completing this transaction:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1225"/>
        <source>&lt;b&gt;Transaction Data&lt;/b&gt; <byte value="x9"/> (Unsigned ID: %1)</source>
        <translation>&lt;b&gt;Données transactionnelles&lt;/b&gt; &lt;byte value=&quot;x9&quot;/&gt; (ID non signé : %1)</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1232"/>
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
        <location filename="TxFrames.py" line="1251"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="425"/>
        <source>Step 2: Review Offline Transaction</source>
        <translation>Étape 2 : examiner la transaction hors ligne</translation>
    </message>
</context>
<context>
    <name>SelectWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="115"/>
        <source>No Wallets!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="115"/>
        <source>There are no wallets to select from.  Please create or import a wallet first.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="159"/>
        <source>Wallet ID:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="160"/>
        <source>Name:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="161"/>
        <source>Description:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="162"/>
        <source>Spendable BTC:</source>
        <translation>BTC disponibles :</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="300"/>
        <source>Source: All addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="199"/>
        <source>Coin Control</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="254"/>
        <source>Source: None selected</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="258"/>
        <source>Source: %1...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="260"/>
        <source>Source: %1 Outputs</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="300"/>
        <source>Source: 0 addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="321"/>
        <source>*Coin Control Subset*</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="328"/>
        <source>(available when online)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SendBitcoinsFrame</name>
    <message>
        <location filename="TxFrames.py" line="56"/>
        <source>Transaction fees go to users who contribute computing power to keep the Bitcoin network secure, and in return they get your transaction included in the blockchain faster.  &lt;b&gt;Most transactions do not require a fee&lt;/b&gt; but it is recommended anyway since it guarantees quick processing and helps the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="72"/>
        <source>Use an existing address for change</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="73"/>
        <source>Send change to first input address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="74"/>
        <source>Specify a change address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="75"/>
        <source>Change:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="84"/>
        <source>Remember for future transactions</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="87"/>
        <source>Most transactions end up with oversized inputs and Armory will send the change to the next address in this wallet.  You may change this behavior by checking this box.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="91"/>
        <source>Guarantees that no new addresses will be created to receive change. This reduces anonymity, but is useful if you created this wallet solely for managing imported addresses, and want to keep all funds within existing addresses.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="96"/>
        <source>You can specify any valid Bitcoin address for the change.  &lt;b&gt;NOTE:&lt;/b&gt; If the address you specify is not in this wallet, Armory will not be able to distinguish the outputs when it shows up in your ledger.  The change will look like a second recipient, and the total debit to your wallet will be equal to the amount you sent to the recipient &lt;b&gt;plus&lt;/b&gt; the change.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="103"/>
        <source>Check this box to create an unsigned transaction to be signed and/or broadcast later.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="106"/>
        <source>Create Unsigned</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="280"/>
        <source>Send!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="108"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="150"/>
        <source>Manually Enter &quot;bitcoin:&quot; Link</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="151"/>
        <source>
         Armory does not always succeed at registering itself to handle 
         URL links from webpages and email.  
         Click this button to copy a &quot;bitcoin:&quot; link directly into Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="216"/>
        <source>&lt;b&gt;Sending from Wallet:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="231"/>
        <source>Send Bitcoins</source>
        <translation>Envoyer des bitcoins</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="277"/>
        <source>Continue</source>
        <translation>Poursuivre</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="278"/>
        <source>Click to create an unsigned transaction!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="281"/>
        <source>Click to send bitcoins!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="871"/>
        <source>Invalid Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="509"/>
        <source>You have entered an invalid address. The error has been highlighted on the entrry screen.</source>
        <comment>You have entered %1 invalid addresses. The errors have been highlighted on the entry screen</comment>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="518"/>
        <source>Wrong Network!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="518"/>
        <source>
                     Address %1 is for the wrong network!  You are on the &lt;b&gt;%2&lt;/b&gt;
                     and the address you supplied is for the the &lt;b&gt;%3&lt;/b&gt;!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="535"/>
        <source>Zero Amount</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="535"/>
        <source>You cannot send 0 BTC to any recipients.  &lt;br&gt;Please enter a positive amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="541"/>
        <source>Negative Value</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="541"/>
        <source>You have specified a negative amount for recipient %1. &lt;br&gt;Only positive values are allowed!.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="546"/>
        <source>Too much precision</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="546"/>
        <source>Bitcoins can only be specified down to 8 decimal places. The smallest value that can be sent is  0.0000 0001 BTC. Please enter a new amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="552"/>
        <source>Missing recipient amount</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="552"/>
        <source>You did not specify an amount to send!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="556"/>
        <source>Invalid Value String</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="556"/>
        <source>The amount you specified to send to address %1 is invalid (%2).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="576"/>
        <source>Non-Standard to Spend</source>
        <translation type="unfinished"/>
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
        <location filename="TxFrames.py" line="578"/>
        <source>Excessive Fee</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="576"/>
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
        <location filename="TxFrames.py" line="591"/>
        <source>Insufficient Fee</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="590"/>
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
        <location filename="TxFrames.py" line="605"/>
        <source>Coin Selection Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="605"/>
        <source>
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="727"/>
        <source>Wallet is Locked</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="727"/>
        <source>Cannot sign transaction while your wallet is locked. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="871"/>
        <source>
                     You specified an invalid change address for this 
                     transcation.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="914"/>
        <source>Invalid Input</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="914"/>
        <source>Cannot compute the maximum amount because there is an error in the amount for recipient %1.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="923"/>
        <source>Insufficient funds</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="923"/>
        <source>You have specified more than your spendable balance to the other recipients and the transaction fee.  Therefore, the maximum amount for this recipient would actually be negative.</source>
        <translation>Les montants indiqués pour les autres destinataires ainsi que les frais de transaction dépassent le solde disponible. Par conséquent, le montant maximal pour ce destinataire devrait être négatif.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="965"/>
        <source>&lt;u&gt;&lt;/u&gt;Fills in the maximum spendable amount minus the amounts specified for other recipients and the transaction fee </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1047"/>
        <source>+ Recipient</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1049"/>
        <source>- Recipient</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="938"/>
        <source>Fills in the maximum spendable amount minus the amounts specified for other recipients and the transaction fee </source>
        <translation>Saisit le montant disponible maximal, moins les montants  indiqués pour les autres destinataires ainsi que les frais de transaction</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="507"/>
        <source>You have entered an invalid address. The error has been highlighted on the entry screen.</source>
        <comment>You have entered %1 invalid addresses. The errors have been highlighted on the entry screen</comment>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="56"/>
        <source>Transaction fees go to users who contribute computing power to keep the Bitcoin network secure, and in return they get your transaction included in the blockchain faster.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="578"/>
        <source>
               Your transaction comes with a fee rate of &lt;b&gt;%1 satoshis per byte&lt;/b&gt;.
               &lt;/br&gt;&lt;/br&gt; 
               This is much higher than the median fee rate of &lt;b&gt;%2 satoshi/Byte&lt;/b&gt;.
               &lt;br&gt;&lt;br&gt;
               Are you &lt;i&gt;absolutely sure&lt;/i&gt; that you want to send with this
               fee? If you do not want to proceed with this fee rate, click &quot;No&quot;.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="591"/>
        <source>
               Your transaction comes with a fee rate of &lt;b&gt;%1 satoshi/Byte&lt;/b&gt;.
               &lt;/br&gt;&lt;br&gt; 
               This is much lower than the median fee rate of &lt;b&gt;%2 satoshi/Byte&lt;/b&gt;.
               &lt;br&gt;&lt;br&gt;
               Are you &lt;i&gt;absolutely sure&lt;/i&gt; that you want to send with this
               fee? If you do not want to proceed with this fee rate, click &quot;No&quot;.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SentToAddrBookModel</name>
    <message>
        <location filename="armorymodels.py" line="1408"/>
        <source>Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1409"/>
        <source>Ownership</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1410"/>
        <source>Times Used</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1411"/>
        <source>Comment</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SetPassphraseFrame</name>
    <message>
        <location filename="WalletFrames.py" line="561"/>
        <source>Please enter a passphrase for wallet encryption.

A good passphrase consists of at least 10 or more
random letters, or 6 or more random words.
</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="566"/>
        <source>New Passphrase:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="571"/>
        <source>Again:</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="606"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is non-ASCII!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="610"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases do not match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="614"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrase is too short!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="618"/>
        <source>&lt;font color=%1&gt;&lt;b&gt;Passphrases match!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>SignBroadcastOfflineTxFrame</name>
    <message>
        <location filename="TxFrames.py" line="1312"/>
        <source>Sign</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1313"/>
        <source>Broadcast</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1314"/>
        <source>Save file...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1315"/>
        <source>Load file...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1316"/>
        <source>Copy Text</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1317"/>
        <source>Copy Raw Tx (Hex)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1336"/>
        <source>Signature is Invalid!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1347"/>
        <source>This is wallet from which the offline transaction spends bitcoins</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1354"/>
        <source>The name of the wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1355"/>
        <source>&lt;b&gt;Wallet Label:&lt;/b&gt;</source>
        <translation>&lt;b&gt;Étiquette de porte-monnaie :&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1365"/>
        <source>&lt;b&gt;Pre-Broadcast ID:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1370"/>
        <source>Net effect on this wallet&apos;s balance</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1372"/>
        <source>&lt;b&gt;Transaction Amount:&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1375"/>
        <source>Click here for more&lt;br&gt; information about &lt;br&gt;this transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1446"/>
        <source>Inconsistent Data!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1446"/>
        <source>This transaction contains inconsistent information.  This is probably not your fault...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1452"/>
        <source>Wrong Network!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1452"/>
        <source>This transaction is actually for a different network!  Did you load the correct transaction?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1468"/>
        <source>No connection to Bitcoin network!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1479"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Unrecognized!&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1489"/>
        <source>Offline Warning</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1489"/>
        <source>&lt;b&gt;Please review your transaction carefully before signing and broadcasting it!&lt;/b&gt;  The extra security of using offline wallets is lost if you do not confirm the transaction is correct!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1495"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Unsigned&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1499"/>
        <source>&lt;b&gt;&lt;font color=&quot;red&quot;&gt;Bad Signature!&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1503"/>
        <source>&lt;b&gt;&lt;font color=&quot;green&quot;&gt;All Signatures Valid!&lt;/font&gt;&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1522"/>
        <source>Multiple Input Wallets</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1522"/>
        <source>Somehow, you have obtained a transaction that actually pulls from more than one wallet.  The support for handling multi-wallet signatures is not currently implemented (this also could have happened if you imported the same private key into two different wallets).</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1530"/>
        <source>Unrelated Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1530"/>
        <source>This transaction appears to have no relationship to any of the wallets stored on this computer.  Did you load the correct transaction?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1590"/>
        <source>[[ Unrelated ]]</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1610"/>
        <source>Invalid Transaction</source>
        <translation>Transaction invalide</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1610"/>
        <source>Transaction data is invalid and cannot be shown!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1623"/>
        <source>Cannot Sign</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1623"/>
        <source>This transaction is not relevant to any of your wallets.Did you load the correct transaction?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1629"/>
        <source>Not Signable</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1629"/>
        <source>This is not a valid transaction, and thus it cannot be signed. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1634"/>
        <source>Already Signed</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1634"/>
        <source>This transaction has already been signed!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1640"/>
        <source>No Private Keys!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1640"/>
        <source>This transaction refers one of your wallets, but that wallet is a watching-only wallet.  Therefore, private keys are not available to sign this transaction.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1663"/>
        <source>Missing Change</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1663"/>
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
        <location filename="TxFrames.py" line="1683"/>
        <source>Send Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1690"/>
        <source>Wallet is Locked</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1690"/>
        <source>Cannot sign transaction while your wallet is locked. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1716"/>
        <source>No Internet!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1736"/>
        <source>Armory lost its connection to , and cannot broadcast any transactions until it is reconnected. Please verify that  (or bitcoind) is open and synchronized with the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1716"/>
        <source>You do not currently have a connection to the Bitcoin network. If this does not seem correct, verify that  is open and synchronized with the network.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1727"/>
        <source>Signature Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1727"/>
        <source>
            Not all signatures are valid.  This transaction
            cannot be broadcast.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1731"/>
        <source>Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1731"/>
        <source>
            There was an error processing this transaction, for reasons 
            that are probably not your fault...</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1757"/>
        <source>File Remove Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1757"/>
        <source>The file could not be deleted.  If you want to delete it, please do so manually.  The file was loaded from: &lt;br&gt;&lt;br&gt;%1: </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1795"/>
        <source>Formatting Error</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1795"/>
        <source>The transaction data was not in a format recognized by Armory.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1787"/>
        <source>Transaction Saved!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1787"/>
        <source>Your transaction has been saved to the following location:

%1

It can now be broadcast from any computer running Armory in online mode.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1826"/>
        <source>Load Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1848"/>
        <source>&lt;i&gt;Copied!&lt;/i&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="TxFrames.py" line="1297"/>
        <source>Copy or load a transaction from file into the text box below.  If the transaction is unsigned and you have the correct wallet, you will have the opportunity to sign it.  If it is already signed you will have the opportunity to broadcast it to the Bitcoin network to make it final.</source>
        <translation>Copiez ou chargez une transaction d&apos;un fichier dans la boîte de texte ci-dessous. Si la transaction n&apos;est pas signée et que vous avez le bon porte-monnaie, vous aurez l&apos;occasion de la signer. Si elle l&apos;est déjà, vous aurez l&apos;occasion de la diffuser sur le réseau Bitcoin pour la finaliser.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1360"/>
        <source>A unique string that identifies an &lt;i&gt;unsigned&lt;/i&gt; transaction.  This is different than the ID that the transaction will have when it is finally broadcast, because the broadcast ID cannot be calculated without all the signatures</source>
        <translation>Une chaîne unique qui identifie une transaction &lt;i&gt;non signée&lt;/i&gt;. Elle est différente de l&apos;ID que la transaction aura quand elle sera finalement diffusée, car l&apos;ID de diffusion ne peut pas être calculé sans toutes les signatures.</translation>
    </message>
    <message>
        <location filename="TxFrames.py" line="1709"/>
        <source>Armory lost its connection to Bitcoin Core, and cannot broadcast any transactions until it is reconnected. Please verify that Bitcoin Core (or bitcoind) is open and synchronized with the network.</source>
        <translation>Armory a perdu sa connexion à Bitcoin Core et ne pourra diffuser aucune transaction tant que la connexion ne sera pas rétablie. Veuillez vérifier que Bitcoin Core (ou bitcoind) est ouvert et synchronisé avec le réseau.</translation>
    </message>
</context>
<context>
    <name>SignBroadcastOfflineTxPage</name>
    <message>
        <location filename="Wizards.py" line="430"/>
        <source>Sign/Broadcast Offline Transaction</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="432"/>
        <source>Step 3: Sign/Broadcast Offline Transaction</source>
        <translation>Étape 3 : signer ou diffuser la transaction hors ligne</translation>
    </message>
</context>
<context>
    <name>SignatureVerificationWidget</name>
    <message>
        <location filename="toolsDialogs.py" line="200"/>
        <source>Verify Signature</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="201"/>
        <source>Clear All</source>
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="toolsDialogs.py" line="320"/>
        <source>Message:</source>
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1217"/>
        <source>Sender</source>
        <translation>Expéditeur</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1218"/>
        <source>Amount</source>
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1311"/>
        <source>Recipient</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1312"/>
        <source>Amount</source>
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="355"/>
        <source>Send!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="369"/>
        <source>Next</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>VerifyPassphraseFrame</name>
    <message>
        <location filename="WalletFrames.py" line="633"/>
        <source>&lt;font color=&quot;red&quot;&gt;&lt;b&gt;!!! DO NOT FORGET YOUR PASSPHRASE !!!&lt;/b&gt;&lt;/font&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="636"/>
        <source>&lt;b&gt;No one can help you recover you bitcoins if you forget the passphrase and don&apos;t have a paper backup!&lt;/b&gt; Your wallet and any &lt;u&gt;digital&lt;/u&gt; backups are useless if you forget it.  &lt;br&gt;&lt;br&gt;A &lt;u&gt;paper&lt;/u&gt; backup protects your wallet forever, against hard-drive loss and losing your passphrase.  It also protects you from theft, if the wallet was encrypted and the paper backup was not stolen with it.  Please make a paper backup and keep it in a safe place.&lt;br&gt;&lt;br&gt;Please enter your passphrase a third time to indicate that you are aware of the risks of losing your passphrase!&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>VerifyPassphrasePage</name>
    <message>
        <location filename="Wizards.py" line="297"/>
        <source>Invalid Passphrase</source>
        <translation>Phrase de passe invalide</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="297"/>
        <source>You entered your confirmation passphrase incorrectly!</source>
        <translation type="unfinished"/>
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
        <translation>Cette adresse a été créée par Armory pour recevoir de la monnaie-rendue-à-soi d&apos;une transaction surdimensionnée</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="1061"/>
        <source>Address</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1062"/>
        <source>Comment</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1063"/>
        <source>#Tx</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="armorymodels.py" line="1064"/>
        <source>Balance</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>WalletBackupFrame</name>
    <message>
        <location filename="WalletFrames.py" line="678"/>
        <source>&lt;b&gt;Backup Options&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="679"/>
        <source>
         Armory wallets only need to be backed up &lt;u&gt;one time, ever.&lt;/u&gt;
         The backup is good no matter how many addresses you use. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="685"/>
        <source>Printable Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="687"/>
        <source>Single-Sheet (Recommended)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="689"/>
        <source>Fragmented Backup (M-of-N)</source>
        <translation>Sauvegarde fragmentée (M de N)</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="692"/>
        <source>Digital Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="694"/>
        <source>Unencrypted</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="696"/>
        <source>Encrypted</source>
        <translation>Chiffré</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1034"/>
        <source>Export Key Lists</source>
        <translation>Exporter les listes de clés</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="766"/>
        <source>
         Every time you click &quot;Receive Bitcoins,&quot; a new address is generated.
         All of these addresses are generated from a single seed value, which
         is included in all backups.   Therefore, all addresses that you have
         generated so far &lt;b&gt;and&lt;/b&gt; will ever be generated with this wallet, 
         are protected by this backup! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="773"/>
        <source>
         &lt;i&gt;This wallet &lt;u&gt;does not&lt;/u&gt; currently have any imported
         addresses, so you can safely ignore this feature!&lt;/i&gt;
         When imported addresses are present, backups only protects those
         imported before the backup was made.  You must replace that
         backup if you import more addresses! </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="780"/>
        <source>
         Lost/forgotten passphrases are, &lt;b&gt;by far&lt;/b&gt;, the most common
         reason for users losing bitcoins.  It is critical you have
         at least one backup that works if you forget your wallet
         passphrase. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="786"/>
        <source>
         USB drives and CD/DVD disks are not intended for long-term storage.
         They will &lt;i&gt;probably&lt;/i&gt; last many years, but not guaranteed
         even for 3-5 years.   On the other hand, printed text on paper will
         last many decades, and useful even when thoroughly faded. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="792"/>
        <source>
         The ability to look at a backup and determine if
         it is still usable.   If a digital backup is stored in a safe
         deposit box, you have no way to verify its integrity unless
         you take a secure computer/device with you.  A simple glance at
         a paper backup is enough to verify that it is still intact. </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="799"/>
        <source>
         If multiple pieces/fragments are required to restore this wallet.
         For instance, encrypted backups require the backup
         &lt;b&gt;and&lt;/b&gt; the passphrase.  This feature is only needed for those
         concerned about physical security, not just online security.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="807"/>
        <source>Protects All Future Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="893"/>
        <source>Protects Imported Addresses</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="809"/>
        <source>Forgotten Passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="810"/>
        <source>Long-term Durability</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="811"/>
        <source>Visual Integrity</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="812"/>
        <source>Multi-Point Protection</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="840"/>
        <source>Create Backup</source>
        <translation type="unfinished"/>
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
        <location filename="WalletFrames.py" line="883"/>
        <source>
         &lt;b&gt;Backup Options for Wallet &quot;%1&quot; (%2)&lt;/b&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="896"/>
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
        <location filename="WalletFrames.py" line="907"/>
        <source>
               Digital backups can be saved to an external hard-drive or
               USB removable media.  It is recommended you make a few
               copies to protect against &quot;bit rot&quot; (degradation). &lt;br&gt;&lt;br&gt;</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="911"/>
        <source>
               &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt; Do not save an unencrypted digital
               backup to your primary hard drive!&lt;/b&gt;
               Please save it &lt;i&gt;directly&lt;/i&gt; to the backup device.
               Deleting the file does not guarantee the data is actually
               gone!  </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="917"/>
        <source>
               &lt;b&gt;&lt;u&gt;IMPORTANT:&lt;/u&gt; It is critical that you have at least
               one unencrypted backup!&lt;/b&gt;  Without it, your bitcoins will
               be lost forever if you forget your passphrase!  This is &lt;b&gt;
               by far&lt;/b&gt; the most common reason users lose coins!  Having
               at least one paper backup is recommended.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="923"/>
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
        <location filename="WalletFrames.py" line="937"/>
        <source>Single-Sheet Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="946"/>
        <source>Fragmented Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="955"/>
        <source>Unencrypted Digital Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="964"/>
        <source>Encrypted Digital Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1013"/>
        <source>Create Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1022"/>
        <source>Create Digital Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1045"/>
        <source>Unlocking Wallet</source>
        <translation>Déverrouillage du porte-monnaie</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1072"/>
        <source>Unlock Failed</source>
        <translation>Échec de déverrouillage</translation>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1066"/>
        <source>
                     Wallet was not be unlocked.  The public keys and addresses
                     will still be shown, but private keys will not be available
                     unless you reopen the dialog with the correct passphrase.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="1072"/>
        <source>
                     &apos;Wallet could not be unlocked to display individual keys.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="WalletFrames.py" line="875"/>
        <source>
            When imported addresses are present, backups only protects those
            imported before the backup was made!  You must replace that
            backup if you import more addresses!
            &lt;i&gt;Your wallet &lt;u&gt;does&lt;/u&gt; contain imported addresses&lt;/i&gt;.</source>
        <translation type="unfinished"/>
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
        <translation>Vérification des importations pour le porte-monnaie %s</translation>
    </message>
</context>
<context>
    <name>WalletCreationPage</name>
    <message>
        <location filename="Wizards.py" line="247"/>
        <source>Invalid Target Compute Time</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="247"/>
        <source>You entered Target Compute Time incorrectly.

Enter: &lt;Number&gt; (ms, s)</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="251"/>
        <source>Invalid Max Memory Usage</source>
        <translation>L&apos;utilisation maximale de la mémoire est invalide</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="251"/>
        <source>You entered Max Memory Usag incorrectly.

nter: &lt;Number&gt; (kb, mb)</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>WalletWizard</name>
    <message>
        <location filename="Wizards.py" line="80"/>
        <source>Wallet Creation Wizard</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="148"/>
        <source>Wallet Backup Warning</source>
        <translation type="unfinished"/>
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
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>WizardCreateWatchingOnlyWalletFrame</name>
    <message>
        <location filename="WalletFrames.py" line="1090"/>
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
        <location filename="qtdialogs.py" line="10956"/>
        <source>Invalid Code</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10956"/>
        <source>
            You didn't enter a full SecurePrintâ¢ code.  This
            code is needed to decrypt your backup file.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10967"/>
        <source>Bad SecurePrintâ¢ Code</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10961"/>
        <source>
            The SecurePrintâ¢ code you entered has an error
            in it.  Note that the code is case-sensitive.  Please verify
            you entered it correctly and try again.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="10967"/>
        <source>
         The SecurePrintâ¢ code you entered has unrecognized characters
         in it.  %1 Only the following characters are allowed: %2</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>dlgChangeOwner</name>
    <message>
        <location filename="qtdialogs.py" line="1980"/>
        <source>This wallet is mine</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="1983"/>
        <source>
               The funds in this wallet are currently identified as
               belonging to &lt;b&gt;&lt;i&gt;you&lt;/i&gt;&lt;/b&gt;.  As such, any funds
               available to this wallet will be included in the total
               balance displayed on the main screen.  


               If you do not actually own this wallet, or do not wish
               for its funds to be considered part of your balance,
               uncheck the box below.  Optionally, you can include the
               name of the person or organization that does own it.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2003"/>
        <source>
               The funds in this wallet are currently identified as
               belonging to &lt;i&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/i&gt;.  If these funds are actually
               yours, and you would like the funds included in your balance in
               the main window, please check the box below.

</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2012"/>
        <source>
               You might choose this option if you keep a full
               wallet on a non-internet-connected computer, and use this
               watching-only wallet on this computer to generate addresses
               and monitor incoming transactions.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2023"/>
        <source>Wallet owner (optional):</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2031"/>
        <source>Set Wallet Owner</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>dlgWarn</name>
    <message>
        <location filename="qtdefines.py" line="443"/>
        <source>&amp;Yes</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="444"/>
        <source>&amp;No</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="452"/>
        <source>&amp;Cancel</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="454"/>
        <source>&amp;OK</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="505"/>
        <source>Do not show this message again</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="508"/>
        <source>Do not ask again</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdefines.py" line="511"/>
        <source>Do not show this warning again</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="qtdialogs.py" line="2038"/>
        <source>Careful!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2038"/>
        <source>Armory is not online yet, and will eventually need to be online toaccess any funds sent to your wallet.  Please &lt;u&gt;&lt;b&gt;do not&lt;/b&gt;&lt;/u&gt;receive Bitcoins to your Armory wallets until you have successfullygotten online &lt;i&gt;at least one time&lt;/i&gt;.&lt;br&gt;&lt;br&gt;Armory is still beta software, and some users report difficultyever getting online.&lt;br&gt;&lt;br&gt;Do you wish to continue?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2038"/>
        <source>Armory is not online yet, and will eventually need to be online to access any funds sent to your wallet.  Please &lt;u&gt;&lt;b&gt;do not&lt;/b&gt;&lt;/u&gt; receive Bitcoins to your Armory wallets until you have successfully gotten online &lt;i&gt;at least one time&lt;/i&gt;. &lt;br&gt;&lt;br&gt; Armory is still beta software, and some users report difficulty ever getting online. &lt;br&gt;&lt;br&gt; Do you wish to continue? </source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>parent</name>
    <message>
        <location filename="qtdefines.py" line="118"/>
        <source>Standard User</source>
        <translation>Utilisateur normal</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="120"/>
        <source>Advanced User</source>
        <translation>Utilisateur avancé</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="122"/>
        <source>Expert User</source>
        <translation>Utilisateur expert</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2071"/>
        <source>This is not your wallet!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2057"/>
        <source>You are getting an address for a wallet thatdoes not appear to belong to you.  Any money sent to thisaddress will not appear in your total balance, and cannotbe spent from this computer.&lt;br&gt;&lt;br&gt;If this is actually your wallet (perhaps you maintain the fullwallet on a separate computer), then please change the&quot;Belongs To&quot; field in the wallet-properties for this wallet.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2071"/>
        <source>Do not show this warning again</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2071"/>
        <source>You are getting an address for a wallet that you have specified belongs to you, but you cannot actually spend the funds from this computer.  This is usually the case when you keep the full wallet on a separate computer for security purposes.&lt;br&gt;&lt;br&gt;If this does not sound right, then please do not use the following address.  Instead, change the wallet properties &quot;Belongs To&quot; field to specify that this wallet is not actually yours.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7030"/>
        <source>Unlock Paper Backup</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7033"/>
        <source>Unlock Failed</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7033"/>
        <source>
            The wallet could not be unlocked.  Please try again with
            the correct unlock passphrase.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7043"/>
        <source>
         If the backup was printed with SecurePrintâ¢, please
         make sure you wrote the SecurePrintâ¢ code on the
         printed sheet of paper. Note that the code &lt;b&gt;&lt;u&gt;is&lt;/u&gt;&lt;/b&gt;
         case-sensitive!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7050"/>
        <source>
         If the backup was created with SecurePrintâ¢, please
         make sure you wrote the SecurePrintâ¢ code on each
         fragment (or stored with each file fragment). The code is the
         same for all fragments.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7056"/>
        <source>Verify Your Backup!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7056"/>
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
        <location filename="qtdialogs.py" line="7192"/>
        <source>Bad Public Key</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7192"/>
        <source>Public key data was not recognized</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7201"/>
        <source>Bad Signature</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7201"/>
        <source>Signature data is malformed!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7209"/>
        <source>Address Mismatch</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="7209"/>
        <source>!!! The address included in the signature block does not
         match the supplied public key!  This should never happen,
         and may in fact be an attempt to mislead you !!!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8216"/>
        <source>Select</source>
        <translation>Sélectionner</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8222"/>
        <source>No wallets!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8222"/>
        <source>You have no wallets so
            there is no address book to display.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="8233"/>
        <source>Select from Address Book</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12490"/>
        <source>Recovery Test</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12490"/>
        <source>
         From the data you entered, Armory calculated the following
         wallet ID: &lt;font color=&quot;blue&quot;&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/font&gt;
         &lt;br&gt;&lt;br&gt;
         Does this match the wallet ID on the backup you are
         testing?</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12518"/>
        <source>Bad Backup!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12498"/>
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
        <location filename="qtdialogs.py" line="12531"/>
        <source>Backup is Good!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="12508"/>
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
        <location filename="qtdialogs.py" line="12518"/>
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
        <location filename="qtdialogs.py" line="13737"/>
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
        <location filename="qtdialogs.py" line="13761"/>
        <source>Test Your Backup!</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="qtdialogs.py" line="13761"/>
        <source>
      </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="615"/>
        <source>Export Lockbox Definition</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="MultiSigDialogs.py" line="616"/>
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
        <location filename="qtdialogs.py" line="12531"/>
        <source>Your backup works! &lt;br&gt;&lt;br&gt; The wallet ID computed from the data you entered matches the expected ID.  This confirms that the backup produces the same sequence of private keys as the original wallet! &lt;br&gt;&lt;br&gt; Computed wallet ID: %1 &lt;br&gt; Expected wallet ID: %2 &lt;br&gt; &lt;br&gt;</source>
        <translation>Votre sauvegarde fonctionne ! &lt;br&gt;&lt;br&gt; L&apos;ID de porte-monnaie calculé à partir des données que vous avez saisies correspond à l&apos;ID attendu. Cela confirme que la sauvegarde produit la même séquence de clés privées que le porte-monnaie original ! &lt;br&gt;&lt;br&gt; ID de porte-monnaie calculé : %1 &lt;br&gt; ID de porte-monnaie attendu : %2 &lt;br&gt; &lt;br&gt;</translation>
    </message>
    <message>
        <location filename="qtdialogs.py" line="2057"/>
        <source>You are getting an address for a wallet that does not appear to belong to you.  Any money sent to this address will not appear in your total balance, and cannot be spent from this computer. &lt;br&gt;&lt;br&gt; If this is actually your wallet (perhaps you maintain the full wallet on a separate computer), then please change the &quot;Belongs To&quot; field in the wallet-properties for this wallet.</source>
        <translation type="unfinished"/>
    </message>
</context>
<context>
    <name>self.main</name>
    <message>
        <location filename="armorymodels.py" line="496"/>
        <source>&lt;a href=edtBlock&gt;Block:&lt;/a&gt;</source>
        <translation>&lt;a href=edtBlock&gt;Bloc :&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="502"/>
        <source>&lt;a href=edtDate&gt;Date:&lt;/a&gt;</source>
        <translation>&lt;a href=edtDate&gt;Date :&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="armorymodels.py" line="508"/>
        <source>&lt;a href=goToTop&gt;Top&lt;/a&gt;</source>
        <translation>&lt;a href=goToTop&gt;Haut&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="128"/>
        <source>Address Type: </source>
        <translation>Type d&apos;adresse :</translation>
    </message>
    <message>
        <location filename="AddressTypeSelectDialog.py" line="142"/>
        <source>&lt;u&gt;&lt;font color=&apos;blue&apos;&gt;%1&lt;/font&gt;&lt;/u&gt;</source>
        <translation>&lt;u&gt;&lt;font color=&apos;blue&apos;&gt;%1&lt;/font&gt;&lt;/u&gt;</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="463"/>
        <source>Unspent Outputs</source>
        <translation>Sorties non dépensées</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="464"/>
        <source>RBF Eligible</source>
        <translation>Éligible RBF</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="465"/>
        <source>CPFP Outputs</source>
        <translation>Sorties CPFP</translation>
    </message>
</context>
<context>
    <name>self.parent_qobj</name>
    <message>
        <location filename="TreeViewGUI.py" line="352"/>
        <source>Used Addresses</source>
        <translation>Adresses utilisées</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="353"/>
        <source>Change Addresses</source>
        <translation>Changer les adresses</translation>
    </message>
    <message>
        <location filename="TreeViewGUI.py" line="354"/>
        <source>Unused Addresses</source>
        <translation>Adresses inutilisées</translation>
    </message>
</context>
<context>
    <name>wizard</name>
    <message>
        <location filename="Wizards.py" line="218"/>
        <source>Shuffle a deck of cards</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="221"/>
        <source>Step 1: Add Manual Entropy</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="222"/>
        <source>
            Use a deck of cards to get a new random number for your wallet.
            </source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="238"/>
        <source>Step 1: Create Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="239"/>
        <source>
            Create a new wallet for managing your funds.
            The name and description can be changed at any time.</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="267"/>
        <source>Set Passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="270"/>
        <source>Step 2: Set Passphrase</source>
        <translation>Étape 2 : définir la phrase de passe</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="285"/>
        <source>Verify Passphrase</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="289"/>
        <source>Step 3: Verify Passphrase</source>
        <translation>Étape 3 : vérifier la phrase de passe</translation>
    </message>
    <message>
        <location filename="Wizards.py" line="306"/>
        <source>Backup Wallet</source>
        <translation type="unfinished"/>
    </message>
    <message>
        <location filename="Wizards.py" line="310"/>
        <source>Step 4: Backup Wallet</source>
        <translation>Étape 4 : sauvegarder le porte-monnaie</translation>
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
        <translation>Créer une transaction</translation>
    </message>
</context>
<context>
    <name>wndw</name>
    <message>
        <location filename="qtdefines.py" line="181"/>
        <source>Offline</source>
        <translation>Hors ligne</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="183"/>
        <source>Watching-Only</source>
        <translation>Regarder-seulement</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="185"/>
        <source>Encrypted</source>
        <translation>Chiffré</translation>
    </message>
    <message>
        <location filename="qtdefines.py" line="187"/>
        <source>No Encryption</source>
        <translation>Pas de chiffrement</translation>
    </message>
</context>
</TS>