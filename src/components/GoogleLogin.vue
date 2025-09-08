<template>
  <div>
    <a href="#" @click.prevent="moveToGoogleOAuth">Google でログイン</a>
  </div>
</template>

<script lang="ts">
import Vue from "vue";
import axios from "axios";

interface LoginPathResponse {
  url: string;
}

export default Vue.extend({
  methods: {
    async moveToGoogleOAuth() {
      try {
        const res = await axios.get<LoginPathResponse>("/api/login/google/loginPath");
        window.location.href = res.data.url;
      } catch (err) {
        console.error("Google OAuth へのリダイレクト失敗", err);
        alert("ログイン処理でエラーが発生しました");
      }
    },
  },
});
</script>
