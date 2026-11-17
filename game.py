
import pygame
import random
import requests
import os

SERVER = os.environ.get("GAME_SERVER_URL", "http://127.0.0.1:5000")
API_KEY = os.environ.get("GAME_API_KEY", "")
PLAYER = "Chantal"

pygame.init()

CELL = 20
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Cloud Snake")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)

snake = [(5, 5), (4, 5), (3, 5)]
direction = (1, 0)
next_direction = direction

def new_food():
    free = [
        (x, y)
        for x in range(WIDTH // CELL)
        for y in range(HEIGHT // CELL)
        if (x, y) not in snake
    ]
    return random.choice(free) if free else None

food = new_food()
score = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            moves = {
                pygame.K_UP: (0, -1),
                pygame.K_DOWN: (0, 1),
                pygame.K_LEFT: (-1, 0),
                pygame.K_RIGHT: (1, 0)
            }
            candidate = moves.get(event.key, next_direction)
            if candidate != (-direction[0], -direction[1]):
                next_direction = candidate

    if not running:
        break

    direction = next_direction
    head = (
        snake[0][0] + direction[0],
        snake[0][1] + direction[1]
    )

    eating = head == food
    body = snake if eating else snake[:-1]

    if (
        head[0] < 0 or head[0] >= WIDTH // CELL
        or head[1] < 0 or head[1] >= HEIGHT // CELL
        or head in body
    ):
        break

    snake.insert(0, head)

    if eating:
        score += 10
        food = new_food()
        if food is None:
            break
    else:
        snake.pop()

    screen.fill((18, 24, 38))

    for x, y in snake:
        pygame.draw.rect(
            screen, (40, 210, 100),
            (x * CELL, y * CELL, CELL - 2, CELL - 2)
        )

    if food:
        pygame.draw.rect(
            screen, (240, 70, 70),
            (food[0] * CELL, food[1] * CELL,
             CELL - 2, CELL - 2)
        )

    label = font.render(f"Score: {score}", True, "white")
    screen.blit(label, (10, 10))

    pygame.display.flip()
    clock.tick(8)

pygame.quit()

print(f"Game over! Score: {score}")

try:
    response = requests.post(
        f"{SERVER}/score",
        json={"player": PLAYER, "score": score},
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    response.raise_for_status()
    print("Game server response:", response.json())
except requests.RequestException as error:
    print("Could not send score:", error)
