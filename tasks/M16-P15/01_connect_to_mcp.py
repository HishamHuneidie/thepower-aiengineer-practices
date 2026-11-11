"""
MCP client. It connects to MCP server in localhost:8000/mcp
"""

import json
import sys
from urllib.request import Request, urlopen

from colorize import colorize


class MCPClient:

    def __init__(self):
        self.url = 'http://localhost:8000/mcp'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'MCP-Protocol-Version': '2025-06-18',
        }
        self.config = {
            'protocolVersion': 'protocolVersion',
            'capabilities': {},
            'clientInfo': {
                'name': 'easy-client',
                'version': '1.0',
            },
        }

        self.initialize()

    def initialize(self) -> None:
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': self.config,
        }

        self.request(body)

    def list_tools(self) -> dict | list[dict] | None:
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list',
            'params': {},
        }

        response = self.request(body)

        try:
            return response['result']['tools']
        except IndexError:
            return None

    def call_tool(self, method: str, arguments: dict | None = None) -> dict | list[dict] | None:
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                "name": method,
                "arguments": arguments or {},
            },
        }

        response = self.request(body)

        try:
            return response['result']['structuredContent']['result']
        except IndexError:
            return None

    def list_resources(self) -> dict | list[dict] | None:
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'resources/list',
            'params': {},
        }

        response = self.request(body)

        try:
            return response['result']['resources']
        except IndexError:
            return None

    def read_resource(self, name: str) -> dict | list[dict] | None:
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'resources/read',
            'params': {
                "uri": name,
            },
        }

        response = self.request(body)

        try:
            return response['result']['contents'][0]['text']
        except IndexError:
            return None

    def request(self, body: dict) -> dict | list[dict] | None:
        request = Request(self.url, method='POST', data=json.dumps(body).encode(), headers=self.headers)

        with urlopen(request) as response:
            content = json.loads(response.read())

        return content


client = MCPClient()

print()
print('TOOLS =================')
print()
print('Call list of tools:')
print(colorize(str(client.list_tools()), 'yellow'))
print()
print('Get all orders:')
print(colorize(str(client.call_tool('get_all_orders')), 'blue'))
print()
print('Get order by id:')
print(colorize(str(client.call_tool('get_order_by_id', {'id': 1234})), 'magenta'))
print()
print('Get non-existent order by id:')
print(colorize(str(client.call_tool('get_order_by_id', {'id': 7777})), 'red'))
print()
print()
print('TOOLS =================')
print()
print('List resources:')
print(colorize(str(client.list_resources()), 'blue'))
print()
print('Read resource:')
print(colorize(str(client.read_resource('orders://structure')), 'green'))
