import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokergames import *
from pokerstrategy import *
from environment import *

leduc = leduc_rules()
agents = [HumanAgent(leduc, x) for x in range(leduc.players)]
sim = GameSimulator(leduc, agents, verbose=True, showhands=True)

# play forever
while True:
    sim.play()
    # move the button after every hand
    if p0.seat == 0:
        p0.seat = 1
        p1.seat = 0
    else:
        p0.seat = 0
        p1.seat = 1
    print ''