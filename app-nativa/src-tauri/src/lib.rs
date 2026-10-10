//! Comandos Tauri que ligam a interface ao núcleo de cálculo (crate `mcdm`).
//!
//! Os dados dos cinco casos entram no executável na compilação (app-nativa/dados/caso_*.json, gerados por
//! scripts/exportar_app_json.py); não se lê nem se grava nada no disco. O comportamento dos métodos é o do
//! núcleo, testado contra o Python; aqui só se preparam os pedidos (pesos, η, exclusões) e se resumem as
//! respostas.

use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use mcdm::metodos::{avaliar, avaliar_com_pesos, Metodo};
use mcdm::monte_carlo::{monte_carlo_com_progresso, OpcoesMonteCarlo, Variar};
use mcdm::perfis::{avaliar_perfil, excluir, Perfil, ResultadoPerfil};
use mcdm::pesos::{combinar_pesos, pesos_desvio_padrao, renormalizar};
use mcdm::{Caso, Problema, Ranking};
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, State};

/// Os casos, pelo nome usado na interface, com o JSON embutido no executável.
const DADOS: [(&str, &str); 5] = [
    ("Haste", include_str!("../../dados/caso_haste.json")),
    ("Stent", include_str!("../../dados/caso_stent.json")),
    ("Scaffold", include_str!("../../dados/caso_scaffold.json")),
    ("Par articular", include_str!("../../dados/caso_par_articular.json")),
    ("Implante dentário", include_str!("../../dados/caso_implante_dentario.json")),
];

/// Limite de iterações do Monte Carlo pedido pela interface (proteção contra pedidos absurdos).
const MAX_ITERACOES: usize = 1_000_000;

/// Estado partilhado: os casos lidos no arranque e o sinal de "parar" do Monte Carlo.
pub struct Estado {
    casos: BTreeMap<String, Caso>,
    parar: Arc<AtomicBool>,
}

impl Estado {
    /// Lê os cinco casos embutidos; falha se algum JSON não for válido.
    pub fn carregar() -> Result<Estado, mcdm::Erro> {
        let mut casos = BTreeMap::new();
        for (nome, texto) in DADOS {
            casos.insert(nome.to_string(), Caso::de_json(texto)?);
        }
        Ok(Estado { casos, parar: Arc::new(AtomicBool::new(false)) })
    }

    fn caso(&self, nome: &str) -> Result<&Caso, String> {
        self.casos.get(nome).ok_or_else(|| format!("caso desconhecido: {nome}"))
    }
}

fn texto_erro(e: mcdm::Erro) -> String {
    e.0
}

/// Pedido de ranking de um caso: cenário, pesos ajustados (opcional), η (opcional) e materiais a excluir
/// (filtros de RM, ISO 10993-1 ou esterilização).
#[derive(Debug, Clone, Deserialize)]
pub struct PedidoCaso {
    pub caso: String,
    pub cenario: String,
    #[serde(default)]
    pub pesos: Option<Vec<f64>>,
    #[serde(default)]
    pub eta: Option<f64>,
    #[serde(default)]
    pub excluir: Vec<String>,
}

/// Prepara o problema de um pedido: pesos do utilizador (renormalizados), exclusões e, por fim, η.
///
/// Em linguagem simples: parte do problema do cenário, troca os pesos pelos dos cursores (se os houver),
/// tira os materiais excluídos pelos filtros e, se η < 1, mistura os pesos com os pesos objetivos
/// (desvio-padrão) calculados sobre os materiais que ficam. Devolve o problema e os materiais que saíram.
pub fn preparar(caso: &Caso, pedido: &PedidoCaso) -> Result<(Problema, Vec<String>), String> {
    let mut p = caso.problema(&pedido.cenario).map_err(texto_erro)?.clone();
    if let Some(w) = &pedido.pesos {
        if w.len() != p.n() {
            return Err(format!("são precisos {} pesos e chegaram {}", p.n(), w.len()));
        }
        if w.iter().any(|v| !v.is_finite() || *v < 0.0) || w.iter().sum::<f64>() <= 0.0 {
            return Err("os pesos têm de ser positivos ou zero, e não podem ser todos zero".into());
        }
        p.pesos = renormalizar(w);
    }
    let excluidos = if pedido.excluir.is_empty() {
        Vec::new()
    } else {
        excluir(&mut p, &pedido.excluir).map_err(texto_erro)?
    };
    if let Some(eta) = pedido.eta {
        if eta < 1.0 {
            let objetivos = pesos_desvio_padrao(&p.x_tipico, &p.tipos).map_err(texto_erro)?;
            p.pesos = combinar_pesos(&p.pesos, &objetivos, eta).map_err(texto_erro)?;
        }
    }
    Ok((p, excluidos))
}

/// Resposta de um ranking: o problema usado (com os pesos finais), as pontuações e posições, e os excluídos.
#[derive(Debug, Clone, Serialize)]
pub struct RespostaCaso {
    pub problema: Problema,
    pub ranking: Ranking,
    pub excluidos: Vec<String>,
}

/// TOPSIS, WASPAS, VIKOR e Borda de um caso, com os pesos, o η e as exclusões do pedido.
#[tauri::command]
fn avaliar_caso(pedido: PedidoCaso, estado: State<'_, Estado>) -> Result<RespostaCaso, String> {
    let caso = estado.caso(&pedido.caso)?;
    let (problema, excluidos) = preparar(caso, &pedido)?;
    let ranking = avaliar_com_pesos(&problema, &problema.pesos);
    Ok(RespostaCaso { problema, ranking, excluidos })
}

/// Pedido do fluxo do doente: caso, cenário e dados do doente (nome do dado -> número ou texto).
#[derive(Debug, Clone, Deserialize)]
pub struct PedidoDoente {
    pub caso: String,
    pub cenario: String,
    pub perfil: Perfil,
}

/// Caso de base e resultado com o perfil, para a comparação lado a lado e a lista "o que mudou".
#[derive(Debug, Clone, Serialize)]
pub struct RespostaDoente {
    pub base_problema: Problema,
    pub base: Ranking,
    pub resultado: ResultadoPerfil,
}

/// Aplica as regras de data/perfis_doente.csv ao caso e devolve o caso de base e o resultado do doente.
#[tauri::command]
fn avaliar_doente(pedido: PedidoDoente, estado: State<'_, Estado>) -> Result<RespostaDoente, String> {
    let caso = estado.caso(&pedido.caso)?;
    let base_problema = caso.problema(&pedido.cenario).map_err(texto_erro)?.clone();
    let base = avaliar(&base_problema);
    let resultado = avaliar_perfil(caso, &pedido.perfil, &pedido.cenario).map_err(texto_erro)?;
    Ok(RespostaDoente { base_problema, base, resultado })
}

/// Pedido de Monte Carlo: o mesmo que um ranking, mais o número de iterações e o que varia.
#[derive(Debug, Clone, Deserialize)]
pub struct PedidoMonteCarlo {
    #[serde(flatten)]
    pub base: PedidoCaso,
    pub n_iter: usize,
    /// "propriedades" ou "pesos".
    pub variar: String,
    #[serde(default)]
    pub spread: Option<f64>,
    #[serde(default)]
    pub semente: Option<u64>,
}

/// Evento de progresso enviado à interface (nome "mc-progresso").
#[derive(Debug, Clone, Serialize)]
struct Progresso {
    feitas: usize,
    total: usize,
}

/// Resumo de um método no Monte Carlo: % em 1.º, % em 2.º e posição média de cada material.
#[derive(Debug, Clone, Serialize)]
pub struct ResumoMetodo {
    pub metodo: String,
    pub pct_primeiro: Vec<f64>,
    pub pct_segundo: Vec<f64>,
    pub posicao_media: Vec<f64>,
}

/// Resumo do Monte Carlo; `parado` é verdadeiro se a interface mandou parar antes do fim.
#[derive(Debug, Clone, Serialize)]
pub struct ResumoMonteCarlo {
    pub alternativas: Vec<String>,
    pub pedidas: usize,
    pub feitas: usize,
    pub parado: bool,
    pub metodos: Vec<ResumoMetodo>,
}

/// Converte o texto da interface no tipo do núcleo.
fn ler_variar(texto: &str) -> Result<Variar, String> {
    match texto {
        "propriedades" => Ok(Variar::Propriedades),
        "pesos" => Ok(Variar::Pesos),
        outro => Err(format!("o Monte Carlo varia \"propriedades\" ou \"pesos\", não {outro:?}")),
    }
}

/// Opções do núcleo a partir do pedido; a incerteza dos valores únicos vem de data/parametros.csv.
fn opcoes(caso: &Caso, pedido: &PedidoMonteCarlo) -> Result<OpcoesMonteCarlo, String> {
    if pedido.n_iter < 1 || pedido.n_iter > MAX_ITERACOES {
        return Err(format!("o número de iterações tem de estar entre 1 e {MAX_ITERACOES}"));
    }
    let omissao = OpcoesMonteCarlo::default();
    Ok(OpcoesMonteCarlo {
        n_iter: pedido.n_iter,
        semente: pedido.semente.unwrap_or(omissao.semente),
        variar: ler_variar(&pedido.variar)?,
        spread: pedido.spread.unwrap_or(omissao.spread),
        incerteza_valor_unico: caso.parametro("incerteza_valor_unico", omissao.incerteza_valor_unico),
    })
}

/// Monte Carlo com progresso (cerca de 100 eventos) e paragem a pedido; corre fora da linha da interface.
#[tauri::command]
async fn monte_carlo(
    pedido: PedidoMonteCarlo,
    app: AppHandle,
    estado: State<'_, Estado>,
) -> Result<ResumoMonteCarlo, String> {
    let (problema, op) = {
        let caso = estado.caso(&pedido.base.caso)?;
        let (problema, _) = preparar(caso, &pedido.base)?;
        (problema, opcoes(caso, &pedido)?)
    };
    let parar = estado.parar.clone();
    parar.store(false, Ordering::SeqCst);
    let total = op.n_iter;
    let passo = (total / 100).max(1);
    let app_calculo = app.clone();
    let resultado = tauri::async_runtime::spawn_blocking(move || {
        monte_carlo_com_progresso(&problema, &op, |k| {
            if k % passo == 0 {
                let _ = app_calculo.emit("mc-progresso", Progresso { feitas: k, total });
            }
            !parar.load(Ordering::Relaxed)
        })
    })
    .await
    .map_err(|e| format!("o cálculo foi interrompido: {e}"))?
    .map_err(texto_erro)?;
    let feitas = resultado.n_iter();
    let _ = app.emit("mc-progresso", Progresso { feitas, total });
    let metodos = Metodo::TODOS
        .iter()
        .map(|&m| ResumoMetodo {
            metodo: m.nome().to_string(),
            pct_primeiro: resultado.pct_posicao(m, 1),
            pct_segundo: resultado.pct_posicao(m, 2),
            posicao_media: resultado.posicao_media(m),
        })
        .collect();
    Ok(ResumoMonteCarlo { alternativas: resultado.alternativas.clone(), pedidas: total, feitas, parado: feitas < total, metodos })
}

/// Botão "parar" do Monte Carlo.
#[tauri::command]
fn parar_monte_carlo(estado: State<'_, Estado>) {
    estado.parar.store(true, Ordering::SeqCst);
}

/// Ponto de entrada da aplicação (Windows e, mais tarde, Android).
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let estado = Estado::carregar().expect("os dados dos casos (app-nativa/dados) não são válidos");
    tauri::Builder::default()
        .manage(estado)
        .invoke_handler(tauri::generate_handler![avaliar_caso, avaliar_doente, monte_carlo, parar_monte_carlo])
        .run(tauri::generate_context!())
        .expect("não foi possível iniciar a aplicação");
}

#[cfg(test)]
mod testes {
    use super::*;

    fn pedido(caso: &str, cenario: &str) -> PedidoCaso {
        PedidoCaso { caso: caso.into(), cenario: cenario.into(), pesos: None, eta: None, excluir: Vec::new() }
    }

    #[test]
    fn carrega_os_cinco_casos() {
        let e = Estado::carregar().unwrap();
        for (nome, _) in DADOS {
            assert!(e.caso(nome).is_ok(), "{nome}");
        }
        assert!(e.caso("Outro").is_err());
    }

    #[test]
    fn preparar_sem_alteracoes_da_o_caso_de_base() {
        let e = Estado::carregar().unwrap();
        let caso = e.caso("Stent").unwrap();
        let (p, sai) = preparar(caso, &pedido("Stent", "A")).unwrap();
        assert_eq!(&p, caso.problema("A").unwrap());
        assert!(sai.is_empty());
        assert_eq!(avaliar_com_pesos(&p, &p.pesos), avaliar(caso.problema("A").unwrap()));
    }

    #[test]
    fn preparar_renormaliza_pesos_e_exclui() {
        let e = Estado::carregar().unwrap();
        let caso = e.caso("Stent").unwrap();
        let n = caso.problema("B").unwrap().n();
        let mut ped = pedido("Stent", "B");
        ped.pesos = Some(vec![2.0; n]);
        ped.excluir = vec!["PLLA (bioabsorvível)".into()];
        let (p, sai) = preparar(caso, &ped).unwrap();
        assert!(p.pesos.iter().all(|w| (w - 1.0 / n as f64).abs() < 1e-12));
        assert_eq!(sai, vec!["PLLA (bioabsorvível)".to_string()]);
        assert!(!p.alternativas.contains(&"PLLA (bioabsorvível)".to_string()));
        ped.pesos = Some(vec![1.0; n - 1]);
        assert!(preparar(caso, &ped).is_err());
        ped.pesos = Some(vec![0.0; n]);
        assert!(preparar(caso, &ped).is_err());
    }

    #[test]
    fn eta_mistura_pesos_objetivos() {
        let e = Estado::carregar().unwrap();
        let caso = e.caso("Haste").unwrap();
        let mut ped = pedido("Haste", "A");
        ped.eta = Some(0.0);
        let (p, _) = preparar(caso, &ped).unwrap();
        let base = caso.problema("A").unwrap();
        let obj = pesos_desvio_padrao(&base.x_tipico, &base.tipos).unwrap();
        assert!(p.pesos.iter().zip(&obj).all(|(a, b)| (a - b).abs() < 1e-12));
    }

    #[test]
    fn opcoes_validam_iteracoes_e_variar() {
        let e = Estado::carregar().unwrap();
        let caso = e.caso("Stent").unwrap();
        let mut ped = PedidoMonteCarlo { base: pedido("Stent", "A"), n_iter: 100, variar: "pesos".into(), spread: None, semente: None };
        let op = opcoes(caso, &ped).unwrap();
        assert_eq!(op.variar, Variar::Pesos);
        assert_eq!(op.incerteza_valor_unico, caso.parametro("incerteza_valor_unico", 0.0));
        ped.n_iter = 0;
        assert!(opcoes(caso, &ped).is_err());
        ped.n_iter = 10;
        ped.variar = "outro".into();
        assert!(opcoes(caso, &ped).is_err());
    }
}
