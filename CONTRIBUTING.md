# Contributing Guidelines

Fork the repo and submit a PR with your changes. 

*(No specific format is required for PRs at this point...as long as its reasonable/understandble and focuses on the core development areas needed (discussed below) it will be considered.)*

TODO: include how to run a new experiment (run_widget, run_api, etc), add a new character sheet, etc.

## Contributing to Character Sheets Database

## Contributing to Core Simulation Engine Codebase (including AI, models, graphs, prompts, etc.)

## Directory Structure

TODO - add dir structure when codebase is more stable
```sh
# START: EXPLAINER FILES/FOLDERS
├── CONTRIBUTING.md # 🎯 you are here
├── README.md # entry point for the repo
├── LICENSE.md # available to use by anyone for anything
├── docs # docs for the codebase (TODO: currently just scaffolded)
├── images # for images in README or other top-level .md files
# END: EXPLAINER FILES/FOLDERS
```

## Contributing Instructions

### 1) Fork the repo
[Here are some instructions](https://docs.github.com/en/get-started/quickstart/fork-a-repo) on how to do that if you are unfamiliar

### 2) Start docker daemon
Dev container is configured to run docker so it will throw an error if you try to launch the dev container before starting the docker daemon. To launch either run docker gui or run ```docker info``` in terminal

### 3) Launch dev container
From VS-code make sure you have the [DevContainers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension intalled then launch the dev container like this or by clicking the green button in the bottom left of the VS-code window
![launch dev container](images/launch_dev_container.png)

At this point all dev dependencies have been installed and you can start running code, tests, making changes, etc.

### 4) Contribute
Probably wise to start by running unit tests to wrap your head around how things work and are called and unitized. But do whatever suits your fancy.

For example, now your terminal in VS-code will be running in the dev container so you can make sure poetry successfully installed all deps by running ```poetry show``` in the terminal

```sh
# NOTE: you prob need to run poetry install so that dcs_simulation_engine is aviable in ipython and in tests scripts 
poetry install
```

![terminal in dev container](images/terminal_in_container.png)

OR you can launch ipython by running ```ipython``` in the terminal

![ipython usage](images/ipython_usage.png)

OR you can run unit tests like this

Note: if dev.Dockerfile include --no-root you may need to install local package "poetry install" to make dcs_simulation_engine avaiable in tests

#### Run Tests

```sh
# runs all unit tests
poetry run pytest tests/unit_tests

# runs a specific unit test for a module/file
poetry run pytest tests/test_utils

# runs a specific unit test within a module/file
poetry run pytest tests/test_utils::test_specific_thing
```

![pytest usage](images/pytest_usage.png)
or all tests
![pytest all unit tests](images/unit_tests.png)

OR you can run any of the scripts by typing copi (tab completion to get the copilot-bla scripts)

![scripts](images/copilot_scripts.png)

Running the `run_cli` script looks like this 
![run_cli](images/run_cli.png)

and outputs TODO

#### Run API

```sh
uvicorn dcs_simulation_engine.api.main:app --reload
```

### 5) Submit PR
Once you are done making changes and want to submit a PR you can do so by clicking the "create pull request" button in the github UI


# Troublshooting and Additional Gotchas you may run into

- If you are contributing to .ipynb notebooks you need to run `nbstripout --install` so that no nb output is committed

⸻

Thank you for contributing!