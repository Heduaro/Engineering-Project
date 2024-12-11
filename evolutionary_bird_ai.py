import pygame
import random
import os
from Testgame2 import Bird, Pipe, Base, draw_window

# Constants
WIN_WIDTH = 500
WIN_HEIGHT = 800
GENERATION_SIZE = 10
MUTATION_RATE = 0.1

# Helper functions
def mutate(weights):
    """Randomly mutate weights."""
    for i in range(len(weights)):
        if random.random() < MUTATION_RATE:
            weights[i] += random.uniform(-0.5, 0.5)
    return weights

def crossover(parent1, parent2):
    """Perform crossover between two parents to generate a child."""
    return [random.choice([w1, w2]) for w1, w2 in zip(parent1, parent2)]

# Bird Controller class
class BirdController:
    def __init__(self, weights=None):
        self.weights = weights if weights else [random.uniform(-1, 1) for _ in range(3)]
        self.fitness = 0

    def decide(self, bird_y, pipe_top, pipe_bottom):
        """Simple linear decision model."""
        inputs = [bird_y / WIN_HEIGHT, pipe_top / WIN_HEIGHT, pipe_bottom / WIN_HEIGHT]
        decision = sum(w * i for w, i in zip(self.weights, inputs))
        return decision > 0  # Returns True to jump

# Evolutionary Algorithm class
class EvolutionaryAlgorithm:
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation = 0
        self.population = []  # List of BirdController objects
        self.birds = []  # List of Bird objects during simulation

    def initialize_population(self):
        """Initialize the population with random BirdControllers."""
        self.population = [BirdController() for _ in range(self.population_size)]

    def evaluate_generation(self):
        """Evaluate the current generation by running a simulation."""
        self.birds = [Bird(230, 350) for _ in range(len(self.population))]
        base = Base(730)
        pipes = [Pipe(600)]
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        clock = pygame.time.Clock()
        score = 0
        run = True

        while run:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            # Check if there are no birds left
            if len(self.birds) == 0:
                run = False
                break

            # Determine which pipe to use for decisions
            pipe_ind = 0
            if len(pipes) > 1 and self.birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

            # Move birds and make decisions
            for i, bird in enumerate(self.birds):
                bird.move()
                pipe = pipes[pipe_ind]
                if self.population[i].decide(bird.y, pipe.height, pipe.bottom):
                    bird.jump()

            # Pipe logic
            add_pipe = False
            rem = []
            for pipe in pipes:
                for i in reversed(range(len(self.birds))):  # Iterate in reverse to avoid index issues
                    if pipe.collide(self.birds[i]):
                        self.population[i].fitness = score
                        self.birds.pop(i)
                        self.population.pop(i)

                if not pipe.passed and self.birds and pipe.x < self.birds[0].x:
                    pipe.passed = True
                    add_pipe = True

                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                pipe.move()

            if add_pipe:
                score += 1
                pipes.append(Pipe(600))

            for r in rem:
                pipes.remove(r)

            # Check if birds hit the ground or fly out of bounds
            for i in reversed(range(len(self.birds))):  # Iterate in reverse to avoid index issues
                if self.birds[i].y + self.birds[i].img.get_height() >= 730 or self.birds[i].y < 0:
                    self.population[i].fitness = score
                    self.birds.pop(i)
                    self.population.pop(i)

            base.move()
            draw_window(win, self.birds, pipes, base, score)

    def reproduce(self):
        """Create the next generation."""
        # Sort population by fitness
        self.population.sort(key=lambda bc: bc.fitness, reverse=True)

        # Select top performers
        next_generation = self.population[:2]

        # Create children from top performers
        while len(next_generation) < self.population_size:
            parent1, parent2 = random.choices(self.population[:5], k=2)
            child_weights = crossover(parent1.weights, parent2.weights)
            child_weights = mutate(child_weights)
            next_generation.append(BirdController(child_weights))

        self.population = next_generation

    def run(self):
        """Run the evolutionary algorithm for a fixed number of generations."""
        self.initialize_population()
        max_generations = 10  # Set the maximum number of generations

        try:
            while self.generation < max_generations:
                print(f"Generation {self.generation + 1}")
                self.evaluate_generation()
                self.reproduce()
                self.generation += 1
        except Exception as e:
            print(f"Unexpected error: {e}. Exiting the simulation.")
        finally:
            print("Simulation complete.")


if __name__ == "__main__":
    pygame.font.init()
    ea = EvolutionaryAlgorithm(GENERATION_SIZE)
    ea.run()
