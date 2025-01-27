# Invenio NRP Command-line client

This is a command-line client for the NRP. It allows you to interact with NRP repositories based on Invenio RDM without using the web interface. This is useful for scripting and automation.

## Installation

```bash
pip install invenio-nrp-cli
```

## Adding a repository

Before interacting with a repository, you need to add it to the client's configuration. You can do this by running the following command:

```sh
nrp-cmd add repository https://zenodo.org
```