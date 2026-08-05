"""Knowledge base sanity tests."""

from app.services.pipeline.knowledge import TOPIC_KNOWLEDGE, lookup_topic, research


def test_curated_topics_complete():
    required = {"abcs", "animals", "colors", "numbers", "solar system",
                "dinosaurs", "fruits", "vehicles"}
    assert required.issubset(set(TOPIC_KNOWLEDGE))
    for name, entry in TOPIC_KNOWLEDGE.items():
        assert len(entry["learning_objectives"]) >= 3, name
        assert len(entry["vocabulary"]) >= 3, name
        assert len(entry["facts"]) >= 3, name
        assert len(entry["scene_seeds"]) >= 6, name
        for seed in entry["scene_seeds"]:
            assert seed["focus"] and seed["object"] and seed["fact"], name
        assert entry["quiz"], name


def test_alias_lookup():
    assert lookup_topic("ABC") is not None
    assert lookup_topic("the alphabet") or lookup_topic("alphabet")
    assert lookup_topic("Counting 1-10") is not None  # substring fallback
    assert lookup_topic("space") is not None


def test_generic_fallback():
    kb = research("Underwater Volcanoes")
    assert kb["curated"] is False
    assert kb["learning_objectives"]
    assert len(kb["scene_seeds"]) >= 4
    assert "Underwater Volcanoes" in kb["display_name"]


def test_research_summary_shape():
    kb = research("Colors")
    for key in ("learning_objectives", "vocabulary", "facts", "teaching_points",
                "scene_seeds", "quiz", "summary"):
        assert key in kb
