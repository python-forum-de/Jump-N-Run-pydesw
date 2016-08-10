# -*- coding: utf-8 -*-
import pygame
import configparser
import json
import re
import os


class Configurations(object):
    ''' Klasse behandelt alle Konfigs die geladen / gespeichert / verändert werden
    '''

    anzahl_configurations = 0
    def __init__(self):
        self.configurations = dict()

    def set(self, filename, selection, option, value):
        # setzt den jeweiligen Wert neu
        # Datei wird nur bei neuen Daten geschrieben
        config = self.configurations[filename]    
        value_old = json.loads(config.get(selection, option))
        config.set(selection, option, str(value))
        if value != value_old:
            self.save_file(filename)
    
    def save_file(self, filename):
        with open(filename, 'w') as configfile:
            self.configurations[filename].write(configfile)

    def load_dict(self, defaults, filename):
        # Uebergebenes Dictionary muss immer zuerst eingelesen werden
        # Konfig soll diese Standardwerte immer überschreiben
        if filename not in self.configurations:
            Configurations.anzahl_configurations += 1
            self.configurations[filename] = configparser.ConfigParser()
            self.configurations[filename].read_dict(defaults)
            self.load_file(filename)

    def load_file(self, filename):
        # Datei einlesen mittels ConfigParser
        if filename not in self.configurations:
            Configurations.anzahl_configurations += 1
            self.configurations[filename] = configparser.ConfigParser()
        try:
            with open(filename, 'r') as configfile:
                self.configurations[filename].read_file(configfile)
        except FileNotFoundError:
            print("Datei existiert nicht, wenn Optionen geandert werden, wird diese geschrieben")

    def get_options(self, filename, sections):
        ''' Example Usage
            # (self.display, self.menu) = self.get_options(filename, ("display", "menu",))
        '''
        data = dict()

        self.load_file(filename)
        config = self.configurations[filename]
        for section in sections:
            data[section] = dict()
            try: 
                options = config.options(section)
                for option in options:
                    value = str(re.sub("'","\"",config.get(section, option)))
                    try:
                        data[section][option] = json.loads(value)
                    except ValueError:
                        # Fehler tritt auf, weil in value kein valider Syntax für json ist
                        data[section][option] = config.get(section, option)

            except configparser.NoSectionError:
                print("Auswahl nicht vorhanden: %s" % section)
        
        # falls nur ein Abschnitt geholt werden muss
        if len(sections) == 1:
            return data[sections[0]]
        else:
            return [data[x] for x in sections]
  
class Game(object):
    def __init__(self, configurations, filename):
        self.configurations = configurations
        self.game_display = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.filename = filename
        self.setup_game()
    
    def setup_game(self):
        self.exit = False
        self.choosed_option = ""
        self.figures = pygame.sprite.Group()
        self.display, self.colors = self.configurations.get_options(self.filename, ("display", "colors"))
        self.player = Figure(self.figures)

    def loop(self):
        pygame.event.clear()
        self.setup_game()
        while not self.exit:
            if pygame.key.get_pressed()[pygame.K_LEFT] != 0 :
                self.player.left()
            if pygame.key.get_pressed()[pygame.K_RIGHT] != 0 :
                self.player.right()

            # event = pygame.event.wait()
            for event in pygame.event.get():
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        self.choosed_option = "menu"
                        self.exit = True
                if event.type == pygame.QUIT:
                    self.choosed_option = "menu"
                    self.exit = True
                    
            self.game_display.fill((192,0,0))
            self.show_fps()

            self.figures.draw(self.game_display)

            pygame.display.update()
            self.clock.tick(self.display["fps"])
        
        return self.choosed_option
    
    def show_fps(self):
        fps = self.clock.get_fps()
        font = pygame.font.Font('freesansbold.ttf', 85)
        self.game_display.blit(font.render("fps: %i" % fps, 1, self.colors["white"]), (0, 0))
      
class Figure(pygame.sprite.Sprite):
    ''' Erstellt ein pygame.image mit Text 
    '''
    def __init__(self, blocks_group, color=(255,224,224)):
        pygame.sprite.Sprite.__init__(self, blocks_group)
        self.image = pygame.Surface([48, 48])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.left = 200
        self.rect.top = 300
    
    def left(self):
        if self.rect.left > 0:
            self.rect.left -= 3
    
    def right(self):
        display = pygame.display.get_surface()
        rect = display.get_rect()
        if self.rect.right < rect.right:
            self.rect.left += 3
        
class Block(pygame.sprite.Sprite):
    ''' Erstellt ein pygame.image mit Text 
    '''
    def __init__(self, name, element_number, blocks_group, message=""):
        pygame.sprite.Sprite.__init__(self, blocks_group)
        self.function_name = name
        self.name = name
        self.special_message = message
        self.largeText = pygame.font.Font('freesansbold.ttf', 85)
        self.height = element_number
        self.normal()

    def create_text_surface(self, text, font, color=(0, 0, 0)):
        textSurface = font.render( text.capitalize(), True, color)
        return textSurface, textSurface.get_rect()
 
    def normal(self):
        # erzeugt einen Text mit schwarzer Schriftfarbe
        name = "%s %s" % (self.name, self.special_message)
        self.image, self.rect = self.create_text_surface(name, self.largeText)
        self.rect.left = 100
        self.rect.top = 90 * self.height
        
    def hover(self):
        # erzeugt einen Text mit blauer Schriftfarbe - eine Art Highlighting weil es durch Mouseover erzeugt wird
        name = "%s %s" % (self.name, self.special_message)
        self.image, self.rect = self.create_text_surface(name, self.largeText, (32, 128, 224))
        self.rect.left = 100
        self.rect.top = 90 * self.height

class Menu(object):
    def __init__(self, configurations, filename="standard.cfg"):
        self.configurations = configurations
        self.filename = filename
        self.clock = pygame.time.Clock()
        self.packed_functions = {"quit": self.quit}
        self.configurations.load_dict(self.load_standard_configuration(), self.filename)
        self.setup_settings()
        
    def setup_settings(self):
        # alle notwendigen Variablen setzen / resetten und das Menu laden
        self.choosed_option = ""
        self.exit = False
        self.display, self.colors = self.configurations.get_options(self.filename, ("display", "colors"))
        self.game_display = pygame.display.set_mode((self.display["width"], self.display["height"]))
        self.load_menu()

    def load_standard_configuration(self):
        # Platzhalter - Hook
        options = { 
            "display" : {"width": 640, "height": 480, "fps": 30},
            "info": {"title": "menu", "order_menu": ["quit"]},
            "colors": {"black": [0, 0, 0], "white": [255, 255, 255]},
            "menu": {"quit": "quit"}
        }
        return options

    def load_menu(self):
        self.blocks = pygame.sprite.Group()
        info = self.configurations.get_options(self.filename, ("info",))
        pygame.display.set_caption(info["title"])
        if len(info["order_menu"]) == 1:
            Block(info["order_menu"][0], 1, self.blocks)
        else:
            for nr, point in enumerate(info["order_menu"]):
                Block(point, nr+1, self.blocks)
    
    def loop(self):
        pygame.event.clear()
        self.setup_settings()
        while not self.exit:
            # event = pygame.event.wait()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEMOTION:
                    for (block, coordinates) in [ (block, block.rect) for block in self.blocks ]:
                        if coordinates.collidepoint(pygame.mouse.get_pos()): block.hover()
                        else: block.normal()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for (function_name, coordinates) in [ (block.function_name, block.rect) for block in self.blocks ]:
                        if coordinates.collidepoint(pygame.mouse.get_pos()):
                            try: self.packed_functions[function_name]()
                            except KeyError:
                                print("Hinterlegte Funktion existiert nicht!")
                    
            self.game_display.fill(self.colors["white"])
            self.blocks.draw(self.game_display)
            pygame.display.update()
            
            self.clock.tick(self.display["fps"])

        return self.choosed_option

    def quit(self):
        # schließt das Menu
        self.exit = True

class StartMenu(Menu):
    def __init__(self, configurations, filename="standard.cfg"):
        self.configurations = configurations
        # self.load_standard_configuration()
        Menu.__init__(self, configurations, filename)
        self.packed_functions ={"start": self.start_game, "options": self.show_options, "quit": self.quit,
                                "multiplayer": self.multiplayer, "fps": self.change_fps, "size": self.change_size,
                                "zurueck": self.backward}
        self.filename = filename
        self.depth = ["menu"]
       
    def load_options(self):
        self.blocks = pygame.sprite.Group()
        (info, options) = self.configurations.get_options(self.filename, ("info", "options"))
        pygame.display.set_caption("Optionen")
        for nr, point in enumerate(info["order_options"]):
            message = ""
            if point in options:
                if point == "fps":
                    message = "%i" % self.display["fps"]
                elif point == "size":
                    message = "%sx%s" % (self.display["width"], self.display["height"])
            Block(point, nr+1, self.blocks, str(message))

    def load_standard_configuration(self):
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
        self.choosed_option = "game"
        self.exit = True
    
    def show_options(self):
        # lädt das Menu für die Optionen
        self.depth.append("options")
        self.load_options()
    
    def change_fps(self):
        # ändert die FPS anhand der hinterlegten Optionen
        options = self.configurations.get_options(self.filename, ("options",))
        nummer = options["fps"].index(self.display["fps"])
        if len(options["fps"])-1 == nummer: message = options["fps"][0]
        else: message = options["fps"][nummer+1]
        self.display["fps"] = message
        self.configurations.set(self.filename, "display", "fps", message)
        self.load_options()
    
    def change_size(self):
        # ändert die Grösse des Fensters anhand der hinterlegten Optionen
        options = self.configurations.get_options(self.filename, ("options",))
        message = "%sx%s" % (self.display["width"], self.display["height"])
        nummer = options["size"].index(message)
        if len(options["size"])-1 == nummer: message = options["size"][0]
        else: message = options["size"][nummer+1]
        (width, height) = message.split("x")
        self.display["width"] = int(width)
        self.display["height"] = int(height)
        self.configurations.set(self.filename, "display", "width", self.display["width"])
        self.configurations.set(self.filename, "display", "height", self.display["height"])

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
    configuration_filename = "%s\\menu.cfg" % pfad
    configuration = Configurations()
    spielmenu = StartMenu(configuration, configuration_filename)
    spiel = Game(configuration, configuration_filename)

    # möglichkeit zwischen menu und spiel zuwechseln
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
