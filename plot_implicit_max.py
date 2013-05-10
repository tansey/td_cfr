import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
import matplotlib.pyplot as plt
import numpy as np
import random
from itertools import product

def max_ev(portfolio, opponent, profile, nash_ev):
    max_response = None
    max_ev = None
    for response in portfolio:
        profile.strategies = [response, opponent]
        ev = profile.expected_value()[0]
        response_ev = ev - nash_ev[0]
        if max_response is None or max_ev < response_ev:
            max_response = response
            max_ev = response_ev
    return max_ev

def make_strategy(preflop, flop, profile):
    s = Strategy(1)
    s.policy = { infoset: probs for infoset,probs in preflop.iteritems() }
    for infoset,probs in flop.iteritems():
        s.policy[infoset] = probs
    profile.strategies[1] = s
    return profile.best_response()[0].strategies[0]

strat_dir = 'stationary_agents/results/'
output_dir = 'data/paper/implicit_max/'

leduc = leduc_rules()
nash0 = Strategy(0, strat_dir +'nash0.strat')
nash1 = Strategy(1, strat_dir +'nash1.strat')
profile = StrategyProfile(leduc, [nash0, nash1])
nash_ev = profile.expected_value()
nash_br = profile.best_response()[0].strategies[0]


responses = []
strategies = []
print 'Loading strategies and responses'
for difficulty in ['simple', 'complex']:
    print difficulty
    for i in range(100):
        if i % 10 == 0:
            print i
        strategies.append(Strategy(1, strat_dir + 'skewednash_{0}_{1}'.format(difficulty, i)))
        profile.strategies[1] = strategies[-1]
        br = profile.best_response()
        responses.append(br[0].strategies[0])

preflop_subpolicies = [{ infoset: probs for infoset,probs in model.policy.items() if infoset.count('/') == 1 } for model in strategies]
flop_subpolicies = [{ infoset: probs for infoset,probs in model.policy.items() if infoset.count('/') == 2 } for model in strategies]
model_nums = [i for i in range(200)]

print 'Computing maximum potential performance'

samples = 500
for complexity_i,difficulty in enumerate(['simple', 'complex']):
    results = []
    subpolicy_results = []
    subpolicy_gain_results = []
    for i in range(samples):
        if i % 10 == 0:
            print i
        portfolio_nums = random.sample(model_nums, 4)
        portfolio = [responses[m] for m in portfolio_nums]
        preflop_portfolio = [preflop_subpolicies[m] for m in portfolio_nums]
        flop_portfolio = [flop_subpolicies[m] for m in portfolio_nums]
        subpolicy_portfolio = [make_strategy(preflop, flop, profile) for preflop,flop in product(preflop_portfolio, flop_portfolio)]
        opponent = strategies[(i % 100) + (complexity_i * 100)]
        profile.strategies = [nash0, opponent]
        nash_ev = profile.expected_value()
        portfolio_max_ev = max_ev(portfolio, opponent, profile, nash_ev)
        subpolicy_max_ev = max_ev(subpolicy_portfolio, opponent, profile, nash_ev)
        subpolicy_gain = subpolicy_max_ev - portfolio_max_ev
        results.append(portfolio_max_ev)
        subpolicy_results.append(subpolicy_max_ev)
        subpolicy_gain_results.append(subpolicy_gain)
    # the histogram of the data
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(results, 20, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('Max portfolio exploitability (bets/hand)')
    ax.set_ylabel('Best portfolio response (pct of samples)'.format(difficulty))
    ax.set_title('Maximum Implicit Modeling Performance\n({0} trials, {1} opponent)'.format(samples, difficulty))
    plt.savefig('{0}fullpolicy_{1}.pdf'.format(output_dir, difficulty))
    plt.clf()
    # the histogram of the data
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(subpolicy_results, 20, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('Max subpolicy exploitability (bets/hand)')
    ax.set_ylabel('Best subpolicy responses (pct of samples)'.format(difficulty))
    ax.set_title('Maximum Implicit Subpolicy Modeling Performance\n({0} trials, {1} opponent)'.format(samples, difficulty))
    plt.savefig('{0}subpolicy_{1}.pdf'.format(output_dir, difficulty))
    plt.clf()
    # the histogram of the data
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(subpolicy_gain_results, 20, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('Max subpolicy exploitability gain (bets/hand)')
    ax.set_ylabel('Gain (pct of samples)'.format(difficulty))
    ax.set_title('Maximum Implicit Subpolicy Modeling Performance Gain\n({0} trials, {1} opponent)'.format(samples, difficulty))
    plt.savefig('{0}gain_{1}.pdf'.format(output_dir, difficulty))
    plt.clf()


