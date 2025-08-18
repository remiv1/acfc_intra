document.getElementById('client_recherche').addEventListener('input', async function () {
  const query = this.value;
  if (query.length < 2) return;

  const res = await fetch(`/clients/clients?query=${encodeURIComponent(query)}`);
  const clients = await res.json();

  const list = document.getElementById('clients_suggestions');
  list.innerHTML = '';

  clients.forEach(client => {
    const li = document.createElement('li');
    li.textContent = `${client.global_name} (${client.id})`;
    li.addEventListener('click', () => {
      document.getElementById('client_recherche').value = client.global_name;
      document.getElementById('client').value = client.id;
      list.innerHTML = '';
    });
    list.appendChild(li);
  });
});