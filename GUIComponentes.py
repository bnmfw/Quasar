barra_comprida = "---------------------------"

class InterfaceComponentes:

    def __init__(self) -> None:
        pass

    def requisitar_circuito(self) -> str:
        return input(barra_comprida+"\nEscolha o circuito: ")

    def requisitar_vdd(self) -> float:
        return float(input(f"{barra_comprida}\nVdd da simulacao: "))

    def requisitar_menu(self, circuito_nome: str, vdd: float) -> int:
        return int(input(f"{barra_comprida}\n"
                     f"Trabalhando com o {circuito_nome} em {vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analisar LET Unico\n"
                     "3. Analise Monte Carlo\n"
                     "4. Analise Monte Carlo Unica\n"
                     "5. Analise Monte Carlo Total\n"
                     "6. Sair\n"
                     "Resposta: "))

    def requisitar_num_analises(self) -> int:
        return int(input(f"{barra_comprida}\nQuantidade de analises: "))

    def requisitar_entradas_e_saidas(self) -> tuple:
        return (input("entradas: ").split() , input("saidas: ").split())

    def requisitar_nodo_e_saida(self) -> list:
        return input("nodo e saida do LET: ").split()

    def requisitar_pulsos(self) -> list:
        return input("pulsos na entrada e saida do LET: ").split()

    def requisitar_cadastro(self) -> bool:
        cadastro = None
        while not cadastro in {"y","n"}:
            cadastro: bool = input(f"{barra_comprida}\nCadastro do circuito nao encontrado\nDeseja gera-lo? (y/n) ")
        return cadastro == "y"

GUIComponents = InterfaceComponentes()