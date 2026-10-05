from pydantic import BaseModel

from .allocation import Allocation
from .profile import UserProfile
from .risk import RiskResult

ASSETS = ("equity", "debt", "gold", "liquid")


class Simulation(BaseModel):
    simulation_id: str
    before: dict[str, int]
    after: dict[str, int]
    trace: list[str]
    warnings: list[str]


def rebalance(weights: dict[str, int], asset: str, value: int) -> dict[str, int]:
    """asset ko value% par set karo, baaki sab ko proportionally adjust karo (total hamesha 100)."""
    others = [k for k in weights if k != asset]
    remaining = 100 - value
    base = sum(weights[k] for k in others)
    if base == 0:
        new = {k: remaining // len(others) for k in others}
    else:
        new = {k: int(weights[k] * remaining / base + 0.5) for k in others}
    new[asset] = value
    diff = 100 - sum(new.values())          # rounding ka fark sabse bade hisse se adjust
    if diff:
        biggest = max(others, key=lambda k: new[k])
        new[biggest] += diff
    return {k: new[k] for k in weights}


def check_guardrails(weights: dict[str, int], profile: UserProfile, recommended_equity: int) -> list[str]:
    """Roke nahi, sirf warning de: faisla user ka hai."""
    w: list[str] = []
    if weights["equity"] > recommended_equity + 15:
        w.append(f"Equity {weights['equity']}% is much higher than the {recommended_equity}% "
                 f"suggested for your risk profile; expect bigger swings and possible losses.")
    if profile.investing_horizon_years < 3 and weights["equity"] > 20:
        w.append("Your horizon is under 3 years; equity can fall sharply in the short term.")
    if profile.emergency_fund_months < 3 and weights["liquid"] < 20:
        w.append("Your emergency fund is below 3 months; keeping little in liquid funds is risky.")
    top = max(weights, key=weights.get)
    if weights[top] >= 80:
        w.append(f"{weights[top]}% in a single asset class ({top}) is highly concentrated.")
    if weights["gold"] > 20:
        w.append(f"Gold at {weights['gold']}% is high; gold gives no regular income and can stay flat for years.")
    return w


class PortfolioManager:
    """Versions + simulate -> apply -> undo. LLM sirf in methods ko call karega, numbers yahin se aayenge."""

    def __init__(self, profile: UserProfile, risk: RiskResult, allocation: Allocation):
        self.profile = profile
        self.risk = risk
        self.versions: list[dict[str, int]] = [dict(allocation.weights)]
        self._sims: dict[str, Simulation] = {}

    @property
    def current(self) -> dict[str, int]:
        return dict(self.versions[-1])

    def simulate(self, asset: str, value: int) -> Simulation:
        """Naya version calculate karo, bina apply kiye."""
        if asset not in ASSETS:
            raise ValueError(f"Unknown asset '{asset}'. Choose from {ASSETS}.")
        if not 0 <= value <= 100:
            raise ValueError("Weight must be between 0 and 100.")
        before = self.current
        after = rebalance(before, asset, value)
        sim = Simulation(
            simulation_id=f"sim_{len(self._sims) + 1}",
            before=before, after=after,
            trace=[f"Set {asset} to {value}%; other assets scaled proportionally to keep the total at 100%."],
            warnings=check_guardrails(after, self.profile, self.versions[0]["equity"]),
        )
        self._sims[sim.simulation_id] = sim
        return sim

    def apply(self, simulation_id: str) -> dict[str, int]:
        sim = self._sims.get(simulation_id)
        if sim is None:
            raise ValueError(f"Unknown simulation '{simulation_id}'.")
        if sim.before != self.current:
            raise ValueError("Portfolio changed since this simulation; run it again.")
        self.versions.append(dict(sim.after))
        return self.current

    def undo(self) -> dict[str, int]:
        if len(self.versions) == 1:
            raise ValueError("Already at the original recommendation.")
        self.versions.pop()
        return self.current