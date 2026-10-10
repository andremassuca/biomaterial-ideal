//! Perfis de doente em Rust contra results/perfis_referencia.csv (gerado por scripts/run_all.py
//! com src/biomat_mcdm/perfis.py): pontuações até 1e-6, posições, pesos e regras aplicadas.

mod comum;

use std::collections::{BTreeMap, HashMap};

use comum::{ler_caso, ler_csv, raiz};
use mcdm::perfis::{avaliar_perfil, Perfil, ValorPerfil};

const TOL: f64 = 1e-6;

fn num(l: &HashMap<String, String>, c: &str) -> f64 {
    l[c].parse().unwrap_or_else(|_| panic!("{c} não é número: {:?}", l[c]))
}

#[test]
fn perfis_iguais_ao_python() {
    let f = raiz().join("results").join("perfis_referencia.csv");
    let texto = std::fs::read_to_string(&f)
        .unwrap_or_else(|e| panic!("{}: {e}; corra python scripts/run_all.py", f.display()));
    let linhas = ler_csv(&texto);
    let mut por_perfil: BTreeMap<String, Vec<&HashMap<String, String>>> = BTreeMap::new();
    for l in &linhas {
        por_perfil.entry(l["perfil"].clone()).or_default().push(l);
    }
    assert!(por_perfil.len() >= 6, "faltam perfis de referência");
    for (pid, ls) in &por_perfil {
        let caso = ler_caso(&ls[0]["caso"]);
        let perfil = &caso.perfis_referencia.get(pid).unwrap_or_else(|| panic!("{pid} não está no JSON do caso")).perfil;
        let res = avaliar_perfil(&caso, perfil, &ls[0]["cenario"]).unwrap();
        let ids: Vec<&str> = res.regras.iter().map(|r| r.id.as_str()).collect();
        assert_eq!(ids.join("; "), ls[0]["regras"], "{pid}: regras");
        assert_eq!(res.excluidos.join("; "), ls[0]["excluidos"], "{pid}: excluídos");
        assert_eq!(res.notas.join("; "), ls[0]["notas"], "{pid}: notas");
        let pesos: BTreeMap<String, f64> = serde_json::from_str(&ls[0]["pesos"]).unwrap();
        for (c, w) in res.problema.criterios.iter().zip(&res.problema.pesos) {
            assert!((w - pesos[c]).abs() <= 1e-9, "{pid}: peso de {c}: {w} vs {}", pesos[c]);
        }
        assert_eq!(res.ranking.alternativas.len(), ls.len(), "{pid}: número de materiais");
        for l in ls {
            let i = res.ranking.alternativas.iter().position(|a| *a == l["material"]).expect("material");
            let k = &res.ranking;
            for (rot, rust, py) in [("C", k.c_topsis[i], num(l, "C_TOPSIS")), ("Q", k.q_waspas[i], num(l, "Q_WASPAS")),
                                    ("P", k.p_vikor[i], num(l, "P_VIKOR"))] {
                assert!((rust - py).abs() <= TOL, "{pid} {} {rot}: Rust {rust} vs Python {py}", l["material"]);
            }
            for (rot, rust) in [("pos_TOPSIS", k.pos_topsis[i]), ("pos_WASPAS", k.pos_waspas[i]),
                                ("pos_VIKOR", k.pos_vikor[i]), ("pos_Borda", k.pos_borda[i])] {
                assert_eq!(rust as f64, num(l, rot), "{pid} {} {rot}", l["material"]);
            }
        }
        // comparação com o caso de base (perfil vazio)
        let base = avaliar_perfil(&caso, &Perfil::new(), &ls[0]["cenario"]).unwrap();
        for l in ls {
            let i = base.ranking.alternativas.iter().position(|a| *a == l["material"]).unwrap();
            assert_eq!(base.ranking.pos_borda[i] as f64, num(l, "pos_ref_Borda"), "{pid} pos_ref_Borda");
        }
    }
}

#[test]
fn niquel_no_cenario_b_funciona_e_suspeita_de_titanio_so_da_nota() {
    // PLLA e Mg WE43 com 0 % de níquel: o WASPAS usa a eq. 11 com T = 0 e o perfil funciona no cenário B
    let stent = ler_caso("Stent");
    let p: Perfil = [("alergia_niquel".to_string(), ValorPerfil::Texto("sim".into()))].into_iter().collect();
    let r = avaliar_perfil(&stent, &p, "B").unwrap();
    assert!(r.ranking.q_waspas.iter().all(|q| q.is_finite()));
    let dent = ler_caso("Implante dentário");
    let s: Perfil = [("hipersens_titanio_suspeita".to_string(), ValorPerfil::Texto("sim".into()))].into_iter().collect();
    let r = avaliar_perfil(&dent, &s, "A").unwrap();
    assert_eq!(r.notas, vec!["recomenda-se avaliação clínica; testes pouco fiáveis".to_string()]);
    assert!(r.excluidos.is_empty());
    assert_eq!(r.ranking, avaliar_perfil(&dent, &Perfil::new(), "A").unwrap().ranking);
}

#[test]
fn sem_regra_para_o_sexo() {
    let haste = ler_caso("Haste");
    let p: Perfil = [("sexo".to_string(), ValorPerfil::Texto("F".into()))].into_iter().collect();
    assert!(avaliar_perfil(&haste, &p, "A").unwrap().regras.is_empty());
}
