import llm_moonshot


def test_get_moonshot_models_falls_back_to_default_catalog(monkeypatch):
    monkeypatch.setattr(llm_moonshot, "fetch_cached_json", lambda *args, **kwargs: {"data": []})

    models = llm_moonshot.get_moonshot_models()

    assert models == [{"id": model_id} for model_id in llm_moonshot.DEFAULT_MOONSHOT_MODEL_IDS]


def test_register_models_uses_fallback_catalog_without_key(monkeypatch):
    monkeypatch.setattr(llm_moonshot, "get_moonshot_models", lambda: [{"id": "kimi-latest"}])
    registered = []

    llm_moonshot.register_models(registered.append)

    assert len(registered) == 1
    model = registered[0]
    assert model.model_id == "moonshot/kimi-latest"
    assert model.model_name == "kimi-latest"
