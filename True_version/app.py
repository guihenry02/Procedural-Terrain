from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from terrain import Terrain

class MyApp(App):
    def build(self):
        root = FloatLayout()
        self.terrain_widget = Terrain(size_hint=(1, 1))
        root.add_widget(self.terrain_widget)
        self.control_panel = BoxLayout(orientation='vertical', size_hint=(None, None), size=(300, 200), spacing=5, padding=5)
        self.control_panel.pos_hint = {'y': 0.5, 'right': 1}
        
        # Controles
        controls = [
            ("Sea Level", self.terrain_widget.sea_level, self.decrease_sea_level, self.increase_sea_level),
            ("Scale", self.terrain_widget.scale, self.decrease_scale, self.increase_scale),
            ("Persistence", self.terrain_widget.persistence, self.decrease_persistence, self.increase_persistence),
            ("Lacunarity", self.terrain_widget.lacunarity, self.decrease_lacunarity, self.increase_lacunarity),
            ("Octaves", self.terrain_widget.octaves, self.decrease_octaves, self.increase_octaves)
        ]
        
        for name, value, dec, inc in controls:
            self.control_panel.add_widget(self.create_control_row(name, value, dec, inc))
        
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

    # Métodos de controle
    def decrease_scale(self, label):
        step = 0.001
        new_value = max(0.005, self.terrain_widget.scale - step)
        self.terrain_widget.scale = new_value
        label.text = f"Scale: {new_value:.3f}"

    def increase_scale(self, label):
        step = 0.001
        new_value = min(0.0125, self.terrain_widget.scale + step)
        self.terrain_widget.scale = new_value
        label.text = f"Scale: {new_value:.3f}"

    def decrease_persistence(self, label):
        step = 0.1
        new_value = max(0.5, self.terrain_widget.persistence - step)
        self.terrain_widget.persistence = new_value
        label.text = f"Persistence: {new_value:.1f}"

    def increase_persistence(self, label):
        step = 0.025
        new_value = min(0.7, self.terrain_widget.persistence + step)
        self.terrain_widget.persistence = new_value
        label.text = f"Persistence: {new_value:.2f}"

    def decrease_lacunarity(self, label):
        step = 0.025
        new_value = max(2.0, self.terrain_widget.lacunarity - step)
        self.terrain_widget.lacunarity = new_value
        label.text = f"Lacunarity: {new_value:.2f}"

    def increase_lacunarity(self, label):
        step = 0.025
        new_value = min(3.0, self.terrain_widget.lacunarity + step)
        self.terrain_widget.lacunarity = new_value
        label.text = f"Lacunarity: {new_value:.1f}"

    def decrease_octaves(self, label):
        step = 1
        new_value = max(1, self.terrain_widget.octaves - step)
        self.terrain_widget.octaves = new_value
        label.text = f"Octaves: {new_value}"

    def increase_octaves(self, label):
        step = 1
        new_value = min(10, self.terrain_widget.octaves + step)
        self.terrain_widget.octaves = new_value
        label.text = f"Octaves: {new_value}"

    def decrease_sea_level(self, label):
        step = 0.01
        new_value = self.terrain_widget.sea_level - step
        new_value = max(-0.3, new_value)
        self.terrain_widget.set_sea_level(new_value)
        label.text = f"Sea Level: {new_value:.2f}"

    def increase_sea_level(self, label):
        step = 0.01
        new_value = self.terrain_widget.sea_level + step
        new_value = min(0.3, new_value)
        self.terrain_widget.set_sea_level(new_value)
        label.text = f"Sea Level: {new_value:.2f}"

    def on_window_resize(self, instance, width, height):
        self.terrain_widget.generate_noise_texture()