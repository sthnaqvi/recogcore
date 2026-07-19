from recog_core.greeting import GreetingCooldown, GreetingStabilizer, build_greeting
from recog_core.vision.recognizer import RecognitionResult


def test_build_greeting_known_uses_known_phrasing_and_fills_name():
    result = RecognitionResult(name="Alice", is_known=True, confidence=0.9)
    greeting = build_greeting(result, known_phrasings=["Hi, {name}!"], unknown_phrasings=["Hi there!"])
    assert greeting == "Hi, Alice!"


def test_build_greeting_unknown_uses_unknown_phrasing():
    result = RecognitionResult(name="unknown", is_known=False, confidence=0.0)
    greeting = build_greeting(result, known_phrasings=["Hi, {name}!"], unknown_phrasings=["Hi there!"])
    assert greeting == "Hi there!"


def test_build_greeting_picks_from_multiple_phrasings():
    result = RecognitionResult(name="Bob", is_known=True, confidence=0.8)
    phrasings = ["Hi, {name}!", "Welcome back, {name}!"]
    greeting = build_greeting(result, known_phrasings=phrasings, unknown_phrasings=["Hi there!"])
    assert greeting in {"Hi, Bob!", "Welcome back, Bob!"}


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def test_cooldown_allows_first_greeting():
    clock = _FakeClock()
    cooldown = GreetingCooldown(cooldown_seconds=90, clock=clock)
    assert cooldown.should_greet("Alice") is True


def test_cooldown_blocks_regreeting_within_window():
    clock = _FakeClock()
    cooldown = GreetingCooldown(cooldown_seconds=90, clock=clock)

    cooldown.mark_greeted("Alice")
    clock.now += 30  # still within the 90s cooldown

    assert cooldown.should_greet("Alice") is False


def test_cooldown_allows_regreeting_after_window():
    clock = _FakeClock()
    cooldown = GreetingCooldown(cooldown_seconds=90, clock=clock)

    cooldown.mark_greeted("Alice")
    clock.now += 91  # past the cooldown

    assert cooldown.should_greet("Alice") is True


def test_cooldown_tracks_each_person_independently():
    clock = _FakeClock()
    cooldown = GreetingCooldown(cooldown_seconds=90, clock=clock)

    cooldown.mark_greeted("Alice")
    assert cooldown.should_greet("Bob") is True


def test_cooldown_shares_one_key_for_all_unknown_faces():
    clock = _FakeClock()
    cooldown = GreetingCooldown(cooldown_seconds=90, clock=clock)

    cooldown.mark_greeted("unknown")
    clock.now += 10

    assert cooldown.should_greet("unknown") is False


def test_stabilizer_requires_consecutive_passes_before_stable():
    stabilizer = GreetingStabilizer(required_consecutive=3)

    assert stabilizer.observe({"Alice"}) == set()
    assert stabilizer.observe({"Alice"}) == set()
    assert stabilizer.observe({"Alice"}) == {"Alice"}


def test_stabilizer_one_pass_flicker_never_becomes_stable():
    # The exact bug from live testing: one person flickering across several identities.
    # None of the flickers should ever reach stability.
    stabilizer = GreetingStabilizer(required_consecutive=3)

    assert stabilizer.observe({"Tauseef"}) == set()
    assert stabilizer.observe({"Afsha"}) == set()
    assert stabilizer.observe({"Jazib"}) == set()
    assert stabilizer.observe({"unknown"}) == set()


def test_stabilizer_resets_streak_when_identity_disappears_for_a_pass():
    stabilizer = GreetingStabilizer(required_consecutive=3)

    stabilizer.observe({"Alice"})
    stabilizer.observe({"Alice"})
    stabilizer.observe(set())  # Alice missing for one pass -- streak resets
    assert stabilizer.observe({"Alice"}) == set()
    assert stabilizer.observe({"Alice"}) == set()
    assert stabilizer.observe({"Alice"}) == {"Alice"}


def test_stabilizer_tracks_multiple_identities_independently():
    stabilizer = GreetingStabilizer(required_consecutive=2)

    stabilizer.observe({"Alice", "Bob"})
    assert stabilizer.observe({"Alice", "Bob"}) == {"Alice", "Bob"}


def test_stabilizer_stays_stable_while_identity_remains_in_view():
    stabilizer = GreetingStabilizer(required_consecutive=2)

    stabilizer.observe({"Alice"})
    assert stabilizer.observe({"Alice"}) == {"Alice"}
    assert stabilizer.observe({"Alice"}) == {"Alice"}


def test_stabilizer_holds_unknown_to_double_the_streak_requirement():
    stabilizer = GreetingStabilizer(required_consecutive=2)

    # A named identity stabilizes at 2 passes; "unknown" must wait for 2 * 2 = 4.
    assert stabilizer.observe({"unknown"}) == set()
    assert stabilizer.observe({"unknown"}) == set()
    assert stabilizer.observe({"unknown"}) == set()
    assert stabilizer.observe({"unknown"}) == {"unknown"}
