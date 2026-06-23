import { expect, test, type Page } from "@playwright/test";

const publicSettings = {
  app_name: "Metrix",
  registration_enabled: true,
  registration_approval_required: true,
  registration_required_fields: {
    phone: true,
    email: true,
    company: false,
    department: false
  },
  default_locale: "zh-CN",
  api_enabled: true,
  api_token_reveal_enabled: true
};

const adminSession = {
  token: "browser-test-token",
  user: {
    id: 1,
    username: "rootadmin",
    full_name: "管理员",
    phone: "",
    email: "",
    company: "",
    department: "",
    approval_status: "approved",
    is_active: true,
    is_builtin: true,
    roles: []
  },
  permissions: [
    "action:dashboard:read",
    "action:user:read",
    "action:setting:read",
    "action:container:create",
    "action:container:read",
    "action:container:update",
    "action:container:delete",
    "action:container:operate",
    "action:container:manage_others",
    "action:database:create",
    "action:database:read",
    "action:database:update",
    "action:database:delete",
    "action:database:operate",
    "action:database:manage_others",
    "action:demo_item:create",
    "action:demo_item:read",
    "action:demo_item:update",
    "action:demo_item:delete",
    "action:demo_item:manage_others"
  ]
};

test("redirects to install page when system is not initialized", async ({ page }) => {
  await mockApi(page, { installed: false });

  await page.goto("/");

  await expect(page).toHaveURL(/\/install$/);
});

test("shows login page for initialized anonymous users", async ({ page }) => {
  await mockApi(page, { installed: true });

  await page.goto("/");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: /登录|Login/i })).toBeVisible();
});

test("restores session and opens permitted module page", async ({ page }) => {
  await mockApi(page, { installed: true, session: adminSession });
  await setSessionToken(page);

  await page.goto("/demo-crud");

  await expect(page).toHaveURL(/\/demo-crud$/);
  await expect(page.locator(".page-title strong")).toContainText(/CRUD 示例|CRUD Demo/);
  await expect(page.getByRole("button", { name: /新增示例|New demo/i })).toBeVisible();
});

test("shows not found page for unknown authenticated routes", async ({ page }) => {
  await mockApi(page, { installed: true, session: adminSession });
  await setSessionToken(page);

  await page.goto("/not-found-route");

  await expect(page).toHaveURL(/\/not-found-route$/);
  await expect(page.getByRole("heading", { name: "404" })).toBeVisible();
});

test("opens database management and embedded jobs without raw i18n keys", async ({ page }) => {
  const dataJobRequests: string[] = [];
  await mockApi(page, { installed: true, session: adminSession });
  await page.route("**/api/databases**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 })
    })
  );
  await page.route("**/api/database-transfer-jobs**", (route) => {
    dataJobRequests.push(route.request().url());
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            job_id: "job-1",
            conn_id: "db_test",
            connection_name: "test",
            kind: "export",
            format: "xlsx",
            status: "success",
            file_name: "export.xlsx",
            file_size: 1024,
            row_count: 1,
            error_code: "",
            created_by: 1,
            created_by_username: "rootadmin",
            created_at: "2026-06-14T00:00:00Z",
            expires_at: "2026-06-15T00:00:00Z"
          }
        ],
        total: 1,
        page: 1,
        page_size: 20
      })
    });
  });
  await setSessionToken(page);

  await page.goto("/database");
  await expect(page).toHaveURL(/\/database$/);
  await expect(page.getByRole("button", { name: "任务" })).toBeVisible();

  await page.getByRole("button", { name: "任务" }).click();
  await expect(page.getByRole("button", { name: "返回" })).toBeVisible();
  await expect(page.getByText("common.back")).toHaveCount(0);

  await page.locator(".database-jobs-view .n-data-table-th").filter({ hasText: "创建时间" }).click();
  await expect.poll(() => dataJobRequests.some((url) => url.includes("sort_order=ascend"))).toBe(true);
});

test("keeps database workbench layout readable", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  await mockApi(page, { installed: true, session: adminSession });
  await page.route("**/api/databases**", (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/databases/db_test/schemas") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify([{ name: "0421" }])
      });
    }
    if (url.pathname === "/api/databases/db_test/tables") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify([{ name: "capacityreport" }])
      });
    }
    if (url.pathname === "/api/databases/db_test/table-data") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          columns: [],
          primary_keys: [],
          rows: [],
          total: 0,
          page: 1,
          page_size: 100
        })
      });
    }
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: 1,
            conn_id: "db_test",
            name: "test",
            db_type: "mysql",
            host: "127.0.0.1",
            port: 3306,
            username: "root",
            default_database: "0421",
            is_shared: true,
            is_active: true,
            created_by: 1,
            created_by_username: "rootadmin",
            created_at: "2026-06-14T00:00:00Z",
            updated_at: "2026-06-14T00:00:00Z"
          }
        ],
        total: 1,
        page: 1,
        page_size: 20
      })
    });
  });
  await page.route("**/api/sql-scripts**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 100 })
    })
  );
  await page.route("**/api/database-transfer-jobs/unseen-count**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ count: 0 })
    })
  );
  await page.route("**/api/database-transfer-jobs/mark-seen**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ count: 0 })
    })
  );
  await page.route("**/api/databases/*/server-info**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ db_type: "mysql", version: "8.0.0", load_data_infile: true })
    })
  );
  await loginWithMockSession(page);
  await page.evaluate(() => {
    localStorage.removeItem("metrix.databaseWorkbench.sidebarWidth");
    localStorage.removeItem("app.databaseWorkbench.sidebarWidth");
  });
  await page.getByText("数据库管理", { exact: true }).click();
  await expect(page).toHaveURL(/\/database$/);
  const connectionLink = page.locator(".storage-name-link").filter({ hasText: "test" }).first();
  await expect(connectionLink).toBeVisible();
  await connectionLink.evaluate((node) => (node as HTMLElement).click());
  await expect.poll(() => page.getByRole("button", { name: "返回" }).first().innerText()).toBe("");
  await expect(page.locator(".database-sidebar")).toBeVisible();

  await expect.poll(() => page.locator(".database-sidebar").evaluate((node) => node.getBoundingClientRect().width)).toBeGreaterThanOrEqual(220);

  await expect(page.locator(".database-tree").getByText("0421")).toBeVisible();
  await expect(page.locator(".database-tree").getByText("表", { exact: true })).toBeVisible();
  await expect(page.locator(".database-tree").getByText("脚本", { exact: true })).toBeVisible();
  await expect(page.locator(".database-tree").getByText("capacityreport")).toBeVisible();

  await page.getByRole("button", { name: "新建标签" }).click();
  await page.getByText("临时 SQL", { exact: true }).click();
  await expect.poll(() => page.locator(".database-sql-editor").evaluate((node) => node.getBoundingClientRect().height)).toBeGreaterThanOrEqual(280);
});

test("renders container images in short viewports", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 520 });
  await mockApi(page, { installed: true, session: adminSession });
  await page.route("**/api/container-engine/status", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        available: true,
        message: "",
        version: "29.5.3",
        os_type: "linux",
        architecture: "x86_64",
        docker_host: "fake://docker",
        containers: 0,
        images: 1
      })
    })
  );
  await page.route("**/api/container-instances**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 })
    })
  );
  await page.route("**/api/container-images**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "sha256:test-image",
            short_id: "sha256:test",
            repo_tags: ["alpine:3.20"],
            size: 3641182,
            created_at: "2026-04-16T23:53:26Z",
            labels: {},
            owner_user_id: null,
            owner_username: "",
            is_public: true,
            source: "docker"
          }
        ],
        total: 1,
        page: 1,
        page_size: 20
      })
    })
  );
  await page.route("**/api/container-jobs**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 })
    })
  );
  await loginWithMockSession(page);

  await page.goto("/containers");
  await page.locator(".n-tabs-tab__label").filter({ hasText: "镜像" }).click();

  await expect(page.getByText("alpine:3.20")).toBeVisible();
  await expect(page.getByText("sha256:test-image")).toBeVisible();
});

async function mockApi(
  page: Page,
  options: {
    installed: boolean;
    session?: typeof adminSession;
  }
) {
  await page.route("**/api/install/status", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ installed: options.installed, database_type: options.installed ? "sqlite" : null })
    })
  );
  await page.route("**/api/settings/public", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(publicSettings)
    })
  );
  await page.route("**/api/announcements/public", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: "[]"
    })
  );
  await page.route("**/api/announcements/mine", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: "[]"
    })
  );
  await page.route("**/api/auth/me", (route) => {
    if (!options.session) {
      return route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "error.unauthorized", message: "Unauthorized", params: {} } })
      });
    }
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(options.session)
    });
  });
  await page.route("**/api/auth/login", (route) => {
    if (!options.session) {
      return route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "error.unauthorized", message: "Unauthorized", params: {} } })
      });
    }
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(options.session)
    });
  });
  await page.route("**/api/demo-items**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 })
    })
  );
}

async function loginWithMockSession(page: Page) {
  await page.goto("/login");
  await page.locator("input").nth(0).fill("rootadmin");
  await page.locator("input").nth(1).fill("browser-test-password");
  await page.getByRole("button", { name: /登录|Login/i }).click();
  await expect(page).toHaveURL(/\/$/);
}

async function setSessionToken(page: Page, options: { clearDatabaseSidebarWidth?: boolean } = {}) {
  await page.addInitScript((clearDatabaseSidebarWidth) => {
    localStorage.setItem("metrix.token", "browser-test-token");
    localStorage.setItem("app.token", "browser-test-token");
    if (clearDatabaseSidebarWidth) {
      localStorage.removeItem("metrix.databaseWorkbench.sidebarWidth");
      localStorage.removeItem("app.databaseWorkbench.sidebarWidth");
    }
  }, Boolean(options.clearDatabaseSidebarWidth));
}
