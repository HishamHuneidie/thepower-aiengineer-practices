"""List of public methods in MCP Server"""

from mcp.server import MCPServer
import app.application.use_cases as application
from app.domain.entities import Order
import json


mcp = MCPServer('orders')


@mcp.tool()
def get_order_by_id(id: int) -> Order|None:
    """Get order by id. Examples of valid ids are: 1234, 4567, 7890"""
    return application.get_order(id)


@mcp.tool()
def get_all_orders() -> list[Order]:
    """Get list of orders"""
    return application.get_orders()


@mcp.tool()
def create_order(order: dict) -> None:
    """Create an order"""
    return application.create_order(order)


@mcp.resource('orders://structure')
def create_order() -> str:
    """It shows the structure of an order"""
    return json.dumps({
        'entity_name': 'Order',
        'fields': {
            'id': 'integer',
            'title': 'string',
            'status': 'Literal["created", "updated", "deleted"]',
            'price': 'float',
            'currency': 'Literal["EUR", "USD"]',
        },
        'required': ['title', 'price'],
        'default_fields': {
            'status': 'created',
            'currency': 'EUR',
        },
    })


if __name__ == '__main__':
    mcp.run(
        transport='streamable-http',
        host='0.0.0.0',
        port=8000,
        stateless_http=True,
        json_response=True,
    )