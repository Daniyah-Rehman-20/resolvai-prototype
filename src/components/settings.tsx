"use client";
import { useState } from "react";
import { Sun, Moon, Save, RotateCcw, ShieldCheck } from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel, Modal } from "@/components/common/ui";
import { saveSettings, resetWorkspace } from "@/lib/api";
export function Settings() {
  const { data, refresh, notify } = useWorkspace();
  const [settings, setSettings] = useState(data.settings);
  const [reset, setReset] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save() {
    setBusy(true);
    setError("");
    try {
      await saveSettings(settings);
      await refresh();
      notify("Workspace preferences saved.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="YOUR WORKSPACE"
        title="Settings"
        description="Make the workspace yours and control operational preferences."
      />
      <div className="settings-layout">
        <Panel title="Workspace preferences" subtitle="Saved in this browser">
          <div className="setting-row">
            <div>
              <strong>Appearance</strong>
              <p>Choose a comfortable workspace theme.</p>
            </div>
            <div className="segmented">
              <button
                aria-pressed={settings.theme === "light"}
                onClick={() => setSettings({ ...settings, theme: "light" })}
              >
                <Sun size={16} />
                Light
              </button>
              <button
                aria-pressed={settings.theme === "dark"}
                onClick={() => setSettings({ ...settings, theme: "dark" })}
              >
                <Moon size={16} />
                Dark
              </button>
            </div>
          </div>
          <label className="setting-row">
            <span>
              <strong>Review notifications</strong>
              <p>Show approval reminders in the notification menu.</p>
            </span>
            <input
              type="checkbox"
              role="switch"
              checked={settings.notifications}
              onChange={(e) =>
                setSettings({ ...settings, notifications: e.target.checked })
              }
            />
          </label>
          <label className="setting-row">
            <span>
              <strong>Source failure mode</strong>
              <p>Exercise investigation error handling and document indexing recovery.</p>
            </span>
            <input
              type="checkbox"
              role="switch"
              checked={settings.simulateFailure}
              onChange={(e) =>
                setSettings({ ...settings, simulateFailure: e.target.checked })
              }
            />
          </label>
          <div className="setting-row">
            <div>
              <strong>Currency & timezone</strong>
              <p>Indian Rupee (INR) · India Standard Time (IST)</p>
            </div>
            <span className="subtle">Workspace default</span>
          </div>
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          <button className="button" disabled={busy} onClick={save}>
            <Save size={16} />
            {busy ? "Saving…" : "Save preferences"}
          </button>
        </Panel>
        <Panel title="Operational safeguards">
          <div className="callout">
            <ShieldCheck size={24} />
            <div>
              <strong>External execution controls</strong>
              <p>
                Sensitive actions remain approval-gated. External payment execution and external AI providers are not connected from this workspace.
              </p>
            </div>
          </div>
          <p>
            Workspace preferences are stored in this browser. Operational records are managed by the backend.
          </p>
          <p>
            Use the reset below to restore the starter workspace records.
            Export anything you need before resetting.
          </p>
          <button
            className="button secondary danger"
            onClick={() => setReset(true)}
          >
            <RotateCcw size={16} />
            Reset workspace data
          </button>
        </Panel>
      </div>
      {reset && (
        <Modal
          title="Reset the workspace?"
          onClose={() => {
            if (!busy) setReset(false);
          }}
        >
          <p>
            This removes local investigations, review decisions, document
            metadata, case updates, and preferences, then restores the starter dataset.
          </p>
          <div className="modal-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setReset(false)}
            >
              Cancel
            </button>
            <button
              className="button danger-solid"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await resetWorkspace();
                  await refresh();
                  setSettings({
                    theme: "light",
                    notifications: true,
                    simulateFailure: false,
                  });
                  setReset(false);
                  notify("Workspace data reset.");
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              Reset workspace
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
