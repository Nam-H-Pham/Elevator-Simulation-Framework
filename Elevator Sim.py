import random
global TOP_FLOOR, FLOORS_DEMAND_DISTRIBUTION, GROUND_FLOOR, BLACK_LISTED_DESTINATIONS

random.seed(0)

GROUND_FLOOR = 1 # ground floor. default starting floor for elevators
TOP_FLOOR = 4  # top floor of the building

FLOORS_DEMAND_DISTRIBUTION = [0.1, 0.4, 0.4, 0.05, 0.05] # distribution of destination floors
FLOORS_START_DISTRIBUTION = [0.1, 0.4, 0.4, 0.05, 0.05] # distribution of starting floors

BLACK_LISTED_DESTINATIONS = [] # destinations elevators wont cover

TIME_TAKEN_TO_TRAVEL_ONE_FLOOR = 8 # time taken to travel one floor
TIME_TAKEN_TO_PICKUP_PASSENGER = 2 # time taken to pick up a passenger
TIME_TAKEN_TO_DROP_PASSENGER = 2 # time taken to drop off a passenger

TIME_TAKEN_TO_WALK_ONE_FLOOR = 15 # time taken to walk one floor

TOTAL_ELEVATORS = 2 # total number of elevators
TOTAL_PASSENGERS = 200 # total number of passengers

MAX_ELAVATOR_CAPACITY = 10 # max capacity of an elevator
MAX_STAIR_CAPACITY = 32 # max capacity of stairs

# behavior
CHANCE_TO_TAKE_ELEVATOR = 0 # chance to take the elevator instead of the stairs if the elevator is available
                            # 0 - Always take the stairs when elevators are not available, 1 - always take the elevator

class Passenger:
    def __init__(self, current_floor, destination_floor) -> None:
        self.current_floor = current_floor
        self.destination_floor = destination_floor

        self.start_time = 0
        self.end_time = 0

    def get_duration(self) -> int:
        return self.end_time - self.start_time

    def get_direction(self) -> str:
        if self.current_floor < self.destination_floor:
            return 'up'
        elif self.current_floor > self.destination_floor:
            return 'down'
        else:
            return 'stopped'

    def arrived(self) -> bool: 
        # not in any elevator as a passenger and arrived at destination floor
        return (self.current_floor == self.destination_floor) \
                and (self not in [p for elevator in ELEVATORS for p in elevator.passengers]) \
                and (self not in [p for p, _ in STAIRS.passengers])

    def at_destination(self) -> bool:
        return (self.current_floor == self.destination_floor) 

    def __str__(self) -> str:
        return f"{self.current_floor},{self.destination_floor}"

class Stairs:
    def __init__(self):
        self.passengers = []
        self.max_capacity = MAX_STAIR_CAPACITY

    def take_passengers(self) -> None:

        for passenger in ELEVATOR_QUEUE[:]:

            if len(self.passengers) >= self.max_capacity:
                break
            
            if len(ELEVATORS) == 0 or all([elevator.is_full() for elevator in ELEVATORS]) or (passenger.destination_floor in BLACK_LISTED_DESTINATIONS):

                # check if passenger will take the elevator if it is available
                if (passenger.destination_floor not in BLACK_LISTED_DESTINATIONS) and len(ELEVATORS) > 0:
                    if random.random() < CHANCE_TO_TAKE_ELEVATOR:
                        continue

                ELEVATOR_QUEUE.remove(passenger)
                self.passengers.append((passenger, TIME_TAKEN_TO_WALK_ONE_FLOOR))


    def move_passengers(self) -> None:
        for passenger, time in self.passengers:

            if time == 0:
                if passenger.get_direction() == 'up':
                    passenger.current_floor += 1

                    STAIR_MOVEMENTS.append(1)

                elif passenger.get_direction() == 'down':
                    passenger.current_floor -= 1

                    STAIR_MOVEMENTS.append(-1)

                if passenger.at_destination():
                    passenger.end_time = simulation_clock

                self.passengers.remove((passenger, time))
                if not passenger.arrived():
                    ELEVATOR_QUEUE.append(passenger)


    def decrement_cooldown(self):
        for i, (p, time) in enumerate(self.passengers):
            self.passengers[i] = (p, max(0, time - 1))

class Elevator:
    def __init__(self, id=1) -> None:
        self.current_floor = GROUND_FLOOR
        self.destination_floor = GROUND_FLOOR
        self.passengers = []
        self.max_capacity = MAX_ELAVATOR_CAPACITY
        self.id = id
        self.cooldown = 0

    def is_full(self) -> bool:
        return len(self.passengers) == self.max_capacity

    def is_empty(self) -> bool:
        return len(self.passengers) == 0

    def get_direction(self):
        if self.current_floor < self.destination_floor:
            return 'up'
        elif self.current_floor > self.destination_floor:
            return 'down'
        else:
            return 'stopped'

    def take_passengers(self) -> None:
        if self.cooldown > 0:
            return

        elevator_queue_filtered = [p for p in ELEVATOR_QUEUE if p.destination_floor not in BLACK_LISTED_DESTINATIONS]

        # if there are passengers on the same floor, add them to the elevator
        if self.current_floor in [p.current_floor for p in elevator_queue_filtered]:

            # get direction of elevator if it is stopped
            if self.get_direction() == 'stopped':
                for passenger in elevator_queue_filtered:
                    if passenger.current_floor == self.current_floor:
                        
                        self.destination_floor = passenger.destination_floor

                        break

            # collect all passengers going in the same direction
            collected_passengers = []
            for passenger in elevator_queue_filtered:
                if self.is_full():
                    break
                if passenger.current_floor == self.current_floor and passenger.get_direction() == self.get_direction():
                    self.passengers.append(passenger)
                    collected_passengers.append(passenger)
                    ELEVATOR_QUEUE.remove(passenger)

            # update destination floor
            if len(self.passengers) > 0:
                if self.get_direction() == 'up':
                    self.destination_floor = max([p.destination_floor for p in self.passengers])
                elif self.get_direction() == 'down':
                    self.destination_floor = min([p.destination_floor for p in self.passengers])
            

            # print collected passengers
            for passenger in collected_passengers:
                self.cooldown += TIME_TAKEN_TO_PICKUP_PASSENGER


        else: # if there are no passengers on the same floor, 
            if len(ELEVATOR_QUEUE) > 0 and len(self.passengers) == 0: # elevator is available
                for passenger in elevator_queue_filtered: # find the next person to travel to
                    self.destination_floor = passenger.current_floor
                    break


    def move(self) -> None:
        if self.cooldown > 0 or any([p.at_destination() for p in self.passengers]):
            return

        if self.get_direction() == 'up':
            self.current_floor += 1

            ELEVATOR_MOVEMENTS.append(1)

            for passenger in self.passengers:
                passenger.current_floor += 1
            self.cooldown += TIME_TAKEN_TO_TRAVEL_ONE_FLOOR
        elif self.get_direction() == 'down':
            self.current_floor -= 1

            ELEVATOR_MOVEMENTS.append(-1)

            for passenger in self.passengers:
                passenger.current_floor -= 1
            self.cooldown += TIME_TAKEN_TO_TRAVEL_ONE_FLOOR
        else:
            self.cooldown = 0

    def drop_off_passengers(self) -> None:
        if self.cooldown > 0:
            return

        # print dropped off passengers
        dropped_off_passengers = [p for p in self.passengers if p.destination_floor == self.current_floor]
        for passenger in dropped_off_passengers:
            self.passengers.remove(passenger)
            passenger.end_time = simulation_clock
            self.cooldown += TIME_TAKEN_TO_DROP_PASSENGER

        # update destination floor
        if len(self.passengers) > 0:
            if self.get_direction() == 'up':
                self.destination_floor = max([p.destination_floor for p in self.passengers])
            elif self.get_direction() == 'down':
                self.destination_floor = min([p.destination_floor for p in self.passengers])
        else:
            self.destination_floor = self.current_floor # elevator is empty. Direction is stopped

    def decrement_cooldown(self):
        self.cooldown = max(0, self.cooldown - 1)

    def __str__(self) -> str:
        return f"Elevator {self.id}: {self.current_floor} -> {self.destination_floor}"

def create_elevator_queue(num_passengers=5):
    ELEVATOR_QUEUE = []
    
    for i in range(num_passengers):

        start_floor = random.choices(range(0, TOP_FLOOR+1), FLOORS_START_DISTRIBUTION)[0] # Set the floor to a random floor based on the distribution

        demand_distrubition = FLOORS_DEMAND_DISTRIBUTION.copy()
        demand_distrubition[start_floor] = 0 # Set the demand for the starting floor to 0

        end_floor = random.choices(range(0, TOP_FLOOR+1), demand_distrubition)[0] # Set the floor to a random floor based on the distribution

        ELEVATOR_QUEUE.append(Passenger(start_floor, end_floor))

    return ELEVATOR_QUEUE

def check_arrived(ALL_PASSENGERS):
    return all([p.arrived() for p in ALL_PASSENGERS])

def initialise_simulation():
    global ELEVATORS, STAIRS, ALL_PASSENGERS, ELEVATOR_QUEUE, ELEVATOR_MOVEMENTS, STAIR_MOVEMENTS, simulation_clock

    ELEVATORS = [Elevator(i) for i in range(TOTAL_ELEVATORS)]
    STAIRS = Stairs()

    # trackers
    ELEVATOR_MOVEMENTS = [] # elevator movements e.g. 1 for up, -1 for down
    STAIR_MOVEMENTS = [] # stair movements e.g. 1 for up, -1 for down


    ALL_PASSENGERS = []
    ALL_PASSENGERS.extend(create_elevator_queue(num_passengers=TOTAL_PASSENGERS))

    ELEVATOR_QUEUE = []

    simulation_clock = 1

def introduce_new_passengers(passengers):
    for passenger in passengers:
        ELEVATOR_QUEUE.append(passenger)
        passenger.start_time = simulation_clock

def run_simulation():
    global simulation_clock
    initialise_simulation()

    introduce_new_passengers(ALL_PASSENGERS)

    while not check_arrived(ALL_PASSENGERS):

        STAIRS.take_passengers()
        STAIRS.move_passengers()

        for elevator in ELEVATORS:
            elevator.take_passengers()

        for elevator in ELEVATORS:
            elevator.move()

        for elevator in ELEVATORS:
            elevator.drop_off_passengers()

        for elevator in ELEVATORS:
            elevator.decrement_cooldown()

        STAIRS.decrement_cooldown()

        simulation_clock += 1

    return simulation_clock, len(ELEVATOR_MOVEMENTS), len(STAIR_MOVEMENTS), ALL_PASSENGERS[:]
    
def get_stats():
    simulation_clock, num_elevator_movements, num_stair_movements, passengers = run_simulation()

    elevator_movements_per_passenger = num_elevator_movements / TOTAL_PASSENGERS
    stair_movements_per_passenger = num_stair_movements / TOTAL_PASSENGERS
    average_time_taken_per_passenger = sum([p.get_duration() for p in passengers]) / TOTAL_PASSENGERS

    return simulation_clock, num_elevator_movements, num_stair_movements, elevator_movements_per_passenger, stair_movements_per_passenger, average_time_taken_per_passenger

def get_average_stats(num_simulations=100):
    simulation_clocks = []
    num_elevator_movements = []
    num_stair_movements = []
    elevator_movements_per_passenger = []
    stair_movements_per_passenger = []
    average_time_taken_per_passenger = []

    for i in range(num_simulations):
        simulation_clock, num_elevator_movement, num_stair_movement, elevator_movement_per_passenger, stair_movement_per_passenger, average_time_taken = get_stats()

        simulation_clocks.append(simulation_clock)
        num_elevator_movements.append(num_elevator_movement)
        num_stair_movements.append(num_stair_movement)
        elevator_movements_per_passenger.append(elevator_movement_per_passenger)
        stair_movements_per_passenger.append(stair_movement_per_passenger)
        average_time_taken_per_passenger.append(average_time_taken)

    return sum(simulation_clocks) / num_simulations, sum(num_elevator_movements) / num_simulations, sum(num_stair_movements) / num_simulations, sum(elevator_movements_per_passenger) / num_simulations, sum(stair_movements_per_passenger) / num_simulations, sum(average_time_taken_per_passenger) / num_simulations

if __name__ == "__main__":
    simulation_clock_graph = []
    num_elevator_movements_graph = []
    num_stair_movements_graph = []
    elevator_movements_per_passenger_graph = []
    stair_movements_per_passenger_graph = []
    average_time_taken_per_passenger_graph = []

    value_range = (1, 10)
    for i in range(*value_range):
        print(f"Percetage complete: {i/value_range[1]*100}%")
        TOTAL_ELEVATORS = i

        average_simulation_clock, \
            average_num_elevator_movements, \
            average_num_stair_movements, average_elevator_movements_per_passenger, \
            average_stair_movements_per_passenger, \
            average_average_time_taken_per_passenger = get_average_stats( num_simulations=70 )

        simulation_clock_graph.append(average_simulation_clock)
        num_elevator_movements_graph.append(average_num_elevator_movements)
        num_stair_movements_graph.append(average_num_stair_movements)
        elevator_movements_per_passenger_graph.append(average_elevator_movements_per_passenger)
        stair_movements_per_passenger_graph.append(average_stair_movements_per_passenger)
        average_time_taken_per_passenger_graph.append(average_average_time_taken_per_passenger)

    import matplotlib.pyplot as plt

    topic = "No. of Elevators"

    # create subplots
    fig, axs = plt.subplots(2, 2)

    label_size = 8

    # plot simulation clock
    axs[0, 0].plot(range(*value_range), simulation_clock_graph)
    axs[0, 0].set_title(f'Simulation Time Elapsed (s) vs {topic}')
    # Add x and y labels
    axs[0, 0].set_xlabel(topic, fontsize= label_size)
    axs[0, 0].set_ylabel('Simulation Time Elapsed (s)', fontsize= label_size)

    # plot average time taken per passenger
    axs[0, 1].plot(range(*value_range), average_time_taken_per_passenger_graph)
    axs[0, 1].set_title(f'Average Time Taken per Passenger (s) vs {topic}')
    # Add x and y labels
    axs[0, 1].set_xlabel(topic , fontsize= label_size)
    axs[0, 1].set_ylabel('Average Time Taken per Passenger (s)' , fontsize= label_size)

    # set spacing between subplots for extra space
    plt.tight_layout()
    
    print(simulation_clock_graph)
    print(average_time_taken_per_passenger_graph)
    plt.show()

