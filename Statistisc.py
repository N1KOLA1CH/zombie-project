import arcade
import arcade.gui
import csv
import os


class RecordsView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.v_box = arcade.gui.UIBoxLayout(space_between=10)

        header = arcade.gui.UILabel(text="ТАБЛИЦА РЕКОРДОВ", font_size=30, text_color=arcade.color.GOLD)
        self.v_box.add(header)

        if os.path.exists("res.csv"):
            with open("res.csv", mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)

                rows = list(reader)[-7:]

                for row in rows:

                    if len(row) >= 4:
                        text = (f"{row[0]} | Монеты: {row[1]} | Убито зомби: {row[3]} | "
                            f"Смертей (Зомби): {row[2]} | Смертей (Лава): {row[4]}")
                        label = arcade.gui.UILabel(text=text, font_size=16, text_color=arcade.color.WHITE)
                        self.v_box.add(label)
        else:
            self.v_box.add(arcade.gui.UILabel(text="Файл res.csv не найден", text_color=arcade.color.GRAY))

        btn_back = arcade.gui.UIFlatButton(text="НАЗАД В МЕНЮ", width=200)
        btn_back.on_click = self.go_back
        self.v_box.add(btn_back)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_hide_view(self):
        self.manager.disable()

    def go_back(self, event):
        import Main
        self.window.show_view(Main.Menu())

    def on_draw(self):
        self.clear()
        self.manager.draw()