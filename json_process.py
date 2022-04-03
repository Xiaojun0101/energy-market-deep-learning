import json
import numpy as np
import matplotlib.pyplot as plt


# Opening JSON file
f = open('result_Simple Shadow SimpleMarket-v00 .json')

# returns JSON object as
# a dictionary
data = json.load(f)

# Iterating through the json
# list
print(len(data['timeseries']['epoch_reward']['data']))
'''for i in data['timeseries']['epoch_reward']['data']:
    print(i)'''

# Closing file
f.close()


y = data['timeseries']['epoch_reward']['data'][:-10]
print(len(y))
x = np.arange(0, len(y))
plt.plot(x,y)
plt.ylabel('Reward ($)')
plt.xlabel('Training Episode')
plt.show()

'''y1 = data['timeseries']['epoch_reward']['data'][-10:]
x1 = np.arange(0, 10)
plt.plot(x1,y1)
plt.ylabel('Reward ($)')
plt.xlabel('Testing Episode')
plt.show()'''
