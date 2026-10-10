// Vídeo de demonstração de cerca de 60 s (plano B da apresentação), gerado pela própria aplicação: o Playwright
// grava a versão web (dist-web) servida localmente, sem captura de ecrã, a 1920 x 1080, e o ffmpeg converte para
// MP4 (H.264). Nada é publicado: o servidor só escuta em 127.0.0.1.
//
// Uso (em app-nativa/, depois de `npm run build:web`):
//   node e2e/video_demo.mjs [saída.mp4]
// Por omissão grava em ../design/video/demo_app_60s.mp4. O ffmpeg vem da variável FFMPEG, do PATH ou do pacote
// imageio-ffmpeg do Python indicado na variável PYTHON.
//
// Guião: Início; haste femoral (três métodos e consenso); doente com o perfil "jovem ativo", que troca o vencedor
// do TOPSIS; Monte Carlo em direto da haste; stent.
import { execFileSync, spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const AQUI = dirname(fileURLToPath(import.meta.url));
const SAIDA = resolve(process.argv[2] ?? join(AQUI, "..", "..", "design", "video", "demo_app_60s.mp4"));
const PORTA = Number(process.env.PORTA ?? 4318);
const URL_APP = `http://127.0.0.1:${PORTA}/biomaterial-ideal/`;
const LARGURA = 1920;
const ALTURA = 1080;

/** Caminho do ffmpeg: variável FFMPEG, PATH, ou o binário do imageio-ffmpeg (Python da variável PYTHON). */
function ffmpeg() {
  if (process.env.FFMPEG && existsSync(process.env.FFMPEG)) return process.env.FFMPEG;
  try {
    execFileSync("ffmpeg", ["-version"], { stdio: "ignore" });
    return "ffmpeg";
  } catch {
    /* segue para o imageio-ffmpeg */
  }
  const py = process.env.PYTHON ?? "python";
  return execFileSync(py, ["-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"], { encoding: "utf-8" }).trim();
}

/** Espera pelo servidor local. */
async function esperarServidor() {
  for (let k = 0; k < 100; k++) {
    try {
      if ((await fetch(URL_APP)).ok) return;
    } catch {
      /* ainda a arrancar */
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("o servidor local não arrancou");
}

/** Legenda na parte de baixo do ecrã (só no vídeo; não altera a aplicação). */
async function legenda(page, texto) {
  await page.evaluate((t) => {
    let el = document.getElementById("legenda-video");
    if (!el) {
      el = document.createElement("div");
      el.id = "legenda-video";
      el.style.cssText =
        "position:fixed;left:50%;bottom:36px;transform:translateX(-50%);z-index:9999;max-width:1400px;padding:14px 28px;" +
        "border-radius:12px;background:rgba(11,27,46,.88);color:#fff;font:600 28px/1.35 Inter,system-ui,sans-serif;" +
        "text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.25);transition:opacity .3s";
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, texto);
}

const pausa = (page, ms) => page.waitForTimeout(ms);

/** Desloca a área principal suavemente até um elemento. */
async function mostrar(page, locator) {
  await locator.evaluate((el) => el.scrollIntoView({ behavior: "smooth", block: "center" }));
  await pausa(page, 900);
}

async function menu(page, texto) {
  await page.getByRole("navigation", { name: "Ecrãs" }).getByRole("button", { name: texto, exact: true }).click();
  await page.locator("main .animate-pulse").first().waitFor({ state: "detached", timeout: 15_000 }).catch(() => {});
}

async function guiao(page) {
  const marcas = [];
  const t0 = Date.now();
  const marca = (nome) => marcas.push([nome, (Date.now() - t0) / 1000]);

  // 1. Início (cerca de 6 s)
  marca("início");
  await legenda(page, "Biomaterial Ideal: escolha multicritério de biomateriais (TOPSIS, WASPAS, VIKOR)");
  await pausa(page, 6000);

  // 2. Haste femoral (cerca de 11 s)
  marca("haste");
  await menu(page, "Haste femoral");
  await legenda(page, "Haste femoral: os três métodos e o consenso de Borda, com os pesos do relatório");
  await page.getByRole("region", { name: "Ranking TOPSIS" }).waitFor();
  await pausa(page, 5000);
  const cursor = page.getByRole("slider").first();
  await mostrar(page, cursor);
  await legenda(page, "Os pesos mudam e os materiais trocam de lugar em direto");
  await cursor.focus();
  for (let k = 0; k < 8; k++) {
    await page.keyboard.press("ArrowRight");
    await pausa(page, 180);
  }
  await pausa(page, 1500);
  for (let k = 0; k < 8; k++) await page.keyboard.press("ArrowLeft");
  await pausa(page, 1000);

  // 3. Doente: perfil que troca o vencedor (cerca de 15 s)
  marca("doente");
  await menu(page, "Doente");
  await legenda(page, "Doente: os dados do doente mudam os pesos segundo regras com fonte");
  await pausa(page, 3500);
  await page.getByRole("button", { name: /^H1:/ }).click();
  await page.getByText("Com os dados do doente").waitFor();
  await legenda(page, "Perfil H1, jovem ativo: a fadiga pesa mais e o vencedor do TOPSIS muda");
  await pausa(page, 5500);
  await mostrar(page, page.getByText("Lado a lado com o caso de base"));
  await legenda(page, "Lado a lado com o caso de base: posição em cada método, antes e depois");
  await pausa(page, 4500);

  // 4. Monte Carlo da haste (cerca de 14 s)
  marca("monte carlo");
  await menu(page, "Haste femoral");
  await page.getByRole("region", { name: "Ranking TOPSIS" }).waitFor();
  const correr = page.getByRole("button", { name: "Correr" });
  await mostrar(page, correr);
  await legenda(page, "Monte Carlo em direto: 10 000 repetições com as propriedades a variar");
  await pausa(page, 1500);
  await correr.click();
  const tabela = page.locator("table").filter({ hasText: "app / relatório" });
  await tabela.waitFor({ timeout: 60_000 });
  await mostrar(page, page.getByRole("img", { name: /Percentagem de repetições/ }));
  await pausa(page, 4500);
  await mostrar(page, tabela);
  await legenda(page, "A aplicação reproduz o Monte Carlo do relatório (% de vezes em 1.º lugar)");
  await pausa(page, 5000);

  // 5. Stent (cerca de 12 s)
  marca("stent");
  await menu(page, "Stent");
  await legenda(page, "Stent expansível por balão: o mesmo método noutro dispositivo");
  await page.getByRole("region", { name: "Ranking TOPSIS" }).waitFor();
  await pausa(page, 5500);
  await page.getByRole("radio", { name: "Cenário B" }).click();
  await legenda(page, "Cenário B: o vencedor depende das prioridades, por isso se mostra a robustez");
  await pausa(page, 6000);
  marca("fim");
  return marcas;
}

async function main() {
  const dist = join(AQUI, "..", "dist-web", "index.html");
  if (!existsSync(dist)) throw new Error("falta dist-web: correr primeiro `npm run build:web`");
  const servidor = spawn(process.execPath, [join(AQUI, "servidor.mjs"), String(PORTA)], { stdio: "ignore" });
  const pastaVideo = mkdtempSync(join(tmpdir(), "video-demo-"));
  try {
    await esperarServidor();
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: LARGURA, height: ALTURA },
      deviceScaleFactor: 1,
      locale: "pt-PT",
      colorScheme: "light",
      recordVideo: { dir: pastaVideo, size: { width: LARGURA, height: ALTURA } },
    });
    const inicioGravacao = Date.now();
    const page = await context.newPage();
    const erros = [];
    page.on("pageerror", (e) => erros.push(e.message));
    page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
    await page.goto(URL_APP);
    await page.getByRole("navigation", { name: "Ecrãs" }).waitFor();
    await pausa(page, 800);
    const corte = (Date.now() - inicioGravacao) / 1000;
    const marcas = await guiao(page);
    await context.close();
    await browser.close();
    if (erros.length) throw new Error(`erros na consola durante a gravação:\n${erros.join("\n")}`);

    const webm = readdirSync(pastaVideo).find((f) => f.endsWith(".webm"));
    if (!webm) throw new Error("o Playwright não gravou o vídeo");
    mkdirSync(dirname(SAIDA), { recursive: true });
    // corta o início em branco (antes de a aplicação aparecer) e converte para H.264, 30 imagens por segundo
    execFileSync(
      ffmpeg(),
      [
        "-y", "-loglevel", "error",
        "-ss", corte.toFixed(2),
        "-i", join(pastaVideo, webm),
        "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        "-movflags", "+faststart", "-an",
        SAIDA,
      ],
      { stdio: "inherit" },
    );
    console.log(`vídeo: ${SAIDA} (${(statSync(SAIDA).size / 1e6).toFixed(1)} MB)`);
    for (const [nome, t] of marcas) console.log(`  ${t.toFixed(1).padStart(5)} s  ${nome}`);
  } finally {
    servidor.kill();
    rmSync(pastaVideo, { recursive: true, force: true });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
