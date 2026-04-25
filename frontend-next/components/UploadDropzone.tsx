"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud } from "lucide-react";

export default function UploadDropzone({ onFile }: { onFile: (file: File) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFile = (selected: File | null) => {
    if (!selected) return;
    setFile(selected);
    setProgress(0);
    onFile(selected);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 120);
  };

  return (
    <div className="glass rounded-3xl p-8">
      <label className="flex cursor-pointer flex-col items-center gap-4 rounded-2xl border border-dashed border-white/40 px-8 py-12 text-center">
        <UploadCloud className="text-ink" />
        <div>
          <p className="text-lg font-semibold">Drag & drop</p>
          <p className="text-sm text-ink/60">PNG, JPG, MP4 up to 50MB</p>
        </div>
        <input
          type="file"
          className="hidden"
          accept="image/*,video/*"
          onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
        />
      </label>

      {file && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6"
        >
          <p className="text-sm text-ink/70">Selected: {file.name}</p>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/30">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-pink-500"
              animate={{ width: `${progress}%` }}
            />
          </div>
        </motion.div>
      )}
    </div>
  );
}
