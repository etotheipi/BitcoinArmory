################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
import sys
from PyQt4.QtGui  import QColor, QPalette, QApplication


"""
# Here's what the palette looks like on Ubuntu 10.04, default theme

qp.color(QPalette.Window);           240 235 226 255
qp.color(QPalette.Background);       240 235 226 255
qp.color(QPalette.WindowText);        60  59  55 255
qp.color(QPalette.Foreground);        60  59  55 255
qp.color(QPalette.Base);             255 255 255 255
qp.color(QPalette.AlternateBase);    239 239 239 255
qp.color(QPalette.Text);              58  57  53 255
qp.color(QPalette.Button);           240 235 226 255
qp.color(QPalette.BrightText);       255 255 255 255
qp.color(QPalette.ToolTipBase);      255 255 220 255
qp.color(QPalette.ToolTipText);      255 255 255 255
qp.color(QPalette.Light);            255 255 255 255
qp.color(QPalette.Midlight);         203 199 196 255
qp.color(QPalette.Dark);             200 196 189 255
qp.color(QPalette.Mid);              184 181 178 255
qp.color(QPalette.Shadow);           185 181 174 255
qp.color(QPalette.Highlight);        198 185 166 255
qp.color(QPalette.HighlightedText);   50  50  50 255
qp.color(QPalette.Link);               0   0 255 255
qp.color(QPalette.LinkVisited);      255   0 255 255
"""


class InvalidColor(Exception): pass


################################################################################
def tweakColor(qcolor, op, tweaks):
   """
   We want to be able to take existing colors (from the palette)
   and tweak them.  This may involved "inverting" them, or 
   multiplying or adding scalars to the various channels.
   """
   if len(tweaks) != 3:
      raise InvalidColor, 'Must supply list or tuple of RGB tweaks'
   
   # Determine what the "tweaks" list/tuple means
   tweakChannel = lambda x,mod: x  # identity
   if op.lower() in ('times', '*'):
      def tweakChannel(color, mod):
         if mod < 0:
            color = (255 - color)
            mod *= -1
         returnColor = color * mod
         returnColor = min(returnColor, 255)
         return int(max(returnColor, 0))
   elif op.lower() in ('plus', '+'):
      def tweakChannel(color, mod):
         returnColor = color + mod
         returnColor = min(returnColor, 255)
         return int(max(returnColor, 0))
   else:
      raise InvalidColor, 'Invalid color operation: "%s"' % op

   r,g,b = qcolor.red(), qcolor.green(), qcolor.blue()
   r = tweakChannel(r, tweaks[0])
   g = tweakChannel(g, tweaks[1])
   b = tweakChannel(b, tweaks[2])
   return QColor(r,g,b)




################################################################################
def luminance(qcolor):
   """ Gives the pseudo-equivalent greyscale value of this color """
   r,g,b = qcolor.red(), qcolor.green(), qcolor.blue()
   return int(0.2*r + 0.6*g + 0.2*b)
   

QAPP = QApplication(sys.argv)
qpal = QAPP.palette()

# Some of the standard colors to be tweaked
class ArbitraryStruct: pass
Colors = ArbitraryStruct()

Colors.Background       = qpal.color(QPalette.Window)
Colors.Foreground       = qpal.color(QPalette.WindowText)
Colors.HighlightBG      = qpal.color(QPalette.Highlight)
Colors.HighlightFG      = qpal.color(QPalette.HighlightedText)
Colors.Link             = qpal.color(QPalette.Link)
Colors.Mid              = qpal.color(QPalette.Mid)
Colors.DisableFG        = qpal.color(QPalette.Disabled, QPalette.WindowText)

Colors.isDarkBkgd       = (luminance(Colors.Background) < 128)

Colors.TextWarn         = tweakColor(Colors.Foreground, '+', [+100,  -40,  -40])
Colors.TextRed          = tweakColor(Colors.Foreground, '+', [+100,  -40,  -40])
Colors.TextGreen        = tweakColor(Colors.Foreground, '+', [ -40, +100,  -40])
Colors.TextBlue         = tweakColor(Colors.Foreground, '+', [ -40,  -40, +100])
Colors.SlightRed        = tweakColor(Colors.Background, '*', [1.05, 0.95, 0.95])
Colors.SlightGreen      = tweakColor(Colors.Background, '*', [0.92, 1.08, 0.92])
Colors.SlightBlue       = tweakColor(Colors.Background, '*', [0.95, 0.95, 1.05])
Colors.SlightBkgdDark   = tweakColor(Colors.Background, '*', [0.95, 0.95, 0.95])
Colors.SlightBkgdLight  = tweakColor(Colors.Background, '*', [1.05, 1.05, 1.05])

Colors.TextNoConfirm    = tweakColor(Colors.Mid, '*', [ 0.9,  0.9,  0.9])
Colors.TextSomeConfirm  = tweakColor(Colors.Mid, '*', [ 0.7,  0.7,  0.7])


Colors.MoneyPos         = tweakColor(Colors.Foreground, '+', [ -50, +100,  -50])
Colors.MoneyNeg         = tweakColor(Colors.Foreground, '+', [+150,  -40,  -40])
Colors.TblWltOther      = tweakColor(Colors.Background, '*', [1.00, 1.00, 1.00])
Colors.TblWltMine       = tweakColor(Colors.Background, '*', [0.95, 0.95, 1.3 ])
Colors.TblWltOffline    = tweakColor(Colors.Background, '*', [0.85, 0.85, 1.35])

if(Colors.isDarkBkgd):
   Colors.LBtnNormalBG  = Colors.Background
   Colors.LBtnHoverBG   = tweakColor(Colors.Background, '+', [ +25,  +25,    0])
   Colors.LBtnNormalFG  = tweakColor(Colors.Link,       '+', [+150, +150,    0])
   Colors.LBtnHoverFG   = tweakColor(Colors.Link,       '+', [+150, +150,    0])
else:
   Colors.LBtnNormalBG  = Colors.Background
   Colors.LBtnHoverBG   = tweakColor(Colors.Background, '*', [ 0.8,  0.8,  1.7])
   Colors.LBtnNormalFG  = Colors.Link
   Colors.LBtnHoverFG   = Colors.Link

Colors.ToolTipQ         = Colors.LBtnNormalFG



################################################################################
def htmlColor(name):
   """ 
   These are not official HTML colors:  this is simply a method
   for taking one of the above colors and converting to a hex string
   """
   try:
      qcolor = Colors.__dict__[name]
      r,g,b = qcolor.red(), qcolor.green(), qcolor.blue()
      rstr = hex(r)[2:].rjust(2, '0')
      gstr = hex(g)[2:].rjust(2, '0')
      bstr = hex(b)[2:].rjust(2, '0')
      return '#%s%s%s' % (rstr, gstr, bstr)
   except:
      raise InvalidColor, 'Invalid color: ' + name



if __name__== "__main__":

   print Colors.TextWarn
   print htmlColor("TextRed")
   print htmlColor("TextWarn")

   print "Colors in the palette!"
   for name,qc in Colors.__dict__.iteritems():
      if not isinstance(qc, QColor):
         continue
      print '\t',
      print ('"'+name+'"').ljust(20), 
      print str(qc.red()).rjust(3),
      print str(qc.green()).rjust(3),
      print str(qc.blue()).rjust(3),
      print '\t(%s)' % htmlColor(name)



