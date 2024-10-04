import pandas as pd
from matplotlib import pyplot as plt
from os import path


class DataAnalist:
    def __init__(self) -> None:
        plt.style.use("ggplot")

    def quantitative_scatter(
        self,
        data: dict,
        x: str,
        y: str,
        target: str,
        directory: str,
        cmap: str = "winter",
    ):
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
        plt.figure(figsize=(10, 7))

        # plt.scatter(data[x], data[y], marker='o', c=data[target], cmap=cmap)

        # Separate positive and negative values
        data[target] = data[target] * 1e-6
        positive_data = data[data[target] >= 0]
        negative_data = data[data[target] < 0]

        vmin = data[target].min()
        vmax = data[target].max()

        # Plot positive values with 'X' marker
        scatter1 = plt.scatter(
            positive_data[x],
            positive_data[y],
            marker="1",
            c=positive_data[target],
            cmap=cmap,
            label="TG",
            vmin=vmin,
            vmax=vmax,
        )

        # Plot negative values with 'O' marker
        scatter2 = plt.scatter(
            negative_data[x],
            negative_data[y],
            marker="o",
            c=negative_data[target],
            cmap=cmap,
            label="CMOS",
            vmin=vmin,
            vmax=vmax,
        )

        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend(loc="lower right", fontsize="x-large")
        plt.title(target)
        plt.colorbar(scatter1)
        plt.savefig(
            path.join(directory, f"{target}_scatter.png"), format="png", dpi=300
        )

    def qualitative_scatter(
        self, data: dict, x: str, y: str, target: str, directory: str
    ):
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
        color = (
            c
            for c in [
                "tab:blue",
                "tab:orange",
                "tab:green",
                "tab:red",
                "tab:purple",
                "tab:brown",
                "tab:pink",
                "tab:gray",
                "tab:olive",
                "tab:cyan",
            ]
        )

        plt.style.use("ggplot")
        data = pd.DataFrame(data)

        plt.figure(figsize=(10, 7))

        for value in sorted(data[target].unique()):
            # Filter only data corresponding to designated value
            value_data = data[data[target] == value]

            # Plots all points corresponding to the value
            plt.scatter(
                value_data[x], value_data[y], marker="o", label=value, c=next(color)
            )

        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend(loc="lower right", fontsize="x-large")
        plt.title(target)
        plt.savefig(
            path.join(directory, f"{target}_scatter.png"), format="png", dpi=300
        )

    def describe(self, data: dict, directory: str):
        """
        Generates a csv describing the main statistics of the data.

        Args:
            data (dict): Data given in form of a dictionary.
            directory (str): directory in wich the data is to be saved.
        """

        data = pd.DataFrame(data)
        data.describe().to_csv(path.join(directory, "description.csv"))

    def count_unique(self, data: dict, target: str, directory: str):
        """
        Generates a csv countainig the count of each unique value in target column.

        Args:
            data (dict): Data given in form of a dictionary
            target (str): Data to be plotted.
            directory (str): Directory in which the plot is to be saved.
        """
        # Finds all unique values
        unique: dict = {}
        for value in data[target]:
            if value not in unique:
                unique[value] = 0
            unique[value] += 1

        # Puts data in csv
        csv = ",count,ratio\n"
        for value, count in unique.items():
            csv += f"{value},{count},{count/len(data[target])}\n"

        with open(path.join(directory, f"{target}_count.csv"), "w") as file:
            file.writelines(csv)


if __name__ == "__main__":
    # scatter_data = {"PMOS": [], "NMOS": [], "Best Version":[]}
    # with open("graph.csv", "r") as file:
    #     for i, linha in enumerate(file):
    #         if not i: continue
    #         best, pmos, nmos = linha.split(",")
    #         scatter_data["PMOS"].append(float(pmos))
    #         scatter_data["NMOS"].append(float(nmos))
    #         scatter_data["Best Version"].append(best)
    # DataAnalist().qualitative_scatter(scatter_data, "PMOS", "NMOS", "Best Version", ".")
    title = "LETth Difference (MeVcm²mg⁻¹)"
    scatter_data = {"PMOS": [], "NMOS": [], title: []}
    with open("xorcomp.csv", "r") as file:
        for i, linha in enumerate(file):
            if not i:
                continue
            pmos, nmos, best = linha.split(",")
            scatter_data["PMOS"].append(float(pmos))
            scatter_data["NMOS"].append(float(nmos))
            scatter_data[title].append(-float(best))
    DataAnalist().quantitative_scatter(scatter_data, "PMOS", "NMOS", title, ".")
    exit()
    scatter_data = {
        "PMOS": [],
        "NMOS": [],
        "node": [],
        "output": [],
        "current": [],
        "LETth": [],
        "pulse_in": [],
        "pulse_out": [],
    }
    with open(f"utils/nand_mc_LET.csv") as file:
        for linha in file:
            pmos, nmos, node, output, pulse_in, pulse_out, current, let, *inputs = (
                linha.split(",")
            )
            scatter_data["PMOS"].append(float(pmos))
            scatter_data["NMOS"].append(float(nmos))
            scatter_data["node"].append(node)
            scatter_data["output"].append(output)
            scatter_data["current"].append(float(current))
            scatter_data["LETth"].append(float(let))
            scatter_data["pulse_in"].append(pulse_in.strip("['").strip("'"))
            scatter_data["pulse_out"].append(pulse_in.strip("'").strip("']"))
    DataAnalist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "node", "utils")
