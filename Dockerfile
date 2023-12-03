FROM archlinux:latest
RUN pacman -Sy python python-pip git wget --noconfirm
RUN pip install -r requirements.txt
RUN python3 bot.py
