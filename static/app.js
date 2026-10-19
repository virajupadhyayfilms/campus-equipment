'use strict';
let state = null;
let currentPage = 'dashboard';
let formAction = null;
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const badge = value => `<span class="badge ${escapeHTML(value.toLowerCase().replaceAll(' ','-'))}">${escapeHTML(value)}</span>`;
const dateText = value => value ? new Date(value + 'T12:00:00').toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}) : '—';
const table = (headers, body) => body.length ? `<table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${body.join('')}</tbody></table>` : '<div class="empty">No matching records.</div>';
function notice(message, error=false) { $('notice').textContent=message; $('notice').className=error?'error':''; $('notice').hidden=false; }
async function api(path, method='GET', payload) {
  const response = await fetch(path,{method,headers:{'Content-Type':'application/json'},...(payload?{body:JSON.stringify(payload)}:{})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
  return result;
}
async function load() {
  try { state=await api('/api/data'); $('loading').hidden=true; render(); showPage(currentPage); }
  catch(e) { $('loading').hidden=true; notice(e.message,true); }
}
function showPage(page) {
  currentPage=page;
  document.querySelectorAll('.page').forEach(el=>el.hidden=el.id!==page || !state);
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.page===page));
  const titles={dashboard:['Overview','Keep track of equipment, borrowers, and returns.'],equipment:['Equipment','Manage individual assets and their availability.'],students:['Students','Maintain borrower records and contact details.'],loans:['Loans & Returns','Issue equipment, record returns, and view loan history.'],reports:['Reports','A summary of inventory and borrowing activity.']};
  $('page-title').textContent=titles[page][0]; $('page-subtitle').textContent=titles[page][1];
}
function loanRows(loans) {
  return loans.map(l=>`<tr><td><strong>${escapeHTML(l.equipment_name)}</strong><small>${escapeHTML(l.asset_code)} · Loan #${l.loan_id}</small></td><td>${escapeHTML(l.student_name)}<small>${escapeHTML(l.roll_number)}</small></td><td>${dateText(l.issue_date)}</td><td>${dateText(l.due_date)}</td><td>${badge(l.status)}</td><td>${l.return_date?dateText(l.return_date):`<button class="small-button" data-return="${l.loan_id}">Record Return</button>`}</td></tr>`);
}
function render() {
  const {equipment,students,loans,events,reports}=state;
  const available=equipment.filter(e=>e.status==='Available').length;
  const open=loans.filter(l=>l.return_date===null);
  const late=open.filter(l=>l.status==='Overdue').length;
  $('stats').innerHTML=[['Total Equipment',equipment.length,'Individual campus assets',''],['Available',available,'Ready to be issued','available'],['On Loan',open.length,'Awaiting a return',''],['Overdue',late,'Past the due date','overdue']].map(([label,note,sub,cl])=>`<div class="stat ${cl}"><div class="label">${label}</div><strong>${note}</strong><small>${sub}</small></div>`).join('');
  $('current-loans').innerHTML=table(['Equipment','Borrower','Issued','Due Date','Status','Return'],loanRows([...open].sort((a,b)=>a.due_date.localeCompare(b.due_date)).slice(0,5)));
  $('activity').innerHTML=events.slice(0,5).map(e=>{const l=loans.find(l=>l.loan_id===e.loan_id);return `<div class="event"><span class="event-dot"></span><div><strong>${escapeHTML(l?.equipment_name||'Equipment')} ${e.event_type==='Issued'?'issued to':'returned by'} ${escapeHTML(l?.student_name||'student')}</strong><small>Loan #${e.loan_id} · ${escapeHTML(new Date(e.recorded_at).toLocaleString('en-IN'))}</small></div></div>`;}).join('')||'<div class="empty">No activity yet.</div>';
  renderCharts();renderEquipment();renderStudents();renderLoans();
  $('category-report').innerHTML=table(['Category','Total Items','On Loan','Maintenance','Available'],reports.map(r=>`<tr><td>${escapeHTML(r.category_name)}</td><td>${r.total_items}</td><td>${r.on_loan}</td><td>${r.maintenance_items}</td><td>${r.total_items-r.on_loan-r.maintenance_items}</td></tr>`));
  $('borrower-report').innerHTML=table(['Student','Roll Number','Total Loans','Open Loans'],state.borrower_report.map(s=>`<tr><td>${escapeHTML(s.student_name)}</td><td>${escapeHTML(s.roll_number)}</td><td>${s.total_loans}</td><td>${s.open_loans}</td></tr>`));
}
const STATUS_COLORS={'Available':'var(--available)','On Loan':'var(--onloan)','Maintenance':'var(--maint)','Active':'var(--onloan)','Overdue':'var(--overdue)','Returned':'var(--available)'};
// rows: [{name, parts:[{label,value,color}]}] -> horizontal (stacked) bars sharing one scale.
function barChart(rows,stack=false) {
  const max=Math.max(1,...rows.map(r=>r.parts.reduce((t,p)=>t+p.value,0)));
  if(!rows.length)return '<div class="empty">No data yet.</div>';
  return rows.map(r=>{const total=r.parts.reduce((t,p)=>t+p.value,0);const parts=r.parts.filter(p=>p.value>0);
    return `<div class="bar-row${stack?' stack':''}"><span class="name" title="${escapeHTML(r.name)}">${escapeHTML(r.name)}</span><span class="track"><span class="bar" style="width:calc((100% - 34px) * ${(total/max).toFixed(4)})">${parts.map(p=>`<span class="seg" style="flex:${p.value};background:${p.color}" data-tip="${escapeHTML(r.name)} · ${escapeHTML(p.label)}: ${p.value}"></span>`).join('')}</span><span class="value">${total}</span></span></div>`;}).join('');
}
function renderCharts() {
  const {equipment,loans,students}=state;
  const cats=['Available','On Loan','Maintenance'];
  $('category-legend').innerHTML=cats.map(c=>`<span><i style="background:${STATUS_COLORS[c]}"></i>${c}</span>`).join('');
  const byCat={};equipment.forEach(e=>{(byCat[e.category_name]??={Available:0,'On Loan':0,Maintenance:0})[e.status]++;});
  $('category-chart').innerHTML=barChart(Object.entries(byCat).sort((a,b)=>a[0].localeCompare(b[0])).map(([name,c])=>({name,parts:cats.map(k=>({label:k,value:c[k],color:STATUS_COLORS[k]}))})));
  $('status-chart').innerHTML=barChart(['Active','Overdue','Returned'].map(k=>({name:k,parts:[{label:'Loans',value:loans.filter(l=>l.status===k).length,color:STATUS_COLORS[k]}]})));
  const dept={};students.forEach(s=>dept[s.department]??=0);
  const deptOf=Object.fromEntries(students.map(s=>[s.student_id,s.department]));
  loans.forEach(l=>{const d=deptOf[l.student_id];if(d)dept[d]++;});
  $('department-chart').innerHTML=barChart(Object.entries(dept).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).map(([name,v])=>({name,parts:[{label:'Loans',value:v,color:'var(--teal)'}]})),true);
}
document.addEventListener('mousemove',event=>{const tip=$('chart-tip');const t=event.target.closest?.('[data-tip]');
  if(!t){tip.hidden=true;return;}tip.textContent=t.dataset.tip;tip.hidden=false;
  const x=Math.min(event.clientX+12,window.innerWidth-tip.offsetWidth-8);tip.style.left=x+'px';tip.style.top=(event.clientY-36)+'px';});
function renderEquipment() {
  const q=$('equipment-search').value.toLowerCase();const filter=$('equipment-filter').value;
  $('equipment-table').innerHTML=table(['Asset Code','Equipment','Category','Condition','Status','Actions'],state.equipment.filter(e=>(!filter||e.status===filter)&&`${e.asset_code} ${e.equipment_name} ${e.category_name}`.toLowerCase().includes(q)).map(e=>`<tr><td>${escapeHTML(e.asset_code)}</td><td><strong>${escapeHTML(e.equipment_name)}</strong></td><td>${escapeHTML(e.category_name)}</td><td>${escapeHTML(e.condition)}</td><td>${badge(e.status)}</td><td>${e.status==='On Loan'?'—':`<button class="small-button" data-condition="${e.equipment_id}">Condition</button><button class="small-button danger" data-delete-equipment="${e.equipment_id}">Delete</button>`}</td></tr>`));
}
function renderStudents() {
  const q=$('student-search').value.toLowerCase();
  $('students-table').innerHTML=table(['Roll Number','Student','Department','Email','Actions'],state.students.filter(s=>`${s.student_name} ${s.roll_number}`.toLowerCase().includes(q)).map(s=>`<tr><td>${escapeHTML(s.roll_number)}</td><td><strong>${escapeHTML(s.student_name)}</strong></td><td>${escapeHTML(s.department)}</td><td>${escapeHTML(s.email)}</td><td><button class="small-button danger" data-delete-student="${s.student_id}">Delete</button></td></tr>`));
}
function renderLoans() {
  const q=$('loan-search').value.toLowerCase();const filter=$('loan-filter').value;
  $('loans-table').innerHTML=table(['Equipment','Borrower','Issued','Due Date','Status','Returned / Action'],loanRows(state.loans.filter(l=>(!filter||l.status===filter)&&`${l.student_name} ${l.equipment_name} ${l.asset_code}`.toLowerCase().includes(q))));
}
const input=(label,name,type='text',max=100)=>`<label>${label}<input name="${name}" type="${type}" maxlength="${max}" required></label>`;
const select=(label,name,items)=>`<label>${label}<select name="${name}" required><option value="">Select…</option>${items.map(([v,t])=>`<option value="${escapeHTML(v)}">${escapeHTML(t)}</option>`).join('')}</select></label>`;
const conditions=()=>select('Condition','condition',['Good','Fair','Maintenance'].map(c=>[c,c]));
function modal(title,fields,action,submit='Save') { $('modal-title').textContent=title;$('form-fields').innerHTML=fields;$('form-error').textContent='';$('submit-form').textContent=submit;formAction=action;$('modal').showModal(); }
function issueForm() {
  if(!state)return notice('Connect to the database first.',true);
  const available=state.equipment.filter(e=>e.status==='Available');
  if(!available.length||!state.students.length)return notice('Add a student and an available item before issuing equipment.',true);
  modal('Issue Equipment',select('Borrower','student_id',state.students.map(s=>[s.student_id,`${s.student_name} (${s.roll_number})`]))+select('Equipment','equipment_id',available.map(e=>[e.equipment_id,`${e.asset_code} — ${e.equipment_name}`]))+input('Due Date','due_date','date')+'<label>Notes (Optional)<input name="notes" maxlength="300" placeholder="Purpose of borrowing"></label>',p=>api('/api/loans','POST',p),'Issue Equipment');
  document.querySelector('[name=due_date]').min=state.today;
}
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>showPage(b.dataset.page));
$('new-loan').onclick=issueForm;$('view-loans').onclick=()=>showPage('loans');
$('close-modal').onclick=$('cancel-modal').onclick=()=>$('modal').close();
$('add-student').onclick=()=>modal('Add Student',input('Roll Number','roll_number','text',30)+input('Student Name','student_name')+input('Department','department','text',60)+input('Email','email','email',120),p=>api('/api/students','POST',p));
$('add-category').onclick=()=>modal('Add Category',input('Category Name','category_name','text',60),p=>api('/api/categories','POST',p));
$('add-equipment').onclick=()=>state?modal('Add Equipment',input('Asset Code','asset_code','text',30)+input('Equipment Name','equipment_name')+select('Category','category_id',state.categories.map(c=>[c.category_id,c.category_name]))+conditions(),p=>api('/api/equipment','POST',p)):notice('Connect to the database first.',true);
$('entry-form').onsubmit=async event=>{event.preventDefault();const submit=$('submit-form');submit.disabled=true;try{const p=Object.fromEntries(new FormData(event.target));const result=await formAction(p);$('modal').close();notice(result.message);await load();}catch(e){$('form-error').textContent=e.message;}finally{submit.disabled=false;}};
for(const [id,fn] of [['equipment-search',renderEquipment],['student-search',renderStudents],['loan-search',renderLoans]])$(id).oninput=()=>state&&fn();
$('equipment-filter').onchange=()=>state&&renderEquipment();$('loan-filter').onchange=()=>state&&renderLoans();
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.condition){modal('Update Condition',conditions(),p=>api(`/api/equipment/${b.dataset.condition}`,'PATCH',p));document.querySelector('[name=condition]').value=state.equipment.find(e=>e.equipment_id===Number(b.dataset.condition)).condition;return;}
 let path,method='POST',question;
 if(b.dataset.return){path=`/api/loans/${b.dataset.return}/return`;question='Record this equipment as returned today?';}
 else if(b.dataset.deleteStudent){path=`/api/students/${b.dataset.deleteStudent}`;method='DELETE';question='Delete this student? Students with loan history cannot be deleted.';}
 else if(b.dataset.deleteEquipment){path=`/api/equipment/${b.dataset.deleteEquipment}`;method='DELETE';question='Delete this equipment? Items with loan history cannot be deleted.';}
 else return;
 if(!confirm(question))return;
 b.disabled=true;try{const r=await api(path,method);notice(r.message);await load();}catch(e){notice(e.message,true);}finally{b.disabled=false;}
});
load();
