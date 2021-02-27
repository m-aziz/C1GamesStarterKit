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
        self.turretStart = [[3, 12], [24, 12], [7, 10], [11, 10], [16, 10], [20, 10]]
        self.wallStart = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [11, 11], [16, 11]]
        self.supStart = [[11, 9], [16, 9]]

        self.turretCur = []
        self.wallCur = []
        self.supCur = []

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

        self.turretDeath = []
        self.wallDeath = []

        self.turretRefund = []

        self.attackingUnitLoc = {}
        self.healthDmgByLoc = {}
        self.dmgTakenLoc = {}
        
    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.attempt_spawn(DEMOLISHER, [21, 7], 1)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        
        self.starter_strategy(game_state)

        game_state.submit_turn()

        self.attackingUnitLoc = {}
        self.healthDmgByLoc = {}
        self.dmgTakenLoc = {}

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    # def calcIdle(self):
        

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
        if game_state.turn_number == 0:
            numWall = game_state.attempt_spawn(WALL, self.wallStart)
            numTur = game_state.attempt_spawn(TURRET, self.turretStart)
            numSup = game_state.attempt_spawn(SUPPORT, self.supStart)
            self.turretCur = self.turretStart[:numTur]
            self.wallCur = self.wallStart[:numWall]
            self.supCur = self.supStart[:numSup]
        else:
            self.buildRefundDef(game_state)
            self.rebuildDef(game_state)
            self.buildNewDef(game_state)
            self.removeDef(game_state)

    def buildRefundDef(self, game_state):
        if self.turretRefund:
            for turret in self.turretRefund:
                if game_state.attempt_spawn(TURRET, [turret[:2]]) == 1:
                    self.turretCur.append(turret[:2].copy())
                if turret[2] == 1:
                    game_state.attempt_upgrade([turret[:2]])

        self.turretRefund = []
        
    def removeDef(self, game_state):
        # refund logic
        maxDmg = 0
        curSP = game_state._player_resources[0]["SP"]
        if self.healthDmgByLoc:
            maxKey = max(self.healthDmgByLoc, key=lambda key: self.healthDmgByLoc[key][2])
            maxDmg = self.healthDmgByLoc[maxKey][2]

        remove = []
        for wall in self.wallCur:
            curWall = game_state.game_map[wall][0]
            if (curWall.health < curWall.max_health and curWall.health < maxDmg and maxDmg < curWall.max_health):
                game_state.attempt_remove([wall])
                refund = 2.7 if curWall.upgraded else 0.97
                curSP += refund * (curWall.health / curWall.max_health)
                remove.append(wall)
        for wall in remove:
            self.wallCur.remove(wall)
        
        for turret in self.turretCur:
            curTurret = game_state.game_map[turret][0]
            if (curTurret.health < curTurret.max_health and curTurret.health < maxDmg and maxDmg < curTurret.max_health):
                refund = 5.4 if curTurret.upgraded else 1.94
                cost = 6 if curTurret.upgraded else 2
                if curSP + refund >= cost:
                    curSP += refund
                    game_state.attempt_remove([turret])
                    self.turretRefund.append(turret.copy())
                    if curTurret.upgraded:
                        self.turretRefund[-1].append(1)
                    else:
                        self.turretRefund[-1].append(0)
        
        for turret in self.turretRefund:
            self.turretCur.remove(turret[:2])

    def buildNewDef(self, game_state):
        # spawn new turrets and walls in set order
        for turret in self.turretEnd:
            if not(turret in self.turretCur):
                if game_state.attempt_spawn(TURRET, [turret]) == 1:
                    self.turretCur.append(turret)
                else:
                    break
        for wall in self.wallEnd:
            if not(wall in self.wallCur):
                if game_state.attempt_spawn(WALL, [wall]) == 1:
                    self.wallCur.append(wall)
                else:
                    break
        
    def rebuildDef(self, game_state):
        # Rebuilds and fortifies structures that have died
        if len(self.turretDeath) != 0:
            self.rebuildTurret(game_state)
        if len(self.wallDeath) != 0:
            self.rebuildWall(game_state)

        # spawn walls and upgrade walls and turrets to protect turrets
        turretByDmg = []
        for turret in self.turretCur:
            key = str(turret[0]) + ',' + str(turret[1])
            key2 = str(turret[0]) + ',' + str(turret[1] - 1)
            turret2 = turret.copy()
            if key in self.dmgTakenLoc:
                turret2.append(self.dmgTakenLoc[key])
            elif key2 in self.dmgTakenLoc:
                turret2.append(self.dmgTakenLoc[key2])
            else:
                turret2.append(0)
            turretByDmg.append(turret2)
        
        turretByDmg.sort(reverse=True, key=lambda x: x[2])
        for turret in turretByDmg:
            closest = self.findClosest(game_state, turret[:2], 2)
            count = 0
            for wall in closest[1]:
                if count == 3:
                    break
                if wall[:2] in self.wallCur:
                    count += 1
                    continue
                elif game_state.attempt_spawn(WALL, [wall[:2]]) == 1:
                    self.wallCur.append(wall[:2].copy())
                    count += 1
            game_state.attempt_upgrade([turret[:2]])
            count = 0
            for wall in closest[1]:
                if count == 3:
                    break
                if game_state.attempt_upgrade([wall[:2]]) == 1:
                    count += 1

    def rebuildTurret(self, game_state):
        health = 0
        dmgPerFrame = 1
        remove = []
        for turret in self.turretDeath:
            if len(turret) == 4:
                attackLoc = turret[2]
                healthDmg = turret[3]
            else:
                key = str(turret[0]) + ',' + str(turret[1])
                attackLoc = max(self.attackingUnitLoc[key], key=self.attackingUnitLoc[key].count)
                key = str(attackLoc[0]) + ',' + str(attackLoc[1])
                healthDmg = self.healthDmgByLoc[key]
            if game_state.attempt_spawn(TURRET, [turret[:2]]) == 1:
                remove.append(turret)
                self.turretCur.append(turret[:2].copy())
                health = 60
                dmgPerFrame = 6
            elif not(turret[:2] in self.turretCur) and len(turret) != 3:
                turret.append(attackLoc)
                turret.append(healthDmg)
            if game_state.attempt_upgrade([turret[:2]]) == 1:
                health = 100
                dmgPerFrame = 20
            
            opMaxDmgPerFrame = healthDmg[2]
            opMaxHealth = (healthDmg[0] * 15) + ((healthDmg[1] / 2) * 5)
            closest = self.findClosest(game_state, attackLoc, 3)
            for wall in closest[1]:
                if wall[:2] in self.wallCur:
                    health += game_state.game_map[wall[0], wall[1]][0].health

            for turret in closest[0]:
                if turret[:2] in self.turretCur:
                    if game_state.game_map[turret[0], turret[1]][0].upgraded:
                        dmgPerFrame += 20
                    else:
                        dmgPerFrame += 6

            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                for turret in closest[0]:
                    if turret[:2] in self.turretCur:
                        if not(game_state.game_map[turret[0], turret[1]][0].upgraded):
                            if game_state.attempt_upgrade([turret[:2]]) == 1:
                                dmgPerFrame += 14
                                if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                    break
            
                for turret in closest[0]:
                    if not(turret[:2] in self.turretCur):
                        if game_state.attempt_spawn(TURRET, [turret[:2]]) == 1:
                            self.turretCur.append(turret[:2].copy())
                            dmgPerFrame += 6
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                        if game_state.attempt_upgrade([turret[:2]]) == 1:
                            dmgPerFrame += 14
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                
                for wall in closest[1]:
                    if wall[:2] in self.wallCur:
                        if not(game_state.game_map[wall[0], wall[1]][0].upgraded):
                            if game_state.attempt_upgrade([wall[:2]]) == 1:
                                health += 140
                                if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                    break
                
                for wall in closest[0]:
                    if not(wall[:2] in self.wallCur):
                        if game_state.attempt_spawn(WALL, [wall[:2]]) == 1:
                            self.wallCur.append(wall[:2].copy())
                            health += 60
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                        else:
                            shouldBreak = True
                            break
                        if game_state.attempt_upgrade([wall[:2]]) == 1:
                            health += 140
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break

        for turret in remove:
            self.turretDeath.remove(turret)

    def rebuildWall(self, game_state):
        health = 0
        dmgPerFrame = 1
        remove = []

        for wall in self.wallDeath:
            if len(wall) == 4:
                attackLoc = wall[2]
                healthDmg = wall[3]
            else:
                key = str(wall[0]) + ',' + str(wall[1])
                attackLoc = max(self.attackingUnitLoc[key], key=self.attackingUnitLoc[key].count)
                key = str(attackLoc[0]) + ',' + str(attackLoc[1])
                healthDmg = self.healthDmgByLoc[key]
            if game_state.attempt_spawn(WALL, [wall[:2]]) == 1:
                self.wallCur.append(wall[:2].copy())
                remove.append(wall)
                health = 60
                dmgPerFrame = 6
            elif not(wall[:2] in self.wallCur):
                if len(wall) != 4:
                    wall.append(attackLoc)
                    wall.append(healthDmg)
            if game_state.attempt_upgrade([wall[:2]]) == 1:
                health = 100
                dmgPerFrame = 20

            opMaxDmgPerFrame = healthDmg[2]
            opMaxHealth = (healthDmg[0] * 15) + ((healthDmg[1] / 2) * 5)
            closest = self.findClosest(game_state, attackLoc, 3)

            for turret in closest[0]:
                if turret[:2] in self.turretCur:
                    if game_state.game_map[turret[0], turret[1]][0].upgraded:
                        dmgPerFrame += 20
                    else:
                        dmgPerFrame += 6
            
            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                for turret in closest[0]:
                    if turret[:2] in self.turretCur:
                        if not(game_state.game_map[turret[0], turret[1]][0].upgraded):
                            if game_state.attempt_upgrade([turret[:2]]) == 1:
                                dmgPerFrame += 14
                                if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                    break
            
                for turret in closest[0]:
                    if not(turret[:2] in self.turretCur):
                        if game_state.attempt_spawn(TURRET, [turret[:2]]) == 1:
                            self.turretCur.append(turret[:2].copy())
                            dmgPerFrame += 6
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                        if game_state.attempt_upgrade([turret[:2]]) == 1:
                            dmgPerFrame += 14
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                
                for wall in closest[1]:
                    if wall[:2] in self.wallCur:
                        if not(game_state.game_map[wall[0], wall[1]][0].upgraded):
                            if game_state.attempt_upgrade([wall[:2]]) == 1:
                                health += 140
                                if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                    break
                
                for wall in closest[0]:
                    if not(wall[:2] in self.wallCur):
                        if game_state.attempt_spawn(WALL, [wall[:2]]) == 1:
                            self.wallCur.append(wall[:2].copy())
                            health += 60
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
                        else:
                            shouldBreak = True
                            break
                        if game_state.attempt_upgrade([wall[:2]]) == 1:
                            health += 140
                            if (health/opMaxDmgPerFrame) < (opMaxHealth/dmgPerFrame):
                                        break
    
        for wall in remove:
            self.wallDeath.remove(wall)

    def calcDist(self, loc1, loc2):
        return math.sqrt(((loc1[0]-loc2[0])**2)+((loc1[1]-loc2[1])**2))

    def findClosest(self, game_state, loc, radius):
        turrets = []
        walls = []

        for turret in self.turretEnd:
            dist = self.calcDist(turret, loc)
            if dist <= radius:
                turrets.append([turret[0], turret[1], dist])
        
        for wall in self.wallEnd:
            dist = self.calcDist(wall, loc)
            if dist <= radius:
                walls.append([wall[0], wall[1], dist])

        turrets.sort(key=lambda x: x[2])
        walls.sort(key=lambda x: x[2])

        return [turrets, walls]




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
        deaths = events["death"]
        attacks = events["attack"]

        for attack in attacks:
            if attack[6] == 2:
                key = str(attack[1][0]) + ',' + str(attack[1][1])
                if key in self.attackingUnitLoc:
                    self.attackingUnitLoc[key].append(attack[0])
                else:
                    self.attackingUnitLoc[key] = [attack[0]]
                if key in self.dmgTakenLoc:
                    self.dmgTakenLoc[key] += attack[2]
                else:
                     self.dmgTakenLoc[key] = attack[2]

                key = str(attack[0][0]) + ',' + str(attack[0][1])
                if key in self.healthDmgByLoc:
                    self.healthDmgByLoc[key][2] += attack[2]
                    if attack[3] == 3:
                        self.healthDmgByLoc[key][0] += 1
                    elif attack[3] == 4:
                        self.healthDmgByLoc[key][1] += 1
                else:
                    self.healthDmgByLoc[key] = [0, 0, attack[2]]
                    if attack[3] == 3:
                        self.healthDmgByLoc[key][0] += 1
                    elif attack[3] == 4:
                        self.healthDmgByLoc[key][1] += 1

        for death in deaths:
            if death[3] == 1:
                if death[1] == 0:
                    if not death[4]:
                        gamelib.debug_write("DEATH")
                        gamelib.debug_write(death)
                        self.wallDeath.append(death[0])
                    if death[0] in self.wallCur:    
                        self.wallCur.remove(death[0])
                if death[1] == 2:
                    if not death[4]:
                        self.turretDeath.append(death[0])
                    if death[0] in self.turretCur:
                        self.turretCur.remove(death[0])

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
