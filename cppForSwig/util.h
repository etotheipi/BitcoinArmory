#ifndef UTIL_H
#define UTIL_H

template<class Container>
class IterateSecond
{
   Container &c;
public:
   typedef decltype(c.begin()->second) value_type;

   IterateSecond(Container &c) : c(c) { }

   class Iterator
   {
      friend class IterateSecond;
      typename Container::iterator i;
   public:
      Iterator(const Iterator &copy)
         : i(copy.i)
      { }
      Iterator()
      { }
   
      value_type& operator*() { return i->second; }
      const value_type& operator*() const { return i->second; }
      
      Iterator& operator++()
      {
         ++i;
         return *this;
      }
      Iterator operator++(int)
      {
         Iterator x;
         x.i = i;
         ++x.i;
         return x;
      }
      
      bool operator==(const Iterator &other) const { return i == other.i; }
      bool operator!=(const Iterator &other) const { return i != other.i; }
   };

   class ConstIterator
   {
      friend class IterateSecond;
      typename Container::const_iterator i;
   public:
      ConstIterator(const Iterator &copy)
         : i(copy.i)
      { }
      ConstIterator(const ConstIterator &copy)
         : i(copy.i)
      { }
      ConstIterator()
      { }
      const value_type& operator*() const { return i->second; }
      
      ConstIterator& operator++()
      {
         ++i;
         return *this;
      }
      ConstIterator operator++(int)
      {
         ConstIterator x;
         x.i = i;
         ++x.i;
         return x;
      }
      bool operator==(const ConstIterator &other) const { return i == other.i; }
      bool operator!=(const ConstIterator &other) const { return i != other.i; }
   };
   
   Iterator begin() { Iterator x; x.i = c.begin(); return x; }
   Iterator end() { Iterator x; x.i = c.end(); return x; }

   ConstIterator begin() const  { ConstIterator x; x.i = c.begin(); return x; }
   ConstIterator end() const  { ConstIterator x; x.i = c.end(); return x; }
};

template<class Container>
inline IterateSecond<Container> values(Container &c)
   { return IterateSecond<Container>(c); }

#endif

// kate: indent-width 3; replace-tabs on;
