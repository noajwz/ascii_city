# Money

**One balance for the whole city.** `main()` owns a `Wallet` — `STARTING_MONEY`, a thousand
dollars — and everything that costs anything takes from it: the slot and the blackjack table
(which used to have their own chips), the exchange (`Broker.cash` is the wallet's), the claw
machine (`CLAW_COST` a go), the strength tester (`STRIKE_COST` a swing), the arcade
(`ARCADE_COST` a game), and the city's buildings, by `FEES`: a seat at the pictures and the club's
cover are paid on the way in, the bowl and the coffee when you sit down — once a visit, keyed on
the venue, so walking out and back in is another ticket. Can't pay, and `render_turned_away()` is
what you get instead: the usher, the bouncer, the cook's sign, the drone. The lifts cost
(`LIFT_FEES`: a sky deck, the roof party; the fire escapes and the lighthouse stair are free), a
taxi by the fare, and
a show from the lighthouse is `SHOW_FEE`; refused, the HUD says what it costs. The balance leads
the HUD everywhere. Nothing tops it up for nothing — the casino's old stake when you were broke
would have been money for nothing — but you can earn it driving a cab (see Driving it
yourself), and `+` in the menu is `+$1000`. Like everything else you carry, it is
for the session and nowhere else.
