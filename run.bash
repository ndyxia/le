pacman -Sy python python-venv python-pip git wget --noconfirm
python3 -m venv .env
cd .env
source bin/activate
pip install -r requirements.txt
python3 bot.py
deactivate
