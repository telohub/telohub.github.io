# Observatório do Açaí

Um documento vivo sobre a cadeia produtiva do açaí (*Euterpe oleracea*) no Amapá — do açaizal ao consumidor — e o quadro normativo federal, estadual (Amapá, Pará, Amazonas) e municipal (Macapá e outras capitais) que a regula.

## Sobre o projeto

O projeto nasceu como um diagrama LaTeX/TikZ da cadeia produtiva e evoluiu em três fases:

1. **Levantamento normativo** — pesquisa e fact-check de ~90 normas (federais, estaduais, municipais e técnicas) aplicáveis à cadeia, cada uma com fonte linkada ou sinalizada como "a conferir".
2. **Website interativo** — "Observatório do Açaí": interface inspirada em Edward Tufte (clareza, poucos adornos, notas de margem), com padrão visual de SaaS comercial e edição de conteúdo in-place.
3. **Remodelagem conceitual** — adoção da metodologia de Blumenschein (2004, tese de doutorado UnB) para reorganizar a cadeia em cadeia de suprimentos / cadeia principal (de processos) / cadeia auxiliar, situadas dentro de um ecossistema de sete sistemas de contexto (normas, legislação ambiental, sanitário, trabalhista, tributário, educacional, legislação urbana), desenhado como círculos concêntricos clicáveis.

## Estrutura do repositório

```
.
├── README.md
├── observatorio-acai.html      # site publicado (HTML autocontido — o que está no link acima)
├── cadeia_acai_amapa.tex       # diagrama original da cadeia produtiva (LaTeX/TikZ)
├── cadeia_acai_amapa.pdf       # ...renderizado
└── src/                        # fonte modular do conteúdo do site
    ├── meta.json                 # identidade do documento: slug, título, ícone, descrição (+ margem, ver abaixo)
    ├── modelo.json               # o vocabulário do documento: grupos (raias), sistemas de contexto, etiquetas de elo, vistas (menu e telas)
    ├── blocos.json               # os 30 elos da cadeia (um por nó do diagrama)
    ├── normas.json                # as ~90 normas/fontes legais
    ├── notas.json                 # pendências e lacunas conhecidas
    ├── siglas.json                 # dicionário de siglas/abreviações (expansão + link institucional)
    ├── template.html              # casca da página (HTML/CSS/JS), com um placeholder __SEED_JSON__
    └── build.py                   # valida e remonta os 6 JSONs + template → observatorio-acai.html
```

`observatorio-acai.html` é gerado a partir de `src/`, não editado diretamente — ver abaixo.

## Como regenerar o site

```bash
cd src
python3 build.py                    # escreve ../observatorio-acai.html
python3 build.py /caminho/saida.html  # ou escolha outro destino
```

O script injeta `meta.json` + `modelo.json` + `blocos.json` + `normas.json` + `notas.json` + `siglas.json` no placeholder `__SEED_JSON__` de `template.html`. Antes de montar, `validate()` confere (1) o próprio `modelo.json` — campos obrigatórios e tipos, ids únicos, cor num slot de paleta válido, elos coerentes — e (2) a integridade referencial dos dados contra esse modelo: todo `bloco.grupo`, `bloco.sistemas[]` e `norma.elos[]` precisa apontar para um id que o modelo defina, e toda sigla precisa ter uma expansão não vazia. Recusa o build com uma mensagem clara se algo não bater, em vez de deixar o site publicar um card, um anel ou uma dica vazia por engano. Nenhum conjunto de ids está mais fixo no código: o que `build.py` ainda conhece é só `COR_SLOTS` (os slots de paleta que o CSS sabe pintar), `TIPOS_ELO` e, desde a Fase 3, os tipos de vista (`TIPOS_VISTA`, `COMPONENTES_DIAGRAMA`, `FONTES_LISTA`) — cada um corresponde a um renderizador do template. `validate()` também confere `meta` (slug, título, ícone e descrição) e as regras de `modelo.vistas`. Três placeholders do `<head>` (`__TITULO__`, `__DESCRICAO__`, `__FAVICON__`) são preenchidos com os textos de `meta.json`, escapados; o favicon é um SVG com o emoji de `meta.icone`, embutido como data-URI. O build é a única fonte do `<head>`; em tempo de execução o título da aba segue `state.meta.titulo`.

## Modelo de dados

**`bloco`** (um elo da cadeia):

| campo | tipo | observação |
|---|---|---|
| `id` | string | `e1`…`e10` (elos numerados — `e1`…`e4` no grupo `suprimentos`, `e5`…`e10` no grupo `principal`) ou id livre (demais grupos). O id não muda quando o bloco troca de grupo: é ele que `norma.elos[]` referencia e que o botão "Ver legislação" filtra |
| `grupo` | id | um dos `grupos[].id` de `modelo.json` (hoje `principal`, `suprimentos`, `auxiliar`, `circular`, `institucional`) |
| `nome`, `resumo` | string | — |
| `secoes` | lista | `{titulo, itens, margem?}` — o conteúdo expandido do card |
| `sistemas` | lista de ids \| ausente | quais dos `sistemas[].id` do modelo (hoje 7) esse bloco toca (relação N:N) |

**`norma`** (uma fonte legal/normativa):

| campo | tipo | observação |
|---|---|---|
| `esfera` | string | Federal, Amapá, Pará, Amazonas, Macapá, Belém, Manaus, Outros estados, Técnicas |
| `titulo`, `resumo`, `fonte` | string | — |
| `elos` | lista de ids | quais etiquetas de `modelo.elos` essa norma recebe (hoje `e1`…`e10`, `auxiliar`, `apoio`) |
| `status` | enum | `ok` (conferida) \| `conferir` (pendente de verificação) |

**`siglas`** (dicionário de acrônimos e abreviações; chave = a sigla, exatamente como ela aparece no texto — a correspondência é sensível a maiúsculas/minúsculas):

| campo | tipo | observação |
|---|---|---|
| `expansao` | string | obrigatório; o que a sigla significa |
| `url` | string \| ausente | link institucional opcional (nem toda sigla tem uma só instituição-dona, ex.: `IN`, `LC`, `PL`) |
| `status` | enum | `ok` \| `conferir` — mesma convenção de `norma.status` |

**`modelo`** (`src/modelo.json` — o *vocabulário* do documento; é dado, não código, e viaja junto com o conteúdo no estado, no export e no import). Chama-se `modelo` e não `schema` de propósito: no futuro, a *gramática* dos dados será um XSD, e este arquivo continua sendo o vocabulário que ela valida.

| campo | tipo | observação |
|---|---|---|
| `grupos[]` | lista (a ordem é a ordem das raias) | `{id, etiqueta, sequencial, raia, cor, filtroElo?, nome*, icone*, subtitulo*}` (\* obrigatórios quando `raia` é `true`). `etiqueta` = rótulo na tag do painel; `sequencial` = cartões numerados com setas; `raia` = se o grupo ganha uma raia na vista Cadeia; `cor` = slot de paleta (`principal`, `sup`, `aux`, `apoio`, `neutro`) — nunca um valor CSS livre, para o modo escuro continuar funcionando; `filtroElo` = elo agregado que o botão "Ver legislação aplicável" usa para os blocos do grupo que não são elo |
| `sistemas[]` | lista (do anel externo ao interno) | `{id, nome, desc}` — os sistemas de contexto do diagrama de ecossistema |
| `elos[]` | lista | etiquetas de legislação: `{id, tipo, abrev, rotulo?, apelidos?}`. `tipo: "bloco"` = a etiqueta é o id de um bloco (e1…e10) e o rótulo vem do nome dele; `tipo: "agregado"` = reúne vários (`auxiliar`, `apoio`) e traz `rotulo`. O campo "elos" da tabela de normas reconhece, sem diferenciar maiúsculas, exatamente o `id`, a `abrev` ou um dos `apelidos` (mais `todos`/`t`); o que não casa é descartado |
| `ecossistema` | objeto | `{nucleo, nota, semItem, dicaChip}` — textos do diagrama de anéis (`dicaChip` = a dica ao passar o mouse num anel) |
| `vistas[]` | lista (a ordem é a do menu; a primeira é a vista inicial) | as telas do documento, ver abaixo |

**`vistas[]`** — cada vista tem `{id, tipo, rotulo, icone, titulo, intro}` (`rotulo`/`icone` = botão do menu e título da barra mobile; `titulo` = o `<h1>`; `intro` = texto simples, com siglas expandidas) mais campos do seu `tipo`. O `id` (`^[a-z][a-z0-9-]*$`) vira o id da seção no DOM (`view-<id>`), então ids de vista não podem repetir.

| `tipo` | campos próprios | observação |
|---|---|---|
| `diagrama` | `componentes[]` — `"ecossistema"` e/ou `"raias"`, na ordem em que aparecem, sem repetir | no máximo **uma** vista (id de DOM único `#diagram`) |
| `normas` | `colunas{esfera,norma,resumo,elos}`, `ordemEsferas[]`, `rotulos{busca, buscaAria, contagem, adicionar, filtroElo, aConferir, verElo, verAplicavel}` | no máximo **uma** vista. `contagem` usa `{total}` e `{visiveis}`. Na `intro`, o token `{aConferir}` vira o selo (texto = `rotulos.aConferir`). Os botões "Ver legislação…" do painel lateral só existem se houver uma vista `normas`: é ela que os nomeia e para onde saltam. As `colunas` também nomeiam os campos da norma para leitores de tela no modo de edição |
| `cartoes` | `grupo` — id de um `grupos[]` | lista os blocos desse grupo; pode haver quantas vistas quiser |
| `lista` | `fonte` — hoje só `"notas"` | lista editável; quantas quiser |

**`meta`** (`src/meta.json` — a *identidade* do documento): `slug` (`^[a-z0-9][a-z0-9-]*$`; define a chave de armazenamento local `<slug>:content/main` e o nome do arquivo exportado `<slug>.json`; é lido **sempre da semente do build**, nunca do estado nem de um arquivo importado, para um arquivo de fora não poder redirecionar o armazenamento), `titulo` (marca no menu, título da aba), `icone` (emoji do favicon), `subtitulo` (a `<meta description>`), `atualizado`. `margem` é um dado sem uso hoje (nenhum código o lê), mantido intocado. O antigo `meta.intro` passou a ser a `intro` da vista Cadeia.

Para montar um documento de **outro domínio**, troque `meta/modelo/blocos/normas/notas/siglas.json`; `build.py` e `template.html` não mudam (há um teste que faz exatamente isso — com identidade, menu, vocabulário da vista de normas, duas vistas de cartões e sem vista de notas próprios). Ainda fixos no código e a tratar nas próximas fases: os nomes das entidades (blocos, normas, notas, siglas), o texto genérico do editor ("Editar conteúdo", "Desfazer", confirmações de importação, o sufixo "(ids separados por vírgula)") e a paleta (cinco slots, em CSS). No navegador, um modelo importado é conferido com as mesmas regras do build — com uma diferença deliberada: um elo `tipo: "bloco"` sem o bloco correspondente é tolerado, para não recusar arquivos parciais. Exports de antes da Fase 3 (modelo sem `vistas`/`dicaChip`, `meta` sem título/ícone, com `intro`) continuam entrando: o que falta é completado com os dados do build, campo a campo; se as vistas do build não combinarem com o modelo importado (por exemplo, apontam para um grupo que ele não tem), o arquivo é recusado. Como o modelo (e, com ele, as vistas) viaja no export, a definição das telas já é compartilhável por arquivo; ainda não há interface para editá-la.

## Siglas e abreviações

Qualquer sigla cadastrada em `siglas.json` ganha, no site, um sublinhado pontilhado: passar o mouse, navegar até ela com Tab, ou tocar nela num celular/tablet mostra a expansão e, quando houver, um link para o site institucional. A correspondência roda inteiramente no `template.html` (função `wrapSiglas`, ao lado de `el()`/`editableSpan()`): o texto livre é varrido com uma expressão regular montada a partir das chaves de `siglas.json`, e cada ocorrência vira um `<span tabindex="0">` focável (nunca `innerHTML`, e nunca um `<button>` — ver "Segurança e robustez" abaixo). Três regras foram necessárias para não quebrar o resto do site:

- **Fica fora do modo de edição.** Em edição, o campo volta a ser texto puro — zero risco de a marcação da dica atrapalhar o cursor ou ser salva junto do conteúdo.
- **Nunca aninha dentro do link da fonte.** No título de uma norma (que já é um link para `fonte`), a sigla principal vira seu próprio span ao lado do link, em vez de ficar dentro dele — um link não pode conter outro link.
- **Em touch, um toque alterna a dica.** Tocar a sigla abre; tocar de novo na mesma, tocar em outra sigla, tocar fora, rolar a página ou apertar Esc fecha (só uma dica fica aberta por vez). Como não existe hover de verdade em touch, um `touchstart` liga uma flag (`touchActive`) que faz o `mouseover`/`mouseout` "fantasma" que o navegador dispara logo antes do `click` ser ignorado — sem essa flag, o toque abriria a dica duas vezes (uma por engano via hover, outra pelo toque de fato) e o `click` seguinte a fecharia na hora, dando a impressão de que nada aconteceu. Tocar no link institucional dentro da dica continua navegando normalmente (nada de `preventDefault`); a dica fechar junto é só um efeito colateral inofensivo.

## Segurança e robustez

Uma revisão de código (2026-10-16) encontrou e corrigiu um XSS real, além de vários pontos de robustez e acessibilidade, no `template.html`:

- **Links vindos de dados importados passam por um allowlist.** `norma.fonte` e `sigla.url` só viram `<a href>` se forem `http://`/`https://` (função `safeHref()`); um JSON importado com `fonte: "javascript:..."` agora renderiza como texto puro, nunca como link clicável.
- **Importar/restaurar ficou mais defensivo.** `validShape()` confere o tipo de cada campo que o render de fato usa (não só a presença de `meta`/`blocos`/`normas`/`notas`); o novo estado é montado campo a campo em vez de `Object.assign({}, seed, parsed)` (uma chave `"__proto__"` no arquivo importado não tem mais como alterar o protótipo do estado); um erro ao desenhar a tela depois de importar volta para a seed original sem salvar nada quebrado; e há um "↺ Desfazer" de um nível depois de importar ou restaurar o conteúdo original. Desde a Fase 2, `validShape()` também confere o `modelo` (o do arquivo, ou o do build se o arquivo — um export antigo — não trouxer um) com as mesmas regras do build e recusa blocos/normas que apontem para grupo, sistema ou elo que esse modelo não define; a cor de um grupo é sempre um slot de paleta, nunca um valor CSS vindo do arquivo. Desde a Fase 3, também confere `modelo.vistas` e `meta`: título, ícone e descrição do arquivo viram texto (nunca HTML) na página, o `slug` do arquivo é ignorado, e `meta`, `modelo` e `ecossistema` são montados campo a campo (uma chave `"__proto__"` em qualquer deles não contamina nada).
- **O gatilho de uma sigla é um `<span>` focável, não mais um `<button>`.** Um `<button>` com um `<a>` dentro (o link institucional da dica) é HTML inválido — conteúdo interativo não pode aninhar em conteúdo interativo. O span mantém o mesmo comportamento de Tab/hover/foco de antes, com `aria-describedby` + `role="tooltip"` para leitores de tela.
- **O painel lateral (drawer) tem semântica de diálogo.** `role="dialog"` + `aria-modal`, Tab fica preso dentro dele enquanto está aberto, e o foco volta para o elemento que o abriu ao fechar (✕, Escape, ou o fundo escurecido).
- **Colar e arrastar-e-soltar em campos editáveis só aceitam texto puro.** Antes, só colar era filtrado; uma `<img onerror="...">` arrastada para dentro de um campo não executa mais. O texto puro passou a ser inserido via `Selection`/`Range` em vez de `document.execCommand` (descontinuado).
- Uma `<meta http-equiv="Content-Security-Policy">` com `object-src`/`base-uri`/`form-action` todos `'none'` fecha mais uma camada, sem tocar em `script-src`/`style-src` (a página é de propósito um único arquivo com `<script>`/`<style>` inline, sem build step).
- **Conteúdo publicado agora vence uma cópia local desatualizada (2026-10-22).** Antes, qualquer edição salva no navegador (mesmo uma acidental, feita só testando o modo "Editar") passava a vencer a semente embutida pra sempre — inclusive num hard refresh — porque `init()` fazia `Object.assign({}, cloneSeed(), snap.data())`, e esse merge raso substitui cada array (`blocos`/`normas`/`notas`/`siglas`) inteiro pelo que estava salvo, por mais antigo que fosse. Um link corrigido em `normas.json`, por exemplo, nunca chegava a quem já tivesse qualquer coisa salva localmente. Agora `build.py` calcula um hash do conteúdo (`SEED_VERSION`, não um timestamp — o mesmo conteúdo gera sempre a mesma versão) e `doSave()` grava esse hash junto do estado; no carregamento, `init()` só reaproveita o que está salvo se a versão bater com a deste build — caso contrário (incluindo salvamentos de antes desta correção existir, que não têm hash nenhum) descarta a cópia local em favor do conteúdo publicado, avisando na barra de status ("Conteúdo atualizado nesta página…"). Uma edição feita ao vivo no navegador continua funcionando normalmente entre um salvamento e outro, enquanto o build não mudar.

## Modelo conceitual

Seguindo Blumenschein (2004), a cadeia é lida em quatro grupos (o quarto, "circular", é extensão própria deste projeto — economia circular de subprodutos e funções de apoio sem equivalente direto na indústria da construção):

- **Cadeia de suprimentos** (7 blocos) — tudo que antecede a transformação do fruto: produção primária, colheita, transporte primário e comercialização do fruto (`e1`…`e4`, desde 2026-11-04) mais insumos, máquinas, energia e utilidades. Os blocos aparecem como cartões soltos, sem numeração.
- **Cadeia principal / de processos** (6 blocos, `e5`…`e10`) — do beneficiamento ao consumo final, em sequência numerada.
- **Cadeia auxiliar** (3 blocos) — conhecimento, pesquisa, consultoria, transporte.
- **Economia circular e de apoio** (8 blocos) — subprodutos (caroço, fibras, efluentes) e funções de apoio (mão de obra, crédito, mercados).

Essas cadeias existem dentro de um ecossistema de **7 sistemas de contexto**, representados como círculos concêntricos clicáveis na tela "Cadeia":

| sistema | cobre |
|---|---|
| Sistema de Normas Técnicas | padrões de identidade, qualidade e registro — MAPA, DIAGRO |
| Legislação Urbana | uso e ocupação do solo urbano — sem equivalente direto nesta cadeia rural/extrativista (anel propositalmente vazio) |
| Legislação Ambiental | licenciamento, manejo, território — SEMA, IBAMA, ICMBio, INCRA, SPU |
| Sistema Sanitário | vigilância sanitária de alimentos — Anvisa e vigilância estadual/municipal |
| Sistema Trabalhista | segurança e direitos no trabalho rural — MTE, NRs |
| Sistema Tributário | tributos e obrigações fiscais — SEFAZ, Receita Federal |
| Sistema Educacional | pesquisa, ATER, capacitação — Embrapa, universidades, Sebrae, Senar, Senai |

Um bloco institucional (6 ao todo) também pode pertencer a mais de um sistema ao mesmo tempo — por isso `sistemas` é armazenado como lista diretamente no bloco, em vez de um mapa externo bloco→sistema: a relação é N:N, e um mapa parcial de 1:1 esconde silenciosamente os casos que não cobre. `validate()` em `build.py` é o equivalente barato, em tempo de build, do que um checador de tipos somados (p. ex. Elixir/Dialyzer) faria em tempo de compilação — e é o motivo de essa linguagem estar cogitada como próximo passo.

## Princípios de design

- **Tufte**: clareza antes de ornamento, notas de margem, poucos elementos de chrome, dados em primeiro plano.
- **SaaS comercial**: sidenav fixo com 4 telas (Cadeia, Legislação, Institucional, Notas), cards, tema claro/escuro.
- **YAGNI / KISS / DRY**: um único arquivo HTML autocontido publicado; conteúdo editável in-place com persistência em nuvem (artifact DB) e fallback automático em `localStorage` quando o arquivo é aberto fora do claude.ai.

## Status atual

- **30 blocos** — 6 cadeia principal · 7 suprimentos · 8 circular/apoio · 3 auxiliar · 6 institucional.
- **92 normas** — 53 federais · 10 Amapá · 8 Pará · 6 Macapá · 5 técnicas · 4 Manaus · 3 outros estados · 2 Belém · 1 Amazonas. 17 ainda marcadas `conferir`.
- **97 siglas** cadastradas — 59 com status `ok`, 38 ainda `conferir` (em geral, o link institucional, não a expansão).

### Lacunas conhecidas (ver `src/notas.json` para a lista completa)

- Vigência da Lei 0869/2004 (AP) frente às Leis 3.426/2026 e 3.428/2026 — Portaria DIAGRO de dez/2025 ainda citava a lei de 2004.
- Alcance do Decreto 12.709/2025 sobre outros decretos federais já citados aqui.
- Amazonas sem lei/decreto estadual específico sobre açaí identificado.
- Número do Código Sanitário de Macapá ainda não confirmado.
- Status de sanção do PL 169/2024 (Pará) não confirmado.
- Tributário (ICMS, IBS/CBS), exportação, navegação e regime de várzeas ainda não cobertos.
- Siglas ainda sem entrada em `src/siglas.json` (nome oficial incerto): Sipeagro, ACTB, DAPP/RAP/RAPC, SVS-GEA, SEDCON, SLIM.

## Próximos passos

**Generalização do framework** (de PoC para método reaproveitável, uma fase por vez): ✅ 1 elos 1-4 movidos para Suprimentos · ✅ 2 grupos/sistemas/elos viram dados (`modelo.json`) · ✅ 3 identidade e vistas do documento dirigidas por dados (`meta.json`, `modelo.vistas`) · 4 edição estrutural (editar o próprio modelo) · 5 build administrativo separado (importação/edição profunda fora do build publicado) · 6 fluxo colaborativo (equipes propõem, equipe administrativa adota seletivamente) · 7 migração JSON → XML/XSD (já decidida; depois do modelo estabilizar) · 8 empacotamento como framework para outros domínios. Cada fase ganha seu próprio plano antes de ser implementada.

- Componente em **Elixir** para validar/interagir com a estrutura do seed — escopo ainda em aberto: ferramenta de validação mais rigorosa que `validate()`, ou algo mais permanente substituindo o JSON embutido por um serviço.
- Fechar as lacunas listadas acima conforme novas fontes forem localizadas.

## Fontes principais

- Blumenschein, R. N. (2004). *A Sustentabilidade na Cadeia Produtiva da Indústria da Construção*. Tese de doutorado, Universidade de Brasília — modelo de cadeias + ecossistema de círculos concêntricos (Figura 2, p. 47).
- Embrapa Amapá — material sobre processamento, utensílios e uso tradicional do termo "vinho" para a polpa batida.
- Diário Oficial da União, do Amapá, do Pará, do Amazonas e dos municípios — fonte primária de cada norma citada em `src/normas.json`.
