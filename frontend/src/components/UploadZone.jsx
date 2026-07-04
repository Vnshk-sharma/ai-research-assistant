import { useRef, useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";

export default function UploadZone({ onUpload, uploading }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files) => {
    [...files].filter((f) => f.type === "application/pdf").forEach(onUpload);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-card p-8 text-center cursor-pointer transition-colors
        ${dragging ? "border-sienna bg-sienna/5" : "border-rule hover:border-indigo/50"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {uploading ? (
        <Loader2 className="mx-auto mb-2 animate-spin text-indigo" size={28} />
      ) : (
        <UploadCloud className="mx-auto mb-2 text-ink-soft" size={28} />
      )}
      <p className="font-display text-ink">
        {uploading ? "Processing manuscript…" : "Drop research papers here"}
      </p>
      <p className="text-xs text-ink-soft mt-1 font-mono">PDF only · click to browse</p>
    </div>
  );
}
