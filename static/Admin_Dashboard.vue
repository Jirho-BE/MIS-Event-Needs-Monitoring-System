<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

// ==========================================
// REACTIVE STATES
// ==========================================
const isLoading = ref(true)

// Data Lists
const allEvents = ref([])
const collegeList = ref([]) 
const departmentList = ref([])
const organizationList = ref([])
const itemList = ref([])
const accountList = ref([]) 

// Junction & Needs Lists
const needsList = ref([])
const eventNeedsList = ref([])

// UI States
const profileDropdownOpen = ref(false)
const profileContainer = ref(null)
const activeModal = ref(null) 
const newUsername = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')

const menuModalOpen = ref(false)
const activeTab = ref('Events') 
const tabMode = ref('add') 
const selectedItemToEdit = ref('')
const tabsList = ['Events', 'Account', 'Item', 'College', 'Department', 'Organization']

// Event View State
const viewEvent = ref(null)

// Forms
const eventForm = ref({ title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] })
const accountForm = ref({ username: '', firstName: '', lastName: '', organization: '', password: '' })
const itemForm = ref({ name: '' })
const collegeForm = ref({ name: '' })
const departmentForm = ref({ name: '', college: '' })
const orgForm = ref({ name: '', department: '', college: '' })

// ==========================================
// CUSTOM NOTIFICATION & CONFIRM SYSTEM
// ==========================================
const toasts = ref([])
let toastIdCounter = 0

function showToast(message, type = 'success') {
  const id = toastIdCounter++
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3500)
}

const confirmDialog = ref({ open: false, title: '', message: '', onConfirm: null })

function requestConfirm(title, message, onConfirmCallback) {
  confirmDialog.value = { open: true, title, message, onConfirm: onConfirmCallback }
}

function executeConfirm() {
  if (confirmDialog.value.onConfirm) confirmDialog.value.onConfirm()
  confirmDialog.value.open = false
}

function closeConfirm() {
  confirmDialog.value.open = false
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
// DATA FETCHING & COMPUTEDS
// ==========================================
async function fetchAllData() {
  try {
    const [events, colleges, departments, orgs, items, accounts, needs, eventNeeds] = await Promise.all([
      apiFetch('/api/events-list/'),
      apiFetch('/api/college-list/'),
      apiFetch('/api/department-list/'),
      apiFetch('/api/organization-list/'),
      apiFetch('/api/item-list/'),
      apiFetch('/api/account-lists/'),
      apiFetch('/api/needs-list/').catch(() => []), // Added Needs
      apiFetch('/api/event-needs-list/').catch(() => []) // Added Event-Needs Junction
    ])
    allEvents.value = events
    collegeList.value = colleges
    departmentList.value = departments
    organizationList.value = orgs
    itemList.value = items
    accountList.value = accounts
    needsList.value = needs
    eventNeedsList.value = eventNeeds
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

function getTodayDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Sort Logic
const pendingEvents = computed(() => allEvents.value.filter(event => !event.approved))
const ongoingEvents = computed(() => allEvents.value.filter(event => event.approved && event.date === getTodayDate()))
const currentEvents = computed(() => allEvents.value.filter(event => event.approved && event.date !== getTodayDate()))

// Computed: Resolve Item Needs for the View Modal
const viewEventNeeds = computed(() => {
  if (!viewEvent.value) return []
  const eventId = viewEvent.value.id
  
  // Find all junction records linking this event to needs
  const linkedNeeds = eventNeedsList.value.filter(en => en.event_id === eventId)
  
  // Map junction records to actual item names and quantities
  return linkedNeeds.map(en => {
    const needData = needsList.value.find(n => n.id === en.needs_id)
    if (needData) {
      const actualItem = itemList.value.find(i => i.id === needData.item_id)
      return {
        name: actualItem ? actualItem.name : 'Unknown Item',
        quantity: needData.quantity
      }
    }
    return null
  }).filter(Boolean)
})

// Name Mappers
function getOrgName(orgId) {
  const org = organizationList.value.find(o => o.id === orgId)
  return org ? org.name : (orgId || 'N/A')
}

function getOwnerName(ownerId) {
  const acc = accountList.value.find(a => a.id === ownerId)
  return acc ? (acc.username || acc.first_name) : (ownerId || 'N/A')
}

const currentEditList = computed(() => {
  switch (activeTab.value) {
    case 'Events': return allEvents.value
    case 'Account': return accountList.value
    case 'Item': return itemList.value
    case 'College': return collegeList.value
    case 'Department': return departmentList.value
    case 'Organization': return organizationList.value
    default: return []
  }
})

// ==========================================
// WATCHERS & FORM POPULATION
// ==========================================
function resetForms() {
  eventForm.value = { title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] }
  accountForm.value = { username: '', firstName: '', lastName: '', organization: '', password: '' }
  itemForm.value = { name: '' }
  collegeForm.value = { name: '' }
  departmentForm.value = { name: '', college: '' }
  orgForm.value = { name: '', department: '', college: '' }
  selectedItemToEdit.value = ''
}

watch(selectedItemToEdit, (newId) => {
  if (!newId) return
  const item = currentEditList.value.find(i => (i.id || i.username) == newId)
  if (!item) return

  switch (activeTab.value) {
    case 'College': collegeForm.value.name = item.name; break
    case 'Department':
      departmentForm.value.name = item.name
      departmentForm.value.college = item.college_id || item.college || ''
      break
    case 'Organization':
      orgForm.value.name = item.name
      orgForm.value.department = item.dept_id || item.department || ''
      orgForm.value.college = item.college_id || item.college || ''
      break
    case 'Item': itemForm.value.name = item.name; break
    case 'Account':
      accountForm.value.username = item.username
      accountForm.value.firstName = item.first_name
      accountForm.value.lastName = item.last_name
      accountForm.value.organization = item.org_id || item.organization || ''
      accountForm.value.password = '' 
      break
    case 'Events':
      eventForm.value.title = item.title
      eventForm.value.venue = item.venue
      eventForm.value.attendies = item.no_of_attendies
      eventForm.value.date = item.date
      // Catch potential DB spelling "start_tiime"
      eventForm.value.startTime = item.start_tiime || item.start_time
      eventForm.value.endTime = item.end_time
      eventForm.value.organization = item.org_id || item.organization || ''

      // AUTO-FILL NEEDS LOGIC: Link Event -> Event_Needs -> Needs
      const existingLinks = eventNeedsList.value.filter(en => en.event_id === item.id)
      const mappedFormNeeds = existingLinks.map(en => {
        const matchingNeed = needsList.value.find(n => n.id === en.needs_id)
        if (matchingNeed) {
          return { id: matchingNeed.id, item: matchingNeed.item_id, quantity: matchingNeed.quantity }
        }
        return null
      }).filter(Boolean)

      eventForm.value.needs = mappedFormNeeds.length ? mappedFormNeeds : [{ id: null, item: '', quantity: 1 }]
      break
  }
})

// ==========================================
// LIFECYCLE HOOK
// ==========================================
onMounted(async () => {
  document.addEventListener('click', handleProfileOutsideClick)
  const token = localStorage.getItem('access_token')
  if (!token) return window.location.replace('/')

  try {
    await apiFetch('/api/account-lists/')
    isLoading.value = false
    await fetchAllData()
  } catch (error) {
    localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token')
    window.location.replace('/')
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleProfileOutsideClick)
})

// ==========================================
// EVENT VIEW, APPROVAL & REJECTION
// ==========================================
function openViewEvent(eventObj) {
  viewEvent.value = eventObj
}
function closeViewEvent() { viewEvent.value = null }

function approveEvent(eventId, clickEvent) {
  clickEvent.stopPropagation() 
  requestConfirm('Approve Event', 'Are you sure you want to approve this event?', async () => {
    try {
      await apiFetch(`/api/events/edit/${eventId}/`, 'PATCH', { approved: true })
      showToast('Event approved successfully!')
      fetchAllData()
    } catch (err) { showToast(err.message, 'error') }
  })
}

function rejectEvent(eventId, clickEvent) {
  clickEvent.stopPropagation() 
  requestConfirm('Reject Event', 'Are you sure you want to completely reject and delete this event request?', async () => {
    try {
      await apiFetch(`/api/events/delete/${eventId}/`, 'DELETE')
      showToast('Event rejected and deleted.')
      fetchAllData()
    } catch (err) { showToast(err.message, 'error') }
  })
}

// ==========================================
// MENU ACTIONS & CRUD
// ==========================================
function openMenuModal() { menuModalOpen.value = true }
function closeMenuModal() { menuModalOpen.value = false; resetForms() }
function setTab(tab) { resetForms(); activeTab.value = tab; if (tab === 'Account') tabMode.value = 'edit' }
function setTabMode(mode) { resetForms(); tabMode.value = mode }
function addEventNeedRow() { eventForm.value.needs.push({ id: null, item: '', quantity: 1 }) }
function removeEventNeedRow(idx) { if (eventForm.value.needs.length > 1) eventForm.value.needs.splice(idx, 1) }

async function handleTabSubmit() {
  switch (activeTab.value) {
    case 'College': tabMode.value === 'add' ? await addCollege() : await editCollege(); break
    case 'Department': tabMode.value === 'add' ? await addDepartment() : await editDepartment(); break
    case 'Events': tabMode.value === 'add' ? await addEvent() : await editEvent(); break
    case 'Item': tabMode.value === 'add' ? await addItem() : await editItem(); break
    case 'Organization': tabMode.value === 'add' ? await addOrganization() : await editOrganization(); break
    case 'Account': if (tabMode.value === 'edit') await editAccount(); break
  }
}

async function addCollege() {
  if (!collegeForm.value.name.trim()) return showToast('Please enter a college name.', 'error')
  try { await apiFetch('/api/college-create/', 'POST', { name: collegeForm.value.name.trim() }); showToast('College added!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function addDepartment() {
  if (!departmentForm.value.name.trim() || !departmentForm.value.college) return showToast('Fill all fields.', 'error')
  try { await apiFetch('/api/department-create/', 'POST', { name: departmentForm.value.name.trim(), college_id: departmentForm.value.college }); showToast('Department added!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function addOrganization() {
  if (!orgForm.value.name.trim() || !orgForm.value.college || !orgForm.value.department) return showToast('Fill all fields.', 'error')
  try { await apiFetch('/api/organization-create/', 'POST', { name: orgForm.value.name.trim(), dept_id: orgForm.value.department, college_id: orgForm.value.college }); showToast('Organization added!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function addItem() {
  if (!itemForm.value.name.trim()) return showToast('Enter an item name.', 'error')
  try { await apiFetch('/api/item-create/', 'POST', { name: itemForm.value.name.trim() }); showToast('Item added!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function addEvent() {
  const { title, venue, attendies, date, startTime, endTime, organization, needs } = eventForm.value
  if (!title.trim() || !venue.trim() || !String(attendies).trim() || !date || !startTime || !endTime || !organization) return showToast('Fill all event details.', 'error')
  try {
    const createdEvent = await apiFetch('/api/events-create/', 'POST', { title: title.trim(), venue: venue.trim(), no_of_attendies: Number(attendies), date, start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization })
    const eventId = createdEvent.id || createdEvent.event_id
    
    const validNeeds = needs.filter(n => n.item && Number(n.quantity) > 0)
    for (const need of validNeeds) {
      const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
      const needId = createdNeed.id || createdNeed.needs_id
      await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: eventId })
    }
    showToast('Event created successfully!'); resetForms(); fetchAllData(); closeMenuModal()
  } catch (err) { showToast(err.message, 'error') }
}

async function editCollege() {
  if (!selectedItemToEdit.value) return showToast('Select an item to edit.', 'error')
  try { await apiFetch(`/api/college-edit/${selectedItemToEdit.value}/`, 'PUT', { name: collegeForm.value.name.trim() }); showToast('College updated!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function editDepartment() {
  if (!selectedItemToEdit.value) return showToast('Select an item to edit.', 'error')
  try { await apiFetch(`/api/department-edit/${selectedItemToEdit.value}/`, 'PATCH', { name: departmentForm.value.name.trim(), college_id: departmentForm.value.college }); showToast('Department updated!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function editOrganization() {
  if (!selectedItemToEdit.value) return showToast('Select an item to edit.', 'error')
  try { await apiFetch(`/api/organization-edit/${selectedItemToEdit.value}/`, 'PATCH', { name: orgForm.value.name.trim(), dept_id: orgForm.value.department, college_id: orgForm.value.college }); showToast('Organization updated!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function editItem() {
  if (!selectedItemToEdit.value) return showToast('Select an item to edit.', 'error')
  try { await apiFetch(`/api/item-edit/${selectedItemToEdit.value}/`, 'PUT', { name: itemForm.value.name.trim() }); showToast('Item updated!'); resetForms(); fetchAllData(); closeMenuModal() } catch (err) { showToast(err.message, 'error') }
}
async function editAccount() {
  if (!selectedItemToEdit.value) return showToast('Select an account to edit.', 'error')
  try { 
    const payload = { username: accountForm.value.username, first_name: accountForm.value.firstName, last_name: accountForm.value.lastName, org_id: accountForm.value.organization }
    if (accountForm.value.password) payload.password = accountForm.value.password

    await apiFetch(`/api/profile/edit/${selectedItemToEdit.value}/`, 'PUT', payload)
    showToast('Account updated!'); resetForms(); fetchAllData(); closeMenuModal() 
  } catch (err) { showToast(err.message, 'error') }
}
async function editEvent() {
  if (!selectedItemToEdit.value) return showToast('Select an event to edit.', 'error')
  const { title, venue, attendies, date, startTime, endTime, organization, needs } = eventForm.value
  
  try { 
    // 1. Update Core Event
    await apiFetch(`/api/events/edit/${selectedItemToEdit.value}/`, 'PATCH', { title, venue, no_of_attendies: attendies, date, start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization })
    
    // 2. Process Needs Map
    const validNeeds = needs.filter(n => n.item && Number(n.quantity) > 0)
    for (const need of validNeeds) {
      if (need.id) {
        // Update existing need
        await apiFetch(`/api/needs/edit/${need.id}/`, 'PATCH', { item_id: need.item, quantity: Number(need.quantity) })
      } else {
        // Create newly added need and link via event_needs
        const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
        const needId = createdNeed.id || createdNeed.needs_id
        await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: selectedItemToEdit.value })
      }
    }

    showToast('Event and needs updated!'); resetForms(); fetchAllData(); closeMenuModal() 
  } catch (err) { showToast(err.message, 'error') }
}

function handleDeleteItem() {
  if (!selectedItemToEdit.value) return
  requestConfirm('Delete Item', `Are you sure you want to delete this ${activeTab.value}? This action cannot be undone.`, async () => {
    try {
      let endpoint = ''
      switch(activeTab.value) {
        case 'College': endpoint = `/api/college-delete/${selectedItemToEdit.value}/`; break
        case 'Department': endpoint = `/api/department-delete/${selectedItemToEdit.value}/`; break
        case 'Organization': endpoint = `/api/organization-delete/${selectedItemToEdit.value}/`; break
        case 'Item': endpoint = `/api/item-delete/${selectedItemToEdit.value}/`; break
        case 'Events': endpoint = `/api/events/delete/${selectedItemToEdit.value}/`; break
        case 'Account': endpoint = `/api/profile/delete/${selectedItemToEdit.value}/`; break
      }
      if(endpoint) {
        await apiFetch(endpoint, 'DELETE')
        showToast(`${activeTab.value} deleted.`)
        resetForms(); fetchAllData(); closeMenuModal()
      }
    } catch (err) { showToast(err.message, 'error') }
  })
}

function toggleProfileDropdown() { profileDropdownOpen.value = !profileDropdownOpen.value }
function handleProfileOutsideClick(event) {
  if (profileDropdownOpen.value && profileContainer.value && !profileContainer.value.contains(event.target)) {
    profileDropdownOpen.value = false
  }
}
function openModal(modalName) { activeModal.value = modalName; profileDropdownOpen.value = false }
function closeModal() { activeModal.value = null; newUsername.value = ''; newPassword.value = ''; confirmNewPassword.value = '' }
function logout() { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); window.location.replace('/') }
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

    <!-- GLOBAL CONFIRM MODAL -->
    <div v-if="confirmDialog.open" class="overlay" style="z-index: 1000;">
      <section class="auth-card confirm-modal">
        <h2>[[ confirmDialog.title ]]</h2>
        <p>[[ confirmDialog.message ]]</p>
        <div class="confirm-actions">
          <button class="btn-action" @click="closeConfirm">Cancel</button>
          <button class="btn-action approve" @click="executeConfirm">Confirm</button>
        </div>
      </section>
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
          <p><span>OWNER:</span> [[ getOwnerName(viewEvent.owner) ]]</p>
        </div>

        <!-- RESOLVED NEEDS FROM JUNCTION TABLE -->
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
      <div class="brand"><span class="brand-icon">M</span><span>MIS <span class="muted">DASHBOARD</span></span></div>
      <div class="profile-container" ref="profileContainer">
        <button class="profile-circle" @click="toggleProfileDropdown">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </button>
        <div v-if="profileDropdownOpen" class="dropdown-menu">
          <div class="dropdown-header"><span>ADMINISTRATOR</span></div>
          <button class="dropdown-item" @click="openModal('username')">Change Username</button>
          <button class="dropdown-item" @click="openModal('password')">Change Password</button>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item danger" @click="logout">Log Out</button>
        </div>
      </div>
    </header>

    <!-- DASHBOARD CONTENT (SCROLLABLE COLUMNS) -->
    <section class="dashboard-grid">
      
      <!-- 01. CURRENT EVENTS -->
      <div class="dashboard-column">
        <div class="column-header"><span class="column-index">01</span><h2>CURRENT EVENTS</h2><span class="count">[[ currentEvents.length ]]</span></div>
        <div class="events-list">
          <div v-for="event in currentEvents" :key="event.id" class="event-card clickable" @click="openViewEvent(event)">
            <h3 class="event-title">[[ event.title ]]</h3>
            <div class="event-details">
              <p><span>DATE:</span> [[ event.date ]]</p>
              <p><span>VENUE:</span> [[ event.venue ]]</p>
              <p><span>TIME:</span> [[ event.start_time || event.start_tiime ]] - [[ event.end_time ]]</p>
              <p><span>ATTENDEES:</span> [[ event.no_of_attendies ]]</p>
              <p><span>ORG:</span> [[ getOrgName(event.org_id || event.organization) ]]</p>
              <p><span>OWNER:</span> [[ getOwnerName(event.owner) ]]</p>
            </div>
          </div>
          <div v-if="currentEvents.length === 0" class="empty-state">No current events.</div>
        </div>
      </div>

      <!-- 02. ONGOING EVENTS -->
      <div class="dashboard-column">
        <div class="column-header"><span class="column-index">02</span><h2>ONGOING EVENTS</h2><span class="count">[[ ongoingEvents.length ]]</span></div>
        <div class="events-list">
          <div v-for="event in ongoingEvents" :key="event.id" class="event-card clickable" @click="openViewEvent(event)">
            <h3 class="event-title">[[ event.title ]]</h3>
            <div class="event-details">
              <p><span>VENUE:</span> [[ event.venue ]]</p>
              <p><span>TIME:</span> [[ event.start_time || event.start_tiime ]] - [[ event.end_time ]]</p>
              <p><span>ATTENDEES:</span> [[ event.no_of_attendies ]]</p>
              <p><span>ORG:</span> [[ getOrgName(event.org_id || event.organization) ]]</p>
              <p><span>OWNER:</span> [[ getOwnerName(event.owner) ]]</p>
            </div>
          </div>
          <div v-if="ongoingEvents.length === 0" class="empty-state">No ongoing events.</div>
        </div>
      </div>

      <!-- 03. PENDING APPROVAL -->
      <div class="dashboard-column">
        <div class="column-header"><span class="column-index">03</span><h2>PENDING APPROVAL</h2><span class="count">[[ pendingEvents.length ]]</span></div>
        <div class="events-list">
          <div v-for="event in pendingEvents" :key="event.id" class="event-card pending-card clickable" @click="openViewEvent(event)">
            <h3 class="event-title">[[ event.title ]]</h3>
            <div class="event-details">
              <p><span>DATE:</span> [[ event.date ]]</p>
              <p><span>VENUE:</span> [[ event.venue ]]</p>
              <p><span>TIME:</span> [[ event.start_time || event.start_tiime ]] - [[ event.end_time ]]</p>
              <p><span>ATTENDEES:</span> [[ event.no_of_attendies ]]</p>
              <p><span>ORG:</span> [[ getOrgName(event.org_id || event.organization) ]]</p>
              <p><span>OWNER:</span> [[ getOwnerName(event.owner) ]]</p>
            </div>
            <div class="card-actions">
              <button class="btn-action approve" @click="approveEvent(event.id, $event)">Approve</button>
              <button class="btn-action reject" @click="rejectEvent(event.id, $event)">Reject</button>
            </div>
          </div>
          <div v-if="pendingEvents.length === 0" class="empty-state">No pending requests.</div>
        </div>
      </div>
    </section>

    <!-- FAB BUTTON -->
    <button class="fab-menu" @click="openMenuModal">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
    </button>

    <!-- MANAGEMENT POPUP -->
    <div v-if="menuModalOpen" class="overlay" @click.self="closeMenuModal" @keydown.esc="closeMenuModal">
      <div class="menu-modal-container">
        <header class="menu-modal-header">
          <div class="card-brand"><span class="brand-icon small">M</span><span>SYSTEM MANAGEMENT</span></div>
          <button class="close-button" @click="closeMenuModal">×</button>
        </header>

        <div class="menu-modal-body">
          <aside class="tab-sidebar">
            <button v-for="tab in tabsList" :key="tab" class="tab-btn" :class="{ active: activeTab === tab }" @click="setTab(tab)">[[ tab ]]</button>
          </aside>

          <section class="tab-content-panel">
            <div class="panel-top-controls">
              <div class="mode-toggle">
                <button v-if="activeTab !== 'Account'" class="toggle-btn" :class="{ active: tabMode === 'add' }" @click="setTabMode('add')">ADD</button>
                <button class="toggle-btn" :class="{ active: tabMode === 'edit' }" @click="setTabMode('edit')">EDIT</button>
              </div>
              <button v-if="tabMode === 'edit'" class="btn-delete" @click="handleDeleteItem" :disabled="!selectedItemToEdit">DELETE [[ activeTab.toUpperCase() ]]</button>
            </div>

            <!-- DYNAMIC EDIT SELECTOR -->
            <div v-if="tabMode === 'edit'" class="edit-selector-container">
              <label class="field">
                <span>Select [[ activeTab ]] to Edit</span>
                <select v-model="selectedItemToEdit">
                  <option value="" disabled>-- Select existing [[ activeTab ]] --</option>
                  <option v-for="opt in currentEditList" :key="opt.id || opt.username" :value="opt.id || opt.username">
                    [[ opt.name || opt.title || opt.username ]]
                  </option>
                </select>
              </label>
            </div>

            <div class="form-scroll-area">
              <!-- 1. EVENTS -->
              <div v-if="activeTab === 'Events'" class="tab-form">
                <h3 class="section-title">01. EVENT DETAILS</h3>
                <div class="field-grid">
                  <label class="field"><span>Title</span><input v-model="eventForm.title" placeholder="Event Title" /></label>
                  <label class="field"><span>Venue</span><input v-model="eventForm.venue" placeholder="Venue Name" /></label>
                  <label class="field"><span>Attendees</span><input type="number" v-model="eventForm.attendies" /></label>
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

              <!-- 2. ACCOUNT -->
              <div v-if="activeTab === 'Account'" class="tab-form">
                <div class="field-grid">
                  <label class="field"><span>Username</span><input v-model="accountForm.username" readonly /></label>
                  <label class="field"><span>Password</span><input type="password" v-model="accountForm.password" placeholder="Leave blank to keep current password" /></label>
                  <label class="field"><span>First Name</span><input v-model="accountForm.firstName" /></label>
                  <label class="field"><span>Last Name</span><input v-model="accountForm.lastName" /></label>
                  <label class="field full-width">
                    <span>Organization</span>
                    <select v-model="accountForm.organization">
                      <option value="" disabled>Select Organization</option>
                      <option v-for="org in organizationList" :key="org.id" :value="org.id">[[ org.name ]]</option>
                    </select>
                  </label>
                </div>
              </div>

              <!-- 3. ITEM -->
              <div v-if="activeTab === 'Item'" class="tab-form"><label class="field"><span>Item Name</span><input v-model="itemForm.name" /></label></div>

              <!-- 4. COLLEGE -->
              <div v-if="activeTab === 'College'" class="tab-form"><label class="field"><span>College Name</span><input v-model="collegeForm.name" /></label></div>

              <!-- 5. DEPARTMENT -->
              <div v-if="activeTab === 'Department'" class="tab-form">
                <div class="field-grid">
                  <label class="field"><span>Department Name</span><input v-model="departmentForm.name" /></label>
                  <label class="field">
                    <span>College</span>
                    <select v-model="departmentForm.college">
                      <option value="" disabled>Select College</option>
                      <option v-for="col in collegeList" :key="col.id" :value="col.id">[[ col.name ]]</option>
                    </select>
                  </label>
                </div>
              </div>

              <!-- 6. ORGANIZATION -->
              <div v-if="activeTab === 'Organization'" class="tab-form">
                <div class="field-grid">
                  <label class="field full-width"><span>Organization Name</span><input v-model="orgForm.name" /></label>
                  <label class="field">
                    <span>Department</span>
                    <select v-model="orgForm.department">
                      <option value="" disabled>Select Department</option>
                      <option v-for="dep in departmentList" :key="dep.id" :value="dep.id">[[ dep.name ]]</option>
                    </select>
                  </label>
                  <label class="field">
                    <span>College</span>
                    <select v-model="orgForm.college">
                      <option value="" disabled>Select College</option>
                      <option v-for="col in collegeList" :key="col.id" :value="col.id">[[ col.name ]]</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>

            <footer class="panel-bottom-action">
              <button class="submit-button action-btn" @click="handleTabSubmit">
                [[ tabMode === 'add' ? 'ADD ' + activeTab.toUpperCase() : 'SAVE CHANGES' ]] <span>↗</span>
              </button>
            </footer>

          </section>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) { background: #101010; min-width: 320px; margin: 0; }

.loader-screen { height: 100vh; background: #101010; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #929292; font-family: Inter, sans-serif; font-size: 11px; letter-spacing: 0.1em; }
.spinner { width: 24px; height: 24px; border: 2px solid #333; border-top-color: #f5f5f5; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* PAGE CONSTRAINT */
.dashboard-page {
  --bg: #101010; --surface: #141414; --white: #f5f5f5; --muted: #929292; --line: #333333;
  height: 100vh; overflow: hidden;
  display: flex; flex-direction: column;
  padding: 28px clamp(20px, 5vw, 76px) 20px;
  background: var(--bg); color: var(--white); font-family: Inter, sans-serif; position: relative;
}

/* TOPBAR */
.topbar { display: flex; align-items: center; justify-content: space-between; padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 24px; }
.brand { display: inline-flex; align-items: center; gap: 11px; font-size: 12px; font-weight: 750; letter-spacing: .13em; }
.brand-icon { display: grid; width: 30px; height: 30px; place-items: center; border: 1px solid #777; font-size: 15px; font-weight: 800; }
.brand-icon.small { width: 26px; height: 26px; font-size: 12px; }
.muted { color: var(--muted); }

/* PROFILE DROPDOWN */
.profile-container { position: relative; }
.profile-circle { width: 40px; height: 40px; border-radius: 50%; background: var(--surface); border: 1px solid var(--line); color: var(--white); cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 8px; }
.dropdown-menu { position: absolute; top: 50px; right: 0; width: 200px; background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 8px 0; z-index: 20; }
.dropdown-header { padding: 8px 16px 12px; font-size: 9px; font-weight: 700; color: var(--muted); border-bottom: 1px solid var(--line); margin-bottom: 8px; }
.dropdown-item { width: 100%; text-align: left; background: transparent; border: none; padding: 10px 16px; color: var(--white); font-size: 12px; cursor: pointer; }
.dropdown-item:hover { background: #202020; }
.dropdown-item.danger { color: #ff9292; }

/* 3-COLUMN DASHBOARD GRID (SCROLLABLE) */
.dashboard-grid { 
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; 
  flex: 1; height: 100%; min-height: 0;
}
.dashboard-column { 
  display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--line); padding: 20px; 
  height: 100%; overflow: hidden;
}
.column-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
.column-index { color: var(--muted); font-size: 10px; font-weight: 700; }
.column-header h2 { margin: 0; font-size: 14px; font-weight: 650; letter-spacing: .1em; flex: 1; }
.count { background: #333; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }

.events-list { 
  display: flex; flex-direction: column; gap: 16px; 
  flex: 1; overflow-y: auto; padding-right: 4px; 
}
.events-list::-webkit-scrollbar { width: 4px; }
.events-list::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }

.event-card { background: #1a1a1a; border: 1px solid #2a2a2a; padding: 16px; border-radius: 2px; transition: border-color 0.2s, background 0.2s; }
.event-card.clickable { cursor: pointer; }
.event-card.clickable:hover { border-color: #777; background: #202020; }
.pending-card { border-left: 2px solid #a8a8a8; }
.event-title { margin: 0 0 12px 0; font-size: 14px; font-weight: 600; letter-spacing: -.02em; }
.event-details p { margin: 6px 0; font-size: 11px; color: #ccc; display: flex; justify-content: space-between; }
.event-details span { color: var(--muted); font-size: 9px; font-weight: 700; letter-spacing: .08em; }
.empty-state { color: var(--muted); font-size: 11px; text-align: center; padding: 30px 0; }

.card-actions { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px dashed #333; }
.btn-action { flex: 1; padding: 8px; border: 1px solid var(--line); background: transparent; color: var(--white); font-size: 10px; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: .1em; }
.btn-action.approve { background: #fff; color: #000; border-color: #fff; }
.btn-action.approve:hover { background: #d5d5d5; }
.btn-action.reject:hover { background: #3a1515; border-color: #ff9292; color: #ff9292; }

/* FAB */
.fab-menu { position: fixed; bottom: 30px; right: 30px; width: 56px; height: 56px; border-radius: 50%; background: var(--white); color: #111; border: none; box-shadow: 0 4px 20px rgba(0,0,0,0.5); cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10; }
.fab-menu:hover { transform: scale(1.05); }

/* TOASTS & CONFIRM MODAL */
.toast-container { position: fixed; top: 30px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; gap: 10px; z-index: 2000; }
.toast { padding: 12px 24px; border-radius: 4px; font-size: 12px; font-weight: 600; color: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.8); animation: slideDown 0.3s ease; }
.toast.success { background: #1a1a1a; border: 1px solid #4caf50; border-left: 4px solid #4caf50; }
.toast.error { background: #1a1a1a; border: 1px solid #ff5252; border-left: 4px solid #ff5252; }
@keyframes slideDown { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.confirm-modal { text-align: center; }
.confirm-modal p { color: #ccc; font-size: 13px; line-height: 1.5; margin-bottom: 24px; }
.confirm-actions { display: flex; gap: 12px; }

/* OVERLAYS & MODALS */
.overlay { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; padding: 20px; background: #000c; backdrop-filter: blur(5px); }
.auth-card { position: relative; width: min(100%, 430px); padding: clamp(23px, 5vw, 38px); border: 1px solid #373737; background: #141414; }
.close-button { position: absolute; top: 14px; right: 15px; width: 32px; height: 32px; border: 0; background: transparent; color: #aaa; cursor: pointer; font-size: 24px; }
.card-eyebrow { margin: 0 0 10px; font-size: 9px; font-weight: 700; letter-spacing: .15em; color: var(--muted); }
.auth-card h2 { margin: 0 0 25px 0; font-size: clamp(1.6rem, 4vw, 2rem); font-weight: 650; letter-spacing: -.05em; }

/* VIEW EVENT MODAL */
.view-modal { width: min(100%, 550px); }
.view-title { margin-bottom: 24px !important; }
.view-grid { display: grid; gap: 12px; padding-bottom: 16px; border-bottom: 1px dashed var(--line); }
.view-grid p { margin: 0; font-size: 13px; color: #ddd; display: flex; justify-content: space-between; align-items: center; }
.view-grid span { font-size: 10px; font-weight: 700; color: var(--muted); letter-spacing: .1em; }
.view-needs ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.view-needs li { display: flex; justify-content: space-between; background: #1a1a1a; border: 1px solid var(--line); padding: 10px 16px; font-size: 12px; color: #eee; }
.need-qty { font-weight: 700; color: var(--muted); }

/* 80% WINDOW MENU POPUP */
.menu-modal-container { width: 80vw; height: 80vh; max-width: 1200px; max-height: 800px; background: #141414; border: 1px solid #373737; display: flex; flex-direction: column; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
.menu-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--line); background: #101010; }
.menu-modal-body { display: flex; flex: 1; overflow: hidden; }

/* SIDEBAR & TABS */
.tab-sidebar { flex: 0 0 25%; background: #101010; border-right: 1px solid var(--line); display: flex; flex-direction: column; padding: 16px 0; }
.tab-btn { width: 100%; padding: 16px 24px; background: transparent; border: none; border-left: 3px solid transparent; color: var(--muted); font-size: 12px; font-weight: 700; letter-spacing: .1em; text-align: left; cursor: pointer; }
.tab-btn:hover { color: var(--white); background: #171717; }
.tab-btn.active { color: var(--white); background: #171717; border-left-color: var(--white); }

/* TAB CONTENT */
.tab-content-panel { flex: 0 0 75%; display: flex; flex-direction: column; background: #141414; }
.panel-top-controls { display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; border-bottom: 1px solid var(--line); }
.mode-toggle { display: flex; border: 1px solid var(--line); border-radius: 2px; overflow: hidden; }
.toggle-btn { padding: 8px 20px; background: transparent; border: none; color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .1em; cursor: pointer; }
.toggle-btn.active { background: var(--white); color: #111; }
.btn-delete { background: transparent; border: 1px solid #ff9292; color: #ff9292; padding: 8px 16px; font-size: 10px; font-weight: 700; cursor: pointer; }
.btn-delete:hover:not(:disabled) { background: #3a1515; }
.btn-delete:disabled { opacity: 0.3; cursor: not-allowed; border-color: #555; color: #555; }
.edit-selector-container { padding: 16px 30px; background: #101010; border-bottom: 1px solid var(--line); }
.form-scroll-area { flex: 1; padding: 30px; overflow-y: auto; }
.section-title { font-size: 11px; font-weight: 700; letter-spacing: .15em; color: var(--muted); margin: 0 0 16px 0; }
.section-title.margin-top { margin-top: 32px; }

/* FORM FIELDS & DATE VISIBILITY FIX */
.field-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.field.full-width { grid-column: span 2; }
.field > span { color: #d0d0d0; font-size: 11px; font-weight: 600; }
.field input, .field select { width: 100%; padding: 11px 12px; border: 1px solid #383838; background: #101010; color: var(--white); font-size: 12px; outline: none; }
.field input:focus, .field select:focus { border-color: #aaa; }
.field input[readonly] { color: #666; background: #1a1a1a; cursor: not-allowed; }

/* DARK MODE FIX FOR CALENDAR/CLOCK ICONS */
input[type="date"], input[type="time"] { color-scheme: dark; }
input[type="date"]::-webkit-calendar-picker-indicator, input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(1); cursor: pointer; }

/* NEEDS */
.needs-list { display: flex; flex-direction: column; gap: 12px; }
.need-row { display: flex; gap: 12px; align-items: flex-end; }
.flex-grow { flex: 1; }
.qty-field { width: 100px; }
.btn-remove-row { height: 40px; width: 40px; background: transparent; border: 1px solid #383838; color: #ff9292; cursor: pointer; }
.btn-add-row { align-self: flex-start; background: transparent; border: 1px dashed #555; color: var(--white); padding: 10px 16px; font-size: 11px; font-weight: 600; cursor: pointer; margin-top: 8px; }

.panel-bottom-action { padding: 20px 30px; border-top: 1px solid var(--line); background: #101010; display: flex; justify-content: flex-end; }
.submit-button { display: flex; min-height: 45px; align-items: center; justify-content: space-between; gap: 12px; padding: 0 15px; border: 1px solid #f1f1f1; background: #f1f1f1; color: #111; font-weight: 750; font-size: 12px; cursor: pointer; }

/* RESPONSIVE LAYOUTS */
@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
  .dashboard-page { overflow: auto; }
  .dashboard-column { min-height: 500px; overflow: hidden; }

  /* Put management tabs above the form on tablet and smaller screens. */
  .menu-modal-container {
    width: 95vw;
    height: 90vh;
    height: 90dvh;
    max-height: none;
    min-width: 0;
    min-height: 0;
  }
  .menu-modal-body {
    flex-direction: column;
    min-height: 0;
  }
  .tab-sidebar {
    flex: 0 0 auto;
    flex-direction: row;
    gap: 4px;
    padding: 8px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: thin;
  }
  .tab-btn {
    flex: 0 0 auto;
    width: auto;
    padding: 12px 16px;
    border-left: 0;
    border-bottom: 3px solid transparent;
    text-align: center;
    white-space: nowrap;
  }
  .tab-btn.active {
    border-left-color: transparent;
    border-bottom-color: var(--white);
  }
  .tab-content-panel {
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
    min-height: 0;
    overflow: hidden;
  }
  .form-scroll-area { min-height: 0; }
  .field-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .field { min-width: 0; }
  .field input, .field select { min-width: 0; max-width: 100%; }
  .field.full-width { grid-column: 1 / -1; }
}

@media (max-width: 640px) {
  .dashboard-page {
    min-height: 100vh;
    min-height: 100dvh;
    height: auto;
    padding: 18px 14px 14px;
  }

  .menu-modal-container {
    width: calc(100vw - 12px);
    height: calc(100vh - 12px);
    height: calc(100dvh - 12px);
    max-width: none;
    max-height: none;
  }
  .menu-modal-header { padding: 12px 16px; }
  .menu-modal-body { flex: 1 1 auto; min-height: 0; }
  .tab-sidebar { padding: 6px; gap: 2px; }
  .tab-btn { padding: 11px 12px; font-size: 10px; letter-spacing: .06em; }

  .panel-top-controls {
    flex-wrap: wrap;
    gap: 10px;
    padding: 12px 14px;
  }
  .mode-toggle { max-width: 100%; }
  .toggle-btn { padding: 8px 12px; }
  .btn-delete { max-width: 100%; padding: 8px 10px; }
  .edit-selector-container { padding: 12px 14px; }
  .form-scroll-area { padding: 16px 14px; }
  .field-grid { grid-template-columns: minmax(0, 1fr); gap: 14px; }
  .field.full-width { grid-column: 1 / -1; }
  .field input, .field select { width: 100%; min-width: 0; font-size: 13px; }

  .need-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 68px 36px;
    align-items: end;
    gap: 8px;
  }
  .flex-grow { min-width: 0; }
  .qty-field { width: auto; min-width: 0; }
  .btn-remove-row { width: 36px; }

  .panel-bottom-action { padding: 12px 14px; }
  .submit-button { width: 100%; }
  .overlay { padding: 6px; }
}
</style>