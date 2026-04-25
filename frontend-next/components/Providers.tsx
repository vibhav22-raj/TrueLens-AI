"use client";

import "@/lib/i18n";
import { ThemeProvider } from "@/components/ThemeContext";
import { I18nextProvider } from "react-i18next";
import i18n from "@/lib/i18n";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nextProvider i18n={i18n}>
      <ThemeProvider>{children}</ThemeProvider>
    </I18nextProvider>
  );
}
