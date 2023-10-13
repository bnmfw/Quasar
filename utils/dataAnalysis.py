import pandas as pd
from matplotlib import pyplot as plt

class DataAnalist:
    def __init__(self) -> None:
        plt.style.use('ggplot')

    def quantitative_scatter(self, data: dict, x: str, y: str, target: str, directory: str, cmap: str = "inferno"):
        """
        Draws a quantitative Scatter plot of the given data.

        Args:
            data (dict): Data given in form of a dictionary
            x (str): X axis label.
            y (str): Y axis label.
            target (str): Data to be plotted.
            directory (str): Directory in which the plot is to be saved.
            cmap (str, optional): Color style of the plot. Defaults to "inferno".
        """
        data = pd.DataFrame(data)
        plt.figure(figsize=(10,7))
        plt.scatter(data[x], data[y], marker='o', c=data[target], cmap=cmap)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend(loc='lower right', fontsize="x-large")
        plt.title(target)
        plt.colorbar()
        plt.savefig(f'{directory}/{target}_scatter.png', format='png', dpi=300)
    
    def qualitative_scatter(self, data: dict, x: str, y: str, target: str, directory: str):
        """
        Draws a quantitative Scatter plot of the given data.

        Args:
            data (dict): Data given in form of a dictionary
            x (str): X axis label.
            y (str): Y axis label.
            target (str): Data to be plotted.
            directory (str): Directory in which the plot is to be saved.
        """

        # Color generator
        color = (c for c in ['tab:blue','tab:orange','tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan'])

        plt.style.use('ggplot')
        data = pd.DataFrame(data)

        plt.figure(figsize=(10,7))

        for value in sorted(data[target].unique()):
            # Filter only data corresponding to designated value
            value_data = data[data[target]==value]

            # Plots all points corresponding to the value
            plt.scatter(value_data[x], value_data[y], marker="o", label=value, c=next(color))

        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend(loc='lower right', fontsize="x-large")
        plt.title(target)
        plt.savefig(f'{directory}/{target}_scatter.png', format='png', dpi=300)

    def describe(self, data: dict, directory: str):
        """
        Describes the main statistics of the data

        Args:
            data (dict): Data given in form of a dictionary.
            directory (str): directory in wich the data is to be saved.
        """
        
        data = pd.DataFrame(data)
        data.describe().to_csv(f"{directory}/description.csv")

if __name__ == "__main__":
    exit()
    scatter_data = {"PMOS": [],"NMOS":[],"node":[],"output":[],"current":[],"LETth":[],"pulse_in":[],"pulse_out":[]}
    with open(f"utils/nand_mc_LET.csv") as file:
        for linha in file:
            pmos, nmos, node, output, pulse_in, pulse_out, current, let, *inputs = linha.split(",")
            scatter_data["PMOS"].append(float(pmos))
            scatter_data["NMOS"].append(float(nmos))
            scatter_data["node"].append(node)
            scatter_data["output"].append(output)
            scatter_data["current"].append(float(current))
            scatter_data["LETth"].append(float(let))
            scatter_data["pulse_in"].append(pulse_in.strip("['").strip("'"))
            scatter_data["pulse_out"].append(pulse_in.strip("'").strip("']"))
    DataAnalist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "node", "utils")