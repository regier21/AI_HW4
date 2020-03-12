  # -*- coding: latin-1 -*-
import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *


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
        super(AIPlayer,self).__init__(inputPlayerId, "Echo")
        #the coordinates of the agent's food and tunnel will be stored in these
        #variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None
        self.nextAttack = None
    
    ##
    #getPlacement 
    #
    # The agent uses a hardcoded arrangement for phase 1 to provide maximum
    # protection to the queen.  Enemy food is placed randomly.
    #
    def getPlacement(self, currentState):
        self.food = None
        self.tunnel = None
        self.queenProtectingWorkers = 10
        self.queenParked = False
        self.firstWorker = False
        self.firstDrone = False
        self.myAnthill = None
        self.highFood = 5
        if currentState.phase == SETUP_PHASE_1:
            return [(7,2), (2, 1), 
                    (0,3), (1,3), (2,3), (3,3),
                    (4,3), (5,3), (6,3),
                    (8,3), (9,3) ]
                    
        elif currentState.phase == SETUP_PHASE_2:
            me = currentState.whoseTurn
            #find the enemy constructions
            enemyAnthill = self.findEnemyConstruct(currentState, ANTHILL)
            enemyTunnel = self.findEnemyConstruct(currentState, TUNNEL)
            
            print("Enemy Anthill: " + str(enemyAnthill.coords) + " Enemy Tunnel: " 
                + str(enemyTunnel.coords))
            
            #build a list of all empty enemy spaces
            emptySpots = self.findEmptyEnemySpaces(currentState)
            
            #make a list of distances from each empty space to the enemy constructions
            distancesToConstr = []
            for coord in emptySpots:
                distanceToAnthill = stepsToReach(currentState, coord, enemyAnthill.coords)
                distanceToTunnel = stepsToReach(currentState, coord, enemyTunnel.coords)
                if (distanceToTunnel < distanceToAnthill):
                    distancesToConstr.append(distanceToTunnel)
                else:
                    distancesToConstr.append(distanceToAnthill)
            print(distancesToConstr)

            #make a list of distances to the border
            distancesToBorder = []
            for coord in emptySpots:
                distancesToBorder.append(coord[1]-6)
            print(distancesToBorder)

            #make a list of scores
            scores = []
            for x in range(len(emptySpots)):
                scores.append(distancesToConstr[x] - distancesToBorder[x])
            print(scores)

            #pick the two highest scores
            bestSpotIndex = self.pickHighestScore(emptySpots, scores, (-1,)) #pick highest score index
            bestSpotCoords = emptySpots[bestSpotIndex]
            nextBestSpotIndex = self.pickHighestScore(emptySpots, scores, (bestSpotIndex,)) #pick highest score again
            nextBestSpotCoords = emptySpots[nextBestSpotIndex]

            #make spaces non-empty
            currentState.board[bestSpotCoords[0]][bestSpotCoords[1]].constr == True
            currentState.board[nextBestSpotCoords[0]][nextBestSpotCoords[1]].constr == True

            #append the moves and return
            moves = []
            moves.append(bestSpotCoords)
            moves.append(nextBestSpotCoords)

            return moves


        else:            
            return None  #should never happen
    
    ##
    #getMove
    #
    # This agent will perform the following actions in the following order:
    #   1. Move the queen
    #   2. Build units
    #   3. Move workers
    #   4. Move fighters
    #   5. Ends turn
    ##
    def getMove(self, currentState):
        self.inv = getCurrPlayerInventory(currentState)
        self.state = currentState

        # Update overlays to reflect current state
        self.makeOverlays()

        # This will only occur the first time this method is called
        if (self.tunnel == None):
            self.me = currentState.whoseTurn
            self.tunnel = getConstrList(currentState, self.me, (TUNNEL,))[0]
            self.makeFoodPaths()
            self.fightTypeMultiplier = stepsToReach(currentState, (0, 9), self.inv.getAnthill().coords)
            self.anthill = self.inv.getAnthill()

        #if the queen hasn't moved, do so
        queen = self.inv.getQueen()
        if (not queen.hasMoved):
            return self.getQueenMove(queen)

        #if I have food and the anthill is empty, decide whether or not to make a unit
        anthill = self.inv.getAnthill()
        workers = getAntList(currentState, self.me, (WORKER,))
        soldiers = getAntList(currentState, self.me, (SOLDIER, DRONE))
        enemyCombatUnits = getAntList(currentState, 1-self.me, (DRONE, SOLDIER, R_SOLDIER))
        myCombatUnits = getAntList(currentState, self.me, (DRONE, SOLDIER, R_SOLDIER))
        if (not getAntAt(currentState, anthill.coords) and self.inv.foodCount >= 1):
            #At the start of the game, If I havent already, build a worker, then a drone as soon as possible
            if (self.firstWorker == False):
                self.firstWorker = True
                if (self.max_workers > 1):
                    return Move(BUILD, [anthill.coords], WORKER)
            if (self.firstDrone == False):
                if (self.inv.foodCount > 1):
                    self.firstDrone = True
                    return Move(BUILD, [anthill.coords], DRONE)

            #The usual behavior for the AI
            #Generally, the AI favors a more aggressive strategy, only  building workers to maintain its economic base
            #It will build soldiers if challenged by the enemy, but will build drones if no enemy units are present
            #It will not stock food, opting to overwhelm or at least match enemy forces
            if (self.firstWorker and self.firstDrone):
                if (len(enemyCombatUnits) > 0):
                    if (len(workers) >= self.max_workers):
                        if (self.inv.foodCount >= 2):
                            return Move(BUILD, [anthill.coords], SOLDIER)
                    else:
                        if (self.inv.foodCount >= self.highFood):
                            if (self.inv.foodCount >= 2):
                                return Move(BUILD, [anthill.coords], SOLDIER)
                        else:
                            if (self.queenProtectingWorkers != 0):
                                if (len(myCombatUnits) > 0):
                                    return Move(BUILD, [anthill.coords], WORKER)
                                else:
                                    if (self.inv.foodCount >= 2):
                                        return Move(BUILD, [anthill.coords], SOLDIER)
                            else:
                                if (len(myCombatUnits) > len(enemyCombatUnits)):
                                    return Move(BUILD, [anthill.coords], WORKER)
                                else:
                                    if (self.inv.foodCount >= 2):
                                        return Move(BUILD, [anthill.coords], SOLDIER)
                else:
                    if (len(workers) >= self.max_workers):
                        if (self.inv.foodCount >= 2):
                            return Move(BUILD, [anthill.coords], DRONE)
                    else:
                        if (self.inv.foodCount >= self.highFood):
                            if (self.inv.foodCount >= 2):
                                return Move(BUILD, [anthill.coords], DRONE)
                        else:
                            return Move(BUILD, [anthill.coords], WORKER)
        
        #Move all the workers
        for worker in workers:
            if worker.hasMoved:
                continue
            move = self.getWorkerMove(worker)
            if move != None:
                return move

        #Move all the fighters
        for fighter in myCombatUnits:
            if fighter.hasMoved:
                continue
            return self.getFighterMove(fighter)

        return Move(END)

    ##
    # getQueenMove
    #
    # Determines where the queen ought to move
    # 
    # Parameters:
    #   queen - the AI's queen
    #
    # Return: A Move object
    def getQueenMove(self, queen):
        paths = listAllMovementPaths(self.state, queen.coords, UNIT_STATS[QUEEN][MOVEMENT])
        paths = filter(lambda path: path[-1][1] < 4, paths) # Legal moves
        paths = list(filter(lambda path: self.isLivableMove(path, queen), paths))
        if (len(paths) == 0):
            # Give up, the queen will die
            return Move(END)
        if (self.queenParked):
            return Move(MOVE_ANT, [queen.coords])
        if (self.queenProtectingWorkers > 0):
            self.queenProtectingWorkers -= 1
            return self.getQueenProtectMove(queen, paths)
        else:
            return self.getQueenHoldMove(queen, paths)

    ##
    # getQueenProtectMove
    #
    # Called so queen can try to protect workers from early game rush
    #
    # Parameters:
    #   queen - the AI's queen
    #   paths - paths for moves the queen can consider taking
    #
    # Return: A Move object
    def getQueenProtectMove(self, queen, paths):
        # Always fight
        move = self.getQueenAttackMove(queen, paths)
        if move != None:
            return move
        else:
            clearPaths = list(filter(lambda path: not self.blocksWorker(path), paths))
            if (len(clearPaths) > 0):
                paths = clearPaths
            nonBlockingPaths = list(filter(lambda x: x[-1] != self.anthill.coords, paths))
            if (len(nonBlockingPaths) == 0):
                return Move(MOVE_ANT, paths[0])
            move = self.getWorkerEnterLoopMove(queen, nonBlockingPaths, self.endpoints_to)
            if move == None:
                return Move(MOVE_ANT, nonBlockingPaths[0])
            return move

    ##
    # getQueenHoldMove
    # 
    # Called so queen can hold the anthill
    #
    # Parameters:
    #   state - current game state
    #   queen - the AI's queen
    #   paths - paths for moves the queen can consider taking
    #
    # Return: A Move object
    def getQueenHoldMove(self, queen, paths):
        clearPaths = list(filter(lambda path: not self.blocksWorker(path), paths))
        if (len(clearPaths) > 0):
            paths = clearPaths
        safePaths = list(filter(lambda path: self.isUncontestedMove(path), paths))
        if (len(safePaths) == 0):
            # May as well fight
            move = self.getQueenAttackMove(queen, paths)
            if move != None:
                return move
            return self.getRetreatMove(queen, paths)
        # Move close to the anthill, but not on top of it (unless not possible)
        nonBlockingPaths = list(filter(lambda x: x[-1] != self.anthill.coords, paths))
        if (len(nonBlockingPaths) == 0):
            return Move(MOVE_ANT, paths[0])
        path = min(nonBlockingPaths, key=lambda path: stepsToReach(self.state, path[-1], self.anthill.coords))
        self.queenParked = True
        return Move(MOVE_ANT, path)

    ## Has queen make best attack possible; returns None if no attack possible
    def getQueenAttackMove(self, queen, paths):
        attacks = getAttacks(self.state, queen, paths)
        if (len(attacks) == 0):
            return None
        attack = max(attacks, key=lambda attack: self.valueFight(attack))
        self.nextAttack = attack[-1]
        return Move(MOVE_ANT, attack[:-1])

    ##
    # getWorkerMove
    # 
    # Determines what move a given worker should take
    # 
    # Parameters:
    #   worker - the worker to move
    #
    # Return: A Move object, or None if the worker ought not to move yet
    def getWorkerMove(self, worker):
        coords = worker.coords
        target_end = []
        target_path = []
        if worker.carrying:
            target_end = self.endpoints_from
            target_path = self.path_from
        else:
            target_end = self.endpoints_to
            target_path = self.path_to
        if (coords in target_end):
            start = target_path.index(coords)
            stop = start + 1
            moves = UNIT_STATS[WORKER][MOVEMENT]
            while moves > 0 and stop < len(target_path):
                cost = 1
                const = getConstrAt(self.state, target_path[stop])
                if const is not None:
                    cost = const.movementCost
                moves -= cost
                if moves >= 0:
                    if getAntAt(self.state, target_path[stop]) != None:
                        return None
                    stop += 1
            path = target_path[start:stop]
            return Move(MOVE_ANT, path)     
        else:
            paths = listAllMovementPaths(self.state, coords, UNIT_STATS[WORKER][MOVEMENT])
            move = self.getWorkerEnterLoopMove(worker, paths, target_end)
            if (move != None and len(move.coordList) > 1):
                return move
            return None

    ##
    # getFighterMove
    #
    # Determines what move a fighter (soldier or drone, untested on ranged) ought to take
    # This is one of the most complicated methods in the agent - it was designed to be
    #   versatile enough to handle a large variety of board states.
    #
    # Paramters:
    #   fighter - the fighter to move
    # 
    # Return: A Move object
    def getFighterMove(self, fighter):
        # Occupy the anthill
        paths = listAllMovementPaths(self.state, fighter.coords, UNIT_STATS[fighter.type][MOVEMENT], UNIT_STATS[fighter.type][IGNORES_GRASS])
        enemyAnthillCoords = getEnemyInv(None, self.state).getAnthill().coords
        for path in paths:
            if(path[-1] == enemyAnthillCoords):
                return Move(MOVE_ANT, path)

        # Kill if possible. This includes coordinating a kill with neighbors.
        attacks = getAttacks(self.state, fighter, paths)
        kills = self.getKills(attacks)
        if (len(kills) > 0):
            return self.getAttackMove(fighter, kills)

        # Attack the queen if possible.
        queenAttacks = list(filter(lambda attack: isQueenAttack(self.state, attack), attacks))
        if (len(queenAttacks) > 0):
            attack = queenAttacks[0] # We don't care which one
            self.nextAttack = attack[-1]
            return Move(MOVE_ANT, attack[:-1])

        # Try to live
        livePaths = list(filter(lambda path: self.isLivableMove(path, fighter), paths))
        if len(livePaths) == 0:
            # Go out with a bang or reposition in a place to be avenged most easily
            if len(attacks) > 0:
                return self.getAttackMove(fighter, attacks)
            return self.getRetreatMove(fighter, paths)
        paths = livePaths

        # Try to prevent losing
        # Prevent anthill siege
        anthillAnt = getAntAt(self.state, self.anthill.coords)
        if (anthillAnt != None and anthillAnt.player != self.me):
            return Move(MOVE_ANT, createPathToward(self.state, fighter.coords, self.anthill.coords, UNIT_STATS[fighter.type][MOVEMENT]))

        # Save the queen
        queen = getAntList(self.state, self.me, (QUEEN,))[0]
        x, y = queen.coords
        if self.enemyOverlay[y][x] > 0:
            # Queen in danger even after moving, which is bad
            return Move(MOVE_ANT, createPathToward(self.state, fighter.coords, queen.coords, UNIT_STATS[fighter.type][MOVEMENT]))

        # Find safe moves, which are where we can deal more damage to that square than the enemy
        safePaths = list(filter(lambda x: self.isSafeMove(x), paths))
        if (len(safePaths) == 0):
            # Treat this the same as if we were going to die
            attacks = filter(lambda attack: self.isLivableMove(attack[:-1], fighter), attacks)
            if len(attacks) > 0:
                return self.getAttackMove(fighter, attacks)
            else:
                return self.getRetreatMove(fighter, paths)
        else:
            # Take any safe attacks
            attacks = getAttacks(self.state, fighter, paths)
            if len(attacks) > 0:
                return self.getAttackMove(fighter, attacks)

            # At this point we are not attacking, we are merely repositioning
            # This will simply go for the nearest enemy worker in a safe path, if a worker yet lives
            them = 1 - self.me
            workers = getAntList(self.state, them, (WORKER,))
            if (len(workers) > 0):
                path = min(paths, key=lambda path: distanceToWorker(self.state, path[-1], them))
                return Move(MOVE_ANT, path)

            # Otherwise charge the anthill
            target = getEnemyInv(None, self.state).getAnthill().coords
            path = min(paths, key=lambda path: stepsToReach(self.state, path[-1], target))
            return Move(MOVE_ANT, path)          

    ## Finds and returns the best attack
    def getAttackMove(self, ant, attacks):
        attack = max(attacks, key=lambda x: self.valueFight(x))
        self.nextAttack = attack[-1]
        return Move(MOVE_ANT, attack[:-1])

    ## Moves to tile where ant can live (if possible) and most likely to be avenged
    def getRetreatMove(self, ant, paths):
        return Move(MOVE_ANT, max(paths, key=lambda x: self.homeOverlay[x[1]][x[0]]))

    ## Used to move a worker into the food loop
    # Ensures they do not block workers already gathering food
    def getWorkerEnterLoopMove(self, ant, paths, ends):
        paths = list(filter(lambda path: not self.blocksWorkerPath(path, ends), paths))
        if(len(paths) == 0):
            return None
        nearest = min(ends, key=lambda x: stepsToReach(self.state, x, ant.coords))
        path = min(paths, key=lambda path: stepsToReach(self.state, path[-1], nearest))
        return Move(MOVE_ANT, path)

    ## Returns whether a path will end at a tile more strongly controlled by you or your opponent
    def isSafeMove(self, path):
        x, y = path[-1]
        enemyControl = self.enemyOverlay[y][x]
        return enemyControl == 0 or self.homeOverlay[y][x] > enemyControl     

    ## Returns whether a path will end at a place where the ant must live
    def isLivableMove(self, path, ant):
        x, y = path[-1]
        return self.enemyOverlay[y][x] < ant.health

    ## Returns whether a path will end at a place where the enemy can do no damage
    def isUncontestedMove(self, path):
        x, y = path[-1]
        return self.enemyOverlay[y][x] == 0              
    
    ## Determine how good a fight is to take, with higher scores being better.
    def valueFight(self, fightPath):
        # Get the fight where the target is:
        #   Highest priority type
        #   Closest to anthill (taxicab distance)
        # Maximum distance to anthill + 1 stored in self.fightTypeMultiplier
        ant = getAntAt(self.state, fightPath[-1])
        typePriority = 0
        if ant.type == QUEEN:
            typePriority = 4
        elif ant.type == SOLDIER:
            typePriority = 3
        elif ant.type == R_SOLDIER:
            typePriority = 2
        elif ant.type == DRONE:
            typePriority = 1
        elif ant.type == WORKER:
            typePriority = 0
        else:
            raise ValueError("Unexpected ant type")

        return typePriority * self.fightTypeMultiplier + stepsToReach(self.state, ant.coords, getCurrPlayerInventory(self.state).getAnthill().coords)

    ##
    # getAttack
    #
    # Ideally, the target is picked when the move is selected and saved in self.nextAttack
    # If not, we attack arbitrarily
    #
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        if self.nextAttack in enemyLocations:
            return self.nextAttack
        return enemyLocations[0] # if we get here, we accidentially attacked. Great
        
    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

    ##
    # makeFoodPaths
    #
    # Creates the paths the workers use to gather food
    #
    # Parameters:
    #   state - the game state
    #
    # Return: None
    #
    # Side Effects:
    #   self.bestFood set to the closest food to the tunnel
    #   self.max_workers set to the max number of workers that can gather food
    #   self.path_to, self.endpoints_to set to the path from the food to the tunnel
    #       and vice versa for path_from and endpoints_from
    def makeFoodPaths(self):
        me = self.state.whoseTurn
        foods = getConstrList(self.state, None, (FOOD,))
        self.bestFood = foods[0]
        #find the food closest to the tunnel
        bestDistSoFar = 1000 #i.e., infinity
        for food in foods:
            # Ignore enemy food
            if food.coords[1] > 3:
                continue
            dist = stepsToReach(self.state, self.tunnel.coords, food.coords)
            if (dist < bestDistSoFar):
                self.bestFood = food
                bestDistSoFar = dist
        tunnel_loc = self.tunnel.coords
        food_loc = self.bestFood.coords

        # We need to pretend the worker is not on the tunnel so this works right
        fakeState = self.state.clone()
        worker = getAntAt(fakeState, tunnel_loc)
        fakeState.inventories[me].ants.remove(worker)

        self.path_to, self.endpoints_to = self.makeFoodPath(fakeState, tunnel_loc, food_loc, [])
        self.path_from, self.endpoints_from = self.makeFoodPath(fakeState, food_loc, tunnel_loc, self.path_to[1:])
        self.max_workers = len(self.endpoints_from) + len(self.endpoints_to) - 3

    ##
    # makeFoodPath
    #
    # Makes a path for workers to travel between points
    #
    # Parameters:
    #   state - the game state
    #   start - where the path should start
    #   end - where the path should end
    #   bans - list of tiles the path should not go through
    #
    # Return: A tuple consisting of
    #   The path
    #   The endpoints of the path for workers
    def makeFoodPath(self, state, start, end, bans):
        path = [start]
        endpoints = set()
        endpoints.add(start)
        bans = set(bans)
        while (path[-1] != end):
            options = listAllMovementPaths(state, path[-1], UNIT_STATS[WORKER][MOVEMENT])
            options = list(filter(lambda option: isValidPath(option[1:], bans), options)) # Should never fail
            if (len(options) == 0):
                pass
            best = min(options, key=lambda option: getWorkerPathRank(state, option, end))
            path += best[1:]
            endpoints.add(best[-1])
            for point in best:
                bans.add(point)
        return (path, endpoints)

    ##
    # makeOverlays
    #
    # Calculates how much damage each team can do to each tile
    # Used to find safe and dangerous moves for ants
    #
    # Return: None
    # 
    # Side Effects:
    #   self.homeOverlay, self.enemyOverlay, self.activeHomeOverlay set to 2D array of the damage
    #       the AI's ants can do, the enemy's ants can do, and the AI's ants that have
    #       yet to move can do, respectively. Arrays correspond to board positions.
    def makeOverlays(self):
        width = len(self.state.board)
        height = len(self.state.board[0])
        homeAnts = getCurrPlayerInventory(self.state).ants
        self.homeOverlay = [[0 for x in range(width)] for y in range(height)]
        self.makeOverlay(self.homeOverlay, homeAnts)
        self.activeHomeOverlay = [[0 for x in range(width)] for y in range(height)]
        self.makeOverlay(self.activeHomeOverlay, filter(lambda ant: not ant.hasMoved, homeAnts))
        self.enemyOverlay = [[0 for x in range(width)] for y in range(height)]
        self.makeOverlay(self.enemyOverlay, getEnemyInv(None, self.state).ants)

    ## Makes a single overlay - helper for makeOverlays
    def makeOverlay(self, overlay, ants):
        for ant in ants:
            if ant.type == WORKER:
                continue
            attackable = getAttackable(self.state, ant)
            damage = UNIT_STATS[ant.type][ATTACK]
            for x, y in attackable:
                overlay[y][x] += damage

    ## Finds attacks that can kill an ant
    def getKills(self, attacks):
        return list(filter(lambda x: self.isKillable(x[-1]), attacks))

    ## Returns whether AI's ants, working together, can kill an ant at a given square
    def isKillable(self, coord):
        x, y = coord
        ant = getAntAt(self.state, coord)
        if ant != None:
            return ant.health <= self.activeHomeOverlay[y][x]
        return False

    ## Determines whether path ends on a part of a worker path that is not in a set of endpoints
    #  Used to make paths for workers to enter the paths
    def blocksWorkerPath(self, path, ends):
        if path[-1] in ends:
            return False
        return self.blocksWorker(path)

    ## Determines whether path ends on a worker path
    def blocksWorker(self, path):
        return path[-1] in self.path_to or path[-1] in self.path_from

    ##
    #findEnemyConstruct
    #
    # finds specified enemy building of requested type. Can only search for ANTHILL or TUNNEL
    # at the moment because it returns a single item, and cannot return multiple items
    # returns None if encounters error
    #
    # Parameters: 
    #   currentState: current state of the game
    #   requestedType: type of constructs to search for
    #
    # Return:
    #   constr: the object of the named enemy construct searched for
    #
    def findEnemyConstruct(self, currentState, requestedType):
        print("Beginning FEC method")
        if (requestedType != ANTHILL and requestedType != TUNNEL):
            return None
        allConstrs = getConstrList(currentState, None, (requestedType,))
        enemyConstrs = []
        for constr in allConstrs:
            if (constr.coords[1] >= 6):
                enemyConstrs.append(constr)
        for constr in enemyConstrs:
            if (constr.type == requestedType):
                return constr


    #build a list of all empty enemy spaces
    def findEmptyEnemySpaces(self, currentState):
        emptySpots = []
        for x in range(10):
            for y in range(6, 10):
                constrAtSpace = getConstrAt(currentState, (x,y))
                if (constrAtSpace == None):
                    emptySpots.append((x,y))
        return emptySpots


    ##
    #pickHighestScore
    #
    #picks the highest score from the lists given
    #return the index of the best spot WITHOUT modifying the lists
    #
    #parameters:
    #   emptyspots: a list of all the empty spots to be judged
    #   scores: a list of the same size that contains the score of the corresponding spot, which entails 
    #           distance from the nearest enemy tunnel or anthill combined with its distance from the upper border
    #   previousScoreIndeces: the indeces of any previous scores that were selected from the list
    def pickHighestScore(self, emptySpots, scores, previousScoreIndeces):
        print(previousScoreIndeces)
        bestSpotValue = -1
        for x in range(len(emptySpots)):
            if (scores[x] > bestSpotValue and not(x in previousScoreIndeces)):
                bestSpotValue = scores[x]
                bestSpotIndex = x
        print("Best spot index: " + str(bestSpotIndex))
        return bestSpotIndex

## Gets all squares that can be attacked by an ant on their next move.
def getAttackable(state, ant):
    paths = listAllMovementPaths(state, ant.coords, UNIT_STATS[ant.type][MOVEMENT])
    dests = list(path[-1] for path in paths)
    result = set()
    for dest in dests:
        for loc in listAttackable(dest, UNIT_STATS[ant.type][RANGE]):
            if (getAntAt(state, loc) != None):
                result.add(loc)
    return result

## Gets all moves that result in an attack
# The return is a list consisting of a move path followed by an attack target
def getAttacks(state, ant, paths):
    # An attack is a path to an attack followed by the coordinate of the attack
    attacks = []
    for path in paths:
        dest = path[-1]
        for loc in listAttackable(dest, UNIT_STATS[ant.type][RANGE]):
            target = getAntAt(state, loc)
            if (target != None and target.player != state.whoseTurn):
                attacks.append(path + [loc])
    return attacks

## Determines whether an attack is attacking the enemy queen
def isQueenAttack(state, attack):
    ant = getAntAt(state, attack[-1])
    if ant != None and ant.type == QUEEN:
        return True
    return False

## Determines how far a location is from a given player's workers
def distanceToWorker(state, coord, pid):
    workers = getAntList(state, pid, (WORKER,))
    if (len(workers) == 0):
        return 0
    dists = map(lambda worker: stepsToReach(state, coord, worker.coords), workers)
    return min(dists)

## Gives a weight to how good a worker path is, with smaller better.
# Designed to make a path that moves to the food as fast as possible, then
#   stays as far away from the enemy as possible.
def getWorkerPathRank(state, path, targetCoords):
    if len(path) == 1:
        return 100000 # Infinity
    dist = stepsToReach(state, path[-1], targetCoords)
    # Since board size is 10, multiplying distances by 11 ensures that a shorter distance
    #  is always the top priority
    return dist * 11 * UNIT_STATS[WORKER][MOVEMENT]+ sum(map(lambda coord: coord[1], path))

## Determines if a path goes through any banned tiles
def isValidPath(path, bans):
    for coord in path:
        if coord in bans:
            return False
    return True