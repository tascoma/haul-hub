import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface UploadState {
  file: File | null;
  uploading: boolean;
  done: boolean;
  error: string | null;
}

function FileInput({
  label,
  accept,
  value,
  onChange,
}: {
  label: string;
  accept: string;
  value: File | null;
  onChange: (f: File | null) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div>
      <label style={{ display: "block", marginBottom: 6 }}>{label}</label>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button
          type="button"
          className="hh-btn"
          style={{ height: 38, fontSize: 13 }}
          onClick={() => ref.current?.click()}
        >
          {value ? "Change file" : "Choose file"}
        </button>
        <span style={{ fontSize: 13, color: value ? "var(--hh-ink-700)" : "var(--hh-ink-400)" }}>
          {value ? value.name : "No file chosen"}
        </span>
      </div>
      <input
        ref={ref}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}

export function DocumentsOnboardingPage() {
  const navigate = useNavigate();

  // Insurance state
  const [insuranceFile, setInsuranceFile] = useState<File | null>(null);
  const [carrierName, setCarrierName] = useState("");
  const [policyNumber, setPolicyNumber] = useState("");
  const [expiresOn, setExpiresOn] = useState("");
  const [insurance, setInsurance] = useState<UploadState>({ file: null, uploading: false, done: false, error: null });

  // Driver's license state
  const [licenseFile, setLicenseFile] = useState<File | null>(null);
  const [license, setLicense] = useState<UploadState>({ file: null, uploading: false, done: false, error: null });

  const [submitting, setSubmitting] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const uploadInsurance = async (): Promise<boolean> => {
    if (!insuranceFile) {
      setInsurance((s) => ({ ...s, error: "Please choose an insurance certificate file" }));
      return false;
    }
    setInsurance((s) => ({ ...s, uploading: true, error: null }));
    const fd = new FormData();
    fd.append("file", insuranceFile);
    fd.append("kind", "insurance_certificate");
    if (carrierName) fd.append("carrier_name", carrierName);
    if (policyNumber) fd.append("policy_number", policyNumber);
    if (expiresOn) fd.append("expires_on", expiresOn);
    try {
      await api.upload("/me/documents/upload", fd);
      setInsurance((s) => ({ ...s, uploading: false, done: true }));
      return true;
    } catch (err) {
      setInsurance((s) => ({
        ...s,
        uploading: false,
        error: err instanceof ApiError ? err.detail : "Upload failed",
      }));
      return false;
    }
  };

  const uploadLicense = async (): Promise<boolean> => {
    if (!licenseFile) {
      setLicense((s) => ({ ...s, error: "Please choose a driver's license image" }));
      return false;
    }
    setLicense((s) => ({ ...s, uploading: true, error: null }));
    const fd = new FormData();
    fd.append("file", licenseFile);
    fd.append("kind", "drivers_license");
    try {
      await api.upload("/me/verifications/upload", fd);
      setLicense((s) => ({ ...s, uploading: false, done: true }));
      return true;
    } catch (err) {
      setLicense((s) => ({
        ...s,
        uploading: false,
        error: err instanceof ApiError ? err.detail : "Upload failed",
      }));
      return false;
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGlobalError(null);
    setSubmitting(true);
    const [insOk, licOk] = await Promise.all([uploadInsurance(), uploadLicense()]);
    setSubmitting(false);
    if (insOk && licOk) navigate("/onboarding");
  };

  return (
    <div className="auth-card" style={{ maxWidth: 560 }}>
      <h1>Verification documents</h1>
      <div className="sub">
        We're required to collect proof of insurance and a valid driver's license before you can
        accept haul jobs.
      </div>

      <form className="form-grid" onSubmit={onSubmit}>
        {/* ─── Insurance certificate ─────────────────────────── */}
        <fieldset
          style={{
            border: "1px solid var(--hh-ink-100)",
            borderRadius: 12,
            padding: "14px 16px",
            display: "grid",
            gap: 12,
          }}
        >
          <legend style={{ padding: "0 6px", font: "700 12px var(--hh-font-display)" }}>
            Proof of insurance
          </legend>

          <FileInput
            label="Insurance certificate (image or PDF)"
            accept="image/*,application/pdf"
            value={insuranceFile}
            onChange={setInsuranceFile}
          />

          <div>
            <label htmlFor="carrier_name">Insurance carrier</label>
            <input
              id="carrier_name"
              placeholder="e.g. State Farm"
              value={carrierName}
              onChange={(e) => setCarrierName(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="policy_number">Policy number</label>
            <input
              id="policy_number"
              placeholder="e.g. POL-123456"
              value={policyNumber}
              onChange={(e) => setPolicyNumber(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="expires_on">Policy expiry date</label>
            <input
              id="expires_on"
              type="date"
              value={expiresOn}
              onChange={(e) => setExpiresOn(e.target.value)}
            />
          </div>

          {insurance.done && (
            <div style={{ color: "var(--hh-success, #16a34a)", fontSize: 13 }}>
              ✓ Insurance certificate uploaded
            </div>
          )}
          {insurance.error && <div className="error">{insurance.error}</div>}
        </fieldset>

        {/* ─── Driver's license ──────────────────────────────── */}
        <fieldset
          style={{
            border: "1px solid var(--hh-ink-100)",
            borderRadius: 12,
            padding: "14px 16px",
            display: "grid",
            gap: 12,
          }}
        >
          <legend style={{ padding: "0 6px", font: "700 12px var(--hh-font-display)" }}>
            Driver's license
          </legend>

          <FileInput
            label="Driver's license photo (front)"
            accept="image/*"
            value={licenseFile}
            onChange={setLicenseFile}
          />

          {license.done && (
            <div style={{ color: "var(--hh-success, #16a34a)", fontSize: 13 }}>
              ✓ Driver's license uploaded
            </div>
          )}
          {license.error && <div className="error">{license.error}</div>}
        </fieldset>

        <button
          type="submit"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          disabled={submitting}
        >
          {submitting ? "Uploading…" : "Continue"}
        </button>
        {globalError && <div className="error">{globalError}</div>}
      </form>
    </div>
  );
}
