"""
Use counterfactual regret minimization to play rock paper scissors

The AVERAGE strategy profile converges to a solution NOT the FINAL solution

Author: Samuel Furman
"""
import random
import pandas as pd
from matplotlib import pyplot as plt 

class RPSTrainer():
    def __init__(self, *args, **kwargs):
        self.ROCK = 0
        self.PAPER = 1
        self.SCISSORS = 2
        self.NUM_ACTIONS = 3

        self.strategy = [0] * self.NUM_ACTIONS
        self.strategySum = [0] * self.NUM_ACTIONS
        self.regretSum = [0] * self.NUM_ACTIONS
        self.strats = []

        self.oppStrategy = [0] * self.NUM_ACTIONS
        self.oppStrategySum = [0] * self.NUM_ACTIONS
        self.oppRegretSum = [0] * self.NUM_ACTIONS
        self.oppStrats = []

    def getStrategy(self):
        normalizingSum = 0
        for i in range(self.NUM_ACTIONS):
            self.strategy[i] = max(self.regretSum[i], 0) 
            normalizingSum += self.strategy[i]
        
        for i in range(self.NUM_ACTIONS):
            if (normalizingSum > 0):
                self.strategy[i] /= normalizingSum
            else:
                self.strategy[i] = 1 / self.NUM_ACTIONS
            self.strategySum[i] += self.strategy[i]
        return self.strategy


    def getStrategyOpp(self):
        normalizingSum = 0
        for i in range(self.NUM_ACTIONS):
            self.oppStrategy[i] = max(self.oppRegretSum[i], 0) 
            normalizingSum += self.oppStrategy[i]
        
        for i in range(self.NUM_ACTIONS):
            if (normalizingSum > 0):
                self.oppStrategy[i] /= normalizingSum
            else:
                self.oppStrategy[i] = 1 / self.NUM_ACTIONS
            self.oppStrategySum[i] += self.oppStrategy[i]
        return self.oppStrategy


    def getAction(self, currStrategy):
        roll = random.uniform(0,1)
        probSum = 0
        option = 0

        while (probSum < roll):
            probSum += currStrategy[option]
            if(roll < probSum):
                break
            option += 1
        
        return option


    def computeUtilies(self, myAction, otherAction):
        actionUtility = [0] * self.NUM_ACTIONS
        actionUtility[otherAction] = 0 #tie
        actionUtility[0 if otherAction == self.NUM_ACTIONS - 1 else otherAction + 1] = 1 #win
        actionUtility[self.NUM_ACTIONS - 1 if otherAction == 0 else otherAction - 1] = -1 #loss
        return actionUtility


    def train(self, iterations, oppMode):
        fixedStrat = [.5,.3,.2]
        for epoch in range(iterations):
            currStrategy = self.getStrategy()
            oppCurrStrategy = self.getStrategyOpp() if oppMode == 1 else fixedStrat
            myAction = self.getAction(currStrategy)
            otherAction = self.getAction(oppCurrStrategy)
            utilities = self.computeUtilies(myAction, otherAction)
            oppUtilities = self.computeUtilies(otherAction, myAction)

            for i in range(self.NUM_ACTIONS):
                self.regretSum[i] += utilities[i] - utilities[myAction]
                self.oppRegretSum[i] += oppUtilities[i] - oppUtilities[otherAction]

            self.strats.append(self.getAverageStrategy())
            self.oppStrats.append(self.getOppAverageStrategy() if oppMode == 1 else fixedStrat)


    def getAverageStrategy(self):
        avgStrategy  = [0] * self.NUM_ACTIONS
        normalizingSum = 0
        for i in range(self.NUM_ACTIONS):
            normalizingSum += self.strategySum[i]
        for i in range(self.NUM_ACTIONS):
            if (normalizingSum > 0):
                avgStrategy[i] = self.strategySum[i] / normalizingSum
            else:
                avgStrategy[i] = 1 / NUM_ACTIONS

        return avgStrategy


    def getOppAverageStrategy(self):
        avgStrategy  = [0] * self.NUM_ACTIONS
        normalizingSum = 0
        for i in range(self.NUM_ACTIONS):
            normalizingSum += self.oppStrategySum[i]
        for i in range(self.NUM_ACTIONS):
            if (normalizingSum > 0):
                avgStrategy[i] = self.oppStrategySum[i] / normalizingSum
            else:
                avgStrategy[i] = 1 / self.NUM_ACTIONS

        return avgStrategy


    def getStratDataFrames(self):
        return (pd.DataFrame.from_records(self.strats, columns = ['Rock', 'Paper', 'Scissors']), 
        pd.DataFrame.from_records(self.oppStrats, columns = ['Rock', 'Paper', 'Scissors']))


    def visualizeStrategies(self):
        stratDF, _ = self.getStratDataFrames()
        index = stratDF.index.to_numpy()
        rocks = stratDF['Rock']
        papers = stratDF['Paper']
        scissors = stratDF['Scissors']
        plt.title('Convergence of Player Strategy when CFR vs Fixed')
        plt.ylabel('Action Probability')
        plt.xlabel('Training Iterations')
        plt.plot(index, rocks, label ='Rock')
        plt.plot(index, papers, label = 'Paper')
        plt.plot(index, scissors, label = 'Scissors')
        plt.legend(loc='upper right')
        plt.show()

    def visualizeOppStrategies(self):
        _, oppStratDF = self.getStratDataFrames()
        index = oppStratDF.index.to_numpy()
        rocks = oppStratDF['Rock']
        papers = oppStratDF['Paper']
        scissors = oppStratDF['Scissors']
        plt.title('Convergence of Opponent Strategy when CFR vs Fixed')
        plt.ylabel('Action Probability')
        plt.xlabel('Training Iterations')
        plt.plot(index, rocks, label ='Rock')
        plt.plot(index, papers, label = 'Paper')
        plt.plot(index, scissors, label = 'Scissors')
        plt.legend(loc='upper right')
        plt.show()

if __name__ == "__main__":
    trainer = RPSTrainer()
    trainer.train(100000, 0)
    trainer.visualizeStrategies()
    trainer.visualizeOppStrategies()