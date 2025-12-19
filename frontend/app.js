const API = "https://SEU_BACKEND.onrender.com";

function login() {
  localStorage.setItem("user_id", "teste-user");
  window.location.href = "dashboard.html";
}

function gerarOrcamento() {
  const tipo = document.getElementById("tipo").value;
  const margem = document.getElementById("margem").value;
  const user_id = localStorage.getItem("user_id");

  fetch(`${API}/orcamento/gerar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id,
      tipo_servico: tipo,
      margem_percentual: Number(margem)
    })
  })
  .then(res => res.json())
  .then(data => {
    localStorage.setItem("resultado",
      JSON.stringify(data.orcamento, null, 2));
    window.location.href = "resultado.html";
  });
}
