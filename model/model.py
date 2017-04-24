import pygame
import logging
import os
import csv
import copy

class Objects:

    PLAYER = "player"
    TREE = "tree"
    CRATE = "crate"
    BUSH = "bush"
    WALL = "wall"
    PLAYER = "player"
    TREASURE = "treasure"
    DOOR = "door"
    DOOR_OPEN = "open_door"
    KEY = "key"
    TRAP = "trap"
    BOSS = "boss"

class RPGObject(object):

    TOUCH_FIELD_X = 2
    TOUCH_FIELD_Y = 2

    def __init__(self, name : str,
                 rect : pygame.Rect,
                 height : int = None,
                 solid : bool = True,
                 visible : bool = True,
                 interactable : bool = True):

        self.name = name
        self._rect = pygame.Rect(rect)
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
        return self != other_object and\
               self.rect.colliderect(other_object.rect)

    def is_touching(self, other_object):

        touch_field = self.rect.inflate(RPGObject.TOUCH_FIELD_X, RPGObject.TOUCH_FIELD_Y)

        logging.info("Checking {0} touching {1}".format(touch_field, other_object.rect))

        return self != other_object and \
               self.is_visible and\
               self.is_interactable and\
               touch_field.colliderect(other_object.rect)

    def move(self, dx : int, dy : int):
        self._old_rect = self._rect.copy()
        self.rect.x += dx
        self.rect.y += dy

    def set_pos(self, x : int, y : int):
        self._old_rect = self._rect.copy()
        self.rect.move_ip(x, y)

    def get_pos(self):
        return self._rect.x, self._rect.y

class Player(RPGObject):

    def __init__(self, name : str,
                 rect : pygame.Rect,
                 height : int = 40):

        super(Player, self).__init__(name=name, rect=rect, height=height)

        self.treasure = 0
        self.keys = 0
        self.HP = 10

class Monster(RPGObject):

    def __init__(self, name : str,
                 rect : pygame.Rect,
                 height : int = 30):

        super(Monster, self).__init__(name=name, rect=rect, height=height)


class Floor:

    def __init__(self, name : str, rect : pygame.Rect):
        self.name = name
        self.rect = rect
        self.players = {}
        self.objects = []
        self.monsters = []

    def add_player(self, new_player : Player):
        self.players[new_player.name] = new_player

    def add_object(self, new_object : RPGObject):
        self.objects.append(new_object)
        logging.info("Added {0} at location ({1},{2})".format(new_object.name,new_object.rect.x,new_object.rect.y))

    def remove_object(self, object : RPGObject):
        self.objects.remove(object)

    def swap_object(self, object : RPGObject, new_object_type : str):

        x,y = object.get_pos()

        swap_object = FloorObjectLoader.get_object_copy_by_name(new_object_type)
        swap_object.set_pos(x,y)
        self.objects.remove(object)
        self.objects.append(swap_object)




    def add_monster(self, new_object : Monster):
        self.monsters.append(new_object)


    def is_player_collide(self, target : RPGObject):

        collide = False

        for player in self.players.values():
            if target.is_colliding(player):
                collide = True
                break

        return collide

    def colliding_objects(self, target : RPGObject):

        colliding = []

        for object in self.objects:
            if object.is_colliding(target):
                colliding.append(object)

        return colliding

    def touching_objects(self, target : RPGObject):

        touching = []

        for object in self.objects:
            if object.is_touching(target):
                touching.append(object)

        return touching

    def move_player(self, name : str, dx : int = 0, dy : int = 0):

        if name not in self.players.keys():
            raise Exception("{0}:move_player() - Player {1} is not on floor (2).".format(__class__, name, self.name))

        selected_player = self.players[name]

        selected_player.move(dx,0)

        for object in self.objects:

            if object.is_colliding(selected_player):
                logging.info("{0}:Player {1} has hit object {2}".format(__class__,selected_player.name, object.name))
                if object.is_solid is True:
                    selected_player.back()
                    break


        selected_player.move(0,dy)

        for object in self.objects:
            if object.is_colliding(selected_player):
                logging.info("{0}:Player {1} has hit object {2}".format(__class__,selected_player.name, object.name))
                if object.is_solid is True:
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

    def __init__(self, name : str):

        self.name = name
        self.player = None
        self._state = Game.LOADED
        self.tick_count = 0
        self.floor_factory = None
        self.current_player = None


    def initialise(self):

        logging.info("Initialising {0}...".format(self.name))

        self._state = Game.READY
        self.player = None
        self.tick_count = 0

        self.floor_factory = FloorBuilder(Game.DATA_FILES_DIR)
        self.floor_factory.initialise()
        self.floor_factory.load_floors()

        self.current_floor_id = "Floor1"
        self.current_player = None


    @property
    def state(self):

        return self._state

    @property
    def current_floor(self):
        return self.floor_factory.floors[self.current_floor_id]

    def tick(self):
        self.tick_count += 1
        self.check_collision()

    def create_player(self, new_player_name : str):

        new_object = FloorObjectLoader.get_object_copy_by_name(Objects.PLAYER)

        new_player = Player(name=new_player_name, rect=(0,0,new_object.rect.width, new_object.rect.height), height=32)

        return new_player


    def add_player(self, new_player : Player):
        self.current_player = new_player
        self.current_floor.add_player(new_player)

    def move_player(self, dx : int, dy : int):

        self.current_floor.move_player(self.current_player.name, dx,dy)

        colliding_objects = self.current_floor.colliding_objects(self.current_player)

        for object in colliding_objects:
            print("{0} is colliding with {1}".format(self.current_player.name, object.name))

        touching_objects = self.current_floor.touching_objects(self.current_player)

        for object in touching_objects:
            print("{0} is touching {1}".format(self.current_player.name, object.name))

            if object.name == Objects.TREASURE:
                self.current_player.treasure += 1
                self.current_floor.remove_object(object)
                print("You found some treasure!")

            if object.name == Objects.KEY:
                self.current_player.keys += 1
                self.current_floor.remove_object(object)
                print("You found a key!")

            elif object.name == Objects.DOOR:
                print("You found a door!")
                if self.current_player.keys > 0:
                    self.current_player.keys -= 1
                    self.current_floor.swap_object(object, Objects.DOOR_OPEN)
                    print("You opened the door with a key!")
                else:
                    print("The door is locked!")

    def check_collision(self):

        colliding_objects = self.current_floor.colliding_objects(self.current_player)

        for object in colliding_objects:
            #print("{0} is colliding with {1}".format(self.current_player.name, object.name))
            if object.name == Objects.TRAP and self.tick_count % Game.DOT_DAMAGE_RATE == 0:
                self.current_player.HP -= 1
                print("You stepped on a trap!")




class FloorBuilder():

    FLOOR_LAYOUT_FILE_NAME = "_floor_layouts.csv"
    FLOOR_OBJECT_FILE_NAME = "_floor_objects.csv"


    def __init__(self, data_file_directory : str):
        self.data_file_directory = data_file_directory
        self.floors = {}

    def initialise(self, file_prefix : str = "default"):

        self.floor_objects = FloorObjectLoader(self.data_file_directory + file_prefix + FloorBuilder.FLOOR_OBJECT_FILE_NAME)
        self.floor_objects.load()

        self.floor_layouts = FloorLayoutLoader(self.data_file_directory + file_prefix + FloorBuilder.FLOOR_LAYOUT_FILE_NAME)
        self.floor_layouts.load()

    def load_floors(self):
        floor_name="Floor1"
        new_floor = FloorLayoutLoader.floor_layouts[floor_name]
        #new_floor = Floor(name = "start", rect=(0,0,500,500))

        # new_player = Player(name="keith", rect=(32, 32, 20, 20))
        # new_floor.add_player(new_player)

        self.floors[floor_name] = new_floor


class FloorLayoutLoader():

    floor_layouts = {}

    DEFAULT_OBJECT_WIDTH = 32
    DEFAULT_OBJECT_DEPTH = 32

    EMPTY_OBJECT_CODE = "_"

    def __init__(self, file_name):
        self.file_name = file_name

    def load(self):

        # Attempt to open the file
        with open(self.file_name, 'r') as object_file:

            # Load all rows in as a dictionary
            reader = csv.DictReader(object_file)

            # Get the list of column headers
            header = reader.fieldnames

            current_layout_name = None

            # For each row in the file....
            for row in reader:

                floor_layout_name = row.get("Name")

                if floor_layout_name != current_layout_name:
                    FloorLayoutLoader.floor_layouts[floor_layout_name] = Floor(floor_layout_name,(0,0,0,0))
                    current_layout_name = floor_layout_name
                    y=0

                floor = FloorLayoutLoader.floor_layouts[floor_layout_name]
                floor_layout = row.get("Layout")
                x=0
                for object_code in floor_layout:
                    if object_code != FloorLayoutLoader.EMPTY_OBJECT_CODE:
                        new_floor_object = FloorObjectLoader.get_object_copy_by_code(object_code)
                        new_floor_object.rect.x = x
                        new_floor_object.rect.y = y
                        floor.add_object(new_floor_object)
                    x+=FloorLayoutLoader.DEFAULT_OBJECT_WIDTH

                y+=FloorLayoutLoader.DEFAULT_OBJECT_DEPTH


class FloorObjectLoader():


    floor_objects = {}
    map_object_name_to_code = {}

    BOOL_MAP = { "TRUE" : True, "FALSE" : False}

    def __init__(self, file_name : str):
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

                new_object = RPGObject( row.get("Name"), \
                                        rect = (0,0,int(row.get("width")),int(row.get("depth"))), \
                                        height = int(row.get("height")), \
                                        solid = FloorObjectLoader.BOOL_MAP[row.get("solid").upper()], \
                                        visible = FloorObjectLoader.BOOL_MAP[row.get("visible").upper()], \
                                        interactable=FloorObjectLoader.BOOL_MAP[row.get("interactable").upper()] \
                                        )


                # Store the floor object in the code cache
                FloorObjectLoader.floor_objects[object_code] = new_object

                # Store mapping of object name to code
                FloorObjectLoader.map_object_name_to_code[new_object.name] = object_code

                logging.info("{0}.load(): Loaded Floor Object {1}".format(__class__, new_object.name))

    @staticmethod
    def get_object_copy_by_code(object_code : str):

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


