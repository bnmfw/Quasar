"""
Spice Model Manager.
This class is responsible for managing the models imported by spice files
"""

from os import path, listdir
import re


class SpiceModel:
    """
    Represents a single spice model
    """

    def __init__(self, name: str, model_type: str, extra: str) -> None:
        """
        Constructor

        Args:
            name (str): model name.
            model_type (str): model type.
            extra (str): whatever else is in the model declaration besides name and type.
            model_atributes (list): list of lists of tuple atributes in the format (atribute,nominal value).
        """
        self.name = name
        self.model_type = model_type
        self.extra = extra
        self.model_atributes = []
        self.params = {}

    def append(self, atribute_line: list) -> None:
        """
        Adds a new atribute line to mode_atributes

        Args:
            atribute_line (list): the new atribute line in forma [(name,value)]
        """
        self.model_atributes.append(
            list(
                map(
                    lambda e: {
                        "name": e[0],
                        "nominal": float(e[1]),
                        "value": float(e[1]),
                    },
                    atribute_line,
                )
            )
        )

    def __setitem__(self, key: str, value: float) -> None:
        """
        Allows for altering the value of an atribute.

        Args:
            key (str): key for some atribute in model_atributes
            value (float): value to be assigned
        """
        for line in self.model_atributes:
            for model_atribute in line:
                if model_atribute["name"] != key.lower():
                    continue
                numeric: bool = True
                try:
                    value = float(value)
                except ValueError:
                    numeric = False

                if numeric:
                    model_atribute["value"] = value
                    if key in self.params:
                        self.params.pop(key)
                    return

                model_atribute["value"] = f"{key}_{self.name}_param"
                self.params[key] = value
                return

        raise ValueError(
            f"Model {self.name} does not contain the attribute {key.lower()}"
        )

    def __getitem__(self, key: str) -> float:
        """
        Allows for accesing the current value of an atribute

        Args:
            key (str): key for some atribute in model_atributess
        Returns:
            float: The associated value
        """
        for line in self.model_atributes:
            for model_atribute in line:
                if model_atribute["name"] != key.lower():
                    continue
                return model_atribute["value"]
        raise ValueError(
            f"Model {self.name} does not contain the attribute {key.lower()}"
        )

    def reset(self) -> None:
        """
        Resets all values to nominal
        """
        for line in self.model_atributes:
            for model_atribute in line:
                model_atribute["value"] = model_atribute["nominal"]

    def compiled(self) -> str:
        """
        Compiles a model string to be written

        Returns:
            str: the string that can be directly written to a file
        """
        tab = "\t"
        model_string = f".model {self.name} {self.model_type} {self.extra}\n"
        for atribute_line in self.model_atributes:
            model_string += (
                "+"
                + tab.join(
                    f'{att["name"].ljust(8)}= {str(att["value"]).ljust(10)}'
                    for att in atribute_line
                )
                + "\n"
            )
        return model_string


class SpiceModelManager:
    def __init__(self, circuit_file: str, path_to_folder="project") -> None:
        self.path_to_folder = path_to_folder
        self.models_name_used = self.parseCircuitFile(circuit_file)
        self.models = {}
        for filename in listdir(path.join(path_to_folder, "models")):
            self.parseModelFile(path.join(path_to_folder, "models", filename))

    def parseModelFile(self, filename: str) -> None:
        """
        Parses a model file and create spice models for used models

        Args:
            filename (str): filename
        """
        current_model: SpiceModel = None
        with open(filename, "r") as model_file:
            for i, line in enumerate(model_file):
                line = line.strip()
                if not i or not len(line) or line[0] == "*":
                    continue
                if line[0] == ".":
                    tokens = [t.lower() for t in line.split()]
                    if (
                        current_model is not None
                        and current_model.name in self.models_name_used
                    ):
                        self.models[current_model.name] = current_model
                    current_model = SpiceModel(
                        tokens[1], tokens[2], " ".join(tokens[3:])
                    )
                    {
                        "name": tokens[1],
                        "type": tokens[2],
                        "extra": " ".join(tokens[3:]),
                        "attributes": [],
                    }
                if line[0] == "+":
                    line = line[1:]
                    t = [e for e in re.split(r"[ =\n]", line) if e]
                    att = [(t[i].lower(), t[i + 1]) for i in range(0, len(t), 2)]
                    current_model.append(att)
            if (
                current_model is not None
                and current_model.name in self.models_name_used
            ):
                self.models[current_model.name] = current_model

    def writeModelFile(self) -> None:
        """
        Genrates the compiled model file and param file
        """
        with open(
            path.join(self.path_to_folder, "include", "models.pm"), "w"
        ) as model_file:
            model_file.write("*Quasar compiled model file\n\n")
            model: SpiceModel
            for model in self.models.values():
                model_file.write(model.compiled() + "\n")

        with open(
            path.join(self.path_to_folder, "include", "params.cir"), "w"
        ) as params_file:
            params_file.write("*Quasar compiled params file\n\n")
            for model in self.models.values():
                for param, value in model.params.items():
                    params_file.write(f".param {param}_{model.name}_param = {value}\n")

    def __getitem__(self, key: str) -> SpiceModel:
        """
        Returns a model

        Args:
            key (str): model_name
        """
        return self.models[key.lower()]

    def resetModel(self, model_name: str) -> None:
        """
        Resets a model atributes to nominal values

        Args:
            model_name (str): name of the model
        """
        self.models[model_name].reset()

    def parseCircuitFile(self, filename: str) -> set:
        """
        Parses a circuit file getting its models

        Args:
            filename (str): filename
        """
        with open(filename, "r") as circuit_file:
            model_names = set()
            for i, line in enumerate(circuit_file):
                line = line.strip()
                if not i or not len(line):
                    continue

                # A line starting with M identifies a transistor, wich means its connected to availabel nodes
                if "M" in line[0] or "X" in line[0]:
                    _, _, _, _, _, model, *_ = [token.lower() for token in line.split()]
                    model_names.add(model)
        return model_names
