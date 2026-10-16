// Gráfico do ativo-objeto com KLineCharts 10: candles D1/W1/H4, EMA 17/34 calculadas no backend
// (mesma fórmula documentada) e níveis da operação sobrepostos.
const Candles = (() => {
  const EMA_FAST_COLOR = "#d000d0"; // magenta
  const EMA_SLOW_COLOR = "#ff8c00"; // laranja
  const EMA_WIDTH = 2.5;
  const PERIODS = {
    mn1: { type: "month", span: 1 }, w1: { type: "week", span: 1 }, d1: { type: "day", span: 1 },
    h4: { type: "hour", span: 4 }, h1: { type: "hour", span: 1 },
  };
  const RIGHT_GAP_BARS = 3; // folga à direita da última barra
  const MIN_BAR_SPACE = 0.25;
  let chart = null;
  let bars = [];
  let levels = [];
  let ready = false;

  function registerOnce() {
    if (ready) return;
    ready = true;
    klinecharts.registerLocale("pt-BR", {
      time: "Data: ", open: "Abertura: ", high: "Máxima: ", low: "Mínima: ", close: "Fechamento: ",
      volume: "Volume: ", turnover: "Financeiro: ", change: "Variação: ",
      second: "s", minute: "", hour: "h", day: "D", week: "S", month: "M", year: "A",
    });
    // EMAs vêm prontas da API (campos ema_fast/ema_slow de cada barra).
    klinecharts.registerIndicator({
      name: "EMA_API",
      shortName: "EMA",
      series: "price",
      precision: 2,
      calcParams: [17, 34],
      figures: [
        { key: "fast", title: "EMA 17: ", type: "line", styles: () => ({ color: EMA_FAST_COLOR, size: EMA_WIDTH }) },
        { key: "slow", title: "EMA 34: ", type: "line", styles: () => ({ color: EMA_SLOW_COLOR, size: EMA_WIDTH }) },
      ],
      calc: (list) => list.map((b) => ({
        fast: b.ema_fast === null ? undefined : b.ema_fast,
        slow: b.ema_slow === null ? undefined : b.ema_slow,
      })),
    });
    // Linha horizontal com rótulo, para os níveis da operação.
    klinecharts.registerOverlay({
      name: "nivel",
      totalStep: 1,
      needDefaultPointFigure: false,
      needDefaultXAxisFigure: false,
      needDefaultYAxisFigure: true,
      createPointFigures: ({ coordinates, bounding, overlay }) => {
        const y = coordinates[0].y;
        const e = overlay.extendData || {};
        return [
          {
            type: "line",
            attrs: { coordinates: [{ x: 0, y }, { x: bounding.width, y }] },
            styles: { color: e.color, size: e.size || 1.2, style: e.dashed ? "dashed" : "solid", dashedValue: e.dash || [6, 4] },
            ignoreEvent: true,
          },
          {
            type: "text",
            attrs: { x: 6, y: y - 2, text: e.label, align: "left", baseline: "bottom" },
            styles: { color: e.color, size: 11, family: FONT, backgroundColor: "rgba(255,255,255,0.85)", paddingLeft: 2, paddingRight: 2, paddingTop: 1, paddingBottom: 1, borderSize: 0 },
            ignoreEvent: true,
          },
        ];
      },
    });
  }

  // O padrão do KLineCharts é "Helvetica Neue", ausente no Windows (cai numa fonte serifada).
  const FONT = '"Segoe UI", system-ui, -apple-system, Arial, sans-serif';
  function withFont(obj) {
    if (Array.isArray(obj)) return obj.map(withFont);
    if (!obj || typeof obj !== "object") return obj;
    const out = {};
    for (const [k, v] of Object.entries(obj)) out[k] = k === "family" ? FONT : withFont(v);
    return out;
  }
  function useFont(c) { c.setStyles(withFont(c.getStyles())); }

  function ensureChart(dom) {
    registerOnce();
    if (chart) return chart;
    chart = klinecharts.init(dom, {
      locale: "pt-BR",
      timezone: "America/Sao_Paulo",
      // Mínimo padrão é 1 px/barra: num painel estreito, 400 barras não caberiam.
      layout: { barSpaceLimit: { min: MIN_BAR_SPACE, max: 50 } },
      thousandsSeparator: { sign: "." },
      decimalFold: { threshold: 99 },
      styles: {
        grid: { horizontal: { color: "#eef0f4" }, vertical: { color: "#eef0f4" } },
        candle: {
          type: "candle_solid",
          bar: {
            compareRule: "current_open",
            upColor: "#FFFFFF", upBorderColor: "#000000", upWickColor: "#000000",
            downColor: "#000000", downBorderColor: "#000000", downWickColor: "#000000",
            noChangeColor: "#FFFFFF", noChangeBorderColor: "#000000", noChangeWickColor: "#000000",
          },
          priceMark: { last: { upColor: "#1d2330", downColor: "#1d2330", noChangeColor: "#1d2330" } },
          tooltip: { showRule: "follow_cross" },
        },
        indicator: { tooltip: { showRule: "always" } },
        xAxis: { tickText: { color: "#667085" } },
        yAxis: { tickText: { color: "#667085" } },
      },
    });
    useFont(chart);
    chart.createIndicator({ name: "EMA_API", paneId: "candle_pane" }, true);
    // Escala vertical: além dos candles visíveis, inclui os níveis marcados com `fit`
    // (pernas, breakeven), para que a estrutura apareça mesmo longe do preço atual.
    chart.overrideYAxis({
      paneId: "candle_pane",
      createRange: ({ defaultRange }) => {
        const vals = levels.filter((l) => l.fit && FMT.ok(l.value)).map((l) => l.value);
        if (!vals.length) return defaultRange;
        let from = Math.min(defaultRange.from, ...vals);
        let to = Math.max(defaultRange.to, ...vals);
        if (from === defaultRange.from && to === defaultRange.to) return defaultRange;
        const pad = (to - from) * 0.04;
        from -= pad;
        to += pad;
        const range = to - from;
        return { from, to, range, realFrom: from, realTo: to, realRange: range, displayFrom: from, displayTo: to, displayRange: range };
      },
    });
    chart.setDataLoader({
      getBars: ({ type, callback }) => callback(type === "init" ? bars : [], false),
    });
    new ResizeObserver(() => chart && chart.resize()).observe(dom);
    return chart;
  }

  function setData(dom, symbol, tf, data) {
    bars = data;
    const c = ensureChart(dom);
    c.setSymbol({ ticker: `${symbol}:${tf}`, pricePrecision: 2, volumePrecision: 0 });
    c.setPeriod(PERIODS[tf]);
    c.resetData();
    drawLevels();
    requestAnimationFrame(fitAll);
  }

  // Ajusta o espaçamento para caberem TODAS as barras carregadas (o padrão do KLineCharts mostra
  // só as ~60 últimas e esconde o resto à esquerda). Espaço por barra entre MIN_BAR_SPACE e 50 px.
  function fitAll() {
    if (!chart || !bars.length) return;
    const size = chart.getSize("candle_pane", "main");
    const width = size && size.width ? size.width : 0;
    if (!width) return;
    const space = Math.max(MIN_BAR_SPACE, Math.min(50, width / (bars.length + RIGHT_GAP_BARS)));
    chart.setBarSpace(space);
    chart.setOffsetRightDistance(space * RIGHT_GAP_BARS);
    chart.scrollToRealTime();
  }

  let fitKey = "";
  function setLevels(list) {
    levels = list;
    drawLevels();
    // Recalcula a escala vertical só se mudaram os níveis que a definem (pernas, breakeven);
    // o equilíbrio da data simulada muda a cada passo do slider e não deve reescalar o gráfico.
    const key = list.filter((l) => l.fit).map((l) => l.value).join("|");
    if (chart && key !== fitKey) { fitKey = key; chart.resize(); }
  }

  function drawLevels() {
    if (!chart || !bars.length) return;
    chart.removeOverlay({ name: "nivel" });
    const ts = bars[bars.length - 1].timestamp;
    for (const lv of levels) {
      if (!FMT.ok(lv.value)) continue;
      chart.createOverlay({
        name: "nivel",
        lock: true,
        points: [{ timestamp: ts, value: lv.value }],
        extendData: { label: `${lv.label} ${FMT.price(lv.value)}`, color: lv.color, dashed: lv.dashed, dash: lv.dash, size: lv.size },
      });
    }
  }

  function resize() { if (chart) chart.resize(); }

  // Diagnóstico (console/testes): rótulos desenhados e faixa visível do eixo de preço.
  function debug() {
    if (!chart) return null;
    const axis = (chart.getYAxes ? chart.getYAxes({ paneId: "candle_pane" }) : [])[0];
    const range = axis && axis.getRange ? axis.getRange() : null;
    return {
      ticker: chart.getSymbol() && chart.getSymbol().ticker,
      bars: chart.getDataList().length,
      barSpace: chart.getBarSpace(),
      visible: chart.getVisibleRange ? chart.getVisibleRange() : null,
      overlays: chart.getOverlays({ name: "nivel" }).map((o) => o.extendData.label),
      range: range ? [range.from, range.to] : null,
    };
  }

  return { setData, setLevels, resize, fitAll, debug };
})();
