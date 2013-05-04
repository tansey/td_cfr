import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from pokercfr import *
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

class GaussianMutation(RewardShaper):
    def __init__(self, means, stdevs):
        self.means = means
        self.stdevs = stdevs

    def shape_payoffs(self, node):
        shifts = [1.0 + random.gauss(self.means[i], self.stdevs[i]) for i in range(len(node.holecards)) ]
        node.payoffs = { hands: [winnings * shifts[player] for player,winnings in enumerate(payoff)] for hands,payoff in node.payoffs.items() }

def create_skewed_agents(rules, skewer, cfr_iterations, filename_prefix, verbose=False):
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
            cfr.profile.strategies[i].save_to_file(filename_prefix + i + '.strat')
        print 'Done!'
        print ''
    else:
        cfr.run(cfr_iterations)
    return cfr.profile