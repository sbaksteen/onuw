from mlsolver.kripke import *
from mlsolver.formula import *
from more_itertools import distinct_permutations as dp
import networkx as nx
import matplotlib.pyplot as plt
from functools import reduce
import pygraphviz
import sys


AGENTS = ['a', 'b', 'c', 'd', 'e']
ROLES = ['t', 'w', 's', 'f', 'm']

class WerewolvesGame:
    def __init__(self, roles):
        self.num_players = len(roles)
        self.roles = roles
        worlds = [World(''.join(x), {r + AGENTS[i]: True for (i, r) in enumerate(x)}) for x in dp(roles)]
        relations = {AGENTS[i]: set((a.name, b.name) for a in worlds for b in worlds if a.name[i] == b.name[i]) for i in range(self.num_players)}
        self.kripke = KripkeStructure(worlds, relations)

    def plot_knowledge(self):
        G = nx.DiGraph()
        nodes = self.kripke.worlds.keys()
        edges     = [(w, v, {'label': ''.join([a for a in AGENTS[:self.num_players] if (w,v) in self.kripke.relations[a]])})
                     for (w, v) in reduce(lambda x, y : x.union(y), self.kripke.relations.values()) if w != v]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges) 
        pos = nx.nx_agraph.graphviz_layout(G)
        nodenames = {n: "\n".join(n.split(",")) for n in G.nodes}
        numlines = list(G.nodes.keys())[0].count(",")+1
        nx.draw(G, pos, with_labels=True, labels=nodenames, node_size=400 * max(self.num_players, numlines*1.5))
        if (self.num_players < 5):
            nx.draw_networkx_edge_labels(G, pos, {(w,v):l for (w,v,l) in G.edges(data="label")})
        plt.show()

    def apply_action_model(self, action_model):
        worlds = self.kripke.worlds.values()
        new_world_pairs = [(w, a) for w in worlds for a in action_model.actions if a.precon.semantic(self.kripke, w.name)]
        new_worlds = [World(f"{w.name},{a.name}", w.assignment) for (w,a) in new_world_pairs]
        new_relations = {i: set((f"{w1.name},{a1.name}", f"{w2.name},{a2.name}") 
                                for (w1, a1) in new_world_pairs for (w2, a2) in new_world_pairs
                                if (w1.name, w2.name) in self.kripke.relations[i] and 
                                    (a1.name, a2.name) in action_model.equivs[i])
                            for i in AGENTS[:self.num_players]}
        self.kripke = KripkeStructure(new_worlds, new_relations)
    
class ActionModel:
    def __init__(self, actions, equivs):
        self.actions = actions
        self.equivs = equivs

class Action:
    def __init__(self, name, precon):
        self.name = name
        self.precon = precon

class WerewolfActionModel(ActionModel):
    def __init__(self, num_players):
        agents = AGENTS[:num_players]
        actions = [Action(f"w{i}{j}", And(Atom(f"w{i}"), Atom(f"w{j}"))) for i in agents for j in agents if i < j]
        equivs = {a: set((u.name, v.name) for u in actions for v in actions 
                            if (u.name[1] != a and u.name[2] != a and
                               v.name[1] != a and v.name[2] != a) or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)

class SeerActionModel(ActionModel):
    def __init__(self, num_players):
        agents = AGENTS[:num_players]
        actions = [Action(f"S{i}{r}{j}", And(Atom(f"s{i}"), Atom(f"{r}{j}"))) for i in agents for j in agents for r in ROLES
                                                                              if i != j]
        equivs = {a: set((u.name, v.name) for u in actions for v in actions
                            if (u.name[1] != a and v.name[1] != a) or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)


game_string = sys.argv[1]
num_players = len(game_string)
g = WerewolvesGame(game_string)
g.plot_knowledge()
if game_string.count('w') == 2:
    g.apply_action_model(WerewolfActionModel(3))
    g.plot_knowledge()
if game_string.count('s') == 1:
    g.apply_action_model(SeerActionModel(3))
    g.plot_knowledge()