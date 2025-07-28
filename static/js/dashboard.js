const form = document.getElementById("form-imovel");
const tabelaCorpo = document.querySelector("#tabela-imoveis tbody");

async function carregarImoveis() {
  const res = await fetch("/imoveis");
  const imoveis = await res.json();

  tabelaCorpo.innerHTML = "";
  imoveis.forEach((imovel) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${imovel.id}</td>
      <td>${imovel.endereco}</td>
      <td>${imovel.descricao || ""}</td>
      <td>${imovel.preco.toFixed(2)}</td>
      <td>
        <button class="btn btn-sm btn-warning me-2" onclick="editarImovel(${imovel.id})">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-danger" onclick="deletarImovel(${imovel.id})">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    tabelaCorpo.appendChild(tr);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = document.getElementById("imovel-id").value;
  const endereco = document.getElementById("endereco").value.trim();
  const descricao = document.getElementById("descricao").value.trim();
  const preco = parseFloat(document.getElementById("preco").value);

  if (!endereco || isNaN(preco)) {
    alert("Endereço e preço são obrigatórios");
    return;
  }

  const dados = { endereco, descricao, preco };

  if (id) {
    // Atualizar
    const res = await fetch(`/imoveis/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const data = await res.json();
    alert(data.mensagem);
  } else {
    // Criar
    const res = await fetch("/imoveis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const data = await res.json();
    alert(data.mensagem);
  }

  limparFormulario();
  carregarImoveis();
});

function limparFormulario() {
  document.getElementById("imovel-id").value = "";
  document.getElementById("endereco").value = "";
  document.getElementById("descricao").value = "";
  document.getElementById("preco").value = "";
}

async function editarImovel(id) {
  const res = await fetch(`/imoveis`);
  const imoveis = await res.json();
  const imovel = imoveis.find((i) => i.id === id);

  if (imovel) {
    document.getElementById("imovel-id").value = imovel.id;
    document.getElementById("endereco").value = imovel.endereco;
    document.getElementById("descricao").value = imovel.descricao || "";
    document.getElementById("preco").value = imovel.preco;
  }
}

async function deletarImovel(id) {
  if (!confirm("Quer mesmo deletar esse imóvel?")) return;

  const res = await fetch(`/imoveis/${id}`, { method: "DELETE" });
  const data = await res.json();
  alert(data.mensagem);
  carregarImoveis();
}

// Carrega a lista quando a página abre
window.onload = carregarImoveis;
