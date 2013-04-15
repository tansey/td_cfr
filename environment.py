import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
import random

class Agent(object):
    """
    An abstract base class that poker agents must extend.
    """
    def __init__(self, rules, seat):
        self.infoset = None
        self.possible_states = None
        self.seat = seat
        self.rules = rules

    def episode_starting(self):
        pass

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        For now, we assume all imperfect information is revealed at the end of the episode.
        """
        pass

    def set_infoset(self, infoset):
        self.infoset = infoset

    def get_action(self):
        pass

    def observe_reward(self, r):
        pass

class HumanAgent(Agent):
    def __init__(self, rules, seat):
        Agent.__init__(self, rules, seat)

    def set_holecards(self, hc):
        Agent.set_holecards(self, hc)
        print 'Player {0}: {1}'.format(self.seat, self.holecards)

    def get_action(self):
        s = raw_input('Your action (f, c, r) >> ')
        while s is not 'f' and s is not 'c' and s is not 'r':
            s = raw_input('Your action (f, c, r) >> ')
        if s is 'f':
            return FOLD
        if s is 'c':
            return CALL
        return RAISE

class GameSimulator(object):
    def __init__(self, rules, agents, verbose=False, showhands=True):
        self.agents = agents
        self.verbose = verbose
        self.showhands = showhands
        self.rules = rules
        self.tree = GameTree(rules)
        self.tree.build()

    def play(self):
        for agent in self.agents:
            agent.episode_starting()
        self.play_helper(self.tree.root)

    def play_helper(self, node):
        if type(node) is TerminalNode:
            return self.terminal_node(node)
        if type(node) is HolecardChanceNode or type(node) is BoardcardChanceNode:
            return self.chance_node(node)
        return self.action_node(node)

    def terminal_node(self, node):
        for i,agent in enumerate(self.agents):
            agent.observe_reward(node.payoffs[i])
            agent.episode_over(node)
        if self.verbose:
            self.print_payoffs(node)
        return node.payoffs

    def chance_node(self, node):
        next = random.choice(node.children)
        if self.verbose:
            if type(node) is HolecardChanceNode:
                print 'Dealing holecards'
            if type(node) is BoardcardChanceNode:
                print 'Dealing board: {0}'.format(next.board)
        if type(node) is HolecardChanceNode:
            for i,agent in enumerate(self.agents):
                agent.set_holecards(next.holecards[i])
        return self.play_helper(next)

    def action_node(self, node):
        agent = self.agents[node.player]
        agent.set_infoset(node.player_view)
        action = agent.get_action()
        next = node.valid(action)
        if self.verbose:
            self.print_action(action, node, next)
        return self.play_helper(next)

    def print_action(self, action, curnode, nextnode):
        if action is FOLD:
            print 'Player {0} folds.'.format(curnode.player)
        else:
            commit = nextnode.committed[curnode.player] - curnode.committed[curnode.player]
            if action is CALL:
                if commit == 0:
                    print 'Player {0} checks.'.format(curnode.player)
                else:
                    print 'Player {0} calls ${1}'.format(curnode.player, commit)
            else:
                cur_round = curnode.bet_history.count('/') - 1
                bets = curnode.bet_history[curnode.bet_history.rfind('/'):].count('r')
                if bets > 0 or (cur_round is 0 and self.rules.blinds is not None and len(self.rules.blinds) > 0):
                    print 'Player {0} raises ${1}'.format(curnode.player, commit)
                else:
                    print 'Player {0} bets ${1}'.format(curnode.player, commit)

    def print_payoffs(self, node):
        if self.showhands:
            for i,agent in enumerate(self.agents):
                print 'Player {0} shows {1}'.format(i, node.holecards[i])
        for i,agent in enumerate(self.agents):
            potshare = node.payoffs[i] + node.committed[i]
            if potshare > 0:
                print 'Player {0} wins ${1}'.format(i, potshare)

