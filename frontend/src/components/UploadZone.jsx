import { useState, useRef, useCallback } from "react";
import { BorderBeam } from "./ui/BorderBeam";

export default function UploadZone({ onFileAccepted }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file) return;
    if (!file.name.endsWith(".csv")) { alert("Please upload a .csv file."); return; }
    onFileAccepted(file);
  }, [onFileAccepted]);

  const openPicker = () => inputRef.current?.click();

  return (
    <div className="upload-shell">
      <h1 className="upload-title">Upload your results CSV</h1>
      <p className="upload-sub">Validex audits supported CSV result-table fields and deterministic statistical-value checks.</p>
      <div
        className={`dropzone${dragging ? " drag-over" : ""}`}
        style={{ position: "relative" }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files?.[0]); }}
      >
        <label htmlFor="validex-csv-upload" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>
          Choose a CSV file for Validex audit
        </label>
        <input id="validex-csv-upload" ref={inputRef} type="file" accept=".csv" onChange={e => handleFile(e.target.files?.[0])} style={{ display: "none" }} />
        <BorderBeam
          size={160}
          duration={dragging ? 3 : 6}
          colorFrom={dragging ? "#4ade80" : "#c8b99a"}
          colorTo={dragging ? "#60a5fa" : "#4ade80"}
          borderRadius="16px"
        />
        <div className="dropzone-icon">📊</div>
        <div className="dropzone-title">Drop your CSV here</div>
        <button
          type="button"
          className="dropzone-sub"
          onClick={openPicker}
          style={{ border: "none", background: "transparent", padding: 0, cursor: "pointer", font: "inherit" }}
        >
          or click to browse files
        </button>
        <div className="dropzone-hint">CSV · up to 200 MB</div>
      </div>
    </div>
  );
}
