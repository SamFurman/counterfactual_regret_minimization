"""
Use counterfactual regret minimization to play kuhn poker
Jump from one-shot games to sequential games

Author: Samuel Furman
"""

import random
import pandas as pd
from matplotlib import pyplot as plt 
NUM_ACTIONS = 2

class Node():
    def __init__(self, *args, **kwargs):
        self.infoSet = ''
        self.regretSum = [0] * NUM_ACTIONS
        self.strategy = [0] * NUM_ACTIONS
        self.strategySum = [0] * NUM_ACTIONS


    def getStrategy(self, realizationWeight):
        normalizingSum = 0
        for i in range(NUM_ACTIONS):
            self.strategy[i] = max(self.regretSum[i], 0)
            normalizingSum += self.strategy[i]
        
        for i in range(NUM_ACTIONS):
            if normalizingSum > 0:
                self.strategy[i] /= normalizingSum
            else:
                self.strategy[i] = 1 / NUM_ACTIONS
            self.strategySum[i] += realizationWeight * self.strategy[i]
        
        return self.strategy


    def getAverageStrategy(self):
        avgStrategy = [0] * NUM_ACTIONS
        normalizingSum = 0

        for i in range(NUM_ACTIONS):
            normalizingSum += self.strategySum[i]

        for i in range(NUM_ACTIONS):       
            if normalizingSum > 0:
                avgStrategy[i] = self.strategySum[i] / normalizingSum
            else:
                avgStrategy[i] = 1 / NUM_ACTIONS
        
        return avgStrategy

    def toString(self):
        def specialRound(num):
            threshhold = .0001
            if 1 - num < threshhold:
                return 1
            elif num < threshhold:
                return 0
            elif abs(.5 - num) < threshhold:
                return .5

            return num

        def cleanStrat(strat):
            return [specialRound(x) for x in strat]

        return '{0:4s}: {1:s}'.format(self.infoSet, str(cleanStrat(self.getAverageStrategy())))

class KPTrainer():
    def __init__(self, *args, **kwargs):
        self.PASS = 0
        self.BET = 1
        self.nodeMap = {}

    def train(self, iterations):
        cards = [1,2,3]
        util = 0
        for epoch in range(iterations):
            cards = self.shuffleCards(cards)
            util += self.cfr(cards, '', 1, 1)

        print("Average game value:", util/iterations)
        for _,v in sorted(self.nodeMap.items()):
            print(v.toString())
        
    def shuffleCards(self, cards):
        for c1 in range(len(cards) - 1, 0, -1):
            c2 = random.randint(0, c1)
            tmp = cards[c1]
            cards[c1] = cards[c2]
            cards[c2] = tmp

        return cards

    def cfr(self, cards, history, p0, p1):
        def terminalPayoff(crds, hist, plys, playr, opp):
            terminalPass = history[-1] == 'p'
            doubleBet = history[-2:] == 'bb'
            isPlayerCardHigher = crds[playr] > crds[opp]

            if (terminalPass):
                if hist == 'pp':
                    return 1 if isPlayerCardHigher else -1
                else:
                    return 1
            elif doubleBet:
                return 2 if isPlayerCardHigher else -2
            
            return None

        def updateInfoSet(infoS):
            node = self.nodeMap.get(infoS, None)
            if (node == None):
                node = Node()
                node.infoSet = infoS
                self.nodeMap[infoS] = node
            
            return node

        plays = len(history)
        player = plays % 2 
        opponent = 1 - player

        #check if we are at a terminal state
        if plays > 1:
            payoff = terminalPayoff(cards, history, plays, player, opponent)
            if payoff:
                return payoff


        infoSet = str(cards[player]) + history
        node = updateInfoSet(infoSet)

        #recursively call cfr with additional history and probability
        strategy = node.getStrategy(p0 if player == 0 else p1)
        util = [0] * NUM_ACTIONS
        nodeUtil = 0
        for i in range(NUM_ACTIONS):
            nextHistory = history + ('p' if i == self.PASS else 'b')
            if player == 0:
                util[i] = self.cfr(cards, nextHistory, p0 * strategy[i], p1)
            else:      
                util[i] = self.cfr(cards, nextHistory, p0, p1 * strategy[i])

            nodeUtil += strategy[i] * util[i]

        #accumlate regret
        for i in range(NUM_ACTIONS):
            regret = util[i] - nodeUtil
            node.regretSum[i] += (p1 if player == 0 else p0) * regret

        return nodeUtil


if __name__ == "__main__":
    KPTrainer().train(1000000)