# HR 19/08/2019 to 10/12/2019
# Added all extra code I've done up to this point

# TH: I am using this to turn the script into a module file to make it useable else where
# We can add functionally as new things are made.

# HR July 2019
# To parse STEP file

### ---
# HR 12/12/2019 onwards
# Version 5.2
### ---

### ---
# HR 23/03/2020 onwards
# Version 5.3
### ---
# Removed treelib entirely, now using networkx for all operations
# A lot of old functionality replaced with simpler networkx methods



# Ordered dictionary
from collections import OrderedDict as odict

# Regular expression module
import re

# Natural Language Toolkit module, for Levenshtein distance
import nltk

import numpy as np
from scipy.special import comb
# from math import log

# # For powerset construction
# from itertools import chain, combinations

# def powerset(iterable):
#     "e.g. powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
#     s = list(iterable)
#     return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

# Import networkx for plotting lattice
import networkx as nx

#TH: useful for working with files
import os

# HR 10/7/20 All python-occ imports for 3D viewer
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Solid, TopoDS_Compound
# from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
# from OCC.Core.StlAPI import stlapi_Read, StlAPI_Writer
# from OCC.Core.BRep import BRep_Builder
# from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Pnt2d
# from OCC.Core.Bnd import Bnd_Box2d
# from OCC.Core.TopoDS import TopoDS_Compound
# from OCC.Core.IGESControl import IGESControl_Reader, IGESControl_Writer
# from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
# from OCC.Core.Interface import Interface_Static_SetCVal
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool)
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# from OCC.Extend.TopologyUtils import (discretize_edge, get_sorted_hlr_edges,
                                      # list_of_shapes_to_compound)



class StepParse(nx.DiGraph):

    # Override constructor to add part_level
    def __init__(self, *args, **kwargs):

           super().__init__(*args, **kwargs)
           self.part_level = 1
           self.topo_types = (TopoDS_Solid, TopoDS_Compound)



    # OVERRIDDEN METHODS TO ADD LABELS TO NODES WHEN CREATED
    # ---
    # Alternatively can use "set_all_labels" method below



    # # Overridden to add label to node upon creation
    # def add_node(self, node, **attr):
    #     super().add_node(node, **attr)
    #     self.nodes[node]['label'] = node
    #     # print('Adding node {} via "add_node"'.format(node))



    # # Overridden to add label to node upon creation
    # # as "add_edge" creates nodes if they don't already exist
    # def add_edge(self, node1, node2, **attr):
    #     super().add_edge(node1, node2, **attr)
    #     self.nodes[node1]['label'] = node1
    #     self.nodes[node2]['label'] = node2
    #     # print('Adding edge {} via "add_edge"'.format((node1, node2)))



    # # Overridden to add label to node upon creation
    # # Grab node list before invoking super().add_nodes_from as produces generator
    # def add_nodes_from(self, nodes_for_adding, **attr):
    #     node_list = [el[0] for el in list(nodes_for_adding)]
    #     print('Node list: ', node_list)
    #     super().add_nodes_from(node_list, **attr)
    #     for node in node_list:
    #         self.nodes[node]['label'] = node
    #         print('Adding label to node ', node)
    #     # print('Adding nodes {} via "add_nodes_from"'.format(node_list))



    # # Overridden to add label to node upon creation
    # # Grab node list before invoking super().add_edges_from as produces generator
    # def add_edges_from(self, ebunch_to_add, **attr):
    #     edge_list = [el for el in list(ebunch_to_add)]
    #     print('Edge list: ', edge_list)
    #     super().add_edges_from(edge_list, **attr)
    #     print('Edge list: ', edge_list)
    #     for edge in edge_list:
    #         self.nodes[edge[0]]['label'] = edge[0]
    #         self.nodes[edge[1]]['label'] = edge[1]
    #         print('Adding labels to nodes {} via "add_edges_from"'.format(edge))
    #     # print('Adding edges {} via "add_edges_from"'.format(edge_list))



    # Set node and edge labels to node identifier
    # For use later in tree reconciliation
    def set_all_tags(self):
        for node in self.nodes:
            if not 'tag' in self.nodes[node].keys():
                self.nodes[node]['tag'] = node
        for edge in self.edges:
            if not 'tag' in self.edges[edge].keys():
                self.edges[edge]['tag'] = edge



    def load_step(self, step_filename):

        self.nauo_lines          = []
        self.prod_def_lines      = []
        self.prod_def_form_lines = []
        self.prod_lines          = []
        self.filename = os.path.splitext(step_filename)[0]



        line_hold = ''
        line_type = ''

        # Find all search lines
        with open(step_filename) as f:
            for line in f:
                # TH: read pointer of lines as they are read, so if the file has text wrap it will notice and add it to the following lines
                index = re.search("#(.*)=", line)
                if index:
                    # TH: if not none then it is the start of a line so read it
                    # want to hold line until it has checked next line
                    # if next line is a new indexed line then save previous line
                    if line_hold:
                        if line_type == 'nauo':
                            self.nauo_lines.append(line_hold)
                        elif line_type == 'prod_def':
                            self.prod_def_lines.append(line_hold)
                        elif line_type == 'prod_def_form':
                            self.prod_def_form_lines.append(line_hold)
                        elif line_type == 'prod':
                            self.prod_lines.append(line_hold)
                        line_hold = ''
                        line_type = ''



                    prev_index = True  # TH remember previous line had an index
                    if 'NEXT_ASSEMBLY_USAGE_OCCURRENCE' in line:
                        line_hold = line.rstrip()
                        line_type = 'nauo'
                    elif ('PRODUCT_DEFINITION ' in line or 'PRODUCT_DEFINITION(' in line):
                        line_hold = line.rstrip()
                        line_type = 'prod_def'
                    elif 'PRODUCT_DEFINITION_FORMATION' in line:
                        line_hold = line.rstrip()
                        line_type = 'prod_def_form'
                    elif ('PRODUCT ' in line or 'PRODUCT(' in line):
                        line_hold = line.rstrip()
                        line_type = 'prod'
                else:
                    prev_index = False
                    #TH: if end of file and previous line was held
                    if 'ENDSEC;' in line:
                        if line_hold:
                            if line_type == 'nauo':
                                self.nauo_lines.append(line_hold)
                            elif line_type == 'prod_def':
                                self.prod_def_lines.append(line_hold)
                            elif line_type == 'prod_def_form':
                                self.prod_def_form_lines.append(line_hold)
                            elif line_type == 'prod':
                                self.prod_lines.append(line_hold)
                            line_hold = ''
                            line_type = ''
                    else:
                        #TH: if not end of file
                        line_hold = line_hold + line.rstrip()



        self.nauo_refs          = []
        self.prod_def_refs      = []
        self.prod_def_form_refs = []
        self.prod_refs          = []

        # TH: added 'replace(","," ").' to replace ',' with a space to make the spilt easier if there are not spaces inbetween the words'
        # Find all (# hashed) line references and product names
        # TH: it might be worth finding a different way of extracting data we do want rather than fixes to get rid of the data we don't
        for j,el_ in enumerate(self.nauo_lines):
            self.nauo_refs.append([el.rstrip(',')          for el in el_.replace(","," ").replace("="," ").replace(")"," ").split()                  if el.startswith('#')])
        for j,el_ in enumerate(self.prod_def_lines):
            self.prod_def_refs.append([el.rstrip(',')      for el in el_.replace(","," ").replace("="," ").replace(")"," ").split()                  if el.startswith('#')])
        for j,el_ in enumerate(self.prod_def_form_lines):
            self.prod_def_form_refs.append([el.rstrip(',') for el in el_.replace(","," ").replace("="," ").replace(")"," ").split()                  if el.startswith('#')])
        for j,el_ in enumerate(self.prod_lines):
            self.prod_refs.append([el.strip(',')           for el in el_.replace(","," ").replace("("," ").replace(")"," ").replace("="," ").split() if el.startswith('#')])
            self.prod_refs[j].append(el_.split("'")[1])

        # Get first two items in each sublist (as third is shape ref)
        #
        # First item is 'PRODUCT_DEFINITION' ref
        # Second item is 'PRODUCT_DEFINITION_FORMATION <etc>' ref
        self.prod_all_refs = [el[:2] for el in self.prod_def_refs]

        # Match up all references down to level of product name
        for j,el_ in enumerate(self.prod_all_refs):

            # Add 'PRODUCT_DEFINITION' ref
            for i,el in enumerate(self.prod_def_form_refs):
                if el[0] == el_[1]:
                    el_.append(el[1])
                    break

            # Add names from 'PRODUCT_DEFINITION' lines
            for i,el in enumerate(self.prod_refs):
                if el[0] == el_[2]:
                    el_.append(el[2])
                    break



        # Find all parent and child relationships (3rd and 2nd item in each sublist)
        self.parent_refs = [el[1] for el in self.nauo_refs]
        self.child_refs  = [el[2] for el in self.nauo_refs]

        # Find distinct parts and assemblies via set operations; returns list, so no repetition of items
        self.all_type_refs  = set(self.child_refs) | set(self.parent_refs)
        self.ass_type_refs  = set(self.parent_refs)
        self.part_type_refs = set(self.child_refs) - set(self.parent_refs)
        #TH: find root node
        self.root_type_refs = set(self.parent_refs) - set(self.child_refs)

        # Create simple parts dictionary (ref + label)
        # print(self.prod_all_refs)
        self.part_dict     = {el[0]:el[3] for el in self.prod_all_refs}

        # print('Parent:   ', self.parent_refs)
        # print('Children: ', self.child_refs)



    def create_tree(self):

        #TH: create tree diagram in newick format
        #TH: find root node

        #TH: check if there are any parts to make a tree from, if not don't bother
        if self.part_dict == {}:
            return

        root_node_ref = list(self.root_type_refs)[0]

        starter = 0
        self.add_node(starter)

        #TH: created root node now fill in next layer
        #TH: create dict for tree, as each node needs a unique name
        i = [starter] # Iterates through nodes
        self.step_dict = odict()
        self.step_dict[i[0]] = root_node_ref

        def tree_next_layer(self, parent):
            root_node = self.step_dict[i[0]]
            for line in self.nauo_refs:
                if line[1] == root_node:
                    i[0] += 1
                    self.step_dict[i[0]] = str(line[2])
                    self.add_node(i[0])
                    self.add_edge(parent, i[0])
                    tree_next_layer(self, i[0])

        tree_next_layer(self, starter)
        # self.appended = False

        self.remove_redundants()



    def OCC_read_file(self, filename):
        #######################################################################
        ## HR 14/7/20
        ## All python-occ intialisation for 3D view
        ## Adapted from src/Extend/DataExchange.py script from python-occ, here:
        ## https://github.com/tpaviot/pythonocc-core

        # Changed to odict to allow direct mapping to step_dict (see later)
        output_shapes = odict()

        # Create an handle to a document
        doc = TDocStd_Document(TCollection_ExtendedString("pythonocc-doc"))

        # Get root assembly
        shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
        color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())
        #layer_tool = XCAFDoc_DocumentTool_LayerTool(doc.Main())
        #mat_tool = XCAFDoc_DocumentTool_MaterialTool(doc.Main())

        step_reader = STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)
        step_reader.SetGDTMode(True)

        status = step_reader.ReadFile(filename)
        if status == IFSelect_RetDone:
            step_reader.Transfer(doc)
            print('Transfer done')

        locs = []

        def _get_sub_shapes(lab, loc):

            l_subss = TDF_LabelSequence()
            shape_tool.GetSubShapes(lab, l_subss)
            #print("Nb subshapes   :", l_subss.Length())
            l_comps = TDF_LabelSequence()
            shape_tool.GetComponents(lab, l_comps)
            #print("Nb components  :", l_comps.Length())
            #print()
            name = lab.GetLabelName()
            print("Name :", name)

            if shape_tool.IsAssembly(lab):
                l_c = TDF_LabelSequence()
                shape_tool.GetComponents(lab, l_c)
                for i in range(l_c.Length()):
                    label = l_c.Value(i+1)
                    if shape_tool.IsReference(label):
                        label_reference = TDF_Label()
                        shape_tool.GetReferredShape(label, label_reference)
                        loc = shape_tool.GetLocation(label)

                        locs.append(loc)
                        _get_sub_shapes(label_reference, loc)
                        locs.pop()

            elif shape_tool.IsSimpleShape(lab):
                shape = shape_tool.GetShape(lab)

                loc = TopLoc_Location()
                for l in locs:
                    loc = loc.Multiplied(l)

                c = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)  # default color
                colorSet = False
                if (color_tool.GetInstanceColor(shape, 0, c) or
                        color_tool.GetInstanceColor(shape, 1, c) or
                        color_tool.GetInstanceColor(shape, 2, c)):
                    color_tool.SetInstanceColor(shape, 0, c)
                    color_tool.SetInstanceColor(shape, 1, c)
                    color_tool.SetInstanceColor(shape, 2, c)
                    colorSet = True
                    n = c.Name(c.Red(), c.Green(), c.Blue())
                    print('    Instance color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                if not colorSet:
                    if (color_tool.GetColor(lab, 0, c) or
                            color_tool.GetColor(lab, 1, c) or
                            color_tool.GetColor(lab, 2, c)):
                        color_tool.SetInstanceColor(shape, 0, c)
                        color_tool.SetInstanceColor(shape, 1, c)
                        color_tool.SetInstanceColor(shape, 2, c)

                        n = c.Name(c.Red(), c.Green(), c.Blue())
                        print('    Shape color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                shape_disp = BRepBuilderAPI_Transform(shape, loc.Transformation()).Shape()
                if not shape_disp in output_shapes:
                    output_shapes[shape_disp] = [lab.GetLabelName(), c]

                for i in range(l_subss.Length()):
                    lab_subs = l_subss.Value(i+1)
                    shape_sub = shape_tool.GetShape(lab_subs)

                    c = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)  # default color
                    colorSet = False
                    if (color_tool.GetInstanceColor(shape_sub, 0, c) or
                            color_tool.GetInstanceColor(shape_sub, 1, c) or
                            color_tool.GetInstanceColor(shape_sub, 2, c)):
                        color_tool.SetInstanceColor(shape_sub, 0, c)
                        color_tool.SetInstanceColor(shape_sub, 1, c)
                        color_tool.SetInstanceColor(shape_sub, 2, c)
                        colorSet = True
                        n = c.Name(c.Red(), c.Green(), c.Blue())
                        print('    Instance color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                    if not colorSet:
                        if (color_tool.GetColor(lab_subs, 0, c) or
                                color_tool.GetColor(lab_subs, 1, c) or
                                color_tool.GetColor(lab_subs, 2, c)):
                            color_tool.SetInstanceColor(shape, 0, c)
                            color_tool.SetInstanceColor(shape, 1, c)
                            color_tool.SetInstanceColor(shape, 2, c)

                            n = c.Name(c.Red(), c.Green(), c.Blue())
                            print('    Shape color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())
                    shape_to_disp = BRepBuilderAPI_Transform(shape_sub, loc.Transformation()).Shape()

                    # position the subshape to display
                    if not shape_to_disp in output_shapes:
                        output_shapes[shape_to_disp] = [lab_subs.GetLabelName(), c]



        def _get_shapes():
            labels = TDF_LabelSequence()
            shape_tool.GetFreeShapes(labels)


            print("Number of shapes at root: ", labels.Length())
            for i in range(labels.Length()):
                root_item = labels.Value(i+1)
                print('Root item: ', root_item)
                _get_sub_shapes(root_item, None)

        # HR 15/7/20
        #
        # Want to link existing node IDs from create_tree() with OCC
        # First try: assume file-read order is same for both...
        # ...and also OCC only gets "simple parts", i.e. leaves...
        # ...which is corrected for below
        #
        # MUST CORRECT IN FUTURE TO BE SINGLE FILE-READ METHOD...
        # ...FOR BOTH GRAPH AND OCC/SHAPE DATA

        _get_shapes()
        self.shapes = output_shapes
        # return self.output_shapes
        # Get all TopoDS_Solid objects in OCC dict
        OCC_list  = [k for k in self.shapes.keys() if type(k) in self.topo_types]
        # Get all leaves in step_dict (could also just get list from leaves method)
        tree_list = [k for k in self.step_dict.keys() if k in self.leaves]

        # Map master IDs to OCC objects
        self.OCC_dict = dict(zip(tree_list, OCC_list))
        #######################################################################



    # Remove all single-child sub-assemblies as not compatible with lattice
    def remove_redundants(self, _tree = None):

        # Operate on whole tree by default
        if not _tree:
            _tree = self.nodes

        # Get list of redundant nodes and link past them...
        _to_remove = []
        for _node in _tree:
            if self.out_degree(_node) == 1:
                _parent = self.get_parent(_node)
                _child  = self.get_child(_node)
                # Don't remove if at head of tree (i.e. if in_degree == 0)...
                # ...as Networkx would create new "None" node as parent
                if self.in_degree(_node) != 0:
                    print('Parent/child to add edge b/t: ', _parent, _child)
                    self.add_edge(_parent, _child)
                _to_remove.append(_node)

        # ...then remove in separate loop to avoid list changing size during previous loop
        for _node in _to_remove:
            print('Removing node ', _node)
            self.remove_node(_node)

        # # Check for loose nodes
        # loose_nodes = [node for node in self.nodes if self.out_degree[node] == 0 and self.in_degree[node] == 0]

        # print('Check: loose nodes (i.e. no in or out degree): ', loose_nodes)

        # if not loose_nodes:
        #     print('All redundant (i.e. single-child) sub-assemblies removed...')
        #     print('...as not compatible with lattice representation')
        # else:
        #     print('Some loose nodes remain: redundant sub-assemblies not fully removed')



    # Finds root of graph containing reference node, which is passed for speed;
    # otherwise start with first in node list (as any will do)
    def get_root(self, node = None):

        # root = [el for el in self.nodes if self.in_degree(el) == 0][0]
        # Get random node if none given
        if node is None:
            node = list(self.nodes)[0]

        parent = self.get_parent(node)
        if parent is None:
            return node

        while parent is not None:
            child = parent
            parent = self.get_parent(child)

        return child



    def get_parent(self, node):

        # Get parent of node; return None if parent not present
        parent = [el for el in self.predecessors(node)]
        if parent:
            return parent[-1]
        else:
            return None



    def get_child(self, node):

        # Get (single) child of node; return None if parent not present
        # Best used only when removing redundant (i.e. single-child) subassemblies
        child = [el for el in self.successors(node)]
        if child:
            return child[-1]
        else:
            return None



    @property
    def leaves(self):

        # Get leaf nodes
        leaves = {el for el in self.nodes if self.out_degree(el) == 0}
        return leaves



    def get_node_depth(self, node):

        # Get depth of node(s) from root
        root = self.get_root(node)
        depth = nx.shortest_path_length(self, root, node)
        return depth



    def move_node(self, node, new_parent):

        old_parent = self.get_parent(node)
        self.remove_edge(old_parent, node)
        self.add_edge(new_parent, node)



    def remove_dependants_from(self, nodes):

        if type(nodes) == int:
            nodes = [nodes]

        # Remove dependants from nodes list
        depth_dict = {el:self.get_node_depth(el) for el in nodes}
        depth_list = sorted(list(set(depth_dict.values())))

        removed_nodes = []
        for depth in depth_list:
            at_depth    = [k for k,v in depth_dict.items() if v == depth]
            above_depth = [k for k,v in depth_dict.items() if v < depth]
            to_check    = list(set(nodes) - set(removed_nodes) - set(at_depth) - set(above_depth))
            for node in at_depth:
                for el in to_check:
                    if nx.has_path(self, node, el):
                        removed_nodes.append(el)

        retained_nodes = list(set(nodes) - set(removed_nodes))

        print('Descendant nodes: ', removed_nodes)
        print('Retained nodes:   ', retained_nodes)
        return retained_nodes



    # Generate set of parts contained by node(s); node list optional argument
    def set_parts_in(self, _nodes = None):

        # If no nodes passed, default to all nodes in assembly
        if not _nodes:
            _nodes = self.nodes

        # Convert to list if only one item
        if type(_nodes) == int:
            _nodes = [_nodes]

        leaves = self.leaves
        non_leaves = self.nodes - leaves

        # Get all levels, i.e. number of parts (n_p) and assemblies (n_a)...
        # ...contained in each node
        for node in _nodes:
            des_all   = nx.descendants(self, node)
            des_parts = des_all - non_leaves
            n_a = len(des_all) + 1
            n_p = len(des_parts)
            # If 0, change to level of individual part
            if n_p == 0:
                n_p = self.part_level
            self.nodes[node]['n_a'] = n_a
            self.nodes[node]['n_p'] = n_p
            if node in leaves:
                self.nodes[node]['parts'] = {node}
                self.nodes[node]['all']   = {node}
            else:
                self.nodes[node]['parts'] = des_parts
                self.nodes[node]['all']   = des_all



    def set_node_positions(self):

        # Populate set of parts contained by each node
        self.set_parts_in()

        # Generate list of all part levels in nodes
        self.levels_a = set([self.nodes[el]['n_a'] for el in self.nodes])
        self.levels_a.remove(self.part_level)
        self.levels_p = set([self.nodes[el]['n_p'] for el in self.nodes])
        # self.levels_p.remove(self.part_level)

        self.levels_p_sorted = sorted(list(self.levels_p))
        self.levels_a_sorted = sorted(list(self.levels_a))

        self.levels_dict = {}
        for level in self.levels_p:
            self.levels_dict[level] = []

        nodes = self.nodes
        for node in nodes:
            level = nodes[node]['n_p']
            self.levels_dict[level].append(node)

        # Get total number of combinations, S, for each part level
        _len = len(self.leaves)
        self.S_p = {el:comb(_len, el) for el in range(int(_len+1))}

        # Map leaves to combinatorial numbering starting at 1
        self.leaf_dict = {}
        self.leaf_dict_inv = {}
        leaves = list(self.leaves)
        for i in range(_len):
            leaf = leaves[i]
            self.leaf_dict[leaf] = i+1
            self.leaf_dict_inv[i+1] = leaf

        # for node in ass.nodes:
        #     n_p = ass.nodes[node]['n_p']
        #     comb_ = comb(S_p[n_p], n_p)
        #     ass.nodes[node]['x_comb'] = np.log(comb_)

        for k,v in self.levels_dict.items():
            S = self.S_p[k]
            for node in v:
                parts = [self.leaf_dict[el] for el in self.nodes[node]['parts']]
                rank = self.rank(parts)
                # print('Node, rank = ', node, rank)
                if S <= 1:
                    self.nodes[node]['x'] = 0
                else:
                    self.nodes[node]['x'] = ((rank/(S-1))-0.5)*np.log(S-1)

        print('Finished setting node positions')



    def get_positions(self):

        # Get dict of positions for "pos" in nx.draw
        x = nx.get_node_attributes(self, 'x')
        y = nx.get_node_attributes(self, 'n_p')
        # pos_nodes = {k:(x[k], y[k]) for k in self.nodes}

        pos_nodes = {}
        for k in self.nodes:
            try:
                pos_nodes[k] = (x[k], y[k])
            except:
                print('Position not found for node: ', k)
                print('Node data: ', self.nodes[k])



        pos_edges = {}
        for u,v in self.edges:
            _u = self.nodes[u]
            _v = self.nodes[v]
            pos_edges[(u,v)] = [(_u['x'], _u['n_p']), (_v['x'], _v['n_p'])]

        # pos = [(self.nodes[el]['x'], self.nodes[el]['n_p']) for el in self.nodes]
        return (pos_nodes, pos_edges)



    ## HR 12/05/20
    ## -----------
    ## All combinatorial ranking/unranking methods here
    ## -----------



    def stirling_ln(self, n):
        # if n in (0, 1):
        #     _result = 0
        #     return _result

        _result = (n+0.5)*np.log(n) - n + np.log(np.sqrt(2*np.pi)) + (1/(12*n)) - (1/(360*n**3)) + (1/(1260*n**5)) - (1/(1680*n**7))
        # _result = (n+0.5)*np.log(n) - n + np.log(np.sqrt(2*np.pi)) + (1/(12*n))
        # print('Log Stirling approx. for n = ', n, ': ', _result)
        return _result



    def comb_ln(self, n, k):
        _result = self.stirling_ln(n) - self.stirling_ln(k) - self.stirling_ln(n-k)
        # print('Log combination approx. for (n, k) = ', (n,k), ': ', _result)
        return _result



    # RANKING OF COMBINATION
    # --
    # Find position (rank) of combination in ordered list of all combinations
    # Items list argument consists of zero-based indices
    # --
    def rank(self, items):

        if not items:
            print('Item list empty or not conditioned: returning None')
            return None

        if 0 in items:
            print('Item list contains 0 element: returning None')
            return None

        if not all(isinstance(item, int) for item in items):
            print('One or more non-integers present in item list: returning None')
            return None

        if len(items) != len(set(items)):
            print('Item list contains duplicate(s): returning None')
            return None

        # if len(items) == 1:
        #     items = [items]

        if len(items) > 1:
            items.sort()

        _rank = 0
        items.sort()
        for i, item in enumerate(items):
            _comb = comb(item-1, i+1)
            _rank += _comb

        return _rank



    # UNRANKING OF COMBINATORIAL INDEX
    # --
    # Find combination of nCk items at position "rank" in ordered list of all combinations
    # Ordering is zero-based
    # --
    def unrank(self, n, k, rank):

        # Check all arguments (except "self") are integers
        args_ = {k:v for k,v in locals().items() if k != 'self'}
        # print(['{} = {}'.format(k,v) for k,v in locals().items() if k != 'self'])
        print(['{} = {}'.format(k,v) for k,v in args_.items()])

        if not all(isinstance(el, (int, float)) for el in args_.values()):
        # if not all(isinstance(el, int) for el in (n, k, rank)):
            print('Not all arguments are integers: returning None')
            return None

        if rank < 0:
            print('Rank must be b/t 0 and (nCk-1); returning None')
            return None

        # Increase by one to satisfy zero-based indexing; check/resolve in future
        rank += 1

        # Check whether "rank" within nCk
        max_ln = self.comb_ln(n, k)

        # Check whether rank is massive; if so, calculate log(x) = log(x/a) + log(a)
        # where x = rank and a = chop
        # as np.log can't handle large numbers (actually x > 1e308 or so)
        chop = 1
        if rank > 1e100:
            print('Chopping rank for log')
            chop = 1000

        log_  = np.log(chop) + np.log(rank/chop)
        print('log_  = ', log_)

        if log_ > max_ln:
            print('Rank outside nCk bounds: returning None')
            return None

        # Convert to float to allow large n values
        rank = float(rank)



        # Optimisation as (n+1 k) = (n k)*(n+1)/(n+1-m)
        def next_comb(n_, k_, _comb):
            _next = _comb*(n_+1)/(n_+1-k_)
            return _next

        # Using scipy comb; can optimise in future, e.g. with Stirling approx.
        def comb_(n_, k_):
            _result = comb(n_, k_)
            return _result



        # MAIN ALGORITHM
        # ---
        _items = []
        remainder = rank

        # print('Starting, k = {}'.format(k))
        # Find each of k items
        for i in range(k, 0, -1):

            # Initialise at 1 as kCk = 1 for all k
            c_i = 1
            count = i

            if c_i >= remainder:
                last_comb = c_i
            else:
                while c_i < remainder:
                    last_comb = c_i
                    c_i = next_comb(count, i, c_i)
                    count += 1

            # print('i   = {}'.format(i))
            # print('c_i = {}\n'.format(c_i))
            _items.append(count)
            remainder -= last_comb

        return _items


    def similarity(self, str1, str2):

        _lev_dist  = nltk.edit_distance(str1, str2)
        _sim = 1 - _lev_dist/max(len(str1), len(str2))

        return _lev_dist, _sim



    ## ------------------------------------------------------------------------
    ## TREE RECONCILIATION
    ## HR 3/6/20
    ## Based on Networkx "optimal_edit_paths" method

    # a1 and a2 are assemblies 1 and 2
    # Call as "paths, cost = StepParse.Reconcile(a1, a2)"

    @classmethod
    def Reconcile(self, a1, a2, lev_tol = 0.1):

        # ---------------------------------------------------------------------
        # STAGE 1: MAP NODES/EDGES B/T THE TWO ASSEMBLIES

        # Currently done simply via tags
        # More sophisticated metrics to be implemented in future

        # Method of assembly class (StepParse) to set item tags to their IDs
        a1.set_all_tags()
        a2.set_all_tags()

        # for a in [a1, a2]:

        #     print('\nleaves:', a.leaves, '\n')
        #     for node in a.nodes:
        #         print('node ', node, 'tag: ', a.nodes[node]['tag'])
        #     print('\n')
        #     for u,v in a.edges:
        #         print('edge ', u,v,  'tag: ', a.edges[(u,v)]['tag'])
        #     print('\n')



        def similarity(str1, str2):

            _lev_dist  = nltk.edit_distance(str1, str2)
            _sim = 1 - _lev_dist/max(len(str1), len(str2))

            return _lev_dist, _sim



        def remove_special_chars(_str):

            # Strip out special characters
            _str = re.sub('[!@#$_]', '', _str)

            return _str



        # Comparing nodes directly gives equality simply if both are NX nodes...
        # ...i.e. same object type...
        # ---
        # ..so equality in this context defined as having same tags...
        # ...as cannot compare node IDs directly with Networkx
        def return_eq(item1, item2):

            _eq = False

            tag1 = item1['tag']
            tag2 = item2['tag']

            # 1. Simple equality test based on tags (which are just IDs copied to "tag" field)...
            _eq = tag1 == tag2
            if _eq:
                print('Mapped ', tag1, 'to ', tag2)

            # # 2. ...then do test based on parts contained by nodes...
            # if tag1 and tag2 in (a1.nodes or a2.nodes) and not _eq:
            #     try:
            #         _eq = item1['parts'] == item2['parts']
            #     except:
            #         pass

            # # 3. ...then do test based on Levenshtein distance b/t items, if leaves
            # if not _eq and (tag1 and tag2 in (a1.leaves or a2.leaves)):

            #     tag1_ = remove_special_chars(tag1)
            #     tag2_ = remove_special_chars(tag2)

            #     try:
            #         dist = similarity(tag1_, tag2_)
            #         _eq  = dist < lev_tol
            #     except:
            #         pass

            # if _eq:
            #     print('Nodes/edges mapped:     ', tag1, tag2)
            # else:
            #     pass

            return _eq
            # return item1 == item2




        def MyReconcile(a1, a2, node_match = None, edge_match = None):

            a1.set_all_tags()
            a2.set_all_tags()

            n1 = set(a1.nodes)
            n2 = set(a2.nodes)
            e1 = set(a1.edges)
            e2 = set(a2.edges)

            node_deletions = []
            node_additions = []
            edge_deletions = []
            edge_additions = []

            # Find additions and deletions by set difference (relative complement)
            #
            for _node in n1 - n2:
                node_deletions.append((_node, None))
            print('Node deletions: ', node_deletions)

            for _node in n2 - n1:
                node_additions.append((None, _node))
            print('Node deletions: ', node_additions)

            for _edge in e1 - e2:
                edge_deletions.append((_edge, None))
            print('Edge deletions: ', edge_deletions)

            for _edge in e2 - e1:
                edge_additions.append((None, _edge))
            print('Edge additions: ', edge_additions)



            paths = [list(set(node_deletions + node_additions)), list(set(edge_deletions + edge_additions))]

            cost = len(node_deletions) + len(node_additions) + len(edge_deletions) + len(edge_additions)

            return paths, cost


        # ---------------------------------------------------------------------
        # STAGE 2: FIND EDIT PATHS VIA NETWORKX AND GENERATE REPORT

        # paths, cost_nx = nx.optimal_edit_paths(a1, a2, node_match = return_eq, edge_match = return_eq)
        # paths = paths[0]

        paths, cost = MyReconcile(a1, a2, node_match = return_eq, edge_match = return_eq)

        node_edits = [el for el in paths[0] if el[0] != el[1]]
        edge_edits = [el for el in paths[1] if el[0] != el[1]]
        cost_from_edits = len(node_edits) + len(edge_edits)

        print('Node edits: {}\nEdge edits: {}\nTotal cost (Networkx): {}\nTotal cost (no. of edits): {}'.format(
            node_edits, edge_edits, cost, cost_from_edits))

        return paths, cost, cost_from_edits, node_edits, edge_edits


    ## ------------------------------------------------------------------------
