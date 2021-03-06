from constants import ARBITRAGE_CURRENCY
from enums.exchange import EXCHANGE

from data.base_data import BaseData
from data.balance import Balance
from utils.currency_utils import split_currency_pairs
from core.base_analysis import get_change


def dummy_balance_init(timest, default_volume, default_available_volume):
    balance = {}

    total_balance = {}
    available_balance = {}

    for currency_id in ARBITRAGE_CURRENCY:
        total_balance[currency_id] = default_volume

    for currency_id in ARBITRAGE_CURRENCY:
        available_balance[currency_id] = default_available_volume

    for exchange_id in EXCHANGE.values():
        balance[exchange_id] = Balance(exchange_id, timest, available_balance, total_balance)

    return BalanceState(balance)


class BalanceState(BaseData):
    def __init__(self, balance_per_exchange):
        self.balance_per_exchange = balance_per_exchange.copy()

    def __str__(self):
        str_repr = ""
        for b in self.balance_per_exchange:
            str_repr += str(self.balance_per_exchange[b]) + "\n"

        return str_repr

    def add_balance(self, currency_id, exchange_id, volume):
        prev_volume = self.balance_per_exchange[exchange_id].available_balance[currency_id]
        self.balance_per_exchange[exchange_id].available_balance[currency_id] = volume + prev_volume
        # FIXME NOTE: total_balance ?

    def subtract_balance(self, currency_id, exchange_id, volume):
        prev_volume = self.balance_per_exchange[exchange_id].available_balance[currency_id]
        self.balance_per_exchange[exchange_id].available_balance[currency_id] = prev_volume - volume
        # FIXME NOTE: total_balance ?

    def add_balance_by_pair(self, order_book, volume, price):
        # i.e. we BUY dst_currency_id for src_currency_id
        src_currency_id, dst_currency_id = split_currency_pairs(order_book.pair_id)

        self.subtract_balance(src_currency_id, order_book.exchange_id, volume * price)  # <<<==== bitcoin!

        self.add_balance(dst_currency_id, order_book.exchange_id, volume)

        self.update_time(order_book.exchange_id, order_book.timest)

    def subtract_balance_by_pair(self, order_book, volume, price):
        # i.e. we SELL dst_currency_id for src_currency_id
        src_currency_id, dst_currency_id = split_currency_pairs(order_book.pair_id)
        self.subtract_balance(dst_currency_id, order_book.exchange_id, volume)

        self.add_balance(src_currency_id, order_book.exchange_id, volume * price) # <<<==== bitcoin!

        self.update_time(order_book.exchange_id, order_book.timest)

    def do_we_have_enough_by_pair(self, pair_id, exchange_id, volume, price):

        # i.e. we are going to BUY volume of dst_currency by price
        # using base_currency so we have to adjust volume

        base_currency_id, dst_currency_id = split_currency_pairs(pair_id)

        return self.do_we_have_enough(base_currency_id, exchange_id, volume * price)

    def do_we_have_enough(self, currency_id, exchange_id, volume):
        return self.balance_per_exchange[exchange_id].available_balance[currency_id] >= volume

    """def get_volume_by_pair_id(self, pair_id, exchange_id, price_mutliplicator):
        src_currency_id, dst_currency_id = split_currency_pairs(pair_id)
        return self.balance_per_exchange[exchange_id].balance[src_currency_id] * price_mutliplicator
        """

    def get_available_volume_by_currency(self, currency_id, exchange_id):
        return self.balance_per_exchange[exchange_id].available_balance[currency_id]

    def update_time(self, exchange_id, timest):
        self.balance_per_exchange[exchange_id].last_update = timest

    def expired(self, timest, src_exchange_id, dst_exchange_id, threshold):
        diff1 = timest - self.balance_per_exchange[src_exchange_id].last_update
        diff2 = timest - self.balance_per_exchange[dst_exchange_id].last_update

        res = diff1 > threshold or diff2 > threshold
        if res:
            print "BALANCE_EXPIRE TRACE"
            print "src_exchange_id", src_exchange_id, "diff", diff1, "ts", timest, "last_update", self.balance_per_exchange[src_exchange_id].last_update
            print "src", self.balance_per_exchange[src_exchange_id]
            print "dst_exchange_id", dst_exchange_id, "diff", diff2, "ts", timest, "last_update", self.balance_per_exchange[dst_exchange_id].last_update
            print "dst", self.balance_per_exchange[dst_exchange_id]

        return res

    def is_there_disbalance(self, currency_id, src_exchange_id, dst_exchange_id, threshold):
        """
            Check whether amount of dst_currency at pair of exchange do not differ more than threshold
            in percent.

        :param dst_currency_id:
        :param src_exchange_id:
        :param dst_exchange_id:
        :return:
        """
        balance_1 = self.balance_per_exchange[src_exchange_id].available_balance[currency_id]
        balance_2 = self.balance_per_exchange[dst_exchange_id].available_balance[currency_id]

        return get_change(balance_1, balance_2, provide_abs=False) > threshold
