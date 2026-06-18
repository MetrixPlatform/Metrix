import { Database20Regular } from "@vicons/fluent";

import { actionPermission, defineMenuGroup, defineModule, definePage } from "../types";

export default defineModule({
  key: "demo-crud",
  version: "0.1.0",
  order: 90,
  dependencies: ["core"],
  menuGroups: [
    // 示例模块默认不显示在导航中；开发新页面时可给页面补回 menu，并按需启用该分组。
    defineMenuGroup({ key: "examples", labelKey: "route.group.examples", icon: Database20Regular, order: 80 })
  ],
  pages: [
    definePage({
      key: "demoCrud",
      path: "/demo-crud",
      titleKey: "route.demoCrud",
      component: () => import("./views/DemoCrudView.vue"),
      permission: actionPermission("demo_item", "read"),
      fallbackOrder: 90
      // menu: { group: "examples", icon: Database20Regular, order: 10 }
    })
  ]
});
