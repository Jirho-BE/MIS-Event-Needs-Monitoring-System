<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

// User dashboard states
const isLoading = ref(true)
const allEvents = ref([])
const organizationList = ref([])
const itemList = ref([])
const accountList = ref([])
const needsList = ref([])
const eventNeedsList = ref([])

const authIdentity = ref({ id: null, username: '' })
const currentAccount = ref(null)
const selectedEventDate = ref(getTodayDate())

const profileDropdownOpen = ref(false)
const profileContainer = ref(null)
const profileForm = ref({ username: '', firstName: '', lastName: '', organization: '', password: '' })
const profileSaving = ref(false)

const menuModalOpen = ref(false)
const tabMode = ref('add')
const selectedItemToEdit = ref('')
const tabsList = ['Events']
const eventForm = ref({ title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] })
const viewEvent = ref(null)

const toasts = ref([])
let toastIdCounter = 0
const confirmDialog = ref({ open: false, title: '', message: '', onConfirm: null })

function getTodayDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function showToast(message, type = 'success') {
  const id = toastIdCounter++
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 3500)
}

function requestConfirm(title, message, onConfirmCallback) {
  confirmDialog.value = { open: true, title, message, onConfirm: onConfirmCallback }
}
function executeConfirm() {
  const callback = confirmDialog.value.onConfirm
  confirmDialog.value.open = false
  if (callback) callback()
}
function closeConfirm() { confirmDialog.value.open = false }

async function apiFetch(endpoint, method = 'GET', payload = null) {
  const token = localStorage.getItem('access_token')
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', Accept: 'application/json' }
  const config = { method, headers }
  if (payload !== null) config.body = JSON.stringify(payload)
  const response = await fetch(endpoint, config)
  if (method === 'DELETE' && response.ok) return { success: true }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const firstKey = Object.keys(data)[0]
    const errorMsg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey] || response.statusText
    const error = new Error(errorMsg || `HTTP ${response.status}`)
    error.status = response.status
    throw error
  }
  return data
}

function asList(value) {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.results)) return value.results
  if (Array.isArray(value?.data)) return value.data
  return []
}

function readAuthIdentity() {
  const token = localStorage.getItem('access_token')
  const identity = { id: localStorage.getItem('account_id') || localStorage.getItem('user_id') || null, username: localStorage.getItem('username') || localStorage.getItem('account_username') || '' }
  if (!token) return identity
  try {
    const tokenPart = token.split('.')[1]
    if (!tokenPart) return identity
    const base64 = tokenPart.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')))
    identity.id = payload.account_id ?? payload.user_id ?? payload.id ?? payload.pk ?? identity.id
    identity.username = payload.username ?? payload.user?.username ?? identity.username
  } catch (error) {
    // Some authentication systems use opaque tokens; use locally stored identity fields when available.
  }
  return identity
}

function resolveCurrentAccount(accounts) {
  const identity = authIdentity.value
  if (identity.id !== null && identity.id !== undefined && identity.id !== '') {
    const byId = accounts.find(account => String(account.id ?? account.pk) === String(identity.id))
    if (byId) return byId
  }
  if (identity.username) {
    const byUsername = accounts.find(account => String(account.username || '').toLowerCase() === String(identity.username).toLowerCase())
    if (byUsername) return byUsername
  }
  return null
}

function ownerReference(value) {
  if (value && typeof value === 'object') {
    return {
      id: value.id ?? value.pk ?? value.user_id ?? value.account_id ?? null,
      username: value.username ?? value.user?.username ?? ''
    }
  }
  return { id: value ?? null, username: '' }
}

function isCurrentUsersEvent(event) {
  const owner = ownerReference(event.owner ?? event.owner_id ?? event.user_id)
  const accountId = currentAccount.value?.id ?? currentAccount.value?.pk ?? authIdentity.value.id
  const username = currentAccount.value?.username || authIdentity.value.username
  if (accountId !== null && accountId !== undefined && accountId !== '' && owner.id !== null && owner.id !== undefined) {
    return String(owner.id) === String(accountId)
  }
  if (username && owner.username) return String(owner.username).toLowerCase() === String(username).toLowerCase()
  // Do not expose events as editable when ownership could not be resolved.
  return false
}

const myEvents = computed(() => allEvents.value.filter(isCurrentUsersEvent).sort((a, b) => {
  const dateCompare = String(a.date || '').localeCompare(String(b.date || ''))
  return dateCompare || String(a.start_time || a.start_tiime || '').localeCompare(String(b.start_time || b.start_tiime || ''))
}))

// The selected-date panel shows approved events scheduled for that date.
const selectedDateEvents = computed(() => allEvents.value
  .filter(event => Boolean(event.approved) && String(event.date || '').slice(0, 10) === selectedEventDate.value)
  .sort((a, b) => String(a.start_time || a.start_tiime || '').localeCompare(String(b.start_time || b.start_tiime || ''))))

const viewEventNeeds = computed(() => {
  if (!viewEvent.value) return []
  const eventId = viewEvent.value.id
  const linkedNeeds = eventNeedsList.value.filter(link => String(link.event_id ?? link.event) === String(eventId))
  return linkedNeeds.map(link => {
    const needData = needsList.value.find(need => String(need.id) === String(link.needs_id ?? link.needs))
    if (!needData) return null
    const actualItem = itemList.value.find(item => String(item.id) === String(needData.item_id ?? needData.item))
    return { name: actualItem ? actualItem.name : 'Unknown Item', quantity: needData.quantity }
  }).filter(Boolean)
})

function getOrgName(orgId) {
  const organization = organizationList.value.find(org => String(org.id) === String(orgId?.id ?? orgId))
  return organization ? organization.name : (orgId?.name || orgId || 'N/A')
}
function getOwnerName(ownerId) {
  const owner = ownerReference(ownerId)
  if (owner.username) return owner.username
  const account = accountList.value.find(acc => String(acc.id) === String(owner.id))
  return account ? (account.username || account.first_name) : (owner.id || 'N/A')
}
function sameId(a, b) { return String(a ?? '') === String(b ?? '') }

function hydrateProfileForm() {
  const account = currentAccount.value
  if (!account) return
  profileForm.value = {
    username: account.username || '',
    firstName: account.first_name || account.firstName || '',
    lastName: account.last_name || account.lastName || '',
    organization: account.org_id ?? account.organization?.id ?? account.organization ?? '',
    password: ''
  }
}

function resetEventForm() {
  eventForm.value = { title: '', venue: '', attendies: '', date: '', startTime: '', endTime: '', organization: '', needs: [{ id: null, item: '', quantity: 1 }] }
  selectedItemToEdit.value = ''
}

watch(selectedItemToEdit, (newId) => {
  if (!newId) return
  const item = myEvents.value.find(event => sameId(event.id, newId))
  if (!item) return
  eventForm.value.title = item.title || ''
  eventForm.value.venue = item.venue || ''
  eventForm.value.attendies = item.no_of_attendies ?? item.attendies ?? ''
  eventForm.value.date = String(item.date || '').slice(0, 10)
  eventForm.value.startTime = item.start_tiime || item.start_time || ''
  eventForm.value.endTime = item.end_time || ''
  eventForm.value.organization = item.org_id?.id ?? item.org_id ?? item.organization?.id ?? item.organization ?? ''

  const existingLinks = eventNeedsList.value.filter(link => sameId(link.event_id ?? link.event, item.id))
  const mappedNeeds = existingLinks.map(link => {
    const need = needsList.value.find(entry => sameId(entry.id, link.needs_id ?? link.needs))
    return need ? { id: need.id, item: need.item_id ?? need.item, quantity: need.quantity ?? 1 } : null
  }).filter(Boolean)
  eventForm.value.needs = mappedNeeds.length ? mappedNeeds : [{ id: null, item: '', quantity: 1 }]
})

async function fetchAllData() {
  const [eventsResponse, organizationsResponse, itemsResponse, accountsResponse, needsResponse, eventNeedsResponse] = await Promise.all([
    apiFetch('/api/events-list/'),
    apiFetch('/api/organization-list/'),
    apiFetch('/api/item-list/'),
    apiFetch('/api/account-lists/').catch(() => []),
    apiFetch('/api/needs-list/').catch(() => []),
    apiFetch('/api/event-needs-list/').catch(() => [])
  ])
  allEvents.value = asList(eventsResponse)
  organizationList.value = asList(organizationsResponse)
  itemList.value = asList(itemsResponse)
  accountList.value = asList(accountsResponse)
  needsList.value = asList(needsResponse)
  eventNeedsList.value = asList(eventNeedsResponse)
  currentAccount.value = resolveCurrentAccount(accountList.value)
  if (currentAccount.value) hydrateProfileForm()
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    window.location.replace('/')
    return
  }
  authIdentity.value = readAuthIdentity()
  document.addEventListener('click', handleProfileOutsideClick)
  document.addEventListener('keydown', handleEscapeKey)
  try {
    await fetchAllData()
  } catch (error) {
    console.error('Failed to load user dashboard:', error)
    if (error.status === 401 || error.status === 403) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.replace('/')
      return
    }
    showToast(error.message || 'Unable to load dashboard data.', 'error')
  } finally {
    isLoading.value = false
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleProfileOutsideClick)
  document.removeEventListener('keydown', handleEscapeKey)
})

function handleProfileOutsideClick(event) {
  if (profileDropdownOpen.value && profileContainer.value && !profileContainer.value.contains(event.target)) {
    profileDropdownOpen.value = false
  }
}
function handleEscapeKey(event) {
  if (event.key === 'Escape') {
    profileDropdownOpen.value = false
    if (menuModalOpen.value) closeMenuModal()
    if (viewEvent.value) closeViewEvent()
    if (confirmDialog.value.open) closeConfirm()
  }
}

// Event management popup
function openMenuModal() {
  resetEventForm()
  tabMode.value = 'add'
  menuModalOpen.value = true
}
function closeMenuModal() {
  menuModalOpen.value = false
  resetEventForm()
  tabMode.value = 'add'
}
function setTabMode(mode) {
  resetEventForm()
  tabMode.value = mode
}
function addEventNeedRow() { eventForm.value.needs.push({ id: null, item: '', quantity: 1 }) }
function removeEventNeedRow(index) {
  if (eventForm.value.needs.length > 1) eventForm.value.needs.splice(index, 1)
}
function openViewEvent(event) { viewEvent.value = event }
function closeViewEvent() { viewEvent.value = null }

async function handleEventSubmit() {
  if (tabMode.value === 'add') await addEvent()
  else await editEvent()
}

async function addEvent() {
  const { title, venue, attendies, date, startTime, endTime, organization, needs } = eventForm.value
  if (!title.trim() || !venue.trim() || !String(attendies).trim() || !date || !startTime || !endTime || !organization) {
    return showToast('Fill all event details.', 'error')
  }
  try {
    const createdEvent = await apiFetch('/api/events-create/', 'POST', {
      title: title.trim(), venue: venue.trim(), no_of_attendies: Number(attendies), date,
      start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization
    })
    const eventId = createdEvent.id || createdEvent.event_id
    const validNeeds = needs.filter(need => need.item && Number(need.quantity) > 0)
    for (const need of validNeeds) {
      const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
      const needId = createdNeed.id || createdNeed.needs_id
      await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: eventId })
    }
    showToast('Event created successfully!')
    await fetchAllData()
    closeMenuModal()
  } catch (error) {
    showToast(error.message || 'Unable to create event.', 'error')
  }
}

async function editEvent() {
  if (!selectedItemToEdit.value) return showToast('Select one of your events to edit.', 'error')
  const ownedEvent = myEvents.value.find(event => sameId(event.id, selectedItemToEdit.value))
  if (!ownedEvent) return showToast('You can only edit events you created.', 'error')
  const { title, venue, attendies, date, startTime, endTime, organization, needs } = eventForm.value
  if (!title.trim() || !venue.trim() || !String(attendies).trim() || !date || !startTime || !endTime || !organization) {
    return showToast('Fill all event details.', 'error')
  }
  try {
    await apiFetch(`/api/events/edit/${selectedItemToEdit.value}/`, 'PATCH', {
      title: title.trim(), venue: venue.trim(), no_of_attendies: Number(attendies), date,
      start_time: startTime, start_tiime: startTime, end_time: endTime, org_id: organization
    })
    const validNeeds = needs.filter(need => need.item && Number(need.quantity) > 0)
    for (const need of validNeeds) {
      if (need.id) {
        await apiFetch(`/api/needs/edit/${need.id}/`, 'PATCH', { item_id: need.item, quantity: Number(need.quantity) })
      } else {
        const createdNeed = await apiFetch('/api/needs-create/', 'POST', { item_id: need.item, quantity: Number(need.quantity) })
        const needId = createdNeed.id || createdNeed.needs_id
        await apiFetch('/api/event-needs-create/', 'POST', { needs_id: needId, event_id: selectedItemToEdit.value })
      }
    }
    showToast('Event and needs updated!')
    await fetchAllData()
    closeMenuModal()
  } catch (error) {
    showToast(error.message || 'Unable to update event.', 'error')
  }
}

function deleteMyEvent() {
  if (!selectedItemToEdit.value) return
  const ownedEvent = myEvents.value.find(event => sameId(event.id, selectedItemToEdit.value))
  if (!ownedEvent) return showToast('You can only delete events you created.', 'error')
  requestConfirm('Delete Event', 'Are you sure you want to delete this event? This action cannot be undone.', async () => {
    try {
      await apiFetch(`/api/events/delete/${selectedItemToEdit.value}/`, 'DELETE')
      showToast('Event deleted.')
      await fetchAllData()
      closeMenuModal()
    } catch (error) {
      showToast(error.message || 'Unable to delete event.', 'error')
    }
  })
}

function toggleProfileDropdown() {
  profileDropdownOpen.value = !profileDropdownOpen.value
  if (profileDropdownOpen.value) {
    if (currentAccount.value) hydrateProfileForm()
    else showToast('Your account details could not be identified. Please check the account-list API and token identity.', 'error')
  }
}

async function saveProfile() {
  const accountId = currentAccount.value?.id ?? currentAccount.value?.pk ?? null
  if (accountId === null || accountId === undefined || accountId === '') {
    return showToast('Unable to identify your account. Profile changes were not saved.', 'error')
  }
  profileSaving.value = true
  const payload = {
    username: profileForm.value.username,
    first_name: profileForm.value.firstName,
    last_name: profileForm.value.lastName,
    org_id: profileForm.value.organization
  }
  if (profileForm.value.password) payload.password = profileForm.value.password
  try {
    await apiFetch(`/api/profile/edit/${accountId}/`, 'PUT', payload)
    showToast('Profile updated successfully!')
    profileForm.value.password = ''
    await fetchAllData()
  } catch (error) {
    showToast(error.message || 'Unable to update profile.', 'error')
  } finally {
    profileSaving.value = false
  }
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.replace('/')
}
</script>

<template>
  <div v-if="isLoading" class="loader-screen">
    <div class="spinner"></div><p>VERIFYING ACCESS...</p>
  </div>

  <main v-else class="dashboard-page user-dashboard-page">
    <!-- Notifications -->
    <div class="toast-container">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">[[ toast.message ]]</div>
    </div>

    <!-- Confirm dialog -->
    <div v-if="confirmDialog.open" class="overlay confirm-overlay" @click.self="closeConfirm">
      <section class="auth-card confirm-modal">
        <h2>[[ confirmDialog.title ]]</h2>
        <p>[[ confirmDialog.message ]]</p>
        <div class="confirm-actions">
          <button class="btn-action" @click="closeConfirm">Cancel</button>
          <button class="btn-action approve" @click="executeConfirm">Confirm</button>
        </div>
      </section>
    </div>

    <!-- Event details -->
    <div v-if="viewEvent" class="overlay" @click.self="closeViewEvent">
      <section class="auth-card view-modal">
        <button class="close-button" aria-label="Close event details" @click="closeViewEvent">×</button>
        <p class="card-eyebrow">EVENT INFORMATION</p>
        <h2 class="view-title">[[ viewEvent.title ]]</h2>
        <div class="view-grid">
          <p><span>STATUS:</span><strong>[[ viewEvent.approved ? 'Approved' : 'Pending Approval' ]]</strong></p>
          <p><span>DATE:</span><strong>[[ viewEvent.date || 'N/A' ]]</strong></p>
          <p><span>VENUE:</span><strong>[[ viewEvent.venue || 'N/A' ]]</strong></p>
          <p><span>TIME:</span><strong>[[ viewEvent.start_time || viewEvent.start_tiime || 'N/A' ]] – [[ viewEvent.end_time || 'N/A' ]]</strong></p>
          <p><span>ATTENDEES:</span><strong>[[ viewEvent.no_of_attendies ?? 'N/A' ]]</strong></p>
          <p><span>ORGANIZATION:</span><strong>[[ getOrgName(viewEvent.org_id || viewEvent.organization) ]]</strong></p>
          <p><span>OWNER:</span><strong>[[ getOwnerName(viewEvent.owner) ]]</strong></p>
        </div>
        <div v-if="viewEventNeeds.length > 0" class="view-needs">
          <p class="card-eyebrow needs-heading">REQUESTED ITEMS</p>
          <ul><li v-for="(need, index) in viewEventNeeds" :key="index"><span>[[ need.name ]]</span><strong>x[[ need.quantity ]]</strong></li></ul>
        </div>
      </section>
    </div>

    <!-- Top navigation -->
    <header class="topbar">
      <div class="brand"><span class="brand-icon">M</span><span>MIS <span class="muted">DASHBOARD</span></span></div>
      <div ref="profileContainer" class="profile-container">
        <button class="profile-circle" aria-label="Open profile menu" :aria-expanded="profileDropdownOpen" @click="toggleProfileDropdown">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </button>
        <div v-if="profileDropdownOpen" class="profile-popover" @click.stop>
          <div class="profile-popover-header">
            <div><p class="card-eyebrow">ACCOUNT SETTINGS</p><h2>MY PROFILE</h2></div>
            <button class="popover-close" aria-label="Close profile menu" @click="profileDropdownOpen = false">×</button>
          </div>
          <div v-if="currentAccount" class="profile-form">
            <label class="field"><span>Username</span><input v-model="profileForm.username" readonly /></label>
            <label class="field"><span>Password</span><input v-model="profileForm.password" type="password" placeholder="Leave blank to keep current password" autocomplete="new-password" /></label>
            <div class="field-grid">
              <label class="field"><span>First Name</span><input v-model="profileForm.firstName" /></label>
              <label class="field"><span>Last Name</span><input v-model="profileForm.lastName" /></label>
            </div>
            <label class="field"><span>Organization</span>
              <select v-model="profileForm.organization">
                <option value="">Select Organization</option>
                <option v-for="organization in organizationList" :key="organization.id" :value="organization.id">[[ organization.name ]]</option>
              </select>
            </label>
            <button class="submit-button profile-save" :disabled="profileSaving" @click="saveProfile">[[ profileSaving ? 'SAVING…' : 'SAVE PROFILE' ]] <span>↗</span></button>
          </div>
          <p v-else class="profile-unavailable">Your account information could not be loaded. Contact the system administrator if this continues.</p>
          <div class="profile-popover-footer"><button class="logout-button" @click="logout">LOG OUT <span>↗</span></button></div>
        </div>
      </div>
    </header>

    <!-- Two-panel user dashboard -->
    <section class="dashboard-grid user-dashboard-grid">
      <div class="dashboard-column">
        <div class="column-header"><span class="column-index">01</span><h2>MY EVENTS</h2><span class="count">[[ myEvents.length ]]</span></div>
        <div class="column-intro">
          <p>Events created by your account.</p>
          <button class="manage-events-button" @click="openMenuModal">MANAGE EVENTS <span>↗</span></button>
        </div>
        <div class="events-list">
          <div v-for="event in myEvents" :key="event.id" class="event-card clickable" @click="openViewEvent(event)">
            <div class="event-card-heading"><h3 class="event-title">[[ event.title ]]</h3><span class="status-pill" :class="event.approved ? 'approved-status' : 'pending-status'">[[ event.approved ? 'APPROVED' : 'PENDING' ]]</span></div>
            <div class="event-details">
              <p><span>DATE:</span><strong>[[ event.date || 'N/A' ]]</strong></p>
              <p><span>VENUE:</span><strong>[[ event.venue || 'N/A' ]]</strong></p>
              <p><span>TIME:</span><strong>[[ event.start_time || event.start_tiime || 'N/A' ]] – [[ event.end_time || 'N/A' ]]</strong></p>
              <p><span>ATTENDEES:</span><strong>[[ event.no_of_attendies ?? 'N/A' ]]</strong></p>
              <p><span>ORGANIZATION:</span><strong>[[ getOrgName(event.org_id || event.organization) ]]</strong></p>
            </div>
          </div>
          <div v-if="myEvents.length === 0" class="empty-state">No events were found for your account. Use Manage Events to create one.</div>
        </div>
      </div>

      <div class="dashboard-column">
        <div class="column-header date-column-header"><span class="column-index">02</span><h2>ONGOING EVENTS</h2><span class="count">[[ selectedDateEvents.length ]]</span></div>
        <div class="date-filter-row">
          <label class="date-filter"><span>VIEW EVENTS FOR</span><input v-model="selectedEventDate" type="date" /></label>
          <p>Approved events scheduled for the selected date.</p>
        </div>
        <div class="events-list">
          <div v-for="event in selectedDateEvents" :key="event.id" class="event-card clickable" @click="openViewEvent(event)">
            <h3 class="event-title">[[ event.title ]]</h3>
            <div class="event-details">
              <p><span>DATE:</span><strong>[[ event.date || 'N/A' ]]</strong></p>
              <p><span>VENUE:</span><strong>[[ event.venue || 'N/A' ]]</strong></p>
              <p><span>TIME:</span><strong>[[ event.start_time || event.start_tiime || 'N/A' ]] – [[ event.end_time || 'N/A' ]]</strong></p>
              <p><span>ATTENDEES:</span><strong>[[ event.no_of_attendies ?? 'N/A' ]]</strong></p>
              <p><span>ORGANIZATION:</span><strong>[[ getOrgName(event.org_id || event.organization) ]]</strong></p>
              <p><span>OWNER:</span><strong>[[ getOwnerName(event.owner) ]]</strong></p>
            </div>
          </div>
          <div v-if="selectedDateEvents.length === 0" class="empty-state">No approved events are scheduled for [[ selectedEventDate || 'this date' ]].</div>
        </div>
      </div>
    </section>

    <!-- Floating shortcut to the event management menu -->
    <button class="fab-menu" aria-label="Manage events" @click="openMenuModal">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
    </button>

    <!-- Event management popup -->
    <div v-if="menuModalOpen" class="overlay management-overlay" @click.self="closeMenuModal">
      <div class="menu-modal-container">
        <header class="menu-modal-header">
          <div class="card-brand"><span class="brand-icon small">M</span><span>EVENT MANAGEMENT</span></div>
          <button class="close-button" aria-label="Close event management" @click="closeMenuModal">×</button>
        </header>
        <div class="menu-modal-body">
          <aside class="tab-sidebar"><button v-for="tab in tabsList" :key="tab" class="tab-btn active">[[ tab ]]</button></aside>
          <section class="tab-content-panel">
            <div class="panel-top-controls">
              <div class="mode-toggle">
                <button class="toggle-btn" :class="{ active: tabMode === 'add' }" @click="setTabMode('add')">ADD</button>
                <button class="toggle-btn" :class="{ active: tabMode === 'edit' }" @click="setTabMode('edit')">EDIT</button>
              </div>
              <button v-if="tabMode === 'edit'" class="btn-delete" :disabled="!selectedItemToEdit" @click="deleteMyEvent">DELETE EVENT</button>
            </div>
            <div v-if="tabMode === 'edit'" class="edit-selector-container">
              <label class="field"><span>Select one of your events to edit</span>
                <select v-model="selectedItemToEdit">
                  <option value="" disabled>-- Select your event --</option>
                  <option v-for="event in myEvents" :key="event.id" :value="event.id">[[ event.title ]] — [[ event.date || 'No date' ]]</option>
                </select>
              </label>
              <p v-if="myEvents.length === 0" class="selector-note">You have no events available to edit.</p>
            </div>
            <div class="form-scroll-area">
              <div class="tab-form">
                <h3 class="section-title">01. EVENT DETAILS</h3>
                <div class="field-grid">
                  <label class="field"><span>Title</span><input v-model="eventForm.title" placeholder="Event Title" /></label>
                  <label class="field"><span>Venue</span><input v-model="eventForm.venue" placeholder="Venue Name" /></label>
                  <label class="field"><span>Attendees</span><input v-model="eventForm.attendies" type="number" min="1" /></label>
                  <label class="field"><span>Date</span><input v-model="eventForm.date" type="date" /></label>
                  <label class="field"><span>Start Time</span><input v-model="eventForm.startTime" type="time" /></label>
                  <label class="field"><span>End Time</span><input v-model="eventForm.endTime" type="time" /></label>
                  <label class="field full-width"><span>Organization</span>
                    <select v-model="eventForm.organization">
                      <option value="" disabled>Select Organization</option>
                      <option v-for="organization in organizationList" :key="organization.id" :value="organization.id">[[ organization.name ]]</option>
                    </select>
                  </label>
                </div>
                <h3 class="section-title margin-top">02. EVENT NEEDS</h3>
                <div class="needs-list">
                  <div v-for="(need, index) in eventForm.needs" :key="index" class="need-row">
                    <label class="field flex-grow"><span>Item Name</span>
                      <select v-model="need.item">
                        <option value="" disabled>Select Item</option>
                        <option v-for="item in itemList" :key="item.id" :value="item.id">[[ item.name ]]</option>
                      </select>
                    </label>
                    <label class="field qty-field"><span>Quantity</span><input v-model="need.quantity" type="number" min="1" /></label>
                    <button class="btn-remove-row" type="button" aria-label="Remove item need" @click="removeEventNeedRow(index)">✕</button>
                  </div>
                  <button class="btn-add-row" type="button" @click="addEventNeedRow">+ Add Item Need</button>
                </div>
              </div>
            </div>
            <footer class="panel-bottom-action"><button class="submit-button action-btn" @click="handleEventSubmit">[[ tabMode === 'add' ? 'ADD EVENT' : 'SAVE CHANGES' ]] <span>↗</span></button></footer>
          </section>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) { background: #101010; min-width: 320px; margin: 0; }
:global(button), :global(input), :global(select) { font: inherit; }
.loader-screen { min-height: 100vh; min-height: 100dvh; background: #101010; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #929292; font-family: Inter, sans-serif; font-size: 11px; letter-spacing: .1em; }
.spinner { width: 24px; height: 24px; border: 2px solid #333; border-top-color: #f5f5f5; border-radius: 50%; animation: spin .8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.dashboard-page { --bg: #101010; --surface: #141414; --white: #f5f5f5; --muted: #929292; --line: #333; min-height: 100vh; min-height: 100dvh; height: 100vh; height: 100dvh; overflow: hidden; display: flex; flex-direction: column; padding: 28px clamp(20px, 5vw, 76px) 20px; background: var(--bg); color: var(--white); font-family: Inter, sans-serif; position: relative; }
.topbar { flex: 0 0 auto; display: flex; align-items: center; justify-content: space-between; padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 24px; }
.brand { display: inline-flex; align-items: center; gap: 11px; font-size: 12px; font-weight: 750; letter-spacing: .13em; }
.brand-icon { display: grid; width: 30px; height: 30px; place-items: center; border: 1px solid #777; font-size: 15px; font-weight: 800; flex: 0 0 auto; }
.brand-icon.small { width: 26px; height: 26px; font-size: 12px; }
.muted { color: var(--muted); }
.profile-container { position: relative; z-index: 30; }
.profile-circle { width: 40px; height: 40px; border-radius: 50%; background: var(--surface); border: 1px solid var(--line); color: var(--white); cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 8px; }
.profile-circle svg { width: 22px; height: 22px; }
.profile-popover { position: absolute; top: calc(100% + 10px); right: 0; width: min(390px, calc(100vw - 28px)); max-height: min(76vh, 720px); max-height: min(76dvh, 720px); overflow-y: auto; background: #141414; border: 1px solid #373737; box-shadow: 0 18px 45px #000a; z-index: 40; padding: 18px; }
.profile-popover-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; padding-bottom: 14px; margin-bottom: 16px; border-bottom: 1px solid var(--line); }
.profile-popover-header h2 { margin: 4px 0 0; font-size: 16px; letter-spacing: -.02em; }
.popover-close { border: 0; background: transparent; color: #aaa; font-size: 26px; line-height: 1; cursor: pointer; }
.profile-form { display: flex; flex-direction: column; gap: 14px; }
.profile-form .field-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.profile-save { width: 100%; margin-top: 2px; }
.profile-unavailable { margin: 0 0 16px; color: #bbb; font-size: 12px; line-height: 1.6; }
.profile-popover-footer { border-top: 1px solid var(--line); margin-top: 16px; padding-top: 14px; }
.logout-button { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 12px; background: transparent; color: #ff9292; border: 1px solid #553333; font-size: 11px; font-weight: 750; letter-spacing: .1em; cursor: pointer; }
.logout-button:hover { background: #251717; }

.dashboard-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; flex: 1 1 auto; min-height: 0; }
.dashboard-column { display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--line); padding: 20px; min-width: 0; min-height: 0; overflow: hidden; }
.column-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
.column-index { color: var(--muted); font-size: 10px; font-weight: 700; flex: 0 0 auto; }
.column-header h2 { margin: 0; font-size: 14px; font-weight: 650; letter-spacing: .1em; flex: 1; min-width: 0; }
.count { background: #333; padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; flex: 0 0 auto; }
.column-intro { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 16px; }
.column-intro p { margin: 0; color: var(--muted); font-size: 11px; line-height: 1.5; }
.manage-events-button { display: inline-flex; align-items: center; gap: 18px; padding: 10px 12px; background: #f5f5f5; color: #111; border: 1px solid #f5f5f5; font-size: 10px; font-weight: 800; letter-spacing: .08em; cursor: pointer; white-space: nowrap; }
.manage-events-button:hover { background: #d8d8d8; }
.events-list { display: flex; flex-direction: column; gap: 16px; flex: 1 1 auto; min-height: 0; overflow-y: auto; padding-right: 4px; }
.events-list::-webkit-scrollbar { width: 4px; }
.events-list::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }
.event-card { background: #1a1a1a; border: 1px solid #2a2a2a; padding: 16px; border-radius: 2px; transition: border-color .2s, background .2s; }
.event-card.clickable { cursor: pointer; }
.event-card.clickable:hover { border-color: #777; background: #202020; }
.event-card-heading { display: flex; gap: 10px; justify-content: space-between; align-items: flex-start; }
.event-title { margin: 0 0 12px; font-size: 14px; font-weight: 600; letter-spacing: -.02em; overflow-wrap: anywhere; }
.status-pill { flex: 0 0 auto; margin-bottom: 8px; padding: 4px 6px; font-size: 8px; font-weight: 800; letter-spacing: .06em; border: 1px solid #444; color: #ccc; }
.approved-status { border-color: #686868; color: #f5f5f5; }
.pending-status { border-color: #5a4b32; color: #d9c29c; }
.event-details p { margin: 7px 0; font-size: 11px; color: #ccc; display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.event-details span { color: var(--muted); font-size: 9px; font-weight: 700; letter-spacing: .08em; flex: 0 0 auto; }
.event-details strong { color: #ddd; font-weight: 500; text-align: right; overflow-wrap: anywhere; }
.empty-state { color: var(--muted); font-size: 11px; line-height: 1.7; text-align: center; padding: 30px 14px; border: 1px dashed #333; }
.date-filter-row { display: flex; flex-direction: column; gap: 9px; margin-bottom: 16px; }
.date-filter-row > p { margin: 0; color: var(--muted); font-size: 11px; }
.date-filter { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.date-filter span { color: #d0d0d0; font-size: 10px; font-weight: 700; letter-spacing: .1em; }
.date-filter input { width: min(220px, 60%); padding: 9px 10px; border: 1px solid #383838; background: #101010; color: var(--white); font-size: 12px; color-scheme: dark; }
.fab-menu { position: fixed; bottom: 30px; right: 30px; width: 56px; height: 56px; border-radius: 50%; background: var(--white); color: #111; border: none; box-shadow: 0 4px 20px #0008; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10; }
.fab-menu svg { width: 23px; height: 23px; }
.fab-menu:hover { transform: scale(1.05); }

.toast-container { position: fixed; top: 30px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; gap: 10px; z-index: 2000; width: min(92vw, 440px); }
.toast { padding: 12px 18px; border-radius: 4px; font-size: 12px; font-weight: 600; color: #fff; box-shadow: 0 10px 30px #000c; animation: slideDown .3s ease; background: #1a1a1a; overflow-wrap: anywhere; }
.toast.success { border: 1px solid #4caf50; border-left: 4px solid #4caf50; }
.toast.error { border: 1px solid #ff5252; border-left: 4px solid #ff5252; }
@keyframes slideDown { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.overlay { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; padding: 20px; background: #000c; backdrop-filter: blur(5px); }
.auth-card { position: relative; width: min(100%, 550px); max-height: 90vh; max-height: 90dvh; overflow-y: auto; padding: clamp(23px, 5vw, 38px); border: 1px solid #373737; background: #141414; }
.close-button { position: absolute; top: 14px; right: 15px; width: 32px; height: 32px; border: 0; background: transparent; color: #aaa; cursor: pointer; font-size: 24px; }
.card-eyebrow { margin: 0 0 10px; font-size: 9px; font-weight: 700; letter-spacing: .15em; color: var(--muted); }
.auth-card h2 { margin: 0 0 25px; font-size: clamp(1.6rem, 4vw, 2rem); font-weight: 650; letter-spacing: -.05em; overflow-wrap: anywhere; }
.view-title { padding-right: 28px; margin-bottom: 24px !important; }
.view-grid { display: grid; gap: 12px; padding-bottom: 16px; border-bottom: 1px dashed var(--line); }
.view-grid p { margin: 0; font-size: 13px; color: #ddd; display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
.view-grid span { font-size: 10px; font-weight: 700; color: var(--muted); letter-spacing: .1em; flex: 0 0 auto; }
.view-grid strong { font-weight: 500; text-align: right; overflow-wrap: anywhere; }
.view-needs .needs-heading { margin-top: 24px; margin-bottom: 12px; }
.view-needs ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.view-needs li { display: flex; justify-content: space-between; gap: 12px; background: #1a1a1a; border: 1px solid var(--line); padding: 10px 16px; font-size: 12px; color: #eee; }
.view-needs li strong { color: var(--muted); }
.confirm-modal { text-align: center; width: min(100%, 430px); }
.confirm-modal p { color: #ccc; font-size: 13px; line-height: 1.5; margin-bottom: 24px; }
.confirm-actions { display: flex; gap: 12px; }
.btn-action { flex: 1; padding: 10px; border: 1px solid var(--line); background: transparent; color: var(--white); font-size: 10px; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: .1em; }
.btn-action.approve { background: #fff; color: #000; border-color: #fff; }

/* Event management popup */
.menu-modal-container { width: 80vw; height: 80vh; height: 80dvh; max-width: 1200px; max-height: 800px; min-width: 0; min-height: 0; background: #141414; border: 1px solid #373737; display: flex; flex-direction: column; box-shadow: 0 20px 50px #000c; }
.menu-modal-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 16px 24px; border-bottom: 1px solid var(--line); background: #101010; }
.card-brand { display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 750; letter-spacing: .12em; padding-right: 36px; }
.menu-modal-body { display: flex; flex: 1 1 auto; min-height: 0; overflow: hidden; }
.tab-sidebar { flex: 0 0 25%; background: #101010; border-right: 1px solid var(--line); display: flex; flex-direction: column; padding: 16px 0; }
.tab-btn { width: 100%; padding: 16px 24px; background: #171717; border: none; border-left: 3px solid var(--white); color: var(--white); font-size: 12px; font-weight: 700; letter-spacing: .1em; text-align: left; }
.tab-content-panel { flex: 1 1 75%; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: #141414; overflow: hidden; }
.panel-top-controls { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 20px 30px; border-bottom: 1px solid var(--line); }
.mode-toggle { display: flex; border: 1px solid var(--line); border-radius: 2px; overflow: hidden; flex: 0 0 auto; }
.toggle-btn { padding: 8px 20px; background: transparent; border: none; color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .1em; cursor: pointer; }
.toggle-btn.active { background: var(--white); color: #111; }
.btn-delete { background: transparent; border: 1px solid #ff9292; color: #ff9292; padding: 8px 16px; font-size: 10px; font-weight: 700; cursor: pointer; }
.btn-delete:disabled { opacity: .3; cursor: not-allowed; border-color: #555; color: #555; }
.edit-selector-container { padding: 16px 30px; background: #101010; border-bottom: 1px solid var(--line); }
.selector-note { color: var(--muted); font-size: 11px; margin: 9px 0 0; }
.form-scroll-area { flex: 1 1 auto; min-height: 0; padding: 30px; overflow-y: auto; }
.section-title { font-size: 11px; font-weight: 700; letter-spacing: .15em; color: var(--muted); margin: 0 0 16px; }
.section-title.margin-top { margin-top: 32px; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.field { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.field.full-width { grid-column: 1 / -1; }
.field > span { color: #d0d0d0; font-size: 11px; font-weight: 600; }
.field input, .field select { width: 100%; min-width: 0; max-width: 100%; padding: 11px 12px; border: 1px solid #383838; background: #101010; color: var(--white); font-size: 12px; outline: none; border-radius: 0; }
.field input:focus, .field select:focus { border-color: #aaa; }
.field input[readonly] { color: #777; background: #1a1a1a; cursor: not-allowed; }
input[type="date"], input[type="time"] { color-scheme: dark; }
.needs-list { display: flex; flex-direction: column; gap: 12px; }
.need-row { display: flex; gap: 12px; align-items: flex-end; min-width: 0; }
.flex-grow { flex: 1 1 auto; min-width: 0; }
.qty-field { width: 100px; flex: 0 0 100px; }
.btn-remove-row { height: 40px; width: 40px; flex: 0 0 40px; background: transparent; border: 1px solid #383838; color: #ff9292; cursor: pointer; }
.btn-add-row { align-self: flex-start; background: transparent; border: 1px dashed #555; color: var(--white); padding: 10px 16px; font-size: 11px; font-weight: 600; cursor: pointer; margin-top: 8px; }
.panel-bottom-action { padding: 20px 30px; border-top: 1px solid var(--line); background: #101010; display: flex; justify-content: flex-end; }
.submit-button { display: flex; min-height: 45px; align-items: center; justify-content: space-between; gap: 12px; padding: 0 15px; border: 1px solid #f1f1f1; background: #f1f1f1; color: #111; font-weight: 750; font-size: 12px; cursor: pointer; }
.submit-button:disabled { opacity: .6; cursor: wait; }

@media (max-width: 1024px) {
  .dashboard-page { height: auto; min-height: 100vh; min-height: 100dvh; overflow: auto; padding: 22px clamp(16px, 3vw, 30px) 24px; }
  .dashboard-grid { grid-template-columns: minmax(0, 1fr); flex: 0 0 auto; }
  .dashboard-column { min-height: 440px; }
  .menu-modal-container { width: 95vw; height: 90vh; height: 90dvh; max-height: none; }
  .menu-modal-body { flex-direction: column; }
  .tab-sidebar { flex: 0 0 auto; flex-direction: row; gap: 4px; padding: 8px; border-right: 0; border-bottom: 1px solid var(--line); overflow-x: auto; overflow-y: hidden; }
  .tab-btn { flex: 0 0 auto; width: auto; padding: 12px 16px; border-left: 0; border-bottom: 3px solid var(--white); white-space: nowrap; }
  .tab-content-panel { flex: 1 1 auto; width: 100%; }
  .form-scroll-area { min-height: 0; }
  .fab-menu { bottom: 22px; right: 22px; }
}

@media (max-width: 640px) {
  .dashboard-page { min-height: 100vh; min-height: 100dvh; height: auto; padding: 16px 12px calc(88px + env(safe-area-inset-bottom)); }
  .topbar { padding-bottom: 16px; margin-bottom: 16px; }
  .brand { font-size: 10px; gap: 8px; }
  .brand-icon { width: 28px; height: 28px; }
  .dashboard-grid { gap: 14px; }
  .dashboard-column { min-height: 360px; padding: 14px; }
  .column-header { gap: 8px; margin-bottom: 12px; padding-bottom: 12px; }
  .column-header h2 { font-size: 12px; letter-spacing: .07em; }
  .column-intro { align-items: flex-start; flex-direction: column; gap: 10px; }
  .manage-events-button { width: 100%; justify-content: space-between; }
  .date-filter { align-items: flex-start; flex-direction: column; gap: 8px; }
  .date-filter input { width: 100%; }
  .event-card { padding: 13px; }
  .event-card-heading { flex-direction: column; gap: 0; }
  .event-title { font-size: 13px; }
  .status-pill { align-self: flex-start; }
  .event-details p { font-size: 10px; gap: 8px; }
  .event-details span { font-size: 8px; }
  .profile-popover { position: fixed; top: 68px; right: 10px; width: calc(100vw - 20px); max-height: calc(100vh - 82px); max-height: calc(100dvh - 82px); padding: 15px; }
  .profile-form .field-grid { grid-template-columns: minmax(0, 1fr); }
  .fab-menu { width: 50px; height: 50px; right: 16px; bottom: calc(16px + env(safe-area-inset-bottom)); }
  .menu-modal-container { width: calc(100vw - 12px); height: calc(100vh - 12px); height: calc(100dvh - 12px); max-width: none; max-height: none; }
  .menu-modal-header { padding: 12px 16px; }
  .menu-modal-body { flex: 1 1 auto; min-height: 0; }
  .tab-sidebar { padding: 6px; }
  .tab-btn { padding: 10px 14px; font-size: 10px; }
  .panel-top-controls { flex-wrap: wrap; gap: 10px; padding: 12px 14px; }
  .mode-toggle { max-width: 100%; }
  .toggle-btn { padding: 8px 12px; }
  .btn-delete { padding: 8px 10px; }
  .edit-selector-container { padding: 12px 14px; }
  .form-scroll-area { padding: 16px 14px; }
  .field-grid { grid-template-columns: minmax(0, 1fr); gap: 14px; }
  .field.full-width { grid-column: 1 / -1; }
  .field input, .field select { font-size: 13px; }
  .need-row { display: grid; grid-template-columns: minmax(0, 1fr) 68px 36px; align-items: end; gap: 8px; }
  .qty-field { width: auto; min-width: 0; flex: initial; }
  .btn-remove-row { width: 36px; height: 40px; }
  .panel-bottom-action { padding: 12px 14px; }
  .submit-button { width: 100%; }
  .overlay { padding: 6px; }
  .view-grid p { flex-direction: column; gap: 4px; }
  .view-grid strong { text-align: left; }
}
</style>
