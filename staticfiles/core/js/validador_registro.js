// static/core/js/validacion_registro.js

 $(document).ready(function() {

  // 1) Método para validar RUT chileno (formato NNNNNNNN-DV, sin puntos)
  $.validator.addMethod("rutChileno", function(value, element) {
    if (!value) return false;
    // Acepta 7 u 8 dígitos + guión + dígito verificador (0-9 o K)
    var regex = /^[0-9]{7,8}-[0-9Kk]$/;
    if (!regex.test(value)) return false;
    var partes = value.split('-');
    var cuerpo = partes[0];
    var dv     = partes[1].toUpperCase();
    var suma = 0, mul = 2;
    for (var i = cuerpo.length - 1; i >= 0; i--) {
      suma += parseInt(cuerpo.charAt(i), 10) * mul;
      mul = (mul < 7) ? (mul + 1) : 2;
    }
    var comp = 11 - (suma % 11);
    comp = (comp === 11) ? '0' : (comp === 10) ? 'K' : comp.toString();
    return comp === dv;
  }, "Ingresa un RUT válido (Ej: 12345678-5)");

  // 2) Método para permitir sólo letras y espacios
  $.validator.addMethod("soloLetrasEspacios", function(value, element) {
    return this.optional(element) || /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(value);
  }, "Sólo se permiten letras y espacios");

  // 3) Configuración del validador
  $("#form").validate({
    rules: {
      rut: {
        required: true,
        rutChileno: true
      },
      nombre_empresa: {
        required: true,
        soloLetrasEspacios: true,
        minlength: 3
      },
      username: {
        required: true,
        minlength: 3
      },
      email: {
        required: true,
        email: true
      },
      password1: {
        required: true,
        minlength: 8
      },
      password2: {
        required: true,
        equalTo: "#id_password1"
      }
    },
    messages: {
      rut: {
        required: "Debe ingresar el RUT de la empresa"
      },
      nombre_empresa: {
        required: "Debe ingresar el nombre de la empresa",
        minlength: "Mínimo 3 caracteres"
      },
      username: {
        required: "Debe elegir un nombre de usuario",
        minlength: "Mínimo 3 caracteres"
      },
      email: {
        required: "Debe ingresar un correo de contacto",
        email: "Ingresa un correo válido"
      },
      password1: {
        required: "Debe ingresar una contraseña",
        minlength: "La contraseña debe tener al menos 8 caracteres"
      },
      password2: {
        required: "Confirma la contraseña",
        equalTo: "Las contraseñas no coinciden"
      }
    },
    errorPlacement: function(error, element) {
      error.addClass("text-danger small");
      error.insertAfter(element);
    },
    highlight: function(element) {
      $(element).addClass("is-invalid");
    },
    unhighlight: function(element) {
      $(element).removeClass("is-invalid");
    }
  });

  // Asignar placeholders
  $("#id_rut").attr("placeholder", "Ej: 12345678-5");
  $("#id_nombre_empresa").attr("placeholder", "Ej: Mi Empresa SPA");
  $("#id_username").attr("placeholder", "Ej: miusuario");
  $("#id_email").attr("placeholder", "Ej: contacto@empresa.cl");
  $("#id_password1").attr("placeholder", "8 caracteres mínimo");
  $("#id_password2").attr("placeholder", "Repite la contraseña");
});
