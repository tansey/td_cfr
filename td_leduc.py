import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
from tdcfr import *
from online_cfr import *

leduc = leduc_rules()
#agents = [TDCFRAgent(leduc, x) for x in range(leduc.players)]
#agents = [OnlineCFRAgent(leduc, x, exploration_decay=0.99999) for x in range(leduc.players)]
agents = [TDCFRAgent(leduc, 0), SavedAgent(leduc, 1, '../cfr/strategies/leduc/1.strat')]
#agents = [OnlineCFRAgent(leduc, 0), SavedAgent(leduc, 1, '../cfr/strategies/leduc/1.strat')]
#agents = [OnlineCFRAgent(leduc, 0), StationaryRandomAgent(leduc, 1)]
sim = GameSimulator(leduc, agents, verbose=False, showhands=True)

iterations = 10000
games_per_iteration = 10000
for iteration in range(iterations):
    for game in range(games_per_iteration):
        sim.play()
    profile = StrategyProfile(leduc, [x.strategy for x in agents])
    result = profile.best_response()
    print 'Games played: {0}'.format((iteration+1) * games_per_iteration)
    try:
        print "Exploitability: P1={0:.9f} P2={1:.9f} EV: {2} Exploration: {3:.9f}".format(result[1][1], result[1][0], profile.expected_value(), agents[0].exploration)
    except:
        print "Exploitability: P1={0:.9f} P2={1:.9f} EV: {2}".format(result[1][1], result[1][0], profile.expected_value())
    if (iteration+1) % 100 == 0:
        for agent in agents:
            agent.strategy.save_to_file('results/leduc/temp/player{0}/{1}.strat'.format(agent.seat, iteration+1))
    #sys.exit(0)