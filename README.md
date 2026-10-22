# Observatório do Açaí

Um documento vivo sobre a cadeia produtiva do açaí (*Euterpe oleracea*) no Amapá — do açaizal ao consumidor — e o quadro normativo federal, estadual (Amapá, Pará, Amazonas) e municipal (Macapá e outras capitais) que a regula.

**Site publicado:** https://claude.ai/artifact/RWBp1eMePkiokKxsEyMfLD

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
    ├── meta.json                 # título, subtítulo, introdução, notas de margem
    ├── blocos.json               # os 30 elos da cadeia (um por nó do diagrama)
    ├── normas.json                # as ~90 normas/fontes legais
    ├── notas.json                 # pendências e lacunas conhecidas
    ├── siglas.json                 # dicionário de siglas/abreviações (expansão + link institucional)
    ├── template.html              # casca da página (HTML/CSS/JS), com um placeholder __SEED_JSON__
    └── build.py                   # remonta os 5 JSONs + template → observatorio-acai.html
```

`observatorio-acai.html` é gerado a partir de `src/`, não editado diretamente — ver abaixo.

## Como regenerar o site

```bash
cd src
python3 build.py                    # escreve ../observatorio-acai.html
python3 build.py /caminho/saida.html  # ou escolha outro destino
```

O script injeta `meta.json` + `blocos.json` + `normas.json` + `notas.json` + `siglas.json` no placeholder `__SEED_JSON__` de `template.html`. Antes de montar, `validate()` confere a integridade referencial dos dados — todo `bloco.grupo`, `bloco.sistemas[]` e `norma.elos[]` precisa apontar para um id que exista, e toda sigla precisa ter uma expansão não vazia — e recusa o build com uma mensagem clara se algo não bater, em vez de deixar o site publicar um card, um anel ou uma dica vazia por engano.

## Modelo de dados

**`bloco`** (um elo da cadeia):

| campo | tipo | observação |
|---|---|---|
| `id` | string | `e1`…`e10` (cadeia principal) ou id livre (demais grupos) |
| `grupo` | enum | `principal` \| `suprimentos` \| `auxiliar` \| `circular` \| `institucional` |
| `nome`, `resumo` | string | — |
| `secoes` | lista | `{titulo, itens, margem?}` — o conteúdo expandido do card |
| `sistemas` | lista de ids \| ausente | quais dos 7 sistemas de contexto esse bloco toca (relação N:N) |

**`norma`** (uma fonte legal/normativa):

| campo | tipo | observação |
|---|---|---|
| `esfera` | string | Federal, Amapá, Pará, Amazonas, Macapá, Belém, Manaus, Outros estados, Técnicas |
| `titulo`, `resumo`, `fonte` | string | — |
| `elos` | lista de ids | quais blocos da cadeia essa norma regula (`e1`…`e10`, `auxiliar`, `apoio`) |
| `status` | enum | `ok` (conferida) \| `conferir` (pendente de verificação) |

**`siglas`** (dicionário de acrônimos e abreviações; chave = a sigla, exatamente como ela aparece no texto — a correspondência é sensível a maiúsculas/minúsculas):

| campo | tipo | observação |
|---|---|---|
| `expansao` | string | obrigatório; o que a sigla significa |
| `url` | string \| ausente | link institucional opcional (nem toda sigla tem uma só instituição-dona, ex.: `IN`, `LC`, `PL`) |
| `status` | enum | `ok` \| `conferir` — mesma convenção de `norma.status` |

## Siglas e abreviações

Qualquer sigla cadastrada em `siglas.json` ganha, no site, um sublinhado pontilhado: passar o mouse (ou navegar até ela com Tab) mostra a expansão e, quando houver, um link para o site institucional. A correspondência roda inteiramente no `template.html` (função `wrapSiglas`, ao lado de `el()`/`editableSpan()`): o texto livre é varrido com uma expressão regular montada a partir das chaves de `siglas.json`, e cada ocorrência vira um `<span tabindex="0">` focável (nunca `innerHTML`, e nunca um `<button>` — ver "Segurança e robustez" abaixo). Duas regras foram necessárias para não quebrar o resto do site:

- **Fica fora do modo de edição.** Em edição, o campo volta a ser texto puro — zero risco de a marcação da dica atrapalhar o cursor ou ser salva junto do conteúdo.
- **Nunca aninha dentro do link da fonte.** No título de uma norma (que já é um link para `fonte`), a sigla principal vira seu próprio span ao lado do link, em vez de ficar dentro dele — um link não pode conter outro link.

## Segurança e robustez

Uma revisão de código (2026-10-16) encontrou e corrigiu um XSS real, além de vários pontos de robustez e acessibilidade, no `template.html`:

- **Links vindos de dados importados passam por um allowlist.** `norma.fonte` e `sigla.url` só viram `<a href>` se forem `http://`/`https://` (função `safeHref()`); um JSON importado com `fonte: "javascript:..."` agora renderiza como texto puro, nunca como link clicável.
- **Importar/restaurar ficou mais defensivo.** `validShape()` confere o tipo de cada campo que o render de fato usa (não só a presença de `meta`/`blocos`/`normas`/`notas`); o novo estado é montado campo a campo em vez de `Object.assign({}, seed, parsed)` (uma chave `"__proto__"` no arquivo importado não tem mais como alterar o protótipo do estado); um erro ao desenhar a tela depois de importar volta para a seed original sem salvar nada quebrado; e há um "↺ Desfazer" de um nível depois de importar ou restaurar o conteúdo original.
- **O gatilho de uma sigla é um `<span>` focável, não mais um `<button>`.** Um `<button>` com um `<a>` dentro (o link institucional da dica) é HTML inválido — conteúdo interativo não pode aninhar em conteúdo interativo. O span mantém o mesmo comportamento de Tab/hover/foco de antes, com `aria-describedby` + `role="tooltip"` para leitores de tela.
- **O painel lateral (drawer) tem semântica de diálogo.** `role="dialog"` + `aria-modal`, Tab fica preso dentro dele enquanto está aberto, e o foco volta para o elemento que o abriu ao fechar (✕, Escape, ou o fundo escurecido).
- **Colar e arrastar-e-soltar em campos editáveis só aceitam texto puro.** Antes, só colar era filtrado; uma `<img onerror="...">` arrastada para dentro de um campo não executa mais. O texto puro passou a ser inserido via `Selection`/`Range` em vez de `document.execCommand` (descontinuado).
- Uma `<meta http-equiv="Content-Security-Policy">` com `object-src`/`base-uri`/`form-action` todos `'none'` fecha mais uma camada, sem tocar em `script-src`/`style-src` (a página é de propósito um único arquivo com `<script>`/`<style>` inline, sem build step).

## Modelo conceitual

Seguindo Blumenschein (2004), a cadeia é lida em quatro grupos (o quarto, "circular", é extensão própria deste projeto — economia circular de subprodutos e funções de apoio sem equivalente direto na indústria da construção):

- **Cadeia de suprimentos** (3 blocos) — insumos e fornecedores a montante.
- **Cadeia principal / de processos** (10 blocos, `e1`…`e10`) — do açaizal ao consumo final.
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

- **30 blocos** — 10 cadeia principal · 3 suprimentos · 8 circular/apoio · 3 auxiliar · 6 institucional.
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

- Componente em **Elixir** para validar/interagir com a estrutura do seed — escopo ainda em aberto: ferramenta de validação mais rigorosa que `validate()`, ou algo mais permanente substituindo o JSON embutido por um serviço.
- Fechar as lacunas listadas acima conforme novas fontes forem localizadas.

## Fontes principais

- Blumenschein, R. N. (2004). *A Sustentabilidade na Cadeia Produtiva da Indústria da Construção*. Tese de doutorado, Universidade de Brasília — modelo de cadeias + ecossistema de círculos concêntricos (Figura 2, p. 47).
- Embrapa Amapá — material sobre processamento, utensílios e uso tradicional do termo "vinho" para a polpa batida.
- Diário Oficial da União, do Amapá, do Pará, do Amazonas e dos municípios — fonte primária de cada norma citada em `src/normas.json`.
