## FOR TESTING StepParse CLASS AND StrEmbed


from step_parse_5_4 import StepParse
# import networkx as nx
# from scipy.special import comb
# import numpy as np
# import matplotlib.pyplot as plt

ass = StepParse()
# ass.load_step('5 parts_{3,1},1.STEP')
ass.load_step('Torch Assembly.STEP')
# # ass.load_step('cakestep.stp')
ass.create_tree()

# ass.set_node_positions()

# ass.remove_redundants()

ass.add_nodes_from([100*el for el in range(10)])

upper = 10
new_edges = [(upper, 1000*(el+1)) for el in range(10)]

ass2 = ass.copy()
ass2.remove_node(5)

# n = 2
# ass2.remove_edges_from(list(ass2.edges)[:n])

ass2.add_edges_from(new_edges)

# paths, cost_nx, cost, node_edits, edge_edits = StepParse.Reconcile(ass,ass2)

ass2.add_edge(ass.get_root(), 100)

# for node in ass2.nodes():
    



    









