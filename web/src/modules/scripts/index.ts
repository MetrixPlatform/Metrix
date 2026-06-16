import { Code20Regular } from "@vicons/fluent";

import { defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "scripts",
  version: "0.1.0",
  order: 50,
  dependencies: ["core", "containers"],
  pages: [
    definePage({
      key: "scripts",
      path: "/scripts",
      titleKey: "route.scripts",
      component: () => import("./views/ScriptManageView.vue"),
      permission: routePermission("scripts"),
      fallbackOrder: 88,
      menu: { icon: Code20Regular, order: 50 }
    })
  ]
});
