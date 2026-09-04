---
name: intelect-devorer-skill
description: Captura e organiza conhecimento no vault "second brain" do Obsidian do usuário — de sessões de código, estudos, projetos e ideias — como notas atômicas, interligadas e recuperáveis, seguindo uma estrutura fixa de pastas (00 Dump, 01 Daily, 02 Projects, 03 Knowledge, 04 Resources, 05 Archives). Use esta skill sempre que o usuário quiser salvar, capturar, registrar, anotar ou arquivar algo no vault / segundo cérebro / Obsidian — por exemplo "anota isso", "salva no meu vault", "registra essa decisão do projeto", "transforma isso numa nota de conhecimento", "adiciona ao meu segundo cérebro", ou ao final de uma sessão de código/estudo que valha a pena preservar. Também vale quando se está trabalhando diretamente dentro de um diretório de vault do Obsidian. Dispare mesmo que o usuário não diga "Obsidian" explicitamente, desde que a intenção seja claramente persistir conhecimento nas notas dele.
---

# Intelect Devorer Skill

O papel desta skill não é guardar informação — é transformar informação dispersa em **conhecimento estruturado, recuperável e conectado**. O vault é uma **rede**, não uma hierarquia de pastas: na dúvida, **links importam mais que pastas**.

Todo o conteúdo das notas é em **português**. Nomes canônicos de conceitos e tecnologias ficam na forma original (*Java Streams*, *OAuth 2.0*, *PostgreSQL MVCC*) — traduzir quebraria a ligação com o conceito real. Sobre a marcação deles, ver [Nomes canônicos](#nomes-canônicos).

## Onde cada coisa vive

| Pasta | Papel | Vai pra cá quando… |
|-------|-------|--------------------|
| `00 - Dump` | captura rápida, incompleta | é um fragmento que ainda não merece lar definitivo; ponto de partida de outra nota. **Não** é destino permanente |
| `01 - Daily` | índice temporal do dia | **sempre** — toda nota criada/atualizada ganha uma menção (wikilink + descrição curta). Nunca guarda o conhecimento em si |
| `02 - Projects` | atividade com começo/meio/fim | acompanhar progresso, decisões técnicas, aprendizados de um projeto (software ou qualquer coisa mensurável) |
| `03 - Knowledge` | conceitos e aprendizados atômicos | a informação continua útil **fora** do contexto onde foi descoberta |
| `04 - Resources` | arquivos anexos (pdf, ppt, etc.) | há um arquivo a guardar. Links pra sites/blogs ficam **dentro da nota**, não aqui |
| `05 - Archives` | conteúdo depreciado | algo deixou de ser útil e sai de circulação (nunca delete por conta própria — mova) |

Não crie novas pastas de nível superior sem uma necessidade clara e recorrente.

## Templates: a fonte de verdade é o vault

A estrutura de cada tipo de nota (frontmatter e seções) é definida pelos arquivos em `<vault>/templates/` — `Daily Template.md`, `Dump Template.md`, `Knowledge Template.md`, `Project Template.md`. **Nunca** invente um layout próprio nem copie um template para dentro desta skill: sempre parta do template do vault, para que a nota criada pelo Claude seja indistinguível de uma criada pelo usuário no Obsidian.

Para obter um template já renderizado (com `created:` na data de hoje):

```bash
python3 scripts/vault.py template "<caminho-do-vault>" <daily|dump|knowledge|project>
```

Se o template do vault mudar, o comportamento acompanha — sem ajustes na skill.

## O fluxo de captura

Quando o usuário quiser persistir algo, siga este raciocínio (nem todo passo se aplica sempre — use o bom senso):

1. **Entenda e decomponha.** Uma nota responde a uma ideia específica. Se o material mistura assuntos, quebre em notas atômicas. Prefira `Java Streams`, `Java Records`, `JVM Garbage Collection` a um `Java.md` gigante — isso permite conectar conceitos com precisão.

2. **Classifique cada ideia** usando a tabela acima. O teste decisivo pra Knowledge é: *"isso continuaria útil se o projeto/contexto onde descobri deixasse de existir?"* Se sim → Knowledge. Se é detalhe específico do projeto → fica no Project.

3. **Verifique se já existe** antes de criar (evita duplicatas e variantes órfãs):

   ```bash
   python3 scripts/vault.py find "<caminho-do-vault>" "<conceito>"
   ```

   Se existe, **linke/atualize** a nota existente em vez de criar outra. O `find` também casa por `aliases`, então `OAuth2` encontra `[[OAuth 2.0]]`.

4. **Crie ou atualize a nota.** O nome do arquivo é o título da nota (`03 - Knowledge/PostgreSQL MVCC.md`); wikilinks referenciam pelo título. Parta sempre do template do vault (`python3 scripts/vault.py template <vault> <tipo>`, ou leia `<vault>/templates/` direto) e preencha os campos — `created` com a data de hoje, `aliases` quando fizer sentido. Escreva seguindo **[Como escrever](#como-escrever)**, com links no corpo pros conceitos citados. Não altere as seções nem o frontmatter definidos pelo template.

   Preencha também `tags` com o domínio da nota, reusando o vocabulário que já existe antes de inventar termo novo:

   ```bash
   python3 scripts/vault.py tags "<caminho-do-vault>"
   ```

   Sobre os campos de metadado do frontmatter: `created` e `skill_version` já vêm preenchidos pelo `vault.py template` — **não** os edite à mão. `template_version` é do vault e fica como está. Já `llm_model_used` só você sabe responder: preencha com o modelo que está escrevendo a nota (ex: `claude-opus-5`).

5. **Extraia aprendizados permanentes.** Se um projeto rendeu um aprendizado com valor além dele, crie a nota em Knowledge e faça o Project **apontar** pra ela. Não copie o conhecimento pro Project.

6. **Normalize a forma.** Depois de criar ou editar qualquer nota, rode o `fmt` nela:

   ```bash
   python3 scripts/vault.py fmt "<caminho-da-nota-ou-do-vault>"
   ```

   Ele desfaz hard wrap, insere o `---` faltante sob cada cabeçalho e normaliza as linhas em branco. Densidade textual ele não resolve — isso é julgamento seu, e está em [Como escrever](#como-escrever).

7. **Registre na Daily.** Para cada nota tocada:

   ```bash
   python3 scripts/vault.py log "<caminho-do-vault>" "<Título>" "<descrição curta>" --section <Projetos|Aprendizados|"Outras notas">
   ```

   Escolha a seção pelo tipo da nota: nota de `02 - Projects` → `Projetos`, nota de `03 - Knowledge` → `Aprendizados`, o resto → `Outras notas` (padrão). Isso cria a nota do dia a partir do `Daily Template.md` do vault se ela não existir, remove os bullets de exemplo do template e adiciona a linha sem duplicar. A Daily preserva o contexto do dia mas **não** contém o conhecimento — só o wikilink e no máximo uma linha do que mudou.

8. **Arquivos → Resources.** Se o conhecimento vem com um arquivo (pdf, ppt…), coloque-o em `04 - Resources/` e referencie a partir da nota relevante (`![[palestra.pdf]]` ou `[[palestra.pdf]]`). Links pra fontes externas ficam dentro da nota, não em Resources.

## Como escrever

A nota existe para ser **reencontrada**, não lida de ponta a ponta. Quem chega nela daqui a seis meses quer a informação em segundos — texto a mais é custo de recuperação, não generosidade.

### Densidade

Escreva como quem toma nota para si mesmo: direto, sem enfeite. Frases completas e artigos **ficam** — o alvo é prosa enxuta, não telegrama, e pronome sem antecedente claro custa mais caro que a palavra economizada. Termo técnico, número, comando e mensagem de erro vão exatos.

Corte sempre:

- **Preâmbulo** que anuncia o assunto em vez de entregá-lo: "Vale entender que…", "Neste ponto é importante notar…".
- **Meta-comentário** sobre a descoberta: "erro que quase todo mundo comete na primeira vez", "aprendi isso da forma difícil". Não é o conhecimento, é a moldura dele.
- **Hedge** (`talvez`, `de certa forma`, `costuma`, `geralmente`) quando o fato é firme. Mantenha só quando a incerteza for real e informativa.
- **Conclusão que só resume** o que os parágrafos acima já disseram.
- **Repetição do título** no corpo — o título já está no topo do arquivo.

Orçamento, como limite e não como meta: bullet de Decisão técnica ou Progresso em **até 2 frases**; entrada de Daily em **uma linha** (~120 caracteres).


### Nomes canônicos

Nome canônico de conceito ou tecnologia que **não** vira link vai em *itálico*: *Java Streams*, *OAuth 2.0*, *PostgreSQL MVCC*, *Docker*. O itálico marca "isto é o nome de uma coisa", e é o que permite varrer a nota e achar de que ela trata sem ler cada frase.

Quando o nome vira wikilink, o link já cumpre esse papel: escreva `[[OAuth 2.0]]`, nunca `*[[OAuth 2.0]]*`. Uma marcação só por nome.

Backtick continua reservado ao que é **literal de código** — comando, caminho, identificador, flag, valor de config, mensagem de erro (`docker compose up`, `~/.config/nvim`, `proxy_set_header`, `SignatureDoesNotMatch`). O critério é o uso, não a palavra: *Docker* como tecnologia vai em itálico, `docker` como comando digitado no shell vai em backtick.

### Quebra de linha

**Um parágrafo é uma linha física**, por mais longa que fique. Quem quebra a linha é o Obsidian, não você. A quebra marca **fronteira semântica**, nunca largura de tela — linha em branco entre parágrafos, item novo de lista, sub-item indentado. Só isso.

### Cabeçalho e divider

Todo cabeçalho `##` leva `---` na linha seguinte, e o conteúdo começa **imediatamente** abaixo do divider. Uma linha em branco antes do próximo cabeçalho. Vale também para os cabeçalhos que você cria fora do template — é a convenção do vault, não um detalhe dos templates.

## Princípios que guiam as decisões

**Links são mais importantes que pastas.** Sempre que uma nota tiver relação relevante com outra, crie o link (`[[PostgreSQL MVCC]]`). Não tenha medo de criar muitos links — uma nota rica em links é o objetivo, não um problema. O vault deve ser uma rede.

**Não duplique conhecimento.** Se um conceito já é (ou deveria ser) uma nota, **referencie**: escreva `O projeto usa [[OAuth 2.0]]`, e não cole a explicação inteira de OAuth dentro da nota do projeto. Antes de explicar um conceito geral dentro de um Project ou Daily, pergunte-se se ele não deveria ser uma nota de Knowledge própria.

**Notas atômicas.** Uma nota = uma ideia razoavelmente bem definida. Evite notas gigantes que tentam explicar assuntos completamente diferentes. Uma nota pode (e deve) ter muitos links.

**Tags são o eixo de domínio; links são o eixo de relação.** Os dois convivem e respondem a perguntas diferentes. O link liga *duas notas específicas* ("este projeto usa [[OAuth 2.0]]"); a tag diz *a que domínio amplo a nota pertence*, e é o que a pasta faria se o vault fosse hierárquico — só que atravessando os tipos de nota. `Runbook Homeserver` (Project) e `Docker Compose Override` (Knowledge) vivem em pastas diferentes e compartilham a tag `docker`; é ela que responde "o que eu já sei sobre Docker?".

Como taguear, na prática:

- **Toda nota de Project e Knowledge recebe tag** — de 1 a 4, no campo `tags:` do frontmatter (nunca inline no corpo). Zero tag é quase sempre erro.
- **A tag é o domínio, não o assunto da nota.** Uma nota `Docker Compose` recebe `docker`, não `docker-compose` — tag que serve a uma nota só não agrupa nada, e esse papel o próprio título já cumpre. Na dúvida, use o balde mais largo que ainda seja verdadeiro.
- **Reuse antes de inventar.** Rode `vault.py tags` e escolha do vocabulário existente; só crie tag nova quando nenhuma servir. O risco real não é ter tags demais, é ter `docker`, `containers` e `conteinerizacao` convivendo.
- **Formato:** minúsculas, sem acento, palavras ligadas por hífen — `docker`, `postgresql`, `spring-boot`, `homeserver`. (Exceção às formas canônicas: o Obsidian não aceita espaço em tag e trata caixa de forma inconsistente.)
- **Tags de status** (`revisar`, `wip`) não são permitidas — esse tipo de informação vai para a Daily.

**Frontmatter com propósito.** O frontmatter de cada tipo já vem do template do vault (`<vault>/templates/`) — respeite-o. Só adicione uma propriedade extra se ela servir a filtragem, Dataview, automação, status ou recuperação. Propriedade que não vai ser usada é ruído.

## Ciclo de vida: Dump e Archives

**Dump não é depósito permanente.** É trampolim. Quando revisitar uma nota de Dump — ou quando ela amadurecer — promova-a: transforme em nota de Knowledge ou Project apropriada, ajuste os links, e limpe o fragmento do Dump. Evite deixar informação importante apodrecendo ali.

**Archives só recebe, e só por decisão explícita.** Mova pra `05 - Archives/` o que o usuário considera depreciado — nunca delete no lugar dele. Mover o arquivo entre pastas **não quebra** os wikilinks `[[título]]` (o Obsidian resolve por nome, não por caminho), desde que o nome do arquivo continue único. Se houver colisão de nome, resolva antes de mover.

## Ao terminar

Feche o loop em uma linha: o que foi criado/atualizado, onde, e os principais links criados. Isso deixa o usuário confiar que a rede está crescendo de forma coerente — e perceber conexões que talvez queira reforçar depois.

## Referências

- `<vault>/templates/` — a fonte de verdade do layout de cada tipo de nota (frontmatter + seções). Sob controle do usuário, no próprio Obsidian. Leia (ou renderize com `vault.py template`) antes de criar/editar notas; esta skill não guarda templates próprios.
- `scripts/vault.py` — helper para localizar pastas, achar notas existentes (evitar duplicar), listar o vocabulário de tags, renderizar templates do vault, normalizar a formatação (`fmt`) e gerenciar a Daily. `python3 scripts/vault.py -h` lista os subcomandos.
