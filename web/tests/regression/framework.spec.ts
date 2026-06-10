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
    "route:dashboard",
    "route:users",
    "route:settings",
    "route:demo_crud",
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
  await page.addInitScript(() => {
    localStorage.setItem("metrix.token", "browser-test-token");
  });

  await page.goto("/demo-crud");

  await expect(page).toHaveURL(/\/demo-crud$/);
  await expect(page.locator(".page-title strong")).toContainText(/CRUD 示例|CRUD Demo/);
  await expect(page.getByRole("button", { name: /新增示例|New demo/i })).toBeVisible();
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
  await page.route("**/api/demo-items**", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 })
    })
  );
}
