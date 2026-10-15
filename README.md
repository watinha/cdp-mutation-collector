# CDP Mutation Collector

O **CDP Mutation Collector** é um script de automação e raspagem avançada (web scraping) desenvolvido em Python. Ele utiliza Selenium combinado com o Chrome DevTools Protocol (CDP) para navegar em páginas web, identificar elementos interativos, simular ações de usuário (cliques, digitação, foco) e registrar minuciosamente as mutações que ocorrem no DOM (Document Object Model) como resultado dessas interações.

Além de registrar as mudanças estruturais da página, a ferramenta extrai um conjunto robusto de características geométricas e semânticas dos elementos HTML e captura capturas de tela (*screenshots*) em diferentes estados de interação.

## 🚀 Funcionalidades Principais

* **Detecção Automática de Eventos:** Utiliza CDP (`DOMDebugger.getEventListeners`) para encontrar automaticamente todos os nós do DOM que possuem *event listeners* ativos (ex: `click`, `mouseover`, `keydown`, `change`).
* **Rastreamento de Mutações (MutationObserver):** Injeta scripts no navegador para monitorar ativamente nós adicionados, removidos ou modificados após as interações.
* **Simulação de Interações Realistas:** Executa eventos como *hover*, *click* e entrada de texto nos elementos descobertos utilizando `ActionChains` do Selenium.
* **Extração Avançada de Características (Feature Engineering):** Calcula métricas complexas via JavaScript, incluindo:
  * Dimensões e posicionamento absoluto (Top, Left, Width, Height).
  * Contagem de palavras e nós filhos.
  * Ancestrais semânticos (Landmarks como `main`, `nav`, `footer`).
  * XPath relativo.
  * Médias e desvios padrão espaciais ponderados de elementos filhos.
* **Registro Visual:** Salva capturas de tela automáticas durante os estados de *hover*, ação e tecla pressionada.

## 🛠️ Tecnologias e Dependências

* **Python 3.x**
* **Selenium:** Para orquestração do navegador e interações em tela.
* **Chrome DevTools Protocol (CDP):** Para acesso de baixo nível à árvore DOM e aos eventos registrados em memória.
* Servidor remoto do **Chromium/Chrome** configurado para receber conexões (ex: contêiner Docker).
