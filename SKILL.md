---
name: intelect-devorer-skill
description: Captura e organiza conhecimento no vault "second brain" do Obsidian do usuário — de sessões de código, estudos, projetos e ideias — como notas atômicas, interligadas e recuperáveis, seguindo uma estrutura fixa de pastas (dump, daily, projects, lessons, knowledge, resources, archives). Use esta skill sempre que o usuário quiser salvar, capturar, registrar, anotar ou arquivar algo no vault / segundo cérebro / Obsidian — por exemplo "anota isso", "salva no meu vault", "registra essa decisão do projeto", "abre uma task pra isso", "transforma isso numa nota de conhecimento", "adiciona ao meu segundo cérebro", ou ao final de uma sessão de código/estudo que valha a pena preservar. Também vale quando se está trabalhando diretamente dentro de um diretório de vault do Obsidian. Dispare mesmo que o usuário não diga "Obsidian" explicitamente, desde que a intenção seja claramente persistir conhecimento nas notas dele.
---

# Intelect Devorer Skill

O papel desta skill não é guardar informação — é transformar informação dispersa em **conhecimento estruturado, recuperável e conectado**. O vault é uma **rede**, não uma hierarquia de pastas: na dúvida, **links importam mais que pastas**.

Todo o conteúdo das notas é em **português**. Nomes canônicos de conceitos e tecnologias ficam na forma original (*Java Streams*, *OAuth 2.0*, *PostgreSQL MVCC*) — traduzir quebraria a ligação com o conceito real. Sobre a marcação deles, ver [Nomes canônicos](#nomes-canônicos).

## Onde cada coisa vive

| Pasta | Papel | Vai pra cá quando… |
|-------|-------|--------------------|
| `dump` | captura rápida, incompleta | é um fragmento que ainda não merece lar definitivo; ponto de partida de outra nota. **Não** é destino permanente |
| `daily` | índice temporal do dia | **sempre** — toda nota criada/atualizada ganha uma menção (wikilink + descrição curta). Nunca guarda o conhecimento em si |
| `projects` | atividade com começo/meio/fim | acompanhar objetivo, decisões técnicas, progresso e pendências de um projeto. Cada projeto é uma **pasta**, não um arquivo |
| `lessons` | aprendizado que **nasceu de um projeto** | a descoberta veio de fazer: um bug, uma armadilha de config, um comportamento inesperado da ferramenta |
| `knowledge` | conhecimento que **nasceu de estudo** | li um artigo, estudei uma tecnologia, pesquisei um conceito — e quero documentar independente de projeto |
| `resources` | arquivos anexos (pdf, ppt, etc.) | há um arquivo a guardar. Links pra sites/blogs ficam **dentro da nota**, não aqui |
| `archives` | conteúdo depreciado | algo deixou de ser útil e sai de circulação (nunca delete por conta própria — mova) |

Não crie novas pastas de nível superior sem uma necessidade clara e recorrente.

## Nomenclatura

**Todo arquivo do vault é kebab-case**: minúsculas, sem acento, sem caractere especial, palavras ligadas por hífen. `Versionamento do diretório .obsidian` vira `versionamento-do-diretorio-obsidian.md`. Nunca digite o nome do arquivo de cabeça — derive:

```bash
python3 scripts/vault.py slug "<Título da nota>"
```

Como o nome do arquivo deixou de ser o título, **o título humano vive no campo `title:` do frontmatter**. É ele que aparece nos links e na Daily.

**Todo wikilink tem a forma `[[slug|Título]]`**: `[[docker-compose-merge-de-override|Docker Compose Merge de Override]]`. O alvo é o nome real do arquivo (não depende de alias para resolver) e o texto é o nome humano (a nota continua legível). Quando slug e título coincidem — `[[dotfiles]]` — o pipe é ruído: não escreva. O `find` já imprime a forma pronta; copie de lá em vez de montar à mão.

Exceções de nome, ambas datadas e já compatíveis com kebab: a nota de daily (`2026-09-05.md`) e a de task (`2026-09-05-expor-minio-no-nginx.md`).

## Projects: pasta, nota principal e tasks

Cada projeto é uma pasta com o slug do projeto, contendo a nota principal (mesmo slug) e a subpasta `tasks/`:

```
projects/langfuse-self-hosted/
├── langfuse-self-hosted.md
└── tasks/
    └── 2026-09-05-expor-minio-no-nginx.md
```

A nota principal tem cinco seções — **Objetivo**, **Decisões técnicas**, **Progresso**, **Aprendizados**, **Pendências** — e duas regras não-negociáveis:

- **Decisões técnicas e Progresso são sempre datados** (`yyyy-mm-dd`), porque os dois só fazem sentido em ordem cronológica: `- 2026-09-05: **decisão curta** — motivo.`
- **Todo avanço no projeto vira uma task**, e o bullet de Progresso aponta pra ela: `- 2026-09-05: síntese em até 2 frases. O bullet é o índice; o detalhe (spec, execução, validação) mora na task.

A nota de task normalmente deriva de uma `.spec`: os requisitos e critérios de aceite vão na seção **Spec**, o que foi feito vai em **Execução**, e o que foi validado em **Resultado**. Se o trabalho não tem spec, a seção Spec fica com os critérios que você usaria pra dizer que a task terminou.

**Aprendizados da nota principal é uma lista de links** pras notas de `lessons/` e `knowledge/` que o projeto rendeu — nunca o conhecimento colado ali dentro.

Criar exige o helper, que já monta pasta, `tasks/`, frontmatter e o bullet de Progresso:

```bash
python3 scripts/vault.py new "<vault>" project "<Nome do Projeto>"
python3 scripts/vault.py new "<vault>" task "<Título da task>" --project <slug-do-projeto> [--progress "<síntese do bullet>"]
```

## Lessons e Knowledge: a fonte decide

As duas pastas guardam conhecimento reutilizável; o que as separa é **de onde a descoberta veio**, não o assunto.

Estudar *Langfuse* e documentar o que a ferramenta faz é `knowledge`. Descobrir, mexendo no **seu** Langfuse, que uma variável não é repassada pelo compose oficial é `lessons`.

**Na dúvida, `knowledge` prevalece.** Se a mesma sessão rendeu as duas leituras e não está claro qual é, escreva em `knowledge` — a nota nasce menos amarrada ao contexto de um projeto, que é o que a torna reaproveitável depois.

O teste que continua valendo pras duas: *"isso continuaria útil se o projeto/contexto onde descobri deixasse de existir?"* Se não → é detalhe do projeto, fica na nota principal ou na task, não vira nota própria.

## Templates: a fonte de verdade é o vault

A estrutura de cada tipo de nota (frontmatter e seções) é definida pelos arquivos em `<vault>/templates/` — `daily-template.md`, `dump-template.md`, `project-template.md`, `task-template.md`, `lesson-template.md`, `knowledge-template.md`. **Nunca** invente um layout próprio nem copie um template para dentro desta skill: sempre parta do template do vault, para que a nota criada pelo Claude seja indistinguível de uma criada pelo usuário no Obsidian.

O `vault.py new` já parte do template certo. Para só inspecionar um template renderizado:

```bash
python3 scripts/vault.py template "<caminho-do-vault>" <daily|dump|project|task|lesson|knowledge> [--title "<Título>"]
```

Se o template do vault mudar, o comportamento acompanha — sem ajustes na skill.

## O fluxo de captura

Quando o usuário quiser persistir algo, siga este raciocínio (nem todo passo se aplica sempre — use o bom senso):

1. **Entenda e decomponha.** Uma nota responde a uma ideia específica. Se o material mistura assuntos, quebre em notas atômicas. Prefira `java-streams`, `java-records`, `jvm-garbage-collection` a um `java.md` gigante — isso permite conectar conceitos com precisão.

2. **Classifique cada ideia** pela tabela de pastas e, para conhecimento reutilizável, pela fonte.

3. **Verifique se já existe** antes de criar (evita duplicatas e variantes órfãs):

   ```bash
   python3 scripts/vault.py find "<caminho-do-vault>" "<conceito>"
   ```

   Se existe, **linke/atualize** a nota existente em vez de criar outra. O `find` casa por slug, título e `aliases`, e devolve o wikilink já na forma canônica.

4. **Crie a nota pelo helper**, nunca escrevendo o caminho à mão — ele garante slug, pasta e frontmatter corretos:

   ```bash
   python3 scripts/vault.py new "<vault>" <project|task|lesson|knowledge|dump> "<Título>" [--project <slug-do-projeto>]
   ```

5. **Preencha o conteúdo.** Escreva seguindo **[Como escrever](#como-escrever)**, com links no corpo pros conceitos citados. Não altere as seções nem o frontmatter definidos pelo template.

   Preencha `tags` com o domínio da nota, reusando o vocabulário que já existe antes de inventar termo novo:

   ```bash
   python3 scripts/vault.py tags "<caminho-do-vault>"
   ```

   Sobre os campos de metadado: `title`, `created` e `skill_version` já vêm preenchidos pelo `vault.py` — **não** os edite à mão. `template_version` é do vault e fica como está. Já `llm_model_used` só você sabe responder: preencha com o modelo que está escrevendo a nota (ex: `claude-opus-5`).

6. **Extraia aprendizados permanentes.** Se um projeto rendeu um aprendizado com valor além dele, crie a nota em `lessons/` (ou `knowledge/`, pela regra da fonte) e faça o Project **apontar** pra ela. Não copie o conhecimento pro Project.

7. **Normalize e confira.** Depois de criar ou editar qualquer nota:

   ```bash
   python3 scripts/vault.py fmt "<caminho-da-nota-ou-do-vault>"
   python3 scripts/vault.py lint "<caminho-do-vault>"
   ```

   O `fmt` desfaz hard wrap, insere o `---` faltante sob cada cabeçalho e normaliza as linhas em branco. O `lint` pega o que a forma não pega: nome fora do padrão, `title`/`tags` faltando, task sem `project`, link fora do kebab e projeto sem `tasks/`. Link para nota que ainda não existe ele reporta como `[pendente]`, não como erro — é uso legítimo do Obsidian. Densidade textual nenhum dos dois resolve: isso é julgamento seu, e está em [Como escrever](#como-escrever).

8. **Registre na Daily.** Para cada nota tocada:

   ```bash
   python3 scripts/vault.py log "<caminho-do-vault>" "<Título ou slug>" "<descrição curta>" --section <Projetos|Aprendizados|"Outras notas">
   ```

   Escolha a seção pelo tipo da nota: `projects` (nota principal ou task) → `Projetos`; `lessons` e `knowledge` → `Aprendizados`; o resto → `Outras notas` (padrão). Isso cria a nota do dia a partir do `daily-template.md` do vault se ela não existir, remove os bullets de exemplo do template e adiciona a linha sem duplicar. A Daily preserva o contexto do dia mas **não** contém o conhecimento — só o wikilink e no máximo uma linha do que mudou.

9. **Arquivos → `resources`.** Se o conhecimento vem com um arquivo (pdf, ppt…), coloque-o em `resources/` e referencie a partir da nota relevante (`![[palestra.pdf]]` ou `[[palestra.pdf]]`). Links pra fontes externas ficam dentro da nota, não em `resources`.

10. **Versione o vault.** Depois que **todas** as notas da sessão estiverem criadas, formatadas, linteadas e registradas na Daily — nunca antes:
```bash
python3 scripts/vault.py commit "<caminho-do-vault>"
```

    O commit é **um por sessão, não um por nota**: uma anotação costuma tocar a nota nova, o Project e a Daily de uma vez, e commitar cada arquivo separado quebraria em pedaços algo que só faz sentido junto. Se a sessão não mudou nada, o script diz isso e não cria commit vazio. Se o vault ainda não for um repositório git, ele avisa — não rode `git init` sem o usuário pedir.

## Como escrever

A nota existe para ser **reencontrada**, não lida de ponta a ponta. Quem chega nela daqui a seis meses quer a informação em segundos — texto a mais é custo de recuperação, não generosidade.

### Densidade

Escreva como quem toma nota para si mesmo: direto, sem enfeite. Frases completas e artigos **ficam** — o alvo é prosa enxuta, não telegrama, e pronome sem antecedente claro custa mais caro que a palavra economizada. Termo técnico, número, comando e mensagem de erro vão exatos.

Corte sempre:

- **Preâmbulo** que anuncia o assunto em vez de entregá-lo: "Vale entender que…", "Neste ponto é importante notar…".
- **Meta-comentário** sobre a descoberta: "erro que quase todo mundo comete na primeira vez", "aprendi isso da forma difícil". Não é o conhecimento, é a moldura dele.
- **Hedge** (`talvez`, `de certa forma`, `costuma`, `geralmente`) quando o fato é firme. Mantenha só quando a incerteza for real e informativa.
- **Conclusão que só resume** o que os parágrafos acima já disseram.
- **Repetição do título** no corpo — o título já está no frontmatter.

Orçamento, como limite e não como meta: bullet de Decisão técnica ou Progresso em **até 2 frases**; entrada de Daily em **uma linha** (~120 caracteres).

### Nomes canônicos

Nome canônico de conceito ou tecnologia que **não** vira link vai em *itálico*: *Java Streams*, *OAuth 2.0*, *PostgreSQL MVCC*, *Docker*. O itálico marca "isto é o nome de uma coisa", e é o que permite varrer a nota e achar de que ela trata sem ler cada frase.

Quando o nome vira wikilink, o link já cumpre esse papel: escreva `[[oauth-2-0|OAuth 2.0]]`, nunca `*[[oauth-2-0|OAuth 2.0]]*`. Uma marcação só por nome.

Backtick continua reservado ao que é **literal de código** — comando, caminho, identificador, flag, valor de config, mensagem de erro (`docker compose up`, `~/.config/nvim`, `proxy_set_header`, `SignatureDoesNotMatch`). O critério é o uso, não a palavra: *Docker* como tecnologia vai em itálico, `docker` como comando digitado no shell vai em backtick.

### Quebra de linha

**Um parágrafo é uma linha física**, por mais longa que fique. Quem quebra a linha é o Obsidian, não você. A quebra marca **fronteira semântica**, nunca largura de tela — linha em branco entre parágrafos, item novo de lista, sub-item indentado. Só isso.

### Cabeçalho e divider

Todo cabeçalho `##` leva `---` na linha seguinte, e o conteúdo começa **imediatamente** abaixo do divider. Uma linha em branco antes do próximo cabeçalho. Vale também para os cabeçalhos que você cria fora do template — é a convenção do vault, não um detalhe dos templates.

## Princípios que guiam as decisões

**Links são mais importantes que pastas.** Sempre que uma nota tiver relação relevante com outra, crie o link. Não tenha medo de criar muitos links — uma nota rica em links é o objetivo, não um problema. O vault deve ser uma rede.

**Não duplique conhecimento.** Se um conceito já é (ou deveria ser) uma nota, **referencie**: escreva `O projeto usa [[oauth-2-0|OAuth 2.0]]`, e não cole a explicação inteira de OAuth dentro da nota do projeto. Antes de explicar um conceito geral dentro de um Project ou Daily, pergunte-se se ele não deveria ser uma nota própria.

**Notas atômicas.** Uma nota = uma ideia razoavelmente bem definida. Evite notas gigantes que tentam explicar assuntos completamente diferentes. Uma nota pode (e deve) ter muitos links.

**Tags são o eixo de domínio; links são o eixo de relação.** Os dois convivem e respondem a perguntas diferentes. O link liga *duas notas específicas* ("este projeto usa [[oauth-2-0|OAuth 2.0]]"); a tag diz *a que domínio amplo a nota pertence*, e é o que a pasta faria se o vault fosse hierárquico — só que atravessando os tipos de nota. Uma nota de `projects` e uma de `lessons` compartilham a tag `docker`; é ela que responde "o que eu já sei sobre Docker?".

Como taguear, na prática:

- **Toda nota de project, task, lesson e knowledge recebe tag** — de 4 a 12, no campo `tags:` do frontmatter (nunca inline no corpo). Zero tag é quase sempre erro.
- **A tag é o domínio, não o assunto da nota.** Uma nota `docker-compose` recebe `docker`, não `docker-compose` — tag que serve a uma nota só não agrupa nada, e esse papel o próprio título já cumpre. Na dúvida, use o balde mais largo que ainda seja verdadeiro.
- **Reuse antes de inventar.** Rode `vault.py tags` e escolha do vocabulário existente; só crie tag nova quando nenhuma servir. O risco real não é ter tags demais, é ter `docker`, `containers` e `conteinerizacao` convivendo.
- **Formato:** minúsculas, sem acento, palavras ligadas por hífen — `docker`, `postgresql`, `spring-boot`, `homeserver`. (Exceção às formas canônicas: o Obsidian não aceita espaço em tag e trata caixa de forma inconsistente.)
- **Tags de status** (`revisar`, `wip`) não são permitidas — esse tipo de informação vai para a Daily.

**Frontmatter com propósito.** O frontmatter de cada tipo já vem do template do vault — respeite-o. Só adicione uma propriedade extra se ela servir a filtragem, Dataview, automação, status ou recuperação. Propriedade que não vai ser usada é ruído.

## Ciclo de vida: Dump e Archives

**Dump não é depósito permanente.** É trampolim. Quando revisitar uma nota de `dump` — ou quando ela amadurecer — promova-a: transforme na nota de `projects`, `lessons` ou `knowledge` apropriada, ajuste os links, e limpe o fragmento do Dump. Evite deixar informação importante apodrecendo ali.

**Archives só recebe, e só por decisão explícita.** Mova pra `archives/` o que o usuário considera depreciado — nunca delete no lugar dele. Mover o arquivo entre pastas **não quebra** os wikilinks (o Obsidian resolve por nome de arquivo, não por caminho), desde que o slug continue único. Se houver colisão de nome, resolva antes de mover.

## Ao terminar

Rode o `vault.py commit` e feche o loop em uma linha: o que foi criado/atualizado, onde, e os principais links criados. Isso deixa o usuário confiar que a rede está crescendo de forma coerente — e perceber conexões que talvez queira reforçar depois.

## Referências

- `<vault>/templates/` — a fonte de verdade do layout de cada tipo de nota (frontmatter + seções). Sob controle do usuário, no próprio Obsidian. Leia (ou renderize com `vault.py template`) antes de criar/editar notas; esta skill não guarda templates próprios.
- `scripts/vault.py` — helper para derivar slug, localizar pastas, achar notas existentes (evitar duplicar), criar nota nova no lugar certo, listar o vocabulário de tags, renderizar templates do vault, normalizar a formatação (`fmt`), auditar o padrão (`lint`), gerenciar a Daily e versionar o vault num commit único (`commit`). `python3 scripts/vault.py -h` lista os subcomandos.
