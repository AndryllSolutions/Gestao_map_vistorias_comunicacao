function logar() {
  const email = document.getElementById("email").value.trim();
  const senha = document.getElementById("senha").value.trim();

  fetch("/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",  // ⬅️ ESSENCIAL para sessões funcionarem com ngrok!
    body: JSON.stringify({ email: email, password: senha }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.redirect) {
        window.location.href = data.redirect;
      } else {
        alert(data.error || "Login inválido");
      }
    })
    .catch((error) => {
      console.error("Erro no login:", error);
      alert("Erro no login");
    });
}
