import { Server20Regular } from "@vicons/fluent";

import { defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "storage",
  version: "0.1.0",
  order: 30,
  dependencies: ["core"],
  pages: [
    definePage({
      key: "storage",
      path: "/storage",
      titleKey: "route.storage",
      component: () => import("./views/StorageManageView.vue"),
      permission: routePermission("storage"),
      fallbackOrder: 85,
      menu: { icon: Server20Regular, order: 20 }
    })
  ]
});
