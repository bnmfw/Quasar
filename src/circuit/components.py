from ..simconfig.simulationConfig import sim_config


class Signal_Input:
    """
    Object that represent an input signal, has a name and a logical signal
    """

    def __init__(self, name: str):
        self.name = name
        self.signal = "setup"

    def codec(self) -> dict:
        """
        Codifies the object into a dict.

        Returns:
            dict: Codifies the object
        """
        dic = {}
        dic["name"] = self.name
        dic["signal"] = self.signal
        return dic

    def decodec(self, dic: dict) -> None:
        """
        Decodifies the object. Codec method reciprocal.

        Args:
            dic (dict): Dictionary from wich the object will be decodified
        """
        self.name = dic["name"]
        self.signal = dic["signal"]

    def __repr__(self):
        return f"{self.name}:{self.signal}"


class LET:
    """
    LET object.
    Has the current or value of the fault, node where the fault originated and output interface to wich the fault propagates.
    Has all input states in wich the let is the same and the fault edge at the node struck and output.
    """

    def __init__(
        self,
        current: float,
        vdd: float,
        node_name: str,
        output_name: list,
        edges: list,
        input_states: list = None,
    ):
        """_summary_
        Args:
            current (float): Let current in micro amps. Can be None
            vdd (float): Voltage operation in volts.
            node_name (str): Name of the node the particle struck.
            output_name (list): Output interface the fault propagates to.
            edges (list[str]): Two element list. Both elements must be either 'rise', 'fall' or None
            input_states (list[bool], optional): Input states in witch the let is valid. Defaults to None.
        """
        self.value: float = None
        self.__current: float = current
        self.orientacao: list = edges
        self.vdd: float = vdd
        self.node_name: str = node_name
        self.output_name: str = output_name
        if input_states is None:
            self.input_states = []
        else:
            self.input_states = input_states
        self.var_table = {}

    @property
    def current(self) -> float:
        return self.__current

    @current.setter
    def current(self, current):
        self.__current = current
        self.value = sim_config.current_to_let(current)

    def __eq__(self, other):
        if self.semi_fault_config != other.semi_fault_config:
            return False
        return len(self.input_set & other.input_set)

    def __repr__(self):
        return f"{self.node_name} {self.output_name} {self.orientacao} {self.current}"

    def __len__(self):
        return len(self.input_states)

    def __lt__(self, other):
        return self.current < other.current

    def __le__(self, other):
        return self.current <= other.current

    def __gt__(self, other):
        return self.current > other.current

    def __ge__(self, other):
        return self.current >= other.current

    @property
    def input_set(self) -> set:
        return {"".join(inputs) for inputs in self.input_states}

    @property
    def semi_fault_config(self) -> tuple:
        """
        Returns:
            tuple: the semi fault configuration of the let
        """
        return (
            self.node_name,
            self.output_name,
            self.orientacao[0],
            self.orientacao[1],
        )

    @property
    def fault_config(self) -> tuple:
        """
        Returns:
            tuple: the fault configuration of the let
        """
        return (
            self.node_name,
            self.output_name,
            self.orientacao[0],
            self.orientacao[1],
            tuple(["".join(inputs) for inputs in self.input_states]),
        )

    def append(self, input_state: list):
        """
        Codifies the object into a dict.

        Returns:
            dict: Codifies the object
        """
        if type(input_state) != list:
            raise TypeError("Validacao nao eh uma lista")
        if not input_state in self.input_states:
            self.input_states.append(input_state)

    def codec(self) -> dict:
        """
        Codifies the object into a dict.

        Returns:
            dict: Codifies the object
        """
        dic = {}
        dic["corr"] = self.current
        dic["orie"] = self.orientacao
        dic["nodo"] = self.node_name
        dic["said"] = self.output_name
        dic["val"] = self.input_states
        return dic

    def decodec(self, dic: dict) -> None:
        """
        Decodifies the object. Codec method reciprocal.

        Args:
            dic (dict): Dictionary from wich the object will be decodified
        """
        if type(dic) != dict:
            raise TypeError(f"Nao recebi um dicionario, recebi {type(dic)}: {dic}")
        self.current = dic["corr"]
        self.orientacao = dic["orie"]
        self.node_name = dic["nodo"]
        self.output_name = dic["said"]
        self.input_states = dic["val"]


class Node:
    """
    Represents a circuit node. Has the collection of valid LETs that originate from it.
    """

    def __init__(self, name: str):
        self.name = name
        self.LETs: list[LET] = []
        # Eh um dicionario de dicionarios
        self.delay = {}

    def filter_let(self, let: LET) -> LET:
        """
        Runs through all the LETs already in the node. If it detects that the let already exists it returns that let, otherwise it just returns the input let

        Args:
            let (LET): The let analysed

        Returns:
            LET: Either the input let or an equivalent already in the circuit
        """
        for let_ in self.LETs:
            if let == let:
                return let_
        return let

    def add_let(self, let: LET) -> None:
        """
        Args:
            let (LET): Adds a let to the circuit's let list
        """
        for let_ in self.LETs:
            # The exact same let, diferent inputs
            if (
                let_.semi_fault_config == let.semi_fault_config
                and let_.current == let.current
            ):
                for input_state in let.input_states:
                    let_.append(input_state)
                return
        self.LETs.append(let)

    def __repr__(self):
        return f"<N>{self.name}"

    def codec(self) -> dict:
        """
        Codifies the object into a dict.

        Returns:
            dict: Codifies the object
        """
        dic = {}
        dic["name"] = self.name
        dic["delay"] = self.delay
        let_list = []
        let: LET
        for let in self.LETs:
            let_list.append(let.codec())
        dic["lets"] = let_list
        return dic

    def decodec(self, dic: dict):
        """
        Decodifies the object. Codec method reciprocal.

        Args:
            dic (dict): Dictionary from wich the object will be decodified
        """
        if not isinstance(dic, dict) or not isinstance(sim_config.vdd, (int, float)):
            raise TypeError(
                f"dic (dict): {type(dic)}, vdd (float): {type(sim_config.vdd)}"
            )
        self.name = dic["name"]
        self.delay = dic["delay"]
        for dicionario_let in dic["lets"]:
            let = LET(None, sim_config.vdd, "node", "output", ["edge", "edge"])
            let.decodec(dicionario_let)
            self.LETs.append(let)


if __name__ == "__main__":

    objeto_codificado = vars(LET(154.3, 0.7, "nodo1", "saida1", ["fall", "rise"]))
    print(objeto_codificado.values())
