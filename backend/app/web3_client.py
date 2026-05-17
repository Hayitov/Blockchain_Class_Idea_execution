from functools import lru_cache

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from app.settings import settings


@lru_cache(maxsize=1)
def get_web3() -> Web3:
    # Sepolia uses PoA-style extraData (>32 bytes); without this middleware
    # block decoding raises "extraData longer than 32 bytes".
    w3 = Web3(Web3.HTTPProvider(settings.sepolia_rpc_url, request_kwargs={"timeout": 15}))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3
