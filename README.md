# passive-dcv
A system to complete domain control validation via one-time static configuration instead of an online challenge protocol. Any (athorized) client can get a new cert whether or not it has access to the operating domain infrastructure.

The entire system is stateless and can be thought of as a service that, with a single HTTP POST call, any HTTP(S) client can obtain a certificate (presuming it send the proper secret token and a domain is configured correctly).

The clients that obtain certs merely perform a single web request, they are not full ACME clients. After initial static domain configuration, just send an HTTP post with a CSR and proper secret value and get back a signed cert.


# Useage

The project can be used in either a 3rd-party or self-hosted environment. This documentation uses the hosted endpiont https://pdcv.henrybirgelee.com but the project can be run with docker compose and then self hosted at any endpoint. The endpoint must be publically accessable and we recommend the endpoint run HTTPS to ensure secrete values are not leaked (e.g., the hosted version has the docker compose up script running behind an nginx reverse proxy that manages HTTPS).

## 1. Create a secret
A secret is the way only your clients are authenticated and allowed to get certs for your domain. A client without your secret can't get a cert for your domain from the service and any client with your secret can get a domain. Secrets can be changed if compromised (via changing the magic redirect configured next), but keep in mind there are no accounts. Your secret is your way of authenticating with the service. The secret system makes the service stateless and requre no registration.

A secret is essentially the preimage of a SHA256 hash which is your public key. Essentially SHA256(sevret) = public.

A secret can be any string. We recommend having significant entropy particularly since is potentially targetable with offline attacks. Thus, a possible way of generating it is:

```
python -c "import string
import secrets
alphabet = string.ascii_letters + string.digits
print(''.join([secrets.choice(alphabet) for i in range(40)]), end='')" > my_secret.key
```

The public is just the SHA256 hex digest of the secret. You can get this with:

```
sha256sum my_secret.key | awk '{ print $1 }' > public.key
```

(presuming my_secret.key is where you saved your secret)

## 2. Create a magic redirect

The step that actually authorizes the service to get certs for your domain is the magic redirect. Note that this redirect is a one-liner you can put into a config file. Once you are up and running, you never need to touch it and the clients getting certs don't need access to your domain.

The redirect line in nginx should go in the appropriate server block and read:

```
rewrite ^/.well-known/ https://pdcv.henrybirgelee.com/domain/<YOUR_PUBLIC_HERE>/$host$request_uri;
```

Reload your nginx server to ensure it takes effect. Use the hex digest public you produced above (e.g., public.key) in the redirect statement.

## 3. Generate a CSR

The service DOES NOT store or even handle your private keys. It works entierly on CSRs so that the key stays safely on your server. To make a CSR you can use the open-ssl command:

```
openssl req -newkey rsa:4096 -keyout private.key -out req.csr -nodes -subj "/emailAddress=./CN=<YOUR_DOMAIN_HERE>/O=./OU=./C=US/ST=./L=."
```

YOUR_DOMAIN_HERE is the domain you installed the redirect on and are requesting a cert for.

## 4. Get certs

The nice thing is that steps 1-3 only need to be done once (you may want to redo step 3 if you plan on changing private keys on renewal, this is optional). At this point, store the CSR and a client from ANYWHERE IN THE WORLD without operational access to your domain can get or renew a cert presuming it has contorl of the secret. There are large advantages to this given that the clients that get certs don't need to have highly-sensitive DNS credentials or some fort of advanced integration or with the webserver to complete challenges (and respective webserver credentials). You don't even need to actually install an ACME client. They only need a single secret value that authorizes them to get certs. Its also nice in the case of multiple content replicas, distributed systems, and load balancing where many certs need to be managed and deployed but there is no gaurantee the CAs challenge will nessesarily talk your your content replica. Here, no coordination is needed between the replicas, they can all get certs.

To get a cert, just send a post request with the following schema:

POST "https://pdcv.henrybirgelee.com/cert"

HEADERS (-H): "Content-Type: application/json"

BODY:
```
{
    "domain": "YOUR_DOMAIN_HERE",
    "csr": "THE_CSR_FILE_ENCODED_AS_A_JSON_STRING",
    "secret": "YOUR_SECRET"
}
```

For a python oneliner (presuming your secret is my_secret.key, and your CSR is req.csr)

```
python -c "import requests
from pathlib import Path
secret = Path('my_secret.key').read_text()
csr = Path('req.csr').read_text()
print(requests.post('https://pdcv.henrybirgelee.com/cert', json={'domain': 'YOUR_DOMAIN_HERE', 'csr': csr, 'secret': secret}).text)"
```

The resulting JSON will have your cert, chain, and fullchain in json string form which can be installed along with your private key from openssl to run an HTTPS site.


Another variant with writing to output files for later use by a webserver:
```
python -c "import requests
import json
from pathlib import Path
secret = Path('my_secret.key').read_text()
csr = Path('req.csr').read_text()
response = json.loads(requests.post('https://pdcv.henrybirgelee.com/cert', json={'domain': 'YOUR_DOMAIN_HERE', 'csr': csr, 'secret': secret}).text)
Path('fullchain.pem').write_text(response['full_chain'])
Path('chain.pem').write_text(response['chain'])
Path('cert.pem').write_text(response['cert'])"
```