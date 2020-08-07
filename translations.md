# Translations

## Writing strings for translating

Each string that needs to be translated needs to be enclosed in`<qobj>.tr()`. `<qobj>` must be a class which extends QObject. Typically this will be `self`. 

For strings that need cases for singular and plural forms, the string should contain a generic string that can work with singular and plural in English. When enlosing it in `tr()`, the format of that call must be like `self.tr("String", "", <num>)` where `<num>` is the number which would be causing the necessity for singular and plural forms. `<num>` will also be substitued for the `%n` format specifier in the string if you need to use that number in the string somewhere.

In order to create the plural forms for English, you must use Qt Linguist and create an "English translation" for the strings.

If the string is a formatted string with variables that are added into the string for the display, then following the `tr()` there needs to be `.args(<vars>)` where <vars> are the variables that are being inserted into the string. For formatting the string, use `%1, %2, ...` format specifiers where each number in the specifier points to an insertion in `.args()` in the number order.

### Examples

Normal string translation

    self.tr("This string needs to be translated")

Translation with string formatting

    self.tr("Your first string is %1. The second string is %2").arg(str1, str2)

Translation string with plurals

    self.tr("There are %n string(s) to display", "", len(strings))

## Translating strings

To translate strings, visit the [Transifex page](https://www.transifex.com/bitcoin-armory/bitcoin-armory-software/)

## Update Transifex translations

Transifex is set to automatically pull the english resource file, `lang/armory_en.ts`. In order to update this file, use the following command:

    pylupdate4 ArmoryQt.py armorymodels.py qtdefines.py qtdialogs.py ui/MultiSigDialogs.py ui/MultiSigModels.py ui/TxFrames.py ui/WalletFrames.py ui/Wizards.py ui/toolsDialogs.py ui/AddressTypeSelectDialog.py ui/CoinControlUI.py ui/FeeSelectUI.py ui/TreeViewGUI.py ui/WalletMirrorDialog.py -ts lang/armory_en.ts

If a new file has been added that has strings that require translating, add it to the above command in the list of files containing strings for translation (after `ui/WalletMirrorDialog.py` and before `-ts`).

## Pull down translations from Transifex

The translations that are being used are those that have 5% or greater strings translated. These can be downloaded manually from Transifex's resource page for all languages and clicking on each language that will be downloaded. Then click the link for `Download for Use` and save that file as `lang/armory_<code>.ts` where `<code>` is the two letter ISO 639-1 language code.

This can also be done automatically if you have [installed the Transifex client](https://docs.transifex.com/client/installing-the-client). Once the client is installed, run the following command:

    tx pull -f

## Compiling translations for use

The command for compiling the translations for use by Armory is included in the Makefile. It will be done automatically when `make` is run to build Armory.
