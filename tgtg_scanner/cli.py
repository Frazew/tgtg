"""Command Line Interface for the TGTG Scanner
"""
import sys
from os import path, getcwd
import logging
import argparse
import json
from typing import NoReturn
import requests
from packaging import version
from .scanner import Scanner
from .helper import Helper
from .models import ConfigurationError, TgtgAPIError

VERSION_URL = 'https://api.github.com/repos/Der-Henning/tgtg/releases/latest'
VERSION = "1.9.0"


def welcome_message():
    """Prints a formatted welcome message
    """
    # pylint: disable=W1401
    print("  ____  ___  ____  ___    ____   ___   __   __ _  __ _  ____  ____  ")
    print(" (_  _)/ __)(_  _)/ __)  / ___) / __) / _\ (  ( \(  ( \(  __)(  _ \ ")
    print("   )( ( (_ \  )( ( (_ \  \___ \( (__ /    \/    //    / ) _)  )   / ")
    print("  (__) \___/ (__) \___/  (____/ \___)\_/\_/\_)__)\_)__)(____)(__\_) ")
    print("")
    print("Version", VERSION)
    print("©2021, Henning Merklinger")
    print("For documentation and support please visit https://github.com/Der-Henning/tgtg")
    print("")
    # pylint: enable=W1401


def check_version():
    """Returns information for new version if available

    Returns:
        dict | None: contains version and url
    """
    res = requests.get(VERSION_URL)
    res.raise_for_status()
    last_release = res.json()
    if version.parse(VERSION) < version.parse(last_release['tag_name']):
        return {'version': version.parse(last_release['tag_name']), 'url': last_release['html_url']}
    return None


def print_new_verion():
    """Checks if a new release is available in github.com.
    """
    try:
        vers = check_version()
        if vers:
            print("New Version %s available!", vers['version'])
            print("Please visit %s", vers['url'])
            print("")
    except Exception as err:
        print("Version check Error! - %s", err)


def start_scanner() -> NoReturn:
    """Starts the scanner as command line tool
    """
    prog_folder = path.dirname(sys.executable) if getattr(
        sys, '_MEIPASS', False) else getcwd()
    config_file = path.join(prog_folder, 'config.ini')
    log_file = path.join(prog_folder, 'scanner.log')
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode="w"),
            logging.StreamHandler()
        ])
    log = logging.getLogger('tgtg')
    log.setLevel(logging.INFO)
    welcome_message()
    print_new_verion()
    try:
        scanner = Scanner(config_file) if path.isfile(
            config_file) else Scanner()
        scanner.run()
    except ConfigurationError as err:
        log.error("Configuration Error - %s", err)
        sys.exit(1)
    except TgtgAPIError as err:
        log.error("TGTG API Error: %s", err)
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Shutting down scanner ...")
        sys.exit(0)
    except SystemExit:
        sys.exit(1)
    except:
        log.error("Unexpected Error! - %s", sys.exc_info())
        sys.exit(1)


def start() -> NoReturn:
    """Provides a command line interface with options for helper functions
    """
    parser = argparse.ArgumentParser(
        description='''
        Runs TGTG Scanner. Use optional arguments for helper functions.

        For documentation and support please visit https://github.com/Der-Henning/tgtg
        ©2021, Henning Merklinger
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        '-v', '--version', action='version', version=f"Version: {VERSION}")
    arg_group.add_argument('-f', '--favorites', action='store_true',
                           help='returns all your favorites and exit')
    arg_group.add_argument('-c', '--credentials', action='store_true',
                           help='returns tgtg credentials and exit')
    arg_group.add_argument('-a', '--add', metavar="ITEM_ID",
                           help='add ITEM_ID to favorites and exit')
    arg_group.add_argument('-d', '--delete', metavar="ITEM_ID",
                           help='delete [all | ITEM_ID] from favorites and exit')
    parser.add_argument('-s', '--short', action='store_true',
                        help='only display item_ids')
    args = parser.parse_args()

    config_file = path.join(getcwd(), 'config.ini')
    if args.favorites:
        helper = Helper(config_file, notifiers=False) if path.isfile(
            config_file) else Helper()
        if args.short:
            print(json.dumps([{"display_name": f["display_name"], "item_id": f["item"]["item_id"]}
                  for f in helper.favorites], sort_keys=True, indent=4, ensure_ascii=False))
        else:
            print(json.dumps(helper.favorites, sort_keys=True, indent=4))
    elif args.credentials:
        helper = Helper(config_file, notifiers=False) if path.isfile(
            config_file) else Helper()
        print(json.dumps(helper.credentials, sort_keys=True, indent=4))
    elif args.add:
        helper = Helper(config_file, notifiers=False) if path.isfile(
            config_file) else Helper()
        helper.set_favorite(args.add)
    elif args.delete:
        helper = Helper(config_file, notifiers=False) if path.isfile(
            config_file) else Helper()
        if args.delete == "all":
            if input("Delete all your favorites? [y/n]") == "y":
                helper.remove_all_favorites()
        else:
            if input(f"Delete {args.delete} form your favorites? [y/n]") == "y":
                helper.unset_favorite(args.delete)
    else:
        start_scanner()
