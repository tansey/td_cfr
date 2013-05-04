import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from pokercfr import *
import random

class RestrictedNashResponse(CounterfactualRegretMinimizer):
    def __init__(self, rules, response_player, fixed_strategy_profile, prob_fixed):
        CounterfactualRegretMinimizer.__init__(self, rules)
        self.response_player = response_player
        self.fixed_profile = fixed_strategy_profile
        self.prob_fixed = prob_fixed

    def cfr_action_node(self, root, reachprobs):
        # Calculate strategy from counterfactual regret
        strategy = self.cfr_strategy_update(root, reachprobs)
        next_reachprobs = deepcopy(reachprobs)
        # Only real change is here. We allow the response player to respond fully, but the other players
        # are restricted to playing their fixed strategy some portion of the time
        if root.player == self.response_player:
            action_probs = { hc: strategy.probs(self.rules.infoset_format(root.player, hc, root.board, root.bet_history)) for hc in reachprobs[root.player] }
        else:
            action_probs = self.mix_probs(root, strategy, reachprobs)
        action_payoffs = [None, None, None]
        if root.fold_action:
            next_reachprobs[root.player] = { hc: action_probs[hc][FOLD] * reachprobs[root.player][hc] for hc in reachprobs[root.player] }
            action_payoffs[FOLD] = self.cfr_helper(root.fold_action, next_reachprobs)
        if root.call_action:
            next_reachprobs[root.player] = { hc: action_probs[hc][CALL] * reachprobs[root.player][hc] for hc in reachprobs[root.player] }
            action_payoffs[CALL] = self.cfr_helper(root.call_action, next_reachprobs)
        if root.raise_action:
            next_reachprobs[root.player] = { hc: action_probs[hc][RAISE] * reachprobs[root.player][hc] for hc in reachprobs[root.player] }
            action_payoffs[RAISE] = self.cfr_helper(root.raise_action, next_reachprobs)
        payoffs = []
        for player in range(self.rules.players):
            player_payoffs = { hc: 0 for hc in reachprobs[player] }
            for i,subpayoff in enumerate(action_payoffs):
                if subpayoff is None:
                    continue
                for hc,winnings in subpayoff[player].iteritems():
                    # action_probs is baked into reachprobs for everyone except the acting player
                    if player == root.player:
                        player_payoffs[hc] += winnings * action_probs[hc][i]
                    else:
                        player_payoffs[hc] += winnings
            payoffs.append(player_payoffs)
        # Update regret calculations
        self.cfr_regret_update(root, action_payoffs, payoffs[root.player])
        return payoffs

    def mix_probs(self, root, cfr_strategy, reachprobs):
        action_probs = { }
        for hc in reachprobs[root.player]:
            probs = [0,0,0]
            fixed_probs = self.fixed_profile.strategies[root.player].probs(self.rules.infoset_format(root.player, hc, root.board, root.bet_history))
            cfr_probs = cfr_strategy.probs(self.rules.infoset_format(root.player, hc, root.board, root.bet_history))
            for i in range(3):
                probs[i] = self.prob_fixed * fixed_probs[i] + (1.0 - self.prob_fixed) * cfr_probs[i]
            action_probs[hc] = probs
        return action_probs


