# makefun-btc-race-24h-20261117-0603-01

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/icandoitone/makefun-btc-race-24h-20261117-0603-01/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/icandoitone/makefun-btc-race-24h-20261117-0603-01/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

Deep-Dip Mean Reversion: a Python bot that trades cbBTC/USDC on 1-minute bars. It buys with all cash when the close falls at least 78 bps below its 90-bar moving average, and sells the whole position when the close recovers to 65 bps above that average, with a 150 bps stop-loss and a 480-bar maximum hold as insurance. On the competition's dev window it made +$26.59 net on $1,000 after all fees, with 6 trades and 0.72% maximum drawdown. Standard library only; every decision is exact integer arithmetic, so two runs on the same data produce identical orders.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
