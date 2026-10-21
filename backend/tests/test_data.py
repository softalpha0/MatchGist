from app.simulator.engine import load_clubs


def test_clubs_are_complete_and_fictional():
    clubs = load_clubs()
    assert set(clubs) == {"RIV", "NOR"}
    for club in clubs.values():
        assert len(club.players) == 16
        assert len(club.starters()) == 11
        positions = [p.position for p in club.starters()]
        assert positions.count("GK") == 1 and positions.count("DF") == 4
        assert len({p.shirt_number for p in club.players}) == 16
        assert all(p.player_id.startswith(club.club_id) for p in club.players)
    names = [p.name for c in clubs.values() for p in c.players]
    assert len(set(names)) == len(names)
