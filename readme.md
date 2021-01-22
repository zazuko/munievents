# Munievents

Munievents is a tool visualizing events in swiss municipalities. Swiss communes are very dynamic, and adjust to the popluation needs. They change their names, adjust the territory, merge with other communes or split into multiple new communes. Munievents visualizes all such events. The data covers all swiss communes and associated events since 1960.

This is what you can expect from munievents app:
![sample event](example.png?raw=true)

## Installation

To setup munievents app locally:

* ```python3 -m venv venv``` create virtual environment
* ```source venv/bin/activate``` to activate venv on Linux or  ```venv\Scripts\activate.bat``` to activate venv on Windows
* ```pip install -e .``` installs medico project in an editable mode
* ```munievents``` starts local munievents webserver: http://127.0.0.1:8050/