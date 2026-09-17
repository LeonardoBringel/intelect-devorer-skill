# Templates: como instanciar um template do vault

**Carregue no passo 3 do fluxo**, antes de escrever qualquer arquivo novo no vault: é aqui que a nota nasce certa.

O template em `<vault>/templates/` é lido por você, interpretado por você e instanciado por você — o script só confere depois, no `fmt` e no `lint`. O que era garantido por geração determinista agora depende de uma distinção que você faz na leitura: **o que no template é estrutura a manter, e o que é instrução a consumir.**

## Ler um template: estrutura versus instrução
---
O vault não marca placeholder com `{{chave}}` — os templates são notas legíveis, e a linha de exemplo tem a mesma aparência de uma linha de conteúdo. A distinção é semântica, não sintática:

| Elemento do template | O que é | O que fazer |
|---|---|---|
| Chaves do frontmatter | estrutura | manter todas, na ordem; preencher o valor |
| `## Cabeçalho` e o `---` abaixo | estrutura | copiar exatamente |
| Bullet sob um cabeçalho | **instrução** | descreve o que escrever ali; substituir por conteúdo real ou deixar a seção vazia |
| Frase de corpo solta | **instrução** | idem |

Regra operacional: **nada do corpo do template sai idêntico para a nota, exceto cabeçalho e divider.** Se uma linha do corpo do arquivo novo pode ser encontrada com `grep -F` no template, ela é placeholder sobrevivente — a única exceção são as linhas `## ...` e os `---` logo abaixo delas. O frontmatter não entra nessa conta e segue a regra da tabela — todas as chaves mantidas, na ordem, com o valor preenchido, e `type` e `template_version` copiados do template sem toque —, que é também como o `lint` audita: ele descarta o frontmatter e compara só o corpo contra o template. Seção sem conteúdo real fica com o cabeçalho, o divider e o corpo vazio; **nunca** com o bullet de exemplo.

Errado:
```markdown
## Outras notas
---
- Wikilink - síntese da adição/modificação
- Outras informações sobre o dia
```

Certo, com conteúdo:
```markdown
## Outras notas
---
- [[versionamento-do-diretorio-obsidian|Versionamento do diretório .obsidian]] — `.obsidian` entrou no repo com os plugins de fora.
```

Certo, sem conteúdo — cabeçalho, divider, linha em branco, próximo cabeçalho:
```markdown
## Outras notas
---

```

## Tipo, template e destino
---
- `project` → `project-template.md` → `projects/<slug>/<slug>.md`, mais a subpasta `projects/<slug>/tasks/` criada vazia (o `lint` reprova projeto sem ela)
- `task` → `task-template.md` → `projects/<projeto>/tasks/<yyyy-mm-dd>-<slug>.md`
- `lesson` → `lesson-template.md` → `lessons/<slug>.md`
- `knowledge` → `knowledge-template.md` → `knowledge/<slug>.md`
- `dump` → `dump-template.md` → `dump/<slug>.md`
- `daily` → `daily-template.md` → `daily/<yyyy-mm-dd>.md`

Resolva a pasta olhando o vault em vez de montar o caminho de cabeça. Liste a raiz com `ls "<vault>"` e escolha, para cada papel (`dump`, `daily`, `projects`, `lessons`, `knowledge`, `resources`, `archives`), a pasta cujo nome — sem espaços nas pontas e em minúsculas — é exatamente o papel: `Projects`, `projects` e `PROJECTS ` todos resolvem para `projects`.

O vault real hoje tem as sete pastas já no nome limpo (`archives`, `daily`, `dump`, `knowledge`, `lessons`, `projects`, `resources`, mais `templates`), então uma passada de `ls` basta: nenhum papel precisa de tradução.

Nota já existente nunca é recriada: o passo 2 do fluxo roda `vault.py find` antes, e um `find` com resultado significa editar o arquivo que voltou.

## Slug
---
Minúsculas, acento removido, todo caractere não-alfanumérico vira hífen, hífens consecutivos colapsam em um, hífen das pontas some. O título inteiro entra — sem truncar, sem tirar preposição.

- `Versionamento do diretório .obsidian` → `versionamento-do-diretorio-obsidian.md` (acento cai, o ` .` vira um hífen só)
- Daily: o nome é a data de `date +%F`, sem slug nenhum — `daily/2026-09-16.md`
- Task: data de `date +%F`, hífen, slug do título — `Expor MinIO no Nginx` vira `tasks/2026-09-16-expor-minio-no-nginx.md`. A data é prefixo do arquivo, não entra no `title`

## Frontmatter, campo a campo
---
Preencha só as chaves que o template daquele tipo traz, na ordem em que ele as traz. **Não crie chave que o template não tem** e não remova chave que ele tem — o `dump` não tem `tags`, a `daily` não tem `title`, e isso é decisão do vault.

- `type` — já vem preenchido pelo template. Não toque.
- `title` — o título humano, com acento, maiúscula e espaço: `Expor MinIO no Nginx`. É ele que aparece nos wikilinks e na Daily; o slug é só o nome do arquivo.
- `created` — a data de hoje, de `date +%F`. **Nunca muda em nota existente**, por mais que a nota seja reescrita inteira.
- `updated` — a data de hoje, de `date +%F`. Na criação é igual a `created`; em toda edição posterior passa a ser o dia da edição.
- `tags` — lista YAML em bloco, um item por linha, dois espaços de indentação. Regras na seção abaixo.
- `aliases` — só em `lesson` e `knowledge`. Zero a duas formas humanas alternativas pelas quais você procuraria a nota daqui a seis meses (`Instrução proibitiva em prompt`), no mesmo formato de lista. Sem alternativa real, deixe vazio.
- `project` — só em `task`, na forma `project: "[[slug|Título]]"`. As aspas são obrigatórias: sem elas o YAML lê `[[` como lista aninhada. O título é o `title:` da nota principal do projeto, não o slug.
- `status` — só em `task`. Fica no `todo` que o template entrega enquanto a task não terminou; task registrada depois do trabalho feito nasce `done`.
- `template_version` — do vault. Copie como está, aspas inclusive, e não incremente.
- `skill_version` — a versão desta skill: o campo `metadata.version` do frontmatter do `SKILL.md`, que você já tem em contexto. Entre aspas: `skill_version: "0.5.0"`.
- `llm_model_used` — o modelo que está escrevendo agora, sem aspas: `claude-opus-5`. Se estiver editando uma nota já existente que foi criada por um modelo diferente, atualize.

Uma data por sessão: rode `date +%F` uma vez e reuse o valor em todas as notas tocadas.

## Tags
---
De **4 a 12 tags** em cada nota de `project`, `task`, `lesson` e `knowledge`. Menos de quatro é quase sempre nota sub-tagueada; acima de doze a tag deixa de discriminar. `dump` e `daily` não têm o campo.

A tag é o **domínio**, não o assunto: a nota `docker-compose-merge-de-override` recebe `docker`, não `docker-compose`. Tag que serve a uma nota só não agrupa nada, e esse papel o título já cumpre. Na dúvida, o balde mais largo que ainda seja verdadeiro.
```bash
python3 scripts/vault.py tags "<vault>" [<termo>]
```

Formato kebab minúsculo, sem acento nem espaço: `docker`, `postgresql`, `spring-boot`, `homeserver`, `seguranca`. Tag de status (`wip`, `revisar`, `todo`) é proibida.

Exemplo completo, na task do caso central:
```yaml
tags:
  - nginx
  - minio
  - docker
  - homeserver
```
