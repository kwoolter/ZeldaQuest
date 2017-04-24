import pygame
import model
import os
import logging



class Colours:
    # set up the colours
    BLACK = (0, 0, 0)
    BROWN = (128,64,0)
    WHITE = (255, 255, 255)
    RED = (237, 28, 36)
    GREEN = (34, 177, 76)
    BLUE = (63, 72, 204)
    DARK_GREY = (40, 40, 40)
    GREY = (128,128,128)
    GOLD = (255, 201, 14)
    YELLOW = (255, 255, 0)

class ImageManager:

    DEFAULT_SKIN = "default"
    RESOURCES_DIR = os.path.dirname(__file__) + "\\resources\\"

    image_cache = {}
    skins = {}
    initialised = False

    def __init__(self):
        pass

    def initialise(self):
        if ImageManager.initialised is False:
            self.load_skins()

    def get_image(self, image_file_name : str, width : int = 32, height : int =32):

        if image_file_name not in ImageManager.image_cache.keys():

            filename = ImageManager.RESOURCES_DIR + image_file_name
            try:
                logging.info("Loading image {0}...".format(filename))
                original_image = pygame.image.load(filename)
                image = pygame.transform.scale(original_image, (width, height))
                ImageManager.image_cache[image_file_name] = image
                logging.info("Image {0} loaded and cached.".format(filename))
            except Exception as err:
                print(str(err))

        return self.image_cache[image_file_name]

    def load_skins(self):

        new_skin_name = ImageManager.DEFAULT_SKIN
        new_skin = (new_skin_name, {

                                    model.Objects.TREE: "forest_tree.png",
                                    model.Objects.WALL: "forest_wall.png",
                                    model.Objects.CRATE: "forest_crate.png",
                                    model.Objects.BUSH: "forest_bush.png",
                                    model.Objects.BOSS: ("fallen_knight1.png","fallen_knight2.png","fallen_knight3.png", \
                                                       "fallen_knight2.png","fallen_knight1.png","fallen_knight4.png", \
                                                       "fallen_knight5.png","fallen_knight4.png"
                                                       ),
                                    model.Objects.PLAYER: ("player1.png","player.png","player2.png","player.png"),
                                    model.Objects.TREASURE : "treasure.png",
                                    model.Objects.DOOR: "door.png",
                                    model.Objects.DOOR_OPEN: "door_open.png",
                                    model.Objects.KEY: "key.png",
                                    model.Objects.TRAP: ("empty.png","spike0.png","spike1.png","spike2.png","spike3.png",
                                                        "spike2.png","spike1.png","spike0.png"),

        })

        ImageManager.skins[new_skin_name] = new_skin


    def get_skin_image(self, tile_name: str, skin_name: str = DEFAULT_SKIN, tick=0, width : int = 32, height : int =32):

        if skin_name not in ImageManager.skins.keys():
            raise Exception("Can't find specified skin {0}".format(skin_name))

        name, tile_map = ImageManager.skins[skin_name]

        if tile_name not in tile_map.keys():
            name, tile_map = ImageManager.skins[ImageManager.DEFAULT_SKIN]
            if tile_name not in tile_map.keys():
                raise Exception("Can't find tile name '{0}' in skin '{1}'!".format(tile_name, skin_name))

        tile_file_names = tile_map[tile_name]

        image = None

        if tile_file_names is None:
            image = None
        elif isinstance(tile_file_names, tuple):
            if tick == 0:
                tile_file_name = tile_file_names[0]
            else:
                tile_file_name = tile_file_names[tick % len(tile_file_names)]

            image = self.get_image(image_file_name=tile_file_name, width=width, height=height)

        else:
            image = self.get_image(tile_file_names,width=width, height=height)

        return image

class View:

    image_manager = ImageManager()

    def __init__(self):
        self.tick_count = 0
        View.image_manager.initialise()

    def initialise(self):
        self.tick_count = 0

    def tick(self):
        self.tick_count += 1

    def draw(self):
        pass

    def end(self):
        pass


class MainFrame(View):

    TITLE_HEIGHT = 80
    STATUS_HEIGHT = 50

    INVENTORY = "Inventory"
    PLAYING = "Playing"
    SHOPPING = "Shopping"

    RESOURCES_DIR = os.path.dirname(__file__) + "\\resources\\"

    def __init__(self, width: int = 600, height: int = 600):

        super(MainFrame, self).__init__()

        self.state = None
        self.game = None

        height = MainFrame.TITLE_HEIGHT + MainFrame.STATUS_HEIGHT + (32*20)
        playing_area_height = height - MainFrame.TITLE_HEIGHT - MainFrame.STATUS_HEIGHT
        playing_area_width = width

        self.surface = pygame.display.set_mode((width, height))

        self.floor_view = FloorView(playing_area_width, playing_area_height)

    def initialise(self, game: model.Game):

        super(MainFrame, self).initialise()

        self.state = MainFrame.PLAYING
        self.game = game

        os.environ["SDL_VIDEO_CENTERED"] = "1"
        pygame.init()
        pygame.display.set_caption(self.game.name)
        filename = MainFrame.RESOURCES_DIR + "icon.png"

        try:
            image = pygame.image.load(filename)
            image = pygame.transform.scale(image, (32, 32))
            pygame.display.set_icon(image)
        except Exception as err:
            print(str(err))

        images = ImageManager()
        images.initialise()

        self.floor_view.initialise(self.game.current_floor)

    def draw(self):

        super(MainFrame, self).draw()

        self.surface.fill(Colours.RED)

        pane_rect = self.surface.get_rect()

        x=0
        y=pane_rect.y + MainFrame.TITLE_HEIGHT

        self.floor_view.draw()
        self.surface.blit(self.floor_view.surface, (x, y))



    def update(self):
        pygame.display.update()

    def tick(self):

        super(MainFrame, self).tick()
        self.floor_view.tick()


class FloorView(View):

    BG_COLOUR = Colours.DARK_GREY
    TILE_WIDTH = 32
    TILE_HEIGHT = 32

    def __init__(self, width : int, height : int, tile_width : int = TILE_WIDTH, tile_height : int = TILE_HEIGHT):

        super(FloorView, self).__init__()

        self.surface = pygame.Surface((width, height))
        self.floor = None
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.skin_name = None

    def initialise(self, floor : model.Floor):
        self.floor = floor

    def draw(self):

        self.surface.fill(FloorView.BG_COLOUR)

        if self.floor is None:
            raise ("No Floor to view!")

        view_objects = list(self.floor.players.values()) + self.floor.objects + self.floor.monsters

        view_objects = sorted(view_objects, key=lambda obj : obj.rect.y, reverse=False)

        for view_object in view_objects:
            if view_object.is_visible is True:
                if isinstance(view_object, model.Player):

                    image = View.image_manager.get_skin_image(view_object.name,
                                                              tick=self.tick_count,
                                                              width=view_object.rect.width,
                                                              height = view_object.height)
                    if image is None:
                        pygame.draw.rect(self.surface, Colours.WHITE, self.model_to_view_rect(view_object))
                        pygame.draw.rect(self.surface, Colours.RED, self.model_to_view_rect(view_object), 1)
                    else:
                        self.surface.blit(image,self.model_to_view_rect(view_object))

                elif isinstance(view_object, model.Monster):
                    pygame.draw.rect(self.surface, Colours.RED, self.model_to_view_rect(view_object))
                    pygame.draw.rect(self.surface, Colours.GOLD, self.model_to_view_rect(view_object), 1)
                elif isinstance(view_object, model.RPGObject):
                    image = View.image_manager.get_skin_image(view_object.name,
                                                              tick=self.tick_count,
                                                              width=view_object.rect.width,
                                                              height = view_object.height)
                    if image is None:
                        pygame.draw.rect(self.surface, Colours.GREEN, self.model_to_view_rect(view_object))
                        pygame.draw.rect(self.surface, Colours.GOLD, self.model_to_view_rect(view_object), 1)
                    else:
                        self.surface.blit(image,self.model_to_view_rect(view_object))

    def model_to_view_rect(self, model_object : model.RPGObject):

        HEIGHT_ANGLE_FACTOR = 1.0


        view_rect = model_object.rect.copy()
        bottom = view_rect.bottom
        view_rect.height = model_object.height * HEIGHT_ANGLE_FACTOR
        view_rect.bottom = bottom

        return view_rect
