import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
from tdcfr import *
from online_cfr import *

kuhn = half_street_kuhn_rules()
agents = [TDCFRAgent(kuhn, x) for x in range(kuhn.players)]
agents = [OnlineCFRAgent(kuhn, x) for x in range(kuhn.players)]
sim = GameSimulator(kuhn, agents, verbose=False, showhands=True)

iterations = 10000
games_per_iteration = 1000
for iteration in range(iterations):
    for game in range(games_per_iteration):
        sim.play()
    profile = StrategyProfile(kuhn, [x.strategy for x in agents])
    result = profile.best_response()
    br = result[0].strategies[0]
    ev = result[1][0]
    print 'Games played: {0}'.format((iteration+1) * games_per_iteration)
    print "Exploitability: P1={0:.9f} P2={1:.9f} Exploration: {2:.9f}".format(result[1][1], result[1][0], agents[0].exploration)
    if (iteration+1) % 100 == 0:
        for agent in agents:
            agent.strategy.save_to_file('results/hskuhn/alphaavging/player{0}/{1}.strat'.format(agent.seat, iteration+1))