import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import os


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.turretLoc = [[3, 12], [24, 12], [7, 10], [11, 10], [16, 10], [20, 10]]
        self.wallLoc = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [11, 11], [16, 11]]
        self.supLoc = [[11, 9], [16, 9]]
        self.turretEnd = [
            [1, 12], [2, 12], [3, 12], [24, 12], [25, 12], [26, 12],
            [2, 11], [3, 11], [4, 11], [23, 11], [24, 11], [25, 11],
            [3, 10], [4, 10], [5, 10], [6, 10], [7, 10], [8, 10], [9, 10], [10, 10], [11, 10],
            [16, 10], [17, 10], [18, 10], [19, 10], [20, 10], [21, 10], [22, 10], [23, 10], [24, 10],
            [4, 9], [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [10, 9],
            [17, 9], [18, 9], [19, 9], [20, 9], [21, 9], [22, 9], [23, 9],
            [8, 5], [9, 5], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5], [18, 5], [19, 5],
            [9, 4], [10, 4], [11, 4], [12, 4], [13, 4], [14, 4], [15, 4], [16, 4], [17, 4], [18, 4],
            [10, 3], [11, 3], [12, 3], [13, 3], [14, 3], [15, 3], [16, 3], [17, 3]

        ]
        self.wallEnd = [
            [0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13],
            [15, 13], [16, 13], [17, 13], [18, 13], [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13],
            [4, 12], [5, 12], [6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12], [12, 12],
            [15, 12], [16, 12], [17, 12], [18, 12], [19, 12], [20, 12], [21, 12], [22, 12], [23, 12],
            [5, 11], [6, 11], [7, 11], [8, 11], [9, 11], [10, 11], [11, 11], [12, 11],
            [15, 11], [16, 11], [17, 11], [18, 11], [19, 11], [20, 11], [21, 11], [22, 11],
            [12, 10], [12, 9], [15, 10], [15, 9],
            [5, 8], [6, 8], [7, 8], [8, 8], [9, 8], [10, 8], [11, 8], [12, 8],
            [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 8], [21, 8], [22, 8],
            [7, 6], [8, 6], [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 6], [18, 6], [19, 6], [20, 6]
        ]
        self.attackLoc = {}

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.attempt_spawn(DEMOLISHER, [21, 7], 3)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

        self.attackLoc = {}


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.

            # Only spawn Scouts every other turn
            # Sending more at once is better since attacks can only hit a single scout at a time
            if game_state.turn_number % 2 == 1:
                # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[6, 7], [21, 7]]
                best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                game_state.attempt_spawn(SCOUT, best_location, 1000)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        game_state.attempt_spawn(WALL, self.wallLoc)
        game_state.attempt_spawn(TURRET, self.turretLoc)
        game_state.attempt_spawn(SUPPORT, self.supLoc)
        self.rebuildDef(game_state)
        self.buildNewDef(game_state)

    def rebuildDef(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        turrets = []
        upgradeTur = []
        for x,y in self.turretLoc:
            if len(game_state.game_map[x, y]) == 1:
                turret = game_state.game_map[x, y][0]
                if self.canBeDestroyed(game_state, turret):
                    if not(turret.upgraded) and self.shouldUpgradeInstead(game_state, turret):
                        upgradeTur.append(turret)
                    else:
                        turrets.append(turret)
            else:
                game_state.attempt_spawn(TURRET, [[x, y]])
        turrets.sort(key=lambda x: x.health)
        upgradeTur.sort(key=lambda x: x.health)

        walls = []
        upgradeWall = []
        for x,y in self.wallLoc:
            if len(game_state.game_map[x, y]) == 1:
                wall = game_state.game_map[x, y][0]
                if self.canBeDestroyed(game_state, wall):
                    if not(wall.upgraded) and self.shouldUpgradeInstead(game_state, wall):
                        upgradeWall.append(wall)
                    else:
                        walls.append(wall)
            else:
                spawn = [[x, y]]
                game_state.attempt_spawn(WALL, [[x, y]])
        walls.sort(key=lambda x: x.health)
        upgradeWall.sort(key=lambda x: x.health)
        
        remove = []
        for turret in turrets:
            if turret.health <= 40:
                remove.append([turret.x, turret.y])

        for wall in walls:
            if wall.health <= 40:
                remove.append([wall.x, wall.y])

        if len(remove) > 0:
            game_state.attempt_remove(remove)

        for wall in upgradeWall:
            game_state.attempt_upgrade([[wall.x, wall.y]])
        for turret in upgradeTur:
            game_state.attempt_upgrade([[turret.x, turret.y]])

    def canBeDestroyed(self, game_state, struc):
        opMP = game_state._player_resources[1]['MP'] + 4
        demolisher = math.floor(opMP/3)
        scout = opMP % 3
        totalAttack = (demolisher * 8 * 18) + (scout * 2 * 7)
        if struc.health < totalAttack:
            return True
        return False

    def shouldUpgradeInstead(self, game_state, struc):
        addHealth = 40 if struc.unit_type == 'DF' else 140
        opMP = game_state._player_resources[1]['MP'] + 4
        demolisher = math.floor(opMP/3)
        scout = opMP % 3
        totalAttack = (demolisher * 8 * 18) + (scout * 2 * 7)
        if struc.health + addHealth < totalAttack:
            return False
        return True

    def buildNewDef(self, game_state):
        top5 = []
        count = 0;
        while self.attackLoc and count < 5:
            maxAttack = max(self.attackLoc, key=lambda key:self.attackLoc[key])
            del self.attackLoc[maxAttack]
            loc = maxAttack.split(',')
            loc[0] = int(loc[0])
            loc[1] = int(loc[1])
            top5.append(self.getClosest(game_state, loc))
            count += 1

        curSP = game_state._player_resources[0]['SP']
        index = [[0] * 2] * len(top5)
        topIndex = 0
        while curSP >= 1 and len(top5) != 0:
            curTurret = top5[topIndex][0][index[topIndex][0]][:2]
            curWall = top5[topIndex][1][index[topIndex][1]][:2]
            if game_state.attempt_spawn(TURRET, [curTurret]) == 1:
                gamelib.debug_write("SPAWNED")
                self.turretLoc.append(curTurret)
                curSP -= 2
            elif game_state.attempt_upgrade([curTurret]) == 1:
                curSP -= 4
            if game_state.attempt_spawn(WALL, [curWall]) == 1:
                self.wallLoc.append(curWall)
                curSP -= 1
            elif game_state.attempt_upgrade([curWall]) == 1:
                curSP -= 2
            if index[topIndex][0] + 1 == len(top5[topIndex][0]) or index[topIndex][1] + 1 == len(top5[topIndex][1]):
                break
            index[topIndex][0] += 1
            index[topIndex][1] += 1 
            topIndex = topIndex + 1 if topIndex < len(top5) - 1 else 0

    def getClosest(self, game_state, loc):
        turrets = self.turretEnd.copy()
        walls = self.wallEnd.copy()

        for i in range(1, len(self.turretEnd)):
            if len(turrets[i]) < 3:
                dist = self.calcDist(loc, turrets[i])
                turrets[i].append(dist)
            key = turrets[i]    
            j = i-1
            while j >= 0:
                if len(turrets[j]) < 3:
                    dist = self.calcDist(loc, turrets[j])
                    turrets[j].append(dist)
                if key[2] > turrets[j][2]:
                    break
                turrets[j+1] = turrets[j]
                j -= 1
            turrets[j+1] = key

        for i in range(1, len(self.wallEnd)):
            if len(walls[i]) < 3:
                dist = self.calcDist(loc, walls[i])
                walls[i].append(dist)
            key = walls[i]    
            j = i-1
            while j >= 0:
                if len(walls[j]) < 3:
                    dist = self.calcDist(loc, walls[j])
                    walls[j].append(dist)
                if key[2] > walls[j][2]:
                    break
                walls[j+1] = walls[j]
                j -= 1
            walls[j+1] = key
        
        return [turrets, walls]

            
    def calcDist(self, loc1, loc2):
        return math.sqrt( ((loc1[0]-loc2[0])**2)+((loc1[1]-loc2[1])**2) )

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        damages = events["damage"]

        for damage in damages:
            if damage[4] == 1:
                if (damage[2] == 0) or (damage[2] == 2):
                    key = str(damage[0][0]) + ',' + str(damage[0][1])
                    if key in self.attackLoc:
                        self.attackLoc[key] += 1
                    else:
                        self.attackLoc[key] = 1

        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                self.scored_on_locations.append(location)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
