# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 10:32:48 2020

@author: prehr
"""

from step_parse_5_5 import StepParse
import time

a1 = StepParse()
a2 = StepParse()

# file = 'PARKING_TROLLEY.STEP'
# file = 'Torch Assembly.STEP'
# file = 'cakestep.stp'

# file1 = 'PARKING_TROLLEY.STEP'
file1 = 'Torch Assembly.STEP'
file2 = 'Torch (with all four bulbs).STEP'
# file1 = 'cakestep.stp'



print('Loading files...\n\n')
a1.load_step(file1)
a2.load_step(file2)

a1.create_tree()
a2.create_tree()

print('Loaded files!\n\n')



a1.remove_node(12)
a1.add_node(1000, label = 'what', text = 'what')
a1.add_edge(15,1000)

a2.add_node(2000, label = 'hello', text = 'hello')
a2.add_node(3000, label = 'why', text = 'how')
a2.add_edge(6,2000)
a2.add_edge(6,3000)

a1.remove_redundants()
a2.remove_redundants()

results = StepParse.map_nodes(a1,a2)



