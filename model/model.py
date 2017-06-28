import copy
import csv
import logging
import os
from datetime import datetime

import pygame

import utils.trpg as trpg


class Objects:
    PLAYER = "player"
    TREE1 = "tree1"
    TREE2 = "tree2"
    GRASS = "grass"
    TILE1 = "tile1"
    TILE2 = "tile2"
    CRATE = "crate"
    BUSH = "bush"
    WALL = "wall"
    PLAYER = "player"
    TREASURE = "treasure"
    TREASURE_CHEST = "treasure chest"
    DOOR = "door"
    DOOR_NORTH = "door north"
    DOOR_OPEN = "open_door"
    KEY = "key"
    BOSS_KEY = "boss key"
    TRAP = "trap"
    BOSS = "boss"
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"
    WALL_CORNER_TL = "wall corner tl"
    WALL_CORNER_TR = "wall corner tr"
    WALL_CORNER_BL = "wall corner bl"
    WALL_CORNER_BR = "wall corner br"
    WALL_TOP_HORIZONTAL = "wall top horizontal"
    WALL_BOTTOM_HORIZONTAL = "wall bottom horizontal"
    WALL_LEFT_VERTICAL = "wall left vertical"
    WALL_RIGHT_VERTICAL = "wall right vertical"
    WALL_TL = "wall tl"
    WALL_TR = "wall tr"
    WALL_BL = "wall bl"
    WALL_BR = "wall br"
    WALL_TOP = "wall top"
    WALL_BLOCK = "wall block"

    DIRECTIONS = (NORTH, SOUTH, EAST, WEST)
    DOORS = (DOOR_NORTH, DOOR)


class RPGObject(object):
    TOUCH_FIELD_X = 4
    TOUCH_FIELD_Y = 4

    def __init__(self, name: str,
                 rect: pygame.Rect,
                 layer: int = 1,
                 height: int = None,
                 solid: bool = True,
                 visible: bool = True,
                 interactable: bool = True):
        self.name = name
        self._rect = pygame.Rect(rect)

        self.layer = layer
        self._old_rect = self._rect.copy()
        if height is None:
            height = self._rect.height
        self.height = height
        self.is_solid = solid
        self.is_visible = visible
        self.is_interactable = interactable
        self.dx = 0
        self.dy = 0
        self.d2x = 0
        self.d2y = 0

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, new_rect):
        self._old_rect = self._rect.copy()
        self._rect = new_rect

    def back(self):
        logging.info("Moving Player {0} back from {1} to {2}".format(self.name, self._rect, self._old_rect))
        self._rect = self._old_rect.copy()

    def is_colliding(self, other_object):
        return self.layer == other_object.layer and \
               self != other_object and \
               self.rect.colliderect(other_object.rect)

    def is_touching(self, other_object):
        # logging.info("Checking {0} touching {1}".format(touch_field, other_object.rect))

        touch_field = self._rect.inflate(RPGObject.TOUCH_FIELD_X, RPGObject.TOUCH_FIELD_Y)

        return self.layer == other_object.layer and \
               self.is_visible and \
               self.is_interactable and \
               self != other_object and \
               touch_field.colliderect(other_object.rect)

    def move(self, dx: int, dy: int):
        self._old_rect = self._rect.copy()
        self.rect.x += dx
        self.rect.y += dy

    def set_pos(self, x: int, y: int):
        self._old_rect = self._rect.copy()
        self.rect.x = x
        self.rect.y = y

    def get_pos(self):
        return self._rect.x, self._rect.y


class Player(RPGObject):
    def __init__(self, name: str,
                 rect: pygame.Rect,
                 height: int = 40):
        super(Player, self).__init__(name=name, rect=rect, height=height)

        self.treasure = 0
        self.keys = 0
        self.boss_keys = 0
        self.HP = 10
        self.layer = 1


class Monster(RPGObject):
    def __init__(self, name: str,
                 rect: pygame.Rect,
                 height: int = 30):
        super(Monster, self).__init__(name=name, rect=rect, height=height)


class Floor:
    EXIT_NORTH = "NORTH"
    EXIT_SOUTH = "SOUTH"
    EXIT_EAST = "EAST"
    EXIT_WEST = "WEST"
    EXIT_UP = "UP"
    EXIT_DOWN = "DOWN"

    OBJECT_TO_DIRECTION = {Objects.WEST: EXIT_WEST,
                           Objects.EAST: EXIT_EAST,
                           Objects.NORTH: EXIT_NORTH,
                           Objects.SOUTH: EXIT_SOUTH,
                           Objects.UP: EXIT_UP,
                           Objects.DOWN: EXIT_DOWN}

    REVERSE_DIRECTION = {EXIT_WEST: EXIT_EAST,
                         EXIT_EAST: EXIT_WEST,
                         EXIT_NORTH: EXIT_SOUTH,
                         EXIT_SOUTH: EXIT_NORTH,
                         EXIT_UP: EXIT_DOWN,
                         EXIT_DOWN: EXIT_UP}

    def __init__(self, id: int, name: str, rect: pygame.Rect, skin_name: str = "default"):
        self.id = id
        self.name = name
        self.skin_name = skin_name
        self.rect = pygame.Rect(rect)
        self.players = {}
        self.objects = []
        self.monsters = []
        self.layers = {}
        self.exits = {}

    def __str__(self):
        return "Floor {0}: rect={1}, objects={2}, monsters={3}".format(self.name, self.rect, self.object_count,
                                                                       len(self.monsters))

    @property
    def object_count(self):
        count = 0
        for layer in self.layers.values():
            count += len(layer)
        return count

    def add_player(self, new_player: Player, position: str = None):

        self.players[new_player.name] = new_player

        if position in self.exits.keys():
            exit_rect = self.exits[position].rect
            player_rect = new_player.rect
            x = exit_rect.centerx - int(player_rect.width / 2)
            y = exit_rect.centery - int(player_rect.height / 2)

            if position == Floor.EXIT_NORTH:
                y = exit_rect.bottom + RPGObject.TOUCH_FIELD_Y + 1
            elif position == Floor.EXIT_SOUTH:
                y = exit_rect.top - new_player.rect.height - RPGObject.TOUCH_FIELD_Y - 1
            elif position == Floor.EXIT_WEST:
                x = exit_rect.right + RPGObject.TOUCH_FIELD_X + 1
            elif position == Floor.EXIT_EAST:
                x = exit_rect.left - new_player.rect.width - RPGObject.TOUCH_FIELD_X - 1
        else:
            x = (self.rect.width / 2)
            y = (self.rect.height / 2)

        print("Adding player at {0},{1}".format(x, y))
        new_player.set_pos(x, y)

    def add_object(self, new_object: RPGObject):

        if new_object.layer not in self.layers.keys():
            self.layers[new_object.layer] = []

        objects = self.layers[new_object.layer]
        objects.append(new_object)
        self.rect.union_ip(new_object.rect)

        self.layers[new_object.layer] = sorted(objects, key=lambda obj: obj.layer * 1000 + obj.rect.y, reverse=False)

        if new_object.name in Objects.DIRECTIONS:
            self.exits[Floor.OBJECT_TO_DIRECTION[new_object.name]] = new_object

        logging.info("Added {0} at location ({1},{2})".format(new_object.name, new_object.rect.x, new_object.rect.y))

    def remove_object(self, object: RPGObject):
        objects = self.layers[object.layer]
        objects.remove(object)

    def swap_object(self, object: RPGObject, new_object_type: str):

        objects = self.layers[object.layer]

        x, y = object.get_pos()

        swap_object = FloorObjectLoader.get_object_copy_by_name(new_object_type)
        swap_object.set_pos(x, y)
        objects.remove(object)
        objects.append(swap_object)

    def add_monster(self, new_object: Monster):

        self.monsters.append(new_object)

    def is_player_collide(self, target: RPGObject):

        collide = False

        for player in self.players.values():
            if target.is_colliding(player):
                collide = True
                break

        return collide

    def colliding_objects(self, target: RPGObject):

        objects = self.layers[target.layer]

        # print("colliding check {0} objects".format(len(objects)))

        colliding = []

        for object in objects:
            if object.is_colliding(target):
                colliding.append(object)

        return colliding

    def touching_objects(self, target: RPGObject):

        objects = self.layers[target.layer]

        # print("touching check {0} objects".format(len(objects)))

        touching = []

        for object in objects:
            if object.is_touching(target):
                touching.append(object)

        return touching

    def move_player(self, name: str, dx: int = 0, dy: int = 0):

        if name not in self.players.keys():
            raise Exception("{0}:move_player() - Player {1} is not on floor (2).".format(__class__, name, self.name))

        selected_player = self.players[name]

        objects = self.layers[selected_player.layer]

        if dx != 0:
            selected_player.move(dx, 0)

            if self.rect.contains(selected_player.rect) == False:
                selected_player.back()
            else:
                for object in objects:
                    if object.is_solid is True and object.is_colliding(selected_player):
                        selected_player.back()
                        break
        if dy != 0:
            selected_player.move(0, dy)

            if self.rect.contains(selected_player.rect) == False:
                selected_player.back()
            else:
                for object in objects:
                    if object.is_solid is True and object.is_colliding(selected_player):
                        selected_player.back()
                        break


class Game:
    LOADED = "LOADED"
    READY = "READY"
    PLAYING = "PLAYING"
    SHOPPING = "SHOPPING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME OVER"
    END = "END"
    EFFECT_COUNTDOWN_RATE = 4
    DOT_DAMAGE_RATE = 3
    ENEMY_DAMAGE_RATE = 2
    TARGET_RUNE_COUNT = 4
    MAX_STATUS_MESSAGES = 5
    STATUS_MESSAGE_LIFETIME = 16

    DATA_FILES_DIR = os.path.dirname(__file__) + "\\data\\"

    def __init__(self, name: str):

        self.name = name
        self.player = None
        self._state = Game.LOADED
        self.tick_count = 0
        self.floor_factory = None
        self.current_player = None
        self.maps = None

    def initialise(self):

        logging.info("Initialising {0}...".format(self.name))

        self._state = Game.READY
        self.player = None
        self.tick_count = 0

        self.floor_factory = FloorBuilder(Game.DATA_FILES_DIR)
        self.floor_factory.initialise()
        self.floor_factory.load_floors()

        self.current_floor_id = 1
        self.current_player = None

        self.maps = trpg.MapFactory()
        self.maps.load("ZeldaQuest", 1, Game.DATA_FILES_DIR + "maplinks.csv")
        self.current_map = self.maps.get_map(1)
        self.current_map.print()

    @property
    def state(self):

        return self._state

    @property
    def current_floor(self):
        return self.floor_factory.floors[self.current_floor_id]

    def tick(self):
        self.tick_count += 1
        self.check_collision()

    def create_player(self, new_player_name: str):

        new_object = FloorObjectLoader.get_object_copy_by_name(Objects.PLAYER)

        new_player = Player(name=new_player_name, rect=(0, 0, new_object.rect.width, new_object.rect.height), height=32)

        return new_player

    def add_player(self, new_player: Player):
        self.current_player = new_player
        self.current_floor.add_player(new_player)

    def move_player(self, dx: int, dy: int):

        dt1 = datetime.now()

        self.current_floor.move_player(self.current_player.name, dx, dy)

        # colliding_objects = self.current_floor.colliding_objects(self.current_player)

        # for object in colliding_objects:
        #     print("{0} is colliding with {1}".format(self.current_player.name, object.name))
        #     if object.name in Floor.OBJECT_TO_DIRECTION.keys():
        #         direction = Floor.OBJECT_TO_DIRECTION[object.name]
        #         try:
        #             self.check_exit(direction)
        #         except Exception as e:
        #             print(str(e))

        touching_objects = self.current_floor.touching_objects(self.current_player)

        for object in touching_objects:
            # print("{0} is touching {1}".format(self.current_player.name, object.name))
            if object.name in Floor.OBJECT_TO_DIRECTION.keys():
                direction = Floor.OBJECT_TO_DIRECTION[object.name]
                try:
                    self.check_exit(direction)
                except Exception as e:
                    print(str(e))

            elif object.name == Objects.TREASURE:
                self.current_player.treasure += 1
                self.current_floor.remove_object(object)
                print("You found some treasure!")

            elif object.name == Objects.TREASURE_CHEST:
                if self.current_player.keys > 0:
                    self.current_player.keys -= 1
                    self.current_floor.remove_object(object)
                    print("You opened the chest!")
                else:
                    print("You don't have a key.")

            elif object.name == Objects.KEY:
                self.current_player.keys += 1
                self.current_floor.remove_object(object)
                print("You found a key!")

            elif object.name == Objects.BOSS_KEY:
                self.current_player.boss_keys += 1
                self.current_floor.remove_object(object)
                print("You found a boss key!")

            elif object.name in Objects.DOORS:
                print("You found a door!")
                if self.current_player.keys > 0:
                    self.current_player.keys -= 1
                    self.current_floor.swap_object(object, Objects.DOOR_OPEN)
                    print("You opened the door with a key!")
                else:
                    print("The door is locked!")

        dt2 = datetime.now()
        # print("move={0}".format(dt2.microsecond - dt1.microsecond))

    def check_exit(self, direction):

        # Check if a direction was even specified
        if direction is "":
            raise (Exception("You need to specify a direction e.g. NORTH"))

        # Check if the direction is a valid one
        direction = direction.upper()
        if direction not in trpg.MapLink.valid_directions:
            raise (Exception("Direction %s is not valid" % direction.title()))

        # Now see if the map allows you to go in that direction
        links = self.current_map.get_location_links_map(self.current_floor_id)

        # OK stat direction is valid...
        if direction in links.keys():
            link = links[direction]

            # ..but see if it is currently locked...
            if link.is_locked() is True:
                raise (Exception("You can't go %s - %s" % (direction.title(), link.locked_description)))

            # If all good move to the new location
            print("You go %s %s..." % (direction.title(), link.description))

            # self.add_status_message("You go {0} {1}...".format(direction.title(), link.description))

            self.current_floor_id = link.to_id
            self.current_floor.add_player(self.current_player, Floor.REVERSE_DIRECTION[direction])

        else:
            raise (Exception("You can't go {0} from here!".format(direction)))

    def check_collision(self):

        colliding_objects = self.current_floor.colliding_objects(self.current_player)

        for object in colliding_objects:
            # print("{0} is colliding with {1}".format(self.current_player.name, object.name))
            if object.name == Objects.TRAP and self.tick_count % Game.DOT_DAMAGE_RATE == 0:
                self.current_player.HP -= 1
                print("You stepped on a trap!")


class FloorBuilder():
    FLOOR_LAYOUT_FILE_NAME = "_floor_layouts.csv"
    FLOOR_OBJECT_FILE_NAME = "_floor_objects.csv"

    def __init__(self, data_file_directory: str):
        self.data_file_directory = data_file_directory
        self.floors = {}

    def initialise(self, file_prefix: str = "default"):

        self.floor_objects = FloorObjectLoader(
            self.data_file_directory + file_prefix + FloorBuilder.FLOOR_OBJECT_FILE_NAME)
        self.floor_objects.load()

        self.floor_layouts = FloorLayoutLoader(
            self.data_file_directory + file_prefix + FloorBuilder.FLOOR_LAYOUT_FILE_NAME)
        self.floor_layouts.load()

    def load_floors(self):

        for floor_id, new_floor in FloorLayoutLoader.floor_layouts.items():
            self.floors[floor_id] = new_floor

        for floor in self.floors.values():
            print(str(floor))


class FloorLayoutLoader():
    floor_layouts = {}

    DEFAULT_OBJECT_WIDTH = 32
    DEFAULT_OBJECT_DEPTH = 32

    EMPTY_OBJECT_CODE = " "

    def __init__(self, file_name):
        self.file_name = file_name

    def load(self):

        # Attempt to open the file
        with open(self.file_name, 'r') as object_file:

            # Load all rows in as a dictionary
            reader = csv.DictReader(object_file)

            # Get the list of column headers
            header = reader.fieldnames

            current_floor_id = None
            current_floor_layer = None

            # For each row in the file....
            for row in reader:

                floor_id = int(row.get("ID"))
                floor_layout_name = row.get("Name")
                floor_skin_name = row.get("Skin")

                if floor_id != current_floor_id:
                    FloorLayoutLoader.floor_layouts[floor_id] = Floor(floor_id, floor_layout_name, (0, 0, 0, 0),
                                                                      skin_name=floor_skin_name)
                    current_floor_id = floor_id
                    y = 0

                floor = FloorLayoutLoader.floor_layouts[floor_id]

                floor_layer = int(row.get("Layer"))
                if floor_layer != current_floor_layer:
                    current_floor_layer = floor_layer
                    y = 0

                floor_layout = row.get("Layout")
                x = 0
                for object_code in floor_layout:
                    if object_code != FloorLayoutLoader.EMPTY_OBJECT_CODE:
                        new_floor_object = FloorObjectLoader.get_object_copy_by_code(object_code)
                        new_floor_object.rect.x = x
                        new_floor_object.rect.y = y
                        new_floor_object.layer = floor_layer
                        floor.add_object(new_floor_object)
                    x += FloorLayoutLoader.DEFAULT_OBJECT_WIDTH

                y += FloorLayoutLoader.DEFAULT_OBJECT_DEPTH


class FloorObjectLoader():
    floor_objects = {}
    map_object_name_to_code = {}

    BOOL_MAP = {"TRUE": True, "FALSE": False}

    def __init__(self, file_name: str):
        self.file_name = file_name

    def load(self):

        # Attempt to open the file
        with open(self.file_name, 'r') as object_file:
            # Load all rows in as a dictionary
            reader = csv.DictReader(object_file)

            # Get the list of column headers
            header = reader.fieldnames

            # For each row in the file....
            for row in reader:
                print("loading {0}".format(row))

                object_code = row.get("Code")

                new_object = RPGObject(row.get("Name"), \
                                       rect=(0, 0, int(row.get("width")), int(row.get("depth"))), \
                                       height=int(row.get("height")), \
                                       solid=FloorObjectLoader.BOOL_MAP[row.get("solid").upper()], \
                                       visible=FloorObjectLoader.BOOL_MAP[row.get("visible").upper()], \
                                       interactable=FloorObjectLoader.BOOL_MAP[row.get("interactable").upper()] \
                                       )

                # Store the floor object in the code cache
                FloorObjectLoader.floor_objects[object_code] = new_object

                # Store mapping of object name to code
                FloorObjectLoader.map_object_name_to_code[new_object.name] = object_code

                logging.info("{0}.load(): Loaded Floor Object {1}".format(__class__, new_object.name))

    @staticmethod
    def get_object_copy_by_code(object_code: str):

        if object_code not in FloorObjectLoader.floor_objects.keys():
            raise Exception("Can't find object by code '{0}'".format(object_code))

        return copy.deepcopy(FloorObjectLoader.floor_objects[object_code])

    @staticmethod
    def get_object_copy_by_name(object_name: str):

        if object_name not in FloorObjectLoader.map_object_name_to_code.keys():
            raise Exception("Can't find object by name '{0}'".format(object_name))

        object_code = FloorObjectLoader.map_object_name_to_code[object_name]

        if object_code not in FloorObjectLoader.floor_objects.keys():
            raise Exception("Can't find object by code '{0}'".format(object_name))

        return FloorObjectLoader.get_object_copy_by_code(object_code)
