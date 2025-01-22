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
    Aprimoramentos:
    Melhorar a renderização do terreno (agilizar)
    Incluir possibilidade de zoom e movimentação do terreno
    Conseguir colocar iluminação no ambiente
    Regenerar automaticamente
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
        self.scale = 0.02
        self.octaves = 7
        self.persistence = 0.5
        self.lacunarity = 2
    
        self.waterTerrain = TerrainType(0.0, 0.4, (30, 176, 251), (40, 255, 255))
        self.sandTerrain = TerrainType(0.4, 0.465, (215, 192, 158), (255, 246, 193))
        self.grassTerrain = TerrainType(0.465, 0.7, (2, 166, 155), (118, 239, 124))
        self.treesTerrain = TerrainType(0.7, 1.0, (22, 181, 141), (10, 145, 113))
        self.light_source = (Window.width/2, Window.height/2)
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
                normalized_value = (noise_value + 1) / 2
                terrain_color = self.get_terrain_color(normalized_value)
                pixels.extend([int(c) for c in terrain_color])
                row.append(normalized_value)
            self.height_map.append(row)
        self.texture.blit_buffer(bytes(pixels), colorfmt='rgb', bufferfmt='ubyte')

        with self.canvas:
            self.canvas.clear()
            Rectangle(texture=self.texture, pos=(0, 0), size=(Window.width, Window.height * 0.8))

        
        
            
    """def Shadow_Cast(self, light_pos):
        vector_count = 1000
        angle_step = 2 * math.pi / vector_count
        shadow_lines = []
        max_distance = 600  # Define a distância máxima para os vetores de sombra

        for i in range(vector_count):
            angle = i * angle_step
            x0, y0 = light_pos
            max_height = -float('inf')
            shadow_points = []
            
            for d in range(max_distance):
                x = int(x0 + math.cos(angle) * d)
                y = int(y0 + math.sin(angle) * d)

                if 0 <= x < len(self.height_map[0]) and 0 <= y < len(self.height_map):
                    height = self.height_map[y][x]
                    
                    if height > max_height:
                        max_height = height
                        shadow_points = [(x,y)]
                    else:
                        shadow_points.append((x,y))
                else:
                    break
                
            shadow_lines.append(shadow_points)
            
        with self.canvas:
            for shadow_points in shadow_lines:
                for i in range(len(shadow_points) - 1):
                    x1, y1 = shadow_points[i]
                    x2, y2 = shadow_points[i + 1]
                    Line(points=[x1, y1, x2, y2], width=1, close=False)"""
                
            
        

    def get_terrain_color(self, normalized_value):
        if normalized_value < self.waterTerrain.maxHeight:
            return self.get_color(normalized_value, self.waterTerrain)
        elif normalized_value < self.sandTerrain.maxHeight:
            return self.get_color(normalized_value, self.sandTerrain)
        elif normalized_value < self.grassTerrain.maxHeight:
            return self.get_color(normalized_value, self.grassTerrain)
        else:
            return self.get_color(normalized_value, self.treesTerrain)

    def get_color(self, noise_value, terrain):
        normalized = self.normalize(noise_value, terrain.maxHeight, terrain.minHeight)
        color = self.lerp_color(terrain.minColor, terrain.maxColor, normalized + terrain.lerpAdjustment)
        return tuple(max(0, min(255, c)) for c in color)

    def lerp_color(self, color1, color2, factor):
        return tuple(int(color1[i] + (color2[i] - color1[i]) * factor) for i in range(3))

    def normalize(self, value, max, min):
        if value > max:
            return 1
        if value < min:
            return 0
        return (value - min) / (max - min)


class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')  

       
        control_panel = BoxLayout(orientation='horizontal', size_hint=(1, None), height=100)

        scale_label = Label(text="Scale")
        self.scale_slider = Slider(min=0.005, max=0.03, value=0.02, step=0.005)

        persistence_label = Label(text="Persistence")
        self.persistence_slider = Slider(min=0.1, max=0.6, value=0.5, step=0.1)

        lacunarity_label = Label(text="Lacunarity")
        self.lacunarity_slider = Slider(min=1.0, max=3, value=2, step=0.1)

        octave_label = Label(text="Octaves")
        self.octaves_slider = Slider(min=1.0, max = 10.0, value = 7.0, step = 1.0)
        
    
        
        regenerate_button = Button(text="Regenerate Terrain", size_hint=(1, 0.1))
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
           
            self.gradient_color = Color(30/255, 176/255, 251/255, 1)  
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
