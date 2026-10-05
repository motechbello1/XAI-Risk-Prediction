const $ = (s, root = document) => root.querySelector(s);
const esc = (v) => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths = {
  arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>', back:'<path d="M19 12H5m6-6-6 6 6 6"/>',
  up:'<path d="M12 19V5m-6 6 6-6 6 6"/>', sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  moon:'<path d="M20 15A8.5 8.5 0 0 1 9 4a8.5 8.5 0 1 0 11 11Z"/>',
  present:'<rect x="3" y="4" width="18" height="12" rx="2"/><path d="m8 21 4-5 4 5M9 8l5 2-5 3Z"/>',
  menu:'<path d="M5 7h14M5 12h14M5 17h14"/>',check:'<path d="m5 12 4 4L19 6"/>',
  shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  leaf:'<path d="M20 3C8 2 3 9 6 15s14 4 14-12Z"/><path d="M4 21 16 8"/>',
  changes:'<path d="M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4"/>',
  lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
  eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',file:'<path d="M14 3H5v18h14V8Zm0 0v5h5M8 12h8M8 16h8"/>',
};
const icon = (name, extra = '') => `<svg class="icon ${extra}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.arrow}</svg>`;
function hydrateIcons() { document.querySelectorAll('[data-icon]').forEach(el => el.innerHTML = icon(el.dataset.icon)); }
function storedTheme() { try { return localStorage.getItem('clarity-theme'); } catch { return null; } }
const preferredTheme = storedTheme() || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.documentElement.dataset.theme = preferredTheme;
function updateThemeButton() { $('.theme-button').innerHTML = icon(document.documentElement.dataset.theme === 'dark' ? 'moon' : 'sun'); $('.theme-button').setAttribute('aria-label', `Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme`); }
hydrateIcons(); updateThemeButton();
$('.theme-button').addEventListener('click', () => {
  document.body.classList.add('theme-transition');
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('clarity-theme', theme); } catch { /* Theme also works without storage. */ }
  updateThemeButton(); setTimeout(() => document.body.classList.remove('theme-transition'), 550);
});
$('#menu-button').addEventListener('click', () => { const open = $('header nav').classList.toggle('open'); $('#menu-button').setAttribute('aria-expanded', String(open)); });
window.addEventListener('scroll', () => $('#back-top').hidden = scrollY < 500, {passive:true});
$('#back-top').addEventListener('click', () => window.scrollTo({top:0,behavior:'smooth'}));
let toastTimer;
function toast(message) { $('#toast').textContent = message; $('#toast').classList.add('visible'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#toast').classList.remove('visible'), 3500); }

const [config, metrics, experiment] = await Promise.all([
  fetch('/assets/config.json').then(r => { if (!r.ok) throw Error(); return r.json(); }),
  fetch('/assets/metrics.json').then(r => r.json()), fetch('/assets/exp_metrics.json').then(r => r.json()),
]).catch(() => { $('#main').innerHTML = '<div class="container page-intro"><h1>Let’s try that again.</h1><p>The project files could not load. Please refresh this page.</p></div>'; throw Error('Project files unavailable'); });

const exampleMeta = [
  {title:'A typical profile', short:'Typical profile', text:'Start with the middle values from the dataset. A simple first look at the model.', note:'MEDIAN DATASET VALUES', icon:'leaf'},
  {title:'Room for change', short:'Room for change · Applicant 8347', text:'Explore a higher-risk profile and the changes that could bring its score down.', note:'TEST APPLICANT 8347', icon:'changes'},
  {title:'A more difficult case', short:'Difficult case · Applicant 6470', text:'See why a higher-risk profile may receive no suitable options from the search.', note:'TEST APPLICANT 6470', icon:'lock'},
];
const groups = ['Credit history','Delinquency history','Credit inquiries','Balances and utilisation'];
const groupNames = ['Account history','Payment history','Recent credit checks','Balances & borrowing'];
const groupDescriptions = ['How long the accounts have existed and how many there are.','Whether payments were late, and how long ago.','How often lenders recently checked the credit record.','How much is still owed and how much of the available credit is used.'];
const labels = {
  ExternalRiskEstimate:'Credit bureau score', MSinceOldestTradeOpen:'Age of oldest account', MSinceMostRecentTradeOpen:'Age of newest account',
  AverageMInFile:'Average account age', NumSatisfactoryTrades:'Accounts in good standing', NumTotalTrades:'Total credit accounts',
  NumTradesOpeninLast12M:'Accounts opened in the past year', PercentInstallTrades:'Share of instalment accounts',
  PercentTradesNeverDelq:'Share of accounts never paid late', NumTrades60Ever2DerogPubRec:'Accounts ever 60+ days late',
  NumTrades90Ever2DerogPubRec:'Accounts ever 90+ days late', MSinceMostRecentDelq:'Time since last late payment',
  MaxDelq2PublicRecLast12M:'Worst late-payment code this year', MaxDelqEver:'Worst late-payment code on record',
  MSinceMostRecentInqexcl7days:'Time since last credit check', NumInqLast6M:'Credit checks in the past 6 months',
  NumInqLast6Mexcl7days:'Credit checks excluding the last 7 days', NetFractionRevolvingBurden:'Card credit used',
  NetFractionInstallBurden:'Instalment loan balance ratio', NumRevolvingTradesWBalance:'Card accounts with money owed',
  NumInstallTradesWBalance:'Instalment loans with money owed', NumBank2NatlTradesWHighUtilization:'Card accounts using over 75% of credit',
  PercentTradesWBalance:'Share of accounts with money owed',
};
const explanations = {
  ExternalRiskEstimate:'The bureau’s risk score, from 0 to 100. A higher score usually signals a safer profile.',
  MSinceOldestTradeOpen:'Months since the first account opened. For example, 24 means 2 years.',
  MSinceMostRecentTradeOpen:'Months since the newest account opened. Enter 0 if it opened this month.',
  AverageMInFile:'The average age of all accounts, in months.',
  NumSatisfactoryTrades:'The number of accounts recorded as being in good standing.',
  NumTotalTrades:'The total number of credit accounts in the bureau record.',
  NumTradesOpeninLast12M:'How many new credit accounts opened in the last 12 months.',
  PercentInstallTrades:'The percentage of accounts with scheduled loan payments. Enter 40 for 40%.',
  PercentTradesNeverDelq:'The percentage of accounts that have never had a late payment.',
  NumTrades60Ever2DerogPubRec:'Accounts ever at least 60 days late, or linked to a serious negative public record.',
  NumTrades90Ever2DerogPubRec:'Accounts ever at least 90 days late, or linked to a serious negative public record.',
  MSinceMostRecentDelq:'Months since the last late payment. If the record says “condition not met”, choose that below.',
  MaxDelq2PublicRecLast12M:'Use the original bureau category code, from 0 to 9. This is not a number of late payments.',
  MaxDelqEver:'Use the original bureau category code, from 0 to 9. Do not guess this from days late.',
  MSinceMostRecentInqexcl7days:'Months since the last credit check, ignoring checks from the past 7 days. Maximum 24.',
  NumInqLast6M:'How many times lenders checked this person’s credit in the last 6 months.',
  NumInqLast6Mexcl7days:'The same count, but leave out credit checks from the most recent 7 days.',
  NetFractionRevolvingBurden:'Card balances divided by their limits, as a percentage. ₦20,000 of a ₦100,000 limit means 20.',
  NetFractionInstallBurden:'Money still owed on instalment loans divided by the original loan amounts, as a percentage.',
  NumRevolvingTradesWBalance:'The number of credit cards or revolving accounts that still have a balance.',
  NumInstallTradesWBalance:'The number of instalment loans that still have a balance.',
  NumBank2NatlTradesWHighUtilization:'Bank or national card accounts using more than 75% of their limit.',
  PercentTradesWBalance:'The percentage of all accounts that still have money owed.',
};
const label = f => labels[f] || config.features[f].label;
const unit = f => f.startsWith('MSince') || f === 'AverageMInFile' ? ' months' : f.startsWith('Percent') || f.startsWith('NetFraction') ? '%' : '';
const specialText = {'-7':'Condition not met', '-8':'No usable record', '-9':'No bureau record'};
const valueText = (f, v) => v < 0 ? specialText[String(v)] : `${v}${unit(f)}`;
let state = {values:Object.fromEntries(config.order.map(f => [f,null])),example:'custom',step:0,result:null,assessed:null,options:null,runBusy:false,optionsBusy:false,error:'',present:-1};
let activeRun, activeOptions;
function go(route) { if (location.hash === `#${route}`) { render(); window.scrollTo(0,0); } else location.hash = route; }
const route = () => location.hash.slice(1) || 'home';
function exampleCards() { return exampleMeta.map((x,i) => `<button class="example-card" data-example="${i}"><span class="example-icon">${icon(x.icon)}</span>${icon('arrow','card-arrow')}<h3>${x.title}</h3><p>${x.text}</p><small>${x.note}</small></button>`).join(''); }
function home() { return `<div class="container">
  <section class="hero"><div class="hero-copy"><div class="eyebrow"><i></i> EXPLAINABLE AI. UNDERSTANDABLE RESULTS.</div>
    <h1>A clear view<br>of <em>credit risk.</em></h1><p>See the risk. Understand the reasons. Explore what could change. One simple space to make sense of the model.</p>
    <div class="hero-actions"><button class="button" data-example="1">Try an example ${icon('arrow')}</button><a class="button text" href="#assess">Enter a profile ${icon('arrow')}</a></div>
    <div class="hero-note">${icon('shield')} No sign-up. Example profiles ready to explore.</div>
  </div><div class="hero-art" aria-label="Illustration of the typical example profile result"><div class="art-grid"></div><div class="orbit"></div><div class="orbit two"></div>
    <div class="preview-card"><div class="preview-top"><span>A typical profile</span><span class="tiny-pill">Model result</span></div>
      <div class="preview-score"><div class="mini-dial"><svg viewBox="0 0 100 100"><circle class="dial-bg" cx="50" cy="50" r="43" fill="none" stroke-width="5"/><circle class="dial-line" cx="50" cy="50" r="43" fill="none" stroke-width="5" stroke-dasharray="131 270" stroke-linecap="round"/></svg><div>48.4<span style="font-size:14px">%</span></div></div><div><b>Below the threshold</b><p>Predicted default probability<br>50% research cut-off</p></div></div>
      <div class="preview-reasons"><p>MORE THAN A NUMBER</p><div class="preview-line"><span>Why this result?</span><span>TreeSHAP reasons</span></div><div class="preview-line"><span>What could change?</span><span>Rule-based options</span></div></div>
    </div><div class="float-card">${icon('eye')}<div><b>Every result has a reason.</b><p>Explore what the model sees.</p></div></div>
  </div></section>
  <div class="method-strip"><span>Built on the original research</span><div class="methods"><div>XGBoost<small>The risk prediction</small></div><div>TreeSHAP<small>The reasons behind it</small></div><div>Constrained DiCE<small>The possible changes</small></div></div></div>
  <section class="section"><div class="section-head"><div><div class="eyebrow">A GOOD PLACE TO START</div><h2>Three profiles. Three stories.</h2></div><p>No credit record at hand? Choose an example to see the complete experience with real model results.</p></div><div class="examples">${exampleCards()}</div></section>
  <div class="steps-strip"><div><span class="step-number">01</span><div><h3>Choose or enter a profile</h3><p>Use an example or add 23 credit values.</p></div></div><div><span class="step-number">02</span><div><h3>Understand the result</h3><p>See the score and the reasons that shaped it.</p></div></div><div><span class="step-number">03</span><div><h3>Explore the possibilities</h3><p>Search for changes within the research rules.</p></div></div></div>
</div>`; }

function fieldsForStep(step) { return config.order.filter(f => config.features[f].group === groups[step]); }
function fieldHTML(f) {
  const v = state.values[f]; const coded = v !== null && v < 0;
  return `<div class="field"><label for="value-${f}">${esc(label(f))}${unit(f) === ' months' ? ' (months)' : unit(f) === '%' ? ' (%)' : ''}</label><p id="help-${f}">${esc(explanations[f])}</p>
    <input id="value-${f}" data-field="${f}" type="number" inputmode="numeric" step="1" min="0" max="${config.features[f].max}" value="${coded || v === null ? '' : v}" placeholder="Enter a whole number" aria-describedby="help-${f}" ${coded ? 'disabled' : 'required'}>
    <select aria-label="Record status for ${esc(label(f))}" data-code="${f}"><option value="recorded" ${!coded ? 'selected' : ''}>Recorded value</option><option value="-7" ${v === -7 ? 'selected' : ''}>Condition not met (code -7)</option><option value="-8" ${v === -8 ? 'selected' : ''}>No usable record (code -8)</option><option value="-9" ${v === -9 ? 'selected' : ''}>No bureau record (code -9)</option></select></div>`;
}
function assess() { return `<div class="container"><div class="page-intro"><a class="back-link" href="#home">${icon('back')} Back to overview</a><h1>Let’s look at the profile.</h1><p>Four short sections. Use the values from the credit record, or choose an example below.</p></div>
  <div class="assessment-layout"><aside class="form-sidebar"><p>YOUR ASSESSMENT</p><div class="wizard-steps">${groupNames.map((g,i) => `<button class="wizard-step ${state.step === i ? 'current' : ''}" data-step="${i}" ${state.step === i ? 'aria-current="step"' : ''}><span class="step-dot">${i+1}</span>${g}</button>`).join('')}</div><div class="sidebar-tip"><b>Missing information?</b>Use the record status below each box. The model understands the original bureau codes. Please do not invent a value.</div></aside>
    <section class="form-panel"><div class="profile-selector"><p>${state.example === 'custom' ? 'Your own credit profile' : 'Example profile loaded. You can edit any value.'}</p><select id="profile-choice" aria-label="Choose an example profile"><option value="custom" ${state.example === 'custom' ? 'selected' : ''}>Enter my own profile</option>${exampleMeta.map((x,i) => `<option value="${i}" ${String(state.example) === String(i) ? 'selected' : ''}>${x.short}</option>`).join('')}</select></div>
    <h2>${groupNames[state.step]}</h2><p class="group-description">${groupDescriptions[state.step]}</p>
    <form id="assessment-form"><div class="fields">${fieldsForStep(state.step).map(fieldHTML).join('')}</div>${state.error ? `<p class="form-error" role="alert">${esc(state.error)}</p>` : ''}
    <div class="form-actions"><button class="button outline" type="button" data-prev>${icon('back')} ${state.step ? 'Previous' : 'Overview'}</button><span>SECTION ${state.step + 1} OF 4</span><button class="button" type="submit">${state.step === 3 ? 'See the risk result' : 'Continue'} ${icon('arrow')}</button></div></form>
    </section></div></div>`; }

function loading() { return `<div class="container"><section class="loading-panel" role="status"><div class="loader"></div><h2>Making sense of the profile.</h2><p>The original model is calculating the score and its reasons. The first assessment may take a little longer.</p><button class="button text" data-cancel>Cancel ${icon('back')}</button></section></div>`; }
function reasonHTML(reason, max) {
  const raises = reason.contribution > 0;
  return `<div class="reason"><div class="reason-top"><span>${esc(label(reason.feature))} <span style="color:var(--muted)">· ${esc(valueText(reason.feature, reason.value))}</span></span><small class="${raises ? 'raises' : 'lowers'}">${raises ? 'Raises risk' : 'Lowers risk'}</small></div><div class="reason-bar-track"><div class="reason-bar ${raises ? 'raises' : ''}" style="width:${Math.max(1,Math.abs(reason.contribution)/max*100)}%"></div></div></div>`;
}
function result() {
  if (state.runBusy) return loading();
  if (!state.result) return `<div class="container"><div class="page-intro"><h1>${state.error ? 'Let’s try that again.' : 'Start with a profile.'}</h1><p role="alert">${esc(state.error || 'Choose an example or enter a credit profile to see a result.')}</p><a href="#assess" class="button" style="margin-top:25px">Return to the profile ${icon('arrow')}</a></div></div>`;
  const r = state.result; const p = (r.probability*100).toFixed(1); const max = Math.max(...r.reasons.map(x => Math.abs(x.contribution)),.0001);
  return `<div class="container"><div class="page-intro"><a class="back-link" href="#home">${icon('back')} Explore another profile</a><div class="result-title"><div><div class="eyebrow">THE MODEL’S ASSESSMENT</div><h1>The score. And the story.</h1><p>${state.example === 'custom' ? 'Your entered profile' : exampleMeta[Number(state.example)].short} · Original XGBoost model</p></div><div class="result-actions"><a class="button outline small" href="#assess">Edit profile ${icon('changes')}</a><button class="button outline small" data-print>Save report ${icon('download')}</button></div></div></div>
    <div class="result-grid"><section class="score-card ${r.higher_risk ? 'high' : ''}"><div class="eyebrow">PREDICTED DEFAULT PROBABILITY</div><div class="result-dial"><svg viewBox="0 0 180 180" aria-hidden="true"><circle class="dial-bg" cx="90" cy="90" r="76" fill="none" stroke-width="7"/><circle cx="90" cy="90" r="76" fill="none" stroke="${r.higher_risk ? 'var(--risk)' : 'var(--green)'}" stroke-width="7" stroke-linecap="round" stroke-dasharray="${r.probability * 477.522} 477.522"/></svg><div><strong>${p}%</strong><small>${r.band.toUpperCase()} RISK BAND</small></div></div><h2>${r.higher_risk ? 'Above the research threshold' : 'Below the research threshold'}</h2><p>The model estimates the chance of falling 90 or more days behind on payments. This is a prediction, not a fact about this person.</p><div class="threshold"><span>Research cut-off</span><span>50% probability</span></div></section>
    <section class="reasons-card"><div class="card-heading"><h3>What shaped this result?</h3><span class="tiny-pill">TreeSHAP</span></div><p>These are the five strongest influences. A longer bar means a stronger push on the model’s score.</p>${r.reasons.slice(0,5).map(x => reasonHTML(x,max)).join('')}<div class="reason-caption">${icon('eye')} Each reason explains the model’s behaviour. It does not prove that a factor caused a missed payment.</div></section></div>
    <details class="details"><summary>See all 23 reasons and the calculation</summary><p>TreeSHAP breaks the model’s score into contributions. Positive values raise the score. Negative values lower it. These values are in log-odds, not percentage points.</p><p>Starting score ${r.base_value.toFixed(4)} + contributions ${r.reasons.reduce((n,x)=>n+x.contribution,0).toFixed(4)} = ${(r.base_value+r.reasons.reduce((n,x)=>n+x.contribution,0)).toFixed(4)} log-odds. Converting that score to a probability gives ${p}%.</p><table class="research-table"><thead><tr><th>Credit value</th><th>Input</th><th>TreeSHAP</th></tr></thead><tbody>${r.reasons.map(x => `<tr><td>${esc(label(x.feature))}<br><small>${x.feature}</small></td><td>${esc(valueText(x.feature,x.value))}</td><td class="${x.contribution > 0 ? 'raises' : 'lowers'}">${x.contribution > 0 ? '+' : ''}${x.contribution.toFixed(4)}</td></tr>`).join('')}</tbody></table></details>
    <section class="options-section" id="options-section">${r.higher_risk ? `<div class="options-start"><div><h2>What could change the result?</h2><p>Search for up to three sets of changes that bring the score below 50%. The model keeps past history fixed and only explores changes allowed by the research rules.</p></div><button class="button" data-options ${state.optionsBusy ? 'disabled' : ''}>${state.options ? 'Search again' : 'Explore possible changes'} ${icon('arrow')}</button></div><div class="rule-pills"><span>Past history stays fixed</span><span>Up to 24 months</span><span>Whole-number values</span><span>Every option checked</span></div><div id="options-body" aria-live="polite">${optionsHTML()}</div>` : `<div class="options-start"><div><h2>Already below the cut-off.</h2><p>This profile is below the model’s 50% research threshold, so the study’s counterfactual search is not needed. You can edit the profile to explore a different result.</p></div><a class="button outline" href="#assess">Edit profile ${icon('changes')}</a></div>`}</section>
    <p class="print-only">Clarity · Jamal E.O. Obaseki · Baze University, Abuja. Research and education only. US FICO HELOC data. Not a lending decision or financial advice.</p>
  </div>`;
}
function optionsHTML() {
  if (state.optionsBusy) return `<div class="inline-loader" role="status"><div class="loader"></div><span>Searching for realistic options. This can take a minute or two. You can still explore the rest of this page.</span></div>`;
  if (!state.options) return '<p class="options-note">The search runs when you choose “Explore possible changes”. Model suggestions are not financial advice or a promise of approval.</p>';
  if (state.options.error) return `<div class="form-error" role="alert">${esc(state.options.error)}</div>`;
  if (!state.options.options.length) return `<div class="callout"><b>No suitable option found.</b>The search did not find a set of allowed changes that brought this score below 50% within the 24-month rules. This does not prove that every possible option is impossible. The reasons above show what the model is responding to.</div>`;
  return state.options.options.map((option,i) => `<div class="option-card"><div class="card-heading"><h3>Possibility ${i+1}</h3><strong>${(state.result.probability*100).toFixed(1)}% → ${(option.probability*100).toFixed(1)}%</strong></div><div class="option-changes">${option.changes.map(c => `<div class="option-change"><span>${esc(label(c.feature))}${unit(c.feature) === ' months' ? '<small> · months</small>' : ''}</span><span>${esc(valueText(c.feature,c.old))} → ${esc(valueText(c.feature,c.new))}</span></div>`).join('')}</div><button class="button text small" data-apply-option="${i}">View this changed profile ${icon('arrow')}</button></div>`).join('')+'<p class="options-note">These are model scenarios, not guaranteed outcomes. Time-based values are searched separately, even though they move together in real life. Each shown option follows the rules and was checked against the model again.</p>';
}
const metric = (name,value,text) => `<div class="metric-card"><span class="metric-label">${name}</span><strong>${value}</strong><p>${text}</p></div>`;
function evidence() { return `<div class="container"><div class="page-intro"><div class="eyebrow">THE RESEARCH, IN THE OPEN</div><h1>Evidence behind the model.</h1><p>The recorded study results, with a plain-English explanation of what each number tells us.</p></div>
  <section class="evidence-section"><div class="metric-grid">${metric('AUC-ROC',metrics.auc.toFixed(4),'How well the model ranks risky profiles above safer ones. 0.5 is chance; 1.0 is perfect.')}${metric('Accuracy',`${(metrics.acc*100).toFixed(1)}%`,'The share of test profiles classified correctly at the 50% cut-off.')}${metric('Held-out test profiles','2,092','Real applicants set aside to assess the model after training.')}${metric('Credit values per profile','23','The bureau features used to make each prediction.')}</div>
  <h2>Prediction quality</h2><p class="evidence-note">The dataset contains 10,459 US home-equity credit applicants. The study split it into 8,367 training profiles and 2,092 test profiles. SMOTE added 367 synthetic training rows. The recorded AUC 95% bootstrap interval is ${metrics.auc_ci_low.toFixed(3)} to ${metrics.auc_ci_high.toFixed(3)}.</p>
  <table class="research-table"><thead><tr><th>Measure</th><th>Recorded result</th><th>What it means</th></tr></thead><tbody><tr><td>Precision</td><td>${(metrics.prec*100).toFixed(1)}%</td><td>Of profiles flagged as risky, this share was actually in the “Bad” class.</td></tr><tr><td>Recall</td><td>${(metrics.rec*100).toFixed(1)}%</td><td>Of the “Bad” profiles, this share was found by the model.</td></tr><tr><td>F1 score</td><td>${metrics.f1.toFixed(4)}</td><td>A single score balancing precision and recall.</td></tr><tr><td>Gini</td><td>${metrics.gini.toFixed(4)}</td><td>Another ranking measure, calculated as 2 × AUC − 1.</td></tr><tr><td>KS statistic</td><td>${metrics.ks.toFixed(4)}</td><td>The largest separation between the two class score distributions.</td></tr></tbody></table>
  <div class="charts-grid">${[['fig_roc.png','Risk ranking','The curve shows the trade-off between finding risky profiles and incorrectly flagging safer ones.'],['fig_confusion.png','Correct and incorrect classifications','Read the counts of correct predictions, false alarms, and missed risky profiles.'],['fig_shap_importance.png','The strongest overall influences','These are the average TreeSHAP contributions across the evaluated profiles.'],['fig_baselines.png','Comparison with other models','The notebook compared the tuned model with its recorded baseline models.']].map(([file,title,text]) => `<figure class="chart"><img src="/assets/${file}" loading="lazy" alt="Original notebook figure: ${title}"><figcaption>${title}</figcaption><p>${text}</p></figure>`).join('')}</div>
  <h2>Possible changes: what the study found</h2><p class="evidence-note">These are saved results from <b>10 rejected test applicants</b>, not all 2,092 test profiles. The study requested 30 options and found 14. Five of the ten applicants received at least one option.</p>
  <div class="metric-grid">${metric('Decision-flipping options','14 of 14','Every produced option brought the profile below the research cut-off.')}${metric('Applicant coverage','5 of 10','Half of the ten rejected study profiles received a suitable option.')}${metric('Rule compliance','14 of 14','Every produced option followed the study’s actionability rules.')}${metric('Changes per option',experiment.sparsity.toFixed(2),'The average number of credit values changed in a produced option.')}</div>
  <h2>Stability and limits</h2><p class="evidence-note">The study checked whether decisions and explanations stayed similar when inputs or search seeds changed. These are different checks, so their results should be read separately.</p>
  <table class="research-table"><thead><tr><th>Check</th><th>Result</th><th>Meaning</th></tr></thead><tbody><tr><td>Whole-number noise</td><td>${(experiment['prediction_stability_whole_0.10sd']*100).toFixed(1)}%</td><td>Decisions unchanged after small whole-number input changes.</td></tr><tr><td>Very small decimal noise</td><td>${(experiment['prediction_stability_literal_0.01units']*100).toFixed(1)}%</td><td>Decisions unchanged with 0.01-unit continuous noise.</td></tr><tr><td>TreeSHAP top-five repeat overlap</td><td>${experiment.shap_top5_rerun_jaccard.toFixed(2)}</td><td>The top five reasons were identical when the same input was explained again.</td></tr><tr><td>Advice overlap across seeds</td><td>${experiment.cf_stability_seed.toFixed(2)}</td><td>Average overlap of the features suggested when the search seed changed.</td></tr><tr><td>Advice overlap with input noise</td><td>${experiment.cf_stability_noise.toFixed(2)}</td><td>Average overlap after the input was slightly changed.</td></tr></tbody></table>
  <div class="callout"><b>Where this research stops</b>This is a US home-equity dataset. The results have not been validated for Nigerian lending or other products. The original study computed special-code weights on the full dataset and included a training-only sensitivity check. Searchable features can move together in real life, but the counterfactual search treats them separately. A prediction or an option is not a guarantee.</div>
  <div class="project-note"><b>Original research</b><br>Explainable Artificial Intelligence in Financial Risk Prediction: A Dual-Layer Framework for Stable and Actionable Counterfactuals.<br>Jamal E.O. Obaseki · MSc Computer Science · Baze University, Abuja.<br><a class="link" href="https://github.com/motechbello1/XAI-Risk-Prediction" target="_blank" rel="noopener noreferrer">Open the source code and full notebook ${icon('arrow')}</a></div>
  </section></div>`; }
function guide() { return `<div class="container"><div class="page-intro"><div class="eyebrow">A SIMPLE WALKTHROUGH</div><h1>Make the model make sense.</h1><p>You do not need to know machine learning to explore this project. Start with a profile, then follow the story.</p></div>
  <div class="guide-layout"><section><div class="guide-step"><span class="step-number">01</span><div><h3>Start with an example</h3><p>Choose “Room for change” on the home page. It loads a real test profile and sends its 23 credit values to the original model. You can also enter your own values in four short sections.</p><button class="button outline small" data-example="1">Try the example ${icon('arrow')}</button></div></div>
  <div class="guide-step"><span class="step-number">02</span><div><h3>Read the score</h3><p>The percentage is the model’s estimated chance of the “Bad” outcome in this dataset: falling 90 or more days behind. For example, 60% means the model estimated a chance of 60 out of 100. It does not mean the model is 60% accurate. This research uses 50% as its cut-off.</p></div></div>
  <div class="guide-step"><span class="step-number">03</span><div><h3>Look at the reasons</h3><p>The model gives each credit value a push up or down. TreeSHAP measures those pushes. The website shows the five strongest first. Open “See all 23 reasons” to see the full calculation.</p></div></div>
  <div class="guide-step"><span class="step-number">04</span><div><h3>Explore what could change</h3><p>For a score at or above 50%, choose “Explore possible changes”. DiCE searches for changes that could bring the model’s score down. It cannot rewrite past late payments. It uses whole numbers and a 24-month horizon. Sometimes the search finds no suitable option.</p></div></div>
  <div class="guide-step"><span class="step-number">05</span><div><h3>Show the evidence</h3><p>Open “Model & evidence” to show the recorded test results and original figures. For a school presentation, choose “Present project” at the top. It walks you through the project with short, simple lines you can say aloud.</p><button class="button outline small" data-present>Start the presentation ${icon('present')}</button></div></div></section>
  <aside class="glossary"><h2>A few useful words.</h2><dl><dt>Credit bureau</dt><dd>An organisation that keeps records of borrowing and payments.</dd><dt>XGBoost</dt><dd>The prediction model. Many small decision trees work together to estimate the risk.</dd><dt>TreeSHAP</dt><dd>A way to divide the model’s score into the contribution of each input. Think of asking who pushed a team’s score up or down.</dd><dt>Counterfactual</dt><dd>A “what if” example. If some values changed, would the model give a different result?</dd><dt>Constrained DiCE</dt><dd>A search for different “what if” examples, with rules that limit which values can change.</dd><dt>Weight of Evidence</dt><dd>A learned score used to replace special missing-record codes before the model reads them.</dd><dt>HELOC</dt><dd>A home-equity line of credit. A US borrowing product secured against a home.</dd></dl></aside></div>
  <div class="project-note"><b>About your inputs</b><br>The website sends the 23 credit values to its prediction service. It does not ask for a name, bank account or identity number. The application processes values in memory and does not save profiles or reports on the server. “Save report” opens your browser’s print dialog, where you can choose Save as PDF. Hosting providers may keep ordinary request metadata.<br><br><b>Missing-record codes</b><br>−7: condition not met. −8: no usable or valid records. −9: no bureau record. Choose the meaning from the credit report. Do not replace missing information with a guessed number.</div></div>`; }

function render() {
  const current = route();
  document.title = `${({home:'Credit risk, explained',assess:'Risk assessment',result:'Your risk result',evidence:'Model & evidence',guide:'How it works'})[current] || 'Credit risk, explained'} | Clarity`;
  $('#main').innerHTML = `<div class="page-enter">${({home,assess,result,evidence,guide}[current] || home)()}</div>`;
  document.querySelectorAll('[data-nav]').forEach(a => { const selected = a.dataset.nav === (current === 'result' ? 'assess' : current); a.classList.toggle('active',selected); if(selected) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); });
  $('header nav').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded','false');
  renderPresentation();
}
async function request(operation, values, controller) {
  const timeout = setTimeout(() => controller.abort(), operation === 'options' ? 285000 : 90000);
  try {
    const response = await fetch('/api/index', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({operation,values}),signal:controller.signal});
    const data = await response.json().catch(() => ({error:'The service returned an unexpected response. Please try again.'}));
    if (!response.ok) throw new Error(data.error || 'The model could not complete this request.');
    return data;
  } finally { clearTimeout(timeout); }
}
async function runAssessment() {
  activeRun?.abort(); activeOptions?.abort();
  const controller = new AbortController(); activeRun = controller;
  state.error = ''; state.runBusy = true; state.result = null; state.options = null; state.optionsBusy = false; state.assessed = {...state.values}; go('result');
  try { const data = await request('predict',state.assessed,controller); if (activeRun !== controller) return; state.result = data; }
  catch (e) { if (activeRun !== controller) return; state.error = e.name === 'AbortError' ? 'The request took too long or was cancelled. Please try again.' : e.message; }
  finally { if(activeRun === controller) { state.runBusy = false; if(route() === 'result') render(); } }
}
async function searchOptions() {
  if (state.optionsBusy || !state.result) return;
  const controller = new AbortController(); activeOptions = controller;
  state.optionsBusy = true; state.options = null;
  const refresh = () => { if (route() === 'result' && $('#options-body')) { $('#options-body').innerHTML = optionsHTML(); $('[data-options]').disabled = state.optionsBusy; } renderPresentation(); };
  refresh();
  try { const data = await request('options',state.assessed,controller); if(activeOptions === controller) state.options = data; }
  catch(e) { if(activeOptions === controller) state.options = {error:e.name === 'AbortError' ? 'The search took too long. Please try again. Your risk result is still available.' : e.message}; }
  finally { if(activeOptions === controller) { state.optionsBusy = false; refresh(); } }
}
function loadExample(i) { activeRun?.abort(); activeOptions?.abort(); state = {...state,values:{...config.examples[i]},example:String(i),step:0,result:null,options:null,error:'',optionsBusy:false,runBusy:false}; }
function checkAll() { for(const f of config.order) { const v=state.values[f]; if(v === null || !Number.isInteger(v) || (v<0 && ![-7,-8,-9].includes(v)) || v>config.features[f].max) { state.step = groups.indexOf(config.features[f].group); state.error = `Please check “${label(f)}”. Enter a whole number between 0 and ${config.features[f].max}, or choose a record status.`; render(); $(`#value-${f}`)?.focus(); return false; } } return true; }
document.addEventListener('input', e => { const f=e.target.dataset.field; if(f) { state.values[f] = e.target.value === '' ? null : Number(e.target.value); state.result=null; state.options=null; } });
document.addEventListener('change', e => {
  if(e.target.dataset.code) { const f=e.target.dataset.code; state.values[f] = e.target.value === 'recorded' ? null : Number(e.target.value); state.result=null; state.options=null; render(); $(`[data-code="${f}"]`).focus(); }
  if(e.target.id === 'profile-choice') { if(e.target.value === 'custom') { state.values=Object.fromEntries(config.order.map(f=>[f,null])); state.example='custom'; state.result=null; state.options=null; state.error=''; } else loadExample(Number(e.target.value)); render(); }
});
document.addEventListener('submit', e => {
  if(e.target.id !== 'assessment-form') return;
  e.preventDefault(); state.error='';
  if(state.step < 3) { state.step++; render(); $('.form-panel h2').setAttribute('tabindex','-1'); $('.form-panel h2').focus({preventScroll:true}); $('.form-panel').scrollIntoView({behavior:'smooth',block:'start'}); }
  else if(checkAll()) runAssessment();
});
document.addEventListener('click', async e => {
  const target=e.target.closest('button, a'); if(!target) return;
  if(target.dataset.example !== undefined) { loadExample(Number(target.dataset.example)); await runAssessment(); }
  else if(target.dataset.step !== undefined) { state.step=Number(target.dataset.step); state.error=''; render(); }
  else if(target.hasAttribute('data-prev')) { if(state.step) {state.step--;state.error='';render();}else go('home'); }
  else if(target.hasAttribute('data-options')) searchOptions();
  else if(target.hasAttribute('data-print')) { document.querySelectorAll('.details').forEach(x=>x.open=true); window.print(); }
  else if(target.hasAttribute('data-cancel')) { activeRun?.abort(); activeRun=null; state.runBusy=false; go('assess'); }
  else if(target.dataset.applyOption !== undefined) { const option=state.options?.options[Number(target.dataset.applyOption)]; if(option) { state.values={...option.values}; state.example='custom'; state.step=0; await runAssessment(); toast('Assessing the changed profile.'); } }
  else if(target.hasAttribute('data-present') || target.id === 'present-button') { if(state.present>=0) stopPresentation(); else { state.present=0;go('home');renderPresentation(); } }
  else if(target.hasAttribute('data-stop-presentation')) stopPresentation();
  else if(target.hasAttribute('data-next-presentation')) await nextPresentation();
});
const presentationSteps = [
  ['Introduce the project','“My project predicts credit risk and explains the result. I will show the score, its main reasons, and the changes the model can explore.”','Open the example'],
  ['Show the prediction','“This is one of the test profiles. The percentage is the model’s estimated risk. The study uses 50% as the cut-off. It is a research result, not a real lending decision.”','Show the reasons'],
  ['Explain the reasons','“These bars show the strongest pushes on the score. TreeSHAP tells me which inputs raised the model’s score and which inputs lowered it.”','Explore changes'],
  ['Show the possible changes','“The search keeps past history fixed. It only tries allowed changes over 24 months. Every shown option is checked by the model. If none is found, the website says so.”','Show the evidence'],
  ['Explain the evidence','“The model was tested on 2,092 held-out profiles. Its AUC is 0.7933. The options study covered ten rejected profiles. These results are for this dataset and do not guarantee performance elsewhere.”','Finish presentation'],
];
function renderPresentation() {
  const host=$('#presentation'); host.hidden=state.present<0;
  $('#present-button').innerHTML = `${icon('present')}<span>${state.present>=0 ? 'End presentation' : 'Present project'}</span>`;
  if(state.present<0) return;
  const [title,text,next]=presentationSteps[state.present];
  host.innerHTML=`<div class="presentation-bar"><div><b>${state.present+1} / 5 · ${title}</b><p>${text}</p></div><div class="presentation-controls"><button class="button small" data-next-presentation ${state.runBusy || state.optionsBusy ? 'disabled' : ''}>${state.runBusy || state.optionsBusy ? 'Please wait…' : next} ${icon('arrow')}</button><button class="icon-button" aria-label="End presentation" data-stop-presentation>${icon('close')}</button></div></div>`;
}
function stopPresentation(){state.present=-1;renderPresentation();}
async function nextPresentation() {
  state.present++;
  if(state.present===1){loadExample(1);await runAssessment();}
  else if(state.present===2){go('result');setTimeout(()=>$('.reasons-card')?.scrollIntoView({behavior:'smooth',block:'center'}),30);}
  else if(state.present===3){go('result');setTimeout(()=>$('#options-section')?.scrollIntoView({behavior:'smooth',block:'center'}),30);await searchOptions();}
  else if(state.present===4) go('evidence');
  else {stopPresentation();toast('Presentation complete.');}
  renderPresentation();
}
window.addEventListener('hashchange', () => { render();window.scrollTo(0,0);$('#main').focus({preventScroll:true}); });
render();
