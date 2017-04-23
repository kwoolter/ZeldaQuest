import os
import pygame
import sys
from pygame.locals import *

import model as model
import view as view
import pickle
import logging

class Controller:

    INVENTORY = "Inventory"
    PLAYING = "Playing"
    SHOP = "Shop"

    def __init__(self):
        self.game = None
        self.view = None
        self.audio = None
        self._mode = None

        self.music_on = True
        self.sound_on = True


    def initialise(self):

        self._mode = Controller.PLAYING
        self._test_mode = False

        self.game = model.Game("Adventure World")
        self.view = view.MainFrame(width=20*32, height=730)


        new_player = model.Player(name="player", rect=(80, 100, 48, 32),height=64)
        self.game.initialise()
        self.game.add_player(new_player)
        self.view.initialise(self.game)

        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()


    def run(self):

        os.environ["SDL_VIDEO_CENTERED"] = "1"

        FPSCLOCK = pygame.time.Clock()

        pygame.time.set_timer(USEREVENT + 1, 250)

        loop = True

        # main game_template loop
        while loop == True:

            for event in pygame.event.get():
                if event.type == QUIT:
                    loop = False
                elif event.type == USEREVENT + 1:
                    try:
                        self.game.tick()
                        self.view.tick()

                    except Exception as err:
                        print(str(err))
                elif event.type == USEREVENT + 1:
                    try:
                        if self.game.state == model.Game.PLAYING:
                            self.game.tick()
                        self.view.tick()

                    except Exception as err:
                        print(str(err))

                elif event.type == KEYDOWN:
                    pass

            # Move the player if an arrow key is pressed
            key = pygame.key.get_pressed()
            if key[pygame.K_LEFT]:
                self.game.move_player(-1, 0)
            if key[pygame.K_RIGHT]:
                self.game.move_player(1, 0)
            if key[pygame.K_UP]:
                self.game.move_player(0, -1)
            if key[pygame.K_DOWN]:
                self.game.move_player(0, 1)


            FPSCLOCK.tick(120)

            self.view.draw()
            self.view.update()


        #Finish main game loop
        self.end()
        pygame.quit()
        sys.exit()

    def end(self):
        pass

