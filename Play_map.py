import random

import arcade
import time
from arcade.camera import Camera2D
from arcade.particles import FadeParticle, EmitBurst, Emitter

SCREEN_W = 1280
SCREEN_H = 720

# скорость игрока
MOVE_SPEED = 8
LADDER_SPEED = 5

# настройки прыжков
COYOTE_TIME = 0.15
JUMP_BUFFER = 0.12
MAX_JUMPS = 1
GRAVITY = 0.5
JUMP_SPEED = 15

# Зомби настройки
AGGRO_DISTANCE = 500
ZOMBIE_SPEED = 2
PATROL_DISTANCE = 200


class MyGame(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_music = arcade.load_sound('assets/sound/game_music.mp3')
        arcade.play_sound(self.background_music, volume=0.1, loop=True)

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

        self.health = 3
        self.score = 0
        self.safe_time = 0

        self.coins_collected = 0
        self.total_coins = 0
        self.coin_message_timer = 0.0
        self.paused = False

    def setup(self):
        map_name = 'assets/tiles/one_level.tmx'
        layer_options = {
            'platform': {'use_spatial_hash': True},
            'walls': {'use_spatial_hash': True},
            'lava': {'use_spatial_hash': False},
        }
        self.tile_map = arcade.load_tilemap(map_name, scaling=1.0, layer_options=layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)


        self.hearts = arcade.load_texture('assets/images/heart.jpg')

        self.player = arcade.Sprite(
            ':resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png',
            scale=0.4
        )

        self.spawn = self.tile_map.sprite_lists['spawn'][0]
        self.respawn()
        self.scene.add_sprite('Player', self.player)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite=self.player,
            gravity_constant=GRAVITY,
            walls=self.scene['walls'],
            platforms=self.scene['platform'],
            ladders=self.scene['ladders']
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
        self.score = 0
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




    def on_draw(self):
        self.clear()
        self.world_camera.use()
        self.scene.draw()

        # Сообщение о монетах над головой
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
            arcade.draw_text('ПАУЗА\nESC - Играть | R - Рестарт', SCREEN_W / 2, SCREEN_H / 2,
                             arcade.color.WHITE, 30, anchor_x='center', multiline=True, width=500)


    def on_update(self, delta_time):
        if self.paused:
            return

        coin_hit_list = arcade.check_for_collision_with_list(self.player, self.scene['Coin'])
        for coin in coin_hit_list:
            coin.remove_from_sprite_lists()
            self.music = arcade.load_sound('assets/sound/coin.mp3')
            arcade.play_sound(self.music, volume=0.5, loop=False)
            self.coins_collected += 1

        exit_hit_list = arcade.check_for_collision_with_list(self.player, self.scene['exit'])
        if exit_hit_list:
            if self.coins_collected >= self.total_coins:
                print('Уровень пройден!')
            else:
                self.coin_message_timer = 5.0


        if self.coin_message_timer > 0:
            self.coin_message_timer -= delta_time

        if self.zoom_in_pressed:
            self.view_zoom += 0.01
        elif self.zoom_out_pressed:
            self.view_zoom -= 0.01

        self.view_zoom = arcade.math.clamp(self.view_zoom, 0.5, 2.0)
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
        self.scene.update_animation(delta_time)

        for z in self.scene['zombie']:
            dx = self.player.center_x - z.center_x
            dy = self.player.center_y - z.center_y
            ZOMBIE_SPEED = z.properties['speed']

            if abs(dx) < AGGRO_DISTANCE and abs(dy) < 50:
                if dx > 0:
                    z.change_x = ZOMBIE_SPEED * 2
                else:
                    z.change_x = -ZOMBIE_SPEED * 2


            # патруль зомби
            else:
                if z.change_x == 0:
                    z.change_x = ZOMBIE_SPEED

                if z.center_x >= z.properties['right_side'] and z.change_x > 0:
                    z.change_x = -ZOMBIE_SPEED
                elif z.center_x <= z.properties['left_side'] and z.change_x < 0:
                    z.change_x = ZOMBIE_SPEED

            # отзеркаливание зомби
            if z.change_x > 0:
                z.scale_x = abs(z.scale_x)
            elif z.change_x < 0:
                z.scale_x = -abs(z.scale_x)

            z.center_x += z.change_x


        if arcade.check_for_collision_with_list(self.player, self.scene['lava']):
            self.health -= 3

            if self.health <= 0:
                death = arcade.load_sound('assets/sound/death.mp3')
                arcade.play_sound(death, volume=0.5)
                self.setup()

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
                self.player.change_y = 10
                self.score += 100

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
                self.player.change_x = direction * 10
                self.player.change_y = 8

                if self.health <= 0:
                    death = arcade.load_sound('assets/sound/death.mp3')
                    arcade.play_sound(death, volume=0.5, loop=False)

                    self.setup()

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
        if key == arcade.key.ESCAPE:
            self.paused = not self.paused

        # рестарт
        if key == arcade.key.R:
            self.setup()
            self.paused = False

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
