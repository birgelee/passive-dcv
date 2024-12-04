import asyncio
import sys

from fastapi import FastAPI

import time

import yaml

import requests
import random
import os
import json

import threading
from fastapi.responses import PlainTextResponse


from subprocess import Popen, PIPE, STDOUT


from abc import ABC
from pydantic import BaseModel # type: ignore


class CertRequest(BaseModel):
    domain: str


class CertResponse(BaseModel):
    domain: str



app = FastAPI()

domain_challenge_map = {}


@app.post("/cert")
async def perform_cert_request(request: CertRequest):
    global domain_challenge_map
    p = Popen(['certbot', 'certonly', '--manual', '--register-unsafely-without-email', '--agree-tos', '-d', request.domain], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    print("running subproc v2")
    sys.stdout.flush()
    #await asyncio.sleep(5)


    #full_output = ""
    line = p.stdout.readline().rstrip().decode("utf-8")

    
    data = ""
    while True:
        if line.startswith("And make it available"):
            break
        if line.startswith("Create a file containing"):
            next_line_is_data = True
            p.stdout.readline().rstrip().decode("utf-8")
            data = p.stdout.readline().rstrip().decode("utf-8")
        #print(line)
        line = p.stdout.readline().rstrip().decode("utf-8")
    print(p.stdout.readline().rstrip().decode("utf-8"), flush=True)
    location_url = p.stdout.readline().rstrip().decode("utf-8")
    print(f"data: {data}, at location: {location_url}", flush=True)
    domain_challenge_map[request.domain] = data
    p.stdin.write('\n'.encode("utf-8"))
    p.stdin.flush()
    print("entering async wait", flush=True)
    await asyncio.sleep(20)
    print("emding asunc wait")
    #t = threading.Thread(name='non-daemon', target=p.communicate)
    print(p.communicate())

    return CertResponse(domain = request.domain)




@app.get("/domain/{domain_name}", response_class=PlainTextResponse)
async def domain_challenge(domain_name: str):
    global domain_challenge_map
    print(f"domain challenge for {domain_name}")
    return domain_challenge_map[domain_name]
