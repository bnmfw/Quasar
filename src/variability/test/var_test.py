from ...utils.math import InDir, Time, compare_fault_config_lists
from ...simconfig.simulationConfig import sim_config
from ...spiceInterface.spiceRunner import HSpiceRunner
from ...circuit.circuit import Circuito
from ..distribution import SpiceGaussianDist
from ..mcManager import MCManager
from os import path
import json


def run_test(
        circuit: str,
        vdd: float,
        pvar_model: str,
        pvar_var: str,
        pvar_sigmas: float,
        pvar_std: float,
        nvar_model: str,
        nvar_var: str,
        nvar_sigmas: float,
        nvar_std: float,
        mcManager_kwargs: dict = {},
        single_threaded: bool = False,
        var_points: int = 20,
        ans_file: str = None,
    ):
    sim_config.runner_type = HSpiceRunner
    if sim_config.runner.test_spice():
        exit(1)
    sim_config.vdd = vdd

    print("\tTesting MC simulation...")
    with InDir("debug"):
        sim_config.circuit = Circuito(circuit).from_json()
        pvar_mean = sim_config.model_manager[pvar_model][pvar_var]
        nvar_mean = sim_config.model_manager[nvar_model][nvar_var]
        pvar = SpiceGaussianDist(pvar_model, pvar_var, pvar_mean, pvar_sigmas, pvar_std)
        nvar = SpiceGaussianDist(nvar_model, nvar_var, nvar_mean, nvar_sigmas, nvar_std)
        mc = MCManager(**mcManager_kwargs)
        mc.full_mc_analysis(var_points, [pvar, nvar], single_threaded=single_threaded)
        with open(mc.results_file, "r") as file:
            results_data = file.read()
        if (results_data.count("\n") != var_points):
            print("MC SIMULATION FAILED")
            return False

    if ans_file:
        with open(ans_file, "r") as file:
            ans = json.load(file)
        with InDir("debug"):
            with open(path.join(sim_config.circuit.path_to_my_dir, "Raw_data.csv"), "r") as file:
                data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))

        for line in data:
            line[4] = int(float(line[4]))
        if compare_fault_config_lists(data, ans):
            print("Results OK")
            return True
        else:
            print("Test Failed: Simulation results are different than expected")
            return False
    else:
        print("ans_file was not provided")
        return None

if __name__ == "__main__":
    test_config = {
        "circuit": "nand_fin",
        "vdd": 0.7,
        "pvar_model": "pmos_rvt",
        "pvar_var": "phig",
        "pvar_sigmas": 3,
        "pvar_std": 0.05,
        "nvar_model": "nmos_rvt",
        "nvar_var": "phig",
        "nvar_sigmas": 3,
        "nvar_std": 0.05,
        "mcManager_kwargs": {},
        "single_threaded": True,
        "var_points": 20,
        "ans_file": path.join("src", "variability", "test", "data", "nand_fin_fault_config_list.json"),
    }
    run_test(**test_config)

if __name__ == "__main__" and False:
    sim_config.runner_type = HSpiceRunner
    if sim_config.runner.test_spice():
        exit(1)
    sim_config.vdd = 0.7
    
    print("Testing MC Manager...")

    print("\tTesting MC simulation...")
    with InDir("debug"):
        nand = Circuito("nand_fin").from_json()
        sim_config.circuit = nand
        n = 500
        pvar = SpiceGaussianDist(
            "pmos_rvt", "phig", sim_config.model_manager["pmos_rvt"]["phig"], 3, 0.05
        )
        nvar = SpiceGaussianDist(
            "nmos_rvt", "phig", sim_config.model_manager["nmos_rvt"]["phig"], 3, 0.05
        )
        MCManager().full_mc_analysis(n, [pvar, nvar])
        with open(
            path.join("project", "circuits", "nand_fin", "nand_fin_mc_LET.csv"), "r"
        ) as file:
            assert file.read().count("\n") == n, "MC SIMULATION FAILED"

        with open(path.join(nand.path_to_my_dir, "Raw_data.csv"), "r") as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data:
                line[4] = int(float(line[4]))
            ans = [
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    226,
                    "01",
                    "4.7442987080000005",
                    "4.313604653333333",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    226,
                    "10",
                    "4.7442987080000005",
                    "4.313604653333333",
                ],
                ["g1", "g1", "fall", "fall", 247, "01", "4.8108", "4.372"],
                ["g1", "g1", "fall", "fall", 247, "10", "4.8108", "4.372"],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    251,
                    "01",
                    "4.8280387000000005",
                    "4.3524935933333335",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    251,
                    "10",
                    "4.8280387000000005",
                    "4.3524935933333335",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    265,
                    "01",
                    "4.882529028",
                    "4.494102673333333",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    265,
                    "10",
                    "4.882529028",
                    "4.494102673333333",
                ],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    144,
                    "11",
                    "4.882529028",
                    "4.494102673333333",
                ],
                ["g1", "g1", "rise", "rise", 176, "11", "4.8108", "4.372"],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    180,
                    "11",
                    "4.8280387000000005",
                    "4.3524935933333335",
                ],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    188,
                    "11",
                    "4.7442987080000005",
                    "4.313604653333333",
                ],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    226,
                    "10",
                    "4.7442987080000005",
                    "4.313604653333333",
                ],
                ["i1", "g1", "fall", "fall", 247, "10", "4.8108", "4.372"],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    252,
                    "10",
                    "4.8280387000000005",
                    "4.3524935933333335",
                ],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    265,
                    "10",
                    "4.882529028",
                    "4.494102673333333",
                ],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    246,
                    "11",
                    "4.882529028",
                    "4.494102673333333",
                ],
                ["i1", "g1", "rise", "rise", 286, "11", "4.8108", "4.372"],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    291,
                    "11",
                    "4.8280387000000005",
                    "4.3524935933333335",
                ],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    299,
                    "11",
                    "4.7442987080000005",
                    "4.313604653333333",
                ],
            ]
            assert compare_fault_config_lists(data, ans), "MC MANAGER FAILED"


if __name__ == "__main__" and False:
    with InDir("debug"):
        c17v3 = Circuito("c17v3").from_json()
        sim_config.circuit = c17v3
        n = var_points
        pvar = SpiceGaussianDist(
            "pmos_rvt", "phig", sim_config.model_manager["pmos_rvt"]["phig"], 3, 0.05
        )
        nvar = SpiceGaussianDist(
            "nmos_rvt", "phig", sim_config.model_manager["nmos_rvt"]["phig"], 3, 0.05
        )
        MCManager().full_mc_analysis(n, [pvar, nvar])

if __name__ == "__main__" and False:
        sim_config.vdd = 0.9
        nand = Circuito("nand").from_json()
        sim_config.circuit = nand
        # n = 4
        pvar = SpiceGaussianDist(
            "pmos", "vth0", sim_config.model_manager["pmos"]["vth0"], 3, 0.01
        )
        nvar = SpiceGaussianDist(
            "nmos", "vth0", sim_config.model_manager["nmos"]["vth0"], 3, 0.01
        )
        MCManager().full_mc_analysis(n, [pvar, nvar])
        with open(
            path.join("project", "circuits", "nand", "Raw_data.csv"), "r"
        ) as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data:
                line[4] = int(float(line[4]))
            ans = [
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    136,
                    "01",
                    "-0.506208021",
                    "0.4967190959066667",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    136,
                    "10",
                    "-0.506208021",
                    "0.4967190959066667",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    141,
                    "01",
                    "-0.49507277499999996",
                    "0.4935192230266667",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    141,
                    "10",
                    "-0.49507277499999996",
                    "0.4935192230266667",
                ],
                ["g1", "g1", "fall", "fall", 142, "01", "-0.49155", "0.49396"],
                ["g1", "g1", "fall", "fall", 142, "10", "-0.49155", "0.49396"],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    148,
                    "01",
                    "-0.477960281",
                    "0.4926404681866667",
                ],
                [
                    "g1",
                    "g1",
                    "fall",
                    "fall",
                    148,
                    "10",
                    "-0.477960281",
                    "0.4926404681866667",
                ],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    60,
                    "11",
                    "-0.506208021",
                    "0.4967190959066667",
                ],
                ["g1", "g1", "rise", "rise", 60, "11", "-0.49155", "0.49396"],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    60,
                    "11",
                    "-0.49507277499999996",
                    "0.4935192230266667",
                ],
                [
                    "g1",
                    "g1",
                    "rise",
                    "rise",
                    60,
                    "11",
                    "-0.477960281",
                    "0.4926404681866667",
                ],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    136,
                    "10",
                    "-0.506208021",
                    "0.4967190959066667",
                ],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    140,
                    "10",
                    "-0.49507277499999996",
                    "0.4935192230266667",
                ],
                ["i1", "g1", "fall", "fall", 142, "10", "-0.49155", "0.49396"],
                [
                    "i1",
                    "g1",
                    "fall",
                    "fall",
                    147,
                    "10",
                    "-0.477960281",
                    "0.4926404681866667",
                ],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    116,
                    "11",
                    "-0.506208021",
                    "0.4967190959066667",
                ],
                ["i1", "g1", "rise", "rise", 116, "11", "-0.49155", "0.49396"],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    116,
                    "11",
                    "-0.49507277499999996",
                    "0.4935192230266667",
                ],
                [
                    "i1",
                    "g1",
                    "rise",
                    "rise",
                    116,
                    "11",
                    "-0.477960281",
                    "0.4926404681866667",
                ],
            ]
            assert compare_fault_config_lists(data, ans), "MC MANAGER FAILED"

if __name__ == "__main__" and False:
    with InDir("debug"):
        sim_config.vdd = 0.7
        fadder = Circuito("fadder").from_json()
        sim_config.circuit = fadder
        n = var_points
        pvar = SpiceGaussianDist(
            "pmos_rvt", "phig", sim_config.model_manager["pmos_rvt"]["phig"], 3, 0.05
        )
        nvar = SpiceGaussianDist(
            "nmos_rvt", "phig", sim_config.model_manager["nmos_rvt"]["phig"], 3, 0.05
        )
        MCManager().full_mc_analysis(n, [pvar, nvar])

    print("MC Manager OK")
