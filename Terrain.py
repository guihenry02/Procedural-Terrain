from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, Line
from kivy.graphics.texture import Texture
from noise import pnoise2
from kivy.clock import Clock
from concurrent.futures import ThreadPoolExecutor
import math
import numpy as np

"""
    Possibilidades de Aprimoramentos:
    Melhorar a interface
    Melhorar a renderização do terreno (agilizar)
    Incluir possibilidade de zoom e movimentação do terreno
    Conseguir colocar iluminação no ambiente (dificil)
    Geração de biomas (chunks com padrões pré-definidos)
"""


class TerrainType:
    def __init__(self, minHeight, maxHeight, minColor, maxColor, lerpAdjustment=0):
        self.minHeight = minHeight
        self.maxHeight = maxHeight
        self.minColor = minColor
        self.maxColor = maxColor
        self.lerpAdjustment = lerpAdjustment


class MyWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = 0.007
        self.octaves = 7
        self.persistence = 0.5
        self.lacunarity = 2

        # Definições de terreno ajustadas para novas faixas
        self.waterTerrain = TerrainType(-1.0, -0.15, (0, 0, 0), (40, 255, 255))  # Água (azul claro)
        self.sandTerrain = TerrainType(-0.15, -0.1, (215, 192, 100), (255, 246, 120))  # Areia (bege)
        self.grassTerrain = TerrainType(-0.1, 0.2, (20, 150, 40), (100, 200, 50))  # Grama (verde)
        self.forestTerrain = TerrainType(0.2, 0.3, (34, 139, 34), (85, 160, 85))  # Floresta (verde escuro)
        self.mountainTerrain = TerrainType(0.3, 0.45, (120, 100, 60), (180, 160, 100))  # Montanhas (marrom)
        self.snowTerrain = TerrainType(0.45, 1.0, (245, 245, 245), (255, 255, 255))  # Neve (branco)
        
        self.height_map = []
        self.generate_noise_texture()
        
    def generate_noise_texture(self):
        pixels = []
        self.texture = Texture.create(size=(int(Window.width), int(Window.height * 0.8)), colorfmt='rgb')
        for y in range(int(Window.height * 0.8)):
            row = []
            for x in range(int(Window.width)):
                noise_value = pnoise2(
                    x * self.scale,
                    y * self.scale,
                    octaves=self.octaves,
                    persistence=self.persistence,
                    lacunarity=self.lacunarity,
                    base=42
                )
                terrain_color = self.get_terrain_color(noise_value)
                pixels.extend([int(c) for c in terrain_color])
                row.append(noise_value)
            self.height_map.append(row)
        self.texture.blit_buffer(bytes(pixels), colorfmt='rgb', bufferfmt='ubyte')

        with self.canvas:
            self.canvas.clear()
            Rectangle(texture=self.texture, pos=(0, 0), size=(Window.width, Window.height * 0.8))

    def get_terrain_color(self, noise_value):

        if noise_value < self.waterTerrain.maxHeight:
            return self.get_color(noise_value, self.waterTerrain)
        elif noise_value < self.sandTerrain.maxHeight:
            return self.get_color(noise_value, self.sandTerrain)
        elif noise_value < self.grassTerrain.maxHeight:
            return self.get_color(noise_value, self.grassTerrain)
        elif noise_value < self.forestTerrain.maxHeight:
            return self.get_color(noise_value, self.forestTerrain)
        elif noise_value < self.mountainTerrain.maxHeight:
            return self.get_color(noise_value, self.mountainTerrain)
        else:
            return self.get_color(noise_value, self.snowTerrain)


    def get_color(self, noise_value, terrain):
        # Para outros terrenos, mapeamos diretamente o valor de noise
        if noise_value < terrain.minHeight:
            return terrain.minColor
        elif noise_value > terrain.maxHeight:
            return terrain.maxColor
        else:
            # Linear interpolation para obter a cor intermediária
            factor = (noise_value - terrain.minHeight) / (terrain.maxHeight - terrain.minHeight)
            return self.lerp_color(terrain.minColor, terrain.maxColor, factor)

    def lerp_color(self, color1, color2, factor):
        return tuple(int(color1[i] + (color2[i] - color1[i]) * factor) for i in range(3))


class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        control_panel = BoxLayout(orientation='horizontal', size_hint=(1, None), height=100, padding=[0, 0, 30, 0])

        scale_label = Label(text="Scale")
        self.scale_slider = Slider(min=0.005, max=0.0125, value=0.007, step=0.001)

        persistence_label = Label(text="Persistence")
        self.persistence_slider = Slider(min=0.1, max=0.6, value=0.5, step=0.1)

        lacunarity_label = Label(text="Lacunarity")
        self.lacunarity_slider = Slider(min=1.0, max=3, value=2, step=0.1)

        octave_label = Label(text="Octaves")
        self.octaves_slider = Slider(min=1.0, max=10.0, value=7.0, step=1.0)

        regenerate_button = Button(text="Regenerate", size_hint=(1, 0.25))
        regenerate_button.bind(on_release=self.regenerate_terrain)

        control_panel.add_widget(scale_label)
        control_panel.add_widget(self.scale_slider)
        control_panel.add_widget(persistence_label)
        control_panel.add_widget(self.persistence_slider)
        control_panel.add_widget(lacunarity_label)
        control_panel.add_widget(self.lacunarity_slider)
        control_panel.add_widget(octave_label)
        control_panel.add_widget(self.octaves_slider)
        control_panel.add_widget(regenerate_button)

        layout.add_widget(control_panel)

        self.terrain_widget = MyWidget()
        layout.add_widget(self.terrain_widget)

        with layout.canvas.before:
            self.gradient_color = Color(30 / 255, 176 / 255, 251 / 255, 1)
            self.rect = Rectangle(size=Window.size, pos=layout.pos)

            self.update_gradient()

        Window.bind(on_resize=self.on_window_resize)

        return layout

    def on_window_resize(self, instance, width, height):
        self.update_gradient()
        self.rect.size = instance.size
        self.terrain_widget.generate_noise_texture()

    def regenerate_terrain(self, instance):
        self.terrain_widget.scale = self.scale_slider.value
        self.terrain_widget.persistence = self.persistence_slider.value
        self.terrain_widget.lacunarity = self.lacunarity_slider.value
        self.terrain_widget.octaves = int(self.octaves_slider.value)
        self.terrain_widget.generate_noise_texture()

    def update_gradient(self):
        gradient = Texture.create(size=(Window.width, Window.height), colorfmt='rgb')
        gradient_pixels = []

        for y in range(Window.height):
            r = g = b = 30 + (y / Window.height) * (118 - 30)
            gradient_pixels.extend([int(r), int(g), int(b)] * Window.width)

        gradient.blit_buffer(bytes(gradient_pixels), colorfmt='rgb', bufferfmt='ubyte')
        self.rect.texture = gradient

if __name__ == '__main__':
    MyApp().run()