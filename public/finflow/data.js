/**
 * FinFlow · CURC26 财务开源可视化 —— 数据模块
 * 数据口径：收付实现制 · 现金口径 · 已审计确认
 * 数据截至：2026-07-25
 * 单位：人民币元（CNY）
 *
 * 本文件为纯数据模块，挂载到 window.FINFLOW_DATA，index.html 直接引用。
 * 数字经审计确认，修改前请与出纳/审计双线核对。
 */
(function (global) {
  'use strict';

  var FINFLOW_DATA = {
    meta: {
      project: 'FinFlow',
      title: 'FinFlow · CURC26 财务开源可视化',
      subtitle: '常州工 NEC 机器人队 · 2026 赛季 · 收付实现制·现金口径 · 数据截至 2026-07-25',
      team: '常州工 NEC 机器人队',
      season: '2026 赛季（CURC26）',
      basis: '收付实现制 · 现金口径',
      asOf: '2026-07-25',
      currency: 'CNY'
    },

    /* ===== 主账：NEC 自有资金池（现金口径） ===== */
    inflows: [
      {
        key: 'crowd_mid',
        label: '26赛季中期后众筹',
        amount: 10800.00,
        count: 36,
        note: '2026.04.30 – 05.10',
        color: '#22d3ee'
      },
      {
        key: 'sponsor',
        label: 'Sponsor 赞助',
        amount: 8400.00,
        count: 5,
        note: '李俊杰 / 王辞凡 / 孙振祥 / 沈家耀 / 王浩',
        color: '#34d399'
      },
      {
        key: 'crowd_jul',
        label: '7月队内众筹（净）',
        amount: 6600.00,
        count: 44,
        note: '毛收 6,750（含李畅畅 150 自27赛季归入）− 王辞凡退回 150',
        color: '#a78bfa'
      },
      {
        key: 'zhu_fill',
        label: '朱佩韦补平缺口',
        amount: 374.39,
        count: 1,
        note: '2026-07-25 垫资/捐助，补平后资金池归零',
        color: '#fbbf24'
      }
    ],

    outflows: [
      {
        key: 'mid_cash',
        label: '中期支出现金部分',
        amount: 19200.00,
        count: null,
        note: '账面 23,612.71 − 关联方直接承担 4,412.71',
        color: '#f472b6'
      },
      {
        key: 'jul_spend',
        label: '7月支出细目',
        amount: 5974.39,
        count: 44,
        note: '44 笔日常支出',
        color: '#fb923c'
      },
      {
        key: 'repay_sun',
        label: '归还孙诗睿垫付余款',
        amount: 1000.00,
        count: 1,
        note: '2026-07-25',
        color: '#60a5fa'
      }
    ],

    pool: {
      totalIn: 26174.39,
      totalOut: 26174.39,
      inCount: 86,
      fcf: 0.00,
      note: '朱佩韦 2026-07-25 补平 374.39 后，自由现金池结余 FCF = 0.00 ✓'
    },

    /* 三路径勾稽验证（均为 0.00） */
    reconciliation: {
      paths: [
        {
          key: 'cash',
          name: '现金口径',
          formula: '流入 26,174.39 − 流出 26,174.39',
          result: 0.00
        },
        {
          key: 'audit',
          name: '审计递推',
          formula: '1,675.61 − 王辞凡退回 150 − 27赛季 900 并入队服专项 − 归还垫付 1,000 + 朱佩韦补平 374.39',
          result: 0.00
        },
        {
          key: 'fcfe',
          name: 'FCFE 映射',
          formula: '自由现金流 FCF（补平后资金池归零）',
          result: 0.00
        }
      ]
    },

    /* ===== 体外 / 专项独立核算（7 项，不计入主账） ===== */
    offbook: [
      {
        key: 'reimbursed',
        name: '已报销账目（三次）',
        amount: 18148.38,
        note: '学校 / 项目经费，✔ 按源文件口径',
        color: '#22d3ee'
      },
      {
        key: 'volleyball',
        name: '排球独立资金',
        amount: 1250.00,
        note: '450 在 LWC 彭柯尹处，800 在吴梦婷处用于开销支出；王辞凡 150 已由朱佩韦退回',
        color: '#34d399'
      },
      {
        key: 'sun_advance',
        name: '孙诗睿垫付',
        amount: 2561.27,
        note: '25 笔小票无发票；✔ 全部结清：1,561.27 经7月支出归还 + 余款 1,000 于 7-25 从资金池归还',
        color: '#a78bfa'
      },
      {
        key: 'jersey',
        name: '队服专项',
        amount: 2151.50,
        note: '赞助 = 采购收支相抵；27赛季募集 900 已并入本专项单独管理',
        color: '#fbbf24'
      },
      {
        key: 'related_party',
        name: '横向项目捐助（关联方承担）',
        amount: 4412.71,
        note: '非现金，不纳入自有资金流入',
        color: '#f472b6'
      },
      {
        key: 'lodging',
        name: '住宿位捐助 / 垫付',
        amount: 3060.00,
        note: '5 个住宿位；住宿全款 8,100 已由朱佩韦向江阴泓昇苑酒店付清，队员交费 6,000 = 20人×300，侯佳奕/杨万洁退回，朱佩韦垫付缺口 2,100',
        color: '#fb923c'
      },
      {
        key: 'battery',
        name: '电池类捐助',
        amount: 1193.16,
        note: '5 笔淘宝订单；另有 1 笔 70.24 交易关闭不计入',
        color: '#60a5fa'
      }
    ],

    /* ===== 27赛季专项勾稽（已平衡，差额 0） ===== */
    s27: {
      sources: [
        { key: 's27_crowd', label: '27赛季社区募集', amount: 900.00, note: '6人 × 150；李畅畅 150 已归 7月众筹', color: '#34d399' },
        { key: 's27_jersey', label: '队服专项赞助', amount: 2151.50, note: '定向覆盖队服专项支出', color: '#fbbf24' },
        { key: 's27_darren', label: 'DarrenPig（朱佩韦）Sponsor 赞助', amount: 606.01, note: '', color: '#22d3ee' }
      ],
      spends: [
        { key: 'sp_jersey', label: '队服专项支出', amount: 2151.50, note: '专项赞助 2,151.50 定向覆盖', color: '#fbbf24' },
        { key: 'sp_polo', label: '索洛纳 Polo 队服样板费用', amount: 221.00, note: '', color: '#22d3ee' },
        { key: 'sp_vest', label: '背心打板', amount: 232.00, note: '', color: '#34d399' },
        { key: 'sp_figure', label: 'NEC 社区文创手办打板', amount: 195.00, note: '89 + 88 + 18', color: '#a78bfa' },
        { key: 'sp_gloves', label: '文创手套', amount: 178.01, note: '120 + 58.01', color: '#f472b6' },
        { key: 'sp_whitepaper', label: '白皮书设计', amount: 680.00, note: '50 + 420 + 160 + 50', color: '#fb923c' }
      ],
      totalSources: 3657.51,
      totalSpends: 3657.51,
      diff: 0.00
    },

    /* ===== 遗留待办（4 项） ===== */
    todos: [
      {
        code: 'EX-03',
        title: '第二次报销差 6.93',
        desc: '逐项合计 5,721.57 vs 表内 5,728.50，需逐项复核差异来源。',
        level: '低'
      },
      {
        code: 'EX-04',
        title: '中期三笔「转账孙诗睿」合计 6,600',
        desc: '需采购凭证排除与大疆 3,300 重复计列。',
        level: '高'
      },
      {
        code: 'EX-05',
        title: '中期支出笔数不一致',
        desc: '声称 20 笔仅列示 16 笔，需出纳补充缺失明细。',
        level: '中'
      },
      {
        code: 'EX-02',
        title: '关联方承担口径不一致',
        desc: '4,412.71 vs 7,472.71，需横向项目负责人书面确认。',
        level: '高'
      }
    ]
  };

  /* 内部一致性自检（加载时打印到控制台，便于审计复核） */
  function sum(list) {
    return list.reduce(function (acc, x) { return acc + x.amount; }, 0);
  }
  var inSum = sum(FINFLOW_DATA.inflows);
  var outSum = sum(FINFLOW_DATA.outflows);
  var s27src = sum(FINFLOW_DATA.s27.sources);
  var s27spd = sum(FINFLOW_DATA.s27.spends);
  FINFLOW_DATA._check = {
    inflowSum: Math.round(inSum * 100) / 100,
    outflowSum: Math.round(outSum * 100) / 100,
    inflowBalanced: Math.abs(inSum - FINFLOW_DATA.pool.totalIn) < 0.005,
    outflowBalanced: Math.abs(outSum - FINFLOW_DATA.pool.totalOut) < 0.005,
    s27SourcesSum: Math.round(s27src * 100) / 100,
    s27SpendsSum: Math.round(s27spd * 100) / 100,
    s27Balanced: Math.abs(s27src - s27spd) < 0.005
  };
  if (global.console && console.log) {
    console.log('[FinFlow] 数据自检：', FINFLOW_DATA._check);
  }

  global.FINFLOW_DATA = FINFLOW_DATA;
})(typeof window !== 'undefined' ? window : globalThis);
