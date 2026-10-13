# Autossuficiência: a nota se explica sozinha

**Carregue no passo 4 do fluxo**, junto com `rules/escrita.md`, antes de escrever ou editar qualquer nota de `projects` — nota principal ou task. É obrigatória quando o trabalho saiu de um fluxo *spec driven* (`.specs/`, `spec.md`, `design.md`, `tasks.md`, `STATE.md`), porque é aí que a tentação de apontar em vez de escrever aparece.

O vault é o registro permanente; a spec é andaime. Quem lê a nota daqui a seis meses não tem a spec aberta, talvez nem o repositório clonado — e a spec pode ter sido reescrita, apagada ou nunca versionada. Por isso **a nota lida sozinha basta**: qual era o problema, o que se pretendia, o que foi feito, por quê, e como ficou.

## A spec é fonte, não destino
---
Ler a spec para escrever a nota é o esperado; citar a spec no lugar de escrever é o erro. Tudo que a nota precisa sai da spec **traduzido** para prosa do vault:

| Na spec | Na nota do vault |
|---|---|
| id de tarefa do `tasks.md` (`T3`, `T1–T5`) | o que a etapa fez, nomeada pelo conteúdo: *a remoção do código morto* |
| id de requisito (`AUTH-01`, `CART-03`) | o requisito enunciado: *a sessão expira após 30 min sem atividade* |
| decisão registrada no `STATE.md` (`AD-009`) | a decisão e o motivo; se ela vale para o projeto, também bullet em Decisões técnicas |
| critério EARS (`WHEN … THE SYSTEM SHALL …`) | o comportamento esperado em português corrido |
| "conforme o `design.md`", "ver a spec" | o trecho do desenho que importa, em uma ou duas frases |
| vocabulário que a spec definiu (apelido de componente, nome de fase) | explicado na primeira aparição, ou trocado pelo nome comum |

O método pode ser nomeado — *planejada com a skill tlc-spec-driven* diz como o trabalho foi conduzido. O que não entra é caminho de arquivo da spec nem identificador interno dela: os dois só significam alguma coisa para quem tem a spec aberta.

## O que pode ficar como rastro
---
Rastro para artefato permanente do repositório — hash de commit, tag, link de PR, caminho de arquivo de código — pode aparecer, porque leva quem quiser ao código. A condição é **a frase se sustentar sem ele**: `A remoção do código morto apagou 192 linhas (`0800fd9`).` passa; `Ver `0800fd9`.` não passa.

## Dois testes antes de gravar
---
1. **O teste da borracha**: apague mentalmente todo identificador, caminho de spec e menção a artefato de planejamento. Se alguma frase perde o sentido ou fica sem sujeito, ela dependia da spec — reescreva com o conteúdo que o identificador escondia.
2. **O leitor de fora**: alguém que conhece a stack mas não participou da sessão entende, só com a nota, qual era o problema, o que foi feito e o que isso mudou no projeto? Se precisaria perguntar "o que é isso?", a resposta vai para a nota.


## Errado / certo
---
Errado — três referências que só a spec resolve:
```markdown
- **T5 — adiada** por `AD-009`, registrada em `STATE.md` sem commit de código.
```

Certo — a decisão, o motivo e o destino:
```markdown
- **Fallback silencioso do `decrypt()` — adiado.** Remover o retorno do token cru quando a descriptografia falha só é seguro depois de confirmar que não restam linhas legadas em texto plano no banco; sem essa confirmação, essas linhas passariam a falhar na leitura. Ficou como pendência do projeto, sem mudança de código.
```

Errado — a etapa identificada pelo número do plano:
```markdown
T1 (`a5a947b`) criou `utils/i18n.py` e `utils/locales/pt_BR.json`.
```

Certo — a etapa identificada pelo que fez, com o commit como rastro:
```markdown
A infraestrutura de tradução (`a5a947b`) criou `utils/i18n.py`, que carrega as mensagens, e `utils/locales/pt_BR.json` com os textos em português.
```

## Na nota principal do projeto
---
- **Objetivo** descreve o projeto para quem nunca viu a spec: o que ele entrega, para quem, e o limite do escopo.
- **Decisões técnicas**: decisão do `STATE.md` ou do `design.md` que importa para o projeto vira bullet com a decisão e o motivo — nunca o id dela.
- **Pendências**: item adiado ou fora de escopo na spec vira pendência dizendo o que falta decidir e do que depende.
