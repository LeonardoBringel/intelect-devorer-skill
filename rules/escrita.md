# Escrita: como escrever o corpo da nota

**Carregue no passo 4 do fluxo**, imediatamente antes de escrever o corpo de qualquer nota — nota nova, edição de nota existente, bullet de projeto ou linha de Daily. É obrigatório e não tem exceção: esta é a regra que o `fmt` e o `lint` não alcançam.

A nota existe para ser **reencontrada**, não lida de ponta a ponta. Quem chega nela daqui a seis meses quer a informação em segundos — texto a mais é custo de recuperação, não generosidade. Este arquivo é escrito como as notas devem ser escritas: use a forma dele como amostra, não só as regras que ele enuncia.

## O que cada parte do texto entrega
---
Cada linha da nota carrega um fato, uma relação ou um link. Onde a tentação é enfeitar, há uma contrapartida afirmativa que ocupa o mesmo espaço com mais conteúdo:

- **O primeiro parágrafo entrega o fato**, não anuncia o assunto. Comece pela conclusão — o que é verdade, o que quebrou, o que a ferramenta faz — e deixe o contexto para o segundo parágrafo, se ele for necessário.
- **A observação sobre a descoberta vira a condição que a produziu.** Em vez de contar que foi difícil, diga em que cenário o comportamento aparece: é isso que o leitor futuro precisa para reconhecer o próprio caso.
- **A afirmação direta substitui o hedge** quando o fato é firme. Hedge fica quando a incerteza é real e informativa — e aí ele vem nomeado: *não testado em produção*, *válido até a versão 2.4*, *não verifiquei se vale para o driver assíncrono*.
- **A última linha acrescenta**: um link, uma pendência, uma consequência que ainda não foi dita. Se ela só recapitula os parágrafos acima, apague-a — o texto já terminou uma linha antes.
- **O corpo começa pelo conteúdo.** O título já está no campo `title:` do frontmatter e aparece nos links; repeti-lo na primeira frase gasta a linha mais valiosa da nota.

Frases completas e artigos **ficam** — o alvo é prosa enxuta, não telegrama. Pronome sem antecedente claro custa mais caro que a palavra economizada. Termo técnico, número, comando e mensagem de erro vão exatos, copiados da fonte e nunca de memória.

## Densidade: errado / certo
---
Errado — três linhas de moldura antes do fato:
```markdown
Vale entender que o Docker Compose tem um comportamento interessante aqui. Aprendi isso da forma difícil, depois de algumas horas de debug — é um erro que quase todo mundo comete na primeira vez. De certa forma, variáveis de ambiente costumam não ser repassadas para o container em alguns casos.
```

Certo — o fato na primeira linha, a condição em seguida:
```
Variável declarada em `.env` não chega ao container quando o serviço define `env_file` apontando para outro arquivo: `env_file` substitui o carregamento implícito do `.env`, não soma com ele. O sintoma é a aplicação subir com o valor default em vez do configurado, sem nenhum aviso no log.
```

## Itálico, backtick e link
---
Nome canônico de conceito ou tecnologia que **não** vira link vai em *itálico*: *Java Streams*, *OAuth 2.0*, *PostgreSQL MVCC*, *Docker*. O itálico marca "isto é o nome de uma coisa" e é o que permite varrer a nota e descobrir de que ela trata sem ler cada frase.

Backtick é reservado ao **literal de código** — comando, caminho, identificador, flag, valor de config, mensagem de erro: `docker compose up`, `~/.config/nvim`, `proxy_set_header`, `SignatureDoesNotMatch`. O critério é o uso, não a palavra: *Docker* como tecnologia vai em itálico, `docker` como comando digitado no shell vai em backtick.

**Uma marcação só por nome.** Quando o nome vira wikilink, o link já cumpre o papel do itálico.

Errado:
```markdown
O projeto usa *[[oauth-2-0|OAuth 2.0]]* para autenticar.
Rodei o *docker compose up* e o `Docker` reclamou do `Host` header.
Estudei `Java Streams` esta semana.
```

Certo:
```markdown
O projeto usa [[oauth-2-0|OAuth 2.0]] para autenticar.
Rodei o `docker compose up` e o *Docker* reclamou do `Host` header.
Estudei *Java Streams* esta semana.
```

## Quebra de linha
---
**Um parágrafo é uma linha física**, por mais longa que fique. Quem quebra a linha é o Obsidian, não você. A quebra marca **fronteira semântica** — linha em branco entre parágrafos, item novo de lista, sub-item indentado — e nunca largura de tela.

## Cabeçalho e divider
---
Todo cabeçalho `##` leva `---` na linha seguinte, o conteúdo começa **imediatamente** abaixo do divider, e uma linha em branco separa o bloco do próximo cabeçalho. Vale também para os cabeçalhos que você cria fora do template — é a convenção do vault, não um detalhe dos templates.

## Orçamento: limite, não meta
---
Os números abaixo são teto. Uma frase que já baste vale mais que duas que preencham o orçamento:

- **Bullet de Decisão técnica ou Progresso: até 2 frases.** A primeira diz o que foi decidido ou feito, a segunda o motivo ou o resultado. O bullet é índice — o detalhe (spec, execução, validação) mora na task para a qual ele aponta.
- **Entrada de Daily: uma linha, e a síntese em até ~110 caracteres.** O wikilink não entra na conta: o comprimento dele vem do slug, que nem sempre se pode encurtar — o de uma task datada tem mediana 116 caracteres e chega a 134 sozinho. A Daily preserva o contexto do dia, nunca o conhecimento.

Exemplo de bullet de Progresso no teto:
```markdown
- 2026-09-05: [[2026-09-05-expor-minio-no-nginx|Expor MinIO no Nginx]] — proxy respondendo em `s3.local`. Faltou ajustar o `Host` header, que quebrava a assinatura das requisições.
```

Exemplos de entrada de Daily no teto — duas entradas reais do vault, já com a marcação que a seção acima pede: síntese de 112 e de 114 caracteres. O `~` do teto é isto: dois caracteres de marcação não justificam reescrever uma linha boa.
```markdown
- [[plugins-da-comunidade-no-obsidian|Plugins da comunidade no Obsidian]] — *Obsidian* não reinstala plugins sozinho; `community-plugins.json` só habilita, customização mora no `data.json`
- [[langfuse-self-hosted|Langfuse Self-Hosted]] — Setup do Langfuse v4 no homeserver via `docker compose`, atrás da *Tailscale*, instância fechada de usuário único.
```

## Não duplique conhecimento
---
Conceito que já é (ou deveria ser) uma nota entra por **referência**, não por cópia. Escreva `O projeto usa [[oauth-2-0|OAuth 2.0]] para autenticar o callback` — não cole a explicação de *OAuth 2.0* dentro da nota do projeto.

Antes de explicar um conceito geral dentro de um Project, de uma task ou da Daily, pergunte se ele não deveria ser uma nota própria. Se deveria e ainda não existe, crie a nota e linke: wikilink para nota inexistente é uso legítimo do Obsidian, e o `lint` reporta isso como `[pendente]`, não como erro.

## Autoconferência antes de gravar
---
Rode estas seis perguntas contra o rascunho, com o texto à vista. Cada uma é verificável olhando para o que está escrito:

1. O primeiro parágrafo **entrega o fato** ou apenas anuncia o assunto?
2. Existe alguma frase que, apagada, não levaria informação junto — meta-comentário, conclusão que só resume, repetição do título?
3. Cada hedge que sobrou (`talvez`, `costuma`, `geralmente`, `de certa forma`) corresponde a uma incerteza real que você conseguiria justificar em uma frase?
4. Cada nome canônico tem **exatamente uma** marcação — itálico, backtick ou link — e o critério foi o uso (tecnologia versus literal de código)?
5. Cada quebra de linha marca fronteira semântica, e cada `##` tem `---` logo abaixo com o conteúdo colado nele?
6. Algum parágrafo explica um conceito que já é (ou deveria ser) nota própria, em vez de linkar para ela?

Qualquer resposta desconfortável se corrige no rascunho, antes de gravar — depois de gravado, `fmt` conserta a forma, mas densidade só você conserta.

A conferência deixa **uma linha de rastro por nota**, escrita na conversa imediatamente antes de gravar e nunca dentro da nota: `conferência <slug>: <n.º da pergunta> — <o que mudou no rascunho>`. Uma correção basta como rastro. Quando nenhuma das seis bate, o rastro é `conferência <slug>: nenhuma bateu` — e essa frase é uma afirmação sobre o rascunho que está à vista, não uma formalidade. Duas notas, dois rastros; o bullet de Progresso acrescentado a um projeto é uma nota tocada e tem o rastro dele.

O teto é o que a linha genérica não cumpre: `revisei as seis` não diz sobre qual texto, e é exatamente o que sai de uma conferência rodada de cabeça.
