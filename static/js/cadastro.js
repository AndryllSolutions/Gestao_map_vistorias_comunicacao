async function cadastrar() {
  const email = document.getElementById("email").value.trim();
  const senha = document.getElementById("senha").value.trim();

  if (!email || !senha) {
    alert("Preencha todos os campos");
    return;
  }

  const res = await fetch("/cadastro", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });

  const data = await res.json();
  alert(data.mensagem);

  if (res.status === 201) {
    window.location.href = "/";
  }
}
