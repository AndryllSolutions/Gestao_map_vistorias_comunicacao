const msg = document.getElementById('mensagem')

document.getElementById('formCadastro').addEventListener('submit', async (e) => {
  e.preventDefault()
  const nome = document.getElementById('nome').value
  const email = document.getElementById('emailCadastro').value
  const senha = document.getElementById('senhaCadastro').value

  const res = await fetch('http://localhost:5000/api/cadastrar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nome, email, senha })
  })

  const data = await res.json()
  msg.innerText = data.message || data.error
})

document.getElementById('formLogin').addEventListener('submit', async (e) => {
  e.preventDefault()
  const email = document.getElementById('emailLogin').value
  const senha = document.getElementById('senhaLogin').value

  const res = await fetch('http://localhost:5000/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, senha })
  })

  const data = await res.json()
  msg.innerText = data.message || data.error
})
