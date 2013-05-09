import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from environment import *
import random
import math

class TDCFRAgent(Agent):
    def __init__(self, rules, seat, gametree=None, exploration=0.5, exploration_decay=0.999, learning_rate=0.01, learning_rate_decay=0.99999):
        Agent.__init__(self, rules, seat)
        self.strategy = Strategy(seat)
        self.current_strategy = Strategy(seat)
        self.gametree = gametree
        self.exploration = exploration
        self.exploration_decay = exploration_decay
        self.learning_rate = learning_rate
        self.learning_rate_decay = learning_rate_decay
        self.winnings = 0
        if self.gametree is None:
            self.gametree = GameTree(rules)
        if self.gametree.root is None:
            self.gametree.build()
        self.strategy.build_default(self.gametree)
        self.current_strategy.build_default(self.gametree)
        self.hands_played = 0
        self.transition_probs = { }
        self.q_function = { }
        #self.avg_posregret = { }
        self.counterfactual_regret = { }
        self.action_reachprobs = { }
        self.node_visits = { }
        self.action_counts = { }
        for infoset,nodes in self.gametree.information_sets.iteritems():
            if nodes[0].player is seat:
                self.transition_probs[infoset] = [1.0 / len(nodes)]*len(nodes)
                self.q_function[infoset] = [self.initialize_q(infoset)] * len(nodes) # TODO: optimistic initialization?
                #self.avg_posregret[infoset] = [0,0,0]
                self.counterfactual_regret[infoset] = [0,0,0]
                self.action_reachprobs[infoset] = [0,0,0]
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
        self.reachprobs = 1

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        For now, we assume all imperfect information is revealed at the end of the episode.
        """
        self.hands_played += 1
        for infoset,action in self.episode_history:
            total_visits = sum(self.node_visits[infoset])
            #self.learning_rate = min(0.1, 1000.0 / max(1,total_visits))
            for i,node in enumerate(self.gametree.information_sets[infoset]):
                if node.holecards == state.holecards:
                    # we were in this state all along, so increase its probability and update the q function for the (s,a) pair
                    self.transition_probs[infoset][i] = 1.0 / (total_visits+1) * (total_visits * self.transition_probs[infoset][i] + 1)
                    self.q_function[infoset][i][action] = 1.0 / (self.action_counts[infoset][i][action]+1) * (self.action_counts[infoset][i][action] * self.q_function[infoset][i][action] + self.reward)
                    #self.transition_probs[infoset][i] = (1.0 - self.learning_rate) * self.transition_probs[infoset][i] + self.learning_rate
                    #self.q_function[infoset][i][action] = (1.0 - self.learning_rate) * self.q_function[infoset][i][action] + self.learning_rate * self.reward
                    self.node_visits[infoset][i] += 1
                    self.action_counts[infoset][i][action] += 1
                else:
                    # we were not in this state, so decrease its probability
                    self.transition_probs[infoset][i] = 1.0 / (total_visits+1) * (total_visits * self.transition_probs[infoset][i])
                    #self.transition_probs[infoset][i] *= 1.0 - self.learning_rate
        self.exploration *= self.exploration_decay
        self.learning_rate *= self.learning_rate_decay

    def set_infoset(self, infoset):
        self.infoset = infoset

    """
    def get_action(self):
        self.update_policy(self.infoset)
        if random.random() < self.exploration:
            action = self.random_action()
            self.episode_history = [(self.infoset, action)]
        else:
            #print 'Infoset: {0} Probs: {1} Posregrets: {2}'.format(self.infoset, self.strategy.probs(self.infoset), self.avg_posregret[self.infoset])
            action = self.strategy.sample_action(self.infoset)
            self.episode_history.append((self.infoset, action))
        return action
    """

    def get_action(self):
        probs = self.cfr_strategy_update()
        #print '{0}: {1} P: {2} Q(s,a): {3} CFR: {4}'.format(self.infoset, probs, self.transition_probs[self.infoset], self.q_function[self.infoset], self.counterfactual_regret[self.infoset])
        #print ''
        if random.random() < self.exploration:
            action = self.random_action()
            self.episode_history = [(self.infoset, action)]
        else:
            #print 'Infoset: {0} Probs: {1} Posregrets: {2}'.format(self.infoset, self.strategy.probs(self.infoset), self.avg_posregret[self.infoset])
            action = self.current_strategy.sample_action(self.infoset)
            self.episode_history.append((self.infoset, action))
        # Update the reach probability for this player
        self.reachprobs *= probs[action]
        # Update the regret using bootstrapped values
        payoffs = self.get_action_payoffs()
        ev = sum([probs[i] * payoffs[i] for i in range(3)])
        self.cfr_regret_update(payoffs, ev)
        return action

    def get_action_payoffs(self):
        payoffs = [0,0,0]
        for i,node in enumerate(self.gametree.information_sets[self.infoset]):
            for action in range(3):
                if not node.valid(action):
                    payoffs[action] = -1000
                    continue
                payoffs[action] += self.transition_probs[self.infoset][i] * self.q_function[self.infoset][i][action]
        return payoffs

    def random_action(self):
        a = random.randrange(0,3)
        node = self.gametree.information_sets[self.infoset][0]
        if (a == FOLD and node.fold_action is None) or (a == CALL and node.call_action is None) or (a == RAISE and node.raise_action is None):
            return self.random_action()
        return a

    def observe_reward(self, r):
        self.reward += r
        self.winnings += r

    """
    def update_policy(self, infoset):
        probs = self.strategy.probs(infoset)
        example_state = self.gametree.information_sets[infoset][0]
        winnings = [0,0,0]
        for i,node in enumerate(self.gametree.information_sets[infoset]):
            for action in range(3):
                winnings[action] += self.transition_probs[infoset][i] * self.q_function[infoset][i][action]
        ev = sum([probs[action] * winnings[action] for action in range(3)])
        posregrets = [max(0,winnings[action] - ev) for action in range(3)]
        infoset_visits = sum(self.node_visits[infoset])
        self.avg_posregret[infoset] = [1.0 / (infoset_visits+1) * (self.avg_posregret[infoset][action] * infoset_visits + posregrets[action]) for action in range(3)]
        #alpha = 0.00001
        #self.avg_posregret[infoset] = [(1.0 - alpha) * self.avg_posregret[infoset][action] + alpha * posregrets[action] for action in range(3)]
        total_posregret = sum(self.avg_posregret[infoset])
        probs = [0,0,0]
        if total_posregret == 0:
            probs = self.equal_probs()
        else:
            avg = self.avg_posregret[infoset]
            if example_state.fold_action:
                probs[FOLD] = avg[FOLD] / total_posregret
            if example_state.call_action:
                probs[CALL] = avg[CALL] / total_posregret
            if example_state.raise_action:
                probs[RAISE] = avg[RAISE] / total_posregret
        self.strategy.policy[infoset] = probs
    """

    def cfr_strategy_update(self):
        # Get the current CFR
        prev_cfr = self.counterfactual_regret[self.infoset]
        # Get the total positive CFR
        sumpos_cfr = float(sum([max(0,x) for x in prev_cfr]))
        # Use the updated strategy as our current strategy
        if sumpos_cfr == 0:
            # Default strategy is equal probability
            probs = self.equal_probs()
        else:
            # Use the strategy that's proportional to accumulated positive CFR
            probs = [max(0,x) / sumpos_cfr for x in prev_cfr]
        self.current_strategy.policy[self.infoset] = probs
        # Update the weighted policy probabilities (used to recover the average strategy)
        for i in range(3):
            self.action_reachprobs[self.infoset][i] = (self.learning_rate * self.reachprobs * probs[i]) + (1.0 - self.learning_rate) * self.action_reachprobs[self.infoset][i]
        if sum(self.action_reachprobs[self.infoset]) == 0:
            # Default strategy is equal weight
            self.strategy.policy[self.infoset] = self.equal_probs()
        else:
            # Recover the weighted average strategy
            self.strategy.policy[self.infoset] = [self.action_reachprobs[self.infoset][i] / sum(self.action_reachprobs[self.infoset]) for i in range(3)]
        # Return and use the current CFR strategy
        return probs

    def cfr_regret_update(self, action_payoffs, ev):
        for i,subpayoff in enumerate(action_payoffs):
            if subpayoff is None:
                continue
            immediate_cfr = subpayoff - ev
            self.counterfactual_regret[self.infoset][i] += immediate_cfr

    def num_actions_available(self):
        return len(self.gametree.information_sets[self.infoset][0].children)

    def equal_probs(self):
        total_actions = self.num_actions_available()
        node = self.gametree.information_sets[self.infoset][0]
        probs = [0,0,0]
        if node.fold_action:
            probs[FOLD] = 1.0 / total_actions
        if node.call_action:
            probs[CALL] = 1.0 / total_actions
        if node.raise_action:
            probs[RAISE] = 1.0 / total_actions
        return probs
