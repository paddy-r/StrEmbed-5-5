# StrEmbed-5-4

Version 5-4 of Structure Embedding

Part of the Design Configuration Spaces (DCS) project hosted by the University of Leeds

Hugh Rice (HR/HPR), Tom Hazlehurst (TH) and Hau Hing Chau (HHC)

January-August 2020

School of Mechanical Engineering  
University of Leeds  
LS2 9JT

All communication, including bug/issues reports, to: h.p.rice@leeds.ac.uk

<i> ```StrEmbed-5-4``` is a graphical user interface for visualisation and manipulation of part-whole relationships in assemblies of parts, and is written in Python. The user can read files in the [STEP format](https://en.wikipedia.org/wiki/ISO_10303-21), which is a common data exchange format containing both assembly information (i.e. part-whole information) and shape data; Functionality is based on [```StrEmbed-4```](https://github.com/hhchau/StrEmbed-4) (and earlier versions) by Hau Hing Chau, written in Perl.</i>  

<b>This research is supported by the UK Engineering and Physical Sciences Research Council (EPSRC) under grant number EP/S016406/1.</b>

There are several ways to run ```StrEmbed-5-4```, which are described below and in more detail in the user manual. The simplest is to download the latest release, which contains all the Python scripts and a standalone executable file. To run StrEmbed-5-4 you can then do one of the following:

(1) Run as a Python script in your own environment. Three scripts are required:

1. ```StrEmbed_5_4``` (main script)
2. ```step_parse_5_4``` (contains class for for file and graph operations)
3. ```wxDisplay``` (for 3D viewer, from ```Python-OCC``` [here](https://github.com/tpaviot/pythonocc-core))

```StrEmbed-5-4``` has a large number of dependencies that must also be installed in your environment. Contact the developers if you encounter problems.

(2) Run as a standalone executable. This does not require you to have Python or any IDE installed. Simply double-click on one of the files ending with  ```.exe``` and the user interface will appear. Please note that two executables are provided, with and without console output for debugging purposes. Please make a record of the output if you encounter problems and wish to contact the developers for help.

Several STEP file examples are provided. The "Images" folder contains images necessary for the application; temporary images corresponding to the parts in a loaded STEP file are also stored there. As a result, any images beginning with ```#```, which are created on-the-fly at runtime, can be deleted once you have closed the application.

```StrEmbed-5-4``` was developed in Spyder, an IDE for Python that is packaged with the Anaconda distribution, which can be downloaded [here](https://www.anaconda.com/distribution/).

```StrEmbed-5-4``` is published under the GNU General Purpose License version 3, which is given in the LICENSE document.
