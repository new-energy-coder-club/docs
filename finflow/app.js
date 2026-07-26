"use strict";
const {
  useState,
  useEffect,
  useRef,
  useMemo
} = React;
const D = window.FINFLOW_DATA;

/* ---------- 工具 ---------- */
function fmt(n, dec = 2) {
  return Number(n).toLocaleString('zh-CN', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec
  });
}

/* 数字滚动动画 CountUp */
function CountUp({
  value,
  decimals = 2,
  duration = 1300,
  className = '',
  prefix = '',
  suffix = ''
}) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let raf,
      start = null;
    const step = ts => {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(value * eased);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return /*#__PURE__*/React.createElement("span", {
    className: className
  }, prefix, fmt(display, decimals), suffix);
}

/* 通用 tooltip 状态钩子：绑定在 position:relative 的容器内 */
function useTooltip() {
  const [tip, setTip] = useState(null);
  const show = (e, content) => {
    const rect = e.currentTarget.closest('.chart-box').getBoundingClientRect();
    setTip({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      content
    });
  };
  const hide = () => setTip(null);
  const node = tip ? /*#__PURE__*/React.createElement("div", {
    className: "tooltip",
    style: {
      left: tip.x,
      top: tip.y
    }
  }, tip.content) : null;
  return {
    show,
    hide,
    node
  };
}

/* ---------- 横向条形图（动画加载 + 悬停 tooltip + 可点击图例筛选） ---------- */
function BarChart({
  data,
  total
}) {
  const [loaded, setLoaded] = useState(false);
  const [hidden, setHidden] = useState({});
  const {
    show,
    hide,
    node
  } = useTooltip();
  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 60);
    return () => clearTimeout(t);
  }, []);
  const visible = data.filter(d => !hidden[d.key]);
  const max = Math.max(...data.map(d => d.amount));
  const toggle = k => setHidden(h => ({
    ...h,
    [k]: !h[k]
  }));
  return /*#__PURE__*/React.createElement("div", {
    className: "chart-box"
  }, node, visible.map((d, i) => /*#__PURE__*/React.createElement("div", {
    className: "bar-row",
    key: d.key,
    onMouseMove: e => show(e, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700
      }
    }, d.label), /*#__PURE__*/React.createElement("div", {
      className: "t-amt"
    }, "\xA5 ", fmt(d.amount)), /*#__PURE__*/React.createElement("div", {
      className: "t-dim"
    }, "\u5360\u6BD4 ", fmt(d.amount / total * 100, 1), "%", d.count ? ` · ${d.count} 笔` : ''), d.note && /*#__PURE__*/React.createElement("div", {
      className: "t-dim",
      style: {
        whiteSpace: 'normal',
        maxWidth: 280
      }
    }, d.note))),
    onMouseLeave: hide
  }, /*#__PURE__*/React.createElement("div", {
    className: "bar-label"
  }, d.label), /*#__PURE__*/React.createElement("div", {
    className: "bar-track"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bar-fill",
    style: {
      width: loaded ? `${d.amount / max * 100}%` : '0%',
      background: `linear-gradient(90deg, ${d.color}55, ${d.color})`,
      transitionDelay: `${i * 120}ms`
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "bar-value"
  }, "\xA5 ", fmt(d.amount), d.count != null && /*#__PURE__*/React.createElement("div", {
    className: "bar-count"
  }, d.count, " \u7B14")))), /*#__PURE__*/React.createElement("div", {
    className: "legend"
  }, data.map(d => /*#__PURE__*/React.createElement("button", {
    key: d.key,
    className: 'legend-item' + (hidden[d.key] ? ' off' : ''),
    onClick: () => toggle(d.key),
    title: "\u70B9\u51FB\u7B5B\u9009\u663E\u793A / \u9690\u85CF"
  }, /*#__PURE__*/React.createElement("span", {
    className: "legend-swatch",
    style: {
      background: d.color
    }
  }), d.label))));
}

/* ---------- 环形图（SVG 自绘 + 悬停 tooltip + 可点击图例筛选） ---------- */
function Donut({
  data,
  size = 240,
  thickness = 34
}) {
  const [hidden, setHidden] = useState({});
  const [hover, setHover] = useState(null);
  const {
    show,
    hide,
    node
  } = useTooltip();
  const visible = data.filter(d => !hidden[d.key]);
  const total = visible.reduce((s, d) => s + d.amount, 0) || 1;
  const r = (size - thickness) / 2;
  const cx = size / 2,
    cy = size / 2;
  const toggle = k => setHidden(h => ({
    ...h,
    [k]: !h[k]
  }));

  // 逐段生成圆弧 path
  let angle = -Math.PI / 2;
  const arcs = visible.map(d => {
    const frac = d.amount / total;
    const a0 = angle,
      a1 = angle + frac * Math.PI * 2;
    angle = a1;
    const large = frac > 0.5 ? 1 : 0;
    const r0 = r,
      r1 = r + thickness;
    const p = (rr, a) => [cx + rr * Math.cos(a), cy + rr * Math.sin(a)];
    const [x0, y0] = p(r1, a0),
      [x1, y1] = p(r1, a1);
    const [x2, y2] = p(r0, a1),
      [x3, y3] = p(r0, a0);
    const path = `M ${x0} ${y0} A ${r1} ${r1} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${r0} ${r0} 0 ${large} 0 ${x3} ${y3} Z`;
    return {
      ...d,
      path,
      frac
    };
  });
  return /*#__PURE__*/React.createElement("div", {
    className: "chart-box",
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }
  }, node, /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: `0 0 ${size} ${size}`,
    role: "img",
    "aria-label": "\u652F\u51FA\u7ED3\u6784\u73AF\u5F62\u56FE"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: cx,
    cy: cy,
    r: r + thickness / 2,
    fill: "none",
    stroke: "rgba(255,255,255,.05)",
    strokeWidth: thickness
  }), arcs.map(a => /*#__PURE__*/React.createElement("path", {
    key: a.key,
    d: a.path,
    fill: a.color,
    opacity: hover === a.key ? 1 : 0.82,
    style: {
      cursor: 'pointer',
      transition: 'opacity .18s ease',
      filter: hover === a.key ? `drop-shadow(0 0 10px ${a.color})` : 'none'
    },
    onMouseEnter: () => setHover(a.key),
    onMouseLeave: () => {
      setHover(null);
      hide();
    },
    onMouseMove: e => show(e, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700
      }
    }, a.label), /*#__PURE__*/React.createElement("div", {
      className: "t-amt"
    }, "\xA5 ", fmt(a.amount)), /*#__PURE__*/React.createElement("div", {
      className: "t-dim"
    }, "\u5360\u6BD4 ", fmt(a.frac * 100, 1), "%", a.count ? ` · ${a.count} 笔` : ''), a.note && /*#__PURE__*/React.createElement("div", {
      className: "t-dim",
      style: {
        whiteSpace: 'normal',
        maxWidth: 280
      }
    }, a.note)))
  })), /*#__PURE__*/React.createElement("text", {
    x: cx,
    y: cy - 8,
    textAnchor: "middle",
    fill: "var(--text-dim)",
    fontSize: "12"
  }, "\u5408\u8BA1"), /*#__PURE__*/React.createElement("text", {
    x: cx,
    y: cy + 16,
    textAnchor: "middle",
    fill: "var(--gold)",
    fontSize: "17",
    fontWeight: "800",
    fontFamily: "var(--mono)"
  }, "\xA5 ", fmt(total))), /*#__PURE__*/React.createElement("div", {
    className: "legend"
  }, data.map(d => /*#__PURE__*/React.createElement("button", {
    key: d.key,
    className: 'legend-item' + (hidden[d.key] ? ' off' : ''),
    onClick: () => toggle(d.key),
    title: "\u70B9\u51FB\u7B5B\u9009\u663E\u793A / \u9690\u85CF"
  }, /*#__PURE__*/React.createElement("span", {
    className: "legend-swatch",
    style: {
      background: d.color
    }
  }), d.label))));
}
/* ---------- 资金流向图：简化 Sankey（资金来源 → 资金池 → 支出去向） ---------- */
function Sankey({
  inflows,
  outflows,
  pool
}) {
  const {
    show,
    hide,
    node
  } = useTooltip();
  const [focus, setFocus] = useState(null); // 'in:key' | 'out:key' | null

  const W = 1000,
    H = 560;
  const colTop = 70,
    colH = 430,
    gap = 18;
  const nodeW = 16;
  const xL = 60,
    xC = W / 2 - nodeW / 2,
    xR = W - 60 - nodeW;
  const totalIn = inflows.reduce((s, d) => s + d.amount, 0);
  const totalOut = outflows.reduce((s, d) => s + d.amount, 0);
  const scaleIn = (colH - gap * (inflows.length - 1)) / totalIn;
  const scaleOut = (colH - gap * (outflows.length - 1)) / totalOut;

  // 左侧来源节点布局
  let accY = colTop;
  const left = inflows.map(d => {
    const h = Math.max(6, d.amount * scaleIn);
    const n = {
      ...d,
      x: xL,
      y: accY,
      h
    };
    accY += h + gap;
    return n;
  });
  // 右侧去向节点布局
  accY = colTop;
  const right = outflows.map(d => {
    const h = Math.max(6, d.amount * scaleOut);
    const n = {
      ...d,
      x: xR,
      y: accY,
      h
    };
    accY += h + gap;
    return n;
  });
  const poolH = colH - gap * 2;
  const poolNode = {
    x: xC,
    y: colTop + gap,
    h: poolH
  };

  // 链接带：cubic bezier 流带（上下两条曲线围成面积）
  function band(x0, y0t, y0b, x1, y1t, y1b) {
    const mx = (x0 + x1) / 2;
    return `M ${x0} ${y0t} C ${mx} ${y0t}, ${mx} ${y1t}, ${x1} ${y1t}
            L ${x1} ${y1b} C ${mx} ${y1b}, ${mx} ${y0b}, ${x0} ${y0b} Z`;
  }

  // 左侧链接（来源 → 池）：按来源金额顺序在池左缘堆叠
  let poolInY = poolNode.y;
  const linksIn = left.map(n => {
    const h = n.h; // 同一比例视觉带宽
    const d = band(n.x + nodeW, n.y, n.y + h, poolNode.x, poolInY, poolInY + h);
    const o = {
      ...n,
      d,
      poolTop: poolInY
    };
    poolInY += h;
    return o;
  });
  // 右侧链接（池 → 去向）
  let poolOutY = poolNode.y;
  const linksOut = right.map(n => {
    const h = n.h;
    const d = band(poolNode.x + nodeW, poolOutY, poolOutY + h, n.x, n.y, n.y + h);
    const o = {
      ...n,
      d
    };
    poolOutY += h;
    return o;
  });
  const tipFor = (d, dir) => /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700
    }
  }, dir === 'in' ? '来源：' : '去向：', d.label), /*#__PURE__*/React.createElement("div", {
    className: "t-amt"
  }, "\xA5 ", fmt(d.amount)), /*#__PURE__*/React.createElement("div", {
    className: "t-dim"
  }, "\u5360", dir === 'in' ? '流入' : '流出', " ", fmt(d.amount / (dir === 'in' ? totalIn : totalOut) * 100, 1), "%", d.count ? ` · ${d.count} 笔` : ''), d.note && /*#__PURE__*/React.createElement("div", {
    className: "t-dim",
    style: {
      whiteSpace: 'normal',
      maxWidth: 300
    }
  }, d.note));
  const dimWhen = predicate => focus && !predicate ? 0.12 : 0.55;
  return /*#__PURE__*/React.createElement("div", {
    className: "chart-box"
  }, node, /*#__PURE__*/React.createElement("svg", {
    viewBox: `0 0 ${W} ${H}`,
    style: {
      width: '100%',
      height: 'auto',
      display: 'block'
    },
    role: "img",
    "aria-label": "\u8D44\u91D1\u6D41\u5411\u56FE"
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: "poolGrad",
    x1: "0",
    y1: "0",
    x2: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0%",
    stopColor: "#22d3ee"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "100%",
    stopColor: "#34d399"
  }))), /*#__PURE__*/React.createElement("text", {
    className: "sankey-stage",
    x: xL,
    y: colTop - 26
  }, "\u8D44\u91D1\u6765\u6E90 INFLOWS"), /*#__PURE__*/React.createElement("text", {
    className: "sankey-stage",
    x: xC - 40,
    y: colTop - 26
  }, "\u81EA\u6709\u8D44\u91D1\u6C60 POOL"), /*#__PURE__*/React.createElement("text", {
    className: "sankey-stage",
    x: xR - 20,
    y: colTop - 26
  }, "\u652F\u51FA\u53BB\u5411 OUTFLOWS"), linksIn.map(l => /*#__PURE__*/React.createElement("path", {
    key: 'lin' + l.key,
    className: "sankey-link",
    d: l.d,
    fill: l.color,
    opacity: focus === 'in:' + l.key ? 0.9 : dimWhen(focus === 'in:' + l.key),
    onMouseEnter: () => setFocus('in:' + l.key),
    onMouseLeave: () => {
      setFocus(null);
      hide();
    },
    onMouseMove: e => show(e, tipFor(l, 'in'))
  })), linksOut.map(l => /*#__PURE__*/React.createElement("path", {
    key: 'lout' + l.key,
    className: "sankey-link",
    d: l.d,
    fill: l.color,
    opacity: focus === 'out:' + l.key ? 0.9 : dimWhen(focus === 'out:' + l.key),
    onMouseEnter: () => setFocus('out:' + l.key),
    onMouseLeave: () => {
      setFocus(null);
      hide();
    },
    onMouseMove: e => show(e, tipFor(l, 'out'))
  })), left.map(n => /*#__PURE__*/React.createElement("g", {
    key: 'nl' + n.key,
    onMouseEnter: () => setFocus('in:' + n.key),
    onMouseLeave: () => {
      setFocus(null);
      hide();
    },
    onMouseMove: e => show(e, tipFor(n, 'in')),
    style: {
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("rect", {
    x: n.x,
    y: n.y,
    width: nodeW,
    height: n.h,
    rx: 3,
    fill: n.color,
    opacity: focus === 'in:' + n.key ? 1 : 0.9
  }), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-label",
    x: n.x - 8,
    y: n.y + n.h / 2 - 2,
    textAnchor: "end"
  }, n.label), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-amt",
    x: n.x - 8,
    y: n.y + n.h / 2 + 13,
    textAnchor: "end"
  }, "\xA5", fmt(n.amount)))), /*#__PURE__*/React.createElement("g", {
    onMouseMove: e => show(e, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700
      }
    }, "NEC \u81EA\u6709\u8D44\u91D1\u6C60"), /*#__PURE__*/React.createElement("div", {
      className: "t-amt"
    }, "\u6D41\u5165 \xA5", fmt(pool.totalIn), " = \u6D41\u51FA \xA5", fmt(pool.totalOut)), /*#__PURE__*/React.createElement("div", {
      className: "t-dim"
    }, "\u7ED3\u4F59 FCF = \xA50.00\uFF08\u6731\u4F69\u97E6\u8865\u5E73\u540E\u5F52\u96F6 \u2713\uFF09"))),
    onMouseLeave: hide,
    style: {
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("rect", {
    x: poolNode.x,
    y: poolNode.y,
    width: nodeW + 10,
    height: poolNode.h,
    rx: 5,
    fill: "url(#poolGrad)",
    opacity: "0.95"
  }), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-label",
    x: poolNode.x + nodeW / 2 + 5,
    y: poolNode.y - 12,
    textAnchor: "middle",
    fontWeight: "700"
  }, "NEC \u81EA\u6709\u8D44\u91D1\u6C60"), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-amt",
    x: poolNode.x + nodeW / 2 + 5,
    y: poolNode.y + poolNode.h + 20,
    textAnchor: "middle"
  }, "\xA5", fmt(pool.totalIn), " \u2192 FCF \xA50.00")), right.map(n => /*#__PURE__*/React.createElement("g", {
    key: 'nr' + n.key,
    onMouseEnter: () => setFocus('out:' + n.key),
    onMouseLeave: () => {
      setFocus(null);
      hide();
    },
    onMouseMove: e => show(e, tipFor(n, 'out')),
    style: {
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("rect", {
    x: n.x,
    y: n.y,
    width: nodeW,
    height: n.h,
    rx: 3,
    fill: n.color,
    opacity: focus === 'out:' + n.key ? 1 : 0.9
  }), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-label",
    x: n.x + nodeW + 8,
    y: n.y + n.h / 2 - 2
  }, n.label), /*#__PURE__*/React.createElement("text", {
    className: "sankey-node-amt",
    x: n.x + nodeW + 8,
    y: n.y + n.h / 2 + 13
  }, "\xA5", fmt(n.amount))))));
}
/* ---------- 视图①：总览 Dashboard ---------- */
function Dashboard() {
  return /*#__PURE__*/React.createElement("div", {
    className: "view-anim"
  }, /*#__PURE__*/React.createElement("div", {
    className: "grid g4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "glowline"
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-label"
  }, "\u73B0\u91D1\u6D41\u5165\u5408\u8BA1"), /*#__PURE__*/React.createElement(CountUp, {
    className: "kpi-value cyan",
    value: D.pool.totalIn,
    prefix: "\xA5 "
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-sub"
  }, D.pool.inCount, " \u7B14 \xB7 4 \u7C7B\u6765\u6E90")), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "glowline"
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-label"
  }, "\u73B0\u91D1\u6D41\u51FA\u5408\u8BA1"), /*#__PURE__*/React.createElement(CountUp, {
    className: "kpi-value pink",
    value: D.pool.totalOut,
    prefix: "\xA5 "
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-sub"
  }, "3 \u7C7B\u53BB\u5411 \xB7 \u6536\u652F\u76F8\u62B5")), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "glowline"
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-label"
  }, "\u81EA\u7531\u73B0\u91D1\u6C60\u7ED3\u4F59 FCF"), /*#__PURE__*/React.createElement(CountUp, {
    className: "kpi-value green",
    value: D.pool.fcf,
    prefix: "\xA5 "
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-sub"
  }, "\u6731\u4F69\u97E6\u8865\u5E73 \xA5374.39 \u540E\u5F52\u96F6 \u2713")), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "glowline"
  }), /*#__PURE__*/React.createElement("div", {
    className: "kpi-label"
  }, "\u52FE\u7A3D\u9A8C\u8BC1"), /*#__PURE__*/React.createElement("div", {
    className: "kpi-value gold",
    style: {
      fontSize: 20
    }
  }, "\u4E09\u8DEF\u5F84\u4E00\u81F4"), /*#__PURE__*/React.createElement("div", {
    className: "kpi-sub"
  }, "\u73B0\u91D1\u53E3\u5F84 = \u5BA1\u8BA1\u9012\u63A8 = FCFE \u6620\u5C04 = \xA50.00"))), /*#__PURE__*/React.createElement("div", {
    className: "grid g2",
    style: {
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot"
  }), "\u73B0\u91D1\u6D41\u5165\u7ED3\u6784\uFF08\u5408\u8BA1 \xA5", fmt(D.pool.totalIn), "\uFF09"), /*#__PURE__*/React.createElement(BarChart, {
    data: D.inflows,
    total: D.pool.totalIn
  })), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      background: 'var(--pink)',
      boxShadow: '0 0 10px var(--pink)'
    }
  }), "\u73B0\u91D1\u6D41\u51FA\u7ED3\u6784\uFF08\u5408\u8BA1 \xA5", fmt(D.pool.totalOut), "\uFF09"), /*#__PURE__*/React.createElement(Donut, {
    data: D.outflows
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      background: 'var(--green)',
      boxShadow: '0 0 10px var(--green)'
    }
  }), "\u52FE\u7A3D\u9A8C\u8BC1 \xB7 \u5BA1\u8BA1\u9012\u63A8\u8DEF\u5F84"), /*#__PURE__*/React.createElement("div", {
    className: "mono muted",
    style: {
      lineHeight: 2
    }
  }, "\u5BA1\u8BA1\u53E3\u5F84\u7ED3\u4F59 1,675.61 \u2212 \u738B\u8F9E\u51E1\u9000\u56DE ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--pink)'
    }
  }, "150.00"), "\u2212 27\u8D5B\u5B63 ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--pink)'
    }
  }, "900.00"), " \u5E76\u5165\u961F\u670D\u4E13\u9879 \u2212 \u5F52\u8FD8\u57AB\u4ED8 ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--pink)'
    }
  }, "1,000.00"), "+ \u6731\u4F69\u97E6\u8865\u5E73 ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--green)'
    }
  }, "374.39"), "= ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--green)',
      fontWeight: 800
    }
  }, "0.00 \u2713"))));
}

/* ---------- 视图②：资金流向 Flow ---------- */
function FlowView() {
  return /*#__PURE__*/React.createElement("div", {
    className: "view-anim"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot"
  }), "\u8D44\u91D1\u6D41\u5411\u56FE \xB7 \u8D44\u91D1\u6765\u6E90 \u2192 \u8D44\u91D1\u6C60 \u2192 \u652F\u51FA\u53BB\u5411"), /*#__PURE__*/React.createElement(Sankey, {
    inflows: D.inflows,
    outflows: D.outflows,
    pool: D.pool
  }), /*#__PURE__*/React.createElement("div", {
    className: "muted",
    style: {
      marginTop: 10
    }
  }, "\u60AC\u505C\u4EFB\u610F\u6D41\u5E26 / \u8282\u70B9\u67E5\u770B\u91D1\u989D\u4E0E\u5360\u6BD4\u660E\u7EC6\u3002")), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      background: 'var(--green)',
      boxShadow: '0 0 10px var(--green)'
    }
  }), "\u52FE\u7A3D\u8DEF\u5F84\u9A8C\u8BC1 \xB7 \u4E09\u7EBF\u5F52\u96F6"), D.reconciliation.paths.map(p => /*#__PURE__*/React.createElement("div", {
    className: "recon-row",
    key: p.key
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "recon-name"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      width: 7,
      height: 7,
      borderRadius: '50%',
      background: 'var(--green)',
      display: 'inline-block'
    }
  }), p.name), /*#__PURE__*/React.createElement("div", {
    className: "recon-formula"
  }, p.formula)), /*#__PURE__*/React.createElement("div", {
    className: "recon-result"
  }, "= \xA5 ", fmt(p.result), " \u2713"))), /*#__PURE__*/React.createElement("div", {
    className: "balance-strip"
  }, /*#__PURE__*/React.createElement("span", {
    className: "muted"
  }, "\u4E09\u6761\u52FE\u7A3D\u8DEF\u5F84\uFF08\u73B0\u91D1\u53E3\u5F84 / \u5BA1\u8BA1\u9012\u63A8 / FCFE \u6620\u5C04\uFF09\u4E92\u76F8\u9A8C\u8BC1\uFF0C\u7ED3\u679C\u4E00\u81F4"), /*#__PURE__*/React.createElement("span", {
    className: "b-num"
  }, "\u5DEE\u989D \xA5 0.00 \u2713"))));
}

/* ---------- 视图③：体外专项 ---------- */
function OffbookView() {
  const total = D.offbook.reduce((s, d) => s + d.amount, 0);
  const chartData = D.offbook.map(d => ({
    key: d.key,
    label: d.name,
    amount: d.amount,
    count: null,
    note: d.note,
    color: d.color
  }));
  return /*#__PURE__*/React.createElement("div", {
    className: "view-anim"
  }, /*#__PURE__*/React.createElement("div", {
    className: "muted",
    style: {
      marginBottom: 14
    }
  }, "\u4EE5\u4E0B ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--gold)'
    }
  }, "7 \u9879"), " \u4E3A\u4F53\u5916 / \u4E13\u9879\u72EC\u7ACB\u6838\u7B97\uFF0C", /*#__PURE__*/React.createElement("b", null, "\u4E0D\u8BA1\u5165\u4E3B\u8D26"), "\u81EA\u6709\u8D44\u91D1\u6C60\uFF1B\u5408\u8BA1\u89C4\u6A21", /*#__PURE__*/React.createElement("span", {
    className: "mono",
    style: {
      color: 'var(--cyan)'
    }
  }, " \xA5 ", fmt(total)), "\uFF08\u542B\u975E\u73B0\u91D1\u53E3\u5F84\uFF09\u3002"), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot"
  }), "\u4F53\u5916 / \u4E13\u9879\u89C4\u6A21\u5BF9\u6BD4"), /*#__PURE__*/React.createElement(BarChart, {
    data: chartData,
    total: total
  })), /*#__PURE__*/React.createElement("div", {
    className: "grid g3"
  }, D.offbook.map(d => /*#__PURE__*/React.createElement("div", {
    className: "card",
    key: d.key
  }, /*#__PURE__*/React.createElement("div", {
    className: "kpi-label",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "legend-swatch",
    style: {
      background: d.color
    }
  }), d.name), /*#__PURE__*/React.createElement("div", {
    className: "offbook-amt"
  }, "\xA5 ", /*#__PURE__*/React.createElement(CountUp, {
    value: d.amount,
    duration: 1100
  })), /*#__PURE__*/React.createElement("div", {
    className: "offbook-note"
  }, d.note)))));
}

/* ---------- 视图④：27赛季专项勾稽 ---------- */
function S27View() {
  return /*#__PURE__*/React.createElement("div", {
    className: "view-anim"
  }, /*#__PURE__*/React.createElement("div", {
    className: "grid g2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      background: 'var(--green)',
      boxShadow: '0 0 10px var(--green)'
    }
  }), "\u8D44\u91D1\u6765\u6E90 \xB7 \u5408\u8BA1 \xA5", fmt(D.s27.totalSources)), /*#__PURE__*/React.createElement(BarChart, {
    data: D.s27.sources.map(s => ({
      ...s,
      count: null
    })),
    total: D.s27.totalSources
  })), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("h3", null, /*#__PURE__*/React.createElement("span", {
    className: "dot",
    style: {
      background: 'var(--orange)',
      boxShadow: '0 0 10px var(--orange)'
    }
  }), "\u4E13\u9879\u652F\u51FA \xB7 \u5408\u8BA1 \xA5", fmt(D.s27.totalSpends)), /*#__PURE__*/React.createElement(BarChart, {
    data: D.s27.spends.map(s => ({
      ...s,
      count: null
    })),
    total: D.s27.totalSpends
  }))), /*#__PURE__*/React.createElement("div", {
    className: "balance-strip"
  }, /*#__PURE__*/React.createElement("span", {
    className: "muted"
  }, "\u6765\u6E90 \xA5", fmt(D.s27.totalSources), "\uFF08\u793E\u533A\u52DF\u96C6 900 + \u961F\u670D\u4E13\u9879\u8D5E\u52A9 2,151.50 + DarrenPig \u8D5E\u52A9 606.01\uFF09 = \u652F\u51FA \xA5", fmt(D.s27.totalSpends), "\uFF086 \u9879\uFF09"), /*#__PURE__*/React.createElement("span", {
    className: "b-num"
  }, "\u5DEE\u989D \xA5 ", fmt(D.s27.diff), " \u2713 \u5DF2\u5E73\u8861")));
}

/* ---------- 视图⑤：遗留待办 ---------- */
function TodosView() {
  return /*#__PURE__*/React.createElement("div", {
    className: "view-anim"
  }, /*#__PURE__*/React.createElement("div", {
    className: "muted",
    style: {
      marginBottom: 14
    }
  }, "\u5BA1\u8BA1\u9057\u7559\u5F85\u529E ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--gold)'
    }
  }, "4 \u9879"), "\uFF0C\u5747\u4E0D\u5F71\u54CD\u4E3B\u8D26\u52FE\u7A3D\u7ED3\u8BBA\uFF0C\u9700\u8D23\u4EFB\u65B9\u8865\u5145\u51ED\u8BC1 / \u4E66\u9762\u786E\u8BA4\u540E\u5173\u95ED\u3002"), /*#__PURE__*/React.createElement("div", {
    className: "grid g2"
  }, D.todos.map(t => /*#__PURE__*/React.createElement("div", {
    className: "card",
    key: t.code
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "todo-code"
  }, t.code), /*#__PURE__*/React.createElement("span", {
    className: `todo-level ${t.level}`
  }, "\u4F18\u5148\u7EA7 \xB7 ", t.level)), /*#__PURE__*/React.createElement("div", {
    className: "todo-title"
  }, t.title), /*#__PURE__*/React.createElement("div", {
    className: "todo-desc"
  }, t.desc)))));
}

/* ---------- App ---------- */
const TABS = [{
  key: 'dashboard',
  label: '① 总览 Dashboard'
}, {
  key: 'flow',
  label: '② 资金流向 Flow'
}, {
  key: 'offbook',
  label: '③ 体外专项'
}, {
  key: 's27',
  label: '④ 27赛季专项勾稽'
}, {
  key: 'todos',
  label: '⑤ 遗留待办'
}];
function App() {
  const [tab, setTab] = useState('dashboard');
  return /*#__PURE__*/React.createElement("div", {
    className: "wrap"
  }, /*#__PURE__*/React.createElement("header", {
    className: "hero"
  }, /*#__PURE__*/React.createElement("div", {
    className: "brand"
  }, /*#__PURE__*/React.createElement("div", {
    className: "logo"
  }, "F\xA5"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", null, D.meta.title), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, D.meta.subtitle))), /*#__PURE__*/React.createElement("div", {
    className: "badges"
  }, /*#__PURE__*/React.createElement("span", {
    className: "badge ok"
  }, "\u2713 \u5DF2\u5BA1\u8BA1\u786E\u8BA4"), /*#__PURE__*/React.createElement("span", {
    className: "badge ok"
  }, "\u2713 \u4E09\u8DEF\u5F84\u52FE\u7A3D = \xA50.00"), /*#__PURE__*/React.createElement("span", {
    className: "badge gold"
  }, "\u6536\u4ED8\u5B9E\u73B0\u5236 \xB7 \u73B0\u91D1\u53E3\u5F84"), /*#__PURE__*/React.createElement("span", {
    className: "badge"
  }, "AS-OF ", D.meta.asOf), /*#__PURE__*/React.createElement("span", {
    className: "badge"
  }, "MIT License"))), /*#__PURE__*/React.createElement("nav", {
    className: "tabs"
  }, TABS.map(t => /*#__PURE__*/React.createElement("button", {
    key: t.key,
    className: 'tab' + (tab === t.key ? ' active' : ''),
    onClick: () => setTab(t.key)
  }, t.label))), /*#__PURE__*/React.createElement("main", null, tab === 'dashboard' && /*#__PURE__*/React.createElement(Dashboard, null), tab === 'flow' && /*#__PURE__*/React.createElement(FlowView, null), tab === 'offbook' && /*#__PURE__*/React.createElement(OffbookView, null), tab === 's27' && /*#__PURE__*/React.createElement(S27View, null), tab === 'todos' && /*#__PURE__*/React.createElement(TodosView, null)), /*#__PURE__*/React.createElement("footer", null, /*#__PURE__*/React.createElement("div", null, "FinFlow \xB7 CURC26 \u8D22\u52A1\u5F00\u6E90\u53EF\u89C6\u5316 \u2014 \u5E38\u5DDE\u5DE5 NEC \u673A\u5668\u4EBA\u961F 2026 \u8D5B\u5B63"), /*#__PURE__*/React.createElement("div", null, "\u6570\u636E\u53E3\u5F84\uFF1A\u6536\u4ED8\u5B9E\u73B0\u5236 \xB7 \u73B0\u91D1\u53E3\u5F84 \xB7 \u6570\u636E\u622A\u81F3 ", D.meta.asOf, " \xB7 \u6570\u5B57\u7ECF\u5BA1\u8BA1\u786E\u8BA4\uFF0C\u672A\u7ECF\u8BB8\u53EF\u4E0D\u5F97\u6539\u52A8"), /*#__PURE__*/React.createElement("div", null, "\u5F00\u6E90\u534F\u8BAE\uFF1AMIT License \xB7 \u7EAF\u524D\u7AEF\u5355\u6587\u4EF6\u5E94\u7528\uFF08React 18 + Babel standalone + \u81EA\u7ED8 SVG\uFF09\uFF0C\u65E0\u91CD\u578B\u56FE\u8868\u5E93\u4F9D\u8D56")));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(App, null));