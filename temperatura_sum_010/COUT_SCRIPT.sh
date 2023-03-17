#!/bin/bash 

#####################################################
#   Script: Generation of Nominal Values (FinFET)   #
#              Technologies: 7nm, 20nm              #
#	               Node:   HP & LP                  #
#              Standard Cells:10 cells              #
#         Developed by: Fábio G. Rossato Gomes      #
#####################################################
nohup  hspice 'ADDER_HYBRID_COUT'.cir > 'Resultados/ADDER_HYBRID_COUT'.results
nohup  hspice 'ADDER_MIRROR_COUT'.cir > 'Resultados/ADDER_MIRROR_COUT'.results
nohup  hspice 'ADDER_TFA_COUT'.cir > 'Resultados/ADDER_TFA_COUT'.results
nohup  hspice 'ADDER_TGA_COUT'.cir > 'Resultados/ADDER_TGA_COUT'.results
nohup  hspice 'ADDER_V1V1_COUT'.cir > 'Resultados/ADDER_V1V1_COUT'.results
nohup  hspice 'ADDER_V1V5_COUT'.cir > 'Resultados/ADDER_V1V5_COUT'.results
nohup  hspice 'ADDER_V1V8_COUT'.cir > 'Resultados/ADDER_V1V8_COUT'.results
nohup  hspice 'ADDER_V5V1_COUT'.cir > 'Resultados/ADDER_V5V1_COUT'.results
nohup  hspice 'ADDER_V5V5_COUT'.cir > 'Resultados/ADDER_V5V5_COUT'.results
nohup  hspice 'ADDER_V5V8_COUT'.cir > 'Resultados/ADDER_V5V8_COUT'.results
nohup  hspice 'ADDER_V8V1_COUT'.cir > 'Resultados/ADDER_V8V1_COUT'.results
nohup  hspice 'ADDER_V8V5_COUT'.cir > 'Resultados/ADDER_V8V5_COUT'.results
nohup  hspice 'ADDER_V8V8_COUT'.cir > 'Resultados/ADDER_V8V8_COUT'.results

			rm *.st0
			rm *.ic0
			rm *.mt0
			rm *.tr0
			rm *.pa0

echo 'Done:'  
