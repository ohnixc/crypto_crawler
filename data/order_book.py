import re
import copy

from bittrex.currency_utils import get_currency_pair_from_bittrex
from kraken.currency_utils import get_currency_pair_from_kraken
from poloniex.currency_utils import get_currency_pair_from_poloniex
from binance.currency_utils import get_currency_pair_from_binance
from huobi.currency_utils import get_currency_pair_from_huobi

from analysis.binary_search import binary_search

from data.base_data import BaseData
from data.deal import Deal

from enums.exchange import EXCHANGE
from enums.status import STATUS

from utils.exchange_utils import get_exchange_name_by_id
from utils.time_utils import get_now_seconds_utc_ms, get_date_time_from_epoch
from utils.file_utils import log_to_file
from utils.currency_utils import get_pair_name_by_id
from utils.system_utils import die_hard

from constants import MIN_VOLUME_ORDER_BOOK
from utils.debug_utils import SOCKET_ERRORS_LOG_FILE_NAME
from logging_tools.socket_logging import log_sequence_id_mismatch

# FIXME NOTE - not the smartest idea to deal with
regex_string = "\[exchange - (.*) exchange_id - (.*) pair - (.*) pair_id - (.*) timest - (.*) bids - (.*) asks - (.*)\]"
regex = re.compile(regex_string)

deal_array_regex_string = "price - ([0-9]*.[0-9e-]*) volume - ([0-9]*.[0-9e-]*)"
deal_array_regex = re.compile(deal_array_regex_string)

ORDER_BOOK_TYPE_NAME = "order_book"

ORDER_BOOK_INSERT_BIDS = "insert into order_book_bid(order_book_id, price, volume) values (%s, %s, %s);"
ORDER_BOOK_INSERT_ASKS = "insert into order_book_ask(order_book_id, price, volume) values (%s, %s, %s);"

ORDER_BOOK_TABLE_NAME = "order_book"
ORDER_BOOK_COLUMNS = ("pair_id", "exchange_id", "timest", "date_time")
ORDER_BOOK_INSERT_QUERY = """insert into {table_name} ({columns}) values(%s, %s, %s, %s) returning id;""".format(
    table_name=ORDER_BOOK_TABLE_NAME, columns=','.join(ORDER_BOOK_COLUMNS))


def cmp_method_ask(a, b):
    return a.price < b.price


def cmp_method_bid(a, b):
    return a.price > b.price


class OrderBook(BaseData):
    insert_query = ORDER_BOOK_INSERT_QUERY
    type = ORDER_BOOK_TYPE_NAME

    table_name = ORDER_BOOK_TABLE_NAME
    columns = ORDER_BOOK_COLUMNS

    def __init__(self, pair_id, timest, sell_bids, buy_bids, exchange_id, sequence_id=None):
        # FIXME NOTE - various volume data?
        self.pair_id = int(pair_id)
        self.pair_name = get_pair_name_by_id(self.pair_id)
        self.timest = timest
        self.ask = sell_bids
        self.bid = buy_bids
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)
        self.sequence_id = sequence_id

    def is_valid(self):
        return self.ask and self.bid

    def sort_by_price(self):
        self.bid = sorted(self.bid, key=lambda x: x.price, reverse=True)        # highest - first
        self.ask = sorted(self.ask, key=lambda x: x.price, reverse=False)       # lowest - first

    def get_pg_arg_list(self):
        return (self.pair_id,
                self.exchange_id,
                self.timest,
                get_date_time_from_epoch(self.timest)
                )

    def __str__(self):
        attr_list = [a for a in dir(self) if not a.startswith('__') and
                     not a.startswith("ask") and not a.startswith("bid") and
                     not a.startswith("insert") and not callable(getattr(self, a))]
        str_repr = "["
        for every_attr in attr_list:
            str_repr += every_attr + " - " + str(getattr(self, every_attr)) + " "

        str_repr += "bids - [" + "\n".join(map(str, self.bid)) + "] "
        str_repr += "asks - [" + "\n".join(map(str, self.ask)) + "]]"

        return str_repr

    @classmethod
    def from_poloniex(cls, json_document, currency, timest):
        """
        {"asks":[["0.00006604",11590.35669799],["0.00006606",25756.70896058]],
        "bids":[["0.00006600",46771.47390146],["0.00006591",25268.665],],
        "isFrozen":"0","seq":41049600}
        """

        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document["asks"]]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document["bids"]]

        pair_id = get_currency_pair_from_poloniex(currency)

        sequence_id = long(json_document["seq"])

        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.POLONIEX, sequence_id)

    @classmethod
    def from_kraken(cls, json_document, currency, timest):
        """
        {"error":[],"result":{"XETHXXBT":{"asks":[["0.081451","0.200",1501690777],["0.081496","163.150",1501691124]
        "bids":[["0.080928","0.100",1501691107],["0.080926","0.255",1501691110]
        """

        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document["asks"]]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document["bids"]]

        pair_id = get_currency_pair_from_kraken(currency)

        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, json_document, currency, timest):
        """
        {"success":true,"message":"","result":{"buy":[{"Quantity":12.76073322,"Rate":0.01557999},{"Quantity":12.01802925,"Rate":0.01557998}
        "sell":[{"Quantity":0.38767680,"Rate":0.01560999},{"Quantity":2.24182363,"Rate":0.01561999}
        """

        sell_bids = []
        if "sell" in json_document and json_document["sell"] is not None:
            for b in json_document["sell"]:
                sell_bids.append(Deal(b["Rate"], b["Quantity"]))

        buy_bids = []
        if "buy" in json_document and json_document["buy"] is not None:
            for b in json_document["buy"]:
                buy_bids.append(Deal(b["Rate"], b["Quantity"]))

        pair_id = get_currency_pair_from_bittrex(currency)

        # DK FIXME! not exactly but Rest API doesnt offer any viable options :/
        sequence_id = get_now_seconds_utc_ms()

        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BITTREX, sequence_id)

    @classmethod
    def from_binance(cls, json_document, currency, timest):
        """
        "lastUpdateId":1668114,"bids":[["0.40303000","22.00000000",[]],],"asks":[["0.41287000","1.00000000",[]]
        """

        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get("asks", [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get("bids", [])]

        pair_id = get_currency_pair_from_binance(currency)

        sequence_id = long(json_document["lastUpdateId"])

        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BINANCE, sequence_id)

    @classmethod
    def from_huobi(cls, json_document, pair_name, timest):
        """
        "tick": {
            "id": 1489464585407,
            "ts": 1489464585407,
            "bids": [
              [7964, 0.0678], // [price, amount]
              [7963, 0.9162],
              [7961, 0.1],
            ],
            "asks": [
              [7979, 0.0736],
              [7980, 1.0292],
            ]

        :param pair_name:
        :param timest:
        :return:
        """

        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get("asks", [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get("bids", [])]

        pair_id = get_currency_pair_from_huobi(pair_name)

        sequence_id = long(json_document["version"])

        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.HUOBI, sequence_id)

    @classmethod
    def from_row(cls, db_row, asks_rows, sell_rows):
        # id, pair_id, exchange_id, timest, date_time
        # id, order_book_id, price, volume

        currency_pair_id = db_row[1]
        exchange_id = db_row[2]
        timest = db_row[3]

        ask_bids = [Deal(entry[2], entry[3]) for entry in asks_rows]
        sell_bids = [Deal(entry[2], entry[3]) for entry in sell_rows]

        return OrderBook(currency_pair_id, timest, ask_bids, sell_bids, exchange_id)

    def insert_new_bid_preserve_order(self, new_bid, overwrite_volume=True, err_msg=None):
        """
            Bids array are sorted in reversed order i.e. highest - first
            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!

        """

        item_insert_point = binary_search(self.bid, new_bid, cmp_method_bid)
        is_present = False
        if item_insert_point < len(self.bid):
            is_present = self.bid[item_insert_point] == new_bid

        almost_zero = new_bid.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and not overwrite_volume
        update_volume_error = not is_present and not overwrite_volume
        should_delete = almost_zero and is_present

        if should_delete:
            del self.bid[item_insert_point]
        elif is_present:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_overwrite:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_update_volume:
            self.bid[item_insert_point].volume -= new_bid.volume
            
            if self.bid[item_insert_point].volume < 0:
                die_hard("Negative value of bid!")

        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            # FIXME NOTE O(n) - slow by python implementation
            self.bid.insert(item_insert_point, new_bid)

    def insert_new_ask_preserve_order(self, new_ask, overwrite_volume=True, err_msg=None):
        """
            Ask array are sorted in reversed order i.e. lowest - first

            self.ask = sorted(self.ask, key = lambda x: x.price, reverse=False)

            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!
        """

        item_insert_point = binary_search(self.ask, new_ask, cmp_method_ask)
        is_present = False
        if item_insert_point < len(self.ask):
            is_present = self.ask[item_insert_point] == new_ask

        almost_zero = new_ask.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and not overwrite_volume
        update_volume_error = not is_present and not overwrite_volume
        should_delete = almost_zero and is_present

        if should_delete:
            del self.ask[item_insert_point]
        elif should_overwrite:
            self.ask[item_insert_point].volume = new_ask.volume
        elif should_update_volume:
            self.ask[item_insert_point].volume -= new_ask.volume

            if self.ask[item_insert_point].volume < 0:
                die_hard("Negative value of ask!")

        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            # FIXME NOTE O(n) - slow by python implementation
            self.ask.insert(item_insert_point, new_ask)

    def update_for_poloniex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """

        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)

            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                # DK NOTE: we dont care about outdated updates
                return STATUS.SUCCESS
            if (self.sequence_id + 1) != order_book_update.sequence_id:
                log_sequence_id_mismatch("Poloniex", self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE

            self.sequence_id = order_book_update.sequence_id

            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)

            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)

        return STATUS.SUCCESS

    def _copy_order_book(self, other_order_book):

        self.timest = other_order_book.timest
        self.exchange_id = other_order_book.exchange_id
        self.exchange = other_order_book.exchange_id
        self.pair_id = other_order_book.pair_id
        self.pair_name = other_order_book.pair_id

        self.ask = copy.deepcopy(other_order_book.ask)
        self.bid = copy.deepcopy(other_order_book.bid)
        self.sequence_id = other_order_book.sequence_id

    def update_for_bittrex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """

        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)

            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                # DK NOTE: we dont care about outdated updates
                return STATUS.SUCCESS
            elif (self.sequence_id + 1) != order_book_update.sequence_id:
                log_sequence_id_mismatch("Bittrex", self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE
            
            self.sequence_id = order_book_update.sequence_id

            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)

            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)

            for trade_sell in order_book_update.trades_sell:
                err_msg = "Bittrex socket CANT FIND fill request FILL AND UPDATE - SELL??? {wtf}".format(wtf=trade_sell)
                self.insert_new_ask_preserve_order(trade_sell, overwrite_volume=False, err_msg=err_msg)

            for trade_buy in order_book_update.trades_buy:
                err_msg = "Bittrex socket CANT FIND fill request FILL AND UPDATE - BUY??? {wtf}".format(wtf=trade_buy)
                self.insert_new_bid_preserve_order(trade_buy, overwrite_volume=False, err_msg=err_msg)

        # FIXME case for sequence_id!
        return STATUS.SUCCESS

    def update_for_binance(self, order_book_update):
        """
        For binance sequence_id is a range of number.
        one number for every price level updates.

        "U": 157,           // First update ID in event
        "u": 160,           // Final update ID in event

        During update parsing we are use following logic:

        sequence_id = long(order_book_delta["U"])

        :param order_book_update:
        :return:
        """

        if self.sequence_id >= order_book_update.sequence_id:
            # DK NOTE: we dont care about outdated updates
            return STATUS.SUCCESS

        if (self.sequence_id + 1) != order_book_update.sequence_id:
            log_sequence_id_mismatch("Binance", self.sequence_id, order_book_update.sequence_id)
            return STATUS.FAILURE

        self.sequence_id = order_book_update.sequence_id_end

        for ask in order_book_update.ask:
            self.insert_new_ask_preserve_order(ask)

        for bid in order_book_update.bid:
            self.insert_new_bid_preserve_order(bid)

        return STATUS.SUCCESS

    def update_for_huobi(self, order_book_update):
        """
        NOTE: always get full order book
        :param order_book_update:
        :return:
        """

        self._copy_order_book(order_book_update)

        self.sort_by_price()

        return STATUS.SUCCESS

    def update(self, exchange_id, order_book_delta):

        # DK FIXME - performance wise - remove logging!
        # ts_ms = str(get_now_seconds_utc_ms())
        # exchange_name = get_exchange_name_by_id(exchange_id)
        # 
        # file_name = exchange_name + "_" + ts_ms + "_raw.txt"
        # log_to_file(order_book_delta, file_name)
        #        
        # file_name = exchange_name + "_" + ts_ms + "_before.txt"
        # 
        # log_to_file(self, file_name)

        method = {
            EXCHANGE.POLONIEX: self.update_for_poloniex,
            EXCHANGE.BITTREX: self.update_for_bittrex,
            EXCHANGE.BINANCE: self.update_for_binance,
            EXCHANGE.HUOBI: self.update_for_huobi
        }[exchange_id]

        return method(order_book_delta)

        # DK FIXME - performance wise - remove logging!
        # file_name = exchange_name + "_" + ts_ms + "_after.txt"
        # log_to_file(self, file_name)
