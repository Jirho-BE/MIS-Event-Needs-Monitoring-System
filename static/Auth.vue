<script setup>
import { ref, onMounted } from 'vue'

const mode = ref('login')
const formOpen = ref(false)
const authenticated = ref(false)
const currentUser = ref({
  firstName: '',
  organization: ''
})

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const options = ref([]) 

async function fetchOrganizations() {
  try {

    const response = await fetch('/api/organization-list/') 
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    options.value = data
    
  } catch (error) {
    console.error('Failed to load organizations:', error)
    errorMessage.value = 'Could not load organizations from server.'
  }
}

onMounted(() => {
  fetchOrganizations()
})

const registerForm = ref({
  firstName: '',
  lastName: '',
  organization: ''
})

function openForm(nextMode) {
  mode.value = nextMode
  formOpen.value = true
  errorMessage.value = ''
  successMessage.value = ''
}

function closeForm() {
  formOpen.value = false
  errorMessage.value = ''
  successMessage.value = ''
}

function resetPage() {
  closeForm()
}

function clearFields() {
  username.value = ''
  password.value = ''
  confirmPassword.value = ''
  registerForm.value = { firstName: '', lastName: '', organization: '' }
  errorMessage.value = ''
  successMessage.value = ''
}

function switchMode() {
  const nextMode = mode.value === 'login' ? 'register' : 'login'
  clearFields()
  openForm(nextMode)
}

async function submitForm() {
  errorMessage.value = ''
  successMessage.value = ''

  const cleanUsername = username.value.trim()

  // 1. Basic Client-Side Validation
  if (cleanUsername.length < 3) {
    errorMessage.value = 'Username must contain at least 3 characters.'
    return
  }

  if (password.value.length < 5) {
    errorMessage.value = 'Password must contain at least 6 characters.'
    return
  }

  // ==========================================
  // REGISTRATION LOGIC
  // ==========================================
  if (mode.value === 'register') {
    const { firstName, lastName, organization } = registerForm.value

    if (!firstName.trim() || !lastName.trim() || !organization) {
      errorMessage.value = 'Please complete all required fields.'
      return
    }

    if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Passwords do not match.'
      return
    }

    // Match your Django Accounts model fields
    const payload = {
      username: cleanUsername,
      password: password.value,
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      org_id: organization // This should now be the ID from your dropdown
    }

    try {
      const response = await fetch('api/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        // Handle Django DRF validation errors (e.g., {"username": ["Already exists."]})
        const firstErrorKey = Object.keys(data)[0]
        const firstErrorMessage = Array.isArray(data[firstErrorKey])
          ? data[firstErrorKey][0]
          : data[firstErrorKey]

        errorMessage.value = `${firstErrorKey}: ${firstErrorMessage}`
        return
      }

      // Success: Clear fields and switch to login
      clearFields()
      mode.value = 'login'
      successMessage.value = 'Account created successfully. You can now login.'

    } catch (error) {
      console.error('Registration error:', error)
      errorMessage.value = 'Network error. Could not reach the server.'
    }
    return
  }

  // ==========================================
  // LOGIN LOGIC
  // ==========================================
  if (mode.value === 'login') {
    const payload = {
      username: cleanUsername,
      password: password.value
    }

    try {
      const response = await fetch('api/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      // Handle invalid credentials (401 Unauthorized)
      if (!response.ok) {
        errorMessage.value = data.detail || 'Invalid username or password.'
        return
      }

      // ---------------------------------------------------------
      // SUCCESS: SAVE TOKENS TO LOCAL STORAGE
      // ---------------------------------------------------------
      // Inside submitForm() -> mode.value === 'login' block

        localStorage.setItem('access_token', data.tokens.access)
      localStorage.setItem('refresh_token', data.tokens.refresh)

      currentUser.value = {
        firstName: cleanUsername, // Temporarily use username until profile is fetched
        organization: '' 
      }
      
      authenticated.value = true
      closeForm()
      clearFields()

      console.log('Logged in successfully! Tokens saved.')
        window.location.href = '/admin-dashboard/'

    } catch (error) {
      console.error('Login error:', error)
      errorMessage.value = 'Network error. Could not reach the server.'
    }
  }
}

function logout() {
  authenticated.value = false
  currentUser.value = { firstName: '', organization: '' }
  clearFields()
  openForm('login')
}
</script>

<template>
  <main class="auth-page">
    <header class="topbar">
      <a class="brand" href="#" @click.prevent="resetPage">
        <span class="brand-icon">M</span>
        <span>MIS <span class="muted">EVENT MONITORING</span></span>
      </a>
      <span class="system-label">EVENT MANAGEMENT SYSTEM</span>
    </header>

    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">ORGANIZE. MONITOR. EXECUTE.</span>

        <h1>
          MIS EVENT<br />
          MONITORING<span class="period">.</span>
        </h1>

        <p class="description">
          A centralized space to manage events, monitor progress,
          and keep every detail organized.
        </p>

        <div v-if="!authenticated" class="actions">
          <button class="btn btn-primary" @click="openForm('login')">
            Login <span aria-hidden="true">↗</span>
          </button>
          <button class="btn btn-secondary" @click="openForm('register')">
            Create account
          </button>
        </div>

        <div v-else class="session">
          <span class="session-dot"></span>
          <div class="session-info">
            <strong>Welcome, [[ currentUser.firstName ]]</strong>
            <span>[[ currentUser.organization ]]</span>
          </div>
          <button class="text-button" @click="logout">Sign out</button>
        </div>

        <p class="footnote">ONE WORKSPACE. EVERY EVENT.</p>
      </div>

      <aside class="info-panel">
        <span class="panel-index">01 / OVERVIEW</span>
        <div class="panel-content">
          <span class="panel-line"></span>
          <h2>Everything<br />in one place.</h2>
          <p>
            Keep your event information organized and your
            monitoring workflow simple.
          </p>
        </div>
        <div class="panel-bottom">
          <span>EVENT MONITORING</span>
          <span>EST. 2026</span>
        </div>
      </aside>
    </section>

    <footer class="footer">
      <span>MIS EVENT MONITORING</span>
      <span>MINIMAL BY DESIGN.</span>
    </footer>

    <!-- Authentication modal -->
    <div
      v-if="formOpen"
      class="overlay"
      @click.self="closeForm"
      @keydown.esc="closeForm"
    >
      <section
        class="auth-card"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="'auth-heading'"
      >
        <button
          class="close-button"
          type="button"
          aria-label="Close"
          @click="closeForm"
        >×</button>

        <div class="card-brand">
          <span class="brand-icon small">M</span>
          <span>MIS EVENT MONITORING</span>
        </div>

        <p class="card-eyebrow">
          [[ mode === 'login' ? 'ACCOUNT ACCESS' : 'NEW ACCOUNT' ]]
        </p>

        <h2 id="auth-heading">
          [[ mode === 'login' ? 'Welcome back.' : 'Get started.' ]]
        </h2>

        <p class="card-description">
          [[ mode === 'login'
            ? 'Sign in to continue to your workspace.'
            : 'Enter your details to create an account.' ]]
        </p>

        <form @submit.prevent="submitForm">
          <template v-if="mode === 'register'">
            <div class="field-row">
              <label class="field">
                <span>First name</span>
                <input
                  v-model.trim="registerForm.firstName"
                  placeholder="First name"
                  autocomplete="given-name"
                  required
                />
              </label>

              <label class="field">
                <span>Last name</span>
                <input
                  v-model.trim="registerForm.lastName"
                  placeholder="Last name"
                  autocomplete="family-name"
                  required
                />
              </label>
            </div>
          </template>

          <label class="field">
            <span>Username</span>
            <input
              v-model.trim="username"
              placeholder="Enter your username"
              autocomplete="username"
              minlength="3"
              required
            />
          </label>

          <label class="field">
            <span>Password</span>
            <input
              v-model="password"
              type="password"
              placeholder="Enter your password"
              :autocomplete="mode === 'login'
                ? 'current-password'
                : 'new-password'"
              minlength="5"
              required
            />
          </label>

          <label v-if="mode === 'register'" class="field">
            <span>Confirm password</span>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="Re-enter your password"
              autocomplete="new-password"
              minlength="5"
              required
            />
          </label>

          <label v-if="mode === 'register'" class="field">
            <span>Organization</span>
            <select v-model="registerForm.organization" required>
              <option value="" disabled>Select organization</option>
              <!-- Updated to loop through 'options' -->
              <option
                v-for="option in options"
                :key="option.id"
                :value="option.id"
              >
                [[ option.name ]]
              </option>
            </select>
          </label>

          <p v-if="errorMessage" class="message error" role="alert">
            [[ errorMessage ]]
          </p>

          <p v-if="successMessage" class="message success" role="status">
            [[ successMessage ]]
          </p>

          <button class="submit-button" type="submit">
            [[ mode === 'login' ? 'Login' : 'Create account' ]]
            <span aria-hidden="true">↗</span>
          </button>
        </form>

        <p class="switch-text">
          [[ mode === 'login'
            ? 'Don’t have an account?'
            : 'Already have an account?' ]]

          <button type="button" @click="switchMode">
            [[ mode === 'login' ? 'Register' : 'Sign in' ]]
          </button>
        </p>

        <p class="security-note">
          Prototype authentication · Connect Django for production use.
        </p>
      </section>
    </div>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(html),
:global(body),
:global(#app) {
  min-height: 100%;
  margin: 0;
}

:global(body) {
  min-width: 320px;
  background: #101010;
}

:global(button),
:global(input),
:global(select) {
  font: inherit;
}

.auth-page {
  --bg: #101010;
  --surface: #171717;
  --white: #f5f5f5;
  --muted: #929292;
  --line: #333333;

  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 28px clamp(20px, 5vw, 76px) 20px;
  overflow: hidden;
  background: var(--bg);
  color: var(--white);
  font-family: Inter, "Segoe UI", Arial, sans-serif;
}

.topbar,
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--white);
  text-decoration: none;
  font-size: 12px;
  font-weight: 750;
  letter-spacing: .13em;
}

.brand-icon {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid #777;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0;
}

.brand-icon.small {
  width: 26px;
  height: 26px;
  font-size: 12px;
}

.muted,
.system-label,
.eyebrow,
.panel-index,
.panel-bottom,
.footnote,
.footer,
.card-eyebrow,
.security-note {
  color: var(--muted);
}

.system-label,
.eyebrow,
.panel-index,
.panel-bottom,
.footnote,
.footer {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .14em;
}

.hero {
  display: grid;
  width: min(1100px, 100%);
  flex: 1;
  grid-template-columns: minmax(0, 1.4fr) minmax(250px, .6fr);
  align-items: center;
  gap: clamp(40px, 8vw, 120px);
  margin: 40px auto;
}

.hero-copy {
  min-width: 0;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: clamp(2.7rem, 6.2vw, 6.1rem);
  font-weight: 850;
  letter-spacing: -.075em;
  line-height: .98;
  overflow-wrap: anywhere;
}

.period {
  color: #777;
}

.description {
  max-width: 390px;
  margin: 23px 0 0;
  color: #a0a0a0;
  font-size: 14px;
  line-height: 1.8;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 30px;
}

.btn {
  display: inline-flex;
  min-height: 43px;
  align-items: center;
  justify-content: center;
  gap: 22px;
  padding: 0 19px;
  border: 1px solid var(--line);
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  transition: background .18s, color .18s, border-color .18s;
}

.btn-primary {
  border-color: var(--white);
  background: var(--white);
  color: #111;
}

.btn-primary:hover {
  background: #d5d5d5;
}

.btn-secondary {
  background: transparent;
  color: var(--white);
}

.btn-secondary:hover {
  border-color: #888;
  background: #ffffff08;
}

.footnote {
  margin-top: 52px;
}

.info-panel {
  display: flex;
  min-height: 340px;
  flex-direction: column;
  justify-content: space-between;
  padding: 22px;
  border: 1px solid #303030;
  background: #141414;
}

.panel-content {
  padding: 25px 0;
}

.panel-line {
  display: block;
  width: 28px;
  height: 2px;
  margin-bottom: 25px;
  background: #eee;
}

.panel-content h2 {
  margin: 0;
  font-size: clamp(1.8rem, 3vw, 2.7rem);
  font-weight: 650;
  letter-spacing: -.055em;
  line-height: 1.1;
}

.panel-content p {
  max-width: 230px;
  margin-top: 17px;
  color: #999;
  font-size: 12px;
  line-height: 1.8;
}

.panel-bottom {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding-top: 17px;
  border-top: 1px solid var(--line);
  font-size: 8px;
}

.footer {
  padding-top: 17px;
  border-top: 1px solid #292929;
  font-size: 8px;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  overflow-y: auto;
  place-items: center;
  padding: 20px;
  background: #000c;
  backdrop-filter: blur(5px);
}

.auth-card {
  position: relative;
  width: min(100%, 430px);
  max-height: calc(100dvh - 40px);
  overflow-y: auto;
  padding: clamp(23px, 5vw, 38px);
  border: 1px solid #373737;
  background: #141414;
}

.close-button {
  position: absolute;
  top: 14px;
  right: 15px;
  width: 32px;
  height: 32px;
  border: 0;
  background: transparent;
  color: #aaa;
  cursor: pointer;
  font-size: 24px;
}

.card-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-right: 20px;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: .1em;
}

.card-eyebrow {
  margin: 32px 0 10px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .15em;
}

.auth-card h2 {
  margin: 0;
  font-size: clamp(1.8rem, 5vw, 2.25rem);
  font-weight: 650;
  letter-spacing: -.06em;
}

.card-description {
  margin: 10px 0 25px;
  color: #999;
  font-size: 12px;
  line-height: 1.7;
}

.auth-card form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 8px;
}

.field > span {
  color: #d0d0d0;
  font-size: 11px;
  font-weight: 600;
}

.field-row {
  display: flex;
  gap: 12px;
}

.field input,
.field select {
  width: 100%;
  min-width: 0;
  min-height: 43px;
  padding: 11px 12px;
  border: 1px solid #383838;
  border-radius: 2px;
  outline: none;
  background: #101010;
  color: #f4f4f4;
  font-size: 12px;
}

.field input::placeholder {
  color: #696969;
}

.field input:focus,
.field select:focus {
  border-color: #aaa;
}

.field select:invalid {
  color: #888;
}

.submit-button {
  display: flex;
  min-height: 45px;
  align-items: center;
  justify-content: space-between;
  margin-top: 3px;
  padding: 0 15px;
  border: 1px solid #f1f1f1;
  background: #f1f1f1;
  color: #111;
  cursor: pointer;
  font-size: 12px;
  font-weight: 750;
  transition: background .18s;
}

.submit-button:hover {
  background: #d6d6d6;
}

.switch-text {
  margin: 22px 0 0;
  color: #999;
  font-size: 11px;
  text-align: center;
}

.switch-text button,
.text-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: #f5f5f5;
  cursor: pointer;
  font-size: inherit;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.security-note {
  margin: 24px 0 0;
  font-size: 9px;
  line-height: 1.6;
  text-align: center;
}

.message {
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
}

.error {
  color: #ff9292;
}

.success {
  color: #c9c9c9;
}

.session {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 30px;
}

.session-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #eee;
}

.session-info {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}

.session-info strong {
  font-size: 12px;
}

.session-info span {
  color: #999;
  font-size: 10px;
}

.text-button {
  font-size: 10px;
}

@media (min-width: 1500px) {
  .hero {
    width: min(1200px, 100%);
  }
}

@media (max-width: 760px) {
  .auth-page {
    padding: 22px 22px 16px;
  }

  .system-label {
    display: none;
  }

  .hero {
    grid-template-columns: 1fr;
    gap: 35px;
    margin: 65px auto 45px;
  }

  h1 {
    font-size: clamp(2.7rem, 9.2vw, 4.6rem);
  }

  .description {
    max-width: 440px;
  }

  .footnote {
    margin-top: 32px;
  }

  .info-panel {
    min-height: 240px;
  }

  .panel-content {
    padding: 28px 0;
  }

  .panel-content h2 {
    font-size: 2rem;
  }

  .footer {
    gap: 12px;
    letter-spacing: .08em;
  }
}

@media (max-width: 420px) {
  .auth-page {
    padding-right: 17px;
    padding-left: 17px;
  }

  .brand {
    font-size: 10px;
    letter-spacing: .08em;
  }

  .hero {
    margin-top: 50px;
  }

  .actions {
    align-items: stretch;
  }

  .btn {
    flex: 1;
    gap: 10px;
    padding: 0 12px;
  }

  .field-row {
    flex-direction: column;
  }

  .auth-card {
    padding: 24px 19px;
  }

  .footer {
    font-size: 7px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
</style>