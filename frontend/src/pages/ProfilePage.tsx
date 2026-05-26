import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { HaulerProfile, VehicleType } from "../lib/types";

const VEHICLE_TYPES: VehicleType[] = [
  "pickup",
  "pickup_with_trailer",
  "flatbed",
  "box_truck",
  "cargo_van",
  "semi",
  "other",
];

const VEHICLE_LABELS: Record<VehicleType, string> = {
  pickup: "Pickup",
  pickup_with_trailer: "Pickup + trailer",
  flatbed: "Flatbed",
  box_truck: "Box truck",
  cargo_van: "Cargo van",
  semi: "Semi",
  other: "Other",
};

function initialsOf(value: string | null | undefined): string {
  if (!value) return "?";
  const parts = value.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || value[0]?.toUpperCase() || "?";
}

export function ProfilePage() {
  const { me, refresh } = useAuth();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState<string | null>(null);

  const [haulerProfile, setHaulerProfile] = useState<HaulerProfile | null>(null);
  const [vehicleType, setVehicleType] = useState<VehicleType>("pickup");
  const [maxWeight, setMaxWeight] = useState("");
  const [vehicleMake, setVehicleMake] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [haulerMsg, setHaulerMsg] = useState<string | null>(null);
  const [savingHauler, setSavingHauler] = useState(false);

  useEffect(() => {
    if (!me) return;
    setFullName(me.profile.full_name ?? "");
    setPhone(me.profile.phone ?? "");
    if (me.profile.hauler_enabled) {
      api
        .get<HaulerProfile>("/me/hauler-profile")
        .then((p) => {
          setHaulerProfile(p);
          setVehicleType(p.vehicle_type);
          setMaxWeight(p.max_weight_lbs?.toString() ?? "");
          setVehicleMake(p.vehicle_make ?? "");
          setVehicleModel(p.vehicle_model ?? "");
        })
        .catch(() => {
          /* not enabled */
        });
    }
  }, [me]);

  if (!me) return null;

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg(null);
    try {
      await api.patch("/me", { full_name: fullName, phone });
      await refresh();
      setProfileMsg("Profile saved.");
    } catch (err) {
      setProfileMsg(err instanceof ApiError ? err.detail : "Save failed");
    } finally {
      setSavingProfile(false);
    }
  };

  const saveHauler = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingHauler(true);
    setHaulerMsg(null);
    const body = {
      vehicle_type: vehicleType,
      max_weight_lbs: maxWeight ? Number(maxWeight) : null,
      vehicle_make: vehicleMake || null,
      vehicle_model: vehicleModel || null,
    };
    try {
      if (haulerProfile) {
        const updated = await api.patch<HaulerProfile>("/me/hauler-profile", body);
        setHaulerProfile(updated);
        setHaulerMsg("Hauler profile saved.");
      } else {
        const created = await api.post<HaulerProfile>("/me/enable-hauler", body);
        setHaulerProfile(created);
        await refresh();
        setHaulerMsg("You're now set up as a hauler.");
      }
    } catch (err) {
      setHaulerMsg(err instanceof ApiError ? err.detail : "Save failed");
    } finally {
      setSavingHauler(false);
    }
  };

  const initials = initialsOf(me.profile.full_name || me.email);
  const verified = !!haulerProfile?.verified_at;

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Profile</h1>
          <div className="sub">Manage your account, role, and vehicle.</div>
        </div>
      </div>

      {/* Identity hero */}
      <div className="card" style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <span className="hh-avatar hh-avatar--xl hh-avatar--dark">{initials}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ font: "700 20px var(--hh-font-display)", letterSpacing: "-0.015em" }}>
            {me.profile.full_name || "Add your name"}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>
            {me.email}
            {me.profile.phone && <> · {me.profile.phone}</>}
          </div>
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            {me.profile.shipper_enabled && (
              <span className="hh-pill hh-pill--info">Shipper</span>
            )}
            {me.profile.hauler_enabled && (
              <span className="hh-pill hh-pill--accent">Hauler</span>
            )}
            {verified && <span className="hh-pill hh-pill--success">Verified</span>}
          </div>
        </div>
      </div>

      <div className="dashboard-cols two">
        <form className="card form-grid" onSubmit={saveProfile}>
          <h2>Account</h2>
          <div>
            <label htmlFor="fn">Full name</label>
            <input id="fn" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label htmlFor="ph">Phone</label>
            <input id="ph" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="actions">
            <button type="submit" className="accent" disabled={savingProfile}>
              {savingProfile ? "Saving…" : "Save profile"}
            </button>
          </div>
          {profileMsg && <div className="muted" style={{ fontSize: 12 }}>{profileMsg}</div>}
        </form>

        <form className="card form-grid" onSubmit={saveHauler}>
          <div className="section-h">
            <h3>{me.profile.hauler_enabled ? "Vehicle" : "Become a hauler"}</h3>
            {haulerProfile && (
              <span className="hh-pill hh-pill--success">
                {verified ? "Verified" : "Pending review"}
              </span>
            )}
          </div>
          <div className="muted" style={{ fontSize: 13 }}>
            {me.profile.hauler_enabled
              ? "Update your vehicle and capacity."
              : "Fill this out to start accepting loads."}
          </div>
          <div>
            <label htmlFor="vt">Vehicle type</label>
            <select
              id="vt"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value as VehicleType)}
            >
              {VEHICLE_TYPES.map((v) => (
                <option key={v} value={v}>
                  {VEHICLE_LABELS[v]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="mw">Max weight (lbs)</label>
            <input
              id="mw"
              type="number"
              min={0}
              value={maxWeight}
              onChange={(e) => setMaxWeight(e.target.value)}
            />
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="mk">Vehicle make</label>
              <input
                id="mk"
                value={vehicleMake}
                onChange={(e) => setVehicleMake(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="md">Vehicle model</label>
              <input
                id="md"
                value={vehicleModel}
                onChange={(e) => setVehicleModel(e.target.value)}
              />
            </div>
          </div>
          <div className="actions">
            <button type="submit" className="primary" disabled={savingHauler}>
              {savingHauler
                ? "Saving…"
                : me.profile.hauler_enabled
                  ? "Save vehicle"
                  : "Enable hauler role"}
            </button>
          </div>
          {haulerMsg && <div className="muted" style={{ fontSize: 12 }}>{haulerMsg}</div>}
        </form>
      </div>

      {haulerProfile && (
        <div className="card">
          <h3>Capacity at a glance</h3>
          <div className="hh-stat-row" style={{ marginTop: 8 }}>
            <div>
              <div className="hh-stat__v">
                {haulerProfile.max_weight_lbs?.toLocaleString() ?? "—"}
              </div>
              <div className="hh-stat__l">max lb</div>
            </div>
            <div>
              <div className="hh-stat__v">
                {haulerProfile.max_length_ft ?? "—"} × {haulerProfile.max_width_ft ?? "—"}
              </div>
              <div className="hh-stat__l">ft (L × W)</div>
            </div>
            <div>
              <div className="hh-stat__v">{haulerProfile.max_height_ft ?? "—"}</div>
              <div className="hh-stat__l">ft tall</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
