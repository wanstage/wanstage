import { upsertLink } from "../src/db";
upsertLink("test01", "https://example.com/?utm_source=wanstage", ["campaign"]);
console.log("[OK] seeded test01");
