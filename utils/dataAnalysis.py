import pandas as pd
from matplotlib import pyplot as plt

class DataAnalist:
    def draw_scatter(data: dict, x: str, y: str, target: str, directory: str, cmap: str = "inferno"):
        """
        Draws a Scatter plot of the given data.

        Args:
            data (dict): Data given in form of a dictionary
            x (str): X axis label.
            y (str): Y axis label.
            target (str): Data to be plotted.
            directory (str): Directory in which the plot is to be saved.
            cmap (str, optional): Color style of the plot. Defaults to "inferno".
        """
        plt.style.use('ggplot')
        data = pd.DataFrame(data)

        plt.figure(figsize=(10,7))
        plt.scatter(data[x], data[y], marker='o', c=data[target], cmap=cmap)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend(loc='lower right', fontsize="x-large")
        plt.title(target)
        plt.colorbar()
        plt.savefig(f'{directory}/letth_scatter.png', format='png', dpi=300)

if __name__ == "__main__":
    pass
    # sample_data = {"PMOS": [],"NMOS":[],"node":[],"output":[],"current":[],"LET":[]}
    # with open("utils/nand_mc_LET.csv") as file:
    #     for linha in file:
    #         pmos, nmos, node, output, current, let = linha.split(",")
    #         sample_data["PMOS"].append(float(pmos))
    #         sample_data["NMOS"].append(float(nmos))
    #         sample_data["node"].append(node)
    #         sample_data["output"].append(output)
    #         sample_data["current"].append(float(current))
    #         sample_data["LET"].append(float(let))
    # DataAnalist.draw_scatter(sample_data, "PMOS", "NMOS", "LET", "utils")