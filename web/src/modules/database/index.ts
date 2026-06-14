import { Database20Regular } from "@vicons/fluent";

import { defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "database",
  version: "0.1.0",
  order: 40,
  dependencies: ["core"],
  pages: [
    definePage({
      key: "database",
      path: "/database",
      titleKey: "route.database",
      component: () => import("./views/DatabaseManageView.vue"),
      permission: routePermission("database"),
      fallbackOrder: 86,
      menu: { icon: Database20Regular, order: 30 }
    })
  ]
});
