import random
import arcade
import time
import csv
from arcade.camera import Camera2D
from arcade.particles import FadeParticle, EmitBurst, Emitter

SCREEN_W = 1280
SCREEN_H = 720

# скорость игрока
MOVE_SPEED = 2
LADDER_SPEED = 2

# настройки прыжков
COYOTE_TIME = 0.15
JUMP_BUFFER = 0.12
MAX_JUMPS = 0
GRAVITY = 0.8
JUMP_SPEED = 9

# Зомби настройки
AGGRO_DISTANCE = 500
PATROL_DISTANCE = 200


class MyGame(arcade.View):
    def __init__(self):
        super().__init__()
        self.player_name = 'Player'
        self.background_music = arcade.load_sound('assets/sound/game_music.mp3')
        self.music = arcade.play_sound(self.background_music, volume=0.1, loop=True)

        self.scene = None
        self.player = None
        self.physics_engine = None

        # Камеры
        self.world_camera = Camera2D()
        self.gui_camera = Camera2D()

        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.ctrl_pressed = False

        # зум камеры
        self.zoom_in_pressed = False
        self.zoom_out_pressed = False
        self.view_zoom = 1.5

        self.time_since_ground = 999.0
        self.jumps_left = MAX_JUMPS

        self.health = 0
        self.safe_time = 0

        self.coins_collected = 0
        self.total_coins = 0
        self.coin_message_timer = 0.0
        self.paused = False
        self.zombie_killed = 0
        self.died_by_zombie = 0
        self.died_by_lava = 0

        #       АНИМАЦИИ
        # бег
        self.run_textures_right = [arcade.load_texture(f"assets/images/anim/run/{i}.png") for i in range(1, 7)]
        self.run_textures_left = [tex.flip_left_right() for tex in self.run_textures_right]

        # покой
        self.idle_textures_right = [arcade.load_texture(f"assets/images/anim/idle/{i}.png") for i in range(1, 3)]
        self.idle_textures_left = [tex.flip_left_right() for tex in self.idle_textures_right]

        # прыжоК
        self.jump_textures_right = [arcade.load_texture(f"assets/images/anim/jump/{i}.png") for i in range(1, 3)]
        self.jump_textures_left = [tex.flip_left_right() for tex in self.jump_textures_right]

        # лазание
        self.climb_textures = [arcade.load_texture(f"assets/images/anim/climb/{i}.png") for i in range(1, 4)]
        self.cur_frame = 0
        self.animation_timer = 0
        self.facing_right = True

    def setup(self, map_name='assets/tiles/1.tmx'):
        layer_options = {
            'walls': {'use_spatial_hash': True},
            'lava': {'use_spatial_hash': False},
        }
        self.tile_map = arcade.load_tilemap(map_name, scaling=1.0, layer_options=layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.current_name_level = map_name

        self.hearts = arcade.load_texture('assets/images/heart.jpg')

        self.player = arcade.Sprite(scale=0.4)
        self.player.texture = self.idle_textures_right[0]

        self.spawn = self.tile_map.sprite_lists['spawn'][0]
        self.respawn()
        self.scene.add_sprite('Player', self.player)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite=self.player,
            gravity_constant=GRAVITY,
            walls=self.scene['walls'],
            ladders=self.scene['ladders'],
            platforms=self.scene['platforms'],
        )
        self.blood_textures = [
            arcade.load_texture('assets/images/died_animation/1.png'),
            arcade.load_texture('assets/images/died_animation/2.png'),
            arcade.load_texture('assets/images/died_animation/3.png'),
            arcade.load_texture('assets/images/died_animation/4.png'),
            arcade.load_texture('assets/images/died_animation/5.png'),

        ]

        self.emitters = []

        self.coins_collected = 0
        self.total_coins = 3
        self.health = 3
        self.coin_message_timer = 0.0

        self.dropped_coin = self.scene['Coin'][0]
        self.pending_coins = []

    def respawn(self):
        self.player.center_x = self.spawn.center_x
        self.player.bottom = self.spawn.bottom
        self.player.change_x = 0
        self.player.change_y = 0
        self.time_since_ground = 999.0
        self.jumps_left = MAX_JUMPS

    def smoke_mutator(self, p):
        p.scale_x *= 1.02
        p.scale_y *= 1.02
        p.alpha = max(0, p.alpha - 2)

    def show_victory(self):

        self.victory_manager = arcade.gui.UIManager()
        self.victory_manager.enable()


        v_box = arcade.gui.UIBoxLayout(space_between=20)


        title = arcade.gui.UILabel(text="ПОБЕДА!", font_size=30, text_color=arcade.color.GOLD)
        v_box.add(title)

        #
        stats_text = f"Собрано монет: {self.coins_collected}\nЗомби убито: {self.zombie_killed}"
        content = arcade.gui.UILabel(text=stats_text, font_size=16, multiline=True, text_color=arcade.color.WHITE)
        v_box.add(content)


        btn_menu = arcade.gui.UIFlatButton(text="В МЕНЮ", width=200)
        btn_menu.on_click = self.go_to_menu_action
        v_box.add(btn_menu)


        anchor = arcade.gui.UIAnchorLayout()


        bg_tex = arcade.make_soft_square_texture(100, arcade.color.BLACK_OLIVE)

        anchor.add(
            child=v_box.with_background(texture=bg_tex),
            anchor_x="center_x",
            anchor_y="center_y"
        )

        self.victory_manager.add(anchor)
        self.paused = True

    def go_to_menu_action(self, event):
        if hasattr(self, 'victory_manager'):
            self.victory_manager.disable()

        import Main
        menu_view = Main.Menu()
        self.window.show_view(menu_view)

    def on_draw(self):
        self.clear()
        self.world_camera.use()
        self.scene.draw()


        if self.coin_message_timer > 0:
            remaining = self.total_coins - self.coins_collected
            arcade.draw_text(
                f'Нужно найти еще {remaining} монет!',
                self.player.center_x,
                self.player.top + 20,
                arcade.color.RED,
                font_size=14,
                anchor_x='center',
                bold=True
            )
        for e in self.emitters:
            e.draw()

        self.gui_camera.use()

        for i in range(self.health):
            x_pos = 40 + (i * 35)
            arcade.draw_texture_rect(
                self.hearts,
                arcade.XYWH(x_pos, SCREEN_H - 35, 30, 30)
            )

        arcade.draw_text(f'Zoom: {self.view_zoom:.2f}x', 20, SCREEN_H - 80, arcade.color.WHITE, 18)
        arcade.draw_text(f'Монеты: {self.coins_collected}/{self.total_coins}',
                         20, SCREEN_H - 110, arcade.color.WHITE, 18)

        if self.paused:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_W, 0, SCREEN_H, (0, 0, 0, 150))
            arcade.draw_text('ПАУЗА\nESC - Играть | R - Рестарт | M - Меню', SCREEN_W / 2, SCREEN_H / 2,
                             arcade.color.WHITE, 30, anchor_x='center', multiline=True, width=650)
        if hasattr(self, 'victory_manager'):
            self.victory_manager.draw()


    def on_update(self, delta_time):
        if self.paused:
            return
        was_on_ground = self.physics_engine.can_jump(y_distance=6)

        coin_hit_list = arcade.check_for_collision_with_list(self.player, self.scene['Coin'])
        for coin in coin_hit_list:
            coin.remove_from_sprite_lists()
            self.music = arcade.load_sound('assets/sound/coin.mp3')
            arcade.play_sound(self.music, volume=0.5, loop=False)
            self.coins_collected += 1
        if arcade.check_for_collision_with_list(self.player, self.scene['saw']):
            self.health -= 3

        exit_hit_list = arcade.check_for_collision_with_list(self.player, self.scene['exit'])
        if exit_hit_list:
            if self.coins_collected >= self.total_coins:
                with open('res.csv', 'a', encoding='utf8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        self.player_name,
                        self.coins_collected,
                        self.died_by_zombie,
                        self.zombie_killed,
                        self.died_by_lava
                    ])

                if self.current_name_level == 'assets/tiles/1.tmx':
                    self.setup('assets/tiles/2.tmx')
                elif self.current_name_level == 'assets/tiles/2.tmx':

                    self.show_victory()
            else:

                self.coin_message_timer = 5.0

        if self.coin_message_timer > 0:
            self.coin_message_timer -= delta_time

        if self.zoom_in_pressed:
            self.view_zoom += 0.01
        elif self.zoom_out_pressed:
            self.view_zoom -= 0.01

        self.view_zoom = arcade.math.clamp(self.view_zoom, 3, 5)
        self.world_camera.zoom = self.view_zoom

        if self.safe_time > 0:
            self.safe_time -= delta_time
            self.player.alpha = 150 if int(time.time() * 10) % 2 == 0 else 255
        else:
            self.player.alpha = 255

        current_speed = MOVE_SPEED * 1.5 if self.ctrl_pressed else MOVE_SPEED

        if self.safe_time < 0.8:
            self.player.change_x = 0
            if self.left_pressed and not self.right_pressed:
                self.player.change_x = -current_speed
            elif self.right_pressed and not self.left_pressed:
                self.player.change_x = current_speed

        if self.physics_engine.is_on_ladder():
            if self.up_pressed:
                self.player.change_y = LADDER_SPEED
            elif self.down_pressed:
                self.player.change_y = -LADDER_SPEED
            else:
                self.player.change_y = 0

        # прыжки
        grounded = self.physics_engine.can_jump(y_distance=6)
        if grounded:
            self.time_since_ground = 0
            self.jumps_left = MAX_JUMPS
        else:
            self.time_since_ground += delta_time

        want_jump = self.up_pressed
        if want_jump:
            can_coyote = self.time_since_ground <= COYOTE_TIME
            if (grounded or can_coyote) or (self.jumps_left > 0):
                if not (grounded or can_coyote):
                    self.jumps_left -= 1
                else:
                    self.jumps_left = MAX_JUMPS - 1

                self.physics_engine.jump(JUMP_SPEED)
                self.time_since_ground = 999.0

        self.physics_engine.update()
        is_on_ground = self.physics_engine.can_jump(y_distance=6)

        if is_on_ground and not was_on_ground:
            land_e = Emitter(
                center_xy=(self.player.center_x, self.player.bottom),
                emit_controller=EmitBurst(5),
                particle_factory=lambda e: FadeParticle(
                    filename_or_texture=arcade.make_circle_texture(4, arcade.color.LIGHT_GRAY),
                    change_xy=(random.uniform(-2, 2), random.uniform(0, 2)),
                    lifetime=0.3,
                    mutation_callback=self.smoke_mutator
                )
            )
            self.emitters.append(land_e)

        if is_on_ground and abs(self.player.change_x) > 0.1:
            if random.random() < 0.15:
                run_e = Emitter(
                    center_xy=(self.player.center_x, self.player.bottom),
                    emit_controller=EmitBurst(1),
                    particle_factory=lambda e: FadeParticle(
                        filename_or_texture=arcade.make_circle_texture(random.randint(2, 4), arcade.color.GRAY),
                        change_xy=(random.uniform(-1, 1), random.uniform(0, 1)),
                        lifetime=0.4,
                        mutation_callback=self.smoke_mutator
                    )
                )
                self.emitters.append(run_e)

        self.animation_timer += delta_time
        if self.animation_timer > 0.1:
            self.animation_timer = 0
            self.cur_frame += 1

        if self.player.change_x > 0:
            self.facing_right = True
        elif self.player.change_x < 0:
            self.facing_right = False

            # ВЫБОР ТЕКСТУРЫ
        on_ladder = self.physics_engine.is_on_ladder()


        if on_ladder:
            textures = self.climb_textures

            if abs(self.player.change_y) < 0.1:
                self.cur_frame = 0

        elif self.player.change_y != 0:
            textures = self.jump_textures_right if self.facing_right else self.jump_textures_left

            # Бег
        elif self.player.change_x != 0:
            textures = self.run_textures_right if self.facing_right else self.run_textures_left

            # Покой
        else:
            textures = self.idle_textures_right if self.facing_right else self.idle_textures_left

        if self.cur_frame >= len(textures):
            self.cur_frame = 0

        self.player.texture = textures[self.cur_frame]
        self.scene.update_animation(delta_time)

        for z in self.scene['zombie']:
            dx = self.player.center_x - z.center_x
            dy = self.player.center_y - z.center_y
            zombie_speed = z.properties['speed']

            if abs(dx) < AGGRO_DISTANCE and abs(dy) < 10:
                if dx > 0:
                    z.change_x = zombie_speed * 1.5
                else:
                    z.change_x = -zombie_speed * 1.5


            # патруль зомби
            else:
                if z.change_x == 0:
                    z.change_x = zombie_speed

                if z.center_x >= z.properties['right_side'] and z.change_x > 0:
                    z.change_x = -zombie_speed
                elif z.center_x <= z.properties['left_side'] and z.change_x < 0:
                    z.change_x = zombie_speed

            # отзеркаливание зомби
            if z.change_x > 0:
                z.scale_x = abs(z.scale_x)
            elif z.change_x < 0:
                z.scale_x = -abs(z.scale_x)

            z.center_x += z.change_x

        map_height = self.tile_map.height * self.tile_map.tile_height
        for s in self.scene['saw']:
            arcade_vverh = map_height - s.properties['top']
            arcade_niz = map_height - s.properties['bottom']
            speed = s.properties['speed']

            if s.change_y == 0:
                s.change_y = -speed

            if s.center_y >= arcade_vverh and s.change_y > 0:
                s.change_y = -speed
            elif s.center_y <= arcade_niz and s.change_y < 0:
                s.change_y = speed

        self.scene['saw'].update()

        if arcade.check_for_collision_with_list(self.player, self.scene['lava']):
            self.health -= 3
            self.died_by_lava += 1

        if self.health <= 0:
            death = arcade.load_sound('assets/sound/death.mp3')
            arcade.play_sound(death, volume=0.5)
            self.setup(self.current_name_level)

        # убийство зомби/ получение урона
        zombie_hits = arcade.check_for_collision_with_list(self.player, self.scene['zombie'])
        for z in zombie_hits:
            if self.player.bottom > z.center_y and self.player.change_y < 0:

                e = Emitter(
                    center_xy=(z.center_x, z.center_y),
                    emit_controller=EmitBurst(15),
                    particle_factory=lambda e: FadeParticle(
                        filename_or_texture=random.choice(self.blood_textures),
                        change_xy=arcade.math.rand_in_circle((0.0, 0.0), 3.0),
                        lifetime=random.uniform(0.3, 0.6),
                        mutation_callback=self.smoke_mutator
                    )
                )
                self.emitters.append(e)

                z.remove_from_sprite_lists()
                self.player.change_y = 5
                self.zombie_killed += 1

                if z.properties.get('has_coin'):
                    delay = 0.1
                    self.pending_coins.append({
                        'x': z.center_x,
                        'y': z.center_y,
                        'timer': delay
                    })
            # неуязвимость при получении урона
            elif self.safe_time <= 0:
                self.health -= 1
                self.safe_time = 1.0
                direction = -1 if self.player.center_x < z.center_x else 1
                self.player.change_x = direction * 3
                self.player.change_y = 6

                if self.health <= 0:
                    death = arcade.load_sound('assets/sound/death.mp3')
                    arcade.play_sound(death, volume=0.5, loop=False)
                    self.died_by_zombie += 1

                    self.setup(self.current_name_level)

        # задержка выпадения монеты с зомби
        if self.pending_coins:
            for coin in self.pending_coins[:]:
                coin['timer'] -= delta_time
                if coin['timer'] <= 0:
                    new_coin = arcade.TextureAnimationSprite()
                    new_coin.animation = self.dropped_coin.animation
                    new_coin.scale = self.dropped_coin.scale
                    new_coin.center_x = coin['x'] + 20
                    new_coin.center_y = coin['y']
                    self.scene['Coin'].append(new_coin)
                    self.pending_coins.remove(coin)

        for e in self.emitters[:]:
            e.update(delta_time)
            if e.can_reap():
                self.emitters.remove(e)

        self.world_camera.position = (self.player.center_x, self.player.center_y)

    def on_key_press(self, key, modifiers):
        # пауза
        if key == arcade.key.ESCAPE:
            self.paused = not self.paused

        # рестарт
        if key == arcade.key.R:
            self.setup(self.current_name_level)
            self.paused = False
        if self.paused and key == arcade.key.M:
            arcade.stop_sound(self.music)
            from Main import Menu

            menu = Menu()
            self.window.show_view(menu)

        if not self.paused:
            if key == arcade.key.SPACE:
                self.up_pressed = True
            elif key == arcade.key.S:
                self.down_pressed = True
            elif key == arcade.key.A:
                self.left_pressed = True
            elif key == arcade.key.D:
                self.right_pressed = True
            elif key == arcade.key.LCTRL:
                self.ctrl_pressed = True
            elif key == arcade.key.EQUAL:
                self.zoom_in_pressed = True
            elif key == arcade.key.MINUS:
                self.zoom_out_pressed = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.up_pressed = False
            if self.player.change_y > 0 and not self.physics_engine.is_on_ladder():
                self.player.change_y *= 0.5
        elif key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.LCTRL:
            self.ctrl_pressed = False
        elif key == arcade.key.EQUAL:
            self.zoom_in_pressed = False
        elif key == arcade.key.MINUS:
            self.zoom_out_pressed = False
