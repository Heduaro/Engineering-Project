import pygame
import random
import os
import csv
from Testgame3 import PlayerBird, Pipe, Base, draw_window
import time

# Constants
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
GENERATION_SIZE = 20
MUTATION_RATE = 0.05  # Reduced mutation rate
PIPE_SPEED = 2  # Reduced pipe speed
BIRD_REACTION_TIME = 1  # Allow birds more time to react

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
class BirdControll:
    def __init__(self, weights=None):
        self.weights = weights if weights else [random.uniform(-1, 1) for _ in range(3)]
        self.fitness = 0

    def decide(self, bird_y, pipe_top, pipe_bottom):
        """Improved decision model for jumping."""
        inputs = [bird_y / WINDOW_HEIGHT, pipe_top / WINDOW_HEIGHT, pipe_bottom / WINDOW_HEIGHT]
        decision = sum(w * i for w, i in zip(self.weights, inputs))
        return decision > 0  # Returns True to jump

# Evolutionary Algorithm class
class EvolutionaryAlgorithm:
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation = 0
        self.population = []
        self.birds = []
        self.deaths = 0

    def initialize_population(self):
        """Initialize the population with random BirdController."""
        self.population = [BirdControll() for _ in range(self.population_size)]

    def evaluate_generation(self):
        """Evaluate the current generation by running a simulation."""
        if not self.population:
            return

        self.birds = [PlayerBird(230, 350) for _ in range(len(self.population))]
        base = Base(730)
        pipes = [Pipe(600)]
        win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        clock = pygame.time.Clock()
        score = 0

        start_time = time.time()
        run = True

        while run and len(self.birds) > 0:  # Continue while there are birds alive
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            # Determine which pipe to use for decisions
            pipe_ind = 0
            if len(pipes) > 1 and self.birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

            # update_position birds and make decisions
            for i, bird in enumerate(self.birds):
                bird.update_position()
                pipe = pipes[pipe_ind]
                if self.population[i].decide(bird.y, pipe.height, pipe.bottom):
                    bird.jump()

            # Handle pipes
            add_pipe = False
            rem = []
            for pipe in pipes:
                for i in reversed(range(len(self.birds))):
                    if pipe.collide(self.birds[i]):
                        self.population[i].fitness = score + (WINDOW_WIDTH - abs(self.birds[i].x - pipe.x)) / WINDOW_WIDTH
                        self.birds.pop(i)
                        self.population.pop(i)

                if not pipe.passed and self.birds and pipe.x < self.birds[0].x:
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

            # Check for out-of-bounds birds
            for i in reversed(range(len(self.birds))):
                if self.birds[i].y + self.birds[i].img.get_height() >= 730 or self.birds[i].y < 0:
                    self.population[i].fitness = score
                    self.birds.pop(i)
                    self.population.pop(i)

            base.update_position()
            draw_window(win, self.birds, pipes, base, score)

        self.log_generation_results(time.time() - start_time, score)

    def log_generation_results(self, generation_duration, score):
        """Log the results of the current generation."""
        if len(self.population) > 0:
            avg_fitness = sum([bc.fitness for bc in self.population]) / len(self.population)
            best_individual = max(self.population, key=lambda bc: bc.fitness)
            best_fitness = best_individual.fitness
            best_weights = best_individual.weights

            # Prepare data for CSV
            generation_data = {
                'Generation': self.generation,
                'Generation Duration': generation_duration,
                'Average Fitness': avg_fitness,
                'Best Fitness': best_fitness,
                'Score': score
            }

            # Save results to CSV
            self.save_to_csv(generation_data)

    def save_to_csv(self, data):
        """Save the generation results to a CSV file."""
        os.makedirs("csv", exist_ok=True)
        file_path = os.path.join("csv", "EA.csv")

        # Check if file exists to write header
        file_exists = os.path.isfile(file_path)

        with open(file_path, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()  # Write header if file does not exist
            writer.writerow(data)

    def reproduce(self):
        """Create the next generation."""
        if len(self.population) == 0:
            return

        self.population.sort(key=lambda bc: bc.fitness, reverse=True)
        next_generation = self.population[:2]

        while len(next_generation) < self.population_size:
            parent1, parent2 = random.choices(self.population[:5], k=2)
            child_weights = crossover(parent1.weights, parent2.weights)
            child_weights = mutate(child_weights)
            next_generation.append(BirdControll(child_weights))

        self.population = next_generation

    def run(self):
        """Run the evolutionary algorithm for a fixed number of generations."""
        self.initialize_population()
        max_generations = 10

        try:
            while self.generation < max_generations:
                self.evaluate_generation()
                self.reproduce()
                self.generation += 1
        except Exception as e:
            print(f"Unexpected error: {e}. Exiting the simulation.")
        finally:
            print("Simulation complete.")

if __name__ == "__main__":
    pygame.font.init()
    for run_number in range(10):  # Run the simulation 10 times
        print(f"Starting simulation run {run_number + 1}...")
        ea = EvolutionaryAlgorithm(GENERATION_SIZE)
        ea.run()
