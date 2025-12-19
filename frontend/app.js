async function gerar() {
  const userId = document.getElementById("userId").value;
  const tipo = document.getElementById("tipo").value;
  const margem = Number(document.getElementById("margem").value);

  const res = await fetch("https://orcamento-ai-backend.onrender.com/health", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      tipo_servico: tipo,
      margem_percentual: margem
    })
  });

  const data = await res.json();
  const pre = document.getElementById("resultado");
  pre.classList.remove("hidden");
  pre.textContent = JSON.stringify(data, null, 2);
}
