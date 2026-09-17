# Registro: projeto, task e Daily

**Carregue no passo 5 do fluxo** (registrar), depois de o corpo da nota estar escrito e antes de rodar `fmt`/`lint`. É aqui que a nota deixa de ser um arquivo solto e vira parte da rede: o projeto ganha o bullet, a task ganha o detalhe, a Daily ganha o índice.

Data de hoje sempre de `date +%F`, nunca de memória — os três registros abaixo são datados.

## Estrutura de um project
---
Cada projeto é uma **pasta** com o slug do projeto, contendo a nota principal de mesmo slug e a subpasta `tasks/`:

```
projects/langfuse-self-hosted/
├── langfuse-self-hosted.md
└── tasks/
    ├── 2026-09-05-expor-minio-no-nginx.md
    └── 2026-09-07-migrar-o-postgres-para-volume-nomeado.md
```

A nota principal tem cinco seções, na ordem do `project-template.md`: **Objetivo**, **Decisões técnicas**, **Progresso**, **Aprendizados**, **Pendências**.

Duas regras não-negociáveis:

- **Decisões técnicas e Progresso são sempre datados** (`yyyy-mm-dd`), porque os dois só fazem sentido em ordem cronológica — uma decisão de hoje pode reverter a de duas semanas atrás, e sem data ficam duas afirmações contraditórias lado a lado. Decisão: `- 2026-09-05: **decisão curta** — motivo.` Cada bullet em até 2 frases; a decisão revista não é apagada, ganha um bullet novo que diz o que mudou e por quê. Ao adicionar uma nova linha datada, adicione sempre no **fim** da seção.
- **Todo avanço vira uma task**, e o bullet de Progresso aponta pra ela: `- 2026-09-05: síntese em até 2 frases. → [[2026-09-05-expor-minio-no-nginx|Expor MinIO no nginx]]`. O bullet é o índice; o detalhe (spec, execução, validação) mora na task. Progresso que não cabe numa task — não houve trabalho, só uma constatação — normalmente é decisão técnica ou pendência, não progresso.

**Aprendizados é uma lista de links** pras notas de `lessons/` e `knowledge/` que o projeto rendeu: `- [[export-diario-do-crontab-espelha-nao-instala|Export diário do crontab espelha, não instala]]`. Nunca o conhecimento colado ali dentro — o que vale além do projeto vira nota própria e o projeto aponta. Se a seção está vazia num projeto que já rendeu várias tasks, provavelmente há aprendizado não extraído.

**Pendências** carrega o que ficou em aberto no projeto — questão sem resposta, próximo passo conhecido, dívida assumida de propósito. Item resolvido sai da lista quando vira progresso. Antes de adicionar qualquer item aqui, use a tool AskUserQuestion para validar com o usuário quais pendências entram.

O campo `updated:` do frontmatter acompanha a data de hoje a cada edição da nota principal.

## Anatomia da task
---
A nota de task vive em `projects/<slug>/tasks/` e o nome é datado: `yyyy-mm-dd-<slug-do-titulo>.md`. O campo `project:` do frontmatter leva o wikilink da nota principal.

Três seções carregam o trabalho:

- **Spec** — requisitos e critérios de aceite, normalmente derivados de uma `.spec`. Sem spec, escreva os critérios que você usaria pra dizer que a task terminou; a seção nunca fica vazia, porque é ela que torna o Resultado verificável.
- **Execução** — o que foi feito, em ordem. Comando, caminho e mensagem de erro exatos.
- **Resultado** — como ficou e **o que foi validado**, contra os critérios da Spec. "Funcionou" não é resultado; "`curl` no endpoint devolve 200 e o objeto aparece no bucket" é.

Aprendizado que apareceu durante a task e vale além dela não fica na task: vira nota em `lessons/` ou `knowledge/`, e a task e a nota principal apontam pra ela.

## Daily
---
A Daily **indexa, não guarda conhecimento**: wikilink mais uma síntese de até ~110 caracteres dizendo o que mudou — o wikilink não entra na conta, porque o comprimento dele vem do slug. Explicação de conceito, trecho de código e raciocínio longo pertencem à nota linkada — se a linha da Daily precisa de um parágrafo, o parágrafo está na nota errada.

Uma entrada tem a forma `- [[slug|Título]] — síntese.` — travessão, não hífen.

A seção sai do **tipo da nota**:

| Nota em… | Seção da Daily |
|----------|----------------|
| `projects` (nota principal ou task) | `## Projetos` |
| `lessons` e `knowledge` | `## Aprendizados` |
| `dump`, `resources` e o resto | `## Outras notas` |

**O padrão é uma linha por nota tocada**: uma interação, uma entrada — nota tocada uma vez aparece uma vez, não duas. Mas **uma segunda entrada para a mesma nota no mesmo dia é legítima quando houve interação separada e substantiva**: outra sessão, outro avanço, outro assunto dentro do mesmo projeto. O critério é ter algo diferente a dizer, não o wikilink ser inédito — wikilink repetido na Daily é comportamento normal num dia de várias conversas sobre o mesmo projeto, e a segunda linha se justifica pela síntese dela, não pelo slug. Quando o avanço é continuação do mesmo trabalho — a nota principal do projeto tocada duas ou três vezes dentro da mesma sessão —, **enriqueça a linha existente** em vez de acrescentar outra, porque duas linhas quase idênticas descrevendo o mesmo movimento não indexam nada a mais. Releia o arquivo inteiro antes de inserir justamente por isso: a releitura serve pra decidir entre enriquecer a linha que já está lá e abrir uma nova, não pra impedir repetição. A entrada nova vai no **fim** da seção, logo antes da linha em branco que antecede o próximo `##`.

Se a nota do dia não existe, ela nasce do `daily-template.md` seguindo `rules/templates.md` — o que inclui **não deixar os bullets-instrução do template no arquivo**: elas são instrução pro leitor do template, não conteúdo. Seção que recebe entrada real perde o bullet de exemplo; seção que fica sem entrada nenhuma no dia fica vazia, sem o placeholder.

A seção `## Pendentes` é de checkbox de tarefa, não de nota tocada — nenhuma entrada de nota entra ali. Ela **carrega os itens não concluídos da Daily anterior**: ao criar a Daily de hoje, leia a última Daily existente, **mova** para cá os `- [ ]` que continuam abertos. Mover, não recriar — reescrever o item de memória perde o texto original e cria duas versões do mesmo pendente em dias diferentes. Essa seção é exclusiva do usuário, **não** adicione novas linhas nela.
