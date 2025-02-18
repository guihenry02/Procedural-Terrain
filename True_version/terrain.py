from kivy.uix.widget import Widget
from kivy.graphics import Rectangle
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from noise import pnoise2
import math 
class TerrainType:
    def __init__(self, minHeight, maxHeight, minColor, maxColor, lerpAdjustment=0):
        self.minHeight = minHeight
        self.maxHeight = maxHeight
        self.minColor = minColor
        self.maxColor = maxColor
        self.lerpAdjustment = lerpAdjustment

class Terrain(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = 0.005
        self.octaves = 8
        self.persistence = 0.6
        self.lacunarity = 2
        self.sea_level = -0.15
        
        # Parâmetros de iluminação
        self.light_angle = 45  # Ângulo em graus
        self.light_intensity = 0.8
        self.ambient_light = 0.6
        
        self.update_terrain_ranges()
         
        self.zoom = 1.0  
        self.tex_factor = 2.0  
        self.offset_x = 0.5
        self.offset_y = 0.5
        self.last_touch_pos = None
        self.height_map = []
        self.generate_noise_texture()
    
    def calculate_normal(self, x, y, strength=50.0):
        """Calcula a normal do terreno em um ponto específico"""
        
        if self.height_map[y][x] < self.waterTerrain.maxHeight:
            return (0, 0, 1)
        if x <= 0 or x >= len(self.height_map[0])-1:
            dx = 0
        else:
            dx = (self.height_map[y][x-1] - self.height_map[y][x+1]) * strength
            
        if y <= 0 or y >= len(self.height_map)-1:
            dy = 0
        else:
            dy = (self.height_map[y-1][x] - self.height_map[y+1][x]) * strength
            
        return (-dx, -dy, 1.0)

    def get_light_vector(self):
        """Calcula o vetor de direção da luz baseado no ângulo"""
        angle = math.radians(self.light_angle)
        return (math.cos(angle), math.sin(angle), 0.5)

    def apply_lighting(self, color, normal):
        """Aplica iluminação à cor base"""
        light_dir = self.get_light_vector()
        diffuse = max(0, sum(n * l for n, l in zip(normal, light_dir)))
        diffuse = min(diffuse * self.light_intensity, 1.0)
        total_light = self.ambient_light + (1 - self.ambient_light) * diffuse
        return tuple(min(int(c * total_light), 255) for c in color)

    def update_terrain_ranges(self):
        self.waterTerrain = TerrainType(-1.0, self.sea_level, (0, 0, 0), (40, 255, 255))
        sand_max = self.sea_level + 0.05
        self.sandTerrain = TerrainType(self.sea_level, sand_max, (215, 192, 100), (255, 246, 120))
        grass_max = sand_max + 0.25
        self.grassTerrain = TerrainType(sand_max, grass_max, (20, 150, 40), (100, 200, 50))
        forest_max = grass_max + 0.1
        self.forestTerrain = TerrainType(grass_max, forest_max, (34, 139, 34), (85, 160, 85))
        mountain_max = forest_max + 0.15
        self.mountainTerrain = TerrainType(forest_max, mountain_max, (120, 100, 60), (180, 160, 100))
        self.snowTerrain = TerrainType(mountain_max, 1.0, (245, 245, 245), (255, 255, 255))

    def set_sea_level(self, new_level):
        self.sea_level = new_level
        self.update_terrain_ranges()

    def generate_noise_texture(self):
        tex_width = int(Window.width * self.tex_factor)
        tex_height = int(Window.height * self.tex_factor)
        
        # Primeira passada: gerar height_map
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
                row.append(noise_value)
            self.height_map.append(row)
        
        # Segunda passada: aplicar iluminação
        pixels = []
        self.texture = Texture.create(size=(tex_width, tex_height), colorfmt='rgb')
        for y in range(tex_height):
            for x in range(tex_width):
                noise_value = self.height_map[y][x]
                base_color = self.get_terrain_color(noise_value)
                normal = self.calculate_normal(x, y)
                shaded_color = self.apply_lighting(base_color, normal)
                pixels.extend(shaded_color)
        
        self.texture.blit_buffer(bytes(pixels), colorfmt='rgb', bufferfmt='ubyte')
        self.canvas.clear()
        with self.canvas:
            self.rect = Rectangle(texture=self.texture, pos=(0, 0), size=(Window.width, Window.height))
        self.update_zoom()

    # Restante dos métodos do terrain...
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