python "%~dp0get-pip.py"
pip install -r "%~dp0requirements.txt"
python "%~dp0src\eut_main.py"
pause

