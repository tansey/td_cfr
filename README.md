Temporal-Difference Counterfactual Regret Minimization (TD-CFR)
===============================================================
This is an implementation of the Counterfactual Regret Minimization (CFR) algorithm [1] that uses Temporal Difference (TD) learning instead of dynamic programming [1] or Monte Carlo sampling [2].

Running TD-CFR
--------------
Coming soon!

Playing vs. your agent
----------------------
You can play on the console vs. your agent by specifying the rules and creating a simulator instance:

```python
# load the rules of the game
leduc = leduc_rules()

# learn the agent's policy
tdcfr_agent = ... 

# create a human player
p0 = HumanAgent(leduc, 0)
p1 = learned_agent
agents = [p0, p1]

# create a simulator instance
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
```

Dependencies
------------
You need the [pyCFR](https://github.com/tansey/pycfr) library to be in an external sibling folder `../cfr` to run the code. The library provides implementations of poker game trees, expected value, best response, and the canonical CFR algorithm.

TODO
----
The following is a list of items that still need to be implemented:

- 

Contributors
------------
Wesley Tansey

References
----------
[1] Zinkevich, M., Johanson, M., Bowling, M., & Piccione, C. (2008). Regret minimization in games with incomplete information. Advances in neural information processing systems, 20, 1729-1736.

[2] Lanctot, M., Waugh, K., Zinkevich, M., & Bowling, M. (2009). Monte Carlo sampling for regret minimization in extensive games. Advances in Neural Information Processing Systems, 22, 1078-1086.