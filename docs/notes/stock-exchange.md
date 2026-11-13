# The stock exchange

In the financial district only: `EXCHANGE_ODDS` of its street fronts, about two to a district —
one in 900 left some districts without one and the menu's search came back empty from one start
in 96. Low and old among the glass towers: `draw_exchange_column()` is pale stone with a column in
every bay, a cornice, and steps at the foot; `draw_exchange_front()` puts STOCK EXCHANGE over the
columns, in block letters where they fit on screen, and **the tickers cover the wall under it**
(`draw_ticker()`, from `draw_exchange_column()`, so on all four sides and behind anything in front):
rows of the market between gold rails, every other row the other way - every stock, its price, and
the last tick's move in green `^` or red `v`. One letter a column, counted from the middle of that
wall (`v.ticker_anchor`), so it reads at any distance. Block letters were tried first: a wall is one
lot wide, and two or three of them fitted and no stock's name. The columns are lit from the foot and
the pavement takes the colour of its own stock's last tick. It was asked to be more apparent. ctrl-a `e` in the checks' menu stands you on the
floor (a taxi goes there, so it is off the panel).

**The market is a function of time.** Sixteen made-up `STOCKS`, four to each of the `SECTORS`,
and `stock_price(s, t)` for each is four things added in log space: the **market's tide**
(`market()`: slow waves for the long bulls and bears, and a quick term that every stock feels on
the same tick), times the stock's own beta; its **sector's current**, slow and quick, shared with
the other three in it; its **own** swings and noise; and its **mode**. Every `EPOCH` ticks each
stock draws one of `MODES` off a hash — stable, rising, falling, hot, crash, chaotic, in Cookie
Clicker's spirit — and a mode's move rises across its epoch and fades back out across the next,
so a hot streak is followed by the air coming out of it, and only two epochs ever overlap: the
price at any moment is a closed form and nothing is stored. Chaotic is in the noise, not the
drift; the wildness eases over a couple of ticks at an epoch's start so the price does not jump.
Measured over 3000 ticks, tick moves correlate 0.23 across the market and 0.32 within a sector —
the quick shared terms are what made that so; with only slow ones it was 0.02, nothing you could
see — and hot epochs are a median x1.9, with runs of fourteen ticks up. The price you trade at
steps every `TICK_LEN` (`stock_now()`), and a `candle()` is one tick: its open and close are the
two prices, its high and low the extremes of the path between.

Inside (`render_exchange()`): the ticker along the top, the market's `mood()` and the seconds to
the next price, and then the chart — the picked stock's candles, green up, red down — or, with `l`,
the list of all sixteen: price, last move, what you hold and its worth, and `HOT!` or `SLIDE` for
a `streak()` of `STREAK` ticks one way. The arrows pick a stock in either (the list scrolls to
keep it in view); you come in on the exchange's own. `Broker` is the account, one for the night
whichever exchange you are in, its cash the one `Wallet`'s; shares held and what they
cost, profit or loss. `b` buys and `n` sells the picked stock at the current price, `+`/`-` step
the size through `LOTS` (0 is as many as you can).
