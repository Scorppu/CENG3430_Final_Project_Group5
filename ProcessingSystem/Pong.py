import pygame
import sys
import time
import random

# --- Abstract Input Handler ---
class InputHandler:
    @staticmethod
    def get_left_direction():
        keys = pygame.key.get_pressed()
        return -1 if keys[pygame.K_w] else 1 if keys[pygame.K_s] else 0

    @staticmethod
    def get_right_direction():
        keys = pygame.key.get_pressed()
        return -1 if keys[pygame.K_UP] else 1 if keys[pygame.K_DOWN] else 0

    @staticmethod
    def get_menu_change():
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return 1
        return 0

    @staticmethod
    def get_menu_select():
        keys = pygame.key.get_pressed()
        return keys[pygame.K_RETURN]

    @staticmethod
    def get_restart():
        keys = pygame.key.get_pressed()
        return keys[pygame.K_r]

    @staticmethod
    def handle_events():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return True

# --- Abstract Output Renderer ---
class OutputRenderer:
    def __init__(self, width, height):
        self.screen = pygame.display.set_mode((width, height))
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 32)
        self.big_font = pygame.font.SysFont(None, 180)
        self.width = width
        self.height = height

    def clear_screen(self):
        self.screen.fill((0,0,0))

    def draw_paddles(self, left_paddle, right_paddle):
        pygame.draw.rect(self.screen, (255,255,255), left_paddle)
        pygame.draw.rect(self.screen, (255,255,255), right_paddle)

    def draw_ball(self, ball):
        pygame.draw.ellipse(self.screen, (255,255,255), ball)

    def draw_dashed_line(self):
        dash_length = 20
        gap_length = 20
        y = 0
        while y < self.height:
            pygame.draw.line(self.screen, (255,255,255), 
                           (self.width//2, y),
                           (self.width//2, min(y + dash_length, self.height)), 4)
            y += dash_length + gap_length

    def draw_scores(self, left, right):
        text = self.font.render(f"{left}   {right}", True, (255,255,255))
        self.screen.blit(text, (self.width//2 - text.get_width()//2, 20))

    def draw_countdown(self, count):
        if count > 0:
            text = self.big_font.render(str(count), True, (255,255,255))
        else:
            text = self.big_font.render("Go!", True, (255,255,255))
        self.screen.blit(text, (self.width//2 - text.get_width()//2, 
                               self.height//2 - text.get_height()//2))

    def draw_start_screen(self, best_to):
        self.clear_screen()
        title = self.font.render("PONG", True, (255,255,255))
        subtitle = self.small_font.render("Select rounds to win (Best to X)", True, (255,255,255))
        selector = self.font.render(f"Best to: {best_to}", True, (255,255,255))
        instructions = self.small_font.render("Use ←/→ or A/D to change. Press Enter to start.", True, (255,255,255))
        self.screen.blit(title, (self.width//2 - title.get_width()//2, self.height//2 - 120))
        self.screen.blit(subtitle, (self.width//2 - subtitle.get_width()//2, self.height//2 - 60))
        self.screen.blit(selector, (self.width//2 - selector.get_width()//2, self.height//2))
        self.screen.blit(instructions, (self.width//2 - instructions.get_width()//2, self.height//2 + 60))

    def draw_winner(self, winner):
        winner_text = self.font.render(f"{winner} Wins!", True, (255,255,255))
        restart_text = self.small_font.render("Press R to restart", True, (255,255,255))
        self.screen.blit(winner_text, (self.width//2 - winner_text.get_width()//2, self.height//2 - 50))
        self.screen.blit(restart_text, (self.width//2 - restart_text.get_width()//2, self.height//2 + 10))

    def update_display(self):
        pygame.display.flip()

# --- Pong Game Logic ---
class PongGame:
    def __init__(self, input_handler, output_renderer):
        self.input = input_handler
        self.output = output_renderer
        self.width = 800
        self.height = 600
        self.paddle_w = 10
        self.paddle_h = 100
        self.paddle_speed = 7
        self.ball_size = 20
        self.ball_speed_init = [5, 5]
        self.min_best_to = 1
        self.max_best_to = 15
        self.reset_game_state()

    def reset_game_state(self):
        self.left_paddle = pygame.Rect(10, self.height//2 - self.paddle_h//2, self.paddle_w, self.paddle_h)
        self.right_paddle = pygame.Rect(self.width-20, self.height//2 - self.paddle_h//2, self.paddle_w, self.paddle_h)
        self.ball = pygame.Rect(self.width//2 - self.ball_size//2, self.height//2 - self.ball_size//2, self.ball_size, self.ball_size)
        self.ball_speed = self.ball_speed_init.copy()
        self.scores = [0, 0]
        self.best_to = 5
        self.state = "START"
        self.countdown_start_time = 0
        self.countdown_length = 3
        self.first_round = True
        self.last_loser = None  # Track last point loser

    def reset_ball(self, toward=None):
        self.ball.x = self.width//2 - self.ball_size//2
        self.ball.y = self.height//2 - self.ball_size//2
        # Randomize vertical direction
        y_dir = random.choice([-1, 1])
        # Set horizontal direction toward the player who lost the last point
        if toward == "left":
            self.ball_speed = [-abs(self.ball_speed_init[0]), y_dir * abs(self.ball_speed_init[1])]
        elif toward == "right":
            self.ball_speed = [abs(self.ball_speed_init[0]), y_dir * abs(self.ball_speed_init[1])]
        else:
            # On first serve, randomize direction
            self.ball_speed = [random.choice([-1, 1]) * abs(self.ball_speed_init[0]), y_dir * abs(self.ball_speed_init[1])]

    def move_paddles(self):
        # Left paddle movement
        dir_left = self.input.get_left_direction()
        self.left_paddle.y += dir_left * self.paddle_speed
        self.left_paddle.y = max(0, min(self.height - self.paddle_h, self.left_paddle.y))
        # Right paddle movement
        dir_right = self.input.get_right_direction()
        self.right_paddle.y += dir_right * self.paddle_speed
        self.right_paddle.y = max(0, min(self.height - self.paddle_h, self.right_paddle.y))

    def handle_start_screen(self):
        menu_change = self.input.get_menu_change()
        if menu_change != 0:
            self.best_to = max(self.min_best_to, min(self.max_best_to, self.best_to + menu_change))
            time.sleep(0.15)  # debounce
        if self.input.get_menu_select():
            self.reset_game_state()
            self.best_to = self.best_to  # retain selection
            self.state = "COUNTDOWN"
            self.countdown_start_time = time.time()
            self.first_round = True
            self.reset_ball()  # Random direction for first serve
            time.sleep(0.2)  # debounce

    def handle_countdown(self):
        self.move_paddles()
        elapsed = time.time() - self.countdown_start_time
        count = self.countdown_length - int(elapsed)
        self.output.clear_screen()
        self.output.draw_paddles(self.left_paddle, self.right_paddle)
        self.output.draw_dashed_line()
        self.output.draw_scores(self.scores[0], self.scores[1])
        self.output.draw_countdown(count)
        self.output.update_display()
        if elapsed >= self.countdown_length + 1:
            self.state = "PLAYING"
            self.first_round = False

    def handle_playing(self):
        self.move_paddles()
        # Ball movement
        self.ball.x += self.ball_speed[0]
        self.ball.y += self.ball_speed[1]
        # Collisions: top/bottom
        if self.ball.top <= 0 or self.ball.bottom >= self.height:
            self.ball_speed[1] *= -1
        # Collisions: paddles
        if self.ball.colliderect(self.left_paddle) or self.ball.colliderect(self.right_paddle):
            self.ball_speed[0] *= -1
        # Score: left out
        if self.ball.left <= 0:
            self.scores[1] += 1
            self.last_loser = "left"  # Left lost the point
            self.reset_ball(toward="left")
        # Score: right out
        elif self.ball.right >= self.width:
            self.scores[0] += 1
            self.last_loser = "right"  # Right lost the point
            self.reset_ball(toward="right")
        # Win check
        if self.scores[0] >= self.best_to:
            self.state = "GAME_OVER"
            self.winner = "Left Player"
        elif self.scores[1] >= self.best_to:
            self.state = "GAME_OVER"
            self.winner = "Right Player"

    def handle_game_over(self):
        if self.input.get_restart():
            self.state = "START"
            time.sleep(0.2)  # debounce

    def draw(self):
        if self.state == "START":
            self.output.draw_start_screen(self.best_to)
        else:
            self.output.clear_screen()
            self.output.draw_paddles(self.left_paddle, self.right_paddle)
            if self.state != "COUNTDOWN":
                self.output.draw_ball(self.ball)
            self.output.draw_dashed_line()
            self.output.draw_scores(self.scores[0], self.scores[1])
            if self.state == "GAME_OVER":
                self.output.draw_winner(self.winner)
        self.output.update_display()

    def game_loop(self):
        clock = pygame.time.Clock()
        while True:
            self.input.handle_events()
            if self.state == "START":
                self.handle_start_screen()
            elif self.state == "COUNTDOWN":
                self.handle_countdown()
            elif self.state == "PLAYING":
                self.handle_playing()
            elif self.state == "GAME_OVER":
                self.handle_game_over()
            self.draw()
            clock.tick(60)

if __name__ == "__main__":
    pygame.init()
    game = PongGame(InputHandler(), OutputRenderer(800, 600))
    game.game_loop()
