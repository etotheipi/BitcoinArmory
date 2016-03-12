#ifndef _DATAOBJECT_H
#define _DATAOBJECT_H

#include <typeinfo>
#include <typeindex>
#include <vector>
#include <map>
#include <sstream>
#include <string>
#include <initializer_list>
#include <memory>

using namespace std;

///////////////////////////////////////////////////////////////////////////////
class DataMeta
{
private:
   const type_index t_;

public:
   static map<string, uint32_t> strTypeIDs_;
   static const vector<shared_ptr<DataMeta>> iTypeIDs_;

public:
   DataMeta(const type_info& type) :
      t_(type)
   {}

   string getTypeName(void) const
   {
      return t_.name();
   }

   bool isType(type_index in) const { return in == t_; }

   static void initTypeMap(void);

   virtual void serializeToStream(ostream&) const = 0;

   friend ostream& operator << (ostream&, const DataMeta&);
};

///////////////////////////////////////////////////////////////////////////////
template <typename T> class DataObject : public DataMeta
{
   /***
   serialization headers:
   ~: arg type
   *: object count
   +: length of upcoming object
   -: object
   _: object data
   .: arguments delimiter
   &: id
   ***/

private:
   T obj_;

public:
   DataObject() :
      DataMeta(typeid(T))
   {}

   DataObject(const T& theObject) :
      DataMeta(typeid(T)),
      obj_(theObject)
   {}

   DataObject(T&& theObject) :
      DataMeta(typeid(T)),
      obj_(move(theObject))
   {}

   const T getObj(void) const { return obj_; }

   friend ostream& operator << <T> (
      ostream&, const DataObject<T>&);
   friend istream& operator >> <T> (istream&, DataObject<T>&);

   void serializeToStream(ostream& os) const { os << obj_; }
};

///////////////////////////////////////////////////////////////////////////////
template<typename T> istream& operator >> (istream& is, DataObject<T>& obj)
{
   is >> obj.obj_;
   return is;
}

#endif