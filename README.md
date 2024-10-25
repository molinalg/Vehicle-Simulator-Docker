# Vehicle Simulator Docker

## Description
Developed in 2024, "Vehicle Simulator Docker" is a university project made during the fourth course of Computer Engineering at UC3M in collaboration with @EnriqueMorenoG88.

It was made for the subject "Foundations of Internet of Things" and corresponds to one of the practices of this course. The main goal of the project is to learn how to use **Dockers**, the protocol **Mosquitto (MQTT)**, **Databases (MariaDB)** in Python and **Microservices**.

**NOTE:** Part of the code and the comments are in spanish.

The base of this project is [this other one](https://github.com/molinalg/Vehicle-Simulator-For-Raspberry-Pi).

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Problem Proposed](#problem-proposed)
- [License](#license)
- [Contact](#contact)

## Installation
To execute this code, first execute this command to install the neccesary libraries:
```sh
pip install paho-mqtt requests mysql-connector-python Flask Flask-CORS
```
You will also need to generate an API Key in Google Cloud for the service of Google Maps. **Then it is necessary to write it in line 23 of the file "VehicleDigitalTwin.py"**.

## Usage
To run the code, you will need to use **2 different terminals** in different Google Cloud Linux Instances. In the first one, the files in the directory "IOTCloudServices" will be run using docker compose while in the second one, docker compose will be used again to run the files in "VirtualVehicles". More than one vehicle can be executed at the same time.

## Problem Proposed
This program **simulates a vehicle within Docker containers**. It leverages the **Google Maps API** to generate detailed steps for traveling from one location to another. The vehicle simulation follows specific rules as it progresses through each step. During the journey, the vehicle continuously sends **telemetry data** to a **message router** responsible for recording and tracking this information in a database. The telemetry service operates as a **Flask microservice**, and all data exchange uses the **Mosquitto MQTT protocol**.

## License
This project is licensed under the **MIT License**. This means you are free to use, modify, and distribute the software, but you must include the original license and copyright notice in any copies or substantial portions of the software.

## Contact
If necessary, contact the owner of this repository.
