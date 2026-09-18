---
name: intelect-devorer-skill
description: Captura e organiza conhecimento no vault "second brain" do Obsidian do usuário — de sessões de código, estudos, projetos e ideias — como notas atômicas, interligadas e recuperáveis, seguindo uma estrutura fixa de pastas (dump, daily, projects, lessons, knowledge, resources, archives). Use esta skill sempre que o usuário quiser salvar, capturar, registrar, anotar ou arquivar algo no vault / segundo cérebro / Obsidian — por exemplo "anota isso", "salva no meu vault", "registra essa decisão do projeto", "abre uma task pra isso", "transforma isso numa nota de conhecimento", "adiciona ao meu segundo cérebro", ou ao final de uma sessão de código/estudo que valha a pena preservar. Também vale quando se está trabalhando diretamente dentro de um diretório de vault do Obsidian. Dispare mesmo que o usuário não diga "Obsidian" explicitamente, desde que a intenção seja claramente persistir conhecimento nas notas dele.
metadata:
  version: "0.5.2"
---

# Intelect Devorer Skill

## Propósito
---
Transformar informação dispersa em conhecimento recuperável: o vault é uma **rede**, não uma hierarquia de pastas. A pasta só diz o tipo da nota; o valor está nos links que ela tem para as outras — por isso a decisão de pasta se toma em segundos e o tempo se gasta conectando. Todo conteúdo de nota em **português**, com os nomes canônicos de tecnologias e conceitos na forma original (*Java Streams*, *OAuth 2.0*).

## Fluxo
---
Cada passo carrega sua rule **no momento do passo**, não na ativação da skill. Uma rule já lida nesta sessão não precisa ser relida.

```
- [ ] 1. Entender e decompor em notas atômicas → `rules/classificacao.md`
- [ ] 2. Verificar se já existe → `vault.py find`
- [ ] 3. Criar o arquivo a partir do template → `rules/templates.md`
- [ ] 4. Escrever o corpo → `rules/escrita.md`
- [ ] 5. Conectar: Progresso, Aprendizados, Daily → `rules/registro.md`
- [ ] 6. Validar → `vault.py fmt` + `vault.py lint`, em loop até verde
- [ ] 7. Fechar o loop com o usuário → uma linha: o que foi criado ou atualizado, em que pasta, e os wikilinks principais
```

O fluxo vale igual para nota nova e para edição: quando o passo 2 devolve resultado, o passo 3 vira abrir o arquivo que voltou e o passo 4 continua idêntico.

O passo 6 é **loop**: rode `fmt`, rode `lint`, corrija o que ele apontar, rode de novo — até `lint` sair sem erro. Link para nota que ainda não existe aparece como `[pendente]` e é uso legítimo do Obsidian, não pendência a corrigir. `[metadado]` marca `skill_version`/`llm_model_used` vazios em nota escrita à mão pelo usuário no Obsidian e **não se corrige**: não houve agente para declarar o valor, e preencher depois inventa dado.

## Convenções universais
---
Valem em todo passo, por isso ficam aqui e não numa rule:

- **Kebab-case em todo nome de arquivo**; o título humano, com acento e maiúscula, vive no campo `title:` do frontmatter.
- **Todo wikilink na forma `[[slug|Título]]`** — sem o pipe quando slug e título coincidem (`[[dotfiles]]`). `find` já imprime a forma pronta; copie de lá.
- **Links importam mais que pastas.** Toda relação relevante entre duas notas vira link; nota rica em links é o alvo, não um excesso.
- **Não duplique conhecimento — referencie.** Conceito que já é (ou deveria ser) nota própria entra por wikilink, nunca colado.

## Gotchas
---
- **Linha de template copiada literal é o erro mais frequente desta skill.** Bullet dentro de template é instrução sobre o que escrever ali, nunca conteúdo: ou você o substitui por conteúdo real, ou a seção fica vazia sob o cabeçalho. Só `## Cabeçalho` e o `---` abaixo dele saem idênticos do template.
- **`llm_model_used` só o modelo sabe responder**: preencha com o nome do modelo que está escrevendo agora.
- **`created` nunca muda em nota existente**, por mais que ela seja reescrita inteira; `updated` passa a ser o dia da edição. A data de hoje vem de `date +%F` uma vez por sessão, nunca de memória.
- **`dump` não é destino permanente**: é trampolim para uma nota de `projects`, `lessons` ou `knowledge`. `archives` só recebe por decisão explícita do usuário, e nenhum arquivo do vault é deletado — no máximo movido para lá.
- **A Daily indexa, não guarda conhecimento**: wikilink mais uma linha de síntese. Se a entrada precisa de um parágrafo, o parágrafo pertence à nota linkada.
- **Não crie pasta de nível superior nova.** As sete de `rules/classificacao.md` são o conjunto completo; o que parece não caber é `knowledge` ou é detalhe de um projeto.
- **Arquivo binário vai para `resources/`** e é referenciado por embed da nota que o cita — `![[palestra.pdf]]`, com o `!`, senão vira link e não incorpora. Link para site fica dentro da nota que o usa, nunca em `resources`.

## Scripts
---
Todos rodam do diretório da skill, com `python3 scripts/vault.py <sub>`, e `<vault>` é o caminho do vault do usuário. O script **não cria nota** — quem escreve é você; ele procura e audita.

| Subcomando | Uso | O que faz |
|---|---|---|
| `find` | `find "<vault>" "<termo>"` | procura nota existente por slug, título ou alias, e devolve o wikilink já na forma canônica |
| `tags` | `tags "<vault>" [<termo>]` | lista o vocabulário de tags em uso, para reusar termo antes de inventar |
| `fmt` | `fmt <alvo> [--check]` | normaliza a forma de nota, pasta ou vault inteiro: desfaz hard wrap e insere o `---` sob cada cabeçalho |
| `lint` | `lint "<vault>"` | audita o vault contra os templates; sai com código ≠ 0 quando há erro |
