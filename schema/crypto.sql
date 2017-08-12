--
-- refactor schema data etc
--

CREATE TABLE public.candle
(
    id integer DEFAULT nextval('candle_id_seq'::regclass) PRIMARY KEY NOT NULL,
    pair_id integer NOT NULL,
    exchange_id integer NOT NULL,
    open double precision,
    close double precision,
    high double precision,
    low double precision,
    timest bigint,
    date_time timestamp,
    CONSTRAINT candle_pair_id_fk FOREIGN KEY (pair_id) REFERENCES pair (id),
    CONSTRAINT candle_exchange_id_fk FOREIGN KEY (exchange_id) REFERENCES exchange (id)
);
CREATE UNIQUE INDEX candle_id_uindex ON public.candle (id);

CREATE TABLE public.deal_type
(
    id integer DEFAULT nextval('deal_type_id_seq'::regclass) PRIMARY KEY NOT NULL,
    name varchar NOT NULL
);
INSERT INTO public.deal_type (id, name) VALUES (1, 'sell');
INSERT INTO public.deal_type (id, name) VALUES (2, 'buy');

CREATE TABLE public.exchange
(
    id integer DEFAULT nextval('exchange_id_seq'::regclass) PRIMARY KEY NOT NULL,
    name varchar
);
CREATE UNIQUE INDEX exchange_id_uindex ON public.exchange (id);
INSERT INTO public.exchange (id, name) VALUES (1, 'poloniex');
INSERT INTO public.exchange (id, name) VALUES (2, 'kraken');
INSERT INTO public.exchange (id, name) VALUES (3, 'bittrex');

CREATE TABLE public.order_book
(
    id integer DEFAULT nextval('order_book_id_seq'::regclass) PRIMARY KEY NOT NULL,
    pair_id integer NOT NULL,
    exchange_id integer NOT NULL,
    timest bigint,
    date_time timestamp,
    CONSTRAINT order_book_pair_id_fk FOREIGN KEY (pair_id) REFERENCES pair (id),
    CONSTRAINT order_book_exchange_id_fk FOREIGN KEY (exchange_id) REFERENCES exchange (id)
);
CREATE UNIQUE INDEX order_book_id_uindex ON public.order_book (id);

CREATE TABLE public.order_book_ask
(
    id integer DEFAULT nextval('order_book_ask_id_seq'::regclass) PRIMARY KEY NOT NULL,
    order_book_id integer,
    price double precision,
    volume double precision,
    CONSTRAINT order_book_ask_order_book_id_fk FOREIGN KEY (order_book_id) REFERENCES order_book (id)
);
CREATE UNIQUE INDEX order_book_ask_id_uindex ON public.order_book_ask (id);

CREATE TABLE public.order_book_bid
(
    id integer DEFAULT nextval('order_book_bid_id_seq'::regclass) PRIMARY KEY NOT NULL,
    order_book_id integer,
    price double precision,
    volume double precision,
    CONSTRAINT order_book_bid_order_book_id_fk FOREIGN KEY (order_book_id) REFERENCES order_book (id)
);
CREATE UNIQUE INDEX order_book_bid_id_uindex ON public.order_book_bid (id);

CREATE TABLE public.order_history
(
    id integer DEFAULT nextval('order_history_id_seq'::regclass) PRIMARY KEY NOT NULL,
    pair_id integer NOT NULL,
    exchange_id integer NOT NULL,
    deal_type integer,
    price double precision NOT NULL,
    amount double precision,
    total double precision,
    timest bigint,
    date_time timestamp,
    CONSTRAINT order_history_pair_id___fk FOREIGN KEY (pair_id) REFERENCES pair (id),
    CONSTRAINT order_history_exchange_id__fk FOREIGN KEY (exchange_id) REFERENCES exchange (id),
    CONSTRAINT order_history_deal_type_id_fk FOREIGN KEY (deal_type) REFERENCES deal_type (id)
);
CREATE UNIQUE INDEX order_history_id_uindex ON public.order_history (id);

CREATE TABLE public.pair
(
    id integer DEFAULT nextval('pair_id_seq'::regclass) PRIMARY KEY NOT NULL,
    pair varchar NOT NULL
);
INSERT INTO public.pair (id, pair) VALUES (1, 'BTC_TO_DASH');
INSERT INTO public.pair (id, pair) VALUES (2, 'BTC_TO_ETH');
INSERT INTO public.pair (id, pair) VALUES (3, 'BTC_TO_LTC');
INSERT INTO public.pair (id, pair) VALUES (4, 'BTC_TO_XRP');
INSERT INTO public.pair (id, pair) VALUES (5, 'BTC_TO_BCC');
INSERT INTO public.pair (id, pair) VALUES (6, 'BTC_TO_ETC');
INSERT INTO public.pair (id, pair) VALUES (7, 'BTC_TO_SC');
INSERT INTO public.pair (id, pair) VALUES (8, 'BTC_TO_DGB');
INSERT INTO public.pair (id, pair) VALUES (9, 'BTC_TO_XEM');
INSERT INTO public.pair (id, pair) VALUES (10, 'BTC_TO_ARDR');


CREATE TABLE public.tickers
(
    id integer DEFAULT nextval('tickers_id_seq'::regclass) PRIMARY KEY NOT NULL,
    exchange_id integer NOT NULL,
    pair_id integer NOT NULL,
    lowest_ask double precision NOT NULL,
    highest_bid double precision NOT NULL,
    timest bigint NOT NULL,
    date_time timestamp,
    CONSTRAINT exchange_id_fk FOREIGN KEY (exchange_id) REFERENCES exchange (id),
    CONSTRAINT pair_id___fk FOREIGN KEY (pair_id) REFERENCES pair (id)
);
CREATE UNIQUE INDEX tickers_id_uindex ON public.tickers (id);