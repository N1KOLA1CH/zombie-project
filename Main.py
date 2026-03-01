import arcade
import arcade.gui
from Play_map import MyGame

SCREEN_W = 1280
SCREEN_H = 720
TITLE = 'Зомбидавитель'

class Menu(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.background = arcade.load_texture('assets/images/zb.png')
        background_music = arcade.load_sound("assets/sound/menu_music.mp3")
        self.music = arcade.play_sound(background_music, volume=0.5, loop=True)

        vert_box = arcade.gui.UIBoxLayout(space_between=20)

        button_play = arcade.gui.UIFlatButton(text="Играть", width=250, height=60)
        button_records = arcade.gui.UIFlatButton(text="Рекорды", width=250, height=60)
        button_exit = arcade.gui.UIFlatButton(text="Выйти", width=250, height=60)

        button_play.on_click = self.start_play
        button_exit.on_click = self.close_game

        vert_box.add(button_play)
        vert_box.add(button_records)
        vert_box.add(button_exit)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=vert_box,
            anchor_x="center_x",
            anchor_y="center_y"
        )

        self.manager.add(anchor)

    def start_play(self, event):
        game = MyGame()
        arcade.stop_sound(self.music)
        game.setup()
        self.window.show_view(game)

    def close_game(self, event):
        arcade.exit()

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            texture=self.background,
            rect=arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height
            )
        )

        arcade.draw_text(
            "Зомбидавитель",
            self.window.width // 2,
            self.window.height - 100,
            arcade.color.RED,
            50,
            anchor_x="center"
        )
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_W, SCREEN_H, TITLE)
    window.show_view(Menu())
    arcade.run()


if __name__ == '__main__':
    main()
