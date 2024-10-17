# Quasar
Quasar is an open-source tool for evaluating radiation robustness of electrical circuits.
It integrates with a SPICE simulator such as NGSPICE or HSPICE.

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
- Model files must be of the .pm format, .lib is not supported currently
- Netlist files must follow the template:
  ``` spice
  .include ../../include.cir
  <netlist>
  .end
  ```
- Netlists must be plain, no subcircuit can be included

## Using Quasar
To run quasar simply run:
```
make
```
Insert the <filename> of the created circuit.
If this is the first time analysing the circuit it will need to be registered and default configurations will need to be set.
...
