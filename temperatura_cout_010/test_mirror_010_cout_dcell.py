
import fileinput, os
import re
import subprocess
import numpy as np
import csv



#valor1 = valor2 = 0
flag = 0

#=====================FUNCAO: converte a unidade para float e multiplica o valor==================================
def multiplyer_prefix(unidade, float_value):
	# verifica qual foi a unidade recebida (str) para multiplicar o valor recebido (float) pela unidade correta
	if unidade == 'c':
		float_value = float_value * 10**-2
	elif unidade == 'm':
		float_value = float_value * 10**-3
	elif unidade == 'u':
		float_value = float_value * 10**-6
	elif unidade == 'n':
		float_value = float_value * 10**-9
	elif unidade == 'p':
		float_value = float_value * 10**-12

	return float_value

#======================FUNCAO: convert string para float=======================================
def converter(value):
	# retira o ultimo caracter (unidade) da string
	unidade = value[-1]
	# converte o restante da string em float
	float_value = float(value[:-1])
	# Atribui o float convertido e multiplicado pela unidade na variavel float_converted
	float_converted = multiplyer_prefix(unidade, float_value)
	
	#retorna o valor convertido e multiplicado pela unidade
	return float_converted

## verify if the max and min value broke the condition to provoke a fault comparing with half of the vdd value
def compare(value_min, value_max):
	set_happened = False
	if (value_min <= 0.35) or (value_max >= 0.35):
		set_happened = True	
		#print(set_happened)

	return set_happened

def increment_current(set_occurence, current_pulse):
	if set_occurence == True:
		#print('increment current set: ' + str(set_occurence))
		current_pulse = current_pulse + 0
	else:
		current_pulse += .1
		#print(set_occurence)
	
	return current_pulse

#increment the pulse type starting from 0.5
def increment_current_file(currentValue, node_value, pulse_type):
	filepath = 'pulso_radiacao.cir'
	
	if pulse_type == 0:
		x = 'Iset gnd ' + str(node_value) + ' EXP (0 '+str(currentValue)+'u 4ns 10ps 10ps 200ps)'
	else:
		x = 'Iset ' + str(node_value) + ' gnd EXP (0 '+str(currentValue)+'u 4ns 10ps 10ps 200ps)'

	with open(filepath, 'r+') as fp:
		fp.truncate(0)	#apaga o arquivo de texto atual
		fp.write(x)
		fp.close()

#insert the dcell to the colision node
def add_dcell_node(node_counter):
	filepath = 'dcell.cir'
	
	if node_counter == 0:
		x = '*dcell node a\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p1_p2 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p1_p2 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 1:
		x = '*dcell node b\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p3_p4 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p3_p4 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 2:
		x = '*dcell node c\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p6_p9 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p6_p9 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 3:
		x = '*dcell node d\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p10_p11 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p10_p11 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 4:
		x = '*dcell node e\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p11_p12 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p11_p12 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 5:
		x = '*dcell node f\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p2_n1 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p2_n1 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 6:
		x = '*dcell node g\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 p9_n6 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 p9_n6 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 7:
		x = '*dcell node h\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 n1_n2 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 n1_n2 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 8:
		x = '*dcell node i\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 n4_n3 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 n4_n3 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 9:
		x = '*dcell node j\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 n6_n7 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 n6_n7 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 10:
		x = '*dcell node k\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 n10_n11 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 n10_n11 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 11:
		x = '*dcell node l\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 n11_n12 ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 n11_n12 gate_p16 drain_p16 vdd				pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 12:
		x = '*dcell node sum\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 sum ground					nmos_rvt w=27.0n l=20n nfin=3\nMp16 sum gate_p16 drain_p16 vdd					pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	elif node_counter == 13:
		x = '*dcell node cout\nMp15 vccbloco gate_p15 drain_p15 vdd 				pmos_rvt w=27.0n l=20n nfin=3\nMn15 gate_p15 drain_p15 cout ground				nmos_rvt w=27.0n l=20n nfin=3\nMp16 cout gate_p16 drain_p16 vdd					pmos_rvt w=27.0n l=20n nfin=3\nMn16 gate_p16 drain_p16 vssbloco ground				nmos_rvt w=27.0n l=20n nfin=3'
	
	with open(filepath, 'r+') as fp:
		fp.truncate(0)	#apaga o arquivo de texto atual
		fp.write(x)
		fp.close()

def split_word(word):
	
	x = word.split("=")
		
	return x
	
#funciton to resolve the problem of hspice output for negative values
def check_list_size(list):
	x = len(list)		#length of the list
	y = len(list[0])	#length of the first string the list	
	z = len(list[4])	#length 5th string of the list	
	
	if (x == 7):
		#print('ENTREI x')
		if(y > 10):
			#print('ENTREI Y')
			#print('y: ' + str(y))
			b = split_word(list[0])
			#print('b' + str(b))
			if (len(b) > 1):
				list = b + list[1:]
				#print(list)
			if(z > 10):
				#print('ENTREI Z')
				c = split_word(list[4])
				list = list[1:3] + c + list[5:]
		elif (z > 10):
			c = split_word(list[4])
			d = list[:4]
			e = list[5:]
			list = d + c + e
			
	return list

def set_input_vector(vector_type):
		
	if vector_type == 0:
		x = 'Va a gnd ground_valor\nVb b gnd ground_valor\nVcin cin gnd ground_valor'	#VECTOR: 000
		set_measures(0)
	elif vector_type == 1:
		x = 'Va a gnd ground_valor\nVb b gnd ground_valor\nVcin cin gnd supply'			#VECTOR: 001
		set_measures(0)
	elif vector_type == 2:
		x = 'Va a gnd ground_valor\nVb b gnd supply\nVcin cin gnd ground_valor'			#VECTOR: 010
		set_measures(0)
	elif vector_type == 3:
		x = 'Va a gnd ground_valor\nVb b gnd supply\nVcin cin gnd supply'				#VECTOR: 011
		set_measures(1)
	elif vector_type == 4:
		x = 'Va a gnd supply\nVb b gnd ground_valor\nVcin cin gnd ground_valor'			#VECTOR: 100
		set_measures(0)
	elif vector_type == 5:
		x = 'Va a gnd supply\nVb b gnd ground_valor\nVcin cin gnd supply'				#VECTOR: 101
		set_measures(1)
	elif vector_type == 6:
		x = 'Va a gnd supply\nVb b gnd supply\nVcin cin gnd ground_valor'				#VECTOR: 110
		set_measures(1)
	elif vector_type == 7:
		x = 'Va a gnd supply\nVb b gnd supply\nVcin cin gnd supply'						#VECTOR: 111
		set_measures(1)
	else:
		x = 'ERROR'
	
	filepath = 'ondas_radiation_COUT.cir'

	with open(filepath, 'r+') as fp:
		#x = 'Iset gnd ' + str(node_value) + ' EXP (0 '+str(currentValue)+'u 4ns 10ps 10ps 200ps)'
		fp.truncate(0)	#apaga o arquivo de texto atual
		fp.write(x)
		fp.close()

def set_measures(type_measure):
	filepath = 'measures.cir'
	
	if type_measure == 0:
		x = '.meas tran minout min V(ncout) from=1p to=8n\n.meas tran maxout max V(cout) from=1n to=8n'
	else:
		x = '.meas tran minout min V(cout) from=1p to=8n\n.meas tran maxout max V(ncout) from=1p to=8n'
	
	with open(filepath, 'r+') as fp:
		#x = 'Iset gnd ' + str(node_value) + ' EXP (0 '+str(currentValue)+'u 4ns 10ps 10ps 200ps)'
		fp.truncate(0)	#apaga o arquivo de texto atual
		fp.write(x)
		fp.close()
	
	
	
#################################################################
#														        #
### -------------------INICIO DO SCRIPT-------------------#######
#                                                               #
#################################################################

#COMANDO DO TERMINAL: python3 test.py
'''
	DATA:
		TENSAO NOMINAL:0.7V
		TENSAO NEAR THRESHOLD: 0.35V
'''
table_min_max = []
current_pulse = 0					#pulso de corrente que simula a colisao
set_occurence = False				#variavel usada para verificar se houve a falha
table_current_results = []					#tabelas das correntes minimas
#table_nodes = ["p1_p2","p3_p4"]		#tabela dos nos
table_node_counter = 0				#contador para incrementar os nos
input_vector_counter = 0			#contador para os vetores de entrada

#imput_vector_counter = ['000', '001', '010','011', '100','101', '110', '111']
table_nodes = ["p1_p2","p3_p4","p6_p9","p10_p11","p11_n12","p2_n1","p9_n6","n1_n2","n4_n3","n6_n7","n10_n11","n11_n12","sum", "cout"]
#table_nodes = ["p9_p6"]
min = None
max = None


'''
 - executa um comando externo usando run()
 - os comandos sao passados como uma lista de argumentos
 - run() retorna uma instancia de CompletedProcess com as informacoes do processo como o programa e a saida
 - shell = True permite o subprocess a chamar um processo shell intermediario e rodar os comandos
 - PIPE permite capturar a saida do comando e atribuir ao stdout
'''

#while para poder mudar o tipo de vetor de entrada 
while (input_vector_counter != 8):
	
	#input_vector_counter = 4
	table_current_results.append('010')
	table_current_results.append('INPUT VECOTOR: ' + str(input_vector_counter))	
	
	table_node_counter = 0			#zera o contador dos nós para o próximo tipo de pulso
	set_occurence = False			#reset da ocorrencia do set para o proximo no
		
	table_min_max.append('INPUT VECOTOR: ' + str(input_vector_counter))
	set_input_vector(input_vector_counter)
	
	#while para mudar o nó da inserção da falha
	while (table_node_counter != len(table_nodes)):
				
		current_pulse = 0			#zera o pulso de corrente para o novo nodo
		set_occurence = False			#zera o set para o novo no

		increment_current_file(current_pulse, table_nodes[table_node_counter], 0)
		
		#adds the dcell to the right node		
		add_dcell_node(table_node_counter)

		table_min_max.append(str(table_nodes[table_node_counter]))

		#while para incrementar o pulso de corrente até acontecer a falha
		while((current_pulse <= 120) and (set_occurence == False)):
		
			#print('table node length: ' + str(len(table_nodes)))			

			completed = subprocess.run(['hspice ADDER_MIRROR_COUT_DCELL.cir | grep "minout\|maxout"'], shell=True, stdout=subprocess.PIPE,)

			# separa a saida gerada pelo grep e atribuida ao stdout (tipo str) em cada espaco e salva tudo direto numa variavel do tipo lista
			#(precisa dar um decode() pq stdout e por padrao é byte type)
			listOut = completed.stdout.decode('utf-8').split()

			#print(listOut)
			listOut = check_list_size(listOut)
			# pega o segundo elemento da lista e salva numa variavel
			max = listOut[5]
			# pega o sexto elemento da lista e salva numa variavel
			min = listOut[1]


			# converte a string 'min' em float chamando a funcao converter() e atribui na variavel min_converted
			min_converted = converter(min)
			table_min_max.append('min: ' + str(min))

			# converte a string 'max' em float chamando a funcao converter() e atribui na variavel max_converted
			max_converted = converter(max)
			table_min_max.append('max: ' + str(max))

			#print('current pulse before: ' + str(current_pulse))
			print('current: ' + str(current_pulse))
			set_occurence = compare(min_converted, max_converted)
			current_pulse = increment_current(set_occurence, current_pulse)

			#print('current pulse after: ' + str(current_pulse))
			#print('table nodes:' + str(table_nodes))
			#print('table nodes counter: ' + str(table_node_counter) + '\n')
			increment_current_file(current_pulse, table_nodes[table_node_counter], 0)

		table_current_results.append(str(table_nodes[table_node_counter]) +'= ' + str(current_pulse - 0.1))
		table_node_counter = table_node_counter + 1
		print('table: ' + str(table_current_results))

	
	input_vector_counter = input_vector_counter + 1
	#print('input vector counter DEPOIS: ' + str(input_vector_counter))


#print(table_current_results)

with open('min_max_010_cout_dcell.txt', 'w') as filehandle:
	for listitem in table_min_max:
		filehandle.write('%s\n' % listitem)

with open('results_010_cout_dcell.txt', 'w') as filehandle:
    for listitem in table_current_results:
        filehandle.write('%s\n' % listitem)


