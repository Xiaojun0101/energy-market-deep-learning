"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/sutton/book/code/pole.c
permalink: https://perma.cc/C9ZM-652R
"""

import math
import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
from marketsim.logbook.logbook import logbook
from market_config import params as market_config

from marketsim.io.clients.asyncclient import AsyncClient

class SimpleMarket(gym.Env):
    """
    
    """
    
    metadata = {
        'render.modes': ['human'],
        
    }

    def __init__(self):

        # Define
        obs_high = [
                            300, #demand
                            300, #available MW
                            market_config['MAX_PRICE'],  # Last Price
                            market_config['MAX_PRICE'],  # my_price
                            market_config['MAX_PRICE'],  #second paticipants price
                            market_config['MAX_PRICE'],  #third paticipants price
                        ]
        obs_low = [
                            0, #demand
                            0, #available MW
                            0,
                            4,
                            4,
                            4,
                        ]
        obs_high = np.array(obs_high)
        obs_low = np.array(obs_low)
        print('Obs High:', obs_high)
        print('Obs Low:', obs_low)
        # self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high )

        
        self.action_space = spaces.Discrete(10)
        self.seed()
        self.viewer = None
        self.state = np.array(obs_low)
        self._state_dict = None
        self.next_state = None

        self.steps_beyond_done = None

        # Need a way to assign or find id.
        #self.id = 3
        #self.io = AsyncClient(self.id)
        #self.label = 'Bayswater'
        self.total_steps = 0

        self.epoch_reward = 0
        self.last_action = 0
        #cost = $/kwh
        self.cost = {'Nyngan':3, 'Bayswater':4, 'Moree':5}
        self.quantity = {'Nyngan':95, 'Bayswater':100, 'Moree':105}

    def connect(self, participant_name, id_no):
        print("Connecting as ", participant_name, id_no)
        self.id = id_no
        self.label = participant_name
        self.io = AsyncClient(self.id)

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        self.total_steps += 1
        # self.state = (x,x_dot,theta,theta_dot)
        # print("Action:", action)
        self.last_action = action

        print('label is', self.label)
        if self.next_state is not None and self.label == 'Moree':
            self.quantity[self.label] = self.next_state[0] - 100 - 95

        data = {
                'id': self.id,
                'label':self.label,
                'bids' : [
                    [int(action), self.quantity[self.label]],
                ],
            }
        reply = self.io.send(data)
        
        self._state_dict = reply

        amount_dispatched = 0 if self.label not in reply['dispatch'] else float(reply['dispatch'][self.label])
        #print('reply bids information', reply['all_bids'])
        my_price = reply['all_bids'][self.label][0]['price']
        other_paticipants_bids = []
        for key,val in reply['all_bids'].items():
            if key != self.label:
                temp_bids = val[0]
                other_paticipants_bids.append(temp_bids['price'])
        second_participant = other_paticipants_bids[0]
        third_participant = other_paticipants_bids[1]
        #print('other participants price', second_participant, third_participant)

        # state should be a tuple of vals. 
        #next_state = (reply['next_demand'],10)
        next_state = [
            int(reply['next_demand']) if market_config['SHOW_NEXT_DEMAND'] else 0, #Next Demand
            int(amount_dispatched), #Amount Dispatched
            int(reply['price']), # Last clearing Price,
            int(my_price),
            int(second_participant),
            int(third_participant),
        ]
        #print(np.shape(next_state))
        self.next_state = next_state
        
        
        # Reward is product of dispatched and 
        #reward = amount_dispatched * (my_price - self.cost)
        reward = amount_dispatched * int(reply['price']) - self.quantity[self.label] * self.cost[self.label]
        
        self.epoch_reward += reward
        # Every day, start a new epoch.
        done = False
        if self.total_steps % 48 == 0:

            done = True

        # the next next_state, the reward for the last action, the current next_state, a boolean representing whether the current episode of our model is done and some additional info on our problem
        return np.array(next_state), reward, done, {}

    def reset(self):
        #self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(2,))
        # print(str({"metric": "epoch_reward", "value": self.epoch_reward, "step": self.total_steps}))
        print('{"metric": "epoch_reward", "value": '+str(self.epoch_reward)+', "step":'+str(self.total_steps)+'}')
        logbook().record_epoch_reward(self.epoch_reward)
        self.epoch_reward = 0
        return np.array(self.state)

    def render(self, mode='human'):
        # Log bid/value in Floydhub
        # print('{"metric": "bid", "value": '+str(self.last_action)+', "step":'+str(self.total_steps)+'}')
        
        # Log in logbook suite
        logbook().record_price(self._state_dict['price'], self.total_steps)
        logbook().record_demand(self._state_dict['demand'], self.total_steps)
        # Log bidstack in logbook suite.
        print('bid in env', self._state_dict['all_bids'])
        for bid in self._state_dict['all_bids'].values():
            print('bid in env', bid)
            val = bid[0]
            logbook().record_bid(val['label'], val['price'], val['quantity'], self.total_steps)
        return None

    def close(self):
        pass