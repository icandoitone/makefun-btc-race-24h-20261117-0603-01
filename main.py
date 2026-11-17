"""Deep-dip mean-reversion bot for cbBTC on the agent-fun/bars-replay/v1 protocol.

Strategy (tuned on this competition's frozen dev window of 1,440 one-minute
bars of cbBTC/USDC, where it made about +$26.6 net on $1,000 after all fees,
with 6 trades and 0.72% maximum drawdown):

  - Track the simple moving average of the last 90 closes (SMA-90).
  - When flat and the latest close sits at least 78 bps below the SMA-90,
    buy with all available cash. A dip that deep is a stretched rubber band:
    on the dev window the price reverted toward the mean within a few hours.
  - When holding, sell the whole position as soon as the close recovers to
    at least 65 bps above the SMA-90.
  - Insurance exits that never fired on the dev window but cap the damage
    if the race window behaves differently: a stop-loss 150 bps below the
    fill price, and a 480-bar (8-hour) maximum hold.

Why this shape: the dev window is choppy and roughly flat (+0.5% over 24h)
with 1-minute returns that barely persist, so momentum and EMA-cross rules
all lost money there, while patient dip-buying won. A full-size round trip
pays roughly 30-40 bps in fees, slippage and pool impact at this pool's
depth, so only deep dips clear the cost hurdle; shallow dips and trailing
exits were tested and both lost money. The chosen parameters sit in the
middle of a broad profitable plateau (SMA 85-95, dip 75-80 bps, exit
60-70 bps all made +$21 to +$28), and the rule stayed profitable in both
halves of the dev window and at double fees.

Determinism: every comparison is exact integer arithmetic on the bar
closes (no floats, no clock, no randomness, no network, no files). Two
runs on the same data produce byte-identical replies.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SMA_BARS = 90          # length of the mean the price reverts to
DIP_BPS = 78           # buy when close is this far below the SMA (bps)
EXIT_BPS = 65          # sell when close is this far above the SMA (bps)
STOP_BPS = 150         # insurance stop below the fill price (bps)
MAX_HOLD_BARS = 480    # insurance maximum hold (bars)
MAX_SLIPPAGE_BPS = 1000  # 10%: far above any 1-minute move, just a sanity cap


class DipReversionBot:
    """Keeps the close history and the open position's entry price."""

    def __init__(self):
        self.closes = []
        self.window_sum = 0
        self.entry_px = None   # fill price of the open position, else None
        self.hold_bars = 0

    def _entry_price(self, state):
        """Fill price of the open position, for the stop-loss.

        Normally the price of the buy fill that opened it (recorded from
        the batch fills). If that was ever missed, fall back to the
        position's average cost, which the account reports.
        """
        if self.entry_px is not None:
            return self.entry_px
        holding = state.positions.get(SYMBOL)
        if holding is None or holding.qty == 0:
            return None
        scales = state.hello["symbols"][0]
        quote_scale = state.hello["capital"]["quote_scale"]
        return (holding.cost * 10 ** (scales["qty_scale"] + scales["price_scale"])
                // (holding.qty * 10 ** quote_scale))

    def _should_exit(self, state, close, sma):
        """True when a held position should be sold, and why."""
        if (close - sma) * 10000 >= EXIT_BPS * sma:
            return "recovered above the mean"
        entry_px = self._entry_price(state)
        if (entry_px is not None
                and (entry_px - close) * 10000 >= STOP_BPS * entry_px):
            return "stop-loss below the entry"
        if self.hold_bars >= MAX_HOLD_BARS:
            return "maximum hold reached"
        return None

    def on_batch(self, state, batch):
        # Learn what actually filled from the previous reply: the entry
        # price is the fill price, and a filled sell clears the position.
        for fill in batch.get("fills", []):
            if fill.get("symbol") != SYMBOL or fill.get("status") != "filled":
                continue
            if fill.get("side") == "buy":
                self.entry_px = int(fill["price"])
                self.hold_bars = 0
            elif fill.get("side") == "sell":
                self.entry_px = None
                self.hold_bars = 0

        bars = [b for b in batch.get("bars", []) if b.get("symbol") == SYMBOL]
        if not bars or state.warming_up:
            return None
        close = int(bars[-1]["c"])
        self.closes.append(close)
        self.window_sum += close
        if len(self.closes) > SMA_BARS:
            self.window_sum -= self.closes[-SMA_BARS - 1]

        holding = state.positions.get(SYMBOL)
        holding = holding is not None and holding.qty > 0
        if holding:
            self.hold_bars += 1

        if len(self.closes) < SMA_BARS:
            return None
        sma = self.window_sum // SMA_BARS

        if not holding:
            # Deep dip below the mean: buy with all cash.
            if (sma - close) * 10000 >= DIP_BPS * sma:
                notional = state.cash
                if notional >= 1_000_000:
                    return [{"side": "buy", "symbol": SYMBOL,
                             "notional_quote_units": notional,
                             "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return None

        # Holding: sell on recovery above the mean, on the stop, or on age.
        if self._should_exit(state, close, sma) is None:
            return None
        qty = state.positions[SYMBOL].qty
        return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]


def main():
    bot = DipReversionBot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
