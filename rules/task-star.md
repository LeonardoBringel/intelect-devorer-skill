# Task: o método STAR

**Carregue no passo 4 do fluxo**, antes de escrever ou editar o corpo de uma nota de task, junto com `rules/escrita.md` e `rules/autossuficiencia.md`.

A task conta um trabalho do começo ao fim em quatro partes — **Situação, Tarefa, Ação, Resultado**. Quem não participou entende, só com a nota, por que o trabalho existiu, o que ele precisava entregar, o que foi feito e o que isso mudou no projeto.

## Situação
---
O contexto **antes** do trabalho: o estado do sistema, o problema ou a oportunidade, e o que provocou a task — um bug, uma pendência do projeto, um pedido. Responde *o quê, onde e por que agora*.

Até dois parágrafos. O erro clássico do STAR é gastar tempo demais aqui: detalhe que não ajuda a entender a Ação sai. O primeiro parágrafo entrega o problema, não anuncia o assunto — `list_transactions` descriptografava todas as transações do usuário para filtrar em Python, não "esta task trata de performance".

## Tarefa
---
O que a task precisava entregar e **como saber que terminou**: o objetivo, os critérios de pronto, as restrições e o que ficou fora de escopo de propósito.

Com spec, os requisitos entram traduzidos e agrupados por comportamento — o enunciado, não o id; um bullet por comportamento, não um por critério EARS. Sem spec, escreva os critérios que você usaria para dizer que a task terminou. A seção nunca fica vazia, porque é contra ela que o leitor lê o Resultado: o que foi entregue, o que mudou no caminho e o que ficou de fora.

## Ação
---
O que **foi feito**, em ordem, e o porquê das escolhas que não eram óbvias. Comando, caminho e mensagem de erro exatos, copiados da fonte.

- **O que aconteceu, não o que o plano previa.** Etapa planejada e não executada não é Ação: vai para o Resultado como o que ficou de fora.
- **Cada etapa nomeada pelo que faz**, nunca pelo número dela no plano. O hash do commit pode acompanhar a etapa como rastro.
- **Os desvios entram**: o que quebrou, o que se tentou e se abandonou, a decisão tomada no meio do caminho. É a parte que o diff não mostra e que o leitor não consegue reconstruir.
- **Trabalho de subagentes** se descreve pelo que cada frente entregou e por como as entregas convergiram, não pelo nome do agente.
- **Validar não é etapa.** Rodar testes, gate ou verificação independente não vira item da Ação.

## Resultado
---
O que o trabalho **mudou no projeto**, como resposta à Situação: o problema que ela descreveu e o que acontece agora no lugar dele. Quem lê só a Situação e o Resultado entende o que foi resolvido, como, e o que custou.

- **O efeito, antes e depois.** O comportamento que o usuário ou o sistema tinha e o que tem agora: *fechar o modal pelo X e trocar o mês não o reabre mais*. Número entra quando mede o efeito, com os dois lados — *até 12 consultas por render viraram 1*.
- **A solução em uma frase, e por que ela.** A ideia central do que foi feito, no nível do todo, e o motivo de ter sido essa e não a alternativa óbvia. O detalhe etapa por etapa é da Ação e não se repete aqui.
- **O impacto além do sintoma**: o que passa a ser possível, o que deixa de poder quebrar, o que vira contrato para o resto do projeto.
- **Consequências e trade-offs**: o que se aceitou perder, a restrição nova, o comportamento que mudou sem ter sido pedido. É a parte que o diff não conta e que o leitor mais precisa antes de mexer de novo no mesmo código.
- **O que ficou de fora** ou falhou, e para onde foi: pendência do projeto, task futura, decisão adiada com o motivo.

**Validação não é resultado.** Contagem de testes, gate verde, `pre-commit`, falhas injetadas, tag e hash de release não entram no Resultado nem em outra seção da task: provam que o trabalho está correto, não dizem o que ele mudou, e o repositório já guarda esse registro. Frase que caberia no Resultado de qualquer outra task — *134 testes passam*, *gate verde* — não diz nada sobre esta.

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
| `design.md` — alternativas descartadas, trade-offs, riscos | Resultado, como o porquê da solução e o custo aceito |
| `tasks.md` e os commits | Ação |
| verificação, testes, validação manual | nenhuma seção |
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

Errado — o Resultado de um bug de modal que reabria sozinho conta a validação, não o que mudou:
```markdown
## Resultado
---
Tag `v0.22.2` em `8575d48`, patch como previsto. Gate da rodada de validação: `pre-commit run --all-files` verde e 123 unitários passando.
```

Certo — o efeito, a solução e por que ela, o impacto e o custo:
```markdown
## Resultado
---
Fechar o Novo Registro ou o histórico de 12 meses pelo X ou pelo ESC agora vale: trocar o mês na sidebar ou voltar de Lançamentos renderiza o dashboard sem dialog aberto. A correção limpa as chaves de gatilho (`show_form`, `cat_history_open`) na entrada da página em vez de no fechamento, porque o X nativo do *Streamlit* fecha a janela sem executar código nenhum — não existe callback onde limpar.

Era a terceira página com o mesmo defeito, e a suíte passa a reprovar qualquer página que renderize dialog sem limpar o gatilho antes, então ele não volta numa página nova. A limpeza levou junto o cache `cat_hist_*`, que crescia uma entrada por mês visitado e podia servir histórico velho depois de um lançamento novo.

O custo aceito é que todo rerun completo passa a fechar o dialog aberto, não só o rerun depois de fechá-lo. Os dialogs do fluxo de caixa e do onboarding ficaram como estavam, porque já eram imunes.
```

