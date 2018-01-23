from profilehooks import timecall

from binance.balance_utils import get_balance_binance
from binance.buy_utils import add_buy_order_binance
from binance.constants import BINANCE_CURRENCY_PAIRS
from binance.market_utils import cancel_order_binance
from binance.ohlc_utils import get_ohlc_binance
from binance.order_book_utils import get_order_book_binance
from binance.order_utils import get_open_orders_binance
from binance.sell_utils import add_sell_order_binance
from binance.ticker_utils import get_tickers_binance
from bittrex.balance_utils import get_balance_bittrex
from bittrex.buy_utils import add_buy_order_bittrex
from bittrex.market_utils import cancel_order_bittrex
from bittrex.order_utils import get_open_orders_bittrix
from bittrex.sell_utils import add_sell_order_bittrex
from core.backtest import dummy_order_state_init
from dao.deal_utils import init_deals_with_logging_speedy
from dao.dao import get_updated_order_state
from dao.history_utils import get_history_speedup
from dao.ohlc_utils import get_ohlc_speedup, get_ohlc
from dao.order_book_utils import get_order_book_speedup
from dao.ticker_utils import get_ticker_speedup
from data.Trade import Trade
from data.TradePair import TradePair
from data.ArbitrageConfig import ArbitrageConfig
from data_access.classes.ConnectionPool import ConnectionPool
from data_access.memory_cache import generate_nonce
from enums.currency import CURRENCY
from enums.currency_pair import CURRENCY_PAIR
from enums.deal_type import DEAL_TYPE
from enums.exchange import EXCHANGE
from kraken.balance_utils import get_balance_kraken
from kraken.market_utils import cancel_order_kraken
from kraken.order_utils import get_orders_kraken, get_open_orders_kraken
from kraken.sell_utils import add_sell_order_kraken
from poloniex.balance_utils import get_balance_poloniex
from poloniex.market_utils import get_orders_history_poloniex
from poloniex.order_utils import get_open_orders_poloniex
from poloniex.buy_utils import add_buy_order_poloniex
from poloniex.sell_utils import add_sell_order_poloniex
from utils.key_utils import load_keys, get_key_by_exchange
from utils.time_utils import sleep_for, get_now_seconds_utc, get_now_seconds_local
from utils.currency_utils import get_currency_pair_name_by_exchange_id
from data_access.message_queue import get_message_queue

from dao.order_utils import get_open_orders_for_arbitrage_pair
from dao.db import save_order_into_pg, init_pg_connection, is_order_present_in_order_history, \
    is_trade_present_in_trade_history

from debug_utils import LOG_ALL_DEBUG

POLL_PERIOD_SECONDS = 900

def test_binance_ticker_retrieval():
    timest = get_now_seconds_local()
    wtf = get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
    for b in wtf:
        print wtf[b]


def test_binance_ohlc_retrieval():
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    all_ohlc = []
    for currency in BINANCE_CURRENCY_PAIRS:
        period = "15m"
        all_ohlc += get_ohlc_binance(currency, date_start, date_end, period)

    for b in all_ohlc:
        print b


def test_binance_order_book_retrieval():
    res = []
    timest = get_now_seconds_utc()
    for currency in BINANCE_CURRENCY_PAIRS:
        order_book = get_order_book_binance(currency, timest)
        if order_book is not None:
            res.append(order_book)

    for r in res:
        print r


def test_bittrex_market_api(bit_key):
    get_balance_bittrex(bit_key)
    cancel_order_bittrex(bit_key, '0e2ffb00-3509-4150-a7d2-f2b7e8c1a9e4')
    add_buy_order_bittrex(bit_key, "BTC-OMG", 0.00249870, 1)
    add_sell_order_bittrex(bit_key, "BTC-OMG", 0.0025, 1)


def test_kraken_placing_deals(krak_key):
    order_state = dummy_order_state_init()
    order_state = get_updated_order_state(order_state)

    for x in order_state[EXCHANGE.KRAKEN].open_orders:
        if x.pair_id == CURRENCY.BCC and x.volume == 0.1 and x.price == 0.5:
            cancel_order_kraken(krak_key, x.deal_id)

    order_state = get_updated_order_state(order_state)
    cnt = 0
    for x in order_state[EXCHANGE.KRAKEN].open_orders:
        if x.pair_id == CURRENCY.BCC and x.volume == 0.1 and x.price == 0.5:
            cnt += 1
            print x

    print cnt

    print order_state[EXCHANGE.KRAKEN]
    ts1 = get_now_seconds_local()
    for x in range(10000):
        # add_sell_order_kraken_till_the_end(krak_key, "BCHXBT", price=0.5, amount=0.1, order_state=order_state[EXCHANGE.KRAKEN])
        sleep_for(30)

    ts2 = get_now_seconds_local()
    order_state = get_updated_order_state(order_state)
    print "Goal was to set 10000 deals: "
    print "Total number of open orders: ", len(order_state[EXCHANGE.KRAKEN].open_orders)
    print "It take ", ts2-ts1, " seconds"


def test_kraken_market_utils(krak_key):
    res = get_orders_kraken(krak_key)

    print res.get_total_num_of_orders()

    print res

    error_code, r = get_balance_kraken(krak_key)
    print r
    pol_key = get_key_by_exchange(EXCHANGE.POLONIEX)
    r = get_balance_poloniex(pol_key)
    print r
    bit_key = get_key_by_exchange(EXCHANGE.BITTREX)
    r = get_balance_bittrex(bit_key)
    print r
    """add_buy_order_kraken_try_till_the_end(krak_key, "XETHXXBT", 0.07220, 0.02)
    add_sell_order_kraken_till_the_end(krak_key, "XETHXXBT", 0.07220, 0.02)
    add_sell_order_kraken_till_the_end(krak_key, "XETHXXBT", 0.07220, 0.02)
    """
    cancel_order_kraken(krak_key, 'O6PGMG-DXKYV-UU4MNM')


def test_binance_market_utils(bin_key):
    error_code, r = get_balance_binance(bin_key)
    print r
    error_code, r = add_buy_order_binance(bin_key, "RDNBTC", price=0.00022220, amount=10)
    print r

    error_code, r = add_sell_order_binance(bin_key, "RDNBTC", price=1.00022220, amount=1)
    error_code, r = cancel_order_binance(bin_key, "RDNBTC", 1373492)


def test_time_epoch():
    t = get_now_seconds_utc()
    t1 = get_now_seconds_local()
    t2 = generate_nonce()
    print "utc", t
    print "local", t1
    print "nonce", t2


@timecall
def get_ohlc_time_test():
    end_time = get_now_seconds_utc()
    start_time = end_time - 900

    get_ohlc(start_time, end_time)


@timecall
def get_ohlc_time_fast_test():
    processor = ConnectionPool()
    end_time = get_now_seconds_utc()
    start_time = end_time - 900
    return get_ohlc_speedup(start_time, end_time, processor)


@timecall
def get_ticker_time_fast():
    timest = get_now_seconds_utc()
    processor = ConnectionPool()
    return get_ticker_speedup(timest, processor)


@timecall
def get_history_time_fast():
    end_time = get_now_seconds_utc()
    start_time = end_time - POLL_PERIOD_SECONDS
    processor = ConnectionPool()

    trade_history = get_history_speedup(start_time, end_time, processor)
    return trade_history


@timecall
def get_order_book_time_fast():
    end_time = get_now_seconds_utc()
    start_time = end_time - POLL_PERIOD_SECONDS
    processor = ConnectionPool()

    trade_history = get_order_book_speedup(start_time, end_time, processor)
    return trade_history


def check_order_polonie(pol_key):
    er_code, res = get_orders_history_poloniex(pol_key, "all")
    print res

def check_deal_placements():
    create_time = get_now_seconds_utc()
    fake_order_book_time1 = -10
    fake_order_book_time2 = -20
    deal_volume = 5
    deal_price = -1
    pair_id = CURRENCY_PAIR.BTC_TO_ARDR

    sell_exchange_id = EXCHANGE.POLONIEX
    buy_exchange_id = EXCHANGE.BITTREX

    difference = "difference is HUGE"
    file_name = "test.log"

    processor = ConnectionPool(pool_size=2)

    trade_at_first_exchange = Trade(DEAL_TYPE.SELL, sell_exchange_id, pair_id,
                                    0.00000001, deal_volume, fake_order_book_time1,
                                    create_time)

    trade_at_second_exchange = Trade(DEAL_TYPE.BUY, buy_exchange_id, pair_id,
                                     0.00004, deal_volume, fake_order_book_time2,
                                     create_time)

    trade_pairs = TradePair(trade_at_first_exchange, trade_at_second_exchange, fake_order_book_time1, fake_order_book_time2, DEAL_TYPE.DEBUG)

    init_deals_with_logging_speedy(trade_pairs, difference, file_name, processor)


def check_open_order_retrieval():
    load_keys("./secret_keys")
    krak_key = get_key_by_exchange(EXCHANGE.KRAKEN)
    bin_key = get_key_by_exchange(EXCHANGE.BINANCE)
    pol_key = get_key_by_exchange(EXCHANGE.POLONIEX)
    bittrex_key = get_key_by_exchange(EXCHANGE.BITTREX)

    err_code, res = get_open_orders_binance(bin_key, "XMRBTC")
    for r in res:
        print r

    err_code, res = get_open_orders_bittrix(bittrex_key, None)
    for r in res:
        print r

    err_code, res = get_open_orders_kraken(krak_key, None)
    for r in res:
        print r

    err_code, res = get_open_orders_poloniex(pol_key, "BTC_ARDR")
    for r in res:
        print r


def test_kraken_buy_sell_utils():
    load_keys("./secret_keys")
    krak_key = get_key_by_exchange(EXCHANGE.KRAKEN)
    # pair_name, price, amount
    err_code, res = add_sell_order_kraken(krak_key, "XXMRXXBT", price=0.045, amount=10.0)
    print res


def test_open_orders_retrieval_arbitrage():

    sell_exchange_id = EXCHANGE.BINANCE
    buy_exchange_id = EXCHANGE.POLONIEX
    pair_id = CURRENCY_PAIR.BTC_TO_OMG
    threshold = 2.0
    reverse_threshold = 2.0
    deal_expire_timeout = 60
    logging_level = LOG_ALL_DEBUG

    cfg = ArbitrageConfig(sell_exchange_id, buy_exchange_id,
                          pair_id, threshold,
                          reverse_threshold, deal_expire_timeout,
                          logging_level)
    load_keys("./secret_keys")
    msg_queue1 = get_message_queue()
    processor = ConnectionPool(pool_size=2)
    print cfg
    res = get_open_orders_for_arbitrage_pair(cfg, processor)
    print "Length:", len(res)
    for r in res:
        print r


def test_insert_order():
    from enums.exchange import EXCHANGE
    from enums.deal_type import DEAL_TYPE
    from enums.currency_pair import CURRENCY_PAIR
    wtf = Trade(DEAL_TYPE.SELL, EXCHANGE.POLONIEX, CURRENCY_PAIR.BTC_TO_ARDR, 0.00001, 10.4, 1516039961, 1516039961)
    pg_conn = init_pg_connection(_db_host="192.168.1.106", _db_port=5432, _db_name="postgres")
    save_order_into_pg(wtf, pg_conn)


def test_binance_xlm():
    load_keys("./secret_keys")
    key = get_key_by_exchange(EXCHANGE.BINANCE)
    pair_id = CURRENCY_PAIR.BTC_TO_XLM
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, EXCHANGE.BINANCE)
    err, json_repr = add_buy_order_binance(key, pair_name, price=0.00003000, amount=100)
    print json_repr


def test_poloniex_doge():
    load_keys("./secret_keys")
    key = get_key_by_exchange(EXCHANGE.POLONIEX)
    pair_id = CURRENCY_PAIR.BTC_TO_DGB
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, EXCHANGE.POLONIEX)
    err, json_repr = add_buy_order_poloniex(key, pair_name, price=0.00000300, amount=100)
    print json_repr


def test_new_sell_api():
    # STRAT vol 10 sell 0.0015 buy 0.0007

    load_keys("./secret_keys")
    key = get_key_by_exchange(EXCHANGE.POLONIEX)
    pair_id = CURRENCY_PAIR.BTC_TO_STRAT
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, EXCHANGE.POLONIEX)
    err, json_repr = add_buy_order_poloniex(key, pair_name, price=0.0007, amount=10)
    print json_repr
    err, json_repr = add_sell_order_poloniex(key, pair_name, price=0.0015, amount=10)
    print json_repr

    key = get_key_by_exchange(EXCHANGE.BITTREX)
    pair_id = CURRENCY_PAIR.BTC_TO_STRAT
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, EXCHANGE.BITTREX)
    err, json_repr = add_buy_order_bittrex(key, pair_name, price=0.0007, amount=10)
    print json_repr
    err, json_repr = add_sell_order_bittrex(key, pair_name, price=0.0015, amount=10)
    print json_repr


def test_poloniex_trade_history():
    from poloniex.market_utils import get_order_history_for_time_interval_poloniex
    load_keys("./secret_keys")
    key = get_key_by_exchange(EXCHANGE.POLONIEX)
    pair_id = CURRENCY_PAIR.BTC_TO_OMG
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, EXCHANGE.POLONIEX)
    time_end = get_now_seconds_utc()
    time_start = time_end - 24 * 3600

    limit = 100
    get_order_history_for_time_interval_poloniex(key, pair_name, time_start, time_end, limit)


def test_order_presence():
    pg_conn = init_pg_connection(_db_host="192.168.1.106", _db_port=5432)
    # 6479142
    ts = get_now_seconds_utc()
    some_trade = Trade(DEAL_TYPE.BUY, EXCHANGE.BINANCE, CURRENCY_PAIR.BTC_TO_STRAT, price=0.001184, volume=2.08,
                       order_book_time=ts, create_time=ts, execute_time=ts, deal_id='whatever')

    res = is_order_present_in_order_history(pg_conn, some_trade, table_name="tmp_binance_orders")

    print res


def test_trade_present():
    pg_conn = init_pg_connection(_db_host="192.168.1.106", _db_port=5432)
    # 6479142
    ts = 1516142509
    trade = Trade(DEAL_TYPE.BUY, EXCHANGE.BINANCE, CURRENCY_PAIR.BTC_TO_STRAT, price=0.001184, volume=2.08,
                       order_book_time=ts, create_time=ts, execute_time=ts, deal_id='whatever')

    res = is_trade_present_in_trade_history(pg_conn, trade, table_name="tmp_history_trades")

    print res


test_trade_present()