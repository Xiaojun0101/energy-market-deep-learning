import numpy as np
import gym
import sys
import marketsim.openai.envs
from market_config import params as market_config
from marketsim.logbook.logbook import logbook

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
#from keras.optimizers import Adam
from keras.optimizers import adam_v2
#from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory

import pendulum

# Make sure that a participant name is provided.
if len(sys.argv) < 2:
    print('Error: Participant name not provided - usage: python dqn_adversarial.py <participant_name>')
    print('Possible participant names:')
    [print(" -"+p) for p in market_config['PARTICIPANTS']]
    sys.exit()
# Make sure that the participant name is one of hte allowed ones.
elif sys.argv[1] not in market_config['PARTICIPANTS']:
    print('Error: Participant not in list of possible participants. Must be one of:')
    [print(" -"+p) for p in market_config['PARTICIPANTS']]
    sys.exit()
else:
    participant_name = sys.argv[1]

# ENV_NAME = 'CartPole-v0'
ENV_NAME2 = 'SimpleMarket-v0'
ENV_NAME = 'SimpleMarket-v02'
extra_label = "Simple Shadow2"

logbook().set_label(extra_label+" "+ENV_NAME+" "+pendulum.now().format('ddd D/M HH:mm'))
logbook().record_metadata('Environment', ENV_NAME)
logbook().record_metadata('datetime', pendulum.now().isoformat())
for param in market_config:
    logbook().record_metadata('Market: '+param, market_config[param])

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME2)
env.connect(participant_name, market_config['PARTICIPANTS'].index(participant_name))
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n
logbook().record_hyperparameter('action_space', str(env.action_space))
logbook().record_hyperparameter('action_space_size', str(env.action_space.n))

# Next, we build a very simple model.
model = Sequential()
model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(nb_actions))
model.add(Activation('linear'))
print("MODEL SUMMARY",model.summary())

logbook().record_model_json(model.to_json())


# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=50000, window_length=1)
#policy = BoltzmannQPolicy()
policy = EpsGreedyQPolicy()

dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=100, target_model_update=1e-3, policy=policy)
# Record to logbook
logbook().record_hyperparameter('Agent', str(type(dqn)))
logbook().record_hyperparameter('Memory Type', str(type(memory)))
logbook().record_hyperparameter('Memory Limit', memory.limit)
logbook().record_hyperparameter('Memory Window Length', memory.window_length)
logbook().record_hyperparameter('nb_steps_warmup', dqn.nb_steps_warmup) #info on this parameter here: https://datascience.stackexchange.com/questions/46056/in-keras-library-what-is-the-meaning-of-nb-steps-warmup-in-the-dqnagent-objec
logbook().record_hyperparameter('target_model_update', dqn.target_model_update) #info on this parameter here: https://github.com/keras-rl/keras-rl/issues/55
logbook().record_hyperparameter('nb_actions', nb_actions)
logbook().record_hyperparameter('batch_size', dqn.batch_size) #defaults to 32. Info here: https://radiopaedia.org/articles/batch-size-machine-learning
logbook().record_hyperparameter('gamma', dqn.gamma) #defaults to 0.99. 'Discount rate' according to Advanced Deep Learning with Keras



# dqn.compile(Adam(lr=1e-3), metrics=['mae'])
#learning_rate = 1e-5
learning_rate = 1e-3
dqn.compile(adam_v2.Adam(lr=learning_rate), metrics=['mae'])
logbook().record_hyperparameter('Learning Rate', learning_rate)

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
# dqn.fit(env, nb_steps=50000, visualize=False, verbose=2)
#nb_steps = 500000
nb_steps = 50000
dqn.fit(env, nb_steps=nb_steps, visualize=False, verbose=2)
logbook().record_hyperparameter('nb_steps', nb_steps)

# After training is done, we save the final weights.
dqn.save_weights('dqn_{}_weights.h5f'.format(ENV_NAME), overwrite=True)

# Finally, evaluate our algorithm for 5 episodes.
nb_episodes = 10
logbook().record_metadata('nb_episodes (testing)', nb_episodes)
dqn.test(env, nb_episodes=5, visualize=True)



logbook().record_notes("Testing with 10x more steps (500,000). Learning rate and target model update at 1e-3.")
logbook().submit()