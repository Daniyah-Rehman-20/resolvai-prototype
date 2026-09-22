"use client";
import { useState, useRef } from "react";
import { Upload, FileText, Search, CheckCircle2, RotateCw } from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel, Badge, Modal, Empty } from "@/components/common/ui";
import { uploadDocument, finishUpload } from "@/lib/api";
import { dateTime } from "@/lib/utils";
import type { PolicyDocument } from "@/lib/types";
export function Knowledge() {
  const { data, refresh, notify } = useWorkspace();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<PolicyDocument | null>(null);
  const [upload, setUpload] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  async function ingest(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const id = await uploadDocument(file);
      await refresh();
      setUpload(false);
      await finishUpload(id);
      await refresh();
      notify("Simulated document processing finished.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const docs = data.documents.filter((d) =>
    d.name.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <PageTitle
        eyebrow="GROUNDED IN POLICY"
        title="Knowledge Base"
        description="A shared source of guidance for payment investigations."
      >
        <button
          className="button"
          onClick={() => {
            setUpload(true);
            setError("");
          }}
          disabled={busy}
        >
          <Upload size={17} />
          Upload document
        </button>
      </PageTitle>
      <div className="mini-metrics">
        <div>
          <BookCount value={data.documents.length} label="Policy documents" />
        </div>
        <div>
          <BookCount
            value={data.documents.filter((d) => d.indexed).length}
            label="Ready to retrieve"
          />
        </div>
        <div>
          <BookCount
            value={data.documents.reduce((s, d) => s + d.chunks, 0)}
            label="Simulated chunks"
          />
        </div>
      </div>
      <Panel
        title="Policy library"
        subtitle="All policies and indexing values are fictional demo examples"
        action={
          <div className="input-icon">
            <Search size={16} />
            <input
              aria-label="Search documents"
              placeholder="Find a policy…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        }
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Document</th>
                <th>Type</th>
                <th>Uploaded</th>
                <th>Processing</th>
                <th>Chunks</th>
                <th>Index</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>
                    <button
                      className="document-link"
                      onClick={() => setSelected(d)}
                    >
                      <FileText size={20} />
                      {d.name}
                    </button>
                  </td>
                  <td>{d.type}</td>
                  <td>{dateTime(d.uploadedAt)}</td>
                  <td>
                    <Badge value={d.status} />
                  </td>
                  <td>{d.chunks}</td>
                  <td>
                    {d.indexed ? (
                      <span className="indexed">
                        <CheckCircle2 size={14} />
                        Indexed
                      </span>
                    ) : (
                      "Not indexed"
                    )}
                  </td>
                  <td>
                    {d.status === "FAILED" || d.status === "PROCESSING" ? (
                      <button
                        className="button ghost"
                        onClick={async () => {
                          setBusy(true);
                          try {
                            await finishUpload(d.id);
                            await refresh();
                          } catch (e) {
                            notify((e as Error).message);
                          } finally {
                            setBusy(false);
                          }
                        }}
                        disabled={busy}
                      >
                        <RotateCw size={15} />
                        Retry
                      </button>
                    ) : (
                      <button
                        className="text-link"
                        onClick={() => setSelected(d)}
                      >
                        Read policy →
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!docs.length && (
          <Empty
            title="No matching policies"
            detail="Try another document name."
          />
        )}
      </Panel>
      {error && !upload && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      {selected && (
        <Modal title={selected.name} onClose={() => setSelected(null)}>
          <Badge value={selected.status} />
          <p className="policy-body">{selected.content}</p>
          <p className="microcopy">
            {selected.id} · Demo policy. Not official banking guidance.
          </p>
        </Modal>
      )}
      {upload && (
        <Modal
          title="Upload a policy document"
          onClose={() => {
            if (!busy) setUpload(false);
          }}
        >
          <p>
            Choose PDF, TXT, or Markdown, up to 10 MB. This demo stores the
            filename and simulated processing metadata only.
          </p>
          <div
            className="drop-zone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (!busy) void ingest(e.dataTransfer.files[0]);
            }}
          >
            <Upload size={32} />
            <strong>Drop a document here</strong>
            <span>or choose a file from your computer</span>
            <input
              ref={input}
              type="file"
              accept=".pdf,.txt,.md"
              aria-label="Policy document"
              disabled={busy}
              onChange={(e) => void ingest(e.target.files?.[0])}
            />
          </div>
          {busy && <p role="status">Processing document…</p>}
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
        </Modal>
      )}
    </>
  );
}
function BookCount({ value, label }: { value: number; label: string }) {
  return (
    <>
      <strong>{value}</strong>
      <span>{label}</span>
    </>
  );
}
