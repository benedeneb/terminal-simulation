import simpy
import random
import itertools
import sys

#################
### Constants ###
#################

# env
YEARS = 1
DAYS = 365 * YEARS # days
HOURS = DAYS * 24 # hours

# ship
NEEDED_VOL = 38000000 * YEARS # Nm^3
SHIP_VOL = 38000 # Nm^3
SHIP_DUR = 45 * 24 # hours
FREQUENCE = 24 // ((NEEDED_VOL // SHIP_VOL) / 365) # hours

# birth
NUMBER_BIRTH = 3 # -
BIRTH_MOORING = 24 # hours
BIRTH_UNMOORING = 24 # hours

#jetty
NUMBER_JETTY = NUMBER_BIRTH #-
JETTY_VOL = 1000 # Nm^3/h
JETTY_DUR = SHIP_VOL // JETTY_VOL # hours

# storage
STORAGE_SIZE = 760000 # Nm^3
STORAGE_LEVEL = STORAGE_SIZE * 0.1 # Nm^3, storage is filled to X % of total capacity at the beginning

# cracker
CRACKER_IN = 750 # Nm^3/h
CRACKER_EFF = 0.5 # -

#################
##### Simpy #####
#################

################################################ ships ##################################################

def ship(name, env, birth, storage):

    # simulate ship starting in australia
    yield env.timeout(SHIP_DUR)

    # request on of the births
    with birth.request() as req:
        yield req

        # simulate mooring time (birth)
        print('%s starting mooring at %.1f' % (name, env.now))
        yield env.timeout(BIRTH_MOORING)

        # simulate unloading by jetty
        print('%s starting unloading at %.1f' % (name, env.now))

        act_vol = SHIP_VOL
        while act_vol > 0:
            if storage.level >= STORAGE_SIZE - JETTY_VOL:
                yield storage.put(JETTY_VOL)
                act_vol -= JETTY_VOL
            else:
                (f"!!!!!Storage full!!!!! - after {env.now//24} days")
            yield env.timeout(1)
            
            print(f"  {name} | + {JETTY_VOL} Nm3, at {env.now}")

        # simulate unmooring time (birth)
        print('%s starting unmooring at %.1f' % (name, env.now))
        yield env.timeout(BIRTH_UNMOORING)

    # simulate ship heading back to australia
    print('%s heading back to australia at %.1f' % (name, env.now))
    yield env.timeout(SHIP_DUR)


def ship_generator(env, birth, storage):
    # generate ships ever x hours
    for i in itertools.count():
        yield env.timeout(FREQUENCE)
        env.process(ship('Ship %d' % i, env, birth, storage))

################################################ cracker ##################################################

def cracker(env, storage):

    print(f"STORAGE | {storage.level}, at {env.now}")
    # check storage level 
    if storage.level > CRACKER_IN:
        yield storage.get(CRACKER_IN)
        yield env.timeout(1)
        print(f"  CRACKER | - {CRACKER_IN} Nm3, at {env.now}")
    else:
        sys.exit(f"!!!!!Storage empty!!!!! - after {env.now//24} days")
    

def cracker_generator(env, storage):
    yield env.timeout(SHIP_DUR + BIRTH_MOORING)
    # generates a cracker input every hour
    for _ in itertools.count():
        yield env.timeout(1)
        env.process(cracker(env, storage))

################################################ main process ##################################################

env = simpy.Environment()
birth = simpy.Resource(env, NUMBER_BIRTH)
storage = simpy.Container(env, STORAGE_SIZE, init = STORAGE_LEVEL)
env.process(ship_generator(env, birth, storage))
env.process(cracker_generator(env, storage))
env.run(until = HOURS)
# Improvements:
# 