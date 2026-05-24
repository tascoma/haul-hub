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

  return (
    <div>
      <h1>Your profile</h1>

      <form className="card form-grid" onSubmit={saveProfile}>
        <h2 style={{ marginBottom: 0 }}>Account</h2>
        <div className="muted" style={{ fontSize: "0.85rem" }}>{me.email}</div>
        <div>
          <label htmlFor="fn">Full name</label>
          <input id="fn" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="ph">Phone</label>
          <input id="ph" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <button type="submit" className="primary" disabled={savingProfile}>
          {savingProfile ? "Saving…" : "Save"}
        </button>
        {profileMsg && <div className="muted">{profileMsg}</div>}
      </form>

      <form className="card form-grid" onSubmit={saveHauler}>
        <h2 style={{ marginBottom: 0 }}>
          {me.profile.hauler_enabled ? "Hauler details" : "Become a hauler"}
        </h2>
        <div className="muted" style={{ fontSize: "0.85rem" }}>
          {me.profile.hauler_enabled
            ? "Update your vehicle and capacity."
            : "Fill this out to start accepting loads."}
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="vt">Vehicle type</label>
            <select
              id="vt"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value as VehicleType)}
            >
              {VEHICLE_TYPES.map((v) => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
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
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="mk">Vehicle make</label>
            <input id="mk" value={vehicleMake} onChange={(e) => setVehicleMake(e.target.value)} />
          </div>
          <div>
            <label htmlFor="md">Vehicle model</label>
            <input id="md" value={vehicleModel} onChange={(e) => setVehicleModel(e.target.value)} />
          </div>
        </div>
        <button type="submit" className="primary" disabled={savingHauler}>
          {savingHauler
            ? "Saving…"
            : me.profile.hauler_enabled
              ? "Save"
              : "Enable hauler role"}
        </button>
        {haulerMsg && <div className="muted">{haulerMsg}</div>}
      </form>
    </div>
  );
}
