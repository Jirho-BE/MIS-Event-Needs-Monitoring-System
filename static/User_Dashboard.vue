<script setup>
import { ref, computed, onMounted, watch } from 'vue'

// ==========================================
// REACTIVE STATES
// ==========================================
const isLoading = ref(true)

// Data Lists
const allEvents = ref([])
const organizationList = ref([])
const itemList = ref([])
const needsList = ref([])
const eventNeedsList = ref([])

// Current User State
const currentUserId = ref(null)
const viewEvent = ref(null)

// Dashboard Left Column (Management) States
const tabMode = ref('add') 
const selectedEventToEdit = ref('')

// Dashboard Right Column (Viewer) States
const selectedDateFilter = ref(getTodayDate())

// Forms
const eventForm = ref({ title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] })

// ==========================================
// CUSTOM NOTIFICATION & CONFIRM SYSTEM
// ==========================================
const toasts = ref([])
let toastIdCounter = 0

function showToast(message, type = 'success') {
  const id = toastIdCounter++
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 3500)
}

// ==========================================
// REUSABLE API FETCH HELPER
// ==========================================
async function apiFetch(endpoint, method = 'GET', payload = null) {
  const token = localStorage.getItem('access_token')
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Accept': 'application/json' }
  const config = { method, headers }
  if (payload) config.body = JSON.stringify(payload)

  const response = await fetch(endpoint, config)
  if (method === 'DELETE' && response.ok) return { success: true }
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const firstKey = Object.keys(data)[0]
    const errorMsg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey] || response.statusText
    throw new Error(errorMsg || `HTTP ${response.status}`)
  }
  return data
}

// ==========================================
// DATA FETCHING & JWT DECODING
// ==========================================
function getTodayDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function readAccessTokenPayload() {
  try {
    const token = localStorage.getItem('access_token')
    const encodedPayload = token?.split('.')[1]
    if (!encodedPayload) return null

    // JWT payloads use base64url encoding, which may omit padding.
    const base64 = encodedPayload.replace(/-/g, '+').replace(/_/g, '/')
    const paddedBase64 = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')
    return JSON.parse(atob(paddedBase64))
  } catch (error) {
    console.warn('Unable to read the current account from the access token.')
    return null
  }
}

function extractUserIdFromToken() {
  const payload = readAccessTokenPayload()
  return payload?.user_id ?? payload?.account_id ?? payload?.userId ?? payload?.id ?? null
}

// Normalize common REST representations of a foreign key to a comparable ID.
function normalizeForeignKeyId(value) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'object') {
    const nestedId = value.id ?? value.pk ?? value.user_id ?? value.account_id ?? value.owner_id
    return nestedId === null || nestedId === undefined || nestedId === '' ? null : String(nestedId)
  }
  return String(value).trim() || null
}

function getEventOwnerId(event) {
  return normalizeForeignKeyId(event?.owner ?? event?.owner_id ?? event?.account_id ?? event?.account)
}

function asList(responseData) {
  if (Array.isArray(responseData)) return responseData
  if (Array.isArray(responseData?.results)) return responseData.results
  if (Array.isArray(responseData?.data)) return responseData.data
  return []
}

async function fetchAllData() {
  try {
    const [events, orgs, items, needs, eventNeeds] = await Promise.all([
      apiFetch('/api/events-list/'),
      apiFetch('/api/organization-list/'),
      apiFetch('/api/item-list/'),
      apiFetch('/api/needs-list/').catch(() => []),
      apiFetch('/api/event-needs-list/').catch(() => [])
    ])
    allEvents.value = asList(events)
    organizationList.value = asList(orgs)
    itemList.value = asList(items)
    needsList.value = asList(needs)
    eventNeedsList.value = asList(eventNeeds)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    showToast('Some dashboard data could not be loaded. Please refresh and try again.', 'error')
  }
}

// ==========================================
// COMPUTEDS & SYNCING LOGIC
// ==========================================

// Sync Right Column viewer when the user types a date in the left form
watch(() => eventForm.value.date, (newDate) => {
  if (newDate) selectedDateFilter.value = newDate
})

// Right Column Filter: Events matching the selected date
const filteredDateEvents = computed(() => {
  return allEvents.value.filter(event => event.date === selectedDateFilter.value)
})

// Left Column Edit Dropdown: Directly filter events by the logged-in user's ID
const userEvents = computed(() => {
  const loggedInAccountId = normalizeForeignKeyId(currentUserId.value)
  if (!loggedInAccountId) return []

  // This list is deliberately owner-scoped; other accounts' events never appear
  // in the Edit dropdown even though /api/events-list/ may return all events.
  return allEvents.value.filter(event => getEventOwnerId(event) === loggedInAccountId)
})

// Compute Event Needs for the View Modal
const viewEventNeeds = computed(() => {
  if (!viewEvent.value) return []
  const linkedNeeds = eventNeedsList.value.filter(en => en.event_id === viewEvent.value.id)
  return linkedNeeds.map(en => {
    const needData = needsList.value.find(n => n.id === en.needs_id)
    if (needData) {
      const actualItem = itemList.value.find(i => i.id === needData.item_id)
      return { name: actualItem ? actualItem.name : 'Unknown Item', quantity: needData.quantity }
    }
    return null
  }).filter(Boolean)
})

function getOrgName(orgId) {
  const org = organizationList.value.find(o => o.id === orgId)
  return org ? org.name : (orgId || 'N/A')
}

// ==========================================
// FORM POPULATION & WATCHERS
// ==========================================
function resetEventForm() {
  eventForm.value = { title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] }
  selectedEventToEdit.value = ''
}

function setTabMode(mode) {
  tabMode.value = mode
  resetEventForm()
}

watch(selectedEventToEdit, (newId) => {
  if (!newId) return
  const item = userEvents.value.find(i => String(i.id) === String(newId))
  if (!item) return

  eventForm.value.title = item.title
  eventForm.value.venue = item.venue
  eventForm.value.attendies = item.no_of_attendies
  eventForm.value.date = item.date
  eventForm.value.startTime = item.start_tiime || item.start_time
  eventForm.value.endTime = item.end_time
  eventForm.value.organization = item.org_id || item.organization || ''

  const existingLinks = eventNeedsList.value.filter(en => en.event_id === item.id)
  const mappedFormNeeds = existingLinks.map(en => {
    const matchingNeed = needsList.value.find(n => n.id === en.needs_id)
    if (matchingNeed) return { id: matchingNeed.id, item: matchingNeed.item_id, quantity: matchingNeed.quantity }
    return null
  }).filter(Boolean)

  eventForm.value.needs = mappedFormNeeds.length ? mappedFormNeeds : [{ id: null, item: '', quantity: 1 }]
})

// ==========================================
// LIFECYCLE
// ==========================================
onMounted(async () => {
  // Strict check: block access without a token
  const token = localStorage.getItem('access_token')
  if (!token) return window.location.replace('/')

  currentUserId.value = extractUserIdFromToken()

  try {
    isLoading.value = false
    await fetchAllData()
  } catch (error) {
    localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token')
    window.location.replace('/')
  }
})

// ==========================================
// ACTIONS & API CALLS
// ==========================================
function addEventNeedRow() { eventForm.value.needs.push({ id: null, item: '', quantity: 1 }) }
function removeEventNeedRow(idx) { if (eventForm.value.needs.length > 1) eventForm.value.needs.splice(idx, 1) }

async function submitEvent() {
  const { title, venue, attendies, date, startTime, endTime, organization, needs } = eventForm.value
  if (!title.trim() || !venue.trim() || !date || !startTime || !endTime || !organization) return showToast('Fill all event details.', 'error')
  
  try {
    if (tabMode.value === 'add') {
      const createdEvent = await apiFetch('/api/events-create/', 'POST', { title, venue, no_of_attendies: Number(attendies), date, start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization })
      const eventId = createdEvent.id || createdEvent.event_id
      const validNeeds = needs.filter(n => n.item && Number(n.quantity) > 0)
      
      for (const need of validNeeds) {
        const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
        const needId = createdNeed.id || createdNeed.needs_id
        await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: eventId })
      }
      showToast('Event successfully created!')
    } else {
      const ownedEvent = userEvents.value.find(event => String(event.id) === String(selectedEventToEdit.value))
      if (!selectedEventToEdit.value || !ownedEvent) {
        return showToast('Select an event created by your account to edit.', 'error')
      }
      await apiFetch(`/api/events/edit/${ownedEvent.id}/`, 'PATCH', { title, venue, no_of_attendies: attendies, date, start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization })
      
      const validNeeds = needs.filter(n => n.item && Number(n.quantity) > 0)
      for (const need of validNeeds) {
        if (need.id) {
          await apiFetch(`/api/needs/edit/${need.id}/`, 'PATCH', { item_id: need.item, quantity: Number(need.quantity) })
        } else {
          const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
          const needId = createdNeed.id || createdNeed.needs_id
          await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: selectedEventToEdit.value })
        }
      }
      showToast('Event changes saved!')
    }
    resetEventForm()
    await fetchAllData()
  } catch (err) { showToast(err.message, 'error') }
}

function openViewEvent(eventObj) { viewEvent.value = eventObj }
function closeViewEvent() { viewEvent.value = null }
function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('current_username')
  localStorage.removeItem('current_account_id')
  localStorage.removeItem('username')
  localStorage.removeItem('user')
  window.location.replace('/')
}
</script>

<template>
  <div v-if="isLoading" class="loader-screen">
    <div class="spinner"></div><p>VERIFYING ACCESS...</p>
  </div>

  <main v-else class="dashboard-page">
    
    <!-- TOAST NOTIFICATIONS -->
    <div class="toast-container">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">
        [[ toast.message ]]
      </div>
    </div>

    <!-- VIEW EVENT DETAILS MODAL -->
    <div v-if="viewEvent" class="overlay" @click.self="closeViewEvent" @keydown.esc="closeViewEvent">
      <section class="auth-card view-modal">
        <button class="close-button" @click="closeViewEvent">×</button>
        <p class="card-eyebrow">EVENT INFORMATION</p>
        <h2 class="view-title">[[ viewEvent.title ]]</h2>
        
        <div class="view-grid">
          <p><span>STATUS:</span> [[ viewEvent.approved ? 'Approved' : 'Pending' ]]</p>
          <p><span>DATE:</span> [[ viewEvent.date ]]</p>
          <p><span>VENUE:</span> [[ viewEvent.venue ]]</p>
          <p><span>TIME:</span> [[ viewEvent.start_time || viewEvent.start_tiime ]] - [[ viewEvent.end_time ]]</p>
          <p><span>ATTENDEES:</span> [[ viewEvent.no_of_attendies ]]</p>
          <p><span>ORGANIZATION:</span> [[ getOrgName(viewEvent.org_id || viewEvent.organization) ]]</p>
        </div>

        <div v-if="viewEventNeeds.length > 0" class="view-needs">
          <p class="card-eyebrow" style="margin-top: 24px; margin-bottom: 12px;">REQUESTED ITEMS</p>
          <ul>
            <li v-for="(n, index) in viewEventNeeds" :key="index">
              <span class="need-name">[[ n.name ]]</span>
              <span class="need-qty">x[[ n.quantity ]]</span>
            </li>
          </ul>
        </div>
      </section>
    </div>

    <!-- TOP NAVIGATION -->
    <header class="topbar">
      <div class="brand"><span class="brand-icon">M</span><span>MIS <span class="muted">USER DASHBOARD</span></span></div>
      
      <button type="button" class="logout-button" @click="logout" aria-label="Log out of your account">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M10 17l5-5-5-5" />
          <path d="M15 12H3" />
          <path d="M12 3h6a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-6" />
        </svg>
        <span>LOG OUT</span>
      </button>
    </header>

    <!-- USER DASHBOARD CONTENT (2 COLUMNS) -->
    <section class="dashboard-grid">
      
      <!-- COLUMN 1: EVENT MANAGEMENT FORM -->
      <div class="dashboard-column form-column">
        <div class="column-header responsive-header">
          <div class="header-title-group">
            <span class="column-index">01</span><h2>EVENT MANAGEMENT</h2>
          </div>
          <div class="mode-toggle inline">
            <button class="toggle-btn" :class="{ active: tabMode === 'add' }" @click="setTabMode('add')">ADD</button>
            <button class="toggle-btn" :class="{ active: tabMode === 'edit' }" @click="setTabMode('edit')">EDIT</button>
          </div>
        </div>
        
        <!-- EDIT SELECTOR -->
        <div v-if="tabMode === 'edit'" class="edit-selector-container form-embedded">
          <label class="field">
            <span>Select Your Event to Edit</span>
            <select v-model="selectedEventToEdit">
              <option value="" disabled>[[ userEvents.length ? '-- Select existing Event --' : 'No events created by your account' ]]</option>
              <option v-for="opt in userEvents" :key="opt.id" :value="opt.id">[[ opt.title ]]</option>
            </select>
          </label>
        </div>

        <div class="form-scroll-area custom-scroll">
          <div class="tab-form">
            <h3 class="section-title">01. EVENT DETAILS</h3>
            <div class="field-grid">
              <label class="field"><span>Title</span><input v-model="eventForm.title" placeholder="Event Title" /></label>
              <label class="field"><span>Venue</span><input v-model="eventForm.venue" placeholder="Venue Name" /></label>
              <label class="field"><span>No. of Attendees</span><input type="number" v-model="eventForm.attendies" /></label>
              <label class="field"><span>Date</span><input type="date" v-model="eventForm.date" /></label>
              <label class="field"><span>Start Time</span><input type="time" v-model="eventForm.startTime" /></label>
              <label class="field"><span>End Time</span><input type="time" v-model="eventForm.endTime" /></label>
              <label class="field full-width">
                <span>Organization</span>
                <select v-model="eventForm.organization">
                  <option value="" disabled>Select Organization</option>
                  <option v-for="org in organizationList" :key="org.id" :value="org.id">[[ org.name ]]</option>
                </select>
              </label>
            </div>
            
            <h3 class="section-title margin-top">02. EVENT NEEDS</h3>
            <div class="needs-list">
              <div v-for="(need, idx) in eventForm.needs" :key="idx" class="need-row">
                <label class="field flex-grow">
                  <span>Item Name</span>
                  <select v-model="need.item">
                    <option value="" disabled>Select Item</option>
                    <option v-for="item in itemList" :key="item.id" :value="item.id">[[ item.name ]]</option>
                  </select>
                </label>
                <label class="field qty-field"><span>Quantity</span><input type="number" v-model="need.quantity" min="1" /></label>
                <button class="btn-remove-row" @click="removeEventNeedRow(idx)" type="button">✕</button>
              </div>
              <button class="btn-add-row" @click="addEventNeedRow" type="button">+ Add Item Need</button>
            </div>
          </div>
        </div>

        <footer class="panel-bottom-action">
          <button class="submit-button action-btn" style="width: 100%; justify-content: center;" @click="submitEvent">
            [[ tabMode === 'add' ? 'SUBMIT EVENT REQUEST' : 'SAVE CHANGES' ]] <span>↗</span>
          </button>
        </footer>
      </div>

      <!-- COLUMN 2: ONGOING EVENTS VIEWER -->
      <div class="dashboard-column viewer-column">
        <div class="column-header responsive-header">
          <div class="header-title-group">
            <span class="column-index">02</span><h2>EVENTS BY DATE</h2><span class="count">[[ filteredDateEvents.length ]]</span>
          </div>
        </div>

        <!-- EXPLANATORY BANNER -->
        <div class="info-banner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
          <p>Choosing a date on the Event Management form will list down the events for that specific date here.</p>
        </div>
        
        <div class="events-list custom-scroll">
          <div v-for="event in filteredDateEvents" :key="event.id" class="event-card clickable" @click="openViewEvent(event)">
            <h3 class="event-title">[[ event.title ]]</h3>
            <div class="event-details">
              <p><span>STATUS:</span> [[ event.approved ? 'Approved' : 'Pending' ]]</p>
              <p><span>VENUE:</span> [[ event.venue ]]</p>
              <p><span>TIME:</span> [[ event.start_time || event.start_tiime ]] - [[ event.end_time ]]</p>
              <p><span>ORG:</span> [[ getOrgName(event.org_id || event.organization) ]]</p>
            </div>
          </div>
          <div v-if="filteredDateEvents.length === 0" class="empty-state">No events scheduled for [[ selectedDateFilter ]].</div>
        </div>
      </div>

    </section>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html) { min-height: 100%; }
:global(body) { background: #101010; min-width: 320px; margin: 0; overflow-x: hidden; }

.loader-screen { min-height: 100dvh; background: #101010; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #929292; font-family: Inter, sans-serif; font-size: 11px; letter-spacing: 0.1em; }
.spinner { width: 24px; height: 24px; border: 2px solid #333; border-top-color: #f5f5f5; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* DESKTOP PAGE FRAME */
.dashboard-page {
  --bg: #101010; --surface: #141414; --white: #f5f5f5; --muted: #929292; --line: #333333;
  width: 100%; height: 100dvh; min-height: 0; overflow: hidden;
  display: flex; flex-direction: column;
  padding: 28px clamp(16px, 5vw, 76px) 20px;
  background: var(--bg); color: var(--white); font-family: Inter, sans-serif; position: relative;
}

/* TOPBAR */
.topbar { display: flex; flex: 0 0 auto; min-width: 0; align-items: center; justify-content: space-between; gap: 16px; padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 24px; }
.brand { display: inline-flex; align-items: center; gap: 11px; min-width: 0; font-size: 12px; font-weight: 750; letter-spacing: .13em; }
.brand-icon { display: grid; flex: 0 0 auto; width: 30px; height: 30px; place-items: center; border: 1px solid #777; font-size: 15px; font-weight: 800; }
.brand-icon.small { width: 26px; height: 26px; font-size: 12px; }
.muted { color: var(--muted); }
.logout-button {
  display: inline-flex; flex: 0 0 auto; align-items: center; justify-content: center; gap: 9px;
  min-height: 40px; padding: 0 14px; border: 1px solid var(--line); border-radius: 2px;
  background: var(--surface); color: var(--white); font: inherit; font-size: 10px; font-weight: 700;
  letter-spacing: .1em; cursor: pointer; transition: background .2s, border-color .2s;
}
.logout-button svg { width: 16px; height: 16px; flex: 0 0 auto; }
.logout-button:hover, .logout-button:focus-visible { background: #222; border-color: #777; outline: none; }

/* TWO-COLUMN DASHBOARD: all grid children may shrink without overflowing */
.dashboard-grid {
  display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: clamp(16px, 1.8vw, 24px); flex: 1 1 auto; height: auto; min-height: 0; min-width: 0;
}
.dashboard-column {
  display: flex; flex-direction: column; min-width: 0; min-height: 0;
  background: var(--surface); border: 1px solid var(--line); height: auto; overflow: hidden;
}
.column-header { display: flex; flex: 0 0 auto; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; min-width: 0; padding: 20px 20px 16px; border-bottom: 1px solid var(--line); margin-bottom: 16px; }
.header-title-group { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; min-width: 0; }
.column-index { color: var(--muted); font-size: 10px; font-weight: 700; flex: 0 0 auto; }
.column-header h2 { margin: 0; min-width: 0; font-size: clamp(12px, 1vw, 14px); font-weight: 650; letter-spacing: .1em; overflow-wrap: anywhere; }
.count { background: #333; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; flex: 0 0 auto; }

/* EXPLANATORY BANNER */
.info-banner { display: flex; flex: 0 0 auto; align-items: flex-start; gap: 12px; min-width: 0; background: #1a1a1a; border: 1px solid #333; padding: 12px 16px; margin: 0 20px 16px; border-radius: 4px; color: #aaa; }
.info-banner svg { flex: 0 0 16px; width: 16px; height: 16px; margin-top: 2px; color: var(--muted); }
.info-banner p { min-width: 0; margin: 0; font-size: 11px; line-height: 1.5; color: #ccc; overflow-wrap: anywhere; }

/* SHARED SCROLLBARS */
.custom-scroll { overflow-y: auto; overscroll-behavior: contain; }
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }

/* EVENT LIST */
.viewer-column { padding-bottom: 20px; }
.viewer-column .column-header { margin-bottom: 16px; }
.events-list { display: flex; flex: 1 1 auto; flex-direction: column; gap: 16px; min-height: 0; min-width: 0; padding: 0 20px 20px; }
.event-card { min-width: 0; background: #1a1a1a; border: 1px solid #2a2a2a; padding: 16px; border-radius: 2px; transition: border-color 0.2s, background 0.2s; }
.event-card.clickable { cursor: pointer; }
.event-card.clickable:hover { border-color: #777; background: #202020; }
.event-title { margin: 0 0 12px; font-size: 14px; font-weight: 600; letter-spacing: -.02em; overflow-wrap: anywhere; }
.event-details p { margin: 6px 0; min-width: 0; font-size: 11px; color: #ccc; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; overflow-wrap: anywhere; }
.event-details span { flex: 0 0 auto; color: var(--muted); font-size: 9px; font-weight: 700; letter-spacing: .08em; }
.empty-state { color: var(--muted); font-size: 11px; line-height: 1.5; text-align: center; padding: 30px 0; overflow-wrap: anywhere; }

/* FORM AND FIELDS */
.mode-toggle.inline { display: flex; flex: 0 0 auto; border: 1px solid var(--line); border-radius: 2px; overflow: hidden; }
.toggle-btn { padding: 8px 16px; background: transparent; border: none; color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: .1em; cursor: pointer; }
.toggle-btn.active { background: var(--white); color: #111; }
.form-embedded { padding: 0 20px 16px; border-bottom: 1px solid var(--line); background: #101010; }
.form-scroll-area { flex: 1 1 auto; min-height: 0; min-width: 0; padding: 0 20px 20px; }
.tab-form { min-width: 0; }
.section-title { font-size: 11px; font-weight: 700; letter-spacing: .15em; line-height: 1.5; color: var(--muted); margin: 0 0 16px; overflow-wrap: anywhere; }
.section-title.margin-top { margin-top: 32px; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; min-width: 0; }
.field { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.field.full-width { grid-column: 1 / -1; }
.field > span { color: #d0d0d0; font-size: 11px; font-weight: 600; line-height: 1.4; overflow-wrap: anywhere; }
.field input, .field select { display: block; width: 100%; min-width: 0; max-width: 100%; min-height: 40px; padding: 10px 12px; border: 1px solid #383838; border-radius: 0; background: #101010; color: var(--white); font: inherit; font-size: 12px; outline: none; }
.field select { text-overflow: ellipsis; }
.field input:focus, .field select:focus { border-color: #aaa; }
.field input[readonly] { color: #666; background: #1a1a1a; cursor: not-allowed; }
input[type="date"], input[type="time"] { color-scheme: dark; }
input[type="date"]::-webkit-calendar-picker-indicator, input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(1); cursor: pointer; }

/* NEEDS LIST */
.needs-list { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.need-row { display: flex; align-items: flex-end; gap: 12px; width: 100%; min-width: 0; }
.flex-grow { flex: 1 1 0; min-width: 0; }
.qty-field { flex: 0 0 88px; width: 88px; min-width: 0; }
.btn-remove-row { flex: 0 0 40px; height: 40px; width: 40px; padding: 0; background: transparent; border: 1px solid #383838; color: #ff9292; cursor: pointer; }
.btn-add-row { align-self: flex-start; max-width: 100%; background: transparent; border: 1px dashed #555; color: var(--white); padding: 10px 16px; font-size: 11px; font-weight: 600; cursor: pointer; margin-top: 8px; }
.panel-bottom-action { display: flex; flex: 0 0 auto; min-width: 0; padding: 20px; border-top: 1px solid var(--line); background: #101010; }
.submit-button { display: flex; min-width: 0; max-width: 100%; min-height: 45px; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 15px; border: 1px solid #f1f1f1; background: #f1f1f1; color: #111; font-weight: 750; font-size: 12px; line-height: 1.4; overflow-wrap: anywhere; cursor: pointer; }

/* TOASTS */
.toast-container { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: stretch; gap: 10px; width: min(520px, calc(100vw - 24px)); z-index: 2000; }
.toast { max-width: 100%; padding: 12px 18px; border-radius: 4px; font-size: 12px; line-height: 1.5; font-weight: 600; color: #fff; overflow-wrap: anywhere; box-shadow: 0 10px 30px rgba(0,0,0,0.8); animation: slideDown 0.3s ease; }
.toast.success { background: #1a1a1a; border: 1px solid #4caf50; border-left: 4px solid #4caf50; }
.toast.error { background: #1a1a1a; border: 1px solid #ff5252; border-left: 4px solid #ff5252; }
@keyframes slideDown { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

/* EVENT DETAILS MODAL */
.submit-button:disabled { opacity: .6; cursor: wait; }
.overlay { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; overflow-y: auto; padding: 20px; background: #000c; backdrop-filter: blur(5px); }
.auth-card { position: relative; width: min(100%, 430px); min-width: 0; padding: clamp(23px, 5vw, 38px); border: 1px solid #373737; background: #141414; }
.close-button { position: absolute; top: 14px; right: 15px; width: 32px; height: 32px; border: 0; background: transparent; color: #aaa; cursor: pointer; font-size: 24px; }
.card-eyebrow { margin: 0 0 10px; font-size: 9px; font-weight: 700; letter-spacing: .15em; color: var(--muted); }
.auth-card h2 { margin: 0 0 25px; font-size: clamp(1.45rem, 4vw, 2rem); line-height: 1.2; font-weight: 650; letter-spacing: -.05em; overflow-wrap: anywhere; }
.view-modal { width: min(100%, 550px); max-height: 90dvh; overflow-y: auto; }
.view-title { margin-bottom: 24px !important; }
.view-grid { display: grid; gap: 12px; padding-bottom: 16px; border-bottom: 1px dashed var(--line); }
.view-grid p { display: grid; grid-template-columns: 100px minmax(0, 1fr); align-items: start; gap: 12px; min-width: 0; margin: 0; font-size: 13px; line-height: 1.5; color: #ddd; overflow-wrap: anywhere; }
.view-grid span { font-size: 10px; font-weight: 700; color: var(--muted); letter-spacing: .1em; }
.view-needs ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.view-needs li { display: flex; justify-content: space-between; gap: 12px; min-width: 0; background: #1a1a1a; border: 1px solid var(--line); padding: 10px 16px; font-size: 12px; line-height: 1.5; color: #eee; }
.need-name { min-width: 0; overflow-wrap: anywhere; }
.need-qty { flex: 0 0 auto; font-weight: 700; color: var(--muted); }

/* TABLET: stack the panels and let the page scroll naturally */
@media (max-width: 1024px) {
  .dashboard-page { height: auto; min-height: 100dvh; overflow: visible; padding: 24px clamp(16px, 3vw, 32px); }
  .topbar { margin-bottom: 20px; }
  .dashboard-grid { grid-template-columns: minmax(0, 1fr); flex: 0 0 auto; height: auto; min-height: 0; gap: 20px; }
  .dashboard-column { height: auto; min-height: 0; overflow: visible; }
  .form-scroll-area, .events-list { flex: 0 0 auto; min-height: 0; max-height: none; overflow: visible; }
  .viewer-column { padding-bottom: 0; }
}

/* MOBILE */
@media (max-width: 640px) {
  .dashboard-page { padding: 16px 10px 24px; }
  .topbar { gap: 12px; padding-bottom: 16px; margin-bottom: 16px; }
  .brand { gap: 8px; font-size: 10px; line-height: 1.4; letter-spacing: .08em; }
  .brand-icon { width: 28px; height: 28px; font-size: 14px; }
  .logout-button { min-height: 36px; padding: 0 10px; gap: 6px; font-size: 9px; }
  .logout-button svg { width: 14px; height: 14px; }
  .dashboard-grid { gap: 14px; }
  .column-header { padding: 16px 14px 14px; gap: 12px; }
  .responsive-header { flex-direction: column; align-items: stretch; }
  .header-title-group { justify-content: flex-start; gap: 9px; }
  .column-header h2 { font-size: 12px; letter-spacing: .07em; }
  .mode-toggle.inline { width: 100%; }
  .toggle-btn { flex: 1 1 50%; min-width: 0; padding: 10px 12px; text-align: center; }
  .form-embedded { padding: 0 14px 14px; }
  .form-scroll-area { padding: 0 14px 18px; }
  .field-grid { grid-template-columns: minmax(0, 1fr); gap: 14px; }
  .field.full-width { grid-column: 1 / -1; }
  .section-title.margin-top { margin-top: 26px; }
  .need-row { flex-wrap: wrap; gap: 10px; }
  .flex-grow { flex: 1 1 100%; }
  .qty-field { flex: 1 1 calc(100% - 50px); width: auto; }
  .btn-remove-row { flex: 0 0 40px; }
  .btn-add-row { width: 100%; text-align: center; }
  .panel-bottom-action { padding: 14px; }
  .submit-button { width: 100%; text-align: center; }
  .info-banner { margin: 0 14px 14px; padding: 12px; }
  .events-list { padding: 0 14px 16px; gap: 12px; }
  .event-card { padding: 14px; }
  .event-details p { gap: 8px; }
  .overlay { place-items: start center; padding: 8px; }
  .auth-card, .view-modal { width: 100%; max-height: calc(100dvh - 16px); padding: 26px 16px 20px; }
  .close-button { top: 8px; right: 8px; }
  .auth-card h2 { padding-right: 26px; }
  .view-grid p { grid-template-columns: 82px minmax(0, 1fr); gap: 10px; font-size: 12px; }
  .view-needs li { padding: 10px 12px; }
  .toast-container { top: 10px; width: calc(100vw - 20px); }
  .toast { padding: 11px 14px; }
}

@media (prefers-reduced-motion: reduce) {
  .spinner, .toast { animation: none; }
  .event-card { transition: none; }
}
</style>