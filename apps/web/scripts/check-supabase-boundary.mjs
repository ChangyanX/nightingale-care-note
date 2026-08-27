import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = fileURLToPath(new URL("..", import.meta.url));
const sourceRoots = ["app", "components", "lib"];
const allowedClientModule = "lib/supabase/browser.ts";
const violations = [];

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await sourceFiles(path));
    else if ([".ts", ".tsx"].includes(extname(entry.name))) files.push(path);
  }
  return files;
}

for (const root of sourceRoots) {
  for (const path of await sourceFiles(join(webRoot, root))) {
    const name = relative(webRoot, path);
    const source = await readFile(path, "utf8");

    if (name !== allowedClientModule && /from\s+["']@supabase\/(?:ssr|supabase-js)["']/.test(source)) {
      violations.push(`${name}: import the constrained browser client instead of a raw Supabase SDK`);
    }

    if (!source.includes("createSupabaseBrowserClient")) continue;
    const clientExpressions = ["createSupabaseBrowserClient\\(\\)"];
    for (const match of source.matchAll(/\b(?:const|let|var)\s+(\w+)\s*=\s*createSupabaseBrowserClient\(\)/g)) {
      clientExpressions.push(`\\b${match[1]}\\b`);
    }
    for (const expression of clientExpressions) {
      const directDataCall = new RegExp(`(?:${expression})\\s*\\.\\s*(from|rpc|storage|functions)\\b`, "g");
      for (const match of source.matchAll(directDataCall)) {
        violations.push(`${name}: browser Supabase ${match[1]} access is forbidden; use FastAPI`);
      }
    }
  }
}

if (violations.length) {
  console.error("Frontend/Supabase boundary violations:\n" + violations.map((item) => `- ${item}`).join("\n"));
  process.exitCode = 1;
} else {
  console.log("Frontend/Supabase boundary OK: browser use is limited to Auth and Realtime invalidation.");
}
