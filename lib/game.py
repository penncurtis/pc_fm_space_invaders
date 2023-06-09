import pygame, sys
import sqlite3
from random import choice
from player import Player
from alien import Alien
from bullet import Bullet


class Game:

    def __init__(self):
        self.player_name = " "
        player_sprite = Player((screen_width / 2, screen_height), screen_width, 5 )
        self.player = pygame.sprite.GroupSingle(player_sprite)

        self.first_menu = False
        self.start_game = False
        self.game_over = False
        self.column = 9
        self.wave = 1

        self.lives = 3
        self.live_surf = pygame.image.load("./lib/assets/lives.png")
        self.live_x_start_pos = screen_width - (self.live_surf.get_size()[0] * 2 + 20)
        self.score = 0
        self.font = pygame.font.Font("./lib/assets/space_invaders.ttf", 20)

        self.aliens = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1

    def alien_setup(self, rows, cols, x_distance = 60, y_distance = 48, x_offset = 70, y_offset = 20):
        for row_index, row in enumerate(range(rows)):
            for col_index, col in enumerate(range(cols)):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset
                if row_index == 0:
                    alien_sprite = Alien('best_alien', x, y)
                elif 1 <= row_index <=2:
                    alien_sprite = Alien('upgraded_alien', x, y)
                else:
                    alien_sprite = Alien('basic_alien', x, y)
                self.aliens.add(alien_sprite)

    def alien_position_checker(self):
        if not self.aliens:
            self.alien_setup(rows=6, cols=self.column)
            self.wave += 1
            if self.column <= 11:
                self.column += 1
        all_aliens = self.aliens.sprites()
        for alien in all_aliens:
            if alien.rect.right >= screen_width:
                self.alien_direction = -1
                self.alien_move_down(2)
            elif alien.rect.left <= 0:
                self.alien_direction = 1
                self.alien_move_down(2)

    def alien_move_down(self, distance):
        if self.aliens:
            for alien in self.aliens.sprites():
                alien.rect.y += distance

    def alien_shoot(self):
        if self.aliens.sprites() and self.column <= 11:
            random_alien = choice(self.aliens.sprites())
            bullet_sprite = Bullet(random_alien.rect.center, 6, screen_height)
            self.alien_bullets.add(bullet_sprite)
        elif self.aliens.sprites() and self.column == 12:
            random_alien = choice(self.aliens.sprites())
            bullet_sprite = Bullet(random_alien.rect.center, 10, screen_height)
            self.alien_bullets.add(bullet_sprite)

    def collision_checks(self):

        if self.player.sprite.bullets:
            for bullet in self.player.sprite.bullets:
                aliens_hit = pygame.sprite.spritecollide(bullet, self.aliens, True)
                if aliens_hit:
                    for alien in aliens_hit:
                        self.score += alien.value
                    bullet.kill()
        
        if self.alien_bullets:
            for bullet in self.alien_bullets:
                if pygame.sprite.spritecollide(bullet, self.player, False):
                    bullet.kill()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True

        if self.aliens:
            for alien in self.aliens:
                if pygame.sprite.spritecollide(alien, self.player, False):
                    self.game_over = True

    def display_lives(self):
        for live in range(self.lives - 1):
            x = self.live_x_start_pos + (live * (self.live_surf.get_size()[0] + 10))
            screen.blit(self.live_surf, (x, 8))

    def display_wave(self):
        wave_surf = self.font.render(f'Wave: {self.wave}', False, 'white')
        wave_rect = wave_surf.get_rect(topleft = (0, 25))
        screen.blit(wave_surf, wave_rect)

    def display_score(self):
        score_surf = self.font.render(f'Score: {self.score}', False, 'white')
        score_rect = score_surf.get_rect(topleft = (0, 0))
        screen.blit(score_surf, score_rect)

    def end_message(self):
        loss_surf = self.font.render("GAME OVER", False, "white")
        loss_rect = loss_surf.get_rect(center = (screen_width / 2, screen_height / 2 - 150))
        screen.blit(loss_surf, loss_rect)

        self.display_scores()

    def display_scores(self):
        conn = sqlite3.connect("game_scores.db")
        c = conn.cursor()

        c.execute("SELECT player_name, score FROM scores ORDER BY score DESC LIMIT 5")
        top_scores = c.fetchall()

        score_prefix = "TOP SCORES:"
        offset = -50
        prefix_surf = self.font.render(score_prefix, False, 'white')
        prefix_rect = prefix_surf.get_rect(center=(screen_width / 2, screen_height / 2 - 50))
        screen.blit(prefix_surf, prefix_rect)
        for i, score in enumerate(top_scores):
            name, value = score
            score_text = f"{i+1}. {name}: {value}"
            offset += 50

            score_surf = self.font.render(score_text, False, "white")
            score_rect = score_surf.get_rect(center=(screen_width / 2, screen_height / 2 + offset))
            screen.blit(score_surf, score_rect)

        conn.close()
    
    def first_menu_method(self):
        menu_surf = self.font.render("PRESS SPACE AND INPUT NAME", False, 'white')
        menu_rect = menu_surf.get_rect(center = (screen_width / 2, screen_height / 2))
        screen.blit(menu_surf, menu_rect)

    def first_menu_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            self.first_menu = True
            self.player_name = input("Enter Name:")

    def start_menu(self):
        start_surf = self.font.render(f"HELLO {self.player_name}, CLICK TO START", False, "white")
        start_rect = start_surf.get_rect(center = (screen_width / 2, screen_height / 2))
        screen.blit(start_surf, start_rect)
        
    def get_input(self):

        if pygame.mouse.get_pressed(num_buttons=3)[0]:
            self.start_game = True

    def save_score_to_database(self):
        conn = sqlite3.connect("game_scores.db")
        c = conn.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS scores (player_name text, score integer)")
        c.execute("SELECT * FROM scores WHERE player_name = ?", (self.player_name,))
        existing_entry = c.fetchone()

        if existing_entry:
            if self.score > existing_entry[1]:
                c.execute("UPDATE scores SET score = ? WHERE player_name = ?", (self.score, self.player_name))
        else:
            c.execute("INSERT INTO scores (player_name, score) VALUES (?, ?)", (self.player_name, self.score))

        conn.commit()
        conn.close()

    def run(self):
        if not self.first_menu and not self.start_game:
            self.first_menu_method()
            self.first_menu_input()
        if self.first_menu and not self.start_game:
            self.start_menu()
            self.get_input()

        if self.start_game and not self.game_over:
            self.player.update()
            self.aliens.update(self.alien_direction)
            self.alien_bullets.update()

            self.alien_position_checker()
            self.collision_checks()

            self.player.sprite.bullets.draw(screen)
            self.player.draw(screen)
            self.aliens.draw(screen)
            self.alien_bullets.draw(screen)
            self.display_lives()
            self.display_score()
            self.display_wave()

        if self.game_over:
            self.end_message()
            self.save_score_to_database()

if __name__ == '__main__':
    pygame.init()
    screen_width = 800
    screen_height = 600
    background = pygame.image.load('./lib/assets/background.png')
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    game = Game()


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game.start_game:
                ALIENBULLET = pygame.USEREVENT + 1
                pygame.time.set_timer(ALIENBULLET, 500)
                if event.type == ALIENBULLET:
                    game.alien_shoot()
        
        screen.blit(background, (0,0))

        game.run()

        pygame.display.flip()
        clock.tick(60)