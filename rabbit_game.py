import pygame
import random
import math

# Initialize
pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Animal Hero: Rabbit vs Dragon")

# Load assets
background_image = pygame.transform.scale(pygame.image.load("background.jpg").convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
dragon_image = pygame.transform.scale(pygame.image.load("dragon.png").convert_alpha(), (50, 50))
shoot_sound = pygame.mixer.Sound("shoot.wav")
shoot_sound.set_volume(0.5)

# Colors and constants
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
FPS = 60
GRAVITY = 1

clock = pygame.time.Clock()

# Groups
all_sprites = pygame.sprite.Group()
projectiles = pygame.sprite.Group()
enemies = pygame.sprite.Group()
fireballs = pygame.sprite.Group()

# Game state
level = 1
level_timer = 0

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("human_with_gun.png").convert()
        self.image.set_colorkey((255, 255, 255))
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - 70
        self.speed_x = 0
        self.speed_y = 0
        self.is_jumping = False
        self.health = 100
        self.lives = 3
        self.score = 0

    def update(self):
        self.rect.x += self.speed_x
        self.speed_y += GRAVITY
        self.rect.y += self.speed_y
        if self.rect.y > SCREEN_HEIGHT - 70:
            self.rect.y = SCREEN_HEIGHT - 70
            self.is_jumping = False
            self.speed_y = 0
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))

    def jump(self):
        if not self.is_jumping:
            self.speed_y = -15
            self.is_jumping = True

    def move_left(self): self.speed_x = -5
    def move_right(self): self.speed_x = 5
    def stop(self): self.speed_x = 0

    def shoot(self):
        bullet = Projectile(self.rect.centerx, self.rect.centery)
        all_sprites.add(bullet)
        projectiles.add(bullet)
        shoot_sound.play()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_x = 10

    def update(self):
        self.rect.x += self.speed_x
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 165, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_x = -6

    def update(self):
        self.rect.x += self.speed_x
        if self.rect.right < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = dragon_image
        self.rect = self.image.get_rect(x=x, y=y)
        self.health = 10
        self.speed_x = 2

    def update(self):
        self.rect.x -= self.speed_x
        if self.health <= 0 or self.rect.right < 0:
            self.kill()

class FlyingEnemy(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.transform.scale(dragon_image, (60, 40))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.base_y = SCREEN_HEIGHT - 80
        self.rect.y = self.base_y
        self.speed_x = random.randint(2, 4)
        self.amplitude = 10
        self.frequency = 0.12
        self.tick = 0
        self.health = 30
        self.fireball_timer = random.randint(60, 120)

    def update(self):
        self.rect.x -= self.speed_x
        self.rect.y = self.base_y + int(self.amplitude * math.sin(self.frequency * self.tick))
        self.tick += 1
        self.fireball_timer -= 1
        if self.fireball_timer <= 0:
            fireball = Fireball(self.rect.centerx, self.rect.centery)
            fireballs.add(fireball)
            all_sprites.add(fireball)
            self.fireball_timer = random.randint(90, 150)
        if self.health <= 0 or self.rect.right < 0:
            self.kill()

class BossEnemy(pygame.sprite.Sprite):
    def __init__(self, health=30):
        super().__init__()
        self.image = pygame.transform.scale(dragon_image, (120, 120))
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = SCREEN_HEIGHT - 150
        self.health = health
        self.speed_x = random.randint(1, 3)

    def update(self):
        self.rect.x -= self.speed_x
        if self.health <= 0 or self.rect.right < 0:
            self.kill()

def draw_health_bar():
    pygame.draw.rect(screen, RED, (10, 10, 200, 20))
    pygame.draw.rect(screen, GREEN, (10, 10, 200 * (player.health / 100), 20))

def draw_score():
    screen.blit(pygame.font.Font(None, 36).render(f"Score: {player.score}", True, WHITE), (SCREEN_WIDTH - 150, 10))

def draw_lives():
    screen.blit(pygame.font.Font(None, 36).render(f"Lives: {player.lives}", True, WHITE), (SCREEN_WIDTH - 150, 50))

def draw_level():
    screen.blit(pygame.font.Font(None, 36).render(f"Level: {level}", True, WHITE), (10, 40))

def show_restart_menu():
    font = pygame.font.Font(None, 48)
    while True:
        screen.fill(BLACK)
        text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 30))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                    return
                elif event.key == pygame.K_q:
                    pygame.quit(); exit()

def show_fail_screen():
    screen.fill(BLACK)
    text = pygame.font.Font(None, 64).render("You Failed! Time's up!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 50))
    pygame.display.flip()
    pygame.time.wait(3000)
    show_restart_menu()

def game_over():
    screen.fill(BLACK)
    text = pygame.font.Font(None, 64).render("GAME OVER", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 50))
    pygame.display.flip()
    pygame.time.wait(3000)
    show_restart_menu()

def show_main_menu():
    font_title = pygame.font.Font(None, 72)
    font_option = pygame.font.Font(None, 48)
    selected = 0
    options = ["Start Game", "Quit"]
    menu_running = True

    while menu_running:
        screen.fill(BLACK)
        title = font_title.render("Animal Hero: Rabbit vs Dragon", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        for i, option in enumerate(options):
            color = GREEN if i == selected else WHITE
            text = font_option.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 280 + i * 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN: selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "Start Game":
                        menu_running = False
                    elif options[selected] == "Quit":
                        pygame.quit(); exit()

def start_level(lvl):
    global level_timer
    enemies.empty()
    fireballs.empty()
    projectiles.empty()
    all_sprites.empty()
    all_sprites.add(player)
    if lvl == 1:
        for i in range(6):
            e = Enemy(SCREEN_WIDTH + i * 100, SCREEN_HEIGHT - 70)
            enemies.add(e)
            all_sprites.add(e)
    elif lvl == 2:
        boss = BossEnemy()
        enemies.add(boss)
        all_sprites.add(boss)
        for i in range(8):
            e = Enemy(SCREEN_WIDTH + i * 80, SCREEN_HEIGHT - 70)
            enemies.add(e)
            all_sprites.add(e)
    elif lvl == 3:
        level_timer = pygame.time.get_ticks() + 60000
        for i in range(10):
            e = Enemy(SCREEN_WIDTH + i * 80, SCREEN_HEIGHT - 70)
            enemies.add(e)
            all_sprites.add(e)
        pygame.time.set_timer(pygame.USEREVENT + 1, 5000)

player = Player()
all_sprites.add(player)

def main():
    global level
    show_main_menu()
    start_level(level)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: player.move_left()
                elif event.key == pygame.K_RIGHT: player.move_right()
                elif event.key == pygame.K_UP: player.jump()
                elif event.key == pygame.K_SPACE: player.shoot()
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]: player.stop()
            elif event.type == pygame.USEREVENT + 1 and level == 3:
                for i in range(7):
                    f = FlyingEnemy(SCREEN_WIDTH + i * 90)
                    enemies.add(f)
                    all_sprites.add(f)
                for i in range(7):
                    b = BossEnemy(health=30)
                    b.rect.x = SCREEN_WIDTH + i * 120
                    enemies.add(b)
                    all_sprites.add(b)
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)

        screen.blit(background_image, (0, 0))
        all_sprites.update()

        if level == 3 and pygame.time.get_ticks() > level_timer and len(enemies) > 0:
            show_fail_screen()

        for bullet in projectiles:
            for enemy in pygame.sprite.spritecollide(bullet, enemies, False):
                enemy.health -= 10
                bullet.kill()
                player.score += 10

        for fb in fireballs:
            if player.rect.colliderect(fb.rect):
                fb.kill()
                player.health -= 10
                if player.health <= 0:
                    player.lives -= 1
                    player.health = 100
                    if player.lives <= 0:
                        game_over()

        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                player.health -= 20
                enemy.kill()
                if player.health <= 0:
                    player.lives -= 1
                    player.health = 100
                    if player.lives <= 0:
                        game_over()

        if len(enemies) == 0:
            if level != 3 or pygame.time.get_ticks() <= level_timer:
                screen.fill(BLACK)
                screen.blit(pygame.font.Font(None, 64).render("Level Complete!", True, GREEN), (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 - 50))
                pygame.display.flip()
                pygame.time.wait(2000)
                level += 1
                if level > 3:
                    screen.fill(BLACK)
                    screen.blit(pygame.font.Font(None, 64).render("You Win! Congratulations!", True, GREEN), (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 50))
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    break
                else:
                    player.health = 100
                    start_level(level)

        draw_health_bar()
        draw_score()
        draw_lives()
        draw_level()
        all_sprites.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()