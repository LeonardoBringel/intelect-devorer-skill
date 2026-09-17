# Classificação: onde a nota vive

**Carregue no passo 1 do fluxo** (entender e decompor), antes de escolher pasta e antes de rodar `find`. Uma vez por sessão basta, mesmo que a sessão renda várias notas.

O vault é uma rede, não uma hierarquia: a pasta define o *tipo* da nota, os links definem o valor dela. Escolha a pasta em segundos e gaste o tempo nos links.

## Tabela de pastas
---
| Pasta | Papel | Entra aqui quando… |
|-------|-------|--------------------|
| `dump` | captura rápida, incompleta | é fragmento que ainda não tem forma de nota e você quer registrar antes de perder. Ponto de partida de outra nota, nunca destino final |
| `daily` | índice temporal do dia | **sempre** — toda nota criada ou atualizada ganha uma menção (wikilink + descrição de uma linha). O conhecimento em si nunca mora aqui |
| `projects` | atividade com começo, meio e fim | há objetivo, decisões técnicas, progresso e pendências a acompanhar. Cada projeto é uma **pasta** (nota principal + `tasks/`), não um arquivo solto |
| `lessons` | aprendizado que nasceu de **fazer** | a descoberta veio da prática: um bug, uma armadilha de config, um comportamento inesperado da ferramenta no seu ambiente |
| `knowledge` | conhecimento que nasceu de **estudar** | li um artigo, estudei uma tecnologia, pesquisei um conceito — e quero documentar independente de qualquer projeto |
| `resources` | arquivos anexos | há um arquivo binário a guardar (pdf, ppt, imagem). Link para site ou blog fica **dentro** da nota que o cita, não aqui |
| `archives` | conteúdo depreciado | o usuário disse que aquilo saiu de circulação. Só por pedido explícito dele |

Essas sete pastas são o conjunto completo. Não crie pasta de nível superior nova: se algo parece não caber, ou é `knowledge` ou é detalhe de um projeto — em ambos os casos há lugar.

## A regra da fonte: lessons ou knowledge
---
As duas pastas guardam conhecimento reutilizável. O que as separa é **de onde a descoberta veio**, não o assunto: `lessons` nasce de fazer, `knowledge` nasce de estudar.

O caso central: estudar *Langfuse* e documentar o que a ferramenta faz é `knowledge`; descobrir, mexendo no **seu** Langfuse, que uma variável não é repassada pelo compose oficial é `lessons`. Mesma tecnologia, pastas diferentes — porque a primeira nota vale para qualquer pessoa e a segunda nasceu de um sintoma no seu ambiente.

**Na dúvida, `knowledge` prevalece.** Quando a mesma sessão rende as duas leituras e não fica claro qual domina, escreva em `knowledge`: a nota nasce menos amarrada ao contexto de um projeto, e é isso que a torna reaproveitável depois.

## O teste da atomicidade
---
Antes de criar nota própria para uma ideia, pergunte: ***"isso continuaria útil se o projeto onde descobri deixasse de existir?"***

Se **sim** → vira nota própria em `lessons` ou `knowledge`, e a nota principal do projeto aponta para ela pela seção Aprendizados. Se **não** → é detalhe do projeto: fica na nota principal ou na task, e não vira arquivo.

O mesmo teste quebra material misturado. Uma ideia razoavelmente bem definida por nota: prefira `java-streams`, `java-records` e `jvm-garbage-collection` a um `java.md` gigante — notas pequenas se conectam com precisão, nota grande só se conecta por inteiro. Se o material que o usuário trouxe cobre três assuntos que se sustentam sozinhos, são três notas ligadas entre si, não uma com três seções.

## Ciclo de vida: dump e archives
---
**Dump é trampolim, não depósito.** Ao revisitar um fragmento de `dump` — ou quando ele amadurecer — promova: transforme na nota de `projects`, `lessons` ou `knowledge` que ele deveria ser e ajuste os links que apontavam para ele. Promover não é deletar. O piso: a nota sucessora existe, os links apontam para ela, e você **oferece ao usuário mover o fragmento para `archives/`** — quem promove propõe a limpeza, não a executa calado. O teto: o fragmento só sai de `dump/` com o okay dele, e o destino é `archives/`; remover arquivo do vault é decisão exclusivamente dele. Dump que acumula vira lixo que ninguém lê; o sinal de saúde é ele estar quase vazio.

**Archives só recebe, e só por decisão explícita do usuário.** Nenhum arquivo do vault é deletado — no máximo movido para `archives/`. Mover arquivo entre pastas **não quebra wikilink**: o Obsidian resolve por nome de arquivo, não por caminho, desde que o slug continue único. Se houver colisão de nome com algo já em `archives/`, resolva o nome antes de mover.
