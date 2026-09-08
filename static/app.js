const { createApp, ref } = Vue;

createApp({
  delimiters: ["[[", "]]"],
  setup() {
    const text = ref("Hello world");
    const reg_or_log = ref(true); //true for login false for register
    const authenticated = ref(false); //false by default to make the user login or register an account

    return {
      text,
      reg_or_log,
      authenticated,
    };
  },
}).mount("#app");
