import asyncio
import sys

from fastapi import FastAPI

import time

import yaml

import requests
import random
import os
import json


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
    await asyncio.sleep(5)


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
    print(p.stdout.readline().rstrip().decode("utf-8"))
    location_url = p.stdout.readline().rstrip().decode("utf-8")
    print(f"data: {data}, at location: {location_url}")
    domain_challenge_map[request.domain] = data
    p.stdin.write('\n'.encode("utf-8")).flush()
    await asyncio.sleep(10)
    return CertResponse(domain = request.domain)




@app.get("/domain/{domain_name}")
def domain_challenge(domain_name: str):
    print(f"domain challenge for {domain_name}")
