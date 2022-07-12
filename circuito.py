from arquivos import JManager, CManager
from runner import HSRunner
from circuitManager import CircMan
from components import Nodo, Entrada, LET
import os

barra_comprida = "---------------------------"

class Circuito():
    def __init__(self, nome):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.path = f"circuitos/{nome}/"
        self.arquivo = f"{nome}.cir"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0
        self.atrasoCC: float = 0
        self.LETth: LET = None
        self.__iniciado = False

        # Decodifica do Json caso exista, se nao existir tenta criar a partir do arquivo
        if os.path.exists(f"{self.path}{self.nome}.json"):
            JManager.decodificar(self)
            self.__iniciado = True
        else:
            self.__instanciar_nodos()

    @property
    def iniciado(self):
        return self.__iniciado

    @iniciado.setter
    def iniciado(self, iniciado):
        if not self.__iniciado and iniciado:
            JManager.codificar(self)
        self.__iniciado = iniciado
   
    def analise_monte_carlo(self):

        nodo_nome, saida_nome = input("nodo e saida do LET: ").split()

        nodo: Nodo = next(nodo for nodo in self.nodos if nodo.nome == nodo_nome)
        saida: Nodo = next(saida for saida in self.saidas if saida.nome == saida_nome)
        
        print("Orientacoes disponiveis: ")
        
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(let_disponivel.orientacao, let_disponivel.corrente)
        
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        let: LET = next(let for let in nodo.LETs if let.saida_nome == saida.nome and let.orientacao == [pulso_in, pulso_out])
        
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = let.validacoes[0][indice]
        
        with HSRunner.SET(let):
            num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))
            faults = HSRunner.run_simple_MC(self.path, self.nome, let.nodo_nome, let.saida_nome, num_analises, pulso_out, self.vdd)
        
        print(f"Proporcao de falhas: {100 * faults/num_analises}%")
        print("Analise monte carlo realizada com sucesso")

    def analise_monte_carlo_progressiva(self):

        # Configuracao do LETth do circuito no Hspice
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = self.LETth.validacoes[0][indice]
        
        with HSRunner.Inputs(self.vdd, self.entradas), HSRunner.Vdd(self.vdd):
            _, pulso_out = self.LETth.orientacao

            num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))

            mc_dict: dict = {"analises": [num_analises]}

            step: float = 0.05
            for frac in [round(num*step,2) for num in range(1, int(1/step)+1)]:

                with HSRunner.SET(self.LETth, self.LETth.corrente * frac):

                    falhas: int = HSRunner.run_simple_MC(self.path, self.nome, self.LETth.nodo_nome, self.LETth.saida_nome, num_analises, pulso_out, self.vdd)
                    mc_dict[frac] = [falhas]

            print(mc_dict)
            CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc.csv",mc_dict)

            print("Analise monte carlo realizada com sucesso")

    def analise_monte_carlo_total(self):
        # Gera as instancias de nmos e pmos da analise MC
        num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(self.path, self.arquivo, self.nome, num_analises)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}

        print("Encontrando LETth para cada instancia")

        with open("erros.txt", "a") as erro:
            erro.write(f"\nErros do circuito: {self.nome}\n")

        # print(var)

        for i, (pmos, nmos) in var.items():
            print(f"index: {i} pmos: {pmos} nmos: {nmos}")
            with HSRunner.MC_Instance(pmos, nmos):
                CircMan.get_atrasoCC(self)
                CircMan.atualizar_LETths(self, pmos, nmos)
                saida[i] = (round(pmos,4), round(nmos,4), self.LETth.nodo_nome, self.LETth.saida_nome, self.LETth.corrente, self.LETth.valor)
            if i > num_analises: break

        CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

    def __instanciar_nodos(self):
        entradas, saidas = (input("entradas: ").split() , input("saidas: ").split())
        ##### SAIDAS #####
        self.saidas = [Nodo(saida) for saida in saidas]
        ##### ENTRADAS #####
        self.entradas = [Entrada(entrada) for entrada in entradas]
        ##### OUTROS NODOS #####
        self.nodos = [Nodo(nodo) for nodo in HSRunner.get_nodes(self.nome) if "f" not in nodo and "t" not in nodo and nodo not in {"vdd", "gnd"}]

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7
