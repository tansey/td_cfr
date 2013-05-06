import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *

def skew_strategy(baseline, preflop_mod, flop_mod):
    skewed = Strategy(baseline.player)
    for infoset in baseline.policy:
        roundnum = infoset.count('/')
        if roundnum == 0:
            modprobs = preflop_mod
        else:
            modprobs = flop_mod
        probs = [x * (1.0 + modprobs[i]) for i,x in enumerate(baseline.probs(infoset))]
        total = sum(probs)
        probs = [x / total for x in probs]
        skewed.policy[infoset] = probs
    return skewed

strat_dir = 'stationary_agents/results/'
nash1 = Strategy(1, strat_dir +'nash1.strat')
for i in range(100):
    preflop = [random.randrange(0,101) / 100.0 for _ in range(3)]
    flop = [random.randrange(0,101) / 100.0 for _ in range(3)]
    print 'Preflop: {0} Flop: {1}'.format(preflop, flop)
    s = skew_strategy(nash1, preflop, flop)
    s.save_to_file(strat_dir + 'skewednash_{0}'.format(i))

skew_strategy(nash1, [0.05,-0.30,0.25], [0.05,-0.30,0.25]).save_to_file(strat_dir + 'tight_aggressive.strat')
skew_strategy(nash1, [-0.25,0.25,0], [-0.25,0.25,0]).save_to_file(strat_dir + 'loose_passive.strat')
skew_strategy(nash1, [-0.30,0.05,0.25], [-0.30,0.05,0.25]).save_to_file(strat_dir + 'loose_aggressive.strat')
skew_strategy(nash1, [0.25,-0.15,-0.10], [0.25,-0.15,-0.10]).save_to_file(strat_dir + 'tight_passive.strat')