import asyncio
import sys

from fastapi import FastAPI

import time

import yaml

import requests
import random
import os
import json

from pathlib import Path


import threading
from fastapi.responses import PlainTextResponse


from subprocess import Popen, PIPE, STDOUT


from abc import ABC
from pydantic import BaseModel # type: ignore


class CertRequest(BaseModel):
    domain: str
    csr: str


class CertResponse(BaseModel):
    domain: str
    full_chain: str



app = FastAPI()

domain_challenge_map = {}


@app.post("/cert")
async def perform_cert_request(request: CertRequest):
    global domain_challenge_map
    csr_path = f"/tmp/{request.domain}.csr"
    with open(csr_path, 'w') as f:
        f.write(request.csr)
    # make the dir
    print("running subproc v2", flush= True)
    print(f"for csr: {request.csr} at path {csr_path}", flush= True)
    
    web_dir = f"/tmp/{request.domain}"
    Path(web_dir).mkdir(parents=True, exist_ok=True)

    p = Popen(['certbot', 'certonly', '--webroot', '-w', web_dir, '-d', request.domain, '--register-unsafely-without-email', "--csr", csr_path, '--agree-tos', '--test-cert'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    
    await asyncio.sleep(20)
    print(p.communicate())
    
    #


    ##full_output = ""
    #line = p.stdout.readline().rstrip().decode("utf-8")
    ##print(line, flush=True)
    #
    #data = ""
    #while True:
    #    if line.startswith("And make it available"):
    #        break
    #    if line.startswith("Create a file containing"):
    #        p.stdout.readline().rstrip().decode("utf-8")
    #        data = p.stdout.readline().rstrip().decode("utf-8")
    #    #print(line, flush=True)
    #    line = p.stdout.readline().rstrip().decode("utf-8")
    #print(p.stdout.readline().rstrip().decode("utf-8"), flush=True)
    #location_url = p.stdout.readline().rstrip().decode("utf-8")
    #print(f"data: {data}, at location: {location_url}", flush=True)
    #domain_challenge_map[request.domain] = data
    #p.stdin.write('\n'.encode("utf-8"))
    #p.stdin.flush()
    #print("entering async wait", flush=True)
    #await asyncio.sleep(20)
    #print("emding asunc wait", flush=True)
    #t = threading.Thread(name='non-daemon', target=p.communicate)
    #print(p.communicate(), flush=True)

    full_chain = None
    with open(f"/etc/letsencrypt/live/{request.domain}/fullchain.pem") as f:
        full_chain = f.read()

    return CertResponse(domain = request.domain, full_chain = full_chain)




@app.get("/domain/{domain_name}/{challenge_path:path}", response_class=PlainTextResponse)
async def domain_challenge(domain_name: str, challenge_path: str):
    global domain_challenge_map
    print(f"domain challenge for {domain_name}", flush=True)
    print(f"pathpart: {challenge_path}", flush=True)
    web_dir = f"/tmp/{domain_name}"
    file_path = web_dir + challenge_path
    file_contents = None
    with open(file_path) as f:
        file_contents = f.read()
    print(f"file contents: {file_contents}", flush=True)
    return file_contents
