"""Offline unit tests for the tool package (no network, no models)."""

from zerolinc.zeroshot_engine import parse_spec
from zerolinc.normalizer import normalize_text
from zerolinc.memory_engine import _vote
from zerolinc.verbalizer import CATEGORIES, CODES, PROMPT_CONFIGS


def test_twelve_categories():
    assert len(CATEGORIES) == 12
    assert CODES[0] == "CAT1" and CODES[-1] == "CAT12"


def test_prompt_configs_cover_all_categories():
    for name, cfg in PROMPT_CONFIGS.items():
        assert "{}" in cfg.template, name
        assert sorted(cfg.labels.values()) == sorted(CODES), name


def test_normalize_compresses_tags():
    raw = "De [EMAIL_ADDRESS_f6f7086365] host [IP_ADDRESS_907d29be4d]"
    assert normalize_text(raw) == "De <EMAIL> host <IP>"


def test_parse_spec():
    assert parse_spec("gliclass:knowledgator/x") == ("gliclass", "knowledgator/x")
    assert parse_spec("a/b") == ("nli", "a/b")


def test_vote_weighted_majority():
    sims = [0.9, 0.8, 0.1]
    assert _vote(sims, ["CAT3", "CAT3", "CAT5"], [0, 1, 2], 3) == "CAT3"


def test_tool_load_texts(tmp_path):
    import pandas as pd
    from zerolinc.router import _load_texts
    f = tmp_path / "in.csv"
    pd.DataFrame({"incidente_id": ["A1"], "conteudo": ["texto [URL_aabbccdd11]"]}).to_csv(
        f, index=False)
    items = _load_texts(f)
    assert items[0].incident_id == "A1" and "<URL>" in items[0].text


def test_train_and_load_index(tmp_path, monkeypatch):
    import numpy as np
    import zerolinc.memory_engine as me
    import pandas as pd
    f = tmp_path / "labeled.csv"
    pd.DataFrame({"incidente_id": ["A", "B"], "conteudo": ["texto um", "texto dois"],
                  "categoria": ["CAT5", "CAT3"]}).to_csv(f, index=False)
    monkeypatch.setattr(me, "embed_texts",
                        lambda m, texts, **kw: np.eye(2, 4, dtype="float32"))
    out = tmp_path / "idx.npz"
    info = me.build_index(f, "fake/model", out)
    assert info["n_references"] == 2 and out.exists()
    idx = me.load_index(out)
    assert idx["labels"] == ["CAT5", "CAT3"] and idx["model_id"] == "fake/model"
    assert idx["embeddings"].shape == (2, 4)
