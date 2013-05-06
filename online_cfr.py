import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from environment import *
import random
import math

class OnlineCFRAgent(Agent):
    def __init__(self, rules, seat, gametree=None, exploration=0.5, exploration_decay=1, recency_weighting=False, policy_weight=0.001, policy_decay=1):
        Agent.__init__(self, rules, seat)
        self.onpolicy = Strategy(seat)
        self.strategy = self.offpolicy = Strategy(seat)
        self.gametree = gametree
        self.exploration = exploration
        self.exploration_decay = exploration_decay
        self.recency_weighting = recency_weighting
        self.policy_decay = policy_decay
        self.policy_weight = policy_weight
        if self.gametree is None:
            self.gametree = GameTree(rules)
        if self.gametree.root is None:
            self.gametree.build()
        self.onpolicy.build_default(self.gametree)
        self.offpolicy.build_default(self.gametree)
        self.hands_played = 0
        self.counterfactual_regret = { infoset: [0,0,0] for infoset in self.strategy.policy }
        self.action_reachprobs = { infoset: [0,0,0] for infoset in self.strategy.policy }
        self.infoset_visits = { infoset: 0 for infoset in self.strategy.policy }

    def episode_starting(self):
        # Store a history of (infoset, action, action_probs, prefixprob)
        self.episode_history = []
        self.reward = 0
        self.onpolicy_reachprob = 1.0
        self.offpolicy_reachprob = 1.0

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        for infoset,action,offpolicy_action_probs,offpolicy_prefixprob in self.episode_history:
            if offpolicy_prefixprob == 0 or offpolicy_action_probs[action] == 0:
                continue
            suffixprob = self.offpolicy_reachprob / (offpolicy_prefixprob * offpolicy_action_probs[action])
            w = self.reward * suffixprob / self.onpolicy_reachprob
            #print '{0} action: {1} probs: {2} offpolicy_prefix: {3:.5f} offpolicy_suffix: {4:.5f} w: {5:.5f} reward: {6} onpolicy_reach: {7:.5f} offpolicy_reach: {8:.5f}'.format(infoset, ['f','c','r'][action], action_probs, offpolicy_prefixprob, suffixprob, w, self.reward, self.onpolicy_reachprob, self.offpolicy_reachprob)
            self.counterfactual_regret[infoset][action] += w * (1.0 - offpolicy_action_probs[action])
            self.infoset_visits[infoset] = self.hands_played
        self.exploration *= self.exploration_decay
        self.hands_played += 1
        if self.recency_weighting:
            self.policy_weight *= self.policy_decay
        #print ''

    def set_infoset(self, infoset):
        self.infoset = infoset

    def get_action(self):
        probs = self.update_policy()
        if random.random() < self.exploration:
            action = self.random_action()
        else:
            action = self.onpolicy.sample_action(self.infoset)
        self.episode_history.append((self.infoset, action, probs, self.offpolicy_reachprob))
        self.offpolicy_reachprob *= probs[action]
        self.onpolicy_reachprob *= self.exploration / self.num_actions_available() + (1.0 - self.exploration) * probs[action]
        return action

    def random_action(self):
        a = random.randrange(0,3)
        node = self.gametree.information_sets[self.infoset][0]
        if (a == FOLD and node.fold_action is None) or (a == CALL and node.call_action is None) or (a == RAISE and node.raise_action is None):
            return self.random_action()
        return a

    def num_actions_available(self):
        return len(self.gametree.information_sets[self.infoset][0].children)

    def observe_reward(self, r):
        self.reward += r
        self.winnings += r

    def update_policy(self):
        # Get the current CFR
        prev_cfr = self.counterfactual_regret[self.infoset]
        # Get the total positive CFR
        sumpos_cfr = float(sum([max(0,x) for x in prev_cfr]))
        if sumpos_cfr == 0:
            # Default strategy is equal probability
            probs = self.equal_probs()
        else:
            # Use the strategy that's proportional to accumulated positive CFR
            probs = [max(0,x) / sumpos_cfr for x in prev_cfr]
        # Use the updated strategy as our current strategy
        self.onpolicy.policy[self.infoset] = probs
        # Update the weighted policy probabilities (used to recover the average strategy)
        for i in range(3):
            if self.recency_weighting:
                # Update the cumulative strategy using an exponential moving average
                self.action_reachprobs[self.infoset][i] = self.onpolicy_reachprob * probs[i] * self.policy_weight + (1.0 - self.policy_weight) * self.action_reachprobs[self.infoset][i]
            else:
                # Update the cumulative strategy using optimistic averaging (NIPS 2009, appendix)
                self.action_reachprobs[self.infoset][i] += self.onpolicy_reachprob * probs[i] * (self.hands_played - self.infoset_visits[self.infoset])
        if sum(self.action_reachprobs[self.infoset]) == 0:
            # Default strategy is equal weight
            self.offpolicy.policy[self.infoset] = self.equal_probs()
        else:
            # Recover the weighted average strategy
            self.offpolicy.policy[self.infoset] = [self.action_reachprobs[self.infoset][i] / sum(self.action_reachprobs[self.infoset]) for i in range(3)]
        # Return and use the current CFR strategy
        return probs

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