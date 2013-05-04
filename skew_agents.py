import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from pokercfr import *
from pokergames import *
import random

class RewardShaper(object):
    def __init__(self):
        pass

    def shape(self, pubtree):
        self.shape_helper(pubtree.root)

    def shape_helper(self, node):
        if type(node) is TerminalNode:
            self.shape_payoffs(node)
        else:
            for child in node.children:
                self.shape_helper(child)

    def shape_payoffs(self, node):
        pass

class WinBonus(RewardShaper):
    def __init__(self, percentages):
        self.percentages = percentages

    def shape_payoffs(self, node):
        node.payoffs = { hands: [winnings + max(0,winnings) * self.percentages[player] for player,winnings in enumerate(payoff)] for hands,payoff in node.payoffs.items() }

class LossPenalty(RewardShaper):
    def __init__(self, percentages):
        self.percentages = percentages

    def shape_payoffs(self, node):
        node.payoffs = { hands: [winnings + min(0,winnings) * self.percentages[player] for player,winnings in enumerate(payoff)] for hands,payoff in node.payoffs.items() }

class GaussianNoise(RewardShaper):
    def __init__(self, means, stdevs):
        self.means = means
        self.stdevs = stdevs

    def shape_payoffs(self, node):
        shifts = [1.0 + random.gauss(self.means[i], self.stdevs[i]) for i in range(len(node.holecards)) ]
        node.payoffs = { hands: [winnings * shifts[player] for player,winnings in enumerate(payoff)] for hands,payoff in node.payoffs.items() }

def create_skewed_agents(rules, skewer, cfr_iterations, filename_prefix, player=None, verbose=False):
    cfr = CounterfactualRegretMinimizer(rules)
    skewer.shape(cfr.tree)
    if verbose:
        iterations_per_block = 100
        blocks = int(cfr_iterations / iterations_per_block) + 1
        for block in range(blocks):
            print 'Iterations: {0}'.format(block * iterations_per_block)
            cfr.run(iterations_per_block)
            result = cfr.profile.best_response()
            print 'Best response EV: {0}'.format(result[1])
            print 'Total exploitability: {0}'.format(sum(result[1]))
        print 'Saving agents...'
        for i in range(rules.players):
            if player is None or player is i:
                cfr.profile.strategies[i].save_to_file(filename_prefix + i + '.strat')
        print 'Done!'
        print ''
    else:
        cfr.run(cfr_iterations)
    return cfr.profile

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print 'Format: python skew_agents.py <strat_file_prefix> <player> <iterations> <winbonus|losspenalty|gaussnoise> [params]'
        sys.exit(0) 

    leduc = leduc_rules()

    strat_file = sys.argv[1]
    player = int(sys.argv[2])
    iterations = int(sys.argv[3])
    if sys.argv[4] == 'winbonus':
        percents = [0 for x in range(leduc.players)]
        percents[player] = float(sys.argv[5])
        shaper = WinBonus(percents)
    elif sys.argv[4] == 'losspenalty':
        percents = [0 for x in range(leduc.players)]
        percents[player] = float(sys.argv[5])
        shaper = LossPenalty(percents)
    elif sys.argv[4] == 'gaussnoise':
        mu = [0 for x in range(leduc.players)]
        stdev = [0 for x in range(leduc.players)]
        mu[player] = float(sys.argv[5])
        stdev[player] = float(sys.argv[6])
        shaper = GaussianNoise(mu, stdev)

    create_skewed_agents(leduc, shaper, iterations, 'orange', player=player, verbose=True)