import pygame
import neat
import time
import os
import csv
import random
pygame.font.init()

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800

# Changing the size of objects
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird3.png")))]
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BACKGROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "BG.png")))

STAT_FONT = pygame.font.SysFont("arial", 50)


# Bird class
class PlayerBird:
    IMAGE = BIRD_IMAGES
    MAX_ANGLE = 25
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMAGE[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def update_position(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y = self.y + d
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ANGLE:
                self.tilt = self.ROTATION_VELOCITY
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    def animation(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMAGE[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMAGE[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMAGE[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMAGE[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMAGE[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMAGE[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VELOCITY = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE
        self.passed = False
        self.generate_height()

    def generate_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def update_position(self):
        self.x -= self.VELOCITY

    def animation(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False

class Base:
    VELOCITY = 5
    WIDTH = BASE_IMAGE.get_width()
    IMG = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def update_position(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def animation(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))
    
def run_neat(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(main, 10)  # Make sure `main` is passed here
    return winner

# Draw window
def draw_window(win, birds, pipes, base, score):
    win.blit(BACKGROUND_IMAGE, (0, 0))
    for pipe in pipes:
        pipe.animation(win)
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WINDOW_WIDTH - 10 - text.get_width(), 10))
    base.animation(win)
    for bird in birds:
        bird.animation(win)
    pygame.display.update()

def init_csv():
    if not os.path.exists('csv'):
        os.makedirs('csv')  # Create the folder if it doesn't exist
    with open('csv/NEAT.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header for the CSV file
        writer.writerow(['Generation', 'Genome ID', 'Fitness'])

# Function to log data to the CSV file
def log_to_csv(gen, generation, fitness):
    with open('csv/NEAT.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # Log the genome ID, generation, and fitness
        writer.writerow([generation, gen.key, fitness])

# Main function for NEAT
def main(genomes, config):
    nets = []
    ge = []
    birds = []

    init_csv()

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(PlayerBird(230, 350))
        g.fitness = 0
        ge.append(g)

    bird = PlayerBird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    score = 0
    generation = 1
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.update_position()
            ge[x].fitness += 0.1
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.update_position()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.update_position()
        draw_window(win, birds, pipes, base, score)

        for g in ge:
            log_to_csv(g, generation, g.fitness)
 # Check if the score reached 
        if score >= 10:
            run = False
            winner_genome = max(ge, key=lambda g: g.fitness)  # Get the winner genome based on fitness
            print(f"Winner: Genome {winner_genome}")
            winner_text = STAT_FONT.render(f"Winner: Genome {winner_genome}", True, (255, 255, 255))
            win.blit(winner_text, (WINDOW_WIDTH // 2 - winner_text.get_width() // 2, WINDOW_HEIGHT // 2))
            pygame.display.update()
            pygame.time.delay(3000)  # Wait for 3 seconds before quitting
            break
        generation += 1
# Manual play function
def manual_play():
    bird = PlayerBird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

        bird.update_position()

        add_pipe = False
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):
                run = False
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.update_position()

        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
            run = False

        base.update_position()
        draw_window(win, [bird], pipes, base, score)

# Menu function
# Updated Menu function
def show_menu():
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Flappy Bird Game")

    font = pygame.font.SysFont("arial", 40)
    title_text = font.render("Flappy Bird", True, (255, 255, 255))
    play_text = font.render("1. Play using NEAT", True, (255, 255, 255))
    evolutionary_text = font.render("2. Play using EA", True, (255, 255, 255))
    manual_text = font.render("3. Play by Yourself", True, (255, 255, 255))
    quit_text = font.render("Q. Quit", True, (255, 255, 255))

    while True:
        win.blit(BACKGROUND_IMAGE, (0, 0))
        win.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 100))
        win.blit(play_text, (WINDOW_WIDTH // 2 - play_text.get_width() // 2, 200))
        win.blit(evolutionary_text, (WINDOW_WIDTH // 2 - evolutionary_text.get_width() // 2, 300))
        win.blit(manual_text, (WINDOW_WIDTH // 2 - manual_text.get_width() // 2, 400))
        win.blit(quit_text, (WINDOW_WIDTH // 2 - quit_text.get_width() // 2, 500))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    config_path = "config-feedforward.txt"
                    run_neat(config_path)
                elif event.key == pygame.K_2:
                    from evolutionary_bird_ai import EvolutionaryAlgorithm
                    ea = EvolutionaryAlgorithm(population_size=500)
                    ea.run()
                elif event.key == pygame.K_3:
                    manual_play()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()

# Run the menu
show_menu()
