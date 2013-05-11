import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from pokercfr import *

results_dir = sys.argv[1]
if not results_dir.endswith('/'):
    results_dir += '/'

print 'Computing NE for Royal poker'
royal = royal_rules()

cfr = CounterfactualRegretMinimizer(royal)

iterations_per_block = 1
blocks = 10000
for block in range(blocks):
    print 'Iterations: {0}'.format(block * iterations_per_block)
    cfr.run(iterations_per_block)
    result = cfr.profile.best_response()
    print 'Best response EV: {0}'.format(result[1])
    print 'Total exploitability: {0}'.format(sum(result[1]))
    print 'Saving strategies...'
    for i,s in enumerate(cfr.profile.strategies):
        s.save_to_file('{0}royal_nash{1}.strat'.format(results_dir, i))
print 'Done!'
print ''