async function logar() {
  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  const resposta = await fetch("/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ email, senha })
  });

  const data = await resposta.json();
  alert(data.mensagem);

  if (resposta.status === 200) {
    window.location.href = "/dashboard";
  }
}
