function atualizarHora(){
    fetch("/hora")
    .then(res => res.json())
    .then(
        data=>{
            document.getElementById("relogio").innerText = data.hora;
        }
    );
}
setInterval(atualizarHora, 1000);
function destacarHoje() {
const hoje = new Date().getDate();

document.querySelectorAll("td[data-dia]").forEach(td => {
    const dia = parseInt(td.dataset.dia);
    if ( dia === hoje) {
        td.style.backgroundColor = "#cc7f0e";
    }
        });
    }

destacarHoje();
setInterval(destacarHoje, 60000); 