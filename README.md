# reusable-variables

This repo contains common variables or variable patterns defined in ehrQL that may be used in multiple OpenSAFELY studies.

The repo is a very early attempt at collecting reusable variables, 

## Instructions for adding new variables

Please use the following pattern to add a new variable or set of variables:
1. Choose a meaningful identifying `{NAME}` for your variable or set of variables, and use this name consistently.
2. Create a new working branch from `main`.
3. Create a dataset definition `./analysis/{NAME}/dataset_definition.py` in the [`./analysis/`](./analysis/) directory. This dataset definition will contain the new variable(s). You may wish to add further scripts inside the  `./analysis/{NAME}/` directory which define additional functions or other code snippets, if this replicates how the variables should be specified in practice.
4. Any new codelists will need to be added directly to the [`./codelists/codelist.txt`](./codelists/codelist.txt) - specifying codelists in the variable-specific directories does not work neatly with the `opensafely codelists update` operation. Use a large separator, as below, to clearly distinguish groups of codelists belong to each variable(s).
     ````
     #######################################################
     # {NAME}
     #######################################################
     ````
5. Add a new action in the [`./project.yaml`](./project.yaml) file, titled `generate_dataset_{NAME}`, to run the dataset definition.
7. Check everything works as intended then submit a PR for review.

Where ever these variables are used in actual research repos, please link back to this repo.

# About the OpenSAFELY framework

The OpenSAFELY framework is a Trusted Research Environment (TRE) for electronic
health records research in the NHS, with a focus on public accountability and
research quality.

Read more at [OpenSAFELY.org](https://opensafely.org).

# Licences
As standard, research projects have a MIT license. 
