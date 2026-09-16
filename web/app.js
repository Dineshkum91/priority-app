/**
 * Priority App — Frontend Controller & Interactive Application
 */

import {
  HealthDimension,
  checkSafety,
  determinePriority,
  getPresetStudent,
  SUPPORT_RESOURCES
} from './engine.js';

// Application State
const STATE = {
  theme: localStorage.getItem('priority_theme') || 'light',
  viewMode: localStorage.getItem('priority_view_mode') || 'phone', // 'phone' | 'dashboard'
  currentTab: 'today', // 'today' | 'checkin' | 'insights' | 'tools'
  currentPersona: 'priya', // 'priya' | 'marcus' | 'custom'
  profile: null,
  history: [],
  todayCheckin: null,
  recommendation: null,
  hasCheckedInToday: true,
  breathingActive: false,
  breathingTimer: null
};

// Web Audio API for Gentle Chimes & Feedback
class SoundFX {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  playSuccess() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(523.25, now); // C5
    osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.15); // E5
    osc.frequency.exponentialRampToValueAtTime(783.99, now + 0.3); // G5
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.6);
  }
  playWater() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, now);
    osc.frequency.exponentialRampToValueAtTime(1200, now + 0.08);
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.15);
  }
  playChime() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(440, now); // A4
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 1.2);
  }
}

const sfx = new SoundFX();

// Dimension styling metadata
const DIM_META = {
  [HealthDimension.SLEEP]: { label: 'Sleep & Circadian', icon: '🌙', color: '#2D5A43' },
  [HealthDimension.STRESS]: { label: 'Stress & Mental Calm', icon: '🧠', color: '#E07A5F' },
  [HealthDimension.HYDRATION]: { label: 'Hydration', icon: '💧', color: '#457B9D' },
  [HealthDimension.NUTRITION]: { label: 'Nutrition & Fuel', icon: '🥗', color: '#E9C46A' },
  [HealthDimension.ACTIVITY]: { label: 'Movement & Posture', icon: '⚡', color: '#38A3A5' },
  [HealthDimension.RECOVERY]: { label: 'Rest & Recharge', icon: '🌿', color: '#52796F' }
};

// Initialize Application
function initApp() {
  applyTheme(STATE.theme);
  loadPersona(STATE.currentPersona);
  setupEventHandlers();
  renderApp();
}

function applyTheme(theme) {
  STATE.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('priority_theme', theme);
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    themeBtn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }
}

function loadPersona(personaKey) {
  STATE.currentPersona = personaKey;
  const data = getPresetStudent(personaKey);
  STATE.profile = data.profile;
  STATE.history = [...data.history];
  STATE.todayCheckin = { ...data.todayInitial };
  
  // Compute initial recommendation
  STATE.recommendation = determinePriority(
    STATE.todayCheckin,
    STATE.profile,
    STATE.history,
    []
  );
  STATE.hasCheckedInToday = true;

  updatePersonaSelectorUI();
  renderApp();
}

function updatePersonaSelectorUI() {
  const avatarEl = document.getElementById('persona-avatar');
  const nameEl = document.getElementById('persona-name');
  const badgeEl = document.getElementById('persona-badge');

  if (avatarEl) avatarEl.textContent = STATE.profile.avatar;
  if (nameEl) nameEl.textContent = STATE.profile.name;
  if (badgeEl) badgeEl.textContent = STATE.profile.role.split('•')[0].trim();
}

// Render Core App
function renderApp() {
  renderMobileFrameNotchClock();
  
  const mainContentEl = document.getElementById('main-dynamic-container');
  if (!mainContentEl) return;

  // Render based on active view mode and active tab
  if (STATE.viewMode === 'phone') {
    renderMobileView(mainContentEl);
  } else {
    renderDashboardView(mainContentEl);
  }
}

function renderMobileFrameNotchClock() {
  const clockEl = document.getElementById('notch-clock');
  if (clockEl) {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const mins = now.getMinutes().toString().padStart(2, '0');
    clockEl.textContent = `${hours}:${mins}`;
  }
}

// Mobile View (Single Screen Flow matching Flutter App)
function renderMobileView(container) {
  container.innerHTML = `
    <div class="mobile-frame-wrapper">
      <div class="mobile-frame">
        <!-- iOS/Android notch bar -->
        <div class="mobile-notch">
          <span id="notch-clock">09:41</span>
          <div class="mobile-island"></div>
          <span>5G 🔋</span>
        </div>

        <!-- Scrollable content area -->
        <div class="mobile-content" id="mobile-screen-scroll">
          ${renderTabContent(STATE.currentTab)}
        </div>

        <!-- Bottom Navigation Bar matching Flutter NavigationBar -->
        <div class="mobile-bottom-nav">
          <button class="nav-item ${STATE.currentTab === 'today' ? 'active' : ''}" data-tab="today">
            <span class="nav-icon">✨</span>
            <span>Today</span>
          </button>
          <button class="nav-item ${STATE.currentTab === 'checkin' ? 'active' : ''}" data-tab="checkin">
            <span class="nav-icon">📝</span>
            <span>Check-in</span>
          </button>
          <button class="nav-item ${STATE.currentTab === 'insights' ? 'active' : ''}" data-tab="insights">
            <span class="nav-icon">📊</span>
            <span>Insights</span>
          </button>
          <button class="nav-item ${STATE.currentTab === 'tools' ? 'active' : ''}" data-tab="tools">
            <span class="nav-icon">🌿</span>
            <span>Toolkit</span>
          </button>
        </div>
      </div>
    </div>
  `;

  attachTabEvents(container);
  attachInteractiveWidgetEvents();
}

// Expanded Dashboard View (Multi-column Desktop View)
function renderDashboardView(container) {
  container.innerHTML = `
    <div class="dashboard-grid">
      <!-- Left Column: Primary Focus & Check-in / Insights -->
      <div class="dashboard-primary">
        <!-- View selector pills for tabs -->
        <div style="display: flex; gap: 8px; margin-bottom: 20px;">
          <button class="btn-icon-toggle ${STATE.currentTab === 'today' ? 'active' : ''}" data-tab="today">✨ Today's Focus</button>
          <button class="btn-icon-toggle ${STATE.currentTab === 'checkin' ? 'active' : ''}" data-tab="checkin">📝 Daily Check-in</button>
          <button class="btn-icon-toggle ${STATE.currentTab === 'insights' ? 'active' : ''}" data-tab="insights">📊 7-Day Insights</button>
          <button class="btn-icon-toggle ${STATE.currentTab === 'tools' ? 'active' : ''}" data-tab="tools">🌿 Calming Toolkit</button>
        </div>

        <div id="dashboard-tab-content">
          ${renderTabContent(STATE.currentTab)}
        </div>
      </div>

      <!-- Right Column: Student Profile, Hydration Tracker & Quick Breathing -->
      <div class="dashboard-sidebar">
        <!-- Student Persona Card -->
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <span style="font-size: 24px;">${STATE.profile.avatar}</span>
              <div>
                <h3 class="card-title">${STATE.profile.name}</h3>
                <p class="card-subtitle">${STATE.profile.role}</p>
              </div>
            </div>
            <button class="btn-icon-circle" id="sidebar-switch-persona" title="Switch Persona">⇄</button>
          </div>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 14px;">
            ${STATE.profile.bio}
          </p>
          <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-subtle); padding-top: 10px;">
            <span>Sleep Target: <strong>${STATE.profile.typical_sleep_hours}h</strong></span>
            <span>Water Target: <strong>${STATE.profile.target_water} gls</strong></span>
          </div>
        </div>

        <!-- Quick Hydration Tracker -->
        ${renderWaterWidget()}

        <!-- 4-7-8 Breathing Pacer Mini -->
        ${renderBreathingWidget()}
      </div>
    </div>
  `;

  attachTabEvents(container);
  attachInteractiveWidgetEvents();
}

// Render Content for specific tab
function renderTabContent(tab) {
  switch (tab) {
    case 'today':
      return renderTodayScreen();
    case 'checkin':
      return renderCheckinScreen();
    case 'insights':
      return renderInsightsScreen();
    case 'tools':
      return renderToolsScreen();
    default:
      return renderTodayScreen();
  }
}

// Screen 1: Today's Focus (Priority Screen)
function renderTodayScreen() {
  const rec = STATE.recommendation;
  const dim = rec ? rec.priorityDimension : HealthDimension.SLEEP;
  const meta = DIM_META[dim] || { label: dim, icon: '🎯', color: 'var(--primary)' };

  // Safety Flag Alert if triggered
  let safetyBanner = '';
  if (rec && rec.safetyFlagged) {
    safetyBanner = `
      <div class="safety-banner">
        <span class="safety-icon">⚠️</span>
        <div class="safety-body">
          <h4>Safety Layer Alert</h4>
          <p>${rec.safetyMessage}</p>
          <div class="safety-actions">
            <a href="tel:988" class="btn-emergency">📞 Call/Text 988 Lifeline</a>
            <a href="sms:741741" class="btn-emergency">💬 Text 741741</a>
            <button class="btn-emergency" style="background:#586B62;" id="open-support-modal-btn">Campus Resources</button>
          </div>
        </div>
      </div>
    `;
  }

  return `
    ${safetyBanner}

    <!-- Hero Greeting & Prompt -->
    <div style="margin-bottom: 16px;">
      <span class="badge-pill">Daily Focus</span>
      <h2 style="font-family: var(--font-heading); font-size: 24px; font-weight: 700; margin-top: 4px;">
        Good morning, ${STATE.profile.name.split(' ')[0]}
      </h2>
      <p style="font-size: 13px; color: var(--text-muted);">
        One single focus designed for your current capacity.
      </p>
    </div>

    <!-- The ONE Top Priority Hero Card -->
    <div class="card priority-hero-card">
      <div class="priority-badge-container">
        <span class="priority-kicker">
          <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--primary);"></span>
          Today's Single Priority
        </span>
        <span class="badge-pill" style="background: rgba(45,90,67,0.12);">High Impact</span>
      </div>

      <div class="priority-dimension-badge">
        <span class="dim-icon">${meta.icon}</span>
        <span>${dim}</span>
      </div>

      <div class="priority-explanation-box">
        ${rec.llmExplanation || rec.priorityReason}
      </div>

      <!-- Action Items Checklist -->
      <div class="actions-container">
        <div class="actions-title">
          <span>Suggested Micro-Actions</span>
          <span style="font-size: 11px; font-weight: 400; color: var(--text-muted);">(Doable in <20 min)</span>
        </div>
        ${rec.actions.map(act => `
          <div class="action-item ${act.isCompleted ? 'completed' : ''}" data-act-id="${act.id}">
            <div class="action-checkbox">
              ${act.isCompleted ? '✓' : ''}
            </div>
            <div class="action-text">${act.actionText}</div>
          </div>
        `).join('')}
      </div>

      <!-- Complete Button / Feedback -->
      <div class="priority-footer">
        ${rec.isCompleted ? `
          <div style="background: rgba(42, 157, 143, 0.12); border: 1px solid rgba(42, 157, 143, 0.4); border-radius: var(--radius-md); padding: 14px; text-align: center; color: #2A9D8F; font-weight: 700;">
            🎉 Great job today! Action completed.
          </div>
        ` : `
          <button class="btn-primary-action" id="btn-mark-done">
            <span>Mark Priority as Done</span>
            <span>→</span>
          </button>
        `}
      </div>
    </div>

    <!-- Quick stats strip -->
    <div class="insight-metric-grid" style="margin-top: 18px;">
      <div class="metric-box">
        <div class="metric-val">${STATE.todayCheckin.sleep_hours}h</div>
        <div class="metric-label">Last Night Sleep</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">${STATE.todayCheckin.stress_level}/5</div>
        <div class="metric-label">Stress Rating</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">${STATE.todayCheckin.water_glasses}</div>
        <div class="metric-label">Glasses Water</div>
      </div>
    </div>
  `;
}

// Screen 2: 30-Second Check-in Form
function renderCheckinScreen() {
  const current = STATE.todayCheckin;

  return `
    <div class="checkin-hero-banner">
      <h2>Daily Check-in</h2>
      <p>Takes less than 30 seconds. No food scales or calorie logging.</p>
    </div>

    <!-- Sleep Hours Slider -->
    <div class="slider-field">
      <div class="slider-header">
        <span class="slider-label">🌙 How much did you sleep?</span>
        <span class="slider-val-badge" id="lbl-sleep">${current.sleep_hours} hrs</span>
      </div>
      <input type="range" class="range-input" id="input-sleep" min="0" max="12" step="0.5" value="${current.sleep_hours}">
      <div class="slider-ticks">
        <span>0 hrs</span>
        <span>4 hrs (Deficit)</span>
        <span>7.5 hrs (Target)</span>
        <span>12 hrs</span>
      </div>
    </div>

    <!-- Stress Level Selector -->
    <div class="slider-field">
      <div class="slider-header">
        <span class="slider-label">🧠 Stress level today?</span>
        <span class="slider-val-badge" id="lbl-stress">${current.stress_level} / 5</span>
      </div>
      <div class="stress-selector" id="stress-selector-group">
        <div class="stress-pill ${current.stress_level === 1 ? 'active' : ''}" data-val="1">
          <span class="stress-emoji">😌</span>
          <span class="stress-num">1</span>
          <span class="stress-sub">Calm</span>
        </div>
        <div class="stress-pill ${current.stress_level === 2 ? 'active' : ''}" data-val="2">
          <span class="stress-emoji">🙂</span>
          <span class="stress-num">2</span>
          <span class="stress-sub">Mild</span>
        </div>
        <div class="stress-pill ${current.stress_level === 3 ? 'active' : ''}" data-val="3">
          <span class="stress-emoji">😐</span>
          <span class="stress-num">3</span>
          <span class="stress-sub">Moderate</span>
        </div>
        <div class="stress-pill ${current.stress_level === 4 ? 'active' : ''}" data-val="4">
          <span class="stress-emoji">😰</span>
          <span class="stress-num">4</span>
          <span class="stress-sub">High</span>
        </div>
        <div class="stress-pill ${current.stress_level === 5 ? 'active' : ''}" data-val="5">
          <span class="stress-emoji">🚨</span>
          <span class="stress-num">5</span>
          <span class="stress-sub">Max</span>
        </div>
      </div>
    </div>

    <!-- Meals Eaten Slider -->
    <div class="slider-field">
      <div class="slider-header">
        <span class="slider-label">🥗 Meals eaten today?</span>
        <span class="slider-val-badge" id="lbl-meals">${current.meals_eaten} meals</span>
      </div>
      <input type="range" class="range-input" id="input-meals" min="0" max="5" step="1" value="${current.meals_eaten}">
      <div class="slider-ticks">
        <span>0 (Fasting/Skipped)</span>
        <span>2</span>
        <span>3 (Standard)</span>
        <span>5</span>
      </div>
    </div>

    <!-- Water Glasses Slider -->
    <div class="slider-field">
      <div class="slider-header">
        <span class="slider-label">💧 Glasses of water?</span>
        <span class="slider-val-badge" id="lbl-water">${current.water_glasses} glasses</span>
      </div>
      <input type="range" class="range-input" id="input-water" min="0" max="12" step="1" value="${current.water_glasses}">
      <div class="slider-ticks">
        <span>0</span>
        <span>4</span>
        <span>8 (Optimal)</span>
        <span>12</span>
      </div>
    </div>

    <!-- Optional Notes (Triggers safety scanner) -->
    <div class="slider-field notes-field">
      <div class="slider-header">
        <span class="slider-label">💭 Quick thoughts or context (optional)</span>
      </div>
      <textarea id="input-notes" placeholder="Exam coming up, late shift at dining hall, feeling overwhelmed...">${current.notes || ''}</textarea>
    </div>

    <!-- Submit Check-in Button -->
    <button class="btn-primary-action" id="btn-submit-checkin" style="width: 100%; margin-top: 10px;">
      <span>Calculate Today's Focus</span>
      <span>⚡</span>
    </button>
  `;
}

// Screen 3: Insights & 7-Day Patterns
function renderInsightsScreen() {
  const history = [...STATE.history, {
    date: 'Today',
    sleep_hours: STATE.todayCheckin.sleep_hours,
    stress_level: STATE.todayCheckin.stress_level
  }];

  // Compute 7-day stats
  const totalSleep = history.reduce((sum, h) => sum + (h.sleep_hours || 0), 0);
  const avgSleep = (totalSleep / history.length).toFixed(1);
  const avgStress = (history.reduce((sum, h) => sum + (h.stress_level || 0), 0) / history.length).toFixed(1);
  const sleepDebt = Math.max(0, ((STATE.profile.typical_sleep_hours * history.length) - totalSleep)).toFixed(1);

  return `
    <div class="card-header" style="margin-bottom: 8px;">
      <div>
        <h2 style="font-family: var(--font-heading); font-size: 22px; font-weight: 700;">Weekly Pattern</h2>
        <p style="font-size: 13px; color: var(--text-muted);">Correlation between sleep debt & stress</p>
      </div>
      <span class="badge-pill">7-Day Trend</span>
    </div>

    <div class="insight-metric-grid">
      <div class="metric-box">
        <div class="metric-val">${avgSleep}h</div>
        <div class="metric-label">Avg Sleep / Night</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color: var(--danger);">${sleepDebt}h</div>
        <div class="metric-label">Sleep Debt</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color: var(--accent-warm);">${avgStress}/5</div>
        <div class="metric-label">Avg Stress</div>
      </div>
    </div>

    <!-- Interactive SVG Chart -->
    <div class="card chart-card">
      <div class="card-title-group" style="margin-bottom: 12px;">
        <span class="card-title-icon">📈</span>
        <h3 class="card-title">Sleep vs. Stress Curve</h3>
      </div>

      <div class="chart-wrapper">
        ${renderTrendSVGChart(history)}
      </div>

      <div class="chart-legend">
        <span><span class="legend-dot legend-sleep"></span> Sleep (Hours)</span>
        <span><span class="legend-dot legend-stress"></span> Stress (1-5 Scale)</span>
      </div>
    </div>

    <!-- AI Student Observation -->
    <div class="pattern-box">
      <span class="pattern-icon">💡</span>
      <div class="pattern-text">
        <strong>Key Pattern Detected:</strong> On nights when sleep fell below 5.0 hours, reported stress jumped from 3/5 to 5/5 the following afternoon. Prioritising sleep tonight will stabilize your cognitive focus for tomorrow.
      </div>
    </div>
  `;
}

// Generate SVG bezier chart
function renderTrendSVGChart(history) {
  const width = 340;
  const height = 160;
  const padding = 24;

  const pointsCount = history.length;
  const stepX = (width - padding * 2) / (pointsCount - 1);

  // Sleep line points (0 - 12h mapped to height)
  const sleepCoords = history.map((item, i) => {
    const x = padding + i * stepX;
    const y = height - padding - ((item.sleep_hours || 0) / 12) * (height - padding * 2);
    return { x, y, val: item.sleep_hours, label: item.date };
  });

  // Stress line points (1 - 5 mapped to height)
  const stressCoords = history.map((item, i) => {
    const x = padding + i * stepX;
    const y = height - padding - (((item.stress_level || 1) - 1) / 4) * (height - padding * 2);
    return { x, y, val: item.stress_level, label: item.date };
  });

  const sleepPath = createSmoothPath(sleepCoords);
  const stressPath = createSmoothPath(stressCoords);

  return `
    <svg viewBox="0 0 ${width} ${height}" class="chart-svg">
      <!-- Grid lines -->
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="var(--border-subtle)" stroke-width="1" />
      <line x1="${padding}" y1="${height / 2}" x2="${width - padding}" y2="${height / 2}" stroke="var(--border-subtle)" stroke-dasharray="3 3" />
      
      <!-- Sleep Path & Points -->
      <path d="${sleepPath}" fill="none" stroke="var(--primary)" stroke-width="3" stroke-linecap="round" />
      ${sleepCoords.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="4" fill="var(--bg-card-elevated)" stroke="var(--primary)" stroke-width="2" />
      `).join('')}

      <!-- Stress Path & Points -->
      <path d="${stressPath}" fill="none" stroke="var(--accent-warm)" stroke-width="2.5" stroke-dasharray="4 2" stroke-linecap="round" />
      ${stressCoords.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="3.5" fill="var(--bg-card-elevated)" stroke="var(--accent-warm)" stroke-width="2" />
      `).join('')}

      <!-- Day labels -->
      ${history.map((h, i) => `
        <text x="${padding + i * stepX}" y="${height - 6}" font-size="9" fill="var(--text-muted)" text-anchor="middle">
          ${h.date.replace('Day ', 'D')}
        </text>
      `).join('')}
    </svg>
  `;
}

function createSmoothPath(coords) {
  if (coords.length === 0) return '';
  let d = `M ${coords[0].x},${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const p0 = coords[i];
    const p1 = coords[i + 1];
    const mx = (p0.x + p1.x) / 2;
    d += ` C ${mx},${p0.y} ${mx},${p1.y} ${p1.x},${p1.y}`;
  }
  return d;
}

// Screen 4: Tools & Breathing
function renderToolsScreen() {
  return `
    <div style="margin-bottom: 16px;">
      <h2 style="font-family: var(--font-heading); font-size: 22px; font-weight: 700;">Student Wellness Toolkit</h2>
      <p style="font-size: 13px; color: var(--text-muted);">Instant micro-interventions for busy days</p>
    </div>

    ${renderBreathingWidget(true)}
    ${renderWaterWidget()}

    <!-- Support Resources Access -->
    <div class="card" style="margin-top: 14px;">
      <div class="card-header">
        <div class="card-title-group">
          <span class="card-title-icon">🛡️</span>
          <h3 class="card-title">Campus & Crisis Lifelines</h3>
        </div>
      </div>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
        Immediate, confidential support available 24/7.
      </p>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <a href="tel:988" class="btn-emergency" style="justify-content: center;">📞 988 Suicide & Crisis Lifeline (Call/Text)</a>
        <a href="sms:741741" class="btn-emergency" style="background: #38A3A5; justify-content: center;">💬 Crisis Text Line (Text HOME to 741741)</a>
      </div>
    </div>
  `;
}

// Quick Water Widget Component
function renderWaterWidget() {
  const glasses = STATE.todayCheckin.water_glasses;
  const target = STATE.profile.target_water || 8;

  let dropsHtml = '';
  for (let i = 1; i <= target; i++) {
    dropsHtml += `<span class="water-drop ${i <= glasses ? 'filled' : ''}">💧</span>`;
  }

  return `
    <div class="card water-widget">
      <div class="card-header" style="margin-bottom: 8px;">
        <div class="card-title-group">
          <span class="card-title-icon">💧</span>
          <h3 class="card-title">Hydration Today</h3>
        </div>
        <span class="slider-val-badge">${glasses}/${target} glasses</span>
      </div>
      <div class="water-counter-row">
        <div class="water-glasses-track">
          ${dropsHtml}
        </div>
        <button class="btn-add-water" id="btn-quick-add-water">+1 Glass</button>
      </div>
    </div>
  `;
}

// 4-7-8 Guided Breathing Component
function renderBreathingWidget(fullScreen = false) {
  return `
    <div class="card breathing-card">
      <div class="card-header">
        <div class="card-title-group">
          <span class="card-title-icon">🌬️</span>
          <h3 class="card-title">4-4-6 Reset Breathing</h3>
        </div>
      </div>
      <div class="breathing-orb-wrapper">
        <div class="breathing-orb" id="breathing-orb">Breathe</div>
      </div>
      <div class="breathing-instruction" id="breathing-prompt">Tap Start to begin a 60-second nervous system reset.</div>
      <div class="breathing-counter" id="breathing-counter">Inhale: 4s • Hold: 4s • Exhale: 6s</div>
      <button class="btn-primary-action" id="btn-toggle-breathing" style="margin-top: 16px; width: 100%;">
        Start Breathing Pacer
      </button>
    </div>
  `;
}

// Attach Tab and Global Events
function setupEventHandlers() {
  // Theme toggle
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      applyTheme(STATE.theme === 'dark' ? 'light' : 'dark');
    });
  }

  // View Mode Toggles (Phone vs Dashboard)
  const phoneBtn = document.getElementById('view-phone-btn');
  const dashBtn = document.getElementById('view-dashboard-btn');

  if (phoneBtn && dashBtn) {
    phoneBtn.addEventListener('click', () => {
      STATE.viewMode = 'phone';
      localStorage.setItem('priority_view_mode', 'phone');
      phoneBtn.classList.add('active');
      dashBtn.classList.remove('active');
      renderApp();
    });

    dashBtn.addEventListener('click', () => {
      STATE.viewMode = 'dashboard';
      localStorage.setItem('priority_view_mode', 'dashboard');
      dashBtn.classList.add('active');
      phoneBtn.classList.remove('active');
      renderApp();
    });

    // Set initial toggle button states
    if (STATE.viewMode === 'dashboard') {
      dashBtn.classList.add('active');
      phoneBtn.classList.remove('active');
    } else {
      phoneBtn.classList.add('active');
      dashBtn.classList.remove('active');
    }
  }

  // Persona Selector Button
  const personaSelectorBtn = document.getElementById('persona-selector-btn');
  if (personaSelectorBtn) {
    personaSelectorBtn.addEventListener('click', () => {
      openPersonaModal();
    });
  }

  // Modal Close buttons
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', e => {
      if (e.target === modal || e.target.classList.contains('btn-close-modal')) {
        modal.classList.remove('active');
      }
    });
  });
}

function attachTabEvents(container) {
  container.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (tab) {
        STATE.currentTab = tab;
        renderApp();
      }
    });
  });

  const sidebarSwitch = container.querySelector('#sidebar-switch-persona');
  if (sidebarSwitch) {
    sidebarSwitch.addEventListener('click', openPersonaModal);
  }
}

// Attach Interactive Widget Events
function attachInteractiveWidgetEvents() {
  // Action checklist toggles
  document.querySelectorAll('.action-item').forEach(item => {
    item.addEventListener('click', () => {
      const actId = item.getAttribute('data-act-id');
      const action = STATE.recommendation?.actions.find(a => a.id === actId);
      if (action) {
        action.isCompleted = !action.isCompleted;
        sfx.playSuccess();
        renderApp();
        showToast(action.isCompleted ? '✓ Micro-action marked done!' : 'Action unchecked');
      }
    });
  });

  // Mark Priority Done Button
  const markDoneBtn = document.getElementById('btn-mark-done');
  if (markDoneBtn) {
    markDoneBtn.addEventListener('click', () => {
      STATE.recommendation.isCompleted = true;
      sfx.playSuccess();
      showToast('🎉 Priority completed! Excellent work.');
      renderApp();
    });
  }

  // Sliders in Check-in screen
  const sleepInput = document.getElementById('input-sleep');
  const mealsInput = document.getElementById('input-meals');
  const waterInput = document.getElementById('input-water');
  const notesInput = document.getElementById('input-notes');

  if (sleepInput) {
    sleepInput.addEventListener('input', e => {
      const val = parseFloat(e.target.value);
      STATE.todayCheckin.sleep_hours = val;
      const lbl = document.getElementById('lbl-sleep');
      if (lbl) lbl.textContent = `${val.toFixed(1)} hrs`;
    });
  }

  if (mealsInput) {
    mealsInput.addEventListener('input', e => {
      const val = parseInt(e.target.value, 10);
      STATE.todayCheckin.meals_eaten = val;
      const lbl = document.getElementById('lbl-meals');
      if (lbl) lbl.textContent = `${val} meals`;
    });
  }

  if (waterInput) {
    waterInput.addEventListener('input', e => {
      const val = parseInt(e.target.value, 10);
      STATE.todayCheckin.water_glasses = val;
      const lbl = document.getElementById('lbl-water');
      if (lbl) lbl.textContent = `${val} glasses`;
    });
  }

  // Stress pills
  document.querySelectorAll('#stress-selector-group .stress-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const val = parseInt(pill.getAttribute('data-val'), 10);
      STATE.todayCheckin.stress_level = val;
      document.querySelectorAll('#stress-selector-group .stress-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const lbl = document.getElementById('lbl-stress');
      if (lbl) lbl.textContent = `${val} / 5`;
    });
  });

  // Check-in Submit Button
  const submitBtn = document.getElementById('btn-submit-checkin');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      if (notesInput) STATE.todayCheckin.notes = notesInput.value;

      // Recompute priority using Python engine algorithm
      STATE.recommendation = determinePriority(
        STATE.todayCheckin,
        STATE.profile,
        STATE.history,
        []
      );

      sfx.playSuccess();
      showToast('⚡ Calculated your #1 priority!');
      STATE.currentTab = 'today';
      renderApp();
    });
  }

  // Quick Add Water Button
  const addWaterBtn = document.getElementById('btn-quick-add-water');
  if (addWaterBtn) {
    addWaterBtn.addEventListener('click', () => {
      STATE.todayCheckin.water_glasses = Math.min(15, (STATE.todayCheckin.water_glasses || 0) + 1);
      sfx.playWater();
      showToast('💧 Logged +1 glass of water!');
      renderApp();
    });
  }

  // Guided Breathing Pacer Toggle
  const breathingBtn = document.getElementById('btn-toggle-breathing');
  if (breathingBtn) {
    breathingBtn.addEventListener('click', toggleBreathingPacer);
  }

  // Open Support modal button
  const openSupportBtn = document.getElementById('open-support-modal-btn');
  if (openSupportBtn) {
    openSupportBtn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
      const modal = document.getElementById('support-resources-modal');
      if (modal) modal.classList.add('active');
    });
  }
}

// 4-4-6 Breathing Routine Cycle
function toggleBreathingPacer() {
  const orb = document.getElementById('breathing-orb');
  const prompt = document.getElementById('breathing-prompt');
  const btn = document.getElementById('btn-toggle-breathing');

  if (STATE.breathingActive) {
    // Stop
    clearInterval(STATE.breathingTimer);
    STATE.breathingActive = false;
    if (orb) {
      orb.className = 'breathing-orb';
      orb.textContent = 'Breathe';
    }
    if (prompt) prompt.textContent = 'Session finished. Great job resetting.';
    if (btn) btn.textContent = 'Start Breathing Pacer';
  } else {
    // Start
    STATE.breathingActive = true;
    if (btn) btn.textContent = 'Pause Breathing';
    sfx.playChime();

    let step = 0; // 0: inhale (4s), 1: hold (4s), 2: exhale (6s)
    const runCycle = () => {
      if (!STATE.breathingActive) return;
      if (step === 0) {
        // Inhale 4s
        if (orb) {
          orb.className = 'breathing-orb inhale';
          orb.textContent = 'Inhale';
        }
        if (prompt) prompt.textContent = 'Breathe in slowly through your nose (4s)...';
        sfx.playChime();
        step = 1;
        STATE.breathingTimer = setTimeout(runCycle, 4000);
      } else if (step === 1) {
        // Hold 4s
        if (orb) {
          orb.className = 'breathing-orb hold';
          orb.textContent = 'Hold';
        }
        if (prompt) prompt.textContent = 'Gently hold your breath (4s)...';
        step = 2;
        STATE.breathingTimer = setTimeout(runCycle, 4000);
      } else {
        // Exhale 6s
        if (orb) {
          orb.className = 'breathing-orb exhale';
          orb.textContent = 'Exhale';
        }
        if (prompt) prompt.textContent = 'Release smoothly through your mouth (6s)...';
        step = 0;
        STATE.breathingTimer = setTimeout(runCycle, 6000);
      }
    };

    runCycle();
  }
}

// Persona Switcher Dialog
function openPersonaModal() {
  document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
  const modal = document.getElementById('persona-modal');
  if (!modal) return;

  modal.classList.add('active');

  modal.querySelectorAll('[data-persona-select]').forEach(btn => {
    btn.onclick = () => {
      const pKey = btn.getAttribute('data-persona-select');
      loadPersona(pKey);
      modal.classList.remove('active');
      showToast(`Switched profile to ${STATE.profile.name}`);
    };
  });
}

// Toast Notice Helper
function showToast(message) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2400);
}

// Launch on DOM ready
document.addEventListener('DOMContentLoaded', initApp);
