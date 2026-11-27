from app.data.dach_brands import REQUIRED_DACH_NAMES, list_brands


def test_dach_catalog_contains_required_brands():
    names = {b["name"] for b in list_brands()}
    missing = set(REQUIRED_DACH_NAMES) - names
    assert not missing, f"Fehlende Marken: {missing}"
    assert all(b["logo_mode"] == "image" for b in list_brands())
    assert all(b["logo_rights_cleared"] is True for b in list_brands())
    assert all(b.get("logo_url") for b in list_brands())


def test_catalog_brands_api(client, auth_headers):
    res = client.get("/api/catalog/brands", headers=auth_headers)
    assert res.status_code == 200
    brands = res.json()
    assert len(brands) >= 38
    assert brands[0]["logo_mode"] == "image"
    assert brands[0]["logo_url"].startswith("/brand-logos/")

    search = client.get("/api/catalog/brands?q=bmw", headers=auth_headers)
    assert search.status_code == 200
    hits = search.json()
    assert any(b["slug"] == "bmw" for b in hits)
    # Treffer über Name, Slug oder Gruppe (z. B. „BMW Group“ → auch MINI)
    assert all(
        "bmw" in b["name"].casefold()
        or b["slug"] == "bmw"
        or "bmw" in b["group"].casefold()
        for b in hits
    )


def test_catalog_selection_flow_and_capabilities(client, auth_headers):
    models = client.get("/api/catalog/brands/vw/models", headers=auth_headers)
    assert models.status_code == 200
    model_id = models.json()[0]["id"]
    variants = client.get(
        f"/api/catalog/brands/vw/models/{model_id}/variants",
        headers=auth_headers,
    )
    assert variants.status_code == 200
    variant = variants.json()[0]

    caps = client.get("/api/catalog/capabilities?brand_slug=vw", headers=auth_headers)
    assert caps.status_code == 200
    body = caps.json()
    assert "keine Diagnoseabdeckung" in body["disclaimer_de"].casefold() or "Diagnoseabdeckung" in body["disclaimer_de"]
    assert len(body["available"]) >= 1
    assert all(a["status"] == "simulated" for a in body["available"])
    assert len(body["unavailable"]) >= 1

    vin = "WVWZZZ1JZXW000001"
    confirm = client.post(
        "/api/vehicles/confirm",
        headers=auth_headers,
        json={
            "brand_slug": "vw",
            "model_id": model_id,
            "variant_id": variant["id"],
            "year": variant["year_from"],
            "vin": vin,
            "license_plate": "W-TEST-02",
            "odometer_km": 123456,
        },
    )
    assert confirm.status_code == 201, confirm.text
    vehicle = confirm.json()
    assert vehicle["make"] == "VW"
    assert vehicle["vin"] == vin
    assert vehicle["odometer_km"] == 123456
    assert vehicle["is_example_data"] is False
    assert vehicle["catalog_brand_slug"] == "vw"

    # VIN manuell korrigieren
    patched = client.patch(
        f"/api/vehicles/{vehicle['id']}",
        headers=auth_headers,
        json={"vin": "WVWZZZ1JZXW000002", "odometer_km": 123500},
    )
    assert patched.status_code == 200
    assert patched.json()["vin"] == "WVWZZZ1JZXW000002"

    recent = client.get("/api/recent/selections", headers=auth_headers)
    assert recent.status_code == 200
    assert len(recent.json()) >= 1


def test_confirm_rejects_invalid_vin(client, auth_headers):
    models = client.get("/api/catalog/brands/audi/models", headers=auth_headers).json()
    model_id = models[0]["id"]
    variant = client.get(
        f"/api/catalog/brands/audi/models/{model_id}/variants",
        headers=auth_headers,
    ).json()[0]
    res = client.post(
        "/api/vehicles/confirm",
        headers=auth_headers,
        json={
            "brand_slug": "audi",
            "model_id": model_id,
            "variant_id": variant["id"],
            "year": variant["year_from"],
            "vin": "INVALID",
        },
    )
    assert res.status_code == 422 or res.status_code == 400


def test_theme_preferences_and_favorites(client, auth_headers):
    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["theme_preference"] in {"light", "dark", "system"}

    upd = client.patch(
        "/api/preferences",
        headers=auth_headers,
        json={"theme_preference": "light"},
    )
    assert upd.status_code == 200
    assert upd.json()["theme_preference"] == "light"

    me2 = client.get("/api/auth/me", headers=auth_headers)
    assert me2.json()["theme_preference"] == "light"

    fav = client.put(
        "/api/favorites/brands",
        headers=auth_headers,
        json={"brand_slugs": ["bmw", "vw", "bmw"]},
    )
    assert fav.status_code == 200
    assert fav.json()["brand_slugs"] == ["bmw", "vw"]

    got = client.get("/api/favorites/brands", headers=auth_headers)
    assert got.json()["brand_slugs"] == ["bmw", "vw"]


def test_empty_search_and_unknown_brand(client, auth_headers):
    empty = client.get("/api/catalog/brands?q=zzzz-not-a-brand", headers=auth_headers)
    assert empty.status_code == 200
    assert empty.json() == []

    missing = client.get("/api/catalog/brands/does-not-exist/models", headers=auth_headers)
    assert missing.status_code == 404
