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

job = """Log = {0}/condor_logs/{1}_player{2}_response{3}.log
Arguments = robust_response.py {4} {5} {3} {6} {7}
Output = {0}/output/{1}_player{2}_response{3}.out
Error = {0}/error/{1}_player{2}_response{3}.log
Queue 1

"""

strat_str = '{0}/results/{1}_player{2}.strat'
response_str = '{0}/results/{1}_player{2}_response{3}.strat'
iterations = 50000
for player in range(2):
    for response_player in range(2):
        if response_player == player:
            continue
        for prob_fixed_level in range(11):
            prob_fixed = prob_fixed_level / 10.0
            for percentage_int in range(-10,11):
                percentage = percentage_int / 100.0
                
                prefix = 'winbonus_{0}'.format(percentage)
                strat_file = strat_str.format(stationary_dir, prefix, player)
                response_file = response_str.format(stationary_dir, prefix, player, prob_fixed)
                f.write(job.format(experiment_dir, prefix, player, prob_fixed, strat_file, response_player, iterations, response_file))

                prefix = 'losspenalty_{0}'.format(percentage)
                strat_file = strat_str.format(stationary_dir, prefix, player)
                response_file = response_str.format(stationary_dir, prefix, player, prob_fixed)
                f.write(job.format(experiment_dir, prefix, player, prob_fixed, strat_file, response_player, iterations, response_file))
            for mean_int in range(-5,6):
                mean = mean_int / 100.0
                for stdev_int in range(1,6):
                    stdev = stdev_int / 100.0
                    prefix = 'gaussnoise_{0}_{1}'.format(mean, stdev)
                    strat_file = strat_str.format(stationary_dir, prefix, player)
                    response_file = response_str.format(stationary_dir, prefix, player, prob_fixed)
                    f.write(job.format(experiment_dir, prefix, player, prob_fixed, strat_file, response_player, iterations, response_file))
f.flush()
f.close()

