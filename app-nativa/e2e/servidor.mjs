// Servidor local mínimo da versão web (dist-web), no mesmo subcaminho do GitHub Pages (/biomaterial-ideal/),
// para testar os caminhos relativos sem publicar nada. Só escuta em 127.0.0.1.
// Uso: node e2e/servidor.mjs [porta]   (por omissão 4317, ou a variável PORTA)
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const SUBCAMINHO = "/biomaterial-ideal/";
const RAIZ = resolve(fileURLToPath(new URL("../dist-web", import.meta.url)));
const porta = Number(process.argv[2] ?? process.env.PORTA ?? 4317);

const TIPOS = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".wasm": "application/wasm",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ttf": "font/ttf",
  ".woff2": "font/woff2",
  ".glb": "model/gltf-binary",
  ".txt": "text/plain; charset=utf-8",
};

createServer((pedido, resposta) => {
  const url = new URL(pedido.url ?? "/", "http://127.0.0.1");
  if (url.pathname === "/" || url.pathname === SUBCAMINHO.slice(0, -1)) {
    resposta.writeHead(302, { location: SUBCAMINHO });
    resposta.end();
    return;
  }
  if (!url.pathname.startsWith(SUBCAMINHO)) {
    resposta.writeHead(404, { "content-type": "text/html; charset=utf-8" });
    resposta.end("<h1>404</h1>");
    return;
  }
  let relativo = decodeURIComponent(url.pathname.slice(SUBCAMINHO.length)) || "index.html";
  if (relativo.endsWith("/")) relativo += "index.html";
  const ficheiro = normalize(join(RAIZ, relativo));
  if (!ficheiro.startsWith(RAIZ) || !existsSync(ficheiro) || !statSync(ficheiro).isFile()) {
    resposta.writeHead(404, { "content-type": "text/html; charset=utf-8" });
    resposta.end("<h1>404</h1>");
    return;
  }
  resposta.writeHead(200, { "content-type": TIPOS[extname(ficheiro).toLowerCase()] ?? "application/octet-stream" });
  if (pedido.method === "HEAD") resposta.end();
  else createReadStream(ficheiro).pipe(resposta);
}).listen(porta, "127.0.0.1", () => {
  console.log(`versão web em http://127.0.0.1:${porta}${SUBCAMINHO}`);
});
