from urllib import urlencode as _urlencode

from data_access.internet import send_delete_request_with_header

from debug_utils import should_print_debug, print_to_console, LOG_ALL_MARKET_RELATED_CRAP

from utils.key_utils import signed_body_256
from utils.time_utils import get_now_seconds_utc
from utils.file_utils import log_to_file

from binance.constants import BINANCE_CANCEL_ORDER


def cancel_order_binance(key, pair_name, deal_id):

    final_url = BINANCE_CANCEL_ORDER

    body = {
        "recvWindow": 5000,
        "timestamp": get_now_seconds_utc(),
        "symbol": pair_name,
        "orderId": deal_id
    }

    signature = signed_body_256(body, key.secret)

    body["signature"] = signature

    final_url += _urlencode(body)

    headers = {"X-MBX-APIKEY": key.api_key}

    if should_print_debug():
        msg = "cancel_order_binance: url - {url} headers - {headers} body - {body}".format(url=final_url,
                                                                                             headers=headers,
                                                                                             body=body)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, "market_utils.log")

    err_msg = "cancel binance order with id {id}".format(id=deal_id)

    res = send_delete_request_with_header(final_url, headers, {}, err_msg, max_tries=3)

    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, "market_utils.log")

    return res


def parse_deal_id_binance(json_document):
    """
    {u'orderId': 6599290,
    u'clientOrderId': u'oGDxv6VeLXRdvUA8PiK8KR',
    u'origQty': u'27.79000000',
    u'symbol': u'OMGBTC',
    u'side': u'SELL',
    u'timeInForce': u'GTC',
    u'status': u'FILLED',
    u'transactTime': 1514223327566,
    u'type': u'LIMIT',
    u'price': u'0.00111100',
    u'executedQty': u'27.79000000'}
    """
    if json_document is not None and "orderId" in json_document:
        return json_document["orderId"]

    return None