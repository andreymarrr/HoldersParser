import locale
import requests
import csv
import subprocess

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def getDecimals(tokenAddress): # decimals of token
    url = f"https://api.ethplorer.io/getTokenInfo/{tokenAddress}?apiKey=freekey"
    response = requests.get(url)
    return int(response.json().get("decimals", 18))

def getTokenHolders(tokenAddress, count): # get top holders of token
    url = f"https://api.ethplorer.io/getTopTokenHolders/{tokenAddress}?apiKey=freekey&limit={count}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("holders", [])
    else:
        print("Error:", response.status_code)
        return []

def getCurrentBlock(): # need to get block for balance at specific time
    url = "https://mainnet.infura.io/v3/API_KEY"
    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['result']

def getBlock7D():
    currentBlock = int(getCurrentBlock(), 16)
    blocksPerDay = int(86400 / 13)
    blocksPerWeek = blocksPerDay * 7
    return hex(currentBlock - blocksPerWeek)

def getBlock30D():
    currentBlock = int(getCurrentBlock(), 16)
    blocksPerDay = int(86400 / 13)
    blocksPerMonth = blocksPerDay * 30
    return hex(currentBlock - blocksPerMonth)

def getBalanceAnytime(tokenAddress, address, block): # get balance of address at specific block
    url = "https://mainnet.infura.io/v3/API_KEY"
    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {
            "to": f"{tokenAddress}",
            "data": f"0x70a08231000000000000000000000000{address[2:]}" },
            f"{block}"
        ],
        "id": 1
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()['result']
    decimals = getDecimals(tokenAddress)
    resultDec = int(result, 16) / 10 ** decimals
    #formatBalance = locale.format_string("%.2f", resultDec, grouping=True)
    return resultDec

def saveToCSV(tokenAddress, count, filename="tokenHolders.csv"):
    decimals = getDecimals(tokenAddress)
    with open(filename, "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Address", "Balance", "Balance 7D", "Difference 7D ago", "Movement in 7D", "Balance 30D", "Difference 30D ago", "Movement in 30D", "Wallet Status"])

        tokenHolders = getTokenHolders(tokenAddress, count)
        for holder in tokenHolders:
            address = holder.get("address")
            balance = holder.get("balance") / 10 ** decimals
            balance7D = getBalanceAnytime(tokenAddress, address, getBlock7D())
            balance30D = getBalanceAnytime(tokenAddress, address, getBlock30D())
            difference7D = float(balance - balance7D)
            difference30D = float(balance - balance30D)

            formatBalance = locale.format_string("%.2f", balance, grouping=True)
            formatBalance7D = locale.format_string("%.2f", balance7D, grouping=True)
            formatBalance30D = locale.format_string("%.2f", balance30D, grouping=True)
            formatDifference7D = locale.format_string("%.2f", difference7D, grouping=True)
            formatDifference30D = locale.format_string("%.2f", difference30D, grouping=True)
            if difference30D == 0 and difference7D == 0:
                status = 'Inactive'
            else:
                status = 'Active'

            if difference7D < 0:
                movement7D = 'Sold'
            elif difference7D > 0:
                movement7D = 'Bought'
            else:
                movement7D = 'Nothing'

            if difference30D < 0:
                movement30D = 'Sold'
            elif difference30D > 0:
                movement30D = 'Bought'
            else:
                movement30D = 'Nothing'

            writer.writerow([address, formatBalance, formatBalance7D, formatDifference7D, movement7D, formatBalance30D, formatDifference30D, movement30D, status])

    print(f"Saved to {filename}")
    subprocess.call(["open", filename])
    return filename


if __name__ == "__main__":
    tokenAddress = "TOKEN CONTRACT"
    count = 50 # num of top holders including exchanges, smart contracts, dead wallets... (can be fixed with tags)

    saveToCSV(tokenAddress, count)