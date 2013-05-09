import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
import matplotlib.pyplot as plt
import numpy as np

strat_dir = 'stationary_agents/results/'
output_dir = 'data/paper/exploitability/'

leduc = leduc_rules()
nash0 = Strategy(0, strat_dir +'nash0.strat')
nash1 = Strategy(1, strat_dir +'nash1.strat')
profile = StrategyProfile(leduc, [nash0, nash1])
nash_ev = profile.expected_value()

for difficulty in ['simple', 'complex']:
    exploitability = []
    for i in range(100):
        profile.strategies = [nash0, Strategy(1, strat_dir + 'skewednash_{0}_{1}'.format(difficulty, i))]
        br = profile.best_response()
        exploitability.append(br[1][0] - nash_ev[0])
        print '{0} {1}: {2}'.format(difficulty, i, exploitability[-1])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # the histogram of the data
    n, bins, patches = ax.hist(exploitability, 10, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('Exploitability')
    ax.set_ylabel('# of {0} skewed strategies'.format(difficulty))
    ax.set_title('Agent exploitability\n({0} skewing)'.format(difficulty))
    plt.savefig('{0}{1}.png'.format(output_dir,difficulty))
    plt.clf()
    

