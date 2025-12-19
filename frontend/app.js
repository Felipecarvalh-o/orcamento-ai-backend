<script>
const API_URL = "https://SEU_BACKEND.onrender.com";

function getUserId() {
  return localStorage.getItem("user_id");
}

function requireAuth() {
  if (!getUserId()) {
    window.location.href = "index.html";
  }
}
</script>

