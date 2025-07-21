:: Create virtual environment and install mckit into it
:: virtaulenv .venv
:: poetry install -v
call .venv\Scripts\activate
start "VS" "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\IDE\devenv.exe"
