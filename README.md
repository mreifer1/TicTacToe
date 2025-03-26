# Tic-Tac-Toe Multiplayer w/Sockets (Python)

## Authors
- Michael Reifer
- Ivan Goncharuk

## Overview

A classic Tic-Tac-Toe game in Python for two players on separate computers to play against each other over the local network using sockets. 

The GUI will be built with PySide6.

## HOW TO SET UP DEV ENVIRONMENT

create an environment called `venv` or whatever you want
```sh
python -m venv venv
```

execute the activation script. on unix devices it is inside `venv/bin/activate`

on unix:
```sh
source venv/bin/activate
```

on windows:
```sh
.\venv\Scripts\activate
```

install the pip requirements through the list on requirements.txt
the following command will install all packages in this file:
```sh
pip install -r requirements.txt
```


## Goals

- Implement a fully functional two-player Tic-Tac-Toe game.
- Develop a graphical user interface using a modern Python GUI library - ySide6).
- Enable real-time multiplayer functionality between two computers using - thon sockets.
- Ensure a clean and intuitive user experience.
- Structure the codebase in a modular and maintainable way for future expansion.

## Features

- Classic Tic-Tac-Toe Gameplay
- Two-Player Multiplayer
- Game state updates in real-time for both players.
- GUI Interface using PySide6
- Display in GUI for state changes etc etc
- Options for game reset etc etc

## Multiplayer Architecture (Sockets)

The game will utilize a client-server model for network communication