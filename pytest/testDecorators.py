################################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Andy Ofiesh
# Website:    www.bitcoinarmory.com
# Orig Date:  2 January, 2014
#
################################################################################
import sys
sys.path.append('..')
import unittest
import sys

from armoryengine.Decorators import *


class EmailOutputTest(unittest.TestCase):
   """
   Send an email to the fake smtp server created in setup (gets saved to file)
   and make sure the email has what we think it should have.
   """
   EMAIL_FILE = 'email.tmp'

   def setUp(self):
      useMainnet()
      removeIfExists(self.EMAIL_FILE)
      smtp = ''
      if os.path.isfile('mockSMTP.py'):
         smtp = 'mockSMTP.py'
      elif os.path.isdir('pytest'):
         smtp = os.path.join('pytest', 'mockSMTP.py')
      else:
         raise RuntimeError("cannot find mock SMTP server")
      self.smtpd = subprocess.Popen(["python", smtp])
      self.email_from = "sender@nowhere.none"
      self.email_to = "receiver@nowhere.none"
      self.subject = "test email!"
      self.server = "127.0.0.1:1025"
      self.pwd = ' '
      time.sleep(1)

   def tearDown(self):
      if self.smtpd.returncode is None:
         self.smtpd.kill()
         self.smtpd.wait()
      removeIfExists(self.EMAIL_FILE)

   def getEmail(self):
      f = open(self.EMAIL_FILE, 'r')
      data = f.read()
      f.close()
      return data

   def testEmailOutput(self):

      @EmailOutput(self.email_from, self.server, self.pwd, self.email_to,
                   self.subject, True)
      def someStringOutputFunction(inputString):
         return "Hello " + inputString

      actualResult = someStringOutputFunction("World!")
      expectedResult = "Hello World!"
      self.assertEqual(actualResult, expectedResult)

      email = self.getEmail()
      self.assertTrue("From: %s" % self.email_from in email)
      self.assertTrue("To: %s" % self.email_to in email)
      self.assertTrue("Subject: %s" % self.subject in email)
      self.assertTrue(expectedResult in email)


################################################################################
class RemoveRepeatingExtensionsTest(unittest.TestCase):

   def setUp(self):
      useMainnet()

   def testRemove(self):

      @RemoveRepeatingExtensions
      def someFunc(filename):
         return filename

      testMap = {
         "abc.something": "abc.something",
         "abc.something.something": "abc.something",
         "abc.some.thing.some.thing": "abc.some.thing",
         "abc.some.thing.thing": "abc.some.thing",
         "abc.another.thing.thing.another.thing.thing": "abc.another.thing",
      }

      for k, v in testMap.iteritems():
         result = someFunc(k)
         self.assertEqual(result, v)


################################################################################
class CatchErrsForJSONTest(unittest.TestCase):

   def setUp(self):
      useMainnet()

   def testCatch(self):

      @catchErrsForJSON
      def someFunc(exception):
         if exception is not None:
            raise exception
         else:
            return None

      testMap = {
         AddressUnregisteredError: "AddressUnregisteredError",
         KdfError: "KdfError",
         None: None,
      }

      for k, v in testMap.iteritems():
         result = someFunc(k)
         if k is None:
            self.assertEqual(result, None)
         else:
            self.assertEqual(result['Error Type'], v)


################################################################################
class VerifyArgTypeTest(unittest.TestCase):

   def setUp(self):
      useMainnet()

   #############################################################################
   def testSimple(self):

      @VerifyArgTypes(a=int, b=str, c=float)
      def testFunc(a,b,c):
         return b*a + ' ' + str(c)

      out = testFunc(2,'-', 3.2)
      self.assertEqual(out, '-- 3.2')

      self.assertRaises(TypeError, testFunc, 1.1, '-', 3.2)
      self.assertRaises(TypeError, testFunc, 2, 9, 3.2)
      self.assertRaises(TypeError, testFunc, 2, '-', 'hello')
      self.assertRaises(TypeError, testFunc, 2, 9, 'hello')

   #############################################################################
   def testSomeArgs(self):

      @VerifyArgTypes(a=int, c=float)
      def testFunc(a,b,c):
         return str(b)*a + ' ' + str(c)

      self.assertEqual(testFunc(2,'-', 3.2), '-- 3.2')
      self.assertEqual(testFunc(2, 0, 3.2),  '00 3.2')

      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2)
      self.assertRaises(TypeError, testFunc, 1.1, '-', 3.2)
      self.assertRaises(TypeError, testFunc, 1, 0, '-')

   #############################################################################
   def testArgsNotExist(self):

      def defineFuncWithInvalidDecorator():
         @VerifyArgTypes(a=int, b=str, d=int)
         def testFunc(a,b,c):
            return b*a + str(c)

         # This shouldn't run, it should fail before getting here
         assertTrue(False)

      self.assertRaises(TypeError, defineFuncWithInvalidDecorator)

   #############################################################################
   def testWithStarArgs(self):

      @VerifyArgTypes(a=int, c=float)
      def testFunc(a,b,c, *args):
         return a+b+c+len(args)

      self.assertEqual(testFunc(2, 0, 3.2),  5.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99),  6.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99, 99),  7.2)

      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99, 99)

   #############################################################################
   def testWithStarStar(self):

      @VerifyArgTypes(a=int, c=float)
      def testFunc(a,b,c, **kwargs):
         return a+b+c+len(kwargs)

      self.assertEqual(testFunc(2, 0, 3.2),  5.2)
      self.assertEqual(testFunc(2, 0, 3.2, d=99),  6.2)
      self.assertEqual(testFunc(2, 0, 3.2, d=99, e=99),  7.2)

      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99, e=99)
      self.assertRaises(TypeError, testFunc, a=1.1, b=0, c=3.2, d=99, e=99)


   #############################################################################
   def testWithStarAndStarStar(self):

      @VerifyArgTypes(a=int, c=float)
      def testFunc(a,b,c, *args, **kwargs):
         return a+b+c+len(kwargs)+len(args)

      self.assertEqual(testFunc(2, 0, 3.2),  5.2)
      self.assertEqual(testFunc(2, 0, 3.2, d=99),  6.2)
      self.assertEqual(testFunc(2, 0, 3.2, d=99, e=99),  7.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99),  6.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99, 99),  7.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99, d=99),  7.2)
      self.assertEqual(testFunc(2, 0, 3.2, 99, 99, d=99, e=99),  9.2)

      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99, e=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99, 99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99, d=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, 99,99, d=99, e=99)


   #############################################################################
   def testTupleTypes(self):

      @VerifyArgTypes(a=int, c=float, b=(int,str))
      def testFunc(a,b,c, *args, **kwargs):
         return a+int(b)+c+len(kwargs)+len(args)

      self.assertEqual(testFunc(2, 9, 3.2), 14.2)
      self.assertEqual(testFunc(2, '9', 3.2), 14.2)
      self.assertEqual(testFunc(2, '9', 3.2, 'a'), 15.2)
      self.assertEqual(testFunc(2, '9', 3.2, 'a', extra='abc'), 16.2)

      self.assertRaises(TypeError, testFunc, 2,   1.1, 3.2)
      self.assertRaises(TypeError, testFunc, 2,   None, 3.2, d=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99, e=99)


   #############################################################################
   def testListTypes(self):

      # Making sure we can pass a list as well as a tuple (isinstance only
      # accepts tuples, but VerifyArgTypes will take a list and convert)
      @VerifyArgTypes(a=int, c=float, b=[int,str])
      def testFunc(a,b,c, *args, **kwargs):
         return a+int(b)+c+len(kwargs)+len(args)

      self.assertEqual(testFunc(2, 9, 3.2), 14.2)
      self.assertEqual(testFunc(2, '9', 3.2), 14.2)
      self.assertEqual(testFunc(2, '9', 3.2, 'a'), 15.2)
      self.assertEqual(testFunc(2, '9', 3.2, 'a', extra=5), 16.2)

      self.assertRaises(TypeError, testFunc, 2,   1.1, 3.2)
      self.assertRaises(TypeError, testFunc, 2,   None, 3.2, d=99)
      self.assertRaises(TypeError, testFunc, 1.1, 0, 3.2, d=99, e=99)


   #############################################################################
   def testNoneTypes(self):

      # Making sure we can pass a list as well as a tuple (isinstance only
      # accepts tuples, but VerifyArgTypes will take a list and convert)
      @VerifyArgTypes(a=[str,int,None], c=[float, int])
      def testFunc(a,b,c):
         return float(a)+int(b)+c if a is not None else int(b)+c

      self.assertEqual(testFunc('2', 9, 3.2), 14.2)
      self.assertEqual(testFunc(2, '9', 3.2), 14.2)
      self.assertEqual(testFunc(None, '9', 3.2), 12.2)

      self.assertRaises(TypeError, testFunc, 1.1, '2', 3.2)
      self.assertRaises(TypeError, testFunc, 2, None, 3.2)
      self.assertRaises(TypeError, testFunc, 2, '9', None)
