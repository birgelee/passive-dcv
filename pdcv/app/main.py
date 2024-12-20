import asyncio
import shutil

from fastapi import FastAPI
import hashlib
from pathlib import Path
import asyncio
from asyncio.subprocess import PIPE  
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel



async def run_async(cmd):
    print ("[INFO] Starting script...")
    p = await asyncio.create_subprocess_shell(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    stdout, stderr = await p.communicate()
    print(stderr.decode("utf-8"))
    print("[INFO] Script is complete.")
    return stdout.decode("utf-8")


class CertRequest(BaseModel):
    domain: str
    csr: str
    secret: str


class CertResponse(BaseModel):
    domain: str
    full_chain: str
    chain: str
    cert: str



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
    auth_code = hashlib.sha256(request.secret.encode("utf-8")).hexdigest()
    web_dir = f"/tmp/web/{auth_code}/{request.domain}"
    cert_dir = f"/tmp/cert/{auth_code}/{request.domain}"
    config_dir = f"/tmp/config/{auth_code}"
    print(f"{config_dir}")
    Path(web_dir).mkdir(parents=True, exist_ok=True)
    Path(cert_dir).mkdir(parents=True, exist_ok=True)
    Path(config_dir).mkdir(parents=True, exist_ok=True)

    #p = Popen(['certbot', 'certonly', '--webroot', '-w', web_dir, '-d', request.domain, '--register-unsafely-without-email', "--csr", csr_path, '--agree-tos', '--test-cert', '--cert-path', f"{cert_dir}/cert.pem", '--fullchain-path', f"{cert_dir}/fullchain.pem", '--chain-path', f"{cert_dir}/chain.pem", '--config-dir', config_dir], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    certbot_cmd = f"certbot certonly --webroot -w {web_dir} -d {request.domain} --register-unsafely-without-email --csr {csr_path} --agree-tos --test-cert --cert-path {cert_dir}/cert.pem --fullchain-path {cert_dir}/fullchain.pem --chain-path {cert_dir}/chain.pem --config-dir {config_dir}"
    print(certbot_cmd)
    await run_async(certbot_cmd)

    full_chain = None
    #with open(f"/etc/letsencrypt/live/{request.domain}/fullchain.pem") as f:
    with open(f"{cert_dir}/fullchain.pem") as f:
        full_chain = f.read()

    chain = None
    with open(f"{cert_dir}/chain.pem") as f:
        chain = f.read()

    cert = None
    with open(f"{cert_dir}/cert.pem") as f:
        cert = f.read()


    shutil.rmtree(cert_dir)
    shutil.rmtree(web_dir)
    return CertResponse(domain = request.domain, full_chain = full_chain, chain = chain, cert = cert)




@app.get("/domain/{auth_code}/{domain_name}/{challenge_path:path}", response_class=PlainTextResponse)
async def domain_challenge(auth_code: str, domain_name: str, challenge_path: str):
    global domain_challenge_map
    print(f"domain challenge for {domain_name}", flush=True)
    print(f"pathpart: {challenge_path}", flush=True)
    web_dir = f"/tmp/web/{auth_code}/{domain_name}"
    file_path = web_dir + "/" + challenge_path
    file_contents = None
    with open(file_path) as f:
        file_contents = f.read()
    print(f"file contents: {file_contents}", flush=True)
    return file_contents
