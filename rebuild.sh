#!/bin/bash
pip uninstall -y wfdcurses
rm dist/*
python3 -m build
pip install -e .
