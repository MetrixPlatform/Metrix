import { Toolbox20Regular } from "@vicons/fluent";

import { defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "containers",
  version: "0.1.0",
  order: 45,
  dependencies: ["core"],
  pages: [
    definePage({
      key: "containers",
      path: "/containers",
      titleKey: "route.containers",
      component: () => import("./views/ContainerManageView.vue"),
      permission: routePermission("containers"),
      fallbackOrder: 87,
      menu: { icon: Toolbox20Regular, order: 45 }
    })
  ]
});
