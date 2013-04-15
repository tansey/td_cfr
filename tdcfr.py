import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from environment import *
import random

class TDCFRAgent(Agent):
    def __init__(self, rules, seat, gametree=None):
        Agent.__init__(self, rules, seat)
        self.strategy = Strategy(seat)
        self.gametree = gametree
        if self.gametree is None:
            self.gametree = GameTree(rules)
        if self.gametree.root is None:
            self.gametree.build()
        self.strategy.build_default(self.gametree)
        self.transition_probs = { }
        self.q_function = { }
        self.avg_posregret = { }
        self.node_visits = { }
        self.action_counts = { }
        for infoset,nodes in self.gametree.information_sets.iteritems():
            if nodes[0].player is seat:
                self.transition_probs[infoset] = [0] * len(nodes) #[1.0 / len(nodes)]*len(nodes)
                self.q_function[infoset] = [self.initialize_q(infoset)] * len(nodes) # TODO: optimistic initialization?
                self.avg_posregret[infoset] = [0,0,0]
                self.node_visits[infoset] = [0] * len(nodes)
                self.action_counts[infoset] = [[0,0,0]] * len(nodes)

    def initialize_q(self, infoset):
        example_state = self.gametree.information_sets[infoset][0]
        q = [-1000,-1000,-1000]
        if example_state.fold_action:
            q[FOLD] = 1000
        if example_state.call_action:
            q[CALL] = 1000
        if example_state.raise_action:
            q[RAISE] = 1000
        return q

    def episode_starting(self):
        self.episode_history = []
        self.reward = 0

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        For now, we assume all imperfect information is revealed at the end of the episode.
        """
        for infoset,action in self.episode_history:
            total_visits = sum(self.node_visits[infoset])
            for i,node in enumerate(self.gametree.information_sets[infoset]):
                if node.holecards == state.holecards:
                    # we were in this state all along, so increase its probability and update the q function for the (s,a) pair
                    self.transition_probs[infoset][i] = 1.0 / (total_visits+1) * (total_visits * self.transition_probs[infoset][i] + 1)
                    self.q_function[infoset][i][action] = 1.0 / (self.action_counts[infoset][i][action]+1) * (self.action_counts[infoset][i][action] * self.q_function[infoset][i][action] + self.reward)
                    self.node_visits[infoset][i] += 1
                    self.action_counts[infoset][i][action] += 1
                else:
                    # we were not in this state, so decrease its probability
                    self.transition_probs[infoset][i] = 1.0 / (total_visits+1) * (total_visits * self.transition_probs[infoset][i])

    def set_infoset(self, infoset):
        self.infoset = infoset

    def get_action(self):
        self.update_policy(self.infoset)
        #print 'Infoset: {0} Probs: {1} Posregrets: {2}'.format(self.infoset, self.strategy.probs(self.infoset), self.avg_posregret[self.infoset])
        action = self.strategy.sample_action(self.infoset)
        self.episode_history.append((self.infoset, action))
        return action

    def observe_reward(self, r):
        self.reward += r

    def update_policy(self, infoset):
        probs = self.strategy.probs(infoset)
        winnings = [0,0,0]
        for i,node in enumerate(self.gametree.information_sets[infoset]):
            for action in range(3):
                winnings[action] += self.transition_probs[infoset][i] * self.q_function[infoset][i][action]
        ev = sum([probs[action] * winnings[action] for action in range(3)])
        posregrets = [max(0,winnings[action] - ev) for action in range(3)]
        infoset_visits = sum(self.node_visits[infoset])
        self.avg_posregret[infoset] = [1.0 / (infoset_visits+1) * (self.avg_posregret[infoset][action] * infoset_visits + posregrets[action]) for action in range(3)]
        total_posregret = sum(self.avg_posregret[infoset])
        example_state = self.gametree.information_sets[infoset][0]
        probs = [0,0,0]
        if total_posregret == 0:
            equal_prob = 1.0 / len(example_state.children)
            if example_state.fold_action:
                probs[FOLD] = equal_prob
            if example_state.call_action:
                probs[CALL] = equal_prob
            if example_state.raise_action:
                probs[RAISE] = equal_prob
        else:
            avg = self.avg_posregret[infoset]
            if example_state.fold_action:
                probs[FOLD] = avg[FOLD] / total_posregret
            if example_state.call_action:
                probs[CALL] = avg[CALL] / total_posregret
            if example_state.raise_action:
                probs[RAISE] = avg[RAISE] / total_posregret
        self.strategy.policy[infoset] = probs

