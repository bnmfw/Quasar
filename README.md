# Quasar
Quasar is an open-source tool for evaluating radiation robustness of electrical circuits.

It integrates with a SPICE simulator such as NGSPICE or HSPICE.

Keep in mind the current version was fully developed by a single undergrad CS student, if you have any issues please report them in this github.

## Requirements
Quasar requires an instalation of either NGSPICE or HSPICE on the running computer.

## Build Quasar
To build Quasar run the following commands:
```
git clone https://github.com/bnmfw/Quasar.git
cd Quasar
python3 -m venv venv
source venv/bin/activate
make requirements
```

## Test Quasar
To test if the installation was successuf run the following:
```
make test
```

## Setting Up a Circuit
To utilize Quasar a netlist of the circuit must as well as the model files must be provided.
The model files must be included in ```project/models```.
The .cir file must be included in ```project/circuits/<filename>/```.

### Netlist and Model Constraints
Netlist and Model files must follow a template.
- Model files must be of the .pm format.option measform = 3
.option post = 0, .lib is not supported currently.
- Netlist files must follow the template, there is a nand2 template in the project/circuits folder:
  ``` spice
  .include ../../include.cir

  .option measform = 3 
  .option post = 2

  <netlist>
  .end
  ```
- Netlists must be plain, no subcircuit can be included.
- PMOS/NMOS devices must follow the Mp/Mn prefix, e.g. Mp1, Mn2, Mp_faulted, etc...
- The .pm file must be in project/models directory before any simulation is run.

## Running Quasar
To run quasar simply run:
```
make
```

### Setup
Insert the <filename> of the created circuit.
In quasar if an input has "(value)" this is the default, press enter with no insertion to take it.

If this is the first time analysing the circuit it will need to be registered and default configurations will need to be set.

First insert all the circuit logical inputs, separated by spaces.

Then insert all the circuit outputs, separated by spaces.

A first analysis will run.

### Main Menu
A main menu will be presented with 5 options, following is the explanation of the first 4.

### 0 - Update LETS
This require no further inputs, it will rerun every fault configurations and determine the LETs again.

This is usefull for resizing devices on the netlist and see how it impacts robustness.

You can insert capacitors in a netlist an update the LETs to see its impacts

### 1 - Generate LETS CSV
Dumps the radiation profile of the circuit to a csv.

The CSV will be name <circuit name>.csv and can be found on project/circuits/<circuit name> directory.

### 2 - Variability Analysis
Allows to asses physicial parameter variability on radiation robustness.

First insert the number of points on the distributions

Select a model, a physicial parameters and the gaussian distribution parameters.

You can keep inserting more parameters (Currently you must insert 2 distributions in order for things to not break)

A Monte Carlo analysis will be run, it backups periodically.

At the end several pngs will be generated on the circuit file plotting the characteristicis of the LETth Fault Configuration.

### 3 - Analyze a Single Fault Configuration
Mainly used for debugging, allows for the user to see every simulation of the critical LET search of a fault configuration.

Insert:
- Node struck
- Output measured
- Input signals separated by spaces, e.g. "0 0 1 0"
- Pulse direction at both the node and output, separeted by spaces, e.g. "rise fall". (If you are not sure look at the circuit csv, or raw data, it will list this for each fault config.)

### 4 - Configure Simulation
Allows for the re configuration that is done on setup.

## Quasar Caveats
Quasar can be finnicky, this started as a personal project to run my simulations and has become something more sofisticated. Even so, its use is not always intuitive.

If you change the netlist in a way it alters the topology of the transistors (resizing is ok) you MUST delete the <circuit name>.json file on the circuit directory. This file is the circuit log, by changing the topology you change the possible fault configurations, so this file will be obsolete and has to be manually deleted.

Quasar runs something in parallel. If a process worker crashes it will not crash the master which will wait forever, you might have to Ctrl+C by hand to stop it.
