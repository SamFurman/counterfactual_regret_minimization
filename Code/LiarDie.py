"""
Use counterfactual regret minimization to play liar die
this is a second sequential game

Author: Samuel Furman
"""
import random
import sys
import pandas as pd
from matplotlib import pyplot as plt 

def buildEmptyArray(n,m):
    a = [0] * n
    for i in range(n):
        a[i] = [0] * m 

    return a

class Node():
    def __init__(self, numActions, *args, **kwargs):
        self.regretSum = [0] * numActions
        self.strategy = [0] * numActions
        self.strategySum = [0] * numActions
        self.u = 0
        self.pPlayer = 0
        self.pOpponent = 0

    def getStrategy(self):
        normalizingSum = 0
        for i in range(len(self.strategy)):
            self.strategy[i] = max(self.regretSum[i], 0)
            normalizingSum += self.strategy[i]

        for i in range(len(self.strategy)):
            if normalizingSum > 0:
                self.strategy[i] /= normalizingSum
            else:
                self.strategy[i] = 1/len(self.strategy)

        for i in range(len(self.strategy)):
            self.strategySum[i] += self.pPlayer * self.strategy[i]

        return self.strategy

    def getAverageStrategy(self):
        normalizingSum = 0
        for i in range(len(self.strategySum)):
            normalizingSum += self.strategySum[i]

        for i in range(len(self.strategySum)):
            if normalizingSum > 0:
                self.strategySum[i] /= normalizingSum
            else:
                self.strategySum[i] = 1 / len(self.strategySum)

        return self.strategySum

class LDTrainer():
    def __init__(self, sides, *args, **kwargs):
        self.DOUBT = 0
        self.ACCEPT = 1
        self.sides = sides
        self.responseNodes = buildEmptyArray(sides, sides + 1)
        self.claimNodes = buildEmptyArray(sides, sides + 1)

        for myClaim in range(sides + 1):
            for oppClaim in range(myClaim + 1, sides + 1):
                self.responseNodes[myClaim][oppClaim] = Node(1 if (oppClaim == 0 or oppClaim == sides) else 2)
        
        for oppClaim in range(sides):
            for roll in range(1, sides + 1):
                self.claimNodes[oppClaim][roll] = Node(sides - oppClaim)

    def train(self, iterations):
        regret = [0] * self.sides
        rollAfterAcceptingClaim = [0] * self.sides
        for epoch in range(iterations):

            #Initialize rolls and starting probabilities
            for i in range(len(rollAfterAcceptingClaim)):
                rollAfterAcceptingClaim[i] = random.randint(0, self.sides - 1) + 1
            self.claimNodes[0][rollAfterAcceptingClaim[0]].pPlayer = 1
            self.claimNodes[0][rollAfterAcceptingClaim[0]].pOpponent = 1

            #Accumulate realization weights forward
            for oppClaim in range(0, self.sides + 1):
                #visit response Nodes forward
                if oppClaim > 0:
                    for myClaim in range(0, oppClaim):
                        node = self.responseNodes[myClaim][oppClaim]
                        actionProb = node.getStrategy()
                        if oppClaim < self.sides:
                            nextNode = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                            nextNode.pPlayer += actionProb[1] * node.pPlayer
                            nextNode.pOpponent += node.pOpponent

                #visit claim nodes forward
                if oppClaim < self.sides:
                    node = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                    actionProb = node.getStrategy()
                    for myClaim in range(oppClaim + 1, self.sides + 1):
                        nextClaimProb = actionProb[myClaim - oppClaim - 1]
                        if nextClaimProb > 0:
                            nextNode = self.responseNodes[oppClaim][myClaim]
                            nextNode.pPlayer += node.pOpponent
                            nextNode.pOpponent += nextClaimProb * node.pPlayer

            #Backpropagate utilities, adjusting regrets and strategies
            for oppClaim in range(self.sides, -1, -1):
                #visit claim nodes backward
                if oppClaim < self.sides:
                    node = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                    actionProb = node.strategy
                    node.u = 0
                    for myClaim in range(oppClaim + 1, sides + 1):
                        actionIndex = myClaim - oppClaim - 1
                        nextNode = self.responseNodes[oppClaim][myClaim]
                        childUtil = - nextNode.u
                        regret[actionIndex] = childUtil
                        node.u += actionProb[actionIndex] * childUtil

                    for i in range(len(actionProb)):
                        regret[i] -= node.u
                        node.regretSum[i] += node.pOpponent * regret[i]

                    node.pPlayer = node.pOpponent = 0
                    
                #visit response nodes backward
                if oppClaim > 0:
                    for myClaim in range(0, oppClaim):
                        node = self.responseNodes[myClaim][oppClaim]
                        actionProb = node.strategy
                        node.u = 0
                        doubtUtil = 1 if (oppClaim > rollAfterAcceptingClaim[myClaim]) else -1
                        regret[self.DOUBT] = doubtUtil

                        if oppClaim < sides:
                            nextNode = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                            regret[self.ACCEPT] = nextNode.u
                            node.u += actionProb[self.ACCEPT] * nextNode.u

                        for i in range(len(actionProb)):
                            regret[i] -= node.u
                            node.regretSum[i] += node.pOpponent * regret[i]

                        node.pPlayer = node.pOpponent = 0

            #Reset strategy sums after half of training
            if epoch == iterations / 2:
                for row in self.responseNodes:
                    for n in row:
                        if n:
                            for i in range(len(n.strategySum)):
                                n.strategySum[i] = 0

                for row in self.claimNodes:
                    for n in row:
                        if n:
                            for i in range(len(n.strategySum)):
                                n.strategySum[i] = 0


        #print strats

        for initialRoll in range(1, sides + 1):
            print("Initial claim policy with roll {0:d}: ".format(initialRoll), end = '')
            for prob in self.claimNodes[0][initialRoll].getAverageStrategy():
                print('{0:.2f} '.format(prob), end = '')
            print('')
        
        print('\nOld Claim\tNew Claim\tAction Probabilities')
        for myClaim in range(0, sides + 1):
            for oppClaim in range(myClaim + 1, sides + 1):
                print('\t{0:d}\t{1:d}\t{2:s}\n'.format(myClaim, oppClaim, str(self.responseNodes[myClaim][oppClaim].getAverageStrategy())))

        print('\nOld Claim\tRoll\tAction Probabilities')
        for oppClaim in range(0, sides):
            for roll in range(1, sides + 1):
                print('\t{0:d}\t{1:d}\t{2:s}\n'.format(
                    oppClaim, 
                    roll, 
                    str(self.claimNodes[oppClaim][roll].getAverageStrategy()
                )))
                print('regrets', self.claimNodes[oppClaim][roll].regretSum)




if __name__ == "__main__":
    sides = 6
    iterations = 10000
    LDTrainer(6).train(iterations)