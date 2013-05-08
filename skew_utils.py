import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
import random

def skew_strategy(baseline, preflop_mod, flop_mod, jacks_mod, queens_mod, kings_mod):
    skewed = Strategy(baseline.player)
    for infoset in baseline.policy:
        roundnum = infoset.count('/')
        if roundnum == 0:
            round_modprobs = preflop_mod
        else:
            round_modprobs = flop_mod
        if infoset.startswith('J'):
            card_modprobs = jacks_mod
        elif infoset.startswith('Q'):
            card_modprobs = queens_mod
        elif infoset.startswith('K'):
            card_modprobs = kings_mod
        else:
            raise Exception("Unknown card: {0}".format(infoset))
        probs = [x * (1.0 + round_modprobs[i] + card_modprobs[i]) for i,x in enumerate(baseline.probs(infoset))]
        total = sum(probs)
        probs = [x / total for x in probs]
        skewed.policy[infoset] = probs
    return skewed

strat_dir = 'stationary_agents/results/'
nash1 = Strategy(1, strat_dir +'nash1.strat')
for i in range(100):
    round_mods = [[0,0,0],[0,0,0]]
    mod = [random.randrange(0,101) / 100.0 for _ in range(3)]
    mod = [x / sum(mod) for x in mod]
    round_mods[random.randrange(0,2)] = mod
    card_mods = [[0,0,0],[0,0,0],[0,0,0]]
    for i in range(2):
        mod = [random.randrange(0,101) / 100.0 for _ in range(3)]
        mod = [x / sum(mod) for x in mod]
        card_mods[random.randrange(0,3)] = mod
    print 'Rounds: {0} Cards: {1}'.format(round_mods, card_mods)
    s = skew_strategy(nash1, round_mods[0], round_mods[1], card_mods[0], card_mods[1], card_mods[2])
    s.save_to_file(strat_dir + 'skewednash_{0}'.format(i))

skew_strategy(nash1, [0.05,-0.30,0.25], [0.05,-0.30,0.25], [0,0,0], [0,0,0], [0,0,0]).save_to_file(strat_dir + 'tight_aggressive.strat')
skew_strategy(nash1, [-0.30,0.05,0.25], [-0.30,0.05,0.25], [0,0,0], [0,0,0], [0,0,0]).save_to_file(strat_dir + 'loose_aggressive.strat')
skew_strategy(nash1, [0.25,-0.15,-0.10], [0.25,-0.15,-0.10], [0,0,0], [0,0,0], [0,0,0]).save_to_file(strat_dir + 'tight_passive.strat')
skew_strategy(nash1, [-0.25,0.25,0], [-0.25,0.25,0], [0,0,0], [0,0,0], [0,0,0]).save_to_file(strat_dir + 'loose_passive.strat')