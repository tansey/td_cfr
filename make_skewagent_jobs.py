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

experiment_name = 'stationary_agents'
experiment_dir = make_directory(os.getcwd(), experiment_name.replace(' ', '_'))
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
+ProjectDescription = "Stationary leduc agent creation"

""")

job = """Log = {0}/condor_logs/{1}.log
Arguments = skew_agents.py {0}/results/{1} {2} {3} {4} {5}
Output = {0}/output/{1}.out
Error = {0}/error/{1}.log
Queue 1

"""

iterations = 10000
for player in range(2):
    for percentage_int in range(-10,11):
        percentage = percentage_int / 100.0
        f.write(job.format(experiment_dir, 'winbonus_{0}'.format(percentage), player, iterations, 'winbonus', percentage))
        f.write(job.format(experiment_dir, 'losspenalty_{0}'.format(percentage), player, iterations, 'losspenalty', percentage))
    for mean_int in range(-5,6):
        mean = mean_int / 100.0
        for stdev_int in range(1,6):
            stdev = stdev_int / 100.0
            f.write(job.format(experiment_dir, 'gaussnoise_{0}_{1}'.format(mean, stdev), player, iterations, 'losspenalty', '{0} {1}'.format(mean, stdev)))
    
f.flush()
f.close()

