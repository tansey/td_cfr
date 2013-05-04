import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
from nash_response import *
from skew_agents import *

leduc = leduc_rules()

create_skewed_agents(leduc, WinBonus([0,0.07]), 100000, 'orange', verbose=True)

"""
cfr = RestrictedNashResponse(leduc, response_player, fixed_strategy_profile, prob_fixed)

iterations_per_block = 10
blocks = 1000
for block in range(blocks):
    print 'Iterations: {0}'.format(block * iterations_per_block)
    cfr.run(iterations_per_block)
    result = cfr.profile.best_response()
    print 'Best response EV: {0}'.format(result[1])
    print 'Total exploitability: {0}'.format(sum(result[1]))
print 'Done!'
print ''
"""