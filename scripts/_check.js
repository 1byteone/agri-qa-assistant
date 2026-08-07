
/* ═══════════════════════════════════════════════════════════════
   数字孪生 Pro — 事件驱动架构 + 实时数据 + 高级视觉效果
   ═══════════════════════════════════════════════════════════════ */

// ── 工具函数 ──
const fmtNum = (n) => {
  if (n == null || isNaN(n)) return '--';
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿';
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万';
  return n.toLocaleString('zh-CN');
};
const fmtNumRaw = (n) => n == null || isNaN(n) ? '--' : n.toLocaleString('zh-CN',{maximumFractionDigits:1});
const clamp = (v,min,max) => Math.max(min,Math.min(max,v));

// ── 全局 ErrorBoundary ──
(function initErrorBoundary() {
  const toast = document.getElementById('error-toast');
  let timer = null;
  const show = (msg) => {
    toast.textContent = '⚠ ' + (msg || '未知错误');
    toast.style.display = 'block';
    clearTimeout(timer);
    timer = setTimeout(() => { toast.style.display = 'none'; }, 5000);
  };
  window.addEventListener('error', (e) => { show(e.message || 'Runtime Error'); console.error('[ErrorBoundary]', e); });
  window.addEventListener('unhandledrejection', (e) => { show(e.reason?.message || 'Unhandled Promise'); console.error('[ErrorBoundary]', e); });
  window.__showError = show;
})();

// ── FPS 计数器 ──
(function initFPS() {
  let frames = 0, last = performance.now();
  const el = document.getElementById('fps-counter');
  const tick = () => {
    frames++;
    const now = performance.now();
    if (now - last >= 1000) {
      el.textContent = frames + ' FPS';
      frames = 0; last = now;
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();

// ── DataStore: 增强版状态管理 + 事件总线 ──
const DataStore = (() => {
  const _state = {
    year: 2024, metric: 'production', mapRotating: false,
    rawData: null, _loading: false, _ready: false,
    // 实时数据历史
    _history: { total_production: [], total_area: [], food_production_pct: [], economic_production_pct: [] },
    _realtimeInterval: null,
  };
  const _listeners = new Map();

  return {
    get(key) { return _state[key]; },
    set(key, val) {
      const old = _state[key];
      if (old === val) return;
      _state[key] = val;
      this.emit('change:' + key, val, old);
      this.emit('change', { key, val, old });
    },
    on(event, fn) {
      if (!_listeners.has(event)) _listeners.set(event, new Set());
      _listeners.get(event).add(fn);
      return () => _listeners.get(event)?.delete(fn);
    },
    emit(event, ...args) {
      _listeners.get(event)?.forEach(fn => fn(...args));
    },
    getKPI() { const d = _state.rawData; return d ? d.kpi[_state.year] : null; },
    getYoY() { const d = _state.rawData; return d ? d.yoy : null; },
    getCategories() { const d = _state.rawData; return d ? d.categories[_state.year] : null; },
    getRankings() {
      const d = _state.rawData;
      if (!d) return null;
      const key = _state.metric === 'production' ? 'production_by_crop' : 'area_by_crop';
      return d[key][_state.year];
    },
    getProvinceData() {
      const d = _state.rawData;
      if (!d) return null;
      return d.province.filter(p => p.year === _state.year && p.province !== '全国');
    },
    getHistory(key) { return _state._history[key] || []; },
    // 实时数据引擎
    startRealtime() {
      if (_state._realtimeInterval) return;
      _state._realtimeInterval = setInterval(() => {
        const kpi = this.getKPI();
        if (!kpi) return;
        // 对每个 KPI 生成 ±2% 波动
        const keys = ['total_production','total_area','food_production_pct','economic_production_pct'];
        keys.forEach(k => {
          const delta = (Math.random() - 0.5) * 0.04; // ±2%
          const newVal = kpi[k] * (1 + delta);
          kpi[k] = Math.max(0, newVal);
          // 写入历史
          const hist = _state._history[k];
          hist.push(kpi[k]);
          if (hist.length > 20) hist.shift();
        });
        this.emit('realtime:update', kpi);
      }, 3000);
    },
    stopRealtime() {
      if (_state._realtimeInterval) {
        clearInterval(_state._realtimeInterval);
        _state._realtimeInterval = null;
      }
    },
    async load() {
      if (_state._loading) return;
      _state._loading = true;
      let lastErr = null;
      // 3 次重试
      for (let i = 0; i < 3; i++) {
        try {
          const resp = await fetch('dashboard_data.json');
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          _state.rawData = await resp.json();
          _state._ready = true;
          this.emit('ready');
          return;
        } catch (err) {
          lastErr = err;
          console.warn('[DataStore] 重试 ' + (i+1) + '/3:', err.message);
          if (i < 2) await new Promise(r => setTimeout(r, (i+1) * 1000));
        }
      }
      throw lastErr || new Error('数据加载失败');
    },
    isReady() { return _state._ready; },
  };
})();

// ── 数字动画 ──
const _animFrames = {};
const animateNumber = (el, target, suffix = '', duration = 800) => {
  const key = el.dataset.animKey || (el.dataset.animKey = Math.random().toString(36).slice(2));
  if (_animFrames[key]) { cancelAnimationFrame(_animFrames[key]); delete _animFrames[key]; }
  const start = performance.now();
  const from = parseFloat(el.dataset.lastVal) || 0;
  el.dataset.lastVal = target;
  if (from === target) return;
  const tick = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = from + (target - from) * eased;
    el.textContent = fmtNum(val) + suffix;
    if (t < 1) _animFrames[key] = requestAnimationFrame(tick);
    else { el.textContent = fmtNum(target) + suffix; delete _animFrames[key]; }
  };
  _animFrames[key] = requestAnimationFrame(tick);
};

// ── 背景粒子 Canvas 增强版 ──
const initBgCanvas = () => {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  let w, h, particles = [];
  const resize = () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; };
  const create = () => {
    particles = [];
    for (let i = 0; i < 100; i++) {
      particles.push({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2,
        r: Math.random() * 2 + 0.5,
        a: Math.random() * 0.3 + 0.1,
        hue: Math.random() < 0.5 ? 170 : 220, // 青/蓝
      });
    }
  };
  resize(); create();
  const draw = () => {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue},80%,60%,${p.a})`;
      ctx.fill();
    });
    // 连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0,212,170,${0.05 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  };
  draw();
  window.addEventListener('resize', () => { resize(); create(); });
};

// ── MapModule: ECharts GL 3D 地图 + 飞线 ──
const MapModule = (() => {
  let chart = null;
  let geoJSON = null;
  let _updateId = 0;
  let _flylineEnabled = true;

  const MAP_VIEW = { center: [104.5, 35.5, 0], alpha: 0, beta: 89.5 };
  const calcDistance = () => {
    const mw = Math.max(window.innerWidth - 400, 400);
    return Math.min(50, Math.max(18, mw * 0.028));
  };

  const filterValid = (data, metric) =>
    data.filter(p => { const v = metric === 'production' ? p.production : p.area; return v != null && v > 0; });

  const getMapData = () => {
    const raw = DataStore.getProvinceData();
    if (!raw) return [];
    const valid = filterValid(raw, DataStore.get('metric'));
    const metric = DataStore.get('metric');
    return valid.map(p => ({
      name: p.provinceFull,
      value: metric === 'production' ? p.production : p.area,
      province: p.province,
    }));
  };

  const getColorRange = (metric) => {
    // 色块不透明度整体提高（polygons3D 无阴影面时低透明度会近乎不可见）
    if (metric === 'production')
      return ['rgba(0,212,170,0.35)','rgba(0,212,170,0.55)','rgba(245,158,11,0.7)','rgba(245,158,11,0.95)'];
    return ['rgba(59,130,246,0.35)','rgba(59,130,246,0.55)','rgba(139,92,246,0.7)','rgba(139,92,246,0.95)'];
  };

  // 生成飞线数据
  const getFlylineData = () => {
    // 10 个主要省份 → 北京/上海/广州
    const hubs = { '北京': [116.4,39.9], '上海': [121.5,31.2], '广州': [113.3,23.1] };
    const centers = {
      '山东': [117.0,36.7], '河南': [113.7,33.9], '四川': [104.1,30.6],
      '江苏': [119.8,33.0], '河北': [114.5,38.0], '湖南': [112.0,27.6],
      '安徽': [117.3,31.9], '湖北': [112.2,31.0], '浙江': [120.2,29.5],
      '广东': [113.5,23.5],
    };
    const data = [];
    const hubNames = Object.keys(hubs);
    Object.entries(centers).forEach(([prov, coord]) => {
      const target = hubNames[Math.floor(Math.random() * hubNames.length)];
      data.push({
        coords: [coord, hubs[target]],
        lineStyle: { color: Math.random() < 0.5 ? '#00d4aa' : '#3b82f6', opacity: 0.6, width: Math.random() * 2 + 1 },
      });
    });
    return data;
  };

  const render = async () => {
    const id = ++_updateId;
    const dom = document.getElementById('map-chart');
    if (!chart) chart = echarts.init(dom);

    if (!geoJSON) {
      try {
        const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json');
        geoJSON = await resp.json();
        echarts.registerMap('china', geoJSON);
      } catch (e) {
        console.error('GeoJSON 加载失败:', e);
        return;
      }
    }
    if (id !== _updateId) return;

    const mapData = getMapData();
    const values = mapData.map(d => d.value).filter(v => v > 0);
    const maxVal = values.length > 0 ? Math.max(...values) : 1;
    const minVal = values.length > 0 ? Math.min(...values) : 0;
    const metric = DataStore.get('metric');
    const label = metric === 'production' ? '产量' : '面积';
    const unit = metric === 'production' ? '吨' : '亩';

    // 省份名规范化：GeoJSON properties.name 是全名（如“山东省”），dashboard 的 province 是简称（如“山东”）
    // 用同一个 normalize 收敛两侧，保证 value 能按省正确映射（否则全部无色块）
    const normalizeName = (n) => String(n || '')
      .replace(/特别行政区$/, '')
      .replace(/(维吾尔|壮族|回族)?自治区$/, '')
      .replace(/[省市]$/, '');
    const valueByName = {};
    mapData.forEach(d => {
      valueByName[normalizeName(d.name)] = d.value;
      valueByName[normalizeName(d.province)] = d.value;
    });

    // polygons3D 系列：各省色块（替代 map3D 的着色功能），coords 直接取 GeoJSON geometry.coordinates
    const polygonsData = geoJSON.features.map(f => ({
      name: f.properties.name,
      value: valueByName[normalizeName(f.properties.name)] || 0,
      coords: f.geometry.coordinates,
      multiPolygon: f.geometry.type === 'MultiPolygon',
    }));

    // 单次 setOption 一次性提交 geo3D 组件 + polygons3D + lines3D，
    // 三者共享同一个显式 geo3D 坐标系（map3D 系列自建坐标系不与 lines3D 共存，会抛 geo "0" not found）
    const regionHeight = metric === 'production' ? 1 : 0.8;
    const series = [
      {
        id: 'polygons3d',
        type: 'polygons3D',
        coordinateSystem: 'geo3D',
        regionHeight: regionHeight, // polygons3D 自身读取 regionHeight 决定挤出高度
        shading: 'lambert',
        data: polygonsData,
        label: { show: false }, // 省名由 geo3D 组件显示，避免重复
        itemStyle: { borderWidth: 0.5, borderColor: 'rgba(0,212,170,0.25)' },
        emphasis: { itemStyle: { color: '#00d4aa' }, label: { show: true } },
      },
    ];
    // lines3D 飞线：关闭时置空 data（merge 模式下不传该系列会残留旧数据）
    series.push({
      id: 'lines3d',
      type: 'lines3D',
      coordinateSystem: 'geo3D',
      effect: {
        show: _flylineEnabled,
        trailWidth: 3, trailLength: 0.3, trailOpacity: 0.8, trailColor: '#00d4aa', period: 4,
      },
      lineStyle: { width: 2, opacity: 0.4, color: '#3b82f6' },
      data: _flylineEnabled ? getFlylineData() : [],
    });

    chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (p) => {
          const d = p.data || {};
          const v = d.value || 0;
          if (v <= 0) return `<strong>${d.name || p.name}</strong><br/>数据暂缺`;
          return `<strong>${d.name || p.name}</strong><br/>${label}：${fmtNumRaw(v)} ${unit}`;
        },
        backgroundColor: 'rgba(5,10,24,0.85)',
        borderColor: 'rgba(0,212,170,0.3)',
        textStyle: { color: '#e8edf5', fontSize: 13 },
      },
      visualMap: {
        min: minVal, max: maxVal,
        text: ['高','低'],
        textStyle: { color: '#556077' },
        inRange: { color: getColorRange(metric) },
        calculable: true,
        left: 'left', bottom: 40,
        itemWidth: 12, itemHeight: 100,
        seriesIndex: 0, // 只作用于 polygons3D，避免影响 lines3D
      },
      geo3D: {
        id: 'geo3d',
        map: 'china',
        shading: 'lambert',
        boxWidth: 120,
        boxHeight: 8,
        regionHeight: regionHeight,
        environment: '#050a18',
        groundPlane: { show: true, color: '#050a18' },
        light: {
          main: { intensity: 1.2, shadow: true, shadowQuality: 'high', alpha: 30, beta: 40 },
          ambient: { intensity: 0.6 },
        },
        viewControl: {
          projection: 'perspective',
          autoRotate: DataStore.get('mapRotating'),
          autoRotateDirection: 'right',
          autoRotateSpeed: 2,
          distance: calcDistance(),
          minDistance: 15, maxDistance: 150,
          alpha: MAP_VIEW.alpha,
          beta: MAP_VIEW.beta,
          center: MAP_VIEW.center,
          animationDurationUpdate: 1000,
          animationEasingUpdate: 'cubicOut',
          damping: 0.85,
          rotateSensitivity: 1.0,
          zoomSensitivity: 1.0,
          panSensitivity: 0,
        },
        label: {
          show: true, color: '#e8edf5', fontSize: 10,
          textStyle: { textShadowColor: 'rgba(0,0,0,0.8)', textShadowBlur: 4 },
        },
        itemStyle: { color: 'rgba(10,20,45,0.55)', borderColor: 'rgba(0,212,170,0.25)', borderWidth: 0.5 },
        emphasis: {
          label: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
          itemStyle: { borderColor: '#00d4aa', borderWidth: 2 },
        },
      },
      series,
    });
  };

  const init = async () => { await render(); };
  const resize = () => {
    if (!chart) return;
    chart.setOption({ geo3D: { id: 'geo3d', viewControl: { distance: calcDistance(), center: MAP_VIEW.center } } });
    chart.resize();
  };
  const locate = () => {
    if (!chart) return;
    chart.setOption({
      geo3D: {
        id: 'geo3d',
        viewControl: {
          center: MAP_VIEW.center, alpha: MAP_VIEW.alpha, beta: MAP_VIEW.beta,
          distance: calcDistance(), autoRotate: DataStore.get('mapRotating'),
          animationDurationUpdate: 800, animationEasingUpdate: 'cubicOut',
        }
      }
    });
  };
  const toggleRotate = () => {
    const r = !DataStore.get('mapRotating');
    DataStore.set('mapRotating', r);
    if (chart) chart.setOption({ geo3D: { id: 'geo3d', viewControl: { autoRotate: r } } });
    return r;
  };
  const toggleFlyline = () => {
    _flylineEnabled = !_flylineEnabled;
    render();
    return _flylineEnabled;
  };

  return { init, resize, locate, toggleRotate, toggleFlyline, render };
})();

// ── ScanRing: CSS 扫描光圈叠加层（纯 CSS，零 WebGL 开销，避免与 ECharts GL 双上下文冲突） ──
const ScanRing = (() => {
  let initialized = false;

  const init = async () => {
    if (initialized) return;
    initialized = true;
    // CSS 动画已由 <style> 中的 .scan-ring 规则驱动，无需 JS
  };

  const resize = () => { /* CSS 自动适配，无需处理 */ };

  return { init, resize };
})();

// ── KPIModule 增强版 ──
const KPIModule = (() => {
  const METRICS = [
    { key: 'total_production', label: '总产量', unit: '吨', yoyKey: 'production_change_pct' },
    { key: 'total_area', label: '总面积', unit: '亩', yoyKey: 'area_change_pct' },
    { key: 'food_production_pct', label: '粮食占比', unit: '%', yoyKey: 'food_production_change_pct', isPct: true },
    { key: 'economic_production_pct', label: '经济作物占比', unit: '%', yoyKey: 'economic_production_change_pct', isPct: true },
  ];

  const renderSparkline = (key, values) => {
    if (!values || values.length < 2) return '';
    const w = 80, h = 16;
    const max = Math.max(...values), min = Math.min(...values);
    const range = max - min || 1;
    const points = values.map((v, i) => `${i * (w / (values.length - 1))},${h - ((v - min) / range) * h}`).join(' ');
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" class="kpi-sparkline">
      <polyline points="${points}" fill="none" stroke="#00d4aa" stroke-width="1.5" opacity="0.6"/>
      <polygon points="${points} ${w},${h} 0,${h}" fill="url(#grad-${key})" opacity="0.15"/>
      <defs><linearGradient id="grad-${key}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#00d4aa"/><stop offset="100%" stop-color="transparent"/>
      </linearGradient></defs>
    </svg>`;
  };

  const render = () => {
    const kpi = DataStore.getKPI();
    const yoy = DataStore.getYoY();
    if (!kpi) return;
    const grid = document.getElementById('kpi-grid');
    grid.innerHTML = METRICS.map(m => {
      const val = kpi[m.key] || 0;
      const yoyVal = yoy[m.yoyKey];
      const yoyClass = yoyVal != null ? (yoyVal >= 0 ? 'up' : 'down') : '';
      const yoyArrow = yoyVal != null ? (yoyVal >= 0 ? '&#x25B2;' : '&#x25BC;') : '';
      const yoyText = yoyVal != null ? Math.abs(yoyVal).toFixed(1) + '%' : '--';
      const hist = DataStore.getHistory(m.key);
      const sparkline = m.isPct ? '' : renderSparkline(m.key, hist);
      return `
        <div class="kpi-card" data-kpi="${m.key}">
          <div class="kpi-label">${m.label}</div>
          <div class="kpi-value" id="kpi-val-${m.key}">--</div>
          <div class="kpi-yoy ${yoyClass}">${yoyArrow} ${yoyText}</div>
          ${sparkline}
        </div>
      `;
    }).join('');

    METRICS.forEach(m => {
      const el = document.getElementById('kpi-val-' + m.key);
      const val = kpi[m.key] || 0;
      if (m.isPct) animateNumber(el, val, '%');
      else animateNumber(el, val);
    });
  };

  // 实时更新时只更新数字，不重建 DOM
  const updateRealtime = (kpi) => {
    METRICS.forEach(m => {
      const el = document.getElementById('kpi-val-' + m.key);
      if (!el) return;
      const val = kpi[m.key] || 0;
      if (m.isPct) animateNumber(el, val, '%', 600);
      else animateNumber(el, val, '', 600);
      // 脉冲动画
      const card = el.closest('.kpi-card');
      if (card) {
        card.classList.remove('pulse');
        void card.offsetWidth; // reflow
        card.classList.add('pulse');
      }
    });
  };

  return { render, updateRealtime };
})();

// ── StructureModule 增强版 ──
const StructureModule = (() => {
  const render = () => {
    const cats = DataStore.getCategories();
    if (!cats || cats.length === 0) return;
    const metric = DataStore.get('metric');
    const total = cats.reduce((s, c) => s + (metric === 'production' ? c.production : c.area), 0);
    if (total === 0) return;

    const size = 100, cx = 50, cy = 50, r = 38, ir = 24;
    let startAngle = -Math.PI / 2;
    const segments = cats.map(c => {
      const val = metric === 'production' ? c.production : c.area;
      const pct = val / total;
      const angle = pct * Math.PI * 2;
      const endAngle = startAngle + angle;
      const x1 = cx + r * Math.cos(startAngle);
      const y1 = cy + r * Math.sin(startAngle);
      const x2 = cx + r * Math.cos(endAngle);
      const y2 = cy + r * Math.sin(endAngle);
      const large = angle > Math.PI ? 1 : 0;
      const d = `M ${cx + ir * Math.cos(startAngle)} ${cy + ir * Math.sin(startAngle)} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} L ${cx + ir * Math.cos(endAngle)} ${cy + ir * Math.sin(endAngle)} A ${ir} ${ir} 0 ${large} 0 ${cx + ir * Math.cos(startAngle)} ${cy + ir * Math.sin(startAngle)} Z`;
      const seg = { d, color: c.color, name: c.name, pct, val };
      startAngle = endAngle;
      return seg;
    });

    const svg = `<svg width="${size*2}" height="${size*2}" viewBox="0 0 ${size*2} ${size*2}" class="structure-svg">
      ${segments.map(s => `<path d="${s.d}" fill="${s.color}" stroke="#050a18" stroke-width="1.5" opacity="0.85"/>`).join('')}
      <circle cx="${cx*2}" cy="${cy*2}" r="${ir*2}" fill="none"/>
    </svg>`;

    const legend = segments.map(s => `
      <div class="structure-legend-item">
        <span class="structure-legend-dot" style="background:${s.color}"></span>
        <span class="structure-legend-label">${s.name}</span>
        <span class="structure-legend-val">${(s.pct*100).toFixed(1)}%</span>
      </div>
    `).join('');

    document.getElementById('structure-panel').innerHTML = `<div class="structure-wrap">${svg}<div class="structure-legend">${legend}</div></div>`;
  };
  return { render };
})();

// ── RankingModule 增强版 ──
const RankingModule = (() => {
  const CAT_COLORS = { '粮食作物': '#1f7a5a', '经济作物': '#e18b32', '其他作物': '#6b7c93' };
  let _prevData = null;

  const render = () => {
    const data = DataStore.getRankings();
    if (!data || data.length === 0) {
      document.getElementById('rank-list').innerHTML = '<li style="color:var(--text-muted);padding:16px;text-align:center">暂无数据</li>';
      return;
    }
    const sorted = [...data].sort((a, b) => b.value - a.value).slice(0, 15);
    const maxVal = sorted[0]?.value || 1;
    const metric = DataStore.get('metric');
    const unit = metric === 'production' ? '吨' : '亩';

    // 检测变化
    const changedNames = new Set();
    if (_prevData) {
      const prevMap = new Map(_prevData.map(d => [d.name, d.value]));
      sorted.forEach(d => {
        const prev = prevMap.get(d.name);
        if (prev != null && Math.abs(d.value - prev) / prev > 0.01) changedNames.add(d.name);
      });
    }
    _prevData = sorted.map(d => ({ name: d.name, value: d.value }));

    const list = document.getElementById('rank-list');
    list.innerHTML = sorted.map((item, i) => {
      const pct = (item.value / maxVal * 100).toFixed(0);
      const color = CAT_COLORS[item.category] || '#6b7c93';
      const flash = changedNames.has(item.name) ? ' flash' : '';
      return `
        <li class="rank-item${flash}">
          <span class="rank-num">${i+1}</span>
          <span class="rank-name">${item.name}</span>
          <span class="rank-cat">${item.category||''}</span>
          <div class="rank-bar-wrap">
            <div class="rank-bar" style="width:${pct}%;background:${color}"></div>
          </div>
          <span class="rank-val">${fmtNum(item.value)}</span>
        </li>
      `;
    }).join('');
  };

  return { render };
})();

// ── ThreeForest Pro: Bloom + Fog + FlowingParticles ──
const ThreeForest = (() => {
  let scene, camera, renderer, controls, composer;
  let container, bloomPass, rafId = null;
  let initialized = false;
  let meshes = [], flowingParticles = null;

  const init = async () => {
    if (initialized) return;
    container = document.getElementById('three-container');
    const w = container.clientWidth || window.innerWidth * 0.92;
    const h = container.clientHeight || window.innerHeight * 0.92;

    // 动态导入 Three.js：import map 将 'three' 映射到 CDN；examples/jsm 内部裸导入 from 'three' 由 import map 解析
    const THREE = await import('three');
    const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
    const { EffectComposer } = await import('three/addons/postprocessing/EffectComposer.js');
    const { RenderPass } = await import('three/addons/postprocessing/RenderPass.js');
    const { UnrealBloomPass } = await import('three/addons/postprocessing/UnrealBloomPass.js');

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050a18);
    scene.fog = new THREE.FogExp2(0x050a18, 0.025);

    camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
    camera.position.set(25, 20, 25);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Post-processing: Bloom
    composer = new EffectComposer(renderer);
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);
    bloomPass = new UnrealBloomPass(
      new THREE.Vector2(w, h),
      0.3,  // strength
      0.5,  // radius
      0.1   // threshold
    );
    composer.addPass(bloomPass);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.5;
    controls.target.set(0, 2, 0);
    controls.maxPolarAngle = Math.PI / 2.2;

    // 灯光
    const ambient = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(10, 30, 10);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    scene.add(dirLight);
    const fillLight = new THREE.DirectionalLight(0x00d4aa, 0.3);
    fillLight.position.set(-10, 10, -10);
    scene.add(fillLight);

    // 地面
    const groundGeo = new THREE.PlaneGeometry(40, 40);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x080f24, roughness: 0.8, metalness: 0.1,
      transparent: true, opacity: 0.8,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.1;
    ground.receiveShadow = true;
    scene.add(ground);

    // 网格
    const gridHelper = new THREE.GridHelper(40, 20, 0x00d4aa, 0x1a2a4a);
    gridHelper.position.y = 0;
    gridHelper.material.transparent = true;
    gridHelper.material.opacity = 0.3;
    scene.add(gridHelper);

    // 柱体
    const data = DataStore.getRankings();
    if (data && data.length > 0) {
      const sorted = [...data].sort((a, b) => b.value - a.value).slice(0, 30);
      const maxVal = sorted[0]?.value || 1;
      const cols = 6, spacing = 2.8, offsetX = (cols - 1) * spacing / 2;
      const rows = Math.ceil(sorted.length / cols);
      const CAT_COLORS = { '粮食作物': 0x1f7a5a, '经济作物': 0xe18b32, '其他作物': 0x6b7c93 };

      sorted.forEach((item, i) => {
        const col = i % cols, row = Math.floor(i / cols);
        const bh = Math.max(0.3, (item.value / maxVal) * 8);
        const geo = new THREE.BoxGeometry(1.8, bh, 1.8);
        const color = CAT_COLORS[item.category] || 0x6b7c93;
        const mat = new THREE.MeshStandardMaterial({
          color, roughness: 0.3, metalness: 0.2,
          emissive: color, emissiveIntensity: 0.08,
          transparent: true, opacity: 0.9,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(col * spacing - offsetX, bh / 2, row * spacing - (rows - 1) * spacing / 2);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = { name: item.name, value: item.value, category: item.category };
        scene.add(mesh);
        meshes.push(mesh);

        const edgeGeo = new THREE.EdgesGeometry(geo);
        const edgeMat = new THREE.LineBasicMaterial({ color: 0x00d4aa, transparent: true, opacity: 0.2 });
        const edge = new THREE.LineSegments(edgeGeo, edgeMat);
        edge.position.copy(mesh.position);
        scene.add(edge);
      });
    }

    // 流动粒子 (FlowingParticles)
    const fpCount = 300;
    const fpGeo = new THREE.BufferGeometry();
    const fpPos = new Float32Array(fpCount * 3);
    const fpSpeeds = new Float32Array(fpCount);
    for (let i = 0; i < fpCount; i++) {
      fpPos[i*3] = (Math.random() - 0.5) * 30;
      fpPos[i*3+1] = Math.random() * 15 - 5;
      fpPos[i*3+2] = (Math.random() - 0.5) * 30;
      fpSpeeds[i] = 0.005 + Math.random() * 0.015;
    }
    fpGeo.setAttribute('position', new THREE.BufferAttribute(fpPos, 3));
    const fpMat = new THREE.PointsMaterial({
      color: 0x00d4aa, size: 0.12,
      transparent: true, opacity: 0.3,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    flowingParticles = new THREE.Points(fpGeo, fpMat);
    flowingParticles.userData.speeds = fpSpeeds;
    scene.add(flowingParticles);

    initialized = true;
    animate();
  };

  const animate = () => {
    rafId = requestAnimationFrame(animate);
    controls.update();

    // 流动粒子更新
    if (flowingParticles) {
      const pos = flowingParticles.geometry.attributes.position.array;
      const speeds = flowingParticles.userData.speeds;
      for (let i = 0; i < pos.length / 3; i++) {
        pos[i*3+1] += speeds[i];
        if (pos[i*3+1] > 15) pos[i*3+1] = -5;
      }
      flowingParticles.geometry.attributes.position.needsUpdate = true;
    }

    composer.render();
  };

  const open = async () => {
    document.getElementById('modal-overlay').classList.add('open');
    if (!initialized) await init();
    else {
      camera.position.set(25, 20, 25);
      controls.target.set(0, 2, 0);
      controls.update();
    }
  };

  const close = () => {
    document.getElementById('modal-overlay').classList.remove('open');
  };

  const resize = () => {
    if (!initialized || !container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    if (composer) composer.setSize(w, h);
  };

  return { open, close, resize };
})();

// ── App: 主编排器 ──
const App = (() => {
  let _resizeTimer = null;
  let _resizeObserver = null;

  const bindUI = () => {
    document.querySelectorAll('.year-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.year-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        DataStore.set('year', parseInt(tab.dataset.year));
      });
    });
    document.querySelectorAll('.metric-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.metric-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        DataStore.set('metric', tab.dataset.metric);
      });
    });
    document.getElementById('map-locate-btn').addEventListener('click', () => MapModule.locate());
    document.getElementById('map-rotate-toggle').addEventListener('click', () => {
      const r = MapModule.toggleRotate();
      document.getElementById('map-rotate-toggle').textContent = r ? '暂停' : '旋转';
    });
    document.getElementById('flyline-toggle').addEventListener('click', () => {
      const enabled = MapModule.toggleFlyline();
      document.getElementById('flyline-toggle').classList.toggle('active', enabled);
      document.getElementById('flyline-toggle').textContent = enabled ? '飞线' : '飞线关';
    });
    document.getElementById('forest-btn').addEventListener('click', () => ThreeForest.open());
    document.getElementById('modal-close').addEventListener('click', () => ThreeForest.close());
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) ThreeForest.close();
    });
  };

  const load = async () => {
    const barFill = document.getElementById('loading-bar-fill');
    const setPhase = (pct, text) => {
      barFill.style.width = pct + '%';
      document.getElementById('loading-text').textContent = text;
    };
    try {
      setPhase(10, 'LOADING DATA...');
      await DataStore.load();
      setPhase(40, 'INITIALIZING MAP...');
      await MapModule.init();
      setPhase(55, 'INITIALIZING SCAN RING...');
      await ScanRing.init();
      setPhase(70, 'RENDERING PANELS...');
      KPIModule.render();
      StructureModule.render();
      RankingModule.render();
      setPhase(100, 'READY');
      setTimeout(() => {
        document.getElementById('loading-overlay').classList.add('hidden');
      }, 400);
      // 启动实时数据
      DataStore.startRealtime();
    } catch (err) {
      console.error('[DigitalTwin] 初始化失败:', err);
      document.getElementById('loading-text').textContent = '⚠ 加载失败: ' + (err.message || '未知错误');
      document.getElementById('loading-text').style.color = '#ef4444';
      setTimeout(() => {
        document.getElementById('loading-overlay').classList.add('hidden');
      }, 3000);
    }
  };

  const init = () => {
    // 15s 安全兜底
    setTimeout(() => {
      const overlay = document.getElementById('loading-overlay');
      if (overlay && !overlay.classList.contains('hidden')) {
        overlay.classList.add('hidden');
      }
    }, 15000);

    initBgCanvas();
    bindUI();

    // 订阅变化
    DataStore.on('change', ({ key }) => {
      if (key === 'year' || key === 'metric') {
        MapModule.render();
        KPIModule.render();
        StructureModule.render();
        RankingModule.render();
      }
    });

    // 订阅实时更新
    DataStore.on('realtime:update', (kpi) => {
      KPIModule.updateRealtime(kpi);
      // 排名微调
      RankingModule.render();
    });

    // ResizeObserver 替代 window.resize（带兼容性防御）
    if (typeof ResizeObserver !== 'undefined') {
      _resizeObserver = new ResizeObserver(() => {
        clearTimeout(_resizeTimer);
        _resizeTimer = setTimeout(() => {
          MapModule.resize();
          ScanRing.resize();
          ThreeForest.resize();
        }, 200);
      });
      _resizeObserver.observe(document.getElementById('map-area'));
    } else {
      window.addEventListener('resize', () => {
        clearTimeout(_resizeTimer);
        _resizeTimer = setTimeout(() => {
          MapModule.resize();
          ScanRing.resize();
          ThreeForest.resize();
        }, 200);
      });
    }

    load();
  };

  return { init };
})();

// 启动
if (document.readyState === 'complete') {
  App.init();
} else {
  window.addEventListener('load', () => setTimeout(App.init, 50));
}
