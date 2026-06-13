import { Database20Regular, Document20Regular } from "@vicons/fluent";

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
    }),
    definePage({
      key: "database_jobs",
      path: "/database/jobs",
      titleKey: "route.databaseJobs",
      component: () => import("./views/DataJobsView.vue"),
      permission: routePermission("database_jobs"),
      fallbackOrder: 87,
      menu: { icon: Document20Regular, order: 31 }
    })
  ]
});
