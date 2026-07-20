// Los elemenots del DOM
const divMensaje_envio = document.getElementsByClassName("mensaje enviado")
const divMensaje_IA = document.getElementsByClassName("mensaje recibido");
const strMensaje = document.getElementById("textoMensaje")
const btnChatEnviar = document.getElementById("botonEnviar")

//Los eventos

btnChatEnviar.addEventListener("click", () => {
    if (!strMensaje.value){
        strMensaje.placeholder = "Debes escribir algo primero..."
    }else{
        //aqui hay error
        respuestaMensaje = await fetch("/chat",{
            method: "POST",
            headers: JSON.stringify({ texto: strMensaje.value }),
            body: strMensaje.value
        })
    }
});

// Conexion con python





