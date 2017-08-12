from datetime import datetime

from currency_utils import get_pair_name_by_id, get_currency_pair_from_bittrex, \
    get_currency_pair_from_kraken, get_currency_pair_from_poloniex

from BaseData import BaseData
from enums.deal_type import DEAL_TYPE
from enums.exchange import EXCHANGE
from utils.exchange_utils import get_exchange_name_by_id


class OrderHistory(BaseData):
    def __init__(self, pair, timest, deal_type, price, amount, total, exchange):
        # FIXME NOTE - various volume data?
        self.pair_id = pair
        self.pair = get_pair_name_by_id(pair)
        self.timest = long(timest)
        self.deal_type = deal_type
        self.price = float(price)
        self.amount = float(amount)
        self.total = long(total)
        self.exchange_id = exchange
        self.exchange = get_exchange_name_by_id(exchange)

    @classmethod
    def from_poloniex(cls, json_document, pair, timest):
        """
        {
          "globalTradeID":202950655,
          "tradeID":2459916,
          "date":"2017-08-02 17:06:09",
          "type":"sell",
          "rate":"0.00006476",
          "amount":"323.78885919",
          "total":"0.02096856"
        }
        """

        utc_time = datetime.strptime(json_document["date"], "%Y-%m-%d %H:%M:%S")
        deal_timest = (utc_time - datetime(1970, 1, 1)).total_seconds()

        deal_type = DEAL_TYPE.BUY

        if "sell" in json_document["type"]:
            deal_type = DEAL_TYPE.SELL

        price = json_document["rate"]
        amount = json_document["amount"]
        total = json_document["total"]

        currency_pair = get_currency_pair_from_poloniex(pair)

        return OrderHistory(pair, deal_timest, deal_type, price, amount, total, EXCHANGE.POLONIEX)

    @classmethod
    def from_kraken(cls, json_document, pair, timest):
        """
        <pair_name> = pair name
            array of array entries(<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>)
        last = id to be used as since when polling for new trade data
        """

        deal_timest = json_document[2]
        deal_type = DEAL_TYPE.BUY

        if "s" in json_document[3]:
            deal_type = DEAL_TYPE.SELL

        price = float(json_document[0])
        amount = float(json_document[1])
        total = price * amount

        currency_pair = get_currency_pair_from_kraken(pair)

        return OrderHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.POLONIEX)


    @classmethod
    def from_bittrex(cls, json_document, pair, timest):
        """
        [
           {
              "Id":59926023,
              "TimeStamp":"2017-08-02T17:11:28.033",
              "Quantity":3.49909364,
              "Price":0.01565000,
              "Total":0.05476081,
              "FillType":"FILL",
              "OrderType":"SELL"
           },
           {
              "Id":59926007,
              "TimeStamp":"2017-08-02T17:11:15.83",
              "Quantity":0.11242970,
              "Price":0.01566000,
              "Total":0.00176064,
              "FillType":"FILL",
              "OrderType":"BUY"
           }
        ]
        """

        try:
            utc_time = datetime.strptime(json_document["TimeStamp"], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            utc_time = datetime.strptime(json_document["TimeStamp"], "%Y-%m-%dT%H:%M:%S")

        deal_timest = (utc_time - datetime(1970, 1, 1)).total_seconds()

        deal_type = DEAL_TYPE.BUY

        if "SELL" in json_document["OrderType"]:
            deal_type = DEAL_TYPE.SELL

        price = float(json_document["Price"])
        amount = float(json_document["Quantity"])
        total = json_document["Total"]

        currency_pair = get_currency_pair_from_bittrex(pair)

        return OrderHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.POLONIEX)