import sys
sys.argv.append('--nologging')
from sys import argv, path
import os

from armoryengine import PyBtcWallet
from utilities.ArmoryUtils import RightNow
from CppBlockUtils import SecureBinaryData


path.append('..')
path.append('/usr/bin/armory')

if len(argv)<2:
   print '***USAGE: '
   print '    %s /path/to/wallet/file.wallet' % argv[0]
   exit(0)

walletPath = argv[1]

if not os.path.exists(walletPath):
   print 'Wallet does not exist:'
   print '  ', walletPath
   exit(0)


myEncryptedWlt = PyBtcWallet().readWalletFile(walletPath)


def printMaxResultsErrorAndExit():
   print "To many passwords to try. Please reduce the scope of your search."
   exit(1)

def all_casings(input_string, maxResults):
   """
   A useful method for producing a list of all casings of a given string
   """
   out = [] 
   if input_string:
      first = input_string[:1]
      if first.lower() == first.upper():
         for sub_casing in all_casings(input_string[1:], maxResults):
            out.append( first + sub_casing)
      else:
         for sub_casing in all_casings(input_string[1:], maxResults/2 + 1):
            out.append( first.lower() + sub_casing)
            out.append( first.upper() + sub_casing)
   else:
      out = ['']
   if len(out) > maxResults:
      printMaxResultsErrorAndExit()
   return out

def generateRandomStrings(minLen, maxLen, charList, maxResults):
   result = []
   if maxResults > len(charList):
      if maxLen > 1:
         postfixList = generateRandomStrings(minLen - 1, maxLen - 1, charList, maxResults/len(charList) + 1)
         result.extend([prefix + postfix for prefix in charList for postfix in postfixList])
      if minLen < 2:
         result.extend(charList[:maxResults])
   else :
      printMaxResultsErrorAndExit()
   return result
   

def createPwdList(charList, knownWords, minEndingChars, maxEndingChars, maxResults):
   pwdList = []
   prefixList = []
   prefix = ''
   if (maxResults > 0):
      for i in range(len(knownWords)):
         myWord = knownWords[i][0]
         minOffset = knownWords[i][1]
         maxOffset = knownWords[i][2]
         caseKnown = knownWords[i][3]
         if maxOffset == 0:
            if caseKnown:
               prefix += myWord
            else:
               allCasingsList = all_casings(myWord, maxResults)
               if len(allCasingsList) > 1:
                  prefixList = [prefix + case for case in allCasingsList]
               elif len(allCasingsList) == 1:
                  prefix += prefixList[0]
         else:
            prefixList = [prefix + postfix for postfix in generateRandomStrings(minOffset, maxOffset, charList, maxResults)]
            knownWords[i][1] = 0 # remove the offsets since those are handled now
            knownWords[i][2] = 0 
            i -= 1    # back up i to redo this Known word
         if len(prefixList) > 0:
            postfixList = createPwdList(charList, knownWords[i+1:], minEndingChars, maxEndingChars, maxResults/len(prefixList) + 1)
            pwdList = [prefix + postfix for prefix in prefixList for postfix in postfixList]
            break
      if len(pwdList) == 0:
         if maxEndingChars > 0:
            postfixList = generateRandomStrings(minEndingChars, maxEndingChars, charList, maxResults)
            pwdList = [prefix + postfix for postfix in postfixList]
         else:
            pwdList = [prefix] 
   if maxResults== 0 or len(pwdList) > maxResults:
      printMaxResultsErrorAndExit()
   return pwdList

def searchForPassword(passwordList):
   totalTest = len(passwordList)
   startTime = RightNow()
   found = False
   for i,p in enumerate(passwordList):
      isValid = myEncryptedWlt.verifyPassphrase( SecureBinaryData(p) ) 
         
      if isValid:
         # If the passphrase was wrong, it would error out, and not continue
         print 'Passphrase found!'
         print ''
         print '\t', p
         print ''
         print 'Thanks for using this script.  If you recovered coins because of it, '
         print 'please consider donating :) '
         print '   1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'
         print ''
         found = True
         open('FOUND_PASSWORD.txt','w').write(p)
         break
      elif i%100==0:
            telapsed = (RightNow() - startTime)/3600.
            print ('%d/%d passphrases tested... (%0.1f hours so far)'%(i,totalTest,telapsed)).rjust(40)
      print p,
      if i % 10 == 9:
         print
   
   if not found:
      print ''
      
      print 'Script finished!'
      print 'Sorry, none of the provided passphrases were correct :('
      print ''


# Enter 1 for each character to exclude when guessing unspecified characters
EXCLUDED_CHARS = \
[1, #     32;   space
1,  # !   33;   exclamation mark
1,  # "   34;   quotation mark
1,  # #   35;   number sign
1,  # $   36;   dollar sign
1,  # %   37;   percent sign
1,  # &   38;   ampersand
1,  # '   39;   apostrophe
1,  # (   40;   left parenthesis
1,  # )   41;   right parenthesis
1,  # *   42;   asterisk
1,  # +   43;   plus sign
1,  # ,   44;   comma
1,  # -   45;   hyphen
1,  # .   46;   period
1,  # /   47;   slash
1,  # 1   48;   digit 1
1,  # 1   49;   digit 1
1,  # 2   50;   digit 2
0,  # 3   51;   digit 3
1,  # 4   52;   digit 4
1,  # 5   53;   digit 5
1,  # 6   54;   digit 6
1,  # 7   55;   digit 7
1,  # 8   56;   digit 8
1,  # 9   57;   digit 9
1,  # :   58;   colon
1,  # ;   59;   semicolon
1,  # <   60;   less-than
1,  # =   61;   equals-to
1,  # >   62;   greater-than
1,  # ?   63;   question mark
1,  # @   64;   at sign
1,  # A   65;   uppercase A
1,  # B   66;   uppercase B
1,  # C   67;   uppercase C
1,  # D   68;   uppercase D
1,  # E   69;   uppercase E
1,  # F   70;   uppercase F
1,  # G   71;   uppercase G
1,  # H   72;   uppercase H
1,  # I   73;   uppercase I
1,  # J   74;   uppercase J
1,  # K   75;   uppercase K
1,  # L   76;   uppercase L
1,  # M   77;   uppercase M
1,  # N   78;   uppercase N
1,  # O   79;   uppercase O
1,  # P   80;   uppercase P
1,  # Q   81;   uppercase Q
1,  # R   82;   uppercase R
1,  # S   83;   uppercase S
1,  # T   84;   uppercase T
1,  # U   85;   uppercase U
1,  # V   86;   uppercase V
0,  # W   87;   uppercase W
1,  # X   88;   uppercase X
1,  # Y   89;   uppercase Y
1,  # Z   90;   uppercase Z
1,  # [   91;   left square bracket
1,  # \   92;   backslash
1,  # ]   93;   right square bracket
1,  # ^   94;   caret
1,  # _   95;   underscore
1,  # `   96;   grave accent
0,  # a   97;   lowercase a
1,  # b   98;   lowercase b
1,  # c   99;   lowercase c
1,  # d   100;   lowercase d
0,  # e   101;   lowercase e
1,  # f   102;   lowercase f
1,  # g   103;   lowercase g
1,  # h   104;   lowercase h
1,  # i   105;   lowercase i
1,  # j   106;   lowercase j
1,  # k   107;   lowercase k
0,  # l   108;   lowercase l
1,  # m   109;   lowercase m
1,  # n   110;   lowercase n
1,  # o   111;   lowercase o
1,  # p   112;   lowercase p
1,  # q   113;   lowercase q
1,  # r   114;   lowercase r
1,  # s   115;   lowercase s
0,  # t   116;   lowercase t
1,  # u   117;   lowercase u
1,  # v   118;   lowercase v
0,  # w   119;   lowercase w
1,  # x   120;   lowercase x
1,  # y   121;   lowercase y
1,  # z   122;   lowercase z
1,  # {   123;   left curly brace
1,  # |   124;   vertical bar
1,  # }   125;   right curly brace
1]  # ~   126;   tilde

# Specify a list of non overlapping known words
# For each String specify the minimum and maximum offset of the first character from the 
# end of the previous string, or the begining of the Password for the first entry.
# Also specify if you know the case of the string. Use True if you know the case, or False
# to try all case combinations for all alpha characters.
# If you are unsure about a term in the list. Try one run with, and one run without.
KNOWN_WORDS = \
[['FakeWal', 0, 0, True],['le', 0, 0, False],['12' ,1 , 2, True]]

# What is the minimum number of unknown characters at the end of the password
MIN_UNKNOWN_ENDING_CHARS = 1 # Example Value

# What is the maximum number of unknown characters at the end of the password
MAX_UNKNOWN_ENDING_CHARS = 1 # Example Value


# Give an upperlimit for the number of passwords to try.
# The algorithm may give an error for numbers of less than this.
# Example: If you want 5 million results, you may have to set the max to 20 million
MAX_PWD_LIST_LEN = 20000000


# If any arguments are contradictary createPwdList will return empty
charList = [chr(i+32) for i in range(len(EXCLUDED_CHARS)) if not EXCLUDED_CHARS[i]]
passwordList = createPwdList(charList, KNOWN_WORDS, MIN_UNKNOWN_ENDING_CHARS, MAX_UNKNOWN_ENDING_CHARS, MAX_PWD_LIST_LEN)
print 'Number of passwords in guess list:', len(passwordList)
searchForPassword(passwordList)
exit(0)

