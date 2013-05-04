import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *
from nash_response import *
from skew_agents import *

def make_directory(base, subdir):
    if not base.endswith('/'):
        base += '/'
    directory = base + subdir
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

experiment_name = 'robust_responses'
experiment_dir = make_directory(os.getcwd(), experiment_name.replace(' ', '_'))
stationary_dir = make_directory(os.getcwd(), 'stationary_agents')
jobsfile = experiment_dir + '/jobs'

make_directory(experiment_dir, 'condor_logs')
make_directory(experiment_dir, 'results')
make_directory(experiment_dir, 'output')
make_directory(experiment_dir, 'error')

f = open(jobsfile, 'wb')
f.write("""universe = vanilla
Executable=/lusr/bin/python
Requirements = Precise
+Group   = "GRAD"
+Project = "AI_ROBOTICS"
+ProjectDescription = "Robust response to stationary leduc agents"

""")

job = """Log = {0}/condor_logs/{1}_player{2}_response.log
Arguments = robust_response.py 
Output = {0}/output/{1}_player{2}_response.out
Error = {0}/error/{1}_player{2}_response.log
Queue 1

"""

strat_str = '{0}/results/{1}_player{2}.strat'
response_str = '{0}/results/{1}_player{2}_response{3}.strat'
iterations = 50000
for player in range(2):
    for response_player in range(2):
        if response_player == player:
            continue
        for prob_fixed_level for range(11):
            prob_fixed = prob_fixed_level / 10.0
            for percentage_int in range(-10,11):
                percentage = percentage_int / 100.0
                strat_file = strat_str.format(stationary_dir, 'winbonus_{0}'.format(percentage), player)
                response_file = strat_str.format(stationary_dir, 'winbonus_{0}'.format(percentage), player, prob_fixed)
                f.write(job.format(strat_file, response_player, prob_fixed, iterations, response_file))
                strat_file = strat_str.format(stationary_dir, 'losspenalty_{0}'.format(percentage), player)
                response_file = strat_str.format(stationary_dir, 'losspenalty_{0}'.format(percentage), player, prob_fixed)
                f.write(job.format(strat_file, response_player, prob_fixed, iterations, response_file))
            for mean_int in range(-5,6):
                mean = mean_int / 100.0
                for stdev_int in range(1,6):
                    stdev = stdev_int / 100.0
                    strat_file = strat_str.format(stationary_dir, 'gaussnoise_{0}_{1}'.format(mean, stdev), player)
                    response_file = strat_str.format(stationary_dir, 'gaussnoise_{0}_{1}'.format(mean, stdev), player, prob_fixed)
                    f.write(job.format(strat_file, response_player, prob_fixed, iterations, response_file))
f.flush()
f.close()

