// TECNOSOL · Comportamiento de la interfaz (sin librerías externas)

const normalizar = (texto) =>
  (texto || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

document.addEventListener("DOMContentLoaded", () => {
  // Menú lateral en celulares
  const sidebar = document.getElementById("sidebar");
  const velo = document.getElementById("velo");
  const alternarMenu = (abrir) => {
    sidebar?.classList.toggle("abierta", abrir);
    velo?.classList.toggle("visible", abrir);
  };
  document.querySelectorAll("[data-menu]").forEach((boton) =>
    boton.addEventListener("click", () => alternarMenu(!sidebar.classList.contains("abierta")))
  );
  velo?.addEventListener("click", () => alternarMenu(false));

  // Filas de tabla clickeables
  document.querySelectorAll("tr[data-href]").forEach((fila) =>
    fila.addEventListener("click", (evento) => {
      if (evento.target.closest("a, button, form, input, select")) return;
      window.location.href = fila.dataset.href;
    })
  );

  // Confirmación antes de acciones importantes
  document.querySelectorAll("form[data-confirmar]").forEach((form) =>
    form.addEventListener("submit", (evento) => {
      if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
    })
  );

  // Mensajes: se pueden cerrar y los de éxito se ocultan solos
  document.querySelectorAll(".mensaje").forEach((mensaje) => {
    mensaje.querySelector(".cerrar")?.addEventListener("click", () => mensaje.remove());
    if (mensaje.classList.contains("mensaje-exito") || mensaje.classList.contains("mensaje-info")) {
      setTimeout(() => {
        mensaje.style.opacity = "0";
        setTimeout(() => mensaje.remove(), 300);
      }, 5000);
    }
  });

  // Contador de caracteres
  document.querySelectorAll("textarea[data-contador]").forEach((area) => {
    const salida = document.getElementById(area.dataset.contador);
    const actualizar = () => (salida.textContent = `${area.value.length} / ${area.maxLength}`);
    area.addEventListener("input", actualizar);
    actualizar();
  });

  // Ctrl + Enter envía la respuesta del ticket
  const respuesta = document.getElementById("form-respuesta");
  respuesta?.querySelector("textarea")?.addEventListener("keydown", (evento) => {
    if ((evento.ctrlKey || evento.metaKey) && evento.key === "Enter") respuesta.requestSubmit();
  });

  // Detalle de ticket: si el historial se desplaza por dentro, mostrar el último hito
  const historial = document.querySelector("#historial .linea-tiempo");
  if (historial && historial.scrollHeight > historial.clientHeight) {
    historial.scrollTop = historial.scrollHeight;
  }

  // Filtro de clientes en "Nuevo ticket"
  const filtro = document.getElementById("filtro-clientes");
  if (filtro) {
    const opciones = [...document.querySelectorAll(".opcion-cliente")];
    const sinResultados = document.getElementById("sin-resultados-clientes");
    filtro.addEventListener("input", () => {
      const consulta = normalizar(filtro.value);
      let visibles = 0;
      opciones.forEach((opcion) => {
        const coincide = normalizar(opcion.dataset.buscar).includes(consulta);
        opcion.hidden = !coincide;
        if (coincide) visibles++;
      });
      sinResultados.hidden = visibles > 0;
    });
    document.querySelector(".opcion-cliente input:checked")?.scrollIntoView({ block: "nearest" });
  }

  // Nuevo ticket: el selector de producto muestra solo los del tipo elegido
  const selectTipo = document.getElementById("tipo_producto");
  const selectProducto = document.getElementById("producto_id");
  if (selectTipo && selectProducto) {
    const vacio = selectProducto.options[0];
    const todos = [...selectProducto.options].slice(1);
    // Opción "Otro (lo escribo)": solo para clientes; aparece con cualquier tipo
    const otro = todos.find((o) => o.dataset.tipo === "*");
    const campoOtro = document.getElementById("campo-producto-otro");
    const inputOtro = document.getElementById("producto_otro");
    const actualizarCampoOtro = () => {
      if (!campoOtro) return;
      const escribe = selectProducto.value === "OTRO";
      campoOtro.hidden = !escribe;
      inputOtro.required = escribe;
    };
    const actualizarProductos = () => {
      const tipo = selectTipo.value;
      const elegido = selectProducto.value;
      const visibles =
        tipo === "OTRO" ? [otro] : todos.filter((o) => o.dataset.tipo === tipo || (tipo && o === otro));
      selectProducto.replaceChildren(vacio, ...visibles.filter(Boolean));
      const sigue = visibles.some((o) => o && o.value === elegido);
      selectProducto.value = tipo === "OTRO" ? "OTRO" : sigue ? elegido : "";
      selectProducto.disabled = !tipo;
      const cantidad = visibles.filter((o) => o && o !== otro).length;
      vacio.textContent = !tipo
        ? "— Elegí primero el tipo —"
        : cantidad ? "— Elegí un producto —" : "— No hay productos de este tipo —";
      actualizarCampoOtro();
    };
    selectTipo.addEventListener("change", actualizarProductos);
    selectProducto.addEventListener("change", actualizarCampoOtro);
    actualizarProductos();
  }

  // Login: completar con un usuario de prueba
  document.querySelectorAll(".demo-usuario").forEach((boton) =>
    boton.addEventListener("click", () => {
      document.getElementById("email").value = boton.dataset.email;
      document.getElementById("password").value = boton.dataset.clave;
      document.getElementById("password").focus();
    })
  );
});
