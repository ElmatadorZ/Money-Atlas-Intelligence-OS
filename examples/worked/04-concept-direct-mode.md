# Worked example — DIRECT mode

**User:** What happens to bond prices when yields rise?

A concept question with one settled answer. The frameworks still run — they are how
the answer is checked — but the reader gets the answer, not the framework.

---

**Output:**

> **They fall.** A bond's coupon is fixed, so when new bonds pay a higher yield, an
> existing bond is only worth buying at a lower price — low enough that its fixed
> payments give the new, higher return. Price is the present value of future cash
> flows, and a higher discount rate lowers it.
>
> How much it falls depends mostly on **duration**: roughly, % price change ≈
> −duration × change in yield. A bond with a duration of 8 loses about 8% if yields
> rise one percentage point. Longer maturities and lower coupons move more.
>
> Why it matters: a bond you hold to maturity still repays par if the issuer does not
> default; a bond fund has no maturity, so it recovers through higher reinvested income.

---

**Why it is shaped this way**

- No banners, scenarios or confidence field: it is an identity, stated as fact.
- One rule of thumb (duration) because it is what a reader can use next.
- In v2.0 this answer came out as a full market framework with "~95% confidence";
  blind graders scored that 0 for proportion and marked the confidence as under-firm
  (`evals/2026-11-16/`).
