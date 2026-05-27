# Seed Users

All accounts use password: **`Password1!`**

---

## Shippers

| Name | Email | Phone |
|---|---|---|
| Alice Chen | alice.shipper@example.com | +1 (202) 555-0101 |
| Bob Martinez | bob.shipper@example.com | +1 (202) 555-0102 |
| Carol Johnson | carol.shipper@example.com | +1 (202) 555-0103 |

---

## Haulers

| Name | Email | Phone | Vehicle | Rating | Jobs |
|---|---|---|---|---|---|
| Dave Williams | dave.hauler@example.com | +1 (202) 555-0201 | 2020 Ford F-150 (pickup) | ⭐ 4.7 (23 reviews) | 34 |
| Evan Brown | evan.hauler@example.com | +1 (202) 555-0202 | 2019 Ford Transit 250 (cargo van) + 2018 Ram 1500 trailer | ⭐ 4.9 (51 reviews) | 68 |
| Fiona Davis | fiona.hauler@example.com | +1 (202) 555-0203 | 2022 Chevy Silverado (pickup, lift gate) | ⭐ 4.5 (10 reviews) | 12 |

---

## Load snapshot

| Status | Count | Who's involved |
|---|---|---|
| `posted` | 5 | Alice (×2), Bob (×2), Carol (×1) |
| `accepted` | 2 | Carol→Dave, Alice→Evan |
| `in_transit` | 1 | Bob→Fiona (office furniture, Oakland→Santa Clara) |
| `delivered` | 4 | Alice→Dave (×2), Bob→Evan, Carol→Fiona |
| `cancelled` | 1 | Carol (fridge move, never accepted) |

---

## Re-seed

```bash
cd backend
uv run python scripts/seed_data.py
```

The script is idempotent — safe to run again if you wipe and recreate the DB.
