@echo off
::
:: Jupyter kernel setup
::
::
:: dvp, Apr 2022
::

set package=%1

if "%package%"=="" (
    set package=mckit
)

echo Creating jupyter kernel for conda environment %package%

:: Fix pywin32 version for tornado
:: tornado (in jupyter) doesn't work with newer version of pywin, check this on jupyter dependencies updates
:: TODO dvp: check on dependencies updates
:: The following sets version 228 on python39 (after pip or poetry it was 300)
:: call conda install pywin32 -y
call conda install jupyterlab -y

:: Create jupyter kernel pointing to the conda environment
call python -m ipykernel install --user --name %package%
if errorlevel 1 (
    echo ERROR: something wrong with installing Jupyter kernel for %package% environment
    set errorlevel=1
) else (
    echo To use %package% environment in jupyter
    echo   - Run 'jupyter lab'
    echo   - Open or create notebook
    echo   - Select kernel %package%
    echo   - check if import %package% in the notebook works
    echo.
    echo To remove a kernel use jupyter comands:
    echo   jupyter kernelspec list
    echo   jupyter kernelspec remove <kernels...>
)
