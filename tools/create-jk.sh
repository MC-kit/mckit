#!/bin/bash
#
# Jupyter kernel setup
#
#
# dvp, Apr 2022
#

mckit=${1:-mckit}

echo "Creating jupyter kernel for python environment $mckit"
python -m pip install jupyterlab
python -m ipykernel install --user --name "$mckit"
if [[ $? ]]; then
    echo "To use $mckit environment in jupyter:"
    echo "  - Run 'jupyter lab'"
    echo "  - Open or create notebook"
    echo "  - Select kernel $mckit"
    echo "  - check if 'import mckit' in the notebook works"
    echo
    echo "To remove a kernel use jupyter commands:"
    echo "  jupyter kernelspec list"
    echo "  jupyter kernelspec remove <kernels...>"
fi
