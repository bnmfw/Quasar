"""
Graph Module. Used to model wich nodes of a circuit can propagate a fault to and logically simulate a circuit.
"""

from ..utl.math import all_vector_n_bits
from typing import Callable


class LogicSimulationError(Exception):
    pass


class Graph:
    """
    Graph object.
    """

    def __init__(self, transistors: list, fixed: list):
        """
        Creates a graph given a transistor list.

            :transistors (list[tuple[int or None, list[str]]]): List of transistors in the form: (if it was p type, nodes).
            :ignore (list[str]): List of nodes to be ignored in the moddeling.
            :fixed (list[str]): List of nodes that should not be passed through a search (i.g. vdd or gnd)
        """
        self.vertices: dict = {}
        self.transistors: list = []
        self.fixed: set = set(fixed)
        self.input_nodes: set = set()
        self.regions: list = []
        # regions are groups of nodes that see each other through terminals only

        # Creates all nodes
        for is_pmos, transistor in transistors:
            _, gate, _ = transistor
            for node in transistor:
                if not node in self.vertices.keys():
                    self.vertices[node] = {
                        "name": node,
                        "signal": None,
                        "reaches": [],
                        "fall_valid": False,
                        "rise_valid": False,
                        "region": None,
                    }
                if node == gate:
                    continue
                if is_pmos:
                    self.vertices[node]["rise_valid"] = True
                else:
                    self.vertices[node]["fall_valid"] = True

        for name, vertice in self.vertices.items():
            if name in self.fixed or {"a", "b", "cin"}:
                continue
            if not vertice["rise_valid"]:
                print(f"{name}: rise invalid")
            if not vertice["fall_valid"]:
                print(f"{name}: fall invalid")

        # Connects all existing arcs
        for invert, transistor in transistors:
            invert = invert == 1
            source, gate, drain = transistor
            # Creates the relationships
            self.transistors.append(
                {
                    "terminals": (drain, source),
                    source: drain,
                    drain: source,
                    "invert": invert,
                    "control": gate,
                }
            )

        self.transistors = sorted(self.transistors, key=lambda e: e["control"])

        for name, v in self.vertices.items():
            v["terminal"] = list(
                filter(lambda e: name in e["terminals"], self.transistors)
            )
            v["control"] = list(
                filter(lambda e: e["control"] == name, self.transistors)
            )

        # Determines all regions
        seen = set()
        for node in self.vertices:
            if node in seen or node in self.fixed:
                continue
            seen.add(node)
            self.vertices[node]["region"] = {
                "id": len(self.regions),
                "nodes": [node],
                "before": [],
                "after": [],
            }
            self.regions.append(self.vertices[node]["region"])

            dfs = [node]
            dfs_seen = set()
            while len(dfs):
                node = dfs.pop()
                if node in dfs_seen:
                    continue
                seen.add(node)
                dfs_seen.add(node)
                for trans in self.vertices[node]["terminal"]:
                    if trans[node] in self.fixed or trans[node] in dfs_seen:
                        continue
                    self.vertices[trans[node]]["region"] = self.vertices[node]["region"]
                    self.vertices[trans[node]]["region"]["nodes"].append(trans[node])
                    dfs.append(trans[node])

        # Determines region dependency
        for trans in self.transistors:
            if trans["control"] in self.fixed:
                continue
            region_c = self.vertices[trans["control"]]["region"]
            node = (
                trans["terminals"][0]
                if trans["terminals"][0] not in self.fixed
                else trans["terminals"][1]
            )
            region_t = self.vertices[node]["region"]

            if region_c == region_t:
                raise LogicSimulationError("Feedback Loop in region")

            if region_c not in region_t["before"]:
                region_t["before"].append(region_c)
            if region_t not in region_c["after"]:
                region_c["after"].append(region_t)

        def topological_sort_util(region, visited, rec_stack, stack):
            visited[region["id"]] = True
            rec_stack[region["id"]] = True

            for neigh in region["after"]:
                if not visited[neigh["id"]]:
                    if topological_sort_util(neigh, visited, rec_stack, stack):
                        return True
                elif rec_stack[neigh["id"]]:
                    raise LogicSimulationError("Loop between regions")

            rec_stack[region["id"]] = False
            stack.append(region)
            return False

        def topological_sort():
            visited = {region["id"]: False for region in self.regions}
            rec_stack = {region["id"]: False for region in self.regions}
            stack = []

            for region in self.regions:
                if not visited[region["id"]]:
                    if topological_sort_util(region, visited, rec_stack, stack):
                        raise LogicSimulationError("Loop between regions")

            stack.reverse()  # Reverse the stack to get the order
            return stack

        # for region in self.regions:
        #     print(f'{region["nodes"]} before: {[r["nodes"] for r in region["before"]]} after: {[r["nodes"] for r in region["after"]]}')

        self.regions = topological_sort()

    def conducting(self, transistor: dict) -> bool:
        """
        Return wether or not a transistor is conducting
        """

        if self.vertices[transistor["control"]]["signal"] is None:
            return False

        if self.vertices[transistor["control"]]["signal"] == transistor["invert"]:
            return False

        return True

    def sees(self, source: str, target: str, already_seen: set = None) -> bool:
        """
        Returns whether or not source node sees the target. (DPS)

        Args:
            source (str): Source of search
            target (str): Target of search
            already_seen (set, optional): A list of already seen vertices, used by recursive call. Defaults to None.

        Returns:
            bool: Whether or not source node sees the target
        """

        # If there already is a reaches list
        if self.vertices[source]["reaches"] != []:
            return target in self.vertices[source]["reaches"]

        # Creates the already seen set if necessary
        original = False
        if already_seen is None:
            original = True
            already_seen = set()

        # A search should never go through a fixed node
        if not original and source in self.fixed:
            return False

        # Found it
        if source == target:
            return True

        # Stops infinite search
        if source in already_seen:
            return False

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for trans in self.transistors:
            if source in trans["terminals"] and self.sees(
                trans[source], target, already_seen=already_seen
            ):
                return True
            if trans["control"] == source and (
                self.sees(trans["terminals"][0], target, already_seen=already_seen)
                or self.sees(trans["terminals"][1], target, already_seen=already_seen)
            ):
                return True

        # If none of children sees it returns false
        return False

    def my_reach(self, source: str, already_seen: set = None) -> set:
        """
        Returns a set with the names of all vertices the source can see.

        Args:
            source (str): Node that will have its reach defined.
            already_seen (set, optional): A list of already seen vertices, used by recursive call. Defaults to None.

        Returns:
            set: Set with the names of all vertices the source can see.
        """
        # ""
        # Returns a set with the names of all vertices the source can see.

        #     :source (str): Node that will have its reach defined.
        # ""
        # Creates the already seen set if necessary
        original = False
        if already_seen is None:
            original = True
            already_seen = set()

        # A search should never go through a fixed node
        if not original and source in self.fixed:
            return

        # Stops infinite search
        if source in already_seen:
            return

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for trans in self.transistors:
            if source in trans["terminals"]:
                self.my_reach(trans[source], already_seen=already_seen)
            if trans["control"] == source:
                self.my_reach(trans["terminals"][0], already_seen=already_seen)
                self.my_reach(trans["terminals"][1], already_seen=already_seen)

        # If none of children sees it returns false
        return already_seen

    def set_logic(self, input_list: list) -> None:
        """
        Given input values sets the logic value of all vertices. Must contain vdd, gnd and other tension sources

        Args:
            input_list (list): List of tuples on the format (vertice_name, 0 or 1). The list MUST contain vdd, gnd, etc... i.g. (vdd, 1), (gnd, 0).
        """
        # Resets all logic
        for v in self.vertices.values():
            v["signal"] = None

        # Sets the values of all inputs
        input_list = list(filter(lambda e: e[0] in self.vertices, input_list))
        for node, sig in input_list:
            self.vertices[node]["signal"] = sig
            if node not in self.fixed:
                self.input_nodes.add(node)

        # Recursivelly propagates logic
        def recursive_propagation(node: str):

            # Propagates signal to all nodes in region
            # Iterates over arcs starting from the node
            for trans in self.vertices[node]["terminal"]:

                # Arc's controller doesnt allow passing
                if not self.conducting(trans):
                    continue

                # Destiny already has a logic value
                if not self.vertices[trans[node]]["signal"] is None:
                    if (
                        self.vertices[trans[node]]["signal"]
                        != self.vertices[node]["signal"]
                    ):
                        raise LogicSimulationError(
                            "Tried to flip a bit during set logic"
                        )
                    continue

                # Sets the destiny value equal to its own and propagates from it
                self.vertices[trans[node]]["signal"] = self.vertices[node]["signal"]
                recursive_propagation(trans[node])

            # Propagates signal to controlled nodes
            for trans in self.vertices[node]["control"]:

                # I dont allow passing through this transistor
                if not self.conducting(trans):
                    continue

                a_sig = self.vertices[trans["terminals"][0]]["signal"]
                b_sig = self.vertices[trans["terminals"][1]]["signal"]

                # No signal to propagate
                if a_sig is None and b_sig is None:
                    continue

                # This arc conducting SHOULD not change anything
                if a_sig is not None and b_sig is not None:
                    if a_sig != b_sig:
                        raise LogicSimulationError(
                            "Origin and destiny signal are different and they connect"
                        )
                    continue

                if a_sig is not None:
                    recursive_propagation(trans["terminals"][0])

                if b_sig is not None:
                    recursive_propagation(trans["terminals"][1])

        # Propagates
        for node, _ in input_list:
            recursive_propagation(node)

    def is_affected_by(self, node: str, already_seen: set = None) -> set:
        """
        Considering a logical configurates searches the nodes that if changed might affect the node.

        Args:
            node (str): node that is to be affected.
            already_seen (set, optional): Recursive set, not to be inputed. Defaults to None.

        Returns:
            set: All the nodes that might affect the given node.
        """

        # Creates the propagated set
        if already_seen is None:
            already_seen = set()

        # Stops if job has already been done
        if node in set(map(lambda e: e[0], already_seen)):
            return

        # No propagation should be done through fixed nodes
        if node in self.fixed:
            return

        already_seen.add((node, self.vertices[node]["signal"]))

        # Iterates over arcs that go to node
        for trans in self.vertices[node]["terminal"]:

            # Arc's controller always affects node
            self.is_affected_by(trans["control"], already_seen)

            # Arc's controller doesnt allow passing
            # TODO: Does a floating arc on pmos allow passing? Maybe.
            if (
                self.vertices[trans["control"]]["signal"] is None
                or self.vertices[trans["control"]]["signal"] == trans["invert"]
            ):
                continue

            # Propagates search
            self.is_affected_by(trans[node], already_seen)

        return already_seen

    def valid_orientation(self, node: str, orientation: str) -> bool:
        """
        Given a node and a fault orientation returns wether or not said orientation is possible

        Args:
            node (str): node faulted
            orientation (str): orientation, either 'rise', 'fall',

        Returns:
            bool: if the orientation is valid
        """

        if orientation == "rise":
            return self.vertices[node]["rise_valid"]
        return self.vertices[node]["fall_valid"]

    # Updates signals of a region
    def region_update(self, region: dict, special_node: str):

        if len(region["nodes"]) == 1 and region["nodes"][0] in self.input_nodes:
            return

        special_region: bool = (
            special_node is not None and special_node in region["nodes"]
        )

        dfs = list(filter(lambda n: n in self.vertices, self.fixed))
        if special_region:
            dfs += [special_node]
        seen = set()
        report = special_region and False

        while len(dfs):
            node = dfs.pop()

            if node in seen:
                continue
            seen.add(node)

            # Conducting nodes
            for trans in self.vertices[node]["terminal"]:
                if not self.conducting(trans):
                    continue

                other = trans[node]

                # Node out of region
                if other not in region["nodes"]:
                    continue

                # Cant change fixed node
                if (
                    other in self.fixed
                    or other in self.input_nodes
                    or other == special_node
                ):
                    continue

                # Other node already has a signal
                if self.vertices[other]["signal"] is not None:
                    if (
                        self.vertices[other]["signal"] != self.vertices[node]["signal"]
                        and not special_region
                    ):
                        raise LogicSimulationError(
                            f"Inconsistent node signal during simulation between {node} {other}"
                        )
                    else:
                        continue

                self.vertices[other]["signal"] = self.vertices[node]["signal"]
                dfs.append(other)

    def simulate_fault(self, faulted_node: str, output: str) -> bool:
        """
        Assumes the "set logic" method is already set.
        Flips the faulted_node signal and returns if the output was fliped.

        Args:
            faulted_node (str): Faulted node.
            output (str): Output measured.

        Returns:
            bool: Wether or not flipping the node logical value flipped the outputs.
        """

        if faulted_node in self.fixed:
            return False

        # Floating node will never affect an output
        # TODO: It actually can as it can switch a gate on or off
        if self.vertices[faulted_node]["signal"] is None:
            return False

        old_output = self.vertices[output]["signal"]

        # Determines if node had its signal updated
        updated = {v: False for v in self.vertices}
        updated[faulted_node] = True

        # Flips the node
        self.vertices[faulted_node]["signal"] = not self.vertices[faulted_node][
            "signal"
        ]

        # Resets all logic
        for name, v in self.vertices.items():
            if name in self.fixed or name in self.input_nodes or name == faulted_node:
                continue
            v["signal"] = None

        for region in self.regions:
            self.region_update(region, faulted_node)

        # Output changed signal and is not floating
        return (
            old_output != self.vertices[output]["signal"]
            and self.vertices[output]["signal"] != None
        )

    def generate_valid_let_configs(
        self, nodes: list, outputs: list, inputs: list, get_node_callback: Callable
    ) -> list:
        """
        Generates all valid let configs

        Args:
            nodes (list[str]): List of circuit node names
            outputs (list[str]): List of circuit output names
            inputs (list[str]): List of circuit input names
            get_node_callback (Callable): Callable function that returns

        Returns:
            list: all valid lets
        """
        lets_f1 = []
        # Iterates over all input combinations
        for signals in all_vector_n_bits(len(inputs)):
            # Sets the inputs
            logic_signals = [(inp, sig == 1) for inp, sig in zip(inputs, signals)] + [
                ("vdd", True),
                ("vcc", True),
                ("gnd", False),
                ("vss", False),
            ]
            self.set_logic(logic_signals)
            for output in outputs:
                # Gets the nodes that affect it. effect_group is a list of format (node, signal)
                effect_group = list(
                    filter(lambda e: e[0] in nodes, self.is_affected_by(output))
                )
                for nodo in effect_group:
                    if nodo[0] == output:
                        output_dir = (
                            "fall" if nodo[1] else "rise" if nodo[1] == 0 else None
                        )
                        break
                lets_f1 += [
                    [
                        get_node_callback(node[0]),
                        get_node_callback(output),
                        signals,
                        "fall" if node[1] else "rise" if node[1] == 0 else None,
                        output_dir,
                    ]
                    for node in effect_group
                ]

        # Filters orientations that cannot happen due to no nmos or pmos contact
        lets_f2 = list(
            filter(lambda let: self.valid_orientation(let[0].name, let[3]), lets_f1)
        )

        # Filter lets that only actually propagate a fault to output
        lets_f3 = []
        for let in lets_f2:
            faulty_node, output, signals, *_ = let
            logic_signals = [(inp, sig == 1) for inp, sig in zip(inputs, signals)] + [
                ("vdd", True),
                ("vcc", True),
                ("gnd", False),
                ("vss", False),
            ]
            self.set_logic(logic_signals)
            ans = self.simulate_fault(faulty_node.name, output.name)
            if ans:
                lets_f3 += [let]

        return lets_f3

    def __repr__(self) -> str:
        ret = "Nodes:\n"
        for v, vi in self.vertices.items():
            ret += f"\t{v}: {vi['signal']}\n"
        ret += "Arcs:\n"
        for arc in self.arcs:
            # if not arc["conduct"]: continue
            ret += f"\t{arc['from']} --{'p' if arc['invert'] else 'n'}-{arc['control']}--> {arc['to']}\n"
        return ret


if __name__ == "__main__":

    print("Testing Logic module...")

    fadder = [
        (1, "vdd ta p1_p2".split()),
        (1, "p1_p2 tb p2_n1".split()),
        (1, "vdd ta p3_p4".split()),
        (1, "vdd tb p3_p4".split()),
        (1, "p3_p4 tcin p2_n1".split()),
        (1, "vdd tcin p6_p9".split()),
        (1, "vdd ta p6_p9".split()),
        (1, "vdd tb p6_p9".split()),
        (1, "p6_p9 p2_n1 p9_n6".split()),
        (1, "vdd ta p10_p11".split()),
        (1, "p10_p11 tb p11_p12".split()),
        (1, "p11_p12 tcin p9_n6".split()),
        (0, "p2_n1 tb n1_n2".split()),
        (0, "n1_n2 ta gnd".split()),
        (0, "n4_n3 ta gnd".split()),
        (0, "p2_n1 tcin n4_n3".split()),
        (0, "n4_n3 tb gnd".split()),
        (0, "p9_n6 p2_n1 n6_n7".split()),
        (0, "n6_n7 tcin gnd".split()),
        (0, "n6_n7 ta gnd".split()),
        (0, "n6_n7 tb gnd".split()),
        (0, "p9_n6 tcin i10".split()),
        (0, "i10 tb i11".split()),
        (0, "i11 ta gnd".split()),
        (1, "vdd p9_n6 sum".split()),
        (0, "sum p9_n6 gnd".split()),
        (1, "vdd p2_n1 cout".split()),
        (0, "cout p2_n1 gnd".split()),
        (1, "vdd sum nsum".split()),
        (0, "nsum sum gnd".split()),
        (1, "vdd cout ncout".split()),
        (0, "ncout cout gnd".split()),
    ]

    nor = [
        (1, "vdd a i".split()),
        (1, "i b s".split()),
        (0, "s a gnd".split()),
        (0, "s b gnd".split()),
    ]

    nots = [
        (1, "vdd a b".split()),
        (0, "b a gnd".split()),
        (1, "vdd b c".split()),
        (0, "c b gnd".split()),
    ]

    mux_v1 = [
        (1, "vdd select n1".split()),
        (0, "n1 select gnd".split()),
        (1, "vdd n1 x1".split()),
        (1, "vdd a x1".split()),
        (0, "x1 n1 n2".split()),
        (0, "n2 a gnd".split()),
        (1, "vdd select x2".split()),
        (1, "vdd b x2".split()),
        (0, "x2 select n3".split()),
        (0, "n3 b gnd".split()),
        (1, "vdd x2 out".split()),
        (1, "vdd x1 out".split()),
        (0, "out x1 n4".split()),
        (0, "n4 x2 gnd".split()),
        (1, "vdd ina a2".split()),
        (0, "a2 ina gnd".split()),
        (1, "vdd a2 a".split()),
        (0, "a a2 gnd".split()),
        (1, "vdd inb b2".split()),
        (0, "b2 inb gnd".split()),
        (1, "vdd b2 b".split()),
        (0, "b b2 gnd".split()),
        (1, "vdd insel sel2".split()),
        (0, "sel2 insel gnd".split()),
        (1, "vdd sel2 select".split()),
        (0, "select sel2 gnd".split()),
        (1, "vdd out sc1".split()),
        (0, "sc1 out gnd".split()),
        (1, "vdd sc1 sc2".split()),
        (0, "sc2 sc1 gnd".split()),
    ]

    g = Graph(fadder, ["vdd", "gnd"])
    print("\tTesting sees method...")
    assert g.sees("p1_p2", "cout"), "SEES FUNCTION FAILED"
    assert not g.sees("cout", "p1_p2"), "SEES FUNCTION FAILED"

    print("\tTesting my_reach method...")
    assert g.my_reach("p1_p2") == {
        "p9_n6",
        "p3_p4",
        "i11",
        "i10",
        "n1_n2",
        "p2_n1",
        "p1_p2",
        "n4_n3",
        "p6_p9",
        "p11_p12",
        "n6_n7",
        "sum",
        "nsum",
        "p10_p11",
        "ncout",
        "cout",
    }

    print("\tTesting set_logic method...")
    g.set_logic([("ta", 1), ("tb", 0), ("tcin", 1), ("vdd", 1), ("gnd", 0)])
    assert list(map(lambda e: e["signal"], g.vertices.values())) == [
        1,
        1,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        None,
        None,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        1,
        1,
        0,
    ], "SET LOGIC FUNCTION FAILED"

    print("\tTesting is affected_by method...")
    assert set(map(lambda e: e[0], g.is_affected_by("sum"))) == {
        "i10",
        "ta",
        "tb",
        "p2_n1",
        "p6_p9",
        "p9_n6",
        "n4_n3",
        "p1_p2",
        "sum",
        "tcin",
    }, "IS AFFECTED BY FUNCTION FAILED"
    g.set_logic([("ta", 0), ("tb", 0), ("tcin", 0), ("vdd", 1), ("gnd", 0)])
    assert set(map(lambda e: e[0], g.is_affected_by("sum"))) == {
        "ta",
        "tcin",
        "p9_n6",
        "tb",
        "p3_p4",
        "p1_p2",
        "p11_p12",
        "n6_n7",
        "p10_p11",
        "sum",
        "p2_n1",
    }, "IS AFFECTED BY FUNCTION FAILED"

    print("\tTesting valid_orientation method...")
    assert not g.valid_orientation("p6_p9", "fall") and g.valid_orientation(
        "sum", "rise"
    ), "ORIENTATION VALIDATION FAILED"

    print("\tTesting simulate_fault method...")
    propag_test = Graph(nor, ["vdd", "gnd"])
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 1), ("b", 0)])
    assert propag_test.simulate_fault("i", "s"), "FAULT SIMULATION FAILED"
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 0), ("b", 1)])
    assert not propag_test.simulate_fault("i", "s"), "FAULT SIMULATION FAILED"
    # propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 0), ("b", 0)])
    # assert propag_test.simulate_fault("a", "s"), "FAULT SIMULATION FAILED"
    # propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 1), ("b", 1)])
    # assert not propag_test.simulate_fault("a", "s"), "FAULT SIMULATION FAILED"
    propag_test2 = Graph(mux_v1, ["vdd", "gnd"])
    propag_test2.set_logic(
        [("vdd", 1), ("gnd", 0), ("ina", 0), ("inb", 1), ("insel", 1)]
    )
    assert propag_test2.simulate_fault("n4", "sc2"), "FAULT SIMULATION FAILED"

    print("Logic Module OK")
