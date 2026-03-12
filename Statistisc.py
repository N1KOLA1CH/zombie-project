import arcade
import arcade.gui
import csv
import os


class RecordsView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.background = arcade.load_texture('assets/images/zb.png')

        self.vert_box = arcade.gui.UIBoxLayout(space_between=10)

        header = arcade.gui.UILabel(text="ТАБЛИЦА РЕКОРДОВ", font_size=30, text_color=arcade.color.GOLD)
        self.vert_box.add(header.with_padding(bottom=20))

        self.load_records()

        button_back = arcade.gui.UIFlatButton(text="Назад", width=200)
        button_back.on_click = self.go_back
        self.vert_box.add(button_back.with_padding(top=20))
        self.manager.add(
            arcade.gui.UIAnchorLayout(child=self.vert_box)
        )

    def load_records(self):
        if not os.path.exists("statistics.csv"):
            label = arcade.gui.UILabel(text="Рекордов пока нет", text_color=arcade.color.WHITE)
            self.vert_box.add(label)
            return

        with open("statistics.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-5:]
            for row in rows:
                text = f"{row['Name']} | Монеты: {row['coins']} | Зомби: {row['kills_zombie']}"
                record_label = arcade.gui.UILabel(text=text, font_size=14, text_color=arcade.color.WHITE)
                self.vert_box.add(record_label)

    def go_back(self, event):
        from Main import Menu
        self.window.show_view(Menu())

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            texture=self.background,
            rect=arcade.XYWH(self.window.width / 2, self.window.height / 2, self.window.width, self.window.height)
        )
        self.manager.draw()