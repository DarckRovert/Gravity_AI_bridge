# 🗝️ Guía para Activar tu Panel de Admin

¡Sin complicaciones! Sigue estos 4 pasos.

## Opción A: Firebase Authentication (Recomendado)

Esta es la forma segura y moderna. Requiere configurar Firebase primero.

1. Sigue el **[TUTORIAL_SETUP.md](./TUTORIAL_SETUP.md)** (secciones 1 y 3)
2. Crea tu usuario en Firebase Console → Authentication → Add user
3. Ve a `dulcesmoment0s.netlify.app/admin`
4. Inicia sesión con tu email y contraseña de Firebase

> ✅ **Ventaja:** Sesión real con expiración, segura, soporta múltiples admins.

---

## Opción B: Sin Firebase (Modo Local)

Si aún no tienes Firebase configurado, el sistema usa un PIN local de respaldo.

1. Ve a `dulcesmoment0s.netlify.app/admin`
2. Ingresa la clave que está configurada en el proyecto
3. La sesión se guarda en el navegador

> ⚠️ **Nota:** Esta opción es solo para desarrollo/pruebas. Configura Firebase antes de lanzar a producción.

---

## ¿Problemas para entrar?

- **No recuerdo mi contraseña Firebase:** Ve a Firebase Console → Authentication → Users → Reset password
- **¿El login no funciona?** Verifica que tus variables de entorno `NEXT_PUBLIC_FIREBASE_*` estén correctamente configuradas en Netlify
- **¿Sin Firebase?** Verifica que el proyecto esté corriendo correctamente con `npm run dev`

---

🎉 **¡LISTO!**
Una vez dentro, abre el chatbot flotante y escribe **"activar admin"** para empezar a gestionar tu tienda.
