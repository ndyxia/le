pacman -Sy python python-pip git wget --noconfirm
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python3 bot.py
deactivate
