@echo Setting up environment~
%1 -m venv .env
.env\Scripts\activate.bat
pip install -r requirements.txt
