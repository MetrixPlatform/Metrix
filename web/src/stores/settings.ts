import { reactive } from "vue";

import { getPublicSettings } from "../api/settings";
import type { PublicSettings } from "../api/types";
import { APP_NAME } from "../config/app";
import { DEFAULT_LOCALE, isLocale, type Locale } from "../i18n/messages";

export const settingsStore = reactive({
  loaded: false,
  publicSettings: {
    app_name: APP_NAME,
    registration_enabled: true,
    registration_required_fields: {
      phone: true,
      email: true,
      company: false,
      department: false
    },
    default_locale: DEFAULT_LOCALE
  } as PublicSettings,
  async loadPublic() {
    this.publicSettings = await getPublicSettings();
    this.loaded = true;
    return this.publicSettings;
  },
  setPublic(settings: PublicSettings) {
    this.publicSettings = settings;
    this.loaded = true;
  },
  appName() {
    return this.publicSettings.app_name || APP_NAME;
  },
  defaultLocale(): Locale {
    const locale = this.publicSettings.default_locale;
    return isLocale(locale) ? locale : DEFAULT_LOCALE;
  }
});
