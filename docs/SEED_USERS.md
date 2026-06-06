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

## Northwest Arkansas (manually seeded)

Added directly to the `hh` Supabase DB for the load-maps work. Same password
(`Password1!`) as the rest; these use the `479` area code and the
`America/Chicago` timezone. Each shipper has a default-pickup "Home" address.

### Shippers

| Name | Email | Phone | City |
|---|---|---|---|
| Grace Whitman | grace.shipper@example.com | +1 (479) 555-0101 | Bentonville, AR |
| Marcus Reed | marcus.shipper@example.com | +1 (479) 555-0102 | Rogers, AR |
| Priya Anand | priya.shipper@example.com | +1 (479) 555-0103 | Fayetteville, AR |
| Derek Olsen | derek.shipper@example.com | +1 (479) 555-0104 | Springdale, AR |

### Haulers

| Name | Email | Phone | Company | Home base | Vehicle | Rating | Jobs |
|---|---|---|---|---|---|---|---|
| Hank Caldwell | hank.hauler@example.com | +1 (479) 555-0301 | Ozark Haul Co (LLC), 50-mi radius | Bentonville, AR | 2021 Ford F-250 (pickup w/ trailer) | ⭐ 4.8 (37 reviews) | 52 |

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
