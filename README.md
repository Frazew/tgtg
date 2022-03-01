[![Publish multi-arch Docker images](https://github.com/Der-Henning/tgtg/actions/workflows/docker-multi-arch.yml/badge.svg?branch=main)](https://github.com/Der-Henning/tgtg/actions/workflows/docker-multi-arch.yml)
[![Tests](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml)
[![CodeQL](https://github.com/Der-Henning/tgtg/actions/workflows/codeql-analysis.yml/badge.svg?branch=main)](https://github.com/Der-Henning/tgtg/actions/workflows/codeql-analysis.yml)
[![GitHub release](https://img.shields.io/github/release/Der-Henning/tgtg?include_prereleases=&sort=semver&color=blue)](https://github.com/Der-Henning/tgtg/releases/)

# TGTG Scanner

TGTG Scanner observes your favorite TGTG Magic Bags for new available items and notifies you via mail, IFTTT, Telegram, pushSafer or any other WebHook. Notifications will be send when the available amount of Magic Bags rises from zero to something.

Additionally the currently available amounts can be provided via a http server.

Running in a docker container the scanner can be seemlessly integrated with openhab, prometheus and other automation, notification and visualization services.

This software is provided as is without warranty of any kind. If you have problems, find bugs or have suggestions for improvement feel free to create an issue or contribute to the project. Before creating an issue please refere to the [FAQ](https://github.com/Der-Henning/tgtg/wiki/FAQ).

## Disclaimer

Too Good To Go explicitly forbids the use of their plattform the way this tool does. In their Terms and Conditions it says: "The Consumer must not misuse the Platform (including hacking or 'scraping')."

If you use this tool you do it at your own risk. TGTG may stop you from doing so by (temporarily) blocking your access and may even delete your account.

## Installation

You can install this tool on any computer. For 24/7 notifications I recommended to install the tool on a NAS like Synology or a Raspberry Pi. You can also use a virtual cloud server. Starting at 1,00 €/Month at Strato.de or try AWS free tier.

If you have any problems or questions feel free to create an issue.

You have the following four options to install the scanner, ascending in complexity:

### 1. Use prebuild Release

This is the simplest but least flexible solution suitable for most operating systems.

1. Download latest [Releases](https://github.com/Der-Henning/tgtg/releases) for your OS
2. Unzip the archiv
3. Edit ```config.ini``` as described in the file
4. Run scanner

You can run the scanner manually if you need it, add it to your system startup or create a service.

### 2. Run with Docker

My prefered method for servers using the pre build multi-arch linux images available on [Docker Hub](https://hub.docker.com/r/derhenning/tgtg).

1. Install Docker and docker-compose
2. Copy and edit ```docker-compose.yml``` as described in the file
3. Run ```docker-compose up -d```

The container creates a volume mounting ```\tokens``` where the app saves the TGTG credentials after login. These credentials will be reused on every start of the container to avoid the mail login process. To login with a different account you have to delete the created volume.

### 3. Install with pip

1. Install python >= 3.9 and pip
2. Install scanner ```pip install tgtg-scanner```
3. Create ```config.ini``` as described in the file ```config.template.ini```
4. Run ```python -m tgtg_scanner```

### 4. Run from source

Method for developers.

1. Install python >= 3.9 and pip
2. Clone repository ```git clone https://github.com/Der-Henning/tgtg.git```
3. ```cd tgtg```
4. Run ```pip install -r requirements.txt```
5. Create ```src/config.ini``` as described in the file ```config.template.ini```
6. Run ```python src/scanner.py```

### TGTG Login

When the scanner is started it will first try to login to your TGTG account. Similar to loging in to the TGTG app, you have to click on the link send to you by mail. This won't work on your mobile phone if you have installed the TGTG app, so you have to check your mailbox on PC.

After a successfull login the scanner will send a test notification on all configured notifiers. If you don't reveive any notifications, please check your configuration.

### Metrics

Enabling the metrics option will expose a http server on the specified port supplying the currently available items. You can scrape the data with prometheus to create and visualize historic data or use it with your home automation.

Scrape config:

````xml
  - job_name: 'TGTG'
    scrape_interval: 1m
    scheme: http
    metrics_path: /
    static_configs:
    - targets:
      - 'localhost:8000'
````

## Developing

For developement I recommend using docker. The Makefile depends on docker and docker-compose.

Create ```.env``` based on ```sample.env``` for configuration.

Developing with VSCode you can open the project in the configured developement container.

### Makefile commands

```make image``` builds docker image with tag ```tgtg-scanner:latest```

```make install``` installs dependencies

```make start``` short for ```python src/scanner.py```

```make bash``` starts dev python docker image with installed dependencies and mounted project in bash

```make executable``` creates bundled executable in ```/dist```

```make test``` runs unittests

```make clean``` cleans up docker compose

```make package``` builds pip package

### Helper functions

```helper.py``` contains some usefull functions. Running ```python -m tgtg_scanner --help``` displays the available commands.

````
usage: tgtg_scanner [-h] [-v | -f | -c | -a ITEM_ID | -d ITEM_ID] [-s]

        Runs TGTG Scanner. Use optional arguments for helper functions.
        
optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -f, --favorites       returns all your favorites and exit
  -c, --credentials     returns tgtg credentials and exit
  -a ITEM_ID, --add ITEM_ID
                        add ITEM_ID to favorites and exit
  -d ITEM_ID, --delete ITEM_ID
                        delete [all | ITEM_ID] from favorites and exit
  -s, --short           only display item_ids
````

### Creating new notifiers

Feel free to create and contribute new notifiers for other services and endpoints. You can use an existing notifier as template.

Notifiers must extend the ```Notifier``` class and implement the ```_send(self, item: Item)``` function.

Configuration checks should be placed in the ```_init(self)``` function, which is called on startup and only when the notifier is enabled.

See ```tgtg_scanner\models\notifier.py``` for further documentation.

---
If you want to support me, feel free to buy me a coffee.

<a href="https://www.buymeacoffee.com/henning" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="200"></a>
