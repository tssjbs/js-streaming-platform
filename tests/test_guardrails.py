from src.guardrails.policies import validate_external_url


def test_blocks_javascript_scheme():
    ok, reason, _ = validate_external_url("javascript:alert(1)")
    assert not ok
    assert "not allowed" in reason.lower()


def test_allows_youtube_https():
    ok, _, meta = validate_external_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert ok
    assert "iframe_embed" in meta["encoder_hints"][0]