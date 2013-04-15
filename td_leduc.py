import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
from tdcfr import *

leduc = leduc_rules()
agents = [TDCFRAgent(leduc, x) for x in range(leduc.players)]
sim = GameSimulator(leduc, agents, verbose=False, showhands=True)

iterations = 1000
games_per_iteration = 1000
for iteration in range(iterations):
    for game in range(games_per_iteration):
        sim.play()
    profile = StrategyProfile(leduc, [x.strategy for x in agents])
    result = profile.best_response()
    br = result[0].strategies[0]
    ev = result[1][0]
    print 'Games played: {0}'.format((iteration+1) * games_per_iteration)
    print "Exploitability: P1={0:.9f} P2={1:.9f}".format(result[1][1], result[1][0])