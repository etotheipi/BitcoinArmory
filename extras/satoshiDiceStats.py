from math import log, sqrt
from sys import argv

Targets = [1,2,4,8,16,32,64,128,256,512,1000,2000,3000,4000,6000,8000,12000,16000,24000,32000, 32768,48000,64000]

# Assumptions
# Expected Return as defined by the site
E = 0.97

# Standard fee to be returned
F = 0.0000

# Number of bets for the cumulative statistics
nBet = 1000

# Arbitrary Bet Amt
# amt is in the equations to clarify, even though it's just 1 and does nothing
amt = 10.0


def calcAvgAndVar(targ,E,F,X=1):
   pwin = targ/65536.
   plos = 1 - pwin
   winAmt = X * (1 - E/pwin ) - F
   losAmt = X * (1 - (1-E)/2) - F

   avg = winAmt*pwin + losAmt*plos
   var = (winAmt-avg)**2 * pwin  +  (losAmt-avg)**2 * plos
   return [avg,var]
   

print ''
print 'Breakdown of SatoshiDice profit for bets of size: %0.2f BTC' % amt
print '"House Edge" (actual edge is 1/2 this):           %0.1f%%' % (100*(1-E))
print 'Standard fee per return transaction:              %0.4f BTC' % F
print 'Target'.rjust(10), 'Avg Profit'.rjust(12), '1-sigma'.rjust(12), '3-sigma'.rjust(12)
print '-'*50
for targ in Targets:
   avg,var = calcAvgAndVar(targ,E,F,amt)

   print str(targ).rjust(10), 
   print ('%0.6f' % avg).rjust(12),
   print ('%0.4f' % sqrt(var)).rjust(12),
   print ('%0.4f' % (3*sqrt(var))).rjust(12)



print ''
print 'Breakdown of SatoshiDice profit for *%d* bets:  %0.2f BTC each' % (nBet,amt)
print '"House Edge" (actual edge is 1/2 this):            %0.1f%%' % (100*(1-E))
print 'Standard fee per return transaction:               %0.4f BTC' % F
print 'Target'.rjust(10), 'Avg Profit'.rjust(12), '1-sigma'.rjust(12), '3-sigma'.rjust(12)
print '-'*50
for targ in Targets:
   avg,var = calcAvgAndVar(targ,E,F,amt)

   avg = nBet*avg
   var = nBet*var
   sig3 = 3*sqrt(var)
   print str(targ).rjust(10), 
   print ('%0.6f' % avg).rjust(12),
   print ('%0.4f' % sqrt(var)).rjust(12),
   print ('%0.4f' % (3*sqrt(var))).rjust(12),
   print '[%0.4f, %0.4f]' % (avg-sig3, avg+sig3)


nBet = 10000
targ = 32768
betSizes = [0.01, 0.1, 1.0, 10.0, 100.0]
print 'Statistics for varying bet sizes and "house-edge" values'
print 'All data is for "lessthan %d" game.' % targ
print 'Displayed as (mean : 3sigma) after %d bets' % nBet
print ''
print 'BetSize ---> '.rjust(16),
for betsz in betSizes:
   print ('%0.2f'%betsz).rjust(19),
print '\n'
print 'HouseEdge vvv'.rjust(16)
for pct in [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035]:
   print ('%0.1f%%'%(100*pct)).rjust(16),
   for betsz in betSizes:
      avg,var = calcAvgAndVar(targ, 1.0-2*pct ,F, betsz)
      avg = nBet * avg
      std = sqrt(nBet * var)
      avgStr = ('%0.3f'%avg).rjust(8)
      stdStr = ('%0.3f'%(3*std)).rjust(8)
      print '(%s : %s)' % (avgStr, stdStr),
   print ' '
   
