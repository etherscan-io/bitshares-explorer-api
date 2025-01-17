import datetime
import calendar
import connexion

from services.bitshares_websocket_client import client as bitshares_ws_client
from services.bitshares_elasticsearch_client import client as bitshares_es_client
from services.cache import cache
import api.explorer
import es_wrapper
import config


def info():
    return {
        "name": "Bitshares",
        "description": "The BitShares Blockchain is an industrial-grade decentralized platform built for "
                       "high-performance financial smart contracts mostly known for: its token factory,"
                       " a decentralized exchange as a built-in native dapp (known as the DEX) and its stablecoins"
                       " or, as they are called in BitShares, Smartcoins. It represents the first decentralized"
                       " autonomous community that lets its core token holders decide on its future direction and"
                       " products by means of on-chain voting. It is also the first DPoS blockchain in existence and"
                       " the first blockchain to implement stablecoins.",
        "location": "Worldwide",
        "logo": "https://bitshares.org/exchange-logo.png",
        "website": "https://bitshares.org/",
        "twitter": "https://twitter.com/bitshares",
        "capability": {
            "markets": True,
            "trades": True,
            "tradesSocket": False,
            "orders": False,
            "ordersSocket": False,
            "ordersSnapshot": True,
            "candles": False
        }
    }


def markets():
    result = [
        {"id": "CNY-BTS", "base": "CNY", "quote": "BTS"},
        {"id": "USD-BTS", "base": "USD", "quote": "BTS"},
        {"id": "CNY-USD", "base": "CNY", "quote": "USD"},
        {"id": "EUR-BTS", "base": "EUR", "quote": "BTS"},
        {"id": "RUBLE-BTS", "base": "RUBLE", "quote": "BTS"},
        {"id": "SILVER-BTS", "base": "SILVER", "quote": "BTS"},
        {"id": "GOLD-BTS", "base": "GOLD", "quote": "BTS"}
    ]

    return result


@cache.memoize()
def trades(market, since):

    market_id = market.split('-')
    base = market_id[0]
    quote = market_id[1]

    base_asset = api.explorer._get_asset_id_and_precision(base)
    quote_asset = api.explorer._get_asset_id_and_precision(quote)

    trade_history = es_wrapper.get_trade_history(search_after=since, base=base_asset[0], quote=quote_asset[0], size=100,
                                                 sort_by='operation_id_num')

    results = []
    for trade in trade_history:
        base_amount = trade["operation_history"]["op_object"]["fill_price"]["base"]["amount"]
        quote_amount = trade["operation_history"]["op_object"]["fill_price"]["base"]["amount"]

        results.append({
            "id": str(trade["operation_id_num"]),
            "timestamp": trade["block_data"]["block_time"] + "Z",
            "price": str(float(float(base_amount)/int(base_asset[1]))/float(float(quote_amount)/int(quote_asset[1]))),
            "amount": str(trade["operation_history"]["op_object"]["receives"]["amount"]/quote_asset[1])
        })

    return results


def snapshot(market):
    result = {}

    market_id = market.split('-')
    base = market_id[0]
    quote = market_id[1]

    order_book = api.explorer.get_order_book(base, quote, 100)

    bids = []
    asks = []

    for bid in order_book["bids"]:
        bids.append([float(bid["price"]), float(bid["base"])])

    result["bids"] = bids

    for ask in order_book["asks"]:
        asks.append([float(ask["price"]), float(ask["base"])])

    result["asks"] = asks

    result["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    return result
