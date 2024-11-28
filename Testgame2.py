import pygame
import random
import time
pygame.font.init()

# Game configuration
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Changing the size of objects
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load("imgs/bird1.png")),
             pygame.transform.scale2x(pygame.image.load("imgs/bird2.png")),
             pygame.transform.scale2x(pygame.image.load("imgs/bird3.png"))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load("imgs/pipe.png"))
BASE_IMG = pygame.transform.scale2x(pygame.image.load("imgs/base.png"))
BG_IMG = pygame.transform.scale2x(pygame.image.load("imgs/BG.png"))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

# Bird class
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]
        self.fitness = 0  # Fitness value for evolutionary algorithm

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y = self.y + d
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


# Pipe class
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
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


# Base class (the ground)
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# Draw window
def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


# Population for evolutionary algorithm
class Population:
    def __init__(self, size, mutation_rate):
        self.size = size
        self.mutation_rate = mutation_rate
        self.birds = [Bird(230, 350) for _ in range(size)]
        self.generation = 0

    def evolve(self):
        # Perform selection, crossover, and mutation to evolve the population
        self.selection()
        self.crossover()
        self.mutation()

    def selection(self):
        # Sort birds based on fitness and select top birds to mate
        self.birds = sorted(self.birds, key=lambda bird: bird.fitness, reverse=True)
        self.birds = self.birds[:self.size // 2]  # Keep top 50% of birds

    def crossover(self):
        # Perform crossover to create new birds
        new_birds = []
        for i in range(self.size // 2):
            parent1 = self.birds[i]
            parent2 = self.birds[random.randint(0, len(self.birds) - 1)]
            child = Bird(230, 350)  # Create a new bird from parents (using some logic here)
            new_birds.append(child)
        self.birds.extend(new_birds)

    def mutation(self):
        # Mutate birds' properties
        for bird in self.birds:
            if random.random() < self.mutation_rate:
                bird.jump()  # Mutate by making a random jump

    def get_best_bird(self):
        return sorted(self.birds, key=lambda bird: bird.fitness, reverse=True)[0]


# Main evolutionary algorithm
def evolutionary_algorithm():
    population = Population(size=20, mutation_rate=0.01)  # Start with 20 birds
    pipes = [Pipe(600)]
    base = Base(730)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0
    generations = 50  # Set to 50 generations
    current_generation = 0  # Track the current generation

    while current_generation < generations:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Move birds and evolve population
        for bird in population.birds:
            bird.move()
            bird.fitness += 0.1  # Increase fitness over time

            # Birds should jump randomly or based on some criteria
            if random.random() < 0.1:  # Random chance to make a jump
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for bird in population.birds:
                if pipe.collide(bird):
                    population.birds.remove(bird)

            if not pipe.passed and pipe.x < population.birds[0].x:
                pipe.passed = True
                add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()

        if add_pipe:
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        if len(population.birds) == 0:  # If all birds are dead, evolve the population
            print(f"Generation {current_generation + 1} - Evolving population...")
            population.evolve()
            current_generation += 1  # Increment generation count

        # Draw everything
        base.move()
        draw_window(win, population.birds, pipes, base, score)

    print("Evolution complete.")
    pygame.quit()
    quit()


# Start the game and evolutionary algorithm
def show_menu():
    run = True
    while run:
        draw_window(pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT)), [], [], Base(730), 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        evolutionary_algorithm()  # Start evolutionary algorithm

    pygame.quit()
    quit()


show_menu()
