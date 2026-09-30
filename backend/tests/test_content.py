"""Content read endpoints must serve only approved learner-safe content."""


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_taxonomy_shape(client):
    resp = client.get("/api/content/taxonomy")
    assert resp.status_code == 200
    buckets = resp.json()["buckets"]
    assert {b["id"] for b in buckets} == {"quant", "logic"}
    for b in buckets:
        assert b["topics"], f"bucket {b['id']} has no topics"
        for t in b["topics"]:
            assert t["id"].startswith(b["id"])


def test_concepts_have_no_answers(client):
    resp = client.get("/api/content/concepts")
    assert resp.status_code == 200
    concepts = resp.json()
    assert concepts, "bootstrap pack should include concepts"
    for c in concepts:
        blob = str(c).lower()
        assert "correct_option" not in blob
        # ingested concepts embed verified worked examples (answer + why),
        # which is teaching content — never live test answers
        assert ("answer" not in blob or c.get("examples")
                or c.get("common_mistakes") or c.get("formulas"))


def test_flashcards_served(client):
    resp = client.get("/api/content/flashcards")
    assert resp.status_code == 200
    cards = resp.json()
    assert cards
    for fc in cards:
        assert {"id", "skill_id", "front", "back"} <= set(fc.keys())


def test_release_info(client):
    resp = client.get("/api/release")
    assert resp.status_code == 200
    info = resp.json()
    assert info["concept_count"] >= 1
    assert info["family_count"] >= 10
