import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *

leduc = leduc_rules()
agents = [HumanAgent(leduc, x) for x in range(leduc.players)]
sim = GameSimulator(leduc, agents, verbose=True, showhands=True)

#while True:
sim.play()
print ''