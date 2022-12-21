#!/bin/bash
pip uninstall wfdcurses
python -m build
pip install -e .

# python -m twine upload dist/*
