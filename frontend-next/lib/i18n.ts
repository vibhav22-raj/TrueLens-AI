import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./translations/en.json";
import hi from "./translations/hi.json";

if (!i18n.isInitialized) {
  const savedLanguage =
    typeof window !== "undefined" ? window.localStorage.getItem("ds_lang") || "en" : "en";

  i18n
    .use(initReactI18next)
    .init({
      resources: {
        en: { translation: en },
        hi: { translation: hi }
      },
      lng: savedLanguage,
      fallbackLng: "en",
      interpolation: { escapeValue: false }
    });

  i18n.on("languageChanged", (lang) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("ds_lang", lang);
    }
  });
}

export default i18n;
