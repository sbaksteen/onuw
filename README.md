# One-Night Ultimate Werewolf Epistemic Action Model

The runnable script `werewolves.py` is found in the `src` folder.

Running werewolves.py requires the following:
- networkx
- matplotlib
- pygraphviz
- installing the version of mlsolver included in this repository (so not the original) using `python setup.py install` inside the `mlsolver` folder.
  - Changes were made to mlsolver to make it faster. Most notably, we now use a dictionary to store worlds instead of a list, preventing excessive iteration. (It still passes all unit tests)

Usage: `python werewolves.py roles [layout]`: will plot Kripke models for a ONUW game with the given roles, both the initial model and one after each applicable action model is applied. For example, `wts` would run with one werewolf, one townsperson, and one seer, while `mmwwtf` (not recommended) would run with two masons, two werewolves, a townsperson, and a familiar. The optional layout parameter gives the type of layout to use for plotting graphs. These are pygraphviz layout engines, as described at https://graphviz.org/docs/layouts/. The default layout engine is `neato`. 

Most of the code in `mlsolver` is taken from https://github.com/erohkohl/mlsolver. Modifications in `mlsolver/mlsolver/formula.py` and `mlsolver/mlsolver/kripke.py` are marked per function with a comment saying "MODIFIED". A single unit test was also modified, namely `mlsolver/test/test_or.py`, which originally used two worlds of the same name, which is not possible anymore in our version. Everything else is taken verbatim from erohkol/mlsolver.