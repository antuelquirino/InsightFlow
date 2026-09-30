# Data stories

InsightFlow's synthetic data is not random noise. It is generated to hide five
business stories that the dashboard and the AI agent should be able to surface.
This document is the contract for the generator: any change to
`data_generation/` must keep these stories visible, and `tests/test_stories.py`
checks each one.

All figures below come from the published dataset:

```
python -m data_generation.build --seed 42 --end-month 2026-08
```

The window runs from **September 2024 to August 2026** (24 months). Other
seeds or end months tell the same stories with different numbers (see
[Robustness](#robustness)).

## Definitions

These are the definitions the tests use and the dbt marts implement.

| Term | Definition |
|---|---|
| Subscription period | A row in `raw.subscriptions`, covering `[start_date, end_date)`. A plan, seat or price change closes one period and opens the next on the same day. |
| Paying customer | An organization with an open non-trial period on a given day. |
| MRR | Sum of `mrr` (`seats × monthly_price_per_seat`) of the periods active on the last day of the month. |
| Logo churn rate | Customers paying at the previous month end who pay nothing at this month end ÷ customers paying at the previous month end. By plan or channel, each customer counts under the plan it had at the previous month end, so an upgrade is not a churn. |
| NRR (12 months) | Current MRR of the customers who were paying 12 months ago ÷ their MRR back then. Includes churn, contraction, expansion and plan changes. |
| Early churn | Share of customers who churn within 6 months of their first paid day, counting only customers with at least 6 months of history in the window. |

The company launches with the window: September 2024 has 9 paying customers,
so the first months show very high growth rates and noisy churn on a tiny base.

## 1. The Starter price increase

**What happens.** On **15 November 2025** (mid-month 15), Starter goes from
$15 to $19 per seat, for new and existing customers alike. Starter customers
react: logo churn more than doubles for the three following months and then
returns to its usual level. Pro and Enterprise are unaffected.

| Starter logo churn | Monthly average |
|---|---|
| May–Oct 2025 (before) | 3.98% |
| Dec 2025–Feb 2026 (after) | 9.18% (2.3×) |
| Mar–Aug 2026 (settled) | 4.49% |

Pro and Enterprise churn does not rise over the same months (1.5% before, 0.6% after).

**Where it shows.**
- `raw.plans`: two Starter rows, split at 2025-11-15.
- `raw.subscriptions`: existing Starter periods end with `end_reason = 'price_changed'`
  on 2025-11-15, followed by a spike of `churned` Starter periods.
- `fct_churn` by plan; the price change itself appears as **expansion** in
  `fct_mrr_movements` for November 2025, since the same customers pay more.

**Question that reveals it:** *"What happened to Starter churn after the price
change?"*

**Levers** (`data_generation/config.py`): `STARTER_PRICE_CHANGE_MONTH`,
`STARTER_NEW_PRICE`, `PRICE_CHANGE_CHURN_MULTIPLIER`, `PRICE_CHANGE_EFFECT_MONTHS`.

**Tests:** Starter churn after ≥ 1.7× before; the settled level is below 75% of
the spike; the other plans' increase is less than half of Starter's.

## 2. Paid ads bring customers who leave fast

**What happens.** Customers acquired through paid ads churn about twice as often
in their first six months as organic ones. After six months the gap mostly
closes: the ones who stay behave like everyone else.

| Channel | Early churn (first 6 months) |
|---|---|
| Paid ads | 35.2% |
| Organic | 14.9% |
| Partner | 13.7% |
| Outbound | 7.2% |

Paid ads is also the channel that grows the most: its share of new trials goes
from 24% to 40% over the window, and it has the most marketing spend. The unit
economics make it the weakest channel by far (August 2026, trailing 12 months,
80% gross margin):

| Channel | CAC | Monthly logo churn | LTV | LTV:CAC | Payback |
|---|---|---|---|---|---|
| Paid ads | $2,339 | 6.2% | $5,839 | 2.5 | 6.4 months |
| Partner | $907 | 2.8% | $14,214 | 15.7 | 2.3 months |
| Outbound | $1,922 | 2.3% | $36,992 | 19.2 | 2.3 months |
| Organic | $855 | 2.9% | $18,411 | 21.5 | 1.6 months |

**Where it shows.** `raw.organizations.acquisition_channel` joined to churned
periods; `fct_churn` by channel; `fct_unit_economics` (LTV and payback by
channel); `fct_retention_cohorts`.

**Question that reveals it:** *"Which acquisition channel has the highest churn
rate, and how do the unit economics compare?"* The marts hold monthly churn by
channel (paid ads 6.2% a month over the last 12 months, organic 2.9%) rather
than churn by customer age, so the first-six-months effect itself is visible in
the raw data and the tests, and in the marts as higher churn and weaker unit
economics for paid ads.

**Levers:** `PAID_ADS_EARLY_CHURN_MULTIPLIER`, `PAID_ADS_EARLY_MONTHS`,
`CHANNEL_MIX_START`, `CHANNEL_MIX_END`, `SPEND_START`, `SPEND_END`.

**Tests:** paid ads early churn is 1.6× to 3× organic; after six months the
ratio drops below 1.6×.

## 3. Enterprise expansion lifts NRR above 100%

**What happens.** Enterprise customers keep adding seats (small, frequent
increases), and rarely leave. That expansion outweighs the logos lost in the
smaller plans, so revenue from last year's customers grows even though a
quarter of them are gone.

| Customers paying in August 2025 | NRR 12m | Logos retained |
|---|---|---|
| All | 124% | 74% |
| Enterprise | 132% | 95% |
| Starter and Pro | 104% | 70% |

The average Enterprise customer went from 26.5 to 29.6 seats over that year.
In August 2026 Enterprise is 97 of 458 paying customers but 76% of the MRR.

**Where it shows.** `raw.subscriptions` (Enterprise periods ending in
`seats_changed` with more seats in the next period); `fct_mrr_movements`
(expansion); `fct_retention_cohorts` (revenue retention above logo retention);
`kpi_summary` (NRR).

**Question that reveals it:** *"Why is net revenue retention above 100% if we are
losing customers?"*

**Levers:** `EXPANSION["enterprise"]`, `CHURN_BASE["enterprise"]`, `PLAN_MIX_BY_SIZE`.

**Tests:** overall NRR above 100% with logo retention below 90%; Enterprise NRR
above 105% and at least 5 points above the other plans; Enterprise seats added
are more than 3× the seats removed.

## 4. Usage decline anticipates churn

**What happens.** Every customer who churns fades out first: weekly activity
starts falling 6 to 10 weeks before the cancellation and ends at about a third
of its usual level.

| Weeks before churn | 13 | 10 | 8 | 6 | 4 | 2 | 0 |
|---|---|---|---|---|---|---|---|
| Active users (index, weeks 11–15 = 100) | 104 | 100 | 95 | 83 | 67 | 50 | 33 |

Because the simulation runs three months past the window, customers who will
churn right after August 2026 are already fading inside it. `dim_organizations`
flags paying customers by `usage_trend` (last 4 weeks ÷ the 8 weeks before),
and the flag works: in the simulated months after the window,

| Churn risk | Paying customers | Churn within the next 3 months |
|---|---|---|
| High (trend below 0.6) | 14 | 6 (43%) |
| Medium (0.6 to 0.8) | 41 | 6 (15%) |
| Low (0.8 or more) | 385 | 21 (5%) |
| Unknown (too new) | 18 | 2 (11%) |

Most churns two or three months out still look healthy in August: the fade
starts only 6 to 10 weeks before. Healthy customers also have occasional
one-week dips and a Christmas dip, so a single bad week is not a signal.

**Where it shows.** `raw.product_events` (weekly `active_users`, `logins`,
`dashboards_viewed`, `queries_run`, `reports_exported` per organization);
the intermediate weekly activity model; `dim_organizations` (usage trend and
risk flag).

**Question that reveals it:** *"Which customers are at risk of churning?"* or
*"How does activity change before a customer cancels?"*

**Levers:** `PRE_CHURN_DECLINE_WEEKS`, `PRE_CHURN_FLOOR`, `HEALTHY_DIP_RATE`,
`HOLIDAY_WEEKS`.

**Tests:** activity in the last two weeks is below half of the baseline and
already below 85% a month earlier; the baseline is flat; between 2% and 20% of
current customers are fading.

## 5. Seasonality of new signups

**What happens.** Fewer companies start trials in December and January; March
is the peak of the year.

| New trials | Oct | Nov | Dec | Jan | Feb | Mar | Apr |
|---|---|---|---|---|---|---|---|
| 2024–25 | 37 | 32 | 28 | 37 | 41 | 69 | 50 |
| 2025–26 | 56 | 51 | 35 | 29 | 49 | 96 | 71 |

**Where it shows.** `raw.organizations.signup_date`; new MRR in
`fct_mrr_movements`; new customers in `kpi_summary`.

**Question that reveals it:** *"In which months do we sign up the most new
customers?"*

**Levers:** `SEASONALITY`.

**Tests:** March beats the average of February and April by at least 15% in
both years; December and January average below 80% of the two months on each
side.

## Background trends

Besides the stories, the data has the texture of a real SaaS business:

- **Growth that slows down.** MRR goes from $2k in September 2024 to $297k in
  August 2026 (ARR $3.6M); monthly growth averages 19% from March to August
  2025, 10% over the next six months and 6% over the last six. New trials ramp
  up and then plateau.
- **Trials.** 14 days; 53% convert, from 45% for paid ads to 66% for partners.
- **Plan changes.** Upgrades (Starter → Pro → Enterprise), downgrades and seat
  contractions happen every month in small numbers.
- **Reactivations.** 19 of the 179 customers who churned came back within a year.
- **Failed payments.** 3.6% of invoices fail and 0.9% are refunded; Starter
  fails most often.

**Tests:** MRR grows and its growth rate in the last six months is below 60% of
months 6–12; reactivations exist and stay below 20% of churned customers.

## Robustness

The story tests run on seed 42. To check that the stories come from the
mechanisms and not from a lucky seed, the same tests were run on seeds 1–20:
11 of 260 test runs failed, always near a threshold. With about 500 customers,
effects on small groups (Enterprise NRR, organic early churn) move by several
points from seed to seed. When changing a lever, run the story tests on a few
seeds before trusting a result.
