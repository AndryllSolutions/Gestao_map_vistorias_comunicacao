const api = "http://localhost:5000/api";

// CADASTRO
async function cadastrarUsuario(event) {
  event.preventDefault();

  const nome = document.getElementById("nome").value;
  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  const resposta = await fetch(`${api}/cadastrar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, email, senha }),
  });

  const resultado = await resposta.json();
  alert(resultado.message);
}

// LOGIN
async function loginUsuario(event) {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  const resposta = await fetch(`${api}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });

  const resultado = await resposta.json();
  alert(resultado.message);

  if (resultado.success) {
    window.location.href = "dashboard.html";
  }
}
