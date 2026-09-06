import{defineConfig,devices}from"@playwright/test";

export default defineConfig({
 testDir:"./tests/e2e",
 timeout:30000,
 expect:{timeout:7000},
 fullyParallel:false,
 retries:1,
 reporter:"list",
 use:{baseURL:"http://127.0.0.1:4173",trace:"retain-on-failure",screenshot:"only-on-failure",video:"off"},
 projects:[{name:"chromium",use:{...devices["Desktop Chrome"]}}]
});
