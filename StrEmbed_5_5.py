# HR June 2019 onwards
# Version 5 to follow HHC's StrEmbed-4 in Perl
# User interface for lattice-based assembly configurations

### ---
# HR 17/10/19
# Version 5.1 to draw main window as panels within flexgridsizer
# Avoids confusing setup for staticbox + staticboxsizer
### ---

### ---
# HR 12/12/2019 onwards
# Version 5.2
### ---

### BUGS LOG
# 1 // 7/2/20
# Images in selector view does not update when resized until next resize
# e.g. when maximised, images remain small
# FIXED Feb 2020 with CallAfter
# ---
# 2 // 7/2/20
# Image rescaling (via ScaleImage method) may need correction
# Sometimes appears that images overlap border of toggle buttons partly
# ---
# 3 // 6/3/20
# Assembly operation methods (flatten, assemble, etc.) need compressing into fewer methods
# as currently a lot of repeated code

### ---
# HR 23/03/2020 onwards
# Version 5.3
### ---


# WX stuff
import wx
# WX customtreectrl for parts list
import wx.lib.agw.customtreectrl as ctc

# Allows inspection of app elements via Ctrl + Alt + I
# Use InspectableApp() in MainLoop()
# import wx.lib.mixins.inspection as wit
# For scrolled panel
import wx.lib.scrolledpanel as scr

# matplotlib stuff
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

# Ordered dictionary
from collections import OrderedDict as odict

# OS operations for exception-free file checking
import os.path

# Import networkx for plotting lattice
import networkx as nx

# Gets rid of blurring throughout application by getting DPI info
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except:
    pass

# For STEP import
from step_parse_5_4 import StepParse

# import matplotlib.pyplot as plt
import numpy as np
# from scipy.special import comb


# For 3D CAD viewer based on python-occ
from OCC.Display import OCCViewer
import wxDisplay
from OCC.Core.Quantity import (Quantity_Color, Quantity_NOC_WHITE, Quantity_TOC_RGB)

# from OCC.Extend.DataExchange import read_step_file_with_names_colors



class MyTree(ctc.CustomTreeCtrl):

    def __init__(self, parent, style):
        ctc.CustomTreeCtrl.__init__(self, parent = parent, agwStyle = style)
        self.parent = parent
        self.reverse_sort = False
        self.alphabetical = True



    # Overridden method to allow sorting based on data other than text
    # Can be sorted alphabetically or numerically, and in reverse
    # ---
    # This method is called by sorting methods
    # ---
    # NOTE the functionality necessary for this was added to the wxWidgets / Phoenix Github repo
    # in 2018 in response to issue #774 here: https://github.com/wxWidgets/Phoenix/issues/774
    def OnCompareItems(self, item1, item2):

        if self.alphabetical:
            t1 = self.GetItemText(item1)
            t2 = self.GetItemText(item2)
        else:
            t1 = self.GetPyData(item1)['sort_id']
            t2 = self.GetPyData(item2)['sort_id']
            # print('item 1 PyData = ', t1)
            # print('item 2 PyData = ', t2)

        if self.reverse_sort:
            reverse = -1
        else:
            reverse = 1

        if t1 < t2: return -1*reverse
        if t1 == t2: return 0
        return 1*reverse



    def GetAncestors(self, item):

        # Get all children of CTC item recursively
        # ---
        # MUST create shallow copy of children here to avoid strange behaviour
        # According to ctc docs, "It is advised not to change this list
        # [i.e. returned list] and to make a copy before calling
        # other tree methods as they could change the contents of the list."
        # See: https://wxpython.org/Phoenix/docs/html/wx.lib.agw.customtreectrl.GenericTreeItem.html
        ancestors = item.GetChildren().copy()
        # They mess you up, your mum and dad
        parents = ancestors
        while parents:
            # They may not mean to, but they do
            children = []
            for parent in parents:
                children = parent.GetChildren().copy()
                # They fill you with the faults they had
                ancestors.extend(children)
                # And add some extra, just for you
                parents = children
        return ancestors



    def SortAllChildren(self, item):

        # Get all non-leaf nodes of parent CTC object (always should be MainWindow)
        nodes = self.GetAncestors(item)
        nodes = [el for el in nodes if el.HasChildren()]
        for node in nodes:
            count = self.GetChildrenCount(node, recursively = False)
            if count > 1:
                self.SortChildren(node)



class ShapeRenderer(OCCViewer.Viewer3d):
    # HR 17/7/20
    # Adapted/simplified from OffScreenRenderer in OCCViewer <- OCC.Display
    # Dumps render of shape to jpeg file
    """ The offscreen renderer is inherited from Viewer3d.
    The DisplayShape method is overriden to export to image
    each time it is called.
    """
    def __init__(self, screen_size = (1000,1000)):
        OCCViewer.Viewer3d.__init__(self, None)
        self.Create()
        self.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_WHITE))
        self.SetSize(screen_size[0], screen_size[1])
        self.DisableAntiAliasing()
        self.SetModeShaded()
        # self.display_triedron()

        self._rendered = False



class MainWindow(wx.Frame):

    # Constructor
    def __init__(self):

        ### CREATE OBJECT FOR ASSEMBLY MANAGEMENT
        # self.a = []



        wx.Frame.__init__(self, parent = None, title = "StrEmbed-5-4")
        self.SetBackgroundColour('white')
        # self.im_folder = 'Images'
        self._path = os.getcwd()
        # print('CWD:\n', self._path)
        self.im_folder = self._path + '\Images'
        # print('Images folder:\n', self.im_folder)


        ### MENU BAR
        menuBar  = wx.MenuBar()

        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, "&File")
        fileOpen = fileMenu.Append(wx.ID_OPEN, "&Open", "Open file")
        fileSave = fileMenu.Append(wx.ID_SAVE, "&Save", "Save file")
        fileSaveAs = fileMenu.Append(wx.ID_SAVEAS, "&Save as", "Save file as")
        fileClose = fileMenu.Append(wx.ID_CLOSE, "&Close", "Close file")
        fileExit = fileMenu.Append(wx.ID_EXIT, "&Exit", "Exit program")

        partMenu = wx.Menu()
        menuBar.Append(partMenu, "&Parts")

        slctMenu = wx.Menu()
        menuBar.Append(slctMenu, "&Selector")

        lattMenu = wx.Menu()
        menuBar.Append(lattMenu, "&Lattice")

        abtMenu   = wx.Menu()
        menuBar.Append(abtMenu,  "&About")
        menuAbout = abtMenu.Append(wx.ID_ABOUT,"&About", "About StrEmbed-5-4")

        self.SetMenuBar(menuBar)



        # Bindings for menu items
        self.Bind(wx.EVT_MENU, self.OnFileOpen,      fileOpen)
        self.Bind(wx.EVT_MENU, self.DoNothingDialog, fileSave)
        self.Bind(wx.EVT_MENU, self.DoNothingDialog, fileSaveAs)
        self.Bind(wx.EVT_MENU, self.OnExit,  fileClose)
        self.Bind(wx.EVT_MENU, self.OnExit,  fileExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)



        ### TOOLBAR
        # Main window toolbar with assembly operations
        self.tb = wx.ToolBar(self, style = wx.TB_NODIVIDER | wx.TB_FLAT)
        self.SetToolBar(self.tb)
        self.tb.SetToolBitmapSize((40,40))
        self.tb.SetBackgroundColour('white')

        # File tools
        self.fileOpenTool  = self.tb.AddTool(wx.ID_ANY, 'Open',  wx.Bitmap(os.path.join(self.im_folder, "fileopen.bmp")),  bmpDisabled = wx.NullBitmap,
                                   shortHelp = 'File open',  longHelp = 'File open')
        self.exitTool      = self.tb.AddTool(wx.ID_ANY, 'Exit', wx.Bitmap(os.path.join(self.im_folder, "fileclose.bmp")), bmpDisabled = wx.NullBitmap,
                                   shortHelp = 'Exit', longHelp = 'Exit')
        self.tb.AddSeparator()

        # Assembly tools
        self.assembleTool = self.tb.AddTool(wx.ID_ANY, 'Assemble', wx.Bitmap(os.path.join(self.im_folder, "assemble.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Assemble',   longHelp = 'Form assembly from selected parts')
        self.flattenTool = self.tb.AddTool(wx.ID_ANY, 'Flatten', wx.Bitmap(os.path.join(self.im_folder, "flatten.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Flatten', longHelp = 'Flatten selected assembly')
        self.disaggregateTool = self.tb.AddTool(wx.ID_ANY, 'Disaggregate', wx.Bitmap(os.path.join(self.im_folder, "disaggregate.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Disaggregate', longHelp = 'Disaggregate selected assembly')
        self.aggregateTool = self.tb.AddTool(wx.ID_ANY, 'Aggregate', wx.Bitmap(os.path.join(self.im_folder, "aggregate.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Aggregate', longHelp = 'Aggregate selected assembly')
        self.addNodeTool = self.tb.AddTool(wx.ID_ANY, 'Add node', wx.Bitmap(os.path.join(self.im_folder, "add_node.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Add node', longHelp = 'Add node to selected assembly')
        self.removeNodeTool = self.tb.AddTool(wx.ID_ANY, 'Remove node', wx.Bitmap(os.path.join(self.im_folder, "remove_node.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Remove node', longHelp = 'Remove selected node')
        self.sortTool = self.tb.AddTool(wx.ID_ANY, 'Toggle sort type', wx.Bitmap(os.path.join(self.im_folder, "sort_mode.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Toggle sort type', longHelp = 'Toggle sort type (alphabetical/by unique item ID)')
        self.sortReverseTool = self.tb.AddTool(wx.ID_ANY, 'Reverse sort order', wx.Bitmap(os.path.join(self.im_folder, "sort_reverse.bmp")), bmpDisabled = wx.NullBitmap,
                                 shortHelp = 'Reverse sort order', longHelp = 'Reverse sort order: sort all if no items selected')

        self.tb.AddSeparator()

        text = 'Reconcile assemblies'
        self.reconcileTool = self.tb.AddTool(wx.ID_ANY, text, wx.Bitmap(os.path.join(self.im_folder, 'tree_small.bmp')), bmpDisabled = wx.NullBitmap,
                                  shortHelp = text, longHelp = text)

        self.tb.Realize()



        # Bind toolbar tools to actions
        self.Bind(wx.EVT_TOOL, self.OnFileOpen, self.fileOpenTool)
        self.Bind(wx.EVT_TOOL, self.OnExit,     self.exitTool)

        self.Bind(wx.EVT_TOOL, self.OnAssemble, self.assembleTool)
        self.Bind(wx.EVT_TOOL, self.OnFlatten, self.flattenTool)
        self.Bind(wx.EVT_TOOL, self.OnDisaggregate, self.disaggregateTool)
        self.Bind(wx.EVT_TOOL, self.OnAggregate, self.aggregateTool)
        self.Bind(wx.EVT_TOOL, self.OnAddNode, self.addNodeTool)
        self.Bind(wx.EVT_TOOL, self.OnRemoveNode, self.removeNodeTool)

        self.Bind(wx.EVT_TOOL, self.OnSortTool, self.sortTool)
        self.Bind(wx.EVT_TOOL, self.OnSortReverseTool, self.sortReverseTool)

        self.Bind(wx.EVT_TOOL, self.OnReconcileTool, self.reconcileTool)



        ### STATUS BAR
        # Status bar
        self.statbar = self.CreateStatusBar()
        self.statbar.SetBackgroundColour('white')
        # Update status bar with window size on (a) first showing and (b) resizing
        self.Bind(wx.EVT_SIZE, self.OnResize)



        # Create main panel
        self.InitMainPanel()



    def InitMainPanel(self):

        ### MAIN PANEL
        #
        # Create main panel to contain everything
        self.panel = wx.Panel(self)
        self.box   = wx.BoxSizer(wx.VERTICAL)

        # Create FlexGridSizer to have 3 panes
        # 2nd and 3rd arguments are hgap and vgap b/t panes (cosmetic)
        self.grid = wx.FlexGridSizer(cols = 2, rows = 4, hgap = 10, vgap = 10)

        self.part_header = wx.StaticText(self.panel, label = "Parts view")
        self.slct_header = wx.StaticText(self.panel, label = "Selector view")
        self.latt_header = wx.StaticText(self.panel, label = "Lattice view")
        self.occ_header  = wx.StaticText(self.panel, label = "3D view")

        self.panel_style = wx.BORDER_SIMPLE
        self.part_panel = wx.Panel(self.panel, style = self.panel_style)
        self.slct_panel = scr.ScrolledPanel(self.panel, style = self.panel_style)
        self.slct_panel.SetupScrolling()
        self.latt_panel = wx.Panel(self.panel, style = self.panel_style)

        # Create 3D viewer panel and manually set panel style (and bg colour)
        # to avoid tracking back through parent classes
        self.occ_panel = wxDisplay.wxViewer3d(self.panel)
        self.occ_panel.SetWindowStyle(self.panel_style)
        self.occ_panel.InitDriver()
        self.occ_panel._display.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_WHITE))
        
        # Off-screen renderer for producing static images for toggle buttons
        self.renderer = ShapeRenderer()
        
        # Keep track of rendered images so they can be deleted at end of session
        self.saved_images = []
        # If true, show all items contained by selected items
        self.occ_show_sub = True

        # self.occ_panel.Refresh()

        self.part_sizer = wx.BoxSizer(wx.VERTICAL)
        self.latt_sizer = wx.BoxSizer(wx.VERTICAL)
        self.occ_sizer  = wx.BoxSizer(wx.VERTICAL)

        # Some special setup for selector sizer (grid)
        self.image_cols = 4
        self.slct_sizer = wx.FlexGridSizer(cols = self.image_cols, rows = 0, hgap = 5, vgap = 5)
        # Defines tightness of images in grid
        # self.slct_tight = 0.98


        # PARTS VIEW SETUP
        # Custom tree ctrl implementation
        self.treeStyle = (ctc.TR_MULTIPLE | ctc.TR_EDIT_LABELS | ctc.TR_HAS_BUTTONS)
#        self.partTree_ctc = ctc.CustomTreeCtrl(self.part_panel, agwStyle = self.treeStyle)
        self.partTree_ctc = MyTree(self.part_panel, style = self.treeStyle)
        self.partTree_ctc.SetBackgroundColour('white')
        self.part_sizer.Add(self.partTree_ctc, 1, wx.EXPAND)


        self.partTree_ctc.Bind(wx.EVT_RIGHT_DOWN,          self.OnRightClick)
        self.partTree_ctc.Bind(wx.EVT_TREE_BEGIN_DRAG,     self.OnTreeDrag)
        self.partTree_ctc.Bind(wx.EVT_TREE_END_DRAG,       self.OnTreeDrop)
        self.partTree_ctc.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnTreeLabelEditEnd)



        # SELECTOR VIEW SETUP
        # Set up image-view grid, where "rows = 0" means the sizer updates dynamically
        # according to the number of elements it holds
#        self.slct_sizer.Add(self.image_grid, 1, wx.EXPAND)

        # Binding for toggling of part/assembly images
        # though toggle buttons realised later
        self.Bind(wx.EVT_TOGGLEBUTTON, self.ImageToggled)

        self.no_image_ass  = os.path.join(self.im_folder, 'noimage_ass.png')
        self.no_image_part = os.path.join(self.im_folder, 'noimage_part.png')



        # LATTICE VIEW SETUP
        # Set up matplotlib FigureCanvas with toolbar for zooming and movement
        self.latt_figure = mpl.figure.Figure()
        self.latt_canvas = FigureCanvas(self.latt_panel, -1, self.latt_figure)
        self.latt_axes   = self.latt_figure.add_subplot(111)
        self.latt_canvas.Hide()

        # MPL bindings
        self.latt_canvas.mpl_connect('button_press_event',   self.GetLattPos)
        # self.latt_canvas.mpl_connect('button_release_event', self.LattNodeSelected)
        self.latt_canvas.mpl_connect('button_release_event', self.OnLatticeMouseRelease)
        # self.latt_canvas.mpl_connect('pick_event', self.OnNodePick)

        # Realise but hide, to be shown later when file loaded/data updated
        self.latt_tb = NavigationToolbar(self.latt_canvas)
#        self.latt_tb.Realize()
        self.latt_tb.Hide()

        self.latt_sizer.Add(self.latt_canvas, 1, wx.EXPAND | wx.ALIGN_BOTTOM | wx.ALL, border = 5)
        self.latt_sizer.Add(self.latt_tb, 0, wx.EXPAND)

        self.default_colour  = 'red'
        self.selected_colour = 'blue'
        self.alt_colour      = 'green'

        # self.latt_panel.Bind(wx.EVT_MOTION, self.MouseMoved)

        self.new_assembly_text = 'Unnamed item'
        self.new_part_text     = 'Unnamed item'

        self.edge_alt_dict = {}
        self.node_alt_dict = {}



        # OVERALL SIZERS SETUP
        self.part_panel.SetSizer(self.part_sizer)
        self.slct_panel.SetSizer(self.slct_sizer)
        self.latt_panel.SetSizer(self.latt_sizer)
        self.occ_panel.SetSizer(self.occ_sizer)

        # self.grid.AddMany([(self.part_header), (self.slct_header), (self.latt_header),
        #                    (self.part_panel, 1, wx.EXPAND), (self.slct_panel, 1, wx.EXPAND), (self.latt_panel, 1, wx.EXPAND)])

        self.grid.AddMany([(self.part_header), (self.slct_header),
                            (self.part_panel, 1, wx.EXPAND), (self.slct_panel, 1, wx.EXPAND),
                            (self.latt_header), (self.occ_header),
                            (self.latt_panel, 1, wx.EXPAND), (self.occ_panel, 1, wx.EXPAND)])

        # Set all grid elements to "growable" upon resizing
        # Flags (second argument is proportional size)
        self.grid.AddGrowableRow(1,0)
        self.grid.AddGrowableRow(3,0)
        self.grid.AddGrowableCol(0,0)
        self.grid.AddGrowableCol(1,0)
        # self.grid.AddGrowableRow(1,0)
        # self.grid.AddGrowableCol(0,3)
        # self.grid.AddGrowableCol(1,2)
        # self.grid.AddGrowableCol(2,3)

        # Set sizer for/update main panel
        self.box.Add(self.grid, 1, wx.ALL | wx.EXPAND, 5)
        self.panel.SetSizer(self.box)

        # Set max panel sizes to avoid resizing issues
        self.part_panel_max = self.part_panel.GetSize()
        self.part_panel.SetMaxSize(self.part_panel_max)
        self.slct_panel_max = self.slct_panel.GetSize()
        self.slct_panel.SetMaxSize(self.slct_panel_max)
        self.latt_panel_max = self.latt_panel.GetSize()
        self.latt_panel.SetMaxSize(self.latt_panel_max)

        # "File is open" tag
        self.file_open = False



    def GetFilename(self, dialog_text = "Open file", starter = None, ender = None):

        ### General file-open method; takes list of file extensions as argument
        ### and can be used for specific file names ("starter", string)
        ### or types ("ender", string or list)

        # Convert "ender" to list if only one element
        if isinstance(ender, str):
            ender = [ender]

        # Check that only one argument is present
        # Create text for file dialog
        if starter is not None and ender is None:
            file_open_text = starter.upper() + " files (" + starter.lower() + "*)|" + starter.lower() + "*"
        elif starter is None and ender is not None:
            file_open_text = [el.upper() + " files (*." + el.lower() + ")|*." + el.lower() for el in ender]
            file_open_text = "|".join(file_open_text)
        else:
            raise ValueError("Requires starter or ender only")

        # Create file dialog
        fileDialog = wx.FileDialog(self, dialog_text, "", "",
                                   file_open_text,
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        fileDialog.ShowModal()
        filename = fileDialog.GetPath()
        fileDialog.Destroy()

        # Return file name, ignoring rest of path
        return filename



    def OnFileOpen(self, event = None):

        # Get STEP filename
        self.open_filename = self.GetFilename(ender = ["stp", "step"]).split("\\")[-1]

        # Return if filename is empty, i.e. if user selects "cancel" in file-open dialog
        if not self.open_filename:
            return

        # "File is open" tag
        self.file_open = True

        # # Tracker for assembly modifications
        # self.changes_made_to_assembly = False

        # # Append to assembly manager
        # self.a.append(StepParse())



        # Load data, create nodes and edges, etc.
        # self.assembly = self.a[-1]
        self.assembly = StepParse()
        self.assembly.load_step(self.open_filename)
        self.assembly.create_tree()
        self.assembly.set_node_positions()

        # OCC 3D data returned here
        self.assembly.OCC_read_file(self.open_filename)
        # self.assembly.OCC_link()

        ## Discard pile and alternative assembly
        self.assembly.discarded = StepParse()
        self.assembly.alt       = StepParse()

        # self.ctc_dict     = {}
        # self.ctc_dict_inv = {}

        # Toggle buttons
        self.button_dict     = odict()
        self.button_dict_inv = odict()
        self.button_img_dict = {}


        self.saved_images = []


        # Show parts list and lattice
        self.DisplayPartsList()

        # Clear selector window if necessary
        try:
            self.slct_sizer.Clear(True)
        except:
            pass

        # Clear lattice plot if necessary
        try:
            self.latt_axes.clear()
        except:
            pass

        # Display lattice and start 3D viewer data structure
        self.DisplayLattice(set_pos = False)
        self.Update3DView(self.selected_items)



    def Update3DView(self, items = None):

        def display_part(part):
            if part in self.assembly.OCC_dict:
                shape = self.assembly.OCC_dict[part]
                label, c = self.assembly.shapes[shape]
                self.occ_panel._display.DisplayColoredShape(shape, color = Quantity_Color(c.Red(),
                                                                                    c.Green(),
                                                                                    c.Blue(),
                                                                                    Quantity_TOC_RGB))

        if not items:
            items = self.assembly.nodes

        self.occ_panel._display.EraseAll()

        for item in items:
            if item in self.assembly.leaves:
                display_part(item)
            else:
                # Display all parts in selected assembly
                parts = self.assembly.nodes[item]['parts']
                # Add self in case STEP model exists for it (e.g. if previously disaggregated)
                parts.add(item)
                for part in parts:
                    display_part(part)
                # pass

        self.occ_panel._display.View.FitAll()
        self.occ_panel._display.View.ZFitAll()



    def DisplayPartsList(self):

        # Check if file loaded previously
        try:
            self.partTree_ctc.DeleteAllItems()
        except:
            pass

        # Create root node...
        root_id = self.assembly.get_root()
        try:
            root_tag = self.assembly.part_dict[self.assembly.step_dict[root_id]]
        except:
            root_tag = self.new_part_text

        ctc_root_item = self.partTree_ctc.AddRoot(text = root_tag, ct_type = 1, data = {'id_': root_id, 'sort_id': root_id})

        self.ctc_dict     = {}
        self.ctc_dict_inv = {}

        self.ctc_dict[root_id] = ctc_root_item
        self.ctc_dict_inv[ctc_root_item] = root_id

        # ...then all others
        tree_depth = nx.dag_longest_path_length(self.assembly, self.assembly.get_root())
        for i in range(tree_depth + 1)[1:]:
            for node in self.assembly.nodes:
                depth = nx.shortest_path_length(self.assembly, root_id, node)
                if depth == i:
                    parent_id = [el for el in self.assembly.predecessors(node)][-1]
                    ctc_parent = self.ctc_dict[parent_id]
                    # Check if 'label' field exists, which means name has been changed by user previously...
                    if 'label' in self.assembly.nodes[node]:
                        # ...but only if it's a string, as CTC will break if it's an integer...
                        label = self.assembly.nodes[node]['label']
                        if type(label) == str:
                            ctc_text = label
                    # ...else, get name from part dictionary...
                    elif self.assembly.step_dict[node] in self.assembly.part_dict:
                        ctc_text = self.assembly.part_dict[self.assembly.step_dict[node]]
                    # ...or set to default text
                    elif node in self.assembly.leaves:
                        ctc_text = self.new_part_text
                    else:
                        ctc_text = self.new_assembly_text
                    # print('Node: ', node, '; text: ', ctc_text)
                    print('Node: ', node)
                    ctc_item = self.partTree_ctc.AppendItem(ctc_parent, text = ctc_text, ct_type = 1, data = {'id_': node, 'sort_id': node})
                    self.ctc_dict[node]         = ctc_item
                    self.ctc_dict_inv[ctc_item] = node



        # Binding for checking of list items
        self.Bind(ctc.EVT_TREE_ITEM_CHECKED, self.TreeItemChecked)
        self.Bind(ctc.EVT_TREE_SEL_CHANGED,  self.TreeItemSelected)

        self.partTree_ctc.ExpandAll()

        # Sort all tree items
        self.partTree_ctc.SortAllChildren(self.partTree_ctc.GetRootItem())



    def ScaleImage(self, img, p_w = None, scaling = 0.95):

        # Get size of panel holding image if not given as argument
        if p_w == None:
            p_w  = self.slct_panel.GetSize()[0]/self.image_cols

        h, w = img.GetSize()

        if h/w > 1:
            h_new = p_w
            w_new = h_new*w/h
        else:
            w_new = p_w
            h_new = w_new*h/w

        #Rescale
        img = img.Scale(w_new*scaling, h_new*scaling)

        return img



    def get_node_colours(self, return_list = True):

        selected_items = self.selected_items

        # List version of node colours based on which are selected in parts view
        if return_list:
            node_colours = [self.selected_colour if node in selected_items else self.default_colour for node in self.assembly.nodes]

        # Dictionary version (in case useful in future)
        else:
            node_colours = {node:(self.selected_colour if node in selected_items else self.default_colour) for node in self.assembly.nodes}

        return node_colours



    def DisplayLattice(self, set_pos = True, assembly = None):

        if set_pos:
            self.assembly.set_node_positions()

        pos = self.assembly.get_positions()[0]
        print('Got positions')

        colour_map = self.get_node_colours(return_list = False)
        print('Got colour map')

        try:
            self.latt_axes.cla()
            print('Cleared axes')
        except:
            pass

        # Draw to lattice panel figure
        # nx.draw(self.assembly, pos, node_color = colour_map, with_labels = True, ax = self.latt_axes)

        ## -----------------------------------------------
        ## HR 20/05/20
        ## Alternative lattice plot routine in Hasse-like format

        # Draw outline of each level, with end point
        self.line_dict = {}
        for k,v in self.assembly.S_p.items():

            # comb_ = np.log(comb(max_,el))
            if v <= 1:
                line_pos = 0
            else:
                line_pos = 0.5*np.log(v-1)
            self.line_dict[k] = self.latt_axes.plot([-line_pos, line_pos], [k, k], c = 'gray', marker = 'o', mfc = 'gray', mec = 'gray', zorder = -1)

        # Draw nodes
        self.node_dict = {}
        for node in self.assembly.nodes:
            self.node_dict[node] = self.latt_axes.scatter(pos[node][0], pos[node][1], c = colour_map[node], zorder = 1)

        # Draw edges
        self.edge_dict = {}
        for u,v in self.assembly.edges:
            self.edge_dict[(u,v)] = self.latt_axes.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], c = 'red', zorder = 0)

        # Create edges b/t infimum and leaves
        self.origin = (0,0)
        # Here set v in edge (u,v) to None if v is infimum
        for leaf in self.assembly.leaves:
            self.edge_dict[(leaf, None)] = self.latt_axes.plot([self.origin[0], pos[leaf][0]], [self.origin[1], pos[leaf][1]], c = 'red', zorder = 0)

        ## -----------------------------------------------



        # Minimise white space around plot in panel
        self.latt_figure.subplots_adjust(left = 0.01, bottom = 0.01, right = 0.99, top = 0.99)

        # try:
        #     self.latt_axes.set_xlim(self.latt_plotlims[0])
        #     self.latt_axes.set_ylim(self.latt_plotlims[1])
        # except:
        #     pass

        print('Finished "DisplayLattice"')
        self.DoDraw('DisplayLattice')



    def DoDraw(self, called_by = None):

        if called_by:
            print('DoDraw called by ', called_by)

        # Show lattice figure
        self.latt_canvas.draw()
        print('Done "draw"')

        self.latt_canvas.Show()
        print('Done canvas "Show"')

        self.latt_tb.Show()
        print('Done toolbar "Show"')

        # Update lattice panel layout
        self.latt_panel.Layout()
        print('Done layout')

        self.drawn = True
        # line_number = 4
        # l = self.latt_axes.lines.pop(line_number)
        # print(l)
        # del l
        # print('Tried to remove line ', line_number)

        # _c = nx.get_node_attributes(self.assembly, 'color')
        # for k,v in _c.items():
        #     print('Node/colour: ', k, v)



    def OnRightClick(self, event):

        # HR 5/3/20 SOME DUPLICATION HERE WITH OPERATION-SPECIFIC METHOD, E.G. "ONFLATTEN"
        # IN TERMS OF FILTERING/SELECTION OF OPTIONS BASED ON SELECTED ITEM TYPE/QUANTITY

        # HR 5/3/20 SHOULD ADD CHECK HERE THAT MOUSE CLICK IS OVER A SELECTED ITEM
        # pos = event.GetPosition()

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # POPUP MENU (WITH BINDINGS) UPON RIGHT-CLICK IN PARTS VIEW
        # ---
        menu = wx.Menu()

        # FILTERING OF ITEM TYPES -> PARTICULAR POP-UP MENU OPTIONS
        # ---
        # Single-item options
        if len(selected_items) == 1:
            # id_ = self.ctc_dict_inv[selected_items[-1]]
            id_ = selected_items[-1]
            # Part options
            if id_ in self.assembly.leaves:
                menu_item = menu.Append(wx.ID_ANY, 'Disaggregate', 'Disaggregate part into parts')
                self.Bind(wx.EVT_MENU, self.OnDisaggregate, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Remove part', 'Remove part')
                self.Bind(wx.EVT_MENU, self.OnRemoveNode, menu_item)
            # Assembly options
            else:
                menu_item = menu.Append(wx.ID_ANY, 'Flatten', 'Flatten assembly')
                self.Bind(wx.EVT_MENU, self.OnFlatten, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Aggregate', 'Aggregate assembly')
                self.Bind(wx.EVT_MENU, self.OnAggregate, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Add node', 'Add node to assembly')
                self.Bind(wx.EVT_MENU, self.OnAddNode, menu_item)
                # Sorting options
                menu_text = 'Sort children alphabetically'
                menu_item = menu.Append(wx.ID_ANY, menu_text, menu_text)
                self.Bind(wx.EVT_MENU, self.OnSortAlpha, menu_item)
                menu_text = 'Sort children by unique ID'
                menu_item = menu.Append(wx.ID_ANY, menu_text, menu_text)
                self.Bind(wx.EVT_MENU, self.OnSortByID, menu_item)

        # Multiple-item options
        elif len(selected_items) > 1:
            menu_item = menu.Append(wx.ID_ANY, 'Assemble', 'Form assembly from selected items')
            self.Bind(wx.EVT_MENU, self.OnAssemble, menu_item)
            menu_item = menu.Append(wx.ID_ANY, 'Remove parts', 'Remove parts')
            self.Bind(wx.EVT_MENU, self.OnRemoveNode, menu_item)

        # Create popup menu at current mouse position (default if no positional argument passed)
        self.PopupMenu(menu)
        menu.Destroy()



    @property
    def selected_items(self):

        # Get selected items
        #
        # Using GetSelections() rather than maintaining list
        # b/c e.g. releasing ctrl key during multiple selection
        # means not all selections are tracked easily

        # Get IDs of selected items in parts view
        try:
            _selected_items = [self.ctc_dict_inv[item] for item in self.partTree_ctc.GetSelections()]
            return _selected_items
        except AttributeError:
            return



    def render_by_id(self, id_):

        render_ok = False
        self.renderer.EraseAll()

        # Get all children of item
        if self.assembly.nodes[id_]['all']:
            children = self.assembly.nodes[id_]['all']
        else:
            children = [id_]
        print('Children = ', children)

        # Render each child, if possible
        for child in children:
            if child in self.assembly.OCC_dict:
                shape = self.assembly.OCC_dict[child]
                label, c = self.assembly.shapes[shape]
                print('Rendering shape for item ', child)
                self.renderer.DisplayShape(shape, color = Quantity_Color(c.Red(),
                                                                         c.Green(),
                                                                         c.Blue(),
                                                                         Quantity_TOC_RGB))
            else:
                print('Cannot render item ', child, ' as not present as OCC CAD model')
                # return

        img_tag = self.assembly.step_dict[id_]
        img_name = self.get_image_name(img_tag)
        print('Image name in "render_by_id": ', img_name)

        try:
            print('Fitting and dumping image ', img_name)
            self.renderer.View.FitAll()
            self.renderer.View.ZFitAll()
            self.renderer.View.Dump(img_name)
            render_ok = True
        except Exception as e:
            print('Could not dump image to file; exception follows')
            print(e)

        if render_ok:
            print('Adding image ', img_name, 'to "saved_images"')
            self.saved_images.append(img_name)



    def get_image_name(self, img):
        img_path = os.path.join(os.path.join(self.im_folder, img) + '.jpg')
        return img_path



    def TreeItemChecked(self, event):

        def get_image(id_):

            print('Getting image...')
            print('ID = ', id_)

            # Check if ID has CAD model, which is the case if it comes from STEP file...
            # ...and therefore begins with "#..."
            # ...if not, then can't create image from it...
            # if id_ not in self.assembly.step_dict:
            if not self.assembly.step_dict[id_].startswith('#'):
                if id_ in self.assembly.leaves:
                    print('Item is leaf')
                    img_name = self.no_image_part
                else:
                    print('Item is assembly')
                    img_name = self.no_image_ass

            # ...else if it does have a CAD model, create image of all contained parts
            else:
                # Try to find pre-rendered image in folder
                tag = self.assembly.step_dict[id_]
                img_name = self.get_image_name(tag)

                # Get image from folder, otherwise render and dump it
                if os.path.isfile(img_name):
                    print('Found image file')
                else:
                    print('Did not find image file')
                    try:
                        # Render off-screen
                        print('Trying to render image...')
                        print('ID = ', id_)
                        self.render_by_id(id_)
                    except Exception as e:
                        print('Could not render image; exception follows')
                        print(e)
                        img_name = False

            if img_name:
                img = wx.Image(img_name, wx.BITMAP_TYPE_ANY)
            return img

        # Get checked item and search for corresponding image
        item = event.GetItem()
        id_  = self.ctc_dict_inv[item]

        selected_items = self.selected_items

        if item.IsChecked():
            # Get image
            img = get_image(id_)
            if not img:
                print('Image not created')
                return

            # Create/add button in slct_panel
            #
            # Includes rescaling to panel
            img_sc = self.ScaleImage(img)
            # 1/ Start with null image...
            button = wx.BitmapToggleButton(self.slct_panel)
            button.SetBackgroundColour('white')
            self.slct_sizer.Add(button, 1, wx.EXPAND)
            # 2/ Add image after computing size
            button.SetBitmap(wx.Bitmap(self.ScaleImage(img_sc)))

            # Update global list and dict
            #
            # Data is list, i.e. same format as "selected_items"
            # but ctc lacks "get selections" method for checked items
            self.button_dict[id_]         = button
            self.button_dict_inv[button]  = id_
            self.button_img_dict[id_]     = img

            # Toggle if already selected elsewhere
            if id_ in selected_items:
                button.SetValue(True)
            else:
                pass

        else:
            # Remove button from slct_panel
            obj = self.button_dict[id_]
            obj.Destroy()

            # Update global list and dict
            # self.checked_items.remove(item)
            self.button_dict.pop(id_)
            self.button_dict_inv.pop(obj)
            self.button_img_dict.pop(id_)

        self.slct_panel.SetupScrolling(scrollToTop = False)



    def TreeItemSelected(self, event):

        # Update images and lattice view
        self.UpdateToggledImages()
        self.UpdateSelectedNodes()
        self.Update3DView(self.selected_items)



    def ImageToggled(self, event):

        id_ = self.button_dict_inv[event.GetEventObject()]
        self.UpdateListSelections(id_)



    def GetLattPos(self, event):

        print('GetLattPos')

        # print('%s: button = %d, x = %d, y = %d, xdata = %f, ydata = %f' %
        #       ('Double click' if event.dblclick else 'Single click', event.button,
        #        event.x, event.y, event.xdata, event.ydata))

        # Get position and type of click event
        self.click_pos = (event.xdata, event.ydata)
        # print('Click_position = ', self.click_pos)



    def OnLatticeMouseRelease(self, event):

        print('OnLatticeMouseRelease')

        # Tolerance for node/line picker; tweak if necessary
        picker_tol = len(self.assembly.leaves)/100

        # Retain zoom settings for later
        self.latt_plotlims = (self.latt_axes.get_xlim(), self.latt_axes.get_ylim())
        # print('Plot limits: ', self.latt_plotlims)

        # If right-click event, then use pop-up menu...
        if event.button == 3:
            self.OnRightClick(event)
            return

        # ...otherwise select item
        # ---
        # Functor to find nearest value in sorted list
        # ---
        # HR 4/3/20 THIS SHOULD BE REWRITTEN COMPLETELY TO USE MPL PICKER/ARTIST FUNCTIONALITY
        def get_nearest(value, list_in):

            # print('list_in = ', list_in)
            # First check if value beyond upper bound
            if value > list_in[-1]:
                print('case 1: beyond upper bound')
                answer = list_in[-1]

            else:
                for i,el in enumerate(list_in):
                    if value < el:

                        # Then check if below lower bound
                        if i == 0:
                            print('case 2: below lower bound')
                            answer = list_in[0]
                            break

                        # All other cases: somewhere in between
                        else:
                            print('case 3: intermediate')
                            if abs(value - el) < abs(value - list_in[i-1]):
                                answer = el
                            else:
                                answer = list_in[i-1]
                            break

            return answer

        # Check that click and release are in same position
        # as FigureCanvas also allows dragging to move plot position
        if event.xdata == self.click_pos[0] and event.ydata == self.click_pos[1]:

            # Get nearest y value (same as lattice level)
            y_list = self.assembly.levels_p_sorted[:]
            # Must prepend lattice level of single part to list
            y_list.insert(0, self.assembly.part_level)
            y_  = get_nearest(event.ydata, y_list)
            print('y_list = ', y_list)
            print('y_     = ', y_)

            # Get nearest x value within known y level
            # x_dict = {self.assembly.nodes[el]['x']:el for el in self.assembly.nodes if self.assembly.nodes[el]['n_p'] == y_}
            x_all  = self.assembly.levels_dict[y_]
            x_dict = {self.assembly.nodes[el]['x']:el for el in x_all}
            x_list = sorted([k for k,v in x_dict.items()])
            x_  = get_nearest(event.xdata, x_list)
            print('x_list = ', x_list, '\n')
            print('x_dict = ', x_dict, '\n')
            print('x_     = ', x_, '\n')

            # Get nearest node
            id_ = x_dict[x_]

            print('Nearest node: x = %f, y = %f; node ID: %i\n' %
                  (x_, y_, id_))



            ##############################

            ## HR 1/6/20 Added calculation of distance nearest node + tolerance
            ## If outside tolerance, ignore nodes
            ## and generate point on nearest line instead
            ## then unrank and generate alternative assembly

            x_dist = event.xdata - x_
            y_dist = event.ydata - y_
            dist = np.sqrt(x_dist**2 + y_dist**2)

            print('x_dist = %f, y_dist = %f, dist = %f' % (x_dist, y_dist, dist))

            # If too far from any node, get alternative assembly by unranking position
            if dist > picker_tol:
                print('Outside tolerance, getting position on nearest line')

                list_ = [el for el in range(len(self.assembly.leaves)+1)]
                y__ = get_nearest(event.ydata, list_)


                self.OnNewNodeClick(y__, event.xdata)
                return

            print('Inside tolerance, (de)selecting nearest node')

            ##############################



            # Update items in parts list
            self.UpdateListSelections(id_)

            # Update node in lattice view
            # self.UpdateSelectedNodes(id_)

            if id_ in self.selected_items:
                self.node_dict[id_].set_facecolor(self.selected_colour)
            else:
                self.node_dict[id_].set_facecolor(self.default_colour)

            if not self.drawn:
                self.DoDraw('OnLatticeMouseRelease')



    ## HR 1/6/20 abandoned OnNodePick as MPL generates pick_event for every artist within pick radius
    ## Leaving here for reference

    # def OnNodePick(self, event):

    #     print('OnNodePick')

    #     # N.B. MPL generates a pick event for EVERY artist at the click point!

    #     event.artist.set_color('green')

    #     # Get node ID from artist object (i.e. reverse dictionary lookup)
    #     if event.artist in self.node_dict.values():
    #         print('Found artist in node_dict!')
    #         id_ = next(node for node, artist in self.node_dict.items() if event.artist == artist)
    #     elif event.artist in self.line_dict.values():
    #         print('Found artist in line dict!')
    #         id_ = next(line for line, artist in self.line_dict.items() if event.artist == artist)
    #     else:
    #         id_ = None

    #     print('ID = ', id_)
    #     print('Artist = ', event.artist)
    #     print('Event index = ', event.ind)



    def OnNewNodeClick(self, y_, x_):

        print('Creating new nodes and edges by unranking')

        # Ref to alternative assembly for ease of reading
        # ---------------------
        # ass = self.assembly
        # alt = self.assembly.alt
        ax  = self.latt_axes
        # ---------------------

        try:
            # Remove MPL plot objects corresponding to alternative nodes and edges...
            # ...if they exist
            if self.assembly.alt.node_dict:
                for k,v in self.assembly.alt.node_dict.items():
                    # Remove from plot (MPL)
                    v.remove()

            if self.assembly.alt.edge_dict:
                for k,v in self.assembly.alt.edge_dict.items():
                    # Remove from plot (MPL)
                    v.remove()
            self.assembly.alt.clear()
        except:
            pass



        n = len(self.assembly.leaves)

        S     = self.assembly.S_p[y_]
        width = np.log(S-1)
        rank  = int(round(((x_/width) + 0.5)*(S-1)))
        print('rank = ', rank)

        # Quantise x_ to be at position of rank
        x_quant = ((rank/(S-1))-0.5)*np.log(S-1)

        _parts  = self.assembly.unrank(n, y_, rank)



        # Create and populate alternative assembly
        _node_one = self.create_new_id()
        _node_two = _node_one + 1

        _parts_ids = [self.assembly.leaf_dict_inv[el] for el in _parts]
        _others_ids = list(self.assembly.leaves - set(_parts_ids))

        # ...and also create second node containing all other leaves, for illustration
        _others = [self.assembly.leaf_dict[el] for el in _others_ids]

        _y_others = len(_others_ids)
        S_others = self.assembly.S_p[_y_others]

        _others_rank = self.assembly.rank(_others)
        _x_others = ((_others_rank/(S_others-1))-0.5)*np.log(S_others-1)

        ## NX 1. Create and populate data of two new nodes



        ## ------------------------

        ### TO TRY COPYING ASSEMBLY AND REMOVING/ADDING ONLY THOSE NODES NECESSARY
        ### TO AVOID OPTIMAL_EDIT_PATHS TAKING SEVERAL MINUTES!

        self.assembly.alt = self.assembly.copy()
        # alt = self.assembly.alt

        # Remove unwanted edges between root and leaves
        _root = self.assembly.get_root()
        _leaves = self.assembly.leaves
        # _edges_to_remove = [(u,v) for u,v in alt.edges if u == alt_root and v in leaves]
        # # # _edges_to_remove = [(u,v) for u,v in alt.edges]
        # for edge in _edges_to_remove:
        #     alt.remove_edge(edge)

        nodes_to_remove = [node for node in self.assembly.nodes if node not in _leaves and node != _root]
        self.assembly.alt.remove_nodes_from(nodes_to_remove)

        self.assembly.alt.remove_edges_from(list(self.assembly.alt.edges))

        self.assembly.alt.add_edge(_root,_node_one)
        for leaf in _parts_ids:
            self.assembly.alt.add_edge(_node_one,leaf)

        self.assembly.alt.add_edge(_root,_node_two)
        for leaf in _others_ids:
            self.assembly.alt.add_edge(_node_two,leaf)

        # ## ------------------------



        self.assembly.alt.nodes[_node_one]['x']     = x_quant
        self.assembly.alt.nodes[_node_one]['n_p']   = y_
        self.assembly.alt.nodes[_node_one]['n_a']   = y_ + 1
        self.assembly.alt.nodes[_node_one]['parts'] = _parts_ids

        self.assembly.alt.nodes[_node_two]['x']     = _x_others
        self.assembly.alt.nodes[_node_two]['n_p']   = _y_others
        self.assembly.alt.nodes[_node_two]['n_a']   = _y_others + 1
        self.assembly.alt.nodes[_node_two]['parts'] = _others_ids

        self.assembly.alt.node_dict = {}
        self.assembly.alt.edge_dict = {}



        # # ## NX 2. ...copy data to new leaf nodes and root in new assembly...

        # # leaves_and_supremum = list(leaves) + [ass.get_root()]

        # # for _node in leaves_and_supremum:
        # #     alt.add_node(_node)
        # #     for _k,_v in ass.nodes[_node].items():
        # #         alt.nodes[_node][_k] = _v

        # ## NX 3. ...draw edges b/t first new node and its leaves...
        # for leaf in ass.leaves:
        #     alt.add_edge(_node_one, leaf)

        # ## NX 4. ...then b/t second new node and its leaves...
        # for _leaf in _others_ids:
        #     alt.add_edge(_node_two,_leaf)

        # ## NX 4. ...then edges between root and two new nodes
        # alt.add_edge(root,_node_one)
        # alt.add_edge(root,_node_two)

        # for u,v in old_edges:
        #     self.assembly.alt.remove_edge(u,v)

        # Get positions and populate dictionary of MPL objects
        self.assembly.alt.set_node_positions()
        pos_nodes, pos_edges = self.assembly.alt.get_positions()

        for node in self.assembly.alt.nodes:
            pos = pos_nodes[node]
            self.assembly.alt.node_dict[node] = ax.scatter(pos[0], pos[1], c = self.alt_colour, zorder = 0)


        ## HR 17/6/20
        ## MAJOR NOTE: NO EDGES FROM ORIGINAL ASSEMBLY ARE REMOVED AS DOING THAT BREAKS NX'S OPTIMAL_EDIT_PATHS
        ## AND CAUSES IT TO SLOW DOWN SEVERELY
        ## INSTEAD RETAIN THEM AND VARY COLOUR

        for edge in self.assembly.alt.edges:
            pos = pos_edges[edge]
            # if edge in self.assembly.edges:
            #     c = self.default_colour
            # else:
            #     c = self.alt_colour
            self.assembly.alt.edge_dict[edge] = ax.plot([pos[0][0], pos[1][0]], [pos[0][1], pos[1][1]], c = self.alt_colour, zorder = 0)[0]

        self.DoDraw('OnNewNodeClick')



    def UpdateSelectedNodes(self, nodes = None):

        if not nodes:
            nodes = self.selected_items
        elif type(nodes) == int:
            nodes = [nodes]

        nodes_not = self.assembly.nodes - nodes

        # Update selected nodes
        for node in nodes:
            self.node_dict[node].set_facecolor(self.selected_colour)
        # Update unselected nodes
        for node in nodes_not:
            self.node_dict[node].set_facecolor(self.default_colour)

        self.DoDraw('UpdateSelectedNodes')



    def UpdateListSelections(self, id_):

        # Select/deselect parts list item
        # With "select = True", SelectItem toggles state if multiple selections enabled
        self.partTree_ctc.SelectItem(self.ctc_dict[id_], select = True)



    def UpdateToggledImages(self):

        for id_, button in self.button_dict.items():
            button.SetValue(False)

        selected_items = self.selected_items

        for id_ in selected_items:
            # id_    = self.ctc_dict_inv[item]
            # if id_ in self.button_dict:
            #     button = self.button_dict[id_]
            if id_ in self.button_dict:
                button = self.button_dict[id_]
                button.SetValue(True)
            else:
                pass



    def OnAssemble(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # Further checks
        if len(selected_items) > 1:
            print('Selected items to assemble:\n')
            for id_ in selected_items:
                print('\nID = ', id_)
        else:
            print('Cannot assemble: no items or only one item selected\n')
            return

        # Check root is not present in selected items
        if self.assembly.get_root() in selected_items:
            print('Cannot create assembly: items to assemble include root')
            return



        # MAIN "ASSEMBLE" ALGORITHM
        # ---
        # Get selected item that is highest up tree (i.e. lowest depth)
        depths = {}
        for id_ in selected_items:
            depths[id_] = self.assembly.get_node_depth(id_)
            print('ID = ', id_, '; parent depth = ', depths[id_])
        highest_node = min(depths, key = depths.get)
        new_parent      = self.assembly.get_parent(highest_node)
        print('New parent = ', new_parent)

        # Get valid ID for new node then create
        new_id   = self.create_new_id()
        self.assembly.add_node(new_id)
        self.assembly.add_edge(new_parent, new_id)

        self.assembly.step_dict[new_id] = self.new_assembly_text

        # Move all selected items to be children of new node
        for id_ in selected_items:
            self.assembly.move_node(id_, new_id)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def create_new_id(self):

        # Get new item ID that is greater than largest existing ID
        try:
            id_ = max([el for el in self.assembly.nodes] + [el_ for el_ in self.assembly.discarded.nodes]) + 1
        except AttributeError:
            try:
                id_ = max([el for el in self.assembly.nodes]) + 1
            except AttributeError:
                return 0
        return id_



    def OnTreeCtrlChanged(self):

        print('Running OnTreeCtrlChanged')
        # Remake parts list and lattice
        # HR 17/02/2020 CAN BE IMPROVED SO ONLY AFFECTED CTC AND LATTICE ITEMS MODIFIED
        self.DisplayPartsList()
        self.DisplayLattice()



    def OnFlatten(self, event):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of item to flatten = ', id_)
            else:
                print('Cannot flatten: item is a leaf node/irreducible part\n')
                return
        else:
            print('Cannot flatten: more than one item selected\n')
            return



        # MAIN "FLATTEN" ALGORITHM
        # ---
        # Get all children of item
        children_      = nx.descendants(self.assembly, id_)
        children_parts = [el for el in children_ if el in leaves]
        print('Children parts = ', children_parts)
        children_ass   = [el for el in children_ if not el in leaves]
        print('Children assemblies = ', children_ass)

        # Move all children that are indivisible parts
        for child in children_parts:
            self.assembly.move_node(child, id_)

        # Delete all children that are assemblies
        for child in children_ass:
            successors = self.assembly.successors(child)
            parent     = self.assembly.get_parent(child)
            self.assembly.discarded.add_node(child)
            # Add immediate children to data of discarded node for future reconstruction
            self.assembly.discarded.nodes[child]['flatten_children'] = successors
            self.assembly.discarded.nodes[child]['flatten_parent']   = parent
            self.assembly.remove_node(child)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnDisaggregate(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ in leaves:
                print('ID of item to disaggregate = ', id_)
            else:
                print('Cannot disaggregate: item is not a leaf node/irreducible part\n')
                return
        else:
            print('Cannot disaggregate: no or more than one item selected\n')
            return



        # MAIN "DISAGGREGATE" ALGORITHM
        # ---
        # Get valid ID for new node then create
        no_disagg = 2
        for i in range(no_disagg):
            new_id   = self.create_new_id()
            self.assembly.add_node(new_id)
            self.assembly.add_edge(id_, new_id)

            print('New assembly ID = ', new_id)
            self.assembly.step_dict[new_id] = self.new_part_text

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnAggregate(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of item to aggregate = ', id_)
            else:
                print('Cannot aggregate: item is a leaf node/irreducible part\n')
                return
        else:
            print('Cannot aggregate: more than one item selected\n')
            return



        # MAIN "AGGREGATE" ALGORITHM
        # ---
        # Get children of node and remove
        children_ = [el for el in self.assembly.successors(id_)]
        print('Children aggregated: ', children_)
        for child in children_:
            # Get subgraph and add recreate in discard pile
            subgraph = nx.dfs_tree(self.assembly, child)
            self.assembly.discarded.add_nodes_from(subgraph.nodes)
            self.assembly.discarded.add_edges_from(subgraph.edges)
            ## Delete from assembly
            self.assembly.remove_nodes_from(subgraph.nodes)

        # Add list of children IDs as data for future reference
        self.assembly.nodes[id_]['aggregated'] = children_

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnAddNode(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            # id_ = self.ctc_dict_inv[selected_items[-1]]
            # if id_ not in leaves:
            #     print('ID of item to add node to = ', id_)
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of items to add not to = ', id_)
            else:
                print('Cannot add node: item is a leaf node/irreducible part\n')
                print('To add node, disaggregate part first\n')
                return
        else:
            print('Cannot add node: more than one item selected\n')
            return



        # MAIN "ADD NODE" ALGORITHM
        # ---
        # Create new node with selected item as parent
        new_id = self.create_new_id()
        self.assembly.add_node(new_id)
        self.assembly.add_edge(id_, new_id)

        print('New node ID = ', new_id)
        self.assembly.step_dict[new_id] = self.new_part_text

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnRemoveNode(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # Further checks
        if len(selected_items) >= 1:
            print('Selected item(s) to remove:\n')
            for id_ in selected_items:
                # id_ = self.ctc_dict_inv[item]
                # print('ID = ', id_)
                # self.selected_list.append(id_)
                print('ID = ', id_)
        else:
            print('Cannot remove: no items selected\n')
            return

        # Check root is not present in selected items
        _root = self.assembly.get_root()
        if _root in selected_items:
            if len(selected_items) == 1:
                print('Cannot remove root')
                return
            else:
                print('Cannot remove root; removing other selected nodes')
                selected_items.remove(_root)



        # MAIN "REMOVE NODE" ALGORITHM
        # ---
        ## Get all non-connected nodes in list...
        dependants_removed = self.assembly.remove_dependants_from(selected_items)
        # ...then create subtree and copy it to discard pile...
        for node in dependants_removed:
            subgraph = nx.dfs_tree(self.assembly, node)
            parent   = self.assembly.get_parent(node)
            self.assembly.discarded.add_nodes_from(subgraph.nodes)
            self.assembly.discarded.add_edges_from(subgraph.edges)
            # ... retaining head-parent data for future reconstruction...
            self.assembly.discarded.nodes[node]['remove_parent'] = parent
            # ...then remove subtree from main assembly
            self.assembly.remove_nodes_from(subgraph.nodes)


            # And lastly, if only one remaining sibling, remove it as redundant
            # N.B. No need to track back up through parents and remove redundant nodes...
            # ...if they are thus created, as this is done by "remove_redundant_nodes"...
            # ...when entire tree is redrawn via "OnTreeCtrlChanged"...
            # ---
            # ...but it WOULD be necessary if it weren't redrawn in full
            siblings = [el for el in self.assembly.successors(parent)]
            print('Removed all user-specified nodes')
            print('Remaining siblings: ', siblings)
            if len(siblings) == 1:
                print('Removing single remaining sibling as redundant nodes not allowed')
                self.assembly.remove_node(siblings[-1])

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def sort_check(self):

        # Check only one non-part item selected
        # ---
        if not self.assembly.nodes:
            print('No assembly present')
            return

        if len(self.partTree_ctc.GetSelections()) != 1:
            print('No or more than one item(s) selected')
            return

        item = self.partTree_ctc.GetSelection()
        if not item.HasChildren():
            print('Item is leaf node, cannot sort')
            return

        children_count = item.GetChildrenCount(recursively = False)
        if not children_count > 1:
            print('Cannot sort: item has single child')
            return

        # If all checks above passed...
        return True



    def OnSortTool(self, event):

        if not self.sort_check():
            return

        item = self.partTree_ctc.GetSelection()

        # Toggle sort mode, then sort
        if self.partTree_ctc.alphabetical:
            self.partTree_ctc.alphabetical = False
        else:
            self.partTree_ctc.alphabetical = True
        self.partTree_ctc.SortChildren(item)



    def OnSortReverseTool(self, event):

        if not self.sort_check():
            return

        item = self.partTree_ctc.GetSelection()

        # Toggle sort mode, then sort
        if self.partTree_ctc.reverse_sort:
            self.partTree_ctc.reverse_sort = False
        else:
            self.partTree_ctc.reverse_sort = True
        self.partTree_ctc.SortChildren(item)



    def OnReconcileTool(self, event = None):

        self.statbar.SetStatusText('Tree reconciliation running...')

        paths, cost, cost_from_edits, node_edits, edge_edits = StepParse.Reconcile(self.assembly, self.assembly.alt)

        _textout = 'Node edits: {}\nEdge edits: {}\nTotal cost (Networkx): {}\nTotal cost (no. of edits): {}'.format(
            node_edits, edge_edits, cost, cost_from_edits)

        self.statbar.SetStatusText('Tree reconciliation finished')
        self.DoNothingDialog(event, _textout)




    def OnSortAlpha(self, event = None):

        # Sort children of selected items alphabetically
        item = self.partTree_ctc.GetSelection()
        self.partTree_ctc.alphabetical = True
        self.partTree_ctc.SortChildren(item)



    def OnSortByID(self, event = None):

        # Sort children of selected item by ID
        item = self.partTree_ctc.GetSelection()

        # First reset "sort_id" as can be changed by drap and drop elsewhere
        # ---
        # MUST create shallow copy here (".copy()") to avoid strange behaviour
        # According to ctc docs, "It is advised not to change this list
        # [i.e. returned list] and to make a copy before calling
        # other tree methods as they could change the contents of the list."
        children = item.GetChildren().copy()
        for child in children:
            data = self.partTree_ctc.GetPyData(child)
            data['sort_id'] = data['id_']

        self.partTree_ctc.alphabetical = False
        self.partTree_ctc.SortChildren(item)



    def OnTreeDrag(self, event):

        # Drag and drop events are vetoed by default
        event.Allow()
        self.tree_drag_item = event.GetItem()
        id_ = self.ctc_dict_inv[event.GetItem()]
        print('ID of drag item = ', id_)
        self.tree_drag_id = id_



    def OnTreeDrop(self, event):

        # Allow event: drag and drop events vetoed by WX by default
        event.Allow()

        drop_item = event.GetItem()
        id_ = self.ctc_dict_inv[drop_item]
        print('ID of item at drop point = ', id_)

        drag_parent = self.tree_drag_item.GetParent()
        drop_parent = drop_item.GetParent()

        # Check if root node involved; return if so
        if (not drag_parent) or (not drop_parent):
            print('Drag or drop item is root: cannot proceed')
            return


        # CASE 1: DRAG AND DROP ITEMS HAVE THE SAME PARENT: MODIFY SORT ORDER
        # ---
        # If so, prepare sibling items by changing "sort_id" in part tree data
        # ---
        # HR 17/03/20: WHOLE SECTION NEEDS REWRITING TO BE SHORTER AND MORE EFFICIENT
        # PROBABLY VIA A FEW LIST OPERATIONS
        if drop_parent == drag_parent:

            sort_id = 1
            (child_, cookie_) = self.partTree_ctc.GetFirstChild(drop_parent)

            # If drop item found, slip drag item into its place
            if child_ == drop_item:
                self.partTree_ctc.GetPyData(self.tree_drag_item)['sort_id'] = sort_id
                sort_id += 1
            elif child_ == self.tree_drag_item:
                pass
            else:
                self.partTree_ctc.GetPyData(child_)['sort_id'] = sort_id
                sort_id += 1

            child_ = self.partTree_ctc.GetNextSibling(child_)
            while child_:

                # If drop item found, slip drag item into its place
                if child_ == drop_item:
                    self.partTree_ctc.GetPyData(self.tree_drag_item)['sort_id'] = sort_id
                    sort_id += 1
                elif child_ == self.tree_drag_item:
                    pass
                else:
                    self.partTree_ctc.GetPyData(child_)['sort_id'] = sort_id
                    sort_id += 1
                child_ = self.partTree_ctc.GetNextSibling(child_)

            # Resort, then return to avoid redrawing part tree otherwise
            self.partTree_ctc.alphabetical = False
            self.partTree_ctc.SortChildren(drop_parent)
            return

        # CASE 2: DRAG AND DROP ITEMS DO NOT HAVE THE SAME PARENT: SIMPLE MOVE
        # ---
        # Drop item is sibling unless it's root, then it's parent
        if self.assembly.get_parent(id_):
            parent = self.assembly.get_parent(id_)
        else:
            parent = id_
        self.assembly.move_node(self.tree_drag_id, parent)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnTreeLabelEditEnd(self, event):

        text_before = event.GetItem().GetText()
        wx.CallAfter(self.AfterTreeLabelEdit, event, text_before)
        event.Skip()



    def AfterTreeLabelEdit(self, event, text_before):

        item_ = event.GetItem()
        text_ = item_.GetText()
        if text_before != text_:
            id_ = self.ctc_dict_inv[item_]
            self.assembly.nodes[id_]['label'] = text_



    def ClearGUIItems(self):

        # Destroy all button objects
        for button_ in self.button_dict:
            obj = self.button_dict[button_]
            obj.Destroy()

        # Clear all relevant lists/dictionaries
        self.ctc_dict.clear()
        self.ctc_dict_inv.clear()

        self.button_dict.clear()
        self.button_dict_inv.clear()
        self.button_img_dict.clear()



    def okay_to_proceed(self, message = 'Dialog', caption = 'Okay to proceed?', style = wx.OK | wx.CANCEL):

        # Dialogue to return true if user clicks "OK"
        okay = wx.MessageDialog(self, message = message, caption = caption, style = style)
        answer = okay.ShowModal()
        if answer == wx.ID_OK:
            return True
        okay.Destroy()



    def OnAbout(self, event):

        # Show program info
        abt_text = """StrEmbed-5-4: A user interface for manipulation of design configurations\n
            Copyright (C) 2019-2020 Hugh Patrick Rice\n
            This research is supported by the UK Engineering and Physical Sciences
            Research Council (EPSRC) under grant number EP/S016406/1.\n
            This program is free software: you can redistribute it and/or modify
            it under the terms of the GNU General Public License as published by
            the Free Software Foundation, either version 3 of the License, or
            (at your option) any later version.\n
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU General Public License for more details.\n
            You should have received a copy of the GNU General Public License
            along with this program. If not, see <https://www.gnu.org/licenses/>."""

        abt = wx.MessageDialog(self, abt_text, 'About StrEmbed-5-4', wx.OK)
        # Show dialogue that stops process (modal)
        abt.ShowModal()
        abt.Destroy()



    def OnResize(self, event):

        # Display window size in status bar
        self.statbar.SetStatusText("Window size = " + format(self.GetSize()))
        wx.CallAfter(self.AfterResize, event)
        event.Skip()



    def AfterResize(self, event = None):

        # Resize all images in selector view
        if self.file_open:
            # Get size of grid element
            width_ = self.slct_panel.GetSize()[0]/self.image_cols
            for k, v in self.button_dict.items():
                img    = self.button_img_dict[k]
                img_sc = self.ScaleImage(img, width_)
                v.SetBitmap(wx.Bitmap(self.ScaleImage(img_sc)))

            self.slct_panel.SetupScrolling(scrollToTop = False)



    # def MouseMoved(self, event):

    #     # # Display mouse coordinates (panel and absolute) upon movement
    #     # self.panel_pos  = event.GetPosition()
    #     # self.screen_pos = wx.GetMousePosition()
    #     # self.statbar.SetStatusText("Pos in panel = " + format(self.panel_pos) +
    #     #                            "; Screen pos = " + format(self.screen_pos))
    #     # event.Skip()

    #     pass



    def DoNothingDialog(self, event, text = None):

        if not text:
            text = 'Functionality to be added'

        nowt = wx.MessageDialog(self, text, "Dialog", wx.OK)
        # Create modal dialogue that stops process
        nowt.ShowModal()
        nowt.Destroy()



    def remove_saved_images(self):

        text = 'Removing saved images...'
        # Remove all image files from directory, if any present
        if self.saved_images:
            self.statbar.SetStatusText(text)
            print(text)
            for image in self.saved_images:
                try:
                    image_file = os.path.join(os.getcwd(), image)
                    os.remove(image_file)
                except Exception as e:
                    print('Could not delete file at: ', image, '; exception follows')
                    print(e)



    def OnExit(self, event):

        self.remove_saved_images()
        # Close program
        self.Close(True)



if __name__ == '__main__':
    # app = wit.InspectableApp()
    app = wx.App()
    frame = MainWindow()

    frame.Show()
    frame.Maximize()

    app.MainLoop()