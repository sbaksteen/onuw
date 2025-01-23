from mlsolver.kripke import *
from mlsolver.formula import *
from more_itertools import distinct_permutations as dp
import networkx as nx
import matplotlib.pyplot as plt
from functools import reduce
import pygraphviz
import sys
import string
import math


AGENTS = string.ascii_lowercase
ROLES = ['t', 'w', 's', 'f', 'm']

class WerewolvesGame:
    def __init__(self, roles):
        self.num_players = len(roles)
        self.roles = roles
        # Worlds are given by distinct permutations of the multiset of roles.
        worlds = [World(''.join(x), {r + AGENTS[i]: True for (i, r) in enumerate(x)}) for x in dp(roles)]
        # Agents can't distinguish between worlds where they have the same role.
        relations = {AGENTS[i]: set((a.name, b.name) for a in worlds for b in worlds if a.name[i] == b.name[i]) for i in range(self.num_players)}
        self.kripke = KripkeStructure(worlds, relations)

    def plot_knowledge(self, layout="neato", pos=None):
        G = nx.DiGraph()
        nodes = self.kripke.worlds.keys()
        # Edges drawn are given by the union of all agents' relations, with the labels depending on which agents' relations
        # the edge comes from.
        edges     = [(w, v, {'label': ''.join([a for a in AGENTS[:self.num_players] if (w,v) in self.kripke.relations[a]])})
                     for (w, v) in reduce(lambda x, y : x.union(y), self.kripke.relations.values()) if w != v]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges) 
        if pos is None:
            pos = nx.nx_agraph.graphviz_layout(G, layout)
        else:
            # Reuse positions for the appropriate worlds if possible.
            pos = {a: pos[a1] for a in nodes for a1 in pos.keys() if a.startswith(a1)}
        # Use newlines instead of commas in node labels to avoid them being too long
        nodenames = {n: "\n".join(n.split(",")) for n in G.nodes}
        numlines = list(G.nodes.keys())[0].count(",")+1
        # Adjust font size based on how large the node label will be
        node_size = 1000*math.sqrt(numlines)
        font_size = round(node_size / 25 / max(numlines*2.1+.4,0))
        nx.draw(G, pos, with_labels=True, labels=nodenames, node_size=node_size, font_size=font_size, node_color="white", edgecolors="black")
        if (len(edges) < 200):
            # Draw edge labels if it's reasonable to do so
            nx.draw_networkx_edge_labels(G, pos, {(w,v):l for (w,v,l) in G.edges(data="label")})
        plt.show()
        return pos

    def apply_action_model(self, action_model):
        worlds = self.kripke.worlds.values()
        
        # New worlds: (w,a) for w |= pre(a)
        new_world_pairs = [(w, a) for w in worlds for a in action_model.actions if a.precon.semantic(self.kripke, w.name)]
        new_worlds = [World(f"{w.name},{a.name}", w.assignment) for (w,a) in new_world_pairs]

        # New relation (per agent) requires both the worlds and associated actions to be related under the old models
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

    def plot(self, layout="neato"):
        G = nx.DiGraph()
        nodes = [x.name for x in self.actions]
        # Edges drawn are given by the union of all agents' relations, with the labels depending on which agents' relations
        # the edge comes from.
        edges     = [(w, v, {'label': ''.join([a for a in AGENTS[:len(self.equivs.keys())] if (w,v) in self.equivs[a]])})
                     for (w, v) in reduce(lambda x, y : x.union(y), self.equivs.values()) if w != v]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges) 
        pos = nx.nx_agraph.graphviz_layout(G, layout)
        nx.draw(G, pos, with_labels=True, node_size=1200, font_size=24)
        if (len(edges) < 200):
            # Draw edge labels if it's reasonable to do so
            nx.draw_networkx_edge_labels(G, pos, {(w,v):l for (w,v,l) in G.edges(data="label")})
        plt.show()

class Action:
    def __init__(self, name, precon):
        self.name = name
        self.precon = precon

class WerewolfActionModel(ActionModel):
    def __init__(self, num_players):
        agents = AGENTS[:num_players]
        actions = [Action(f"w{i}{j}", And(Atom(f"w{i}"), Atom(f"w{j}"))) 
                    for i in agents for j in agents 
                    if i < j]
        equivs = {a: set((u.name, v.name) for u in actions for v in actions 
                        if (u.name[1] != a and u.name[2] != a and
                            v.name[1] != a and v.name[2] != a) 
                            or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)
        
class MasonActionModel(ActionModel):
    def __init__(self, num_players):
        agents = AGENTS[:num_players]
        actions = [Action(f"m{i}{j}", And(Atom(f"m{i}"), Atom(f"m{j}"))) for i in agents for j in agents if i < j]
        equivs = {a: set((u.name, v.name) for u in actions for v in actions 
                            if (u.name[1] != a and u.name[2] != a and
                               v.name[1] != a and v.name[2] != a) or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)

class FamiliarActionModel(ActionModel):
    def __init__(self, num_players, num_werewolves):
        agents = AGENTS[:num_players]
        actions = []
        if num_werewolves == 2:
            actions = [Action(f"F{i}W{j}{k}", And(Atom(f"f{i}"), And(Atom(f"w{j}"), Atom(f"w{k}")))) 
                        for i in agents for j in agents for k in agents
                        if i != j and i != k and j < k]
        if num_werewolves == 1:
            actions = [Action(f"F{i}W{j}", And(Atom(f"f{i}"), Atom(f"w{j}"))) 
                        for i in agents for j in agents
                        if i != j]
        equivs = {a: set((u.name, v.name) 
                        for u in actions for v in actions
                        if (u.name[1] != a and v.name[1] != a) or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)

class SeerActionModel(ActionModel):
    def __init__(self, num_players):
        agents = AGENTS[:num_players]
        actions = [Action(f"S{i}{r}{j}", And(Atom(f"s{i}"), Atom(f"{r}{j}"))) 
                    for i in agents for j in agents for r in ROLES
                    if i != j]
        equivs = {a: set((u.name, v.name) 
                        for u in actions for v in actions
                        if (u.name[1] != a and v.name[1] != a) or u == v)
                    for a in agents}
        ActionModel.__init__(self, actions, equivs)


game_string = sys.argv[1]
layout = "neato"
if len(sys.argv) > 2:
    layout = sys.argv[2]
num_players = len(game_string)
g = WerewolvesGame(game_string)
pos = g.plot_knowledge(layout)
if game_string.count('w') == 2:
    # If there are exactly two werewolves, apply the werewolf action model
    action = WerewolfActionModel(num_players)
    g.apply_action_model(action)
    g.plot_knowledge(layout, pos)
if game_string.count('f') == 1 and game_string.count('w') in [1, 2]:
    # If there is a familiar and one or two werewolves, apply a familiar action model
    g.apply_action_model(FamiliarActionModel(num_players, game_string.count('w')))
    g.plot_knowledge(layout, pos)
if game_string.count('m') == 2:
    # If there are exactly two masons, apply the mason action model
    g.apply_action_model(MasonActionModel(num_players))
    g.plot_knowledge(layout, pos)
if game_string.count('s') == 1:
    # If there is a seer, apply the seer action model
    g.apply_action_model(SeerActionModel(num_players))
    g.plot_knowledge(layout)