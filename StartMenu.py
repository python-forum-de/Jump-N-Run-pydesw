# -*- coding: utf-8 -*-
import pygame
import configparser
import json
import re
import os


class ConfigHandler(object):
    ''' Klasse behandelt alle Konfigs die geladen / gespeichert / veraendert werden
    '''
    Configurations = dict()

    @staticmethod
    def set(filename="standard", *args):
        # setzt den jeweiligen Wert neu
        config = ConfigHandler.Configurations[filename]    
        if len(args) == 3:
            value = json.loads(config.get(args[0], args[1]))
            config.set(args[0], args[1], str(args[2]))
            if value != args[2]:
                ConfigHandler.save_file(filename)

    @staticmethod
    def load_dict(defaults, filename):
        # Uebergebenes Dictionary muss immer zuerst eingelesen werden
        # Konfig soll diese Standardwerte immer ueberschreiben
        if filename not in ConfigHandler.Configurations:
            ConfigHandler.Configurations[filename] = configparser.ConfigParser()
            ConfigHandler.Configurations[filename].read_dict(defaults)
            ConfigHandler.load_file(filename)
    
    @staticmethod
    def save_file(filename):
        if filename != "standard":
            with open(filename, 'w') as configfile:
                ConfigHandler.Configurations[filename].write(configfile)

    @staticmethod
    def load_file(filename):
        # Datei einlesen mittels ConfigParser
        if filename not in ConfigHandler.Configurations:
            ConfigHandler.Configurations[filename] = configparser.ConfigParser()
        if filename != "standard":
            try:
                with open(filename, 'r') as configfile:
                    ConfigHandler.Configurations[filename].read_file(configfile)
            except FileNotFoundError:
                print("Datei existiert nicht, wenn Optionen geandert werden, wird diese geschrieben")

    @staticmethod
    def get_options(filename, sections):
        ''' Example Usage
            # (self.display, self.menu) = ConfigHandler.get_options(filename, ("display", "menu",))
        '''
        dict1 = dict()

        ConfigHandler.load_file(filename)
        config = ConfigHandler.Configurations[filename]
        for section in sections:
            dict1[section] = dict()
            try: 
                options = config.options(section)
                for option in options:
                    value = str(re.sub("'","\"",config.get(section, option)))
                    try:
                        dict1[section][option] = json.loads(value)
                    except ValueError:
                        # Fehler tritt auf, weil in value kein valider Syntax fuer json ist
                        dict1[section][option] = config.get(section, option)

            except configparser.NoSectionError:
                print("Auswahl nicht vorhanden: %s" % section)
        
        # falls nur ein Abschnitt geholt werden muss
        if len(sections) == 1: return dict1[sections[0]]
        else: return [dict1[x] for x in sections]
  
class Game(object):
    def __init__(self, filename):
        self.exit_option = False
        self.game_display = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.filename = filename
        self.load_settings()
    
    def load_settings(self):
        self.figurs = pygame.sprite.Group()
        self.display, self.colors = ConfigHandler.get_options(self.filename, ("display", "colors"))
        self.player = Figur(self.figurs)

    def loop(self):
        self.load_settings()
        while not self.exit_option:

            if pygame.key.get_pressed()[pygame.K_LEFT] != 0 :
                self.player.left()
            if pygame.key.get_pressed()[pygame.K_RIGHT] != 0 :
                self.player.right()

            # event = pygame.event.wait()
            for event in pygame.event.get():
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        self.exit_option = "menu"
                if event.type == pygame.QUIT:
                    self.exit_option = "menu"
                    
            self.game_display.fill((192,0,0))
            self.show_fps()

            self.figurs.draw(self.game_display)

            pygame.display.update()
            self.clock.tick(self.display["fps"])
        
        temp = self.exit_option
        self.exit_option = False
        return temp
    
    def show_fps(self):
        fps = self.clock.get_fps()
        font = pygame.font.Font('freesansbold.ttf',85)
        self.game_display.blit(font.render("fps: %i" % fps, 1, self.colors["white"]), (0,0))
        # pass
      
class Figur(pygame.sprite.Sprite):
    ''' Erstellt ein pygame.image mit Text 
    '''
    def __init__(self, blocks_group, color=(255,224,224)):
        pygame.sprite.Sprite.__init__(self, blocks_group)
        self.image = pygame.Surface([48, 48])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect[0] = 200
        self.rect[1] = 300
    
    def left(self):
        display = pygame.display.get_surface()
        rect = display.get_rect()
        if self.rect[0] > 0:
            self.rect[0] -= 3
    
    def right(self):
        display = pygame.display.get_surface()
        rect = display.get_rect()
        print(rect)
        if self.rect[0] < rect[2]:
            self.rect[0] += 3
        
class Block(pygame.sprite.Sprite):
    ''' Erstellt ein pygame.image mit Text 
    '''
    def __init__(self, name, element_nummer, blocks_group, msg=""):
        pygame.sprite.Sprite.__init__(self, blocks_group)
        self.function_name = name
        self.name = name
        self.special_msg = msg
        self.largeText = pygame.font.Font('freesansbold.ttf',85)
        self.height = element_nummer
        self.normal()

    def text_objects(self, text, font, color=(0,0,0)):
        textSurface = font.render( text.capitalize(), True, color)
        return textSurface, textSurface.get_rect()
 
    def get_rect(self):
        return self.rect
    
    def normal(self):
        name = "%s %s" % (self.name, self.special_msg)
        self.image, self.rect = self.text_objects(name, self.largeText)
        self.rect[0] = 100
        self.rect[1] = 90 * self.height
        
    def hover(self):
        name = "%s %s" % (self.name, self.special_msg)
        self.image, self.rect = self.text_objects(name, self.largeText, (32, 128, 224))
        self.rect[0] = 100
        self.rect[1] = 90 * self.height

    def get_fkt(self):
        return self.function_name

class Menu(object):
    def __init__(self, filename="standard"):
        self.filename = filename
        self.packed_functions = {"quit": self.quit}
        self.load_settings()
        
        self.game_display = pygame.display.set_mode((self.display["width"], self.display["height"]))
        self.clock = pygame.time.Clock()
        self.exit_option = False
        
        self.load_menu()
    
    def load_settings(self):
        # laedt die fuer das Menu hinterlegten Settings (Aufloesung, Menupunkte etc.)
        ConfigHandler.load_dict(self.load_std_cfg(), self.filename)
        self.display, self.colors = ConfigHandler.get_options(self.filename, ("display", "colors"))

    def load_std_cfg(self):
        # Platzhalter - Hook
        options = { 
            "display" : {"width": 640, "height": 480, "fps": 30},
            "info": {"title": "menu", "order_menu": ["quit"]},
            "colors": {"black": [0,0,0], "white": [255,255,255]},
            "menu": {"quit": "quit"}
        }
        return options

    def load_menu(self):
        self.blocks = pygame.sprite.Group()
        info = ConfigHandler.get_options(self.filename, ("info",))
        pygame.display.set_caption(info["title"])
        if len(info["order_menu"]) == 1:
            Block(info["order_menu"][0], 1, self.blocks)
        else:
            for nr, point in enumerate(info["order_menu"]):
                Block(point, nr+1, self.blocks)
    
    def loop(self):
        self.load_settings()
        pygame.event.clear()
        while not self.exit_option:
            # event = pygame.event.wait()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEMOTION:
                    for (block, coordinates) in [ (block, block.get_rect()) for block in self.blocks ]:
                        if coordinates.collidepoint(pygame.mouse.get_pos()): block.hover()
                        else: block.normal()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for (function_name, coordinates) in [ (block.get_fkt(), block.get_rect()) for block in self.blocks ]:
                        if coordinates.collidepoint(pygame.mouse.get_pos()):
                            try: self.packed_functions[function_name]()
                            except KeyError:
                                print("Hinterlegte Funktion existiert nicht!")
                    
           
            self.game_display.fill(self.colors["white"])
            for element in self.blocks:
                self.game_display.blit(element.image, element.rect.topleft)
            pygame.display.update()
            
            self.clock.tick(self.display["fps"])

        temp = self.exit_option
        self.exit_option = False
        return temp

    def quit(self):
        # schließt das Menu
        self.exit_option = "quit"

class StartMenu(Menu):
    def __init__(self, filename=""):
        # self.load_std_cfg()
        Menu.__init__(self, filename)
        self.packed_functions ={"start": self.start_game, "options": self.show_options, "quit": self.quit,
                                "multiplayer": self.multiplayer, "fps": self.change_fps, "size": self.change_size,
                                "zurueck": self.backward}
        self.filename = filename
        self.depth = ["menu"]
    
    def load_options(self):
        self.blocks = pygame.sprite.Group()
        (info, options) = ConfigHandler.get_options(self.filename, ("info", "options"))
        pygame.display.set_caption("Optionen")
        for nr, point in enumerate(info["order_options"]):
            msg = ""
            if point in options:
                if point == "fps":
                    msg = "%i" % self.display["fps"]
                elif point == "size":
                    msg = "%sx%s" % (self.display["width"], self.display["height"])
            Block(point, nr+1, self.blocks, str(msg))

    def load_std_cfg(self):
        # Standardwerte des Menus
        options = { 
                    "display" : {"width": 800, "height": 600, "fps": 60},
                    "info": {"title": "Spielmenu", "order_menu": ["start", "multiplayer", "options", "quit"], 
                             "order_options": ["fps", "size", "zurueck"]},
                    "colors": {"black": [0,0,0], "white": [255,255,255], "red": [255,0,0], "blue": [0,255,0], "green": [0,0,255]},
                    "options": {"fps":[30,60,90,120], "size":["640x480", "800x600", "1024x768", "1200x900", "1600x1200", "1920x1080"]}
                }
        return options

    def multiplayer(self):
        print("Multiplayer Part")

    def start_game(self):
        self.exit_option = "game"
    
    def show_options(self):
        # laedt das Menu fuer die Optionen
        self.depth.append("options")
        self.load_options()
    
    def change_fps(self):
        # aendert die FPS anhand der hinterlegten Optionen
        options = ConfigHandler.get_options(self.filename, ("options",))
        nummer = options["fps"].index(self.display["fps"])
        if len(options["fps"])-1 == nummer: msg = options["fps"][0]
        else: msg = options["fps"][nummer+1]
        self.display["fps"] = msg
        ConfigHandler.set(self.filename, "display", "fps", msg)
        self.load_options()
    
    def change_size(self):
        # aendert die Groesse des Fensters anhand der hinterlegten Optionen
        options = ConfigHandler.get_options(self.filename, ("options",))
        msg = "%sx%s" % (self.display["width"], self.display["height"])
        nummer = options["size"].index(msg)
        if len(options["size"])-1 == nummer: msg = options["size"][0]
        else: msg = options["size"][nummer+1]
        (width, height) = msg.split("x")
        self.display["width"] = int(width)
        self.display["height"] = int(height)
        ConfigHandler.set(self.filename, "display", "width", self.display["width"])
        ConfigHandler.set(self.filename, "display", "height", self.display["height"])

        self.game_display = pygame.display.set_mode((self.display["width"], self.display["height"]))
        self.load_options()
    
    def backward(self):
        # geht ein Menupunkt hoch
        self.depth.pop()
        if self.depth[-1] == "menu":
            self.load_menu()
 

def main():
    pygame.init()

    pfad = os.path.dirname(os.path.realpath(__file__))
    cfg = "%s\\menu.cfg" % pfad
    spielmenu = StartMenu(cfg)
    spiel = Game(cfg)

    # meoglichkeit zwischen menu und spiel zuwechseln
    option = "menu"
    while True:
        if "menu" == option:
            option = spielmenu.loop()
        elif "game" == option:
            option = spiel.loop()
        else: 
            break

    pygame.quit()
    quit()

if '__main__' == __name__:
    main()
