import requests
from concurrent.futures import ThreadPoolExecutor
import json

class AlchemyScanner:
    BASE_URL = "https://eth-mainnet.g.alchemy.com/v2"

    def __init__(self, api_key, address, max_threads=10):
        self.api_key = api_key
        self.address = address
        self.max_threads = max_threads
        self.result = []
    
    def fetch_transactions(self, page_key=None):
        """Gửi request đến Alchemy để lấy giao dịch"""
        url = f"{self.BASE_URL}/{self.api_key}"
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": "0x0",
                "toBlock": "latest",
                "fromAddress": self.address,
                "category": ["external", "internal", "erc20", "erc721", "erc1155"],
                "maxCount": "0x3E8",  # 1000 giao dịch
                "order": "desc"
            }],
            "id": 1
        }

        if page_key:
            payload["params"][0]["pageKey"] = page_key  # Tiếp tục lấy từ pageKey

        response = requests.post(url, json=payload).json()
        
        if "result" in response and "transfers" in response["result"]:
            return response["result"].get("transfers", []), response["result"].get("pageKey")
        
        return [], None

    def get_transactions(self, max_txs=100000):
        """Lấy tối đa 100,000 giao dịch bằng multi-threading"""
        page_key = None

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            while len(self.result) < max_txs:
                future = executor.submit(self.fetch_transactions, page_key)
                futures.append(future)

                for f in futures:
                    transactions, page_key = f.result()
                    self.result.extend(transactions)

                    print(f"📦 Đã lấy {len(self.result)} giao dịch...")

                    if len(self.result) >= max_txs or not page_key:
                        self.save_to_file()  # Ghi dữ liệu vào file khi hoàn thành
                        return self.result[:max_txs]  # Dừng khi đủ hoặc hết dữ liệu
        
        self.save_to_file()
        return self.result[:max_txs]

    def save_to_file(self, filename="transactions.txt"):
        """Lưu giao dịch vào file .txt"""
        with open(filename, "w", encoding="utf-8") as f:
            for tx in self.result:
                f.write(json.dumps(tx, ensure_ascii=False) + "\n")
        
        print(f"✅ Giao dịch đã được lưu vào {filename}")

# 🔥 Chạy chương trình
if __name__ == "__main__":
    api_key = "vHX215j9gH01Qc94rX2eEAsLeYohIu9X"
    eth_address = "0x1f9090aaE28b8a3dCeaDf281B0F12828e676c326"

    scanner = AlchemyScanner(api_key, eth_address, max_threads=20)
    transactions = scanner.get_transactions()
    print(f"✅ Tổng số giao dịch lấy được: {len(transactions)}")
