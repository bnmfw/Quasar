"""
Graph Module. Used to model wich nodes of a circuit can propagate a fault to.
"""

class Graph:
    """
    Graph object.
    """
    def __init__(self, transistors: list, ignore: list):
        """
        Creates a graph given a transistor list.

            :param list[list[str]] transistors: List of transistors to be interpreted as vertices.
        """
        self.vertices: dict = {}
        self.ignore_list = ignore

        def put(lista: list, item):
            if not item in lista:
                lista.append(item)

        # Creates the graph from transistor files
        for transistor in transistors:
            source_name, gate_name, drain_name = transistor

            # Gets the source, gate and drain objects
            # Look I had to do it fast, didnt have much time, sorry
            if not source_name in ignore:
                if source_name not in self.vertices.keys(): self.vertices[source_name] = {"name": source_name, "sees": [], "reaches": []}
                source: set = self.vertices[source_name]
            if not gate_name in ignore:
                if gate_name not in self.vertices.keys(): self.vertices[gate_name] = {"name": gate_name, "sees": [], "reaches": []}
                gate: set = self.vertices[gate_name]
            if not drain_name in ignore:
                if drain_name not in self.vertices.keys(): self.vertices[drain_name] = {"name": drain_name, "sees": [], "reaches": []}
                drain: set = self.vertices[drain_name]

            # Creates the relationships
            if not drain_name in ignore and not source_name in ignore:
                put(drain["sees"], self.vertices[source_name])
                put(source["sees"], self.vertices[drain_name])
            if not drain_name in ignore and not gate_name in ignore:
                put(gate["sees"], self.vertices[drain_name])
            if not source_name in ignore and not gate_name in ignore:
                put(gate["sees"], self.vertices[source_name])
    
        for vi in self.vertices.values():
            vi["reaches"] = self.my_reach(vi["name"])
    
    def sees(self, source: str, target: str, already_seen: set = None) -> bool:
        """
        Returns whether or not source node sees the target. (DPS)

            :param str source: Source og the search.
            :param str target: Target of the search.
            :param str already_seen: A list of already seen vertices, used by recursive call.
        """

        # If there already is a reaches list
        if self.vertices[source]["reaches"] != []:
            return target in self.vertices[source]["reaches"]

        # Creates the already seen set if necessary
        if already_seen is None:
            already_seen = set()
        
        # Found it
        if source == target:
            return True

        # Stops infinite search
        if source in already_seen:
            return False

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for child in map(lambda e: e["name"], self.vertices[source]["sees"]):
            if self.sees(child, target, already_seen=already_seen):
                return True

        # If none of children sees it returns false
        return False

    def my_reach(self, source: str, already_seen: set = None) -> set:
        """
        Returns a set with the names of all vertices the source can see.
        """
        # Creates the already seen set if necessary
        if already_seen is None:
            already_seen = set()

        # Stops infinite search
        if source in already_seen:
            return False

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for child in map(lambda e: e["name"], self.vertices[source]["sees"]):
            self.my_reach(child, already_seen=already_seen)

        # If none of children sees it returns false
        return already_seen

if __name__ == "__main__":

    print("Testing Graph module...")

    transistors = [
        "vdd a1 p1_p2".split(),
        "p1_p2 b1 p2_n1".split(),
        "vdd a1 p3_p4".split(),
        "p3_p4 cin1 p2_n1".split(),
        "vdd b1 p3_p4".split(),
        "vdd cin1 p6_p9".split(),
        "vdd a1 p6_p9".split(),
        "vdd b1 p6_p9".split(),
        "p6_p9 p2_n1 p9_n6".split(),
        "vdd a1 p10_p11".split(),
        "p10_p11 b1 p11_p12".split(),
        "p11_p12 cin1 p9_n6".split(),
        "p2_n1 b1 n1_n2".split(),
        "n1_n2 a1 vdd".split(),
        "n4_n3 a1 vdd".split(),
        "p2_n1 cin1 n4_n3".split(),
        "n4_n3 b1 vdd".split(),
        "p9_n6 p2_n1 n6_n7".split(),
        "n6_n7 cin1 vdd".split(),
        "n6_n7 a1 vdd".split(),
        "n6_n7 b1 vdd".split(),
        "p9_n6 cin1 i10".split(),
        "i10 b1 i11".split(),
        "i11 a1 vdd".split(),
        "vdd p9_n6 sum".split(),
        "sum p9_n6 vdd".split(),
        "vdd p2_n1 cout".split(),
        "cout p2_n1 vdd".split(),
        "n6_n7 cin1 vdd".split(),
        "vdd sum nsum".split(),
        "nsum sum gnd".split(),
        "vdd cout ncout".split(),
        "ncout cout gnd".split()
    ]

    print("\tTesting sees method...")
    g = Graph(transistors, ["vdd", "gnd"])
    assert g.sees("p1_p2","cout"), "SEES FUNCTION FAILED"
    assert not g.sees("cout","p1_p2"), "SEES FUNCTION FAILED"
    print("\tTesting my_reach method...")
    assert g.my_reach("p1_p2") == {'p9_n6', 'p3_p4', 'i11', 'i10', 'n1_n2', 'p2_n1', 'p1_p2', 'n4_n3', 'p6_p9', 'p11_p12', 'n6_n7', 'sum', 'nsum', 'p10_p11', 'ncout', 'cout'}