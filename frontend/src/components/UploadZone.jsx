import { useState, useRef, useCallback } from "react";

export default function UploadZone({ onFileAccepted }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file) return;
    if (!file.name.endsWith(".csv")) { alert("Please upload a .csv file."); return; }
    onFileAccepted(file);
  }, [onFileAccepted]);

  return (
    <div className="upload-shell">
      <h1 className="upload-title">Upload your results CSV</h1>
      <p className="upload-sub">Validex will detect your statistical schema and run a full validity audit.</p>
      <div
        className={`dropzone${dragging ? " drag-over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files?.[0]); }}
        onClick={() => inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept=".csv" onChange={e => handleFile(e.target.files?.[0])} style={{ display: "none" }} />
        <div className="dropzone-icon">📊</div>
        <div className="dropzone-title">Drop your CSV here</div>
        <div className="dropzone-sub">or click to browse files</div>
        <div className="dropzone-hint">CSV · up to 200 MB</div>
      </div>
    </div>
  );
}
