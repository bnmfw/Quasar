from .matematica import corrente_para_let

modo_debug: bool = False

class Entrada:
    def __init__(self, nome: str):
        self.nome = nome
        self.sinal = "setup"

    def codec(self):
        dic = {}
        dic["nome"] = self.nome
        dic["sinal"] = self.sinal
        return dic

    def decodec(self, dic: dict):
        self.nome = dic["nome"]
        self.sinal = dic["sinal"]

    def __repr__(self):
        return str(self.nome)

class Nodo:
    def __init__(self, nome: str):
        self.nome = nome
        self.LETs = []
        # Eh um dicionario de dicionarios
        self.LETth: LET = LET(None, None, self.nome, "saida", "aa")
        self.atraso = {}

    def __repr__(self):
        return f"\nnome: {self.nome}\tLETth: {self.LETth.corrente}\tQuantidade de LETs:{len(self.LETs)}"

    def codec(self):
        dic = {}
        dic["nome"] = self.nome
        dic["critico"] = self.LETth.codec()
        dic["atraso"] = self.atraso
        lista_de_lets = []
        for let in self.LETs:
            lista_de_lets.append(let.codec())
        dic["lets"] = lista_de_lets
        return dic

    def decodec(self, dic:dict, vdd:float):
        if not isinstance(dic, dict) or not isinstance(vdd,(int, float)): raise TypeError(f"dic (dict): {type(dic)}, vdd (float): {type(vdd)}")
        self.nome = dic["nome"]
        self.LETth = LET(None, vdd, "nodo", "saida", "orientacao")
        self.LETth.decodec(dic["critico"])
        self.atraso = dic["atraso"]
        for dicionario_let in dic["lets"]:
            let = LET(None, vdd, "nodo", "saida", "orientacao")
            let.decodec(dicionario_let)
            self.LETs.append(let)

class LET:
    def __init__(self, corrente:float, vdd:float, nodo_nome:str, saida_nome:list, orientacao:str, validacoes:list = None):
        self.valor: float = None
        self.__corrente: float = corrente
        self.orientacao: list = orientacao
        self.vdd: float = vdd
        self.nodo_nome: str = nodo_nome
        self.saida_nome: str = saida_nome
        if validacoes == None:
            self.validacoes = []
        else:
            self.validacoes = validacoes

    @property
    def corrente(self) -> float:
        return self.__corrente

    @corrente.setter
    def corrente(self, corrente):
        self.__corrente = corrente
        self.valor = corrente_para_let(corrente)

    def __eq__(self, other):
        return (self.nodo_nome == other.nodo_nome and self.saida_nome == other.saida_nome and self.orientacao == other.orientacao)

    def __repr__(self):
        return f"\ncorrente: {self.corrente}, orientacao: {self.orientacao}, vdd: {self.vdd}, nodo: {self.nodo_nome}, saida: {self.saida_nome}"

    def __len__(self):
        return len(self.validacoes)

    def __lt__(self, other):
        return self.corrente < other.corrente
    
    def __le__(self, other):
        return self.corrente <= other.corrente
    
    def __gt__(self, other):
        return self.corrente > other.corrente

    def __ge__(self, other):
        return self.corrente >= other.corrente

    def append(self, validacao: list):
        if type(validacao) != list: raise TypeError("Validacao nao eh uma lista")
        if not validacao in self.validacoes:
            self.validacoes.append(validacao)  

    def codec(self):
        dic = {}
        dic["corr"] = self.corrente
        dic["orie"] = self.orientacao
        dic["nodo"] = self.nodo_nome
        dic["said"] = self.saida_nome
        dic["val"] = self.validacoes
        return dic

    def decodec(self, dic: dict):
        if type(dic) != dict: raise TypeError(f"Nao recebi um dicionario, recebi {type(dic)}: {dic}")
        self.corrente = dic["corr"]
        self.orientacao = dic["orie"]
        self.nodo_nome = dic["nodo"]
        self.saida_nome = dic["said"]
        self.validacoes = dic["val"]

if __name__ == "__main__":

    objeto_codificado = vars(LET(154.3, 0.7, "nodo1", "saida1", ["fall", "rise"]))
    print(objeto_codificado.values())

    #TESTES DE ENTRADA
    # e1 = Entrada("ent1", "t")
    # e2 = Entrada("ent2", "t")
    # print(e1.codec())
    # e2.decodec(e1.codec())
    # assert e1.nome == e2.nome and e1.sinal == e2.sinal, "Entrada FALHOU"

    # # TESTE DE NODO
    # n1 = Nodo("nodo1")
    # n2 = Nodo("nodo2")
    # n2.decodec(n1.codec(),0.7)
    # assert n1.nome == n2.nome and n1.atraso == n2.atraso and \
    #         n1.LETs == n2.LETs and\
    #        n1.LETth == n2.LETth, "Nodo FALHOU"

    # # TESTE DE LET
    # let1 = LET(154.3, 0.7, "nodo1", "saida1", ["fall", "rise"])
    # let2 = LET(300, 0.7, "nodo1", "saida1", ["rise","fall"])
    # let2.decodec(let1.codec())
    # assert let1 == let2, "LET FALHOU no teste de Overloading e Codificacao"

    # entrada = [0,0,1,0,1]
    # let1.append(entrada)
    # assert entrada in let1.validacoes, "LET FALHOU no teste de Append"