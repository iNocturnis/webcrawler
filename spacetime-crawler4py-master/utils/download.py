import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None):
    host, port = config.cache_server
    #gotta check header first to make sure we are not downloading anything above 1MB, because 2MB is the avg size of a webpage with all images and scripts,
    #roughly 1MB is the upper limit of just the html marking and stuff alone, that is essentially double the avg of a webpage without the other stuff
    #
    resp = requests.head(
        f"http://{host}:{port}/",
        params=[("q", f"{url}"), ("u", f"{config.user_agent}")])
    
    if resp.headers['content-length'] and resp.headers['content-length'].isdigit():
        if int(resp.headers['content-length']) > 1000000:
            print(int(resp.headers['content-length']))
            return Response({
                "error": f"FILE TOO LARGE !",
                "status": 606,
                "url" : url})

    resp = requests.get(
        f"http://{host}:{port}/",
        params=[("q", f"{url}"), ("u", f"{config.user_agent}")])
    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError) as e:
        pass
    logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": resp.status_code,
        "url": url})
