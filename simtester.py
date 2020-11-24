# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 13:57:19 2020

@author: prehr
"""

from StrEmbed_5_5 import MyParse
import nltk
import networkx as nx

def similarity(str1, str2):
    _lev_dist  = nltk.edit_distance(str1, str2)
    _sim = 1 - _lev_dist/max(len(str1), len(str2))
    # print('L, S:', _lev_dist, _sim)
    return _lev_dist, _sim


a1 = MyParse()
a2 = MyParse()

# _file = 'Torch Assembly.STEP'
# # _file = 'PARKING_TROLLEY.STEP'
# a1.load_step(_file)
# a2.load_step(_file)

# a1.create_tree()
# a2.create_tree()

# new_id = max(a2.nodes)+1
# a2.add_node(new_id, 'Hi', 'Hello')
# a2.add_edge(max(a2.nodes), new_id)

# _map = {}
# for node1 in a1.nodes:
#     for node2 in a2.nodes:
#         _map[(node1, node2)] = similarity(a1.nodes[node1]['label'], a2.nodes[node2]['label'])

# _g = nx.compose(a1,a2)
# print('Nodes:', _g.nodes)
# print('Edges:', _g.edges)

a1.add_node(0,0,0)
a1.add_node(1,1,1)
a1.add_node(2,2,2)
a1.add_node(3,3,3)
a1.add_node(4,4,4)

a1.add_edge(0,1)
a1.add_edge(0,2)
a1.add_edge(2,3)
a1.add_edge(2,4)



a2.add_node(-1,-1,-1)
a2.add_node(0,0,0)
a2.add_node(1,1,1)
a2.add_node(2,2,2)
a2.add_node(3,3,3)
a2.add_node(4,4,4)

a2.add_edge(-1,0)
a2.add_edge(0,1)
a2.add_edge(0,2)
a2.add_edge(1,3)
a2.add_edge(2,4)

