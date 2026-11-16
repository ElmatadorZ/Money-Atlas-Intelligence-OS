Not quite. The "3%" is how far the price can move before your stop triggers. It is not how much of your money you lose. Leverage multiplies that move.

**The math**

At 20x, a 3% move in ETH is a **60% loss on your margin**, because 3% × 20 = 60%.

Example: you put up $1,000 at 20x, so your position is $20,000 of ETH.
- ETH drops 3%, which is $600 on a $20,000 position.
- Your stop hits and you lose **$600, or 60% of your margin**, plus fees.

**Other risks to know about**

1. **Liquidation is close to your stop.** At 20x, a move of roughly 5% against you liquidates you, and the exchange's maintenance margin brings that closer, often around 4–4.5%. Your stop at 3% leaves only about 1–1.5% of buffer.
2. **Stops don't always fill at your price.** ETH can wick or gap several percent in seconds, especially around news, CPI or FOMC releases, or liquidation cascades. With slippage your exit can land well past 3%. In a fast move you could be liquidated before the stop fills.
3. **Fees and funding are charged on the full $20,000**, not your $1,000. Over many trades or long holds, that adds up quickly.
4. **Tight stops get hit by normal noise.** ETH's ordinary daily range is often bigger than 3%. You may get stopped out often even when your direction was right.

**What "risking 3%" should mean**

Professionals usually mean "I lose at most X% of my *whole account* if the stop hits." Size the position from that:

> Position size = (Account × risk %) ÷ stop distance

Example: $10,000 account, risking 1% ($100), stop 3% away:
$100 ÷ 0.03 = **about $3,333 position**

That's only about 0.33x leverage on the account. You can still use 20x on the exchange to tie up less margin, but what matters is **position size**, not the leverage setting. Leverage only decides how much collateral is tied up and how close liquidation sits.

**Bottom line**

- If the $1,000 margin is your whole trading account, you're risking about 60% of it, not 3%. That isn't safe.
- If the $1,000 is a small part of a larger account and the possible $600 loss is 1–2% of that account, the setup is reasonable. Even then, use isolated margin and check the liquidation price on the order screen before you enter.

How big is your account and how much margin are you putting up? I can work out the exact size that keeps your real risk where you want it.
