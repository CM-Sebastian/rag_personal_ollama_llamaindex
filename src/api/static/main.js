// Los elemenots del DOM

const navMenu = document.getElementById("menu-div")
const divMensaje_envio = document.getElementsByClassName("mensaje enviado")
const divMensaje_IA = document.getElementsByClassName("mensaje recibido");
const strMensaje = document.getElementById("textoMensaje")
const btnChatEnviar = document.getElementById("botonEnviar")
const rolCuadro = document.getElementById("rol-div")


//Botones de cierre
const btnCerrarRoles = document.getElementById("CerrarRoles-button")

//Variables para IA
let rol = ""


//LOS EVENTOS

//Funciones de utilidad

function CerrarCuadro(objectoX,cuadro){
    objectoX.addEventListener("click",()=>{
        cuadro.style.display = "None"
    })

}


//Eventos en navegacion
navMenu.addEventListener('click', (e) => {
    // Verificar que el elemento clicado sea un botón
    if (e.target.tagName === 'BUTTON') {
        
        // 1. Opcional: Remover la selección de otros botones si solo quieres uno activo a la vez
        const botones = navMenu.querySelectorAll('button');
        botones.forEach(btn => btn.classList.remove('seleccionado'));
        
        // 2. Marcar el botón actual como seleccionado
        e.target.classList.add('seleccionado');
        
        // 3. Verificar si fue seleccionado (comprobando la clase)
        if (e.target.classList.contains('seleccionado') && e.target.id == "CambiarRol") {
            rolCuadro.style.display = "block";
        }
    }
});



btnChatEnviar.addEventListener("click",async () => {
    if (!strMensaje.value){
        strMensaje.placeholder = "Debes escribir algo primero..."
    }else{
        //aqui hay error
        respuestaMensaje = await fetch("/chat-input",{
            method: "POST",
            headers: JSON.stringify({ texto: strMensaje.value }),
            body: strMensaje.value
        })
    }
});

// Conexion con python




//Funciones de solo apariencia

//Cerrar
CerrarCuadro(btnCerrarRoles,rolCuadro)



