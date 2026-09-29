"""Customer lifecycle simulation.

Month by month: existing customers may churn, change plan or seats, or come
back after churning; then new organizations sign up for a 14-day trial that
either converts or expires. The result is a list of organizations, each with
its chain of subscription periods. A period covers [start_date, end_date):
the next period of the same organization starts on the day the previous ends.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
from faker import Faker

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.dates import add_months, month_end, months_between


@dataclass
class Period:
    organization_id: str
    plan_id: str
    seats: int
    monthly_price_per_seat: float
    is_trial: bool
    start_date: date
    end_date: date | None = None
    end_reason: str | None = None
    subscription_id: str = ""  # assigned once the simulation is over

    @property
    def mrr(self) -> float:
        return 0.0 if self.is_trial else round(self.seats * self.monthly_price_per_seat, 2)

    def is_active_on(self, d: date) -> bool:
        return self.start_date <= d and (self.end_date is None or d < self.end_date)


@dataclass
class Organization:
    organization_id: str
    name: str
    industry: str
    country: str
    company_size: str
    acquisition_channel: str
    signup_date: date
    periods: list[Period] = field(default_factory=list)

    @property
    def open_period(self) -> Period | None:
        last = self.periods[-1]
        return last if last.end_date is None else None

    @property
    def first_paid_start(self) -> date | None:
        return next((p.start_date for p in self.periods if not p.is_trial), None)

    @property
    def churned_on(self) -> date | None:
        last = self.periods[-1]
        return last.end_date if last.end_reason == "churned" else None


def simulate(cfg: BuildConfig) -> list[Organization]:
    organizations = _Simulator(cfg).run()
    _assign_subscription_ids(organizations)
    return organizations


def _assign_subscription_ids(organizations: list[Organization]) -> None:
    # Chronological ids, so the rows emitted for the window never leave gaps.
    periods = [p for org in organizations for p in org.periods]
    # Trials first on a tie: a trial and a subscription never start on the same day
    # for one organization, but keep the order explicit anyway.
    periods.sort(key=lambda p: (p.start_date, p.organization_id, not p.is_trial))
    for i, period in enumerate(periods, start=1):
        period.subscription_id = f"sub_{i:06d}"


class _Simulator:
    def __init__(self, cfg: BuildConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng([cfg.seed, 0])
        self.fake = Faker()
        self.fake.seed_instance(cfg.seed)
        self.orgs: list[Organization] = []

    def run(self) -> list[Organization]:
        month, index = self.cfg.start_month, 0
        while month <= self.cfg.sim_end_month:
            if month == self.cfg.price_change_date.replace(day=1):
                self._apply_price_change()
            self._evolve_customers(month)
            self._acquire(month, index)
            month, index = add_months(month, 1), index + 1
        return self.orgs

    # --- prices and periods ---------------------------------------------------

    def _price_on(self, plan_id: str, d: date) -> float:
        if plan_id == "starter" and d >= self.cfg.price_change_date:
            return C.STARTER_NEW_PRICE
        return C.PLANS[plan_id]["price"]

    def _open(self, org: Organization, plan_id: str, seats: int, start: date, is_trial=False) -> Period:
        period = Period(
            organization_id=org.organization_id,
            plan_id=plan_id,
            seats=seats,
            monthly_price_per_seat=self._price_on(plan_id, start),
            is_trial=is_trial,
            start_date=start,
        )
        org.periods.append(period)
        return period

    def _switch(self, org: Organization, day: date, reason: str, plan_id: str, seats: int) -> None:
        current = org.open_period
        current.end_date, current.end_reason = day, reason
        self._open(org, plan_id, seats, day)

    def _apply_price_change(self) -> None:
        # Existing Starter customers move to the new price on the change date.
        change = self.cfg.price_change_date
        for org in self.orgs:
            current = org.open_period
            if current and current.plan_id == "starter" and current.start_date < change:
                self._switch(org, change, "price_changed", "starter", current.seats)

    # --- existing customers ---------------------------------------------------

    def _evolve_customers(self, month: date) -> None:
        for org in self.orgs:
            current = org.open_period
            if current is None:
                if org.churned_on:
                    self._maybe_reactivate(org, month)
                continue
            # A uniform day in the month; days before the period started mean no
            # event this month, which scales exposure for periods starting mid-month.
            day = self._random_day(month)
            if day <= current.start_date:
                continue
            if self.rng.random() < self._churn_probability(org, current, day):
                current.end_date, current.end_reason = day, "churned"
            else:
                self._maybe_change(org, current, day)

    def _churn_probability(self, org: Organization, current: Period, day: date) -> float:
        plan, channel = current.plan_id, org.acquisition_channel
        multiplier = C.CHANNEL_CHURN_MULTIPLIER[channel]
        early = day < add_months(org.first_paid_start, C.PAID_ADS_EARLY_MONTHS)
        if channel == "paid_ads" and early:
            multiplier = C.PAID_ADS_EARLY_CHURN_MULTIPLIER
        change = self.cfg.price_change_date
        effect_end = add_months(change.replace(day=1), 1 + C.PRICE_CHANGE_EFFECT_MONTHS)
        if plan == "starter" and change <= day < effect_end:
            multiplier *= C.PRICE_CHANGE_CHURN_MULTIPLIER
        return C.CHURN_BASE[plan] * multiplier

    def _maybe_change(self, org: Organization, current: Period, day: date) -> None:
        plan, seats = current.plan_id, current.seats
        plan_index = C.PLAN_ORDER.index(plan)
        options = [
            ("upgraded", C.UPGRADE.get(plan, 0.0)),
            ("downgraded", C.DOWNGRADE.get(plan, 0.0)),
            ("expansion", C.EXPANSION[plan][0]),
            ("contraction", C.CONTRACTION[plan][0]),
        ]
        u, cumulative = self.rng.random(), 0.0
        for kind, probability in options:
            cumulative += probability
            if u >= cumulative:
                continue
            if kind == "upgraded":
                new_plan = C.PLAN_ORDER[plan_index + 1]
                self._switch(org, day, kind, new_plan, max(seats, C.PLANS[new_plan]["min_seats"]))
            elif kind == "downgraded":
                new_plan = C.PLAN_ORDER[plan_index - 1]
                self._switch(org, day, kind, new_plan, min(seats, C.SEATS_BY_PLAN[new_plan][2]))
            elif kind == "expansion":
                _, low, high = C.EXPANSION[plan]
                added = max(1, round(seats * self.rng.uniform(low, high)))
                self._switch(org, day, "seats_changed", plan, seats + added)
            else:
                _, low, high = C.CONTRACTION[plan]
                removed = max(1, round(seats * self.rng.uniform(low, high)))
                new_seats = max(C.PLANS[plan]["min_seats"], seats - removed)
                if new_seats != seats:
                    self._switch(org, day, "seats_changed", plan, new_seats)
            return

    def _maybe_reactivate(self, org: Organization, month: date) -> None:
        churned_on = org.churned_on
        if not 1 <= months_between(churned_on, month) <= C.REACTIVATION_WINDOW_MONTHS:
            return
        if self.rng.random() >= C.REACTIVATION_RATE:
            return
        day = self._random_day(month)
        if day <= churned_on:
            return
        last = org.periods[-1]
        self._open(org, last.plan_id, last.seats, day)

    # --- new organizations ----------------------------------------------------

    def _acquire(self, month: date, index: int) -> None:
        ramp = 1 - math.exp(-index / C.SIGNUPS_RAMP_MONTHS)
        expected = (C.SIGNUPS_BASE + C.SIGNUPS_GROWTH * ramp) * C.SEASONALITY[month.month]
        progress = min(index / (C.HISTORY_MONTHS - 1), 1.0)
        mix = np.array(C.CHANNEL_MIX_START) + progress * (
            np.array(C.CHANNEL_MIX_END) - np.array(C.CHANNEL_MIX_START)
        )
        mix /= mix.sum()

        signup_days = sorted(self._random_day(month) for _ in range(self.rng.poisson(expected)))
        for signup in signup_days:
            channel = C.CHANNELS[self.rng.choice(len(C.CHANNELS), p=mix)]
            size = C.COMPANY_SIZES[self.rng.choice(3, p=C.SIZE_MIX_BY_CHANNEL[channel])]
            plan = C.PLAN_ORDER[self.rng.choice(3, p=C.PLAN_MIX_BY_SIZE[size])]
            org = Organization(
                organization_id=f"org_{len(self.orgs) + 1:05d}",
                name=self.fake.unique.company(),
                industry=self._weighted(C.INDUSTRIES),
                country=self._weighted(C.COUNTRIES),
                company_size=size,
                acquisition_channel=channel,
                signup_date=signup,
            )
            self.orgs.append(org)

            seats = self._seats(plan)
            trial = self._open(org, plan, seats, signup, is_trial=True)
            trial_end = signup + timedelta(days=C.TRIAL_DAYS)
            converted = self.rng.random() < C.TRIAL_CONVERSION[channel]
            trial.end_date = trial_end
            trial.end_reason = "trial_converted" if converted else "trial_expired"
            if converted:
                self._open(org, plan, seats, trial_end)

    # --- sampling helpers -----------------------------------------------------

    def _random_day(self, month: date) -> date:
        return month + timedelta(days=int(self.rng.integers(0, month_end(month).day)))

    def _weighted(self, weights: dict[str, float]) -> str:
        keys = list(weights)
        p = np.array([weights[k] for k in keys])
        return keys[self.rng.choice(len(keys), p=p / p.sum())]

    def _seats(self, plan: str) -> int:
        median, sigma, maximum = C.SEATS_BY_PLAN[plan]
        seats = round(median * math.exp(sigma * self.rng.standard_normal()))
        return int(min(max(seats, C.PLANS[plan]["min_seats"]), maximum))
