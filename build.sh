#!/bin/bash
# Устанавливаем Python 3.11
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
update-alternatives --set python3 /usr/bin/python3.11

# Устанавливаем pip для Python 3.11
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip

# Устанавливаем зависимости
python3 -m pip install -r requirements.txt
