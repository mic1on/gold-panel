"""
HTTP 客户端模块
"""

import httpx
from usepy.dict import AdDict


class ApiClient:
    def __init__(self, base_url, timeout=10):
        self.base_url = base_url
        self.timeout = timeout

        # 创建 httpx 客户端
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            },
        )

    def _response_to_dict(self, response):
        return AdDict(response.json())

    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return self._response_to_dict(response)

    def post(self, endpoint, data=None, json=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        # 合并额外的 headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        response = self.client.post(url, data=data, json=json, headers=request_headers)
        response.raise_for_status()
        return self._response_to_dict(response)

    def __del__(self):
        """清理资源"""
        if hasattr(self, "client"):
            self.client.close()


class JdjrApi:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    def get_latest_gold_price(self):
        """获取实时金价"""
        resp = self.api_client.get("/gw/generic/hj/h5/m/latestPrice")
        return resp.resultData.datas


api_client = ApiClient(base_url="https://api.jdjygold.com/")
client = JdjrApi(api_client)
