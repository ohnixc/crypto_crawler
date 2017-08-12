from constants import BITTREX_GET_OHLC
import requests
from data.Candle import Candle
from daemon import should_print_debug


def get_ohlc_bittrex(currency, date_end, date_start, period):
    result_set = []
    # https://bittrex.com/Api/v2.0/pub/market/GetTicks?tickInterval=oneMin&marketName=BTC-ETH&_=timest

    final_url = BITTREX_GET_OHLC + period + "&marketName=" + currency + "&_=" + str(date_start)

    if should_print_debug():
        print final_url

    try:
        r = requests.get(final_url).json()

        if "result" in r:
            # result":[{"O":0.08184725,"H":0.08184725,"L":0.08181559,"C":0.08181559,"V":9.56201864,"T":"2017-07-21T17:26:00","BV":0.78232812},
            # {"O":0.08181559,"H":0.08184725,"L":0.08181559,"C":0.08184725,"V":3.28483907,"T":"2017-07-21T17:27:00","BV":0.26876032}
            for record in r["result"]:
                result_set.append(Candle.from_bittrex(record, currency))
    except Exception, e:
        print "get_ohlc_bittrex: ", currency, date_start, str(e)

    return result_set
