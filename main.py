from web3 import Web3
from web3.eth import AsyncEth
import json
import random
from web3.middleware import ExtraDataToPOAMiddleware
from concurrent.futures import ThreadPoolExecutor
from web3 import AsyncWeb3
import asyncio

with open("erc-20-abi.json", 'rb+') as f:
    abi = json.load(f)

async def get_wallets_at_block(w3, block):
    blockdata = await w3.eth.get_block(block, True)
    addresses = set()
    print('GOT TRANSACTOINS')
    for transaction in blockdata.transactions:
        addresses.add(transaction["from"])
        addresses.add(transaction["to"])

    return addresses


async def get_balances(w3, addresses, token, abi):
    token_contract = w3.eth.contract(address=token, abi=abi)
    return_dict = {}

    for address in addresses:
        address = w3.to_checksum_address(address)
        amount  = await token_contract.functions.balanceOf(address).call()
        if amount > 0:
            amount = Web3.from_wei(amount, "ether") # all tokens have 18 decimals as ether has
            return_dict[address] = amount

    return return_dict


def select_winners(number_block, holders):
    weighted_list = []
    for address, total_tokens in holders.items():
        weighted_list.extend([address] * total_tokens)


    random.seed(number_block)

    winners = random.sample(weighted_list, 100)
    return winners

async def get_wallets(w3, number_block):
    addresses = await get_wallets_at_block(w3, number_block)

    tokens = ["0x20ef84969f6d81Ff74AE4591c331858b20AD82CD",
             "0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10",
             "0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D"]

    # adds = list(addresses)[:10] for tests it could be used
    results = []

    async def fetch_balances(token):
        balances = await get_balances(w3, addresses, token, abi)
        results.append(balances)


    with ThreadPoolExecutor(max_workers=3) as executor:
        tasks = [asyncio.get_event_loop().run_in_executor(executor, lambda t=token: asyncio.run(fetch_balances(t))) for token in tokens]
        await asyncio.gather(*tasks)

    dict1 = results[0]
    dict2 = results[1]
    dict3 = results[2]

    common_keys = set(dict1.keys()) & set(dict2.keys()) & set(dict3.keys())
    result_dict = {key: dict1[key] + dict2[key] + dict3[key] for key in common_keys}

    winners = select_winners(number_block, result_dict)

    return winners


async def main():
    # paste ur rpc for faster connection and parsing
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider("https://base.drpc.org"), modules={'eth': (AsyncEth,)})

    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    print("Is connected: ", await w3.is_connected())
    block = int(input("Input number block: "))
    print(await get_wallets(w3, block))

if __name__ == '__main__':
    asyncio.run(main())