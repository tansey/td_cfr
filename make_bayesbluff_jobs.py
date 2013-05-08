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

experiment_name = 'bayes_bluff'
experiment_dir = make_directory(os.getcwd(), experiment_name.replace(' ', '_'))
stationary_dir = make_directory(os.getcwd(), 'stationary_agents')
jobsfile = experiment_dir + '/jobs'

#make_directory(experiment_dir, 'condor_logs')
make_directory(experiment_dir, 'results')
make_directory(experiment_dir, 'results/simple')
make_directory(experiment_dir, 'results/complex')
make_directory(experiment_dir, 'results/nash')
#make_directory(experiment_dir, 'output')
make_directory(experiment_dir, 'error')
make_directory(experiment_dir, 'error/simple')
make_directory(experiment_dir, 'error/complex')
make_directory(experiment_dir, 'error/nash')


f = open(jobsfile, 'wb')
f.write("""universe = vanilla
Executable=/lusr/bin/python
Requirements = Precise
+Group   = "GRAD"
+Project = "AI_ROBOTICS"
+ProjectDescription = "Bayesian response to stationary leduc agents"

""")

job = """
Arguments = exploit.py {0}/results/{3}/{2}_{1}.csv {2} {3} {4}
Error = {0}/error/{3}/{1}.log
Queue 1

"""

for model in sys.argv[1].split(','):
    for match in range(int(sys.argv[2])):
        for difficulty in ['simple','complex','nash']:
            f.write(job.format(experiment_dir, match, model, difficulty, match % 100))
f.flush()
f.close()

