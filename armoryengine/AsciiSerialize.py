from ArmoryUtils import makeAsciiBlock, readAsciiBlock
from armoryengine.ArmoryUtils import LOGERROR, UnserializeError

class AsciiSerializable(object):
   """
   This is intended to be a virtual class (roughly speaking).  The below four
   methods will be inherited by all classes that derive from this one.  The 
   only requirements for these methods to work is that the objects have the 
   following attributes and methods defined:

      Class Static Members
         self.BLKSTRING
         self.EQ_ATTRS_SIMPLE
         self.EQ_ATTRS_LISTS
         self.EQ_ATTRS_MAPS

      Object members:
         self.asciiID

      Class Methods:
         self.serialize()
         self.unserialize()

   The EQ_ATTRS_* is a list of strings of this class's members' names that can
   be directly compared via == operator, or a list or map of such objects.  
   These will be iterated and checked in the __eq__(self, other) function that
   will be inherited.  For instance, you might right the class the following 
   way:

   class MyClass(AsciiSerializable):
      BLKSTRING       = "MyObject"
      EQ_ATTRS_SIMPLE = ['myInt', 'myStr']
      EQ_ATTRS_LISTS  = ['myVect']
      EQ_ATTRS_MAPS   = ['myMapA', 'myMapB']

      def __init__(self, initInt, initStr, initVect, initMap1, initMap2):
         self.myInt  = initInt
         self.myStr  = initStr
         self.myVect = initVect
         self.myMapA = initMap1
         self.myMapB = initMap2
      
   If you would like to do more in the __eq__ function than just compare those
   simple things, call this first inside your overridden __eq__ func, then 
   define your extra logic:
   
      def __eq__(self, obj2):
         if not super(MyClass, self).__eq__(obj2):
            return False
            
         # We'll consider them equal if the first is a multiple of the second
         return (self.modulus % obj2.modulus)==0

   """

   #############################################################################
   def serializeAscii(self):
      headStr = '%s-%s' % (self.BLKSTRING, self.asciiID)
      return makeAsciiBlock(self.serialize(), headStr)


   #############################################################################
   def unserializeAscii(self, ustxBlock, skipMagicCheck=False):
      headStr,rawData = readAsciiBlock(ustxBlock, self.BLKSTRING)
      if rawData is None:
         LOGERROR('Expected str "%s", got "%s"' % (self.BLKSTRING, headStr))
         raise UnserializeError('Unexpected BLKSTRING')

      expectID = headStr.split('-')[-1]
      return self.unserialize(rawData, expectID, skipMagicCheck)
   


   #############################################################################
   def __eq__(self, aso2):
      if not isinstance(aso2, self.__class__):
         return False

      # Expect three lists of comparables to be present (static or otherwise)
      #   self.EQ_ATTRS_SIMPLE
      #   self.EQ_ATTRS_LISTS
      #   self.EQ_ATTRS_MAPS

      #### Regular compares
      if hasattr(self, 'EQ_ATTRS_SIMPLE'):
         for attr in self.EQ_ATTRS_SIMPLE:
            if not getattr(self, attr) == getattr(aso2, attr):
               LOGERROR('Compare failed for attribute: %s' % attr)
               LOGERROR('  self:   %s' % str(getattr(self,attr)))
               LOGERROR('  other:  %s' % str(getattr(aso2,attr)))
               return False

      #### List iteration compares
      if hasattr(self, 'EQ_ATTRS_LISTS'):
         for attr in self.EQ_ATTRS_LISTS:
            selfList  = getattr(self, attr)
            otherList = getattr(aso2, attr)
         
            if not len(selfList)==len(otherList):
               LOGERROR('List size compare failed for %s' % attr)
               return False
   
            i = -1
            for a,b in zip(selfList, otherList):
               i+=1
               if not a==b:
                  LOGERROR('Failed list compare for attr %s, index %d' % (attr,i))
                  return False


      #### Map iteration compares
      if hasattr(self, 'EQ_ATTRS_MAPS'):
         for attr in self.EQ_ATTRS_MAPS:
            selfMap  = getattr(self, attr)
            otherMap = getattr(aso2, attr)

            if not len(selfMap)==len(otherMap):
               LOGERROR('Map size compare failed for %s' % attr)
               return False
   
            for key,val in selfMap.iteritems():
               if not key in otherMap:
                  LOGERROR('First map has key not in second map: "%s"' % key)
                  return False
   
               if not val==otherMap[key]:
                  LOGERROR('Value for attr=%s, key=%s does not match' % (attr,key))
                  return False 
            
      return True


   #############################################################################
   def __ne__(self, aso2):
      return not self.__eq__(aso2)

