---
name: intelect-devorer-skill
description: Captura e organiza conhecimento no vault "second brain" do Obsidian do usuário — de sessões de código, estudos, projetos e ideias — como notas atômicas, interligadas e recuperáveis, seguindo uma estrutura fixa de pastas (00 Dump, 01 Daily, 02 Projects, 03 Knowledge, 04 Resources, 05 Archives). Use esta skill sempre que o usuário quiser salvar, capturar, registrar, anotar ou arquivar algo no vault / segundo cérebro / Obsidian — por exemplo "anota isso", "salva no meu vault", "registra essa decisão do projeto", "transforma isso numa nota de conhecimento", "adiciona ao meu segundo cérebro", ou ao final de uma sessão de código/estudo que valha a pena preservar. Também vale quando se está trabalhando diretamente dentro de um diretório de vault do Obsidian. Dispare mesmo que o usuário não diga "Obsidian" explicitamente, desde que a intenção seja claramente persistir conhecimento nas notas dele.
---

# Intelect Devorer Skill

O papel desta skill não é só guardar informação. É ajudar a transformar
informação dispersa em **conhecimento estruturado, recuperável e conectado**. O
vault é uma **rede de conhecimento**, não uma hierarquia rígida de pastas — por
isso, na dúvida, **links importam mais que pastas**.

Todo o conteúdo das notas é em **português**. Nomes canônicos de conceitos e
tecnologias ficam na forma original (`Java Streams`, `OAuth 2.0`,
`PostgreSQL MVCC`) — traduzir quebraria a ligação com o conceito real.

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

A estrutura de cada tipo de nota (frontmatter e seções) é definida pelos
arquivos em `<vault>/templates/` — `Daily Template.md`, `Dump Template.md`,
`Knowledge Template.md`, `Project Template.md`. **Nunca** invente um layout
próprio nem copie um template para dentro desta skill: sempre parta do template
do vault, para que a nota criada pelo Claude seja indistinguível de uma criada
pelo usuário no Obsidian.

Para obter um template já renderizado (com `created:` na data de hoje):

```bash
python3 scripts/vault.py template "<caminho-do-vault>" <daily|dump|knowledge|project>
```

Se o template do vault mudar, o comportamento acompanha — sem ajustes na skill.

## O fluxo de captura

Quando o usuário quiser persistir algo, siga este raciocínio (nem todo passo se
aplica sempre — use o bom senso):

1. **Entenda e decomponha.** Uma nota deve responder a uma ideia específica. Se
   o material mistura assuntos, quebre em notas atômicas. Prefira
   `Java Streams`, `Java Records`, `JVM Garbage Collection` a um `Java.md`
   gigante — isso permite conectar conceitos com precisão.

2. **Classifique cada ideia** usando a tabela acima. O teste decisivo pra
   Knowledge é: *"isso continuaria útil se o projeto/contexto onde descobri
   deixasse de existir?"* Se sim → Knowledge. Se é detalhe específico do
   projeto → fica no Project.

3. **Verifique se já existe** antes de criar (evita duplicatas e variantes
   órfãs):

   ```bash
   python3 scripts/vault.py find "<caminho-do-vault>" "<conceito>"
   ```

   Se existe, **linke/atualize** a nota existente em vez de criar outra. O
   `find` também casa por `aliases`, então `OAuth2` encontra `[[OAuth 2.0]]`.

4. **Crie ou atualize a nota.** O nome do arquivo é o título da nota
   (`03 - Knowledge/PostgreSQL MVCC.md`); wikilinks referenciam pelo título.
   Parta sempre do template do vault (`python3 scripts/vault.py template <vault>
   <tipo>`, ou leia `<vault>/templates/` direto) e preencha os campos —
   `created` com a data de hoje, `aliases` quando fizer sentido. Escreva prosa
   em português, com links no corpo pros conceitos citados. Não altere as
   seções nem o frontmatter definidos pelo template.

   Preencha também `tags` com o domínio da nota, reusando o vocabulário que já
   existe antes de inventar termo novo:

   ```bash
   python3 scripts/vault.py tags "<caminho-do-vault>"
   ```

5. **Extraia aprendizados permanentes.** Se um projeto rendeu um aprendizado com
   valor além dele, crie a nota em Knowledge e faça o Project **apontar** pra
   ela. Não copie o conhecimento pro Project.

6. **Registre na Daily.** Para cada nota tocada:

   ```bash
   python3 scripts/vault.py log "<caminho-do-vault>" "<Título>" "<descrição curta>" --section <Projetos|Aprendizados|Outros>
   ```

   Escolha a seção pelo tipo da nota: nota de `02 - Projects` → `Projetos`,
   nota de `03 - Knowledge` → `Aprendizados`, o resto → `Outros` (padrão). Isso
   cria a nota do dia a partir do `Daily Template.md` do vault se ela não
   existir, remove os bullets de exemplo do template e adiciona a linha sem
   duplicar. A Daily preserva o contexto do dia mas **não** contém o
   conhecimento — só o wikilink e no máximo uma linha do que mudou.

7. **Arquivos → Resources.** Se o conhecimento vem com um arquivo (pdf, ppt…),
   coloque-o em `04 - Resources/` e referencie a partir da nota relevante
   (`![[palestra.pdf]]` ou `[[palestra.pdf]]`). Links pra fontes externas ficam
   dentro da nota, não em Resources.

## Princípios que guiam as decisões

**Links são mais importantes que pastas.** Sempre que uma nota tiver relação
relevante com outra, crie o link (`[[PostgreSQL MVCC]]`). Não tenha medo de
criar muitos links — uma nota rica em links é o objetivo, não um problema. O
vault deve ser uma rede.

**Não duplique conhecimento.** Se um conceito já é (ou deveria ser) uma nota,
**referencie**: escreva `O projeto usa [[OAuth 2.0]]`, e não cole a explicação
inteira de OAuth dentro da nota do projeto. Antes de explicar um conceito geral
dentro de um Project ou Daily, pergunte-se se ele não deveria ser uma nota de
Knowledge própria — quase sempre deveria.

**Notas atômicas.** Uma nota = uma ideia razoavelmente bem definida. Evite notas
gigantes que tentam explicar assuntos completamente diferentes. Uma nota pode
(e deve) ter muitos links.

**Tags são o eixo de domínio; links são o eixo de relação.** Os dois convivem e
respondem a perguntas diferentes. O link liga *duas notas específicas* ("este
projeto usa [[OAuth 2.0]]"); a tag diz *a que domínio amplo a nota pertence*, e
é o que a pasta faria se o vault fosse hierárquico — só que atravessando os
tipos de nota. `Runbook Homeserver` (Project) e `Docker Compose Override`
(Knowledge) vivem em pastas diferentes e compartilham a tag `docker`; é ela que
responde "o que eu já sei sobre Docker?".

Como taguear, na prática:

- **Toda nota de Project e Knowledge recebe tag** — de 1 a 4, no campo `tags:`
  do frontmatter (nunca inline no corpo). Zero tag é quase sempre erro.
- **A tag é o domínio, não o assunto da nota.** Uma nota `Docker Compose` recebe
  `docker`, não `docker-compose` — tag que serve a uma nota só não agrupa nada,
  e esse papel o próprio título já cumpre. Na dúvida, use o balde mais largo que
  ainda seja verdadeiro.
- **Reuse antes de inventar.** Rode `vault.py tags` e escolha do vocabulário
  existente; só crie tag nova quando nenhuma servir. O risco real não é ter
  tags demais, é ter `docker`, `containers` e `conteinerizacao` convivendo.
- **Formato:** minúsculas, sem acento, palavras ligadas por hífen — `docker`,
  `postgresql`, `spring-boot`, `homeserver`. (Exceção às formas canônicas: o
  Obsidian não aceita espaço em tag e trata caixa de forma inconsistente.)
- Tags de **status** (`revisar`, `wip`) não são permitidas, esse tipo de informação deve ir para Daily

**Frontmatter com propósito.** O frontmatter de cada tipo já vem do template do
vault (`<vault>/templates/`) — respeite-o. Só adicione uma propriedade extra se
ela servir a filtragem, Dataview, automação, status ou recuperação. Propriedade
que não vai ser usada é ruído.

## Ciclo de vida: Dump e Archives

**Dump não é depósito permanente.** É trampolim. Quando revisitar uma nota de
Dump — ou quando ela amadurecer — promova-a: transforme em nota de Knowledge ou
Project apropriada, ajuste os links, e limpe o fragmento do Dump. Evite deixar
informação importante apodrecendo ali.

**Archives só recebe, e só por decisão explícita.** Mova pra `05 - Archives/` o
que o usuário considera depreciado — nunca delete no lugar dele. Mover o arquivo
entre pastas **não quebra** os wikilinks `[[título]]` (o Obsidian resolve por
nome, não por caminho), desde que o nome do arquivo continue único. Se houver
colisão de nome, resolva antes de mover.

## Ao terminar

Feche o loop de forma útil: diga em uma linha o que foi criado/atualizado e
onde, mencionando os principais links criados. Isso ajuda o usuário a confiar
que a rede está crescendo de forma coerente — e a perceber conexões que talvez
queira reforçar depois.

## Referências

- `<vault>/templates/` — a fonte de verdade do layout de cada tipo de nota
  (frontmatter + seções). Sob controle do usuário, no próprio Obsidian. Leia
  (ou renderize com `vault.py template`) antes de criar/editar notas; esta skill
  não guarda templates próprios.
- `scripts/vault.py` — helper para localizar pastas, achar notas existentes
  (evitar duplicar), listar o vocabulário de tags, renderizar templates do
  vault e gerenciar a Daily.
  `python3 scripts/vault.py -h` lista os subcomandos.
