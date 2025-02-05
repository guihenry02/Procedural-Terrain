from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.graphics.texture import Texture
from noise import pnoise2
from kivy.clock import Clock
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
        self.scale = 0.005
        self.octaves = 8
        self.persistence = 0.6
        self.lacunarity = 2

        self.waterTerrain = TerrainType(-1.0, -0.15, (0, 0, 0), (40, 255, 255)) 
        self.sandTerrain = TerrainType(-0.15, -0.1, (215, 192, 100), (255, 246, 120))  
        self.grassTerrain = TerrainType(-0.1, 0.2, (20, 150, 40), (100, 200, 50))  
        self.forestTerrain = TerrainType(0.2, 0.3, (34, 139, 34), (85, 160, 85)) 
        self.mountainTerrain = TerrainType(0.3, 0.45, (120, 100, 60), (180, 160, 100))  
        self.snowTerrain = TerrainType(0.45, 1.0, (245, 245, 245), (255, 255, 255))  
        
        self.zoom = 1.0  
        self.tex_factor = 2.0  


        self.offset_x = 0.5
        self.offset_y = 0.5
        self.last_touch_pos = None
        
        self.height_map = []
        self.generate_noise_texture()
        
    def generate_noise_texture(self):
        tex_width = int(Window.width * self.tex_factor)
        tex_height = int(Window.height * self.tex_factor)
        pixels = []
        self.texture = Texture.create(size=(tex_width, tex_height), colorfmt='rgb')
        self.height_map = []  
        for y in range(tex_height):
            row = []
            for x in range(tex_width):
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

        self.canvas.clear()
        with self.canvas:
            self.rect = Rectangle(texture=self.texture, pos=(0, 0), size=(Window.width, Window.height))
        self.update_zoom()

    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                self.zoom = max(self.zoom * 0.9, 1.0 / self.tex_factor)
            elif touch.button == 'scrollup':
                self.zoom = min(self.zoom * 1.1, 10.0)
            self.update_zoom()
            return True
        else:
            self.last_touch_pos = (touch.x, touch.y)
            return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.last_touch_pos is not None:
            dx = touch.x - self.last_touch_pos[0]
            dy = touch.y - self.last_touch_pos[1]
            default_range_x = float(Window.width) / self.texture.width
            default_range_y = float(Window.height) / self.texture.height
            new_range_x = default_range_x / self.zoom
            new_range_y = default_range_y / self.zoom

            self.offset_x -= dx * (new_range_x / Window.width)
            self.offset_y -= dy * (new_range_y / Window.height)
            self.last_touch_pos = (touch.x, touch.y)
            self.update_zoom()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self.last_touch_pos = None
        return super().on_touch_up(touch)

    def update_zoom(self):
        default_range_x = float(Window.width) / self.texture.width
        default_range_y = float(Window.height) / self.texture.height
        new_range_x = default_range_x / self.zoom
        new_range_y = default_range_y / self.zoom

        min_offset_x = new_range_x / 2.0
        max_offset_x = 1.0 - new_range_x / 2.0
        min_offset_y = new_range_y / 2.0
        max_offset_y = 1.0 - new_range_y / 2.0
        self.offset_x = max(min(self.offset_x, max_offset_x), min_offset_x)
        self.offset_y = max(min(self.offset_y, max_offset_y), min_offset_y)

        u_min = self.offset_x - new_range_x / 2.0
        u_max = self.offset_x + new_range_x / 2.0
        v_min = self.offset_y - new_range_y / 2.0
        v_max = self.offset_y + new_range_y / 2.0
        self.rect.tex_coords = [u_min, v_min, u_max, v_min, u_max, v_max, u_min, v_max]

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
        if noise_value < terrain.minHeight:
            return terrain.minColor
        elif noise_value > terrain.maxHeight:
            return terrain.maxColor
        else:
            factor = (noise_value - terrain.minHeight) / (terrain.maxHeight - terrain.minHeight)
            return self.lerp_color(terrain.minColor, terrain.maxColor, factor)

    def lerp_color(self, color1, color2, factor):
        return tuple(int(color1[i] + (color2[i] - color1[i]) * factor) for i in range(3))


class MyApp(App):
    def build(self):
        root = FloatLayout()
        self.terrain_widget = MyWidget(size_hint=(1, 1))
        root.add_widget(self.terrain_widget)
        self.control_panel = BoxLayout(orientation='vertical',size_hint=(None, None),size=(300, 240),spacing=5,padding=5)
        self.control_panel.pos_hint = {'top': 1, 'right': 1}
        self.scale_box = self.create_control_row("Scale", self.terrain_widget.scale,self.decrease_scale, self.increase_scale)
        self.control_panel.add_widget(self.scale_box)
        self.persistence_box = self.create_control_row("Persistence", self.terrain_widget.persistence, self.decrease_persistence, self.increase_persistence)
        self.control_panel.add_widget(self.persistence_box)
        self.lacunarity_box = self.create_control_row("Lacunarity", self.terrain_widget.lacunarity, self.decrease_lacunarity, self.increase_lacunarity)
        self.control_panel.add_widget(self.lacunarity_box)
        self.octaves_box = self.create_control_row("Octaves", self.terrain_widget.octaves,self.decrease_octaves, self.increase_octaves)
        self.control_panel.add_widget(self.octaves_box)
        
        regenerate_button = Button(text="Regenerate", size_hint=(1, None), height=40)
        regenerate_button.bind(on_release=lambda instance: self.terrain_widget.generate_noise_texture())
        self.control_panel.add_widget(regenerate_button)

        root.add_widget(self.control_panel)
        Window.bind(on_resize=self.on_window_resize)
        return root

    def create_control_row(self, name, initial_value, dec_callback, inc_callback):
        row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5)
        label = Label(text=f"{name}: {initial_value}", size_hint=(0.6, 1))
        btn_dec = Button(text="-", size_hint=(0.2, 1))
        btn_dec.bind(on_release=lambda instance: dec_callback(label))
        btn_inc = Button(text="+", size_hint=(0.2, 1))
        btn_inc.bind(on_release=lambda instance: inc_callback(label))
        row.add_widget(label)
        row.add_widget(btn_dec)
        row.add_widget(btn_inc)
        return row

    def decrease_scale(self, label):
        step = 0.001
        new_value = max(0.005, self.terrain_widget.scale - step)
        self.terrain_widget.scale = new_value
        label.text = f"Scale: {new_value:.3f}"
        self.terrain_widget.generate_noise_texture()

    def increase_scale(self, label):
        step = 0.001
        new_value = min(0.0125, self.terrain_widget.scale + step)
        self.terrain_widget.scale = new_value
        label.text = f"Scale: {new_value:.3f}"
        self.terrain_widget.generate_noise_texture()

    def decrease_persistence(self, label):
        step = 0.1
        new_value = max(0.1, self.terrain_widget.persistence - step)
        self.terrain_widget.persistence = new_value
        label.text = f"Persistence: {new_value:.1f}"
        self.terrain_widget.generate_noise_texture()

    def increase_persistence(self, label):
        step = 0.1
        new_value = min(0.6, self.terrain_widget.persistence + step)
        self.terrain_widget.persistence = new_value
        label.text = f"Persistence: {new_value:.1f}"
        self.terrain_widget.generate_noise_texture()

    def decrease_lacunarity(self, label):
        step = 0.1
        new_value = max(1.0, self.terrain_widget.lacunarity - step)
        self.terrain_widget.lacunarity = new_value
        label.text = f"Lacunarity: {new_value:.1f}"
        self.terrain_widget.generate_noise_texture()

    def increase_lacunarity(self, label):
        step = 0.1
        new_value = min(3.0, self.terrain_widget.lacunarity + step)
        self.terrain_widget.lacunarity = new_value
        label.text = f"Lacunarity: {new_value:.1f}"
        self.terrain_widget.generate_noise_texture()

    def decrease_octaves(self, label):
        step = 1
        new_value = max(1, self.terrain_widget.octaves - step)
        self.terrain_widget.octaves = new_value
        label.text = f"Octaves: {new_value}"
        self.terrain_widget.generate_noise_texture()

    def increase_octaves(self, label):
        step = 1
        new_value = min(10, self.terrain_widget.octaves + step)
        self.terrain_widget.octaves = new_value
        label.text = f"Octaves: {new_value}"
        self.terrain_widget.generate_noise_texture()

    def on_window_resize(self, instance, width, height):

        self.terrain_widget.generate_noise_texture()

if __name__ == '__main__':
    MyApp().run()
