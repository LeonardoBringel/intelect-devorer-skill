# Task: o método STAR

**Carregue no passo 4 do fluxo**, antes de escrever ou editar o corpo de uma nota de task, junto com `rules/escrita.md` e `rules/autossuficiencia.md`.

A task conta um trabalho do começo ao fim em quatro partes — **Situação, Tarefa, Ação, Resultado**. Quem não participou entende, só com a nota, por que o trabalho existiu, o que ele precisava entregar, o que foi feito e com que evidência terminou.

## Situação
---
O contexto **antes** do trabalho: o estado do sistema, o problema ou a oportunidade, e o que provocou a task — um bug, uma pendência do projeto, um pedido. Responde *o quê, onde e por que agora*.

Até dois parágrafos. O erro clássico do STAR é gastar tempo demais aqui: detalhe que não ajuda a entender a Ação sai. O primeiro parágrafo entrega o problema, não anuncia o assunto — `list_transactions` descriptografava todas as transações do usuário para filtrar em Python, não "esta task trata de performance".

## Tarefa
---
O que a task precisava entregar e **como saber que terminou**: o objetivo, os critérios de pronto, as restrições e o que ficou fora de escopo de propósito.

Com spec, os requisitos entram traduzidos e agrupados por comportamento — o enunciado, não o id; um bullet por comportamento, não um por critério EARS. Sem spec, escreva os critérios que você usaria para dizer que a task terminou. A seção nunca fica vazia, porque é ela que torna o Resultado verificável.

## Ação
---
O que **foi feito**, em ordem, e o porquê das escolhas que não eram óbvias. Comando, caminho e mensagem de erro exatos, copiados da fonte.

- **O que aconteceu, não o que o plano previa.** Etapa planejada e não executada não é Ação: vai para o Resultado como o que ficou de fora.
- **Cada etapa nomeada pelo que faz**, nunca pelo número dela no plano. O hash do commit pode acompanhar a etapa como rastro.
- **Os desvios entram**: o que quebrou, o que se tentou e se abandonou, a decisão tomada no meio do caminho. É a parte que o diff não mostra e que o leitor não consegue reconstruir.
- **Trabalho de subagentes** se descreve pelo que cada frente entregou e por como as entregas convergiram, não pelo nome do agente.

## Resultado
---
O estado **depois** do trabalho e a evidência de cada critério da Tarefa: teste, comando, número, comparação antes e depois. "Funcionou" não é resultado; "`curl` no endpoint devolve 200 e o objeto aparece no bucket" é. Mudança mensurável vai com os dois números — *até 12 consultas por render viraram 1*.

Fecha com o que ficou de fora ou falhou e para onde foi: pendência do projeto, task futura, decisão adiada com o motivo.

## Aprendizados
---
Lista de wikilinks para as notas de `lessons/` e `knowledge/` que a task rendeu. Aprendizado que vale além da task não fica colado nela: vira nota própria, e a task e a nota principal do projeto apontam para ela.

## Da spec para o STAR
---
Quando a task veio de um fluxo *spec driven*, cada artefato alimenta uma seção — sempre traduzido, nunca referenciado (`rules/autossuficiencia.md`):

| Artefato | Alimenta |
|---|---|
| `spec.md` — problema, contexto, motivação | Situação |
| `spec.md` — requisitos, critérios de aceite, fora de escopo | Tarefa |
| `design.md` — escolhas de arquitetura | Ação, como o porquê das escolhas; Decisões técnicas do projeto, se valem além da task |
| `tasks.md` e os commits | Ação |
| verificação, testes, validação manual | Resultado |
| `STATE.md` — decisões e adiamentos | Ação ou Resultado; Pendências do projeto, se ficou algo em aberto |

## Orçamento: limite, não meta
---
- **Situação**: até dois parágrafos.
- **Tarefa**: até ~8 bullets; mais que isso é sinal de critério copiado um a um em vez de agrupado.
- **Ação**: uma etapa por item de lista numerada, cada uma em até três frases; sub-itens quando a etapa tem frentes paralelas.
- **Resultado**: até três parágrafos ou o equivalente em bullets.

## Errado / certo
---
Errado — a Situação delega o contexto à spec:
```markdown
## Situação
---
Implementação da feature de performance conforme `.specs/features/performance/spec.md`.
```

Certo — o problema e a consequência, lidos sem abrir nada:
```markdown
## Situação
---
`list_transactions` carregava e descriptografava todas as transações do usuário para depois filtrar por ano em Python, ignorando a coluna indexada `year`. O grid anual do fluxo de caixa disparava uma consulta por mês, até 12 por render.
```

Errado — a Ação identificada pelo plano:
```markdown
1. T1 (`5741b0b`): predicado no SQL.
```

Certo — a Ação identificada pelo que fez e por quê:
```markdown
1. Predicado de ano no SQL (`5741b0b`): a query ganha `.filter(Transaction.year == year)` quando `year` é passado, usando o índice `ix_transactions_user_year`. Mês e dia continuam filtrados em Python porque `date` é criptografado.
```

