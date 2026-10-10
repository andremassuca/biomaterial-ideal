// Leitor de markdown mínimo (títulos, listas, parágrafos, negrito e itálico) para textos de docs/
// exportados em app.json. Não interpreta HTML: o texto entra só como texto.
import { Fragment, type ReactNode } from "react";

function emLinha(texto: string): ReactNode[] {
  // **negrito**, *itálico* e `código`
  const partes = texto.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return partes.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`")) return <code key={i}>{p.slice(1, -1)}</code>;
    if (p.startsWith("*") && p.endsWith("*") && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
    return <Fragment key={i}>{p}</Fragment>;
  });
}

/** Mostra markdown simples; `semTitulo` salta o título de nível 1. */
export function Markdown({ texto, semTitulo = true }: { texto: string; semTitulo?: boolean }) {
  const linhas = texto.replace(/\r\n/g, "\n").split("\n");
  const blocos: ReactNode[] = [];
  let lista: string[] = [];
  let paragrafo: string[] = [];

  const fecharLista = () => {
    if (lista.length) {
      blocos.push(
        <ul key={`l${blocos.length}`}>
          {lista.map((t, i) => (
            <li key={i}>{emLinha(t)}</li>
          ))}
        </ul>,
      );
      lista = [];
    }
  };
  const fecharParagrafo = () => {
    if (paragrafo.length) {
      blocos.push(<p key={`p${blocos.length}`}>{emLinha(paragrafo.join(" "))}</p>);
      paragrafo = [];
    }
  };

  for (const bruta of linhas) {
    const l = bruta.trimEnd();
    if (/^#\s/.test(l)) {
      fecharLista();
      fecharParagrafo();
      if (!semTitulo) blocos.push(<h2 key={`h${blocos.length}`}>{emLinha(l.slice(2))}</h2>);
    } else if (/^##+\s/.test(l)) {
      fecharLista();
      fecharParagrafo();
      blocos.push(<h3 key={`h${blocos.length}`}>{emLinha(l.replace(/^##+\s/, ""))}</h3>);
    } else if (/^\s*-\s/.test(l)) {
      fecharParagrafo();
      lista.push(l.replace(/^\s*-\s/, ""));
    } else if (/^\s{2,}\S/.test(l) && lista.length) {
      lista[lista.length - 1] += " " + l.trim(); // continuação de um item
    } else if (l.trim() === "") {
      fecharLista();
      fecharParagrafo();
    } else {
      fecharLista();
      paragrafo.push(l.trim());
    }
  }
  fecharLista();
  fecharParagrafo();
  return <div className="prosa text-sm text-texto">{blocos}</div>;
}
