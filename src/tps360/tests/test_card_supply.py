from tps360.simulation.services.card_supply import initial_hand, round_offer


def test_commander_hand_wider_than_member() -> None:
    commander = initial_hand("local-gov-head", "wildfire")
    member = initial_hand("vol-fire-member", "wildfire")
    assert len(commander) > len(member)


def test_initial_hand_deterministic() -> None:
    assert initial_hand("emerg-dsns", "wildfire") == initial_hand("emerg-dsns", "wildfire")


def test_round_offer_deterministic() -> None:
    a = round_offer("emerg-dsns", "wildfire", 1, 0.2)
    b = round_offer("emerg-dsns", "wildfire", 1, 0.2)
    assert a == b


def test_no_liquidation_card_before_escalation() -> None:
    offer = round_offer("emerg-dsns", "wildfire", 1, 0.2)
    assert offer.includes_liquidation is False
    assert "EXTINGUISH_FIRE" not in offer.offered


def test_liquidation_card_appears_on_escalation() -> None:
    offer = round_offer("emerg-dsns", "wildfire", 3, 0.8)
    assert offer.includes_liquidation is True
    assert "EXTINGUISH_FIRE" in offer.offered


def test_offer_is_not_a_single_obvious_card() -> None:
    # anti-guessing: at least two options (real + distractor)
    offer = round_offer("emerg-dsns", "wildfire", 1, 0.2)
    assert len(offer.offered) >= 2
