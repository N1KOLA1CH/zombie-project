# Укажем правильный старт (из твоих логов это 539)
        start_gid = 539

        self.lch_textures = []

        for i in range(22):
            gid = start_gid + i
            # ТУТ ИЗМЕНЕНИЕ: используем встроенный метод получения готовой текстуры тайла
            # Это заставит Arcade взять только нужный квадрат 96x96, а не всю простыню
            tile = self.tile_map._get_tile_by_gid(gid)
            if tile:
                # Берем уже готовую текстуру из данных тайла
                self.lch_textures.append(tile.texture)

        print("Loaded lch textures:", len(self.lch_textures))

        # Присваиваем текстуры всем объектам lch
        for ray in self.scene["lch"]:
            # Используем .copy() если хочешь, но можно и без него
            ray.textures = self.lch_textures
            ray.cur_frame_idx = 0
            ray.anim_timer = 0.0
            if self.lch_textures:
                ray.texture = self.lch_textures[0]