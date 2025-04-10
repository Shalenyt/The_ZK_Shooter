# -*- coding: utf-8 -*-
import pygame
import json
import random
from gameRole import *
from sys import exit

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Succinct Labs: The ZK Shooter')

background = pygame.image.load('resources/image/shoot_background.png')
gameover = pygame.image.load('resources/image/gameover.png')
sprite_sheet = pygame.image.load('resources/image/shoot.png')

pygame.mixer.music.load('resources/sound/game_music.wav')
pygame.mixer.music.play(-1)
bullet_sound = pygame.mixer.Sound('resources/sound/bullet.wav')
enemy_down_sound = pygame.mixer.Sound('resources/sound/enemy_down.wav')
game_over_sound = pygame.mixer.Sound('resources/sound/gameover.wav')

bullet_sound.set_volume(0.3)
enemy_down_sound.set_volume(0.3)
game_over_sound.set_volume(0.3)
pygame.mixer.music.set_volume(0.25)

with open('resources/sprite_mapping.json', 'r') as f:
    mapping = json.load(f)

def get_sprite(name):
    x, y, w, h = mapping[name]["x"], mapping[name]["y"], mapping[name]["width"], mapping[name]["height"]
    return sprite_sheet.subsurface(pygame.Rect(x, y, w, h)).copy()

player_rect = [
    pygame.Rect(mapping['hero1_1']['x'], mapping['hero1_1']['y'], mapping['hero1_1']['width'], mapping['hero1_1']['height']),
    pygame.Rect(mapping['hero1_2']['x'], mapping['hero1_2']['y'], mapping['hero1_2']['width'], mapping['hero1_2']['height'])
]

player_pos = [200, 600]
player = Player(sprite_sheet, player_rect, player_pos, mapping)

bullet_img = get_sprite('bullet1')

enemy_imgs = {
    'enemy1': get_sprite('enemy1'),
    'enemy2': get_sprite('enemy2'),
    'enemy3': get_sprite('enemy3')
}

enemy_down_imgs = {
    'enemy1': [get_sprite(f'enemy1_down{i}') for i in range(1, 5)],
    'enemy2': [get_sprite(f'enemy2_down{i}') for i in range(1, 5)],
    'enemy3': [get_sprite(f'enemy3_down{i}') for i in range(1, 5)]
}

enemies = pygame.sprite.Group()
enemies_down = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()

shoot_frequency = 0
enemy_frequency = 0
player_down_index = 16
score = 0
clock = pygame.time.Clock()
running = True
game_over = False

while running:
    clock.tick(50)
    screen.blit(background, (0, 0))

    if not player.is_hit:
        if shoot_frequency % 15 == 0:
            bullet_sound.play()
            player.shoot(bullet_img)
        shoot_frequency += 1
        if shoot_frequency >= 15:
            shoot_frequency = 0

    if enemy_frequency % 50 == 0:
        enemy_type = random.choice(['enemy1', 'enemy2', 'enemy3'])
        enemy_pos = [random.randint(0, SCREEN_WIDTH - mapping[enemy_type]['width']), 0]
        
        safe = True
        for e in enemies:
            if pygame.Rect(enemy_pos, (mapping[enemy_type]['width'], mapping[enemy_type]['height'])).colliderect(e.rect):
                safe = False
                break
        if safe:
            enemy = Enemy(enemy_imgs[enemy_type], enemy_down_imgs[enemy_type], enemy_pos, enemy_type)
            enemies.add(enemy)

    enemy_frequency += 1
    if enemy_frequency >= 100:
        enemy_frequency = 0

    for bullet in player.bullets:
        bullet.move()
        if bullet.rect.bottom < 0:
            player.bullets.remove(bullet)

    for bullet in enemy_bullets:
        bullet.move()
        if bullet.rect.top > SCREEN_HEIGHT:
            enemy_bullets.remove(bullet)
        if bullet.rect.colliderect(player.rect):
            player.is_hit = True
            game_over_sound.play()
            break

    for enemy in enemies:
        enemy.move()
        if enemy.type == 'enemy3' and random.randint(0, 100) < 2:
            enemy.shoot(bullet_img, enemy_bullets)

        if pygame.sprite.collide_circle(enemy, player):
            enemies_down.add(enemy)
            enemies.remove(enemy)
            player.is_hit = True
            game_over_sound.play()
            break

        if enemy.rect.top > SCREEN_HEIGHT:
            enemies.remove(enemy)

    enemies_hit = pygame.sprite.groupcollide(enemies, player.bullets, 1, 1)
    for enemy_hit in enemies_hit:
        enemies_down.add(enemy_hit)

    for enemy_down in enemies_down:
        if enemy_down.down_index == 0:
            enemy_down_sound.play()
        if enemy_down.down_index > 7:
            enemies_down.remove(enemy_down)
            score += 100
            continue
        screen.blit(enemy_down.down_imgs[enemy_down.down_index // 2], enemy_down.rect)
        enemy_down.down_index += 1

    if not player.is_hit:
        player.img_index = shoot_frequency // 8
        player.img_index = player.img_index % len(player.image)
        screen.blit(player.image[player.img_index], player.rect)
    else:
        player.img_index = player_down_index // 8
        player.img_index = player.img_index % len(player.image)
        screen.blit(player.image[player.img_index], player.rect)
        player_down_index += 1
        if player_down_index > 47:
            game_over = True
            break

    player.bullets.draw(screen)
    enemies.draw(screen)
    enemy_bullets.draw(screen)

    score_font = pygame.font.Font(None, 36)
    score_text = score_font.render(f'SCORE: {score}', True, (0, 0, 0))
    screen.blit(score_text, (10, 10))

    handle_text = score_font.render("@0xShalen", True, (0, 0, 0))
    handle_rect = handle_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
    screen.blit(handle_text, handle_rect)

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    key_pressed = pygame.key.get_pressed()
    if not player.is_hit:
        if key_pressed[pygame.K_w] or key_pressed[pygame.K_UP]:
            player.moveUp()
        if key_pressed[pygame.K_s] or key_pressed[pygame.K_DOWN]:
            player.moveDown()
        if key_pressed[pygame.K_a] or key_pressed[pygame.K_LEFT]:
            player.moveLeft()
        if key_pressed[pygame.K_d] or key_pressed[pygame.K_RIGHT]:
            player.moveRight()

# Game Over Screen + Retry
while game_over:
    screen.blit(gameover, (0, 0))

    font = pygame.font.Font(None, 48)
    retry_text = font.render("PRESS R TO RETRY", True, (255, 0, 0))
    retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    screen.blit(retry_text, retry_rect)

    score_font = pygame.font.Font(None, 60)
    score_text = score_font.render(f'SCORE: {score}', True, (0, 0, 0))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(score_text, score_rect)

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                exec(open('index.py').read())
