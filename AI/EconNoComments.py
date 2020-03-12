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
        super(AIPlayer,self).__init__(inputPlayerId, "Economy Destroyer No Comments")
        #the coordinates of the agent's food and tunnel will be stored in these
        #variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None
        self.nextAttack = None
    
    def getPlacement(self, currentState):
        self.food = None
        self.tunnel = None
        self.queenProtectingWorkers = 10
        if currentState.phase == SETUP_PHASE_1:
            return [(7,2), (2, 1), 
                    (0,3), (1,3), (2,3), (3,3),
                    (4,3), (5,3), (6,3),
                    (8,3), (9,3) ]
                    
        elif currentState.phase == SETUP_PHASE_2:
            allConstr = getConstrList(currentState, None, (ANTHILL, TUNNEL))
            #find the enemy constructions
            enemyConstr = []
            for constr in allConstr:
                if (constr.coords[1] >= 6):
                    enemyConstr.append(constr)
            if (enemyConstr[0].type == ANTHILL):
                enemyAnthill = enemyConstr[0]
                enemyTunnel = enemyConstr[1]
            else:
                enemyAnthill = enemyConstr[1]
                enemyTunnel = enemyConstr[0]
            
            #build a list of all empty enemy spaces
            emptySpots = []
            for x in range(10):
                for y in range(6, 10):
                    constrAtSpace = getConstrAt(currentState, (x,y))
                    if (constrAtSpace == None):
                        emptySpots.append((x,y))
            
            #make a list of distances to the enemy spaces
            distancesToConstr = []
            for coord in emptySpots:
                distanceToAnthill = stepsToReach(currentState, coord, enemyAnthill.coords)
                distanceToTunnel = stepsToReach(currentState, coord, enemyTunnel.coords)
                if (distanceToTunnel < distanceToAnthill):
                    distancesToConstr.append(distanceToTunnel)
                else:
                    distancesToConstr.append(distanceToAnthill)

            #make a list of distances to the border
            distancesToBorder = []
            for coord in emptySpots:
                distancesToBorder.append(coord[1]-6)

            #make a list of scores
            scores = []
            for x in range(len(emptySpots)):
                scores.append(distancesToConstr[x] - distancesToBorder[x])

            #pick the two highest scores
            bestSpotValue = -1
            bestSpot = (0,0)
            for x in range(len(emptySpots)):
                if (scores[x] > bestSpotValue):
                    bestSpotValue = scores[x]
                    bestSpot = emptySpots[x] 

            bestSpotValue = -1
            nextBestSpot = (0,0)
            for x in range(len(emptySpots)):
                if (scores[x] > bestSpotValue and emptySpots[x] != bestSpot):
                    bestSpotValue = scores[x]
                    nextBestSpot = emptySpots[x]

            #make spaces non-empty
            currentState.board[bestSpot[0]][bestSpot[1]].constr == True
            currentState.board[nextBestSpot[0]][nextBestSpot[1]].constr == True

            #append the moves and return
            moves = []
            moves.append(bestSpot)
            moves.append(nextBestSpot)

            return moves

        else:            
            return None  #should never happen
    

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

        #if I have food and the anthill is empty, make a worker
        workers = getAntList(currentState, self.me, (WORKER,))
        fighters = getAntList(currentState, self.me, (SOLDIER,DRONE))
        if (not getAntAt(currentState, self.anthill.coords)):
            if (self.inv.foodCount >= 1 and len(workers) < self.max_workers):
                return Move(BUILD, [self.anthill.coords], WORKER)
            elif (self.inv.foodCount >= 2 and len(fighters) < 3):
                return Move(BUILD, [self.anthill.coords], SOLDIER)
        
        #Move all the workers
        for worker in workers:
            if worker.hasMoved:
                continue
            move = self.getWorkerMove(worker)
            if move != None:
                return move

        #Move all the fighters
        for fighter in fighters:
            if fighter.hasMoved:
                continue
            return self.getFighterMove(fighter)

        return Move(END)

    def getQueenMove(self, queen):
        paths = listAllMovementPaths(self.state, queen.coords, UNIT_STATS[QUEEN][MOVEMENT])
        paths = filter(lambda path: path[-1][1] < 4, paths) # Legal moves
        paths = list(filter(lambda path: self.isLivableMove(path, queen), paths))
        if (len(paths) == 0):
            # Give up, the queen will die
            return Move(END)
        if (self.queenProtectingWorkers > 0):
            self.queenProtectingWorkers -= 1
            return self.getQueenProtectMove(queen, paths)
        else:
            return self.getQueenHoldMove(queen, paths)

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
        return Move(MOVE_ANT, path)

    ## Has queen make best attack possible; returns None if no attack possible
    def getQueenAttackMove(self, queen, paths):
        attacks = getAttacks(self.state, queen, paths)
        if (len(attacks) == 0):
            return None
        attack = max(attacks, key=lambda attack: self.valueFight(attack))
        self.nextAttack = attack[-1]
        return Move(MOVE_ANT, attack[:-1])

    def getWorkerMove(self, worker):
        coords = worker.coords
        path = []
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
        move = self.getDefensiveMove(fighter, paths)
        if move != None:
            return move

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
            return self.getSafeMove(fighter, safePaths)

    def getDefensiveMove(self, ant, paths):
        # Prevent anthill siege
        anthillAnt = getAntAt(self.state, self.anthill.coords)
        if (anthillAnt != None and anthillAnt.player != self.me):
            return Move(MOVE_ANT, createPathToward(self.state, ant.coords, self.anthill.coords, UNIT_STATS[ant.type][MOVEMENT]))

        # Save the queen
        queen = getAntList(self.state, self.me, (QUEEN,))[0]
        x, y = queen.coords
        if self.enemyOverlay[y][x] > 0:
            # Queen in danger even after moving, which is bad
            return Move(MOVE_ANT, createPathToward(self.state, ant.coords, queen.coords, UNIT_STATS[ant.type][MOVEMENT]))

        return None

    def getSafeMove(self, ant, paths):
        # Take any safe attacks
        attacks = getAttacks(self.state, ant, paths)
        if len(attacks) > 0:
            return self.getAttackMove(ant, attacks)

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

    def getAttack(self, currentState, attackingAnt, enemyLocations):
        if self.nextAttack in enemyLocations:
            return self.nextAttack
        return enemyLocations[0] # if we get here, we accidentially attacked. Great

    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

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

def getAttackable(state, ant):
    paths = listAllMovementPaths(state, ant.coords, UNIT_STATS[ant.type][MOVEMENT])
    dests = list(path[-1] for path in paths)
    result = set()
    for dest in dests:
        for loc in listAttackable(dest, UNIT_STATS[ant.type][RANGE]):
            if (getAntAt(state, loc) != None):
                result.add(loc)
    return result

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

def isQueenAttack(state, attack):
    ant = getAntAt(state, attack[-1])
    if ant != None and ant.type == QUEEN:
        return True
    return False

def distanceToWorker(state, coord, pid):
    workers = getAntList(state, pid, (WORKER,))
    if (len(workers) == 0):
        return 0
    dists = map(lambda worker: stepsToReach(state, coord, worker.coords), workers)
    return min(dists)

def getWorkerPathRank(state, path, targetCoords):
    if len(path) == 1:
        return 100000 # Infinity
    dist = stepsToReach(state, path[-1], targetCoords)
    # Since board size is 10, multiplying distances by 11 ensures that a shorter distance
    #  is always the top priority
    return dist * 11 * UNIT_STATS[WORKER][MOVEMENT]+ sum(map(lambda coord: coord[1], path))

def isValidPath(path, bans):
    for coord in path:
        if coord in bans:
            return False
    return True