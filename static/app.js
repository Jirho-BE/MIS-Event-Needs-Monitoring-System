const { createApp, ref } = Vue;

createApp({
  delimiters: ["[[", "]]"],
  setup() {
    const text = ref("Hello world");

    return {
      text,
    };
  },
}).mount("#app");
