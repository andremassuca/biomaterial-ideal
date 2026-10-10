"""Testes de scripts/verificar_referencias.py (o script carrega-se pelo caminho)."""
import importlib.util
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "verificar_referencias.py"
spec = importlib.util.spec_from_file_location("verificar_referencias", CAMINHO)
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)


def test_citacoes_reconhece_as_formas_usadas():
    t = ("(Higuchi et al. 2019, por radiografia; Teeter et al. 2017) e Hu e Yoon 2018; NJR 2026; "
         "Higuchi et al. 2019 de novo; o Absorb 2017 não é citação")
    assert vr.citacoes(t, {"NJR 2026"}) == ["Higuchi 2019", "Teeter 2017", "Hu 2018", "NJR 2026"]
    assert "Absorb 2017" in vr.citacoes(t)  # sem lista de chaves, conta tudo


def test_rotulo_segue_o_numero_de_autores():
    assert vr.rotulo("Ashby, M. F. (2017). Livro.") == "Ashby"
    assert vr.rotulo("Hu, C. Y., e Yoon, T.-R. (2018). Título.") == "Hu e Yoon"
    assert vr.rotulo("Nikam, N., Steinberg, T. B., e Steinberg, D. H. (2014). Título.") == "Nikam et al."
    assert vr.rotulo("National Joint Registry [NJR]. (2026). Relatório.") == "NJR"


def test_citar_apa_dentro_e_fora_de_parenteses():
    refs = {"Teeter 2017": "Teeter, M. G., Yuan, X., e Somerville, L. E. (2017). T.",
            "Higuchi 2019": "Higuchi, Y., e Seki, T. (2019). T."}
    texto, citadas = vr.citar_apa("(Higuchi et al. 2019, por radiografia; Teeter et al. 2017) e Teeter et al. 2017; "
                                  "Smith 2000", refs)
    assert texto == ("(Higuchi e Seki, 2019, por radiografia; Teeter et al., 2017) e Teeter et al. (2017); "
                     "Smith 2000")
    assert citadas == ["Higuchi 2019", "Teeter 2017"]


def test_verificar_compara_textos_e_lista(tmp_path):
    (tmp_path / "introducao_rascunho.md").write_text("Ver Jahan et al. 2010 e Silva et al. 2002.", encoding="utf-8")
    refs = tmp_path / "refs.md"
    refs.write_text("- [Jahan 2010] Jahan A. Título.\n- [Ashby 2017] Ashby MF. Livro.\n", encoding="utf-8")
    sem_ref, nao_citadas = vr.verificar(tmp_path, refs)
    assert sem_ref == ["Silva 2002"] and nao_citadas == ["Ashby 2017"]


def test_lista_do_relatorio_cobre_todas_as_citacoes_e_so_as_citadas():
    sem_ref, nao_citadas = vr.verificar()
    assert sem_ref == [] and nao_citadas == []


def test_ano_entre_parenteses_tambem_conta():
    refs = {"Petković 2025": "Petković, D. L., Madić, M. J., e Mitković, M. M. (2025). T."}
    assert vr.citacoes("segundo Petković et al. (2025), o método", set(refs)) == ["Petković 2025"]
    texto, _ = vr.citar_apa("segundo Petković et al. (2025), o método", refs)
    assert texto == "segundo Petković et al. (2025), o método"
