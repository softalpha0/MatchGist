import pytest
from pydantic import ValidationError

from app.fans.profiles import FanProfile, load_fans


def test_demo_personas_validate():
    fans = load_fans()
    assert len(fans) == 6
    assert {f.channel for f in fans} >= {"broadcast", "sms", "voice", "push", "watch"}
    assert {f.language for f in fans} == {"en", "id", "pcm", "pt-BR", "hi", "ar"}


def test_hindi_persona_exercises_ucs2_sms():
    delhi = next(f for f in load_fans() if f.fan_id == "fan_delhi")
    assert (delhi.channel, delhi.language, delhi.favorite_player) == ("sms", "hi", "RIV-10")


def test_profile_rules():
    with pytest.raises(ValidationError):
        FanProfile(fan_id="x", display_name="x", language="en", mode="player_focus", channel="sms")
    with pytest.raises(ValidationError):
        FanProfile(
            fan_id="x", display_name="x", language="en", mode="casual", channel="sms", only_if_involved=True
        )
    with pytest.raises(ValidationError):
        FanProfile(fan_id="x", display_name="x", language="xx", mode="casual", channel="sms")
