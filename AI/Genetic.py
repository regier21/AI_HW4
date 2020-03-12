import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

NUM_GENES = 6 # Should be even
NUM_GAMES = 1

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Genetic")
        #three instant vars
        self.genes = []
        self.fitnesses = []
        self.nextGeneIndex = 0
        self.gameIndex = 0

    def initGenes(self):
        for i in range(NUM_GENES):
            self.genes.append(Gene([], True))
            self.fitnesses.append(0.0)

    def reproduce(self):
        newGenes = []

        totalFitness = sum(self.fitnesses)
        for i in range(NUM_GENES / 2):
            parent1 = random.random()
            parent2 = random.random()
            p1gene = p2gene = None
            for i, fitness in enumerate(self.fitnesses):
                total += fitness / totalFitness
                if total > parent1 and parent1 > prev:
                    p1gene = self.genes[i]
                if total > parent2 and parent2 > prev:
                    p2gene = self.genes[i]
                prev = total
            gene1, gene2 = p1gene.mateWith(p2gene)
            newGenes.append(gene1)
            newGenes.append(gene2)

        self.dna = newGenes
        
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            return self.genes[self.nextGeneIndex].getOurConstrs()
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            return self.genes[self.nextGeneIndex].getEnemyFood()
        else:
            return [(0, 0)]
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        moves = listAllLegalMoves(currentState)
        selectedMove = moves[random.randint(0,len(moves) - 1)];

        #don't do a build move if there are already 3+ ants
        numAnts = len(currentState.inventories[currentState.whoseTurn].ants)
        while (selectedMove.moveType == BUILD and numAnts >= 3):
            selectedMove = moves[random.randint(0,len(moves) - 1)];
            
        return selectedMove
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        self.gameIndex += 1
        if self.gameIndex == NUM_GAMES:
            self.gameIndex = 0

            # TODO: Calculate and set fitness

            self.nextGeneIndex += 1
            if self.nextGeneIndex == NUM_GENES:
                self.reproduce()
                self.nextGeneIndex = 0

NUM_GRASS = 9
NUM_ENEMY_FOOD = 2
ENEMY_COORD_OFFSET = 6
PROB_MUTATION = 0.25
class Gene:

    def __init__(self, dna, rand=False):
        if not rand:
            self.dna = dna # Array of integers
        
        self.dna = []
        self.dna.append(getRandCoord()) # Anthill
        self.dna.append(getRandCoord()) # Tunnel
        for i in range(NUM_GRASS):
            self.dna.append(getRandCoord())
        for i in range(NUM_ENEMY_FOOD):
            x, y = getRandCoord()
            self.dna.append((x, y + ENEMY_COORD_OFFSET))

    def getOurConstrs(self):
        coords = self.dna[:-NUM_ENEMY_FOOD]
        usedCoords = set()
        for i in range(0, len(coords), 2):
            x = coords[i]
            y = coords[i + 1]
            coord = (x, y)
            while coord in usedCoords:
                x += 1
                if x >= X_RANGE:
                    x = 0
                    y += 1
                    y %= Y_RANGE
                coord = (x, y)
            coords[i] = coord
            usedCoords.add(coord)
        return coords

    def getEnemyFood(self):
        coords = self.dna[-NUM_ENEMY_FOOD:]
        usedCoords = set()
        for i in range(0, len(coords), 2):
            x = coords[i]
            y = coords[i + 1]
            coord = (x, y)
            while coord in usedCoords:
                x += 1
                if x >= X_RANGE:
                    x = 0
                    y += 1
                    if y == ENEMY_COORD_OFFSET + Y_RANGE - 1:
                        y = ENEMY_COORD_OFFSET
                coord = (x, y)
            coords[i] = coord
            usedCoords.add(coord)
        return coords

    def mutate(self):
        if random.random() <= PROB_MUTATION:
            index = random.randint(len(self.dna))
            if index % 2 == 0:
                self.dna[index] = random.randint(0, X_RANGE - 1)
            elif len(self.dna) - index <= NUM_ENEMY_FOOD:
                self.dna[index] = random.randint(0, Y_RANGE - 1) + ENEMY_COORD_OFFSET
            else:
                self.dna[index] = random.randint(0, Y_RANGE - 1)

    def mateWith(self, other):
        size = len(self.dna)
        crossover = random.randint(0, size)
        child1 = Gene(self.dna[:crossover] + other.dna[crossover:])
        child1.mutate()
        child2 = Gene(other.dna[:crossover] + self.dna[crossover:])
        child2.mutate()
        return (child1, child2)
        

X_RANGE = 10
Y_RANGE = 4
def getRandCoord():
    return (random.randint(0, X_RANGE - 1), random.randint(0, Y_RANGE - 1))
