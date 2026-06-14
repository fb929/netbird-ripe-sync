#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from os.path import expanduser
import sys
import yaml


# load config {{
scriptName = os.path.basename(sys.argv[0]).split('.')[0]
homeDir = expanduser("~")
defaultConfigFiles = [
    homeDir + '/.' + scriptName + '.yaml',
    './.config.yaml',
]
for configFile in defaultConfigFiles:
    if os.path.isfile(configFile):
        try:
            with open(configFile, 'r') as ymlfile:
                try:
                    cfg = yaml.load(ymlfile,Loader=yaml.Loader)
                except Exception as e:
                    logging.warning("main: skipping load load config file: '%s', error '%s'", configFile, e)
                    continue
        except:
            continue
# }}


# create session
session = requests.Session()
session.headers.update({
    "Authorization": f"Token {cfg['netbird']['token']}",
    "Content-Type": "application/json",
})


# get exists routes
routes = session.get(f"{cfg['netbird']['api_url']}/routes").json()
existing = {
    route["network"]: route
    for route in routes
}
# debug
#print(f"existing routes: {existing}")


# update routes
for asn in cfg['asns']:
    r = requests.get(
        "https://stat.ripe.net/data/announced-prefixes/data.json",
        params={"resource": asn}
    )

    for p in r.json()["data"]["prefixes"]:
        prefix = p["prefix"]
        if prefix not in existing:
            route = existing.get(prefix)
            if route:
                print( f"Deleting existing route {prefix} ({route['id']})")
                response = session.delete(f"{cfg['netbird']['api_url']}/routes/{route['id']}")
                response.raise_for_status()

            print(f"creating route for: {prefix}")
            response = session.post(
                f"{cfg['netbird']['api_url']}/routes",
                json={
                    "network": prefix,
                    "peer": cfg['netbird']['peer_id'],
                    "network_id": prefix.replace("/", "-"),
                    "enabled": True,
                    "metric": cfg['route']['metric'],
                    "groups": cfg['route']['groups'],
                    "description": f"Managed by RIPE sync: route to {prefix} for asn {asn}",
                    "masquerade": cfg['route']['masquerade'],
                },
            )
            response.raise_for_status()
            print(response.text,response.status_code)
