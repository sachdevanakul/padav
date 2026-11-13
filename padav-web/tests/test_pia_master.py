"""Guards the 50-item master form: structure, assets, deterministic build, and a full API run using its real keys."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from app.core.config import settings
from app.schemas.pia import PiaContentFile
from app.services.pia_blueprint import SUBTESTS, validate_form_shape
from app.services.pia_content import PiaContentImporter
from tests.test_pia import answer, base, begin

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "content" / "pia-master-v1.json"


@pytest.fixture(scope="module")
def raw():
    return json.loads(MASTER.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def master(raw):
    return PiaContentFile.model_validate(raw)


def test_master_matches_the_blueprint(master):
    pairs = [(i.domain, i.difficulty) for i in master.items]
    assert validate_form_shape(pairs) == []
    assert Counter(i.domain for i in master.items) == {s.domain: s.questions for s in SUBTESTS}
    assert master.form and master.form.items == [i.item_code for i in master.items]


def test_every_item_is_bilingual_draft_and_original(master):
    for item in master.items:
        assert set(item.translations) == {"en", "hi"}, item.item_code
        assert item.status == "draft" and item.reviewer is None  # nothing is claimed as reviewed
        assert all(not t.reviewed for t in item.translations.values())
        assert item.author and "pending expert review" in item.author
        for language, text in item.translations.items():
            assert text.explanation, f"{item.item_code}/{language} needs an explanation"
            assert 2 <= len(text.options) <= 4


def test_assets_exist_and_are_safe_svgs(master):
    ids = {i.asset_id for i in master.items if i.asset_id}
    assert len(ids) == 12
    for asset in ids:
        svg = (ROOT / "content" / "pia-assets" / f"{asset}.svg").read_text(encoding="utf-8")
        assert svg.startswith("<svg") and "<script" not in svg.lower() and "onload" not in svg.lower() and "href" not in svg.lower()
    visual = [i for i in master.items if i.asset_id]
    assert all(i.accessibility_notes and "non-visual" in i.accessibility_notes for i in visual)


def test_timed_items_have_stimulus_in_both_languages(master):
    timed = [i for i in master.items if i.stimulus_display_seconds]
    assert {i.domain for i in timed} == {"gwm", "glr"} and len(timed) == 8
    assert all(t.stimulus for i in timed for t in i.translations.values())


def test_answer_keys_are_spread_out(master):
    keys = Counter(i.answer_key for i in master.items)
    assert set(keys) == set("abcd") and max(keys.values()) <= 20  # not all 'a'


def test_build_is_deterministic(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_master", ROOT / "content" / "pia" / "build_master.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # its own asserts re-verify every computed key
    monkeypatch.setattr(module, "OUT", tmp_path / "out.json")
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    module.main()
    assert (tmp_path / "out.json").read_bytes() == MASTER.read_bytes()
    for svg in (tmp_path / "assets").glob("*.svg"):
        assert svg.read_bytes() == (ROOT / "content" / "pia-assets" / svg.name).read_bytes()


def test_drafts_cannot_be_activated_without_the_dev_flag(db, master):
    from app.core.exceptions import BadRequestError
    with pytest.raises(BadRequestError, match="draft"):
        PiaContentImporter(db).import_content(master, activate=True)


def test_full_run_with_the_real_form(client, user, db, raw, master):
    """Imports the real form, plays it through the API with the real keys, and gets 50/50."""
    PiaContentImporter(db).import_content(master, activate=True, allow_draft=True)
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    keys = {i["item_code"]: i["answer_key"] for i in raw["items"]}
    for subtest in SUBTESTS:
        domain = subtest.domain
        items = client.post(f"{base(sid, domain)}/start", headers=h).json()
        assert len(items) == subtest.questions
        for item in items:
            if item["stimulus_display_seconds"]:
                assert item["stimulus"] is None  # withheld until released
                released = client.post(f"{base(sid, domain)}/items/{item['item_code']}/stimulus", headers=h)
                assert released.status_code == 200 and released.json()["stimulus"]
            if item["asset_id"]:
                assert item["asset_data_uri"].startswith("data:image/svg+xml;base64,")
            assert answer(client, h, sid, domain, item["item_code"], keys[item["item_code"]]).status_code == 200
        assert client.post(f"{base(sid, domain)}/complete", headers=h).status_code == 200
    report = client.post(f"{base(sid)}/finish", headers=h).json()
    assert report["total_correct"] == 50 and report["raw_accuracy"] == 1.0
    assert settings.pia_asset_dir.is_dir()
