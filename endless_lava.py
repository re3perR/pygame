import os
import random
import sys
import math
import pygame

FPS = 60
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

GRAVITY = 0.4
PLAYER_SPEED_X = 4
PLAYER_JUMP_SPEED = -10
LAVA_RISE_SPEED = 2

PLATFORM_WIDTH = 120
PLATFORM_HEIGHT = 30
PLATFORM_GAP = 110
NUM_PLATFORMS = 15

SPARK_GENERATE_INTERVAL = 200
COIN_SPAWN_CHANCE = 0.3
LAVA_HEIGHT = 50

FONT_NAME = "Arial"
FONT_SIZE = 26

START_FON = "fon.png"
HELP_FON = "help_fon.jpg"
PAUSE_FON = "pause_fon.jpg"
SHOP_FON = "shop_fon.jpg"
MINIMAP_FRAME = "minimap_frame.png"

PLAYER_STAND_IMG = "hero_stand.png"
PLAYER_JUMP_IMG = "hero_jump.png"
PLATFORM_IMG = "platform.png"
PLATFORM_TRAP_IMG = "platform_trap.png"
COIN_IMG = "coin.png"
LAVA_SHEET_IMG = "lava_sheet.png"
SPARK_IMG = "spark.jpg"

MUSIC_BACKGROUND = "bg_music.mp3"
SOUND_JUMP = "jump.wav"
SOUND_COIN = "coin.mp3"
SOUND_DEATH = "death.wav"
buy_sound = "buy_sound.wav"

POWERUP_TRANSLATIONS = {
    "double_jump": "двойной прыжок",
    "triple_jump": "тройной прыжок",
    "quadruple_jump": "четверной прыжок"
}

GAME_TITLE = "Endless Lava Escape"


def load_image(filename, colorkey=None):
    fullname = os.path.join("data", filename)
    if not os.path.isfile(fullname):
        print(f"Файл '{fullname}' не найден в папке data")
        sys.exit(1)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_sound(filename):
    fullname = os.path.join("data", filename)
    if not os.path.isfile(fullname):
        print(f"Звуковой файл '{fullname}' не найден. Звук отключён.")
        return None
    return pygame.mixer.Sound(fullname)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x=0, y=0, fps=10, *groups):
        super().__init__(*groups)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect().move(x, y)
        self.counter_time = 0
        self.frame_interval = 1000 // fps

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(
                    pygame.Rect(frame_location, self.rect.size)))

    def update(self, dt, *args):
        self.counter_time += dt
        if self.counter_time >= self.frame_interval:
            self.counter_time = 0
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.dx = 0
        self.dy = 0

    def update(self, target):
        center_y = SCREEN_HEIGHT // 2
        self.dy = -(target.rect.y - center_y)
        self.dx = 0


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, *groups):
        super().__init__(*groups)
        self.img_normal = pygame.transform.scale(
            load_image(PLATFORM_IMG, colorkey=-1), (w, h))
        self.img_trap = pygame.transform.scale(
            load_image(PLATFORM_TRAP_IMG, colorkey=-1), (w, h))
        self.image = self.img_normal
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.is_trap = False

    def become_trap(self):
        self.is_trap = True
        self.image = self.img_trap


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            load_image(COIN_IMG, colorkey=-1), (24, 24))
        self.rect = self.image.get_rect(center=(x, y))


class Lava(AnimatedSprite):
    def __init__(self, *groups):
        sheet = load_image(LAVA_SHEET_IMG, colorkey=-1)
        super().__init__(sheet, 8, 1, 0, 0, 8, *groups)
        self.frames = [pygame.transform.scale(f, (SCREEN_WIDTH, LAVA_HEIGHT))
                       for f in self.frames]
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.bottom = SCREEN_HEIGHT
        self.lava_level = self.rect.top

    def rise(self, dy):
        self.rect.y -= dy
        self.lava_level = self.rect.top

    def check_collision(self, player):
        lava_rect = pygame.Rect(0, self.lava_level, SCREEN_WIDTH,
                                SCREEN_HEIGHT - self.lava_level)
        return lava_rect.colliderect(player.rect)


class LavaSpark(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            load_image(SPARK_IMG, colorkey=-1), (10, 10))
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-4, -1)
        self.alpha = 255

    def update(self, dt, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.alpha -= 5
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)


class PowerUp:
    def __init__(self, name):
        self.name = name
        self.active = False

    def activate(self, player):
        if self.name == "double_jump":
            player.max_extra_jumps = 1
        elif self.name == "triple_jump":
            player.max_extra_jumps = 2
        elif self.name == "quadruple_jump":
            player.max_extra_jumps = 3
        self.active = True
        self.display_name = POWERUP_TRANSLATIONS.get(self.name, self.name)

    def update(self, player):
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        stand_img = load_image(PLAYER_STAND_IMG, colorkey=-1)
        jump_img = load_image(PLAYER_JUMP_IMG, colorkey=-1)
        scale = 0.5
        self.orig_image_stand = pygame.transform.scale(
            stand_img, (int(stand_img.get_width() * scale),
                        int(stand_img.get_height() * scale)))
        self.orig_image_jump = pygame.transform.scale(
            jump_img, (int(jump_img.get_width() * scale),
                       int(jump_img.get_height() * scale)))
        self.image = self.orig_image_stand
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.player_start_y = y
        self.max_height_reached = y
        self.score = 0.0
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.coins = 0
        self.double_jump_unlocked = False
        self.double_jump_used = False
        self.jump_sound = load_sound(SOUND_JUMP)
        self.coin_sound = load_sound(SOUND_COIN)
        self.death_sound = load_sound(SOUND_DEATH)
        self.is_jumping = False
        self.jump_timer = 0
        self.facing_right = True
        self.current_platform = None
        self.coyote_timer = 0
        self.coyote_time_limit = 100
        self.max_extra_jumps = 0
        self.extra_jumps_used = 0
        self.total_jumps = 0

    def update(self, dt, platforms, trap_platforms, game_ref):
        if self.jump_timer > 0:
            self.jump_timer -= dt
            if self.jump_timer <= 0:
                self.jump_timer = 0
                self.is_jumping = False
        self.vy += GRAVITY
        self.rect.x += self.vx
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0
        collidex = pygame.sprite.spritecollide(self, platforms, False)
        if collidex:
            if self.vx > 0:
                self.rect.right = min(p.rect.left for p in collidex)
            elif self.vx < 0:
                self.rect.left = max(p.rect.right for p in collidex)
        self.rect.y += self.vy
        self.on_ground = False
        if self.vy >= 0:
            for p in platforms:
                if self.rect.right > p.rect.left and self.rect.left < p.rect.right:
                    gap = p.rect.top - self.rect.bottom
                    if 0 <= gap < 5:
                        self.rect.bottom = p.rect.top
                        self.vy = 0
                        self.on_ground = True
                        if p != self.current_platform:
                            game_ref.convert_platforms_below_to_traps(p.rect.y)
                            self.current_platform = p
                        break
        if self.on_ground:
            self.extra_jumps_used = 0
        if self.on_ground:
            self.coyote_timer = self.coyote_time_limit
        else:
            self.coyote_timer = max(0, self.coyote_timer - dt)
        if self.rect.y < self.max_height_reached:
            self.max_height_reached = self.rect.y
        self.score = (self.player_start_y - self.max_height_reached) / 5.0
        new_img = self.orig_image_jump if self.is_jumping else self.orig_image_stand
        if not self.facing_right:
            new_img = pygame.transform.flip(new_img, True, False)
        self.image = new_img
        if pygame.sprite.spritecollide(self, trap_platforms, False):
            self.kill_player()

    def jump(self):
        if self.on_ground:
            self.vy = PLAYER_JUMP_SPEED
            self.on_ground = False
            self.extra_jumps_used = 0
            if self.jump_sound:
                self.jump_sound.play()
            self.total_jumps += 1
            return True
        elif self.extra_jumps_used < self.max_extra_jumps:
            self.vy = PLAYER_JUMP_SPEED
            self.extra_jumps_used += 1
            if self.jump_sound:
                self.jump_sound.play()
            self.total_jumps += 1
            return True
        return False

    def move_left(self):
        self.vx = -PLAYER_SPEED_X
        self.facing_right = False

    def move_right(self):
        self.vx = PLAYER_SPEED_X
        self.facing_right = True

    def stop_x(self):
        self.vx = 0

    def pick_coin(self):
        self.coins += 1
        if self.coin_sound:
            self.coin_sound.play()

    def kill_player(self):
        if self.death_sound:
            self.death_sound.play()
        self.vx = 0
        self.vy = 0
        self.rect.y = 999999


class MiniMap:
    def __init__(self, x, y, w, h, game):
        self.rect = pygame.Rect(x, y, w, h)
        self.game = game
        try:
            self.frame_img = pygame.transform.scale(
                load_image(MINIMAP_FRAME), (w, h))
        except Exception:
            self.frame_img = None
        self.view_height = 1200
        self.view_width = self.game.map_width

    def update(self):
        player_y = self.game.player.rect.y
        min_y = 10
        max_y = SCREEN_HEIGHT - self.rect.height - 10
        desired_y = max_y - (player_y * 0.1)
        self.rect.y = max(min_y, min(desired_y, max_y))

    def draw(self, surface):
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        if self.frame_img:
            surface.blit(self.frame_img, (self.rect.x, self.rect.y))
        half_h = self.view_height // 2
        player_y = self.game.player.rect.centery
        view_top = player_y - half_h
        view_bottom = player_y + half_h
        world_w = float(self.view_width)
        world_h = float(view_bottom - view_top)
        if world_h <= 0:
            return

        def minimap_pos(x, y):
            nx = x / world_w
            ny = (y - view_top) / world_h
            return self.rect.x + nx * self.rect.width, \
                   self.rect.y + ny * self.rect.height

        for pf in self.game.platforms:
            if pf.rect.bottom < view_top or pf.rect.top > view_bottom:
                continue
            mini_x = self.rect.x + (pf.rect.x / world_w) * self.rect.width
            mini_y = self.rect.y + ((pf.rect.y - view_top) / world_h) * self.rect.height
            mini_w = pf.rect.width * (self.rect.width / world_w)
            mini_h = pf.rect.height * (self.rect.height / world_h)
            color = RED if pf.is_trap else GREEN
            pygame.draw.rect(surface, color, (mini_x, mini_y, mini_w, mini_h))

        for tp in self.game.trap_platforms:
            if tp.rect.bottom < view_top or tp.rect.top > view_bottom:
                continue
            mini_x = self.rect.x + (tp.rect.x / world_w) * self.rect.width
            mini_y = self.rect.y + ((tp.rect.y - view_top) / world_h) * self.rect.height
            mini_w = tp.rect.width * (self.rect.width / world_w)
            mini_h = tp.rect.height * (self.rect.height / world_h)
            pygame.draw.rect(surface, RED, (mini_x, mini_y, mini_w, mini_h))

        for coin in self.game.coins_group:
            if coin.rect.bottom < view_top or coin.rect.top > view_bottom:
                continue
            mx, my = minimap_pos(coin.rect.centerx, coin.rect.centery)
            pygame.draw.circle(surface, YELLOW, (int(mx), int(my)), 2)

        lava_top = self.game.lava.lava_level
        if lava_top < view_bottom:
            if lava_top < view_top:
                lava_top = view_top
            _, lava_my = minimap_pos(0, lava_top)
            lava_rect = pygame.Rect(self.rect.x, lava_my, self.rect.width,
                                    self.rect.bottom - lava_my)
            pygame.draw.rect(surface, (200, 50, 50), lava_rect)

        mx, my = minimap_pos(self.game.player.rect.centerx,
                             self.game.player.rect.centery)
        pygame.draw.circle(surface, BLUE, (int(mx), int(my)), 3)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "START"
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.music_bg = None
        if os.path.isfile(os.path.join("data", MUSIC_BACKGROUND)):
            pygame.mixer.music.load(os.path.join("data", MUSIC_BACKGROUND))
            pygame.mixer.music.set_volume(0.5)
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.trap_platforms = pygame.sprite.Group()
        self.coins_group = pygame.sprite.Group()
        self.lava_sparks = pygame.sprite.Group()
        self.map_width = SCREEN_WIDTH
        self.player = None
        self.lava = None
        self.previous_score = None
        self.best_score = 0
        self.reset_game(initial=True)
        pygame.time.set_timer(pygame.USEREVENT + 1, SPARK_GENERATE_INTERVAL)
        self.active_powerup = None
        self.minimap = MiniMap(10, 400, 150, 150, self)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.buy_sound = load_sound("buy_sound.wav")

    def update_world(self):
        removal_threshold = self.player.rect.y + (5 * PLATFORM_GAP)
        for group in (self.platforms, self.trap_platforms, self.coins_group):
            for obj in list(group):
                if obj.rect.y > removal_threshold:
                    group.remove(obj)
                    if obj in self.all_sprites:
                        self.all_sprites.remove(obj)
        if self.platforms:
            highest_platform = min(self.platforms, key=lambda p: p.rect.y)
            highest_y = highest_platform.rect.y
            prev_x = highest_platform.rect.x
        else:
            highest_y = self.player.rect.y - PLATFORM_GAP
            prev_x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
        target_y = self.player.rect.y - (6 * PLATFORM_GAP)
        while highest_y > target_y:
            new_y = highest_y - PLATFORM_GAP
            offset = random.randint(-250, 230)
            x_candidate = prev_x + offset
            if x_candidate < 0 or x_candidate > SCREEN_WIDTH - PLATFORM_WIDTH:
                offset = -offset
                x_candidate = prev_x + offset
            new_pf = Platform(x_candidate, new_y, PLATFORM_WIDTH, PLATFORM_HEIGHT,
                              self.all_sprites, self.platforms)
            if random.random() < COIN_SPAWN_CHANCE:
                Coin(new_pf.rect.centerx, new_pf.rect.top - 12,
                     self.all_sprites, self.coins_group)
            highest_y = new_y
            prev_x = x_candidate

    def recenter_world(self):
        if self.player.rect.y < 100:
            offset = 100 - self.player.rect.y
            for sprite in self.all_sprites:
                sprite.rect.y += offset
            self.player.max_height_reached -= offset

    def spawn_platforms_above(self):
        if self.platforms:
            highest_y = min(p.rect.y for p in self.platforms)
        else:
            highest_y = SCREEN_HEIGHT - 150
        target_y = highest_y - 600
        current_y = highest_y - PLATFORM_GAP
        if self.platforms:
            sorted_platforms = sorted(self.platforms, key=lambda p: p.rect.y)
            prev_platform = sorted_platforms[0]
        else:
            prev_platform = None
        while current_y >= target_y:
            if prev_platform:
                offset = random.randint(-250, 230)
                x_candidate = prev_platform.rect.x + offset
                if x_candidate < 0 or x_candidate > SCREEN_WIDTH - PLATFORM_WIDTH:
                    offset = -offset
                    x_candidate = prev_platform.rect.x + offset
                x = x_candidate
            else:
                x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
            new_pf = Platform(x, current_y, PLATFORM_WIDTH, PLATFORM_HEIGHT,
                              self.all_sprites, self.platforms)
            if random.random() < COIN_SPAWN_CHANCE:
                Coin(new_pf.rect.centerx, new_pf.rect.top - 12,
                     self.all_sprites, self.coins_group)
            prev_platform = new_pf
            current_y -= PLATFORM_GAP

    def reset_game(self, initial=False):
        self.all_sprites.empty()
        self.platforms.empty()
        self.trap_platforms.empty()
        self.coins_group.empty()
        self.lava_sparks.empty()
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 300,
                             self.all_sprites)
        self.lava = Lava(self.all_sprites)
        self.player.player_start_y = self.player.rect.y
        self.player.max_height_reached = self.player.rect.y
        self.player.score = 0.0
        self.player.total_jumps = 0
        bottom_platform = self.generate_platforms()
        if bottom_platform:
            self.player.rect.bottom = bottom_platform.rect.top
            self.player.rect.centerx = bottom_platform.rect.centerx
            self.player.on_ground = True
        if not initial:
            self.active_powerup = None
            self.state = "RUNNING"

    def generate_platforms(self):
        bottom_y = SCREEN_HEIGHT - 150
        gap = PLATFORM_GAP
        bottom_platform = None
        prev_x = None
        for i in range(NUM_PLATFORMS):
            y = bottom_y - i * gap
            if i == 0:
                x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
            else:
                offset = random.randint(-250, 230)
                x_candidate = prev_x + offset
                if x_candidate < 0 or x_candidate > SCREEN_WIDTH - PLATFORM_WIDTH:
                    offset = -offset
                    x_candidate = prev_x + offset
                x = x_candidate
            pf = Platform(x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT,
                          self.all_sprites, self.platforms)
            if random.random() < COIN_SPAWN_CHANCE:
                Coin(pf.rect.centerx, pf.rect.top - 12,
                     self.all_sprites, self.coins_group)
            if i == 0:
                bottom_platform = pf
            prev_x = x
        return bottom_platform

    def convert_platforms_below_to_traps(self, y_threshold):
        to_convert = [p for p in self.platforms if p.rect.y > y_threshold and
                      not p.is_trap]
        for p in to_convert:
            p.become_trap()
            self.trap_platforms.add(p)
            self.platforms.remove(p)

    def run(self):
        if self.music_bg:
            pygame.mixer.music.play(-1)
        while self.running:
            dt = self.clock.tick(FPS)
            if self.state == "START":
                self.show_start_screen()
            elif self.state == "HELP":
                self.show_help_screen()
            elif self.state == "HOW_TO_PLAY":
                self.show_how_to_play_screen()
            elif self.state == "SHOP":
                self.show_shop_screen()
            elif self.state == "RUNNING":
                self.game_loop(dt)
            elif self.state == "PAUSE":
                self.show_pause_screen()
            elif self.state == "GAMEOVER":
                self.show_game_over_screen()
        pygame.quit()

    def game_loop(self, dt):
        self.handle_events(dt)
        self.lava.rise(LAVA_RISE_SPEED)
        if self.lava.check_collision(self.player):
            self.player.kill_player()
        if self.player.rect.y >= 999999:
            self.state = "GAMEOVER"
            return
        if self.active_powerup:
            self.active_powerup.update(self.player)
        self.lava.update(dt)
        self.all_sprites.update(dt, self.platforms, self.trap_platforms, self)
        self.lava_sparks.update(dt)
        for _ in pygame.sprite.spritecollide(self.player, self.coins_group, True):
            self.player.pick_coin()
        if self.player.score >= 100:
            pass
        self.camera.update(self.player)
        self.recenter_world()
        self.update_world()
        self.minimap.update()
        self.draw_game()

    def handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "PAUSE"
                elif event.key in (pygame.K_UP, pygame.K_w):
                    if self.player.jump():
                        self.player.is_jumping = True
                        self.player.jump_timer = 300
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.player.move_left()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.player.move_right()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    self.player.stop_x()
            elif event.type == pygame.USEREVENT + 1:
                spark_x = random.randint(0, SCREEN_WIDTH)
                spark_y = self.lava.lava_level
                self.all_sprites.add(LavaSpark(spark_x, spark_y, self.lava_sparks))

    def draw_game(self):
        self.screen.fill(BLACK)
        for spr in self.all_sprites:
            self.screen.blit(spr.image, (spr.rect.x + self.camera.dx,
                                         spr.rect.y + self.camera.dy))
        for spark in self.lava_sparks:
            self.screen.blit(spark.image, (spark.rect.x + self.camera.dx,
                                           spark.rect.y + self.camera.dy))
        lava_top = self.lava.rect.top + self.camera.dy
        if lava_top < SCREEN_HEIGHT:
            lava_frame = self.lava.image
            frame_h = lava_frame.get_height() or 1
            y = lava_top
            while y < SCREEN_HEIGHT:
                self.screen.blit(lava_frame, (0, y))
                y += frame_h
        self.minimap.draw(self.screen)
        if self.player.score > self.best_score:
            self.best_score = int(self.player.score)
        self.draw_text(f"Счёт: {int(self.player.score)}", 20, 20, WHITE)
        self.draw_text(f"Монеты: {self.player.coins}", 20, 50, YELLOW)
        if self.active_powerup and self.active_powerup.active:
            self.draw_text(f"Усиление: {self.active_powerup.display_name}",
                           20, 80, CYAN)
        if self.previous_score is not None:
            self.draw_text(f"Крайний счёт: {self.previous_score}",
                           SCREEN_WIDTH - 205, 20, WHITE)
        self.draw_text(f"Лучший счёт: {self.best_score}",
                       SCREEN_WIDTH - 205, 50, WHITE)
        pygame.display.flip()

    def draw_text(self, text, x, y, color=WHITE):
        img = self.font.render(text, True, color)
        self.screen.blit(img, (x, y))

    def show_start_screen(self):
        bg = pygame.transform.scale(load_image(START_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        title_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 20, bold=True)
        command_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        waiting = True
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        while waiting and self.running and self.state == "START":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        pygame.mixer.music.stop()
                        self.state = "RUNNING"
                        waiting = False
                    elif event.key == pygame.K_h:
                        self.state = "HELP"
                        waiting = False
                    elif event.key == pygame.K_o:
                        self.state = "HOW_TO_PLAY"
                        waiting = False

            self.screen.blit(bg, (0, 0))
            title_img = title_font.render("ENDLESS LAVA ESCAPE", True, WHITE)
            self.screen.blit(title_img, title_img.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 330)))
            subtitle_img = command_font.render("УБЕГИ ОТ ЛАВЫ", True, WHITE)
            self.screen.blit(subtitle_img, subtitle_img.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 270)))
            command_img = command_font.render(
                "[H]elp    H[o]w to play   [ENTER] Start", True, WHITE)
            self.screen.blit(command_img, command_img.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))
            pygame.display.flip()

    def show_help_screen(self):
        bg = pygame.transform.scale(load_image(HELP_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        title_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 20, bold=True)
        text_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        instructions = ["←/→ или A/D – движение", "↑ или W – прыжок",
                        "ESC – Пауза/Выход", "Нажмите любую клавишу, чтобы вернуться..."]
        waiting = True
        while waiting and self.running and self.state == "HELP":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.state = "START"
                    waiting = False
            self.screen.blit(bg, (0, 0))
            title_img = title_font.render("Управление", True, WHITE)
            self.screen.blit(title_img, title_img.get_rect(
                center=(SCREEN_WIDTH // 2, 180)))
            start_y = 280
            for line in instructions:
                line_img = text_font.render(line, True, WHITE)
                self.screen.blit(line_img, line_img.get_rect(
                    center=(SCREEN_WIDTH // 2, start_y)))
                start_y += 40
            pygame.display.flip()

    def show_how_to_play_screen(self):
        bg = pygame.transform.scale(load_image(HELP_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        info_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        instructions = [
            "КАК ИГРАТЬ:",
            "",
            "Поднимайтесь всё выше и выше,",
            "пытаясь сбежать от надвигающейся лавы.",
            "Собирайте монеты для покупки бонусов,",
            "которые помогут увеличить число прыжков.",
            "",
            "ЦЕЛЬ ИГРЫ:",
            "",
            "Достигайте как можно большей высоты,",
            "избегая лавы и ловушек.",
            "",
            "Нажмите любую клавишу, чтобы вернуться..."
        ]
        waiting = True
        while waiting and self.running and self.state == "HOW_TO_PLAY":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.state = "START"
                    waiting = False
            self.screen.blit(bg, (0, 0))
            start_y = 60
            for line in instructions:
                line_img = info_font.render(line, True, WHITE)
                self.screen.blit(line_img, line_img.get_rect(
                    center=(SCREEN_WIDTH // 2, start_y)))
                start_y += 40
            pygame.display.flip()

    def show_shop_screen(self):
        bg = pygame.transform.scale(load_image(SHOP_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        shop_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 5, bold=True)
        waiting = True
        while waiting and self.running and self.state == "SHOP":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        if (self.active_powerup is None or self.active_powerup.name not in
                            ["double_jump", "triple_jump", "quadruple_jump"]) and \
                                self.player.coins >= 3:
                            self.player.coins -= 3
                            self.active_powerup = PowerUp("double_jump")
                            self.active_powerup.activate(self.player)
                            if self.buy_sound is not None:
                                self.buy_sound.play()
                    elif event.key == pygame.K_2:
                        if (self.active_powerup is None or self.active_powerup.name not in
                            ["triple_jump", "quadruple_jump"]) and self.player.coins >= 5:
                            self.player.coins -= 5
                            self.active_powerup = PowerUp("triple_jump")
                            self.active_powerup.activate(self.player)
                            if self.buy_sound is not None:
                                self.buy_sound.play()
                    elif event.key == pygame.K_3:
                        if (self.active_powerup is None or self.active_powerup.name !=
                            "quadruple_jump") and self.player.coins >= 7:
                            self.player.coins -= 7
                            self.active_powerup = PowerUp("quadruple_jump")
                            self.active_powerup.activate(self.player)
                            if self.buy_sound is not None:
                                self.buy_sound.play()
                    self.state = "PAUSE"
                    return
            self.screen.blit(bg, (0, 0))
            if self.active_powerup is not None and self.active_powerup.name in [
                "double_jump", "triple_jump", "quadruple_jump"]:
                line1 = "[1] ДВОЙНОЙ ПРЫЖОК - РАСПРОДАН"
            else:
                line1 = "Нажмите [1], чтобы купить ДВОЙНОЙ ПРЫЖОК за 3 монеты"
            if self.active_powerup is not None and self.active_powerup.name in [
                "triple_jump", "quadruple_jump"]:
                line2 = "[2] ТРОЙНОЙ ПРЫЖОК - РАСПРОДАН"
            else:
                line2 = "Нажмите [2], чтобы купить ТРОЙНОЙ ПРЫЖОК за 5 монет"
            if self.active_powerup is not None and self.active_powerup.name == "quadruple_jump":
                line3 = "[3] ЧЕТВЕРНОЙ ПРЫЖОК - РАСПРОДАН"
            else:
                line3 = "Нажмите [3], чтобы купить ЧЕТВЕРНОЙ ПРЫЖОК за 7 монет"
            line1_img = shop_font.render(line1, True, WHITE)
            line2_img = shop_font.render(line2, True, WHITE)
            line3_img = shop_font.render(line3, True, WHITE)
            self.screen.blit(line1_img, line1_img.get_rect(
                center=(SCREEN_WIDTH // 2, 200)))
            self.screen.blit(line2_img, line2_img.get_rect(
                center=(SCREEN_WIDTH // 2, 250)))
            self.screen.blit(line3_img, line3_img.get_rect(
                center=(SCREEN_WIDTH // 2, 300)))
            exit_img = shop_font.render(
                "Нажмите любую другую клавишу для выхода...", True, WHITE)
            self.screen.blit(exit_img, exit_img.get_rect(
                center=(SCREEN_WIDTH // 2, 400)))
            pygame.display.flip()

    def show_pause_screen(self):
        bg = pygame.transform.scale(load_image(PAUSE_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        pause_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        waiting = True
        while waiting and self.running and self.state == "PAUSE":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.state = "RUNNING"
                        return
                    if event.key == pygame.K_s:
                        self.state = "SHOP"
                        return
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        waiting = False
            self.screen.blit(bg, (0, 0))
            line1_img = pause_font.render("[ENTER] - ПРОДОЛЖИТЬ", True, WHITE)
            line2_img = pause_font.render("[S] - МАГАЗИН    [ESC] - ВЫХОД",
                                          True, WHITE)
            self.screen.blit(line1_img, line1_img.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 330)))
            self.screen.blit(line2_img, line2_img.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 270)))
            pygame.display.flip()

    def show_game_over_screen(self):
        self.previous_score = int(self.player.score)
        new_record = ""
        if self.player.score >= self.best_score:
            self.best_score = int(self.player.score)
            new_record = "Новый рекорд!"
        bg = pygame.transform.scale(load_image(START_FON),
                                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(bg, (0, 0))
        title_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 20, bold=True)
        info_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        center_x = SCREEN_WIDTH // 2
        game_over_img = title_font.render("Игра окончена!", True, RED)
        self.screen.blit(game_over_img, game_over_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 450)))
        score_img = info_font.render(f"Ваш счёт: {int(self.player.score)}",
                                     True, WHITE)
        self.screen.blit(score_img, score_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 350)))
        coins_img = info_font.render(f"Монеты: {self.player.coins}", True, YELLOW)
        self.screen.blit(coins_img, coins_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 300)))
        if new_record:
            new_record_img = info_font.render(new_record, True, CYAN)
            self.screen.blit(new_record_img, new_record_img.get_rect(
                center=(center_x, SCREEN_HEIGHT - 500)))
        jumps_img = info_font.render(
            f"Количество прыжков: {self.player.total_jumps}", True, WHITE)
        self.screen.blit(jumps_img, jumps_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 250)))
        bonus_text = "БОНУС: " + (
            self.active_powerup.display_name if self.active_powerup is not None and hasattr(self.active_powerup,
                                                                                            "display_name") else "НЕТ")
        bonus_img = info_font.render(bonus_text, True, CYAN)
        self.screen.blit(bonus_img, bonus_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 150)))
        command_img = info_font.render("[ENTER] To restart    [ESC] To exit",
                                       True, WHITE)
        self.screen.blit(command_img, command_img.get_rect(
            center=(center_x, SCREEN_HEIGHT - 50)))
        pygame.display.flip()
        waiting = True
        while waiting and self.running and self.state == "GAMEOVER":
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.reset_game(initial=False)
                        waiting = False
                        return
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        waiting = False


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
